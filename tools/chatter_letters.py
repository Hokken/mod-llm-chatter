"""Reactivity letters: mail that answers what the player did.

One background pass reads llm_reactivity_inbox, turns deeds into
scheduled letters and rumors, and writes letters that have come due.
The worldserver sends rows marked ready. Nothing here waits on a live
player, so letters written for someone offline reach them at next login.
"""

import json
import logging
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import chatter_progression
from chatter_db import get_race_name
from chatter_llm import call_llm
from chatter_mode import build_player_identity, is_roleplay
from chatter_reactive_rumors import (
    settle_voicings,
    unlock_rumor,
)
from chatter_reactivity_data import (
    PROFESSION_SKILLS,
    faction_allows,
    gifts,
    letter_by_key,
    letter_for_achievement,
    letter_for_quest,
    rumor_for_achievement,
    rumor_for_quest,
    sender_for,
    trainer_entry,
)
from chatter_letter_prompts import (
    deed_letter_prompt,
    memory_letter_prompt,
    profession_letter_prompt,
    starter_letter_prompt,
)
from chatter_shared import (
    get_chatter_mode,
    get_class_name,
    get_gender_label,
    localize_item_name,
)
from chatter_structured import ResponseContract
from chatter_trainer_rumor_data import PROFESSION_TRAINERS

logger = logging.getLogger(__name__)

INBOX_BATCH = 100
MAX_ATTEMPTS = 3
RETRY_MINUTES = 10
NO_BOT_RETRY_HOURS = 24
STUCK_SENDING_MINUTES = 30
# The model counts words far better than characters, and overruns
# either. This many characters per word it is asked for leaves room.
CHARS_PER_TARGET_WORD = 8
MAX_SIGNOFF_CHARS = 100

MANA_CLASSES = {
    'Paladin', 'Hunter', 'Priest', 'Shaman', 'Mage', 'Warlock', 'Druid',
}
_STRENGTH_CLASSES = {'Warrior', 'Paladin', 'Death Knight'}
_AGILITY_CLASSES = {'Rogue', 'Hunter', 'Shaman', 'Druid'}
_CASTERS = {'Priest', 'Mage', 'Warlock', 'Shaman', 'Druid', 'Paladin'}

# Stack sizes follow the Stacks rule of the gift tables.
_STACKS = {
    'healing': (3, 5), 'mana': (3, 5), 'food': (5, 10),
    'scroll': (1, 3), 'elixir': (1, 3), 'weapon': (1, 3),
    'drink': (1, 3), 'flower': (1, 3), 'gem': (1, 2),
}

_ARMOR_SUBCLASSES = {
    'Mage': (1,), 'Priest': (1,), 'Warlock': (1,),
    'Rogue': (2,), 'Druid': (2,),
    'Hunter': (3,), 'Shaman': (3,),
    'Warrior': (4,), 'Paladin': (4,), 'Death Knight': (4,),
}

# A rare treat among gifts: kept, but seldom picked.
_PRECIOUS_CHANCE = 0.1


def _int(config, key, default) -> int:
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _enabled(config, key, default='1') -> bool:
    return str(config.get(key, default)).strip() == '1'


def letters_enabled(config) -> bool:
    return _enabled(config, 'LLMChatter.Letters.Enable')


def rumors_enabled(config) -> bool:
    return _enabled(config, 'LLMChatter.Rumors.Enable')


def _kind_enabled(config, section: str) -> bool:
    return letters_enabled(config) and _enabled(
        config, f'LLMChatter.Letters.{section}.Enable'
    )


def _roll_range(config, section, low_key, high_key, low, high) -> int:
    first = _int(config, f'LLMChatter.Letters.{section}.{low_key}', low)
    last = _int(config, f'LLMChatter.Letters.{section}.{high_key}', high)
    return random.randint(min(first, last), max(first, last))


def _roll_delay_seconds(config, section, low, high) -> int:
    first = _int(
        config, f'LLMChatter.Letters.{section}.DelayMinDays', low
    )
    last = _int(
        config, f'LLMChatter.Letters.{section}.DelayMaxDays', high
    )
    return random.randint(
        min(first, last) * 86400, max(first, last) * 86400
    )


def _memory_cooldown_seconds(config) -> int:
    first = _int(
        config, 'LLMChatter.Letters.Memories.CooldownMinDays', 7
    )
    last = _int(
        config, 'LLMChatter.Letters.Memories.CooldownMaxDays', 10
    )
    return random.randint(
        min(first, last) * 86400, max(first, last) * 86400
    )


def clean_text(text: str) -> str:
    """Letter text the mail system can carry. The core blanks anything
    holding "| |", and a pipe is the client's link escape."""
    text = str(text or '').replace('|', '')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _cut_at_sentence(text: str, limit: int) -> str:
    cut = text[:limit]
    end = max(cut.rfind(mark) for mark in ('.', '!', '?', '\n'))
    if end >= limit // 2:
        return cut[:end + 1].rstrip()
    return cut.rstrip()


def clamp_body(text: str, limit: int) -> str:
    """Cut at the last full sentence inside the limit, keeping the
    sign-off: a letter must still say who it is from."""
    if len(text) <= limit:
        return text
    head, separator, tail = text.rpartition('\n\n')
    if not head or len(tail) > MAX_SIGNOFF_CHARS:
        return _cut_at_sentence(text, limit)
    kept = _cut_at_sentence(head, limit - len(tail) - len(separator))
    return f'{kept}{separator}{tail}'


def clamp_subject(text: str, limit: int) -> str:
    text = ' '.join(clean_text(text).split())
    return text[:limit].rstrip()


def _limits(config) -> Dict:
    body = _int(config, 'LLMChatter.Letters.MaxChars', 900)
    return {
        'body_chars': body,
        'target_words': body // CHARS_PER_TARGET_WORD,
        'subject_chars': _int(
            config, 'LLMChatter.Letters.MaxSubjectChars', 60
        ),
    }


def items_spec(items: List[Dict]) -> str:
    return ','.join(
        f"{item['entry']}:{item['count']}" for item in items
    )


# ------------------------------------------------------------
# Player facts
# ------------------------------------------------------------

def _character(db, guid: int) -> Optional[Dict]:
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT name, race, class, gender, level, online "
        "FROM characters WHERE guid = %s",
        (guid,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {
        'guid': guid,
        'name': row['name'],
        'race': get_race_name(int(row['race'])),
        'class': get_class_name(int(row['class'])),
        'gender': get_gender_label(int(row['gender'])),
        'level': int(row['level']),
        'online': bool(row['online']),
    }


def _roll_starter_level(level: int, first: int, last: int) -> int:
    """A level inside the window that is still ahead of the character;
    0 when the window has passed."""
    start = max(first, level + 1)
    return random.randint(start, last) if start <= last else 0


def _next_profession_level(config, level: int) -> int:
    start = _int(config, 'LLMChatter.Letters.Professions.FirstLevel', 25)
    if level < start:
        return start
    return level + _roll_range(
        config, 'Professions', 'IntervalMinLevels', 'IntervalMaxLevels',
        10, 16,
    )


def _ensure_state(db, config, guid: int, facts: Dict) -> Dict:
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM llm_reactivity_player_state "
        "WHERE player_guid = %s",
        (guid,),
    )
    state = cursor.fetchone()
    if state:
        return state

    level = int(facts.get('level', 1) or 1)
    one = _roll_starter_level(
        level,
        _int(config, 'LLMChatter.Letters.Starters.FirstMinLevel', 5),
        _int(config, 'LLMChatter.Letters.Starters.FirstMaxLevel', 15),
    )
    two = _roll_starter_level(
        level,
        _int(config, 'LLMChatter.Letters.Starters.SecondMinLevel', 15),
        _int(config, 'LLMChatter.Letters.Starters.SecondMaxLevel', 25),
    )
    state = {
        'player_guid': guid,
        'team': facts.get('team', 'Alliance'),
        'starter_one_level': one,
        'starter_two_level': two,
        'starter_one_skill': None,
        'next_profession_level': _next_profession_level(config, level),
    }
    cursor.execute(
        "INSERT IGNORE INTO llm_reactivity_player_state "
        "(player_guid, team, next_memory_at, starter_one_level, "
        "starter_two_level, next_profession_level) "
        "VALUES (%s, %s, NOW() + INTERVAL %s SECOND, %s, %s, %s)",
        (
            guid, state['team'], _memory_cooldown_seconds(config),
            one, two, state['next_profession_level'],
        ),
    )
    db.commit()
    return state


# ------------------------------------------------------------
# Scheduling
# ------------------------------------------------------------

def _insert_letter(
    db, guid, kind, key, team, status='scheduled',
    delay_seconds=0, sender_type='creature', sender_id=0,
    context=None,
) -> bool:
    """False when this letter was already decided for this player.
    Times are the database's: the bridge may run in another timezone."""
    cursor = db.cursor()
    cursor.execute(
        "INSERT IGNORE INTO llm_reactivity_letters "
        "(player_guid, kind, letter_key, status, not_before, team, "
        "sender_type, sender_id, context) "
        "VALUES (%s, %s, %s, %s, NOW() + INTERVAL %s SECOND, %s, "
        "%s, %s, %s)",
        (
            guid, kind, key, status, delay_seconds, team,
            sender_type, sender_id,
            json.dumps(context) if context else None,
        ),
    )
    db.commit()
    return cursor.rowcount > 0


_DEED_RULES = {
    'dungeon': ('Dungeons', 50, 2, 4),
    'raid': ('Raids', 100, 4, 6),
    'quest': ('Quests', 100, 4, 6),
}


def _schedule_deed_letter(
    db, config, guid, team, found, trigger_id=0
) -> bool:
    if not found:
        return False
    kind, row = found
    section, chance, low, high = _DEED_RULES[kind]
    if not _kind_enabled(config, section):
        return False
    if not faction_allows(row, team):
        return False

    # The roll is stored too: a second achievement for the same
    # dungeon must not earn a second chance at its one letter.
    rolled = random.randint(1, 100) <= _int(
        config, f'LLMChatter.Letters.{section}.Chance', chance
    )
    return _insert_letter(
        db, guid, kind, row['key'], team,
        status='scheduled' if rolled else 'skipped',
        delay_seconds=_roll_delay_seconds(
            config, section, low, high
        ),
        context={'trigger_id': trigger_id},
    ) and rolled


def _trainer_for(
    profession: str, team: str, race: str
) -> Optional[Dict]:
    """A trainer of this profession for the player's race; for a race
    the table does not know, any of the faction's."""
    races = PROFESSION_TRAINERS.get(team, {})
    own = [
        trainer for trainer in races.get(race, [])
        if trainer['skill'] == profession
    ]
    if not own:
        own = [
            trainer for trainers in races.values()
            for trainer in trainers
            if trainer['skill'] == profession
        ]
    named = [t for t in own if trainer_entry(t['name'])]
    return random.choice(named) if named else None


def _known_professions(facts: Dict) -> Dict[str, int]:
    known = {}
    for skill, value in (facts.get('skills') or {}).items():
        name = PROFESSION_SKILLS.get(int(skill))
        if name:
            known[name] = int(value)
    return known


def _schedule_starter(
    db, config, guid: int, state: Dict, facts: Dict, slot: str,
) -> Optional[str]:
    """Returns the profession offered, if a letter was scheduled."""
    if int(facts.get('free_professions', 0) or 0) <= 0:
        return None
    character = _character(db, guid)
    if not character:
        return None

    known = _known_professions(facts)
    choices = [
        name for name in gifts()['starters']
        if name not in known
        and name != state.get('starter_one_skill')
        and chatter_progression.profession_available(db, guid, name)
    ]
    random.shuffle(choices)
    for profession in choices:
        trainer = _trainer_for(
            profession, state['team'], character['race']
        )
        if not trainer:
            continue
        _insert_letter(
            db, guid, 'starter', slot, state['team'],
            sender_id=trainer_entry(trainer['name']),
            context={'profession': profession, 'trainer': trainer},
        )
        return profession
    return None


def eligible_bundle(
    profession: str, skill: int, level: int
) -> Optional[Dict]:
    bundles = [
        bundle for bundle in gifts()['professions'].get(profession, [])
        if bundle['min_skill'] <= skill <= bundle['until_skill']
        and bundle['min_level'] <= level
        and level <= bundle.get('until_level', 80)
    ]
    return random.choice(bundles) if bundles else None


def _schedule_profession(
    db, config, guid: int, state: Dict, facts: Dict, level: int,
) -> bool:
    character = _character(db, guid)
    if not character:
        return False
    known = list(_known_professions(facts).items())
    random.shuffle(known)
    for profession, skill in known:
        bundle = eligible_bundle(profession, skill, level)
        trainer = (
            _trainer_for(profession, state['team'], character['race'])
            if bundle else None
        )
        if not trainer:
            continue
        _insert_letter(
            db, guid, 'profession', f'level{level}', state['team'],
            sender_id=trainer_entry(trainer['name']),
            context={
                'profession': profession,
                'trainer': trainer,
                'bundle': bundle,
            },
        )
        return True
    return False


def _handle_level(db, config, guid: int, level: int, facts: Dict) -> None:
    state = _ensure_state(db, config, guid, facts)
    cursor = db.cursor()

    if _kind_enabled(config, 'Starters'):
        one = int(state['starter_one_level'] or 0)
        two = int(state['starter_two_level'] or 0)
        if one and level >= one:
            offered = _schedule_starter(
                db, config, guid, state, facts, 'first'
            )
            cursor.execute(
                "UPDATE llm_reactivity_player_state "
                "SET starter_one_level = 0, starter_one_skill = %s "
                "WHERE player_guid = %s",
                (offered, guid),
            )
            state['starter_one_skill'] = offered
        if two and level >= two:
            _schedule_starter(
                db, config, guid, state, facts, 'second'
            )
            cursor.execute(
                "UPDATE llm_reactivity_player_state "
                "SET starter_two_level = 0 WHERE player_guid = %s",
                (guid,),
            )

    due = int(state['next_profession_level'] or 0)
    if _kind_enabled(config, 'Professions') and due and level >= due:
        _schedule_profession(db, config, guid, state, facts, level)
        cursor.execute(
            "UPDATE llm_reactivity_player_state "
            "SET next_profession_level = %s WHERE player_guid = %s",
            (_next_profession_level(config, level), guid),
        )
    db.commit()


def _handle_deed(db, config, row: Dict) -> None:
    kind = row['kind']
    guid = int(row['player_guid'])
    trigger = int(row['trigger_id'])
    try:
        facts = json.loads(row.get('extra_data') or '{}')
    except ValueError:
        facts = {}

    if kind == 'login':
        _ensure_state(db, config, guid, facts)
        return
    if kind == 'level':
        _handle_level(db, config, guid, trigger, facts)
        return

    state = _ensure_state(db, config, guid, facts)
    team = state['team']
    if kind == 'achievement':
        letter = letter_for_achievement(trigger)
        rumor = rumor_for_achievement(trigger)
    else:
        letter = letter_for_quest(trigger)
        rumor = rumor_for_quest(trigger)
    _schedule_deed_letter(db, config, guid, team, letter, trigger)
    if rumor and rumors_enabled(config):
        unlock_rumor(db, config, guid, team, rumor)


def _drain_inbox(db, config) -> None:
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, kind, player_guid, trigger_id, extra_data "
        "FROM llm_reactivity_inbox ORDER BY id LIMIT %s",
        (INBOX_BATCH,),
    )
    rows = cursor.fetchall()
    for row in rows:
        try:
            _handle_deed(db, config, row)
        except Exception:
            logger.error(
                "reactivity inbox row %s failed", row['id'],
                exc_info=True,
            )
        cursor.execute(
            "DELETE FROM llm_reactivity_inbox WHERE id = %s",
            (row['id'],),
        )
        db.commit()


def _group_mates(db, guid: int) -> set:
    cursor = db.cursor()
    cursor.execute(
        "SELECT other.memberGuid FROM group_member own "
        "JOIN group_member other ON other.guid = own.guid "
        "WHERE own.memberGuid = %s",
        (guid,),
    )
    return {int(row[0]) for row in cursor.fetchall()}


def _pick_memory_bot(db, guid: int) -> int:
    cursor = db.cursor()
    cursor.execute(
        "SELECT DISTINCT bot_guid FROM llm_bot_memories "
        "WHERE player_guid = %s AND active = 1",
        (guid,),
    )
    mates = _group_mates(db, guid)
    bots = [
        int(row[0]) for row in cursor.fetchall()
        if int(row[0]) not in mates
    ]
    return random.choice(bots) if bots else 0


def _schedule_memory_letters(db, config) -> None:
    if not _kind_enabled(config, 'Memories'):
        return
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT s.player_guid, s.team "
        "FROM llm_reactivity_player_state s "
        "JOIN characters c ON c.guid = s.player_guid "
        "WHERE s.next_memory_at <= NOW() AND c.online = 1"
    )
    for row in cursor.fetchall():
        guid = int(row['player_guid'])
        bot = _pick_memory_bot(db, guid)
        if bot:
            _insert_letter(
                db, guid, 'memory',
                datetime.now().strftime('%Y%m%d%H%M%S'),
                row['team'], sender_type='bot', sender_id=bot,
            )
            wait = _memory_cooldown_seconds(config)
        else:
            wait = NO_BOT_RETRY_HOURS * 3600
        cursor.execute(
            "UPDATE llm_reactivity_player_state SET next_memory_at = "
            "NOW() + INTERVAL %s SECOND WHERE player_guid = %s",
            (wait, guid),
        )
    db.commit()


# ------------------------------------------------------------
# Gifts
# ------------------------------------------------------------

def fits_class(item: Dict, class_name: str) -> bool:
    """Class fit from the gift tables: mana items for mana users, stats
    and weapon boosts for the classes that use them."""
    category = item['cat']
    note = item.get('note', '')
    name = item['name']
    if category == 'mana':
        return class_name in MANA_CLASSES
    if category == 'scroll':
        if 'Strength' in name:
            return class_name in _STRENGTH_CLASSES
        if 'Agility' in name:
            return class_name in _AGILITY_CLASSES
        if 'Intellect' in name or 'Spirit' in name:
            return class_name in _CASTERS
        return True
    if category == 'elixir':
        if 'Strength' in note:
            return class_name in _STRENGTH_CLASSES
        if 'Agility' in note:
            return class_name in _AGILITY_CLASSES
        if any(
            word in note for word in (
                'Intellect', 'Spell power', 'Mana regeneration', 'Spirit',
            )
        ):
            return class_name in _CASTERS
        return True
    if category == 'weapon':
        if note in ('Spell power', 'Mana regeneration'):
            return class_name in _CASTERS
        return class_name not in ('Mage', 'Warlock', 'Priest')
    return True


def _knows_pet(db, guid: int, entry: int) -> bool:
    cursor = db.cursor()
    cursor.execute(
        "SELECT 1 FROM character_spell s "
        "JOIN acore_world.item_template t ON t.spellid_2 = s.spell "
        "WHERE s.guid = %s AND t.entry = %s LIMIT 1",
        (guid, entry),
    )
    return cursor.fetchone() is not None


def _pick_green(db, level: int, class_name: str) -> Optional[Dict]:
    """A green armor piece from open-world drops the player can wear."""
    subclasses = _ARMOR_SUBCLASSES.get(class_name)
    if not subclasses or level < 10:
        return None
    marks = ','.join(['%s'] * len(subclasses))
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT t.entry, t.name FROM acore_world.item_template t "
        "JOIN acore_world.reference_loot_template r ON r.Item = t.entry "
        "WHERE t.Quality = 2 AND t.bonding = 2 AND t.class = 4 "
        f"AND t.subclass IN ({marks}) "
        "AND t.RequiredLevel BETWEEN %s AND %s "
        "ORDER BY RAND() LIMIT 1",
        (*subclasses, max(1, level - 5), level),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {'entry': int(row['entry']), 'name': row['name'], 'count': 1}


def _usable_at(db, entry: int, level: int) -> bool:
    """The tables hold stock levels; a mod may raise them. A gift the
    player cannot use yet is no gift, so the live item decides."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT RequiredLevel FROM acore_world.item_template "
        "WHERE entry = %s",
        (entry,),
    )
    row = cursor.fetchone()
    return bool(row) and int(row[0]) <= level


def pick_common_gift(
    db, guid: int, level: int, class_name: str
) -> Tuple[Optional[Dict], str, bool]:
    """A gift for this level and class: (item, note, is_pet). Each kind
    of gift is equally likely, however long its table."""
    by_category = {}
    for item in gifts()['common']:
        if item['min'] <= level <= item['until'] and fits_class(
            item, class_name
        ):
            by_category.setdefault(item['cat'], []).append(item)
    by_category['green'] = []

    categories = list(by_category)
    random.shuffle(categories)
    for category in categories:
        if category == 'green':
            green = _pick_green(db, level, class_name)
            if green:
                return green, '', False
            continue
        pool = by_category[category]
        common = [i for i in pool if 'gift' not in i.get('note', '')]
        if common and random.random() >= _PRECIOUS_CHANCE:
            pool = common
        random.shuffle(pool)
        for item in pool:
            if not _usable_at(db, item['id'], level):
                continue
            if category == 'pet' and _knows_pet(db, guid, item['id']):
                continue
            count = random.randint(*_STACKS.get(category, (1, 1)))
            return (
                {'entry': item['id'], 'name': item['name'],
                 'count': count},
                item.get('note', ''),
                category == 'pet',
            )
    return None, '', False


# ------------------------------------------------------------
# Writing
# ------------------------------------------------------------

def _query_letter(
    client, config, prompt: str, label: str
) -> Optional[Tuple[str, str]]:
    limits = _limits(config)
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max(600, limits['body_chars']),
        label=label,
        response_contract=ResponseContract('letter'),
    )
    if not response:
        return None
    start = response.find('{')
    end = response.rfind('}')
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(response[start:end + 1])
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    subject = clamp_subject(
        data.get('subject'), limits['subject_chars']
    )
    body = clamp_body(
        clean_text(data.get('body')), limits['body_chars']
    )
    if not subject or not body:
        return None
    return subject, body


def _write_deed_letter(db, client, config, letter, recipient):
    row = letter_by_key(letter['kind'], letter['letter_key'])
    if not row:
        return None
    context = json.loads(letter.get('context') or '{}')
    sender = sender_for(
        row, letter['team'], int(context.get('trigger_id', 0) or 0)
    )
    if not sender:
        return None
    items = row['gift']['items']
    named_items = _localized_gifts(db, items)
    hint = (
        f"News from {row['zone']}" if letter['kind'] == 'quest' else ''
    )
    prompt = deed_letter_prompt(
        sender, recipient, row, named_items, _limits(config),
        subject_hint=hint,
    )
    text = _query_letter(
        client, config, prompt, f"letter_{letter['kind']}"
    )
    if not text:
        return None
    return (*text, 'creature', sender['entry'], items)


def _localized_gifts(db, items: List[Dict]) -> List[Dict]:
    """Copies for the prompt, named as the mail shows them in the
    configured language. The stored items stay as they are."""
    return [
        {
            **item,
            'name': localize_item_name(
                db, item['name'], item.get('entry')
            ),
        }
        for item in items
    ]


def _bot_profile(db, bot_guid: int) -> Dict:
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT c.name, c.race, c.class, c.gender, c.level, "
        "i.trait1, i.trait2, i.trait3, i.tone, i.backstory "
        "FROM characters c "
        "LEFT JOIN llm_bot_identities i ON i.bot_guid = c.guid "
        "WHERE c.guid = %s",
        (bot_guid,),
    )
    return cursor.fetchone() or {}


def _memory_header(profile: Dict, config) -> str:
    mode = get_chatter_mode(config)
    header = build_player_identity(
        profile['name'],
        get_race_name(int(profile['race'])),
        get_class_name(int(profile['class'])),
        profile.get('level'),
        get_gender_label(int(profile['gender'])),
        mode,
    )
    traits = [
        trait for trait in (
            profile.get('trait1'),
            profile.get('trait2'),
            profile.get('trait3'),
        ) if trait
    ]
    lines = [header]
    if traits:
        lines.append("Your personality: " + ', '.join(traits))
    if profile.get('tone'):
        lines.append(f"Your tone: {profile['tone']}")
    if is_roleplay(mode) and profile.get('backstory'):
        lines.append(f"Your background: {profile['backstory']}")
    return '\n'.join(lines)


def _write_memory_letter(db, client, config, letter, recipient):
    bot_guid = int(letter['sender_id'])
    if bot_guid in _group_mates(db, recipient['guid']):
        return None
    cursor = db.cursor()
    cursor.execute(
        "SELECT memory FROM llm_bot_memories "
        "WHERE bot_guid = %s AND player_guid = %s AND active = 1",
        (bot_guid, recipient['guid']),
    )
    memories = [row[0] for row in cursor.fetchall()]
    profile = _bot_profile(db, bot_guid)
    if not memories or not profile:
        return None
    item, note, is_pet = pick_common_gift(
        db, recipient['guid'], recipient['level'], recipient['class']
    )
    if not item:
        return None
    prompt = memory_letter_prompt(
        _memory_header(profile, config), recipient,
        random.choice(memories), _localized_gifts(db, [item]), note,
        is_pet,
        is_roleplay(get_chatter_mode(config)), _limits(config),
    )
    text = _query_letter(client, config, prompt, 'letter_memory')
    if not text:
        return None
    return (*text, 'bot', bot_guid, [item])


def _write_starter_letter(db, client, config, letter, recipient):
    context = json.loads(letter['context'])
    profession = context['profession']
    starter = gifts()['starters'][profession]
    named = {
        **starter, 'items': _localized_gifts(db, starter['items']),
    }
    prompt = starter_letter_prompt(
        context['trainer'], profession, recipient, named,
        _limits(config),
    )
    text = _query_letter(client, config, prompt, 'letter_starter')
    if not text:
        return None
    return (
        *text, 'creature', int(letter['sender_id']), starter['items'],
    )


def _write_profession_letter(db, client, config, letter, recipient):
    context = json.loads(letter['context'])
    bundle = context['bundle']
    named = {**bundle, 'items': _localized_gifts(db, bundle['items'])}
    prompt = profession_letter_prompt(
        context['trainer'], context['profession'], recipient, named,
        _limits(config),
    )
    text = _query_letter(client, config, prompt, 'letter_profession')
    if not text:
        return None
    return (
        *text, 'creature', int(letter['sender_id']), bundle['items'],
    )


_WRITERS = {
    'dungeon': _write_deed_letter,
    'raid': _write_deed_letter,
    'quest': _write_deed_letter,
    'memory': _write_memory_letter,
    'starter': _write_starter_letter,
    'profession': _write_profession_letter,
}


def _claim_letter(db, letter_id: int) -> bool:
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_reactivity_letters "
        "SET status = 'generating', attempts = attempts + 1 "
        "WHERE id = %s AND status = 'scheduled'",
        (letter_id,),
    )
    db.commit()
    return cursor.rowcount == 1


def _letter_failed(db, letter: Dict) -> None:
    cursor = db.cursor()
    if int(letter['attempts']) + 1 >= MAX_ATTEMPTS:
        cursor.execute(
            "UPDATE llm_reactivity_letters SET status = 'failed' "
            "WHERE id = %s",
            (letter['id'],),
        )
    else:
        cursor.execute(
            "UPDATE llm_reactivity_letters SET status = 'scheduled', "
            "not_before = NOW() + INTERVAL %s MINUTE WHERE id = %s",
            (RETRY_MINUTES, letter['id']),
        )
    db.commit()


def _write_due_letters(db, client, config) -> None:
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM llm_reactivity_letters "
        "WHERE status = 'scheduled' AND not_before <= NOW() "
        "ORDER BY not_before LIMIT %s",
        (_int(config, 'LLMChatter.Letters.BatchSize', 3),),
    )
    for letter in cursor.fetchall():
        if not _claim_letter(db, letter['id']):
            continue
        recipient = _character(db, int(letter['player_guid']))
        written = None
        try:
            if recipient:
                written = _WRITERS[letter['kind']](
                    db, client, config, letter, recipient
                )
        except Exception:
            logger.error(
                "reactivity letter %s failed", letter['id'],
                exc_info=True,
            )
        if not written:
            _letter_failed(db, letter)
            continue
        subject, body, sender_type, sender_id, items = written
        cursor.execute(
            "UPDATE llm_reactivity_letters SET status = 'ready', "
            "subject = %s, body = %s, sender_type = %s, "
            "sender_id = %s, items = %s WHERE id = %s",
            (
                subject, body, sender_type, sender_id,
                items_spec(items), letter['id'],
            ),
        )
        db.commit()


def _recover_stuck_letters(db) -> None:
    """Only this pass generates, so a row left generating is from a
    stopped bridge. One left sending may have reached the mailbox, so
    it is retired, never resent."""
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_reactivity_letters SET status = 'scheduled' "
        "WHERE status = 'generating'"
    )
    cursor.execute(
        "UPDATE llm_reactivity_letters SET status = 'failed' "
        "WHERE status = 'sending' "
        "AND updated_at < NOW() - INTERVAL %s MINUTE",
        (STUCK_SENDING_MINUTES,),
    )
    db.commit()


def process_reactivity(db, client, config) -> None:
    """One background pass over deeds, letters and rumor voicings."""
    if not letters_enabled(config) and not rumors_enabled(config):
        return
    _drain_inbox(db, config)
    if letters_enabled(config):
        _recover_stuck_letters(db)
        _schedule_memory_letters(db, config)
        _write_due_letters(db, client, config)
    if rumors_enabled(config):
        settle_voicings(db, config)
