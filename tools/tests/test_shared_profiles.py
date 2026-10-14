"""Shared profile persistence, races, sampling and Guild discovery regressions.

Uses SQLite to execute persistence predicates with a small MySQL syntax adapter;
no live database or provider calls. Run: python tools/tests/test_shared_profiles.py
"""

import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import test_persona_coherence  # dependency stubs and tools path
import chatter_identity as identity
import chatter_identity_jobs as jobs
from chatter_persona import Persona, build_cast_lines, sample_channel_backstory


class Cursor:
    def __init__(self, db, dictionary=False):
        self.db = db
        self.inner = db.connection.cursor()
        self.dictionary = dictionary

    def execute(self, sql, args=()):
        sql = sql.replace('%s', '?').replace('<=>', 'IS')
        sql = sql.replace('INSERT IGNORE', 'INSERT OR IGNORE')
        sql = sql.replace(' FOR UPDATE', '')
        self.inner.execute(sql, args)
        return self

    @property
    def rowcount(self):
        return self.inner.rowcount

    def fetchone(self):
        row = self.inner.fetchone()
        return dict(row) if row is not None and self.dictionary else row

    def fetchall(self):
        rows = self.inner.fetchall()
        return [dict(r) for r in rows] if self.dictionary else rows

    def close(self):
        self.inner.close()


class DB:
    def __init__(self, path=':memory:'):
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def cursor(self, dictionary=False):
        return Cursor(self, dictionary)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()


SCHEMA = """
CREATE TABLE llm_bot_identities (
 bot_guid INTEGER PRIMARY KEY, bot_name TEXT, trait1 TEXT, trait2 TEXT,
 trait3 TEXT, tone TEXT, backstory TEXT, identity_version INTEGER,
 role TEXT, farewell_msg TEXT, created_at TEXT);
CREATE TABLE llm_group_bot_traits (
 group_id INTEGER, bot_guid INTEGER, trait1 TEXT, trait2 TEXT, trait3 TEXT,
 tone TEXT, backstory TEXT, assigned_at INTEGER);
CREATE TABLE characters (
 guid INTEGER PRIMARY KEY, name TEXT, class INTEGER, race INTEGER,
 gender INTEGER, account INTEGER, online INTEGER);
CREATE TABLE guild_member (guid INTEGER, guildid INTEGER);
CREATE TABLE llm_guild_chat_sessions (player_guid INTEGER, guild_id INTEGER);
INSERT INTO characters VALUES (101, 'Gruk', 1, 2, 0, 1, 1);
"""


class Profiles(unittest.TestCase):
    def setUp(self):
        self.db = DB()
        self.db.connection.executescript(SCHEMA)
        self.config = {'LLMChatter.ChatterMode': 'roleplay'}
        identity._failures.clear()
        jobs._last_guid = 0
        self.client_patch = patch.object(identity, 'get_llm_client', return_value=None)
        self.client_patch.start()
        self.llm_patch = patch.object(identity, 'call_llm', side_effect=self.generate)
        self.llm = self.llm_patch.start()

    def tearDown(self):
        self.client_patch.stop()
        self.llm_patch.stop()
        self.db.connection.close()

    @staticmethod
    def generate(client, prompt, config, **kwargs):
        return 'warm and direct' if kwargs['label'] == 'bot_tone' else 'Raised in Durotar.'

    def save(self, **changes):
        data = dict(bot_guid=101, bot_name='Gruk', trait1='loyal',
                    trait2='curious', trait3='patient', tone='dry and warm',
                    backstory='A former scout.', identity_version=1)
        data.update(changes)
        self.db.connection.execute(
            'INSERT OR REPLACE INTO llm_bot_identities ('
            + ','.join(data) + ') VALUES (' + ','.join('?' for _ in data) + ')',
            tuple(data.values()),
        )
        self.db.commit()

    def ensure(self):
        return identity.ensure_bot_profile(self.db, None, self.config, 101, 'Gruk')

    def test_new_profile_persisted_and_reused_without_journals(self):
        self.config['LLMChatter.Memory.Enable'] = 0
        first = self.ensure()
        self.assertEqual(self.llm.call_count, 2)
        self.assertEqual(first.tone, 'warm and direct')
        self.assertEqual(first.backstory, 'Raised in Durotar.')
        self.assertEqual(self.ensure(), first)
        self.assertEqual(self.llm.call_count, 2)

    def test_partial_traits_and_missing_tone_preserve_manual_fields(self):
        self.save(trait2='  ', tone=None)
        p = self.ensure()
        self.assertEqual(p.traits[0], 'loyal')
        self.assertEqual(p.traits[2], 'patient')
        self.assertTrue(p.traits[1].strip())
        self.assertEqual(p.backstory, 'A former scout.')
        self.assertEqual(self.llm.call_count, 1)

    def test_complete_profile_never_calls_provider(self):
        self.save()
        self.assertEqual(self.ensure().tone, 'dry and warm')
        self.llm.assert_not_called()

    def test_complete_profile_never_acquires_generation_lock(self):
        self.save()

        class ForbiddenLock:
            def __enter__(self):
                raise AssertionError('complete profile acquired stripe')

            def __exit__(self, *args):
                pass

        with patch.object(identity, '_locks', (ForbiddenLock(),)):
            self.assertEqual(self.ensure().tone, 'dry and warm')
        self.llm.assert_not_called()

    def test_write_failure_is_throttled_without_provider_calls(self):
        original = Cursor.execute
        attempts = []

        def fail_write(cursor, sql, args=()):
            if 'INSERT IGNORE INTO llm_bot_identities' in sql:
                attempts.append(sql)
                raise RuntimeError('database unavailable')
            return original(cursor, sql, args)

        with patch.object(Cursor, 'execute', fail_write):
            with self.assertLogs(identity.logger, level='WARNING'):
                self.ensure()
            self.ensure()
        self.assertEqual(len(attempts), 1)
        self.llm.assert_not_called()

    def test_backstory_generated_before_failed_inclusion_roll(self):
        with patch('chatter_persona.random.randint', return_value=99):
            p = identity.prepare_channel_persona(
                self.db, None, self.config, 101, 'Gruk', 'general',
            )
        self.assertFalse(p.backstory)
        self.assertEqual(self.llm.call_count, 2)
        self.assertEqual(identity._read_identity(self.db, 101)['backstory'],
                         'Raised in Durotar.')

    def test_read_failure_never_replaces_existing_profile(self):
        self.save()
        with patch.object(identity, '_read_identity', side_effect=RuntimeError):
            with self.assertLogs(identity.logger, level='WARNING'):
                self.ensure()
        self.assertEqual(identity._read_identity(self.db, 101)['tone'],
                         'dry and warm')
        self.llm.assert_not_called()

    def test_normal_and_disabled_backstory(self):
        self.config['LLMChatter.ChatterMode'] = 'normal'
        self.assertFalse(self.ensure().backstory)
        self.llm.assert_not_called()
        self.config['LLMChatter.ChatterMode'] = 'roleplay'
        self.config['LLMChatter.Backstory.Enable'] = 0
        self.assertFalse(self.ensure().backstory)
        self.assertEqual(self.llm.call_count, 1)

    def test_failed_generation_retries_after_ttl(self):
        self.save(tone=None, backstory=None)
        self.llm.side_effect = None
        self.llm.return_value = None
        with patch.object(identity.time, 'monotonic', return_value=100):
            self.ensure()
            self.ensure()
        self.assertEqual(self.llm.call_count, 2)
        self.llm.side_effect = self.generate
        with patch.object(identity.time, 'monotonic', return_value=401):
            self.assertTrue(self.ensure().backstory)
        self.assertEqual(self.llm.call_count, 4)

    def test_manual_edit_during_generation_wins(self):
        self.save(tone=None)

        def edit(*args, **kwargs):
            self.save(trait1='stern', tone='manually edited')
            return 'obsolete generated tone'

        self.llm.side_effect = edit
        p = self.ensure()
        self.assertEqual(p.tone, 'manually edited')
        self.assertEqual(p.traits[0], 'stern')

    def test_version_bump_updates_matching_group(self):
        self.save()
        self.db.connection.execute(
            'INSERT INTO llm_group_bot_traits VALUES (1,101,?,?,?,?,?,1)',
            ('loyal', 'curious', 'patient', 'dry and warm', 'A former scout.'),
        )
        self.db.commit()
        self.config['LLMChatter.Memory.IdentityVersion'] = 2
        p = self.ensure()
        self.assertEqual(p.backstory, 'Raised in Durotar.')
        self.assertEqual(self.llm.call_count, 2)
        self.assertEqual(identity._read_identity(self.db, 101)['identity_version'], 2)

    def test_active_group_missing_fields_are_filled(self):
        self.save()
        self.db.connection.execute(
            'INSERT INTO llm_group_bot_traits VALUES (1,101,?,?,?,NULL,NULL,1)',
            ('loyal', 'curious', 'patient'),
        )
        self.db.commit()
        self.assertEqual(self.ensure().backstory, 'A former scout.')
        self.llm.assert_not_called()

    def test_session_traits_do_not_overwrite_persistent_traits(self):
        self.save(tone=None, backstory=None)
        self.db.connection.execute(
            'INSERT INTO llm_group_bot_traits VALUES (1,101,?,?,?,NULL,NULL,1)',
            ('loud', 'reckless', 'proud'),
        )
        self.db.commit()
        self.assertEqual(self.ensure().traits, ('loud', 'reckless', 'proud'))
        saved = identity._read_identity(self.db, 101)
        self.assertEqual(saved['trait1'], 'loyal')
        self.assertIsNone(saved['tone'])
        self.assertEqual(self.llm.call_count, 2)

    def test_concurrent_first_use_generates_once(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'db.sqlite')
            first, second = DB(path), DB(path)
            first.connection.executescript(SCHEMA)
            errors = []

            def work(db):
                try:
                    identity.ensure_bot_profile(db, None, self.config, 101, 'Gruk')
                except Exception as exc:
                    errors.append(exc)

            threads = [threading.Thread(target=work, args=(db,))
                       for db in (first, second)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(5)
                self.assertFalse(thread.is_alive())
            first.connection.close()
            second.connection.close()
            self.assertFalse(errors)
            self.assertEqual(self.llm.call_count, 2)

    def test_mixed_cast_and_exchange_cache_leave_identity_intact(self):
        self.save()
        p = self.ensure()
        cache = {}
        with patch.object(identity, 'ensure_bot_profile', return_value=p) as ensure:
            with patch('chatter_persona.random.randint', side_effect=[10, 80, 20]):
                cast = [identity.prepare_channel_persona(
                    self.db, None, self.config, guid, str(guid), 'general', cache,
                ) for guid in (101, 102, 103)]
                again = identity.prepare_channel_persona(
                    self.db, None, self.config, 102, '102', 'general', cache,
                )
            self.assertEqual(ensure.call_count, 3)
        self.assertEqual([bool(p.backstory) for p in cast], [True, False, True])
        self.assertFalse(again.backstory)
        text = '\n'.join(build_cast_lines(cast, 'roleplay'))
        self.assertEqual(text.count('A former scout.'), 2)
        self.assertEqual(text.count('dry and warm'), 3)
        self.assertEqual(identity._read_identity(self.db, 101)['backstory'], p.backstory)

    def test_sampling_limits_and_bad_config(self):
        p = Persona('Gruk', ('loyal',), 'warm', 'old story')
        for chance, expected in ((0, False), (100, True), (-5, False), (101, True)):
            config = dict(self.config, **{'LLMChatter.Backstory.GuildChance': chance})
            self.assertEqual(bool(sample_channel_backstory(config, p, 'guild').backstory), expected)
        with patch('chatter_persona.random.randint', return_value=26):
            config = dict(self.config, **{'LLMChatter.Backstory.GuildChance': 'bad'})
            self.assertFalse(sample_channel_backstory(config, p, 'guild').backstory)

    def test_guild_discovery_real_session_batch_and_fairness(self):
        self.db.connection.executescript("""
        ATTACH DATABASE ':memory:' AS acore_auth;
        CREATE TABLE acore_auth.account (id INTEGER, username TEXT);
        INSERT INTO acore_auth.account VALUES (1, 'RNDBOT1'), (2, 'PLAYER');
        INSERT INTO characters VALUES (102, 'Other', 1, 2, 0, 1, 1);
        INSERT INTO characters VALUES (103, 'Hidden', 1, 2, 0, 1, 1);
        INSERT INTO characters VALUES (500, 'Player', 1, 2, 0, 2, 1);
        INSERT INTO guild_member VALUES (101,1), (102,1), (103,2), (500,1);
        """)
        self.assertEqual(jobs.prepare_guild_profiles(self.db, None, self.config), 0)
        self.db.connection.execute('INSERT INTO llm_guild_chat_sessions VALUES (500,1)')
        self.db.commit()
        self.config['LLMChatter.Profile.GuildBatchSize'] = 1
        with patch.object(jobs, 'ensure_bot_profile') as ensure:
            jobs.prepare_guild_profiles(self.db, None, self.config)
            self.assertEqual(ensure.call_args.args[3], 101)
            jobs.prepare_guild_profiles(self.db, None, self.config)
            self.assertEqual(ensure.call_args.args[3], 102)
            self.assertEqual(jobs.prepare_guild_profiles(self.db, None, self.config), 0)

            self.assertEqual(ensure.call_count, 2)
            self.db.connection.execute('UPDATE characters SET online=0 WHERE guid=500')
            self.db.commit()
            self.assertEqual(jobs.prepare_guild_profiles(self.db, None, self.config), 0)

    def test_disabled_guild_sweep_never_touches_database(self):
        for config in (
            {'LLMChatter.ChatterMode': 'normal'},
            dict(self.config, **{'LLMChatter.GuildChatter.Enable': 0}),
            dict(self.config, **{'LLMChatter.Enable': 0}),
        ):
            self.assertEqual(jobs.prepare_guild_profiles(None, None, config), 0)


if __name__ == '__main__':
    unittest.main()
