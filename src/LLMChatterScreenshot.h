#ifndef MOD_LLM_CHATTER_SCREENSHOT_H
#define MOD_LLM_CHATTER_SCREENSHOT_H

#include <string>

class Player;

// World-thread only; no game object pointers cross capture/LLM latency.
void ResetScreenshotProximity();
void UpdateScreenshotProximity();
bool IsScreenshotProximityCurrent(
    Player* player, std::string const& eventJson);

#endif
