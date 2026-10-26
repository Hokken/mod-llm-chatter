#!/usr/bin/env python3
"""NPC and nearby-character genders (C++ payload part).

The C++ side is checked by source shape (it is not compiled here); the
Python consumers are checked with both the old payloads (no gender keys,
"unknown" literal) and the new ones. The NPC gossip model-gender SQL is
executed against SQLite fixtures.

Run directly from the module root:
  python tools/tests/test_npc_genders.py
"""

import json
import re
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_persona_coherence  # noqa: E402,F401  stubs + path

import chatter_db  # noqa: E402
import chatter_proximity as prox  # noqa: E402

MODULE_DIR = Path(__file__).resolve().parents[2]
SRC = MODULE_DIR / 'src'


def _src(name):
    return (SRC / name).read_text(encoding='utf-8')


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


class DB:
    def cursor(self, *args, **kwargs):
        return self

    def execute(self, *args, **kwargs):
        pass

    def fetchall(self):
        return []

    def fetchone(self):
        return None

    def close(self):
        pass


# ------------------------------------------------------------
# C++ payloads (source shape)
# ------------------------------------------------------------
def test_unit_gender_label_maps_only_female_and_male():
    shared = _src('LLMChatterShared.cpp')
    body = shared.split('std::string GetUnitGenderLabel(', 1)[1]
    body = body.split('\n}\n', 1)[0]
    assert 'case GENDER_FEMALE:' in body and 'return "female";' in body
    assert 'case GENDER_MALE:' in body and 'return "male";' in body
    assert 'default:' in body and 'return "";' in body
    assert 'if (!unit)' in body
    assert 'GetUnitGenderLabel(Unit const* unit);' in _src(
        'LLMChatterShared.h')


def test_payload_keys_use_the_shared_label():
    proximity = _src('LLMChatterProximity.cpp')
    participant = proximity.split(
        'std::string BuildNPCParticipantJson(', 1)[1].split('\n}\n', 1)[0]
    assert '= "unknown"' not in participant
    assert 'GetUnitGenderLabel(cr)' in participant
    assert ',\\"responder_gender\\":\\""' in proximity
    assert 'GetUnitGenderLabel(target->ToUnit())' in proximity
    assert ',\\"nearby_genders\\":"' in proximity
    emote = _src('LLMChatterGroupEmote.cpp')
    assert '\\"target_npc_gender\\":\\""' in emote
    assert 'std::string const& npcGender' in emote
    assert 'std::string const& npcGender = ""' in _src(
        'LLMChatterGroupInternal.h')
    assert 'GetUnitGenderLabel(cachedTargetCreature)' in _src(
        'LLMChatterGroupCombat.cpp')
    guild = _src('LLMChatterGuildWorld.cpp')
    assert '"npc_gender":"{}"' in guild and 'GetUnitGenderLabel(npc)' in guild
    boss = _src('LLMChatterBossDialogue.cpp')
    assert '\\"gender\\":\\""' in boss and 'GetUnitGenderLabel(boss)' in boss


def test_nearby_collector_feeds_both_serializers():
    proximity = _src('LLMChatterProximity.cpp')
    collector = proximity.split(
        'std::vector<NearbyEntry> CollectNearbyEntries(', 1)[1].split(
        'std::string BuildNearbyNamesJson(', 1)[0]
    # Name counts cover every visible character (speakers and the
    # excluded one too), before dedup and cap: a bystander sharing a name
    # with a speaker, or with another bystander, gets no gender.
    count_at = collector.index('++nameCounts[key]')
    assert count_at < collector.index('entries.size() >= 4')
    assert re.search(
        r'for \(auto const& c : allCandidates\)\s+countName\(c\);',
        collector)
    assert re.search(
        r'for \(auto const& s : speakers\)\s+countName\(s\);', collector)
    assert 'countName(*additionallyExcluded);' in collector
    assert 'seen.emplace(key, c.isNPC, c.id)' in collector
    assert 'if (nameCounts[key] == 1)' in collector
    base = proximity.split('std::string BuildBaseEventJson(', 1)[1]
    base = base.split('\n}\n', 1)[0]
    assert 'CollectNearbyEntries(\n        allCandidates, speakers, ' \
        'additionallyExcluded)' in base
    assert 'BuildNearbyNamesJson(nearby)' in base
    assert 'BuildNearbyGendersJson(nearby)' in base
    assert not re.search(r'BuildNearbyNamesJson\(\s*allCandidates', proximity)


# ------------------------------------------------------------
# Proximity consumers
# ------------------------------------------------------------
def test_nearby_text_old_and_new_payloads():
    names = ['Hogger', 'Ana', 'Bo']
    assert prox._nearby_gender_text({}, names) == prox._NEARBY_GENDER_RULE
    full = prox._nearby_gender_text(
        {'nearby_genders': {'Hogger': 'male', 'Ana': 'female',
                            'Bo': 'male'}}, names)
    assert 'Ana is female' in full and 'Hogger is male' in full
    assert prox._NEARBY_UNSTATED_RULE not in full
    # Ambiguous or unknown names are absent from the map (C++ omits them).
    partial = prox._nearby_gender_text(
        {'nearby_genders': {'Ana': 'female', 'Bo': 'unknown'}}, names)
    assert 'Ana is female' in partial and 'Bo is' not in partial
    assert prox._NEARBY_UNSTATED_RULE in partial
    none = prox._nearby_gender_text({'nearby_genders': {}}, names)
    assert none == prox._NEARBY_UNSTATED_RULE


def test_nearby_genders_reach_real_prompts():
    npc = {'is_npc': True, 'name': 'Guard Thomas', 'role': 'guard',
           'gender': 'unknown'}
    bot = {'name': 'Gruk', 'bot_guid': 12, 'race': 'Orc',
           'class': 'Warrior', 'gender': 'male', 'level': 40}
    extra = {'player_name': 'Calwen', 'nearby_names': ['Ana', 'Hogger'],
             'nearby_genders': {'Ana': 'female'}}
    prompts = [
        prox._conversation_prompt(DB(), extra, [dict(bot), dict(npc)]),
        prox._player_say_single_prompt(DB(), extra, dict(bot), 'hi', []),
        prox._player_say_conversation_prompt(
            DB(), extra, [dict(bot), dict(npc)], 'hi', []),
    ]
    for prompt in prompts:
        text = _text(prompt)
        assert 'Ana is female' in text
        assert prox._NEARBY_UNSTATED_RULE in text   # Hogger has none
        assert 'gender: unknown' not in text


def test_npc_unknown_literal_never_rendered():
    for gender, expected in (('unknown', None), ('', None),
                             ('female', 'gender: female')):
        desc = prox._describe_speaker(
            DB(), {'is_npc': True, 'name': 'Guard', 'gender': gender})
        if expected:
            assert expected in desc
        else:
            assert 'gender' not in desc


def test_reply_responder_carries_its_gender():
    captured = {}

    def fake_line(db, client, config, event_id, extra, responder, **kw):
        captured['responder'] = responder
        return True

    payload = {'responder_name': 'Guard Thomas', 'responder_is_npc': True,
               'responder_gender': 'female', 'player_message': 'hello',
               'responder_npc_spawn_id': 5001,
               'turn_count': 1}
    with patch.object(prox, 'find_addressed_bot',
                      return_value={'brief_casual': False}), \
            patch.object(prox, 'should_reply_to_optional_casual',
                         return_value=True), \
            patch.object(prox, '_generate_single_line',
                         side_effect=fake_line), \
            patch.object(prox, '_mark_event'):
        prox.handle_proximity_reply(
            DB(), None, {}, {'id': 1, 'extra_data': json.dumps(payload)})
        assert captured['responder']['gender'] == 'female'
        old = dict(payload)
        old.pop('responder_gender')
        prox.handle_proximity_reply(
            DB(), None, {}, {'id': 2, 'extra_data': json.dumps(old)})
        assert 'gender' not in captured['responder']


# ------------------------------------------------------------
# Emote creature, guild NPC, boss, General NPC gossip
# ------------------------------------------------------------
def test_emote_creature_gender():
    from chatter_emote_observer import _build_creature_prompt
    args = ('Gruk', 'Orc', 'Warrior', 'male', 'Calwen', 'wave',
            'Innkeeper Gryshka', 'greeting', 0, 7)
    text = _text(_build_creature_prompt(*args, npc_gender='female'))
    assert 'Innkeeper Gryshka is female' in text
    assert 'Gryshka is' not in _text(_build_creature_prompt(*args))


def test_guild_npc_encounter_gender():
    from chatter_guild_world_events import _npc_scenario
    extra = {'bot_name': 'Aliss', 'npc_name': 'Tognus', 'npc_role': 'smith'}
    assert any('Tognus is male' in line for line in _npc_scenario(
        dict(extra, npc_gender='male'), 'roleplay'))
    assert not any('Genders' in line for line in _npc_scenario(
        extra, 'roleplay'))


def test_boss_speaker_gender():
    import chatter_boss_dialogue as boss
    extra = {'boss': {'name': 'Lady Anacondra', 'role': 'boss',
                      'gender': 'female'}, 'player_name': 'Calwen'}
    assert 'You are Lady Anacondra, boss. You are female.' in _text(
        boss._build_prompt(extra))
    extra['boss']['gender'] = ''
    assert 'You are female' not in _text(boss._build_prompt(extra))


def _model_genders(models, infos):
    db = sqlite3.connect(':memory:')
    db.executescript("""
        CREATE TABLE creature_template (entry INTEGER);
        CREATE TABLE creature_template_model (
            CreatureID INTEGER, Idx INTEGER, CreatureDisplayID INTEGER);
        CREATE TABLE creature_model_info (
            DisplayID INTEGER, Gender INTEGER,
            DisplayID_Other_Gender INTEGER);
    """)
    entries = sorted({m[0] for m in models} | {99})
    db.executemany("INSERT INTO creature_template VALUES (?)",
                   [(e,) for e in entries])
    db.executemany("INSERT INTO creature_template_model VALUES (?, ?, ?)",
                   models)
    db.executemany("INSERT INTO creature_model_info VALUES (?, ?, ?)",
                   infos)
    rows = db.execute(
        f"SELECT ct.entry, {chatter_db.NPC_MODEL_GENDER_SQL} "
        "FROM creature_template ct").fetchall()
    return dict(rows)


def test_npc_model_gender_sql_is_conservative():
    models = [
        (1, 0, 101),                 # one male model
        (2, 0, 201), (2, 1, 202),    # two female models
        (3, 0, 301),                 # male with a female alternate
        (4, 0, 401), (4, 1, 402),    # mixed male/female
        (5, 0, 501), (5, 1, 502),    # one model without metadata
        (6, 0, 601),                 # GENDER_NONE model
    ]
    infos = [
        (101, 0, 0), (201, 1, 0), (202, 1, 0), (301, 0, 302),
        (302, 1, 0), (401, 0, 0), (402, 1, 0), (501, 1, 0), (601, 2, 0),
    ]
    got = _model_genders(models, infos)
    assert got[1] == 0 and got[2] == 1
    for entry in (3, 4, 5, 6, 99):   # 99 has no model at all
        assert got[entry] is None, (entry, got[entry])


def test_gossip_npc_target_gender():
    from chatter_member_gender import gender_from_id
    from chatter_prompts import _format_gossip_target
    for raw, expected in ((1, 'gender=female'), (0, 'gender=male'),
                          (None, None), (2, None)):
        target = {'name': 'Innkeeper Gryshka', 'function': 'innkeeper',
                  'gender': gender_from_id(raw)}
        text = _format_gossip_target(target, 'npc')
        if expected:
            assert expected in text
        else:
            assert 'gender' not in text
    source = Path(chatter_db.__file__).read_text(encoding='utf-8')
    assert '{NPC_MODEL_GENDER_SQL} AS model_gender' in source
    assert "'gender': gender_from_id(row.get('model_gender'))" in source


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} NPC gender checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
