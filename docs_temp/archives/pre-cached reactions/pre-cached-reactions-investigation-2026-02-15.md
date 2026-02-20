# Pre-Cached Reactions (Instant Delivery) - Investigation Report

Date: 2026-02-15
Scope: Identify where pre-cached instant reactions are needed now, and propose an elegant implementation that fits current `mod-llm-chatter` architecture.

## 1) Problem Summary

Current combat chatter pipeline is too slow for "live moment" reactions:

1. C++ hook inserts `llm_chatter_events` row (with `react_after`).
2. Python bridge polls every `LLMChatter.Bridge.PollIntervalSeconds` (default 3s).
3. Bridge processes one pending event per loop (`LIMIT 1`).
4. Bridge calls LLM synchronously.
5. Bridge inserts `llm_chatter_messages` with an additional delay (`delay_seconds`).
6. C++ delivers pending messages on `DeliveryPollMs` cadence (default 1000 ms).

This is excellent for non-urgent flavor chat, but too late for combat callouts.

## 2) Evidence From Current Implementation

### Latency sources in current code

- Bridge poll interval default: `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist:324`
- Bridge sleeps on idle: `modules/mod-llm-chatter/tools/llm_chatter_bridge.py:2267`
- Event fetch is single row per loop (`LIMIT 1`): `modules/mod-llm-chatter/tools/llm_chatter_bridge.py:1011`
- LLM call is synchronous in handlers (example combat): `modules/mod-llm-chatter/tools/chatter_group.py:2620`
- Message insertion adds extra delay (example combat 1s): `modules/mod-llm-chatter/tools/chatter_group.py:2653`
- C++ message delivery poll loop: `modules/mod-llm-chatter/src/LLMChatterScript.cpp:1955`
- C++ message ready query is also `LIMIT 1`: `modules/mod-llm-chatter/src/LLMChatterScript.cpp:1973`

### Existing pre-cache precedent (farewell)

- Pre-generated in Python on join: `modules/mod-llm-chatter/tools/chatter_group.py:331`, `modules/mod-llm-chatter/tools/chatter_group.py:2113`
- Stored in DB (`farewell_msg`): `modules/mod-llm-chatter/data/sql/db-characters/base/llm_chatter_tables.sql:143`
- Delivered instantly from C++ on remove (no LLM call): `modules/mod-llm-chatter/src/LLMChatterScript.cpp:2372`

This confirms the pattern is already valid in your codebase.

## 3) Event Inventory - Where Instant Matters

### Tier A (must pre-cache first)

These are combat-time and lose value if delayed:

1. `bot_group_combat` (pull/opening cry)
- Event queued with short react window: `modules/mod-llm-chatter/src/LLMChatterScript.cpp:3492`
- Bridge still does LLM call then 1s send delay: `modules/mod-llm-chatter/tools/chatter_group.py:2620`, `modules/mod-llm-chatter/tools/chatter_group.py:2653`

2. `bot_group_spell_cast` (heal/cc/shield/buff/reactive spell commentary)
- Event queue point: `modules/mod-llm-chatter/src/LLMChatterScript.cpp:4533`
- Bridge does full LLM call and 2-3s send delay: `modules/mod-llm-chatter/tools/chatter_group.py:4023`, `modules/mod-llm-chatter/tools/chatter_group.py:4053`

3. `bot_group_low_health`
- Event produced by periodic combat-state checks: `modules/mod-llm-chatter/src/LLMChatterScript.cpp:5106`
- Event queued as fast path but still LLM-dependent: `modules/mod-llm-chatter/src/LLMChatterScript.cpp:5037`
- Bridge uses LLM + 1s delay: `modules/mod-llm-chatter/tools/chatter_group.py:4917`, `modules/mod-llm-chatter/tools/chatter_group.py:4946`

4. `bot_group_oom`
- Same pattern as low-health: `modules/mod-llm-chatter/tools/chatter_group.py:5038`, `modules/mod-llm-chatter/tools/chatter_group.py:5067`

5. `bot_group_aggro_loss`
- Same pattern as low-health: `modules/mod-llm-chatter/tools/chatter_group.py:5163`, `modules/mod-llm-chatter/tools/chatter_group.py:5192`

### Tier B (recommended after Tier A)

1. `bot_group_death`
- Time-sensitive in combat pressure moments.
- Current path still LLM-based + delay: `modules/mod-llm-chatter/tools/chatter_group.py:2816`, `modules/mod-llm-chatter/tools/chatter_group.py:2846`

2. `bot_group_wipe`
- Emotional beat, less "split-second critical" than A, but benefits from instant.

3. `bot_group_kill` (especially non-boss chain pulls)
- Not as strict as pull/spell/callouts, but still improved by cache.

### Tier C (generally not required for instant)

- `bot_group_loot`, `bot_group_zone_transition`, `bot_group_dungeon_entry`, `bot_group_corpse_run`, `bot_group_quest_*`, `bot_group_levelup`, `bot_group_achievement`.
- Flavor events where 2-8s latency is acceptable.

## 4) Recommended Architecture

Use a hybrid design:

1. C++ consumes cached responses for urgent combat events and sends immediately.
2. Python generates/replenishes cached responses asynchronously in background.
3. On cache miss, fallback to current event->bridge->LLM path.

This preserves quality and reliability while making urgent events instant.

### Why this is the right fit

- Matches existing farewell model (pre-generate + instant send).
- Keeps C++ in charge of low-latency delivery (already architectural principle in docs).
- Keeps Python/LLM in orchestration layer.
- Safe rollback path: cache miss simply uses current logic.

## 5) Proposed Data Model

New table in characters DB:

`llm_group_cached_responses`

Suggested columns:

- `id` (PK)
- `group_id` (INT UNSIGNED)
- `bot_guid` (INT UNSIGNED)
- `event_category` (VARCHAR/ENUM)
- `variant_key` (VARCHAR, nullable)  
  Example: `spell:heal:self`, `spell:cc:other`, `combat:pull`, `state:oom`
- `message` (VARCHAR(255))
- `emote` (VARCHAR(32), nullable)
- `status` (`ready`, `reserved`, `used`, `expired`)
- `created_at`, `expires_at`, `used_at`

Indexes:

- `(group_id, bot_guid, event_category, status, created_at)`
- `(expires_at)`

## 6) Category Design (Phase 1)

Use coarse categories first (avoid over-fragmentation):

- `combat_pull`
- `state_low_health`
- `state_oom`
- `state_aggro_loss`
- `spell_heal_self`
- `spell_heal_other`
- `spell_cc_self`
- `spell_cc_other`
- `spell_shield`
- `spell_buff`

Optional later:

- `death_reaction`
- `wipe_reaction`
- `kill_reaction`

## 7) Runtime Flow

### A) On urgent event fire (C++)

1. Map event -> cache category (+ optional variant).
2. Try atomically consume one `ready` cached row.
3. If hit:
- Send instantly in party chat (same style as farewell immediate path).
- Mark cached row `used`.
- Enqueue background refill job/event.
- Optionally write observability record.
4. If miss:
- Keep existing behavior (insert normal event row).

### B) Background refill (Python)

1. Refill worker reads pending refill jobs.
2. Builds prompt with bot traits + role/state context.
3. Generates short message (`max_tokens` small).
4. Stores cache row as `ready`.
5. Maintains target buffer depth per category (e.g., 2-4 ready lines each).

## 8) Buffer Strategy

Per bot in active real-player group:

- `combat_pull`: target depth 2
- each spell variant: depth 2
- each state callout category: depth 3

Warm-up moments:

- On group join completion (low-priority batch)
- On combat start (high-priority refill for combat categories)
- After every cache consume (single immediate refill request)

## 9) Key Implementation Points

### C++ changes

- Add cache consume helper in `LLMChatterScript.cpp` near group helper block.
- Integrate into hooks currently queuing urgent events:
  - combat engage
  - spell cast
  - state callouts (low hp/oom/aggro)
- Keep current queue insert as fallback.

### Python changes

- Add cached-response generator module (can live in `chatter_group.py` first, then split later).
- Add refill job processing in bridge main loop.
- Ensure refill processing is lower priority than live events.

### SQL changes

- Base schema + migration for new cache table.
- Optional refill job table if not piggybacking on `llm_chatter_events`.

## 10) Risks and Mitigations

1. Cache staleness (message not matching exact target/spell name)
- Keep categories general and short.
- Prefer "functional callout" style lines over highly specific content.

2. Repetition
- Maintain multiple cached lines per category.
- Refill with anti-repetition context using recent bot lines.

3. Overhead/cost from aggressive prefill
- Hard cap per bot/group/category.
- Refill only when below target depth.
- Backoff when group not in combat.

4. Miss storms after restart
- Warm caches on `bot_group_join` and at first combat detection.
- Fallback path ensures no functional regression.

## 11) Recommended Rollout Plan

Phase 1 (highest value):

1. Table + basic refill worker.
2. Pre-cache and consume for:
- `bot_group_combat`
- `bot_group_low_health`
- `bot_group_oom`
- `bot_group_aggro_loss`

Phase 2:

1. Add spell category cache variants.
2. Tune depth and refill pacing.

Phase 3:

1. Extend to `death` and `wipe`.
2. Evaluate whether `kill` needs inclusion.

## 12) Final Recommendation

Implement pre-cached instant delivery now for all Tier A combat events.  
This is the correct place to invest first because these are exactly the reactions that lose player value when delayed.  
Use the farewell pattern as architectural precedent, but implement it as a generalized per-category cache with C++ fast consume + Python async refill + fallback to current event flow.

