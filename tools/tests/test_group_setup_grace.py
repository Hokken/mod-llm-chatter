#!/usr/bin/env python3
"""Group events that race the group's setup are retried, not dropped.

The orphan guard in process_single_event drops a bot_group_* event when
its group has no llm_group_bot_traits rows, which is right for a group
that has disbanded. But the join handler writes those rows, and it runs
in the urgent lane while most group events run in the filler lane, so a
Dungeon Finder group's dungeon entry could reach the guard first and be
dropped (and the C++ entry cooldown then hid the line on re-entry too).

These tests drive the real consumer path with an in-memory database: a
young event is put back for a retry and delivered once the traits exist,
an old one still expires, and nothing changes for established groups or
lifecycle events.

Run directly from the module root:
  python tools/tests/test_group_setup_grace.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import llm_chatter_bridge as bridge  # noqa: E402

MODULE_ROOT = Path(bridge.__file__).resolve().parent.parent
GROUP_ID = 3
EVENT_ID = 5459


class FakeDb:
    """Just enough of MySQL for the orphan guard, on a fake clock."""

    def __init__(self, traits=False, created_at=0):
        self.now = created_at
        self.groups_with_traits = {GROUP_ID} if traits else set()
        self.row = {
            'status': 'pending',
            'created_at': created_at,
            'react_after': created_at,
        }
        self.deferral_attempts = 0

    def claim(self):
        """Mirror fetch_pending_events' CAS claim."""
        if (self.row['status'] != 'pending'
                or self.row['react_after'] > self.now):
            return False
        self.row['status'] = 'processing'
        return True

    def cursor(self, dictionary=False):
        return FakeCursor(self)

    def commit(self):
        pass

    def close(self):
        pass


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self.rowcount = 0
        self._rows = []

    def execute(self, sql, params=()):
        sql = ' '.join(sql.split())
        row = self.db.row
        self._rows = []
        self.rowcount = 0
        if 'FROM llm_group_bot_traits' in sql:
            if params[0] in self.db.groups_with_traits:
                self._rows = [{'1': 1}]
        elif "SET status = 'pending'" in sql:
            self.db.deferral_attempts += 1
            retry, _event_id, grace = params
            assert "status = 'processing'" in sql
            if (row['status'] == 'processing'
                    and row['created_at'] > self.db.now - grace):
                row['status'] = 'pending'
                row['react_after'] = self.db.now + retry
                self.rowcount = 1
        elif "SET status = 'expired'" in sql:
            row['status'] = 'expired'
            self.rowcount = 1
        else:
            raise AssertionError('unexpected SQL: %s' % sql)

    def fetchone(self):
        return self._rows[0] if self._rows else None


class Harness:
    """Patch the bridge's DB and handler map for one test."""

    def __init__(self, db, event_type):
        self.db = db
        self.event_type = event_type
        self.calls = 0

    def __enter__(self):
        self._saved_conn = bridge.get_db_connection
        self._saved_handler = bridge.EVENT_HANDLERS.get(self.event_type)
        bridge.get_db_connection = lambda config, database=None: self.db

        def handler(db, client, config, event):
            self.calls += 1
            return True

        bridge.EVENT_HANDLERS[self.event_type] = handler
        return self

    def __exit__(self, *exc):
        bridge.get_db_connection = self._saved_conn
        if self._saved_handler is None:
            bridge.EVENT_HANDLERS.pop(self.event_type, None)
        else:
            bridge.EVENT_HANDLERS[self.event_type] = self._saved_handler
        return False

    def attempt(self, config=None):
        assert self.db.claim(), 'event should be claimable'
        event = {
            'id': EVENT_ID,
            'event_type': self.event_type,
            'zone_id': 0,
            '_group_id': GROUP_ID,
        }
        return bridge.process_single_event(event, None, config or {})


def test_setup_race_is_retried_then_delivered_once():
    """The live case: dungeon entry reaches the guard before the join."""
    db = FakeDb(traits=False, created_at=100)
    with Harness(db, 'bot_group_dungeon_entry') as h:
        assert h.attempt() is False
        assert db.row['status'] == 'pending'
        assert db.row['react_after'] == 103, 'default retry is 3s'
        assert h.calls == 0

        assert not db.claim(), 'not due before react_after'

        db.now = 103
        db.groups_with_traits.add(GROUP_ID)
        assert h.attempt() is True
        assert h.calls == 1
        assert not db.claim(), 'delivered event must not come back'


def test_gone_group_expires_at_the_grace_boundary():
    """A disbanded group's event retries briefly, then is dropped."""
    db = FakeDb(traits=False, created_at=0)
    config = {
        'LLMChatter.Bridge.GroupSetupGraceSeconds': '10',
        'LLMChatter.Bridge.GroupSetupRetrySeconds': '4',
    }
    with Harness(db, 'bot_group_dungeon_entry') as h:
        for now in (0, 4, 8):
            db.now = now
            h.attempt(config)
            assert db.row['status'] == 'pending', now
        db.now = 12
        h.attempt(config)
        assert db.row['status'] == 'expired'
        assert h.calls == 0
        assert not db.claim(), 'an expired event is never retried'


def test_established_group_is_handled_without_the_guard():
    db = FakeDb(traits=True, created_at=0)
    with Harness(db, 'bot_group_dungeon_entry') as h:
        assert h.attempt() is True
        assert h.calls == 1
        assert db.deferral_attempts == 0
        assert db.row['status'] == 'processing', 'guard left it alone'


def test_lifecycle_events_skip_the_guard():
    for event_type in ('bot_group_join_batch', 'bot_group_farewell'):
        assert event_type in bridge._ORPHAN_GUARD_EXEMPT
        db = FakeDb(traits=False, created_at=0)
        with Harness(db, event_type) as h:
            assert h.attempt() is True, event_type
            assert h.calls == 1
            assert db.deferral_attempts == 0
            assert db.row['status'] == 'processing'


def test_grace_zero_expires_at_once():
    """0 restores the old behaviour exactly."""
    db = FakeDb(traits=False, created_at=0)
    config = {'LLMChatter.Bridge.GroupSetupGraceSeconds': '0'}
    with Harness(db, 'bot_group_dungeon_entry') as h:
        h.attempt(config)
        assert db.row['status'] == 'expired'
        assert db.deferral_attempts == 0
        assert h.calls == 0


def test_invalid_config_falls_back_safely():
    cases = (
        # (grace, retry, expected react_after offset)
        ('abc', 'xyz', 3),   # unparsable: defaults 30/3
        ('-5', '-5', None),  # clamped: grace 0, retry 1
        ('30', '0', 1),      # retry clamped to 1
    )
    for grace, retry, offset in cases:
        db = FakeDb(traits=False, created_at=50)
        config = {
            'LLMChatter.Bridge.GroupSetupGraceSeconds': grace,
            'LLMChatter.Bridge.GroupSetupRetrySeconds': retry,
        }
        with Harness(db, 'bot_group_dungeon_entry') as h:
            h.attempt(config)
            if offset is None:
                assert db.row['status'] == 'expired', (grace, retry)
            else:
                assert db.row['status'] == 'pending', (grace, retry)
                assert db.row['react_after'] == 50 + offset, (
                    grace, retry)


def test_conf_dist_documents_the_defaults():
    conf = (MODULE_ROOT / 'conf' / 'mod_llm_chatter.conf.dist').read_text(
        encoding='utf-8')
    grace = re.search(
        r'^LLMChatter\.Bridge\.GroupSetupGraceSeconds = (\d+)$', conf, re.M)
    retry = re.search(
        r'^LLMChatter\.Bridge\.GroupSetupRetrySeconds = (\d+)$', conf, re.M)
    assert grace and int(grace.group(1)) == (
        bridge._GROUP_SETUP_GRACE_DEFAULT)
    assert retry and int(retry.group(1)) == (
        bridge._GROUP_SETUP_RETRY_DEFAULT)


def main():
    tests = [
        test_setup_race_is_retried_then_delivered_once,
        test_gone_group_expires_at_the_grace_boundary,
        test_established_group_is_handled_without_the_guard,
        test_lifecycle_events_skip_the_guard,
        test_grace_zero_expires_at_once,
        test_invalid_config_falls_back_safely,
        test_conf_dist_documents_the_defaults,
    ]
    for test in tests:
        test()
    print('%d group-setup grace tests passed' % len(tests))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
