#!/usr/bin/env python3
"""Genders in proximity, emote, duel, PvP, memory, boss and precache
prompts.

Covers the silent emote target, the nearby-names pronoun rule, fight
scenes in every moment (with neutral wording for NPC onlookers), the
neutral player description in NPC casts, the party bot emote exchange,
visible duellists, the open-world PvP enemy, memory prompts and their
event contexts, the boss line, batched Arathi Basin actors and the
precache spell-support rule.

Run directly from the module root:
  python tools/tests/test_proximity_genders.py
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_persona_coherence  # noqa: E402,F401  stubs + path

import chatter_member_gender as gender  # noqa: E402
import chatter_proximity as prox  # noqa: E402

NAMES = {'Ana': 1, 'Bo': 0, 'Jaina': 1, 'Varian': 0, 'Calwen': 1}
GUIDS = {11: 1, 12: 0, 20: 1, 99: 0, 7: 1}


class Cursor:
    def __init__(self, db):
        self.db = db
        self.rows = []

    def execute(self, query, params=None):
        params = tuple(params or ())
        self.db.queries.append(query)
        if 'FROM characters' in query and 'WHERE name IN' in query:
            self.rows = [{'name': n, 'gender': NAMES[n]}
                         for n in params if n in NAMES]
        elif 'FROM characters' in query and 'WHERE guid IN' in query:
            self.rows = [{'guid': g, 'gender': GUIDS[g]}
                         for g in params if g in GUIDS]
        elif 'FROM characters' in query and 'guid = %s' in query:
            guid = params[0] if params else 0
            self.rows = [{'name': 'Calwen', 'race': 1, 'class': 8,
                          'gender': GUIDS.get(guid, 0), 'level': 40}] \
                if guid in GUIDS else []
        else:
            self.rows = []

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class DB:
    def __init__(self):
        self.queries = []

    def cursor(self, *args, **kwargs):
        return Cursor(self)

    def commit(self):
        pass


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


# ------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------
def test_gender_from_id_accepts_only_valid_ids():
    assert gender.gender_from_id(1) == 'female'
    assert gender.gender_from_id('0') == 'male'
    for value in (None, '', 2, -1, 'x', True, 1.5):
        assert gender.gender_from_id(value) == '', value


# ------------------------------------------------------------
# Proximity
# ------------------------------------------------------------
NPC = {'is_npc': True, 'name': 'Guard Thomas', 'role': 'guard',
       'gender': 'male', 'disposition': 'friendly'}
BOT = {'name': 'Gruk', 'bot_guid': 12, 'race': 'Orc', 'class': 'Warrior',
       'gender': 'male', 'level': 40}


def _emote_extra(addressed):
    return {
        'player_name': 'Calwen', 'player_guid': 7,
        'addressed_name': addressed['name'],
        'addressed_participant': addressed,
        'addressed_speaks': False, 'emote': 'wave',
        'emote_category': 'greeting',
    }


def test_silent_emote_target_gets_a_gender():
    for addressed, expected in (
        ({'name': 'Ana', 'bot_guid': 11}, 'Ana is female'),
        ({'name': 'Lady Sylvanas', 'is_npc': True, 'gender': 'female'},
         'Lady Sylvanas is female'),
    ):
        extra = _emote_extra(addressed)
        single = _text(prox._player_emote_single_prompt(
            DB(), extra, dict(BOT), 'wave'))
        conv = _text(prox._player_emote_conversation_prompt(
            DB(), extra, [dict(BOT), dict(BOT, name='Bo', bot_guid=99)],
            'wave'))
        assert expected in single, single
        assert expected in conv
    unknown = _emote_extra({'name': 'Grub', 'is_npc': True,
                            'gender': 'unknown'})
    text = _text(prox._player_emote_single_prompt(
        DB(), unknown, dict(BOT), 'wave'))
    assert 'Grub is' not in text


def test_nearby_names_rule_in_every_listing():
    extra = {'player_name': 'Calwen', 'player_guid': 7,
             'nearby_names': ['Hogger', 'Ana'], 'player_addressed': True}
    prompts = [
        prox._conversation_prompt(DB(), extra, [dict(BOT), dict(NPC)]),
        prox._player_say_single_prompt(DB(), extra, dict(BOT), 'hi', []),
        prox._player_say_conversation_prompt(
            DB(), extra, [dict(BOT), dict(NPC)], 'hi', []),
    ]
    for prompt in prompts:
        assert prox._NEARBY_GENDER_RULE in _text(prompt)


def _fight(kind, moment, **scene):
    data = {'kind': kind, 'moment': moment, 'fighters': [
        {'name': 'Varian', 'race': 1, 'class': 1, 'level': 40,
         'is_player': False},
        {'name': 'Jaina', 'race': 1, 'class': 8, 'level': 40,
         'is_player': True},
    ]}
    data.update(scene)
    return {'fight_scene': data}


def test_fight_genders_in_every_moment():
    scenes = [
        _fight('duel', 'before'),
        _fight('duel', 'during'),
        _fight('duel', 'after', outcome='won', winner_name='Jaina',
               loser_name='Varian'),
        _fight('duel', 'after', outcome='fled', winner_name='Jaina',
               loser_name='Varian'),
        _fight('pvp', 'after', victor_name='Jaina', fallen_name='Varian',
               onlooker_side_won=True),
    ]
    for extra in scenes:
        text = prox._fight_topic(extra, 'roleplay', db=DB())
        assert 'Jaina is female' in text and 'Varian is male' in text
    before = prox._fight_topic(scenes[0], 'roleplay', db=DB())
    assert 'Jaina (level 40 female Human Mage)' in before
    assert prox._fight_topic(scenes[0], 'roleplay') is not None  # no db


def test_fight_topic_neutral_for_npc_onlookers():
    extra = _fight('duel', 'during')
    assert 'the real player' in prox._fight_topic(extra, 'roleplay')
    neutral = prox._fight_topic(extra, 'roleplay', neutral=True)
    assert 'the real player' not in neutral
    assert 'Jaina is taking part' in neutral


def test_npc_casts_use_neutral_player_description():
    extra = {'player_name': 'Calwen', 'player_guid': 7}
    npc_lines = prox._location_lines(extra, 'roleplay', [dict(NPC)], db=DB())
    joined = '\n'.join(npc_lines)
    assert 'The player Calwen' not in joined
    assert 'Calwen is a female Human' in joined
    mixed = prox._location_lines(
        extra, 'roleplay', [dict(NPC), dict(BOT)], db=DB())
    assert 'The player Calwen' not in '\n'.join(mixed)
    bots = prox._location_lines(extra, 'normal', [dict(BOT)], db=DB())
    assert any(line.startswith('The player Calwen is a level 40 female')
               for line in bots)
    # Prompts that also add the player lines do not repeat them.
    single = _text(prox._player_say_single_prompt(
        DB(), dict(extra, player_addressed=True), dict(NPC), 'hi', []))
    assert single.count('Calwen is a female Human') == 1


def test_npc_only_conversation_leaves_player_and_bots_out():
    rp = {'LLMChatter.ChatterMode': 'roleplay'}
    extra = {'player_name': 'Calwen', 'player_guid': 7,
             'player_addressed': True,
             'nearby_names': ['Hogger', 'Ana'],
             'nearby_npc_names': ['Hogger']}
    npcs = [dict(NPC), dict(NPC, name='Guard Ellis')]
    text = _text(prox._conversation_prompt(DB(), extra, npcs, config=rp))
    assert 'Calwen' not in text
    assert 'Let this colour' not in text
    assert 'Also nearby: Hogger. A speaker' in text
    assert 'never address, mention or tell stories about any passing ' \
        'traveller' in text
    # An older payload without the NPC list offers nobody.
    old = {k: v for k, v in extra.items() if k != 'nearby_npc_names'}
    text = _text(prox._conversation_prompt(DB(), old, npcs, config=rp))
    assert 'Also nearby' not in text and 'Hogger' not in text
    assert 'named below' not in text
    # A scene with a playerbot speaker keeps the player and every name.
    mixed = _text(prox._conversation_prompt(
        DB(), extra, [dict(NPC), dict(BOT)], config=rp))
    assert 'Also nearby: Calwen, Hogger, Ana. A speaker' in mixed
    assert 'passing traveller' not in mixed


def test_proximity_payload_marks_nearby_npcs():
    src = (Path(__file__).resolve().parents[2] / 'src'
           / 'LLMChatterProximity.cpp').read_text()
    assert 'entry.isNPC = c.isNPC;' in src
    assert '",\\"nearby_npc_names\\":"' in src
    assert 'BuildNearbyNpcNamesJson(nearby)' in src


# ------------------------------------------------------------
# Emotes and duels
# ------------------------------------------------------------
def test_party_bot_exchange_lists_party_genders():
    import chatter_emote_observer as observer
    captured = {}

    def fake_call(client, prompt, config, **kwargs):
        captured['prompt'] = _text(prompt)
        return ''

    with patch.object(observer, 'get_bot_traits',
                      return_value={'traits': ['calm'], 'tone': 'warm'}), \
            patch('chatter_group_state.get_group_members',
                  return_value=['Gruk', 'Ana']), \
            patch('chatter_group_state.get_group_player_name',
                  return_value='Calwen'), \
            patch.object(observer, 'call_llm', side_effect=fake_call):
        observer._party_bot_exchange(
            DB(), None, {}, 1, {}, 9, 12, 'Gruk', ['calm'], 'warm',
            11, 'Ana', 'Calwen', 'wave', False, 'roleplay', None,
        )
    assert 'Ana is female' in captured['prompt']
    assert 'Calwen (the player) is female' in captured['prompt']


def test_visible_duellists_get_genders():
    import chatter_duel
    import test_duel_events as duel_tests
    data = {'bot_guid': 30, 'reactor_role': 'spectator'}
    data.update(duel_tests.duellist('duellist_a', 20, 'Jaina',
                                    identity_known=True))
    data.update(duel_tests.duellist('duellist_b', 99, 'Garrosh',
                                    in_group=False, identity_known=False))
    chatter_duel._attach_duellist_genders(DB(), data)
    assert data['duellist_a_gender'] == 'female'
    assert 'duellist_b_gender' not in data   # unseen: no lookup result
    prompt = chatter_duel.build_duel_start_prompt(
        duel_tests.BOT, duel_tests.TRAITS, data, 'roleplay')
    assert 'Jaina (level 40 female Human Warrior)' in prompt
    assert 'Garrosh' not in prompt


def test_pvp_enemy_gender_only_when_known_and_valid():
    from chatter_shared import build_pvp_enemy_context
    base = {'is_pvp': True, 'enemy_identity_known': True,
            'enemy_name': 'Thrall', 'enemy_race': 2, 'enemy_class': 7,
            'enemy_level': 60, 'enemy_faction': 'Horde'}
    with patch('chatter_shared.is_pvp_enemy', return_value=True):
        female = build_pvp_enemy_context(dict(base, enemy_gender=1))
        assert 'level 60 female Orc Shaman' in female
        for value in (None, 2, 'x'):
            text = build_pvp_enemy_context(dict(base, enemy_gender=value))
            assert 'female' not in text and ' male' not in text
        assert 'male' not in build_pvp_enemy_context(base)
        hidden = build_pvp_enemy_context(dict(
            base, enemy_gender=1, enemy_identity_known=False))
        assert 'female' not in hidden and 'Thrall' not in hidden


# ------------------------------------------------------------
# Memories, boss dialogue, AB, precache
# ------------------------------------------------------------
def test_memory_prompt_names_player_gender():
    import chatter_memory
    captured = {}

    def fake_call(*args, **kwargs):
        captured['prompt'] = _text(args[1] if len(args) > 1
                                   else kwargs.get('prompt'))
        return ''

    with patch.object(chatter_memory, 'get_llm_client',
                      return_value=object()), \
            patch.object(chatter_memory, 'call_llm',
                         side_effect=fake_call):
        chatter_memory._call_llm_for_memory(
            {}, bot_name='Gruk', bot_class='Warrior', bot_race='Orc',
            bot_gender='male', player_name='Calwen',
            player_gender='female', memory_type='boss_kill')
    assert 'Player companion: Calwen (female)' in captured['prompt']


def test_memory_generator_resolves_player_gender():
    import chatter_memory
    seen = {}

    def fake_llm(config, **kwargs):
        seen.update(kwargs)
        return None, None

    with patch.object(chatter_memory, 'get_db_connection',
                      return_value=DB()), \
            patch.object(chatter_memory, '_call_llm_for_memory',
                         side_effect=fake_llm):
        chatter_memory._execute_generate_memory(
            {}, 0, 12, 7, 'boss_kill', 'Killed Hogger',
            bot_name='Gruk', insert_active=True)
    assert seen['player_name'] == 'Calwen'
    assert seen['player_gender'] == 'female'


def test_memory_event_contexts_carry_genders():
    import chatter_battlegrounds
    assert chatter_battlegrounds._victim_label(
        {'victim_gender': 'female', 'victim_race': 'Troll'}, 'Ana',
    ) == 'Ana, a female Troll,'
    assert chatter_battlegrounds._victim_label({}, 'Ana') == 'Ana'
    source = (Path(chatter_battlegrounds.__file__).parent
              / 'chatter_group_handlers.py').read_text(encoding='utf-8')
    assert "gender_from_id(extra_data.get('enemy_gender'))" in source
    assert 'genders_by_named_guid(\n        db, {leveler_name: leveler_guid}' \
        in source


def test_boss_line_states_player_gender():
    import chatter_boss_dialogue as boss
    extra = {'boss': {'name': 'Hogger', 'role': 'boss'},
             'player_name': 'Calwen', 'player_gender': 'female'}
    assert 'Nearby adventurer: Calwen (female).' in _text(
        boss._build_prompt(extra))
    extra.pop('player_gender')
    assert 'Nearby adventurer: Calwen.' in _text(boss._build_prompt(extra))


def test_batched_ab_actor_gets_a_gender():
    extra = {'node_changes': [{'actor_name': 'Ana'},
                              {'actor_name': 'Bo'}]}
    line = gender.bg_subject_gender_line(
        DB(), extra, 'Ana took the Stables.', 'Gruk')
    assert 'Ana is female' in line
    assert 'Bo' not in line   # not shown in the prompt


def test_precache_support_target_is_never_gendered():
    from chatter_group_prompts import build_precache_spell_support_prompt
    text = _text(build_precache_spell_support_prompt(
        'Mira', 'Human', 'Priest', 40, ['kind'], 'neutral'))
    assert 'never use he/she/him/her for {target}' in text


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} proximity/event gender checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
