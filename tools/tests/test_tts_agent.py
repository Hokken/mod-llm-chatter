"""Offline voice-agent orchestration tests: no network, audio or DB."""

import math
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tts_agent as agent_mod
from tts_agent import (
    InlineExecutor, Mixer, VoiceAgent, decide, load_voice_config,
)
from tts_engines import (
    ElevenLabsEngine, LruClipCache, QuotaExhausted, SynthesisError, VoiceMap,
    clean_voice_text, compute_gain, compute_pan,
)

VOICES = {
    'defaults': {'male': {'voice_id': 'def-m'},
                 'female': {'voice_id': 'def-f'}},
    'archetypes': {
        'brute': {'races': [2, 6, 8], 'male': {'voice_id': 'orc-m'},
                  'female': {'voice_id': ''}},
        'gnome': {'races': [7], 'male': {'voice_id': 'gnome-m'},
                  'female': {'voice_id': 'gnome-f'}},
        'broken': 'not an object',
    },
}


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class Cursor:
    def __init__(self, db):
        self.db = db
        self.rowcount = 0
        self._rows = []

    def execute(self, sql, params):
        self.db.log.append((sql, params))
        if sql.startswith('SELECT'):
            self._rows = self.db.select(sql, params)
        elif 'play_until = NOW(3) + INTERVAL' in sql:
            self.rowcount = self.db.lease(params)
        elif sql.startswith('UPDATE') and 'play_until < NOW(3)' in sql:
            self.rowcount = 0
        elif sql.startswith('UPDATE'):
            self.rowcount = self.db.update(params)
        else:
            self.rowcount = 0

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class FakeDB:
    """Holds row states and presence; answers the agent's queries."""

    def __init__(self, rows, presence=(10, 7), ms_left=3000):
        self.rows = {r['id']: dict(r, state='pending') for r in rows}
        self.presence = presence
        self.ms_left = ms_left
        self.log = []
        self.on_revalidate = None
        self.live = []
        self.leases = {}
        self.on_lease = None
        self.on_live = None

    def cursor(self, dictionary=False):
        return Cursor(self)

    def commit(self):
        pass

    def _view(self, row):
        p_gen, p_listener = (self.presence if self.presence
                             else (None, None))
        return dict(row, p_generation=p_gen, p_listener=p_listener,
                    p_map=1,
                    ms_left=self.ms_left, age_ms=50)

    def select(self, sql, params):
        if sql.startswith('SELECT generation, listener_guid, map_id'):
            if not self.presence:
                return []
            return [{'generation': self.presence[0],
                     'listener_guid': self.presence[1], 'map_id': 1}]
        if 'llm_chatter_voice_live' in sql:
            if self.on_live:
                self.on_live(self)
            return list(self.live)
        if 'WHERE v.id' in sql:
            if self.on_revalidate:
                self.on_revalidate(self)
            row = self.rows.get(params[0])
            return [self._view(row)] if row else []
        return [self._view(r) for r in self.rows.values()
                if r['state'] == 'pending']

    def lease(self, params):
        clip_us, row_id = params
        if self.on_lease:
            self.on_lease(self)
        row = self.rows.get(row_id)
        current = (self.presence is not None
                   and row is not None
                   and self.presence == (row['generation'],
                                         row['listener_guid'])
                   and row['listener_guid'] != 0)
        if row and row['state'] == 'claimed' and self.ms_left > 0                 and current:
            row['state'] = 'playing'
            self.leases[row_id] = clip_us
            return 1
        return 0

    def update(self, params):
        to_state, row_id, from_state = params
        row = self.rows.get(row_id)
        if row and row['state'] == from_state:
            row['state'] = to_state
            return 1
        return 0


class FakeEngine:
    model = 'flash'
    sample_rate = 22050

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def synthesize(self, text, voice, timeout):
        self.calls.append((text, voice))
        if self.error:
            raise self.error
        return b'\x00\x01' * 100

    def quota(self):
        return (10, 30000)


class FakeMixer:
    """Mixer interface without audio; turn-taking off."""

    turn_taking = False

    def __init__(self, accept=True):
        self.accept = accept
        self.played = []
        self.current = {}
        self.targets = []

    def playing(self):
        return dict(self.current)

    def active(self):
        return bool(self.current)

    def set_target(self, row_id, left, right):
        self.targets.append((row_id, left, right))

    def reserve_turn(self):
        return None

    def wait_turn(self, ticket, deadline, poll, clock=None):
        return True

    def forfeit(self, ticket):
        pass

    def start(self, pcm, left, right, meta, ticket=None):
        if not self.accept:
            return 'mixer full'
        self.played.append((left, right, meta['speaker']))
        return None


class HeldExecutor:
    """Keeps submitted work unrun, like a busy pool."""

    def __init__(self):
        self.jobs = []

    def submit(self, fn, *args):
        self.jobs.append((fn, args))


def row(row_id=1, generation=10, listener=7, race=2, gender=0,
        speaker=55, text='For the Horde!'):
    return {'id': row_id, 'listener_guid': listener,
            'generation': generation, 'speaker_guid': speaker,
            'speaker_kind': 'bot', 'speaker_race': race,
            'speaker_gender': gender, 'channel': 'say', 'text': text,
            'distance': 10.0, 'rel_angle': 0.0}


def make_agent(db, engine=None, mixer=None, executor=None, clock=None):
    config = load_voice_config({'LLMChatter.Voice.BoundAccountId': '3'})
    return VoiceAgent(config, VoiceMap(VOICES), engine or FakeEngine(),
                      mixer or FakeMixer(), lambda: db,
                      executor or InlineExecutor(), clock=clock or Clock())


class DecideTests(unittest.TestCase):
    def test_matrix(self):
        self.assertEqual(decide(10, 7, 10, 7), 'play')
        self.assertEqual(decide(9, 7, 10, 7), 'expire')
        self.assertEqual(decide(11, 7, 10, 7), 'wait')
        self.assertEqual(decide(10, 7, 10, 0), 'expire')
        self.assertEqual(decide(10, 7, 10, 8), 'expire')
        self.assertEqual(decide(10, 7, None, None), 'wait')
        self.assertEqual(decide(10, 0, 10, 7), 'wait')


class OrchestrationTests(unittest.TestCase):
    def test_claim_synth_revalidate_play(self):
        db = FakeDB([row()])
        mixer = FakeMixer()
        make_agent(db, mixer=mixer).tick()
        self.assertEqual(db.rows[1]['state'], 'playing')
        self.assertEqual(len(mixer.played), 1)
        self.assertEqual(mixer.played[0][2], ('bot', 55))

    def test_presence_change_during_synthesis_expires(self):
        db = FakeDB([row()])
        db.on_revalidate = lambda d: setattr(d, 'presence', (11, 7))
        mixer = FakeMixer()
        make_agent(db, mixer=mixer).tick()
        self.assertEqual(db.rows[1]['state'], 'expired')
        self.assertEqual(mixer.played, [])

    def test_logout_during_synthesis_expires(self):
        db = FakeDB([row()])
        db.on_revalidate = lambda d: setattr(d, 'presence', (11, 0))
        mixer = FakeMixer()
        make_agent(db, mixer=mixer).tick()
        self.assertEqual(db.rows[1]['state'], 'expired')
        self.assertEqual(mixer.played, [])

    def test_deadline_passed_during_synthesis_expires(self):
        clock = Clock()
        db = FakeDB([row()], ms_left=500)

        class SlowEngine(FakeEngine):
            def synthesize(self, text, voice, timeout):
                clock.now += 1.0
                return super().synthesize(text, voice, timeout)

        mixer = FakeMixer()
        make_agent(db, engine=SlowEngine(), mixer=mixer,
                   clock=clock).tick()
        self.assertEqual(db.rows[1]['state'], 'expired')
        self.assertEqual(mixer.played, [])

    def test_in_flight_full_drops_without_submit(self):
        db = FakeDB([row(1, speaker=1), row(2, speaker=2),
                     row(3, speaker=3)])
        held = HeldExecutor()
        make_agent(db, executor=held).tick()
        self.assertEqual(len(held.jobs), 2)
        self.assertEqual(db.rows[1]['state'], 'claimed')
        self.assertEqual(db.rows[2]['state'], 'claimed')
        self.assertEqual(db.rows[3]['state'], 'expired')

    def test_mixer_refusal_expires(self):
        db = FakeDB([row()])
        make_agent(db, mixer=FakeMixer(accept=False)).tick()
        self.assertEqual(db.rows[1]['state'], 'expired')

    def test_quota_exhausted_stops_claims(self):
        db = FakeDB([row(1)])
        engine = FakeEngine(error=QuotaExhausted('out'))
        agent = make_agent(db, engine=engine)
        agent.tick()
        self.assertTrue(agent.exhausted)
        self.assertEqual(db.rows[1]['state'], 'expired')
        db.rows[2] = dict(row(2), state='pending')
        self.assertEqual(agent.tick(), 0)
        self.assertEqual(db.rows[2]['state'], 'pending')
        self.assertEqual(len(engine.calls), 1)

    def test_quota_in_one_tick_stops_remaining_rows(self):
        db = FakeDB([row(1, speaker=1), row(2, speaker=2),
                     row(3, speaker=3)])
        engine = FakeEngine(error=QuotaExhausted('out'))
        make_agent(db, engine=engine).tick()
        self.assertEqual(len(engine.calls), 1)
        self.assertEqual(db.rows[2]['state'], 'pending')
        self.assertEqual(db.rows[3]['state'], 'pending')

    def test_reserved_worker_skips_request_after_quota(self):
        db = FakeDB([row(1, speaker=1, text='one'),
                     row(2, speaker=2, text='two')])
        engine = FakeEngine(error=QuotaExhausted('out'))
        held = HeldExecutor()
        agent = make_agent(db, engine=engine, executor=held)
        agent.tick()
        self.assertEqual(len(held.jobs), 2)
        for fn, args in held.jobs:
            fn(*args)
        self.assertEqual(len(engine.calls), 1)
        self.assertEqual(db.rows[2]['state'], 'expired')
        self.assertEqual(agent._in_flight, 0)

    def test_quota_count_at_limit_stops(self):
        class FullEngine(FakeEngine):
            def quota(self):
                return (30000, 30000)

        agent = make_agent(FakeDB([]), engine=FullEngine())
        agent.log_quota()
        self.assertTrue(agent.exhausted)

    def test_latency_includes_fetch_and_claim(self):
        clock = Clock()
        db = FakeDB([row()])
        original = db.select

        def slow_select(sql, params):
            clock.now += 0.2
            return original(sql, params)

        db.select = slow_select
        original_update = db.update

        def slow_update(params):
            clock.now += 0.1
            return original_update(params)

        db.update = slow_update
        agent = make_agent(db, clock=clock)
        agent.tick()
        # age 50 ms at fetch + 200 ms fetch + 100 ms claim.
        self.assertAlmostEqual(agent.last_latency['claim'], 350, places=3)
        self.assertGreater(agent.last_latency['play_start'], 350)

    def test_synthesis_error_expires_row(self):
        db = FakeDB([row()])
        make_agent(db, engine=FakeEngine(SynthesisError('500'))).tick()
        self.assertEqual(db.rows[1]['state'], 'expired')

    def test_generations(self):
        db = FakeDB([row(1, generation=9), row(2, generation=11)])
        make_agent(db).tick()
        self.assertEqual(db.rows[1]['state'], 'expired')
        self.assertEqual(db.rows[2]['state'], 'pending')

    def test_cas_lost_releases_reservation(self):
        db = FakeDB([row()])
        db.update = lambda params: 0
        held = HeldExecutor()
        agent = make_agent(db, executor=held)
        agent.tick()
        self.assertEqual(held.jobs, [])
        self.assertEqual(agent._in_flight, 0)

    def test_claim_db_failure_releases_and_recovers(self):
        db = FakeDB([row(1, speaker=1)])
        original = db.update
        failures = {'left': 2}

        def flaky_update(params):
            if params[1] == 'claimed' or params[0] != 'claimed':
                return original(params)
            if failures['left']:
                failures['left'] -= 1
                raise ConnectionError('lost connection')
            return original(params)

        db.update = flaky_update
        connects = []

        def factory():
            connects.append(1)
            return db

        mixer = FakeMixer()
        config = load_voice_config({'LLMChatter.Voice.BoundAccountId': '3'})
        agent = VoiceAgent(config, VoiceMap(VOICES), FakeEngine(), mixer,
                           factory, InlineExecutor(), clock=Clock())
        for _ in range(2):
            with self.assertRaises(ConnectionError):
                agent.tick()
            self.assertEqual(agent._in_flight, 0)
            agent._db = None  # what run() does before reconnecting
        agent.tick()
        self.assertEqual(db.rows[1]['state'], 'playing')
        self.assertEqual(agent._in_flight, 0)
        self.assertGreaterEqual(len(connects), 3)

    def test_submit_failure_after_worker_start_releases_once(self):
        db = FakeDB([row()])

        class FailingAfterWork(InlineExecutor):
            def submit(self, fn, *args):
                fn(*args)
                raise RuntimeError('executor shut down')

        agent = make_agent(db, executor=FailingAfterWork())
        agent.tick()
        self.assertEqual(agent._in_flight, 0)
        self.assertEqual(db.rows[1]['state'], 'playing')

    def test_cache_hit_skips_engine(self):
        db = FakeDB([row(1), row(2)])
        engine = FakeEngine()
        make_agent(db, engine=engine).tick()
        self.assertEqual(len(engine.calls), 1)
        self.assertEqual(db.rows[2]['state'], 'playing')

    def test_unmapped_voice_expires_without_synthesis(self):
        db = FakeDB([row(race=2, gender=1)])
        engine = FakeEngine()
        voices = dict(VOICES, defaults={})
        agent = make_agent(db, engine=engine)
        agent.voice_map = VoiceMap(voices)
        agent.tick()
        self.assertEqual(engine.calls, [])
        self.assertEqual(db.rows[1]['state'], 'expired')


class ConfigTests(unittest.TestCase):
    def test_in_flight_capped_at_two(self):
        for value, expected in (('4', 2), ('99', 2), ('0', 1), ('x', 2)):
            config = load_voice_config(
                {'LLMChatter.Voice.MaxInFlight': value})
            self.assertEqual(config['max_in_flight'], expected, value)


class MathTests(unittest.TestCase):
    def test_gain_inverse_and_floor(self):
        args = ('inverse', 5.0, 1.0, 0.15, 1.0)
        self.assertEqual(compute_gain(2.0, 40, *args), 1.0)
        self.assertAlmostEqual(compute_gain(10.0, 40, *args), 0.5)
        self.assertEqual(compute_gain(1000.0, 40, *args), 0.15)

    def test_gain_linear_and_master(self):
        self.assertAlmostEqual(
            compute_gain(20.0, 40, 'linear', 5, 1, 0.1, 0.5), 0.25)
        self.assertAlmostEqual(
            compute_gain(40.0, 40, 'linear', 5, 1, 0.1, 1.0), 0.1)

    def test_pan(self):
        left, right = compute_pan(0.0, 1.0)
        self.assertAlmostEqual(left, right)
        left, right = compute_pan(math.pi / 2, 1.0)
        self.assertAlmostEqual(right, 0.0, places=6)
        self.assertAlmostEqual(left, 1.0)
        left, right = compute_pan(-math.pi / 2, 1.0)
        self.assertAlmostEqual(left, 0.0, places=6)
        left, right = compute_pan(math.pi / 2, 0.0)
        self.assertAlmostEqual(left, right)
        self.assertAlmostEqual(left ** 2 + right ** 2, 1.0)


class VoiceMapTests(unittest.TestCase):
    def test_resolution_and_fallbacks(self):
        voices = VoiceMap(VOICES)
        self.assertEqual(voices.resolve(2, 0), 'orc-m')
        self.assertEqual(voices.resolve(6, 1), 'def-f')
        self.assertEqual(voices.resolve(7, 2), 'gnome-m')
        self.assertEqual(voices.resolve(99, 1), 'def-f')
        self.assertEqual(VoiceMap({}).resolve(2, 0), '')

    def test_malformed_shapes_do_not_raise(self):
        self.assertEqual(VoiceMap({'archetypes': ['bad']}).resolve(2, 0),
                         '')
        broken = VoiceMap({'archetypes': {'x': {'races': None,
                                                'male': 'nope'}},
                           'defaults': {'male': {'voice_id': 'd'}}})
        self.assertEqual(broken.resolve(2, 0), 'd')
        self.assertEqual(VoiceMap('not a dict').resolve(1, 1), '')

    def test_unsupported_ids_fall_back(self):
        voices = VoiceMap(VOICES)
        self.assertEqual(voices.resolve(2, 0, {'orc-m'}), 'def-m')
        self.assertEqual(voices.resolve(7, 1, {'gnome-f', 'def-f'}),
                         'def-m')
        self.assertEqual(voices.resolve(7, 1, {'gnome-f', 'def-f',
                                               'def-m'}), '')

    def test_unsupported_archetype_plays_default(self):
        db = FakeDB([row(race=2, gender=0)])
        engine = FakeEngine()
        agent = make_agent(db, engine=engine)
        agent.unsupported = {'orc-m'}
        agent.tick()
        self.assertEqual(engine.calls[0][1], 'def-m')
        self.assertEqual(db.rows[1]['state'], 'playing')

    def test_shipped_map_is_valid_and_unconfigured(self):
        voices = agent_mod.load_voice_map(
            str(agent_mod.TOOLS_DIR / 'voice_map.json'))
        self.assertEqual(len(voices.archetypes), 5)
        races = set(voices.race_archetype)
        self.assertEqual(races, {1, 2, 3, 4, 5, 6, 7, 8, 10, 11})
        self.assertTrue(all(not v for _, _, v in voices.entries()))


class CacheAndTextTests(unittest.TestCase):
    def test_lru_evicts_by_bytes(self):
        cache = LruClipCache(10)
        cache.put('a', b'12345')
        cache.put('b', b'12345')
        cache.get('a')
        cache.put('c', b'12345')
        self.assertIsNone(cache.get('b'))
        self.assertIsNotNone(cache.get('a'))
        self.assertLessEqual(cache.size, 10)

    def test_clean_link_markup(self):
        text = ('Got |cff1eff00|Hitem:2589:0:0:0:0:0:0:0|h[Linen Cloth]'
                '|h|r today')
        self.assertEqual(clean_voice_text(text), 'Got Linen Cloth today')


class ProviderErrorTests(unittest.TestCase):
    class Response:
        def __init__(self, status_code, body):
            self.status_code = status_code
            self.body = body
            self.text = str(body)

        def json(self):
            return self.body

    class Client:
        def __init__(self, response):
            self.response = response

        def get(self, *args, **kwargs):
            return self.response

    def engine(self, status_code, body):
        response = self.Response(status_code, body)
        return ElevenLabsEngine('key', 'model', 'pcm_22050',
                                client=self.Client(response))

    def test_missing_permission_is_readable(self):
        body = {'detail': {'status': 'missing_permissions',
                           'message': 'The API key you used is missing '
                                      'the permission voices_read'}}
        with self.assertRaisesRegex(SynthesisError,
                                    'HTTP 401: .*voices_read'):
            self.engine(401, body).list_voices()

    def test_quota_lookup_failure_returns_none(self):
        self.assertIsNone(self.engine(401, {'detail': 'nope'}).quota())


class FakeStream:
    def start(self):
        pass


def real_mixer(**kwargs):
    """The real Mixer at 1000 Hz on a stream that never opens a device."""
    kwargs.setdefault('ramp_ms', 10.0)
    return Mixer(1000, 2, stream_factory=lambda rate, cb: FakeStream(),
                 **kwargs)


def meta(speaker=('bot', 55), generation=10, listener=7, channel='say',
         row_id=1):
    return {'row': row_id, 'speaker': speaker, 'generation': generation,
            'listener': listener, 'channel': channel}


def pcm_ones(frames):
    # Full-scale samples: the output equals the applied gain.
    return b'\xff\x7f' * frames


def render(mixer, frames):
    import numpy as np
    out = np.zeros((frames, 2), dtype=np.float32)
    mixer._callback(out, frames, None, None)
    return out


class MixerTests(unittest.TestCase):
    def test_smoothing_glides_to_target_without_overshoot(self):
        mixer = real_mixer()
        self.assertIsNone(mixer.start(pcm_ones(400), 1.0, 0.0, meta()))
        mixer.set_target(1, 0.0, 1.0)
        out = render(mixer, 100)
        left, right = out[:, 0], out[:, 1]
        # Time constant 10 frames: about 63% of the way after 10 frames,
        # each frame a small step, monotonic, never past the target.
        steps = [float(b - a) for a, b in zip(left, left[1:])]
        self.assertLessEqual(max(abs(s) for s in steps), 0.1)
        self.assertTrue(all(s <= 1e-6 for s in steps))
        self.assertAlmostEqual(float(left[9]), math.exp(-1.0), places=2)
        self.assertGreaterEqual(float(left.min()), -1e-6)
        self.assertLessEqual(float(right.max()), 1.0 + 1e-6)
        self.assertAlmostEqual(float(left[-1]), 0.0, places=3)
        self.assertAlmostEqual(float(right[-1]), 1.0, places=3)

    def test_small_update_glides_like_a_large_one(self):
        # Fixed-rate ramps finish small moves almost at once (audible
        # steps); smoothing spreads every move over the time constant.
        mixer = real_mixer()
        mixer.start(pcm_ones(400), 0.5, 0.5, meta())
        mixer.set_target(1, 0.4, 0.4)
        out = render(mixer, 10)
        self.assertAlmostEqual(float(out[9, 0]),
                               0.4 + 0.1 * math.exp(-1.0), places=3)

    def test_successive_updates_blend_without_reset(self):
        mixer = real_mixer()
        mixer.start(pcm_ones(400), 0.0, 0.0, meta())
        mixer.set_target(1, 1.0, 1.0)
        first = render(mixer, 5)
        mixer.set_target(1, 0.5, 0.5)
        second = render(mixer, 5)
        # The glide continues from where it was: no jump at the update.
        self.assertLess(abs(float(second[0, 0] - first[-1, 0])), 0.1)

    def test_zero_ramp_jumps_at_once(self):
        mixer = real_mixer(ramp_ms=0.0)
        mixer.start(pcm_ones(50), 1.0, 1.0, meta())
        mixer.set_target(1, 0.25, 0.25)
        self.assertAlmostEqual(float(render(mixer, 1)[0, 0]), 0.25, 3)

    def test_set_target_unknown_row_is_noop(self):
        mixer = real_mixer()
        mixer.start(pcm_ones(10), 0.5, 0.5, meta())
        mixer.set_target(2, 0.0, 0.0)
        self.assertAlmostEqual(float(render(mixer, 1)[0, 0]), 0.5, 3)

    def test_without_turns_speaker_busy_and_full(self):
        mixer = real_mixer()
        self.assertIsNone(mixer.start(pcm_ones(50), 1, 1, meta()))
        self.assertEqual(mixer.start(pcm_ones(50), 1, 1, meta()),
                         'speaker busy')
        mixer.start(pcm_ones(50), 1, 1, meta(speaker=('bot', 2)))
        self.assertEqual(mixer.start(pcm_ones(50), 1, 1,
                                     meta(speaker=('bot', 3))),
                         'mixer full')

    def test_clip_ends_and_playing_empties(self):
        mixer = real_mixer()
        mixer.start(pcm_ones(5), 1, 1, meta())
        self.assertIn(('bot', 55), mixer.playing())
        render(mixer, 10)
        self.assertEqual(mixer.playing(), {})
        self.assertFalse(mixer.active())


class TurnTests(unittest.TestCase):
    def test_turns_are_fifo_and_never_overtaken(self):
        mixer = real_mixer(turn_taking=True, max_waiting=2)
        mixer.start(pcm_ones(30), 1, 1, meta(speaker=('bot', 1)))
        first = mixer.reserve_turn()
        second = mixer.reserve_turn()
        order = []
        validating = threading.Event()
        release = threading.Event()

        def worker(ticket, name, slow):
            if not mixer.wait_turn(ticket, time.monotonic() + 5, 0.005):
                order.append(name + ':stale')
                return
            if slow:
                validating.set()
                release.wait(2)  # slow DB revalidation, no lock held
            order.append(name)
            mixer.start(pcm_ones(5), 1, 1,
                        meta(speaker=('bot', len(name))), ticket)

        threads = [
            threading.Thread(target=worker, args=(second, 'bb', False)),
            threading.Thread(target=worker, args=(first, 'a', True)),
        ]
        for thread in threads:
            thread.start()
        time.sleep(0.05)
        self.assertEqual(order, [])  # the first clip is still playing
        render(mixer, 30)            # ... and now it ends
        self.assertTrue(validating.wait(2))
        # The audio callback keeps running while the owner validates.
        render(mixer, 5)
        time.sleep(0.05)
        self.assertEqual(order, [])  # 'bb' cannot overtake 'a'
        release.set()
        for _ in range(200):
            render(mixer, 5)
            if len(order) == 2:
                break
            time.sleep(0.01)
        for thread in threads:
            thread.join(2)
        self.assertEqual(order, ['a', 'bb'])

    def test_waiter_drops_at_deadline(self):
        mixer = real_mixer(turn_taking=True)
        mixer.start(pcm_ones(50), 1, 1, meta())
        ticket = mixer.reserve_turn()
        self.assertFalse(mixer.wait_turn(
            ticket, time.monotonic() + 0.02, 0.005))
        self.assertEqual(mixer._queue, [])

    def test_queue_full_refuses_only_when_waiting(self):
        idle = real_mixer(turn_taking=True, max_waiting=0)
        self.assertIsNotNone(idle.reserve_turn())  # no wait needed
        busy = real_mixer(turn_taking=True, max_waiting=1)
        busy.start(pcm_ones(50), 1, 1, meta())
        self.assertIsNotNone(busy.reserve_turn())
        self.assertIsNone(busy.reserve_turn())

    def test_forfeit_frees_the_turn(self):
        mixer = real_mixer(turn_taking=True)
        ticket = mixer.reserve_turn()
        self.assertTrue(mixer.wait_turn(ticket, time.monotonic() + 1,
                                        0.005))
        other = mixer.reserve_turn()
        mixer.forfeit(ticket)
        self.assertTrue(mixer.wait_turn(other, time.monotonic() + 1,
                                        0.005))


class LeaseAndLiveTests(unittest.TestCase):
    def test_lease_length_from_pcm(self):
        db = FakeDB([row()])
        make_agent(db).tick()
        # FakeEngine returns 100 frames at 22050 Hz.
        self.assertEqual(db.leases[1], int(100 * 1_000_000 / 22050))

    def test_mixer_refusal_after_lease_expires_it(self):
        db = FakeDB([row()])
        make_agent(db, mixer=FakeMixer(accept=False)).tick()
        self.assertEqual(db.leases.keys(), {1})
        self.assertEqual(db.rows[1]['state'], 'expired')

    def test_stale_at_start_takes_no_lease(self):
        db = FakeDB([row()])

        def relog(fake):
            fake.presence = (11, 7)

        db.on_revalidate = relog
        make_agent(db).tick()
        self.assertEqual(db.leases, {})
        self.assertEqual(db.rows[1]['state'], 'expired')

    def live_row(self, generation=10, listener=7, presence=(10, 7)):
        return {'speaker_kind': 'bot', 'speaker_guid': 55,
                'generation': generation, 'listener_guid': listener,
                'distance': 30.0, 'rel_angle': 1.0,
                'p_generation': presence[0], 'p_listener': presence[1]}

    def playing_mixer(self, generation=10):
        mixer = FakeMixer()
        mixer.current = {('bot', 55): meta(generation=generation)}
        return mixer

    def test_live_target_applies_to_matching_clip(self):
        db = FakeDB([])
        db.live = [self.live_row()]
        mixer = self.playing_mixer()
        make_agent(db, mixer=mixer).tick()
        self.assertEqual(len(mixer.targets), 1)
        row_id, left, right = mixer.targets[0]
        self.assertEqual(row_id, 1)
        self.assertGreater(left, right)  # positive angle: on the left

    def test_old_clip_ignores_new_session_row(self):
        db = FakeDB([])
        db.live = [self.live_row(generation=11, presence=(11, 7))]
        mixer = self.playing_mixer(generation=10)
        make_agent(db, mixer=mixer).tick()
        self.assertEqual(mixer.targets, [])

    def test_new_clip_ignores_late_old_upsert(self):
        db = FakeDB([])
        db.live = [self.live_row(generation=10, presence=(11, 7))]
        mixer = self.playing_mixer(generation=11)
        make_agent(db, mixer=mixer).tick()
        self.assertEqual(mixer.targets, [])

    def test_other_listener_row_ignored(self):
        db = FakeDB([])
        db.live = [self.live_row(listener=8, presence=(10, 8))]
        mixer = self.playing_mixer()
        make_agent(db, mixer=mixer).tick()
        self.assertEqual(mixer.targets, [])

    def test_no_live_query_when_idle_or_disabled(self):
        db = FakeDB([])
        make_agent(db).tick()
        self.assertFalse(any('llm_chatter_voice_live' in sql
                             for sql, _ in db.log))
        config = load_voice_config({
            'LLMChatter.Voice.BoundAccountId': '3',
            'LLMChatter.Voice.Live.Enable': '0'})
        agent = VoiceAgent(config, VoiceMap(VOICES), FakeEngine(),
                           self.playing_mixer(), lambda: db,
                           InlineExecutor(), clock=Clock())
        agent.tick()
        self.assertFalse(any('llm_chatter_voice_live' in sql
                             for sql, _ in db.log))

    def test_slow_lease_past_deadline_never_starts(self):
        db = FakeDB([row()])
        clock = Clock()
        mixer = FakeMixer()

        def slow_write(fake):
            clock.now += 20  # the CAS succeeds, but returns too late

        db.on_lease = slow_write
        make_agent(db, mixer=mixer, clock=clock).tick()
        self.assertEqual(mixer.played, [])
        self.assertEqual(db.rows[1]['state'], 'expired')

    def test_lease_refused_when_presence_moved(self):
        db = FakeDB([row()])

        def relog_during_write(fake):
            fake.presence = (11, 7)

        db.on_lease = relog_during_write
        mixer = FakeMixer()
        make_agent(db, mixer=mixer).tick()
        self.assertEqual(db.leases, {})
        self.assertEqual(mixer.played, [])
        self.assertEqual(db.rows[1]['state'], 'expired')

    def test_live_query_never_moves_a_replacement_clip(self):
        mixer = real_mixer()
        mixer.start(pcm_ones(5), 0.5, 0.5, meta(row_id=1))
        db = FakeDB([])
        db.live = [self.live_row()]

        def replace_clip(fake):
            # While the query runs, clip 1 ends and the same speaker
            # starts row 2 in a new session.
            render(mixer, 10)
            mixer.start(pcm_ones(50), 0.5, 0.5,
                        meta(row_id=2, generation=11))

        db.on_live = replace_clip
        make_agent(db, mixer=mixer).tick()
        out = render(mixer, 20)
        self.assertAlmostEqual(float(out[-1, 0]), 0.5, places=3)
        self.assertAlmostEqual(float(out[-1, 1]), 0.5, places=3)

    def test_start_failure_releases_turn_and_lease(self):
        db = FakeDB([row()])
        mixer = real_mixer(turn_taking=True)
        agent = make_agent(db, mixer=mixer)
        # Gains the mixer cannot convert: start() raises after lease.
        agent._levels = lambda *args: ('loud', 'quiet')
        agent.tick()
        self.assertEqual(db.rows[1]['state'], 'expired')
        self.assertIsNone(mixer._owner)
        follower = mixer.reserve_turn()
        self.assertTrue(mixer.wait_turn(follower, time.monotonic() + 1,
                                        0.005))

    def test_odd_length_audio_is_refused_cleanly(self):
        class OddEngine(FakeEngine):
            def synthesize(self, text, voice, timeout):
                return b'\x00\x01\x02'

        db = FakeDB([row()])
        mixer = real_mixer(turn_taking=True)
        make_agent(db, engine=OddEngine(), mixer=mixer).tick()
        self.assertEqual(db.rows[1]['state'], 'expired')
        self.assertEqual(mixer.playing(), {})
        self.assertIsNone(mixer._owner)

    def test_finished_clip_is_acknowledged_played(self):
        db = FakeDB([row()])
        mixer = FakeMixer()
        agent = make_agent(db, mixer=mixer)
        agent.tick()                      # starts the clip
        self.assertEqual(db.rows[1]['state'], 'playing')
        mixer.current = {('bot', 55): meta(row_id=1)}
        agent.tick()                      # still sounding
        self.assertEqual(db.rows[1]['state'], 'playing')
        mixer.current = {}
        agent.tick()                      # finished
        self.assertEqual(db.rows[1]['state'], 'played')
        self.assertEqual(agent._sounding, set())

    def test_refused_clip_is_never_played(self):
        db = FakeDB([row()])
        agent = make_agent(db, mixer=FakeMixer(accept=False))
        agent.tick()
        agent.tick()
        self.assertEqual(db.rows[1]['state'], 'expired')
        self.assertEqual(agent._sounding, set())

    def test_no_completion_work_when_nothing_sounds(self):
        db = FakeDB([])
        make_agent(db).tick()
        self.assertFalse(any("'played'" in str(params)
                             for _, params in db.log))

    def test_crash_recovery_expires_never_plays(self):
        source = Path(agent_mod.__file__).read_text(encoding='utf-8')
        start = source.index('def _maybe_prune')
        prune = source[start:source.index('\n    def ', start + 10)]
        self.assertIn("SET state = 'expired'", prune)
        self.assertNotIn("SET state = 'played'", prune)

    def test_proximity_voices_fade_to_silence_party_keeps_floor(self):
        config = load_voice_config({'LLMChatter.Voice.SayRadius': '25'})
        agent = VoiceAgent(config, VoiceMap(VOICES), FakeEngine(),
                           FakeMixer(), lambda: None, InlineExecutor(),
                           clock=Clock())
        left, right = agent._levels(25.0, 0.0, 'msay')
        self.assertEqual((left, right), (0.0, 0.0))
        near = sum(agent._levels(2.0, 0.0, 'say'))
        mid = sum(agent._levels(12.5, 0.0, 'say'))
        self.assertGreater(near, mid)
        self.assertGreater(mid, 0.0)
        far_party = sum(agent._levels(99.0, 0.0, 'party'))
        self.assertGreater(far_party, 0.0)  # MinGain floor kept

    def test_turn_taking_is_default(self):
        config = load_voice_config({})
        self.assertTrue(config['turn_taking'])
        self.assertEqual(config['max_waiting'], 2)


class FakeCameraSample:
    def __init__(self, x, y, yaw):
        self.x, self.y, self.yaw = x, y, yaw


class FakeCamera:
    """Holds one sample taken for one expected presence."""

    def __init__(self, sample=None, expect=(10, 7, 1)):
        self.sample = sample
        self.expect = expect
        self.updates = []
        self.fresh_calls = 0

    def update(self, expect):
        self.updates.append(expect)
        if expect != self.expect:
            self.expect = expect
            self.sample = None
        return self.sample

    def fresh(self, expect=None):
        self.fresh_calls += 1
        if expect is not None and expect != self.expect:
            return None
        return self.sample


def camera_agent(camera, source='camera', db=None, mixer=None,
                 presence=(10, 7, 1)):
    config = load_voice_config({'LLMChatter.Voice.BoundAccountId': '3',
                                'LLMChatter.Voice.Pan.Source': source})
    agent = VoiceAgent(config, VoiceMap(VOICES), FakeEngine(),
                       mixer or FakeMixer(), lambda: db or FakeDB([]),
                       InlineExecutor(), clock=Clock(), camera=camera)
    agent._presence = presence
    return agent


ORIGIN_CAMERA = FakeCameraSample(0.0, 0.0, 0.0)  # synthetic


class CameraPanTests(unittest.TestCase):
    def test_speaker_left_of_camera_is_left_even_if_right_of_character(self):
        # Synthetic: camera at the origin looking along +x; a speaker at
        # +y is on the camera's left while the server says right.
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA))
        left, right = agent._levels(5.0, -1.2, 'say', 0.0, 5.0, 10, 7)
        self.assertGreater(left, right)

    def test_no_fresh_sample_falls_back_to_character(self):
        agent = camera_agent(FakeCamera(None))
        left, right = agent._levels(5.0, -1.2, 'say', 0.0, 5.0, 10, 7)
        self.assertLess(left, right)  # server rel_angle: right

    def test_start_after_generation_change_ignores_old_sample(self):
        # The camera still holds a generation-10 sample; the clip and
        # presence are generation 11 (relog/map change): character pan.
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA, (10, 7, 1)),
                             presence=(11, 7, 1))
        left, right = agent._levels(5.0, -1.2, 'say', 0.0, 5.0, 11, 7)
        self.assertLess(left, right)

    def test_start_after_map_change_ignores_old_sample(self):
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA, (10, 7, 1)),
                             presence=(10, 7, 571))
        left, right = agent._levels(5.0, -1.2, 'say', 0.0, 5.0, 10, 7)
        self.assertLess(left, right)

    def test_old_session_clip_never_uses_camera(self):
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA))
        left, right = agent._levels(5.0, -1.2, 'say', 0.0, 5.0, 9, 7)
        self.assertLess(left, right)

    def test_failed_presence_refresh_disables_camera(self):
        class BrokenDB(FakeDB):
            def select(self, sql, params):
                raise ConnectionError('lost')

        mixer = FakeMixer()
        mixer.current = {('bot', 55): meta(row_id=1)}
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA), mixer=mixer)
        with self.assertRaises(ConnectionError):
            agent._refresh_presence(BrokenDB([]))
        self.assertIsNone(agent._presence)
        left, right = agent._levels(5.0, -1.2, 'say', 0.0, 5.0, 10, 7)
        self.assertLess(left, right)

    def test_character_source_never_touches_camera(self):
        camera = FakeCamera(ORIGIN_CAMERA)
        agent = camera_agent(camera, source='character')
        agent._levels(5.0, -1.2, 'say', 0.0, 5.0, 10, 7)
        self.assertEqual(camera.fresh_calls, 0)

    def test_character_mode_keeps_no_geometry(self):
        db = FakeDB([row(i, speaker=100 + i) for i in range(1, 21)])
        mixer = FakeMixer()
        agent = camera_agent(None, source='character', db=db, mixer=mixer)
        agent.tick()
        self.assertEqual(len(mixer.played), 20)
        agent.tick()  # all clips finished: acknowledged
        self.assertEqual(agent._geometry, {})
        self.assertEqual(agent._sounding, set())

    def test_camera_mode_geometry_is_released_when_clips_end(self):
        db = FakeDB([row(1), row(2, speaker=56)])
        mixer = FakeMixer()
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA), db=db, mixer=mixer)
        agent.tick()
        self.assertEqual(set(agent._geometry), {1, 2})
        agent.tick()  # FakeMixer reports nothing playing: both ended
        self.assertEqual(agent._geometry, {})

    def test_exception_before_start_releases_geometry(self):
        db = FakeDB([row(i, speaker=100 + i) for i in range(1, 21)])
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA), db=db)

        def broken_levels(*args, **kwargs):
            raise RuntimeError('gain failure')

        agent._levels = broken_levels
        agent.tick()
        self.assertEqual(agent._geometry, {})
        self.assertEqual(agent._sounding, set())

    def test_newer_presence_during_start_keeps_character_pan(self):
        # The clip and the camera sample belong to generation 10. After
        # the lease, generation 11 on map 571 is observed (relog/map
        # change); the worker must not roll presence back and must pan by
        # the character, not the old camera sample.
        clip = dict(row(), speaker_x=0.0, speaker_y=5.0, rel_angle=-1.2)
        db = FakeDB([clip])
        mixer = FakeMixer()
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA, (10, 7, 1)),
                             db=db, mixer=mixer)

        def newer_presence(fake):
            agent._observe_presence(11, 7, 571)

        db.on_lease = newer_presence
        agent.tick()
        self.assertEqual(agent._presence, (11, 7, 571))
        left, right, _ = mixer.played[0]
        self.assertLess(left, right)  # character pan (server: right)

    def test_repan_during_start_cannot_drop_new_clip_geometry(self):
        # Another clip already plays. The worker prepares clip 1; a main
        # repan runs right before mixer.start. The new clip must still
        # end up with geometry once it is in the mixer.
        clip = dict(row(), speaker_x=0.0, speaker_y=5.0)
        db = FakeDB([clip])
        mixer = FakeMixer()
        mixer.current = {('bot', 99): meta(speaker=('bot', 99), row_id=50)}
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA), db=db, mixer=mixer)
        original_start = mixer.start

        def start_after_repan(pcm, left, right, clip_meta, ticket=None):
            agent._repan_camera()          # main thread interleaves here
            result = original_start(pcm, left, right, clip_meta, ticket)
            mixer.current[clip_meta['speaker']] = clip_meta
            return result

        mixer.start = start_after_repan
        agent.tick()
        self.assertIn(1, agent._geometry)
        agent._repan_camera()              # next repan keeps it
        self.assertIn(1, agent._geometry)

    def test_stale_snapshot_cannot_prune_a_clip_starting_meanwhile(self):
        # The repan takes its playing snapshot; a worker then starts
        # clip 1 and publishes its geometry; the prune must not delete
        # it. The worker blocks on the agent lock while the repan holds
        # it, so it publishes after the prune.
        mixer = FakeMixer()
        mixer.current = {('bot', 99): meta(speaker=('bot', 99), row_id=50)}
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA), mixer=mixer)
        original_playing = mixer.playing
        worker = {}

        def start_and_publish():
            mixer.current[('bot', 55)] = meta(row_id=1)
            with agent._lock:
                agent._geometry[1] = {
                    'distance': 5.0, 'rel_angle': 0.0, 'x': 0.0, 'y': 5.0,
                    'channel': 'say', 'generation': 10, 'listener': 7}

        def playing_then_worker():
            snapshot = original_playing()
            if 'thread' not in worker:
                worker['thread'] = threading.Thread(target=start_and_publish)
                worker['thread'].start()
                worker['thread'].join(0.2)  # publishes now unless blocked
            return snapshot

        mixer.playing = playing_then_worker
        agent._repan_camera()
        worker['thread'].join(2)
        self.assertIn(1, agent._geometry)

    def test_presence_never_rolls_back(self):
        agent = camera_agent(FakeCamera(ORIGIN_CAMERA))
        agent._observe_presence(12, 7, 1)
        agent._forget_presence()           # transient unknown state
        agent._observe_presence(10, 7, 1)  # delayed older snapshot
        self.assertIsNone(agent._presence)
        agent._observe_presence(12, 7, 1)
        self.assertEqual(agent._presence, (12, 7, 1))

    def test_repan_reads_camera_not_db_and_rejects_old_session(self):
        db = FakeDB([])
        mixer = FakeMixer()
        mixer.current = {('bot', 55): meta(row_id=1),
                         ('bot', 56): meta(speaker=('bot', 56), row_id=2,
                                           generation=9)}
        camera = FakeCamera(ORIGIN_CAMERA)
        agent = camera_agent(camera, db=db, mixer=mixer)
        agent._geometry = {
            1: {'distance': 5.0, 'rel_angle': 0.0, 'x': 0.0, 'y': 5.0,
                'channel': 'say', 'generation': 10, 'listener': 7},
            2: {'distance': 5.0, 'rel_angle': 0.0, 'x': 0.0, 'y': 5.0,
                'channel': 'say', 'generation': 9, 'listener': 7},
            3: {'distance': 1.0, 'rel_angle': 0.0, 'x': 0.0, 'y': 0.0,
                'channel': 'say', 'generation': 10, 'listener': 7}}
        agent._repan_camera()
        self.assertEqual(db.log, [])                 # no DB at camera rate
        self.assertEqual(camera.updates, [(10, 7, 1)])
        self.assertEqual([t[0] for t in mixer.targets], [1])  # gen 9 skipped
        self.assertNotIn(3, agent._geometry)         # finished clip dropped

    def test_no_camera_reads_while_idle(self):
        camera = FakeCamera(ORIGIN_CAMERA)
        agent = camera_agent(camera)
        agent._repan_camera()
        self.assertEqual(camera.updates, [])

    def test_camera_keys_default(self):
        config = load_voice_config({})
        self.assertEqual(config['pan_source'], 'character')
        self.assertEqual(config['camera_offsets']['world_frame'], 0xB7436C)
        self.assertEqual(config['camera_offsets']['player_guid'], 0xCA1238)


class CountingStream:
    """A fake output stream: counts opens; failures are configurable."""

    opened = 0

    def __init__(self, fail_open=False, fail_start=False, active_raises=False):
        if fail_open:
            raise OSError('no audio device')
        CountingStream.opened += 1
        self.fail_start = fail_start
        self.active_raises = active_raises
        self._active = True
        self.closed = False

    @property
    def active(self):
        if self.active_raises:
            raise RuntimeError('PortAudio: unanticipated host error')
        return self._active

    def start(self):
        if self.fail_start:
            raise OSError('device busy')

    def abort(self):
        self._active = False

    def close(self):
        self.closed = True


class AudioWatchdogTests(unittest.TestCase):
    def setUp(self):
        CountingStream.opened = 0
        self.clock = Clock()
        self.next_stream = {}
        self.created = []

        def factory(rate, callback):
            stream = CountingStream(**self.next_stream)
            self.created.append(stream)
            return stream

        self.mixer = Mixer(1000, 2, stream_factory=factory, clock=self.clock)
        self.db = FakeDB([])
        self.agent = make_agent(self.db, mixer=self.mixer, clock=self.clock)

    def playing_row(self, row_id):
        self.db.rows[row_id] = dict(row(row_id), state='playing')
        self.agent._sounding.add(row_id)
        self.mixer.start(pcm_ones(500), 1, 1,
                         meta(speaker=('bot', row_id), row_id=row_id))

    # -- detection
    def test_healthy_stream_is_not_stalled(self):
        self.mixer.start(pcm_ones(500), 1, 1, meta())
        self.clock.now += 0.5
        render(self.mixer, 10)
        self.clock.now += 0.5
        self.assertFalse(self.mixer.stalled(1.0))

    def test_idle_mixer_is_never_stalled(self):
        self.clock.now += 60
        self.assertFalse(self.mixer.stalled(1.0))

    def test_inactive_stream_is_stalled(self):
        self.mixer._stream._active = False
        self.assertTrue(self.mixer.stalled(1.0))

    def test_failing_health_query_enters_recovery(self):
        self.mixer._stream.active_raises = True
        self.assertTrue(self.mixer.stalled(1.0))
        self.agent.tick()
        self.assertEqual(CountingStream.opened, 2)

    # -- recovery through tick()
    def test_stall_reopens_and_expires_stuck_rows(self):
        self.playing_row(4)
        self.clock.now += 1.5
        self.agent.tick()
        self.assertEqual(self.db.rows[4]['state'], 'expired')
        self.assertEqual(self.agent._sounding, set())
        self.assertEqual(CountingStream.opened, 2)
        self.assertTrue(self.created[0].closed)

    def test_failed_reopen_never_marks_rows_played(self):
        self.playing_row(4)
        self.clock.now += 1.5
        self.next_stream = {'fail_open': True}
        self.agent.tick()
        self.assertEqual(self.db.rows[4]['state'], 'expired')
        self.agent.tick()
        self.assertEqual(self.db.rows[4]['state'], 'expired')

    def test_expire_db_error_retries_and_never_plays(self):
        self.playing_row(4)
        self.playing_row(5)
        self.clock.now += 1.5
        original = self.db.update
        failures = {'left': 1}

        def flaky(params):
            if params[0] == 'expired' and failures['left']:
                failures['left'] -= 1
                raise ConnectionError('lost')
            return original(params)

        self.db.update = flaky
        with self.assertRaises(ConnectionError):
            self.agent.tick()
        self.assertNotIn(4, self.agent._sounding)
        self.assertNotIn(5, self.agent._sounding)
        self.agent.tick()
        self.assertEqual(self.db.rows[4]['state'], 'expired')
        self.assertEqual(self.db.rows[5]['state'], 'expired')

    def test_failed_reopen_is_retried_without_a_new_clip(self):
        self.playing_row(4)
        self.clock.now += 1.5
        self.next_stream = {'fail_open': True}
        self.agent.tick()                       # first attempt fails
        self.assertEqual(CountingStream.opened, 1)
        self.next_stream = {}
        self.clock.now += 1.0
        self.agent.tick()                       # inside the backoff
        self.assertEqual(CountingStream.opened, 1)
        self.clock.now += 5.0
        self.agent.tick()                       # retried, no new clip
        self.assertEqual(CountingStream.opened, 2)
        self.assertFalse(self.mixer.stalled(1.0))

    def test_failed_start_closes_the_replacement(self):
        self.playing_row(4)
        self.clock.now += 1.5
        self.next_stream = {'fail_start': True}
        self.agent.tick()
        self.assertTrue(self.created[-1].closed)
        self.assertEqual(self.db.rows[4]['state'], 'expired')

    def test_start_is_refused_while_reopening(self):
        self.playing_row(4)
        self.clock.now += 1.5
        results = []

        def factory_with_worker(rate, callback):
            # A worker tries to start a clip mid-reopen.
            results.append(self.mixer.start(pcm_ones(50), 1, 1,
                                            meta(row_id=9)))
            return CountingStream()

        self.mixer._factory = factory_with_worker
        self.agent.tick()
        self.assertEqual(results, ['audio unavailable'])
        self.assertIsNone(self.mixer.start(pcm_ones(50), 1, 1,
                                           meta(row_id=10)))


if __name__ == '__main__':
    unittest.main()
