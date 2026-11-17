/*
 * mod-llm-chatter - per-character online flag on logout
 */

#ifndef MOD_LLM_CHATTER_ONLINE_STATE_H
#define MOD_LLM_CHATTER_ONLINE_STATE_H

// Keeps characters.online true for the characters of an account that
// are still in the world when another one of them logs out. The bridge
// reads that column to tell whether a real player is playing.
void AddLLMChatterOnlineStateScripts();

#endif
