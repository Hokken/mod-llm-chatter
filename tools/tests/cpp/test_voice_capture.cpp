// Standalone policy tests. Compile only with explicit build authorization.
#include "LLMChatterVoiceCapture.h"
#include <cassert>

using LLMChatterVoice::ChatCapture;

int main()
{
    constexpr std::uint32_t BOT = 42;
    constexpr std::uint32_t SAY = 1;
    constexpr std::uint32_t YELL = 6;
    ChatCapture capture;
    std::string out;

    // Allowed line: voiced with the text the hooks let through.
    capture.Arm(BOT, SAY);
    capture.Observe(BOT, SAY, "Well met");
    assert(capture.Take(false, out) && out == "Well met");

    // An earlier hook rewrote the text: the rewrite is what is voiced.
    capture.Arm(BOT, SAY);
    capture.Observe(BOT, SAY, "Well met, friend");
    assert(capture.Take(false, out) && out == "Well met, friend");

    // An earlier hook vetoed: our last hook never runs, nothing voiced.
    out.clear();
    capture.Arm(BOT, SAY);
    assert(!capture.Take(false, out) && out.empty());

    // Chat filter rejected the line after the hooks: nothing voiced.
    capture.Arm(BOT, YELL);
    capture.Observe(BOT, YELL, "filtered words");
    assert(!capture.Take(true, out) && out.empty());

    // Another speaker or chat type never satisfies the capture.
    capture.Arm(BOT, SAY);
    capture.Observe(BOT + 1, SAY, "someone else");
    capture.Observe(BOT, YELL, "other type");
    assert(!capture.Take(false, out));

    // Take always disarms: a later unrelated say is not captured.
    capture.Observe(BOT, SAY, "late");
    assert(!capture.armed && !capture.Take(false, out));
    return 0;
}
