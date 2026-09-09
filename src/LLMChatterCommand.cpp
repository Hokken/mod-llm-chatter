/*
 * mod-llm-chatter - player command bridge for the
 * Chatter addon.
 */

#include "Chat.h"
#include "CommandScript.h"
#include "Config.h"
#include "DatabaseEnv.h"
#include "LLMChatterConfig.h"
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

        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Supported commands: roster, "
                "get, set, put, commit, cancel, "
                "setbackstory, regenbackstory, "
                "forget"));
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
