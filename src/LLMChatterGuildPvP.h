/*
 * mod-llm-chatter - open-world PvP reactions
 */

#ifndef MOD_LLM_CHATTER_GUILD_PVP_H
#define MOD_LLM_CHATTER_GUILD_PVP_H

#include "Define.h"

#include <string>

class Player;

// Open-world kill between the factions: records the kill (called from
// the map thread). The next world update may then let the killing bot
// comment in its Guild chat, and the slain bot complain in Guild or in
// its zone's General channel.
void HandleOpenWorldPvpKill(Player* killer, Player* killed);

bool IsPvpReactionEvent(std::string const& eventType);

// Delivery-time check for a PvP reaction line: nullptr when the bot may
// still speak, otherwise the drop reason. The line only goes to the
// guild (guildId) or zone (zoneId) it was written for, and only while a
// real player there can read it.
char const* CheckPvpReactionDelivery(
    Player* bot, std::string const& eventType,
    uint32 guildId, uint32 zoneId);

void AddLLMChatterGuildPvPScripts();

#endif
