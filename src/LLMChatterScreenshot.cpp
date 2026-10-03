/* Screenshot request transport; proximity owns NPC selection and speech. */
#include "LLMChatterScreenshot.h"
#include "LLMChatterConfig.h"
#include "LLMChatterJsonFields.h"
#include "LLMChatterProximity.h"
#include "LLMChatterShared.h"
#include "DatabaseEnv.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "Timer.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <ctime>
#include <map>

namespace
{
struct Capture
{
    uint32 playerGuid;
    uint32 account;
    int64 sessionCreated;
    uint32 map;
    uint32 instance;
    float x, y, z;
    time_t expires;
    bool consumed = false;
};

std::map<std::string, Capture> _captures;
uint32 _lastPoll = 0;
bool _probed = false;
bool _available = false;

bool Enabled()
{
    auto const* c = sLLMChatterConfig;
    return c && c->IsEnabled() && c->_useEventSystem
        && c->_proxChatterEnable && c->_screenshotEnable
        && c->_screenshotProximityEnable && c->_screenshotBoundAccountId;
}

Player* BoundPlayer()
{
    WorldSession* session = sWorldSessionMgr->FindSession(
        sLLMChatterConfig->_screenshotBoundAccountId);
    if (!session || session->PlayerLoading())
        return nullptr;
    Player* player = session->GetPlayer();
    return IsProximityAnchorEligible(player) && !IsPlayerBot(player)
        ? player : nullptr;
}

bool Matches(Player* player, Capture const& capture)
{
    if (!IsProximityAnchorEligible(player) || !player->GetSession()
        || player->GetGUID().GetCounter() != capture.playerGuid
        || player->GetSession()->GetAccountId() != capture.account
        || player->GetSession()->GetCreateTime().count()
            != capture.sessionCreated
        || player->GetMapId() != capture.map
        || player->GetInstanceId() != capture.instance)
        return false;
    float dx = player->GetPositionX() - capture.x;
    float dy = player->GetPositionY() - capture.y;
    float dz = player->GetPositionZ() - capture.z;
    float radius = sLLMChatterConfig->_proxChatterScanRadius;
    return dx * dx + dy * dy + dz * dz <= radius * radius;
}

bool ValidToken(std::string const& token)
{
    return token.size() == 32 && std::all_of(
        token.begin(), token.end(), [](char c)
        {
            return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
        });
}

void Finish(uint32 account, std::string const& token)
{
    CharacterDatabase.DirectExecute(
        "UPDATE llm_screenshot_proximity SET state = 'consumed' "
        "WHERE account_id = {} AND request_token = '{}'",
        account, EscapeString(token));
}
}

void ResetScreenshotProximity()
{
    _captures.clear();
    _probed = false;
    _available = false;
    _lastPoll = 0;
}

void UpdateScreenshotProximity()
{
    if (!Enabled())
        return;
    uint32 nowMs = getMSTime();
    if (getMSTimeDiff(_lastPoll, nowMs)
        < sLLMChatterConfig->_screenshotProximityPollMs)
        return;
    _lastPoll = nowMs;
    if (!_probed)
    {
        _probed = true;
        QueryResult table = CharacterDatabase.Query(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = DATABASE() "
            "AND table_name = 'llm_screenshot_proximity'");
        _available = bool(table);
        if (!_available)
            LOG_ERROR("module", "LLMChatter: screenshot proximity disabled: "
                "apply its characters migration, then reload config");
    }
    if (!_available)
        return;

    time_t now = time(nullptr);
    for (auto it = _captures.begin(); it != _captures.end();)
        if (it->second.expires <= now)
            it = _captures.erase(it);
        else
            ++it;

    uint32 account = sLLMChatterConfig->_screenshotBoundAccountId;
    QueryResult result = CharacterDatabase.Query(
        "SELECT request_token, state, COALESCE(observation, '{{}}') "
        "FROM llm_screenshot_proximity WHERE account_id = {} "
        "AND expires_at > NOW() AND state IN ('requested','observed')",
        account);
    if (!result)
        return;
    Field* fields = result->Fetch();
    std::string token = fields[0].Get<std::string>();
    std::string state = fields[1].Get<std::string>();
    std::string observation = fields[2].Get<std::string>();
    if (!ValidToken(token))
    {
        Finish(account, token);
        return;
    }
    Player* player = BoundPlayer();
    if (state == "requested")
    {
        if (!player || !CanQueueScreenshotProximity(player))
        {
            Finish(account, token);
            return;
        }
        _captures[token] = {
            player->GetGUID().GetCounter(), account,
            player->GetSession()->GetCreateTime().count(),
            player->GetMapId(), player->GetInstanceId(),
            player->GetPositionX(), player->GetPositionY(),
            player->GetPositionZ(),
            now + sLLMChatterConfig->_screenshotProximityMaxAge};
        CharacterDatabase.DirectExecute(
            "UPDATE llm_screenshot_proximity SET state = 'ready', "
            "player_guid = {}, expires_at = DATE_ADD(NOW(), "
            "INTERVAL {} SECOND) WHERE account_id = {} "
            "AND request_token = '{}' AND state = 'requested' "
            "AND expires_at > NOW()",
            player->GetGUID().GetCounter(),
            sLLMChatterConfig->_screenshotProximityMaxAge,
            account, token);
        return;
    }

    // One server consumer: consume synchronously before queueing output.
    // Restart loses in-memory tickets and therefore fails closed.
    Finish(account, token);
    auto capture = _captures.find(token);
    if (capture == _captures.end() || capture->second.consumed)
        return;
    capture->second.consumed = true;
    if (!Matches(player, capture->second)
        || !CanQueueScreenshotProximity(player))
        return;
    LLMChatterJson::Members object;
    if (observation.size() > 8192
        || !LLMChatterJson::ReadObject(observation, object))
        return;
    if (QueueScreenshotProximity(player, token, observation))
        capture->second.expires = now
            + sLLMChatterConfig->_eventExpirationSeconds;
}

bool IsScreenshotProximityCurrent(
    Player* player, std::string const& eventJson)
{
    LLMChatterJson::Members object;
    if (!LLMChatterJson::ReadObject(eventJson, object))
        return false;
    auto field = object.find("screenshot_token");
    if (field == object.end())
        return true;
    if (!Enabled())
        return false;
    std::string token;
    if (!LLMChatterJson::String(object, "screenshot_token", token))
        return false;
    auto it = _captures.find(token);
    return it != _captures.end() && it->second.expires > time(nullptr)
        && Matches(player, it->second);
}
