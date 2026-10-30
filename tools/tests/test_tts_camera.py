"""Offline camera tests: a fake process memory, no client, no Windows."""

import math
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tts_camera import CameraOffsets, ClientCamera, read_camera  # noqa: E402

OFF = CameraOffsets()
FRAME = 0x187A0BAC
CAMERA = 0x16B327B8


def basis(yaw):
    forward = (math.cos(yaw), math.sin(yaw), 0.0)
    side = (-math.sin(yaw), math.cos(yaw), 0.0)
    up = (0.0, 0.0, 1.0)
    return forward, side, up


class FakeMemory:
    """Process memory keyed by (address, size); values may be callables."""

    def __init__(self, pid=1, x=100.0, y=200.0, yaw=0.0, guid=2005,
                 map_id=1, loaded=True, camera_type=0xA1EA54):
        self.pid = pid
        self.exited = False
        self.closed = False
        self.values = {}
        self.set_camera(x, y, yaw)
        self.values[(OFF.world_frame, 4)] = struct.pack('<I', FRAME)
        self.values[(FRAME + OFF.active_camera, 4)] = struct.pack(
            '<I', CAMERA)
        self.values[(CAMERA, 4)] = struct.pack('<I', camera_type)
        self.set_identity(guid, map_id, loaded)

    def set_camera(self, x, y, yaw):
        forward, side, up = basis(yaw)
        self.values[(CAMERA + 8, 48)] = struct.pack(
            '<12f', x, y, 10.0, *forward, *side, *up)

    def set_identity(self, guid, map_id, loaded):
        self.values[(OFF.player_guid, 8)] = struct.pack(
            '<Q', (0x0000000000000000) | guid)
        self.values[(OFF.map_id, 4)] = struct.pack('<I', map_id)
        self.values[(OFF.world_loaded, 1)] = b'\x01' if loaded else b'\x00'

    def read(self, address, size):
        value = self.values.get((address, size))
        return value() if callable(value) else value

    def alive(self):
        return not self.exited

    def close(self):
        self.closed = True


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


EXPECT = (7, 2005, 1)


def make_camera(processes, clock=None, **kwargs):
    by_pid = {mem.pid: mem for mem in processes}
    kwargs.setdefault('rescan_seconds', 0.0)
    return ClientCamera(
        OFF, clock=clock or Clock(),
        memory_factory=lambda pid: by_pid[pid],
        pid_finder=lambda name: list(by_pid), **kwargs)


class ReadCameraTests(unittest.TestCase):
    def test_valid_sample_and_yaw(self):
        sample, reason = read_camera(FakeMemory(yaw=1.25), OFF)
        self.assertIsNone(reason)
        self.assertAlmostEqual(sample.yaw, 1.25, places=4)
        self.assertEqual((sample.x, sample.y), (100.0, 200.0))
        self.assertEqual(sample.identity.guid_low, 2005)

    def test_wrong_type_rejected(self):
        self.assertIsNone(read_camera(FakeMemory(camera_type=1), OFF)[0])

    def test_null_pointer_rejected(self):
        mem = FakeMemory()
        mem.values[(OFF.world_frame, 4)] = struct.pack('<I', 0)
        self.assertIsNone(read_camera(mem, OFF)[0])

    def test_non_orthonormal_and_nan_rejected(self):
        mem = FakeMemory()
        mem.values[(CAMERA + 8, 48)] = struct.pack(
            '<12f', 1, 2, 3, 1, 1, 0, 0, 1, 0, 0, 0, 1)
        self.assertIsNone(read_camera(mem, OFF)[0])
        mem.values[(CAMERA + 8, 48)] = struct.pack(
            '<12f', float('nan'), 2, 3, 1, 0, 0, 0, 1, 0, 0, 0, 1)
        self.assertIsNone(read_camera(mem, OFF)[0])

    def test_world_change_during_read_discarded(self):
        mem = FakeMemory()
        maps = iter([1, 571])
        mem.values[(OFF.map_id, 4)] = lambda: struct.pack('<I', next(maps))
        sample, reason = read_camera(mem, OFF)
        self.assertIsNone(sample)
        self.assertIn('changed', reason)


class BindingTests(unittest.TestCase):
    def test_binds_only_the_listeners_client(self):
        other = FakeMemory(pid=1, guid=9999)
        mine = FakeMemory(pid=2)
        camera = make_camera([other, mine])
        self.assertIsNotNone(camera.update(EXPECT))
        self.assertEqual(camera.bound_pid, 2)
        self.assertTrue(other.closed)

    def test_map_mismatch_and_not_loaded_give_no_camera(self):
        self.assertIsNone(make_camera([FakeMemory(map_id=0)]).update(EXPECT))
        self.assertIsNone(
            make_camera([FakeMemory(loaded=False)]).update(EXPECT))

    def test_several_qualifying_clients_are_unavailable(self):
        camera = make_camera([FakeMemory(pid=1), FakeMemory(pid=2)])
        self.assertIsNone(camera.update(EXPECT))
        self.assertIsNone(camera.bound_pid)

    def test_explicit_pid_still_needs_identity(self):
        camera = make_camera([FakeMemory(pid=5, guid=1)], process_id=5)
        self.assertIsNone(camera.update(EXPECT))

    def test_presence_change_clears_sample(self):
        clock = Clock()
        camera = make_camera([FakeMemory()], clock=clock)
        self.assertIsNotNone(camera.update(EXPECT))
        self.assertIsNotNone(camera.fresh())
        camera.update((8, 0, 0))  # logged out: new generation, no listener
        self.assertIsNone(camera.fresh())

    def test_sample_is_tagged_with_its_presence(self):
        camera = make_camera([FakeMemory()])
        self.assertIsNotNone(camera.update(EXPECT))
        self.assertIsNotNone(camera.fresh(EXPECT))
        # Another session asks: the generation-7 sample is not theirs,
        # even before the next update switches the expectation.
        self.assertIsNone(camera.fresh((8, 2005, 1)))
        tag, _ = camera._accepted
        self.assertEqual(tag, EXPECT)

    def test_sample_ages_out(self):
        clock = Clock()
        camera = make_camera([FakeMemory()], clock=clock, max_age=0.2)
        camera.update(EXPECT)
        clock.now += 0.5
        self.assertIsNone(camera.fresh())

    def test_transient_failure_keeps_binding(self):
        mem = FakeMemory()
        camera = make_camera([mem], fail_ticks=2)
        camera.update(EXPECT)
        good = mem.values[(CAMERA + 8, 48)]
        mem.values[(CAMERA + 8, 48)] = None
        self.assertIsNone(camera.update(EXPECT))
        self.assertEqual(camera.bound_pid, 1)
        mem.values[(CAMERA + 8, 48)] = good
        self.assertIsNotNone(camera.update(EXPECT))

    def test_process_exit_unbinds_and_rebinds_by_identity(self):
        first = FakeMemory(pid=1)
        camera = make_camera([first])
        camera.update(EXPECT)
        first.exited = True
        # Still listed but dead: never rebound.
        self.assertIsNone(camera.update(EXPECT))
        self.assertIsNone(camera.bound_pid)
        restarted = FakeMemory(pid=3)
        camera._pid_finder = lambda name: [1, 3]
        camera._memory_factory = {1: first, 3: restarted}.__getitem__
        self.assertIsNotNone(camera.update(EXPECT))
        self.assertTrue(first.closed)
        self.assertEqual(camera.bound_pid, 3)

    def test_client_switching_character_unbinds(self):
        mem = FakeMemory()
        camera = make_camera([mem])
        camera.update(EXPECT)
        mem.set_identity(4242, 1, True)
        self.assertIsNone(camera.update(EXPECT))
        self.assertIsNone(camera.bound_pid)

    def test_teleport_rebaselines_after_consistent_samples(self):
        mem = FakeMemory(x=100.0)
        camera = make_camera([mem], max_jump=50, rebaseline_ticks=3)
        self.assertIsNotNone(camera.update(EXPECT))
        mem.set_camera(900.0, 200.0, 0.0)
        self.assertIsNone(camera.update(EXPECT))
        self.assertIsNone(camera.update(EXPECT))
        self.assertIsNotNone(camera.update(EXPECT))  # third calm sample
        mem.set_camera(901.0, 200.0, 0.0)
        self.assertIsNotNone(camera.update(EXPECT))



# Recorded on the user's client (CAMERA-PAN.md section 7), rounded as the
# probe printed them: camera position and forward row while orbiting the
# character at about (6459.5, 409.5). Side and up rows were not printed,
# so they are completed orthonormally from the recorded forward row.
RECORDED = (
    {'pos': (6458.9, 403.6, 14.5), 'fwd': (0.11, 0.98, -0.18),
     'yaw_deg': 83.4},
    {'pos': (6464.9, 412.3, 14.0), 'fwd': (-0.88, -0.47, -0.10),
     'yaw_deg': 208.1},
)
ORBIT_CENTER = (6459.5, 409.5)


def recorded_memory(entry):
    fx, fy, fz = entry['fwd']
    norm = math.sqrt(fx * fx + fy * fy + fz * fz)
    forward = (fx / norm, fy / norm, fz / norm)
    side = (-forward[1], forward[0], 0.0)
    side_norm = math.hypot(side[0], side[1])
    side = (side[0] / side_norm, side[1] / side_norm, 0.0)
    up = (forward[1] * side[2] - forward[2] * side[1],
          forward[2] * side[0] - forward[0] * side[2],
          forward[0] * side[1] - forward[1] * side[0])
    mem = FakeMemory()
    mem.values[(CAMERA + 8, 48)] = struct.pack(
        '<12f', *entry['pos'], *forward, *side, *up)
    return mem


class RecordedConventionTests(unittest.TestCase):
    """Pins the empirically checked convention with probe values."""

    def test_recorded_yaw_matches_probe(self):
        for entry in RECORDED:
            sample, reason = read_camera(recorded_memory(entry), OFF)
            self.assertIsNone(reason)
            self.assertAlmostEqual(math.degrees(sample.yaw),
                                   entry['yaw_deg'], delta=1.0)

    def test_recorded_camera_looks_at_the_orbit_center(self):
        for entry in RECORDED:
            sample, _ = read_camera(recorded_memory(entry), OFF)
            bearing = math.atan2(ORBIT_CENTER[1] - sample.y,
                                 ORBIT_CENTER[0] - sample.x)
            off = math.remainder(bearing - sample.yaw, 2 * math.pi)
            self.assertLess(abs(math.degrees(off)), 20.0)

    def test_pan_pipeline_with_recorded_sample(self):
        from tts_agent import VoiceAgent, load_voice_config

        sample, _ = read_camera(recorded_memory(RECORDED[0]), OFF)

        class Holder:
            def fresh(self, expect=None):
                return sample

        config = load_voice_config({'LLMChatter.Voice.Pan.Source': 'camera'})
        agent = VoiceAgent(config, None, None, None, lambda: None, None,
                           camera=Holder())
        agent._presence = (10, 2005, 1)
        # A speaker 5 yd to the camera's left (yaw + 90 degrees) must be
        # louder on the left, whatever the server's character angle.
        left_x = sample.x + 5 * math.cos(sample.yaw + math.pi / 2)
        left_y = sample.y + 5 * math.sin(sample.yaw + math.pi / 2)
        left, right = agent._levels(5.0, -1.5, 'say', left_x, left_y,
                                    10, 2005)
        self.assertGreater(left, right)
        # The character the camera looks at is centred.
        left, right = agent._levels(5.0, -1.5, 'say', *ORBIT_CENTER,
                                    10, 2005)
        self.assertAlmostEqual(left, right, delta=0.2)


if __name__ == '__main__':
    unittest.main()
