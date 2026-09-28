#ifndef MOD_LLM_CHATTER_PROXIMITY_H
#define MOD_LLM_CHATTER_PROXIMITY_H

#include "Define.h"

#include <string>
#include <vector>

class Player;
class Creature;
class Unit;
class WorldObject;

bool IsProximityAnchorEligible(Player* player);

// Fight onlooker helpers (LLMChatterProximityFight.cpp).
// Anchor rule for a duellist: ordinary anchor checks, but
// combat is allowed when it is only with the duel opponent.
bool IsProximityFightAnchorEligible(
    Player* player, uint32 opponentGuid);
// Nearest eligible real player near `center` who is not a
// fighter and can perceive at least one fighter.
Player* FindProximityFightAnchor(
    WorldObject* center,
    std::vector<Unit*> const& fighters);
// Single onlooker policy, used at selection and again before
// each delayed emote: proximity bot eligibility (range, LOS,
// alive, not in combat, not mounted), outside the fight and
// the anchor's group, visible to the anchor. speech=true
// requires the anchor's team and perceiving every fighter;
// speech=false requires the other team and seeing the fight.
bool IsProximityFightOnlookerEligible(
    Player* anchor, Player* bot,
    std::vector<Unit*> const& fighters, bool speech);
// Shared proximity entity cooldown for a bot.
bool IsProximityFightBotOnCooldown(
    Player* anchor, Player* bot);
void MarkProximityFightBotCooldowns(
    Player* anchor, std::vector<Player*> const& roster);
// Eligible, off-cooldown onlookers split by transport.
void CollectProximityFightOnlookers(
    Player* anchor,
    std::vector<Unit*> const& fighters,
    std::vector<Player*>& sameFaction,
    std::vector<Player*>& opposite);
// Queues proximity_say (one bot) or proximity_conversation
// (2-3 bots) with `fightFields` (JSON members, no braces)
// appended. Returns false when a speaker is on cooldown.
bool QueueProximityFightSpeech(
    Player* anchor,
    std::vector<Player*> const& roster,
    std::string const& fightFields);
uint32 ComputeProximityFightChance(
    Player* anchor, uint32 baseChance);
void NoteProximityFightTrigger(Player* anchor);
bool IsProximityPlayerbotEligible(
    Player* player, Player* bot, float radius,
    bool allowMounted);
bool IsProximityDirectedPlayerbotEligible(
    Player* player, Player* bot, float radius);
bool IsProximityPlayerbotEmoteRouteEnabled();
bool IsProximityNPCEligible(
    Player* player, Creature* creature, float radius);

void CheckProximityChatter(bool instanceMaps);
void HandleProximityPlayerSay(
    Player* player, uint32 type, uint32 language,
    std::string const& msg);
void HandleProximityPlayerEmote(
    Player* player, Creature* creature,
    uint32 textEmote, uint32 mirrorEmote);
// customText carries a free-text /e or /me, in which case
// textEmote is 0 and the typed action is what gets reacted to.
bool HandleProximityPlayerbotEmote(
    Player* player, Player* bot,
    uint32 textEmote, uint32 mirrorEmote,
    std::string const& customText = "");
void RecordDeliveredProximityLine(
    uint32 eventId, uint32 playerGuid,
    uint32 zoneId, uint32 mapId,
    uint32 instanceId, uint32 botGuid,
    uint32 npcSpawnId,
    bool replyEligible,
    std::string const& speakerName,
    std::string const& message);

#endif
