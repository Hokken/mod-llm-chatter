/*
 * mod-llm-chatter - open-world PvP reactions
 */

#ifndef MOD_LLM_CHATTER_GUILD_PVP_H
#define MOD_LLM_CHATTER_GUILD_PVP_H

class Player;

// Open-world kill between the factions: the killing bot may comment in
// its Guild chat, and the slain bot may complain in Guild or in its
// zone's General channel.
void HandleOpenWorldPvpKill(Player* killer, Player* killed);

#endif
