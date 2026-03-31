#ifndef MOD_LLM_CHATTER_SHARED_H
#define MOD_LLM_CHATTER_SHARED_H

#include "Define.h"
#include "SharedDefines.h"
#include <ctime>
#include <map>
#include <string>

class Group;
class Player;
class Unit;

enum class LLMChatterPriorityBand : uint8
{
    Filler = 0,
    Normal = 10,
    High = 20,
    // Intra-tier ordering values such as 21 are kept in the
    // implementation file for narrow local ordering cases.
    Critical = 30
};

bool IsPlayerBot(Player* player);
std::string EscapeString(const std::string& str);
std::string JsonEscape(const std::string& str);
std::string GetClassName(uint8 classId);
std::string GetRaceName(uint8 raceId);
std::string BuildBotIdentityFields(
    Player* player, bool includeRoles = false);
std::string BuildBotStateJson(Player* player);
std::string ConvertAllLinks(const std::string& text);
std::string GetZoneName(uint32 zoneId);
uint32 GetTextEmoteId(const std::string& emoteName);
bool IsBGAllowedEmote(const std::string& emoteName);
void SendUnitTextEmote(Unit* unit, uint32 textEmoteId,
                       const std::string& targetName = "");
void SendBotTextEmote(Player* bot, uint32 textEmoteId);
void SendBotTextEmote(Player* bot, uint32 textEmoteId,
                      const std::string& targetName);

std::string GetTextEmoteName(uint32 emoteId);
void SendPartyMessageInstant(
    Player* bot, Group* group,
    const std::string& message,
    const std::string& emote);
void EnsureBotInGeneralChannel(Player* bot);
bool CanSpeakInGeneralChannel(Player* bot);
bool IsEventOnCooldown(
    std::map<std::string, time_t>& cooldownCache,
    const std::string& cooldownKey,
    uint32 cooldownSeconds);
void SetEventCooldown(
    std::map<std::string, time_t>& cooldownCache,
    const std::string& cooldownKey);
// NOTE: extraData must already be valid JSON text and SQL-safe for
// direct insertion into a single-quoted SQL string literal.
void QueueChatterEvent(
    const std::string& eventType,
    const std::string& eventScope,
    uint32 zoneId, uint32 mapId, uint8 priority,
    const std::string& cooldownKey,
    uint32 subjectGuid, const std::string& subjectName,
    uint32 targetGuid, const std::string& targetName,
    uint32 targetEntry, const std::string& extraData,
    uint32 reactAfterSeconds,
    uint32 expiresAfterSeconds,
    bool nullZeroNumeric);
void AppendRaidContext(Player* player, std::string& json);
bool GroupHasBots(Group* group);
Player* FindMentionedMember(
    Player* bot, Group* grp,
    const std::string& message);
Player* FindNearbyDefenderBot(
    Player* intruder, uint32 zoneId,
    TeamId defenderTeam);
uint8 GetChatterEventPriority(
    const std::string& eventType);
uint32 GetReactionDelaySeconds(const std::string& eventType);
void AddLLMChatterPlayerScripts();
void AddLLMChatterWorldScripts();

#endif
