"""Offline source contracts for the voice mailbox; not runtime proof."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'src'
SQL = ROOT / 'data' / 'sql' / 'characters'


def read(path):
    return path.read_text(encoding='utf-8')


def function_body(source, signature):
    start = source.index(signature)
    open_brace = source.index('{', start)
    depth = 0
    for index in range(open_brace, len(source)):
        if source[index] == '{':
            depth += 1
        elif source[index] == '}':
            depth -= 1
            if depth == 0:
                return source[open_brace:index + 1]
    raise AssertionError(f'unbalanced body for {signature}')


class SingleOwnerTests(unittest.TestCase):
    def test_transport_helper_never_records(self):
        body = function_body(read(SRC / 'LLMChatterShared.cpp'),
                             'void SendPartyMessageInstant(')
        self.assertNotIn('RecordVoiceLine', body)

    def test_each_combat_send_records_once(self):
        source = read(SRC / 'LLMChatterGroupCombat.cpp')
        sends = source.count('SendPartyMessageInstant(')
        records = re.findall(
            r'SendPartyMessageInstant\([^;]*;\s*RecordVoiceLine\(', source)
        self.assertEqual(sends, 3)
        self.assertEqual(len(records), sends)

    def test_delivery_records_once_after_send(self):
        source = read(SRC / 'LLMChatterDelivery.cpp')
        self.assertEqual(source.count('RecordVoiceLine('), 1)
        final = source[source.index('    if (sent)\n    {'):]
        self.assertIn('RecordVoiceLine(voiceSpeaker', final.split(
            'else if (botUnavailable)')[0])

    def test_bot_say_yell_voice_only_broadcast_text(self):
        source = read(SRC / 'LLMChatterDelivery.cpp')
        for call, channel in (('ai->Say(', 'VOICE_CHANNEL_SAY'),
                              ('ai->Yell(', 'VOICE_CHANNEL_YELL')):
            send = source.index(call)
            arm = source.rindex('ArmVoiceChatCapture(', 0, send)
            take = source.index('TakeVoiceChatCapture(voiceText)', send)
            self.assertIn(channel, source[arm:send])
            self.assertLess(take - send, 400)

    def test_voice_copies_are_gated(self):
        source = read(SRC / 'LLMChatterDelivery.cpp')
        for assignment in ('voiceText = processedMessage;',
                           'voiceText = msayMessage;'):
            index = source.index(assignment)
            self.assertIn('IsVoiceChannelWanted(',
                          source[index - 300:index])

    def test_capture_hook_requires_running_last(self):
        source = read(SRC / 'LLMChatterVoice.cpp')
        self.assertIn('hooks.back() == _captureScript', source)
        self.assertIn('CaptureIsLast()', function_body(
            source, 'bool ArmVoiceChatCapture('))

    def test_capture_moves_itself_last_at_startup(self):
        source = read(SRC / 'LLMChatterVoice.cpp')
        move = function_body(source, 'void MoveCaptureLast(')
        self.assertIn('hooks.push_back(_captureScript)', move)
        self.assertIn('_captureIsLast = -1', move)
        self.assertIn('WORLDHOOK_ON_STARTUP', source)
        self.assertIn('MoveCaptureLast();', function_body(
            source, 'void OnStartup('))

    def test_remote_viewer_skipped_for_bot_speech(self):
        body = function_body(read(SRC / 'LLMChatterVoice.cpp'),
                             'bool ReceivedBy(')
        self.assertIn('GetSeer() != listener', body)

    def test_only_voice_file_and_owners_record(self):
        owners = {'LLMChatterVoice.cpp', 'LLMChatterDelivery.cpp',
                  'LLMChatterGroupCombat.cpp'}
        for path in SRC.glob('*.cpp'):
            if path.name not in owners:
                self.assertNotIn('RecordVoiceLine(', read(path), path.name)


class SchemaTests(unittest.TestCase):
    UPGRADE_MARKER = '-- Upgrade a mailbox created before playback leases'

    def test_base_mirrors_update(self):
        update = read(SQL / 'updates' / '20261029_voice_mailbox.sql')
        base = read(SQL / 'base' / '00000000_llm_chatter_tables.sql')
        # Fresh installs get the final tables; only the update carries
        # the in-place upgrade for DBs that applied an earlier version.
        tables, upgrade = update.split(self.UPGRADE_MARKER)
        self.assertIn(tables.strip(), base)
        self.assertNotIn(self.UPGRADE_MARKER, base)
        self.assertIn("'playing'", upgrade)
        self.assertIn("COLUMN_NAME  = 'play_until'", upgrade)

    def test_poll_index_and_lifecycle_columns(self):
        update = read(SQL / 'updates' / '20261029_voice_mailbox.sql')
        self.assertIn('KEY `idx_poll` (`account_id`, `state`, `id`)',
                      update)
        for column in ('`generation`', '`expires_at`', '`state`',
                       '`play_until`'):
            self.assertIn(column, update)
        self.assertIn("'claimed', 'playing', 'played'", update)

    def test_live_table_keyed_per_speaker(self):
        update = read(SQL / 'updates' / '20261029_voice_mailbox.sql')
        self.assertIn('CREATE TABLE IF NOT EXISTS `llm_chatter_voice_live`',
                      update)
        self.assertIn('PRIMARY KEY (`account_id`, `speaker_kind`, '
                      '`speaker_guid`)', update)

    def test_turn_away_notes_and_terminal_rows(self):
        voice = read(SRC / 'LLMChatterVoice.cpp')
        delivery = read(SRC / 'LLMChatterDelivery.cpp')
        # Noted only after a queued row, a faced bot and a message id.
        self.assertIn('&& RecordVoiceLine(voiceSpeaker, voiceChannel,',
                      delivery)
        self.assertIn('&& botFacedForLine)', delivery)
        self.assertIn('NoteVoiceFacing(voiceSpeaker->ToPlayer(), messageId,',
                      delivery)
        note = function_body(voice, 'void NoteVoiceFacing(')
        for guard in ('!messageId', '!IsPlayerBot(bot)',
                      '_voiceTurnAwayEnable'):
            self.assertIn(guard, note)
        # The same lease read returns noted terminal rows only.
        issue = function_body(voice, 'void IssueLeaseQuery(')
        self.assertIn("message_id IN (", issue)
        self.assertIn("state IN ('played', 'expired')", issue)
        self.assertIn('message_id, state', issue)
        # Notes are pruned before any delayed terminal row is consumed,
        # and terminal rows must match the current listener.
        apply = function_body(voice, 'void ApplyLeaseSnapshot(')
        self.assertLess(apply.index('PruneTurnNotes('),
                        apply.index('OnTerminal('))
        self.assertIn('!= listenerGuid', apply)
        turn = function_body(voice, 'void TryTurnAway(')
        for guard in ('IsSafeForChatterFacing(bot)', 'StillFacing(',
                      'IsInCombat()', 'IsNonMeleeSpellCast(false)',
                      'roll_chance_i('):
            self.assertIn(guard, turn)
        live = function_body(voice, 'bool LiveWanted(')
        self.assertIn('_voiceTurnAwayEnable', live)

    def test_party_facing_is_chance_gated(self):
        delivery = read(SRC / 'LLMChatterDelivery.cpp')
        # Every bot facing goes through the one gate, rolled once per line.
        self.assertEqual(delivery.count('bot->SetFacingToObject('), 1)
        self.assertEqual(delivery.count('_facingPartyChance'), 1)
        self.assertIn('!IsPlayerBot(person)', delivery)
        self.assertIn('person->IsInSameGroupWith(bot)', delivery)
        self.assertIn('botFacedForLine = turned;', delivery)
        for path in TEMPLATES:
            self.assertRegex(read(path), r'(?m)^LLMChatter\.GroupChatter'
                             r'\.FacingPartyChance = 50$')
        config = read(SRC / 'LLMChatterConfig.cpp')
        self.assertIn('"FacingPartyChance", 50)', config)

    def test_stopped_follower_bot_may_turn(self):
        shared = read(SRC / 'LLMChatterShared.cpp')
        types = function_body(shared, 'bool IsSafeChatterFacingMotionType(')
        self.assertIn('case FOLLOW_MOTION_TYPE:', types)
        self.assertIn('return followerOk;', types)
        gate = function_body(shared, 'bool HasUnsafeChatterFacingMotion(')
        for guard in ('unit->IsPlayer()',
                      '!unit->HasUnitState(UNIT_STATE_FOLLOW_MOVE)',
                      '!unit->isMoving()'):
            self.assertIn(guard, gate)
        # NPCs still turn only when they never move.
        self.assertIn('creature->GetDefaultMovementType() != IDLE_MOTION_TYPE',
                      gate)

    def test_gender_survives_shapeshift(self):
        shared = read(SRC / 'LLMChatterShared.cpp')
        helper = function_body(shared, 'uint8 GetTrueGender(')
        self.assertIn('PLAYER_BYTES_3_OFFSET_GENDER', helper)
        self.assertIn('unit->ToPlayer()', helper)
        # The model gender byte is read only inside the helper (NPCs).
        for path in SRC.glob('*.cpp'):
            source = read(path)
            if path.name == 'LLMChatterShared.cpp':
                source = source.replace(helper, '')
            self.assertNotIn('getGender()', source, path.name)

    def test_voiced_facing_waits_for_audio(self):
        delivery = read(SRC / 'LLMChatterDelivery.cpp')
        voice = read(SRC / 'LLMChatterVoice.cpp')
        # Exactly one rotation path per decided target.
        self.assertIn('if (deferToVoice)', delivery)
        self.assertIn('deferredFaceTarget = target->GetGUID();', delivery)
        self.assertIn('NotePendingFacing(bot, messageId, deferredFaceTarget)',
                      delivery)
        self.assertIn('FaceTargetIfSafe(bot, deferredFaceTarget)', delivery)
        self.assertIn('if (recorded && voiceSpeaker == bot)', delivery)
        # Applied once when its line plays; dropped otherwise.
        apply = function_body(voice, 'void ApplyLeaseSnapshot(')
        self.assertLess(apply.index('PrunePendingFacings('),
                        apply.index('_pendingFacings.Take('))
        self.assertIn('if (state == "playing" && leftUs > 0', apply)
        face = function_body(voice, 'void ApplyPendingFacing(')
        for guard in ('InSamePhase(bot)', 'FaceTargetIfSafe(',
                      'NoteVoiceFacing(bot, pending.messageId, facing)'):
            self.assertIn(guard, face)
        # A late callback never turns after the clip ended.
        self.assertIn('issuedMs + uint64(leftUs / 1000) > nowMs', apply)
        # Notes record the requested angle, not the stale orientation
        # (SetFacingToObject only launches a spline).
        note = function_body(voice, 'void NoteVoiceFacing(')
        self.assertNotIn('GetOrientation()', note)
        self.assertIn('botFacedOrientation = bot->GetAngle(target);',
                      delivery)
        self.assertIn('botFacedOrientation);', delivery)
        self.assertIn('_voiceFaceAtVoiceEnable',
                      function_body(voice, 'bool LiveWanted('))
        issue = function_body(voice, 'void IssueLeaseQuery(')
        self.assertIn('_pendingFacings.Ids()', issue)
        shared = read(SRC / 'LLMChatterShared.cpp')
        safe = function_body(shared, 'bool FaceTargetIfSafe(')
        for guard in ('IsSafeForChatterFacing(bot)', 'InSamePhase(object)',
                      'GetInstanceId()'):
            self.assertIn(guard, safe)
        self.assertLess(safe.index('*facing = bot->GetAngle(object);'),
                        safe.index('bot->SetFacingToObject(object);'))

    def test_live_rows_carry_speaker_position(self):
        for path in (SQL / 'updates' / '20261029_voice_mailbox.sql',
                     SQL / 'base' / '00000000_llm_chatter_tables.sql'):
            source = read(path)
            self.assertIn('`speaker_x` FLOAT NOT NULL DEFAULT 0', source)
            self.assertIn('`speaker_y` FLOAT NOT NULL DEFAULT 0', source)
        update = read(SQL / 'updates' / '20261029_voice_mailbox.sql')
        self.assertIn("COLUMN_NAME  = 'speaker_x'", update)
        voice = read(SRC / 'LLMChatterVoice.cpp')
        publish = function_body(voice, 'void PublishGeometry(')
        self.assertIn('speaker_x, speaker_y', publish)
        self.assertIn('moved <= c->_voiceLiveMinDistanceChange', publish)

    def test_message_index_in_update_and_base(self):
        for path in (SQL / 'updates' / '20261029_voice_mailbox.sql',
                     SQL / 'base' / '00000000_llm_chatter_tables.sql'):
            self.assertIn('KEY `idx_message` (`message_id`)', read(path))

    def test_lease_query_matches_poll_index(self):
        voice = read(SRC / 'LLMChatterVoice.cpp')
        self.assertIn("WHERE account_id = {} AND ((state = 'playing' ", voice)
        self.assertIn('ORDER BY id DESC LIMIT {}', voice)
        # Never a synchronous read on the world thread.
        self.assertNotIn('CharacterDatabase.Query(', voice)


TEMPLATES = (ROOT / 'conf' / 'mod_llm_chatter.conf.dist',
             ROOT / 'conf' / 'presets' / 'mod_ll_chatter_quieter.conf.dist')
VOICE_KEY = re.compile(r'LLMChatter\.Voice\.[A-Za-z.]*[A-Za-z]')


def template_values(path):
    values = {}
    for line in read(path).splitlines():
        line = line.strip()
        if line.startswith('LLMChatter.Voice.') and '=' in line:
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip()
    return values


class TemplateParityTests(unittest.TestCase):
    def loader_keys(self):
        keys = set(VOICE_KEY.findall(read(SRC / 'LLMChatterConfig.cpp')))
        keys |= set(VOICE_KEY.findall(read(ROOT / 'tools' / 'tts_agent.py')))
        return keys

    def test_every_loaded_key_in_both_templates(self):
        for path in TEMPLATES:
            missing = self.loader_keys() - set(template_values(path))
            self.assertEqual(missing, set(), path.name)

    def test_templates_list_same_voice_settings(self):
        first, second = (template_values(path) for path in TEMPLATES)
        self.assertEqual(first, second)

    def test_server_defaults_match_templates(self):
        source = read(SRC / 'LLMChatterConfig.cpp')
        pattern = re.compile(
            r'GetChatterOption<([\w:]+)>\(\s*"(LLMChatter\.Voice\.[\w.]+)",'
            r'\s*([^)]+?)\)')
        found = pattern.findall(source)
        self.assertEqual(len(found), 23)

        def normalize(kind, value):
            value = value.strip().strip('"')
            if kind == 'bool':
                return value in ('1', 'true')
            if kind == 'std::string':
                return value
            return float(value.rstrip('f'))

        for path in TEMPLATES:
            values = template_values(path)
            for kind, key, default in found:
                self.assertEqual(normalize(kind, values[key]),
                                 normalize(kind, default),
                                 (path.name, key))

    def test_agent_defaults_match_templates(self):
        sys.path.insert(0, str(ROOT / 'tools'))
        from tts_agent import load_voice_config
        defaults = load_voice_config({})
        for path in TEMPLATES:
            from_template = load_voice_config(template_values(path))
            self.assertEqual(from_template, defaults, path.name)

    def test_readme_names_migration_and_setup(self):
        readme = read(ROOT / 'README.md')
        self.assertIn('20261029_voice_mailbox.sql', readme)
        self.assertIn('--list-voices', readme)
        self.assertIn('requirements-voice.txt', readme)


class ConfigTests(unittest.TestCase):
    def test_voice_defaults_off(self):
        conf = read(ROOT / 'conf' / 'mod_llm_chatter.conf.dist')
        self.assertRegex(conf, r'(?m)^LLMChatter\.Voice\.Enable = 0$')
        self.assertRegex(conf,
                         r'(?m)^LLMChatter\.Voice\.BoundAccountId = 0$')
        self.assertRegex(
            conf, r'(?m)^LLMChatter\.Voice\.Channels = say,yell,msay,party$')


if __name__ == '__main__':
    unittest.main()
