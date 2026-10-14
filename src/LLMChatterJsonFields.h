#ifndef MOD_LLM_CHATTER_JSON_FIELDS_H
#define MOD_LLM_CHATTER_JSON_FIELDS_H

/*
 * mod-llm-chatter - flat JSON member readers
 *
 * Dependency-free (standard library only) so the readers can
 * be unit-tested outside the server build
 * (tools/tests/cpp/test_json_fields.cpp).
 *
 * Event extra_data is written compactly by C++ but read back
 * from a MySQL JSON column, which re-serialises it as
 * `{"key": value, ...}` with spaces after ':' and ','. These
 * readers accept any whitespace around the colon.
 */

#include <cctype>
#include <cstdint>
#include <limits>
#include <string>
#include <charconv>
#include <map>
#include <string_view>
#include <vector>

namespace LLMChatterJson
{

// Strict structured readers for delivery contracts. Views borrow the input;
// do not retain them after it dies. Existing flat readers remain unchanged.
using Members = std::map<std::string, std::string_view>;

inline void SkipSpace(std::string_view text, size_t& p)
{
    while (p < text.size() && (text[p] == ' ' || text[p] == '\n'
        || text[p] == '\r' || text[p] == '\t'))
        ++p;
}

inline bool ScanString(std::string_view text, size_t& p,
    std::string* decoded = nullptr)
{
    if (p >= text.size() || text[p++] != '"')
        return false;
    while (p < text.size())
    {
        unsigned char c = text[p++];
        if (c == '"')
            return true;
        if (c < 0x20)
            return false;
        if (c == '\\')
        {
            if (p == text.size())
                return false;
            c = text[p++];
            if (c == 'u')
            {
                unsigned value = 0;
                for (unsigned i = 0; i < 4; ++i)
                {
                    if (p == text.size())
                        return false;
                    char h = text[p++];
                    unsigned digit = h >= '0' && h <= '9' ? h - '0'
                        : h >= 'a' && h <= 'f' ? h - 'a' + 10
                        : h >= 'A' && h <= 'F' ? h - 'A' + 10 : 16;
                    if (digit == 16)
                        return false;
                    value = value * 16 + digit;
                }
                // Contract names/tokens are ASCII. Non-ASCII payload text
                // is skipped, never decoded by this contract reader.
                if (decoded && value > 127)
                    return false;
                c = static_cast<unsigned char>(value);
            }
            else
            {
                switch (c)
                {
                    case '"': case '\\': case '/': break;
                    case 'b': c = '\b'; break;
                    case 'f': c = '\f'; break;
                    case 'n': c = '\n'; break;
                    case 'r': c = '\r'; break;
                    case 't': c = '\t'; break;
                    default: return false;
                }
            }
        }
        if (decoded)
            *decoded += static_cast<char>(c);
    }
    return false;
}

inline bool ScanValue(std::string_view text, size_t& p, unsigned depth = 0,
    Members* members = nullptr, std::vector<std::string_view>* array = nullptr)
{
    SkipSpace(text, p);
    if (p == text.size() || depth > 32)
        return false;
    char c = text[p];
    if (c == '"')
        return ScanString(text, p);
    if (c == '{' || c == '[')
    {
        bool object = c == '{';
        char end = object ? '}' : ']';
        ++p;
        SkipSpace(text, p);
        if (p < text.size() && text[p] == end)
        {
            ++p;
            return true;
        }
        while (p < text.size())
        {
            std::string key;
            if (object)
            {
                if (!ScanString(text, p, members ? &key : nullptr))
                    return false;
                SkipSpace(text, p);
                if (p == text.size() || text[p++] != ':')
                    return false;
                SkipSpace(text, p);
            }
            size_t begin = p;
            if (!ScanValue(text, p, depth + 1))
                return false;
            if (object && members
                && !members->emplace(key, text.substr(begin, p - begin)).second)
                return false;
            if (!object && array)
                array->push_back(text.substr(begin, p - begin));
            SkipSpace(text, p);
            if (p == text.size())
                return false;
            if (text[p] == end)
            {
                ++p;
                return true;
            }
            if (text[p++] != ',')
                return false;
            SkipSpace(text, p);
        }
        return false;
    }
    for (std::string_view literal : {"true", "false", "null"})
        if (text.substr(p, literal.size()) == literal)
        {
            p += literal.size();
            return true;
        }
    if (c == '-')
        ++p;
    if (p == text.size() || text[p] < '0' || text[p] > '9')
        return false;
    if (text[p] == '0')
        ++p;
    else
        while (p < text.size() && text[p] >= '0' && text[p] <= '9')
            ++p;
    for (char part : {'.', 'e'})
    {
        if (p < text.size() && (text[p] == part
            || (part == 'e' && text[p] == 'E')))
        {
            ++p;
            if (part == 'e' && p < text.size()
                && (text[p] == '+' || text[p] == '-'))
                ++p;
            size_t begin = p;
            while (p < text.size() && text[p] >= '0' && text[p] <= '9')
                ++p;
            if (begin == p)
                return false;
        }
    }
    return true;
}

inline bool ReadObject(std::string_view json, Members& out)
{
    out.clear();
    size_t p = 0;
    SkipSpace(json, p);
    if (p == json.size() || json[p] != '{'
        || !ScanValue(json, p, 0, &out))
        return false;
    SkipSpace(json, p);
    return p == json.size();
}

inline bool ReadArray(std::string_view json, std::vector<std::string_view>& out)
{
    out.clear();
    size_t p = 0;
    SkipSpace(json, p);
    if (p == json.size() || json[p] != '['
        || !ScanValue(json, p, 0, nullptr, &out))
        return false;
    SkipSpace(json, p);
    return p == json.size();
}

inline bool UInt(Members const& fields, char const* key, std::uint64_t& out)
{
    auto it = fields.find(key);
    if (it == fields.end() || it->second.empty())
        return false;
    auto value = it->second;
    auto result = std::from_chars(value.data(), value.data() + value.size(), out);
    return result.ec == std::errc()
        && result.ptr == value.data() + value.size();
}

inline bool String(Members const& fields, char const* key, std::string& out)
{
    auto it = fields.find(key);
    if (it == fields.end())
        return false;
    out.clear();
    size_t p = 0;
    return ScanString(it->second, p, &out) && p == it->second.size();
}

// Position of the value for member `key`, or npos.
inline std::string::size_type FindValue(
    std::string const& json, char const* key)
{
    if (!key || !*key)
        return std::string::npos;

    std::string const marker =
        std::string("\"") + key + "\"";
    std::string::size_type pos = 0;
    while ((pos = json.find(marker, pos))
        != std::string::npos)
    {
        std::string::size_type p = pos + marker.size();
        while (p < json.size()
            && std::isspace(
                static_cast<unsigned char>(json[p])))
            ++p;
        if (p < json.size() && json[p] == ':')
        {
            ++p;
            while (p < json.size()
                && std::isspace(
                    static_cast<unsigned char>(json[p])))
                ++p;
            return p;
        }
        pos += marker.size();
    }
    return std::string::npos;
}

// Unsigned integer member. False when missing, not a number,
// or out of range.
inline bool ReadUInt64(
    std::string const& json, char const* key,
    std::uint64_t& out)
{
    std::string::size_type p = FindValue(json, key);
    if (p == std::string::npos)
        return false;

    std::uint64_t value = 0;
    bool digit = false;
    std::uint64_t const max =
        std::numeric_limits<std::uint64_t>::max();
    while (p < json.size()
        && std::isdigit(
            static_cast<unsigned char>(json[p])))
    {
        std::uint64_t const d =
            static_cast<std::uint64_t>(json[p] - '0');
        if (value > (max - d) / 10)
            return false;
        value = value * 10 + d;
        digit = true;
        ++p;
    }
    if (!digit)
        return false;
    out = value;
    return true;
}

// String member, with backslash escapes reduced to the
// escaped character (sufficient for the ASCII tokens read).
inline bool ReadString(
    std::string const& json, char const* key,
    std::string& out)
{
    std::string::size_type p = FindValue(json, key);
    if (p == std::string::npos || p >= json.size()
        || json[p] != '"')
        return false;

    std::string value;
    for (++p; p < json.size(); ++p)
    {
        char const c = json[p];
        if (c == '\\')
        {
            if (++p >= json.size())
                return false;
            value += json[p];
            continue;
        }
        if (c == '"')
        {
            out = value;
            return true;
        }
        value += c;
    }
    return false;
}

} // namespace LLMChatterJson

#endif
