#!/usr/bin/env python3
"""The single-instance lock must admit exactly one live bridge.

Two failures this covers, both raised in review of PR #49:

Ordinary duplicate startup -- launching a second bridge against the same
config must be refused rather than quietly running twice against one
event queue.

Overlapping shutdown and startup -- the release path used to unlock the
file and then unlink its pathname. A bridge starting in that window locks
the still-open file, and once the name is gone a third bridge creates a
fresh file at the same path and locks that instead, so two of them run
each believing it holds the only lock. The fix is to leave the pathname
alone, so the test pins the inode across a handoff rather than merely
checking that a second acquisition fails.

Run directly from the module root:
  python tools/tests/test_bridge_single_instance_lock.py
"""

import atexit
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import llm_chatter_bridge as bridge  # noqa: E402

BRIDGE_SOURCE = Path(bridge.__file__).resolve()


def _fresh_runtime(tmp):
    """Config dict pointing the lock at an empty scratch directory."""
    return {'LLMChatter.RuntimeDir': tmp}


def _acquire_capturing_release(config_path, config):
    """Acquire the lock, returning the real atexit release callback.

    Swapping atexit.register out for the duration is what lets the test
    exercise the production release function rather than a copy of it.
    """
    captured = []
    real_register = atexit.register

    def _capture(fn, *args, **kwargs):
        captured.append(fn)
        return fn

    atexit.register = _capture
    try:
        bridge._acquire_single_instance_lock(config_path, config)
    finally:
        atexit.register = real_register
    assert captured, 'lock acquisition registered no release callback'
    return captured[0]


def test_second_startup_for_the_same_config_is_refused():
    """The ordinary duplicate-launch case."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = os.path.join(tmp, 'mod_llm_chatter.conf')
        Path(config_path).write_text('', encoding='utf-8')
        config = _fresh_runtime(tmp)

        release = _acquire_capturing_release(config_path, config)
        try:
            raised = None
            try:
                bridge._acquire_single_instance_lock(config_path, config)
            except SystemExit as exc:
                raised = exc
            assert raised is not None, (
                'a second bridge on the same config was allowed to start')
            assert raised.code == 1
        finally:
            release()


def test_release_leaves_the_lock_file_in_place():
    """Releasing must drop the handle, not the pathname."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = os.path.join(tmp, 'mod_llm_chatter.conf')
        Path(config_path).write_text('', encoding='utf-8')
        config = _fresh_runtime(tmp)
        lock_path = bridge._lock_file_path(
            config_path, bridge._resolve_runtime_dir(config))

        release = _acquire_capturing_release(config_path, config)
        assert os.path.exists(lock_path)
        release()
        assert os.path.exists(lock_path), (
            'release unlinked the lock file, reopening the handoff race')


def test_overlapping_shutdown_and_startup_never_yields_two_holders():
    """A bridge starting as another exits must still be the only one.

    The inode check is the part that matters: if the pathname were
    unlinked and recreated, a later acquisition would lock a different
    file and succeed alongside the one already running.
    """
    with tempfile.TemporaryDirectory() as tmp:
        config_path = os.path.join(tmp, 'mod_llm_chatter.conf')
        Path(config_path).write_text('', encoding='utf-8')
        config = _fresh_runtime(tmp)
        lock_path = bridge._lock_file_path(
            config_path, bridge._resolve_runtime_dir(config))

        first_release = _acquire_capturing_release(config_path, config)
        inode_before = os.stat(lock_path).st_ino
        first_release()

        # The incoming bridge takes over the same pathname.
        second_release = _acquire_capturing_release(config_path, config)
        try:
            assert os.stat(lock_path).st_ino == inode_before, (
                'the lock pathname was replaced during handoff; a third '
                'bridge could hold a lock on the original file')

            raised = None
            try:
                bridge._acquire_single_instance_lock(config_path, config)
            except SystemExit as exc:
                raised = exc
            assert raised is not None, (
                'a third bridge started while the second still held '
                'the lock')
        finally:
            second_release()


def test_locking_backend_is_portable_across_platforms():
    """fcntl is Unix-only; importing it outright breaks Windows startup.

    The import has to stay guarded, and the rest of the module has to go
    through the dispatch helpers rather than calling fcntl directly.
    """
    source = BRIDGE_SOURCE.read_text(encoding='utf-8')
    assert '\nimport fcntl\n' not in source, (
        'fcntl imported unconditionally; a native Windows launch fails '
        'during import, before any configuration can be read')
    assert 'try:\n    import fcntl' in source
    assert 'try:\n    import msvcrt' in source

    assert callable(bridge._lock_file_exclusive)
    assert callable(bridge._unlock_file)

    # Backend calls belong only inside the two dispatch helpers: one
    # lock and one unlock per platform. Anything else is a direct
    # reach for fcntl that would break again on Windows.
    backend_calls = [
        line.strip() for line in source.splitlines()
        if 'fcntl.flock(' in line or 'msvcrt.locking(' in line
    ]
    assert len(backend_calls) == 4, (
        'expected 4 backend calls confined to _lock_file_exclusive and '
        '_unlock_file, found %d: %r' % (len(backend_calls), backend_calls))


def main() -> int:
    test_second_startup_for_the_same_config_is_refused()
    test_release_leaves_the_lock_file_in_place()
    test_overlapping_shutdown_and_startup_never_yields_two_holders()
    test_locking_backend_is_portable_across_platforms()
    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
