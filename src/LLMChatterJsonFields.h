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

namespace LLMChatterJson
{

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
