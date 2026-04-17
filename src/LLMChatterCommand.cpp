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
#include "Player.h"
#include "ScriptMgr.h"

#include <algorithm>
#include <cctype>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;

namespace
{
std::string const kAddonPrefix = "CHATTER_ADDON";

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

    if (value.size() > maxLen)
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

    if (!ValidateField(handler, "Trait 1", trait1, 64)
        || !ValidateField(handler, "Trait 2", trait2, 64)
        || !ValidateField(handler, "Trait 3", trait3, 64))
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

    CharacterDatabase.Execute(
        "INSERT INTO llm_bot_identities "
        "(bot_guid, bot_name, trait1, trait2, "
        " trait3, tone, farewell_msg, backstory, "
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

    // Auto-regenerate backstory for new traits
    std::string bsExtra =
        "{\"bot_guid\": "
        + std::to_string(botGuid)
        + ", \"player_guid\": "
        + std::to_string(playerGuid)
        + "}";
    QueueChatterEvent(
        "bot_backstory_regen",
        "player",
        0, 0, 5, "",
        botGuid, "",
        0, "", 0,
        bsExtra,
        5, 120, true);

    SendAddonLine(
        handler,
        "UPDATED "
        + std::to_string(botGuid)
        + " "
        + PercentEncode(profile.name));
    SendAddonLine(
        handler,
        "PROFILE "
        + std::to_string(botGuid)
        + " " + PercentEncode(profile.name)
        + " " + PercentEncode(trait1)
        + " " + PercentEncode(trait2)
        + " " + PercentEncode(trait3)
        + " " + PercentEncode(""));
    SendAddonLine(
        handler,
        "BACKSTORY "
        + std::to_string(botGuid)
        + " " + PercentEncode(""));
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

    std::string backstory =
        Trim(PercentDecode(bsToken));
    if (backstory.empty())
    {
        SendAddonLine(
            handler,
            "ERROR validation "
            + PercentEncode(
                "Backstory cannot be empty"));
        return true;
    }

    if (backstory.size() > 1000)
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

        if (command == "setbackstory")
            return HandleSetBackstoryCommand(
                handler, rest);

        if (command == "regenbackstory")
            return HandleRegenBackstoryCommand(
                handler, rest);

        SendAddonLine(
            handler,
            "ERROR usage "
            + PercentEncode(
                "Supported commands: roster, "
                "get, set, setbackstory, "
                "regenbackstory"));
        return true;
    }
};

void AddLLMChatterCommandScripts()
{
    new LLMChatterCommandScript();
}
