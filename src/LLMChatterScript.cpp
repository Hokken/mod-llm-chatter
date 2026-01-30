/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Main WorldScript for triggering chatter and delivering messages
 */

#include "LLMChatterConfig.h"
#include "ScriptMgr.h"
#include "Player.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Log.h"
#include "Channel.h"
#include "ChannelMgr.h"
#include "ObjectAccessor.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include <vector>
#include <map>
#include <random>
#include <sstream>

// Helper function to get item quality color
static const char* GetQualityColor(uint8 quality)
{
    switch (quality)
    {
        case 0: return "9d9d9d";  // Poor (gray)
        case 1: return "ffffff";  // Common (white)
        case 2: return "1eff00";  // Uncommon (green)
        case 3: return "0070dd";  // Rare (blue)
        case 4: return "a335ee";  // Epic (purple)
        case 5: return "ff8000";  // Legendary (orange)
        default: return "ffffff";
    }
}

// Convert [[item:ID:Name:Quality]] markers to WoW item links
static std::string ConvertItemLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[item:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos) break;

        std::string content = result.substr(pos + 7, endPos - pos - 7);
        size_t firstColon = content.find(':');
        size_t lastColon = content.rfind(':');

        if (firstColon != std::string::npos && lastColon != std::string::npos && firstColon != lastColon)
        {
            std::string idStr = content.substr(0, firstColon);
            std::string name = content.substr(firstColon + 1, lastColon - firstColon - 1);
            std::string qualityStr = content.substr(lastColon + 1);

            try
            {
                uint32 itemId = std::stoul(idStr);
                uint8 quality = static_cast<uint8>(std::stoul(qualityStr));
                std::ostringstream link;
                link << "|cff" << GetQualityColor(quality)
                     << "|Hitem:" << itemId << ":0:0:0:0:0:0:0:0|h[" << name << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...) { pos = endPos + 2; }
        }
        else { pos = endPos + 2; }
    }
    return result;
}

// Convert [[quest:ID:Name:Level]] markers to WoW quest links
static std::string ConvertQuestLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[quest:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos) break;

        std::string content = result.substr(pos + 8, endPos - pos - 8);
        size_t firstColon = content.find(':');
        size_t lastColon = content.rfind(':');

        if (firstColon != std::string::npos && lastColon != std::string::npos && firstColon != lastColon)
        {
            std::string idStr = content.substr(0, firstColon);
            std::string name = content.substr(firstColon + 1, lastColon - firstColon - 1);
            std::string levelStr = content.substr(lastColon + 1);

            try
            {
                uint32 questId = std::stoul(idStr);
                uint32 level = std::stoul(levelStr);
                std::ostringstream link;
                link << "|cffffff00|Hquest:" << questId << ":" << level << "|h[" << name << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...) { pos = endPos + 2; }
        }
        else { pos = endPos + 2; }
    }
    return result;
}

// Convert [[npc:ID:Name]] markers to green colored NPC names
static std::string ConvertNpcLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[npc:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos) break;

        std::string content = result.substr(pos + 6, endPos - pos - 6);
        size_t colonPos = content.find(':');

        if (colonPos != std::string::npos)
        {
            std::string name = content.substr(colonPos + 1);
            std::string coloredName = "|cff00ff00" + name + "|r";
            result.replace(pos, endPos - pos + 2, coloredName);
            pos += coloredName.length();
        }
        else { pos = endPos + 2; }
    }
    return result;
}

// Convert all link markers to WoW hyperlinks
static std::string ConvertAllLinks(const std::string& text)
{
    std::string result = text;
    result = ConvertItemLinks(result);
    result = ConvertQuestLinks(result);
    result = ConvertNpcLinks(result);
    return result;
}

class LLMChatterWorldScript : public WorldScript
{
public:
    LLMChatterWorldScript() : WorldScript("LLMChatterWorldScript") {}

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sLLMChatterConfig->LoadConfig();
    }

    void OnStartup() override
    {
        if (!sLLMChatterConfig->IsEnabled())
            return;

        // Clear any stale undelivered messages from previous session
        CharacterDatabase.Execute(
            "DELETE FROM llm_chatter_messages WHERE delivered = 0");
        CharacterDatabase.Execute(
            "UPDATE llm_chatter_queue SET status = 'cancelled' "
            "WHERE status IN ('pending', 'processing')");

        LOG_INFO("module", "LLMChatter: Cleared stale messages, WorldScript initialized");
        _lastTriggerTime = 0;
        _lastDeliveryTime = 0;
    }

    void OnUpdate(uint32 /*diff*/) override
    {
        if (!sLLMChatterConfig->IsEnabled())
            return;

        uint32 now = getMSTime();

        // Check for message delivery (simple polling - always check)
        if (now - _lastDeliveryTime >= sLLMChatterConfig->_deliveryPollMs)
        {
            _lastDeliveryTime = now;
            DeliverPendingMessages();
        }

        // Check for new chatter trigger
        if (now - _lastTriggerTime >= sLLMChatterConfig->_triggerIntervalSeconds * 1000)
        {
            _lastTriggerTime = now;
            TryTriggerChatter();
        }
    }

private:
    uint32 _lastTriggerTime = 0;
    uint32 _lastDeliveryTime = 0;

    // Get class name from class ID
    std::string GetClassName(uint8 classId)
    {
        switch (classId)
        {
            case CLASS_WARRIOR:      return "Warrior";
            case CLASS_PALADIN:      return "Paladin";
            case CLASS_HUNTER:       return "Hunter";
            case CLASS_ROGUE:        return "Rogue";
            case CLASS_PRIEST:       return "Priest";
            case CLASS_DEATH_KNIGHT: return "Death Knight";
            case CLASS_SHAMAN:       return "Shaman";
            case CLASS_MAGE:         return "Mage";
            case CLASS_WARLOCK:      return "Warlock";
            case CLASS_DRUID:        return "Druid";
            default:                 return "Unknown";
        }
    }

    // Get race name from race ID
    std::string GetRaceName(uint8 raceId)
    {
        switch (raceId)
        {
            case RACE_HUMAN:         return "Human";
            case RACE_ORC:           return "Orc";
            case RACE_DWARF:         return "Dwarf";
            case RACE_NIGHTELF:      return "Night Elf";
            case RACE_UNDEAD_PLAYER: return "Undead";
            case RACE_TAUREN:        return "Tauren";
            case RACE_GNOME:         return "Gnome";
            case RACE_TROLL:         return "Troll";
            case RACE_BLOODELF:      return "Blood Elf";
            case RACE_DRAENEI:       return "Draenei";
            default:                 return "Unknown";
        }
    }

    // Get zone name from zone ID
    std::string GetZoneName(uint32 zoneId)
    {
        if (AreaTableEntry const* area = sAreaTableStore.LookupEntry(zoneId))
        {
            return area->area_name[0];  // English name
        }
        return "Unknown Zone";
    }

    // Check if player is a bot
    bool IsPlayerBot(Player* player)
    {
        if (!player)
            return false;

        PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
        return ai != nullptr;
    }

    // Get faction (0 = Alliance, 1 = Horde)
    uint32 GetFaction(Player* player)
    {
        return player->GetTeamId();  // TEAM_ALLIANCE = 0, TEAM_HORDE = 1
    }

    // Check if player is in the overworld (not an instance)
    bool IsInOverworld(Player* player)
    {
        if (!player || !player->GetMap())
            return false;

        // Only allow chatter in common world maps (not dungeons, raids, BGs, arenas)
        return !player->GetMap()->Instanceable();
    }

    // Find zones that have real (non-bot) players in the overworld
    std::vector<uint32> GetZonesWithRealPlayers()
    {
        std::map<uint32, bool> zoneMap;

        WorldSessionMgr::SessionMap const& sessions = sWorldSessionMgr->GetAllSessions();
        for (auto const& pair : sessions)
        {
            if (WorldSession* session = pair.second)
            {
                if (Player* player = session->GetPlayer())
                {
                    // Only count real players (not bots) in the overworld
                    if (!IsPlayerBot(player) && player->IsInWorld() && IsInOverworld(player))
                    {
                        uint32 zoneId = player->GetZoneId();
                        if (zoneId > 0)
                        {
                            zoneMap[zoneId] = true;
                        }
                    }
                }
            }
        }

        std::vector<uint32> zones;
        for (auto const& pair : zoneMap)
        {
            zones.push_back(pair.first);
        }

        return zones;
    }

    // Check if a bot is grouped with a real player
    bool IsGroupedWithRealPlayer(Player* bot)
    {
        if (!bot)
            return false;

        Group* group = bot->GetGroup();
        if (!group)
            return false;  // Not in a group, so not grouped with real player

        // Check all group members for real players
        for (GroupReference* itr = group->GetFirstMember(); itr != nullptr; itr = itr->next())
        {
            if (Player* member = itr->GetSource())
            {
                if (member != bot && !IsPlayerBot(member))
                {
                    return true;  // Found a real player in the group
                }
            }
        }

        return false;  // Only bots in the group
    }

    // Get bots in a specific zone, filtered by faction
    // Excludes bots that are grouped with real players
    std::vector<Player*> GetBotsInZone(uint32 zoneId, uint32 faction)
    {
        std::vector<Player*> bots;
        uint32 totalBots = 0;
        uint32 inZone = 0;
        uint32 rightFaction = 0;

        // Get all playerbots from RandomPlayerbotMgr
        PlayerBotMap allBots = sRandomPlayerbotMgr->GetAllBots();
        totalBots = allBots.size();

        for (auto const& pair : allBots)
        {
            Player* player = pair.second;
            if (player && player->IsInWorld() && player->IsAlive())
            {
                if (player->GetZoneId() == zoneId)
                {
                    inZone++;
                    if (GetFaction(player) == faction)
                    {
                        // Only include bots NOT grouped with real players
                        if (!IsGroupedWithRealPlayer(player))
                        {
                            rightFaction++;
                            bots.push_back(player);
                        }
                    }
                }
            }
        }

        LOG_INFO("module", "LLMChatter: GetBotsInZone - total bots: {}, in zone {}: {}, eligible: {}",
                 totalBots, zoneId, inZone, rightFaction);

        return bots;
    }

    // Get the dominant faction of real players in a zone
    uint32 GetDominantFactionInZone(uint32 zoneId)
    {
        uint32 allianceCount = 0;
        uint32 hordeCount = 0;

        WorldSessionMgr::SessionMap const& sessions = sWorldSessionMgr->GetAllSessions();
        for (auto const& pair : sessions)
        {
            if (WorldSession* session = pair.second)
            {
                if (Player* player = session->GetPlayer())
                {
                    if (!IsPlayerBot(player) &&
                        player->IsInWorld() &&
                        player->GetZoneId() == zoneId)
                    {
                        if (GetFaction(player) == TEAM_ALLIANCE)
                            allianceCount++;
                        else
                            hordeCount++;
                    }
                }
            }
        }

        // Return the faction with more players, or random if equal
        if (allianceCount > hordeCount)
            return TEAM_ALLIANCE;
        else if (hordeCount > allianceCount)
            return TEAM_HORDE;
        else
            return urand(0, 1);  // Random if equal
    }

    void TryTriggerChatter()
    {
        LOG_INFO("module", "LLMChatter: TryTriggerChatter called");

        // Roll for trigger chance
        if (urand(1, 100) > sLLMChatterConfig->_triggerChance)
            return;

        // Check pending requests
        QueryResult countResult = CharacterDatabase.Query(
            "SELECT COUNT(*) FROM llm_chatter_queue WHERE status IN ('pending', 'processing')");

        if (countResult)
        {
            uint32 pending = countResult->Fetch()[0].Get<uint32>();
            if (pending >= sLLMChatterConfig->_maxPendingRequests)
            {
                LOG_DEBUG("module", "LLMChatter: Max pending requests reached ({})", pending);
                return;
            }
        }

        // Find zones with real players
        std::vector<uint32> validZones = GetZonesWithRealPlayers();
        LOG_INFO("module", "LLMChatter: Found {} zones with real players", validZones.size());
        if (validZones.empty())
        {
            return;
        }

        // Pick one zone randomly
        std::random_device rd;
        std::mt19937 g(rd());
        std::shuffle(validZones.begin(), validZones.end(), g);
        uint32 selectedZone = validZones[0];
        std::string zoneName = GetZoneName(selectedZone);

        // Get the dominant faction in this zone
        uint32 faction = GetDominantFactionInZone(selectedZone);
        LOG_INFO("module", "LLMChatter: Selected zone {} ({}), dominant faction: {}",
                 selectedZone, zoneName, faction == TEAM_ALLIANCE ? "Alliance" : "Horde");

        // Get bots in this zone with matching faction
        std::vector<Player*> bots = GetBotsInZone(selectedZone, faction);
        LOG_INFO("module", "LLMChatter: Found {} bots in zone {} with faction {}",
                 bots.size(), zoneName, faction == TEAM_ALLIANCE ? "Alliance" : "Horde");

        // Decide: statement or conversation
        bool isConversation = (urand(1, 100) <= sLLMChatterConfig->_conversationChance);

        // Check if we have enough bots
        uint32 requiredBots = isConversation ? 2 : 1;
        if (bots.size() < requiredBots)
        {
            // Try single statement if not enough for conversation
            if (isConversation && bots.size() >= 1)
            {
                isConversation = false;
                LOG_DEBUG("module", "LLMChatter: Not enough bots for conversation in {}, falling back to statement",
                          zoneName);
            }
            else
            {
                LOG_DEBUG("module", "LLMChatter: No bots in {} (faction {})", zoneName, faction);
                return;
            }
        }

        // Shuffle bots and pick
        std::shuffle(bots.begin(), bots.end(), g);

        Player* bot1 = bots[0];
        Player* bot2 = isConversation ? bots[1] : nullptr;

        // Queue the request
        QueueChatterRequest(bot1, bot2, isConversation, zoneName, selectedZone);
    }

    void QueueChatterRequest(Player* bot1, Player* bot2, bool isConversation, const std::string& zoneName, uint32 zoneId)
    {
        std::string requestType = isConversation ? "conversation" : "statement";
        std::string bot1Name = bot1->GetName();
        std::string bot1Class = GetClassName(bot1->getClass());
        std::string bot1Race = GetRaceName(bot1->getRace());
        uint8 bot1Level = bot1->GetLevel();

        // Escape zone name for SQL (handle apostrophes)
        std::string escapedZoneName = zoneName;
        size_t pos = 0;
        while ((pos = escapedZoneName.find('\'', pos)) != std::string::npos)
        {
            escapedZoneName.replace(pos, 1, "''");
            pos += 2;
        }

        if (isConversation && bot2)
        {
            std::string bot2Name = bot2->GetName();
            std::string bot2Class = GetClassName(bot2->getClass());
            std::string bot2Race = GetRaceName(bot2->getRace());
            uint8 bot2Level = bot2->GetLevel();

            CharacterDatabase.Execute(
                "INSERT INTO llm_chatter_queue "
                "(request_type, bot1_guid, bot1_name, bot1_class, bot1_race, bot1_level, bot1_zone, zone_id, "
                "bot2_guid, bot2_name, bot2_class, bot2_race, bot2_level, status) "
                "VALUES ('{}', {}, '{}', '{}', '{}', {}, '{}', {}, {}, '{}', '{}', '{}', {}, 'pending')",
                requestType,
                bot1->GetGUID().GetCounter(), bot1Name, bot1Class, bot1Race, bot1Level, escapedZoneName, zoneId,
                bot2->GetGUID().GetCounter(), bot2Name, bot2Class, bot2Race, bot2Level);

            LOG_INFO("module", "LLMChatter: Queued conversation in {} between {} ({} {}) and {} ({} {})",
                     zoneName, bot1Name, bot1Race, bot1Class, bot2Name, bot2Race, bot2Class);
        }
        else
        {
            CharacterDatabase.Execute(
                "INSERT INTO llm_chatter_queue "
                "(request_type, bot1_guid, bot1_name, bot1_class, bot1_race, bot1_level, bot1_zone, zone_id, status) "
                "VALUES ('{}', {}, '{}', '{}', '{}', {}, '{}', {}, 'pending')",
                requestType,
                bot1->GetGUID().GetCounter(), bot1Name, bot1Class, bot1Race, bot1Level, escapedZoneName, zoneId);

            LOG_INFO("module", "LLMChatter: Queued statement in {} for {} ({} {})",
                     zoneName, bot1Name, bot1Race, bot1Class);
        }
    }

    void DeliverPendingMessages()
    {
        // Find messages ready for delivery
        QueryResult result = CharacterDatabase.Query(
            "SELECT id, bot_guid, bot_name, message, channel "
            "FROM llm_chatter_messages "
            "WHERE delivered = 0 AND deliver_at <= NOW() "
            "ORDER BY deliver_at ASC LIMIT 1");

        if (!result)
            return;

        do
        {
            Field* fields = result->Fetch();
            uint32 messageId = fields[0].Get<uint32>();
            uint32 botGuid = fields[1].Get<uint32>();
            std::string botName = fields[2].Get<std::string>();
            std::string message = fields[3].Get<std::string>();
            std::string channel = fields[4].Get<std::string>();

            // Mark as delivered FIRST to prevent duplicate delivery
            CharacterDatabase.DirectExecute(
                "UPDATE llm_chatter_messages SET delivered = 1, delivered_at = NOW() WHERE id = {}",
                messageId);

            // Find the bot player from RandomPlayerbotMgr
            Player* bot = nullptr;
            PlayerBotMap allBots = sRandomPlayerbotMgr->GetAllBots();
            for (auto const& pair : allBots)
            {
                if (Player* player = pair.second)
                {
                    if (player->GetGUID().GetCounter() == botGuid)
                    {
                        bot = player;
                        break;
                    }
                }
            }

            if (bot && bot->IsInWorld())
            {
                // Send to channel using PlayerbotAI
                if (PlayerbotAI* ai = GET_PLAYERBOT_AI(bot))
                {
                    // Convert any link markers to WoW hyperlinks
                    std::string processedMessage = ConvertAllLinks(message);
                    ai->SayToChannel(processedMessage, ChatChannelId::GENERAL);
                    LOG_INFO("module", "LLMChatter: [General] {}: {}", botName, processedMessage);
                }
            }
            else
            {
                LOG_DEBUG("module", "LLMChatter: Bot {} not found or offline, skipping message", botName);
            }

        } while (result->NextRow());
    }
};

// Register the script
void AddLLMChatterScripts()
{
    new LLMChatterWorldScript();
}
