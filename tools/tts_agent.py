"""Voice Agent — host-side TTS playback for bot chatter.

Runs on the Windows host (not in Docker), next to the game client.
The worldserver records each line the bound player actually received
into llm_chatter_voice; this agent claims those rows, synthesizes
them, revalidates the listener and plays them with distance volume
and stereo panning. Text chat never waits on it.

Usage (from the AzerothCore workspace root):
    python modules/mod-llm-chatter/tools/tts_agent.py --config env/dist/etc/modules/mod_llm_chatter.conf
    python modules/mod-llm-chatter/tools/tts_agent.py --config ... --list-voices

Requirements (host-side, same interpreter):
    python -m pip install -r modules/mod-llm-chatter/tools/requirements.txt
    python -m pip install -r modules/mod-llm-chatter/tools/requirements-voice.txt
"""

import argparse
import logging
import math
import sys
import threading
import time
from pathlib import Path

from chatter_shared import parse_config
from tts_engines import (
    ElevenLabsEngine, LruClipCache, QuotaExhausted, SynthesisError,
    clean_voice_text, compute_gain, compute_pan, load_voice_map,
)

log = logging.getLogger("tts_agent")

TOOLS_DIR = Path(__file__).resolve().parent
QUOTA_LOG_EVERY_CLIPS = 100
PRUNE_EVERY_SECONDS = 300
FAILURE_BACKOFF_AFTER = 3
FAILURE_BACKOFF_SECONDS = 5.0

FETCH_SQL = (
    "SELECT v.id, v.listener_guid, v.generation, v.speaker_guid, "
    "v.speaker_kind, v.speaker_race, v.speaker_gender, v.channel, "
    "v.text, v.distance, v.rel_angle, v.speaker_x, v.speaker_y, "
    "p.generation AS p_generation, p.listener_guid AS p_listener, "
    "p.map_id AS p_map, "
    "TIMESTAMPDIFF(MICROSECOND, NOW(3), v.expires_at) DIV 1000 "
    "AS ms_left, "
    "TIMESTAMPDIFF(MICROSECOND, v.created_at, NOW(3)) DIV 1000 "
    "AS age_ms "
    "FROM llm_chatter_voice v "
    "LEFT JOIN llm_chatter_voice_listener p "
    "ON p.account_id = v.account_id "
    "WHERE v.account_id = %s AND v.state = 'pending' "
    "AND v.expires_at > NOW(3) ORDER BY v.id LIMIT 8"
)

REVALIDATE_SQL = (
    "SELECT v.state, v.listener_guid, v.generation, "
    "p.generation AS p_generation, p.listener_guid AS p_listener, "
    "TIMESTAMPDIFF(MICROSECOND, NOW(3), v.expires_at) DIV 1000 "
    "AS ms_left "
    "FROM llm_chatter_voice v "
    "LEFT JOIN llm_chatter_voice_listener p "
    "ON p.account_id = v.account_id WHERE v.id = %s"
)

# Playback lease: the server follows (geometry, talk emote) only rows
# in 'playing' until play_until. Taken atomically with the row's
# deadline and the current presence (same generation and listener).
LEASE_SQL = (
    "UPDATE llm_chatter_voice v "
    "JOIN llm_chatter_voice_listener p ON p.account_id = v.account_id "
    "SET v.state = 'playing', "
    "v.play_until = NOW(3) + INTERVAL %s MICROSECOND "
    "WHERE v.id = %s AND v.state = 'claimed' "
    "AND v.expires_at > NOW(3) AND v.listener_guid <> 0 "
    "AND p.generation = v.generation "
    "AND p.listener_guid = v.listener_guid"
)

# Camera mode: who and where the listener is, to gate client samples.
PRESENCE_SQL = (
    "SELECT generation, listener_guid, map_id "
    "FROM llm_chatter_voice_listener WHERE account_id = %s"
)

LIVE_SQL = (
    "SELECT l.speaker_kind, l.speaker_guid, l.generation, "
    "l.listener_guid, l.distance, l.rel_angle, l.speaker_x, l.speaker_y, "
    "p.generation AS p_generation, p.listener_guid AS p_listener, "
    "p.map_id AS p_map "
    "FROM llm_chatter_voice_live l "
    "JOIN llm_chatter_voice_listener p ON p.account_id = l.account_id "
    "WHERE l.account_id = %s "
    "AND l.updated_at > NOW(3) - INTERVAL %s SECOND"
)


def hex_option(value, default: int) -> int:
    """An address option: '0xB7436C' or decimal; default if invalid."""
    try:
        return int(str(value).strip(), 0) if value not in (None, '')             else default
    except ValueError:
        return default


def load_voice_config(raw: dict) -> dict:
    """Extract voice-agent config with defaults."""
    def num(key, default, low, high, cast=float):
        try:
            value = cast(raw.get(key, default))
        except (TypeError, ValueError):
            value = cast(default)
        return max(low, min(high, value))

    falloff = raw.get('LLMChatter.Voice.Falloff', 'inverse').lower()
    near_falloff = raw.get(
        'LLMChatter.Voice.Proximity.Falloff', 'linear').lower()
    return {
        'enable': raw.get('LLMChatter.Voice.Enable', '0') == '1',
        'bound_account_id': num(
            'LLMChatter.Voice.BoundAccountId', 0, 0, 2**32 - 1, int),
        'provider': raw.get(
            'LLMChatter.Voice.Provider', 'elevenlabs').lower(),
        'elevenlabs_api_key': raw.get(
            'LLMChatter.Voice.ElevenLabs.ApiKey', ''),
        'elevenlabs_model': raw.get(
            'LLMChatter.Voice.ElevenLabs.Model', 'eleven_flash_v2_5'),
        'elevenlabs_output_format': raw.get(
            'LLMChatter.Voice.ElevenLabs.OutputFormat', 'pcm_22050'),
        'voice_map_file': raw.get(
            'LLMChatter.Voice.VoiceMapFile', 'voice_map.json'),
        'master_volume': num(
            'LLMChatter.Voice.MasterVolume', 80, 0, 100) / 100.0,
        'falloff': falloff if falloff in ('linear', 'inverse')
        else 'inverse',
        'ref_distance': num('LLMChatter.Voice.RefDistance', 5, 0.1, 100),
        'rolloff': num('LLMChatter.Voice.Rolloff', 1.0, 0.0, 10.0),
        'min_gain': num('LLMChatter.Voice.MinGain', 0.15, 0.0, 1.0),
        # Say, yell and NPC say: fade to silence at the channel radius,
        # so a voice never comes from a speaker you cannot place.
        'proximity_falloff': near_falloff
        if near_falloff in ('linear', 'inverse') else 'linear',
        'proximity_min_gain': num(
            'LLMChatter.Voice.Proximity.MinGain', 0.0, 0.0, 1.0),
        'pan_enable': raw.get('LLMChatter.Voice.Pan.Enable', '1') == '1',
        'pan_width': num('LLMChatter.Voice.Pan.Width', 0.8, 0.0, 1.0),
        'say_radius': num('LLMChatter.Voice.SayRadius', 40, 1, 300),
        'yell_radius': num('LLMChatter.Voice.YellRadius', 300, 1, 1000),
        'party_radius': num('LLMChatter.Voice.PartyRadius', 100, 1, 1000),
        'max_concurrent': num(
            'LLMChatter.Voice.MaxConcurrent', 2, 1, 4, int),
        'turn_taking': raw.get('LLMChatter.Voice.TurnTaking', '1') == '1',
        'max_waiting': num('LLMChatter.Voice.MaxWaiting', 2, 0, 4, int),
        'live_enable': raw.get('LLMChatter.Voice.Live.Enable', '1') == '1',
        'live_fresh_seconds': num(
            'LLMChatter.Voice.Live.FreshSeconds', 2, 1, 10, int),
        'live_ramp_ms': num('LLMChatter.Voice.Live.RampMs', 200, 0, 1000),
        # Audio watchdog: reopen an output stream that stopped calling
        # back (device or session change), with a reopen backoff.
        'audio_stall': num(
            'LLMChatter.Voice.Audio.StallMs', 1000, 200, 10000) / 1000.0,
        'audio_reopen': num(
            'LLMChatter.Voice.Audio.ReopenSeconds', 5, 1, 60),
        # Camera-relative panning (read-only client camera; Windows).
        'pan_source': 'camera' if raw.get(
            'LLMChatter.Voice.Pan.Source', 'character').lower() == 'camera'
        else 'character',
        'camera_process_name': raw.get(
            'LLMChatter.Voice.Camera.ProcessName', 'Wow.exe'),
        'camera_process_id': num(
            'LLMChatter.Voice.Camera.ProcessId', 0, 0, 2**32 - 1, int),
        'camera_poll': num(
            'LLMChatter.Voice.Camera.PollMs', 50, 20, 500) / 1000.0,
        'camera_max_age': num(
            'LLMChatter.Voice.Camera.MaxAgeMs', 200, 50, 2000) / 1000.0,
        'camera_fail_ticks': num(
            'LLMChatter.Voice.Camera.FailTicks', 5, 1, 100, int),
        'camera_max_jump': num(
            'LLMChatter.Voice.Camera.MaxJumpYards', 50, 5, 500),
        'camera_rebaseline_ticks': num(
            'LLMChatter.Voice.Camera.RebaselineTicks', 3, 1, 20, int),
        'camera_rescan': num(
            'LLMChatter.Voice.Camera.RescanSeconds', 5, 1, 60),
        'camera_yaw_offset': math.radians(num(
            'LLMChatter.Voice.Camera.YawOffsetDeg', 0, -180, 180)),
        'camera_offsets': {
            name: hex_option(raw.get(key), default)
            for name, key, default in (
                ('world_frame', 'LLMChatter.Voice.Camera.WorldFrame',
                 0xB7436C),
                ('active_camera', 'LLMChatter.Voice.Camera.ActiveOffset',
                 0x7E20),
                ('camera_type', 'LLMChatter.Voice.Camera.Type', 0xA1EA54),
                ('player_guid', 'LLMChatter.Voice.Camera.PlayerGuid',
                 0xCA1238),
                ('map_id', 'LLMChatter.Voice.Camera.MapId', 0xADFBC4),
                ('world_loaded', 'LLMChatter.Voice.Camera.WorldLoaded',
                 0xBEBA40))},
        # Hard cap of two concurrent provider requests (efficiency).
        'max_in_flight': num(
            'LLMChatter.Voice.MaxInFlight', 2, 1, 2, int),
        'poll_interval': num(
            'LLMChatter.Voice.PollIntervalMs', 150, 50, 5000) / 1000.0,
        'idle_poll_interval': num(
            'LLMChatter.Voice.IdlePollIntervalMs', 1000, 100, 10000)
        / 1000.0,
        'cache_bytes': num(
            'LLMChatter.Voice.CacheMB', 32, 0, 1024, int) * 1024 * 1024,
        # Host-side override, as for the screenshot agent: the
        # Docker hostname in Database.Host is not resolvable here.
        'db_host': raw.get(
            'LLMChatter.Voice.DBHost',
            raw.get('LLMChatter.Screenshot.DBHost',
                    raw.get('LLMChatter.Database.Host', '127.0.0.1'))),
        'db_port': int(raw.get('LLMChatter.Database.Port', '3306')),
        'db_user': raw.get('LLMChatter.Database.User', 'root'),
        'db_pass': raw.get('LLMChatter.Database.Password', 'password'),
        'db_name': raw.get(
            'LLMChatter.Database.Name', 'acore_characters'),
    }


def get_db_connection(config: dict):
    """Open a MySQL connection to acore_characters."""
    import mysql.connector
    return mysql.connector.connect(
        host=config['db_host'],
        port=config['db_port'],
        user=config['db_user'],
        password=config['db_pass'],
        database=config['db_name'],
        buffered=True,
        autocommit=False,
    )


def decide(row_generation, row_listener, presence_generation,
           presence_listener) -> str:
    """Pre-playback contract: 'play', 'expire' or 'wait'.

    Presence moves forward asynchronously, so a row newer than the
    published presence waits for it (or for its own expiry).
    """
    if presence_generation is None or not row_listener:
        return 'wait'
    if row_generation < presence_generation:
        return 'expire'
    if row_generation > presence_generation:
        return 'wait'
    if presence_listener and presence_listener == row_listener:
        return 'play'
    return 'expire'


def set_below_normal_priority() -> None:
    """Never compete with the game client for CPU (Windows only)."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        below_normal = 0x00004000
        kernel32.SetPriorityClass(kernel32.GetCurrentProcess(),
                                  below_normal)
    except Exception as exc:
        log.warning('Could not lower process priority: %s', exc)


def open_output_stream(sample_rate: int, callback):
    import sounddevice as sd
    return sd.OutputStream(samplerate=sample_rate, channels=2,
                           dtype='float32', callback=callback)


class Mixer:
    """One persistent stereo output stream mixing short clips.

    Clips start only through start(), right after revalidation; there
    is no audio queue that could outlive it. With turn-taking, ready
    clips wait for their turn (bounded), in arrival order.

    Two locks: the audio lock (callback, clip list, gains) and the
    turn Condition (tickets, owner). The callback only ever takes the
    audio lock, and no DB work happens under either, so a slow
    revalidation can never stall audio output.
    """

    def __init__(self, sample_rate: int, max_concurrent: int,
                 ramp_ms: float = 200.0, turn_taking: bool = False,
                 max_waiting: int = 2, stream_factory=None,
                 clock=time.monotonic):
        import numpy as np
        self._np = np
        self.sample_rate = sample_rate
        self.max_concurrent = max_concurrent
        # One-pole smoothing: each frame closes this fraction of the gap
        # to the target, so updates blend into one glide whatever their
        # size (ramp_ms is the time constant; 0 = jump at once).
        frames = sample_rate * ramp_ms / 1000.0
        self._smooth = 1.0 if frames < 1.0 else 1.0 - math.exp(-1.0 / frames)
        self.turn_taking = turn_taking
        self.max_waiting = max_waiting
        self._lock = threading.Lock()
        self._clips = []
        self._turn = threading.Condition()
        self._queue = []
        self._owner = None
        self._next_ticket = 1
        self._factory = stream_factory or open_output_stream
        self._clock = clock
        # Heartbeat: when the output device last asked for audio. A
        # stream that stops calling back (device or session change) is
        # detected and reopened by the agent loop.
        self._last_callback = clock()
        # Clips dropped by a recovery, kept until the agent takes them
        # (survives a failed reopen), and whether the output is usable.
        self._dropped = []
        self._backend_ok = False
        self._stream = self._factory(sample_rate, self._callback)
        self._stream.start()
        self._backend_ok = True

    # ---------------------------------------------- audio

    def _callback(self, outdata, frames, _time, _status):
        np = self._np
        self._last_callback = self._clock()
        outdata.fill(0)
        with self._lock:
            if not self._clips:
                return
            still = []
            for clip in self._clips:
                mono = clip['mono'][clip['pos']:clip['pos'] + frames]
                count = len(mono)
                start = clip['gain']
                target = clip['target']
                delta = target - start
                if count == 0 or not delta.any():
                    outdata[:count] += mono[:, None] * start
                else:
                    # Exponential approach per frame: continuous, no
                    # clicks, never overshoots.
                    remain = ((1.0 - self._smooth) ** np.arange(
                        1, count + 1, dtype=np.float32))[:, None]
                    gains = target - delta * remain
                    outdata[:count] += mono[:, None] * gains
                    end = gains[-1]
                    # Snap the inaudible tail so the fast path resumes.
                    if np.abs(target - end).max() < 1e-4:
                        end = target
                    clip['gain'] = end.astype(np.float32).copy()
                clip['pos'] += count
                if clip['pos'] < len(clip['mono']):
                    still.append(clip)
            self._clips = still
        np.clip(outdata, -1.0, 1.0, out=outdata)

    def stalled(self, stall_seconds: float) -> bool:
        """True when the output needs recovery.

        That is: no usable backend (a failed or ongoing reopen, retried
        without waiting for a new clip), a health query that raises, a
        stream reporting inactive, or clips present while the device has
        not called back for stall_seconds. An idle healthy mixer is
        never stalled.
        """
        if not self._backend_ok:
            return True
        try:
            active = getattr(self._stream, 'active', True)
        except Exception:
            return True
        if active is False:
            return True
        with self._lock:
            busy = bool(self._clips)
        return busy and self._clock() - self._last_callback > stall_seconds

    def reopen(self) -> None:
        """Replace the output stream on the current default device.

        The stuck clips are moved to the dropped outbox first (see
        take_dropped), so they are never lost even if opening fails.
        While unavailable, start() refuses clips. Raises on failure; a
        partially created stream is closed.
        """
        with self._lock:
            self._backend_ok = False
            self._dropped.extend(clip['meta'] for clip in self._clips)
            self._clips = []
        old, self._stream = self._stream, None
        for action in ('abort', 'close'):
            try:
                getattr(old, action, lambda: None)()
            except Exception:
                pass
        stream = self._factory(self.sample_rate, self._callback)
        try:
            stream.start()
        except Exception:
            try:
                stream.close()
            except Exception:
                pass
            raise
        self._stream = stream
        self._last_callback = self._clock()
        with self._lock:
            self._backend_ok = True

    def take_dropped(self) -> list:
        """Metadata of clips dropped by recoveries since the last call."""
        with self._lock:
            dropped, self._dropped = self._dropped, []
        return dropped

    def _idle(self) -> bool:
        with self._lock:
            return not self._clips

    def playing(self) -> dict:
        """speaker -> clip metadata, for clips still sounding."""
        with self._lock:
            return {c['meta']['speaker']: c['meta'] for c in self._clips}

    def active(self) -> bool:
        with self._turn:
            if self._queue or self._owner is not None:
                return True
        return not self._idle()

    def set_target(self, row_id, left: float, right: float) -> None:
        """Retarget one clip, matched by its row (not just speaker)."""
        np = self._np
        with self._lock:
            for clip in self._clips:
                if clip['meta'].get('row') == row_id:
                    clip['target'] = np.array([left, right],
                                              dtype=np.float32)

    def start(self, pcm: bytes, left: float, right: float, meta,
              ticket=None):
        """Start a clip now; None on success, else the refusal reason.

        With turn-taking only the turn owner may call it, and the turn
        ends here whatever the outcome.
        """
        np = self._np
        try:
            if not pcm or len(pcm) % 2:
                return 'bad audio'
            mono = (np.frombuffer(pcm, dtype='<i2').astype(np.float32)
                    / 32768)
            gains = np.array([left, right], dtype=np.float32)
            with self._lock:
                # No clip starts on an output being reopened or
                # unavailable: it could never be heard.
                if not self._backend_ok:
                    return 'audio unavailable'
                if not self.turn_taking:
                    if any(c['meta']['speaker'] == meta['speaker']
                           for c in self._clips):
                        return 'speaker busy'
                    if len(self._clips) >= self.max_concurrent:
                        return 'mixer full'
                self._clips.append({'mono': mono, 'pos': 0,
                                    'gain': gains,
                                    'target': gains.copy(),
                                    'meta': meta})
            return None
        finally:
            if ticket is not None:
                self.forfeit(ticket)

    # ---------------------------------------------- turns

    def reserve_turn(self):
        """A FIFO ticket, or None when MaxWaiting clips already wait."""
        if not self.turn_taking:
            return None
        with self._turn:
            must_wait = (self._queue or self._owner is not None
                         or not self._idle())
            if must_wait and len(self._queue) >= self.max_waiting:
                return None
            ticket = self._next_ticket
            self._next_ticket += 1
            self._queue.append(ticket)
            return ticket

    def wait_turn(self, ticket, deadline: float, poll: float,
                  clock=time.monotonic) -> bool:
        """Block until ticket owns the turn (True) or deadline passes.

        The owner then revalidates outside every lock and must end the
        turn with start() or forfeit(); nobody can overtake it.
        """
        if not self.turn_taking:
            return True
        with self._turn:
            while True:
                if (self._owner is None and self._queue
                        and self._queue[0] == ticket and self._idle()):
                    self._queue.pop(0)
                    self._owner = ticket
                    return True
                remaining = deadline - clock()
                if remaining <= 0:
                    self._queue.remove(ticket)
                    self._turn.notify_all()
                    return False
                # The callback never notifies; clip ends are polled.
                self._turn.wait(min(poll, remaining))

    def forfeit(self, ticket) -> None:
        with self._turn:
            if self._owner == ticket:
                self._owner = None
            elif ticket in self._queue:
                self._queue.remove(ticket)
            self._turn.notify_all()


class InlineExecutor:
    """Runs work immediately; used by tests for deterministic order."""

    def submit(self, fn, *args):
        fn(*args)


class VoiceAgent:
    def __init__(self, config, voice_map, engine, mixer, db_factory,
                 executor, clock=time.monotonic, unsupported=(),
                 camera=None):
        self.config = config
        self.voice_map = voice_map
        self.engine = engine
        self.mixer = mixer
        self.db_factory = db_factory
        self.executor = executor
        self.clock = clock
        self.unsupported = set(unsupported)
        self.cache = LruClipCache(config['cache_bytes'])
        # Session stop: once set, no new claim or provider request.
        self._exhausted = threading.Event()
        self._db = None
        self._local = threading.local()
        self._lock = threading.Lock()
        self._in_flight = 0
        self._synth_count = 0
        self._chars_sent = 0
        self._failures = 0
        self._backoff_until = 0.0
        self._audio_retry_at = 0.0
        # Rows of dropped clips still to expire in the DB (retried until
        # written); never acknowledged as played meanwhile.
        self._pending_expire = set()
        # Rows whose clip this agent started and has not yet reported
        # finished; see _acknowledge_finished.
        self._sounding = set()
        # Camera mode: the client camera reader, the presence it must
        # match, and each playing clip's last known geometry
        # (row -> distance, rel_angle, x, y, channel, generation,
        # listener) to repan between DB polls.
        self.camera = camera
        self._presence = None
        # Highest presence generation ever observed; survives a
        # transient unknown presence so delayed snapshots never roll
        # the presence back.
        self._presence_high = None
        self._geometry = {}
        self._last_prune = clock()
        self.last_latency = {}

    @property
    def exhausted(self) -> bool:
        return self._exhausted.is_set()

    def _stop_for_quota(self, reason: str) -> None:
        if not self._exhausted.is_set():
            self._exhausted.set()
            log.error('ElevenLabs quota exhausted (%s): voice stops for '
                      'this session; text chat continues', reason)

    # ---------------------------------------------- DB helpers

    def _main_db(self):
        if self._db is None:
            self._db = self.db_factory()
        return self._db

    def _worker_db(self):
        db = getattr(self._local, 'db', None)
        if db is None:
            db = self.db_factory()
            self._local.db = db
        return db

    @staticmethod
    def _query(db, sql, params):
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        finally:
            cursor.close()
        # End the read transaction so later polls see new rows.
        db.commit()
        return rows

    @staticmethod
    def _transition(db, row_id, from_state, to_state,
                    unexpired=False) -> bool:
        """CAS state change; True only if this call made it."""
        sql = ("UPDATE llm_chatter_voice SET state = %s "
               "WHERE id = %s AND state = %s")
        if unexpired:
            sql += " AND expires_at > NOW(3)"
        cursor = db.cursor()
        try:
            cursor.execute(sql, (to_state, row_id, from_state))
            changed = cursor.rowcount == 1
        finally:
            cursor.close()
        db.commit()
        return changed

    # ---------------------------------------------- reservation

    def _reserve(self) -> bool:
        with self._lock:
            if self._in_flight >= self.config['max_in_flight']:
                return False
            self._in_flight += 1
            return True

    def _release(self) -> None:
        with self._lock:
            self._in_flight -= 1

    # ---------------------------------------------- poll

    def tick(self) -> int:
        """One poll; returns how many pending rows were seen."""
        db = self._main_db()
        # Before completion: clips dropped by a stream recovery are
        # expired, never acknowledged as played (nobody heard them).
        self._check_audio(db)
        self._acknowledge_finished(db)
        self._follow_live(db)
        self._refresh_presence(db)
        if self.exhausted:
            return 0
        started = self.clock()
        rows = self._query(db, FETCH_SQL,
                           (self.config['bound_account_id'],))
        for row in rows:
            verdict = decide(row['generation'], row['listener_guid'],
                             row['p_generation'], row['p_listener'])
            if verdict == 'expire':
                self._transition(db, row['id'], 'pending', 'expired')
                continue
            if verdict == 'wait' or self.clock() < self._backoff_until:
                continue
            # A worker may have hit the quota during this same tick.
            if self.exhausted:
                break
            if not self._reserve():
                # Drop, never queue: the line is already on screen.
                self._transition(db, row['id'], 'pending', 'expired')
                log.info('Voice row %s dropped: synthesis busy',
                         row['id'])
                continue
            # Until submit succeeds the reservation is ours to release,
            # including when the claim itself raises (run() reconnects).
            try:
                claimed = self._transition(db, row['id'], 'pending',
                                           'claimed', unexpired=True)
            except Exception:
                self._release()
                raise
            if not claimed:
                self._release()
                continue
            job = dict(row)
            # Local clock read before the query: DB latency can only
            # shorten freshness, never extend it.
            job['deadline'] = started + max(0, row['ms_left']) / 1000.0
            # Server creation time on the local clock, for latency logs
            # that include the fetch and the claim.
            job['created'] = started - max(0, row['age_ms']) / 1000.0
            job['claimed_at'] = self.clock()
            try:
                self.executor.submit(self._work, job)
            except Exception as exc:
                # Once the worker started it owns (and releases) the
                # reservation; never release twice.
                if not job.get('owned'):
                    self._release()
                    self._transition(db, row['id'], 'claimed', 'expired')
                log.warning('Voice row %s not submitted: %s',
                            row['id'], exc)
        self._maybe_prune(db)
        return len(rows)

    def _maybe_prune(self, db) -> None:
        now = self.clock()
        if now - self._last_prune < PRUNE_EVERY_SECONDS:
            return
        self._last_prune = now
        account = (self.config['bound_account_id'],)
        cursor = db.cursor()
        try:
            # Crash recovery only: a lease nobody acknowledged is
            # abandoned, never 'played' (that is reserved for real
            # completion, which may turn the bot away).
            cursor.execute(
                "UPDATE llm_chatter_voice SET state = 'expired' "
                "WHERE account_id = %s AND state = 'playing' "
                "AND play_until < NOW(3) - INTERVAL 1 MINUTE", account)
            cursor.execute(
                "DELETE FROM llm_chatter_voice WHERE account_id = %s "
                "AND state IN ('played', 'expired') "
                "AND created_at < NOW(3) - INTERVAL 10 MINUTE",
                account)
        finally:
            cursor.close()
        db.commit()

    # ---------------------------------------------- completion

    def _check_audio(self, db) -> None:
        """Recover an output stream that stopped calling back.

        Recovery and cancellation are separate: dropped clips leave
        completion tracking before any DB write, and their expirations
        are retried until written, whatever fails in between.
        """
        stalled = getattr(self.mixer, 'stalled', None)
        if stalled is not None and stalled(self.config['audio_stall']):
            now = self.clock()
            if now >= self._audio_retry_at:
                self._audio_retry_at = now + self.config['audio_reopen']
                try:
                    self.mixer.reopen()
                    log.warning('Audio output stalled (device or session '
                                'change?); reopened it')
                except Exception as exc:
                    log.warning('Audio output stalled and could not be '
                                'reopened (%s); retrying in %.0f s', exc,
                                self.config['audio_reopen'])
        take = getattr(self.mixer, 'take_dropped', None)
        dropped = take() if take is not None else []
        with self._lock:
            for meta in dropped:
                row_id = meta.get('row')
                if row_id is None:
                    continue
                self._sounding.discard(row_id)
                self._geometry.pop(row_id, None)
                self._pending_expire.add(row_id)
            pending = sorted(self._pending_expire)
        if dropped:
            log.warning('Dropped %d unheard clip(s) after an audio stall',
                        len(dropped))
        for row_id in pending:
            self._transition(db, row_id, 'playing', 'expired')
            with self._lock:
                self._pending_expire.discard(row_id)

    def _acknowledge_finished(self, db) -> None:
        """Report clips that actually finished: playing -> played.

        The server consumes 'played' as proof the audio completed (a bot
        may then turn away). The sounding set is read before the mixer,
        and a clip joins it only after it is in the mixer, so a clip
        that is just starting is never mistaken for one that ended.
        """
        with self._lock:
            sounding = set(self._sounding)
        if not sounding:
            return
        still = {meta.get('row') for meta in self.mixer.playing().values()}
        for row_id in sounding - still:
            self._transition(db, row_id, 'playing', 'played')
            with self._lock:
                self._sounding.discard(row_id)
                self._geometry.pop(row_id, None)

    # ---------------------------------------------- live geometry

    def _camera_angle(self, x, y, generation=None, listener=None):
        """Speaker bearing relative to the camera, or None.

        None (character panning) unless camera mode is on, the speaker
        position is known, the clip belongs to the current presence
        (generation and listener) and the camera holds a fresh sample
        taken for exactly that presence (session, listener and map).
        """
        if (self.config['pan_source'] != 'camera' or self.camera is None
                or x is None or y is None):
            return None
        presence = self._presence
        if (presence is None or generation is None
                or presence[0] != generation or presence[1] != listener):
            return None
        sample = self.camera.fresh(presence)
        if sample is None:
            return None
        return (math.atan2(y - sample.y, x - sample.x)
                - (sample.yaw + self.config['camera_yaw_offset']))

    def _levels(self, distance, rel_angle, channel, x=None, y=None,
                generation=None, listener=None) -> tuple:
        """(left, right) output gains for a speaker position.

        Volume always follows the server's character-based distance;
        the pan follows the camera when a valid sample exists.
        """
        camera_angle = self._camera_angle(x, y, generation, listener)
        if camera_angle is not None:
            rel_angle = camera_angle
        # Party members stay faintly audible far away; nearby say and
        # NPC voices use their own falloff and floor.
        if channel == 'party':
            falloff, floor = self.config['falloff'], self.config['min_gain']
        else:
            falloff = self.config['proximity_falloff']
            floor = self.config['proximity_min_gain']
        gain = compute_gain(
            distance, self._radius(channel), falloff,
            self.config['ref_distance'], self.config['rolloff'],
            floor, self.config['master_volume'])
        if self.config['pan_enable']:
            left, right = compute_pan(rel_angle, self.config['pan_width'])
        else:
            left = right = 0.7071
        return left * gain, right * gain

    def _follow_live(self, db) -> None:
        """Glide playing clips toward their speaker's live position.

        A row applies only to a clip of the same generation and
        listener, both still current: a clip from before a relog or
        map change keeps its last values, and a late upsert from an
        older session never moves a newer clip.
        """
        if not self.config['live_enable']:
            return
        playing = self.mixer.playing()
        if not playing:
            return
        rows = self._query(db, LIVE_SQL,
                           (self.config['bound_account_id'],
                            self.config['live_fresh_seconds']))
        for live in rows:
            speaker = (live['speaker_kind'], live['speaker_guid'])
            meta = playing.get(speaker)
            if (meta is None
                    or not (live['generation'] == meta['generation']
                            == live['p_generation'])
                    or not (live['listener_guid'] == meta['listener']
                            == live['p_listener'])):
                continue
            self._observe_presence(live['p_generation'],
                                   live['p_listener'], live.get('p_map'))
            with self._lock:
                geometry = self._geometry.get(meta['row'])
                if geometry is not None:
                    geometry.update(
                        distance=live['distance'],
                        rel_angle=live['rel_angle'],
                        x=live.get('speaker_x'), y=live.get('speaker_y'))
            left, right = self._levels(live['distance'], live['rel_angle'],
                                       meta['channel'],
                                       live.get('speaker_x'),
                                       live.get('speaker_y'),
                                       meta['generation'], meta['listener'])
            # By row: if this clip ended during the query, a newer clip
            # from the same speaker is not touched.
            self.mixer.set_target(meta['row'], left, right)

    # ---------------------------------------------- camera

    def _observe_presence(self, generation, listener, map_id) -> None:
        """Adopt a presence observation unless a newer one was seen.

        Workers, live rows and the presence poll all report presence at
        different times; only the newest generation may stand.
        """
        if generation is None or map_id is None:
            return
        with self._lock:
            if (self._presence_high is not None
                    and generation < self._presence_high):
                return
            self._presence_high = generation
            self._presence = (generation, listener, map_id)

    def _forget_presence(self) -> None:
        """Presence unknown: no camera use until observed again."""
        with self._lock:
            self._presence = None

    def _camera_mode(self) -> bool:
        return (self.config['pan_source'] == 'camera'
                and self.camera is not None)

    def _refresh_presence(self, db) -> None:
        """Camera mode, while clips play: the listener to match."""
        if not self._camera_mode() or not self.mixer.playing():
            return
        try:
            rows = self._query(db, PRESENCE_SQL,
                               (self.config['bound_account_id'],))
        except Exception:
            # Unknown presence: no camera use until it is known again.
            self._forget_presence()
            raise
        if rows:
            self._observe_presence(rows[0]['generation'],
                                   rows[0]['listener_guid'],
                                   rows[0]['map_id'])
        else:
            self._forget_presence()

    def _repan_camera(self) -> None:
        """Sample the camera and re-aim every playing clip (no DB)."""
        if self.camera is None:
            return
        with self._lock:
            # Snapshot and prune under the lock that guards publication:
            # a clip that starts meanwhile is either in this snapshot or
            # publishes its geometry after the prune, never in between.
            # (Lock order: agent lock, then the mixer's audio lock; the
            # mixer never takes the agent lock.)
            playing = self.mixer.playing()
            # Geometry of finished clips is never reused.
            rows = {meta['row'] for meta in playing.values()}
            for row_id in list(self._geometry):
                if row_id not in rows:
                    del self._geometry[row_id]
            geometry = {row: dict(g) for row, g in self._geometry.items()}
        if not playing:
            return
        self.camera.update(self._presence)
        presence = self._presence
        for meta in playing.values():
            g = geometry.get(meta['row'])
            # Old-session geometry is rejected at every use.
            if (g is None or presence is None
                    or g['generation'] != presence[0]
                    or g['listener'] != presence[1]):
                continue
            left, right = self._levels(g['distance'], g['rel_angle'],
                                       g['channel'], g['x'], g['y'],
                                       g['generation'], g['listener'])
            self.mixer.set_target(meta['row'], left, right)

    # ---------------------------------------------- worker

    def _radius(self, channel: str) -> float:
        if channel == 'yell':
            return self.config['yell_radius']
        if channel == 'party':
            return self.config['party_radius']
        return self.config['say_radius']

    def _synthesize(self, job, text, voice):
        key = (voice, self.engine.model, text)
        with self._lock:
            pcm = self.cache.get(key)
        if pcm is not None:
            return pcm, True
        remaining = job['deadline'] - self.clock()
        if remaining <= 0:
            return None, False
        # Last gate before spending credits: a reserved worker must
        # not start a request after another hit the quota.
        if self.exhausted:
            raise QuotaExhausted('session already stopped')
        pcm = self.engine.synthesize(text, voice, remaining)
        with self._lock:
            self.cache.put(key, pcm)
            self._synth_count += 1
            self._chars_sent += len(text)
            log_quota = self._synth_count % QUOTA_LOG_EVERY_CLIPS == 0
        if log_quota:
            self.log_quota()
        return pcm, False

    def _still_valid(self, db, job) -> bool:
        checked = self.clock()
        rows = self._query(db, REVALIDATE_SQL, (job['id'],))
        if not rows:
            return False
        row = rows[0]
        fresh = checked + max(0, row['ms_left']) / 1000.0
        return (row['state'] == 'claimed'
                and decide(row['generation'], row['listener_guid'],
                           row['p_generation'], row['p_listener'])
                == 'play'
                and row['ms_left'] > 0
                and self.clock() < min(job['deadline'], fresh))

    def _lease(self, db, row_id, clip_us) -> bool:
        """claimed -> playing until the clip ends; True if ours."""
        cursor = db.cursor()
        try:
            cursor.execute(LEASE_SQL, (clip_us, row_id))
            changed = cursor.rowcount == 1
        finally:
            cursor.close()
        db.commit()
        return changed

    def _play_in_turn(self, db, job, pcm):
        """Wait for the turn, revalidate, lease, start.

        Returns None when the clip started, else the skip reason. The
        turn is always ended (start or forfeit), so a failure here can
        never block the clips behind it.
        """
        mixer = self.mixer
        ticket = mixer.reserve_turn()
        if mixer.turn_taking and ticket is None:
            return 'turn queue full'
        if not mixer.wait_turn(ticket, job['deadline'],
                               self.config['poll_interval'], self.clock):
            return 'stale'
        handed_over = False
        leased = False
        started = False
        try:
            # After any wait: still the same session, still fresh.
            if not self._still_valid(db, job):
                return 'stale'
            clip_us = int(len(pcm) // 2 * 1_000_000
                          / self.engine.sample_rate)
            # Atomic with the deadline and the current presence.
            if not self._lease(db, job['id'], clip_us):
                return 'stale'
            leased = True
            # The lease write itself may have been slow.
            if self.clock() >= job['deadline']:
                return 'stale'
            if self._camera_mode():
                self._observe_presence(job['p_generation'],
                                       job['p_listener'], job.get('p_map'))
            left, right = self._levels(job['distance'], job['rel_angle'],
                                       job['channel'], job.get('speaker_x'),
                                       job.get('speaker_y'),
                                       job['generation'],
                                       job['listener_guid'])
            meta = {'row': job['id'],
                    'speaker': (job['speaker_kind'], job['speaker_guid']),
                    'generation': job['generation'],
                    'listener': job['listener_guid'],
                    'channel': job['channel']}
            # start() ends the turn whatever happens, raising included.
            handed_over = True
            reason = mixer.start(pcm, left, right, meta, ticket)
            started = reason is None
            if started and self._camera_mode():
                # Published only once the clip is in the mixer, so a
                # concurrent repan (which drops rows not playing) can
                # never remove it in between.
                with self._lock:
                    self._geometry[job['id']] = {
                        'distance': job['distance'],
                        'rel_angle': job['rel_angle'],
                        'x': job.get('speaker_x'),
                        'y': job.get('speaker_y'),
                        'channel': job['channel'],
                        'generation': job['generation'],
                        'listener': job['listener_guid']}
            if started:
                with self._lock:
                    self._sounding.add(job['id'])
            return reason
        finally:
            if not started:
                # Defensive: a clip that did not start never keeps
                # cached geometry (it is only published after a start).
                with self._lock:
                    self._geometry.pop(job['id'], None)
            if not handed_over and ticket is not None:
                mixer.forfeit(ticket)
            if leased and not started:
                # No lease may outlive a clip that is not sounding.
                try:
                    self._transition(db, job['id'], 'playing', 'expired')
                except Exception as exc:
                    log.warning('Voice row %s lease cancel failed: %s',
                                job['id'], exc)

    def _work(self, job) -> None:
        job['owned'] = True
        db = None
        outcome = 'expired'
        reason = None
        timing = {}
        try:
            db = self._worker_db()
            text = clean_voice_text(job['text'])
            voice = self.voice_map.resolve(job['speaker_race'],
                                           job['speaker_gender'],
                                           self.unsupported)
            if not text or not voice:
                return
            timing['synth_start'] = self.clock()
            try:
                pcm, cached = self._synthesize(job, text, voice)
            except QuotaExhausted as exc:
                self._stop_for_quota(str(exc))
                return
            except SynthesisError as exc:
                self._note_failure(exc)
                return
            timing['synth_end'] = self.clock()
            timing['cached'] = cached
            if pcm is None:
                reason = 'stale'
                return
            self._failures = 0
            reason = self._play_in_turn(db, job, pcm)
            if reason is None:
                outcome = 'played'
                timing['play_start'] = self.clock()
        except Exception as exc:
            log.warning('Voice row %s failed: %s', job['id'], exc)
            self._local.db = None
        finally:
            try:
                # A started clip stays 'playing' (its lease) until the
                # prune step marks it played.
                if db is not None and outcome != 'played':
                    self._transition(db, job['id'], 'claimed', outcome)
            except Exception as exc:
                log.warning('Voice row %s state update failed: %s',
                            job['id'], exc)
                self._local.db = None
            self._release()
            self._log_latency(job, outcome if reason is None
                              else f'{outcome} ({reason})', timing)

    def _note_failure(self, exc) -> None:
        self._failures += 1
        log.warning('Voice synthesis failed: %s', exc)
        if self._failures >= FAILURE_BACKOFF_AFTER:
            self._backoff_until = self.clock() + FAILURE_BACKOFF_SECONDS
            self._failures = 0

    def _log_latency(self, job, outcome, timing) -> None:
        self.last_latency = latency_ms(job, timing)

        def show(name):
            value = self.last_latency.get(name)
            return '-' if value is None else f'{value:.0f}'

        log.info('Voice row %s %s: claim=%s synth=%s-%s%s play=%s ms '
                 'after creation', job['id'], outcome, show('claim'),
                 show('synth_start'), show('synth_end'),
                 ' (cached)' if timing.get('cached') else '',
                 show('play_start'))

    def log_quota(self) -> None:
        quota = self.engine.quota()
        if quota and None not in quota:
            used, limit = quota
            log.info('ElevenLabs quota: %s/%s characters used '
                     '(%s sent this session)', used, limit,
                     self._chars_sent)
            if limit and used >= limit:
                self._stop_for_quota(f'{used}/{limit} used')

    # ---------------------------------------------- loop

    def run(self) -> None:
        interval = self.config['poll_interval']
        while True:
            try:
                seen = self.tick()
            except Exception as exc:
                log.warning('Voice poll failed: %s; reconnecting', exc)
                self._db = None
                # Presence may be stale: never aim by the camera meanwhile.
                self._forget_presence()
                seen = 0
            # Live gains and waiting turns need the active rate too.
            if seen or self.mixer.active():
                interval = self.config['poll_interval']
            else:
                interval = min(interval * 2,
                               self.config['idle_poll_interval'])
            self._wait(interval)

    def _wait(self, interval) -> None:
        """Sleep until the next DB poll; in camera mode re-aim playing
        clips every Camera.PollMs meanwhile (camera reads only, no DB,
        and only while something plays)."""
        end = time.monotonic() + interval
        if self.camera is None or self.config['pan_source'] != 'camera':
            time.sleep(interval)
            return
        while True:
            if self.mixer.playing():
                try:
                    self._repan_camera()
                except Exception as exc:
                    log.warning('Camera repan failed: %s', exc)
            left = end - time.monotonic()
            if left <= 0:
                return
            time.sleep(min(self.config['camera_poll'], left))


def latency_ms(job, timing) -> dict:
    """Milliseconds from the server recording the line to each step.

    job['created'] maps the server's creation time onto the local clock
    using the time read before the fetch, so fetch and claim time count.
    """
    points = {'claim': job.get('claimed_at')}
    for name in ('synth_start', 'synth_end', 'play_start'):
        points[name] = timing.get(name)
    return {name: None if value is None
            else (value - job['created']) * 1000.0
            for name, value in points.items()}


def validate_voice_map(voice_map, engine) -> tuple:
    """Check configured ids against the account; (ok, unsupported)."""
    available = {v.get('voice_id') for v in engine.list_voices()}
    unsupported = set()
    for label, gender, voice in voice_map.entries():
        slot = f"{label}/{'female' if gender else 'male'}"
        if not voice:
            log.warning('Voice map %s: EMPTY (falls back to defaults)',
                        slot)
        elif voice not in available:
            unsupported.add(voice)
            log.warning('Voice map %s: UNSUPPORTED id %s (not in this '
                        'account; run --list-voices)', slot, voice)
        else:
            log.info('Voice map %s: OK', slot)
    default = voice_map.defaults.get(0, '')
    ok = bool(default) and default not in unsupported
    return ok, unsupported


def print_voices(engine) -> None:
    for voice in sorted(engine.list_voices(),
                        key=lambda v: (v.get('category', ''),
                                       v.get('name', ''))):
        labels = voice.get('labels') or {}
        description = (labels.get('description')
                       or labels.get('descriptive') or '')
        print(f"{voice.get('voice_id', ''):24} "
              f"{voice.get('category', ''):12} "
              f"{voice.get('name', ''):20} "
              f"{labels.get('gender', ''):8} "
              f"{labels.get('accent', ''):12} {description}")


def run_camera_probe(config) -> None:
    """Consented one-off camera check; compares with server presence."""
    from tts_camera import CameraOffsets, probe

    def presence():
        try:
            db = get_db_connection(config)
            try:
                rows = VoiceAgent._query(
                    db, 'SELECT listener_guid, map_id FROM '
                    'llm_chatter_voice_listener WHERE account_id = %s',
                    (config['bound_account_id'],))
            finally:
                db.close()
            return ((rows[0]['listener_guid'], rows[0]['map_id'])
                    if rows else (None, None))
        except Exception as exc:
            return (f'db error: {exc}', None)

    probe(CameraOffsets(**config['camera_offsets']),
          config['camera_process_name'], config['camera_process_id'],
          15, presence)


def main():
    parser = argparse.ArgumentParser(description='Voice (TTS) Agent')
    parser.add_argument('--config', required=True,
                        help='Path to mod_llm_chatter.conf')
    parser.add_argument('--list-voices', action='store_true',
                        help='List voices in your ElevenLabs account '
                             '(free, no credits) and exit')
    parser.add_argument('--camera-probe', action='store_true',
                        help='Read-only check of the game client camera '
                             '(run while logged in) and exit')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    )

    config = load_voice_config(parse_config(args.config))
    if args.camera_probe:
        run_camera_probe(config)
        return
    if config['provider'] != 'elevenlabs':
        log.error('LLMChatter.Voice.Provider %s is not supported yet',
                  config['provider'])
        sys.exit(1)
    if not config['elevenlabs_api_key']:
        log.error('LLMChatter.Voice.ElevenLabs.ApiKey not set')
        sys.exit(1)
    engine = ElevenLabsEngine(config['elevenlabs_api_key'],
                              config['elevenlabs_model'],
                              config['elevenlabs_output_format'])
    if args.list_voices:
        try:
            print_voices(engine)
        except SynthesisError as exc:
            log.error('Cannot list voices: %s', exc)
            sys.exit(1)
        return

    if not config['enable']:
        log.error('LLMChatter.Voice.Enable is not set to 1')
        sys.exit(1)
    if not config['bound_account_id']:
        log.error('LLMChatter.Voice.BoundAccountId is not set')
        sys.exit(1)

    map_path = Path(config['voice_map_file'])
    if not map_path.is_absolute():
        map_path = TOOLS_DIR / map_path
    voice_map = load_voice_map(str(map_path))
    try:
        ok, unsupported = validate_voice_map(voice_map, engine)
    except SynthesisError as exc:
        log.error('Cannot check the voice map against your account: %s',
                  exc)
        sys.exit(1)
    if not ok:
        log.error('Voice map defaults.male is empty or unsupported in '
                  '%s; fill it from --list-voices', map_path)
        sys.exit(1)

    set_below_normal_priority()
    from concurrent.futures import ThreadPoolExecutor
    mixer = Mixer(engine.sample_rate, config['max_concurrent'],
                  ramp_ms=config['live_ramp_ms'],
                  turn_taking=config['turn_taking'],
                  max_waiting=config['max_waiting'])
    camera = None
    if config['pan_source'] == 'camera':
        if sys.platform == 'win32':
            from tts_camera import CameraOffsets, ClientCamera
            camera = ClientCamera(
                CameraOffsets(**config['camera_offsets']),
                process_name=config['camera_process_name'],
                process_id=config['camera_process_id'],
                max_age=config['camera_max_age'],
                fail_ticks=config['camera_fail_ticks'],
                max_jump=config['camera_max_jump'],
                rebaseline_ticks=config['camera_rebaseline_ticks'],
                rescan_seconds=config['camera_rescan'],
                log=log.info)
            log.info('Panning follows the game camera when available '
                     '(read-only), else your character')
        else:
            log.warning('Camera panning needs Windows; using character '
                        'panning')
    agent = VoiceAgent(
        config, voice_map, engine, mixer,
        lambda: get_db_connection(config),
        ThreadPoolExecutor(max_workers=config['max_in_flight']),
        unsupported=unsupported, camera=camera)
    agent.log_quota()
    log.info('Voice agent started (account=%s, model=%s, format=%s); '
             'playback follows the server-recorded mailbox',
             config['bound_account_id'], engine.model,
             engine.output_format)
    try:
        agent.run()
    except KeyboardInterrupt:
        log.info('Voice agent stopped')
    finally:
        if camera is not None:
            camera.close()


if __name__ == '__main__':
    main()
