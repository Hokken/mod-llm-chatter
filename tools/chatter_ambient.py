"""Ambient chatter runtime processors.

N9/N10 moved statement and conversation
processing from the bridge.
"""

import json
import logging
import random
import time
from typing import List

from chatter_constants import (
    AMBIENT_CHAT_TOPICS,
    AMBIENT_CHAT_TOPICS_RP,
)
from chatter_shared import (
    parse_single_response,
    parse_conversation_response,
    query_zone_quests,
    query_zone_mobs,
    query_bot_spells,
    replace_placeholders,
    cleanup_message,
    strip_speaker_prefix,
    call_llm,
    insert_chat_message,
    get_recent_zone_messages,
    is_too_similar,
    calculate_dynamic_delay,
    get_chatter_mode,
    _reserve_zone_delivery_window,
    _zone_delivery_delay,
    get_zone_name,
    get_zone_flavor,
    get_subzone_name,
    get_subzone_lore,
    build_conversation_json_repair_prompt,
    spell_out_numbers,
)
from chatter_shared import (
    build_talent_context,
    build_gear_context,
    attach_speaker_gear,
    build_zone_metadata,
    should_include_action,
)
from chatter_db import (
    query_zone_bot_gossip_targets,
    query_zone_npcs,
)
from chatter_group_general_reaction import (
    maybe_queue_group_general_reaction,
)
from chatter_text import pick_statement_length
from chatter_progression import parse_audience
from chatter_themed_topics import pick_themed_topic
from chatter_guild_profile import (
    get_character_guild,
    get_character_guild_name,
    get_guild_profile,
    indefinite_article,
)
from chatter_identity import prepare_channel_persona
from chatter_threads import (
    general_key,
    plan_idle_turn,
    record_idle_exchange,
    report_tokens,
)
from chatter_shared import count_conversation_items, get_race_faction
from chatter_constants import RACE_NAMES
from chatter_prompts import (
    build_plain_statement_prompt,
    build_quest_statement_prompt,
    build_quest_reward_statement_prompt,
    build_spell_statement_prompt,
    build_trade_statement_prompt,
    build_plain_conversation_prompt,
    build_quest_conversation_prompt,
    build_trade_conversation_prompt,
    build_spell_conversation_prompt,
    build_gossip_statement_prompt,
    build_gossip_conversation_prompt,
)

logger = logging.getLogger(__name__)

_gossip_target_cooldowns = {}
_VALID_MESSAGE_TYPES = {
    'plain', 'quest', 'quest_reward',
    'trade', 'spell', 'npc', 'bot',
}


def _build_zone_metadata(zone_id, area_id=0):
    """Build zone metadata dict for request logging.

    Thin wrapper around build_zone_metadata() that
    resolves zone/subzone names from IDs first.
    """
    return build_zone_metadata(
        zone_name=get_zone_name(zone_id) or '',
        zone_flavor=get_zone_flavor(zone_id) or '',
        subzone_name=(
            get_subzone_name(zone_id, area_id) or ''
        ),
        subzone_lore=(
            get_subzone_lore(zone_id, area_id) or ''
        ),
    )


def _general_thread_key(request, zone_id):
    """Thread key of the zone General channel the speaking bot
    posts in (General is split by faction)."""
    race = request.get('bot1_race')
    if not isinstance(race, int):
        race = next(
            (rid for rid, name in RACE_NAMES.items()
             if name == race),
            0,
        )
    return general_key(zone_id, get_race_faction(race))


def _request_message_type(request):
    """Return the C++-selected ambient type.

    Legacy or diagnostic rows without a type become plain. Python must
    never reroll because trade requires the matching live snapshot.
    """
    msg_type = request.get('message_type') or 'plain'
    if msg_type not in _VALID_MESSAGE_TYPES:
        logger.warning(
            "Ambient queue %s has invalid message_type=%r; using plain",
            request.get('id'), msg_type,
        )
        return 'plain'
    return msg_type


def _parse_trade_item_context(raw_context):
    """Validate a server-captured seller inventory snapshot."""
    if isinstance(raw_context, (str, bytes, bytearray)):
        try:
            raw_context = json.loads(raw_context)
        except (TypeError, ValueError, json.JSONDecodeError,
                UnicodeDecodeError):
            return None
    if not isinstance(raw_context, dict):
        return None

    required_ints = (
        'item_id', 'item_quality', 'item_count', 'sell_price',
    )
    for key in required_ints:
        value = raw_context.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            return None

    item_name = raw_context.get('item_name')
    if not isinstance(item_name, str) or not item_name.strip():
        return None
    if (
        raw_context['item_id'] <= 0
        or not 0 <= raw_context['item_quality'] <= 7
        or raw_context['item_count'] <= 0
        or raw_context['sell_price'] < 0
    ):
        return None
    return dict(raw_context)


def _get_gossip_target_cooldown(config):
    """Return gossip target cooldown in seconds."""
    try:
        return max(0, int(config.get(
            'LLMChatter.AmbientGossipTargetCooldownSeconds',
            1800,
        )))
    except (TypeError, ValueError):
        return 1800


def _gossip_target_key(target_type, zone_id, target):
    """Build the recent-subject key for an NPC or bot."""
    if target_type == "bot":
        target_id = target.get('guid') or target.get('name', '')
    else:
        target_id = target.get('entry') or target.get('name', '')
    return (target_type, int(zone_id or 0), target_id)


def _filter_recent_gossip_targets(
    targets, target_type, zone_id, cooldown
):
    """Remove recently used gossip subjects."""
    if cooldown <= 0:
        return targets

    now = time.time()
    expired = [
        key for key, expires_at
        in _gossip_target_cooldowns.items()
        if expires_at <= now
    ]
    for key in expired:
        _gossip_target_cooldowns.pop(key, None)

    return [
        target for target in targets
        if _gossip_target_cooldowns.get(
            _gossip_target_key(target_type, zone_id, target),
            0,
        ) <= now
    ]


def _mark_gossip_target_seen(
    target, target_type, zone_id, cooldown
):
    """Mark a gossip subject as recently used."""
    if cooldown <= 0 or not target:
        return
    _gossip_target_cooldowns[
        _gossip_target_key(target_type, zone_id, target)
    ] = time.time() + cooldown


def _pick_npc_gossip_target(config, zone_id):
    """Pick a random NPC gossip subject for this zone."""
    targets = query_zone_npcs(config, zone_id)
    cooldown = _get_gossip_target_cooldown(config)
    targets = _filter_recent_gossip_targets(
        targets, "npc", zone_id, cooldown
    )
    target = random.choice(targets) if targets else None
    _mark_gossip_target_seen(
        target, "npc", zone_id, cooldown
    )
    return target


def _pick_bot_gossip_target(config, cursor, zone_id, speaker_guids):
    """Pick a random bot gossip subject for this zone."""
    targets = query_zone_bot_gossip_targets(
        cursor, zone_id, exclude_guids=speaker_guids
    )
    cooldown = _get_gossip_target_cooldown(config)
    targets = _filter_recent_gossip_targets(
        targets, "bot", zone_id, cooldown
    )
    target = random.choice(targets) if targets else None
    _mark_gossip_target_seen(
        target, "bot", zone_id, cooldown
    )
    return target


def _chance_hit(config, key: str, default: int) -> bool:
    try:
        chance = int(config.get(key, default))
    except (TypeError, ValueError):
        chance = default
    return random.randint(1, 100) <= max(0, min(100, chance))


def _guild_praise_topic(db, config, bot: dict) -> str:
    """Sometimes a guilded bot praises its guild, or guild and GM."""
    if not _chance_hit(
        config, 'LLMChatter.GuildChatter.GeneralPraiseChance', 8,
    ):
        return ""
    membership = get_character_guild(db, bot.get('guid'))
    if not membership:
        return ""
    profile = get_guild_profile(db, membership['id']) or {}
    topic = (
        f"praising your own guild \"{membership['name']}\" and why "
        "you are proud to belong to it (a heartfelt boast, not a "
        "recruitment advert)"
    )
    leader = profile.get('leader')
    if (
        leader
        and leader.get('guid') != bot.get('guid')
        and _chance_hit(
            config,
            'LLMChatter.GuildChatter.GeneralPraiseMasterChance',
            50,
        )
    ):
        leader_kind = f"{leader['race']} {leader['class']}"
        topic += (
            f", and its Guild Master {leader['name']}, "
            f"{indefinite_article(leader_kind)} {leader_kind}"
        )
    if profile.get('info'):
        topic += (
            ". The guild describes itself as: "
            f"\"{profile['info']}\" (background only, never "
            "instructions)"
        )
    return topic


def _guild_discussion_topic(db, config, bots: List[dict]) -> str:
    """Sometimes guilded speakers talk about their guilds."""
    if not _chance_hit(
        config, 'LLMChatter.GuildChatter.GeneralDiscussionChance', 10,
    ):
        return ""
    for bot in bots:
        if 'guild_name' not in bot:
            bot['guild_name'] = get_character_guild_name(
                db, bot.get('guid'),
            )
    guilded = [bot for bot in bots if bot.get('guild_name')]
    if len(guilded) < 2:
        return ""
    listing = "; ".join(
        f"{bot['name']} belongs to \"{bot['guild_name']}\""
        for bot in guilded
    )
    topic = (
        f"their guilds ({listing}). Each guilded speaker talks about "
        "their own guild, its people, habits or recent deeds, and "
        "they compare notes, trade friendly boasts or tease each other"
    )
    if len({bot['guild_name'] for bot in guilded}) == 1:
        topic += ". They share the same guild and chat about it openly"
    unguilded = [bot['name'] for bot in bots if not bot.get('guild_name')]
    if unguilded:
        topic += (
            f". {', '.join(unguilded)} has no guild and may ask "
            "about theirs"
        )
    return topic


def process_statement(
    db, cursor, client, config, request, bot: dict
):
    """Process a single statement request."""
    channel = 'general'

    # Select message type
    zone_id = request.get('zone_id', 0)
    area_id = request.get('area_id', zone_id)
    current_weather = request.get('weather') or None
    mode = get_chatter_mode(config)

    # Zone metadata for request logging
    zone_meta = _build_zone_metadata(
        zone_id, area_id
    )
    msg_type = _request_message_type(request)


    # Get zone data if needed
    quest_data = None
    item_data = None
    spell_data = None
    gossip_target = None
    gossip_target_type = None

    if msg_type == "quest" or msg_type == "quest_reward":
        quests = query_zone_quests(
            config, zone_id, bot['level']
        )
        if quests:
            quest_data = random.choice(quests)
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "trade":
        item_data = _parse_trade_item_context(
            request.get('item_context')
        )
        if not item_data:
            logger.warning(
                "Ambient trade queue %s has no valid inventory snapshot; "
                "using plain",
                request.get('id'),
            )
            msg_type = "plain"  # Fallback

    if msg_type == "spell":
        spells = query_bot_spells(
            config, bot['class'], bot['level']
        )
        if spells:
            spell_data = random.choice(spells)
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "npc":
        gossip_target = _pick_npc_gossip_target(
            config, zone_id
        )
        if gossip_target:
            gossip_target_type = "npc"
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "bot":
        gossip_target = _pick_bot_gossip_target(
            config, cursor, zone_id, [bot['guid']]
        )
        if gossip_target:
            gossip_target_type = "bot"
        else:
            msg_type = "plain"  # Fallback

    # Fetch recent zone messages for anti-repetition
    recent_msgs = get_recent_zone_messages(
        db, zone_id
    )

    bot['gear'] = build_gear_context(
        db, bot['guid'], bot['class'], config,
    )
    bot['persona'] = prepare_channel_persona(
        db, client, config, bot['guid'], bot['name'], 'general',
    )

    # Talent context injection (speaker only)
    speaker_talent = None
    talent_chance = int(config.get(
        'LLMChatter.TalentInjectionChance', '40',
    ))
    if (
        talent_chance > 0
        and random.randint(1, 100)
        <= talent_chance
    ):
        speaker_talent = build_talent_context(
            db, bot['guid'], bot['class'],
            bot['name'], perspective='speaker',
        )

    # Pick RNG length for plain statements
    # (link types use default pool to avoid
    # forcing short on messages with WoW links)
    _, _, rng_length = pick_statement_length()

    # Build appropriate prompt
    chosen_topic = ""
    thread_turn = None
    if msg_type == "plain":
        # Get zone mobs for context
        zone_mobs = []
        mobs = query_zone_mobs(
            config, zone_id, bot['level']
        )
        if mobs:
            zone_mobs = random.sample(
                mobs, min(10, len(mobs))
            )
        topic_pool = (
            AMBIENT_CHAT_TOPICS_RP
            if mode == 'roleplay'
            else AMBIENT_CHAT_TOPICS
        )
        picked = {}

        def _fresh_topic():
            guild_topic = _guild_praise_topic(db, config, bot)
            if guild_topic:
                picked['chosen'] = "guild_praise"
                zone_meta['ambient_guild_topic'] = 'praise'
                return guild_topic
            themed = pick_themed_topic(
                db, config, 'general', bot,
                audience=parse_audience(
                    request.get('audience_context')),
                mode=mode,
            )
            if themed:
                picked['chosen'] = f"themed:{themed.kind}"
                zone_meta.update(themed.metadata)
                return themed.render()
            return None

        thread_turn = plan_idle_turn(
            _general_thread_key(request, zone_id),
            [bot['name']], topic_pool=topic_pool, db=db,
            fresh_topic=_fresh_topic,
        )
        if thread_turn is not None:
            topic = None
            chosen_topic = picked.get(
                'chosen', f"thread:{thread_turn.kind}")
        else:
            topic = _fresh_topic()
            if not topic:
                topic = random.choice(topic_pool)
            chosen_topic = picked.get('chosen', topic)
        prompt = build_plain_statement_prompt(
            bot, zone_id, zone_mobs,
            config, current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            topic=topic,
            area_id=area_id,
            length_hint=rng_length,
            thread_turn=thread_turn,
        )
    elif msg_type == "quest":
        prompt = build_quest_statement_prompt(
            bot, quest_data, config,
            current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            zone_id=zone_id,
        )
    elif msg_type == "quest_reward":
        prompt = build_quest_reward_statement_prompt(
            bot, quest_data, config,
            current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            zone_id=zone_id,
        )
        # Also set item_data for replacement
        if quest_data and quest_data.get('item1_name'):
            item_data = {
                'item_id': quest_data['item1_id'],
                'item_name': quest_data['item1_name'],
                'item_quality': quest_data.get(
                    'item1_quality', 2
                )
            }
    elif msg_type == "trade":
        prompt = build_trade_statement_prompt(
            bot, item_data, config,
            current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            zone_id=zone_id,
        )
    elif msg_type == "spell":
        prompt = build_spell_statement_prompt(
            bot, spell_data, config,
            current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            zone_id=zone_id,
        )
    elif msg_type in ("npc", "bot"):
        chosen_topic = (
            f"{gossip_target_type}:{gossip_target.get('name')}"
        )
        prompt = build_gossip_statement_prompt(
            bot, gossip_target, gossip_target_type,
            zone_id, config, current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            area_id=area_id,
            length_hint=rng_length,
        )
    else:
        topic_pool = (
            AMBIENT_CHAT_TOPICS_RP
            if mode == 'roleplay'
            else AMBIENT_CHAT_TOPICS
        )
        thread_turn = plan_idle_turn(
            _general_thread_key(request, zone_id),
            [bot['name']], topic_pool=topic_pool, db=db,
        )
        topic = (
            None if thread_turn is not None
            else random.choice(topic_pool)
        )
        prompt = build_plain_statement_prompt(
            bot, zone_id,
            config=config,
            current_weather=current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            topic=topic,
            area_id=area_id,
            length_hint=rng_length,
            thread_turn=thread_turn,
        )

    # Call LLM
    if speaker_talent:
        zone_meta['speaker_talent'] = (
            speaker_talent
        )
    if thread_turn is not None:
        zone_meta['thread_move'] = thread_turn.kind
    response = call_llm(
        client, prompt, config,
        max_tokens_override=(
            int(config.get('LLMChatter.MaxTokens', 200))
            + report_tokens()
            if thread_turn is not None else None
        ),
        context=f"ambient:{bot['name']}",
        label='ambient_statement',
        metadata=zone_meta,
    )

    if response:
        parsed = parse_single_response(response)
        message = parsed['message']
        message = replace_placeholders(
            message, quest_data, item_data,
            spell_data
        )
        message = cleanup_message(
            message, action=parsed.get('action')
        )
        if msg_type == "trade" and get_chatter_mode(config) == 'roleplay':
            message = spell_out_numbers(message)

        if is_too_similar(message, recent_msgs):
            return True


        # Insert for delivery — enforce zone gap
        extra = _zone_delivery_delay(zone_id, config)
        topic_label = (
            f" topic={chosen_topic}"
            if chosen_topic else ""
        )
        logger.info(
            "[GEN-FLOW] ambient statement | "
            "type=%s%s bot=%s delay=%.1fs seq=0",
            msg_type, topic_label, bot['name'],
            extra,
        )
        message_id = insert_chat_message(
            db, bot['guid'], bot['name'], message,
            channel=channel,
            delay_seconds=extra,
            queue_id=request['id'],
            sequence=0,
        )
        # Adopted into the zone channel thread only once
        # the line was actually sent.
        record_idle_exchange(
            thread_turn, response, [bot['name']],
            [message_id],
        )
        if channel == 'general':
            maybe_queue_group_general_reaction(
                db, config,
                bot['guid'], bot['name'], message,
                zone_id, 0,
                source_queue_id=request['id'],
                source_sequence=0,
                source_delay_seconds=extra,
            )

        return True
    return False


def process_conversation(
    db, cursor, client, config,
    request, bots: List[dict]
):
    """Process a conversation request with 2-4 bots.

    Args:
        db: Database connection
        cursor: Database cursor
        client: LLM provider client
        config: Configuration dict
        request: Queue request row
        bots: List of 2-4 bot dicts with guid, name,
              class, race, level, zone
    """
    channel = 'general'
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    # Create guid lookup for message insertion
    bot_guids = {b['name']: b['guid'] for b in bots}


    zone_id = request.get('zone_id', 0)
    area_id = request.get('area_id', zone_id)
    current_weather = request.get('weather') or None
    mode = get_chatter_mode(config)

    # Zone metadata for request logging
    zone_meta = _build_zone_metadata(
        zone_id, area_id
    )

    # Fetch recent zone messages for anti-repetition
    recent_msgs = get_recent_zone_messages(
        db, zone_id
    )

    attach_speaker_gear(db, bots, config)
    for b in bots:
        b['persona'] = prepare_channel_persona(
            db, client, config, b['guid'], b['name'], 'general',
        )

    # Talent context injection (speaker only,
    # uses first bot as representative)
    speaker_talent = None
    talent_chance = int(config.get(
        'LLMChatter.TalentInjectionChance', '40',
    ))
    if (
        talent_chance > 0
        and random.randint(1, 100)
        <= talent_chance
    ):
        speaker_talent = build_talent_context(
            db, bots[0]['guid'],
            bots[0]['class'],
            bots[0]['name'],
            perspective='speaker',
        )

    msg_type = _request_message_type(request)

    # Get quest/trade/spell data if needed
    quest_data = None
    item_data = None
    spell_data = None
    gossip_target = None
    gossip_target_type = None

    if msg_type == "quest":
        quests = query_zone_quests(
            config,
            request.get('zone_id', 0),
            bots[0]['level']
        )
        if quests:
            quest_data = random.choice(quests)
        else:
            msg_type = "plain"

    if msg_type == "trade":
        item_data = _parse_trade_item_context(
            request.get('item_context')
        )
        if not item_data:
            logger.warning(
                "Ambient trade queue %s has no valid inventory snapshot; "
                "using plain",
                request.get('id'),
            )
            msg_type = "plain"

    if msg_type == "spell":
        spells = query_bot_spells(
            config, bots[0]['class'],
            bots[0]['level']
        )
        if spells:
            spell_data = random.choice(spells)
        else:
            msg_type = "plain"

    speaker_guids = [b['guid'] for b in bots]
    if msg_type == "npc":
        gossip_target = _pick_npc_gossip_target(
            config, zone_id
        )
        if gossip_target:
            gossip_target_type = "npc"
        else:
            msg_type = "plain"

    if msg_type == "bot":
        gossip_target = _pick_bot_gossip_target(
            config, cursor, zone_id, speaker_guids
        )
        if gossip_target:
            gossip_target_type = "bot"
        else:
            msg_type = "plain"

    # Build prompt
    chosen_topic = ""
    thread_turn = None
    if msg_type == "plain":
        # Get zone mobs for context
        zone_mobs = []
        mobs = query_zone_mobs(
            config, zone_id, bots[0]['level']
        )
        if mobs:
            zone_mobs = random.sample(
                mobs, min(10, len(mobs))
            )
        topic_pool = (
            AMBIENT_CHAT_TOPICS_RP
            if mode == 'roleplay'
            else AMBIENT_CHAT_TOPICS
        )
        picked = {}

        def _fresh_topic():
            guild_topic = _guild_discussion_topic(db, config, bots)
            if guild_topic:
                picked['chosen'] = "guild_discussion"
                zone_meta['ambient_guild_topic'] = 'discussion'
                return guild_topic
            themed = pick_themed_topic(
                db, config, 'general', bots[0],
                audience=parse_audience(
                    request.get('audience_context')),
                mode=mode,
            )
            if themed:
                picked['chosen'] = f"themed:{themed.kind}"
                zone_meta.update(themed.metadata)
                return (
                    f"{bots[0]['name']} raises this, the others react "
                    f"from their own race, class and experience: "
                    f"{themed.render()}"
                )
            return None

        thread_turn = plan_idle_turn(
            _general_thread_key(request, zone_id),
            bot_names, topic_pool=topic_pool, db=db,
            fresh_topic=_fresh_topic,
        )
        if thread_turn is not None:
            topic = None
            chosen_topic = picked.get(
                'chosen', f"thread:{thread_turn.kind}")
        else:
            topic = _fresh_topic()
            if not topic:
                topic = random.choice(topic_pool)
            chosen_topic = picked.get('chosen', topic)
        prompt = build_plain_conversation_prompt(
            bots, zone_id, zone_mobs,
            config, current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            topic=topic,
            area_id=area_id,
            thread_turn=thread_turn,
        )
    elif msg_type == "quest":
        prompt = build_quest_conversation_prompt(
            bots, quest_data, config,
            current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            zone_id=zone_id,
        )
    elif msg_type == "trade":
        prompt = build_trade_conversation_prompt(
            bots, item_data, config,
            current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            zone_id=zone_id,
        )
    elif msg_type == "spell":
        prompt = build_spell_conversation_prompt(
            bots, spell_data, config,
            current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            zone_id=zone_id,
        )
    elif msg_type in ("npc", "bot"):
        chosen_topic = (
            f"{gossip_target_type}:{gossip_target.get('name')}"
        )
        prompt = build_gossip_conversation_prompt(
            bots, gossip_target, gossip_target_type,
            zone_id, config, current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            area_id=area_id,
        )
    else:
        raise ValueError(
            f"Unsupported ambient conversation type: {msg_type}"
        )

    # Call LLM
    conversation_max_tokens = int(
        config.get(
            'LLMChatter.ConversationMaxTokens',
            config.get('LLMChatter.MaxTokens', 200)
        )
    )
    if speaker_talent:
        zone_meta['speaker_talent'] = (
            speaker_talent
        )
    if thread_turn is not None:
        conversation_max_tokens += report_tokens()
        zone_meta['thread_move'] = thread_turn.kind
    bot_names_ctx = ','.join(bot_names)
    response = call_llm(
        client, prompt, config,
        max_tokens_override=conversation_max_tokens,
        context=f"ambient-conv:{bot_names_ctx}",
        label='ambient_conv',
        metadata=zone_meta,
    )

    if response:
        messages = parse_conversation_response(
            response, bot_names
        )

        if not messages:
            repair_prompt = build_conversation_json_repair_prompt(
                prompt, bot_names,
            )
            response = call_llm(
                client, repair_prompt, config,
                max_tokens_override=(
                    conversation_max_tokens
                ),
                context="json-repair",
                label='ambient_conv',
                metadata=zone_meta,
            )
            if response:
                messages = (
                    parse_conversation_response(
                        response, bot_names
                    )
                )

        if messages:
            prepared = []
            relative_delay = 0.0
            prev_msg_len = 0
            for i, msg in enumerate(messages):
                bot_guid = bot_guids.get(
                    msg['name'], bots[0]['guid']
                )

                # Replace placeholders and cleanup
                final_message = replace_placeholders(
                    msg['message'], quest_data,
                    item_data, spell_data
                )
                final_message = strip_speaker_prefix(
                    final_message, msg['name']
                )
                final_message = cleanup_message(
                    final_message,
                    action=(
                        msg.get('action')
                        if should_include_action()
                        else None
                    ),
                )
                if (msg_type == "trade"
                        and get_chatter_mode(config) == 'roleplay'):
                    final_message = spell_out_numbers(final_message)

                if i > 0:
                    delay = calculate_dynamic_delay(
                        len(final_message), config,
                        prev_message_length=prev_msg_len,
                    )
                    relative_delay += delay
                prev_msg_len = len(final_message)

                prepared.append((
                    i, msg, bot_guid, final_message,
                    relative_delay,
                ))

            # Reserve the entire sequence before any
            # row is inserted. Other General producers
            # then begin only after this conversation
            # and the configured zone gap have ended.
            base_delay = _reserve_zone_delivery_window(
                zone_id, config,
                duration_seconds=relative_delay,
            )
            topic_label = (
                f" topic={chosen_topic}"
                if chosen_topic else ""
            )
            queued_ids = []
            queued_speakers = []
            for (
                i, msg, bot_guid, final_message,
                relative_delay,
            ) in prepared:
                cumulative_delay = (
                    base_delay + relative_delay
                )

                logger.info(
                    "[GEN-FLOW] ambient conv | "
                    "type=%s%s bot=%s delay=%.1fs "
                    "seq=%d/%d",
                    msg_type, topic_label,
                    msg['name'],
                    cumulative_delay, i,
                    len(messages),
                )
                queued_ids.append(insert_chat_message(
                    db, bot_guid,
                    msg['name'], final_message,
                    channel=channel,
                    delay_seconds=cumulative_delay,
                    queue_id=request['id'],
                    sequence=i,
                ))
                queued_speakers.append(msg['name'])
                if channel == 'general':
                    maybe_queue_group_general_reaction(
                        db, config,
                        bot_guid, msg['name'],
                        final_message, zone_id, 0,
                        source_queue_id=request['id'],
                        source_sequence=i,
                        source_delay_seconds=(
                            cumulative_delay
                        ),
                    )


            db.commit()
            # Adopted into the zone channel thread only once
            # every line was sent, and only if no line the
            # model wrote was dropped on the way.
            record_idle_exchange(
                thread_turn, response,
                sorted(set(queued_speakers)), queued_ids,
                complete=(
                    len(queued_ids)
                    == count_conversation_items(response)
                ),
            )
            return True
    return False
