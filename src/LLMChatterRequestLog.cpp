/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Reader for the Python bridge's JSONL request log
 */

#include "LLMChatterRequestLog.h"
#include "LLMChatterConfig.h"

#include <cstddef>
#include <cstdlib>
#include <fstream>
#include <mutex>
#include <string>
#include <vector>

namespace
{
// Every line the bridge writes is a flat object of string,
// number and null values, so a targeted scanner is enough;
// the core ships no JSON library.

void SkipJsonSpace(std::string const& in, size_t& pos)
{
    while (pos < in.size()
        && (in[pos] == ' ' || in[pos] == '\t'
            || in[pos] == '\r' || in[pos] == '\n'))
    {
        ++pos;
    }
}

void AppendUtf8(std::string& out, uint32 cp)
{
    if (cp < 0x80)
    {
        out.push_back(static_cast<char>(cp));
    }
    else if (cp < 0x800)
    {
        out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    }
    else if (cp < 0x10000)
    {
        out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
        out.push_back(
            static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    }
    else
    {
        out.push_back(static_cast<char>(0xF0 | (cp >> 18)));
        out.push_back(
            static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
        out.push_back(
            static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    }
}

bool ReadHex4(std::string const& in, size_t pos, uint32& out)
{
    if (pos + 4 > in.size())
        return false;

    uint32 value = 0;
    for (size_t i = 0; i < 4; ++i)
    {
        char ch = in[pos + i];
        uint32 digit;
        if (ch >= '0' && ch <= '9')
            digit = static_cast<uint32>(ch - '0');
        else if (ch >= 'a' && ch <= 'f')
            digit = static_cast<uint32>(ch - 'a' + 10);
        else if (ch >= 'A' && ch <= 'F')
            digit = static_cast<uint32>(ch - 'A' + 10);
        else
            return false;

        value = (value << 4) | digit;
    }

    out = value;
    return true;
}

// `pos` must sit on the opening quote; on success it lands
// one past the closing quote.
bool ParseJsonString(
    std::string const& in, size_t& pos, std::string& out)
{
    if (pos >= in.size() || in[pos] != '"')
        return false;

    ++pos;
    out.clear();

    while (pos < in.size())
    {
        char ch = in[pos];

        if (ch == '"')
        {
            ++pos;
            return true;
        }

        if (ch != '\\')
        {
            out.push_back(ch);
            ++pos;
            continue;
        }

        if (pos + 1 >= in.size())
            return false;

        char esc = in[pos + 1];
        pos += 2;

        switch (esc)
        {
            case '"':  out.push_back('"');  break;
            case '\\': out.push_back('\\'); break;
            case '/':  out.push_back('/');  break;
            case 'b':  out.push_back('\b'); break;
            case 'f':  out.push_back('\f'); break;
            case 'n':  out.push_back('\n'); break;
            case 'r':  out.push_back('\r'); break;
            case 't':  out.push_back('\t'); break;
            case 'u':
            {
                uint32 cp = 0;
                if (!ReadHex4(in, pos, cp))
                    return false;
                pos += 4;

                // High surrogate: pair it with the low one.
                if (cp >= 0xD800 && cp <= 0xDBFF
                    && pos + 1 < in.size()
                    && in[pos] == '\\' && in[pos + 1] == 'u')
                {
                    uint32 low = 0;
                    if (ReadHex4(in, pos + 2, low)
                        && low >= 0xDC00 && low <= 0xDFFF)
                    {
                        cp = 0x10000
                            + ((cp - 0xD800) << 10)
                            + (low - 0xDC00);
                        pos += 6;
                    }
                }

                // A surrogate left alone is not encodable.
                if (cp >= 0xD800 && cp <= 0xDFFF)
                    cp = 0xFFFD;

                AppendUtf8(out, cp);
                break;
            }
            default:
                return false;
        }
    }

    return false;
}

// Step over an object or array value we do not model.
bool SkipJsonContainer(std::string const& in, size_t& pos)
{
    char open = in[pos];
    char close = (open == '{') ? '}' : ']';
    int depth = 0;

    while (pos < in.size())
    {
        char ch = in[pos];

        if (ch == '"')
        {
            std::string ignored;
            if (!ParseJsonString(in, pos, ignored))
                return false;
            continue;
        }

        if (ch == open)
            ++depth;
        else if (ch == close)
            --depth;

        ++pos;

        if (depth == 0)
            return true;
    }

    return false;
}

void AssignLogField(
    LLMRequestLogEntry& entry,
    std::string const& key,
    std::string const& value)
{
    if (key == "seq")
        entry.seq = std::strtoull(value.c_str(), nullptr, 10);
    else if (key == "timestamp")
        entry.timestamp = value;
    else if (key == "label")
        entry.label = value;
    else if (key == "model")
        entry.model = value;
    else if (key == "provider")
        entry.provider = value;
    else if (key == "duration_ms")
        entry.durationMs = static_cast<uint32>(
            std::strtoul(value.c_str(), nullptr, 10));
    else if (key == "system_prompt")
        entry.systemPrompt = value;
    else if (key == "prompt")
        entry.prompt = value;
    else if (key == "response")
        entry.response = value;
    else if (!value.empty())
        entry.extras.emplace_back(key, value);
}

bool ParseLogLine(
    std::string const& line, LLMRequestLogEntry& entry)
{
    size_t pos = 0;
    SkipJsonSpace(line, pos);

    if (pos >= line.size() || line[pos] != '{')
        return false;

    ++pos;

    while (true)
    {
        SkipJsonSpace(line, pos);
        if (pos >= line.size())
            return false;

        if (line[pos] == '}')
            return true;

        if (line[pos] == ',')
        {
            ++pos;
            continue;
        }

        std::string key;
        if (!ParseJsonString(line, pos, key))
            return false;

        SkipJsonSpace(line, pos);
        if (pos >= line.size() || line[pos] != ':')
            return false;

        ++pos;
        SkipJsonSpace(line, pos);
        if (pos >= line.size())
            return false;

        char ch = line[pos];
        std::string value;

        if (ch == '"')
        {
            if (!ParseJsonString(line, pos, value))
                return false;
        }
        else if (ch == '{' || ch == '[')
        {
            size_t start = pos;
            if (!SkipJsonContainer(line, pos))
                return false;
            value = line.substr(start, pos - start);
        }
        else
        {
            size_t start = pos;
            while (pos < line.size()
                && line[pos] != ','
                && line[pos] != '}')
            {
                ++pos;
            }

            value = line.substr(start, pos - start);
            while (!value.empty()
                && (value.back() == ' '
                    || value.back() == '\t'))
            {
                value.pop_back();
            }

            // A missing response is logged as JSON null.
            if (value == "null")
                value.clear();
        }

        AssignLogField(entry, key, value);
    }
}

struct RequestLogCache
{
    std::string path;
    // Bytes of the file already folded into `entries`; also
    // the offset the next incremental read starts from.
    uint64 parsedUpTo = 0;
    uint64 lastSize = 0;
    uint64 lastSeq = 0;
    std::vector<LLMRequestLogEntry> entries;

    void Reset()
    {
        parsedUpTo = 0;
        lastSize = 0;
        lastSeq = 0;
        entries.clear();
    }
};

std::mutex g_requestLogMutex;
RequestLogCache g_requestLogCache;

uint64 ConfiguredTailBytes()
{
    uint32 configured = sLLMChatterConfig
        ? sLLMChatterConfig->_addonLogTailBytes
        : 2097152;

    return configured ? configured : 2097152;
}

size_t ConfiguredMaxEntries()
{
    uint32 configured = sLLMChatterConfig
        ? sLLMChatterConfig->_addonLogMaxEntries
        : 100;

    return configured ? configured : 100;
}

// Caller must hold g_requestLogMutex.
bool RefreshCache(std::string const& path, std::string& error)
{
    std::ifstream file(path.c_str(), std::ios::binary);
    if (!file)
    {
        error = "Request log not readable: " + path;
        g_requestLogCache.Reset();
        g_requestLogCache.path = path;
        return false;
    }

    file.seekg(0, std::ios::end);
    std::streamoff endOff = file.tellg();
    if (endOff < 0)
    {
        error = "Could not size the request log";
        return false;
    }

    uint64 size = static_cast<uint64>(endOff);

    if (g_requestLogCache.path != path)
    {
        g_requestLogCache.Reset();
        g_requestLogCache.path = path;
    }

    // Rotation replaces the file with a shorter one, which
    // invalidates every offset we remembered.
    if (size < g_requestLogCache.parsedUpTo)
        g_requestLogCache.Reset();

    if (size == g_requestLogCache.lastSize
        && !g_requestLogCache.entries.empty())
    {
        return true;
    }

    uint64 tailBytes = ConfiguredTailBytes();
    uint64 start = g_requestLogCache.parsedUpTo;

    // A cold read only walks back as far as the tail budget,
    // so the first line it sees is usually a fragment.
    bool dropFirstLine = false;
    if (start == 0 && size > tailBytes)
    {
        start = size - tailBytes;
        dropFirstLine = true;
    }

    if (size <= start)
    {
        g_requestLogCache.lastSize = size;
        return true;
    }

    size_t length = static_cast<size_t>(size - start);
    std::string buffer;
    buffer.resize(length);

    file.seekg(static_cast<std::streamoff>(start),
        std::ios::beg);
    file.read(&buffer[0], static_cast<std::streamsize>(length));
    buffer.resize(static_cast<size_t>(file.gcount()));

    // The bridge may be mid-write, so stop at the last
    // complete line and resume from there next time.
    size_t lastNewline = buffer.find_last_of('\n');
    if (lastNewline == std::string::npos)
    {
        g_requestLogCache.lastSize = size;
        return true;
    }

    uint64 consumed = static_cast<uint64>(lastNewline) + 1;
    buffer.resize(static_cast<size_t>(lastNewline));

    size_t cursor = 0;
    if (dropFirstLine)
    {
        size_t firstNewline = buffer.find('\n');
        if (firstNewline == std::string::npos)
        {
            g_requestLogCache.parsedUpTo = start + consumed;
            g_requestLogCache.lastSize = size;
            return true;
        }

        cursor = firstNewline + 1;
    }

    size_t maxEntries = ConfiguredMaxEntries();

    while (cursor <= buffer.size())
    {
        size_t next = buffer.find('\n', cursor);
        size_t stop = (next == std::string::npos)
            ? buffer.size() : next;

        std::string line =
            buffer.substr(cursor, stop - cursor);

        if (!line.empty() && line.back() == '\r')
            line.pop_back();

        if (!line.empty())
        {
            LLMRequestLogEntry entry;
            // The logger numbers from 1, so a missing seq
            // means the line is not one of its records.
            if (ParseLogLine(line, entry) && entry.seq)
            {
                // The bridge restarts its counter at zero, so
                // a step backwards means these entries belong
                // to a different run than the cached ones.
                if (entry.seq <= g_requestLogCache.lastSeq
                    && !g_requestLogCache.entries.empty())
                {
                    g_requestLogCache.entries.clear();
                }

                g_requestLogCache.lastSeq = entry.seq;
                g_requestLogCache.entries.push_back(entry);
            }
        }

        if (next == std::string::npos)
            break;

        cursor = next + 1;
    }

    if (g_requestLogCache.entries.size() > maxEntries)
    {
        size_t excess =
            g_requestLogCache.entries.size() - maxEntries;
        g_requestLogCache.entries.erase(
            g_requestLogCache.entries.begin(),
            g_requestLogCache.entries.begin()
                + static_cast<std::ptrdiff_t>(excess));
    }

    g_requestLogCache.parsedUpTo = start + consumed;
    g_requestLogCache.lastSize = size;
    return true;
}
}  // namespace

std::string GetRequestLogPath()
{
    if (!sLLMChatterConfig)
        return "";

    return sLLMChatterConfig->_addonLogPath;
}

bool LoadRequestLogTail(
    std::vector<LLMRequestLogEntry>& out, std::string& error)
{
    out.clear();

    std::string path = GetRequestLogPath();
    if (path.empty())
    {
        error = "LLMChatter.AddonLog.Path is empty";
        return false;
    }

    std::lock_guard<std::mutex> guard(g_requestLogMutex);

    if (!RefreshCache(path, error))
        return false;

    out = g_requestLogCache.entries;
    return true;
}

bool FindRequestLogEntry(
    uint64 seq, LLMRequestLogEntry& out, std::string& error)
{
    std::vector<LLMRequestLogEntry> entries;
    if (!LoadRequestLogTail(entries, error))
        return false;

    for (LLMRequestLogEntry const& entry : entries)
    {
        if (entry.seq == seq)
        {
            out = entry;
            return true;
        }
    }

    error = "That entry is no longer in the log tail";
    return false;
}
