"""Persistent profiles shared by Party, General and Guild.

Generation is explicit, never a side effect of candidate/persona lookup.
Conditional writes protect addon edits made while the provider is running.
"""

import functools
import logging
import random
import threading
import time
from collections import OrderedDict

from chatter_constants import PERSONALITY_TRAITS
from chatter_llm import get_llm_client
from chatter_mode import is_roleplay
from chatter_shared import (
    call_llm, get_class_name, get_race_name, get_gender_label, get_chatter_mode,
)

logger = logging.getLogger(__name__)

# Striped locks bound storage independently of the number of world bots.
_locks = tuple(threading.RLock() for _ in range(64))
_failures = OrderedDict()
_failures_lock = threading.Lock()
_FAILURE_CACHE_MAX = 2048
_FIELDS = ('trait1', 'trait2', 'trait3', 'tone', 'backstory')


def config_int(config, key, default, minimum=0, maximum=None):
    try:
        value = int((config or {}).get(key, default))
    except (TypeError, ValueError):
        value = default
    value = max(minimum, value)
    return min(maximum, value) if maximum is not None else value


def _serialized(fn):
    @functools.wraps(fn)
    def wrapped(db, config, bot_guid, *args, **kwargs):
        with _locks[int(bot_guid) % len(_locks)]:
            return fn(db, config, bot_guid, *args, **kwargs)
    return wrapped


def _snapshot(row):
    return tuple((row or {}).get(k) for k in _FIELDS) + (
        (row or {}).get('identity_version'),
    )


def _cooling_down(key):
    now = time.monotonic()
    with _failures_lock:
        expires = _failures.get(key, 0)
        if expires <= now:
            _failures.pop(key, None)
            return False
        return True


def _failed(key, config):
    ttl = config_int(config, 'LLMChatter.Profile.RetrySeconds', 300, 1)
    with _failures_lock:
        _failures[key] = time.monotonic() + ttl
        _failures.move_to_end(key)
        while len(_failures) > _FAILURE_CACHE_MAX:
            _failures.popitem(last=False)


def _read_identity(db, bot_guid):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            'SELECT trait1, trait2, trait3, role, tone, farewell_msg, '
            'backstory, identity_version FROM llm_bot_identities '
            'WHERE bot_guid = %s', (bot_guid,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def _read_group(db, bot_guid, group_id=None):
    cursor = db.cursor(dictionary=True)
    try:
        clause = ' AND group_id = %s' if group_id else ''
        args = (bot_guid, group_id) if group_id else (bot_guid,)
        cursor.execute(
            'SELECT group_id, trait1, trait2, trait3, tone, backstory '
            'FROM llm_group_bot_traits WHERE bot_guid = %s' + clause
            + ' ORDER BY assigned_at DESC LIMIT 1', args,
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def _new_traits():
    categories = random.sample(list(PERSONALITY_TRAITS), 3)
    return [random.choice(PERSONALITY_TRAITS[c]) for c in categories]


def _has(value):
    return bool(str(value or '').strip())


def _rollback(db):
    try:
        db.rollback()
    except Exception:
        logger.debug('Profile rollback failed', exc_info=True)


def _sync_existing_field(db, bot_guid, group_id, field, value, traits):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            f'SELECT trait1, trait2, trait3, {field} '
            'FROM llm_bot_identities WHERE bot_guid=%s FOR UPDATE',
            (bot_guid,),
        )
        current = cursor.fetchone()
        if (not current or current.get(field) != value
                or tuple(current.get(k) for k in _FIELDS[:3]) != tuple(traits)):
            db.commit()
            return
        clause = ' AND group_id=%s' if group_id else ''
        cursor.execute(
            f'UPDATE llm_group_bot_traits SET {field}=%s '
            'WHERE bot_guid=%s AND trait1 <=> %s AND trait2 <=> %s '
            f'AND trait3 <=> %s AND ({field} IS NULL OR TRIM({field})=\'\')'
            + clause,
            (value, bot_guid, *traits, *((group_id,) if group_id else ())),
        )
        db.commit()
    finally:
        cursor.close()


@_serialized
def check_or_create_bot_identity(db, config, bot_guid, bot_name):
    """Create/fill identity idempotently, preserving populated fields."""
    if not config:
        return None
    version = config_int(config, 'LLMChatter.Memory.IdentityVersion', 1)
    failure_key = (bot_guid, 'identity', version)
    try:
        # A preceding candidate lookup may have opened a read snapshot before
        # this worker acquired its bot lock.
        db.commit()
        row = _read_identity(db, bot_guid)
        current = row and int(row['identity_version']) == version
        if current and all(_has(row.get(k)) for k in _FIELDS[:3]):
            return row
        if _cooling_down(failure_key):
            return row if current else None
        group = _read_group(db, bot_guid) if not row else None
        traits = _new_traits()
        source = row if current else group or {}
        values = [source.get(k) or traits[i]
                  for i, k in enumerate(_FIELDS[:3])]
        # Whitespace-only legacy fields count as absent as well.
        values = [v if _has(v) else traits[i] for i, v in enumerate(values)]
        cursor = db.cursor()
        try:
            if row:
                bump = not current
                cursor.execute(
                    'UPDATE llm_bot_identities SET trait1=%s, trait2=%s, '
                    'trait3=%s, tone=%s, backstory=%s, farewell_msg=%s, '
                    'identity_version=%s WHERE bot_guid=%s AND '
                    'trait1 <=> %s AND trait2 <=> %s AND trait3 <=> %s '
                    'AND tone <=> %s AND backstory <=> %s '
                    'AND identity_version <=> %s',
                    (*values, None if bump else row.get('tone'),
                     None if bump else row.get('backstory'),
                     None if bump else row.get('farewell_msg'), version,
                     bot_guid, *_snapshot(row)),
                )
                changed = cursor.rowcount > 0
                if bump and changed:
                    cursor.execute(
                        'UPDATE llm_group_bot_traits SET trait1=%s, '
                        'trait2=%s, trait3=%s, tone=NULL, backstory=NULL '
                        'WHERE bot_guid=%s AND trait1 <=> %s '
                        'AND trait2 <=> %s AND trait3 <=> %s',
                        (*values, bot_guid, *[row.get(k) for k in _FIELDS[:3]]),
                    )
            else:
                cursor.execute(
                    'INSERT IGNORE INTO llm_bot_identities '
                    '(bot_guid, bot_name, trait1, trait2, trait3, tone, '
                    'backstory, identity_version) '
                    'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                    (bot_guid, bot_name, *values, source.get('tone'),
                     source.get('backstory'), version),
                )
                changed = cursor.rowcount > 0
            db.commit()
        finally:
            cursor.close()
        result = _read_identity(db, bot_guid)
        if result and changed and not current:
            result['reason'] = 'version_bump' if row else 'new'
        return result
    except Exception:
        _rollback(db)
        _failed(failure_key, config)
        logger.warning('Could not ensure identity for %s', bot_name,
                       exc_info=True)
        return None


def _generate_field(db, config, bot_guid, group_id, bot_name, field,
                    traits, prompt, token_limit, char_limit,
                    expected_tone=None):
    """Persist derived text only against the exact generation snapshot."""
    from chatter_persona import fallback_tone
    fallback = (fallback_tone(bot_guid, bot_name, 'roleplay')
                if field == 'tone' else None)
    key = None
    try:
        row = _read_identity(db, bot_guid)
        group = _read_group(db, bot_guid, group_id) if group_id else None
        if group and _has(group.get(field)):
            return group[field]
        if row and _has(row.get(field)):
            # Do not copy a different session's derived voice onto these traits.
            if tuple(row.get(k) for k in _FIELDS[:3]) == tuple(traits):
                _sync_existing_field(
                    db, bot_guid, group_id, field, row[field], traits,
                )
                return row[field]
        if not row:
            row = check_or_create_bot_identity(db, config, bot_guid, bot_name)
        if not row:
            return fallback
        if (tuple(row.get(k) for k in _FIELDS[:3]) != tuple(traits)
                and not group):
            return fallback
        source = group or row
        if (field == 'backstory' and _has(source.get('tone'))
                and source['tone'] != expected_tone):
            return source.get('backstory') or fallback
        key = (bot_guid, field, _snapshot(row),
               tuple(traits), group_id)
        if _cooling_down(key):
            return fallback
        # End the read transaction before waiting on the network.
        db.commit()
        value = call_llm(
            get_llm_client(config), prompt, config,
            max_tokens_override=token_limit,
            context=f'{field}:{bot_name}', label=f'bot_{field}',
        )
        value = str(value or '').strip().strip('"').strip()
        if field == 'tone':
            value = value.rstrip('.')
        if not value:
            _failed(key, config)
            return fallback
        value = value[:char_limit]
        # Lock only for the short persistence transaction, never the LLM call.
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                'SELECT trait1, trait2, trait3, tone, backstory, '
                'identity_version FROM llm_bot_identities '
                'WHERE bot_guid=%s FOR UPDATE', (bot_guid,),
            )
            latest = cursor.fetchone()
            if _snapshot(latest) != _snapshot(row):
                db.commit()
                return (latest or {}).get(field) or fallback
            same_traits = tuple(row.get(k) for k in _FIELDS[:3]) == tuple(traits)
            if same_traits:
                cursor.execute(
                    f'UPDATE llm_bot_identities SET {field}=%s '
                    'WHERE bot_guid=%s', (value, bot_guid),
                )
            # Memory-disabled Party may own distinct session traits. Its
            # generated voice belongs to that session, not the persistent row.
            clause = ' AND group_id=%s' if group_id else ''
            args = (group_id,) if group_id else ()
            extra_guard = ''
            if field == 'backstory':
                extra_guard = ' AND tone <=> %s'
                args = ((group or row).get('tone'), *args)
            cursor.execute(
                f'UPDATE llm_group_bot_traits SET {field}=%s '
                'WHERE bot_guid=%s AND trait1 <=> %s '
                'AND trait2 <=> %s AND trait3 <=> %s '
                f"AND ({field} IS NULL OR TRIM({field})='')"
                + extra_guard + clause,
                (value, bot_guid, *traits, *args),
            )
            db.commit()
        finally:
            cursor.close()
        winner = (_read_group(db, bot_guid, group_id) if group_id
                  else _read_identity(db, bot_guid))
        return (winner or {}).get(field) or fallback
    except Exception:
        _rollback(db)
        if key is not None:
            _failed(key, config)
        logger.warning('Could not generate %s for %s', field, bot_name,
                       exc_info=True)
        return fallback


def ensure_bot_profile(db, client, config, bot_guid, bot_name=''):
    """Prepare one already selected speaker; persona lookup stays read-only."""
    from chatter_persona import resolve_persona
    mode = get_chatter_mode(config)
    if not is_roleplay(mode):
        return resolve_persona(db, bot_guid, bot_name, mode)
    try:
        db.commit()
        row = _read_identity(db, bot_guid)
        group = _read_group(db, bot_guid)
        version = config_int(config, 'LLMChatter.Memory.IdentityVersion', 1)
        fields = _FIELDS if config_int(
            config, 'LLMChatter.Backstory.Enable', 1,
        ) else _FIELDS[:-1]
        if (row and int(row.get('identity_version', 0)) == version
                and all(_has(row.get(k)) for k in fields)
                and all(_has((group or row).get(k)) for k in fields)):
            return resolve_persona(db, bot_guid, bot_name, mode)
    except Exception:
        _rollback(db)
    # Only incomplete profiles wait for a stripe shared with another bot.
    # Creation rechecks its reads after acquiring the lock.
    with _locks[int(bot_guid) % len(_locks)]:
        try:
            row = check_or_create_bot_identity(db, config, bot_guid, bot_name)
            if row:
                group = _read_group(db, bot_guid)
                traits = [((group or {}).get(k) or row.get(k))
                          for k in _FIELDS[:3]]
                source = group or row
                needs_tone = not _has(source.get('tone'))
                needs_story = (config_int(config, 'LLMChatter.Backstory.Enable', 1)
                               and not _has(source.get('backstory')))
                if needs_tone or needs_story:
                    cursor = db.cursor(dictionary=True)
                    try:
                        cursor.execute('SELECT name, class, race, gender '
                                       'FROM characters WHERE guid=%s', (bot_guid,))
                        info = cursor.fetchone()
                    finally:
                        cursor.close()
                    if info:
                        name = info['name']
                        klass = get_class_name(info['class'])
                        race = get_race_name(info['race'])
                        tone = (group or {}).get('tone') or row.get('tone')
                        if needs_tone:
                            tone = _generate_bot_tone(
                                db, config, bot_guid, (group or {}).get('group_id'),
                                name, klass, race, traits)
                        if needs_story:
                            _generate_bot_backstory(
                                db, config, bot_guid, (group or {}).get('group_id'),
                                name, klass, race, traits, tone, get_gender_label(info.get('gender', 0)))
        except Exception:
            _rollback(db)
            logger.warning('Profile preparation failed for %s', bot_guid,
                           exc_info=True)
        return resolve_persona(db, bot_guid, bot_name, mode)


def prepare_channel_persona(db, client, config, bot_guid, bot_name,
                            channel, prepared=None):
    """Ensure then independently sample each speaker once per exchange."""
    from chatter_persona import sample_channel_backstory
    key = int(bot_guid)
    if prepared is not None and key in prepared:
        return prepared[key]
    persona = ensure_bot_profile(db, client, config, key, bot_name)
    persona = sample_channel_backstory(config, persona, channel)
    if prepared is not None:
        prepared[key] = persona
    return persona


def prepare_guild_speakers(db, client, config, participants, prepared=None,
                           channel='guild'):
    """Copy selected Guild participants with sampled, canonical profiles."""
    result = []
    for participant in participants:
        persona = prepare_channel_persona(
            db, client, config, participant['guid'], participant['name'],
            channel, prepared,
        )
        speaker = dict(participant['speaker'])
        speaker.update(traits=list(persona.traits), tone=persona.tone,
                       backstory=persona.backstory, mood=persona.mood)
        result.append(dict(participant, speaker=speaker))
    return result


@_serialized
def _generate_bot_tone(
    db, config, bot_guid, group_id,
    bot_name, bot_class, bot_race, traits,
):
    # Build LLM prompt
    trait_str = ', '.join(traits)
    prompt = (
        "You are helping define the communication "
        "style of a WoW bot character.\n\n"
        f"Bot: {bot_name} ({bot_race} {bot_class})\n"
        f"Personality traits: {trait_str}\n\n"
        "Write a short tone description (5-8 words) "
        "that captures how this character speaks.\n"
        "It must be consistent with ALL three traits "
        "— do not contradict any of them.\n"
        "Examples: \"wry, guarded, with quiet "
        "curiosity\" / \"bold and warm, prone to "
        "rambling\" / \"earnest and blunt, "
        "occasionally self-deprecating\"\n\n"
        "Respond with ONLY the tone description, "
        "no quotes, no punctuation at the end."
    )

    # Plain-string prompt — inject language rule
    # directly since this path doesn't go through
    # append_json_instruction.
    from chatter_shared import get_language_rule
    lang_rule = get_language_rule()
    if lang_rule:
        prompt += lang_rule

    return _generate_field(
        db, config, bot_guid, group_id, bot_name, 'tone',
        traits, prompt, 30, 100,
    )


@_serialized
def _generate_bot_backstory(
    db, config, bot_guid, group_id,
    bot_name, bot_class, bot_race, traits, tone, bot_gender='',
):
    if not config_int(config, 'LLMChatter.Backstory.Enable', 1):
        return None
    # Build LLM prompt
    trait_str = ', '.join(traits)
    tone_line = (
        f"\nSpeaking tone: {tone}"
        if tone else ""
    )
    gender_str = (
        f"{bot_gender} " if bot_gender else ""
    )
    prompt = (
        "You are a World of Warcraft lore writer.\n\n"
        f"Character: {bot_name}, a {gender_str}"
        f"{bot_race} {bot_class}.\n"
        f"Personality traits: {trait_str}\n"
        f"{tone_line}\n\n"
        "Write a 3-4 sentence background story for "
        "this character. Include:\n"
        "- A birthplace appropriate to their race "
        "and Warcraft lore\n"
        "- A brief mention of their parents or "
        "upbringing\n"
        "- 1-2 formative events that shaped them\n\n"
        "The story should hint at their current "
        "personality but not rigidly explain every "
        "trait. Stay consistent with Warcraft lore "
        "and the character's race/class "
        f"combination. Use {'she/her' if bot_gender == 'female' else 'he/him'} "
        "pronouns throughout.\n\n"
        "Respond with ONLY the backstory paragraph, "
        "no quotes, no character name prefix."
    )

    # Inject language rule
    from chatter_shared import get_language_rule
    lang_rule = get_language_rule()
    if lang_rule:
        prompt += lang_rule

    return _generate_field(
        db, config, bot_guid, group_id, bot_name, 'backstory',
        traits, prompt, 200, 1000, expected_tone=tone,
    )


def regenerate_missing_identity_tones(
    db, client, config, limit=3,
):
    """Backfill derived tones for bots whose traits are
    set but whose stored tone is currently NULL.

    This supports addon-driven trait edits where the
    traits are the user's input and tone is a derived
    output generated asynchronously.
    """
    if not config or int(config.get(
        'LLMChatter.Memory.Enable', 1
    )) != 1:
        return 0

    try:
        limit = max(1, int(limit))
    except (TypeError, ValueError):
        limit = 1

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.bot_guid,
               COALESCE(i.bot_name, c.name) AS bot_name,
               i.trait1, i.trait2, i.trait3,
               c.class, c.race
        FROM llm_bot_identities i
        JOIN characters c
          ON c.guid = i.bot_guid
        WHERE i.tone IS NULL
          AND i.trait1 IS NOT NULL
          AND i.trait1 != ''
          AND i.trait2 IS NOT NULL
          AND i.trait2 != ''
          AND i.trait3 IS NOT NULL
          AND i.trait3 != ''
          -- A group join clears the tone and generates a new
          -- one itself; skip bots it assigned moments ago so
          -- the two do not generate in parallel.
          AND NOT EXISTS (
              SELECT 1 FROM llm_group_bot_traits g
              WHERE g.bot_guid = i.bot_guid
                AND g.assigned_at
                    > NOW() - INTERVAL 2 MINUTE
          )
        ORDER BY i.created_at DESC, i.bot_guid DESC
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()

    generated = 0
    for row in rows:
        bot_guid = int(row.get('bot_guid') or 0)
        if not bot_guid:
            continue

        bot_name = row.get('bot_name', '') or ''
        bot_class = get_class_name(
            int(row.get('class') or 0)
        )
        bot_race = get_race_name(
            int(row.get('race') or 0)
        )
        if not bot_name or not bot_class or not bot_race:
            continue

        traits = [
            row.get('trait1', '') or '',
            row.get('trait2', '') or '',
            row.get('trait3', '') or '',
        ]
        if not all(traits):
            continue

        tone = _generate_bot_tone(
            db, config, bot_guid, None,
            bot_name, bot_class, bot_race,
            traits,
        )
        if tone:
            generated += 1
            logger.info(
                "Regenerated tone for %s (%s): %s",
                bot_name, bot_guid, tone,
            )

    return generated


@_serialized
def regenerate_bot_backstory(
    db, config, bot_guid,
):
    """Clear and regenerate backstory for a bot.

    Called by the bot_backstory_regen event handler
    when the player requests a new backstory via addon.
    """
    # Clear existing backstory
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE llm_bot_identities"
            " SET backstory = NULL"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        cursor.execute(
            "UPDATE llm_group_bot_traits"
            " SET backstory = NULL"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        db.commit()
    except Exception:
        pass

    # Fetch bot info for generation — try identity
    # table first, fall back to session traits
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.bot_guid,
               COALESCE(i.bot_name, c.name)
                   AS bot_name,
               i.trait1, i.trait2, i.trait3,
               i.tone,
               c.class, c.race, c.gender
        FROM llm_bot_identities i
        JOIN characters c
          ON c.guid = i.bot_guid
        WHERE i.bot_guid = %s
    """, (bot_guid,))
    row = cursor.fetchone()
    if not row:
        # Fall back to session traits
        cursor.execute("""
            SELECT t.bot_guid,
                   COALESCE(t.bot_name, c.name)
                       AS bot_name,
                   t.trait1, t.trait2, t.trait3,
                   t.tone,
                   c.class, c.race, c.gender
            FROM llm_group_bot_traits t
            JOIN characters c
              ON c.guid = t.bot_guid
            WHERE t.bot_guid = %s
            ORDER BY t.assigned_at DESC
            LIMIT 1
        """, (bot_guid,))
        row = cursor.fetchone()
    if not row:
        return None

    bot_name = row.get('bot_name', '') or ''
    bot_class = get_class_name(
        int(row.get('class') or 0)
    )
    bot_race = get_race_name(
        int(row.get('race') or 0)
    )
    bot_gender = get_gender_label(
        int(row.get('gender') or 0)
    )
    traits = [
        row.get('trait1', ''),
        row.get('trait2', ''),
        row.get('trait3', ''),
    ]
    tone = row.get('tone', '')

    if not bot_name or not bot_class or not bot_race:
        return None
    if not all(traits):
        return None

    backstory = _generate_bot_backstory(
        db, config, bot_guid, None,
        bot_name, bot_class, bot_race,
        traits, tone,
        bot_gender=bot_gender,
    )
    if backstory:
        logger.info(
            "Regenerated backstory for %s (%s)",
            bot_name, bot_guid,
        )
    return backstory


def handle_backstory_regen_event(
    db, client, config, event,
):
    """Event handler for bot_backstory_regen.

    Called when a player requests backstory
    regeneration via the addon. Clears and
    regenerates the backstory, then marks the
    event completed.
    """
    import json
    extra = event.get('extra_data')
    if isinstance(extra, str):
        extra = json.loads(extra)

    bot_guid = int(extra.get('bot_guid') or 0)
    if not bot_guid:
        return True

    backstory = regenerate_bot_backstory(
        db, config, bot_guid,
    )
    return True


@_serialized
def regenerate_bot_tone(db, config, bot_guid):
    """Clear and regenerate tone for a bot.

    Called by the bot_tone_regen event handler
    when the player saves new traits via addon.
    """
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE llm_bot_identities"
            " SET tone = NULL"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        cursor.execute(
            "UPDATE llm_group_bot_traits"
            " SET tone = NULL"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        db.commit()
    except Exception:
        pass

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.bot_guid,
               COALESCE(i.bot_name, c.name)
                   AS bot_name,
               i.trait1, i.trait2, i.trait3,
               c.class, c.race
        FROM llm_bot_identities i
        JOIN characters c
          ON c.guid = i.bot_guid
        WHERE i.bot_guid = %s
    """, (bot_guid,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            SELECT t.bot_guid,
                   COALESCE(t.bot_name, c.name)
                       AS bot_name,
                   t.trait1, t.trait2, t.trait3,
                   c.class, c.race
            FROM llm_group_bot_traits t
            JOIN characters c
              ON c.guid = t.bot_guid
            WHERE t.bot_guid = %s
            ORDER BY t.assigned_at DESC
            LIMIT 1
        """, (bot_guid,))
        row = cursor.fetchone()
    if not row:
        return None

    bot_name = row.get('bot_name', '') or ''
    bot_class = get_class_name(
        int(row.get('class') or 0)
    )
    bot_race = get_race_name(
        int(row.get('race') or 0)
    )
    traits = [
        row.get('trait1', '') or '',
        row.get('trait2', '') or '',
        row.get('trait3', '') or '',
    ]

    if not bot_name or not bot_class or not bot_race:
        return None
    if not all(traits):
        return None

    tone = _generate_bot_tone(
        db, config, bot_guid, None,
        bot_name, bot_class, bot_race, traits,
    )
    if tone:
        logger.info(
            "Regenerated tone for %s (%s): %s",
            bot_name, bot_guid, tone,
        )
    return tone


def handle_tone_regen_event(
    db, client, config, event,
):
    """Event handler for bot_tone_regen.

    Called when a player saves new traits via the
    addon. Clears and regenerates the tone, then
    marks the event completed.
    """
    import json
    extra = event.get('extra_data')
    if isinstance(extra, str):
        extra = json.loads(extra)

    bot_guid = int(extra.get('bot_guid') or 0)
    if not bot_guid:
        return True

    regenerate_bot_tone(db, config, bot_guid)
    return True
