/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Main WorldScript for triggering chatter and delivering messages
 *
 * Active features:
 * - Day/Night transition events (WorldScript)
 * - Holiday start/stop events (GameEventScript)
 * - Weather change events (ALEScript) - tracks starting, clearing, intensifying
 * - Ambient bot conversations in zones with real players
 *
 * Future/Planned features:
 * - Transport arrival events
 *   Note: TransportScript is database-bound to specific transports via ScriptName.
 *   Would need to either:
 *   a) Add ScriptNames to transports table and register matching TransportScripts
 *   b) Add a custom periodic check that iterates Map::GetAllTransports()
 *   Both approaches require significant work and database/core understanding.
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
#include "GameEventMgr.h"
#include "GameTime.h"
#include "Group.h"
#include "Weather.h"
#include "MapMgr.h"
#include "Transport.h"
#include "Spell.h"
#include "Chat.h"
#include <algorithm>
#include <vector>
#include <map>
#include <set>
#include <random>
#include <sstream>
#include <unordered_map>
#include <regex>
#include <cstdio>
#include <mutex>

// Check if player is a bot (global helper function)
static bool IsPlayerBot(Player* player)
{
    if (!player)
        return false;

    PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
    return ai != nullptr;
}

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

// Convert [[spell:ID:Name]] markers to WoW spell links
static std::string ConvertSpellLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[spell:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos) break;

        std::string content = result.substr(pos + 8, endPos - pos - 8);
        size_t colonPos = content.find(':');

        if (colonPos != std::string::npos)
        {
            std::string idStr = content.substr(0, colonPos);
            std::string name = content.substr(colonPos + 1);

            try
            {
                uint32 spellId = std::stoul(idStr);
                std::ostringstream link;
                link << "|cff71d5ff|Hspell:" << spellId << "|h[" << name << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...) { pos = endPos + 2; }
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
    result = ConvertSpellLinks(result);
    result = ConvertNpcLinks(result);
    return result;
}

// Map emote name string to TEXT_EMOTE_* enum value
static uint32 GetTextEmoteId(
    const std::string& emoteName)
{
    static const std::unordered_map<
        std::string, uint32> emoteMap = {
        {"agree", TEXT_EMOTE_AGREE},
        {"amaze", TEXT_EMOTE_AMAZE},
        {"angry", TEXT_EMOTE_ANGRY},
        {"apologize", TEXT_EMOTE_APOLOGIZE},
        {"applaud", TEXT_EMOTE_APPLAUD},
        {"bashful", TEXT_EMOTE_BASHFUL},
        {"beckon", TEXT_EMOTE_BECKON},
        {"beg", TEXT_EMOTE_BEG},
        {"bite", TEXT_EMOTE_BITE},
        {"bleed", TEXT_EMOTE_BLEED},
        {"blink", TEXT_EMOTE_BLINK},
        {"blush", TEXT_EMOTE_BLUSH},
        {"bonk", TEXT_EMOTE_BONK},
        {"bored", TEXT_EMOTE_BORED},
        {"bounce", TEXT_EMOTE_BOUNCE},
        {"brb", TEXT_EMOTE_BRB},
        {"bow", TEXT_EMOTE_BOW},
        {"burp", TEXT_EMOTE_BURP},
        {"bye", TEXT_EMOTE_BYE},
        {"cackle", TEXT_EMOTE_CACKLE},
        {"cheer", TEXT_EMOTE_CHEER},
        {"chicken", TEXT_EMOTE_CHICKEN},
        {"chuckle", TEXT_EMOTE_CHUCKLE},
        {"clap", TEXT_EMOTE_CLAP},
        {"confused", TEXT_EMOTE_CONFUSED},
        {"congratulate", TEXT_EMOTE_CONGRATULATE},
        {"cough", TEXT_EMOTE_COUGH},
        {"cower", TEXT_EMOTE_COWER},
        {"crack", TEXT_EMOTE_CRACK},
        {"cringe", TEXT_EMOTE_CRINGE},
        {"cry", TEXT_EMOTE_CRY},
        {"curious", TEXT_EMOTE_CURIOUS},
        {"curtsey", TEXT_EMOTE_CURTSEY},
        {"dance", TEXT_EMOTE_DANCE},
        {"drink", TEXT_EMOTE_DRINK},
        {"drool", TEXT_EMOTE_DROOL},
        {"eat", TEXT_EMOTE_EAT},
        {"eye", TEXT_EMOTE_EYE},
        {"fart", TEXT_EMOTE_FART},
        {"fidget", TEXT_EMOTE_FIDGET},
        {"flex", TEXT_EMOTE_FLEX},
        {"frown", TEXT_EMOTE_FROWN},
        {"gasp", TEXT_EMOTE_GASP},
        {"gaze", TEXT_EMOTE_GAZE},
        {"giggle", TEXT_EMOTE_GIGGLE},
        {"glare", TEXT_EMOTE_GLARE},
        {"gloat", TEXT_EMOTE_GLOAT},
        {"greet", TEXT_EMOTE_GREET},
        {"grin", TEXT_EMOTE_GRIN},
        {"groan", TEXT_EMOTE_GROAN},
        {"grovel", TEXT_EMOTE_GROVEL},
        {"guffaw", TEXT_EMOTE_GUFFAW},
        {"hail", TEXT_EMOTE_HAIL},
        {"happy", TEXT_EMOTE_HAPPY},
        {"hello", TEXT_EMOTE_HELLO},
        {"hug", TEXT_EMOTE_HUG},
        {"hungry", TEXT_EMOTE_HUNGRY},
        {"kiss", TEXT_EMOTE_KISS},
        {"kneel", TEXT_EMOTE_KNEEL},
        {"laugh", TEXT_EMOTE_LAUGH},
        {"laydown", TEXT_EMOTE_LAYDOWN},
        {"moan", TEXT_EMOTE_MOAN},
        {"moon", TEXT_EMOTE_MOON},
        {"mourn", TEXT_EMOTE_MOURN},
        {"no", TEXT_EMOTE_NO},
        {"nod", TEXT_EMOTE_NOD},
        {"nosepick", TEXT_EMOTE_NOSEPICK},
        {"panic", TEXT_EMOTE_PANIC},
        {"peer", TEXT_EMOTE_PEER},
        {"plead", TEXT_EMOTE_PLEAD},
        {"point", TEXT_EMOTE_POINT},
        {"poke", TEXT_EMOTE_POKE},
        {"pray", TEXT_EMOTE_PRAY},
        {"roar", TEXT_EMOTE_ROAR},
        {"rofl", TEXT_EMOTE_ROFL},
        {"rude", TEXT_EMOTE_RUDE},
        {"salute", TEXT_EMOTE_SALUTE},
        {"scratch", TEXT_EMOTE_SCRATCH},
        {"sexy", TEXT_EMOTE_SEXY},
        {"shake", TEXT_EMOTE_SHAKE},
        {"shout", TEXT_EMOTE_SHOUT},
        {"shrug", TEXT_EMOTE_SHRUG},
        {"shy", TEXT_EMOTE_SHY},
        {"sigh", TEXT_EMOTE_SIGH},
        {"snarl", TEXT_EMOTE_SNARL},
        {"spit", TEXT_EMOTE_SPIT},
        {"stare", TEXT_EMOTE_STARE},
        {"surprised", TEXT_EMOTE_SURPRISED},
        {"surrender", TEXT_EMOTE_SURRENDER},
        {"talk", TEXT_EMOTE_TALK},
        {"tap", TEXT_EMOTE_TAP},
        {"thank", TEXT_EMOTE_THANK},
        {"threaten", TEXT_EMOTE_THREATEN},
        {"tired", TEXT_EMOTE_TIRED},
        {"victory", TEXT_EMOTE_VICTORY},
        {"wave", TEXT_EMOTE_WAVE},
        {"welcome", TEXT_EMOTE_WELCOME},
        {"whine", TEXT_EMOTE_WHINE},
        {"whistle", TEXT_EMOTE_WHISTLE},
        {"work", TEXT_EMOTE_WORK},
        {"yawn", TEXT_EMOTE_YAWN},
        {"boggle", TEXT_EMOTE_BOGGLE},
        {"calm", TEXT_EMOTE_CALM},
        {"cold", TEXT_EMOTE_COLD},
        {"comfort", TEXT_EMOTE_COMFORT},
        {"cuddle", TEXT_EMOTE_CUDDLE},
        {"duck", TEXT_EMOTE_DUCK},
        {"insult", TEXT_EMOTE_INSULT},
        {"introduce", TEXT_EMOTE_INTRODUCE},
        {"jk", TEXT_EMOTE_JK},
        {"lick", TEXT_EMOTE_LICK},
        {"listen", TEXT_EMOTE_LISTEN},
        {"lost", TEXT_EMOTE_LOST},
        {"mock", TEXT_EMOTE_MOCK},
        {"ponder", TEXT_EMOTE_PONDER},
        {"pounce", TEXT_EMOTE_POUNCE},
        {"praise", TEXT_EMOTE_PRAISE},
        {"purr", TEXT_EMOTE_PURR},
        {"puzzle", TEXT_EMOTE_PUZZLE},
        {"raise", TEXT_EMOTE_RAISE},
        {"ready", TEXT_EMOTE_READY},
        {"shimmy", TEXT_EMOTE_SHIMMY},
        {"shiver", TEXT_EMOTE_SHIVER},
        {"shoo", TEXT_EMOTE_SHOO},
        {"slap", TEXT_EMOTE_SLAP},
        {"smirk", TEXT_EMOTE_SMIRK},
        {"sniff", TEXT_EMOTE_SNIFF},
        {"snub", TEXT_EMOTE_SNUB},
        {"soothe", TEXT_EMOTE_SOOTHE},
        {"stink", TEXT_EMOTE_STINK},
        {"taunt", TEXT_EMOTE_TAUNT},
        {"tease", TEXT_EMOTE_TEASE},
        {"thirsty", TEXT_EMOTE_THIRSTY},
        {"veto", TEXT_EMOTE_VETO},
        {"snicker", TEXT_EMOTE_SNICKER},
        {"stand", TEXT_EMOTE_STAND},
        {"tickle", TEXT_EMOTE_TICKLE},
        {"violin", TEXT_EMOTE_VIOLIN},
        {"smile", TEXT_EMOTE_SMILE},
        {"rasp", TEXT_EMOTE_RASP},
        {"pity", TEXT_EMOTE_PITY},
        {"growl", TEXT_EMOTE_GROWL},
        {"bark", TEXT_EMOTE_BARK},
        {"scared", TEXT_EMOTE_SCARED},
        {"flop", TEXT_EMOTE_FLOP},
        {"love", TEXT_EMOTE_LOVE},
        {"moo", TEXT_EMOTE_MOO},
        {"commend", TEXT_EMOTE_COMMEND},
        {"train", TEXT_EMOTE_TRAIN},
        {"helpme", TEXT_EMOTE_HELPME},
        {"incoming", TEXT_EMOTE_INCOMING},
        {"charge", TEXT_EMOTE_CHARGE},
        {"flee", TEXT_EMOTE_FLEE},
        {"attacktarget", TEXT_EMOTE_ATTACKMYTARGET},
        {"oom", TEXT_EMOTE_OOM},
        {"follow", TEXT_EMOTE_FOLLOW},
        {"wait", TEXT_EMOTE_WAIT},
        {"healme", TEXT_EMOTE_HEALME},
        {"openfire", TEXT_EMOTE_OPENFIRE},
        {"flirt", TEXT_EMOTE_FLIRT},
        {"joke", TEXT_EMOTE_JOKE},
        {"golfclap", TEXT_EMOTE_GOLFCLAP},
        {"wink", TEXT_EMOTE_WINK},
        {"pat", TEXT_EMOTE_PAT},
        {"serious", TEXT_EMOTE_SERIOUS},
        {"goodluck", TEXT_EMOTE_GOODLUCK},
        {"blame", TEXT_EMOTE_BLAME},
        {"blank", TEXT_EMOTE_BLANK},
        {"brandish", TEXT_EMOTE_BRANDISH},
        {"breath", TEXT_EMOTE_BREATH},
        {"disagree", TEXT_EMOTE_DISAGREE},
        {"doubt", TEXT_EMOTE_DOUBT},
        {"embarrass", TEXT_EMOTE_EMBARRASS},
        {"encourage", TEXT_EMOTE_ENCOURAGE},
        {"enemy", TEXT_EMOTE_ENEMY},
        {"eyebrow", TEXT_EMOTE_EYEBROW},
        {"toast", TEXT_EMOTE_TOAST},
        {"fail", TEXT_EMOTE_FAIL},
        {"highfive", TEXT_EMOTE_HIGHFIVE},
        {"absent", TEXT_EMOTE_ABSENT},
        {"arm", TEXT_EMOTE_ARM},
        {"awe", TEXT_EMOTE_AWE},
        {"backpack", TEXT_EMOTE_BACKPACK},
        {"badfeeling", TEXT_EMOTE_BADFEELING},
        {"challenge", TEXT_EMOTE_CHALLENGE},
        {"chug", TEXT_EMOTE_CHUG},
        {"ding", TEXT_EMOTE_DING},
        {"facepalm", TEXT_EMOTE_FACEPALM},
        {"faint", TEXT_EMOTE_FAINT},
        {"go", TEXT_EMOTE_GO},
        {"going", TEXT_EMOTE_GOING},
        {"glower", TEXT_EMOTE_GLOWER},
        {"headache", TEXT_EMOTE_HEADACHE},
        {"hiccup", TEXT_EMOTE_HICCUP},
        {"hiss", TEXT_EMOTE_HISS},
        {"holdhand", TEXT_EMOTE_HOLDHAND},
        {"hurry", TEXT_EMOTE_HURRY},
        {"idea", TEXT_EMOTE_IDEA},
        {"jealous", TEXT_EMOTE_JEALOUS},
        {"luck", TEXT_EMOTE_LUCK},
        {"map", TEXT_EMOTE_MAP},
        {"mercy", TEXT_EMOTE_MERCY},
        {"mutter", TEXT_EMOTE_MUTTER},
        {"nervous", TEXT_EMOTE_NERVOUS},
        {"offer", TEXT_EMOTE_OFFER},
        {"pet", TEXT_EMOTE_PET},
        {"pinch", TEXT_EMOTE_PINCH},
        {"proud", TEXT_EMOTE_PROUD},
        {"promise", TEXT_EMOTE_PROMISE},
        {"pulse", TEXT_EMOTE_PULSE},
        {"punch", TEXT_EMOTE_PUNCH},
        {"pout", TEXT_EMOTE_POUT},
        {"regret", TEXT_EMOTE_REGRET},
        {"revenge", TEXT_EMOTE_REVENGE},
        {"rolleyes", TEXT_EMOTE_ROLLEYES},
        {"ruffle", TEXT_EMOTE_RUFFLE},
        {"sad", TEXT_EMOTE_SAD},
        {"scoff", TEXT_EMOTE_SCOFF},
        {"scold", TEXT_EMOTE_SCOLD},
        {"scowl", TEXT_EMOTE_SCOWL},
        {"search", TEXT_EMOTE_SEARCH},
        {"shakefist", TEXT_EMOTE_SHAKEFIST},
        {"shifty", TEXT_EMOTE_SHIFTY},
        {"shudder", TEXT_EMOTE_SHUDDER},
        {"signal", TEXT_EMOTE_SIGNAL},
        {"silence", TEXT_EMOTE_SILENCE},
        {"sing", TEXT_EMOTE_SING},
        {"smack", TEXT_EMOTE_SMACK},
        {"sneak", TEXT_EMOTE_SNEAK},
        {"sneeze", TEXT_EMOTE_SNEEZE},
        {"snort", TEXT_EMOTE_SNORT},
        {"squeal", TEXT_EMOTE_SQUEAL},
        {"suspicious", TEXT_EMOTE_SUSPICIOUS},
        {"think", TEXT_EMOTE_THINK},
        {"truce", TEXT_EMOTE_TRUCE},
        {"twiddle", TEXT_EMOTE_TWIDDLE},
        {"warn", TEXT_EMOTE_WARN},
        {"snap", TEXT_EMOTE_SNAP},
        {"charm", TEXT_EMOTE_CHARM},
        {"coverears", TEXT_EMOTE_COVEREARS},
        {"crossarms", TEXT_EMOTE_CROSSARMS},
        {"look", TEXT_EMOTE_LOOK},
        {"object", TEXT_EMOTE_OBJECT},
        {"sweat", TEXT_EMOTE_SWEAT},
        {"yw", TEXT_EMOTE_YW},
    };

    auto it = emoteMap.find(emoteName);
    if (it != emoteMap.end())
        return it->second;
    return 0;
}

// Send a text emote from a bot, producing both
// the orange chat text AND the animation (if any).
// Replicates HandleTextEmoteOpcode behavior.
static void SendBotTextEmote(
    Player* bot, uint32 textEmoteId)
{
    if (!bot || !textEmoteId)
        return;

    // Look up animation from EmotesText DBC
    EmotesTextEntry const* em =
        sEmotesTextStore.LookupEntry(textEmoteId);
    if (em)
    {
        uint32 emoteAnim = em->textid;
        switch (emoteAnim)
        {
            case EMOTE_STATE_SLEEP:
            case EMOTE_STATE_SIT:
            case EMOTE_STATE_KNEEL:
            case EMOTE_ONESHOT_NONE:
                break;
            case EMOTE_STATE_DANCE:
                bot->HandleEmoteCommand(
                    EMOTE_ONESHOT_DANCESPECIAL);
                break;
            default:
                bot->HandleEmoteCommand(emoteAnim);
                break;
        }
    }

    // Broadcast SMSG_TEXT_EMOTE (orange text)
    WorldPacket data(SMSG_TEXT_EMOTE, 20 + 1);
    data << bot->GetGUID();
    data << uint32(textEmoteId);
    data << uint32(0);   // emoteNum sequence
    data << uint32(0);   // target name length
    data << uint8(0x00); // empty name
    bot->SendMessageToSet(&data, true);
}

// ============================================================================
// PRE-CACHE INSTANT REACTION HELPERS
// ============================================================================

// Consume one cached response for a bot+category.
// Returns true on hit, populating outMessage/outEmote.
// Uses DirectExecute (sync) for UPDATE to prevent
// double-consume if two hooks fire same tick.
static bool TryConsumeCachedReaction(
    uint32 groupId, uint32 botGuid,
    const std::string& category,
    std::string& outMessage,
    std::string& outEmote)
{
    QueryResult result = CharacterDatabase.Query(
        "SELECT id, message, emote "
        "FROM llm_group_cached_responses "
        "WHERE group_id = {} AND bot_guid = {} "
        "AND event_category = '{}' "
        "AND status = 'ready' "
        "AND (expires_at IS NULL "
        "     OR expires_at > NOW()) "
        "ORDER BY created_at ASC LIMIT 1",
        groupId, botGuid,
        category);

    if (!result)
        return false;

    Field* fields = result->Fetch();
    uint32 cachedId = fields[0].Get<uint32>();
    outMessage = fields[1].Get<std::string>();
    outEmote = fields[2].IsNull()
        ? "" : fields[2].Get<std::string>();

    // Sync UPDATE prevents double-consume
    CharacterDatabase.DirectExecute(
        "UPDATE llm_group_cached_responses "
        "SET status = 'used', used_at = NOW() "
        "WHERE id = {}",
        cachedId);

    LOG_INFO("module",
        "LLMChatter: Pre-cache HIT [{}] "
        "for bot {} group {} (id={})",
        category, botGuid, groupId, cachedId);

    return true;
}

// Replace {target}, {caster}, {spell} placeholders
// with actual names from hook data. Strip unresolved
// tokens and clamp length.
static void ResolvePlaceholders(
    std::string& message,
    const std::string& target,
    const std::string& caster,
    const std::string& spell)
{
    std::string safeTarget =
        target.empty() ? "" : target;
    std::string safeCaster =
        caster.empty() ? "" : caster;
    std::string safeSpell =
        spell.empty() ? "" : spell;

    size_t pos;
    while ((pos = message.find("{target}"))
           != std::string::npos)
        message.replace(pos, 8, safeTarget);
    while ((pos = message.find("{caster}"))
           != std::string::npos)
        message.replace(pos, 8, safeCaster);
    while ((pos = message.find("{spell}"))
           != std::string::npos)
        message.replace(pos, 7, safeSpell);

    // Strip unresolved {tokens} (LLM hallucination)
    std::regex unresolvedRe("\\{[a-zA-Z_]+\\}");
    message = std::regex_replace(
        message, unresolvedRe, "");

    // Clean up punctuation artifacts from
    // empty placeholder replacement
    // ", ," -> ","  and " , " -> " "
    while ((pos = message.find(", ,"))
           != std::string::npos)
        message.replace(pos, 3, ",");
    while ((pos = message.find(" ,"))
           != std::string::npos)
        message.replace(pos, 2, "");
    // ", !" -> "!"  and ", ." -> "."
    while ((pos = message.find(", !"))
           != std::string::npos)
        message.replace(pos, 3, "!");
    while ((pos = message.find(", ."))
           != std::string::npos)
        message.replace(pos, 3, ".");
    // Trailing comma before end of string
    while (!message.empty()
           && (message.back() == ','
               || message.back() == ' '))
        message.pop_back();

    // Collapse double spaces
    while (message.find("  ") != std::string::npos)
    {
        pos = message.find("  ");
        message.replace(pos, 2, " ");
    }

    // Trim leading/trailing whitespace
    while (!message.empty()
           && message.front() == ' ')
        message.erase(0, 1);
    while (!message.empty()
           && message.back() == ' ')
        message.pop_back();

    // Clamp to max message length
    if (message.size()
        > sLLMChatterConfig->_maxMessageLength)
        message.resize(
            sLLMChatterConfig->_maxMessageLength);
}

// Send a party message instantly via native
// BroadcastPacket, with optional emote animation.
static void SendPartyMessageInstant(
    Player* bot, Group* group,
    const std::string& message,
    const std::string& emote)
{
    WorldPacket data;
    ChatHandler::BuildChatPacket(
        data,
        CHAT_MSG_PARTY,
        message,
        LANG_UNIVERSAL,
        CHAT_TAG_NONE,
        bot->GetGUID(),
        bot->GetName());

    group->BroadcastPacket(&data, false);

    if (!emote.empty())
    {
        uint32 textEmoteId =
            GetTextEmoteId(emote);
        if (textEmoteId)
            SendBotTextEmote(bot, textEmoteId);
    }
}

// Forward declaration (defined after EVENT SYSTEM
// UTILITIES section)
static std::string EscapeString(
    const std::string& str);

// Record a pre-cached message in chat history
// so Python sees it for conversation context.
static void RecordCachedChatHistory(
    uint32 groupId, uint32 botGuid,
    const std::string& botName,
    const std::string& message)
{
    CharacterDatabase.Execute(
        "INSERT INTO llm_group_chat_history "
        "(group_id, speaker_guid, speaker_name, "
        "is_bot, message) "
        "VALUES ({}, {}, '{}', 1, '{}')",
        groupId, botGuid,
        EscapeString(botName),
        EscapeString(message));
}

// ============================================================================
// EVENT SYSTEM UTILITIES
// ============================================================================

// Cooldown cache to prevent spamming database checks
static std::map<std::string, time_t> _cooldownCache;

// Check if a cooldown key is still active
static bool IsOnCooldown(const std::string& cooldownKey, uint32 cooldownSeconds)
{
    auto it = _cooldownCache.find(cooldownKey);
    if (it != _cooldownCache.end())
    {
        time_t now = time(nullptr);
        if (now - it->second < cooldownSeconds)
            return true;
    }

    // Also check database for persistent cooldowns
    QueryResult result = CharacterDatabase.Query(
        "SELECT 1 FROM llm_chatter_events "
        "WHERE cooldown_key = '{}' AND created_at > DATE_SUB(NOW(), INTERVAL {} SECOND) "
        "LIMIT 1",
        cooldownKey, cooldownSeconds);

    if (result)
        return true;

    return false;
}

// Set cooldown in cache
static void SetCooldown(const std::string& cooldownKey)
{
    _cooldownCache[cooldownKey] = time(nullptr);
}

// Escape string for SQL
static std::string EscapeString(const std::string& str)
{
    std::string result = str;
    size_t pos = 0;
    // Escape backslashes first
    while ((pos = result.find('\\', pos)) != std::string::npos)
    {
        result.replace(pos, 1, "\\\\");
        pos += 2;
    }
    pos = 0;
    while ((pos = result.find('\'', pos)) != std::string::npos)
    {
        result.replace(pos, 1, "''");
        pos += 2;
    }
    return result;
}

// Escape string for JSON values that will be inserted via SQL string literal
// MySQL interprets backslashes in string literals, so we need double-escaping:
// - For a JSON quote (\"), we need \\" in SQL to store \" in the database
// - For a literal backslash (\\), we need \\\\ in SQL to store \\ in the database
//
// NOTE: JsonEscape handles BOTH JSON escaping AND SQL
// single-quote escaping. The escaped output is used
// directly in SQL string literals via fmt::format.
// If modifying this function, ensure single-quote
// escaping (case '\'') is preserved to prevent SQL
// injection in CharacterDatabase.Execute() calls.
static std::string JsonEscape(const std::string& str)
{
    std::string result;
    result.reserve(str.size() * 2);
    for (char c : str)
    {
        switch (c)
        {
            case '"':  result += "\\\\\""; break;  // \" in JSON, needs \\" in SQL
            case '\\': result += "\\\\\\\\"; break;  // \\ in JSON, needs \\\\ in SQL
            case '\n': result += "\\\\n"; break;
            case '\r': result += "\\\\r"; break;
            case '\t': result += "\\\\t"; break;
            case '\'': result += "''"; break;  // SQL single quote escape
            default:   result += c; break;
        }
    }
    return result;
}

// Calculate reaction delay based on event type
static uint32 GetReactionDelaySeconds(const std::string& eventType)
{
    // Returns delay in seconds (min, max)
    uint32 minDelay, maxDelay;

    if (eventType == "day_night_transition")
        { minDelay = 120; maxDelay = 600; }
    else if (eventType == "holiday_start" || eventType == "holiday_end")
        { minDelay = 300; maxDelay = 900; }
    else if (eventType == "weather_change")
        { minDelay = 60; maxDelay = 300; }
    else if (eventType == "weather_ambient")
        { minDelay = 120; maxDelay = 600; }
    else if (eventType == "transport_arrives")
        { minDelay = 5; maxDelay = 15; }  // React quickly while transport is still at dock
    else if (eventType == "bot_group_quest_accept")
        { minDelay = 5; maxDelay = 15; }
    else if (eventType == "bot_group_discovery")
        { minDelay = 5; maxDelay = 20; }
    else
        { minDelay = 30; maxDelay = 120; }

    return urand(minDelay, maxDelay);
}

// Queue an event to the database
static void QueueEvent(const std::string& eventType, const std::string& eventScope,
                       uint32 zoneId, uint32 mapId, uint8 priority,
                       const std::string& cooldownKey, uint32 cooldownSeconds,
                       uint32 subjectGuid, const std::string& subjectName,
                       uint32 targetGuid, const std::string& targetName, uint32 targetEntry,
                       const std::string& extraData)
{
    if (!sLLMChatterConfig->IsEnabled() || !sLLMChatterConfig->_useEventSystem)
        return;

    // Event-type specific config gates
    if (eventType == "weather_ambient")
    {
        if (!sLLMChatterConfig->_eventsWeather)
            return;
    }

    // Event-level cooldown bypass for rare transition
    // events that should always be queued when they
    // happen.
    bool bypassEventCooldown =
        (eventType == "weather_change");

    // Check cooldown FIRST, before RNG roll.
    // This prevents multi-tick RNG amplification:
    // transports stay in a zone for multiple check
    // ticks, and each tick would get an independent
    // RNG roll if cooldown isn't set early. By setting
    // cooldown on first detection, each arrival gets
    // exactly one RNG chance.
    if (!bypassEventCooldown
        && !cooldownKey.empty()
        && IsOnCooldown(cooldownKey, cooldownSeconds))
    {
        if (eventType != "transport_arrives")
        {
            LOG_DEBUG("module",
                "LLMChatter: Event {} on cooldown ({})",
                eventType, cooldownKey);
        }
        return;
    }

    // Set cooldown immediately on first detection,
    // regardless of RNG outcome below
    if (!bypassEventCooldown
        && !cooldownKey.empty())
        SetCooldown(cooldownKey);

    // Roll reaction chance
    // Holidays and day/night are rare one-time events;
    // always let them through
    bool alwaysFire =
        (eventType == "holiday_start"
         || eventType == "holiday_end"
         || eventType == "day_night_transition"
         || eventType == "weather_change");

    uint32 reactionChance =
        sLLMChatterConfig->_eventReactionChance;
    if (eventType == "transport_arrives"
        && sLLMChatterConfig->_transportEventChance > 0)
        reactionChance =
            sLLMChatterConfig->_transportEventChance;
    else if (eventType == "minor_event"
        && sLLMChatterConfig->_minorEventChance > 0)
        reactionChance =
            sLLMChatterConfig->_minorEventChance;

    if (!alwaysFire
        && urand(1, 100) > reactionChance)
    {
        LOG_DEBUG("module",
            "LLMChatter: Event {} skipped "
            "(reaction chance {}%)",
            eventType, reactionChance);
        return;
    }

    // Calculate delays
    // Expiration must be AFTER reaction delay,
    // otherwise events expire before they fire
    uint32 reactionDelay =
        GetReactionDelaySeconds(eventType);
    uint32 expirationSeconds =
        reactionDelay
        + sLLMChatterConfig->_eventExpirationSeconds;

    // Insert event
    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_events "
        "(event_type, event_scope, zone_id, map_id, priority, cooldown_key, "
        "subject_guid, subject_name, target_guid, target_name, target_entry, "
        "extra_data, status, react_after, expires_at) "
        "VALUES ('{}', '{}', {}, {}, {}, '{}', {}, '{}', {}, '{}', {}, '{}', 'pending', "
        "DATE_ADD(NOW(), INTERVAL {} SECOND), DATE_ADD(NOW(), INTERVAL {} SECOND))",
        eventType, eventScope,
        zoneId > 0 ? std::to_string(zoneId) : "NULL",
        mapId > 0 ? std::to_string(mapId) : "NULL",
        priority, EscapeString(cooldownKey),
        subjectGuid > 0 ? std::to_string(subjectGuid) : "NULL",
        EscapeString(subjectName),
        targetGuid > 0 ? std::to_string(targetGuid) : "NULL",
        EscapeString(targetName),
        targetEntry > 0 ? std::to_string(targetEntry) : "NULL",
        extraData,  // Already JSON-escaped, don't double-escape
        reactionDelay, expirationSeconds);

    LOG_INFO("module", "LLMChatter: Queued event {} in zone {} (react in {}s)",
             eventType, zoneId, reactionDelay);
}

// Helper: check if a game event is a real holiday
// (not Call to Arms, fishing pools, building phases,
// or fireworks). These non-holiday events have
// HolidayId != HOLIDAY_NONE but aren't actual
// holidays worth triggering chatter for.
static bool IsHolidayEvent(uint16 eventId)
{
    GameEventMgr::GameEventDataMap const& events =
        sGameEventMgr->GetEventMap();
    if (eventId >= events.size())
        return false;
    if (events[eventId].HolidayId == HOLIDAY_NONE)
        return false;

    // Exclude non-holiday events that happen to
    // have a HolidayId (BG rotations, setup phases,
    // fishing pools, fireworks)
    std::string const& desc =
        events[eventId].Description;
    if (desc.find("Call to Arms") != std::string::npos)
        return false;
    if (desc.find("Building") != std::string::npos)
        return false;
    if (desc.find("Fishing Pools")
        != std::string::npos)
        return false;
    if (desc.find("Fireworks") != std::string::npos)
        return false;

    return true;
}

// Helper: check if a game event is a minor
// non-holiday event worth occasional mention
// (Call to Arms BG rotations, fishing derbies,
// fireworks). These fire less often than holidays.
static bool IsMinorGameEvent(uint16 eventId)
{
    GameEventMgr::GameEventDataMap const& events =
        sGameEventMgr->GetEventMap();
    if (eventId >= events.size())
        return false;
    if (events[eventId].HolidayId == HOLIDAY_NONE)
        return false;

    // Only match events explicitly excluded from
    // IsHolidayEvent() (except Building phases
    // which are invisible setup events)
    std::string const& desc =
        events[eventId].Description;
    if (desc.find("Call to Arms") != std::string::npos)
        return true;
    if (desc.find("Fishing Pools")
        != std::string::npos)
        return true;
    if (desc.find("Fireworks") != std::string::npos)
        return true;

    return false;
}

// Helper: check if a zone is a capital city
static bool IsCapitalCity(uint32 zoneId)
{
    if (AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(zoneId))
        return (area->flags
                & AREA_FLAG_CAPITAL) != 0;
    return false;
}

// Helper: check if player is in the overworld
// (not dungeon/raid/BG/arena)
static bool IsInOverworld(Player* player)
{
    if (!player)
        return false;
    WorldSession* session = player->GetSession();
    if (!session || session->PlayerLoading())
        return false;
    Map* map = player->GetMap();
    if (!map)
        return false;
    return !map->Instanceable();
}

// Helper: get zones where real (non-bot) players are
static std::vector<uint32> GetZonesWithRealPlayers()
{
    std::map<uint32, bool> zoneMap;
    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();

    for (auto const& pair : sessions)
    {
        WorldSession* session = pair.second;
        if (!session || session->PlayerLoading())
            continue;
        Player* player = session->GetPlayer();
        if (!player || !player->IsInWorld())
            continue;
        if (!IsPlayerBot(player)
            && IsInOverworld(player))
        {
            uint32 zoneId = player->GetZoneId();
            if (zoneId > 0)
                zoneMap[zoneId] = true;
        }
    }

    std::vector<uint32> zones;
    for (auto const& pair : zoneMap)
        zones.push_back(pair.first);
    return zones;
}

// Queue a holiday event for zones where real
// players are present. Cities get a higher
// chance, open-world zones get a lower chance.
static void QueueHolidayForZones(
    uint16 eventId,
    const std::string& eventType = "holiday_start")
{
    GameEventMgr::GameEventDataMap const& events =
        sGameEventMgr->GetEventMap();
    GameEventData const& eventData =
        events[eventId];

    std::vector<uint32> playerZones =
        GetZonesWithRealPlayers();
    for (uint32 zoneId : playerZones)
    {
        uint32 chance = IsCapitalCity(zoneId)
            ? sLLMChatterConfig->_holidayCityChance
            : sLLMChatterConfig->_holidayZoneChance;

        if (urand(1, 100) > chance)
            continue;

        std::string cooldownKey =
            eventType + ":"
            + std::to_string(eventId)
            + ":zone:"
            + std::to_string(zoneId);
        std::string extraData =
            "{\"event_name\":\""
            + JsonEscape(eventData.Description)
            + "\",\"zone_id\":"
            + std::to_string(zoneId) + "}";

        QueueEvent(
            eventType, "global",
            zoneId, 0, 2, cooldownKey,
            sLLMChatterConfig
                ->_holidayCooldownSeconds,
            0, "", 0, "",
            eventId, extraData);
    }
}

// Get zone name from zone ID (free function for cross-class use)
static std::string GetZoneName(uint32 zoneId)
{
    if (AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(zoneId))
    {
        return area->area_name[0];  // English name
    }
    return "Unknown Zone";
}

// Check if a bot can speak in the General channel
// for its current zone. Verifies the bot is actually
// a member of a General channel matching its zone.
static bool CanSpeakInGeneralChannel(Player* bot)
{
    if (!bot || !bot->IsInWorld())
        return false;

    // Look up the bot's current zone name.
    // Use world default locale to match how
    // SayToChannel() resolves zone names
    // (GetLocalizedAreaName uses
    //  sWorld->GetDefaultDbcLocale()).
    uint32 zoneId = bot->GetZoneId();
    AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(zoneId);
    if (!area)
        return false;
    std::string zoneName =
        area->area_name[
            sWorld->GetDefaultDbcLocale()];
    if (zoneName.empty())
        zoneName = area->area_name[LOCALE_enUS];
    if (zoneName.empty())
        return false;

    // Get ChannelMgr for the bot's faction
    ChannelMgr* cMgr =
        ChannelMgr::forTeam(bot->GetTeamId());
    if (!cMgr)
        return false;

    // Find a General channel whose name contains
    // the bot's zone name
    for (auto const& [key, channel] :
         cMgr->GetChannels())
    {
        if (!channel)
            continue;
        if (channel->GetChannelId()
            != ChatChannelId::GENERAL)
            continue;
        if (channel->GetName().find(zoneName)
            == std::string::npos)
            continue;

        // Found matching General channel for zone.
        // Check if bot is actually a member.
        return bot->IsInChannel(channel);
    }

    // No General channel exists for this zone
    return false;
}

// ------------------------------------------------
// Auto-join bot to General channel for its current
// zone, and leave any stale General channel from a
// previous zone.  Called on zone change so bots
// stay eligible for CanSpeakInGeneralChannel().
// ------------------------------------------------
static void EnsureBotInGeneralChannel(
    Player* bot)
{
    if (!bot || !bot->IsInWorld())
        return;

    // --- resolve current zone name ---------------
    uint32 zoneId = bot->GetZoneId();
    AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(zoneId);
    if (!area)
        return;

    uint8 locale =
        sWorld->GetDefaultDbcLocale();
    std::string zoneName =
        area->area_name[locale];
    if (zoneName.empty())
        zoneName = area->area_name[LOCALE_enUS];
    if (zoneName.empty())
        return;

    // --- build the exact channel name from DBC ---
    ChatChannelsEntry const* chEntry =
        sChatChannelsStore.LookupEntry(
            ChatChannelId::GENERAL);
    if (!chEntry)
        return;

    char nameBuf[100];
    std::snprintf(nameBuf, sizeof(nameBuf),
        chEntry->pattern[locale],
        zoneName.c_str());
    std::string newChanName(nameBuf);

    ChannelMgr* cMgr =
        ChannelMgr::forTeam(bot->GetTeamId());
    if (!cMgr)
        return;

    // Map updates can run on worker threads
    // (MapUpdate.Threads > 1), so bots on
    // different maps may hit this concurrently.
    // Mirrors core's UpdateLocalChannels mutex.
    // Not the *same* lock, but protects our own
    // concurrent calls from each other.
    static std::mutex channelsLock;
    std::lock_guard<std::mutex> guard(
        channelsLock);

    // --- leave any old General channel -----------
    for (auto const& [key, channel] :
         cMgr->GetChannels())
    {
        if (!channel)
            continue;
        if (channel->GetChannelId()
            != ChatChannelId::GENERAL)
            continue;
        if (channel->GetName() == newChanName)
            continue;  // same zone — skip

        // LeaveChannel is a no-op if bot is not
        // a member (checks IsOn internally).
        channel->LeaveChannel(bot, false);
        bot->LeftChannel(channel);
    }

    // --- join the new zone's General channel -----
    Channel* joinChan =
        cMgr->GetJoinChannel(
            newChanName,
            ChatChannelId::GENERAL);
    if (joinChan)
        joinChan->JoinChannel(bot, "");
    else
        LOG_WARN("module",
            "LLMChatter: Failed to get/create "
            "channel '{}' for {}",
            newChanName, bot->GetName());
}

// ------------------------------------------------
// Build bot state JSON fragment for enriched events
// (file-scope so WorldScript + PlayerScript can use)
// ------------------------------------------------
static std::string BuildBotStateJson(
    Player* player)
{
    if (!player)
        return "";

    // Health & power
    float healthPct = player->GetHealthPct();
    bool inCombat = player->IsInCombat();

    // Only include mana for mana-using classes
    int manaPctInt = -1; // sentinel: not mana user
    if (player->GetMaxPower(POWER_MANA) > 0)
        manaPctInt =
            (int)player->GetPowerPct(POWER_MANA);

    // Real role from PlayerbotAI (talent-based)
    std::string role = "dps"; // default
    PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
    if (ai)
    {
        if (PlayerbotAI::IsTank(player))
            role = "tank";
        else if (PlayerbotAI::IsHeal(player))
            role = "healer";
        else if (PlayerbotAI::IsRanged(player))
            role = "ranged_dps";
        else
            role = "melee_dps";
    }

    // Current target
    std::string targetName = "";
    Unit* victim = player->GetVictim();
    if (victim)
        targetName = victim->GetName();

    // Bot state (combat/non-combat/dead)
    std::string botState = "non_combat";
    if (ai)
    {
        BotState state = ai->GetState();
        if (state == BOT_STATE_COMBAT)
            botState = "combat";
        else if (state == BOT_STATE_DEAD)
            botState = "dead";
    }

    return
        "\"bot_state\":{"
        "\"health_pct\":" +
            std::to_string((int)healthPct) + ","
        "\"mana_pct\":" +
            std::to_string(manaPctInt) + ","
        "\"role\":\"" + role + "\","
        "\"in_combat\":" +
            std::string(
                inCombat ? "true" : "false")
            + ","
        "\"target\":\"" +
            JsonEscape(targetName) + "\","
        "\"bot_ai_state\":\"" + botState + "\""
        "}";
}

// ============================================================================
// GAME EVENT SCRIPT - Holiday Events
// ============================================================================

class LLMChatterGameEventScript : public GameEventScript
{
public:
    LLMChatterGameEventScript() : GameEventScript("LLMChatterGameEventScript") {}

    void OnStart(uint16 eventId) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem)
            return;

        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();

        if (sLLMChatterConfig->_eventsHolidays
            && IsHolidayEvent(eventId))
        {
            QueueHolidayForZones(eventId,
                "holiday_start");
            LOG_INFO("module",
                "LLMChatter: Holiday started - {}",
                events[eventId].Description);
        }
        else if (sLLMChatterConfig->_eventsMinor
            && IsMinorGameEvent(eventId))
        {
            QueueHolidayForZones(eventId,
                "minor_event");
            LOG_INFO("module",
                "LLMChatter: Minor event started"
                " - {}",
                events[eventId].Description);
        }
    }

    void OnStop(uint16 eventId) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem)
            return;

        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();

        if (sLLMChatterConfig->_eventsHolidays
            && IsHolidayEvent(eventId))
        {
            QueueHolidayForZones(eventId,
                "holiday_end");
            LOG_INFO("module",
                "LLMChatter: Holiday ended - {}",
                events[eventId].Description);
        }
        // Minor events don't need end messages
        // (BG rotations quietly expire)
    }
};

// ============================================================================
// ALE SCRIPT - Weather Events
// ============================================================================

// Track previous weather state per zone for transition detection
static std::map<uint32, WeatherState> _zoneWeatherState;

// Convert WeatherState enum to readable string
static std::string GetWeatherStateName(WeatherState state)
{
    switch (state)
    {
        case WEATHER_STATE_FINE:             return "clear";
        case WEATHER_STATE_FOG:              return "foggy";
        case WEATHER_STATE_LIGHT_RAIN:       return "light rain";
        case WEATHER_STATE_MEDIUM_RAIN:      return "rain";
        case WEATHER_STATE_HEAVY_RAIN:       return "heavy rain";
        case WEATHER_STATE_LIGHT_SNOW:       return "light snow";
        case WEATHER_STATE_MEDIUM_SNOW:      return "snow";
        case WEATHER_STATE_HEAVY_SNOW:       return "heavy snow";
        case WEATHER_STATE_LIGHT_SANDSTORM:  return "light sandstorm";
        case WEATHER_STATE_MEDIUM_SANDSTORM: return "sandstorm";
        case WEATHER_STATE_HEAVY_SANDSTORM:  return "heavy sandstorm";
        case WEATHER_STATE_THUNDERS:         return "thunderstorm";
        case WEATHER_STATE_BLACKRAIN:        return "black rain";
        case WEATHER_STATE_BLACKSNOW:        return "black snow";
        default:                             return "unknown";
    }
}

// Get weather category (rain, snow, sand, other)
static std::string GetWeatherCategory(WeatherState state)
{
    switch (state)
    {
        case WEATHER_STATE_LIGHT_RAIN:
        case WEATHER_STATE_MEDIUM_RAIN:
        case WEATHER_STATE_HEAVY_RAIN:
        case WEATHER_STATE_BLACKRAIN:
            return "rain";
        case WEATHER_STATE_LIGHT_SNOW:
        case WEATHER_STATE_MEDIUM_SNOW:
        case WEATHER_STATE_HEAVY_SNOW:
        case WEATHER_STATE_BLACKSNOW:
            return "snow";
        case WEATHER_STATE_LIGHT_SANDSTORM:
        case WEATHER_STATE_MEDIUM_SANDSTORM:
        case WEATHER_STATE_HEAVY_SANDSTORM:
            return "sandstorm";
        case WEATHER_STATE_FOG:
            return "fog";
        case WEATHER_STATE_THUNDERS:
            return "storm";
        default:
            return "weather";
    }
}

// Get weather intensity description (based on grade)
static std::string GetWeatherIntensity(float grade)
{
    if (grade < 0.25f)
        return "mild";
    else if (grade < 0.5f)
        return "moderate";
    else if (grade < 0.75f)
        return "strong";
    else
        return "intense";
}

class LLMChatterALEScript : public ALEScript
{
public:
    LLMChatterALEScript() : ALEScript("LLMChatterALEScript") {}

    void OnWeatherChange(Weather* weather, WeatherState state, float grade) override
    {
        LOG_DEBUG("module", "LLMChatter: ALEScript OnWeatherChange - zone {} state {} grade {}",
                  weather->GetZone(), static_cast<uint32>(state), grade);

        if (!sLLMChatterConfig->IsEnabled() || !sLLMChatterConfig->_useEventSystem)
            return;
        if (!sLLMChatterConfig->_eventsWeather)
            return;

        uint32 zoneId = weather->GetZone();

        // Get previous weather state for this zone (default to FINE if unknown)
        // IMPORTANT: Always track state changes even if we skip the event,
        // otherwise transition detection becomes incorrect when a player enters later
        WeatherState prevState = WEATHER_STATE_FINE;
        auto it = _zoneWeatherState.find(zoneId);
        if (it != _zoneWeatherState.end())
            prevState = it->second;

        // Update tracked state (before checking for real players)
        _zoneWeatherState[zoneId] = state;

        // Only create weather events for zones where a real player is present
        // Note: GetAllSessions() is safe to iterate here as ALEScript hooks
        // are called from the main world thread during weather updates
        bool hasRealPlayer = false;
        auto const& sessions = sWorldSessionMgr->GetAllSessions();
        for (auto const& pair : sessions)
        {
            WorldSession* session = pair.second;
            if (!session || session->PlayerLoading())
                continue;

            Player* player = session->GetPlayer();
            if (!player || !player->IsInWorld())
                continue;

            if (!IsPlayerBot(player) && player->GetZoneId() == zoneId)
            {
                hasRealPlayer = true;
                break;
            }
        }

        if (!hasRealPlayer)
        {
            LOG_DEBUG("module", "LLMChatter: No real player in zone {}, skipping weather event", zoneId);
            return;
        }

        // Determine what kind of transition this is
        std::string transitionType;
        if (prevState == WEATHER_STATE_FINE && state != WEATHER_STATE_FINE)
        {
            // Weather starting
            transitionType = "starting";
        }
        else if (prevState != WEATHER_STATE_FINE && state == WEATHER_STATE_FINE)
        {
            // Weather clearing
            transitionType = "clearing";
        }
        else if (prevState != WEATHER_STATE_FINE && state != WEATHER_STATE_FINE)
        {
            // Weather changing (e.g., rain getting heavier, or changing type)
            if (GetWeatherCategory(prevState) == GetWeatherCategory(state))
            {
                // Same category, intensity change
                transitionType = "intensifying";
            }
            else
            {
                // Different weather type
                transitionType = "changing";
            }
        }
        else
        {
            // FINE to FINE - no change
            return;
        }

        std::string weatherName = GetWeatherStateName(state);
        std::string prevWeatherName = GetWeatherStateName(prevState);
        std::string intensity = GetWeatherIntensity(grade);
        std::string category = GetWeatherCategory(state);

        // Use zone + transition specific cooldown
        std::string cooldownKey = "weather:" + std::to_string(zoneId) + ":" + transitionType;

        // Build extra data JSON with transition context
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{\"weather_type\":\"" + weatherName + "\","
                               "\"previous_weather\":\"" + prevWeatherName + "\","
                               "\"transition\":\"" + transitionType + "\","
                               "\"category\":\"" + category + "\","
                               "\"intensity\":\"" + intensity + "\","
                               "\"grade\":" + std::to_string(grade) + "}";

        QueueEvent("weather_change", "zone",
                   zoneId, 0, 5, cooldownKey,
                   sLLMChatterConfig
                       ->_weatherCooldownSeconds,
                   0, "", 0, "",
                   static_cast<uint32>(state),
                   extraData);

        // LOG_INFO("module", "LLMChatter: Weather {} in zone {} - {} -> {} ({})",
        //          transitionType, zoneId, prevWeatherName, weatherName, intensity);
    }
};

// ============================================================================
// TRANSPORT TRACKING
// ============================================================================

// Cached transport info (loaded from DB on startup)
struct TransportInfo
{
    uint32 entry;
    std::string fullName;
    std::string destination;
    std::string transportType;  // "Boat", "Zeppelin", "Turtle"
};

// Transport info cache: entry -> TransportInfo
static std::map<uint32, TransportInfo> _transportCache;

// Transport zone tracking: GUID -> (lastZoneId, lastMapId)
static std::map<ObjectGuid::LowType, std::pair<uint32, uint32>> _transportZones;

// Parse transport name to extract destination and type
// Example: "Auberdine, Darkshore and Stormwind Harbor (Boat, Alliance ("The Bravery"))"
// Returns: destination = "Stormwind Harbor", type = "Boat"
static void ParseTransportName(const std::string& fullName, std::string& destination, std::string& transportType)
{
    destination = "";
    transportType = "";

    // Find " and " to split origin/destination
    size_t andPos = fullName.find(" and ");
    if (andPos == std::string::npos)
    {
        destination = fullName;
        return;
    }

    // Get everything after " and "
    std::string afterAnd = fullName.substr(andPos + 5);

    // Find " (" to cut off the transport type portion
    size_t parenPos = afterAnd.find(" (");
    if (parenPos != std::string::npos)
    {
        destination = afterAnd.substr(0, parenPos);

        // Extract transport type from parentheses
        std::string typeSection = afterAnd.substr(parenPos + 2);
        size_t commaPos = typeSection.find(',');
        if (commaPos != std::string::npos)
        {
            transportType = typeSection.substr(0, commaPos);
        }
        else
        {
            size_t closeParenPos = typeSection.find(')');
            if (closeParenPos != std::string::npos)
            {
                transportType = typeSection.substr(0, closeParenPos);
            }
        }
    }
    else
    {
        destination = afterAnd;
    }
}

// Load transport info from database
static void LoadTransportCache()
{
    _transportCache.clear();

    QueryResult result = WorldDatabase.Query(
        "SELECT entry, name FROM transports");

    if (!result)
    {
        LOG_INFO("module", "LLMChatter: No transports found in database");
        return;
    }

    uint32 count = 0;
    do
    {
        Field* fields = result->Fetch();
        uint32 entry = fields[0].Get<uint32>();
        std::string name = fields[1].Get<std::string>();

        TransportInfo info;
        info.entry = entry;
        info.fullName = name;
        ParseTransportName(name, info.destination, info.transportType);

        _transportCache[entry] = info;
        count++;

        LOG_DEBUG("module", "LLMChatter: Loaded transport {} -> {} ({})",
                  entry, info.destination, info.transportType);
    }
    while (result->NextRow());

    LOG_INFO("module", "LLMChatter: Loaded {} transports into cache", count);
}

// ============================================================================
// WORLD SCRIPT - Main chatter logic, day/night transitions
// ============================================================================

// Forward declaration (defined after PlayerScript)
static void CheckGroupCombatState();

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
        CharacterDatabase.Execute(
            "UPDATE llm_chatter_events SET status = 'expired' "
            "WHERE status IN ('pending', 'processing')");

        // Clear stale group data (groups don't persist across restarts)
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_bot_traits");
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_chat_history");
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_cached_responses");

        // Load transport info cache for transport events
        LoadTransportCache();

        // Check for holidays and minor events
        // already active at startup (OnStart hook
        // only fires at the moment an event begins,
        // not if the server restarts mid-event)
        if (sLLMChatterConfig->_useEventSystem)
        {
            GameEventMgr::GameEventDataMap const&
                events =
                    sGameEventMgr->GetEventMap();
            for (uint16 eventId = 1;
                 eventId < events.size();
                 ++eventId)
            {
                if (!sGameEventMgr
                        ->IsActiveEvent(eventId))
                    continue;

                GameEventData const& eventData =
                    events[eventId];

                if (sLLMChatterConfig->_eventsHolidays
                    && IsHolidayEvent(eventId))
                {
                    LOG_INFO("module",
                        "LLMChatter: Holiday active"
                        " at startup - {}",
                        eventData.Description);
                }
                else if (
                    sLLMChatterConfig->_eventsMinor
                    && IsMinorGameEvent(eventId))
                {
                    LOG_INFO("module",
                        "LLMChatter: Minor event "
                        "active at startup - {}",
                        eventData.Description);
                }
            }
        }

        LOG_INFO("module", "LLMChatter: Cleared stale messages, events, group traits, and chat history on startup");
        _lastTriggerTime = 0;
        _lastDeliveryTime = 0;
        _lastEnvironmentCheckTime = 0;
        _lastTransportCheckTime = 0;
        _lastTimePeriod = "";
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

        // Check for environmental events (configurable)
        if (sLLMChatterConfig->_useEventSystem &&
            now - _lastEnvironmentCheckTime >=
                sLLMChatterConfig
                    ->_environmentCheckSeconds * 1000)
        {
            _lastEnvironmentCheckTime = now;
            CheckDayNightTransition();
            if (sLLMChatterConfig->_eventsHolidays
                || sLLMChatterConfig->_eventsMinor)
                CheckActiveHolidays();
            if (sLLMChatterConfig->_eventsWeather)
                CheckAmbientWeather();
        }

        // Check for transport zone changes
        if (sLLMChatterConfig->_useEventSystem &&
            sLLMChatterConfig->_eventsTransports &&
            now - _lastTransportCheckTime >=
                sLLMChatterConfig
                    ->_transportCheckSeconds * 1000)
        {
            _lastTransportCheckTime = now;
            CheckTransportZones();
        }

        // State-triggered callouts (5s interval)
        {
            static time_t lastCombatStateCheck = 0;
            time_t nowSec = time(nullptr);
            if (nowSec - lastCombatStateCheck >=
                (time_t)sLLMChatterConfig
                    ->_combatStateCheckInterval)
            {
                lastCombatStateCheck = nowSec;
                CheckGroupCombatState();
            }
        }
    }

private:
    uint32 _lastTriggerTime = 0;
    uint32 _lastDeliveryTime = 0;
    uint32 _lastEnvironmentCheckTime = 0;
    uint32 _lastTransportCheckTime = 0;
    std::string _lastTimePeriod = "";

    // Get detailed time period from hour
    // Returns both the period name and a descriptive phrase
    std::pair<std::string, std::string> GetTimePeriod(int hour)
    {
        // Time periods based on typical WoW day cycle
        if (hour >= 5 && hour < 7)
            return {"dawn", "The sun is rising on the horizon"};
        else if (hour >= 7 && hour < 9)
            return {"early_morning", "It's early morning"};
        else if (hour >= 9 && hour < 12)
            return {"morning", "The morning is well underway"};
        else if (hour >= 12 && hour < 14)
            return {"midday", "The sun is at its peak"};
        else if (hour >= 14 && hour < 17)
            return {"afternoon", "It's afternoon"};
        else if (hour >= 17 && hour < 19)
            return {"evening", "Evening approaches"};
        else if (hour >= 19 && hour < 21)
            return {"dusk", "The sun is setting"};
        else if (hour >= 21 && hour < 23)
            return {"night", "Night has fallen"};
        else if (hour == 23 || hour == 0)
            return {"midnight", "It's the middle of the night"};
        else // 1-4
            return {"late_night", "The night is deep and quiet"};
    }

    // Check for time-of-day transitions
    void CheckDayNightTransition()
    {
        if (!sLLMChatterConfig->_eventsDayNight)
            return;

        // Get in-game time
        time_t gameTime = GameTime::GetGameTime().count();
        struct tm* timeInfo = localtime(&gameTime);
        int hour = timeInfo->tm_hour;
        int minute = timeInfo->tm_min;

        // Get current time period
        auto [timePeriod, description] = GetTimePeriod(hour);

        // Only trigger if time period changed
        if (timePeriod == _lastTimePeriod)
            return;

        std::string previousPeriod = _lastTimePeriod;
        _lastTimePeriod = timePeriod;

        // Skip initial state (server just started)
        if (previousPeriod.empty())
            return;

        // Determine if it's day or night (for backward compatibility)
        bool isDay = (hour >= 6 && hour < 18);

        // Use period-specific cooldown
        std::string cooldownKey = "time_period:" + timePeriod;

        // Build rich time context for the LLM
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{"
            "\"is_day\":" + std::string(isDay ? "true" : "false") + ","
            "\"hour\":" + std::to_string(hour) + ","
            "\"minute\":" + std::to_string(minute) + ","
            "\"time_period\":\"" + timePeriod + "\","
            "\"previous_period\":\"" + previousPeriod + "\","
            "\"description\":\"" + JsonEscape(description) + "\""
            "}";

        QueueEvent("day_night_transition", "global",
                   0, 0, 7, cooldownKey,
                   sLLMChatterConfig
                       ->_dayNightCooldownSeconds,
                   0, "", 0, "", 0, extraData);

        // LOG_INFO("module", "LLMChatter: Time transition - {} -> {} ({}:{})",
        //          previousPeriod, timePeriod, hour, minute);
    }

    // Periodically check zones with active (non-clear)
    // weather and queue ambient weather events for zones
    // where a real player is present. Unlike weather_change
    // (which fires on transitions), this lets bots muse
    // about ongoing weather conditions.
    void CheckAmbientWeather()
    {
        for (auto const& pair : _zoneWeatherState)
        {
            uint32 zoneId = pair.first;
            WeatherState state = pair.second;

            // Skip clear weather
            if (state == WEATHER_STATE_FINE)
                continue;

            // Check if a real player is in this zone
            bool hasRealPlayer = false;
            auto const& sessions =
                sWorldSessionMgr->GetAllSessions();
            for (auto const& sp : sessions)
            {
                WorldSession* session = sp.second;
                if (!session || session->PlayerLoading())
                    continue;

                Player* player = session->GetPlayer();
                if (!player || !player->IsInWorld())
                    continue;

                if (!IsPlayerBot(player)
                    && player->GetZoneId() == zoneId)
                {
                    hasRealPlayer = true;
                    break;
                }
            }

            if (!hasRealPlayer)
                continue;

            std::string weatherName =
                GetWeatherStateName(state);
            std::string category =
                GetWeatherCategory(state);

            std::string cooldownKey =
                "weather_ambient:"
                + std::to_string(zoneId);

            // Build extra data JSON
            std::string extraData =
                "{\"weather_type\":\""
                + weatherName + "\","
                "\"category\":\""
                + category + "\","
                "\"intensity\":\"sustained\","
                "\"is_ambient\":true}";

            QueueEvent(
                "weather_ambient", "zone",
                zoneId, 0, 3, cooldownKey,
                sLLMChatterConfig
                    ->_weatherAmbientCooldownSeconds,
                0, "", 0, "",
                static_cast<uint32>(state),
                extraData);
        }
    }

    // Periodically re-queue holiday and minor events
    // when a real player is in a zone.
    void CheckActiveHolidays()
    {
        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();

        for (uint16 eventId = 1;
             eventId < events.size(); ++eventId)
        {
            if (!sGameEventMgr->IsActiveEvent(eventId))
                continue;

            if (sLLMChatterConfig->_eventsHolidays
                && IsHolidayEvent(eventId))
            {
                QueueHolidayForZones(eventId);
            }
            else if (sLLMChatterConfig->_eventsMinor
                && IsMinorGameEvent(eventId))
            {
                QueueHolidayForZones(eventId,
                    "minor_event");
            }
        }
    }

    // Check for transport zone changes
    void CheckTransportZones()
    {
        // Iterate all maps to find transports
        sMapMgr->DoForAllMaps([](Map* map)
        {
            if (!map)
                return;

            // Get all transports on this map
            TransportsContainer const& transports = map->GetAllTransports();

            for (Transport* transport : transports)
            {
                if (!transport)
                    continue;

                ObjectGuid::LowType guid = transport->GetGUID().GetCounter();
                uint32 entry = transport->GetEntry();
                uint32 mapId = map->GetId();

                // Get current zone from transport position
                float x = transport->GetPositionX();
                float y = transport->GetPositionY();
                float z = transport->GetPositionZ();
                uint32 currentZone = map->GetZoneId(transport->GetPhaseMask(), x, y, z);

                // Check for zone change
                auto it = _transportZones.find(guid);
                if (it != _transportZones.end())
                {
                    uint32 lastZone = it->second.first;
                    uint32 lastMap = it->second.second;

                    // Detect zone change or map change
                    if (currentZone != lastZone || mapId != lastMap)
                    {
                        // If we are in "no zone" (open sea), just track it.
                        // We'll announce when we enter a real zone.
                        if (currentZone == 0)
                        {
                            _transportZones[guid] = {currentZone, mapId};
                            continue;
                        }

                        // Zone changed! Queue event if we have transport info
                        auto cacheIt = _transportCache.find(entry);
                        if (cacheIt != _transportCache.end())
                        {
                            const TransportInfo& info = cacheIt->second;

                            // Pre-filter bots that can
                            // speak in General channel
                            // for this zone, so Python
                            // only picks verified bots.
                            std::vector<Player*> zoneBots;
                            auto allBots =
                                sRandomPlayerbotMgr
                                    .GetAllBots();
                            for (auto& pair : allBots)
                            {
                                Player* bot = pair.second;
                                if (!bot
                                    || !bot->IsInWorld())
                                    continue;
                                if (bot->GetZoneId()
                                    != currentZone)
                                    continue;
                                zoneBots.push_back(bot);
                                if (zoneBots.size()
                                    >= sLLMChatterConfig
                                        ->_maxBotsPerZone)
                                    break;
                            }

                            // Also check account bots
                            if (zoneBots.size()
                                < sLLMChatterConfig
                                    ->_maxBotsPerZone)
                            {
                                WorldSessionMgr::
                                    SessionMap const&
                                    sessions =
                                    sWorldSessionMgr
                                        ->GetAllSessions();
                                for (auto const& pair
                                     : sessions)
                                {
                                    WorldSession* sess =
                                        pair.second;
                                    if (!sess)
                                        continue;
                                    Player* p =
                                        sess->GetPlayer();
                                    if (!p
                                        || !p->IsInWorld())
                                        continue;
                                    if (!IsPlayerBot(p))
                                        continue;
                                    if (p->GetZoneId()
                                        != currentZone)
                                        continue;
                                    bool found = false;
                                    for (Player* b
                                         : zoneBots)
                                    {
                                        if (b->GetGUID()
                                            == p->GetGUID())
                                        {
                                            found = true;
                                            break;
                                        }
                                    }
                                    if (!found)
                                    {
                                        zoneBots.push_back(
                                            p);
                                        if (zoneBots.size()
                                            >= sLLMChatterConfig
                                                ->_maxBotsPerZone)
                                            break;
                                    }
                                }
                            }

                            // Filter to bots that can
                            // speak in General channel
                            zoneBots.erase(
                                std::remove_if(
                                    zoneBots.begin(),
                                    zoneBots.end(),
                                    [](Player* b) {
                                        return
                                            !CanSpeakInGeneralChannel(b);
                                    }),
                                zoneBots.end());

                            // Build verified_bots JSON
                            std::string verifiedBots = "[";
                            for (size_t i = 0;
                                 i < zoneBots.size(); ++i)
                            {
                                if (i > 0)
                                    verifiedBots += ",";
                                verifiedBots +=
                                    std::to_string(
                                        zoneBots[i]
                                            ->GetGUID()
                                            .GetCounter());
                            }
                            verifiedBots += "]";

                            // Build cooldown key
                            std::string cooldownKey = "transport:" + std::to_string(entry) +
                                                     ":zone:" + std::to_string(currentZone);

                            // Build extra data JSON
                            // NOTE: extraData is inserted
                            // into SQL via fmt::format;
                            // relies on JsonEscape for
                            // single-quote safety
                            // (see JsonEscape comment)
                            std::string extraData = "{"
                                "\"transport_entry\":" + std::to_string(entry) + ","
                                "\"transport_name\":\"" + JsonEscape(info.fullName) + "\","
                                "\"destination\":\"" + JsonEscape(info.destination) + "\","
                                "\"transport_type\":\"" + JsonEscape(info.transportType) + "\","
                                "\"verified_bots\":" + verifiedBots +
                                "}";

                            QueueEvent(
                                "transport_arrives",
                                "zone",
                                currentZone,
                                mapId,
                                6,  // priority
                                cooldownKey,
                                sLLMChatterConfig->_transportCooldownSeconds,  // per transport+zone cooldown
                                0, "",  // no subject
                                0, info.fullName, entry,  // target info
                                extraData
                            );

                        }
                        else
                        {
                        }
                    }
                }

                // Update tracking
                _transportZones[guid] = {currentZone, mapId};
            }
        });
    }

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

    // Get faction (0 = Alliance, 1 = Horde)
    uint32 GetFaction(Player* player)
    {
        return player->GetTeamId();  // TEAM_ALLIANCE = 0, TEAM_HORDE = 1
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

        // Get all playerbots from RandomPlayerbotMgr
        PlayerBotMap allBots = sRandomPlayerbotMgr.GetAllBots();

        for (auto const& pair : allBots)
        {
            Player* player = pair.second;
            if (!player)
                continue;

            // Check if bot is fully loaded
            WorldSession* session = player->GetSession();
            if (session && session->PlayerLoading())
                continue;

            if (player->IsInWorld() && player->IsAlive())
            {
                if (player->GetZoneId() == zoneId)
                {
                    if (GetFaction(player) == faction)
                    {
                        // Only include bots NOT grouped with real players
                        if (!IsGroupedWithRealPlayer(player))
                        {
                            bots.push_back(player);
                        }
                    }
                }
            }
        }

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
            WorldSession* session = pair.second;
            if (!session)
                continue;

            // Check if session is still loading a player
            if (session->PlayerLoading())
                continue;

            Player* player = session->GetPlayer();
            if (!player)
                continue;

            // Skip players not fully in world
            if (!player->IsInWorld())
                continue;

            if (!IsPlayerBot(player) && player->GetZoneId() == zoneId)
            {
                if (GetFaction(player) == TEAM_ALLIANCE)
                    allianceCount++;
                else
                    hordeCount++;
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
        // Find zones with real players
        std::vector<uint32> validZones =
            GetZonesWithRealPlayers();
        if (validZones.empty())
            return;

        // Check pending requests (once, before
        // per-zone loop)
        QueryResult countResult =
            CharacterDatabase.Query(
                "SELECT COUNT(*) FROM "
                "llm_chatter_queue "
                "WHERE status IN "
                "('pending', 'processing')");

        if (countResult)
        {
            uint32 pending =
                countResult->Fetch()[0]
                    .Get<uint32>();
            if (pending >= sLLMChatterConfig
                               ->_maxPendingRequests)
            {
                LOG_DEBUG("module",
                    "LLMChatter: Max pending "
                    "requests reached ({})",
                    pending);
                return;
            }
        }

        // Per-zone triggering: each zone with a
        // real player gets an independent roll.
        // Cities get a boosted chance.
        std::random_device rd;
        std::mt19937 g(rd());

        for (uint32 selectedZone : validZones)
        {
            uint32 triggerChance =
                sLLMChatterConfig->_triggerChance;
            if (IsCapitalCity(selectedZone))
            {
                triggerChance = std::min(
                    triggerChance
                        * sLLMChatterConfig
                            ->_cityChatterMultiplier,
                    100u);
            }

            if (urand(1, 100) > triggerChance)
                continue;

            std::string zoneName =
                GetZoneName(selectedZone);
            uint32 faction =
                GetDominantFactionInZone(
                    selectedZone);

            std::vector<Player*> bots =
                GetBotsInZone(selectedZone, faction);

            // Filter to bots that can actually
            // speak in General channel
            bots.erase(
                std::remove_if(
                    bots.begin(), bots.end(),
                    [](Player* b) {
                        return !CanSpeakInGeneralChannel(b);
                    }),
                bots.end());

            bool isConversation =
                (urand(1, 100)
                 <= sLLMChatterConfig
                        ->_conversationChance);

            uint32 requiredBots =
                isConversation ? 2 : 1;
            if (bots.size() < requiredBots)
            {
                if (isConversation
                    && bots.size() >= 1)
                    isConversation = false;
                else
                    continue;
            }

            std::shuffle(
                bots.begin(), bots.end(), g);

            uint32 botCount = 1;
            if (isConversation)
            {
                uint32 maxBots = std::min(
                    static_cast<uint32>(
                        bots.size()), 4u);
                uint32 roll = urand(1, 100);
                if (roll <= 50 || maxBots == 2)
                    botCount = 2;
                else if (roll <= 80
                         || maxBots == 3)
                    botCount =
                        std::min(3u, maxBots);
                else
                    botCount = maxBots;
            }

            Player* bot1 = bots[0];
            Player* bot2 =
                (botCount >= 2)
                    ? bots[1] : nullptr;
            Player* bot3 =
                (botCount >= 3)
                    ? bots[2] : nullptr;
            Player* bot4 =
                (botCount >= 4)
                    ? bots[3] : nullptr;

            QueueChatterRequest(
                bot1, bot2, bot3, bot4,
                botCount, isConversation,
                zoneName, selectedZone);
        }
    }

    void QueueChatterRequest(Player* bot1, Player* bot2, Player* bot3, Player* bot4,
                             uint32 botCount, bool isConversation, const std::string& zoneName, uint32 zoneId)
    {
        std::string requestType = isConversation ? "conversation" : "statement";
        std::string bot1Name = bot1->GetName();
        std::string bot1Class = GetClassName(bot1->getClass());
        std::string bot1Race = GetRaceName(bot1->getRace());
        uint8 bot1Level = bot1->GetLevel();

        // Escape zone name for SQL
        std::string escapedZoneName =
            EscapeString(zoneName);

        // Get current weather for this zone
        std::string currentWeather = "clear";
        auto weatherIt = _zoneWeatherState.find(zoneId);
        if (weatherIt != _zoneWeatherState.end())
        {
            currentWeather = GetWeatherStateName(weatherIt->second);
        }

        if (isConversation && bot2)
        {
            std::string bot2Name = bot2->GetName();
            std::string bot2Class = GetClassName(bot2->getClass());
            std::string bot2Race = GetRaceName(bot2->getRace());
            uint8 bot2Level = bot2->GetLevel();

            // Build the SQL dynamically based on how many bots we have
            std::string columns = "request_type, bot1_guid, bot1_name, bot1_class, bot1_race, bot1_level, bot1_zone, zone_id, weather, bot_count, "
                                  "bot2_guid, bot2_name, bot2_class, bot2_race, bot2_level";
            std::string values = fmt::format(
                "'{}', {}, '{}', '{}', '{}', {}, "
                "'{}', {}, '{}', {}, "
                "{}, '{}', '{}', '{}', {}",
                requestType,
                bot1->GetGUID().GetCounter(),
                EscapeString(bot1Name),
                bot1Class, bot1Race, bot1Level,
                escapedZoneName, zoneId,
                currentWeather, botCount,
                bot2->GetGUID().GetCounter(),
                EscapeString(bot2Name),
                bot2Class, bot2Race, bot2Level);

            // Add bot3 if present
            if (bot3)
            {
                std::string bot3Name = bot3->GetName();
                std::string bot3Class = GetClassName(bot3->getClass());
                std::string bot3Race = GetRaceName(bot3->getRace());
                uint8 bot3Level = bot3->GetLevel();
                columns += ", bot3_guid, bot3_name, bot3_class, bot3_race, bot3_level";
                values += fmt::format(
                    ", {}, '{}', '{}', '{}', {}",
                    bot3->GetGUID().GetCounter(),
                    EscapeString(bot3Name),
                    bot3Class, bot3Race,
                    bot3Level);
            }

            // Add bot4 if present
            if (bot4)
            {
                std::string bot4Name = bot4->GetName();
                std::string bot4Class = GetClassName(bot4->getClass());
                std::string bot4Race = GetRaceName(bot4->getRace());
                uint8 bot4Level = bot4->GetLevel();
                columns += ", bot4_guid, bot4_name, bot4_class, bot4_race, bot4_level";
                values += fmt::format(
                    ", {}, '{}', '{}', '{}', {}",
                    bot4->GetGUID().GetCounter(),
                    EscapeString(bot4Name),
                    bot4Class, bot4Race,
                    bot4Level);
            }

            columns += ", status";
            values += ", 'pending'";

            CharacterDatabase.Execute("INSERT INTO llm_chatter_queue ({}) VALUES ({})", columns, values);

            if (botCount == 2)
                LOG_INFO("module", "LLMChatter: Queued {}-bot conversation in {} between {} and {}",
                         botCount, zoneName, bot1Name, bot2Name);
            else if (botCount == 3)
                LOG_INFO("module", "LLMChatter: Queued {}-bot conversation in {} between {}, {}, and {}",
                         botCount, zoneName, bot1Name, bot2Name, bot3->GetName());
            else
                LOG_INFO("module", "LLMChatter: Queued {}-bot conversation in {} between {}, {}, {}, and {}",
                         botCount, zoneName, bot1Name, bot2Name, bot3->GetName(), bot4->GetName());
        }
        else
        {
            CharacterDatabase.Execute(
                "INSERT INTO llm_chatter_queue "
                "(request_type, bot1_guid, "
                "bot1_name, bot1_class, bot1_race, "
                "bot1_level, bot1_zone, zone_id, "
                "weather, bot_count, status) "
                "VALUES ('{}', {}, '{}', '{}', "
                "'{}', {}, '{}', {}, '{}', "
                "1, 'pending')",
                requestType,
                bot1->GetGUID().GetCounter(),
                EscapeString(bot1Name),
                bot1Class, bot1Race, bot1Level,
                escapedZoneName, zoneId,
                currentWeather);

            LOG_INFO("module", "LLMChatter: Queued statement in {} for {} ({} {}) [weather: {}]",
                     zoneName, bot1Name, bot1Race, bot1Class, currentWeather);
        }
    }

    void DeliverPendingMessages()
    {
        // Find messages ready for delivery.
        // Expire messages stuck undelivered for
        // over 60s to prevent queue starvation.
        CharacterDatabase.DirectExecute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 1, delivered_at = NOW() "
            "WHERE delivered = 0 "
            "AND deliver_at < DATE_SUB(NOW(), "
            "INTERVAL 60 SECOND)");

        QueryResult result = CharacterDatabase.Query(
            "SELECT id, bot_guid, bot_name, "
            "message, channel, emote "
            "FROM llm_chatter_messages "
            "WHERE delivered = 0 "
            "AND deliver_at <= NOW() "
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
            std::string channel =
                fields[4].Get<std::string>();
            std::string emoteName =
                fields[5].IsNull()
                    ? ""
                    : fields[5].Get<std::string>();

            // Find the bot player (supports both
            // random bots and account character bots)
            ObjectGuid guid =
                ObjectGuid::Create<HighGuid::Player>(
                    botGuid);
            Player* bot =
                ObjectAccessor::FindPlayer(guid);

            // Skip if bot is still loading
            if (bot)
            {
                WorldSession* session =
                    bot->GetSession();
                if (session
                    && session->PlayerLoading())
                    bot = nullptr;
            }

            // Always mark delivered (fail-fast).
            // Pre-check filter ensures bots can
            // speak in General at selection time.
            CharacterDatabase.DirectExecute(
                "UPDATE llm_chatter_messages "
                "SET delivered = 1, "
                "delivered_at = NOW() "
                "WHERE id = {}",
                messageId);

            if (bot && bot->IsInWorld())
            {
                // Send using PlayerbotAI
                if (PlayerbotAI* ai =
                        GET_PLAYERBOT_AI(bot))
                {
                    std::string processedMessage =
                        ConvertAllLinks(message);

                    bool sent = false;
                    if (channel == "party")
                    {
                        sent = ai->SayToParty(
                            processedMessage);
                    }
                    else
                    {
                        sent = ai->SayToChannel(
                            processedMessage,
                            ChatChannelId::
                                GENERAL);
                    }

                    if (!sent)
                    {
                        LOG_WARN("module",
                            "LLMChatter: "
                            "Delivery failed "
                            "for {} (msg {})",
                            botName,
                            messageId);
                    }

                    // Play emote animation if sent
                    if (sent
                        && !emoteName.empty())
                    {
                        uint32 textEmoteId =
                            GetTextEmoteId(emoteName);
                        if (textEmoteId)
                            SendBotTextEmote(
                                bot, textEmoteId);
                    }
                }
            }
            else
            {
                LOG_DEBUG("module",
                    "LLMChatter: Bot {} not found "
                    "or offline, skipping msg {}",
                    botName, messageId);
            }

        } while (result->NextRow());
    }
};

// ============================================================================
// GROUP SCRIPT - Group chatter when bots join real player groups
// ============================================================================

// Check if a group has at least one real (non-bot) player
static bool GroupHasRealPlayer(Group* group)
{
    if (!group)
        return false;

    for (GroupReference* itr = group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        if (Player* member = itr->GetSource())
        {
            if (!IsPlayerBot(member))
                return true;
        }
    }
    return false;
}

// Pick a random bot from the group, optionally
// excluding a specific player (e.g. the killer)
static Player* GetRandomBotInGroup(
    Group* group, Player* exclude = nullptr)
{
    if (!group)
        return nullptr;

    std::vector<Player*> bots;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (member && IsPlayerBot(member)
            && member != exclude
            && member->IsAlive())
            bots.push_back(member);
    }

    if (bots.empty())
        return nullptr;

    return bots[urand(0, bots.size() - 1)];
}

// Count bots in a group (for dynamic chance scaling)
static uint32 CountBotsInGroup(Group* group)
{
    if (!group)
        return 0;

    uint32 count = 0;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (member && IsPlayerBot(member))
            ++count;
    }
    return count;
}

// Queue a greeting event for a bot joining a group
// Bypasses QueueEvent() since greetings are mandatory
// (no reaction chance, no cooldowns)
static void QueueBotGreetingEvent(
    Player* bot, Group* group)
{
    if (!bot || !group)
        return;

    uint32 groupId = group->GetGUID().GetCounter();
    uint32 botGuid = bot->GetGUID().GetCounter();
    std::string botName = bot->GetName();

    // Get bot info for extra_data
    uint8 botClass = bot->getClass();
    uint8 botRace = bot->getRace();
    uint8 botLevel = bot->GetLevel();

    // Find real player name and count group members
    std::string playerName;
    uint32 groupSize = 0;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        if (Player* member = itr->GetSource())
        {
            ++groupSize;
            if (!IsPlayerBot(member)
                && playerName.empty())
                playerName = member->GetName();
        }
    }

    // Detect bot role for Python trait storage
    std::string role = "dps";
    PlayerbotAI* botAi = GET_PLAYERBOT_AI(bot);
    if (botAi)
    {
        if (PlayerbotAI::IsTank(bot))
            role = "tank";
        else if (PlayerbotAI::IsHeal(bot))
            role = "healer";
        else if (PlayerbotAI::IsRanged(bot))
            role = "ranged_dps";
        else
            role = "melee_dps";
    }

    // Build extra_data JSON
    // NOTE: extraData is inserted into SQL via
    // fmt::format; relies on JsonEscape for
    // single-quote safety (see JsonEscape comment)
    std::string extraData = "{"
        "\"bot_guid\":" + std::to_string(botGuid) + ","
        "\"bot_name\":\"" + JsonEscape(botName) + "\","
        "\"bot_class\":" + std::to_string(botClass) + ","
        "\"bot_race\":" + std::to_string(botRace) + ","
        "\"bot_level\":" + std::to_string(botLevel) + ","
        "\"role\":\"" + role + "\","
        "\"group_id\":" + std::to_string(groupId) + ","
        "\"player_name\":\"" +
            JsonEscape(playerName) + "\","
        "\"group_size\":" +
            std::to_string(groupSize) +
        "}";

    // SQL-escape the whole JSON blob so
    // apostrophes in names don't break the
    // INSERT (JsonEscape handles JSON + SQL
    // inside values, this covers the wrapper)
    extraData = EscapeString(extraData);

    // Direct INSERT - bypass QueueEvent to skip
    // reaction chance and cooldown checks
    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_events "
        "(event_type, event_scope, zone_id, map_id, "
        "priority, cooldown_key, "
        "subject_guid, subject_name, "
        "target_guid, target_name, target_entry, "
        "extra_data, status, react_after, expires_at) "
        "VALUES ('bot_group_join', 'player', "
        "{}, {}, 0, '', "
        "{}, '{}', 0, '', 0, "
        "'{}', 'pending', "
        "DATE_ADD(NOW(), INTERVAL 3 SECOND), "
        "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
        bot->GetZoneId(),
        bot->GetMapId(),
        botGuid, EscapeString(botName),
        extraData);

    LOG_INFO("module",
        "LLMChatter: Queued bot_group_join for {} "
        "(group {})",
        botName, groupId);
}

// Per-zone General channel cooldown: zone_id -> last reaction time
static std::map<uint32, time_t> _generalChatCooldowns;

// Per-group kill cooldown cache: group_id -> last kill event time
static std::map<uint32, time_t> _groupKillCooldowns;

// Per-group death cooldown cache: group_id -> last death event time
static std::map<uint32, time_t> _groupDeathCooldowns;

// Per-group loot cooldown cache: group_id -> last loot event time
static std::map<uint32, time_t> _groupLootCooldowns;

// Per-group player message response cooldown
static std::map<uint32, time_t> _groupPlayerMsgCooldowns;

// Per-group combat engage cooldown
static std::map<uint32, time_t> _groupCombatCooldowns;

// Per-group spell cast cooldown: group_id -> last spell event time
static std::unordered_map<uint32, time_t>
    _groupSpellCooldowns;

// Per-group quest objectives cooldown:
// group_id -> last quest objectives event time
static std::map<uint32, time_t>
    _groupQuestObjCooldowns;

// Per-group resurrect cooldown:
// group_id -> last resurrect event time
static std::map<uint32, time_t>
    _groupResurrectCooldowns;

// Per-group zone transition cooldown:
// group_id -> last zone change event time
static std::map<uint32, time_t>
    _groupZoneCooldowns;

// Per-group+quest accept timestamp:
// (groupId << 32 | questId) -> accept time
// Used to suppress duplicate objectives events
// for travel/breadcrumb quests
static std::unordered_map<uint64, time_t>
    _questAcceptTimestamps;

// Per-group dungeon entry cooldown:
// group_id -> last dungeon entry event time
static std::map<uint32, time_t>
    _groupDungeonCooldowns;

// Per-group wipe cooldown:
// group_id -> last wipe event time
static std::map<uint32, time_t>
    _groupWipeCooldowns;

// Per-group corpse run cooldown:
// group_id -> last corpse run event time
static std::map<uint32, time_t>
    _groupCorpseRunCooldowns;

// Per-group+area discovery cooldown:
// (groupId << 32) | areaId -> last discover time
static std::map<uint64, time_t>
    _groupDiscoveryCooldowns;

// Per-bot state callout cooldowns:
// bot_guid -> last callout time
static std::map<uint32, time_t>
    _botLowHealthCooldowns;
static std::map<uint32, time_t>
    _botOomCooldowns;
static std::map<uint32, time_t>
    _botAggroCooldowns;

// Clean up traits when group no longer qualifies
static void CleanupGroupSession(uint32 groupId)
{
    CharacterDatabase.Execute(
        "DELETE FROM llm_group_bot_traits "
        "WHERE group_id = {}",
        groupId);
    CharacterDatabase.Execute(
        "DELETE FROM llm_group_chat_history "
        "WHERE group_id = {}",
        groupId);
    CharacterDatabase.Execute(
        "DELETE FROM llm_group_cached_responses "
        "WHERE group_id = {}",
        groupId);

    // Prune in-memory cooldown maps for this group
    _groupKillCooldowns.erase(groupId);
    _groupDeathCooldowns.erase(groupId);
    _groupLootCooldowns.erase(groupId);
    _groupPlayerMsgCooldowns.erase(groupId);
    _groupCombatCooldowns.erase(groupId);
    _groupSpellCooldowns.erase(groupId);
    _groupQuestObjCooldowns.erase(groupId);
    _groupResurrectCooldowns.erase(groupId);
    _groupZoneCooldowns.erase(groupId);
    _groupDungeonCooldowns.erase(groupId);
    _groupWipeCooldowns.erase(groupId);
    _groupCorpseRunCooldowns.erase(groupId);

    // Discovery cooldowns use composite key
    // (groupId << 32 | areaId); erase all matching
    uint64 lo =
        (uint64)groupId << 32;
    uint64 hi = lo | 0xFFFFFFFF;
    auto itD = _groupDiscoveryCooldowns.lower_bound(lo);
    while (itD != _groupDiscoveryCooldowns.end()
           && itD->first <= hi)
        itD = _groupDiscoveryCooldowns.erase(itD);

    LOG_INFO("module",
        "LLMChatter: Cleaned up group {} "
        "(traits + chat history + cooldowns)",
        groupId);
}

class LLMChatterGroupScript : public GroupScript
{
public:
    LLMChatterGroupScript()
        : GroupScript("LLMChatterGroupScript") {}

    void OnAddMember(
        Group* group, ObjectGuid guid) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        // Find the player who just joined
        Player* player =
            ObjectAccessor::FindPlayer(guid);
        if (!player)
            return;

        // Only trigger for bots joining a group
        // that has a real player
        if (!IsPlayerBot(player))
            return;

        if (!GroupHasRealPlayer(group))
            return;

        QueueBotGreetingEvent(player, group);
    }

    void OnRemoveMember(
        Group* group, ObjectGuid guid,
        RemoveMethod /*method*/, ObjectGuid /*kicker*/,
        const char* /*reason*/) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!group)
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Always clean up the removed bot's data
        if (guid)
        {
            uint32 botGuid =
                guid.GetCounter();

            // Cache cleanup uses only guid —
            // safe even if Player* is gone
            CharacterDatabase.Execute(
                "DELETE FROM "
                "llm_group_cached_responses "
                "WHERE group_id = {} "
                "AND bot_guid = {}",
                groupId, botGuid);

            Player* removed =
                ObjectAccessor::FindPlayer(guid);
            if (removed && IsPlayerBot(removed))
            {
                // Send farewell message before cleanup
                if (sLLMChatterConfig->_useFarewell)
                {
                QueryResult farewell =
                    CharacterDatabase.Query(
                        "SELECT farewell_msg "
                        "FROM llm_group_bot_traits "
                        "WHERE group_id = {} "
                        "AND bot_guid = {}",
                        groupId, botGuid);
                if (farewell)
                {
                    std::string farewellMsg =
                        farewell->Fetch()[0]
                            .Get<std::string>();
                    if (!farewellMsg.empty())
                    {
                        // Build party chat packet
                        // from leaving bot
                        WorldPacket data;
                        ChatHandler::BuildChatPacket(
                            data,
                            CHAT_MSG_PARTY,
                            LANG_UNIVERSAL,
                            removed,
                            nullptr,
                            farewellMsg);

                        // Send to remaining members
                        for (GroupReference* itr =
                                 group->GetFirstMember();
                             itr != nullptr;
                             itr = itr->next())
                        {
                            Player* member =
                                itr->GetSource();
                            if (member
                                && member != removed
                                && member->GetSession())
                            {
                                member
                                    ->GetSession()
                                    ->SendPacket(
                                        &data);
                            }
                        }
                        LOG_INFO("module",
                            "LLMChatter: Farewell "
                            "from bot {} (group {})"
                            ": {}",
                            botGuid, groupId,
                            farewellMsg);
                    }
                }
                } // _useFarewell

                CharacterDatabase.Execute(
                    "DELETE FROM llm_group_bot_traits "
                    "WHERE group_id = {} "
                    "AND bot_guid = {}",
                    groupId, botGuid);
                CharacterDatabase.Execute(
                    "DELETE FROM "
                    "llm_group_chat_history "
                    "WHERE group_id = {} "
                    "AND speaker_guid = {} "
                    "AND is_bot = 1",
                    groupId, botGuid);
                // Clear state callout cooldowns
                _botLowHealthCooldowns
                    .erase(botGuid);
                _botOomCooldowns
                    .erase(botGuid);
                _botAggroCooldowns
                    .erase(botGuid);

                LOG_INFO("module",
                    "LLMChatter: Cleaned "
                    "traits/history/cache for "
                    "removed bot {} (group {})",
                    botGuid, groupId);
            }
        }

        // If no real player remains, full cleanup
        if (!GroupHasRealPlayer(group))
        {
            CleanupGroupSession(groupId);
        }
    }

    void OnDisband(Group* group) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!group)
            return;

        CleanupGroupSession(
            group->GetGUID().GetCounter());
    }
};

// ============================================================================
// PLAYER SCRIPT - Combat events for grouped bots
// ============================================================================

class LLMChatterPlayerScript : public PlayerScript
{
public:
    LLMChatterPlayerScript()
        : PlayerScript("LLMChatterPlayerScript") {}

    // ------------------------------------------------
    // General channel: player message reaction
    // ------------------------------------------------
    bool OnPlayerCanUseChat(
        Player* player, uint32 /*type*/,
        uint32 /*language*/, std::string& msg,
        Channel* channel) override
    {
        // Always allow chat - we just observe
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGeneralChatReact)
            return true;

        // Only General channel (channelId 1)
        if (!channel || channel->GetChannelId() != 1)
            return true;

        // Skip bots
        if (!player || IsPlayerBot(player))
            return true;

        if (msg.empty())
            return true;

        // Filter ALL_CAPS_WITH_UNDERSCORES (addons)
        {
            bool hasUnderscore = false;
            bool allCapsOrSep = true;
            for (char c : msg)
            {
                if (c == '_')
                    hasUnderscore = true;
                else if (c != ' ' && c != '\t'
                    && c != '\n' && c != '\r'
                    && !(c >= 'A' && c <= 'Z'))
                {
                    allCapsOrSep = false;
                    break;
                }
            }
            if (hasUnderscore && allCapsOrSep)
                return true;
        }

        // Skip link-only messages
        if (msg.size() > 2 && msg[0] == '|'
            && msg[1] == 'c')
        {
            std::string stripped = msg;
            size_t start, end;
            while ((start = stripped.find("|c"))
                   != std::string::npos
                && (end = stripped.find("|r", start))
                   != std::string::npos)
            {
                stripped.erase(start,
                    end - start + 2);
            }
            stripped.erase(0,
                stripped.find_first_not_of(" \t"));
            if (!stripped.empty())
            {
                stripped.erase(
                    stripped.find_last_not_of(
                        " \t") + 1);
            }
            if (stripped.empty())
                return true;
        }

        // Trim and truncate message
        std::string safeMsg = msg;
        size_t firstChar =
            safeMsg.find_first_not_of(" \t\n\r");
        if (firstChar == std::string::npos)
            return true;
        if (firstChar > 0)
            safeMsg = safeMsg.substr(firstChar);
        size_t lastChar =
            safeMsg.find_last_not_of(" \t\n\r");
        if (lastChar != std::string::npos)
            safeMsg =
                safeMsg.substr(0, lastChar + 1);
        if (safeMsg.empty())
            return true;
        if (safeMsg.size()
            > sLLMChatterConfig->_maxMessageLength)
            safeMsg = safeMsg.substr(
                0,
                sLLMChatterConfig->_maxMessageLength);

        uint32 zoneId = player->GetZoneId();
        std::string playerName = player->GetName();

        // Store in General chat history
        CharacterDatabase.Execute(
            "INSERT INTO llm_general_chat_history "
            "(zone_id, speaker_name, is_bot, message)"
            " VALUES ({}, '{}', 0, '{}')",
            zoneId,
            EscapeString(playerName),
            EscapeString(safeMsg));

        // Prune history per zone
        CharacterDatabase.Execute(
            "DELETE FROM llm_general_chat_history "
            "WHERE zone_id = {} AND id NOT IN "
            "(SELECT id FROM (SELECT id FROM "
            "llm_general_chat_history "
            "WHERE zone_id = {} "
            "ORDER BY id DESC LIMIT "
            + std::to_string(
                sLLMChatterConfig
                    ->_generalChatHistoryLimit)
            + ") AS keep)",
            zoneId, zoneId);

        // Per-zone cooldown
        time_t now = time(nullptr);
        auto it =
            _generalChatCooldowns.find(zoneId);
        if (it != _generalChatCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_generalChatCooldown)
            return true;

        // RNG: questions get higher chance
        bool isQuestion =
            !safeMsg.empty()
            && safeMsg.back() == '?';
        uint32 chance = isQuestion
            ? sLLMChatterConfig
                ->_generalChatQuestionChance
            : sLLMChatterConfig
                ->_generalChatChance;
        if (urand(1, 100) > chance)
            return true;

        _generalChatCooldowns[zoneId] = now;

        // Get zone name
        AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(zoneId);
        std::string zoneName =
            area ? area->area_name[0] : "Unknown";

        // Collect candidate bots in this zone.
        // Account bots first (player's own bots
        // are more relevant), then fill remaining
        // slots with random bots.
        std::vector<Player*> zoneBots;
        zoneBots.reserve(8);

        // 1) Account bots via sessions (priority)
        {
            WorldSessionMgr::SessionMap const&
                sessions =
                sWorldSessionMgr
                    ->GetAllSessions();
            for (auto const& pair : sessions)
            {
                WorldSession* session = pair.second;
                if (!session)
                    continue;
                Player* p = session->GetPlayer();
                if (!p || !p->IsInWorld())
                    continue;
                if (!IsPlayerBot(p))
                    continue;
                if (p->GetZoneId() != zoneId)
                    continue;
                zoneBots.push_back(p);
                if (zoneBots.size()
                    >= sLLMChatterConfig
                        ->_maxBotsPerZone)
                    break;
            }
        }

        // 2) Random bots fill remaining slots
        if (zoneBots.size()
            < sLLMChatterConfig->_maxBotsPerZone)
        {
            auto allBots =
                sRandomPlayerbotMgr.GetAllBots();
            for (auto& pair : allBots)
            {
                Player* bot = pair.second;
                if (!bot || !bot->IsInWorld())
                    continue;
                if (bot->GetZoneId() != zoneId)
                    continue;
                // Avoid duplicates with account bots
                bool found = false;
                for (Player* b : zoneBots)
                {
                    if (b->GetGUID()
                        == bot->GetGUID())
                    {
                        found = true;
                        break;
                    }
                }
                if (!found)
                {
                    zoneBots.push_back(bot);
                    if (zoneBots.size()
                        >= sLLMChatterConfig
                            ->_maxBotsPerZone)
                        break;
                }
            }
        }

        // Filter to bots that can actually
        // speak in General channel
        zoneBots.erase(
            std::remove_if(
                zoneBots.begin(), zoneBots.end(),
                [](Player* b) {
                    return !CanSpeakInGeneralChannel(b);
                }),
            zoneBots.end());

        if (zoneBots.empty())
            return true;

        // Shuffle and send all found bots — Python
        // decides how many to use (1 for statement,
        // 2 for conversation)
        std::shuffle(
            zoneBots.begin(), zoneBots.end(),
            std::mt19937{std::random_device{}()});
        uint32 pickCount = zoneBots.size();

        // Build JSON arrays of bot info
        std::string botGuids = "[";
        std::string botNames = "[";
        for (uint32 i = 0; i < pickCount; ++i)
        {
            Player* bot = zoneBots[i];
            if (i > 0)
            {
                botGuids += ",";
                botNames += ",";
            }
            botGuids +=
                std::to_string(
                    bot->GetGUID().GetCounter());
            botNames += "\"" +
                JsonEscape(bot->GetName()) + "\"";
        }
        botGuids += "]";
        botNames += "]";

        std::string extraData = "{"
            "\"player_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"player_message\":\"" +
                JsonEscape(safeMsg) + "\","
            "\"zone_id\":" +
                std::to_string(zoneId) + ","
            "\"zone_name\":\"" +
                JsonEscape(zoneName) + "\","
            "\"bot_guids\":" + botGuids + ","
            "\"bot_names\":" + botNames +
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('player_general_msg', "
            "'zone', "
            "{}, {}, 8, 'general_chat:{}', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 5 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
            zoneId,
            player->GetMapId(),
            zoneId,
            player->GetGUID().GetCounter(),
            EscapeString(playerName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued player_general_msg "
            "from {} in zone {} ({} bots)",
            playerName, zoneName, pickCount);

        return true;
    }

    // ------------------------------------------------
    // Creature Kill event (group chatter)
    // ------------------------------------------------
    void OnPlayerCreatureKill(
        Player* killer, Creature* killed) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!killer || !killed)
            return;

        Group* group = killer->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        // Pick a bot to react: use killer if bot,
        // otherwise pick a random bot from group
        Player* reactor = nullptr;
        if (IsPlayerBot(killer))
            reactor = killer;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
            return;

        // Ranks: 0=Normal, 1=Elite, 2=Rare Elite,
        //        3=Boss, 4=Rare
        CreatureTemplate const* tmpl =
            killed->GetCreatureTemplate();
        if (!tmpl)
            return;

        uint32 rank = tmpl->rank;
        bool isBoss = (rank == 3)
            || (tmpl->type_flags
                & CREATURE_TYPE_FLAG_BOSS_MOB);
        bool isRare = (rank == 2 || rank == 4);
        bool isNormal = !isBoss && !isRare;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown: boss/rare bypass,
        // normal uses config cooldown
        time_t now = time(nullptr);
        if (isNormal)
        {
            auto it =
                _groupKillCooldowns.find(groupId);
            if (it != _groupKillCooldowns.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_groupKillCooldown)
                return;
        }

        // RNG: boss/rare = 100%, normal = config%
        if (isNormal && urand(1, 100)
            > sLLMChatterConfig
                ->_groupKillChanceNormal)
            return;

        _groupKillCooldowns[groupId] = now;

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string creatureName = killed->GetName();
        uint32 creatureEntry = killed->GetEntry();

        // Build extra_data JSON
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"creature_name\":\"" +
                JsonEscape(creatureName) + "\","
            "\"creature_entry\":" +
                std::to_string(creatureEntry) + ","
            "\"is_boss\":" +
                std::string(
                    isBoss ? "true" : "false") + ","
            "\"is_rare\":" +
                std::string(
                    isRare ? "true" : "false") + ","
            "\"is_normal\":" +
                std::string(
                    isNormal ? "true" : "false") + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            + BuildBotStateJson(reactor) + "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        // Direct INSERT with short react_after
        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_kill', 'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(creatureName),
            creatureEntry,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_kill "
            "for {} killing {}",
            botName, creatureName);
    }

    void OnPlayerKilledByCreature(
        Creature* killer, Player* killed) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!killed)
            return;

        Group* group = killed->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();
        time_t now = time(nullptr);

        // === Wipe detection (checked BEFORE death
        // cooldown/RNG so wipes aren't suppressed
        // by individual death filters) ===
        {
            bool allDead = true;
            uint32 memberCount = 0;
            for (GroupReference* itr =
                     group->GetFirstMember();
                 itr != nullptr;
                 itr = itr->next())
            {
                Player* member =
                    itr->GetSource();
                if (!member)
                    continue;
                memberCount++;
                if (member->IsAlive())
                {
                    allDead = false;
                    break;
                }
            }

            // Need at least 2 members
            // for a "wipe"
            if (allDead && memberCount >= 2)
            {
                // Check wipe-specific cooldown
                auto wit =
                    _groupWipeCooldowns
                        .find(groupId);
                if (wit
                    != _groupWipeCooldowns.end()
                    && (now - wit->second)
                       < (time_t)
                           sLLMChatterConfig
                               ->_groupWipeCooldown)
                {
                    // Wipe on cooldown, also
                    // skip normal death
                    return;
                }

                // RNG chance from config
                if (urand(1, 100)
                    > sLLMChatterConfig
                        ->_groupWipeChance)
                    return;

                _groupWipeCooldowns[groupId] =
                    now;

                // Pick a random bot to react
                Player* wipeReactor =
                    GetRandomBotInGroup(group);
                if (!wipeReactor)
                    return;

                uint32 wrGuid =
                    wipeReactor->GetGUID()
                        .GetCounter();
                std::string wrName =
                    wipeReactor->GetName();
                std::string kName =
                    killer
                        ? killer->GetName()
                        : "";
                uint32 kEntry =
                    killer
                        ? killer->GetEntry()
                        : 0;

                std::string wipeData = "{"
                    "\"bot_guid\":" +
                        std::to_string(
                            wrGuid) + ","
                    "\"bot_name\":\"" +
                        JsonEscape(
                            wrName) + "\","
                    "\"bot_class\":" +
                        std::to_string(
                            wipeReactor
                                ->getClass())
                        + ","
                    "\"bot_race\":" +
                        std::to_string(
                            wipeReactor
                                ->getRace())
                        + ","
                    "\"bot_level\":" +
                        std::to_string(
                            wipeReactor
                                ->GetLevel())
                        + ","
                    "\"group_id\":" +
                        std::to_string(
                            groupId) + ","
                    "\"killer_name\":\"" +
                        JsonEscape(
                            kName) + "\","
                    "\"killer_entry\":" +
                        std::to_string(
                            kEntry) + ","
                    + BuildBotStateJson(wipeReactor)
                    + "}";

                wipeData =
                    EscapeString(wipeData);

                CharacterDatabase.Execute(
                    "INSERT INTO "
                    "llm_chatter_events "
                    "(event_type, event_scope, "
                    "zone_id, map_id, priority, "
                    "cooldown_key, "
                    "subject_guid, "
                    "subject_name, "
                    "target_guid, "
                    "target_name, "
                    "target_entry, "
                    "extra_data, status, "
                    "react_after, expires_at) "
                    "VALUES ("
                    "'bot_group_wipe', "
                    "'player', "
                    "{}, {}, 1, '', "
                    "{}, '{}', 0, '{}', {}, "
                    "'{}', 'pending', "
                    "DATE_ADD(NOW(), "
                    "INTERVAL 3 SECOND), "
                    "DATE_ADD(NOW(), "
                    "INTERVAL 120 SECOND))",
                    killed->GetZoneId(),
                    killed->GetMapId(),
                    wrGuid,
                    EscapeString(wrName),
                    EscapeString(kName),
                    kEntry,
                    wipeData);

                LOG_INFO("module",
                    "LLMChatter: GROUP WIPE "
                    "detected! {} reacting "
                    "(killed by {})",
                    wrName, kName);

                // Skip normal death event
                return;
            }
        }

        // --- Normal death reaction (not a wipe) ---
        // Per-group cooldown
        auto it = _groupDeathCooldowns.find(groupId);
        if (it != _groupDeathCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupDeathCooldown)
            return;

        // RNG: config% chance to react to a death
        if (urand(1, 100)
            > sLLMChatterConfig->_groupDeathChance)
            return;

        _groupDeathCooldowns[groupId] = now;

        // Pick a living bot to react
        // (exclude dead player)
        Player* reactor = GetRandomBotInGroup(
            group, killed);
        if (!reactor)
            return;

        uint32 reactorGuid =
            reactor->GetGUID().GetCounter();
        std::string reactorName =
            reactor->GetName();

        bool isPlayerDeath =
            !IsPlayerBot(killed);
        uint32 deadGuid =
            killed->GetGUID().GetCounter();
        std::string deadName =
            killed->GetName();
        std::string killerName =
            killer ? killer->GetName() : "";
        uint32 killerEntry =
            killer ? killer->GetEntry() : 0;

        // Build extra_data JSON
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(reactorGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(reactorName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"dead_name\":\"" +
                JsonEscape(deadName) + "\","
            "\"dead_guid\":" +
                std::to_string(deadGuid) + ","
            "\"killer_name\":\"" +
                JsonEscape(killerName) + "\","
            "\"killer_entry\":" +
                std::to_string(killerEntry) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"is_player_death\":" +
                std::string(
                    isPlayerDeath
                        ? "true" : "false") + ","
            + BuildBotStateJson(reactor) + "}";

        extraData = EscapeString(extraData);

        // Direct INSERT with short react_after
        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_death', 'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
            killed->GetZoneId(),
            killed->GetMapId(),
            reactorGuid,
            EscapeString(reactorName),
            EscapeString(killerName),
            killerEntry,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_death "
            "for {} (reactor: {}) killed by {}{}",
            deadName, reactorName, killerName,
            isPlayerDeath
                ? " (player)" : "");
    }

    // Shared loot handler for both direct loot
    // and group roll rewards
    void HandleGroupLootEvent(
        Player* player, Item* item)
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!player)
            return;

        // Group check BEFORE any Item* access —
        // filters bot-only groups (main crash vector)
        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        bool isBot = IsPlayerBot(player);

        // Item* safety: The use-after-free crash
        // (Session 27b) only affected random bots in
        // bot-only groups, already filtered above by
        // GroupHasRealPlayer(). For bots in the
        // player's group, Item* is valid (StoreLootItem
        // just stored it, hook fires synchronously).
        // Null checks remain as extra safety.
        if (!item)
            return;
        ItemTemplate const* tmpl =
            item->GetTemplate();
        if (!tmpl)
            return;

        uint8 quality = tmpl->Quality;
        if (quality < 2)
            return;
        std::string itemName = tmpl->Name1;
        uint32 itemEntry = item->GetEntry();

        // Quality-based chance from config:
        // green/blue configurable, epic+=100%
        uint32 chance;
        if (quality == 2)
            chance = sLLMChatterConfig
                ->_groupLootChanceGreen;
        else if (quality == 3)
            chance = sLLMChatterConfig
                ->_groupLootChanceBlue;
        else
            chance = 100;

        if (urand(1, 100) > chance)
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group loot cooldown: config seconds
        // for green/blue, epic+ bypasses cooldown
        time_t now = time(nullptr);
        if (quality < 4)
        {
            auto it =
                _groupLootCooldowns.find(groupId);
            if (it != _groupLootCooldowns.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_groupLootCooldown)
                return;
        }

        _groupLootCooldowns[groupId] = now;

        std::string looterName = player->GetName();

        // Reactor selection: pick who comments
        // on the loot. 50% self, 50% other bot.
        // Real player loot always gets a bot reactor.
        Player* reactor = nullptr;
        if (!isBot)
        {
            reactor = GetRandomBotInGroup(group);
        }
        else if (urand(0, 1) == 0)
        {
            // Another bot comments on this loot
            reactor =
                GetRandomBotInGroup(group, player);
            if (!reactor)
                reactor = player; // fallback: self
        }
        else
        {
            reactor = player;
        }

        if (!reactor)
            return;

        uint32 reactorGuid =
            reactor->GetGUID().GetCounter();
        std::string reactorName = reactor->GetName();

        // Build extra_data JSON
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(reactorGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(reactorName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"is_bot\":1,"
            "\"looter_name\":\"" +
                JsonEscape(looterName) + "\","
            "\"item_name\":\"" +
                JsonEscape(itemName) + "\","
            "\"item_entry\":" +
                std::to_string(itemEntry) + ","
            "\"item_quality\":" +
                std::to_string(quality) + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "," + BuildBotStateJson(reactor)
            + "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_loot', 'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 3 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            reactorGuid, EscapeString(reactorName),
            EscapeString(itemName),
            itemEntry,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_loot "
            "for {} looting {} (quality={}, "
            "reactor={})",
            looterName, itemName, quality,
            reactorName);
    }

    void OnPlayerLootItem(
        Player* player, Item* item,
        uint32 /*count*/,
        ObjectGuid /*lootguid*/) override
    {
        HandleGroupLootEvent(player, item);
    }

    void OnPlayerGroupRollRewardItem(
        Player* player, Item* item,
        uint32 /*count*/,
        RollVote /*voteType*/,
        Roll* /*roll*/) override
    {
        HandleGroupLootEvent(player, item);
    }

    void OnPlayerEnterCombat(
        Player* player, Unit* enemy) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!player || !enemy)
            return;

        if (!IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        Creature* creature = enemy->ToCreature();
        if (!creature)
            return;

        CreatureTemplate const* tmpl =
            creature->GetCreatureTemplate();
        if (!tmpl)
            return;

        // Ranks: 0=Normal, 1=Elite, 2=Rare Elite,
        //        3=Boss, 4=Rare
        uint32 rank = tmpl->rank;
        bool isBoss = (rank == 3)
            || (tmpl->type_flags
                & CREATURE_TYPE_FLAG_BOSS_MOB);
        bool isElite = (rank >= 1);
        bool isNormal = !isBoss && !isElite;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown: normal uses config,
        // elite+ uses half
        time_t now = time(nullptr);
        uint32 cooldownSec = isNormal
            ? sLLMChatterConfig->_groupKillCooldown
            : sLLMChatterConfig->_groupKillCooldown
              / 2;
        auto it =
            _groupCombatCooldowns.find(groupId);
        if (it != _groupCombatCooldowns.end()
            && (now - it->second)
               < (time_t)cooldownSec)
            return;

        // RNG: Boss=100%, Elite/Rare=40%, Normal=15%
        uint32 chance;
        if (isBoss)
            chance = 100;
        else if (isElite)
            chance = 40;
        else
            chance = 15;
        if (urand(1, 100) > chance)
            return;

        _groupCombatCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName = player->GetName();
        std::string creatureName =
            creature->GetName();

        // --- Pre-cache instant delivery ---
        if (sLLMChatterConfig->_preCacheEnable
            && sLLMChatterConfig
                   ->_preCacheCombatEnable)
        {
            std::string cachedMsg, cachedEmote;
            if (TryConsumeCachedReaction(
                    groupId, botGuid,
                    "combat_pull",
                    cachedMsg, cachedEmote))
            {
                ResolvePlaceholders(
                    cachedMsg, creatureName,
                    "", "");
                SendPartyMessageInstant(
                    player, group,
                    cachedMsg, cachedEmote);
                RecordCachedChatHistory(
                    groupId, botGuid,
                    botName, cachedMsg);
                return;
            }
            if (!sLLMChatterConfig
                    ->_preCacheFallbackToLive)
                return;
        }

        // Build extra_data JSON
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"creature_name\":\"" +
                JsonEscape(creatureName) + "\","
            "\"creature_entry\":" +
                std::to_string(
                    creature->GetEntry()) + ","
            "\"is_boss\":" +
                std::string(
                    isBoss ? "1" : "0") + ","
            "\"is_elite\":" +
                std::string(
                    isElite ? "1" : "0") + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            + BuildBotStateJson(player) + "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_combat', "
            "'player', {}, {}, 2, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 1 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 30 SECOND))",
            player->GetZoneId(),
            player->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(creatureName),
            creature->GetEntry(),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_combat "
            "for {} vs {}",
            botName, creatureName);
    }

    void OnPlayerBeforeSendChatMessage(
        Player* player, uint32& type,
        uint32& /*lang*/,
        std::string& msg) override
    {
        if (type != CHAT_MSG_PARTY
            && type != CHAT_MSG_PARTY_LEADER)
            return;

        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!player || msg.empty())
            return;

        // Filter internal/addon messages
        // (ALL_CAPS_WITH_UNDERSCORES patterns)
        {
            bool hasUnderscore = false;
            bool allCapsOrSep = true;
            for (char c : msg)
            {
                if (c == '_')
                    hasUnderscore = true;
                else if (c != ' ' && c != '\t'
                    && c != '\n' && c != '\r'
                    && !(c >= 'A' && c <= 'Z'))
                {
                    allCapsOrSep = false;
                    break;
                }
            }
            if (hasUnderscore && allCapsOrSep)
                return;
        }

        // Skip link-only messages (no real text)
        if (msg.size() > 2 && msg[0] == '|'
            && msg[1] == 'c')
        {
            std::string stripped = msg;
            size_t start, end;
            while ((start = stripped.find("|c"))
                   != std::string::npos
                && (end = stripped.find("|r", start))
                   != std::string::npos)
            {
                stripped.erase(start,
                    end - start + 2);
            }
            stripped.erase(0,
                stripped.find_first_not_of(" \t"));
            if (!stripped.empty())
            {
                stripped.erase(
                    stripped.find_last_not_of(
                        " \t") + 1);
            }
            if (stripped.empty())
                return;
        }

        if (IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Must have at least one bot in group
        bool hasBotInGroup = false;
        for (GroupReference* itr =
                 group->GetFirstMember();
             itr != nullptr; itr = itr->next())
        {
            if (Player* member = itr->GetSource())
            {
                if (IsPlayerBot(member))
                {
                    hasBotInGroup = true;
                    break;
                }
            }
        }
        if (!hasBotInGroup)
            return;

        std::string playerName = player->GetName();
        uint32 playerGuid =
            player->GetGUID().GetCounter();

        // Trim and truncate message
        std::string safeMsg = msg;
        size_t firstChar = safeMsg.find_first_not_of(
            " \t\n\r");
        if (firstChar == std::string::npos)
            return;
        if (firstChar > 0)
            safeMsg = safeMsg.substr(firstChar);
        size_t lastChar = safeMsg.find_last_not_of(
            " \t\n\r");
        if (lastChar != std::string::npos)
            safeMsg = safeMsg.substr(0, lastChar + 1);
        if (safeMsg.empty())
            return;
        if (safeMsg.size()
            > sLLMChatterConfig->_maxMessageLength)
            safeMsg = safeMsg.substr(
                0,
                sLLMChatterConfig->_maxMessageLength);

        // Always store in chat history
        CharacterDatabase.Execute(
            "INSERT INTO llm_group_chat_history "
            "(group_id, speaker_guid, speaker_name,"
            " is_bot, message) "
            "VALUES ({}, {}, '{}', 0, '{}')",
            groupId, playerGuid,
            EscapeString(playerName),
            EscapeString(safeMsg));

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupPlayerMsgCooldowns.find(groupId);
        if (it != _groupPlayerMsgCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupPlayerMsgCooldown)
            return;

        _groupPlayerMsgCooldowns[groupId] = now;

        std::string extraData = "{"
            "\"player_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"player_message\":\"" +
                JsonEscape(safeMsg) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names/messages don't
        // break the INSERT
        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_player_msg', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 3 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 60 SECOND))",
            player->GetZoneId(),
            player->GetMapId(),
            player->GetGUID().GetCounter(),
            EscapeString(playerName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued player_msg "
            "from {} in group {}",
            playerName, groupId);
    }

    // ------------------------------------------------
    // Level Up event
    // ------------------------------------------------
    void OnPlayerLevelChanged(
        Player* player, uint8 oldLevel) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- config disabled");
            return;
        }

        if (!player)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- no player");
            return;
        }

        LOG_INFO("module",
            "LLMChatter: LevelChanged - entered "
            "for {} (old lvl {})",
            player->GetName(), oldLevel);

        Group* group = player->GetGroup();
        if (!group)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- no group for {}",
                player->GetName());
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- no real player in group");
            return;
        }

        // Must actually be gaining a level
        uint8 newLevel = player->GetLevel();
        if (newLevel <= oldLevel)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- level unchanged {} -> {}",
                oldLevel, newLevel);
            return;
        }

        bool isBot = IsPlayerBot(player);

        // Pick reactor: bot uses self, real player
        // picks a random bot from group to react
        Player* reactor = nullptr;
        if (isBot)
            reactor = player;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- no reactor bot for {}",
                player->GetName());
            return;
        }

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();

        // Build extra_data JSON
        // leveler_* = who leveled up
        // bot_* = who will react to it
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(newLevel) + ","
            "\"old_level\":" +
                std::to_string(oldLevel) + ","
            "\"is_bot\":" +
                std::string(
                    isBot ? "1" : "0") + ","
            "\"leveler_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT (JsonEscape handles JSON + SQL
        // inside values, this covers the wrapper)
        extraData = EscapeString(extraData);

        LOG_INFO("module",
            "LLMChatter: LevelChanged "
            "- queuing for {} (lvl {} -> {})",
            botName, oldLevel, newLevel);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_levelup', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_levelup "
            "for {} (lvl {} -> {})",
            botName, oldLevel, newLevel);
    }

    // ------------------------------------------------
    // Quest Objectives Complete event
    // (fires when all objectives are done,
    //  BEFORE the player turns in the quest)
    // ------------------------------------------------
    bool OnPlayerBeforeQuestComplete(
        Player* player, uint32 questId) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return true;

        if (!player)
            return true;

        // Player-centric: only react to the real
        // player's quest progress, not bot auto-
        // completes (avoids confusing messages)
        if (IsPlayerBot(player))
            return true;

        Group* group = player->GetGroup();
        if (!group)
            return true;

        if (!GroupHasRealPlayer(group))
            return true;

        // Get quest template for the name
        Quest const* quest =
            sObjectMgr->GetQuestTemplate(questId);
        if (!quest)
            return true;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown to avoid spam
        // from multiple objectives completing
        time_t now = time(nullptr);
        {
            auto it = _groupQuestObjCooldowns
                .find(groupId);
            if (it != _groupQuestObjCooldowns.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_groupQuestObjectiveCooldown)
                return true;
        }

        // Suppress if quest was just accepted
        // (travel/breadcrumb quests fire objectives
        // immediately after accept)
        uint64 questKey =
            ((uint64)groupId << 32) | questId;
        {
            auto it =
                _questAcceptTimestamps.find(questKey);
            if (it != _questAcceptTimestamps.end()
                && (now - it->second) < 10)
            {
                LOG_DEBUG("module",
                    "LLMChatter: QuestObjectives "
                    "- suppressed (quest just "
                    "accepted) [{}]",
                    quest->GetTitle());
                return true;
            }
        }

        _groupQuestObjCooldowns[groupId] = now;

        // RNG chance to avoid reacting
        // to every single quest objective
        if (urand(1, 100) >
            sLLMChatterConfig
                ->_groupQuestObjectiveChance)
            return true;

        bool isBot = IsPlayerBot(player);

        // Pick reactor: bot uses self, real player
        // picks a random bot from group to react
        Player* reactor = nullptr;
        if (isBot)
            reactor = player;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
            return true;

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();
        std::string questName = quest->GetTitle();

        // Build extra_data JSON
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"quest_name\":\"" +
                JsonEscape(questName) + "\","
            "\"quest_id\":" +
                std::to_string(questId) + ","
            "\"completer_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"quest_details\":\"" +
                JsonEscape(
                    quest->GetDetails()
                        .substr(0, 200)) + "\","
            "\"quest_objectives\":\"" +
                JsonEscape(
                    quest->GetObjectives()
                        .substr(0, 150)) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_quest_objectives', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(questName),
            questId,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_quest_objectives "
            "for {} completing objectives [{}]",
            botName, questName);

        return true;
    }

    // ------------------------------------------------
    // Quest Complete event
    // ------------------------------------------------
    void OnPlayerCompleteQuest(
        Player* player,
        Quest const* quest) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- config disabled");
            return;
        }

        if (!player || !quest)
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- no player or quest");
            return;
        }

        // Player-centric: only react to the real
        // player turning in quests
        if (IsPlayerBot(player))
            return;

        LOG_INFO("module",
            "LLMChatter: QuestComplete - entered "
            "for {} quest [{}] (id {})",
            player->GetName(),
            quest->GetTitle(),
            quest->GetQuestId());

        Group* group = player->GetGroup();
        if (!group)
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- no group for {}",
                player->GetName());
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- no real player in group");
            return;
        }

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 questId = quest->GetQuestId();

        // Per-group+quest dedup: only ONE reaction
        // per quest per group (all bots complete
        // the same quest within seconds).
        uint64 questKey =
            ((uint64)groupId << 32) | questId;
        time_t now = time(nullptr);
        {
            static std::unordered_map<
                uint64, time_t> _questCompleteCd;
            auto it = _questCompleteCd.find(questKey);
            if (it != _questCompleteCd.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_questDeduplicationWindow)
            {
                LOG_INFO("module",
                    "LLMChatter: QuestComplete "
                    "- dedup skip for {} [{}]",
                    player->GetName(),
                    quest->GetTitle());
                return;
            }
            _questCompleteCd[questKey] = now;
        }

        // Pick reactor: random bot from group
        Player* reactor =
            GetRandomBotInGroup(group);

        if (!reactor)
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- no reactor bot for {}",
                player->GetName());
            return;
        }

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();
        std::string questName =
            quest->GetTitle();

        // Build extra_data JSON
        // completer_* = who finished the quest
        // bot_* = who will react to it
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"is_bot\":1,"
            "\"completer_is_bot\":" +
                std::string(
                    IsPlayerBot(player)
                        ? "1" : "0") + ","
            "\"completer_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"quest_name\":\"" +
                JsonEscape(questName) + "\","
            "\"quest_id\":" +
                std::to_string(questId) + ","
            "\"quest_details\":\"" +
                JsonEscape(
                    quest->GetDetails()
                        .substr(0, 200)) + "\","
            "\"quest_objectives\":\"" +
                JsonEscape(
                    quest->GetObjectives()
                        .substr(0, 150)) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT (JsonEscape handles JSON + SQL
        // inside values, this covers the wrapper)
        extraData = EscapeString(extraData);

        LOG_INFO("module",
            "LLMChatter: QuestComplete "
            "- queuing [{}] (completer={}, "
            "reactor={})",
            questName, playerName, botName);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_quest_complete', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(questName),
            questId,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_quest_complete "
            "for {} completing [{}]",
            botName, questName);
    }

    // ------------------------------------------------
    // Achievement Complete event
    // ------------------------------------------------
    void OnPlayerAchievementComplete(
        Player* player,
        AchievementEntry const* achievement) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- config disabled");
            return;
        }

        if (!player || !achievement)
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- no player or achievement");
            return;
        }

        LOG_INFO("module",
            "LLMChatter: Achievement - entered "
            "for {} achievement [{}] (id {})",
            player->GetName(),
            achievement->name[0]
                ? achievement->name[0] : "?",
            achievement->ID);

        Group* group = player->GetGroup();
        if (!group)
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- no group for {}",
                player->GetName());
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- no real player in group");
            return;
        }

        bool isBot = IsPlayerBot(player);

        // Pick reactor: bot uses self, real player
        // picks a random bot from group to react
        Player* reactor = nullptr;
        if (isBot)
            reactor = player;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- no reactor bot for {}",
                player->GetName());
            return;
        }

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();

        // Achievement name is locale-indexed;
        // index 0 = English (enUS)
        std::string achName =
            achievement->name[0]
                ? achievement->name[0] : "";
        uint32 achId = achievement->ID;

        // Build extra_data JSON
        // achiever_* = who earned the achievement
        // bot_* = who will react to it
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"is_bot\":" +
                std::string(
                    isBot ? "1" : "0") + ","
            "\"achiever_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"achievement_name\":\"" +
                JsonEscape(achName) + "\","
            "\"achievement_id\":" +
                std::to_string(achId) + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT (JsonEscape handles JSON + SQL
        // inside values, this covers the wrapper)
        extraData = EscapeString(extraData);

        LOG_INFO("module",
            "LLMChatter: Achievement "
            "- queuing for {} earning [{}]",
            botName, achName);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_achievement', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(achName),
            achId,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_achievement "
            "for {} earning [{}]",
            botName, achName);
    }

    // ------------------------------------------------
    // Spell Cast event — heals, CC, resurrects,
    // shields, buffs cast in groups
    // ------------------------------------------------
    void OnPlayerSpellCast(
        Player* player, Spell* spell,
        bool /*skipCheck*/) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!player || !spell)
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        // Per-group rate limiter: max 1 spell event
        // per configured seconds. Check BEFORE any
        // spell classification (cheapest filter first).
        uint32 groupId =
            group->GetGUID().GetCounter();
        time_t now = time(nullptr);
        {
            auto it =
                _groupSpellCooldowns.find(groupId);
            if (it != _groupSpellCooldowns.end()
                && (now - it->second)
                    < sLLMChatterConfig
                        ->_groupSpellCastCooldown)
                return;
        }

        if (!GroupHasRealPlayer(group))
            return;

        SpellInfo const* spellInfo =
            spell->GetSpellInfo();
        if (!spellInfo)
            return;

        // --- Filters (before classification) ---

        // Skip passive spells
        if (spellInfo->IsPassive())
            return;

        // Skip hidden spells (not shown in UI)
        if (spellInfo->HasAttribute(
                SPELL_ATTR0_DO_NOT_DISPLAY))
            return;

        // Skip triggered spells (procs, etc.)
        if (spell->IsTriggered())
            return;

        // Skip spells with no name
        if (!spellInfo->SpellName[0]
            || spellInfo->SpellName[0][0] == '\0')
            return;

        // Skip player self-casts: bots should not
        // comment on the player buffing/shielding
        // themselves (e.g. Aspects, self-heals).
        // Area aura buffs (Bloodlust) are excluded
        // since they affect the whole group.
        if (!IsPlayerBot(player)
            && spellInfo->IsPositive()
            && !spellInfo->HasAreaAuraEffect())
        {
            Unit* tgt =
                spell->m_targets.GetUnitTarget();
            if (!tgt || tgt == player)
                return;
        }

        // --- Classify the spell ---
        // Categories: heal, dispel, cc, resurrect,
        // shield, buff
        std::string spellCategory;

        // 1. RESURRECT — check first (rare, always
        //    fires at 100%)
        if (spellInfo->HasEffect(SPELL_EFFECT_RESURRECT)
            || spellInfo->HasEffect(
                   SPELL_EFFECT_RESURRECT_NEW))
        {
            spellCategory = "resurrect";
        }
        // 2. HEAL — must target a different player
        //    in the same group (not self-heal)
        //    Includes HoTs (Renew, Rejuvenation, etc.)
        else if (
            spellInfo->HasEffect(SPELL_EFFECT_HEAL)
            || spellInfo->HasEffect(
                   SPELL_EFFECT_HEAL_MAX_HEALTH)
            || spellInfo->HasAura(
                   SPELL_AURA_PERIODIC_HEAL))
        {
            Unit* target =
                spell->m_targets.GetUnitTarget();
            if (!target || target == player)
                return;

            Player* targetPlayer =
                target->ToPlayer();
            if (!targetPlayer)
                return;

            // Target must be in the same group
            if (!targetPlayer->GetGroup()
                || targetPlayer->GetGroup()
                       != group)
                return;

            spellCategory = "heal";
        }
        // 3. DISPEL — removing debuffs from a
        //    groupmate (Cleanse, Dispel Magic, etc.)
        else if (
            spellInfo->HasEffect(SPELL_EFFECT_DISPEL))
        {
            Unit* target =
                spell->m_targets.GetUnitTarget();
            if (!target || target == player)
                return;

            Player* targetPlayer =
                target->ToPlayer();
            if (!targetPlayer)
                return;

            if (!targetPlayer->GetGroup()
                || targetPlayer->GetGroup()
                       != group)
                return;

            spellCategory = "dispel";
        }
        // 4. CC (Crowd Control) — stun, root, fear,
        //    charm, confuse (polymorph etc.)
        else if (
            spellInfo->HasAura(
                SPELL_AURA_MOD_STUN)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_ROOT)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_FEAR)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_CHARM)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_CONFUSE))
        {
            spellCategory = "cc";
        }
        // 5. SHIELD/IMMUNITY — positive spell with
        //    immunity, absorb, or damage reduction
        //    (Pain Suppression, Guardian Spirit, etc.)
        else if (spellInfo->IsPositive()
            && (spellInfo->HasAura(
                    SPELL_AURA_SCHOOL_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_DAMAGE_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_MECHANIC_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_SCHOOL_ABSORB)
                || spellInfo->HasAura(
                       SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN)
                || spellInfo->HasAura(
                       SPELL_AURA_SPLIT_DAMAGE_PCT)
                || spellInfo->HasAura(
                       SPELL_AURA_SPLIT_DAMAGE_FLAT)))
        {
            spellCategory = "shield";
        }
        // 6. BUFF — positive spell on a groupmate
        //    (not self). Catches MotW, Fort, Kings,
        //    Arcane Intellect, Bloodlust, Innervate,
        //    etc.
        else if (spellInfo->IsPositive()
            && (spellInfo->HasAura(
                    SPELL_AURA_MOD_STAT)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_TOTAL_STAT_PERCENTAGE)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_RESISTANCE)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_ATTACK_POWER)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_POWER_REGEN)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_POWER_REGEN_PERCENT)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_INCREASE_SPEED)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_MELEE_HASTE)
                || spellInfo->HasAura(
                    SPELL_AURA_HASTE_SPELLS)))
        {
            // Party/raid-wide buffs (Bloodlust,
            // Prayer of Fortitude, Gift of the Wild,
            // Greater Blessings) are self/area-targeted
            // — allow without a distinct friendly target
            if (!spellInfo->HasAreaAuraEffect())
            {
                // Single-target buff: must target
                // a different group member
                Unit* target =
                    spell->m_targets.GetUnitTarget();
                if (!target || target == player)
                    return;

                Player* targetPlayer =
                    target->ToPlayer();
                if (!targetPlayer)
                    return;

                if (!targetPlayer->GetGroup()
                    || targetPlayer->GetGroup()
                           != group)
                    return;
            }

            spellCategory = "buff";
        }
        // 7. OFFENSIVE — negative spell while in combat
        //    (Fireball, Frostbolt, Arcane Bolt, etc.)
        else if (!spellInfo->IsPositive()
                 && player->IsInCombat())
        {
            spellCategory = "offensive";
        }
        // 8. GENERIC SUPPORT — positive spell not
        //    matching the specific categories above
        //    (e.g. misc buffs, utility spells cast
        //    on groupmates)
        else if (spellInfo->IsPositive())
        {
            // Single-target: must target a group
            // member (not NPC/pet/self)
            if (!spellInfo->HasAreaAuraEffect())
            {
                Unit* target =
                    spell->m_targets.GetUnitTarget();
                if (!target || target == player)
                    return;
                Player* targetPlayer =
                    target->ToPlayer();
                if (!targetPlayer)
                    return;
                if (!targetPlayer->GetGroup()
                    || targetPlayer->GetGroup()
                           != group)
                    return;
            }
            spellCategory = "support";
        }
        else
        {
            // Non-combat negative spell (mounts,
            // food, professions) — ignore
            return;
        }

        // --- RNG gate ---
        // Resurrect always fires (100%);
        // everything else: scale chance down by
        // number of bots so total group output
        // stays roughly constant regardless of
        // group size (e.g. 10% / 5 bots = 2% each)
        if (spellCategory != "resurrect")
        {
            uint32 numBots = CountBotsInGroup(group);
            uint32 effectiveChance =
                sLLMChatterConfig
                    ->_groupSpellCastChance
                / std::max(numBots, 1u);
            if (effectiveChance < 1)
                effectiveChance = 1;
            if (urand(1, 100) > effectiveChance)
                return;
        }

        // Update the per-group cooldown
        _groupSpellCooldowns[groupId] = now;

        // --- Determine reactor bot ---
        // If caster is a bot: the caster speaks
        // about their own spell (more natural).
        // If caster is the real player: pick a
        // random bot to react (e.g. say thanks).
        bool casterIsBot = IsPlayerBot(player);
        Player* reactor = nullptr;
        if (casterIsBot)
            reactor = player;  // caster speaks
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
            return;

        // --- Gather data ---
        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string casterName = player->GetName();
        std::string spellName =
            spellInfo->SpellName[0]
                ? spellInfo->SpellName[0] : "";

        // Determine target name
        std::string targetName;
        bool isAreaBuff =
            spellInfo->HasAreaAuraEffect();
        Unit* spellTarget =
            spell->m_targets.GetUnitTarget();

        if (isAreaBuff)
        {
            // Party-wide: "the group" instead of
            // a single target name
            targetName = "the group";
        }
        else if (spellTarget)
        {
            targetName = spellTarget->GetName();
        }
        else
        {
            // AoE spells (Frost Nova, Blizzard,
            // etc.) have no unit target — fall back
            // to caster's current victim
            Unit* victim = player->GetVictim();
            if (victim)
                targetName = victim->GetName();
        }

        // Self-cast: no comment needed when a bot
        // casts on itself (e.g. PW:Shield on self)
        // Exception: area aura buffs (Bloodlust,
        // Prayer of Fortitude) are self-targeted
        // but affect the whole group
        bool isSelfCast = (!isAreaBuff
            && spellTarget
            && spellTarget->GetGUID()
                   == player->GetGUID());
        if (isSelfCast)
            return;

        // --- Pre-cache instant delivery ---
        // Skip resurrect (too important for cached).
        // Pick cache key based on category; offensive
        // cache is caster-perspective so only valid
        // when the bot itself is the caster. Player-
        // cast offensive spells skip cache entirely
        // and fall through to live LLM.
        std::string cacheKey;
        bool canUseCache = true;
        if (spellCategory == "offensive")
        {
            cacheKey = "spell_offensive";
            // Offensive cache is caster-perspective —
            // only valid when bot is the caster
            if (!casterIsBot)
                canUseCache = false;
        }
        else
        {
            cacheKey = "spell_support";
        }

        if (spellCategory != "resurrect"
            && canUseCache
            && sLLMChatterConfig->_preCacheEnable
            && sLLMChatterConfig
                   ->_preCacheSpellEnable)
        {
            std::string cachedMsg, cachedEmote;
            if (TryConsumeCachedReaction(
                    groupId, botGuid,
                    cacheKey,
                    cachedMsg, cachedEmote))
            {
                ResolvePlaceholders(
                    cachedMsg, targetName,
                    casterName, spellName);
                SendPartyMessageInstant(
                    reactor, group,
                    cachedMsg, cachedEmote);
                RecordCachedChatHistory(
                    groupId, botGuid,
                    botName, cachedMsg);
                return;
            }
            if (!sLLMChatterConfig
                    ->_preCacheFallbackToLive)
                return;
        }

        // Build extra_data JSON
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"caster_name\":\"" +
                JsonEscape(casterName) + "\","
            "\"spell_name\":\"" +
                JsonEscape(spellName) + "\","
            "\"spell_category\":\"" +
                spellCategory + "\","
            "\"target_name\":\"" +
                JsonEscape(targetName) + "\","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            + BuildBotStateJson(reactor) + "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_spell_cast', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(casterName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_spell_cast "
            "for {} casting {} [{}]",
            casterName, spellName, spellCategory);
    }

    // -----------------------------------------------
    // Hook: Bot resurrects in a group with real player
    // -----------------------------------------------
    void OnPlayerResurrect(
        Player* player, float /*restore_percent*/,
        bool /*applySickness*/) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig
                   ->_useGroupChatter)
            return;

        if (!player)
            return;

        if (!IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupResurrectCooldowns
                .find(groupId);
        if (it
            != _groupResurrectCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupResurrectCooldown)
            return;

        // RNG chance from config
        if (urand(1, 100)
            > sLLMChatterConfig
                ->_groupResurrectChance)
            return;

        _groupResurrectCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName =
            player->GetName();

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_resurrect', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 3 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            player->GetZoneId(),
            player->GetMapId(),
            botGuid,
            EscapeString(botName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_resurrect for {}",
            botName);
    }

    // -----------------------------------------------
    // Hook: Bot releases spirit (corpse run)
    // -----------------------------------------------
    void OnPlayerReleasedGhost(Player* player) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig
                   ->_useGroupChatter)
            return;

        if (!player)
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupCorpseRunCooldowns
                .find(groupId);
        if (it
            != _groupCorpseRunCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupCorpseRunCooldown)
            return;

        // RNG chance from config
        if (urand(1, 100)
            > sLLMChatterConfig
                ->_groupCorpseRunChance)
            return;

        _groupCorpseRunCooldowns[groupId] = now;

        bool isPlayerDeath =
            !IsPlayerBot(player);
        std::string deadName =
            player->GetName();

        // Pick a bot to react — for player
        // deaths, any bot; for bot deaths,
        // a different bot
        Player* reactor = isPlayerDeath
            ? GetRandomBotInGroup(group)
            : GetRandomBotInGroup(
                  group, player);
        if (!reactor)
            return;

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName =
            reactor->GetName();
        uint32 zoneId = player->GetZoneId();
        std::string zoneName =
            GetZoneName(zoneId);

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"zone_id\":" +
                std::to_string(zoneId) + ","
            "\"zone_name\":\"" +
                JsonEscape(zoneName) + "\","
            "\"dead_name\":\"" +
                JsonEscape(deadName) + "\","
            "\"is_player_death\":" +
                std::string(
                    isPlayerDeath
                        ? "true" : "false")
            + "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_corpse_run', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 5 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            zoneId,
            player->GetMapId(),
            botGuid,
            EscapeString(botName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_corpse_run for "
            "{} (died: {}) in {}",
            botName, deadName, zoneName);
    }

    // -----------------------------------------------
    // Hook: Bot enters a new zone
    // -----------------------------------------------
    void OnPlayerUpdateZone(
        Player* player, uint32 newZone,
        uint32 /*newArea*/) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled())
            return;

        if (!player)
            return;

        if (!IsPlayerBot(player))
            return;

        // Auto-join General channel for new zone
        // (applies to ALL bots, not just grouped)
        EnsureBotInGeneralChannel(player);

        // --- group zone-transition chat below ---
        if (!sLLMChatterConfig->_useGroupChatter)
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupZoneCooldowns.find(groupId);
        if (it != _groupZoneCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupZoneCooldown)
            return;

        // RNG chance
        if (urand(1, 100)
            > sLLMChatterConfig
                  ->_groupZoneChance)
            return;

        // Get zone name from DBC, skip if empty
        AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(
                newZone);
        std::string zoneName =
            area ? area->area_name[0] : "";
        if (zoneName.empty())
            return;

        _groupZoneCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName =
            player->GetName();

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"zone_id\":" +
                std::to_string(newZone) + ","
            "\"zone_name\":\"" +
                JsonEscape(zoneName) + "\""
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_zone_transition', "
            "'player', "
            "{}, {}, 3, '', "
            "{}, '{}', 0, '{}', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 5 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            newZone,
            player->GetMapId(),
            botGuid,
            EscapeString(botName),
            EscapeString(zoneName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_zone_transition "
            "for {} entering {}",
            botName, zoneName);
    }

    // -----------------------------------------------
    // Hook: Bot enters a dungeon/raid instance
    // -----------------------------------------------
    void OnPlayerMapChanged(
        Player* player) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig
                   ->_useGroupChatter)
            return;

        if (!player)
            return;

        if (!IsPlayerBot(player))
            return;

        Map* map = player->GetMap();
        if (!map || !map->IsDungeon())
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupDungeonCooldowns
                .find(groupId);
        if (it
            != _groupDungeonCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupDungeonCooldown)
            return;

        // RNG chance
        if (urand(1, 100)
            > sLLMChatterConfig
                  ->_groupDungeonChance)
            return;

        _groupDungeonCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName =
            player->GetName();
        std::string mapName =
            map->GetMapName();
        bool isRaid = map->IsRaid();

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"map_id\":" +
                std::to_string(
                    map->GetId()) + ","
            "\"map_name\":\"" +
                JsonEscape(mapName) + "\","
            "\"is_raid\":" +
                std::string(
                    isRaid
                        ? "true"
                        : "false") + ","
            "\"zone_id\":" +
                std::to_string(
                    player->GetZoneId()) +
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_dungeon_entry', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 5 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 300 SECOND))",
            player->GetZoneId(),
            map->GetId(),
            botGuid,
            EscapeString(botName),
            EscapeString(mapName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_dungeon_entry "
            "for {} entering {} (raid={})",
            botName, mapName,
            isRaid ? "yes" : "no");
    }

    // -----------------------------------------------
    // Hook: Player/bot discovers a new subzone
    // (exploration XP, xpSource == 3)
    // -----------------------------------------------
    void OnPlayerGiveXP(
        Player* player, uint32& amount,
        Unit* /*victim*/,
        uint8 xpSource) override
    {
        // Only react to exploration XP
        // XPSOURCE_EXPLORE = 3 (Player.h:1002)
        if (xpSource != 3)
            return;

        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem
            || !sLLMChatterConfig
                   ->_useGroupChatter)
            return;

        if (!player)
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 areaId = player->GetAreaId();

        // Look up area name from DBC
        AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(areaId);
        if (!area)
            return;
        std::string areaName =
            area->area_name[
                sWorld->GetDefaultDbcLocale()];
        if (areaName.empty())
            areaName =
                area->area_name[LOCALE_enUS];
        if (areaName.empty())
            return;

        // Per-group+area cooldown: prevents
        // multiple members triggering the same
        // discovery simultaneously
        uint64 cdKey =
            ((uint64)groupId << 32)
            | (uint64)areaId;
        time_t now = time(nullptr);
        auto it =
            _groupDiscoveryCooldowns.find(cdKey);
        if (it != _groupDiscoveryCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupDiscoveryCooldown)
            return;

        // RNG chance gate
        if (urand(1, 100)
            > sLLMChatterConfig
                  ->_groupDiscoveryChance)
            return;

        // Pick a random bot as reactor
        Player* reactor =
            GetRandomBotInGroup(group);
        if (!reactor)
            return;

        _groupDiscoveryCooldowns[cdKey] = now;

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName =
            reactor->GetName();
        std::string playerName =
            player->GetName();

        // Build extra_data JSON
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"area_id\":" +
                std::to_string(areaId) + ","
            "\"area_name\":\"" +
                JsonEscape(areaName) + "\","
            "\"xp_amount\":" +
                std::to_string(amount) + ","
            "\"player_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"player_class\":" +
                std::to_string(
                    player->getClass())
            + "}";

        extraData = EscapeString(extraData);

        uint32 zoneId = player->GetZoneId();

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_discovery', "
            "'player', "
            "{}, {}, 4, '', "
            "{}, '{}', 0, '{}', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL {} SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            zoneId,
            player->GetMapId(),
            botGuid,
            EscapeString(botName),
            EscapeString(areaName),
            extraData,
            urand(5, 20));

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_discovery "
            "for {} discovering {} "
            "(xp={})",
            botName, areaName, amount);
    }
};

// ============================================================
// State-triggered callout helpers (free functions)
// ============================================================

static void QueueStateCallout(
    Player* bot, Group* group,
    const char* eventType, uint32 groupId)
{
    std::string botName = bot->GetName();
    uint32 botGuid =
        bot->GetGUID().GetCounter();

    // Get target name for context
    std::string targetName = "";
    Unit* victim = bot->GetVictim();
    if (victim)
        targetName = victim->GetName();

    // Who has aggro (for aggro_loss context)
    std::string aggroTarget = "";
    if (victim && victim->GetVictim()
        && victim->GetVictim() != bot)
    {
        aggroTarget =
            victim->GetVictim()->GetName();
    }

    // --- Pre-cache instant delivery ---
    if (sLLMChatterConfig->_preCacheEnable
        && sLLMChatterConfig
               ->_preCacheStateEnable
        && group)
    {
        // Map event type to cache category
        std::string category;
        std::string evtStr(eventType);
        if (evtStr == "bot_group_low_health")
            category = "state_low_health";
        else if (evtStr == "bot_group_oom")
            category = "state_oom";
        else if (evtStr == "bot_group_aggro_loss")
            category = "state_aggro_loss";

        if (!category.empty())
        {
            std::string cachedMsg, cachedEmote;
            if (TryConsumeCachedReaction(
                    groupId, botGuid,
                    category,
                    cachedMsg, cachedEmote))
            {
                // aggro_loss uses {target}
                std::string tgt =
                    (category == "state_aggro_loss")
                    ? targetName : "";
                ResolvePlaceholders(
                    cachedMsg, tgt, "", "");
                SendPartyMessageInstant(
                    bot, group,
                    cachedMsg, cachedEmote);
                RecordCachedChatHistory(
                    groupId, botGuid,
                    botName, cachedMsg);
                return;
            }
            if (!sLLMChatterConfig
                    ->_preCacheFallbackToLive)
                return;
        }
    }

    std::string extraData = "{"
        "\"bot_guid\":" +
            std::to_string(botGuid) + ","
        "\"bot_name\":\"" +
            JsonEscape(botName) + "\","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        "\"target_name\":\"" +
            JsonEscape(targetName) + "\","
        "\"aggro_target\":\"" +
            JsonEscape(aggroTarget) + "\","
        + BuildBotStateJson(bot) + "}";

    extraData = EscapeString(extraData);

    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_events "
        "(event_type, event_scope, zone_id, "
        "map_id, priority, cooldown_key, "
        "subject_guid, subject_name, "
        "extra_data, status, "
        "react_after, expires_at) "
        "VALUES ('{}', 'player', "
        "{}, {}, 2, "
        "'state:{}:{}', "
        "{}, '{}', '{}', 'pending', "
        "DATE_ADD(NOW(), "
        "INTERVAL 1 SECOND), "
        "DATE_ADD(NOW(), "
        "INTERVAL 60 SECOND))",
        eventType,
        bot->GetZoneId(),
        bot->GetMapId(),
        eventType, botGuid,
        botGuid,
        EscapeString(botName),
        extraData);

    LOG_INFO("module",
        "LLMChatter: Queued {} for {} "
        "(hp={:.0f}%, mp={:.0f}%)",
        eventType, botName,
        bot->GetHealthPct(),
        bot->GetPowerPct(POWER_MANA));
}

static void CheckGroupCombatState()
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig
            ->_stateCalloutEnabled)
        return;

    if (!sLLMChatterConfig->_useGroupChatter)
        return;

    time_t now = time(nullptr);
    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();
    std::set<uint32> visitedGroups;

    for (auto const& [id, session] : sessions)
    {
        Player* player =
            session->GetPlayer();
        if (!player
            || !player->IsInWorld())
            continue;
        if (IsPlayerBot(player))
            continue;

        Group* group = player->GetGroup();
        if (!group)
            continue;

        uint32 groupId =
            group->GetGUID().GetCounter();
        if (visitedGroups.count(groupId))
            continue;
        visitedGroups.insert(groupId);

        for (GroupReference* itr =
                 group->GetFirstMember();
             itr; itr = itr->next())
        {
            Player* bot = itr->GetSource();
            if (!bot || !IsPlayerBot(bot))
                continue;

            uint32 botGuid =
                bot->GetGUID().GetCounter();
            uint32 cd = sLLMChatterConfig
                ->_stateCalloutCooldown;
            uint32 chance = sLLMChatterConfig
                ->_stateCalloutChance;

            // --- Low Health Check ---
            if (sLLMChatterConfig
                    ->_stateCalloutLowHealth)
            {
                float hp =
                    bot->GetHealthPct();
                if (hp > 0 && hp <=
                    sLLMChatterConfig
                        ->_lowHealthThreshold)
                {
                    auto it =
                        _botLowHealthCooldowns
                            .find(botGuid);
                    if (it ==
                        _botLowHealthCooldowns
                            .end()
                        || (now - it->second)
                            >= (time_t)cd)
                    {
                        if (urand(1, 100)
                            <= chance)
                        {
                            QueueStateCallout(
                                bot, group,
                                "bot_group_"
                                "low_health",
                                groupId);
                        }
                        _botLowHealthCooldowns
                            [botGuid] = now;
                    }
                }
            }

            // --- OOM Check ---
            if (sLLMChatterConfig
                    ->_stateCalloutOom)
            {
                if (bot->GetMaxPower(
                        POWER_MANA) > 0)
                {
                    float mp =
                        bot->GetPowerPct(
                            POWER_MANA);
                    if (mp <=
                        sLLMChatterConfig
                            ->_oomThreshold)
                    {
                        auto it =
                            _botOomCooldowns
                                .find(botGuid);
                        if (it ==
                            _botOomCooldowns
                                .end()
                            || (now - it->second)
                                >= (time_t)cd)
                        {
                            if (urand(1, 100)
                                <= chance)
                            {
                                QueueStateCallout(
                                    bot, group,
                                    "bot_group_"
                                    "oom",
                                    groupId);
                            }
                            _botOomCooldowns
                                [botGuid] = now;
                        }
                    }
                }
            }

            // --- Aggro Loss Check ---
            // (combat-only: requires active target)
            if (sLLMChatterConfig
                    ->_stateCalloutAggro
                && bot->IsInCombat())
            {
                PlayerbotAI* ai =
                    GET_PLAYERBOT_AI(bot);
                if (ai && PlayerbotAI
                        ::IsTank(bot))
                {
                    Unit* victim =
                        bot->GetVictim();
                    if (victim
                        && victim->GetVictim()
                        && victim->GetVictim()
                            != bot)
                    {
                        Player* threatened =
                            victim->GetVictim()
                                ->ToPlayer();
                        if (threatened
                            && group->IsMember(
                                threatened
                                    ->GetGUID()))
                        {
                            auto it =
                                _botAggroCooldowns
                                    .find(
                                        botGuid);
                            if (it ==
                                _botAggroCooldowns
                                    .end()
                                || (now
                                    - it->second)
                                    >= (time_t)cd)
                            {
                                if (urand(1, 100)
                                    <= chance)
                                {
                                    QueueStateCallout(
                                        bot,
                                        group,
                                        "bot_group"
                                        "_aggro_"
                                        "loss",
                                        groupId);
                                }
                                _botAggroCooldowns
                                    [botGuid]
                                        = now;
                            }
                        }
                    }
                }
            }
        }
    }
}

// ================================================
// AllCreatureScript - Quest Accept hook
// (no PlayerScript equivalent exists)
// ================================================
class LLMChatterCreatureScript
    : public AllCreatureScript
{
public:
    LLMChatterCreatureScript()
        : AllCreatureScript(
              "LLMChatterCreatureScript") {}

    bool CanCreatureQuestAccept(
        Player* player,
        Creature* /*creature*/,
        Quest const* quest) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem
            || !sLLMChatterConfig->_useGroupChatter)
            return false;

        if (!player || !quest)
            return false;

        // Player-centric: only react to the real
        // player accepting quests
        if (IsPlayerBot(player))
            return false;

        Group* group = player->GetGroup();
        if (!group)
            return false;

        if (!GroupHasRealPlayer(group))
            return false;

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 questId = quest->GetQuestId();

        // Per-group+quest dedup: only ONE reaction
        // per quest per group (prevents spam when
        // accepting multiple quests at same NPC).
        uint64 questKey =
            ((uint64)groupId << 32) | questId;
        time_t now = time(nullptr);
        auto cdIt =
            _questAcceptTimestamps.find(questKey);
        if (cdIt != _questAcceptTimestamps.end()
            && (now - cdIt->second)
               < (time_t)sLLMChatterConfig
                   ->_groupQuestAcceptCooldown)
        {
            LOG_DEBUG("module",
                "LLMChatter: QuestAccept "
                "- dedup skip for {} [{}]",
                player->GetName(),
                quest->GetTitle());
            return false;
        }

        // RNG chance gate
        if (urand(1, 100) >
            sLLMChatterConfig
                ->_groupQuestAcceptChance)
            return false;

        // Pick reactor: random bot from group
        Player* reactor =
            GetRandomBotInGroup(group);

        if (!reactor)
            return false;

        _questAcceptTimestamps[questKey] = now;

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName =
            reactor->GetName();
        std::string playerName =
            player->GetName();
        std::string questName =
            quest->GetTitle();
        uint32 zoneId = player->GetZoneId();
        std::string zoneName =
            GetZoneName(zoneId);

        // Build extra_data JSON
        // acceptor_* = who accepted the quest
        // bot_* = who will react to it
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"is_bot\":1,"
            "\"acceptor_is_bot\":" +
                std::string(
                    IsPlayerBot(player)
                        ? "1" : "0") + ","
            "\"acceptor_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"quest_name\":\"" +
                JsonEscape(questName) + "\","
            "\"quest_id\":" +
                std::to_string(questId) + ","
            "\"quest_level\":" +
                std::to_string(
                    quest->GetQuestLevel()) + ","
            "\"zone_name\":\"" +
                JsonEscape(zoneName) + "\","
            "\"quest_details\":\"" +
                JsonEscape(
                    quest->GetDetails()
                        .substr(0, 200)) + "\","
            "\"quest_objectives\":\"" +
                JsonEscape(
                    quest->GetObjectives()
                        .substr(0, 150)) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        extraData = EscapeString(extraData);

        std::string cooldownKey =
            "quest_accept:" +
            std::to_string(groupId) + ":" +
            std::to_string(questId);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_quest_accept', "
            "'player', "
            "{}, {}, 1, '{}', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            EscapeString(cooldownKey),
            botGuid, EscapeString(botName),
            EscapeString(questName),
            questId,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_quest_accept "
            "for {} accepting [{}]",
            botName, questName);

        // Return false = don't block quest accept
        return false;
    }
};

// Register scripts
void AddLLMChatterScripts()
{
    new LLMChatterWorldScript();
    new LLMChatterGameEventScript();
    new LLMChatterALEScript();
    new LLMChatterGroupScript();
    new LLMChatterPlayerScript();
    new LLMChatterCreatureScript();
}
