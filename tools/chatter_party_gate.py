"""Party-chat pacing gate.

This module owns visible party-chat pacing for Python-generated chatter.
It intentionally stays separate from domain handlers so event logic can
only choose a policy and reason, while this layer handles scheduling.
"""

import logging
import math
from typing import Optional


logger = logging.getLogger(__name__)

POLICY_BYPASS = 'bypass'
POLICY_RESPONSIVE = 'responsive'
POLICY_URGENT = 'urgent'
POLICY_CONTEXTUAL = 'contextual'
POLICY_FILLER = 'filler'

VALID_POLICIES = {
    POLICY_BYPASS,
    POLICY_RESPONSIVE,
    POLICY_URGENT,
    POLICY_CONTEXTUAL,
    POLICY_FILLER,
}

_CRITICAL_EVENTS = {
    'bot_group_combat',
    'bot_group_spell_cast',
    'bot_group_low_health',
    'bot_group_oom',
    'bot_group_aggro_loss',
    'bg_flag_picked_up',
    'bg_flag_dropped',
    'bg_flag_captured',
    'bg_flag_returned',
    'bg_node_contested',
    'bg_node_captured',
    'raid_boss_pull',
    'raid_boss_kill',
    'raid_boss_wipe',
}

_RESPONSIVE_EVENTS = {
    'bot_group_player_msg',
    'bot_group_emote_reaction',
    'proximity_reply',
}

_FILLER_EVENTS = {
    'group_idle',
    'group_idle_conv',
    'group_bot_question',
    'bot_group_screenshot_observation',
    'bot_group_nearby_object',
    'bg_idle_chatter',
    'raid_idle_morale',
    'bot_group_emote_observer',
}


def gate_enabled(config: dict) -> bool:
    return str(config.get(
        'LLMChatter.PartyGate.Enable', '1'
    )).strip() == '1'


def _debug_enabled(config: dict) -> bool:
    return str(config.get(
        'LLMChatter.PartyGate.DebugLog', '0'
    )).strip() == '1'


def _int_config(
    config: dict,
    key: str,
    default: int,
    minimum: int = 0,
    maximum: int = 300,
) -> int:
    try:
        value = int(config.get(key, default))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def normalize_policy(policy: Optional[str]) -> str:
    if not policy:
        return POLICY_CONTEXTUAL
    normalized = str(policy).strip().lower()
    if normalized in VALID_POLICIES:
        return normalized
    return POLICY_CONTEXTUAL


def policy_for_reason(reason: Optional[str]) -> str:
    """Map event/source names to a pacing policy."""
    key = str(reason or '').strip()
    if key in _CRITICAL_EVENTS:
        return POLICY_URGENT
    if key in _RESPONSIVE_EVENTS:
        return POLICY_RESPONSIVE
    if key in _FILLER_EVENTS:
        return POLICY_FILLER
    if key.startswith('bg_flag_') or key.startswith('bg_node_'):
        return POLICY_URGENT
    if key.startswith('bot_group_emote_reaction'):
        return POLICY_RESPONSIVE
    if key.startswith('group_idle'):
        return POLICY_FILLER
    if key.startswith('screenshot'):
        return POLICY_FILLER
    return POLICY_CONTEXTUAL


def gap_for_policy(config: dict, policy: str) -> int:
    policy = normalize_policy(policy)
    if policy == POLICY_FILLER:
        return _int_config(
            config,
            'LLMChatter.PartyGate.FillerMinGapSeconds',
            8,
        )
    if policy == POLICY_RESPONSIVE:
        return _int_config(
            config,
            'LLMChatter.PartyGate.ResponsiveMinGapSeconds',
            2,
        )
    if policy == POLICY_URGENT:
        return _int_config(
            config,
            'LLMChatter.PartyGate.UrgentMinGapSeconds',
            0,
        )
    if policy == POLICY_BYPASS:
        return 0
    return _int_config(
        config,
        'LLMChatter.PartyGate.ContextualMinGapSeconds',
        6,
    )


def _sanitize_reason(reason: Optional[str]) -> str:
    text = str(reason or '')[:64]
    return text or 'unknown'


def should_defer_party_generation(
    db,
    config: dict,
    group_id: int,
    policy: str = POLICY_FILLER,
    reason: Optional[str] = None,
) -> bool:
    """Return True when filler generation should wait before LLM use."""
    if not gate_enabled(config):
        return False
    policy = normalize_policy(policy)
    if policy != POLICY_FILLER:
        return False
    try:
        group_id = int(group_id or 0)
    except (TypeError, ValueError):
        return False
    if not group_id:
        return False

    threshold = _int_config(
        config,
        'LLMChatter.PartyGate.PreLLMDeferThresholdSeconds',
        4,
        maximum=120,
    )
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT TIMESTAMPDIFF(
            SECOND, NOW(), next_available_at
        ) AS wait_seconds
        FROM llm_party_chat_pacing
        WHERE group_id = %s
        LIMIT 1
    """, (group_id,))
    row = cursor.fetchone()
    cursor.close()
    wait_seconds = 0
    if row and row.get('wait_seconds') is not None:
        wait_seconds = int(row['wait_seconds'] or 0)
    defer = wait_seconds > threshold
    if defer and _debug_enabled(config):
        logger.info(
            "[PARTY-GATE] pre-LLM defer group=%s "
            "reason=%s wait=%ss threshold=%ss",
            group_id,
            _sanitize_reason(reason),
            wait_seconds,
            threshold,
        )
    return defer


def defer_event_for_party_gate(
    db,
    config: dict,
    event_id: int,
    reason: Optional[str] = None,
) -> None:
    """Return an event to pending status for a later gate attempt."""
    delay = max(1, gap_for_policy(config, POLICY_FILLER))
    cursor = db.cursor()
    cursor.execute("""
        UPDATE llm_chatter_events
        SET status = 'pending',
            react_after = DATE_ADD(
                NOW(), INTERVAL %s SECOND
            ),
            processed_at = NULL
        WHERE id = %s
    """, (delay, event_id))
    db.commit()
    cursor.close()
    if _debug_enabled(config):
        logger.info(
            "[PARTY-GATE] event defer event=%s reason=%s "
            "delay=%ss",
            event_id,
            _sanitize_reason(reason),
            delay,
        )


def reserve_party_slot(
    db,
    config: dict,
    group_id: int,
    requested_delay: float,
    policy: Optional[str] = None,
    reason: Optional[str] = None,
) -> int:
    """Reserve the next visible party-chat slot for a group.

    Returns the adjusted delay in whole seconds. The reservation is kept
    short and happens after LLM generation, never while a provider call is
    in flight.
    """
    if not gate_enabled(config):
        return max(0, int(math.ceil(float(requested_delay or 0))))

    try:
        group_id = int(group_id or 0)
    except (TypeError, ValueError):
        group_id = 0
    if not group_id:
        return max(0, int(math.ceil(float(requested_delay or 0))))

    requested_delay = max(0, float(requested_delay or 0))
    policy = normalize_policy(policy or policy_for_reason(reason))
    reason = _sanitize_reason(reason)
    gap = gap_for_policy(config, policy)

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute("""
            INSERT IGNORE INTO llm_party_chat_pacing
                (group_id, next_available_at, last_activity_at)
            VALUES (%s, NOW(), NOW())
        """, (group_id,))
        cursor.execute("""
            SELECT
                UNIX_TIMESTAMP(NOW()) AS now_ts,
                UNIX_TIMESTAMP(next_available_at) AS next_ts
            FROM llm_party_chat_pacing
            WHERE group_id = %s
            FOR UPDATE
        """, (group_id,))
        row = cursor.fetchone() or {}
        now_ts = float(row.get('now_ts') or 0)
        next_ts = float(row.get('next_ts') or now_ts)
        requested_at = now_ts + requested_delay

        if policy in {POLICY_BYPASS, POLICY_URGENT}:
            scheduled_at = requested_at
        else:
            scheduled_at = max(requested_at, next_ts)

        max_delay = None
        if policy == POLICY_FILLER:
            max_delay = _int_config(
                config,
                'LLMChatter.PartyGate.MaxFillerDelaySeconds',
                45,
                maximum=300,
            )
            scheduled_at = min(scheduled_at, now_ts + max_delay)

        next_available = max(next_ts, scheduled_at + gap)
        cursor.execute("""
            UPDATE llm_party_chat_pacing
            SET next_available_at = FROM_UNIXTIME(%s),
                last_activity_at = FROM_UNIXTIME(%s),
                last_policy = %s
            WHERE group_id = %s
        """, (
            int(math.ceil(next_available)),
            int(math.ceil(scheduled_at)),
            policy,
            group_id,
        ))
        db.commit()

        adjusted = max(0, int(math.ceil(scheduled_at - now_ts)))
        if _debug_enabled(config):
            extra = (
                f" max_filler={max_delay}s"
                if max_delay is not None else ""
            )
            logger.info(
                "[PARTY-GATE] reserve group=%s policy=%s "
                "reason=%s requested=%ss adjusted=%ss gap=%ss%s",
                group_id,
                policy,
                reason,
                int(math.ceil(requested_delay)),
                adjusted,
                gap,
                extra,
            )
        return adjusted
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        logger.error(
            "[PARTY-GATE] reservation failed group=%s "
            "policy=%s reason=%s",
            group_id,
            policy,
            reason,
            exc_info=True,
        )
        return max(0, int(math.ceil(requested_delay)))
    finally:
        cursor.close()
