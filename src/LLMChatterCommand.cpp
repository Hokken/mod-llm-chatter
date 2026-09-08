/*
 * mod-llm-chatter - player command bridge for the
 * Chatter addon.
 */

#include "Chat.h"
#include "CommandScript.h"
#include "Config.h"
#include "DatabaseEnv.h"
#include "LLMChatterConfig.h"
#include "LLMChatterRequestLog.h"
#include "LLMChatterShared.h"
#include "WorldSession.h"
#include "Player.h"
#include "PlayerScript.h"
#include "ScriptMgr.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <ctime>
#include <limits>
#include <mutex>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;

namespace
{
std::string const kAddonPrefix = "CHATTER_ADDON";

// The Chatter Companion filter swallows every CHATTER_ADDON
// line it sees, so log traffic needs its own prefix for the
// two addons to coexist.
std::string const kLogPrefix = "CHATTER_LOG";

// Trait columns are VARCHAR(64), which MySQL counts in
// characters, so the server limit is counted the same way.
constexpr size_t kMaxTraitChars = 64;
constexpr size_t kMaxBackstoryChars = 1000;

// Chunked upload caps. The 3.3.5 client truncates outgoing
// chat at 255 characters, and `put <guid> t1 12 12 ` eats
// about 30 of those, so 200 leaves comfortable headroom.
constexpr size_t kMaxChunkLength = 200;
constexpr uint32 kMaxChunksPerField = 24;
constexpr time_t kPendingEditTtlSeconds = 60;

struct BotProfile
{
    uint32 guid = 0;
    std::string name;
    std::string trait1;
    std::string trait2;
    std::string trait3;
    std::string tone;
    std::string backstory;
};

void SendAddonLine(
    ChatHandler* handler, std::string const& payload)
{
    if (!handler)
        return;

    handler->SendSysMessage(
        (kAddonPrefix + " " + payload).c_str());
}

void SendLogLine(
    ChatHandler* handler, std::string const& payload)
{
    if (!handler)
        return;

    handler->SendSysMessage(
        (kLogPrefix + " " + payload).c_str());
}

std::string Trim(std::string value)
{
    auto notSpace = [](unsigned char ch)
    {
        return !std::isspace(ch);
    };

    value.erase(
        value.begin(),
        std::find_if(
            value.begin(), value.end(), notSpace));
    value.erase(
        std::find_if(
            value.rbegin(), value.rend(), notSpace)
            .base(),
        value.end());
    return value;
}

// Counts UTF-8 codepoints, not bytes, so that a limit
// expressed in characters matches what MySQL enforces on a
// VARCHAR column. Continuation bytes are 10xxxxxx.
size_t Utf8CharCount(std::string const& value)
{
    size_t count = 0;
    for (unsigned char ch : value)
    {
        if ((ch & 0xC0) != 0x80)
            ++count;
    }
    return count;
}

bool IsHexChar(char ch)
{
    return std::isxdigit(
        static_cast<unsigned char>(ch)) != 0;
}

int HexValue(char ch)
{
    if (ch >= '0' && ch <= '9')
        return ch - '0';
    if (ch >= 'a' && ch <= 'f')
        return 10 + (ch - 'a');
    if (ch >= 'A' && ch <= 'F')
        return 10 + (ch - 'A');
    return 0;
}

std::string PercentEncode(std::string const& input)
{
    if (input.empty())
        return "-";

    static char const* hex = "0123456789ABCDEF";
    std::string out;
    out.reserve(input.size() * 3);

    for (unsigned char ch : input)
    {
        if (std::isalnum(ch)
            || ch == '-'
            || ch == '_'
            || ch == '.'
            || ch == '~')
        {
            out.push_back(static_cast<char>(ch));
            continue;
        }

        out.push_back('%');
        out.push_back(hex[(ch >> 4) & 0x0F]);
        out.push_back(hex[ch & 0x0F]);
    }

    return out;
}

std::string PercentDecode(std::string const& input)
{
    if (input == "-")
        return "";

    std::string out;
    out.reserve(input.size());

    for (size_t i = 0; i < input.size(); ++i)
    {
        if (input[i] == '%'
            && i + 2 < input.size()
            && IsHexChar(input[i + 1])
            && IsHexChar(input[i + 2]))
        {
            int hi = HexValue(input[i + 1]);
            int lo = HexValue(input[i + 2]);
            out.push_back(
                static_cast<char>((hi << 4) | lo));
            i += 2;
            continue;
        }

        out.push_back(input[i]);
    }

    return out;
}

bool IsKnownBotForPlayer(uint32 playerGuid, uint32 botGuid)
{
    if (!playerGuid || !botGuid)
        return false;

    QueryResult result = CharacterDatabase.Query(
        "SELECT 1 FROM llm_bot_memories "
        "WHERE player_guid = {} "
        "  AND bot_guid = {} "
        "LIMIT 1",
        playerGuid, botGuid);
    return result != nullptr;
}

bool LoadBotProfile(uint32 botGuid, BotProfile& profile)
{
    QueryResult identResult = CharacterDatabase.Query(
        "SELECT c.name, "
        "       i.trait1, i.trait2, i.trait3, "
        "       i.tone, i.backstory "
        "FROM characters c "
        "LEFT JOIN llm_bot_identities i "
        "  ON i.bot_guid = c.guid "
        "WHERE c.guid = {} "
        "LIMIT 1",
        botGuid);

    if (!identResult)
        return false;

    profile.guid = botGuid;
    Field* ident = identResult->Fetch();
    profile.name = ident[0].Get<std::string>();
    if (!ident[1].IsNull())
        profile.trait1 = ident[1].Get<std::string>();
    if (!ident[2].IsNull())
        profile.trait2 = ident[2].Get<std::string>();
    if (!ident[3].IsNull())
        profile.trait3 = ident[3].Get<std::string>();
    if (!ident[4].IsNull())
        profile.tone = ident[4].Get<std::string>();
    if (!ident[5].IsNull())
        profile.backstory =
            ident[5].Get<std::string>();

    QueryResult sessionResult = CharacterDatabase.Query(
        "SELECT bot_name, trait1, trait2, trait3, "
        "       tone, backstory "
        "FROM llm_group_bot_traits "
        "WHERE bot_guid = {} "
        "ORDER BY assigned_at DESC "
        "LIMIT 1",
        botGuid);

    if (sessionResult)
    {
        Field* session = sessionResult->Fetch();
        if (!session[0].IsNull())
            profile.name =
                session[0].Get<std::string>();
        if (profile.trait1.empty()
            && !session[1].IsNull())
            profile.trait1 =
                session[1].Get<std::string>();
        if (profile.trait2.empty()
            && !session[2].IsNull())
            profile.trait2 =
                session[2].Get<std::string>();
        if (profile.trait3.empty()
            && !session[3].IsNull())
            profile.trait3 =
                session[3].Get<std::string>();
        if (profile.tone.empty()
            && !session[4].IsNull())
            profile.tone =
                session[4].Get<std::string>();
        if (profile.backstory.empty()
            && !session[5].IsNull())
            profile.backstory =
                session[5].Get<std::string>();
    }

    return !profile.name.empty();
}

bool ParseGuidArg(
    std::string const& token, uint32& outGuid)
{
    if (token.empty())
        return false;

    for (char ch : token)
    {
        if (!std::isdigit(
                static_cast<unsigned char>(ch)))
            return false;
    }

    try
    {
        unsigned long value = std::stoul(token);
        if (value == 0
            || value
                > static_cast<unsigned long>(
                    std::numeric_limits<uint32>::max()))
        {
            return false;
        }

        outGuid = static_cast<uint32>(value);
    }
    catch (...)
    {
        return false;
    }

    return outGuid != 0;
}

bool ParseSetArgs(
    std::string const& args,
    uint32& botGuid,
    std::string& trait1,
    std::string& trait2,
    std::string& trait3)
{
    std::istringstream iss(args);
    std::string guidToken;
    std::string t1Token;
    std::string t2Token;
    std::string t3Token;
    std::string trailing;

    if (!(iss >> guidToken >> t1Token
          >> t2Token >> t3Token))
        return false;

    if (iss >> trailing)
        return false;

    if (!ParseGuidArg(guidToken, botGuid))
        return false;

    trait1 = Trim(PercentDecode(t1Token));
    trait2 = Trim(PercentDecode(t2Token));
    trait3 = Trim(PercentDecode(t3Token));

    return !trait1.empty()
        && !trait2.empty()
        && !trait3.empty();
}

bool ValidateField(
    ChatHandler* handler,
    std::string const& label,
    std::string const& value,
    size_t maxLen)
{
    if (value.empty())
    {
        SendAddonLine(
            handler,
            "ERROR validation "
            + PercentEncode(label + " cannot be empty"));
        return false;
    }

    if (Utf8CharCount(value) > maxLen)
    {
        SendAddonLine(
            handler,
            "ERROR validation "
            + PercentEncode(
                label + " is too long"));
        return false;
    }

    return true;
}

bool HandleRosterCommand(ChatHandler* handler)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    SendAddonLine(handler, "ROSTER_BEGIN");

    QueryResult result = CharacterDatabase.Query(
        "SELECT DISTINCT m.bot_guid, "
        "       COALESCE(i.bot_name, c.name) AS bot_name "
        "FROM llm_bot_memories m "
        "LEFT JOIN llm_bot_identities i "
        "  ON i.bot_guid = m.bot_guid "
        "LEFT JOIN characters c "
        "  ON c.guid = m.bot_guid "
        "WHERE m.player_guid = {} "
        "ORDER BY bot_name ASC",
        player->GetGUID().GetCounter());

    if (result)
    {
        do
        {
            Field* fields = result->Fetch();
            uint32 botGuid = fields[0].Get<uint32>();
            std::string botName = fields[1].IsNull()
                ? "" : fields[1].Get<std::string>();

            if (botGuid && !botName.empty())
            {
                SendAddonLine(
                    handler,
                    "ROSTER "
                    + std::to_string(botGuid)
                    + " "
                    + PercentEncode(botName));
            }
        }
        while (result->NextRow());
    }

    SendAddonLine(handler, "ROSTER_END");
    return true;
}

bool HandleGetCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    uint32 botGuid = 0;
    if (!ParseGuidArg(Trim(args), botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Usage: .llmc get <botGuid>"));
        return true;
    }

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    if (!IsKnownBotForPlayer(playerGuid, botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR access "
            + PercentEncode(
                "That bot is not in your Chatter roster"));
        return true;
    }

    BotProfile profile;
    if (!LoadBotProfile(botGuid, profile))
    {
        SendAddonLine(
            handler,
            "ERROR missing "
            + PercentEncode(
                "Could not load that bot profile"));
        return true;
    }

    SendAddonLine(
        handler,
        "PROFILE "
        + std::to_string(profile.guid)
        + " " + PercentEncode(profile.name)
        + " " + PercentEncode(profile.trait1)
        + " " + PercentEncode(profile.trait2)
        + " " + PercentEncode(profile.trait3)
        + " " + PercentEncode(profile.tone));
    // Backstory sent separately — too long for
    // a single system message with PROFILE fields
    SendAddonLine(
        handler,
        "BACKSTORY "
        + std::to_string(profile.guid)
        + " " + PercentEncode(profile.backstory));
    return true;
}

bool ApplyTraitUpdate(
    ChatHandler* handler,
    uint32 playerGuid,
    uint32 botGuid,
    std::string const& trait1,
    std::string const& trait2,
    std::string const& trait3)
{
    if (!ValidateField(
            handler, "Trait 1", trait1, kMaxTraitChars)
        || !ValidateField(
            handler, "Trait 2", trait2, kMaxTraitChars)
        || !ValidateField(
            handler, "Trait 3", trait3, kMaxTraitChars))
    {
        return true;
    }

    BotProfile profile;
    if (!LoadBotProfile(botGuid, profile))
    {
        SendAddonLine(
            handler,
            "ERROR missing "
            + PercentEncode(
                "Could not load that bot profile"));
        return true;
    }

    bool traitsChanged =
        (trait1 != profile.trait1
         || trait2 != profile.trait2
         || trait3 != profile.trait3);

    if (traitsChanged)
    {
        // Traits changed — clear tone/backstory
        // so they regenerate for the new traits
        CharacterDatabase.Execute(
            "INSERT INTO llm_bot_identities "
            "(bot_guid, bot_name, trait1, trait2, "
            " trait3, tone, farewell_msg, backstory,"
            " identity_version) "
            "VALUES ({}, '{}', '{}', '{}', '{}', "
            "        NULL, NULL, NULL, {}) "
            "ON DUPLICATE KEY UPDATE "
            " bot_name = VALUES(bot_name), "
            " trait1 = VALUES(trait1), "
            " trait2 = VALUES(trait2), "
            " trait3 = VALUES(trait3), "
            " tone = NULL, "
            " farewell_msg = NULL, "
            " backstory = NULL",
            botGuid,
            EscapeString(profile.name),
            EscapeString(trait1),
            EscapeString(trait2),
            EscapeString(trait3),
            sConfigMgr->GetOption<uint32>(
                "LLMChatter.Memory.IdentityVersion",
                1));

        CharacterDatabase.Execute(
            "UPDATE llm_group_bot_traits "
            "SET bot_name = '{}', "
            "    trait1 = '{}', "
            "    trait2 = '{}', "
            "    trait3 = '{}', "
            "    tone = NULL, "
            "    farewell_msg = NULL, "
            "    backstory = NULL "
            "WHERE bot_guid = {}",
            EscapeString(profile.name),
            EscapeString(trait1),
            EscapeString(trait2),
            EscapeString(trait3),
            botGuid);

        CharacterDatabase.Execute(
            "DELETE FROM llm_group_cached_responses "
            "WHERE bot_guid = {}",
            botGuid);

        // Queue tone regen first (faster than backstory)
        std::string regenExtra =
            "{\"bot_guid\": "
            + std::to_string(botGuid)
            + ", \"player_guid\": "
            + std::to_string(playerGuid)
            + "}";
        QueueChatterEvent(
            "bot_tone_regen",
            "player",
            0, 0, 5, "",
            botGuid, "",
            0, "", 0,
            regenExtra,
            5, 120, true);

        // Queue backstory regen for new traits
        QueueChatterEvent(
            "bot_backstory_regen",
            "player",
            0, 0, 5, "",
            botGuid, "",
            0, "", 0,
            regenExtra,
            5, 120, true);
    }
    else
    {
        // Traits unchanged — just save name,
        // preserve tone/backstory/farewell as-is
        CharacterDatabase.Execute(
            "INSERT INTO llm_bot_identities "
            "(bot_guid, bot_name, trait1, trait2, "
            " trait3, identity_version) "
            "VALUES ({}, '{}', '{}', '{}', '{}', {})"
            " ON DUPLICATE KEY UPDATE "
            " bot_name = VALUES(bot_name), "
            " trait1 = VALUES(trait1), "
            " trait2 = VALUES(trait2), "
            " trait3 = VALUES(trait3)",
            botGuid,
            EscapeString(profile.name),
            EscapeString(trait1),
            EscapeString(trait2),
            EscapeString(trait3),
            sConfigMgr->GetOption<uint32>(
                "LLMChatter.Memory.IdentityVersion",
                1));

        CharacterDatabase.Execute(
            "UPDATE llm_group_bot_traits "
            "SET bot_name = '{}', "
            "    trait1 = '{}', "
            "    trait2 = '{}', "
            "    trait3 = '{}' "
            "WHERE bot_guid = {}",
            EscapeString(profile.name),
            EscapeString(trait1),
            EscapeString(trait2),
            EscapeString(trait3),
            botGuid);
    }

    std::string changedFlag =
        traitsChanged ? "changed" : "unchanged";
    SendAddonLine(
        handler,
        "UPDATED "
        + std::to_string(botGuid)
        + " "
        + PercentEncode(profile.name)
        + " "
        + changedFlag);
    std::string toneToSend =
        traitsChanged ? "" : profile.tone;
    SendAddonLine(
        handler,
        "PROFILE "
        + std::to_string(botGuid)
        + " " + PercentEncode(profile.name)
        + " " + PercentEncode(trait1)
        + " " + PercentEncode(trait2)
        + " " + PercentEncode(trait3)
        + " " + PercentEncode(toneToSend));
    if (!traitsChanged)
    {
        SendAddonLine(
            handler,
            "BACKSTORY "
            + std::to_string(botGuid)
            + " "
            + PercentEncode(profile.backstory));
    }
    return true;
}

bool HandleSetCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    uint32 botGuid = 0;
    std::string trait1;
    std::string trait2;
    std::string trait3;

    if (!ParseSetArgs(
            args, botGuid, trait1, trait2,
            trait3))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Usage: .llmc set <botGuid> "
                "<trait1> <trait2> <trait3>"));
        return true;
    }

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    if (!IsKnownBotForPlayer(playerGuid, botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR access "
            + PercentEncode(
                "That bot is not in your Chatter roster"));
        return true;
    }

    return ApplyTraitUpdate(
        handler, playerGuid, botGuid, trait1, trait2,
        trait3);
}

bool ApplyBackstoryUpdate(
    ChatHandler* handler,
    uint32 botGuid,
    std::string const& backstory)
{
    if (backstory.empty())
    {
        SendAddonLine(
            handler,
            "ERROR validation "
            + PercentEncode(
                "Backstory cannot be empty"));
        return true;
    }

    if (Utf8CharCount(backstory) > kMaxBackstoryChars)
    {
        SendAddonLine(
            handler,
            "ERROR validation "
            + PercentEncode(
                "Backstory is too long "
                "(max 1000 chars)"));
        return true;
    }

    BotProfile profile;
    if (!LoadBotProfile(botGuid, profile))
    {
        SendAddonLine(
            handler,
            "ERROR missing "
            + PercentEncode(
                "Could not load that bot "
                "profile"));
        return true;
    }

    // Reject if bot has no traits — upserting an
    // identity with blank traits would poison
    // future trait assignment
    if (profile.trait1.empty()
        || profile.trait2.empty()
        || profile.trait3.empty())
    {
        SendAddonLine(
            handler,
            "ERROR validation "
            + PercentEncode(
                "Bot has no traits yet. "
                "Invite them to a group "
                "first."));
        return true;
    }

    // Upsert identity row — creates it if the
    // bot only exists via memories/session traits
    CharacterDatabase.Execute(
        "INSERT INTO llm_bot_identities "
        "(bot_guid, bot_name, trait1, trait2, "
        " trait3, backstory, identity_version) "
        "VALUES ({}, '{}', '{}', '{}', '{}', "
        "        '{}', {}) "
        "ON DUPLICATE KEY UPDATE "
        " backstory = VALUES(backstory)",
        botGuid,
        EscapeString(profile.name),
        EscapeString(profile.trait1),
        EscapeString(profile.trait2),
        EscapeString(profile.trait3),
        EscapeString(backstory),
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.Memory.IdentityVersion",
            1));

    CharacterDatabase.Execute(
        "UPDATE llm_group_bot_traits "
        "SET backstory = '{}' "
        "WHERE bot_guid = {}",
        EscapeString(backstory),
        botGuid);

    SendAddonLine(
        handler,
        "BACKSTORY_SAVED "
        + std::to_string(botGuid)
        + " "
        + PercentEncode(profile.name));
    SendAddonLine(
        handler,
        "PROFILE "
        + std::to_string(profile.guid)
        + " " + PercentEncode(profile.name)
        + " " + PercentEncode(profile.trait1)
        + " " + PercentEncode(profile.trait2)
        + " " + PercentEncode(profile.trait3)
        + " " + PercentEncode(profile.tone));
    SendAddonLine(
        handler,
        "BACKSTORY "
        + std::to_string(profile.guid)
        + " " + PercentEncode(backstory));
    return true;
}

bool HandleSetBackstoryCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    // Parse: <guid> <encoded_backstory>
    std::istringstream iss(args);
    std::string guidToken;
    std::string bsToken;

    if (!(iss >> guidToken))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Usage: .llmc setbackstory "
                "<botGuid> <backstory>"));
        return true;
    }

    // Rest of the line is the backstory
    std::getline(iss, bsToken);
    bsToken = Trim(bsToken);

    uint32 botGuid = 0;
    if (!ParseGuidArg(guidToken, botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Invalid bot GUID"));
        return true;
    }

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    if (!IsKnownBotForPlayer(playerGuid, botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR access "
            + PercentEncode(
                "That bot is not in your "
                "Chatter roster"));
        return true;
    }

    return ApplyBackstoryUpdate(
        handler, botGuid,
        Trim(PercentDecode(bsToken)));
}

bool HandleRegenBackstoryCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    uint32 botGuid = 0;
    if (!ParseGuidArg(Trim(args), botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Usage: .llmc regenbackstory "
                "<botGuid>"));
        return true;
    }

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    if (!IsKnownBotForPlayer(playerGuid, botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR access "
            + PercentEncode(
                "That bot is not in your "
                "Chatter roster"));
        return true;
    }

    // Clear existing backstory
    CharacterDatabase.Execute(
        "UPDATE llm_bot_identities "
        "SET backstory = NULL "
        "WHERE bot_guid = {}",
        botGuid);

    CharacterDatabase.Execute(
        "UPDATE llm_group_bot_traits "
        "SET backstory = NULL "
        "WHERE bot_guid = {}",
        botGuid);

    // Queue regen event for Python bridge
    std::string extraData =
        "{\"bot_guid\": "
        + std::to_string(botGuid)
        + ", \"player_guid\": "
        + std::to_string(playerGuid)
        + "}";

    QueueChatterEvent(
        "bot_backstory_regen",
        "player",
        0, 0,
        5,
        "",
        botGuid, "",
        0, "",
        0,
        extraData,
        0,
        120,
        true);

    BotProfile profile;
    LoadBotProfile(botGuid, profile);

    SendAddonLine(
        handler,
        "BACKSTORY_REGEN "
        + std::to_string(botGuid)
        + " "
        + PercentEncode(profile.name));
    return true;
}
bool HandleForgetCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    uint32 botGuid = 0;
    if (!ParseGuidArg(Trim(args), botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Usage: .llmc forget <botGuid>"));
        return true;
    }

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    if (!IsKnownBotForPlayer(playerGuid, botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR access "
            + PercentEncode(
                "That bot is not in your "
                "Chatter roster"));
        return true;
    }

    // Delete only this player's memories of this bot
    CharacterDatabase.Execute(
        "DELETE FROM llm_bot_memories "
        "WHERE player_guid = {} "
        "  AND bot_guid = {}",
        playerGuid,
        botGuid);

    // Fetch name from characters table for response
    std::string botName;
    QueryResult nameResult = CharacterDatabase.Query(
        "SELECT name FROM characters "
        "WHERE guid = {}",
        botGuid);
    if (nameResult)
        botName = nameResult->Fetch()[0]
            .Get<std::string>();

    SendAddonLine(
        handler,
        "FORGOTTEN "
        + std::to_string(botGuid)
        + " "
        + PercentEncode(botName));
    return true;
}

// --- Chunked profile upload -------------------------------
// The 3.3.5 client cuts outgoing chat at 255 characters, so
// a percent-encoded profile does not always fit in a single
// `.llmc set` line. Oversized edits arrive one `put` at a
// time, are staged per player, and are applied by `commit`
// through the very same write paths the single-shot
// commands use.

enum ProfileField : uint8
{
    PROFILE_FIELD_TRAIT1 = 0,
    PROFILE_FIELD_TRAIT2 = 1,
    PROFILE_FIELD_TRAIT3 = 2,
    PROFILE_FIELD_BACKSTORY = 3,
    PROFILE_FIELD_COUNT = 4
};

struct PendingProfileEdit
{
    uint32 botGuid = 0;
    std::array<std::vector<std::string>,
        PROFILE_FIELD_COUNT> chunks;
    std::array<uint32, PROFILE_FIELD_COUNT> expected{};
    time_t lastActivity = 0;
};

// `.llmc` runs on the world thread (CMSG_MESSAGECHAT is
// PROCESS_THREADUNSAFE), so the mutex is defensive.
std::mutex g_pendingEditsMutex;
std::unordered_map<uint32, PendingProfileEdit>
    g_pendingEdits;

void ResetPendingEdit(
    PendingProfileEdit& edit, uint32 botGuid)
{
    edit.botGuid = botGuid;
    for (uint8 field = 0; field < PROFILE_FIELD_COUNT;
         ++field)
    {
        edit.chunks[field].clear();
        edit.expected[field] = 0;
    }
}

// Caller must hold g_pendingEditsMutex.
void PrunePendingEdits(time_t now)
{
    for (auto it = g_pendingEdits.begin();
         it != g_pendingEdits.end();)
    {
        if (now - it->second.lastActivity
            > kPendingEditTtlSeconds)
            it = g_pendingEdits.erase(it);
        else
            ++it;
    }
}

bool ParseFieldToken(
    std::string const& token, uint8& outField)
{
    if (token == "t1")
        outField = PROFILE_FIELD_TRAIT1;
    else if (token == "t2")
        outField = PROFILE_FIELD_TRAIT2;
    else if (token == "t3")
        outField = PROFILE_FIELD_TRAIT3;
    else if (token == "bs")
        outField = PROFILE_FIELD_BACKSTORY;
    else
        return false;

    return true;
}

bool ParseChunkIndex(
    std::string const& token, uint32& outValue)
{
    if (token.empty() || token.size() > 2)
        return false;

    for (char ch : token)
    {
        if (!std::isdigit(
                static_cast<unsigned char>(ch)))
            return false;
    }

    outValue = static_cast<uint32>(std::stoul(token));
    return outValue >= 1
        && outValue <= kMaxChunksPerField;
}

bool HandlePutCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    std::istringstream iss(args);
    std::string guidToken;
    std::string fieldToken;
    std::string seqToken;
    std::string totalToken;
    std::string chunk;
    std::string trailing;

    if (!(iss >> guidToken >> fieldToken >> seqToken
          >> totalToken >> chunk))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Usage: .llmc put <botGuid> <field> "
                "<seq> <total> <chunk>"));
        return true;
    }

    if (iss >> trailing)
    {
        SendAddonLine(
            handler,
            "ERROR chunk "
            + PercentEncode(
                "Chunk payload must not contain "
                "spaces"));
        return true;
    }

    uint32 botGuid = 0;
    uint8 field = 0;
    uint32 seq = 0;
    uint32 total = 0;
    if (!ParseGuidArg(guidToken, botGuid)
        || !ParseFieldToken(fieldToken, field)
        || !ParseChunkIndex(seqToken, seq)
        || !ParseChunkIndex(totalToken, total)
        || seq > total)
    {
        SendAddonLine(
            handler,
            "ERROR chunk "
            + PercentEncode("Malformed chunk header"));
        return true;
    }

    if (chunk.size() > kMaxChunkLength)
    {
        SendAddonLine(
            handler,
            "ERROR chunk "
            + PercentEncode("Chunk is too long"));
        return true;
    }

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    if (!IsKnownBotForPlayer(playerGuid, botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR access "
            + PercentEncode(
                "That bot is not in your Chatter roster"));
        return true;
    }

    time_t now = time(nullptr);
    std::lock_guard<std::mutex> guard(
        g_pendingEditsMutex);
    PrunePendingEdits(now);

    PendingProfileEdit& edit = g_pendingEdits[playerGuid];

    // A chunk for another bot means the previous upload was
    // abandoned. Fields are never merged across bots.
    if (edit.botGuid != botGuid)
        ResetPendingEdit(edit, botGuid);

    // Slots are addressed by seq, so a resend overwrites in
    // place instead of corrupting the sequence.
    if (edit.expected[field] != total)
    {
        edit.expected[field] = total;
        edit.chunks[field].assign(total, "");
    }

    edit.chunks[field][seq - 1] = chunk;
    edit.lastActivity = now;
    return true;
}

bool HandleCommitCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    uint32 botGuid = 0;
    if (!ParseGuidArg(Trim(args), botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Usage: .llmc commit <botGuid>"));
        return true;
    }

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    if (!IsKnownBotForPlayer(playerGuid, botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR access "
            + PercentEncode(
                "That bot is not in your Chatter roster"));
        return true;
    }

    PendingProfileEdit edit;
    {
        std::lock_guard<std::mutex> guard(
            g_pendingEditsMutex);
        PrunePendingEdits(time(nullptr));

        auto it = g_pendingEdits.find(playerGuid);
        if (it == g_pendingEdits.end()
            || it->second.botGuid != botGuid)
        {
            SendAddonLine(
                handler,
                "ERROR chunk "
                + PercentEncode(
                    "No staged profile edit for that "
                    "bot"));
            return true;
        }

        // Staging is dropped whether or not the apply below
        // succeeds, so a rejected upload cannot leak into
        // the next one.
        edit = std::move(it->second);
        g_pendingEdits.erase(it);
    }

    std::array<std::string, PROFILE_FIELD_COUNT> values;
    std::array<bool, PROFILE_FIELD_COUNT> staged{};

    for (uint8 field = 0; field < PROFILE_FIELD_COUNT;
         ++field)
    {
        if (!edit.expected[field])
            continue;

        std::string joined;
        for (std::string const& part : edit.chunks[field])
        {
            if (part.empty())
            {
                SendAddonLine(
                    handler,
                    "ERROR chunk "
                    + PercentEncode(
                        "Upload is incomplete, please "
                        "save again"));
                return true;
            }

            joined += part;
        }

        values[field] = Trim(PercentDecode(joined));
        staged[field] = true;
    }

    bool traitsStaged = staged[PROFILE_FIELD_TRAIT1]
        || staged[PROFILE_FIELD_TRAIT2]
        || staged[PROFILE_FIELD_TRAIT3];

    if (!traitsStaged && !staged[PROFILE_FIELD_BACKSTORY])
    {
        SendAddonLine(
            handler,
            "ERROR chunk "
            + PercentEncode("Nothing staged to commit"));
        return true;
    }

    if (traitsStaged)
    {
        BotProfile profile;
        if (!LoadBotProfile(botGuid, profile))
        {
            SendAddonLine(
                handler,
                "ERROR missing "
                + PercentEncode(
                    "Could not load that bot profile"));
            return true;
        }

        // Fields the addon did not send keep the values
        // already stored for the bot.
        if (!staged[PROFILE_FIELD_TRAIT1])
            values[PROFILE_FIELD_TRAIT1] = profile.trait1;
        if (!staged[PROFILE_FIELD_TRAIT2])
            values[PROFILE_FIELD_TRAIT2] = profile.trait2;
        if (!staged[PROFILE_FIELD_TRAIT3])
            values[PROFILE_FIELD_TRAIT3] = profile.trait3;

        ApplyTraitUpdate(
            handler, playerGuid, botGuid,
            values[PROFILE_FIELD_TRAIT1],
            values[PROFILE_FIELD_TRAIT2],
            values[PROFILE_FIELD_TRAIT3]);
    }

    if (staged[PROFILE_FIELD_BACKSTORY])
    {
        ApplyBackstoryUpdate(
            handler, botGuid,
            values[PROFILE_FIELD_BACKSTORY]);
    }

    return true;
}

bool HandleCancelCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    uint32 botGuid = 0;
    if (!ParseGuidArg(Trim(args), botGuid))
    {
        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Usage: .llmc cancel <botGuid>"));
        return true;
    }

    uint32 playerGuid =
        player->GetGUID().GetCounter();

    std::lock_guard<std::mutex> guard(
        g_pendingEditsMutex);
    auto it = g_pendingEdits.find(playerGuid);
    if (it != g_pendingEdits.end()
        && it->second.botGuid == botGuid)
        g_pendingEdits.erase(it);

    return true;
}

// ----------------------------------------------------------
// Chatter Log addon (`.llmc log ...`)
// ----------------------------------------------------------

size_t LogChunkBudget()
{
    uint32 configured = sLLMChatterConfig
        ? sLLMChatterConfig->_addonLogChunkChars : 512;

    return configured ? configured : 512;
}

// Percent-encode while splitting, so a %XX escape can never
// straddle two chunks. Multi-byte UTF-8 may split, which is
// harmless: the addon concatenates the decoded bytes.
std::vector<std::string> EncodeChunks(
    std::string const& text, size_t budget)
{
    static char const* hex = "0123456789ABCDEF";

    std::vector<std::string> chunks;
    std::string current;

    for (unsigned char ch : text)
    {
        char buffer[3];
        size_t length;

        if (std::isalnum(ch)
            || ch == '-'
            || ch == '_'
            || ch == '.'
            || ch == '~')
        {
            buffer[0] = static_cast<char>(ch);
            length = 1;
        }
        else
        {
            buffer[0] = '%';
            buffer[1] = hex[(ch >> 4) & 0x0F];
            buffer[2] = hex[ch & 0x0F];
            length = 3;
        }

        if (!current.empty()
            && current.size() + length > budget)
        {
            chunks.push_back(current);
            current.clear();
        }

        current.append(buffer, length);
    }

    if (!current.empty())
        chunks.push_back(current);

    if (chunks.empty())
        chunks.push_back("-");

    return chunks;
}

void SendLogField(
    ChatHandler* handler,
    uint64 seq,
    std::string const& field,
    std::string const& text)
{
    std::vector<std::string> chunks =
        EncodeChunks(text, LogChunkBudget());

    for (size_t i = 0; i < chunks.size(); ++i)
    {
        SendLogLine(
            handler,
            "LOG_PART "
            + std::to_string(seq)
            + " " + field
            + " " + std::to_string(i + 1)
            + " " + std::to_string(chunks.size())
            + " " + chunks[i]);
    }
}

std::string BuildLogMeta(LLMRequestLogEntry const& entry)
{
    std::string meta =
        "Time:      " + entry.timestamp + "\n"
        "Seq:       " + std::to_string(entry.seq) + "\n"
        "Label:     " + entry.label + "\n"
        "Model:     " + entry.model + "\n"
        "Provider:  " + entry.provider + "\n"
        "Duration:  " + std::to_string(entry.durationMs)
        + " ms\n";

    for (auto const& extra : entry.extras)
        meta += extra.first + ": " + extra.second + "\n";

    return meta;
}

// One-line teaser for the list pane: the answer if there is
// one, otherwise the tail of the prompt.
std::string BuildLogPreview(LLMRequestLogEntry const& entry)
{
    std::string source = entry.response.empty()
        ? entry.prompt : entry.response;

    std::string flat;
    flat.reserve(source.size());

    bool pendingSpace = false;
    for (char ch : source)
    {
        if (ch == '\n' || ch == '\r' || ch == '\t'
            || ch == ' ')
        {
            pendingSpace = !flat.empty();
            continue;
        }

        if (pendingSpace)
        {
            flat.push_back(' ');
            pendingSpace = false;
        }

        flat.push_back(ch);

        if (flat.size() >= 90)
            break;
    }

    return flat;
}

bool EnsureLogAccess(ChatHandler* handler)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->_addonLogEnable)
    {
        SendLogLine(
            handler,
            "ERROR disabled "
            + PercentEncode(
                "LLMChatter.AddonLog.Enable is off"));
        return false;
    }

    WorldSession* session = handler->GetSession();
    if (!session)
        return false;

    uint32 security =
        static_cast<uint32>(session->GetSecurity());
    if (security < sLLMChatterConfig->_addonLogMinSecurity)
    {
        SendLogLine(
            handler,
            "ERROR access "
            + PercentEncode(
                "Your account may not read the request log"));
        return false;
    }

    return true;
}

bool HandleLogStatusCommand(ChatHandler* handler)
{
    std::vector<LLMRequestLogEntry> entries;
    std::string error;
    bool ok = LoadRequestLogTail(entries, error);

    uint64 lastSeq =
        entries.empty() ? 0 : entries.back().seq;

    SendLogLine(
        handler,
        "LOG_STATUS 1 "
        + std::string(ok ? "1" : "0")
        + " " + PercentEncode(GetRequestLogPath())
        + " " + std::to_string(lastSeq)
        + " " + std::to_string(entries.size()));

    if (!ok)
    {
        SendLogLine(
            handler,
            "ERROR missing " + PercentEncode(error));
    }
    else if (entries.empty())
    {
        SendLogLine(
            handler,
            "ERROR empty "
            + PercentEncode(
                "The request log is empty. Set "
                "LLMChatter.RequestLog.Enable = 1 and "
                "restart the bridge."));
    }

    return true;
}

bool HandleLogListCommand(
    ChatHandler* handler, std::string const& args)
{
    uint32 count = 25;
    uint64 sinceSeq = 0;

    std::istringstream iss(args);
    std::string countArg;
    std::string sinceArg;
    iss >> countArg >> sinceArg;

    if (!countArg.empty())
    {
        uint32 parsed = 0;
        if (ParseGuidArg(countArg, parsed) && parsed)
            count = parsed;
    }

    if (!sinceArg.empty())
    {
        uint32 parsed = 0;
        if (ParseGuidArg(sinceArg, parsed))
            sinceSeq = parsed;
    }

    count = std::min(
        count, sLLMChatterConfig->_addonLogMaxEntries);

    std::vector<LLMRequestLogEntry> entries;
    std::string error;
    if (!LoadRequestLogTail(entries, error))
    {
        SendLogLine(
            handler,
            "ERROR missing " + PercentEncode(error));
        return true;
    }

    std::vector<LLMRequestLogEntry const*> selected;
    for (auto it = entries.rbegin();
        it != entries.rend(); ++it)
    {
        if (it->seq <= sinceSeq)
            break;

        selected.push_back(&(*it));
        if (selected.size() >= count)
            break;
    }

    SendLogLine(
        handler,
        "LOG_LIST_BEGIN "
        + std::to_string(selected.size()));

    // Oldest first, so the addon can append as it reads.
    for (auto it = selected.rbegin();
        it != selected.rend(); ++it)
    {
        LLMRequestLogEntry const* entry = *it;
        size_t promptBytes = entry->systemPrompt.size()
            + entry->prompt.size();

        SendLogLine(
            handler,
            "LOG_ENTRY "
            + std::to_string(entry->seq)
            + " " + PercentEncode(entry->timestamp)
            + " " + PercentEncode(entry->label)
            + " " + PercentEncode(entry->model)
            + " " + std::to_string(entry->durationMs)
            + " " + std::to_string(promptBytes)
            + " " + std::to_string(entry->response.size())
            + " " + PercentEncode(BuildLogPreview(*entry)));
    }

    uint64 lastSeq =
        entries.empty() ? sinceSeq : entries.back().seq;

    SendLogLine(
        handler,
        "LOG_LIST_END " + std::to_string(lastSeq));
    return true;
}

bool HandleLogGetCommand(
    ChatHandler* handler, std::string const& args)
{
    uint32 seq = 0;
    if (!ParseGuidArg(Trim(args), seq))
    {
        SendLogLine(
            handler,
            "ERROR usage "
            + PercentEncode("Usage: .llmc log get <seq>"));
        return true;
    }

    LLMRequestLogEntry entry;
    std::string error;
    if (!FindRequestLogEntry(seq, entry, error))
    {
        SendLogLine(
            handler,
            "ERROR missing " + PercentEncode(error));
        return true;
    }

    SendLogLine(
        handler, "LOG_BEGIN " + std::to_string(entry.seq));

    SendLogField(
        handler, entry.seq, "meta", BuildLogMeta(entry));
    SendLogField(
        handler, entry.seq, "system", entry.systemPrompt);
    SendLogField(
        handler, entry.seq, "prompt", entry.prompt);
    SendLogField(
        handler, entry.seq, "response", entry.response);

    SendLogLine(
        handler, "LOG_END " + std::to_string(entry.seq));
    return true;
}

bool HandleLogCommand(
    ChatHandler* handler, std::string const& args)
{
    if (!EnsureLogAccess(handler))
        return true;

    std::string input = Trim(args);
    if (input.empty() || input == "status")
        return HandleLogStatusCommand(handler);

    std::string command;
    std::string rest;
    std::istringstream iss(input);
    iss >> command;
    std::getline(iss, rest);
    rest = Trim(rest);

    if (command == "list")
        return HandleLogListCommand(handler, rest);

    if (command == "get")
        return HandleLogGetCommand(handler, rest);

    SendLogLine(
        handler,
        "ERROR usage "
        + PercentEncode(
            "Supported: log status, "
            "log list [count] [sinceSeq], log get <seq>"));
    return true;
}

// ----------------------------------------------------------
// Chatter Memory addon (`.llmc mem ...`)
// ----------------------------------------------------------
// Reads llm_bot_memories, the journal the bridge writes about
// each bot-player pair. Everything here is scoped to the
// caller's own guid, exactly like `roster` and `forget`, so a
// player only ever sees what bots remember about them. That
// keeps this at SEC_PLAYER and independent of the AddonLog
// gate, which guards the far more sensitive raw prompt log.

// A memory is capped at 500 characters by the generator, so a
// whole journal fits in one burst. The text therefore ships
// inline with the list instead of costing a round trip each.
constexpr uint32 kMemDefaultCount = 30;
constexpr uint32 kMemMaxCount = 200;

struct MemoryRow
{
    uint32 id = 0;
    std::string header;
    std::string text;
};

void SendMemoryText(
    ChatHandler* handler, uint32 id, std::string const& text)
{
    std::vector<std::string> chunks =
        EncodeChunks(text, LogChunkBudget());

    for (size_t i = 0; i < chunks.size(); ++i)
    {
        SendLogLine(
            handler,
            "MEM_PART "
            + std::to_string(id)
            + " " + std::to_string(i + 1)
            + " " + std::to_string(chunks.size())
            + " " + chunks[i]);
    }
}

bool HandleMemBotsCommand(ChatHandler* handler)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    uint32 playerGuid = player->GetGUID().GetCounter();

    // CAST(... AS UNSIGNED) keeps SUM() out of DECIMAL, which
    // Field::Get<uint32> does not accept.
    QueryResult result = CharacterDatabase.Query(
        "SELECT m.bot_guid, "
        "       COALESCE(i.bot_name, c.name) AS bot_name, "
        "       COUNT(*) AS total, "
        "       CAST(SUM(m.active = 1) AS UNSIGNED) AS act, "
        "       CAST(SUM(m.used = 1) AS UNSIGNED) AS wasused, "
        "       DATE_FORMAT(MAX(m.created_at), "
        "                   '%Y-%m-%d %H:%i') AS newest "
        "FROM llm_bot_memories m "
        "LEFT JOIN llm_bot_identities i "
        "  ON i.bot_guid = m.bot_guid "
        "LEFT JOIN characters c "
        "  ON c.guid = m.bot_guid "
        "WHERE m.player_guid = {} "
        "GROUP BY m.bot_guid, bot_name "
        "ORDER BY bot_name ASC",
        playerGuid);

    // Collected first so MEM_BOTS_BEGIN can carry the count.
    std::vector<std::string> lines;

    if (result)
    {
        do
        {
            Field* fields = result->Fetch();
            uint32 botGuid = fields[0].Get<uint32>();
            if (!botGuid)
                continue;

            std::string botName = fields[1].IsNull()
                ? "" : fields[1].Get<std::string>();
            if (botName.empty())
                botName = "Unknown #"
                    + std::to_string(botGuid);

            std::string newest = fields[5].IsNull()
                ? "" : fields[5].Get<std::string>();

            lines.push_back(
                "MEM_BOT "
                + std::to_string(botGuid)
                + " " + PercentEncode(botName)
                + " " + std::to_string(
                    fields[2].Get<uint32>())
                + " " + std::to_string(
                    fields[3].Get<uint32>())
                + " " + std::to_string(
                    fields[4].Get<uint32>())
                + " " + PercentEncode(newest));
        }
        while (result->NextRow());
    }

    SendLogLine(
        handler,
        "MEM_BOTS_BEGIN " + std::to_string(lines.size()));

    for (std::string const& line : lines)
        SendLogLine(handler, line);

    SendLogLine(
        handler,
        "MEM_BOTS_END " + std::to_string(lines.size()));

    if (lines.empty())
    {
        SendLogLine(
            handler,
            "MEM_ERROR empty "
            + PercentEncode(
                "No bot remembers you yet. Group with a "
                "bot for at least "
                "LLMChatter.Memory.SessionMinutes."));
    }

    return true;
}

bool HandleMemListCommand(
    ChatHandler* handler, std::string const& args)
{
    Player* player = handler->GetSession()->GetPlayer();
    if (!player)
        return true;

    std::istringstream iss(args);
    std::string guidArg;
    std::string countArg;
    iss >> guidArg >> countArg;

    uint32 botGuid = 0;
    if (!ParseGuidArg(guidArg, botGuid))
    {
        SendLogLine(
            handler,
            "MEM_ERROR usage "
            + PercentEncode(
                "Usage: .llmc mem list <botGuid> [count]"));
        return true;
    }

    uint32 count = kMemDefaultCount;
    if (!countArg.empty())
    {
        uint32 parsed = 0;
        if (ParseGuidArg(countArg, parsed) && parsed)
            count = std::min(parsed, kMemMaxCount);
    }

    uint32 playerGuid = player->GetGUID().GetCounter();
    if (!IsKnownBotForPlayer(playerGuid, botGuid))
    {
        SendLogLine(
            handler,
            "MEM_ERROR access "
            + PercentEncode(
                "That bot has no memories of you"));
        return true;
    }

    QueryResult result = CharacterDatabase.Query(
        "SELECT m.id, m.memory_type, m.mood, m.emote, "
        "       m.active, m.used, m.memory, "
        "       DATE_FORMAT(m.created_at, "
        "                   '%Y-%m-%d %H:%i') AS made, "
        "       DATE_FORMAT(m.last_used_at, "
        "                   '%Y-%m-%d %H:%i') AS lastused "
        "FROM llm_bot_memories m "
        "WHERE m.player_guid = {} "
        "  AND m.bot_guid = {} "
        "ORDER BY m.created_at DESC, m.id DESC "
        "LIMIT {}",
        playerGuid, botGuid, count);

    std::vector<MemoryRow> rows;

    if (result)
    {
        do
        {
            Field* fields = result->Fetch();
            uint32 id = fields[0].Get<uint32>();
            if (!id)
                continue;

            auto text = [&fields](uint32 index)
            {
                return fields[index].IsNull()
                    ? std::string()
                    : fields[index].Get<std::string>();
            };

            MemoryRow row;
            row.id = id;
            row.header =
                "MEM_ENTRY "
                + std::to_string(id)
                + " " + PercentEncode(text(1))
                + " " + PercentEncode(text(2))
                + " " + PercentEncode(text(3))
                + " " + std::to_string(static_cast<uint32>(
                    fields[4].Get<uint8>()))
                + " " + std::to_string(static_cast<uint32>(
                    fields[5].Get<uint8>()))
                + " " + PercentEncode(text(7))
                + " " + PercentEncode(text(8));
            row.text = text(6);

            rows.push_back(std::move(row));
        }
        while (result->NextRow());
    }

    SendLogLine(
        handler,
        "MEM_LIST_BEGIN "
        + std::to_string(botGuid)
        + " " + std::to_string(rows.size()));

    for (MemoryRow const& row : rows)
    {
        SendLogLine(handler, row.header);
        SendMemoryText(handler, row.id, row.text);
    }

    SendLogLine(
        handler,
        "MEM_LIST_END " + std::to_string(botGuid));
    return true;
}

bool HandleMemCommand(
    ChatHandler* handler, std::string const& args)
{
    std::string input = Trim(args);
    if (input.empty() || input == "bots")
        return HandleMemBotsCommand(handler);

    std::string command;
    std::string rest;
    std::istringstream iss(input);
    iss >> command;
    std::getline(iss, rest);
    rest = Trim(rest);

    if (command == "list")
        return HandleMemListCommand(handler, rest);

    SendLogLine(
        handler,
        "MEM_ERROR usage "
        + PercentEncode(
            "Supported: mem bots, "
            "mem list <botGuid> [count]"));
    return true;
}
}  // namespace

class LLMChatterCommandScript : public CommandScript
{
public:
    LLMChatterCommandScript()
        : CommandScript("LLMChatterCommandScript")
    {
    }

    ChatCommandTable GetCommands() const override
    {
        static ChatCommandTable commandTable =
        {
            { "llmc", HandleRootCommand,
              SEC_PLAYER, Console::No },
        };

        return commandTable;
    }

    static bool HandleRootCommand(
        ChatHandler* handler, Tail args)
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled())
        {
            SendAddonLine(
                handler,
                "ERROR disabled "
                + PercentEncode(
                    "mod-llm-chatter is disabled"));
            return true;
        }

        std::string input = Trim(std::string(args));
        if (input.empty() || input == "roster")
            return HandleRosterCommand(handler);

        std::string command;
        std::string rest;
        std::istringstream iss(input);
        iss >> command;
        std::getline(iss, rest);
        rest = Trim(rest);

        if (command == "get")
            return HandleGetCommand(handler, rest);

        if (command == "set")
            return HandleSetCommand(handler, rest);

        if (command == "put")
            return HandlePutCommand(handler, rest);

        if (command == "commit")
            return HandleCommitCommand(handler, rest);

        if (command == "cancel")
            return HandleCancelCommand(handler, rest);

        if (command == "setbackstory")
            return HandleSetBackstoryCommand(
                handler, rest);

        if (command == "regenbackstory")
            return HandleRegenBackstoryCommand(
                handler, rest);

        if (command == "forget")
            return HandleForgetCommand(
                handler, rest);

        if (command == "log")
            return HandleLogCommand(handler, rest);

        if (command == "mem")
            return HandleMemCommand(handler, rest);

        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Supported commands: roster, "
                "get, set, put, commit, cancel, "
                "setbackstory, regenbackstory, "
                "forget, log, mem"));
        return true;
    }
};

// Staged uploads belong to a session; a logout ends it.
class LLMChatterCommandPlayerScript : public PlayerScript
{
public:
    LLMChatterCommandPlayerScript()
        : PlayerScript(
              "LLMChatterCommandPlayerScript",
              {PLAYERHOOK_ON_LOGOUT})
    {
    }

    void OnPlayerLogout(Player* player) override
    {
        if (!player)
            return;

        std::lock_guard<std::mutex> guard(
            g_pendingEditsMutex);
        g_pendingEdits.erase(
            player->GetGUID().GetCounter());
    }
};

void AddLLMChatterCommandScripts()
{
    new LLMChatterCommandScript();
    new LLMChatterCommandPlayerScript();
}
