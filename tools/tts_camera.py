"""Read-only camera access for the 3.3.5a client (build 12340).

The voice agent pans by the player's camera instead of the character's
facing. Only the game client knows the camera, so this module reads it
from the client process, read only (PROCESS_VM_READ). It never writes
and never touches any other process.

Every sample is identity-checked: the client's local player GUID and map
must match the server presence row before the camera is trusted, and
anything doubtful falls back to character-relative panning.

Offsets are advanced config; candidates and sources are recorded in
.agents/plans/chatter-tts-voices/chatter-tts-voices.CAMERA-PAN.md.
"""

import ctypes
import math
import struct
import sys
import time
from dataclasses import dataclass

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259
# 32-bit client: user-space pointers only (large-address-aware too).
MIN_POINTER = 0x10000
MAX_POINTER = 0xFFFE0000
WORLD_LIMIT = 20000.0
UNIT_TOLERANCE = 0.05


@dataclass(frozen=True)
class CameraOffsets:
    world_frame: int = 0xB7436C
    active_camera: int = 0x7E20
    camera_type: int = 0xA1EA54
    player_guid: int = 0xCA1238
    map_id: int = 0xADFBC4
    world_loaded: int = 0xBEBA40


@dataclass(frozen=True)
class ClientIdentity:
    guid_low: int
    map_id: int
    loaded: bool


@dataclass(frozen=True)
class CameraSample:
    x: float
    y: float
    z: float
    yaw: float
    forward: tuple
    side: tuple
    up: tuple
    identity: ClientIdentity
    taken: float


class ProcessMemory:
    """A read-only handle on one process (Windows only)."""

    def __init__(self, pid: int):
        if sys.platform != 'win32':
            raise OSError('camera reading needs Windows')
        from ctypes import wintypes
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL,
                                    wintypes.DWORD)
        k32.ReadProcessMemory.restype = wintypes.BOOL
        k32.ReadProcessMemory.argtypes = (
            wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID,
            ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t))
        k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE,
                                           ctypes.POINTER(wintypes.DWORD))
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        self._k32 = k32
        self._wintypes = wintypes
        handle = k32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION,
            False, pid)
        if not handle:
            raise OSError(ctypes.get_last_error(), 'OpenProcess failed')
        self.pid = pid
        self.handle = handle

    def read(self, address: int, size: int):
        """size bytes at address, or None if unreadable."""
        buf = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t()
        ok = self._k32.ReadProcessMemory(
            self.handle, ctypes.c_void_p(address), buf, size,
            ctypes.byref(got))
        return buf.raw if ok and got.value == size else None

    def alive(self) -> bool:
        code = self._wintypes.DWORD()
        if not self._k32.GetExitCodeProcess(self.handle,
                                             ctypes.byref(code)):
            return False
        return code.value == STILL_ACTIVE

    def close(self) -> None:
        if self.handle:
            self._k32.CloseHandle(self.handle)
            self.handle = None


def find_pids(process_name: str) -> list:
    """PIDs of processes named process_name (case-insensitive)."""
    if sys.platform != 'win32':
        return []
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD),
                    ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD),
                    ('th32DefaultHeapID', ctypes.c_void_p),
                    ('th32ModuleID', wintypes.DWORD),
                    ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD),
                    ('pcPriClassBase', ctypes.c_long),
                    ('dwFlags', wintypes.DWORD),
                    ('szExeFile', ctypes.c_wchar * 260)]

    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    # Explicit prototypes: a 64-bit HANDLE must never go through the
    # default C int conversion.
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k32.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    entry_ptr = ctypes.POINTER(PROCESSENTRY32W)
    k32.Process32FirstW.restype = wintypes.BOOL
    k32.Process32FirstW.argtypes = (wintypes.HANDLE, entry_ptr)
    k32.Process32NextW.restype = wintypes.BOOL
    k32.Process32NextW.argtypes = (wintypes.HANDLE, entry_ptr)
    k32.CloseHandle.restype = wintypes.BOOL
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    snapshot = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if not snapshot or snapshot == wintypes.HANDLE(-1).value:
        return []
    pids = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        more = k32.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            if entry.szExeFile.lower() == process_name.lower():
                pids.append(entry.th32ProcessID)
            more = k32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snapshot)
    return pids


def _u32(raw):
    return None if raw is None else struct.unpack('<I', raw)[0]


def _pointer(mem, address):
    value = _u32(mem.read(address, 4))
    if value is None or not MIN_POINTER <= value < MAX_POINTER:
        return None
    return value


def read_identity(mem, offsets: CameraOffsets):
    guid = mem.read(offsets.player_guid, 8)
    map_raw = mem.read(offsets.map_id, 4)
    loaded = mem.read(offsets.world_loaded, 1)
    if guid is None or map_raw is None or loaded is None:
        return None
    return ClientIdentity(
        guid_low=struct.unpack('<Q', guid)[0] & 0xFFFFFFFF,
        map_id=struct.unpack('<I', map_raw)[0],
        loaded=loaded != b'\x00')


def _unit(row):
    return abs(math.sqrt(sum(v * v for v in row)) - 1.0) <= UNIT_TOLERANCE


def _orthogonal(a, b):
    return abs(sum(x * y for x, y in zip(a, b))) <= UNIT_TOLERANCE


def read_camera(mem, offsets: CameraOffsets, clock=time.monotonic):
    """One validated sample, or (None, reason).

    Identity (frame, camera, type, client GUID/map/loaded) is read before
    and after one contiguous basis read; any change discards the sample,
    so a camera switch or world transition mid-read is never used.
    """
    def snapshot():
        frame = _pointer(mem, offsets.world_frame)
        if frame is None:
            return None
        camera = _pointer(mem, frame + offsets.active_camera)
        if camera is None:
            return None
        return frame, camera, _u32(mem.read(camera, 4)), \
            read_identity(mem, offsets)

    before = snapshot()
    if before is None:
        return None, 'no camera pointer'
    frame, camera, camera_type, identity = before
    if camera_type != offsets.camera_type:
        return None, f'camera type {camera_type!r} != expected'
    if identity is None:
        return None, 'identity unreadable'
    raw = mem.read(camera + 8, 48)
    if raw is None:
        return None, 'basis unreadable'
    if snapshot() != before:
        return None, 'camera or world changed during read'
    values = struct.unpack('<12f', raw)
    if not all(math.isfinite(v) for v in values):
        return None, 'non-finite values'
    position, forward, side, up = (values[0:3], values[3:6],
                                   values[6:9], values[9:12])
    if not all(abs(v) <= WORLD_LIMIT for v in position):
        return None, 'position out of world bounds'
    if not (_unit(forward) and _unit(side) and _unit(up)
            and _orthogonal(forward, side) and _orthogonal(forward, up)
            and _orthogonal(side, up)):
        return None, 'basis not orthonormal'
    yaw = math.atan2(forward[1], forward[0]) % (2.0 * math.pi)
    return CameraSample(position[0], position[1], position[2], yaw,
                        forward, side, up, identity, clock()), None


def probe(offsets: CameraOffsets, process_name: str, pid: int,
          seconds: int, presence, out=print) -> None:
    """Consented one-off check: print what the client reports.

    presence() returns (listener_guid, map_id) from the server, so the
    identity offsets can be compared with the truth.
    """
    pids = [pid] if pid else find_pids(process_name)
    out(f'Processes named {process_name}: {pids or "none"}')
    if len(pids) != 1:
        out('Need exactly one client (or set Camera.ProcessId).')
        return
    mem = ProcessMemory(pids[0])
    try:
        out(f'Attached read-only to PID {pids[0]}. Rotate the camera; '
            'with it behind your character, type .gps and compare '
            'the orientation with yaw.')
        for _ in range(seconds):
            frame = _pointer(mem, offsets.world_frame)
            camera = (_pointer(mem, frame + offsets.active_camera)
                      if frame else None)
            camera_type = _u32(mem.read(camera, 4)) if camera else None
            sample, reason = read_camera(mem, offsets)
            identity = read_identity(mem, offsets)
            server = presence()
            out(f'frame={frame and hex(frame)} camera={camera and hex(camera)}'
                f' type={camera_type and hex(camera_type)}'
                f' (expect {hex(offsets.camera_type)})')
            out(f'  client guid={identity and identity.guid_low}'
                f' map={identity and identity.map_id}'
                f' loaded={identity and identity.loaded}'
                f' | server listener={server[0]} map={server[1]}')
            if sample:
                out(f'  pos=({sample.x:.1f}, {sample.y:.1f}, {sample.z:.1f})'
                    f' yaw={math.degrees(sample.yaw):.1f} deg'
                    f' ({sample.yaw:.3f} rad)'
                    f' fwd=({sample.forward[0]:.2f}, {sample.forward[1]:.2f},'
                    f' {sample.forward[2]:.2f})')
            else:
                out(f'  no sample: {reason}')
            time.sleep(1.0)
    finally:
        mem.close()


class ClientCamera:
    """Bound, identity-checked camera samples for the voice agent.

    A process is bound only when its client shows the server's current
    listener (local player GUID) on the server's current map with the
    world loaded; none or several qualifying processes mean no camera.
    Samples, continuity history and binding are dropped whenever the
    expected listener/map/generation changes, the process exits or the
    client stops matching; callers then fall back to character pan.
    """

    def __init__(self, offsets: CameraOffsets, process_name='Wow.exe',
                 process_id=0, max_age=0.2, fail_ticks=5, max_jump=50.0,
                 rebaseline_ticks=3, rescan_seconds=5.0,
                 clock=time.monotonic, memory_factory=None,
                 pid_finder=None, log=None):
        self.offsets = offsets
        self.process_name = process_name
        self.process_id = process_id
        self.max_age = max_age
        self.fail_ticks = fail_ticks
        self.max_jump = max_jump
        self.rebaseline_ticks = rebaseline_ticks
        self.rescan_seconds = rescan_seconds
        self.clock = clock
        self._memory_factory = memory_factory or ProcessMemory
        self._pid_finder = pid_finder or find_pids
        self._log = log
        self._mem = None
        self._expect = None
        # (expect, sample) published as one reference so a reader on
        # another thread never pairs a sample with the wrong session.
        self._accepted = None
        self._baseline = None
        self._jumps = []
        self._failures = 0
        self._unavailable = False
        self._last_scan = None

    # ---------------------------------------------- state

    def _note(self, message):
        if self._log:
            self._log(message)

    def _forget(self):
        self._accepted = None
        self._baseline = None
        self._jumps = []

    def _unbind(self, reason):
        if self._mem is not None:
            self._note(f'Camera unbound from PID {self._mem.pid}: {reason}')
            self._mem.close()
        self._mem = None
        self._failures = 0
        self._forget()

    def close(self):
        self._unbind('agent stopping')

    @property
    def bound_pid(self):
        return self._mem.pid if self._mem is not None else None

    def _matches(self, identity):
        _, listener, map_id = self._expect
        return (identity is not None and identity.loaded
                and identity.guid_low == listener
                and identity.map_id == map_id)

    def _bind(self):
        now = self.clock()
        if (self._last_scan is not None
                and now - self._last_scan < self.rescan_seconds):
            return
        self._last_scan = now
        pids = ([self.process_id] if self.process_id
                else self._pid_finder(self.process_name))
        qualifying = []
        for pid in pids:
            try:
                mem = self._memory_factory(pid)
            except OSError:
                continue
            if mem.alive() and self._matches(
                    read_identity(mem, self.offsets)):
                qualifying.append(mem)
            else:
                mem.close()
        if len(qualifying) == 1:
            self._mem = qualifying[0]
            self._failures = 0
            self._unavailable = False
            self._forget()
            self._note(f'Camera bound to PID {self._mem.pid}')
            return
        for mem in qualifying:
            mem.close()
        if len(qualifying) > 1 and not self._unavailable:
            self._unavailable = True
            self._note('Camera unavailable: several clients show this '
                       'character; set LLMChatter.Voice.Camera.ProcessId')

    # ---------------------------------------------- sampling

    def update(self, expect):
        """Take one sample for expect = (generation, listener, map_id).

        Returns the accepted sample or None (use character pan).
        """
        if expect != self._expect:
            # A new session, listener or map: nothing old is reused.
            # Clear before switching, so no reader sees new tag + old
            # sample.
            self._forget()
            self._expect = expect
        if not expect or not expect[1]:
            return None
        if self._mem is not None and not self._mem.alive():
            self._unbind('process exited')
        if self._mem is None:
            self._bind()
            if self._mem is None:
                return None

        sample, _reason = read_camera(self._mem, self.offsets, self.clock)
        if sample is None:
            # Transient: keep the binding, fall back meanwhile.
            self._failures += 1
            if self._failures >= self.fail_ticks and not self._unavailable:
                self._unavailable = True
                self._note('Camera unavailable: reads keep failing; '
                           'using character panning')
            self._accepted = None
            return None
        if not self._matches(sample.identity):
            self._unbind('client no longer shows the listener/map')
            return None

        self._failures = 0
        if self._unavailable:
            self._unavailable = False
            self._note('Camera available again')
        if not self._continuous(sample):
            self._accepted = None
            return None
        self._accepted = (self._expect, sample)
        return sample

    def _continuous(self, sample):
        """Bounded jumps; a teleport is accepted after a few calm samples."""
        if self._baseline is None:
            self._baseline = sample
            return True
        jump = math.hypot(sample.x - self._baseline.x,
                          sample.y - self._baseline.y)
        if jump <= self.max_jump:
            self._baseline = sample
            self._jumps = []
            return True
        if self._jumps:
            last = self._jumps[-1]
            if math.hypot(sample.x - last.x,
                          sample.y - last.y) > self.max_jump:
                self._jumps = []
        self._jumps.append(sample)
        if len(self._jumps) >= self.rebaseline_ticks:
            self._baseline = sample
            self._jumps = []
            return True
        return False

    def fresh(self, expect=None):
        """The last accepted sample if still young enough, else None.

        With expect = (generation, listener, map_id), only a sample taken
        for exactly that session and world is returned.
        """
        accepted = self._accepted  # one atomic read of the pair
        if accepted is None:
            return None
        tag, sample = accepted
        if expect is not None and expect != tag:
            return None
        if self.clock() - sample.taken <= self.max_age:
            return sample
        return None
