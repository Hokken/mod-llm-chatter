# mod-llm-chatter Architecture

Last updated: 2026-02-19 (after N1-N17 refactor series)

## Purpose

Reference architecture for humans and LLMs editing `modules/mod-llm-chatter`.

This document is intentionally explicit about confusing areas and compatibility layers. Read sections `Confusion Traps` and `Edit Decision Matrix` before making structural changes.

## Scope and Repository Boundaries

- AzerothCore root repo: `C:\azerothcore-wotlk`
- Module repo (separate git repo): `C:\azerothcore-wotlk\modules\mod-llm-chatter`
- Most code changes for chatter behavior belong in the module repo, not the root repo.
- This architecture doc lives in root docs for shared reference, but describes module code.

## High-Level Runtime Flow

1. C++ scripts queue events/requests in MySQL.
2. Python bridge polls, claims, and processes queue items.
3. Python writes generated messages back to DB.
4. C++ delivery tick sends messages in game.
5. Emotes are only played for party channel delivery.

## Main Loops in Python Bridge

`modules/mod-llm-chatter/tools/llm_chatter_bridge.py` runs three loops:

1. Event loop: fetch pending events -> process in thread pool.
2. Ambient queue loop: process `statement` and `conversation` requests from `llm_chatter_queue`.
3. Pre-cache refill loop: top up `llm_group_cached_responses`.

## Current Python Module Map (Post Refactor)

### Entry and orchestration

| File | Approx lines | Primary ownership |
|---|---:|---|
| `tools/llm_chatter_bridge.py` | 1979 | Process loops, event claiming, event routing, worker orchestration |
| `tools/chatter_ambient.py` | 703 | Ambient `process_statement` and `process_conversation` implementations |

### Group domain (party channel)

| File | Approx lines | Primary ownership |
|---|---:|---|
| `tools/chatter_group.py` | 2472 | Group join, group player message flow, idle chatter, composition helpers, compatibility exports |
| `tools/chatter_group_handlers.py` | 3254 | All group reaction event handlers (`bot_group_kill`, `bot_group_loot`, etc.) |
| `tools/chatter_group_prompts.py` | 2853 | Group prompt builders (event, player, pre-cache prompt templates) |
| `tools/chatter_group_state.py` | 491 | Group mood/traits state + chat history helper functions |

### Shared layers

| File | Approx lines | Primary ownership |
|---|---:|---|
| `tools/chatter_shared.py` | 1218 | Compatibility facade + residual utilities + reaction pipeline orchestration |
| `tools/chatter_text.py` | 474 | Parsing/sanitization/anti-repetition text helpers |
| `tools/chatter_llm.py` | 327 | Provider/model calls (`call_llm`, quick analyzer) |
| `tools/chatter_db.py` | 700 | DB connection + delivery insert + zone/query helpers + cache |

### Prompt/data/event support

| File | Approx lines | Primary ownership |
|---|---:|---|
| `tools/chatter_prompts.py` | 2338 | Ambient/event prompt builders |
| `tools/chatter_general.py` | 771 | General channel player message reaction flow |
| `tools/chatter_cache.py` | 425 | Pre-cache refill logic |
| `tools/chatter_events.py` | 729 | Event context building and event cleanup helpers |
| `tools/chatter_constants.py` | 2163 | Static data and configuration constants |
| `tools/spell_names.py` | 67 | Loader for `spell_names.json` |
| `tools/spell_names.json` | data | Spell names/descriptions dataset |
| `tools/import_smoke_check.py` | 82 | Import/cycle smoke check (default stubs, optional strict mode) |

## C++ Module Components

| File | Primary ownership |
|---|---|
| `src/LLMChatterScript.cpp` | Event hooks, DB queue inserts, pre-cache consumption, message delivery, party emote playback |
| `src/LLMChatterConfig.h/.cpp` | Config loading |
| `src/llm_chatter_loader.cpp` | Module registration |

## Event Routing and Handler Ownership

Bridge routing is map-driven via `EVENT_HANDLERS` in `tools/llm_chatter_bridge.py`.

- Group events (`bot_group_*`) route to group handlers.
- `player_general_msg` routes through adapter `_dispatch_player_general_msg`.
- Unknown/unmapped events fall through to bridge orchestration path (zone/global statement or conversation).

### Important signature mismatch

- Group handlers use `(db, client, config, event)`.
- `process_general_player_msg_event` uses `(event, db, client, config)`.
- Bridge adapter `_dispatch_player_general_msg` reorders arguments.
- Do not remove adapter unless signatures are standardized everywhere.

## Ambient Processing Ownership

- Bridge still defines `process_statement(...)` and `process_conversation(...)` as compatibility delegates.
- Real logic is in `tools/chatter_ambient.py`.
- If behavior changes in ambient generation, edit `chatter_ambient.py` first.

## Shared Layer After Decomposition

`tools/chatter_shared.py` is now a stable facade and residual utility layer.

It re-exports moved functions from:

- `chatter_text.py`
- `chatter_llm.py`
- `chatter_db.py`

Residual functions intentionally still in `chatter_shared.py` include:

- Name and mode lookups
- RP context builders
- Link/context formatting helpers
- JSON instruction helpers
- Message type and delay helpers
- `run_single_reaction(...)` orchestration
- Conversation parsing and anti-repetition context builder

Do not assume function implementation is local just because it is imported from `chatter_shared`.

## JSON Output Contracts

### Statement responses

Helper: `append_json_instruction(...)` in `chatter_shared.py`

Expected shape:

```json
{"message": "...", "emote": null, "action": null}
```

### Conversation responses

Helper: `append_conversation_json_instruction(...)` in `chatter_shared.py`

Expected shape:

```json
[
  {"speaker": "BotA", "message": "...", "emote": null, "action": null},
  {"speaker": "BotB", "message": "...", "emote": null, "action": null}
]
```

## Channel and Emote Semantics

- Party channel (`party`): emotes may be used and played by C++.
- General channel (`general`): prompt rules force `emote: null`; delivery does not play emotes.
- C++ additionally guards emote playback by channel check.

This is intentional due to visibility mismatch of text emotes versus zone-wide audience.

## Pre-cache Path (Separate from Live Event Path)

Pre-cache generation is handled by `tools/chatter_cache.py` and consumed by C++ (`TryConsumeCachedReaction`).

Important:

- Pre-cache prompt builders now live in `chatter_group_prompts.py`.
- Pre-cache uses its own generation loop and does not go through `run_single_reaction`.
- C++ attempts cache consume first for configured categories and falls back to live generation when needed.

## Database Tables and State Semantics

| Table | Producer | Consumer | Notes |
|---|---|---|---|
| `llm_chatter_events` | C++ | Python bridge | Event queue; status transitions include `pending`, `processing`, `completed`, `failed`, `skipped`, `expired` |
| `llm_chatter_queue` | C++ | Python bridge | Ambient requests (`statement`, `conversation`) |
| `llm_chatter_messages` | Python | C++ | Outbound messages; C++ marks delivered |
| `llm_group_cached_responses` | Python | C++ | Pre-cache rows for instant reactions |
| `llm_group_bot_traits` | Python | Python | Group personality state |
| `llm_group_chat_history` | Python | Python | Group anti-repetition history |
| `llm_general_chat_history` | Python | Python | General anti-repetition history |

## Import Topology (Practical View)

- `llm_chatter_bridge.py` depends on most runtime modules.
- `chatter_ambient.py` depends on prompts + shared facade.
- `chatter_group.py` composes state/prompts/handlers modules.
- `chatter_prompts.py` depends on constants + shared facade.
- `chatter_events.py` depends on constants + shared facade.
- `chatter_shared.py` depends on constants + decomposed leaf modules.
- Leaf modules:
  - `chatter_text.py`: text parsing/cleanup
  - `chatter_llm.py`: provider calls
  - `chatter_db.py`: database and cache/query helpers

If import cycles appear, check recent cross-imports into `chatter_shared.py` first.

## Confusion Traps (Read Before Editing)

### 1) Two repos in one workspace

- Confusion: editing root repo files when code change belongs in module repo.
- Reality: chatter runtime code is in `modules/mod-llm-chatter`.

### 2) `chatter_shared.py` looks like monolith, but is partly facade

- Confusion: assuming all helpers are implemented in `chatter_shared.py`.
- Reality: many are re-exported from `chatter_text.py`, `chatter_llm.py`, `chatter_db.py`.

### 3) Duplicate-looking helper names are intentional

- `get_zone_level_range` exists in shared (public) and `_get_zone_level_range` in DB (private, cycle-safe).
- `validate_emote` exists in DB and `_validate_emote` in text parser path.
- Do not deduplicate blindly without checking import-cycle implications.

### 4) Bridge ambient wrappers are delegates

- Confusion: changing `process_statement` in bridge expecting behavior change.
- Reality: bridge wrappers call `chatter_ambient.process_statement/process_conversation`.

### 5) General chat handler signature is different

- Confusion: direct map call without adapter breaks arg order.
- Reality: keep `_dispatch_player_general_msg` unless signatures are standardized.

### 6) Group split is partial, not full facade

- Confusion: expecting `chatter_group.py` to be tiny.
- Reality: `chatter_group.py` still owns join/player-msg/idle orchestration and exports handlers for compatibility.

### 7) Pre-cache path bypasses some live path abstractions

- Confusion: expecting pre-cache to use same runner as group handlers.
- Reality: pre-cache has independent generation logic in `chatter_cache.py`.

### 8) Provider imports exist in two places by design

- `llm_chatter_bridge.py` imports provider SDKs for main client initialization/type hints.
- `chatter_llm.py` lazily imports inside quick-analyze client path.
- Do not "clean up" one without validating both runtime paths.

### 9) Default import smoke is non-strict

- `tools/import_smoke_check.py` stubs optional deps by default.
- Use `--strict` to require real `anthropic`, `openai`, and `mysql.connector`.

### 10) Zone cache keying may look odd

- `ZoneDataCache.get_loot(min_level, max_level)` signature suggests level-range keys.
- Current callers pass `(zone_id, 0)` to `get_loot/set_loot`, repurposing `zone_id` as a cache key in the first slot.
- This is legacy-compatible behavior; change only with deliberate cache strategy update.

### 11) Event status meaning is distributed

- Some skip/fail/completed decisions happen in handlers.
- Others happen in bridge catch/fallback paths.
- Preserve status transitions when refactoring, especially error branches.

### 12) Channel behavior is enforced in multiple layers

- Prompt layer sets/encourages `emote: null` in general channel.
- Python insert path can still store emote field.
- C++ delivery finally guards emote playback to party only.
- Do not assume a single gate.

## Edit Decision Matrix (Where to Change What)

| If you need to change... | Primary file |
|---|---|
| Main polling loops, event claim logic, worker behavior | `tools/llm_chatter_bridge.py` |
| Ambient statement/conversation runtime logic | `tools/chatter_ambient.py` |
| Group event reaction runtime behavior | `tools/chatter_group_handlers.py` |
| Group join/player-msg/idle behavior | `tools/chatter_group.py` |
| Group prompt wording/templates | `tools/chatter_group_prompts.py` |
| Shared parsing/sanitization | `tools/chatter_text.py` |
| Provider/model call behavior | `tools/chatter_llm.py` |
| DB inserts, queries, zone cache behavior | `tools/chatter_db.py` |
| Shared utility contracts and compatibility exports | `tools/chatter_shared.py` |
| C++ queue insert/delivery/emote behavior | `src/LLMChatterScript.cpp` |

## Common Task Pointers (Function-Level)

| Task | Primary function(s) |
|---|---|
| Change event dispatch mapping | `tools/llm_chatter_bridge.py`: `EVENT_HANDLERS`, `_dispatch_player_general_msg`, `process_single_event` |
| Change pending event claim policy/prioritization | `tools/llm_chatter_bridge.py`: `fetch_pending_events` |
| Change ambient statement runtime | `tools/chatter_ambient.py`: `process_statement` |
| Change ambient conversation runtime | `tools/chatter_ambient.py`: `process_conversation` |
| Change general-player-message response behavior | `tools/chatter_general.py`: `process_general_player_msg_event` |
| Change group join behavior | `tools/chatter_group.py`: `process_group_event` |
| Change group player message behavior | `tools/chatter_group.py`: `process_group_player_msg_event` |
| Change idle group chatter behavior | `tools/chatter_group.py`: `check_idle_group_chatter`, `_idle_single_statement`, `_idle_conversation` |
| Change group mood/trait state rules | `tools/chatter_group_state.py`: `update_bot_mood`, `assign_bot_traits`, `get_bot_traits` |
| Change any group reaction handler behavior | `tools/chatter_group_handlers.py`: `process_group_*_event` functions |
| Change group reaction prompt wording | `tools/chatter_group_prompts.py`: `build_*_reaction_prompt` functions |
| Change pre-cache prompt wording | `tools/chatter_group_prompts.py`: `build_precache_*_prompt` functions |
| Change pre-cache refill strategy/depth logic | `tools/chatter_cache.py`: `_CATEGORIES`, `refill_precache_pool` |
| Change JSON output instructions (statement) | `tools/chatter_shared.py`: `append_json_instruction` |
| Change JSON output instructions (conversation) | `tools/chatter_shared.py`: `append_conversation_json_instruction` |
| Change LLM provider/model call behavior | `tools/chatter_llm.py`: `resolve_model`, `call_llm`, `quick_llm_analyze` |
| Change response parsing/cleanup rules | `tools/chatter_text.py`: `parse_single_response`, `cleanup_message`, `repair_json_string` |
| Change anti-repetition thresholds | `tools/chatter_text.py`: `is_too_similar`; `tools/chatter_shared.py`: `build_anti_repetition_context` |
| Change DB message insert timing/fields | `tools/chatter_db.py`: `insert_chat_message` |
| Change zone/loot/mob/spell query behavior or cache | `tools/chatter_db.py`: `query_zone_*`, `query_bot_spells`, `ZoneDataCache` |

## Minimal Safety Checklist for Any Refactor

1. Run import smoke:
   - `python tools/import_smoke_check.py`
2. Run strict import smoke when deps are installed:
   - `python tools/import_smoke_check.py --strict`
3. Run syntax check on touched files:
   - `python -m py_compile <touched files>`
4. Restart bridge container:
   - `docker restart ac-llm-chatter-bridge`
5. Replay in-game parity anchors:
   - one statement flow
   - one conversation flow
   - one group reaction flow
6. Verify DB writes:
   - `llm_chatter_events`
   - `llm_chatter_messages`

## Refactor Milestone Summary (2026-02-19)

Completed:

- Group domain split into `chatter_group.py`, `chatter_group_handlers.py`, `chatter_group_prompts.py`, `chatter_group_state.py`.
- Ambient processing extracted into `chatter_ambient.py`.
- Shared decomposition into `chatter_text.py`, `chatter_llm.py`, `chatter_db.py` with compatibility re-exports in `chatter_shared.py`.
- Bridge routing map and general-message adapter stabilized.
- Query and zone cache ownership moved to DB layer.
- Dead import cleanup and stabilization pass completed.

Current architecture intent:

- Prefer stable compatibility imports for existing call sites.
- Avoid forced fragmentation beyond current split until a concrete pain point is demonstrated.
