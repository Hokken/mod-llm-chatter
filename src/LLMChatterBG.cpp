/*
 * mod-llm-chatter - Battleground chatter helpers and hooks
 */

#include "LLMChatterConfig.h"
#include "LLMChatterBG.h"
#include "LLMChatterShared.h"

#include "ScriptMgr.h"
#include "Player.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Battleground.h"
#include "BattlegroundWS.h"
#include "BattlegroundAB.h"
#include "BattlegroundEY.h"
#include "GameTime.h"
#include "Log.h"

#include <map>
#include <unordered_map>
#include <vector>

static std::string GetRaceName(uint8 race)
{
    switch (race)
    {
        case RACE_HUMAN:        return "Human";
        case RACE_ORC:          return "Orc";
        case RACE_DWARF:        return "Dwarf";
        case RACE_NIGHTELF:     return "Night Elf";
        case RACE_UNDEAD_PLAYER:return "Undead";
        case RACE_TAUREN:       return "Tauren";
        case RACE_GNOME:        return "Gnome";
        case RACE_TROLL:        return "Troll";
        case RACE_BLOODELF:     return "Blood Elf";
        case RACE_DRAENEI:      return "Draenei";
        default:                return "Unknown";
    }
}

struct BGStateTracker
{
    uint32 diffAccum = 0;
    uint32 totalElapsedMs = 0;

    uint32 lastScoreAlliance = 0;
    uint32 lastScoreHorde = 0;
    ObjectGuid lastFlagPickerAlliance;
    ObjectGuid lastFlagPickerHorde;
    uint8 lastFlagStateAlliance{0};
    uint8 lastFlagStateHorde{0};

    static constexpr uint32 NO_CAPTURE = UINT32_MAX;
    uint32 lastCaptureAllianceMs{NO_CAPTURE};
    uint32 lastCaptureHordeMs{NO_CAPTURE};

    std::map<uint8, uint8> lastNodeState;

    std::vector<ObjectGuid> pendingArrivals;
    uint32 firstArrivalMs{0};

    uint32 lastIdleChatterMs{0};

    static constexpr uint32 NO_BIG_EVENT = UINT32_MAX;
    uint32 lastBigEventMs = NO_BIG_EVENT;

    bool IsBigEventOnCooldown() const
    {
        if (lastBigEventMs == NO_BIG_EVENT)
            return false;
        uint32 cooldownMs =
            sLLMChatterConfig->_bgBigEventCooldownSec
            * 1000;
        uint32 elapsed =
            totalElapsedMs - lastBigEventMs;
        return elapsed < cooldownMs;
    }

    void MarkBigEvent()
    {
        lastBigEventMs = totalElapsedMs;
    }

    bool WasFlagRecentlyCaptured(
        uint32 captureMs, uint32 suppressMs) const
    {
        if (captureMs == NO_CAPTURE)
            return false;
        return (totalElapsedMs - captureMs)
            <= suppressMs;
    }
};

static std::unordered_map<uint32, BGStateTracker>
    _bgTrackers;

void AppendBGContext(
    Battleground* bg, Player* player,
    std::string& json)
{
    if (!json.empty() && json.back() == '}')
        json.pop_back();

    std::string bgName = bg->GetName();
    for (size_t p = 0;
         (p = bgName.find('"', p))
             != std::string::npos;
         p += 2)
        bgName.insert(p, "\\");

    json += ","
        "\"is_battleground\":true,"
        "\"zone_id\":"
        + std::to_string(
            player->GetZoneId()) + ","
        "\"bg_type\":\"" + bgName + "\","
        "\"bg_type_id\":"
        + std::to_string(
            bg->GetBgTypeID()) + ","
        "\"team\":\""
        + std::string(
            player->GetBgTeamId()
                == TEAM_ALLIANCE
                    ? "Alliance" : "Horde") + "\","
        "\"score_alliance\":"
        + std::to_string(
            bg->GetTeamScore(
                TEAM_ALLIANCE)) + ","
        "\"score_horde\":"
        + std::to_string(
            bg->GetTeamScore(
                TEAM_HORDE)) + ","
        "\"players_alive_team\":"
        + std::to_string(
            bg->GetAlivePlayersCountByTeam(
                player->GetBgTeamId())) + ","
        "\"players_alive_enemy\":"
        + std::to_string(
            bg->GetAlivePlayersCountByTeam(
                player->GetBgTeamId()
                    == TEAM_ALLIANCE
                        ? TEAM_HORDE
                        : TEAM_ALLIANCE));

    /* Real players on same team — name + race */
    {
        TeamId bTeam = player->GetBgTeamId();
        bool first = true;
        json += ",\"real_players\":[";
        for (auto const& [g, p] :
             bg->GetPlayers())
        {
            Player* rp =
                ObjectAccessor::FindPlayer(g);
            if (!rp || IsPlayerBot(rp))
                continue;
            if (rp->GetBgTeamId() != bTeam)
                continue;
            if (!first) json += ",";
            json += "{\"name\":\""
                + JsonEscape(rp->GetName())
                + "\",\"race\":\""
                + JsonEscape(
                    GetRaceName(rp->getRace()))
                + "\"}";
            first = false;
        }
        json += "]";
    }

    /* WSG: inject current flag carriers */
    if (BattlegroundWS* wsg =
            bg->ToBattlegroundWS())
    {
        TeamId pTeam = player->GetBgTeamId();
        /* Enemy flag carrier = our team carrying
           their flag (offense) */
        ObjectGuid offGuid =
            wsg->GetFlagPickerGUID(
                pTeam == TEAM_ALLIANCE
                    ? TEAM_HORDE
                    : TEAM_ALLIANCE);
        if (!offGuid.IsEmpty())
        {
            Player* carrier =
                ObjectAccessor::FindPlayer(
                    offGuid);
            if (carrier)
            {
                json += ","
                    "\"friendly_flag_carrier\":\""
                    + JsonEscape(
                        carrier->GetName())
                    + "\"";
            }
        }
        /* Our flag carrier = enemy carrying our
           flag (defense) */
        ObjectGuid defGuid =
            wsg->GetFlagPickerGUID(pTeam);
        if (!defGuid.IsEmpty())
        {
            Player* eCarrier =
                ObjectAccessor::FindPlayer(
                    defGuid);
            if (eCarrier)
            {
                json += ","
                    "\"enemy_flag_carrier\":\""
                    + JsonEscape(
                        eCarrier->GetName())
                    + "\"";
            }
        }
    }

    json += "}";

    AppendRaidContext(player, json);
}

void QueueBGEvent(
    Player* player,
    const std::string& eventType,
    const std::string& extraJson)
{
    QueueChatterEvent(
        eventType,
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(eventType),
        "",
        player->GetGUID().GetCounter(),
        player->GetName(),
        0, "", 0,
        EscapeString(extraJson),
        GetReactionDelaySeconds(eventType),
        120,
        true);
}

static void QueueBGEventForAllPlayers(
    Battleground* bg,
    const std::string& eventType,
    const std::string& eventSpecificJson)
{
    for (auto const& [guid, bgPlayer] :
         bg->GetPlayers())
    {
        Player* player =
            ObjectAccessor::FindPlayer(guid);
        if (!player || IsPlayerBot(player))
            continue;

        Group* group = player->GetGroup();
        if (!group || !GroupHasBots(group))
            continue;

        std::string extra = eventSpecificJson;
        AppendBGContext(bg, player, extra);
        QueueBGEvent(player, eventType, extra);
    }
}

static bool TryQueueBGBigEvent(
    Battleground* bg,
    BGStateTracker& tracker,
    const std::string& eventType,
    const std::string& eventSpecificJson)
{
    if (tracker.IsBigEventOnCooldown())
        return false;

    QueueBGEventForAllPlayers(
        bg, eventType, eventSpecificJson);
    tracker.MarkBigEvent();
    return true;
}

static void DetectScoreEvents(
    Battleground* bg,
    BGStateTracker& tracker,
    uint32 scoreA, uint32 scoreH,
    ObjectGuid preScorerA = ObjectGuid::Empty,
    ObjectGuid preScorerH = ObjectGuid::Empty)
{
    uint32 bgType = bg->GetBgTypeID();

    if (bgType == BATTLEGROUND_WS)
    {
        if (scoreA > tracker.lastScoreAlliance)
        {
            tracker.lastCaptureHordeMs =
                tracker.totalElapsedMs;
            std::string capJson =
                "{\"flag_team\":"
                "\"Alliance\","
                "\"new_score\":"
                + std::to_string(scoreA);
            if (!preScorerA.IsEmpty())
            {
                Player* sp =
                    ObjectAccessor::
                        FindPlayer(
                            preScorerA);
                if (sp)
                {
                    capJson +=
                        ",\"scorer_name\":"
                        "\"" + JsonEscape(
                            sp->GetName())
                        + "\","
                        "\"scorer_is_real_"
                        "player\":"
                        + std::string(
                            IsPlayerBot(sp)
                            ? "false"
                            : "true");
                }
            }
            capJson += "}";
            QueueBGEventForAllPlayers(
                bg, "bg_flag_captured",
                capJson);
            tracker.MarkBigEvent();
        }
        if (scoreH > tracker.lastScoreHorde)
        {
            tracker.lastCaptureAllianceMs =
                tracker.totalElapsedMs;
            std::string capJson =
                "{\"flag_team\":"
                "\"Horde\","
                "\"new_score\":"
                + std::to_string(scoreH);
            if (!preScorerH.IsEmpty())
            {
                Player* sp =
                    ObjectAccessor::
                        FindPlayer(
                            preScorerH);
                if (sp)
                {
                    capJson +=
                        ",\"scorer_name\":"
                        "\"" + JsonEscape(
                            sp->GetName())
                        + "\","
                        "\"scorer_is_real_"
                        "player\":"
                        + std::string(
                            IsPlayerBot(sp)
                            ? "false"
                            : "true");
                }
            }
            capJson += "}";
            QueueBGEventForAllPlayers(
                bg, "bg_flag_captured",
                capJson);
            tracker.MarkBigEvent();
        }
        return;
    }

    if (bgType == BATTLEGROUND_AB
        || bgType == BATTLEGROUND_EY)
    {
        if (urand(1, 100)
            > sLLMChatterConfig
                ->_bgScoreMilestoneChance)
            return;

        static const uint32 MILESTONES[] = {
            500, 1000, 1500};
        for (uint32 ms : MILESTONES)
        {
            if (scoreA >= ms
                && tracker.lastScoreAlliance < ms)
            {
                TryQueueBGBigEvent(
                    bg, tracker,
                    "bg_score_milestone",
                    "{\"milestone_team\":"
                    "\"Alliance\","
                    "\"milestone_value\":"
                        + std::to_string(ms) + ","
                    "\"milestone_description\":"
                    "\"Alliance reached " +
                        std::to_string(ms) +
                        " resources\"}");
            }
            if (scoreH >= ms
                && tracker.lastScoreHorde < ms)
            {
                TryQueueBGBigEvent(
                    bg, tracker,
                    "bg_score_milestone",
                    "{\"milestone_team\":"
                    "\"Horde\","
                    "\"milestone_value\":"
                        + std::to_string(ms) + ","
                    "\"milestone_description\":"
                    "\"Horde reached " +
                        std::to_string(ms) +
                        " resources\"}");
            }
        }
    }
}

static void PollWSGState(
    Battleground* bg, BGStateTracker& tracker)
{
    BattlegroundWS* wsg =
        bg->ToBattlegroundWS();
    if (!wsg)
        return;

    uint8 aState = wsg->GetFlagState(
        TEAM_ALLIANCE);
    uint8 hState = wsg->GetFlagState(
        TEAM_HORDE);

    constexpr uint32 CAPTURE_SUPPRESS_MS = 10000;

    /* Flag events always fire — no RNG gate,
       no big-event cooldown.  These are the most
       important BG events and must never be
       silently dropped. */

    ObjectGuid allianceCarrier =
        wsg->GetFlagPickerGUID(TEAM_ALLIANCE);
    if (allianceCarrier !=
        tracker.lastFlagPickerAlliance)
    {
        if (!allianceCarrier.IsEmpty()
            && tracker.lastFlagPickerAlliance
                   .IsEmpty())
        {
            std::string pickJson =
                "{\"flag_team\":"
                "\"Alliance\","
                "\"carrier_guid\":"
                + std::to_string(
                    allianceCarrier
                        .GetCounter());
            Player* cp =
                ObjectAccessor::FindPlayer(
                    allianceCarrier);
            if (cp)
            {
                pickJson +=
                    ",\"carrier_name\":\""
                    + JsonEscape(
                        cp->GetName())
                    + "\","
                    "\"carrier_is_real_"
                    "player\":"
                    + std::string(
                        IsPlayerBot(cp)
                        ? "false"
                        : "true");
            }
            pickJson += "}";
            QueueBGEventForAllPlayers(
                bg, "bg_flag_picked_up",
                pickJson);
            tracker.MarkBigEvent();
        }
        else if (allianceCarrier.IsEmpty()
                 && !tracker
                         .lastFlagPickerAlliance
                         .IsEmpty()
                 && aState
                     == BG_WS_FLAG_STATE_ON_GROUND
                 && !tracker
                         .WasFlagRecentlyCaptured(
                             tracker
                                 .lastCaptureAllianceMs,
                             CAPTURE_SUPPRESS_MS))
        {
            std::string dropJson =
                "{\"flag_team\":"
                "\"Alliance\","
                "\"dropper_guid\":"
                + std::to_string(
                    tracker
                        .lastFlagPickerAlliance
                        .GetCounter());
            Player* dp =
                ObjectAccessor::FindPlayer(
                    tracker
                        .lastFlagPickerAlliance);
            if (dp)
            {
                dropJson +=
                    ",\"dropper_name\":\""
                    + JsonEscape(
                        dp->GetName())
                    + "\","
                    "\"dropper_is_real_"
                    "player\":"
                    + std::string(
                        IsPlayerBot(dp)
                        ? "false"
                        : "true");
            }
            dropJson += "}";
            QueueBGEventForAllPlayers(
                bg, "bg_flag_dropped",
                dropJson);
            tracker.MarkBigEvent();
        }
        tracker.lastFlagPickerAlliance =
            allianceCarrier;
    }

    ObjectGuid hordeCarrier =
        wsg->GetFlagPickerGUID(TEAM_HORDE);
    if (hordeCarrier !=
        tracker.lastFlagPickerHorde)
    {
        if (!hordeCarrier.IsEmpty()
            && tracker.lastFlagPickerHorde
                   .IsEmpty())
        {
            std::string pickJson =
                "{\"flag_team\":"
                "\"Horde\","
                "\"carrier_guid\":"
                + std::to_string(
                    hordeCarrier
                        .GetCounter());
            Player* cp =
                ObjectAccessor::FindPlayer(
                    hordeCarrier);
            if (cp)
            {
                pickJson +=
                    ",\"carrier_name\":\""
                    + JsonEscape(
                        cp->GetName())
                    + "\","
                    "\"carrier_is_real_"
                    "player\":"
                    + std::string(
                        IsPlayerBot(cp)
                        ? "false"
                        : "true");
            }
            pickJson += "}";
            QueueBGEventForAllPlayers(
                bg, "bg_flag_picked_up",
                pickJson);
            tracker.MarkBigEvent();
        }
        else if (hordeCarrier.IsEmpty()
                 && !tracker
                         .lastFlagPickerHorde
                         .IsEmpty()
                 && hState
                     == BG_WS_FLAG_STATE_ON_GROUND
                 && !tracker
                         .WasFlagRecentlyCaptured(
                             tracker
                                 .lastCaptureHordeMs,
                             CAPTURE_SUPPRESS_MS))
        {
            std::string dropJson =
                "{\"flag_team\":"
                "\"Horde\","
                "\"dropper_guid\":"
                + std::to_string(
                    tracker
                        .lastFlagPickerHorde
                        .GetCounter());
            Player* dp =
                ObjectAccessor::FindPlayer(
                    tracker
                        .lastFlagPickerHorde);
            if (dp)
            {
                dropJson +=
                    ",\"dropper_name\":\""
                    + JsonEscape(
                        dp->GetName())
                    + "\","
                    "\"dropper_is_real_"
                    "player\":"
                    + std::string(
                        IsPlayerBot(dp)
                        ? "false"
                        : "true");
            }
            dropJson += "}";
            QueueBGEventForAllPlayers(
                bg, "bg_flag_dropped",
                dropJson);
            tracker.MarkBigEvent();
        }
        tracker.lastFlagPickerHorde =
            hordeCarrier;
    }

    tracker.lastFlagStateAlliance = aState;
    tracker.lastFlagStateHorde = hState;
}

static void PollABState(
    Battleground* bg, BGStateTracker& tracker)
{
    BattlegroundAB* ab =
        bg->ToBattlegroundAB();
    if (!ab)
        return;

    static const char* AB_NODE_NAMES[] = {
        "Stables", "Blacksmith", "Farm",
        "Lumber Mill", "Gold Mine"
    };

    for (uint8 i = 0; i < 5; ++i)
    {
        auto const& info =
            ab->GetCapturePointInfo(i);
        uint8 curState = info._state;

        auto it =
            tracker.lastNodeState.find(i);
        uint8 prevState =
            (it != tracker.lastNodeState.end())
                ? it->second
                : BG_AB_NODE_STATE_NEUTRAL;

        if (curState != prevState)
        {
            if (urand(1, 100)
                <= sLLMChatterConfig
                    ->_bgNodeEventChance)
            {
                bool contested =
                    (curState
                         == BG_AB_NODE_STATE_ALLY_CONTESTED
                     || curState
                         == BG_AB_NODE_STATE_HORDE_CONTESTED);
                std::string eventType = contested
                    ? "bg_node_contested"
                    : "bg_node_captured";

                TeamId owner;
                if (curState == BG_AB_NODE_STATE_ALLY_CONTESTED
                    || curState == BG_AB_NODE_STATE_ALLY_OCCUPIED)
                    owner = TEAM_ALLIANCE;
                else if (curState == BG_AB_NODE_STATE_HORDE_CONTESTED
                    || curState == BG_AB_NODE_STATE_HORDE_OCCUPIED)
                    owner = TEAM_HORDE;
                else
                    owner = TEAM_NEUTRAL;

                std::string ownerStr =
                    (owner == TEAM_ALLIANCE)
                        ? "Alliance" : "Horde";

                std::string nodeJson =
                    "{\"node_name\":\"" +
                    std::string(
                        AB_NODE_NAMES[i]) +
                    "\","
                    "\"new_owner\":\"" +
                    ownerStr + "\"";
                float bestDist = 15.0f;
                Player* claimer = nullptr;
                for (auto const& [g, p] :
                     bg->GetPlayers())
                {
                    Player* pp =
                        ObjectAccessor::
                            FindPlayer(g);
                    if (!pp
                        || IsPlayerBot(pp))
                        continue;
                    float d =
                        pp->GetDistance2d(
                            BG_AB_NodePositions
                                [i][0],
                            BG_AB_NodePositions
                                [i][1]);
                    if (d < bestDist)
                    {
                        bestDist = d;
                        claimer = pp;
                    }
                }
                if (claimer)
                {
                    nodeJson +=
                        ",\"claimer_name\":\""
                        + JsonEscape(
                            claimer->GetName())
                        + "\","
                        "\"claimer_is_real_"
                        "player\":true";
                }
                nodeJson += "}";

                TryQueueBGBigEvent(
                    bg, tracker, eventType,
                    nodeJson);
            }

            tracker.lastNodeState[i] = curState;
        }
    }
}

static void PollEYState(
    Battleground* bg, BGStateTracker& tracker)
{
    BattlegroundEY* ey =
        bg->ToBattlegroundEY();
    if (!ey)
        return;

    static const char* EY_NODE_NAMES[] = {
        "Fel Reaver Ruins", "Blood Elf Tower",
        "Draenei Ruins", "Mage Tower"
    };

    for (uint8 i = 0; i < 4; ++i)
    {
        auto const& info =
            ey->GetCapturePointInfo(i);
        TeamId owner = info._ownerTeamId;

        auto it =
            tracker.lastNodeState.find(i);
        TeamId prevOwner =
            (it != tracker.lastNodeState.end())
                ? static_cast<TeamId>(it->second)
                : TEAM_NEUTRAL;

        if (owner != prevOwner)
        {
            tracker.lastNodeState[i] =
                static_cast<uint8>(owner);

            if (owner == TEAM_NEUTRAL)
                continue;

            if (urand(1, 100) >
                sLLMChatterConfig
                    ->_bgNodeEventChance)
                continue;

            std::string ownerStr =
                (owner == TEAM_ALLIANCE)
                    ? "Alliance" : "Horde";

            const char* eventType =
                (prevOwner != TEAM_NEUTRAL)
                    ? "bg_node_contested"
                    : "bg_node_captured";

            std::string nodeJson =
                "{\"node_name\":\"" +
                std::string(EY_NODE_NAMES[i]) +
                "\","
                "\"new_owner\":\"" +
                ownerStr + "\"";
            float bestDist = 15.0f;
            Player* claimer = nullptr;
            for (auto const& [g, p] :
                 bg->GetPlayers())
            {
                Player* pp =
                    ObjectAccessor::
                        FindPlayer(g);
                if (!pp
                    || IsPlayerBot(pp))
                    continue;
                float d =
                    pp->GetDistance2d(
                        BG_EY_TriggerPositions
                            [i][0],
                        BG_EY_TriggerPositions
                            [i][1]);
                if (d < bestDist)
                {
                    bestDist = d;
                    claimer = pp;
                }
            }
            if (claimer)
            {
                nodeJson +=
                    ",\"claimer_name\":\""
                    + JsonEscape(
                        claimer->GetName())
                    + "\","
                    "\"claimer_is_real_"
                    "player\":true";
            }
            nodeJson += "}";

            TryQueueBGBigEvent(
                bg, tracker, eventType,
                nodeJson);
        }
    }

    ObjectGuid flagPicker =
        ey->GetFlagPickerGUID();
    if (flagPicker !=
        tracker.lastFlagPickerAlliance)
    {
        if (!flagPicker.IsEmpty()
            && tracker.lastFlagPickerAlliance
                   .IsEmpty())
        {
            QueueBGEventForAllPlayers(
                bg, "bg_flag_picked_up",
                "{\"flag_team\":\"Neutral\","
                "\"carrier_guid\":"
                    + std::to_string(
                        flagPicker
                            .GetCounter()) +
                "}");
            tracker.MarkBigEvent();
        }
        else if (flagPicker.IsEmpty()
                 && !tracker
                         .lastFlagPickerAlliance
                         .IsEmpty())
        {
            QueueBGEventForAllPlayers(
                bg, "bg_flag_dropped",
                "{\"flag_team\":\"Neutral\"}");
            tracker.MarkBigEvent();
        }
        tracker.lastFlagPickerAlliance =
            flagPicker;
    }
}

class LLMChatterBGScript
    : public AllBattlegroundScript
{
public:
    LLMChatterBGScript()
        : AllBattlegroundScript(
              "LLMChatterBGScript",
              {ALLBATTLEGROUNDHOOK_ON_BATTLEGROUND_START,
               ALLBATTLEGROUNDHOOK_ON_BATTLEGROUND_END_REWARD,
               ALLBATTLEGROUNDHOOK_ON_BATTLEGROUND_UPDATE,
               ALLBATTLEGROUNDHOOK_ON_BATTLEGROUND_DESTROY,
               ALLBATTLEGROUNDHOOK_ON_BATTLEGROUND_ADD_PLAYER})
    {}

    void OnBattlegroundStart(
        Battleground* bg) override
    {
        if (!bg || !bg->isBattleground())
            return;
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_bgChatterEnable)
            return;

        if (urand(1, 100)
            > sLLMChatterConfig
                ->_bgMatchStartChance)
            return;

        QueueBGEventForAllPlayers(
            bg, "bg_match_start",
            "{\"event_detail\":"
            "\"Match starting\"}");

        uint32 instanceId =
            bg->GetInstanceID();
        auto& tracker =
            _bgTrackers[instanceId];
        tracker.MarkBigEvent();

    }

    void OnBattlegroundEndReward(
        Battleground* bg, Player* player,
        TeamId winnerTeamId) override
    {
        if (!bg || !bg->isBattleground())
            return;
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_bgChatterEnable)
            return;
        if (!player || IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group || !GroupHasBots(group))
            return;

        std::string extra =
            "{\"winner_team\":\"" +
                std::string(
                    winnerTeamId == TEAM_ALLIANCE
                        ? "Alliance" : "Horde") +
                "\","
            "\"won\":"
                + std::string(
                    player->GetBgTeamId()
                        == winnerTeamId
                        ? "true" : "false") +
                ","
            "\"final_score_alliance\":"
                + std::to_string(
                    bg->GetTeamScore(
                        TEAM_ALLIANCE)) + ","
            "\"final_score_horde\":"
                + std::to_string(
                    bg->GetTeamScore(
                        TEAM_HORDE));

        auto const* scores =
            bg->GetPlayerScores();
        if (scores)
        {
            auto it = scores->find(
                player->GetGUID()
                    .GetCounter());
            if (it != scores->end())
            {
                extra +=
                    ",\"player_killing_blows\":"
                    + std::to_string(
                        it->second
                            ->GetKillingBlows())
                    + ",\"player_damage_done\":"
                    + std::to_string(
                        it->second
                            ->GetDamageDone())
                    + ",\"player_healing_done\":"
                    + std::to_string(
                        it->second
                            ->GetHealingDone());
            }
        }

        extra += "}";
        AppendBGContext(bg, player, extra);
        QueueBGEvent(
            player, "bg_match_end", extra);

        uint32 instanceId =
            bg->GetInstanceID();
        auto& tracker =
            _bgTrackers[instanceId];
        tracker.MarkBigEvent();
    }

    void OnBattlegroundAddPlayer(
        Battleground* bg,
        Player* player) override
    {
        if (!bg || !bg->isBattleground())
            return;
        if (!player)
            return;
        if (IsPlayerBot(player))
            return;
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig
                   ->_bgChatterEnable)
            return;

        uint32 instanceId =
            bg->GetInstanceID();
        auto& tracker =
            _bgTrackers[instanceId];
        if (tracker.pendingArrivals.empty())
            tracker.firstArrivalMs =
                getMSTime();
        tracker.pendingArrivals.push_back(
            player->GetGUID());
    }

    void OnBattlegroundUpdate(
        Battleground* bg, uint32 diff) override
    {
        if (!bg || !bg->isBattleground())
            return;
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_bgChatterEnable)
            return;

        uint32 instanceId =
            bg->GetInstanceID();
        auto& tracker =
            _bgTrackers[instanceId];

        if (!tracker.pendingArrivals.empty()
            && getMSTimeDiff(
                   tracker.firstArrivalMs,
                   getMSTime()) >= 15000)
        {
            for (auto const& guid :
                 tracker.pendingArrivals)
            {
                Player* arrPlayer =
                    ObjectAccessor::FindPlayer(
                        guid);
                if (!arrPlayer)
                    continue;
                Group* arrGroup =
                    arrPlayer->GetGroup();
                if (!arrGroup
                    || !GroupHasBots(arrGroup))
                    continue;

                std::string extra = "{"
                    "\"player_name\":\"" +
                    JsonEscape(
                        arrPlayer->GetName()) +
                    "\"}";
                AppendBGContext(
                    bg, arrPlayer, extra);
                QueueBGEvent(
                    arrPlayer,
                    "bg_player_arrival",
                    extra);
            }
            tracker.pendingArrivals.clear();
        }

        if (bg->GetStatus()
            != STATUS_IN_PROGRESS)
            return;

        tracker.diffAccum += diff;
        tracker.totalElapsedMs += diff;

        uint32 pollInterval =
            sLLMChatterConfig
                ->_bgStatePollingIntervalMs;
        if (tracker.diffAccum < pollInterval)
            return;
        tracker.diffAccum = 0;

        uint32 scoreA =
            bg->GetTeamScore(TEAM_ALLIANCE);
        uint32 scoreH =
            bg->GetTeamScore(TEAM_HORDE);

        if (scoreA != tracker.lastScoreAlliance
            || scoreH
                != tracker.lastScoreHorde)
        {
            ObjectGuid preScorerA =
                tracker.lastFlagPickerHorde;
            ObjectGuid preScorerH =
                tracker.lastFlagPickerAlliance;
            DetectScoreEvents(
                bg, tracker, scoreA, scoreH,
                preScorerA, preScorerH);
            tracker.lastScoreAlliance = scoreA;
            tracker.lastScoreHorde = scoreH;
        }

        switch (bg->GetBgTypeID())
        {
            case BATTLEGROUND_WS:
                PollWSGState(bg, tracker);
                break;
            case BATTLEGROUND_AB:
                PollABState(bg, tracker);
                break;
            case BATTLEGROUND_EY:
                PollEYState(bg, tracker);
                break;
            default:
                break;
        }

        uint32 idleCooldownMs =
            sLLMChatterConfig
                ->_bgIdleChatterCooldownSec
            * 1000;
        if ((tracker.totalElapsedMs
             - tracker.lastIdleChatterMs)
            >= idleCooldownMs)
        {
            if (urand(1, 100)
                <= sLLMChatterConfig
                    ->_bgIdleChatterChance)
            {
                std::vector<Player*> candidates;
                for (auto const& [g, p] :
                     bg->GetPlayers())
                {
                    Player* pp =
                        ObjectAccessor::
                            FindPlayer(g);
                    if (!pp
                        || IsPlayerBot(pp))
                        continue;
                    Group* grp =
                        pp->GetGroup();
                    if (grp
                        && GroupHasBots(grp))
                        candidates.push_back(pp);
                }
                if (!candidates.empty())
                {
                    Player* chosen =
                        candidates[urand(
                            0,
                            candidates.size()
                                - 1)];
                    std::string extra =
                        "{\"player_name\":\""
                        + JsonEscape(
                            chosen->GetName())
                        + "\"}";
                    AppendBGContext(
                        bg, chosen, extra);
                    QueueBGEvent(
                        chosen,
                        "bg_idle_chatter",
                        extra);
                }
            }
            tracker.lastIdleChatterMs =
                tracker.totalElapsedMs;
        }
    }

    void OnBattlegroundDestroy(
        Battleground* bg) override
    {
        if (!bg)
            return;
        _bgTrackers.erase(
            bg->GetInstanceID());
    }
};

class LLMChatterFlagReturnScript
    : public AllGameObjectScript
{
public:
    LLMChatterFlagReturnScript()
        : AllGameObjectScript(
              "LLMChatterFlagReturnScript") { }

    bool CanGameObjectGossipHello(
        Player* player,
        GameObject* go) override
    {
        if (!player || !go)
            return false;

        uint32 entry = go->GetEntry();
        // Alliance dropped flag: 179785
        // Horde dropped flag: 179786
        if (entry != 179785 && entry != 179786)
            return false;

        if (!player->InBattleground())
            return false;

        Battleground* bg =
            player->GetBattleground();
        if (!bg
            || bg->GetBgTypeID(true)
                   != BATTLEGROUND_WS
            || bg->GetStatus()
                   != STATUS_IN_PROGRESS)
            return false;

        // Mirror core acceptance checks
        if (player->GetVehicle())
            return false;
        if (!player->CanUseBattlegroundObject(
                go))
            return false;
        if (!player->IsWithinDistInMap(
                go, 10.0f))
            return false;

        // Determine if return (same team) or
        // pickup (opposite team)
        // Use GetTeamId() to match core WSG logic
        // in BattlegroundWS::EventPlayerClickedOnFlag
        TeamId playerTeam =
            player->GetTeamId();
        bool isReturn = false;
        std::string flagTeam;

        if (entry == 179785
            && playerTeam == TEAM_ALLIANCE)
        {
            isReturn = true;
            flagTeam = "Alliance";
        }
        else if (entry == 179786
                 && playerTeam == TEAM_HORDE)
        {
            isReturn = true;
            flagTeam = "Horde";
        }

        if (!isReturn)
            return false;

        // Verify flag state is ON_GROUND
        BattlegroundWS* wsg =
            static_cast<BattlegroundWS*>(bg);
        TeamId flagOwner =
            (entry == 179785)
                ? TEAM_ALLIANCE : TEAM_HORDE;
        if (wsg->GetFlagState(flagOwner)
            != BG_WS_FLAG_STATE_ON_GROUND)
            return false;

        // Build JSON and queue event
        std::string retJson =
            "{\"flag_team\":\"" + flagTeam +
            "\","
            "\"returner_name\":\"" +
            JsonEscape(player->GetName()) +
            "\","
            "\"returner_is_real_player\":"
            + std::string(
                IsPlayerBot(player)
                ? "false" : "true") +
            "}";
        // QueueBGEventForAllPlayers already calls
        // AppendBGContext per recipient — no need
        // to call it here
        QueueBGEventForAllPlayers(
            bg, "bg_flag_returned", retJson);

        // Always return false so core continues
        return false;
    }
};

void AddLLMChatterBGScripts()
{
    new LLMChatterBGScript();
    new LLMChatterFlagReturnScript();
}
