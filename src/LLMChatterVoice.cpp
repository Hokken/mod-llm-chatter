/* Voice (TTS) mailbox: records lines the bound listener received. */
#include "LLMChatterVoice.h"
#include "LLMChatterVoiceCapture.h"
#include "LLMChatterVoiceTurn.h"
#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"
#include "AsyncCallbackProcessor.h"
#include "Creature.h"
#include "CreatureData.h"
#include "DBCStores.h"
#include "DatabaseEnv.h"
#include "Field.h"
#include "Group.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <atomic>
#include <cctype>
#include <chrono>
#include <cmath>
#include <iterator>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{
// Monotonic listener generation. Seeded from wall-clock ms so every
// run and reload outranks rows and presence left by earlier ones.
uint64 _generation = 0;
// Account whose presence row we last published as active.
uint32 _publishedAccount = 0;
uint32 _insertCount = 0;

constexpr uint32 RETENTION_EVERY_INSERTS = 256;

LLMChatterVoice::ChatCapture _chatCapture;
// Filter input as Player::Say sees it (the pre-hook text).
std::string const* _captureOriginal = nullptr;
PlayerScript* _captureScript = nullptr;
// Whether our capture hook runs last; re-evaluated after config load.
int8 _captureIsLast = -1;

// Playback leases: clips the agent is actually playing (rows in state
// 'playing' until play_until). They drive live geometry and the talk
// emote. World thread only, except _lastRecordedMs, which map-thread
// hooks also write through RecordVoiceLine.
struct VoiceLease
{
    bool npc = false;
    uint32 speakerGuid = 0;
    uint64 generation = 0;
    uint32 listenerGuid = 0;
    // Local epoch ms, from the query's issue time (never extended by
    // query latency).
    uint64 endsMs = 0;
    bool published = false;
    float distance = 0.0f;
    float angle = 0.0f;
    // Last published speaker position (camera pan needs it).
    float x = 0.0f;
    float y = 0.0f;
    uint64 nextEmoteMs = 0;
};

std::atomic<uint64> _lastRecordedMs{0};
std::unordered_map<uint64, VoiceLease> _leases;
QueryCallbackProcessor _leaseQueries;
bool _leaseQueryInFlight = false;
// Issue time of the newest completed lease query.
uint64 _leaseSnapshotMs = 0;
uint64 _nextLeasePollMs = 0;
// Bots to turn away once their voiced line completed (world thread).
LLMChatterVoice::TurnNotes _turnNotes;
// Bot facings waiting for their line's audio to start (world thread).
LLMChatterVoice::PendingFacings _pendingFacings;

bool CaptureIsLast()
{
    if (_captureIsLast < 0)
    {
        auto const& hooks = ScriptRegistry<PlayerScript>::EnabledHooks[
            PLAYERHOOK_CAN_PLAYER_USE_CHAT];
        _captureIsLast = !hooks.empty() && hooks.back() == _captureScript;
        if (!_captureIsLast)
            LOG_WARN("module", "LLMChatter: another OnPlayerCanUseChat "
                "script runs after the voice capture; bot say/yell lines "
                "will not be voiced");
    }
    return _captureIsLast > 0;
}

// The capture must see the final say/yell text, after every other
// OnPlayerCanUseChat script. Modules loaded after this one (a
// PlayerScript without a hook list enables every hook) would run later
// and switch voicing off, so move the capture to the end once at
// startup, before any player can chat. Every other script keeps its
// relative order; one that vetoes still stops the chain before us.
void MoveCaptureLast()
{
    auto& hooks = ScriptRegistry<PlayerScript>::EnabledHooks[
        PLAYERHOOK_CAN_PLAYER_USE_CHAT];
    auto it = std::find(hooks.begin(), hooks.end(), _captureScript);
    if (it != hooks.end() && std::next(it) != hooks.end())
    {
        hooks.erase(it);
        hooks.push_back(_captureScript);
    }
    _captureIsLast = -1;
}

uint64 EpochMs()
{
    return static_cast<uint64>(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch())
            .count());
}

bool Enabled()
{
    auto const* c = sLLMChatterConfig;
    return c && c->IsEnabled() && c->_voiceEnable
        && c->_voiceBoundAccountId;
}

Player* BoundListener()
{
    WorldSession* session = sWorldSessionMgr->FindSession(
        sLLMChatterConfig->_voiceBoundAccountId);
    if (!session || session->PlayerLoading())
        return nullptr;
    Player* player = session->GetPlayer();
    if (!player || !player->IsInWorld() || IsPlayerBot(player))
        return nullptr;
    return player;
}

bool IsBoundListener(Player* player)
{
    return Enabled() && player && player->GetSession()
        && player->GetSession()->GetAccountId()
            == sLLMChatterConfig->_voiceBoundAccountId
        && !IsPlayerBot(player);
}

// Async workers may apply writes out of order, so presence only ever
// moves forward: an older generation can never overwrite a newer one.
void PublishPresence(uint32 account, uint32 listenerGuid,
    uint32 mapId, uint32 instanceId)
{
    _generation = std::max(_generation + 1, EpochMs());
    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_voice_listener "
        "(account_id, generation, listener_guid, map_id, "
        "instance_id, updated_at) "
        "VALUES ({}, {}, {}, {}, {}, NOW(3)) "
        "ON DUPLICATE KEY UPDATE "
        "listener_guid = IF(VALUES(generation) > generation, "
        "VALUES(listener_guid), listener_guid), "
        "map_id = IF(VALUES(generation) > generation, "
        "VALUES(map_id), map_id), "
        "instance_id = IF(VALUES(generation) > generation, "
        "VALUES(instance_id), instance_id), "
        "updated_at = IF(VALUES(generation) > generation, "
        "VALUES(updated_at), updated_at), "
        "generation = GREATEST(generation, VALUES(generation))",
        account, _generation, listenerGuid, mapId, instanceId);
}

void PublishListener(Player* player)
{
    uint32 account = player->GetSession()->GetAccountId();
    PublishPresence(account, player->GetGUID().GetCounter(),
        player->GetMapId(), player->GetInstanceId());
    _publishedAccount = account;
}

void PruneOldRows()
{
    CharacterDatabase.Execute(
        "DELETE FROM llm_chatter_voice "
        "WHERE created_at < NOW(3) - INTERVAL 10 MINUTE");
    CharacterDatabase.Execute(
        "DELETE FROM llm_chatter_voice_live "
        "WHERE updated_at < NOW(3) - INTERVAL 10 MINUTE");
}

uint64 LeaseKey(bool npc, uint32 speakerGuid)
{
    return (uint64(npc) << 32) | speakerGuid;
}

bool LiveWanted()
{
    auto const* c = sLLMChatterConfig;
    return Enabled()
        && (c->_voiceLiveEnable || c->_voiceTalkEmoteEnable
            || c->_voiceTurnAwayEnable || c->_voiceFaceAtVoiceEnable);
}

// A pending facing can only matter while its line may still start.
void PrunePendingFacings(uint64 nowMs)
{
    _pendingFacings.Prune(nowMs,
        uint64(sLLMChatterConfig->_voiceMaxLagSeconds) * 1000 + 1000,
        _generation);
}

// The line's audio just started: turn the bot as delivery decided, if
// the bot, target and listener are all still where it makes sense.
void ApplyPendingFacing(LLMChatterVoice::PendingFacing const& pending,
    Player* listener)
{
    Player* bot = ObjectAccessor::FindConnectedPlayer(
        ObjectGuid::Create<HighGuid::Player>(pending.botGuid));
    if (!listener || !bot || !bot->IsInWorld()
        || bot->GetMapId() != listener->GetMapId()
        || bot->GetInstanceId() != listener->GetInstanceId()
        || !listener->InSamePhase(bot))
        return;
    float facing = 0.0f;
    if (FaceTargetIfSafe(bot, ObjectGuid(pending.targetRaw), &facing))
        NoteVoiceFacing(bot, pending.messageId, facing);
}

void PruneTurnNotes(uint64 nowMs)
{
    auto const* c = sLLMChatterConfig;
    _turnNotes.Prune(nowMs,
        (uint64(c->_voiceMaxLagSeconds) + c->_voiceTurnAwayMaxWaitSeconds)
            * 1000,
        _generation);
}

// The bot's voiced line completed: look away, as people do, unless
// anything turned or moved it since.
void TryTurnAway(LLMChatterVoice::TurnNote const& note)
{
    auto const* c = sLLMChatterConfig;
    if (!c->_voiceTurnAwayEnable)
        return;
    Player* bot = ObjectAccessor::FindConnectedPlayer(
        ObjectGuid::Create<HighGuid::Player>(note.botGuid));
    if (!bot || !bot->IsInWorld() || !IsPlayerBot(bot)
        || !bot->IsAlive() || bot->IsInCombat()
        || bot->IsNonMeleeSpellCast(false)
        || !IsSafeForChatterFacing(bot)
        || !LLMChatterVoice::StillFacing(bot->GetOrientation(),
            note.orientation,
            c->_voiceTurnAwayToleranceDeg * float(M_PI) / 180.0f)
        || !roll_chance_i(int32(c->_voiceTurnAwayChance)))
        return;
    float toRad = float(M_PI) / 180.0f;
    bot->SetFacingTo(LLMChatterVoice::TurnAwayOrientation(
        bot->GetOrientation(), c->_voiceTurnAwayMinDeg * toRad,
        c->_voiceTurnAwayMaxDeg * toRad, frand(0.0f, 1.0f),
        urand(0, 1) == 0));
}

// Runs on the world thread (ProcessReadyCallbacks in OnUpdate).
void ApplyLeaseSnapshot(QueryResult result, uint64 issuedMs)
{
    _leaseQueryInFlight = false;
    _leaseSnapshotMs = issuedMs;
    // Expired notes go before any delayed terminal row is consumed.
    uint64 nowMs = EpochMs();
    PruneTurnNotes(nowMs);
    PrunePendingFacings(nowMs);

    Player* listener = BoundListener();
    uint32 listenerGuid = listener ? listener->GetGUID().GetCounter() : 0;
    std::unordered_map<uint64, VoiceLease> current;
    if (result)
    {
        do
        {
            Field* fields = result->Fetch();
            bool npc = fields[0].Get<std::string>() == "npc";
            uint32 speakerGuid = fields[1].Get<uint32>();
            uint64 generation = fields[2].Get<uint64>();
            std::string state = fields[6].Get<std::string>();
            // A deferred facing is taken exactly once: applied when its
            // line is playing, dropped when it ended without playing.
            if (!fields[5].IsNull() && !npc && listener
                && fields[3].Get<uint32>() == listenerGuid
                && generation == _generation)
                if (auto pending = _pendingFacings.Take(
                        fields[5].Get<uint32>()))
                {
                    // Only while the clip is still sounding now: the
                    // lease end counts from the query's issue time, so
                    // a late callback cannot turn after the audio.
                    int64 leftUs = fields[4].IsNull()
                        ? 0 : fields[4].Get<int64>();
                    if (state == "playing" && leftUs > 0
                        && issuedMs + uint64(leftUs / 1000) > nowMs)
                        ApplyPendingFacing(*pending, listener);
                }
            if (state != "playing")
            {
                // A noted message's terminal row: 'played' is the
                // agent's completion acknowledgement, 'expired' a
                // cancellation. Same session and listener only.
                if (fields[5].IsNull() || npc
                    || fields[3].Get<uint32>() != listenerGuid)
                    continue;
                if (auto note = _turnNotes.OnTerminal(
                        fields[5].Get<uint32>(), state == "played",
                        generation, speakerGuid);
                    note && generation == _generation)
                    TryTurnAway(*note);
                continue;
            }

            int64 remainingUs = fields[4].IsNull()
                ? 0 : fields[4].Get<int64>();
            if (generation != _generation || remainingUs <= 0)
                continue;

            uint64 key = LeaseKey(npc, speakerGuid);
            VoiceLease lease;
            auto it = _leases.find(key);
            if (it != _leases.end() && it->second.generation == generation)
                lease = it->second;
            lease.npc = npc;
            lease.speakerGuid = speakerGuid;
            lease.generation = generation;
            lease.listenerGuid = fields[3].Get<uint32>();
            lease.endsMs = issuedMs + uint64(remainingUs / 1000);
            current[key] = lease;
        } while (result->NextRow());
    }
    _leases.swap(current);
}

void IssueLeaseQuery(uint64 nowMs)
{
    // The same single read also returns the terminal rows of noted
    // messages (completion or cancellation), via idx_message.
    std::vector<uint32> noted = _turnNotes.Ids();
    for (uint32 id : _pendingFacings.Ids())
        noted.push_back(id);
    std::string terminal;
    if (!noted.empty())
    {
        terminal = " OR (message_id IN (";
        for (std::size_t i = 0; i < noted.size(); ++i)
            terminal += (i ? "," : "") + std::to_string(noted[i]);
        terminal += ") AND state IN ('played', 'expired'))";
    }

    _leaseQueryInFlight = true;
    _leaseQueries.AddCallback(
        CharacterDatabase.AsyncQuery(Acore::StringFormat(
            "SELECT speaker_kind, speaker_guid, generation, "
            "listener_guid, "
            "TIMESTAMPDIFF(MICROSECOND, NOW(3), play_until), "
            "message_id, state "
            "FROM llm_chatter_voice "
            "WHERE account_id = {} AND ((state = 'playing' "
            "AND play_until > NOW(3)){}) ORDER BY id DESC LIMIT {}",
            sLLMChatterConfig->_voiceBoundAccountId, terminal,
            sLLMChatterConfig->_voiceMaxConcurrent + noted.size()))
            .WithCallback([nowMs](QueryResult result)
            {
                ApplyLeaseSnapshot(std::move(result), nowMs);
            }));
}

void PublishGeometry(Player* listener, Unit* speaker, VoiceLease& lease)
{
    auto const* c = sLLMChatterConfig;
    float distance = listener->GetExactDist(speaker);
    float angle = listener->GetRelativeAngle(speaker);
    float x = speaker->GetPositionX();
    float y = speaker->GetPositionY();
    if (lease.published)
    {
        float turned = std::fabs(std::remainder(angle - lease.angle,
            2.0f * float(M_PI)));
        // Moving sideways keeps distance and angle but still moves
        // the voice for camera-relative panning.
        float moved = std::hypot(x - lease.x, y - lease.y);
        if (std::fabs(distance - lease.distance)
                <= c->_voiceLiveMinDistanceChange
            && turned
                <= c->_voiceLiveMinAngleChangeDeg * float(M_PI) / 180.0f
            && moved <= c->_voiceLiveMinDistanceChange)
            return;
    }
    lease.published = true;
    lease.distance = distance;
    lease.angle = angle;
    lease.x = x;
    lease.y = y;
    // Generation only moves forward, as for presence: a late write
    // from an older session never overwrites a newer one.
    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_voice_live "
        "(account_id, speaker_kind, speaker_guid, generation, "
        "listener_guid, distance, rel_angle, speaker_x, speaker_y, "
        "updated_at) "
        "VALUES ({}, '{}', {}, {}, {}, {:.2f}, {:.4f}, {:.2f}, {:.2f}, "
        "NOW(3)) "
        "ON DUPLICATE KEY UPDATE "
        "listener_guid = IF(VALUES(generation) >= generation, "
        "VALUES(listener_guid), listener_guid), "
        "distance = IF(VALUES(generation) >= generation, "
        "VALUES(distance), distance), "
        "rel_angle = IF(VALUES(generation) >= generation, "
        "VALUES(rel_angle), rel_angle), "
        "speaker_x = IF(VALUES(generation) >= generation, "
        "VALUES(speaker_x), speaker_x), "
        "speaker_y = IF(VALUES(generation) >= generation, "
        "VALUES(speaker_y), speaker_y), "
        "updated_at = IF(VALUES(generation) >= generation, "
        "VALUES(updated_at), updated_at), "
        "generation = GREATEST(generation, VALUES(generation))",
        c->_voiceBoundAccountId, lease.npc ? "npc" : "bot",
        lease.speakerGuid, lease.generation, lease.listenerGuid,
        distance, angle, x, y);
}

void DriveLeases(uint64 nowMs)
{
    Player* listener = BoundListener();
    if (!listener)
        return;

    auto const* c = sLLMChatterConfig;
    uint32 listenerGuid = listener->GetGUID().GetCounter();
    for (auto& [key, lease] : _leases)
    {
        if (lease.listenerGuid != listenerGuid
            || lease.generation != _generation)
            continue;

        Unit* speaker = lease.npc
            ? static_cast<Unit*>(FindCreatureBySpawnId(
                listener->GetMap(), lease.speakerGuid))
            : ObjectAccessor::FindConnectedPlayer(
                ObjectGuid::Create<HighGuid::Player>(lease.speakerGuid));
        if (!speaker || !speaker->IsInWorld()
            || speaker->GetMapId() != listener->GetMapId()
            || speaker->GetInstanceId() != listener->GetInstanceId()
            || !listener->InSamePhase(speaker))
            continue;

        if (c->_voiceLiveEnable)
            PublishGeometry(listener, speaker, lease);

        // Talk while the audio plays; never over death, combat or a
        // cast, where it would fight gameplay animations.
        if (c->_voiceTalkEmoteEnable && nowMs >= lease.nextEmoteMs
            && speaker->IsAlive() && !speaker->IsInCombat()
            && !speaker->IsNonMeleeSpellCast(false))
        {
            speaker->HandleEmoteCommand(EMOTE_ONESHOT_TALK);
            lease.nextEmoteMs = nowMs + c->_voiceTalkEmoteRepeatMs;
        }
    }
}

// World update runs after MapMgr::Update has waited for its map
// workers, so unit reads and emotes here never race map updates.
void UpdateVoiceLive()
{
    // Always serviced, so an in-flight snapshot is never stranded.
    _leaseQueries.ProcessReadyCallbacks();

    if (!LiveWanted())
    {
        _leases.clear();
        _turnNotes.Clear();
        _pendingFacings.Clear();
        return;
    }

    // Idle gate: a recorded line may still start until its MaxLag
    // deadline, so keep polling until a snapshot taken after that
    // deadline has come back; then only running leases keep us busy.
    uint64 recorded = _lastRecordedMs.load(std::memory_order_relaxed);
    uint64 startDeadline = recorded
        + uint64(sLLMChatterConfig->_voiceMaxLagSeconds) * 1000;
    bool mayStart = recorded && _leaseSnapshotMs <= startDeadline;
    if (_leases.empty() && !mayStart && !_leaseQueryInFlight
        && _turnNotes.Empty() && _pendingFacings.Empty())
        return;

    uint64 nowMs = EpochMs();
    if (nowMs < _nextLeasePollMs)
        return;
    _nextLeasePollMs = nowMs + sLLMChatterConfig->_voiceLiveIntervalMs;
    PruneTurnNotes(nowMs);
    PrunePendingFacings(nowMs);

    for (auto it = _leases.begin(); it != _leases.end();)
    {
        if (it->second.endsMs <= nowMs)
            it = _leases.erase(it);
        else
            ++it;
    }

    if (!_leaseQueryInFlight
        && (mayStart || !_leases.empty() || !_turnNotes.Empty()
            || !_pendingFacings.Empty()))
        IssueLeaseQuery(nowMs);
    if (!_leases.empty())
        DriveLeases(nowMs);
}

char const* ChannelName(LLMChatterVoiceChannel channel)
{
    switch (channel)
    {
        case VOICE_CHANNEL_SAY:
            return "say";
        case VOICE_CHANNEL_YELL:
            return "yell";
        case VOICE_CHANNEL_MSAY:
            return "msay";
        case VOICE_CHANNEL_PARTY:
            return "party";
        default:
            return "";
    }
}

float ChannelRadius(LLMChatterVoiceChannel channel)
{
    auto const* c = sLLMChatterConfig;
    switch (channel)
    {
        case VOICE_CHANNEL_SAY:
        case VOICE_CHANNEL_MSAY:
            return std::min(c->_voiceSayRadius,
                sWorld->getFloatConfig(CONFIG_LISTEN_RANGE_SAY));
        case VOICE_CHANNEL_YELL:
            return std::min(c->_voiceYellRadius,
                sWorld->getFloatConfig(CONFIG_LISTEN_RANGE_YELL));
        case VOICE_CHANNEL_PARTY:
            return c->_voicePartyRadius;
        default:
            return 0.0f;
    }
}

// Mirrors who the send reached: a subset is fine (audio omitted),
// a superset never is.
bool ReceivedBy(Player* listener, Unit* speaker,
    LLMChatterVoiceChannel channel)
{
    if (channel == VOICE_CHANNEL_PARTY)
    {
        Player* bot = speaker->ToPlayer();
        Group* group = bot ? bot->GetGroup() : nullptr;
        if (!group || listener->GetGroup() != group)
            return false;
        // Raid party lines only reach the speaker's subgroup.
        return !group->isRaidGroup()
            || group->SameSubGroup(bot, listener);
    }

    if (!listener->HaveAtClient(speaker))
        return false;
    // NPC msay goes through Unit::Talk's PlayerDistWorker: client
    // visibility and range, both already checked.
    if (channel == VOICE_CHANNEL_MSAY)
        return true;
    // Bot say/yell use MessageDistDeliverer, which skips a listener
    // viewing through another object unless it rides a vehicle.
    if (listener->GetSeer() != listener && !listener->GetVehicle())
        return false;
    // Bot say/yell use the faction language; across factions the
    // client renders gibberish, so speaking it aloud would leak it.
    if (Player* bot = speaker->ToPlayer())
        if (bot->GetTeamId() != listener->GetTeamId())
            return false;
    return true;
}

void SpeakerIdentity(Unit* speaker, uint32& guid, char const*& kind,
    uint8& race, uint8& gender, uint8& cls)
{
    if (Player* bot = speaker->ToPlayer())
    {
        guid = bot->GetGUID().GetCounter();
        kind = "bot";
        race = bot->getRace();
        gender = GetTrueGender(bot);
        cls = bot->getClass();
        return;
    }

    Creature* npc = speaker->ToCreature();
    guid = npc ? npc->GetSpawnId() : 0;
    kind = "npc";
    cls = 0;
    // Unknown gender/race let the agent fall back to default voices.
    gender = GENDER_NONE;
    race = 0;
    uint32 displayId = speaker->GetDisplayId();
    if (CreatureModelInfo const* model =
            sObjectMgr->GetCreatureModelInfo(displayId))
        gender = model->gender;
    if (CreatureDisplayInfoEntry const* display =
            sCreatureDisplayInfoStore.LookupEntry(displayId))
        if (CreatureDisplayInfoExtraEntry const* extra =
                sCreatureDisplayInfoExtraStore.LookupEntry(
                    display->ExtendedDisplayInfoID))
            race = static_cast<uint8>(extra->DisplayRaceID);
}
}  // namespace

uint32 ParseVoiceChannels(std::string const& configured)
{
    uint32 mask = VOICE_CHANNEL_NONE;
    std::stringstream stream(configured);
    std::string token;
    while (std::getline(stream, token, ','))
    {
        token.erase(std::remove_if(token.begin(), token.end(),
            [](unsigned char ch) { return std::isspace(ch); }),
            token.end());
        std::transform(token.begin(), token.end(), token.begin(),
            [](unsigned char ch) { return std::tolower(ch); });
        if (token.empty())
            continue;
        if (token == "say")
            mask |= VOICE_CHANNEL_SAY;
        else if (token == "yell")
            mask |= VOICE_CHANNEL_YELL;
        else if (token == "msay")
            mask |= VOICE_CHANNEL_MSAY;
        else if (token == "party")
            mask |= VOICE_CHANNEL_PARTY;
        else
            LOG_WARN("module", "LLMChatter: unknown voice channel "
                "'{}' in LLMChatter.Voice.Channels; ignored", token);
    }
    return mask;
}

bool IsVoiceChannelWanted(LLMChatterVoiceChannel channel)
{
    return Enabled() && (sLLMChatterConfig->_voiceChannelMask & channel);
}

bool ArmVoiceChatCapture(Player* bot, LLMChatterVoiceChannel channel,
    std::string const& message)
{
    if (!bot || !IsVoiceChannelWanted(channel) || !CaptureIsLast())
        return false;
    _chatCapture.Arm(bot->GetGUID().GetCounter(),
        channel == VOICE_CHANNEL_YELL ? CHAT_MSG_YELL : CHAT_MSG_SAY);
    _captureOriginal = &message;
    return true;
}

bool TakeVoiceChatCapture(std::string& broadcastText)
{
    bool filtered = false;
    if (_chatCapture.armed && _chatCapture.reached && _captureOriginal)
    {
        // Same check, same input as Player::Say/Yell after the hooks.
        ServerConfigs filterConfig =
            _chatCapture.type == CHAT_MSG_YELL
                ? CONFIG_CHAT_FILTER_YELL : CONFIG_CHAT_FILTER_SAY;
        filtered = sWorld->getBoolConfig(filterConfig)
            && sObjectMgr->IsChatFiltered(*_captureOriginal);
    }
    _captureOriginal = nullptr;
    return _chatCapture.Take(filtered, broadcastText);
}

void ResetVoice()
{
    _captureIsLast = -1;
    // Leases and turn notes belong to the previous generation;
    // snapshots still in flight are filtered by generation.
    _leases.clear();
    _turnNotes.Clear();
    _pendingFacings.Clear();
    if (!Enabled())
    {
        // Deactivated: invalidate whatever the agent may still hold.
        if (_publishedAccount)
        {
            PublishPresence(_publishedAccount, 0, 0, 0);
            _publishedAccount = 0;
        }
        return;
    }

    uint32 account = sLLMChatterConfig->_voiceBoundAccountId;
    if (_publishedAccount && _publishedAccount != account)
        PublishPresence(_publishedAccount, 0, 0, 0);

    PruneOldRows();
    _insertCount = 0;

    if (Player* player = BoundListener())
        PublishListener(player);
    else
    {
        PublishPresence(account, 0, 0, 0);
        _publishedAccount = account;
    }
}

bool RecordVoiceLine(Unit* speaker, LLMChatterVoiceChannel channel,
    std::string const& text, uint32 messageId)
{
    if (!Enabled()
        || !(sLLMChatterConfig->_voiceChannelMask & channel)
        || !speaker || text.empty())
        return false;

    Player* listener = BoundListener();
    if (!listener || listener == speaker
        || listener->GetMapId() != speaker->GetMapId()
        || listener->GetInstanceId() != speaker->GetInstanceId())
        return false;

    float radius = ChannelRadius(channel);
    float distSq = listener->GetExactDistSq(speaker);
    if (distSq > radius * radius || !listener->InSamePhase(speaker)
        || !ReceivedBy(listener, speaker, channel))
        return false;

    uint32 speakerGuid = 0;
    char const* kind = "";
    uint8 race = 0;
    uint8 gender = GENDER_NONE;
    uint8 cls = 0;
    SpeakerIdentity(speaker, speakerGuid, kind, race, gender, cls);

    // Deadline fixed at the send, so a DB backlog cannot make old
    // speech look fresh to the agent.
    uint64 nowMs = EpochMs();
    uint64 expiresMs = nowMs
        + uint64(sLLMChatterConfig->_voiceMaxLagSeconds) * 1000;
    std::string messageSql = messageId
        ? std::to_string(messageId) : "NULL";

    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_voice "
        "(account_id, listener_guid, generation, message_id, "
        "speaker_guid, speaker_kind, speaker_race, speaker_gender, "
        "speaker_class, channel, text, distance, rel_angle, "
        "speaker_x, speaker_y, speaker_z, map_id, instance_id, "
        "created_at, expires_at) VALUES "
        "({}, {}, {}, {}, {}, '{}', {}, {}, {}, '{}', '{}', "
        "{:.2f}, {:.4f}, {:.2f}, {:.2f}, {:.2f}, {}, {}, "
        "FROM_UNIXTIME({:.3f}), FROM_UNIXTIME({:.3f}))",
        listener->GetSession()->GetAccountId(),
        listener->GetGUID().GetCounter(), _generation, messageSql,
        speakerGuid, kind, race, gender, cls, ChannelName(channel),
        EscapeString(text), std::sqrt(distSq),
        listener->GetRelativeAngle(speaker),
        speaker->GetPositionX(), speaker->GetPositionY(),
        speaker->GetPositionZ(), speaker->GetMapId(),
        speaker->GetInstanceId(), nowMs / 1000.0, expiresMs / 1000.0);

    // Opens the lease poll window; see UpdateVoiceLive.
    _lastRecordedMs.store(nowMs, std::memory_order_relaxed);

    if (++_insertCount % RETENTION_EVERY_INSERTS == 0)
        PruneOldRows();
    return true;
}

void NoteVoiceFacing(Player* bot, uint32 messageId, float facing)
{
    auto const* c = sLLMChatterConfig;
    if (!Enabled() || !c->_voiceTurnAwayEnable || !bot || !messageId
        || !IsPlayerBot(bot))
        return;
    // Queued delivery runs on the world thread, like the lease
    // tracker that consumes these notes.
    _turnNotes.Note({messageId, bot->GetGUID().GetCounter(),
        facing, _generation, EpochMs()},
        c->_voiceTurnAwayMaxNotes);
}

LLMChatterVoiceChannel VoiceChannelForDelivery(std::string const& channel)
{
    if (channel == "say")
        return VOICE_CHANNEL_SAY;
    if (channel == "yell")
        return VOICE_CHANNEL_YELL;
    if (channel == "party")
        return VOICE_CHANNEL_PARTY;
    return VOICE_CHANNEL_NONE;
}

bool IsVoiceFacingDeferred(LLMChatterVoiceChannel channel)
{
    return channel != VOICE_CHANNEL_NONE
        && sLLMChatterConfig->_voiceFaceAtVoiceEnable
        && IsVoiceChannelWanted(channel);
}

void NotePendingFacing(Player* bot, uint32 messageId, ObjectGuid target)
{
    auto const* c = sLLMChatterConfig;
    if (!Enabled() || !c->_voiceFaceAtVoiceEnable || !bot || !messageId
        || target.IsEmpty())
        return;
    _pendingFacings.Add({messageId, bot->GetGUID().GetCounter(),
        target.GetRawValue(), _generation, EpochMs()},
        c->_voiceFaceAtVoiceMaxPending);
}

// Presence follows the bound listener's session and map; each event
// bumps the generation so in-flight rows from before it never play.
class LLMChatterVoicePlayerScript : public PlayerScript
{
public:
    LLMChatterVoicePlayerScript()
        : PlayerScript(
              "LLMChatterVoicePlayerScript",
              {PLAYERHOOK_ON_LOGIN,
               PLAYERHOOK_ON_LOGOUT,
               PLAYERHOOK_ON_MAP_CHANGED})
    {
    }

    void OnPlayerLogin(Player* player) override
    {
        if (IsBoundListener(player))
            PublishListener(player);
    }

    void OnPlayerLogout(Player* player) override
    {
        if (!IsBoundListener(player))
            return;
        PublishPresence(player->GetSession()->GetAccountId(),
            0, 0, 0);
    }

    void OnPlayerMapChanged(Player* player) override
    {
        if (IsBoundListener(player))
            PublishListener(player);
    }
};

// Sees a bot say/yell after every earlier OnPlayerCanUseChat hook,
// with their rewrites; only while a delivery send is armed.
class LLMChatterVoiceChatCaptureScript : public PlayerScript
{
public:
    LLMChatterVoiceChatCaptureScript()
        : PlayerScript(
              "LLMChatterVoiceChatCaptureScript",
              {PLAYERHOOK_CAN_PLAYER_USE_CHAT})
    {
    }

    bool OnPlayerCanUseChat(Player* player, uint32 type,
        uint32 /*language*/, std::string& msg) override
    {
        if (_chatCapture.armed && player)
            _chatCapture.Observe(player->GetGUID().GetCounter(), type,
                msg);
        return true;
    }
};

// Follows clips the agent is playing: live geometry and talk emote.
// Returns at once while no voiced line can be starting or playing.
class LLMChatterVoiceLiveScript : public WorldScript
{
public:
    LLMChatterVoiceLiveScript()
        : WorldScript("LLMChatterVoiceLiveScript",
              {WORLDHOOK_ON_STARTUP, WORLDHOOK_ON_UPDATE})
    {
    }

    // All modules' scripts are registered by now, no player online.
    void OnStartup() override
    {
        MoveCaptureLast();
    }

    void OnUpdate(uint32 /*diff*/) override
    {
        UpdateVoiceLive();
    }
};

void AddLLMChatterVoiceScripts()
{
    new LLMChatterVoicePlayerScript();
    new LLMChatterVoiceLiveScript();
    _captureScript = new LLMChatterVoiceChatCaptureScript();
}
