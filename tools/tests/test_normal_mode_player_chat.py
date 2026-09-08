#!/usr/bin/env python3
"""Focused regression checks for normal-mode player chat routing."""

import importlib
import sys
import types
from pathlib import Path


def _ensure_module(name):
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


for dependency in ('anthropic', 'openai'):
    try:
        importlib.import_module(dependency)
    except ModuleNotFoundError:
        module = _ensure_module(dependency)
        attribute = 'Anthropic' if dependency == 'anthropic' else 'OpenAI'
        setattr(module, attribute, type(attribute, (), {}))

try:
    importlib.import_module('mysql.connector')
except ModuleNotFoundError:
    mysql_module = _ensure_module('mysql')
    connector_module = _ensure_module('mysql.connector')
    setattr(mysql_module, 'connector', connector_module)

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from chatter_bg_prompts import (  # noqa: E402
    BG_IDLE_CATEGORIES,
    _bg_base_context,
)
from chatter_cache import discard_ready_precache  # noqa: E402
from chatter_constants import (  # noqa: E402
    AMBIENT_CHAT_TOPICS,
    AMBIENT_CHAT_TOPICS_RP,
    GUILD_CHAT_TOPICS,
    MESSAGE_CATEGORIES,
    MOODS,
    PROXIMITY_PLAYER_CHAT_TOPICS,
)
from chatter_group_prompts import (  # noqa: E402
    BG_QUESTION_TOPICS,
    BOT_QUESTION_TOPICS_NORMAL,
    DUNGEON_QUESTION_TOPICS,
    build_bot_greeting_prompt,
    build_low_health_callout_prompt,
    build_nearby_object_reaction_prompt,
    build_precache_state_prompt,
)
from chatter_group import build_idle_chatter_prompt  # noqa: E402
from chatter_group_general_reaction import (  # noqa: E402
    _build_statement_prompt as _general_relay_prompt,
)
import chatter_group_state as group_state  # noqa: E402
from chatter_guild import (  # noqa: E402
    _build_guild_conversation_prompt,
    _build_guild_prompt,
)
from chatter_guild_login import (  # noqa: E402
    _build_single_prompt as _guild_login_prompt,
)
from chatter_mode import (  # noqa: E402
    build_player_chat_guidance,
    build_player_prompt_header,
    resolve_player_personality,
)
from chatter_prompts import build_plain_statement_prompt  # noqa: E402
from chatter_proximity import (  # noqa: E402
    _conversation_prompt,
    _single_prompt,
)
from chatter_raid_prompts import _raid_base_context  # noqa: E402
from chatter_shared import set_action_chance  # noqa: E402


NORMAL_CONFIG = {'LLMChatter.ChatterMode': 'normal'}
RP_CONFIG = {'LLMChatter.ChatterMode': 'roleplay'}
BOT = {
    'name': 'Aliss',
    'bot_name': 'Aliss',
    'race': 'Human',
    'class': 'Mage',
    'level': 32,
    'gender': 'female',
}


class _Cursor:
    def __init__(self, rows=None, rowcount=0):
        self.rows = list(rows or [])
        self.rowcount = rowcount
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        rows = list(self.rows)
        self.rows.clear()
        return rows


class _DB:
    def __init__(self, rows=None, rowcount=0):
        self.cursor_value = _Cursor(rows, rowcount)
        self.commits = 0

    def cursor(self, *args, **kwargs):
        return self.cursor_value

    def commit(self):
        self.commits += 1


def test_canonical_normal_voice_is_friendly_and_player_side():
    text = build_player_chat_guidance('normal', 'party')
    assert 'person playing WoW' in text
    assert 'Friendly and respectful is the default' in text
    assert 'never force rudeness' in text
    assert 'socially imperfect' not in text
    assert 'physically feel' in text
    assert 'legacy character metadata' in text


def test_normal_personality_replaces_persisted_roleplay_metadata():
    first = resolve_player_personality(
        'Glaskez',
        ['zealous', 'spirit-touched', 'routine-bound'],
        'devoutly precise, mystical, and unwavering',
        'normal',
    )
    second = resolve_player_personality(
        'Glaskez', ['different'], 'different', 'normal'
    )
    assert first == second
    assert len(first[0]) == 3
    joined = ' '.join(first[0] + [first[1]]).lower()
    assert 'spirit' not in joined
    assert 'mystic' not in joined
    assert 'devout' not in joined

    roleplay = resolve_player_personality(
        'Glaskez', ['spirit-touched'], 'mystical', 'roleplay'
    )
    assert roleplay == (['spirit-touched'], 'mystical')


def test_roleplay_header_preserves_in_world_voice():
    text = build_player_prompt_header(
        'Aliss', 'Human', 'Mage', 32, 'female', 'roleplay'
    )
    assert 'CHAT MODE: ROLEPLAY' in text
    assert 'living in Azeroth' in text
    assert 'person playing' not in text


def test_normal_shared_pools_do_not_request_roleplay_sensations():
    joined = ' '.join(MOODS + MESSAGE_CATEGORIES).lower()
    assert 'roleplaying' not in joined
    assert 'sensing something magical nearby' not in joined
    assert PROXIMITY_PLAYER_CHAT_TOPICS


def test_normal_topic_pools_have_scale_and_no_duplicates():
    minimum_sizes = {
        'ambient': (AMBIENT_CHAT_TOPICS, 100),
        'guild': (GUILD_CHAT_TOPICS, 180),
        'proximity': (PROXIMITY_PLAYER_CHAT_TOPICS, 150),
        'party questions': (BOT_QUESTION_TOPICS_NORMAL, 60),
        'dungeon questions': (DUNGEON_QUESTION_TOPICS, 30),
        'battleground questions': (BG_QUESTION_TOPICS, 30),
        'battleground idle': (BG_IDLE_CATEGORIES, 40),
    }
    for label, (pool, minimum) in minimum_sizes.items():
        assert len(pool) >= minimum, (label, len(pool), minimum)
        normalized = {
            str(entry).strip().casefold()
            for entry in pool
        }
        assert len(normalized) == len(pool), label

    normal_only_topic = (
        'wondering whether anyone else changed a useful interface setting'
    )
    assert normal_only_topic in AMBIENT_CHAT_TOPICS
    assert normal_only_topic not in AMBIENT_CHAT_TOPICS_RP


def test_party_low_health_uses_character_boundary():
    prompt = build_low_health_callout_prompt(
        BOT, ['patient'], 'a ghoul', 'normal',
        extra_data={'bot_state': {'health_pct': 8}},
    )
    assert 'CHAT MODE: NORMAL' in prompt.user_prompt
    assert 'Your character is critically low on health' in prompt.user_prompt
    assert 'You are critically wounded' not in prompt.user_prompt


def test_normal_dungeon_greeting_keeps_gameplay_location_context():
    prompt = build_bot_greeting_prompt(
        BOT, ['patient'], 'normal', map_id=33,
    )
    assert 'Your character is currently in a dungeon' in prompt.user_prompt
    assert 'haunted fortress' not in prompt.user_prompt


def test_normal_outdoor_greeting_keeps_zone_name_context():
    prompt = build_bot_greeting_prompt(
        BOT, ['patient'], 'normal', zone_id=12,
    )
    assert 'Zone: Elwynn Forest' in prompt.user_prompt
    assert 'Peaceful human farmland' not in prompt.user_prompt


def test_hot_party_prompts_include_normal_contract_once():
    idle = build_idle_chatter_prompt(
        BOT, ['patient'], 'normal',
    )
    nearby = build_nearby_object_reaction_prompt(
        'Aliss', 'Mage', 'Human', ['patient'],
        [{'name': 'Forge', 'type': 'GameObject'}],
        'Stormwind', 'Trade District', True, False, 'normal',
    )
    assert idle.user_prompt.count('CHAT MODE: NORMAL.') == 1
    assert nearby.user_prompt.count('CHAT MODE: NORMAL.') == 1


def test_general_to_party_relay_hides_rp_location_flavor():
    bot = {
        **BOT,
        'trait1': 'patient',
        'travel_context': 'riding quickly through the rain',
    }
    prompt = _general_relay_prompt(
        bot,
        {'name': 'Rytsen', 'race': 'Dwarf', 'class': 'Warrior'},
        'anyone need this quest?',
        'Player',
        '',
        'normal',
        {
            'dungeon_flavor': 'cold stone pressing around you',
            'zone_flavor': 'the forest whispers to travelers',
            'subzone_lore': 'ancient spirits linger here',
        },
    )
    assert 'CHAT MODE: NORMAL' in prompt.user_prompt
    assert 'Character gameplay travel state' in prompt.user_prompt
    assert 'cold stone pressing' not in prompt.user_prompt
    assert 'ancient spirits' not in prompt.user_prompt


def test_general_statement_uses_canonical_normal_guidance():
    prompt = build_plain_statement_prompt(
        {**BOT, 'zone': 'Elwynn Forest'},
        config=NORMAL_CONFIG,
        topic='the next quest',
    )
    assert 'CHAT MODE: NORMAL' in prompt.user_prompt
    assert 'not roleplaying your character' in prompt.user_prompt
    assert 'physically feel' in prompt.user_prompt


def test_precache_prompt_is_mode_aware():
    normal = build_precache_state_prompt(
        'low_health', 'Aliss', 'Human', 'Mage', 32,
        ['patient'], 'neutral', 'calm', mode='normal',
    )
    roleplay = build_precache_state_prompt(
        'low_health', 'Aliss', 'Human', 'Mage', 32,
        ['patient'], 'neutral', 'calm', mode='roleplay',
    )
    assert 'character is critically low' in normal.user_prompt
    assert 'critically wounded' not in normal.user_prompt
    assert 'critically wounded' in roleplay.user_prompt


def test_guild_normal_omits_backstory_and_rp_bans():
    speaker = {
        **BOT,
        'traits': ['zealous', 'spirit-touched'],
        'tone': 'devoutly precise and mystical',
        'backstory': 'Raised beside the canals of Stormwind.',
    }
    normal = _build_guild_prompt(
        'Aliss', speaker, 'Example', 'Rytsen', NORMAL_CONFIG,
        topic='anyone for a dungeon',
    )
    roleplay = _build_guild_prompt(
        'Aliss', speaker, 'Example', 'Rytsen', RP_CONFIG,
        topic='news from the road',
    )
    assert 'CHAT MODE: NORMAL' in normal.user_prompt
    assert 'Raised beside' not in normal.user_prompt
    assert 'spirit-touched' not in normal.user_prompt
    assert 'devoutly precise' not in normal.user_prompt
    assert 'avoid game-mechanic talk' not in normal.user_prompt
    assert 'Raised beside' in roleplay.user_prompt
    assert 'spirit-touched' in roleplay.user_prompt
    assert 'devoutly precise' in roleplay.user_prompt
    assert 'Stay fully in character' in roleplay.user_prompt
    for term in ('DPS', 'pulls', 'specs', 'loot', 'addons'):
        assert term in roleplay.user_prompt


def test_guild_roleplay_conversation_preserves_explicit_mechanic_bans():
    prompt = _build_guild_conversation_prompt(
        [{
            'name': 'Aliss',
            'speaker': {**BOT, 'traits': ['patient']},
            'zone_id': 0,
            'map_id': 0,
        }],
        'Example', '', 'news from the road', '', False, 1,
        mode='roleplay',
    )
    for term in ('DPS', 'specs', 'talents', 'loot', 'mobs', 'XP',
                 'rotations', 'addons', 'players behind screens'):
        assert term in prompt.user_prompt


def test_guild_login_uses_configured_voice():
    participant = {
        'name': 'Aliss',
        'speaker': {**BOT, 'traits': ['patient']},
        'zone_id': 0,
        'map_id': 0,
    }
    prompt = _guild_login_prompt(
        participant, 'Example', 'Alliance', 'Player',
        False, 120, 'normal',
    )
    assert 'CHAT MODE: NORMAL' in prompt.user_prompt
    assert 'Stay fully in Azeroth' not in prompt.user_prompt


def test_bg_and_raid_hide_lived_world_lore_in_normal_mode():
    bg_extra = {
        '_config': NORMAL_CONFIG,
        'bg_type_id': 2,
        'team': 'Alliance',
    }
    bg_normal = _bg_base_context(bg_extra, BOT)
    bg_rp = _bg_base_context(
        {**bg_extra, '_config': RP_CONFIG}, BOT
    )
    assert 'CHAT MODE: NORMAL' in bg_normal
    assert 'Lore:' not in bg_normal
    assert 'CHAT MODE: NORMAL' not in bg_rp

    raid_extra = {
        '_config': NORMAL_CONFIG,
        'raid_name': 'Icecrown Citadel',
    }
    raid_normal = _raid_base_context(raid_extra, BOT)
    raid_rp = _raid_base_context(
        {**raid_extra, '_config': RP_CONFIG}, BOT
    )
    assert 'CHAT MODE: NORMAL' in raid_normal
    assert 'Lore:' not in raid_normal
    assert 'Lore:' in raid_rp


def test_proximity_routes_npc_and_playerbot_independently():
    npc = {
        'name': 'Innkeeper Allison',
        'is_npc': True,
        'role': 'Innkeeper',
    }
    npc_prompt = _single_prompt(
        _DB(), {}, npc, 'local news', config=NORMAL_CONFIG
    )
    assert 'SPEAKER TYPE: NPC' in npc_prompt.user_prompt
    assert 'CHAT MODE: NORMAL' not in npc_prompt.user_prompt

    db = _DB(rows=[{
        'class': 8,
        'race': 1,
        'gender': 1,
        'level': 32,
    }, None])
    playerbot = {
        'name': 'Aliss',
        'is_npc': False,
        'bot_guid': 7,
    }
    bot_prompt = _single_prompt(
        db, {}, playerbot, 'queue time', config=NORMAL_CONFIG
    )
    assert 'CHAT MODE: NORMAL' in bot_prompt.user_prompt
    assert 'SPEAKER TYPE: NPC' not in bot_prompt.user_prompt


def test_mixed_proximity_scene_has_per_speaker_contracts():
    participants = [
        {
            'name': 'Innkeeper Allison',
            'is_npc': True,
            'role': 'Innkeeper',
        },
        {
            'name': 'Aliss',
            'is_npc': False,
            'bot_guid': 7,
        },
    ]
    db = _DB(rows=[{
        'class': 8,
        'race': 1,
        'gender': 1,
        'level': 32,
    }, None])
    prompt = _conversation_prompt(
        db, {}, participants, NORMAL_CONFIG
    )
    assert '[NPC]' in prompt.user_prompt
    assert '[PLAYERBOT]' in prompt.user_prompt
    assert 'For each roster entry tagged [NPC]' in prompt.user_prompt
    assert 'CHAT MODE: NORMAL' in prompt.user_prompt


def test_normal_playerbot_only_proximity_forbids_actions():
    playerbot = {
        'name': 'Aliss',
        'is_npc': False,
        'bot_guid': 7,
    }
    db = _DB(rows=[{
        'class': 8,
        'race': 1,
        'gender': 1,
        'level': 32,
    }, None])
    set_action_chance(100, mode='roleplay')
    try:
        prompt = _conversation_prompt(
            db, {}, [playerbot], NORMAL_CONFIG
        )
    finally:
        set_action_chance(10, mode='normal')
    assert 'Set "action" to null for ALL messages' in prompt.system_prompt
    assert 'EVERY message MUST include' not in prompt.system_prompt


def test_normal_farewell_is_stored_only_for_active_group():
    db = _DB()
    original_call_llm = group_state.call_llm
    group_state.call_llm = lambda *args, **kwargs: 'gg, thanks all'
    try:
        group_state._generate_farewell(
            db, object(), NORMAL_CONFIG,
            'Aliss', 'Human', 'Mage', 'female',
            ['patient'], 'normal', 42, 7,
        )
    finally:
        group_state.call_llm = original_call_llm

    queries = [query for query, _ in db.cursor_value.queries]
    assert any(
        'UPDATE llm_group_bot_traits' in query
        and 'SET farewell_msg' in query
        for query in queries
    )
    assert not any(
        'UPDATE llm_bot_identities' in query
        and 'SET farewell_msg' in query
        for query in queries
    )


def test_normal_startup_replaces_active_group_rp_metadata():
    db = _DB(rows=[{
        'group_id': 42,
        'bot_guid': 7,
        'bot_name': 'Glaskez',
    }])
    count = group_state.normalize_active_group_personalities(
        db, NORMAL_CONFIG
    )
    assert count == 1
    updates = [
        (query, params)
        for query, params in db.cursor_value.queries
        if 'UPDATE llm_group_bot_traits' in query
    ]
    assert len(updates) == 1
    query, params = updates[0]
    assert 'trait3 = %s' in query
    assert 'backstory = NULL' in query
    combined = ' '.join(str(value) for value in params[:4]).lower()
    assert 'spirit' not in combined
    assert 'mystic' not in combined

    rp_db = _DB()
    assert group_state.normalize_active_group_personalities(
        rp_db, RP_CONFIG
    ) == 0
    assert not rp_db.cursor_value.queries


def test_shipped_config_defaults_to_normal_mode():
    config_path = (
        TOOLS_DIR.parent / 'conf' / 'mod_llm_chatter.conf.dist'
    )
    text = config_path.read_text(encoding='utf-8')
    assert 'Default: normal' in text
    assert 'LLMChatter.ChatterMode = normal' in text
    assert 'Actual NPCs remain in character in either mode' in text


def test_startup_cache_cleanup_only_discards_ready_rows():
    db = _DB(rowcount=4)
    assert discard_ready_precache(db) == 4
    query = db.cursor_value.queries[0][0]
    assert "status = 'ready'" in query
    assert 'DELETE FROM llm_group_cached_responses' in query
    assert db.commits == 1


def main():
    tests = [
        value for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f'{len(tests)} normal-mode player-chat tests passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
