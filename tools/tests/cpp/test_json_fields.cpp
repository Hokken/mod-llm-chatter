// Standalone test for src/LLMChatterJsonFields.h (standard
// library only; not part of the server build).
//
// Built and run by tools/tests/test_json_fields_cpp.py when a
// C++ compiler is available:
//   c++ -std=c++17 -I src tools/tests/cpp/test_json_fields.cpp
//
// The inputs mirror how MySQL re-serialises a JSON column
// (`SELECT CAST(JSON_OBJECT(...) AS CHAR)`): sorted keys and a
// space after every ':' and ','.

#include "LLMChatterJsonFields.h"

#include <cstdint>
#include <cstdio>
#include <string>

namespace
{

int failures = 0;

void Check(bool condition, char const* what)
{
    if (!condition)
    {
        std::printf("FAIL: %s\n", what);
        ++failures;
    }
}

} // namespace

int main()
{
    using LLMChatterJson::ReadString;
    using LLMChatterJson::ReadUInt64;

    // Database-formatted row, as delivery reads it back.
    std::string const db =
        "{\"fight_at\": 0, \"fight_a_guid\": 101, "
        "\"fight_b_guid\": 202, \"fight_instance_id\": 7, "
        "\"fight_kind\": \"duel\", "
        "\"fight_moment\": \"during\", "
        "\"fight_scene\": {\"kind\": \"duel\", "
        "\"moment\": \"during\"}, \"zone_id\": 12}";

    std::string kind;
    Check(ReadString(db, "fight_kind", kind) && kind == "duel",
        "db fight_kind");
    std::string moment;
    Check(ReadString(db, "fight_moment", moment)
            && moment == "during",
        "db fight_moment");
    std::uint64_t value = 0;
    Check(ReadUInt64(db, "fight_instance_id", value)
            && value == 7,
        "db fight_instance_id");
    Check(ReadUInt64(db, "fight_a_guid", value) && value == 101,
        "db fight_a_guid");
    Check(ReadUInt64(db, "fight_b_guid", value) && value == 202,
        "db fight_b_guid");
    Check(ReadUInt64(db, "fight_at", value) && value == 0,
        "db fight_at zero is present");

    // Compact form as written by C++.
    std::string const compact =
        "{\"fight_kind\":\"pvp\",\"fight_at\":1790000000}";
    Check(ReadString(compact, "fight_kind", kind)
            && kind == "pvp",
        "compact fight_kind");
    Check(ReadUInt64(compact, "fight_at", value)
            && value == 1790000000ULL,
        "compact fight_at");

    // Whitespace variants around the colon.
    Check(ReadString("{\"k\" :\t\"v\"}", "k", kind)
            && kind == "v",
        "whitespace before and after colon");

    // Missing members, wrong types, and overflow fail safely.
    Check(!ReadString(db, "fight_missing", kind),
        "missing string");
    Check(!ReadUInt64(db, "fight_missing", value),
        "missing number");
    Check(!ReadUInt64(db, "fight_kind", value),
        "string is not a number");
    Check(!ReadString(db, "fight_instance_id", kind),
        "number is not a string");
    Check(!ReadUInt64(
            "{\"n\": 99999999999999999999999}", "n", value),
        "overflow rejected");

    // A key-like string value is not treated as a member.
    Check(ReadString(
            "{\"note\": \"fight_kind\", \"fight_kind\": \"duel\"}",
            "fight_kind", kind)
            && kind == "duel",
        "key text inside a value is skipped");

    // Structured delivery contracts must only read exact root members.
    using namespace LLMChatterJson;
    Members fields;
    Check(ReadObject(R"({"nested":{"id":12},"id":7})", fields)
        && UInt(fields, "id", value) && value == 7,
        "nested key cannot shadow root identity");
    Check(ReadObject(R"({"nested":{"id":12}})", fields)
        && !UInt(fields, "id", value), "nested-only identity rejected");
    for (auto input : {R"({"id":1,"id":2})", R"({"id":1,})",
        R"({"id":01})", R"({"id":1} trailing)", R"({"id":1oops})"})
        Check(!ReadObject(input, fields), "malformed contract rejected");
    for (auto input : {R"({"id":-1})", R"({"id":1.5})",
        R"({"id":1e3})", R"({"id":"1"})", R"({"id":true})",
        R"({"id":18446744073709551616})"})
        Check(ReadObject(input, fields) && !UInt(fields, "id", value),
            "identity requires whole unsigned integer in range");
    Check(ReadObject(R"({"token":"x\"y","text":"\u00e9"})", fields)
        && String(fields, "token", kind) && kind == "x\"y",
        "escaped token and opaque unicode payload");
    std::vector<std::string_view> nodes;
    Check(ReadArray(R"([{"id":0},{"id":1}])", nodes)
        && nodes.size() == 2 && ReadObject(nodes[1], fields)
        && UInt(fields, "id", value) && value == 1, "node array views");
    Check(!ReadArray("[1,]", nodes), "trailing array comma rejected");

    if (failures == 0)
        std::printf("OK\n");
    return failures == 0 ? 0 : 1;
}
