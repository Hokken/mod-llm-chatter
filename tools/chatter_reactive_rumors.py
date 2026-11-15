"""Reactivity rumors: what friendly NPCs say about the player's deeds.

A deed unlocks a rumor when the bridge reads it. A new rumor is fresh:
it is told at the first chance, in the zones it belongs to, until it has
been heard FreshVoicings times, and then it joins the rest. Deeds from
before this feature count too, read from the character's own records,
at normal priority.

Only lines that reached a player count as heard, so a voicing is
settled against the delivered message rows, not at generation.
"""

import logging
import random
from typing import Dict, List, Optional, Set

from chatter_instance_context import build_instance_context
from chatter_reactivity_data import (
    faction_allows,
    rumor_by_key,
    rumors,
    weighted_choice,
)

logger = logging.getLogger(__name__)

# Tables give only achievements a Frequency; this is the middle of it.
DEFAULT_FREQUENCY = 5
VOICING_TIMEOUT_MINUTES = 60

_FRIENDLY = ('friendly', 'neutral')

_CHAMPION_CITIES = {
    2777: 'Darnassus', 2778: 'the Exodar', 2779: 'Gnomeregan',
    2780: 'Ironforge', 2781: 'Stormwind', 2783: 'Orgrimmar',
    2784: "Sen'jin", 2785: 'Silvermoon City', 2786: 'Thunder Bluff',
    2787: 'the Undercity',
}
_ALDOR_FACTION = 932
_SCRYERS_FACTION = 934


class RumorTopic(str):
    """A topic seed that is a rumor about the nearby player."""

    kind: str
    key: str
    addressed: bool
    notes: str


def _int(config, key, default) -> int:
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _type_enabled(config, kind: str) -> bool:
    section = {
        'achievement': 'Achievements',
        'quest': 'Quests',
        'dungeon': 'Dungeons',
    }[kind]
    return str(config.get(
        f'LLMChatter.Rumors.{section}.Enable', '1'
    )).strip() == '1'


def rumor_zones(row: Dict, kind: str, team: str) -> List[int]:
    """Zones the rumor is told in. [0] means anywhere; [] means this
    faction has no such rumor."""
    if kind == 'achievement':
        return [0]
    if kind == 'quest':
        return row['zones']
    return row['zones'].get(team.lower(), [])


def _allowed(row: Dict, kind: str, team: str) -> bool:
    return kind == 'dungeon' or faction_allows(row, team)


def unlock_rumor(db, config, guid: int, team: str, found) -> bool:
    """Record a new rumor as fresh. Earning a second achievement for
    the same dungeon does not make it fresh again."""
    kind, row = found
    if not _type_enabled(config, kind) or not _allowed(row, kind, team):
        return False
    zones = rumor_zones(row, kind, team)
    if not zones:
        return False
    cursor = db.cursor()
    cursor.execute(
        "INSERT IGNORE INTO llm_reactivity_rumors "
        "(player_guid, kind, rumor_key, fresh) VALUES (%s, %s, %s, 1)",
        (guid, kind, row['key']),
    )
    if cursor.rowcount:
        cursor.executemany(
            "INSERT IGNORE INTO llm_reactivity_fresh_rumor_zones "
            "(player_guid, zone_id, kind, rumor_key) "
            "VALUES (%s, %s, %s, %s)",
            [(guid, zone, kind, row['key']) for zone in zones],
        )
    db.commit()
    return bool(cursor.rowcount)


def _team(db, guid: int) -> str:
    cursor = db.cursor()
    cursor.execute(
        "SELECT team FROM llm_reactivity_player_state "
        "WHERE player_guid = %s",
        (guid,),
    )
    row = cursor.fetchone()
    return row[0] if row else ''


def _fresh_rumors(db, guid: int, zone_id: int) -> List:
    cursor = db.cursor()
    cursor.execute(
        "SELECT kind, rumor_key "
        "FROM llm_reactivity_fresh_rumor_zones "
        "WHERE player_guid = %s AND zone_id IN (0, %s)",
        (guid, zone_id),
    )
    return list(cursor.fetchall())


def _earned_achievements(db, guid: int) -> Set[int]:
    cursor = db.cursor()
    cursor.execute(
        "SELECT achievement FROM character_achievement "
        "WHERE guid = %s",
        (guid,),
    )
    return {int(row[0]) for row in cursor.fetchall()}


def _rewarded_quests(db, guid: int) -> Set[int]:
    cursor = db.cursor()
    cursor.execute(
        "SELECT quest FROM character_queststatus_rewarded "
        "WHERE guid = %s",
        (guid,),
    )
    return {int(row[0]) for row in cursor.fetchall()}


def _recently_voiced(db, config, guid: int) -> Set:
    cursor = db.cursor()
    cursor.execute(
        "SELECT kind, rumor_key FROM llm_reactivity_rumors "
        "WHERE player_guid = %s "
        "AND last_voiced_at > NOW() - INTERVAL %s MINUTE",
        (
            guid,
            _int(config, 'LLMChatter.Rumors.RepeatCooldownMinutes', 180),
        ),
    )
    return {(row[0], row[1]) for row in cursor.fetchall()}


def _standard_options(
    db, config, guid: int, team: str, zone_id: int
) -> List:
    """Every deed of this player that may be told here, weighted."""
    voiced = _recently_voiced(db, config, guid)
    earned = _earned_achievements(db, guid)
    tables = rumors()
    options = []

    def add(kind, row, weight):
        if (kind, row['key']) not in voiced:
            options.append(((kind, row), weight))

    if _type_enabled(config, 'achievement'):
        for row in tables['achievements']:
            if faction_allows(row, team) and earned.intersection(
                row['ids']
            ):
                add('achievement', row, row['frequency'])
    if _type_enabled(config, 'dungeon'):
        for row in tables['dungeons']:
            if zone_id in rumor_zones(
                row, 'dungeon', team
            ) and earned.intersection(row['achievements']):
                add('dungeon', row, DEFAULT_FREQUENCY)
    if _type_enabled(config, 'quest'):
        local = [
            row for row in tables['quests']
            if zone_id in row['zones'] and faction_allows(row, team)
        ]
        if local:
            rewarded = _rewarded_quests(db, guid)
            for row in local:
                if rewarded.intersection(row['quests']):
                    add('quest', row, DEFAULT_FREQUENCY)
    return options


def _order_of_shattrath(db, guid: int) -> str:
    cursor = db.cursor()
    cursor.execute(
        "SELECT faction, standing FROM character_reputation "
        "WHERE guid = %s AND faction IN (%s, %s)",
        (guid, _ALDOR_FACTION, _SCRYERS_FACTION),
    )
    standing = {int(row[0]): int(row[1]) for row in cursor.fetchall()}
    if not standing:
        return ''
    best = max(standing, key=standing.get)
    return 'the Aldor' if best == _ALDOR_FACTION else 'the Scryers'


def _achievement_notes(db, row: Dict, guid: int, team: str) -> str:
    """The row's notes, with the facts they ask for filled in."""
    key = row['key']
    notes = row.get('notes') or ''
    if key == 'shattrath_divided':
        order = _order_of_shattrath(db, guid)
        return f"The hero serves {order}. {notes}" if order else notes
    if key == 'champion_of_a_city':
        earned = _earned_achievements(db, guid)
        cities = [
            city for achievement, city in _CHAMPION_CITIES.items()
            if achievement in earned
        ]
        if cities:
            return f"The hero rides for {random.choice(cities)}."
        return ''
    if key == 'the_diplomat':
        people = 'Kurenai' if team == 'Alliance' else "Mag'har"
        return f"The hero won over the {people}."
    if key == 'the_winds_of_the_north':
        host = (
            'the Alliance Vanguard' if team == 'Alliance'
            else 'the Horde Expedition'
        )
        return f"The hero serves {host}."
    return notes


def _name_hero(text: str, player_name: str) -> str:
    return text.replace('The hero', player_name).replace(
        'the hero', player_name
    )


def _render(
    db, kind: str, row: Dict, guid, team, player_name,
    addressed_chance: int = 50,
):
    if kind == 'achievement':
        addressed = True
        text = row['description']
        notes = _achievement_notes(db, row, guid, team)
    else:
        addressed = random.random() < addressed_chance / 100
        text = random.choice(
            row['addressed'] if addressed else row['recounted']
        )
        notes = ''
    if addressed:
        text = _name_hero(text, player_name)
        notes = _name_hero(notes, player_name)
    topic = RumorTopic(text)
    topic.kind = kind
    topic.key = row['key']
    topic.addressed = addressed
    topic.notes = notes
    return topic


def _speakers_may_tell(speakers: List[Dict]) -> bool:
    return bool(speakers) and all(
        speaker.get('is_npc')
        and str(speaker.get('disposition') or '').lower() in _FRIENDLY
        for speaker in speakers
    )


def pick_rumor(
    db, config, extra: Dict, speakers: List[Dict]
) -> Optional[RumorTopic]:
    """A rumor for this scene, or None for ordinary small talk."""
    if str(config.get('LLMChatter.Rumors.Enable', '1')).strip() != '1':
        return None
    guid = int(extra.get('player_guid', 0) or 0)
    zone_id = int(extra.get('zone_id', 0) or 0)
    if not guid or not zone_id or not _speakers_may_tell(speakers):
        return None
    # A scene with its own subject keeps it.
    if extra.get('fight_scene') or isinstance(
        extra.get('screenshot_observation'), dict
    ):
        return None
    if build_instance_context(extra)['is_instance']:
        return None
    try:
        team = _team(db, guid)
        if not team:
            return None
        chosen = None
        fresh = _fresh_rumors(db, guid, zone_id)
        if fresh:
            kind, key = random.choice(fresh)
            row = rumor_by_key(kind, key)
            chosen = (kind, row) if row else None
        elif random.randint(1, 100) <= _int(
            config, 'LLMChatter.Rumors.Chance', 15
        ):
            chosen = weighted_choice(
                _standard_options(db, config, guid, team, zone_id)
            )
        if not chosen:
            return None
        return _render(
            db, chosen[0], chosen[1], guid, team,
            extra.get('player_name') or 'the stranger',
            max(0, min(100, _int(
                config, 'LLMChatter.Rumors.AddressedChance', 50
            ))),
        )
    except Exception:
        logger.error("rumor selection failed", exc_info=True)
        return None


def rumor_prompt_lines(topic: RumorTopic, player_name: str) -> List[str]:
    """What the speaker is told about the rumor."""
    if topic.addressed:
        lines = [
            f"You recognise {player_name}, who is standing here, and "
            "you have heard what they did. Speak to them about it.",
            f"What you heard: {topic}",
        ]
    else:
        lines = [
            "Pass on a piece of local news you have heard. You do not "
            "know who was behind it and do not link it to anyone here.",
            f"What you heard: {topic}",
        ]
    if topic.notes:
        lines.append(f"Keep in mind: {topic.notes}")
    lines.append(
        "Retell it in your own words, as talk among people who live "
        "here, and react to it as this character would."
    )
    return lines


def record_voicing(db, event_id: int, guid: int, topic) -> None:
    """Note a rumor queued for speech; it counts once delivered."""
    if not isinstance(topic, RumorTopic):
        return
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO llm_reactivity_rumor_voicings "
        "(event_id, player_guid, kind, rumor_key) "
        "VALUES (%s, %s, %s, %s)",
        (event_id, guid, topic.kind, topic.key),
    )
    db.commit()


def _count_voicing(db, config, row: Dict) -> None:
    guid, kind, key = (
        row['player_guid'], row['kind'], row['rumor_key']
    )
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO llm_reactivity_rumors "
        "(player_guid, kind, rumor_key, fresh, voiced_count, "
        "last_voiced_at) VALUES (%s, %s, %s, 0, 1, NOW()) "
        "ON DUPLICATE KEY UPDATE voiced_count = voiced_count + 1, "
        "last_voiced_at = NOW()",
        (guid, kind, key),
    )
    limit = _int(config, 'LLMChatter.Rumors.FreshVoicings', 2)
    cursor.execute(
        "UPDATE llm_reactivity_rumors SET fresh = 0 "
        "WHERE player_guid = %s AND kind = %s AND rumor_key = %s "
        "AND voiced_count >= %s",
        (guid, kind, key, limit),
    )
    if cursor.rowcount:
        cursor.execute(
            "DELETE FROM llm_reactivity_fresh_rumor_zones "
            "WHERE player_guid = %s AND kind = %s AND rumor_key = %s",
            (guid, kind, key),
        )


def settle_voicings(db, config) -> None:
    """Count voicings whose lines arrived; drop the ones that will
    never arrive."""
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT v.id, v.player_guid, v.kind, v.rumor_key, "
        "v.created_at < NOW() - INTERVAL %s MINUTE AS expired, "
        # A claimed row is delivered = 1 before it is sent; only
        # delivered_at marks a line that reached the player.
        "COALESCE(SUM(m.delivered = 1 AND m.delivered_at IS NOT NULL "
        "AND m.drop_reason IS NULL), 0) "
        "AS heard "
        "FROM llm_reactivity_rumor_voicings v "
        "LEFT JOIN llm_chatter_messages m ON m.event_id = v.event_id "
        "GROUP BY v.id",
        (VOICING_TIMEOUT_MINUTES,),
    )
    for row in cursor.fetchall():
        if row['heard']:
            _count_voicing(db, config, row)
        elif not row['expired']:
            continue
        cursor.execute(
            "DELETE FROM llm_reactivity_rumor_voicings WHERE id = %s",
            (row['id'],),
        )
    db.commit()
