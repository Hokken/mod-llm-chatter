"""Chatter Threads - conversations that develop instead of resetting.

This module owns per-group conversation continuity for party idle
chatter:

- the thread store: the current subject, how much life it has left,
  an open point, feelings that linger per speaker, recent
  interruptions (player messages, events) and the last few finished
  subjects for callbacks
- the soft nudge for the next idle exchange (continue, drift,
  callback or a fresh subject, mostly persona-driven), weighted by
  the thread's remaining energy
- prompt rendering of that context, always framed as a nudge the
  model may ignore, never as a script or with example lines
- tolerant parsing of the optional ``thread`` report the model
  returns alongside its chat JSON

Only spoken lines become conversational facts. An idle exchange's
report is held against the ids of the chat rows it queued and is
adopted only once every row was delivered (``delivered = 1`` and
``drop_reason IS NULL``). Dropped or partial exchanges are handled
conservatively. Event facts interrupt immediately, but a queued
reaction line is quoted only after it was delivered.

Every group state carries a session id and a major-event revision.
Stale completions (the group was cleared, restarted, or a wipe/death
took over after planning) are rejected.

The store is in memory, bounded by ``MaxGroups``, expires idle
groups on lookup, and is reconciled against the active party list
every idle tick, so an ended group is forgotten even when its rows
were deleted elsewhere.
"""

import collections
import dataclasses
import itertools
import json
import logging
import random
import re
import threading
import time
from typing import (
    Callable, Deque, Dict, Iterable, List, Optional, Sequence,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
_DEFAULT_WEIGHTS = {
    'high': (70, 20, 5, 5),
    'mid': (35, 35, 15, 15),
    'low': (10, 25, 25, 40),
}


def _default_settings() -> dict:
    return {
        'enable': True,
        'guild_enable': True,
        'general_enable': True,
        'history_size': 5,
        'cool_minutes': 15.0,
        'exchange_decay': 0.7,
        'feeling_turns': 3,
        'persona_weight': 60,
        'surroundings_weight': 30,
        'pool_weight': 10,
        'surprise_chance': 12,
        'high_threshold': 0.6,
        'low_threshold': 0.3,
        'weights': dict(_DEFAULT_WEIGHTS),
        'idle_ttl_minutes': 180.0,
        'max_groups': 200,
        'report_tokens': 90,
        'pending_timeout': 300.0,
        'max_interruptions': 4,
        'max_pending': 6,
    }


_settings = _default_settings()


def _int(config, key, default, low, high):
    try:
        value = int(config.get(key, default))
    except (TypeError, ValueError, AttributeError):
        logger.error("Failed to parse %s", key)
        value = default
    return max(low, min(value, high))


def _weights(config, key, default):
    """Parse 'continue,drift,callback,new' weights (0-100 each)."""
    raw = config.get(key)
    if raw is None:
        return default
    try:
        values = tuple(
            int(part) for part in str(raw).split(',')
        )
    except ValueError:
        values = ()
    if (
        len(values) != 4
        or any(v < 0 or v > 100 for v in values)
        or not any(values)
    ):
        logger.error("Invalid %s, using default", key)
        return default
    return values


def configure_threads(config) -> None:
    """Load thread settings from the bridge config."""
    config = config or {}
    high = _int(
        config, 'LLMChatter.Threads.HighEnergyThreshold', 60, 1, 100
    )
    low = _int(
        config, 'LLMChatter.Threads.LowEnergyThreshold', 30, 0, 99
    )
    if low >= high:
        logger.error(
            "Threads.LowEnergyThreshold must be below "
            "HighEnergyThreshold; using defaults"
        )
        high, low = 60, 30
    _settings.update({
        'enable': _int(
            config, 'LLMChatter.Threads.Enable', 1, 0, 1
        ) == 1,
        'guild_enable': _int(
            config, 'LLMChatter.Threads.GuildEnable', 1, 0, 1
        ) == 1,
        'general_enable': _int(
            config, 'LLMChatter.Threads.GeneralEnable', 1, 0, 1
        ) == 1,
        'history_size': _int(
            config, 'LLMChatter.Threads.HistorySize', 5, 1, 10
        ),
        'cool_minutes': float(_int(
            config, 'LLMChatter.Threads.CoolMinutes', 15, 1, 240
        )),
        'exchange_decay': _int(
            config, 'LLMChatter.Threads.ExchangeDecay', 70, 10, 95
        ) / 100.0,
        'feeling_turns': _int(
            config, 'LLMChatter.Threads.FeelingTurns', 3, 1, 10
        ),
        'persona_weight': _int(
            config, 'LLMChatter.Threads.PersonaTopicWeight',
            60, 0, 100,
        ),
        'surroundings_weight': _int(
            config, 'LLMChatter.Threads.SurroundingsTopicWeight',
            30, 0, 100,
        ),
        'pool_weight': _int(
            config, 'LLMChatter.Threads.PoolTopicWeight', 10, 0, 100
        ),
        'surprise_chance': _int(
            config, 'LLMChatter.Threads.SurpriseChance', 12, 0, 100
        ),
        'high_threshold': high / 100.0,
        'low_threshold': low / 100.0,
        'weights': {
            'high': _weights(
                config, 'LLMChatter.Threads.HighEnergyMoveWeights',
                _DEFAULT_WEIGHTS['high'],
            ),
            'mid': _weights(
                config, 'LLMChatter.Threads.MidEnergyMoveWeights',
                _DEFAULT_WEIGHTS['mid'],
            ),
            'low': _weights(
                config, 'LLMChatter.Threads.LowEnergyMoveWeights',
                _DEFAULT_WEIGHTS['low'],
            ),
        },
        'idle_ttl_minutes': float(_int(
            config, 'LLMChatter.Threads.IdleTTLMinutes',
            180, 10, 1440,
        )),
        'max_groups': _int(
            config, 'LLMChatter.Threads.MaxGroups', 200, 1, 5000
        ),
        'report_tokens': _int(
            config, 'LLMChatter.Threads.ReportTokens', 90, 40, 400
        ),
        'pending_timeout': float(_int(
            config, 'LLMChatter.Threads.PendingTimeoutSeconds',
            300, 30, 3600,
        )),
        'max_interruptions': _int(
            config, 'LLMChatter.Threads.MaxInterruptions', 4, 1, 10
        ),
        'max_pending': _int(
            config, 'LLMChatter.Threads.MaxPending', 6, 1, 50
        ),
    })


def reset_settings() -> None:
    """Restore defaults (tests)."""
    _settings.clear()
    _settings.update(_default_settings())


def threads_enabled(key=None) -> bool:
    """Master switch, plus the per-channel switch for guild and
    General keys."""
    if not _settings['enable']:
        return False
    channel = key[0] if isinstance(key, tuple) and key else 'party'
    if channel == 'guild':
        return bool(_settings['guild_enable'])
    if channel == 'general':
        return bool(_settings['general_enable'])
    return True


def party_key(group_id):
    """Thread key of a party (group id)."""
    try:
        gid = int(group_id or 0)
    except (TypeError, ValueError):
        gid = 0
    return ('party', gid) if gid else None


def guild_key(guild_id):
    """Thread key of a guild's chat."""
    try:
        gid = int(guild_id or 0)
    except (TypeError, ValueError):
        gid = 0
    return ('guild', gid) if gid else None


def general_key(zone_id, faction):
    """Thread key of one zone's General channel for one faction
    (Alliance and Horde each have their own General)."""
    try:
        zid = int(zone_id or 0)
    except (TypeError, ValueError):
        zid = 0
    side = str(faction or '').strip().lower()
    return ('general', zid, side) if zid and side else None


def _key(value):
    """Normalize a thread key. Plain ints are party group ids."""
    if isinstance(value, tuple):
        return value if value else None
    return party_key(value)


def report_tokens() -> int:
    """Extra output tokens reserved for the thread report."""
    return int(_settings['report_tokens'])


# ------------------------------------------------------------------
# State
# ------------------------------------------------------------------
_ENERGY_VALUES = {
    'high': 0.9, 'medium': 0.6, 'low': 0.35, 'spent': 0.1,
}
_NEW_THREAD_ENERGY = 0.9
_EVENT_THREAD_ENERGY = 0.7
_MAJOR_EVENTS = {'bot_group_wipe', 'bot_group_death'}
_MAX_TOPIC = 80
_MAX_POINT = 140
_MAX_FEELING = 120
_REPLY_MIN_ENERGY = 0.15


@dataclasses.dataclass
class Thread:
    topic: str
    energy: float
    origin: str
    started_at: float
    updated_at: float
    exchanges: int = 0
    open_point: str = ''


@dataclasses.dataclass
class PendingExchange:
    """An idle exchange queued but not yet confirmed as spoken."""

    turn: 'IdleTurn'
    report: Optional[dict]
    message_ids: tuple
    speakers: tuple
    created_at: float
    # False when part of the model's dialogue was filtered before
    # queueing; the report then describes more than was said.
    complete: bool = True


@dataclasses.dataclass
class GroupThreads:
    session: int = 0
    major_rev: int = 0
    current: Optional[Thread] = None
    history: Deque[Thread] = dataclasses.field(
        default_factory=collections.deque
    )
    # speaker name -> (feeling, turn it was reported)
    feelings: Dict[str, tuple] = dataclasses.field(
        default_factory=dict
    )
    interruptions: List[dict] = dataclasses.field(
        default_factory=list
    )
    pending: List[PendingExchange] = dataclasses.field(
        default_factory=list
    )
    turn: int = 0
    last_touch: float = 0.0


@dataclasses.dataclass(frozen=True)
class IdleTurn:
    """The plan for one idle exchange, handed back on record."""

    group_id: tuple
    session: int
    major_rev: int
    kind: str                       # continue|drift|callback|new
    source: str = ''                # persona|surroundings|pool
    pool_topic: Optional[str] = None
    callback_topic: str = ''
    surprise: bool = False
    # True when the exchange is meant to build on a live or an
    # earlier subject (continue, drift, callback): the theme ban
    # is relaxed, the wording ban stays.
    builds_on_subject: bool = False
    prompt_block: str = ''
    planned_at: float = 0.0


_store: 'collections.OrderedDict[tuple, GroupThreads]' = (
    collections.OrderedDict()
)
_lock = threading.RLock()
_session_ids = itertools.count(1)


def _now() -> float:
    return time.time()


def _expired(state: GroupThreads, now: float) -> bool:
    return now - state.last_touch > _settings['idle_ttl_minutes'] * 60


def _get(group_id, create: bool) -> Optional[GroupThreads]:
    """Look up (optionally create) a group's state. Holds _lock.

    Expired states are dropped on lookup regardless of store size,
    and the store is capped by evicting least recently used groups.
    """
    group_id = _key(group_id)
    if group_id is None:
        return None
    now = _now()
    state = _store.get(group_id)
    if state is not None and _expired(state, now):
        del _store[group_id]
        state = None
    if state is None:
        if not create:
            return None
        state = GroupThreads(
            session=next(_session_ids),
            history=collections.deque(
                maxlen=_settings['history_size']
            ),
        )
        _store[group_id] = state
        while len(_store) > _settings['max_groups']:
            _store.popitem(last=False)
    state.last_touch = now
    _store.move_to_end(group_id)
    return state


def clear_group(group_id) -> None:
    """Forget a thread (party group id or channel key)."""
    key = _key(group_id)
    if key is None:
        return
    with _lock:
        _store.pop(key, None)


def clear_all() -> None:
    with _lock:
        _store.clear()


def reconcile_active_groups(active_group_ids: Iterable) -> None:
    """Forget groups whose party session no longer exists.

    Called with the current ``llm_group_bot_traits`` group ids on
    every idle tick, so groups that ended through any path (last bot
    removed, disband, logout) are cleared even when other players
    stay online.
    """
    active = {
        party_key(g) for g in active_group_ids or ()
    } - {None}
    with _lock:
        # Only party threads follow the party list; guild and
        # General threads expire through the TTL/LRU limits.
        for key in [
            k for k in _store
            if k[0] == 'party' and k not in active
        ]:
            del _store[key]


def _effective_energy(thread: Thread, now: float) -> float:
    """Energy after cooling off during silence."""
    idle_min = max(0.0, (now - thread.updated_at) / 60.0)
    return thread.energy * 0.5 ** (
        idle_min / _settings['cool_minutes']
    )


def _archive_current(state: GroupThreads) -> None:
    if state.current is not None:
        state.history.append(state.current)
        state.current = None


def _clip(value, limit) -> str:
    if not isinstance(value, str):
        return ''
    text = ' '.join(value.split())
    return text[:limit].rstrip()


def _trim_interruptions(state: GroupThreads) -> None:
    del state.interruptions[:-_settings['max_interruptions']]


# ------------------------------------------------------------------
# Delivery confirmation
# ------------------------------------------------------------------
def _delivery_status(db, message_ids: Sequence[int]) -> Dict[int, tuple]:
    """Map message id -> (delivered|dropped|pending, age seconds).

    Only a row that was actually sent counts as delivered: C++
    first *claims* a row (delivered = 1, drop_reason NULL,
    delivered_at still NULL) and sets delivered_at only after the
    send. Claimed rows stay pending. A drop sets drop_reason. A row
    that no longer exists counts as dropped. The age comes from the
    database clock so no timezone conversion is needed.
    """
    ids = [int(i) for i in message_ids if i]
    if not ids or db is None:
        return {}
    cursor = db.cursor(dictionary=True)
    marks = ','.join(['%s'] * len(ids))
    cursor.execute(
        "SELECT id, delivered, drop_reason, delivered_at, "
        "TIMESTAMPDIFF(SECOND, delivered_at, NOW()) AS age_s "
        f"FROM llm_chatter_messages WHERE id IN ({marks})",
        ids,
    )
    status = {i: ('dropped', None) for i in ids}
    for row in cursor.fetchall() or []:
        mid = int(row['id'])
        if row.get('drop_reason') is not None:
            status[mid] = ('dropped', None)
        elif (
            int(row.get('delivered') or 0) == 1
            and row.get('delivered_at') is not None
        ):
            age = row.get('age_s')
            try:
                age = max(0.0, float(age))
            except (TypeError, ValueError):
                age = 0.0
            status[mid] = ('delivered', age)
        else:
            status[mid] = ('pending', None)
    return status


def _reconcile(db, state: GroupThreads, now: float) -> None:
    """Promote or discard pending exchanges and event quotes.

    Holds _lock. When the lookup fails, confirmed facts stay as
    they are, but proposals and quotes older than
    PendingTimeoutSeconds still expire, so nothing lingers forever.
    """
    ids = [
        mid for p in state.pending for mid in p.message_ids
    ] + [
        i['message_id'] for i in state.interruptions
        if i.get('quote') == 'pending' and i.get('message_id')
    ]
    if not ids:
        return
    try:
        status = _delivery_status(db, ids)
    except Exception:
        logger.error("thread delivery lookup failed", exc_info=True)
        status = {}
    timeout = _settings['pending_timeout']
    for item in state.interruptions:
        if item.get('quote') == 'pending':
            result = status.get(item.get('message_id'), ('pending',))
            if result[0] == 'delivered':
                item['quote'] = 'delivered'
            elif result[0] == 'dropped' or now - item['at'] > timeout:
                item['quote'] = 'dropped'
    still_pending = []
    for pending in state.pending:
        results = [status.get(mid, ('pending', None))
                   for mid in pending.message_ids]
        states = [r[0] for r in results]
        timed_out = now - pending.created_at > timeout
        if 'pending' in states and not timed_out:
            still_pending.append(pending)
            continue
        ages = [r[1] for r in results if r[0] == 'delivered']
        if not ages:
            continue  # Nothing was said: the exchange never happened.
        # Time basis: when the last line was actually heard, so a
        # late reconciliation does not make old talk look fresh.
        spoken_at = now - min(ages)
        full = len(ages) == len(results) and pending.complete
        # Partial or incomplete: something was said, but not the
        # exchange the report describes. Count it, adopt nothing.
        _promote(state, pending, spoken_at, full=full)
    state.pending = still_pending


# ------------------------------------------------------------------
# Recording interruptions
# ------------------------------------------------------------------
def _event_label(event_type: str) -> str:
    label = str(event_type or 'event')
    if label.startswith('bot_group_'):
        label = label[len('bot_group_'):]
    return label.replace('_', ' ')


_ANY_SESSION = object()


def capture_session(group_id) -> Optional[int]:
    """Session id to hand back to note_event after slow work.

    Taken before an LLM call. A group without thread state gets its
    session created here, so even a first event carries a real
    identity: if the group is cleared or replaced during the wait,
    the completion is rejected instead of resurrecting or
    contaminating state. Returns None when threads are disabled.
    """
    key = _key(group_id)
    if key is None or not threads_enabled(key):
        return None
    with _lock:
        return _get(key, create=True).session


def note_event(group_id, event_type, speaker='', message='',
               message_id=None, session=_ANY_SESSION) -> None:
    """Record a party event reaction against the thread.

    The event itself is a fact and interrupts at once. The queued
    reaction line is quoted only after it was delivered. Minor
    events let the subject resume later; major events (wipe, death)
    take over, moving the old subject to history where it can still
    be called back.

    ``session`` comes from capture_session() before the reaction
    was generated; the event then applies only to that same, still
    live session (capture_session creates it for a first event).
    Without it (direct callers), the event applies to the current
    state, creating one if needed.
    """
    key = _key(group_id)
    if key is None or not threads_enabled(key):
        return
    now = _now()
    label = _event_label(event_type)
    with _lock:
        if session is not _ANY_SESSION:
            state = _get(key, create=False)
            if (
                session is None
                or state is None
                or state.session != session
            ):
                return
        else:
            state = _get(key, create=True)
        state.interruptions.append({
            'kind': 'event',
            'label': label,
            'speaker': _clip(speaker, 40),
            'text': _clip(message, _MAX_POINT),
            'message_id': message_id,
            'quote': 'pending' if message_id else 'dropped',
            'at': now,
        })
        _trim_interruptions(state)
        if event_type in _MAJOR_EVENTS:
            state.major_rev += 1
            _archive_current(state)
            state.current = Thread(
                topic=f"the {label}",
                energy=_EVENT_THREAD_ENERGY,
                origin='event',
                started_at=now,
                updated_at=now,
            )


def note_player_message(group_id, player_name, message) -> None:
    """Record something the real player said in party chat.

    Player lines reach this point already spoken in game, so they
    are facts immediately.
    """
    key = _key(group_id)
    if key is None or not message or not threads_enabled(key):
        return
    with _lock:
        state = _get(key, create=True)
        state.interruptions.append({
            'kind': 'player',
            'label': 'player',
            'speaker': _clip(player_name, 40),
            'text': _clip(message, _MAX_POINT),
            'at': _now(),
        })
        _trim_interruptions(state)


# ------------------------------------------------------------------
# Planning the next idle exchange
# ------------------------------------------------------------------
_MOVES = ('continue', 'drift', 'callback', 'new')


def _pick_move(energy: Optional[float], has_history: bool) -> str:
    if energy is None:
        weights = [0, 0, 30 if has_history else 0, 70]
    elif energy >= _settings['high_threshold']:
        weights = list(_settings['weights']['high'])
    elif energy >= _settings['low_threshold']:
        weights = list(_settings['weights']['mid'])
    else:
        weights = list(_settings['weights']['low'])
    if not has_history:
        weights[3] += weights[2]
        weights[2] = 0
    if not any(weights):
        weights[3] = 1
    return random.choices(_MOVES, weights=weights)[0]


def _pick_source(in_instance: bool, has_pool: bool) -> str:
    weights = {
        'persona': _settings['persona_weight'],
        'surroundings': _settings['surroundings_weight'],
        'pool': _settings['pool_weight'] if (
            has_pool and not in_instance
        ) else 0,
    }
    if not any(weights.values()):
        return 'persona'
    names = list(weights)
    return random.choices(
        names, weights=[weights[n] for n in names]
    )[0]


def plan_idle_turn(
    group_id,
    speaker_names: Sequence[str],
    in_instance: bool = False,
    topic_pool: Optional[Sequence[str]] = None,
    db=None,
    fresh_topic: Optional[Callable[[], Optional[str]]] = None,
) -> Optional[IdleTurn]:
    """Choose a soft direction for the next idle exchange.

    ``db`` lets pending exchanges and quotes be confirmed against
    delivery first. Returns None when threads are disabled; callers
    then keep their original topic behaviour.

    ``fresh_topic`` is called only when the thread wants a fresh
    subject. A non-empty result becomes that subject (``source`` is
    ``'topic'`` and ``pool_topic`` holds it); otherwise the usual
    persona, surroundings or pool choice applies.
    """
    key = _key(group_id)
    if key is None or not threads_enabled(key):
        return None
    now = _now()
    solo = len(speaker_names) <= 1
    with _lock:
        state = _get(key, create=True)
        _reconcile(db, state, now)
        current = state.current
        energy = (
            _effective_energy(current, now) if current else None
        )
        history = list(state.history)
        move = _pick_move(energy, bool(history))
        if current is None and move in ('continue', 'drift'):
            move = 'new'
        source, pool_topic, callback_topic = '', None, ''
        if move == 'new':
            chosen = fresh_topic() if fresh_topic else None
            if chosen:
                source, pool_topic = 'topic', chosen
            else:
                source = _pick_source(in_instance, bool(topic_pool))
            if source == 'pool':
                pool_topic = random.choice(list(topic_pool))
        elif move == 'callback':
            callback_topic = random.choice(history).topic
        surprise = (
            random.randint(1, 100) <= _settings['surprise_chance']
        )
        block = _render_idle_block(
            state, current, energy, history, move, source,
            pool_topic, callback_topic, surprise, solo, now,
        )
        return IdleTurn(
            group_id=key,
            session=state.session,
            major_rev=state.major_rev,
            kind=move,
            source=source,
            pool_topic=pool_topic,
            callback_topic=callback_topic,
            surprise=surprise,
            builds_on_subject=move in (
                'continue', 'drift', 'callback'
            ),
            prompt_block=block,
            planned_at=now,
        )


# ------------------------------------------------------------------
# Rendering
# ------------------------------------------------------------------
def _energy_words(energy: float) -> str:
    if energy >= 0.6:
        return 'plenty of life left'
    if energy >= 0.3:
        return 'some life left'
    if energy >= 0.15:
        return 'little life left'
    return 'mostly run its course'


def _ago(seconds: float) -> str:
    minutes = int(seconds // 60)
    if minutes < 1:
        return 'just now'
    if minutes < 60:
        return f"{minutes} min ago"
    return f"{minutes // 60} h ago"


def _render_interruptions(state: GroupThreads, now: float) -> str:
    parts = []
    for item in state.interruptions:
        when = _ago(now - item['at'])
        if item['kind'] == 'player':
            parts.append(
                f"{item['speaker'] or 'The player'} (the player) "
                f"said \"{item['text']}\" ({when})."
            )
            continue
        said = ''
        if (
            item.get('quote') == 'delivered'
            and item['text'] and item['speaker']
        ):
            said = f" {item['speaker']} reacted: \"{item['text']}\""
        parts.append(f"Event: {item['label']} ({when}).{said}")
    return ' '.join(parts)


def _render_feelings(state: GroupThreads) -> str:
    limit = _settings['feeling_turns']
    parts = [
        f"{name}: {text}"
        for name, (text, turn) in state.feelings.items()
        if state.turn - turn < limit
    ]
    return '; '.join(parts)


def _nudge_sentence(move, source, pool_topic, callback_topic,
                    solo) -> str:
    who = 'you' if solo else 'someone'
    if move == 'continue':
        return (
            f"The current subject still has pull: {who} might "
            "push it further, disagree, or take up the open point."
        )
    if move == 'drift':
        return (
            "The talk may drift to something the current subject "
            f"reminds {who} of."
        )
    if move == 'callback':
        return (
            f"{'You' if solo else 'Someone'} might bring back an "
            f"earlier subject: {callback_topic}."
        )
    if source == 'pool' and pool_topic:
        return f"A possible fresh subject: {pool_topic}."
    if source == 'surroundings':
        return (
            "A fresh subject could come from the surroundings or "
            "the situation the group is in."
        )
    owner = (
        'you personally care about'
        if solo else
        'one of the speakers personally cares about'
    )
    return (
        f"A fresh subject would come most naturally from something "
        f"{owner}: personality, history, race or class."
    )


def _render_idle_block(state, current, energy, history, move, source,
                       pool_topic, callback_topic, surprise, solo,
                       now) -> str:
    lines = ["<conversation_thread>"]
    firm_topic = move == 'new' and source == 'topic' and pool_topic
    if current is not None and move == 'new':
        lines.append(
            f"Previous subject (finished, leave it behind): "
            f"{current.topic}"
        )
    elif current is not None:
        lines.append(
            f"Current subject: {current.topic} "
            f"({_energy_words(energy)}; "
            f"{current.exchanges} exchange"
            f"{'' if current.exchanges == 1 else 's'} so far)"
        )
        if current.open_point:
            lines.append(f"Open point: {current.open_point}")
    earlier = [t.topic for t in history][-3:]
    if earlier:
        lines.append(
            "Earlier subjects this session: " + '; '.join(earlier)
        )
    since = _render_interruptions(state, now)
    if since:
        lines.append(f"Since the last exchange: {since}")
    feelings = _render_feelings(state)
    if feelings:
        lines.append(f"Still on their minds: {feelings}")
    if firm_topic:
        lines.append(
            f"New subject for this exchange: {pool_topic}. Open "
            "with it and keep the talk on it; an earlier subject "
            "may get a passing nod at most, never the focus."
        )
    else:
        lines.append(
            "Where it might go (a nudge, not a script; follow the "
            "conversation if it wants to go elsewhere): "
            + _nudge_sentence(
                move, source, pool_topic, callback_topic, solo
            )
        )
    if surprise:
        lines.append(
            "Room for surprise: a speaker may change their mind, go "
            "off on a tangent, reveal something, or take an "
            "unexpected stance, as long as it is believable for who "
            "they are."
        )
    lines.append(
        "Leftover feelings and subject changes play out through "
        "each speaker's personality: whoever still cared about an "
        "earlier subject reacts the way they naturally would. "
        "Disagreement is welcome but stays friendly."
    )
    lines.append("</conversation_thread>")
    return '\n'.join(lines)


def render_for_player_reply(group_id, db=None) -> str:
    """Read-only thread context for replies to the real player.

    Only confirmed (delivered) conversation is described.
    """
    key = _key(group_id)
    if key is None or not threads_enabled(key):
        return ''
    now = _now()
    with _lock:
        state = _get(key, create=False)
        if state is None:
            return ''
        _reconcile(db, state, now)
        current = state.current
        if current is None:
            return ''
        if _effective_energy(current, now) < _REPLY_MIN_ENERGY:
            return ''
        topic = current.topic
        feelings = _render_feelings(state)
    text = (
        f"Before this message the bots were talking about "
        f"{topic}. If the player's message relates to it, "
        "weave it in; otherwise answer the player and let that "
        "subject rest for now."
    )
    if feelings:
        text += f" Still on their minds: {feelings}."
    return text


# ------------------------------------------------------------------
# Thread report (optional JSON the model returns)
# ------------------------------------------------------------------
THREAD_REPORT_OBJECT = (
    '{"thread": {"topic": "2-6 word label for what is being '
    'talked about now", "energy": "high|medium|low|spent", '
    '"subject_changed": true|false, "open_point": "an unanswered '
    'question or unfinished point, or empty", "feelings": '
    '{"<speaker name>": "what is still on their mind, max 12 '
    'words"}}}'
)
THREAD_REPORT_FIELD = THREAD_REPORT_OBJECT[1:-1]
THREAD_REPORT_RULE = (
    "The thread object is private bookkeeping for later "
    "conversation and never appears in chat. Put it last. List "
    "feelings only for speakers who still carry something; use "
    "an empty object otherwise."
)


def _find_thread_object(text: str) -> Optional[dict]:
    decoder = json.JSONDecoder()
    for match in re.finditer(r'"thread"\s*:\s*', text):
        start = match.end()
        if start >= len(text) or text[start] != '{':
            continue
        try:
            obj, _ = decoder.raw_decode(text, start)
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def parse_thread_report(
    response: str, speaker_names: Sequence[str] = (),
) -> Optional[dict]:
    """Extract and validate the optional thread report.

    Returns a normalized dict, or None when absent or unusable.
    """
    if not response or not isinstance(response, str):
        return None
    raw = _find_thread_object(response)
    if not raw:
        return None
    topic = _clip(raw.get('topic'), _MAX_TOPIC)
    energy_label = raw.get('energy')
    energy = (
        _ENERGY_VALUES.get(energy_label.strip().lower())
        if isinstance(energy_label, str) else None
    )
    changed = raw.get('subject_changed')
    report = {
        'topic': topic,
        'energy': energy,
        # Only a real JSON boolean counts; "false" strings do not.
        'subject_changed': changed if isinstance(changed, bool)
        else None,
        'open_point': _clip(raw.get('open_point'), _MAX_POINT),
        'feelings': {},
    }
    known = {n.casefold(): n for n in speaker_names or ()}
    feelings = raw.get('feelings')
    if isinstance(feelings, dict):
        for name, text in feelings.items():
            key = str(name).strip().casefold()
            clipped = _clip(text, _MAX_FEELING)
            if clipped and key in known:
                report['feelings'][known[key]] = clipped
    if not topic and energy is None and not report['feelings']:
        return None
    return report


def record_idle_exchange(
    turn: Optional[IdleTurn],
    response: str,
    speaker_names: Sequence[str],
    message_ids: Sequence[int],
    complete: bool = True,
) -> None:
    """Hold an idle exchange until its lines are confirmed spoken.

    ``message_ids`` are the chat rows actually queued and
    ``speaker_names`` the speakers of those rows only. With no rows,
    nothing was said and nothing is recorded. ``complete`` is False
    when any line of the model's dialogue was filtered before
    queueing; the report is then never adopted.
    """
    if turn is None or not threads_enabled(turn.group_id):
        return
    ids = tuple(int(i) for i in message_ids or () if i)
    if not ids:
        return
    report = parse_thread_report(response, speaker_names)
    with _lock:
        state = _get(turn.group_id, create=False)
        if state is None or state.session != turn.session:
            return
        state.pending.append(PendingExchange(
            turn=turn,
            report=report,
            message_ids=ids,
            speakers=tuple(speaker_names),
            created_at=_now(),
            complete=bool(complete),
        ))
        # Bound unconfirmed work; the oldest proposal goes first.
        del state.pending[:-_settings['max_pending']]


def _decay_current(state: GroupThreads, now: float) -> None:
    current = state.current
    if current is not None:
        current.energy = (
            _effective_energy(current, now)
            * _settings['exchange_decay']
        )
        current.exchanges += 1
        current.updated_at = now


def _promote(state: GroupThreads, pending: PendingExchange,
             now: float, full: bool) -> None:
    """Adopt a confirmed exchange into the thread. Holds _lock.

    ``full`` is False for partial delivery: the exchange counts,
    but its report is not adopted. A major event after planning
    also blocks adoption so an older report never overwrites it.
    """
    turn = pending.turn
    if state.session != turn.session:
        return
    state.turn += 1
    state.interruptions = [
        i for i in state.interruptions
        if i['at'] > turn.planned_at
    ]
    report = pending.report
    if not full or report is None or state.major_rev != turn.major_rev:
        if state.major_rev == turn.major_rev:
            _decay_current(state, now)
        _expire_feelings(state)
        return
    topic = report['topic']
    changed = report['subject_changed']
    if changed is None:
        changed = (
            state.current is None
            or turn.kind in ('new', 'callback')
        )
    current = state.current
    if topic and (current is None or changed):
        _archive_current(state)
        state.current = Thread(
            topic=topic,
            energy=(
                report['energy']
                if report['energy'] is not None
                else _NEW_THREAD_ENERGY
            ),
            origin=(
                turn.source or turn.kind
                if turn.kind in ('new', 'callback')
                else turn.kind
            ),
            started_at=now,
            updated_at=now,
            exchanges=1,
            open_point=report['open_point'],
        )
    elif current is not None:
        # Same subject, or a change without a usable new label:
        # keep the subject and apply only safe updates.
        if topic and not changed:
            current.topic = topic
        current.energy = (
            report['energy']
            if report['energy'] is not None and not changed
            else _effective_energy(current, now)
            * _settings['exchange_decay']
        )
        if not changed:
            current.open_point = report['open_point']
        current.exchanges += 1
        current.updated_at = now
    for name, text in report['feelings'].items():
        state.feelings[name] = (text, state.turn)
    _expire_feelings(state)


def _expire_feelings(state: GroupThreads) -> None:
    limit = _settings['feeling_turns']
    for name in [
        n for n, (_, t) in state.feelings.items()
        if state.turn - t >= limit
    ]:
        del state.feelings[name]


def snapshot(group_id) -> Optional[GroupThreads]:
    """Deep copy of a group's state (tests and diagnostics)."""
    with _lock:
        state = _store.get(_key(group_id))
        if state is None:
            return None
        return dataclasses.replace(
            state,
            current=(
                dataclasses.replace(state.current)
                if state.current else None
            ),
            history=collections.deque(
                (dataclasses.replace(t) for t in state.history),
                maxlen=state.history.maxlen,
            ),
            feelings=dict(state.feelings),
            interruptions=[dict(i) for i in state.interruptions],
            pending=list(state.pending),
        )
