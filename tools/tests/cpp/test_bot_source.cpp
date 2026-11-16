// Standalone test for src/LLMChatterBotSource.h (standard
// library only; not part of the server build).
//
// Built and run by tools/tests/test_bot_source_cpp.py when a
// C++ compiler is available:
//   c++ -std=c++17 -I src tools/tests/cpp/test_bot_source.cpp
//
// Covers issue #98: random and alt bot registries merge without
// duplicates, and the General/Guild speaker rule admits bots only,
// alt bots only while enabled.

#include "LLMChatterBotSource.h"

#include <cstdint>
#include <cstdio>
#include <map>
#include <random>
#include <set>
#include <string>
#include <vector>

namespace
{

using LLMChatterBotSource::AppendUniqueBot;
using LLMChatterBotSource::ClassifySpeaker;
using LLMChatterBotSource::SpeakerDropReason;
using LLMChatterBotSource::SpeakerVerdict;

int failures = 0;

void Check(bool condition, char const* what)
{
    if (!condition)
    {
        std::printf("FAIL: %s\n", what);
        ++failures;
    }
}

struct FakeBot
{
    int id;
};

using Registry = std::map<std::uint64_t, FakeBot*>;

// Mirrors GetChatterBots(): random registry first, then each
// owner's alt registry when enabled.
std::vector<FakeBot*> Collect(
    Registry const& random, std::vector<Registry> const& owners,
    bool altBotsEnabled)
{
    std::vector<FakeBot*> out;
    std::set<std::uint64_t> seen;
    for (auto const& [guid, bot] : random)
        AppendUniqueBot(out, seen, guid, bot);
    if (!altBotsEnabled)
        return out;
    for (Registry const& owner : owners)
        for (auto const& [guid, bot] : owner)
            AppendUniqueBot(out, seen, guid, bot);
    return out;
}

void TestMerge()
{
    FakeBot r1{1}, r2{2}, a1{11}, a2{12}, dup{99};

    std::vector<FakeBot*> altOnly = Collect({}, {{{11, &a1}}}, true);
    Check(altOnly.size() == 1 && altOnly[0] == &a1,
        "alt-only registry yields its alt bot");

    std::vector<FakeBot*> randomOnly =
        Collect({{1, &r1}, {2, &r2}}, {}, true);
    Check(randomOnly.size() == 2, "random-only registry unchanged");

    std::vector<FakeBot*> mixed = Collect(
        {{1, &r1}, {2, &r2}},
        {{{11, &a1}, {2, &dup}}, {{12, &a2}, {11, &dup}}}, true);
    Check(mixed.size() == 4, "mixed registries deduplicate by GUID");
    bool randomKept = false;
    bool dupPresent = false;
    for (FakeBot* bot : mixed)
    {
        randomKept |= bot == &r2;
        dupPresent |= bot == &dup;
    }
    Check(randomKept && !dupPresent,
        "first registry to add a GUID wins");

    std::vector<FakeBot*> disabled = Collect(
        {{1, &r1}}, {{{11, &a1}}, {{12, &a2}}}, false);
    Check(disabled.size() == 1 && disabled[0] == &r1,
        "disabled keeps random-bot-only selection");

    std::vector<FakeBot*> withNull = Collect(
        {{1, nullptr}, {2, &r2}}, {{{1, &a1}}}, true);
    Check(withNull.size() == 2,
        "a null entry is skipped and does not claim its GUID");
}

void TestClassify()
{
    // A real player or self-bot (IsPlayerBot false) never speaks.
    for (bool random : {false, true})
        for (bool enabled : {false, true})
            Check(ClassifySpeaker(false, random, enabled)
                    == SpeakerVerdict::NotBot,
                "real player or self-bot is NotBot");

    Check(ClassifySpeaker(true, true, true) == SpeakerVerdict::Ok,
        "random bot speaks when enabled");
    Check(ClassifySpeaker(true, true, false) == SpeakerVerdict::Ok,
        "random bot speaks when alt bots are disabled");
    Check(ClassifySpeaker(true, false, true) == SpeakerVerdict::Ok,
        "alt bot speaks when enabled");
    Check(ClassifySpeaker(true, false, false)
            == SpeakerVerdict::AltDisabled,
        "alt bot is refused when disabled");

    Check(std::string(SpeakerDropReason(SpeakerVerdict::NotBot))
            == "speaker_not_bot",
        "NotBot drop reason");
    Check(std::string(SpeakerDropReason(SpeakerVerdict::AltDisabled))
            == "alt_bots_disabled",
        "AltDisabled drop reason");
    Check(std::string(SpeakerDropReason(SpeakerVerdict::Ok)).empty(),
        "Ok has no drop reason");
}

void TestSample()
{
    // Issue #98 review: a full random cohort (8 = MaxBotsPerZone
    // default) must not permanently exclude an alt appended after it.
    std::vector<FakeBot> randoms(8);
    FakeBot alt{100};
    Registry random;
    for (std::uint64_t i = 0; i < randoms.size(); ++i)
    {
        randoms[i].id = static_cast<int>(i);
        random[i + 1] = &randoms[i];
    }
    std::vector<Registry> owners{{{100, &alt}}};

    std::mt19937 rng(98);
    int altPicked = 0;
    bool capHeld = true;
    for (int trial = 0; trial < 400; ++trial)
    {
        std::vector<FakeBot*> pool = Collect(random, owners, true);
        LLMChatterBotSource::SampleBots(pool, 8, rng);
        capHeld &= pool.size() == 8;
        for (FakeBot* bot : pool)
            altPicked += bot == &alt;
    }
    Check(capHeld, "sample keeps exactly the cap from a larger pool");
    // Expected 8/9 of trials (~356); a fair sample is far from 0 or 400.
    Check(altPicked > 300 && altPicked < 400,
        "alt after a full random cohort is sampled fairly");

    int altWhenDisabled = 0;
    for (int trial = 0; trial < 100; ++trial)
    {
        std::vector<FakeBot*> pool = Collect(random, owners, false);
        LLMChatterBotSource::SampleBots(pool, 8, rng);
        for (FakeBot* bot : pool)
            altWhenDisabled += bot == &alt;
    }
    Check(altWhenDisabled == 0, "disabled mode never samples an alt");

    std::vector<FakeBot*> small = Collect({{1, &randoms[0]}}, owners, true);
    LLMChatterBotSource::SampleBots(small, 8, rng);
    Check(small.size() == 2, "a pool below the cap is kept whole");
}

} // namespace

int main()
{
    TestMerge();
    TestClassify();
    TestSample();
    if (failures)
    {
        std::printf("%d bot source check(s) failed\n", failures);
        return 1;
    }
    std::printf("bot source checks passed\n");
    return 0;
}
