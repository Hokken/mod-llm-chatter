/*
 * mod-llm-chatter - group emote domain
 *
 * Owns:
 *   - DelayedCreatureMirrorEmoteEvent
 *   - DelayedMirrorEmoteEvent
 *   - Emote static data (mirror maps, denylist,
 *     contagious set, combat callouts)
 *   - HandleEmoteAtGroupBot()
 *   - HandleEmoteAtCreature()
 *   - HandleEmoteObserver()
 *   - EvictEmoteCooldowns()
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "Creature.h"
#include "Group.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"

#include <ctime>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

// ── Emote reaction system ──────────────────────────────

/// Fires SendBotTextEmote after a short delay so the
/// mirror emote doesn't look instant/robotic.
class DelayedCreatureMirrorEmoteEvent : public BasicEvent
{
public:
    DelayedCreatureMirrorEmoteEvent(ObjectGuid playerGuid,
                                    ObjectGuid creatureGuid,
                                    uint32 emoteId,
                                    std::string playerName)
        : _playerGuid(playerGuid)
        , _creatureGuid(creatureGuid)
        , _emoteId(emoteId)
        , _playerName(std::move(playerName))
    {}

    bool Execute(uint64 /*time*/,
                 uint32 /*diff*/) override
    {
        Player* player =
            ObjectAccessor::FindConnectedPlayer(
                _playerGuid);
        if (!player || !player->IsInWorld())
            return true;

        Creature* creature =
            player->GetMap()->GetCreature(
                _creatureGuid);
        if (!creature || !creature->IsAlive()
            || creature->IsInCombat())
            return true;

        // Face the player just before animating
        creature->SetFacingToObject(player);
        SendUnitTextEmote(
            creature, _emoteId, _playerName);
        return true;
    }

private:
    ObjectGuid  _playerGuid;
    ObjectGuid  _creatureGuid;
    uint32      _emoteId;
    std::string _playerName;
};

class DelayedMirrorEmoteEvent : public BasicEvent
{
public:
    DelayedMirrorEmoteEvent(ObjectGuid botGuid,
                            ObjectGuid playerGuid,
                            uint32 emoteId,
                            std::string playerName)
        : _botGuid(botGuid)
        , _playerGuid(playerGuid)
        , _emoteId(emoteId)
        , _playerName(std::move(playerName))
    {}

    bool Execute(uint64 /*time*/,
                 uint32 /*diff*/) override
    {
        Player* bot =
            ObjectAccessor::FindConnectedPlayer(
                _botGuid);
        if (!bot || !bot->IsInWorld()
            || !bot->IsAlive())
            return true;

        // Face player just before the animation
        // so the bot hasn't drifted since hook time
        if (sLLMChatterConfig->_facingEnable
            && !bot->IsInCombat())
        {
            Player* target =
                ObjectAccessor::FindConnectedPlayer(
                    _playerGuid);
            if (target)
                bot->SetFacingToObject(target);
        }

        SendBotTextEmote(bot, _emoteId, _playerName);
        return true;
    }

private:
    ObjectGuid  _botGuid;
    ObjectGuid  _playerGuid;
    uint32      _emoteId;
    std::string _playerName;
};

// Emotes that should NOT trigger social reactions.
// All other text emotes are fair game -- even purely
// text-only emotes can generate interesting LLM responses.
// Combat callouts are handled separately by
// s_combatCalloutEmotes.
const std::unordered_set<uint32>
    s_ignoredEmotes = {
    TEXT_EMOTE_BRB,           // out-of-character meta
    TEXT_EMOTE_MESSAGE,       // system-ish
    TEXT_EMOTE_MOUNT_SPECIAL, // mount ability, not social
    TEXT_EMOTE_STOPATTACK,    // combat directive
};

// Combat callouts excluded from social reactions
const std::unordered_set<uint32>
    s_combatCalloutEmotes = {
    TEXT_EMOTE_HELPME, TEXT_EMOTE_INCOMING,
    TEXT_EMOTE_CHARGE, TEXT_EMOTE_FLEE,
    TEXT_EMOTE_ATTACKMYTARGET, TEXT_EMOTE_OOM,
    TEXT_EMOTE_FOLLOW, TEXT_EMOTE_WAIT,
    TEXT_EMOTE_HEALME, TEXT_EMOTE_OPENFIRE,
};

// Mirror map: incoming emote ID -> bot response emote ID
static const std::unordered_map<uint32, uint32>
    s_mirrorEmoteMap = {
    {TEXT_EMOTE_WAVE,         TEXT_EMOTE_WAVE},
    {TEXT_EMOTE_HELLO,        TEXT_EMOTE_WAVE},
    {TEXT_EMOTE_GREET,        TEXT_EMOTE_WAVE},
    {TEXT_EMOTE_BYE,          TEXT_EMOTE_BYE},
    {TEXT_EMOTE_WELCOME,      TEXT_EMOTE_NOD},
    {TEXT_EMOTE_BOW,          TEXT_EMOTE_BOW},
    {TEXT_EMOTE_SALUTE,       TEXT_EMOTE_SALUTE},
    {TEXT_EMOTE_CURTSEY,      TEXT_EMOTE_BOW},
    {TEXT_EMOTE_KNEEL,        TEXT_EMOTE_NOD},
    {TEXT_EMOTE_NOD,          TEXT_EMOTE_NOD},
    {TEXT_EMOTE_NO,           TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_THANK,        TEXT_EMOTE_NOD},
    {TEXT_EMOTE_YW,           TEXT_EMOTE_NOD},
    {TEXT_EMOTE_CHEER,        TEXT_EMOTE_CHEER},
    {TEXT_EMOTE_APPLAUD,      TEXT_EMOTE_APPLAUD},
    {TEXT_EMOTE_CLAP,         TEXT_EMOTE_CLAP},
    {TEXT_EMOTE_VICTORY,      TEXT_EMOTE_CHEER},
    {TEXT_EMOTE_COMMEND,      TEXT_EMOTE_NOD},
    {TEXT_EMOTE_CONGRATULATE, TEXT_EMOTE_APPLAUD},
    {TEXT_EMOTE_TOAST,        TEXT_EMOTE_CHEER},
    {TEXT_EMOTE_FLIRT,        TEXT_EMOTE_SHY},
    {TEXT_EMOTE_KISS,         TEXT_EMOTE_BLUSH},
    {TEXT_EMOTE_LAUGH,        TEXT_EMOTE_LAUGH},
    {TEXT_EMOTE_GIGGLE,       TEXT_EMOTE_GIGGLE},
    {TEXT_EMOTE_ROFL,         TEXT_EMOTE_LAUGH},
    {TEXT_EMOTE_GOLFCLAP,     TEXT_EMOTE_GOLFCLAP},
    {TEXT_EMOTE_JOKE,         TEXT_EMOTE_LAUGH},
    {TEXT_EMOTE_RUDE,         TEXT_EMOTE_CHICKEN},
    {TEXT_EMOTE_CHICKEN,      TEXT_EMOTE_RUDE},
    {TEXT_EMOTE_TAUNT,        TEXT_EMOTE_ROAR},
    {TEXT_EMOTE_INSULT,       TEXT_EMOTE_ANGRY},
    {TEXT_EMOTE_BLAME,        TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_DISAGREE,     TEXT_EMOTE_NO},
    {TEXT_EMOTE_DOUBT,        TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_CRY,          TEXT_EMOTE_MOURN},
    {TEXT_EMOTE_PLEAD,        TEXT_EMOTE_NOD},
    {TEXT_EMOTE_GROVEL,       TEXT_EMOTE_NOD},
    {TEXT_EMOTE_BEG,          TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_SURRENDER,    TEXT_EMOTE_NOD},
    {TEXT_EMOTE_DANCE,        TEXT_EMOTE_DANCE},
    {TEXT_EMOTE_POINT,        TEXT_EMOTE_NOD},
    // affection
    {TEXT_EMOTE_HUG,          TEXT_EMOTE_HUG},
    {TEXT_EMOTE_LOVE,         TEXT_EMOTE_BLUSH},
    {TEXT_EMOTE_PAT,          TEXT_EMOTE_NOD},
    {TEXT_EMOTE_WINK,         TEXT_EMOTE_SHY},
    {TEXT_EMOTE_POKE,         TEXT_EMOTE_SHY},
    {TEXT_EMOTE_TICKLE,       TEXT_EMOTE_GIGGLE},
    {TEXT_EMOTE_CUDDLE,       TEXT_EMOTE_SHY},
    // social / greeting
    {TEXT_EMOTE_SMILE,        TEXT_EMOTE_SMILE},
    {TEXT_EMOTE_AGREE,        TEXT_EMOTE_NOD},
    {TEXT_EMOTE_INTRODUCE,    TEXT_EMOTE_WAVE},
    {TEXT_EMOTE_HIGHFIVE,     TEXT_EMOTE_HIGHFIVE},
    {TEXT_EMOTE_GOODLUCK,     TEXT_EMOTE_NOD},
    // gratitude / encouragement
    {TEXT_EMOTE_APOLOGIZE,    TEXT_EMOTE_NOD},
    {TEXT_EMOTE_PRAISE,       TEXT_EMOTE_APPLAUD},
    {TEXT_EMOTE_ENCOURAGE,    TEXT_EMOTE_CHEER},
    {TEXT_EMOTE_TRUCE,        TEXT_EMOTE_NOD},
    // mockery / provocation responses
    {TEXT_EMOTE_MOCK,         TEXT_EMOTE_RUDE},
    {TEXT_EMOTE_SLAP,         TEXT_EMOTE_ANGRY},
    {TEXT_EMOTE_PUNCH,        TEXT_EMOTE_ANGRY},
    {TEXT_EMOTE_SPIT,         TEXT_EMOTE_ANGRY},
    {TEXT_EMOTE_POUNCE,       TEXT_EMOTE_ROAR},
    // misc expressive
    {TEXT_EMOTE_PANIC,        TEXT_EMOTE_CONFUSED},
    {TEXT_EMOTE_FACEPALM,     TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_ROLLEYES,     TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_FROWN,        TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_SHRUG,        TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_THINK,        TEXT_EMOTE_PONDER},
};

// Contagious emotes -- secondary bots may join in
// (mood spread, Phase 6)
static const std::unordered_set<uint32>
    s_contagiousEmotes = {
    TEXT_EMOTE_DANCE, TEXT_EMOTE_CHEER,
    TEXT_EMOTE_LAUGH, TEXT_EMOTE_APPLAUD,
    TEXT_EMOTE_ROFL, TEXT_EMOTE_VICTORY,
};

// ============================================================================
// HandleEmoteAtGroupBot
// ============================================================================

void HandleEmoteAtGroupBot(
    Player* player, Player* targetBot,
    uint32 textEmote, Group* group)
{
    if (urand(1, 100)
        > sLLMChatterConfig->_emoteMirrorChance)
        return;

    if (!targetBot->IsAlive()) return;

    uint32 botGuid =
        targetBot->GetGUID().GetCounter();
    uint32 groupId =
        group->GetGUID().GetCounter();
    time_t now = time(nullptr);

    // Only react if this emote has a mirror
    auto mit = s_mirrorEmoteMap.find(textEmote);
    if (mit == s_mirrorEmoteMap.end()) return;
    uint32 mirrorEmote = mit->second;

    // Per-bot mirror cooldown (checked and stamped
    // after confirming a mirror exists so unsupported
    // emotes don't consume the cooldown slot)
    auto it =
        _emoteReactCooldowns.find(botGuid);
    if (it != _emoteReactCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
                 ->_emoteMirrorCooldown)
        return;
    _emoteReactCooldowns[botGuid] = now;

    uint32 delayMs = urand(800, 2500);
    targetBot->m_Events.AddEvent(
        new DelayedMirrorEmoteEvent(
            targetBot->GetGUID(),
            player->GetGUID(),
            mirrorEmote,
            player->GetName()),
        targetBot->m_Events.CalculateTime(
            delayMs));

    // Phase 4 -- queue verbal reaction
    if (urand(1, 100)
        <= sLLMChatterConfig
               ->_emoteReactionChance)
    {
        auto vit =
            _emoteVerbalCooldowns.find(botGuid);
        if (vit == _emoteVerbalCooldowns.end()
            || (now - vit->second)
               >= (time_t)(
                   sLLMChatterConfig
                       ->_emoteMirrorCooldown
                   * 2))
        {
            _emoteVerbalCooldowns[botGuid] = now;
            std::string emoteName =
                GetTextEmoteName(textEmote);

            std::string extraData =
                "{\"bot_guid\":"
                + std::to_string(botGuid)
                + ",\"bot_name\":\""
                + JsonEscape(
                      targetBot->GetName())
                + "\",\"bot_class\":"
                + std::to_string(
                      targetBot->getClass())
                + ",\"bot_race\":"
                + std::to_string(
                      targetBot->getRace())
                + ",\"bot_gender\":"
                + std::to_string(
                      targetBot->getGender())
                + ",\"bot_level\":"
                + std::to_string(
                      targetBot->GetLevel())
                + ",\"emote_name\":\""
                + JsonEscape(emoteName)
                + "\",\"player_name\":\""
                + JsonEscape(player->GetName())
                + "\",\"directed\":true"
                + ",\"group_id\":"
                + std::to_string(groupId)
                + "}";

            QueueChatterEvent(
                "bot_group_emote_reaction",
                "player",
                player->GetZoneId(),
                player->GetMapId(),
                GetChatterEventPriority(
                    "bot_group_emote_reaction"),
                "",
                botGuid,
                targetBot->GetName(),
                0, "", 0,
                EscapeString(extraData),
                GetReactionDelaySeconds(
                    "bot_group_emote_reaction"),
                60, false
            );
        }
    }
    // Mood spread (Phase 6 -- deferred):
    // s_contagiousEmotes check goes here
}

// ============================================================================
// HandleEmoteAtCreature
// ============================================================================

void HandleEmoteAtCreature(
    Player* player, Creature* creature,
    uint32 textEmote)
{
    if (!sLLMChatterConfig->_emoteNPCMirrorEnable)
        return;
    if (!creature->IsAlive()) return;
    if (creature->IsInCombat()) return;
    if (creature->IsHostileTo(player)) return;
    if (creature->GetCreatureTemplate()->rank >= 3)
        return; // no bosses

    auto mit = s_mirrorEmoteMap.find(textEmote);
    if (mit == s_mirrorEmoteMap.end()) return;
    uint32 mirrorEmote = mit->second;

    uint32 creatureGuidLow =
        creature->GetGUID().GetCounter();
    time_t now = time(nullptr);
    auto it =
        _creatureEmoteCooldowns.find(
            creatureGuidLow);
    if (it != _creatureEmoteCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
                 ->_emoteMirrorCooldown)
        return;

    if (urand(1, 100)
        > sLLMChatterConfig->_emoteMirrorChance)
        return;

    _creatureEmoteCooldowns[creatureGuidLow] = now;

    uint32 delayMs = urand(800, 2500);
    player->m_Events.AddEvent(
        new DelayedCreatureMirrorEmoteEvent(
            player->GetGUID(),
            creature->GetGUID(),
            mirrorEmote,
            player->GetName()),
        player->m_Events.CalculateTime(delayMs));
}

// ============================================================================
// HandleEmoteObserver
// ============================================================================

void HandleEmoteObserver(
    Player* player, uint32 textEmote,
    Group* group,
    uint32 tgtType,
    const std::string& targetName,
    uint32 npcRank, uint32 npcType,
    uint32 npcEntry,
    const std::string& npcSubName,
    const std::vector<Player*>& candidates)
{
    if (candidates.empty()) return;

    uint32 groupId =
        group->GetGUID().GetCounter();
    time_t now = time(nullptr);

    // Per-group observer cooldown
    auto it =
        _emoteObserverCooldowns.find(groupId);
    if (it != _emoteObserverCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
                 ->_emoteObserverCooldown)
        return;
    if (urand(1, 100)
        > sLLMChatterConfig
              ->_emoteObserverChance)
        return;
    _emoteObserverCooldowns[groupId] = now;

    // Pick reactor from nearby alive bots only
    Player* reactor = candidates[
        urand(0, (uint32)(candidates.size() - 1))];
    if (!reactor) return;

    std::string emoteName =
        GetTextEmoteName(textEmote);

    const char* tgtTypeStr =
        (tgtType == EMOTE_TGT_CREATURE)
            ? "creature"
        : (tgtType == EMOTE_TGT_EXT_PLAYER)
            ? "player_external"
        : "none";

    std::string extraData =
        "{\"bot_guid\":"
        + std::to_string(
            reactor->GetGUID().GetCounter())
        + ",\"bot_name\":\""
        + JsonEscape(reactor->GetName())
        + "\",\"bot_class\":"
        + std::to_string(reactor->getClass())
        + ",\"bot_race\":"
        + std::to_string(reactor->getRace())
        + ",\"bot_gender\":"
        + std::to_string(reactor->getGender())
        + ",\"bot_level\":"
        + std::to_string(reactor->GetLevel())
        + ",\"emote_name\":\""
        + JsonEscape(emoteName)
        + "\",\"player_name\":\""
        + JsonEscape(player->GetName())
        + "\",\"target_type\":\""
        + tgtTypeStr
        + "\",\"target_name\":\""
        + JsonEscape(targetName)
        + "\",\"npc_rank\":"
        + std::to_string(npcRank)
        + ",\"npc_type\":"
        + std::to_string(npcType)
        + ",\"npc_subname\":\""
        + JsonEscape(npcSubName)
        + "\",\"group_id\":"
        + std::to_string(groupId)
        + "}";

    // For creature targets pass npcEntry as both
    // target_guid (creature sentinel: non-zero)
    // and target_entry so the delivery loop's
    // Phase 1 can FindNearestCreature() and face
    // the bot toward the NPC before speaking.
    uint32 facingEntry =
        (tgtType == EMOTE_TGT_CREATURE)
            ? npcEntry : 0u;

    QueueChatterEvent(
        "bot_group_emote_observer",
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(
            "bot_group_emote_observer"),
        "",
        reactor->GetGUID().GetCounter(),
        reactor->GetName(),
        facingEntry, targetName, facingEntry,
        EscapeString(extraData),
        GetReactionDelaySeconds(
            "bot_group_emote_observer"),
        60, false
    );
}

// ============================================================================
// EvictEmoteCooldowns
// ============================================================================

void EvictEmoteCooldowns()
{
    // Age-based eviction for per-bot and per-creature
    // emote cooldown maps.  These are keyed by unit
    // GUID (not group), so CleanupGroupSession can't
    // reach them.  Called from the World update tick
    // on the same interval as nearby-object scans.
    time_t now = time(nullptr);
    auto evict = [now](
        std::unordered_map<uint32, time_t>& m,
        time_t window)
    {
        for (auto it = m.begin(); it != m.end();)
        {
            if (now - it->second > window)
                it = m.erase(it);
            else
                ++it;
        }
    };
    time_t mirrorWindow =
        (time_t)sLLMChatterConfig->_emoteMirrorCooldown;
    evict(_emoteReactCooldowns,   mirrorWindow);
    evict(_emoteVerbalCooldowns,  mirrorWindow * 2);
    evict(_creatureEmoteCooldowns, mirrorWindow);
}
