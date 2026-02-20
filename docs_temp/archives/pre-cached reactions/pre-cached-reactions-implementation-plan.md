# Pre-Cached Reactions (Instant Delivery) - Implementation Plan

Date: 2026-02-15
Owner: mod-llm-chatter
Status: Planned (revised after investigation + peer review)

## 1) Goal

Deliver combat-time group reactions instantly (no live LLM call on hot path), with safe fallback to current behavior on cache miss.

## 2) Scope

### Phase 1 (ship first)

1. `bot_group_combat` (pull cries) -- C++ hook exists at line ~3489
2. `bot_group_spell_cast` support reactions (heal/buff/shield/cc) -- C++ hook exists at line ~4530
3. `bot_group_low_health` -- C++ hook exists (state callout, periodic combat check)
4. `bot_group_oom` -- C++ hook exists (state callout, periodic combat check)
5. `bot_group_aggro_loss` -- C++ hook exists (state callout, periodic combat check)

### Phase 2 (placeholder, re-plan after metrics)

1. `bot_group_death`
2. `bot_group_wipe`
3. Optional: `bot_group_kill`

### Out of scope for now

1. General chat
2. Non-urgent group flavor events (loot, zone transition, dungeon entry, quest, levelup, achievement)

## 3) Design Principles

1. C++ handles instant consume + delivery.
2. Python bridge handles background generation.
3. Cache miss falls back to current event path (on-demand LLM call).
4. Start minimal, then expand categories using hit-rate/quality data.

## 4) Data Model (Simplified)

## New table: `llm_group_cached_responses`

Columns:

1. `id` INT UNSIGNED PK AUTO_INCREMENT
2. `group_id` INT UNSIGNED NOT NULL
3. `bot_guid` INT UNSIGNED NOT NULL
4. `event_category` VARCHAR(48) NOT NULL
5. `message` VARCHAR(255) NOT NULL
6. `emote` VARCHAR(32) DEFAULT NULL
7. `status` ENUM('ready','used','expired') NOT NULL DEFAULT 'ready'
8. `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
9. `expires_at` TIMESTAMP NULL DEFAULT NULL
10. `used_at` TIMESTAMP NULL DEFAULT NULL

Indexes:

1. `idx_lookup` (`group_id`, `bot_guid`, `event_category`, `status`, `created_at`)
2. `idx_expiry` (`status`, `expires_at`)

Notes:

1. No refill-job table in Phase 1.
2. Python refills by scanning depth each loop.

## SQL files

1. Update base schema: `modules/mod-llm-chatter/data/sql/db-characters/base/llm_chatter_tables.sql`
2. Add migration: `modules/mod-llm-chatter/data/sql/db-characters/updates/20260216_pre_cached_reactions.sql`

## 5) Cache Categories (Phase 1 Minimal)

1. `combat_pull`
2. `state_low_health`
3. `state_oom`
4. `state_aggro_loss`
5. `spell_support`

Rationale:

1. Keeps join-time/warm-up generation small.
2. Still covers support-spell instant feedback requested by product goals.
3. Category splitting (heal vs cc vs shield/buff, self vs ally) can be added in Phase 2.

## 6) Config Additions

Add to:

1. `modules/mod-llm-chatter/src/LLMChatterConfig.h`
2. `modules/mod-llm-chatter/src/LLMChatterConfig.cpp`
3. `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist`

New keys:

1. `LLMChatter.GroupChatter.PreCacheEnable = 1`
2. `LLMChatter.GroupChatter.PreCacheCombatEnable = 1`
3. `LLMChatter.GroupChatter.PreCacheStateEnable = 1`
4. `LLMChatter.GroupChatter.PreCacheSpellEnable = 1`
5. `LLMChatter.GroupChatter.PreCacheDepthCombat = 2`
6. `LLMChatter.GroupChatter.PreCacheDepthState = 2`
7. `LLMChatter.GroupChatter.PreCacheDepthSpell = 2`
8. `LLMChatter.GroupChatter.PreCacheTTLSeconds = 3600`
9. `LLMChatter.GroupChatter.PreCacheGeneratePerLoop = 2`
10. `LLMChatter.GroupChatter.PreCacheFallbackToLive = 1`

## 7) C++ Implementation Tasks

File: `modules/mod-llm-chatter/src/LLMChatterScript.cpp`

### 7.1 Cache consume helper (UPDATED after investigation)

Implement `TryConsumeCachedReaction(...)` using simple Query + Execute:

```cpp
static bool TryConsumeCachedReaction(
    uint32 groupId, uint32 botGuid,
    const std::string& category,
    std::string& outMessage, std::string& outEmote)
{
    // Sync SELECT -- filter expired rows
    QueryResult result = CharacterDatabase.Query(
        "SELECT id, message, emote "
        "FROM llm_group_cached_responses "
        "WHERE group_id = {} AND bot_guid = {} "
        "AND event_category = '{}' "
        "AND status = 'ready' "
        "AND (expires_at IS NULL "
        "     OR expires_at > NOW()) "
        "ORDER BY created_at ASC LIMIT 1",
        groupId, botGuid,
        EscapeString(category));

    if (!result)
        return false;

    Field* fields = result->Fetch();
    uint32 cachedId = fields[0].Get<uint32>();
    outMessage = fields[1].Get<std::string>();
    outEmote = fields[2].IsNull()
        ? "" : fields[2].Get<std::string>();

    // Sync UPDATE -- DirectExecute blocks until
    // complete, preventing double-consume if two
    // hooks fire in the same world update tick.
    CharacterDatabase.DirectExecute(
        "UPDATE llm_group_cached_responses "
        "SET status = 'used', used_at = NOW() "
        "WHERE id = {}",
        cachedId);

    return true;
}
```

Investigation findings:

1. **`DirectExecute()` (sync) used for UPDATE** to prevent double-consume. While hooks fire on the single world thread, `Execute()` (async) queues the UPDATE on the DB thread. If two hooks fire in the same tick for the same bot+category, the second `Query()` could see the row still as 'ready' before the async UPDATE is applied. `DirectExecute()` blocks until the row is marked 'used', guaranteeing single-consume. Sub-millisecond cost for a single-row PK update.
2. **AzerothCore transactions don't support SELECT with results.** The `Transaction` API is write-only. `SELECT ... FOR UPDATE` requires manual connection management, which is unnecessary since `DirectExecute()` solves the race.
3. **`CharacterDatabase.Query()` is synchronous** -- blocks until result arrives, returns `QueryResult` smart pointer.
4. **`expires_at` filter added** to consume query to skip stale rows that haven't been cleaned up yet.
5. **No affected-row API exists** -- `Execute()` and `DirectExecute()` return void/bool, not row counts. So we must SELECT first, then UPDATE by id.

### 7.2 Placeholder injection helper

Cached messages contain `{target}`, `{caster}`, and `{spell}` placeholders
that are resolved at consume time using data available at the hook point.

```cpp
static void ResolvePlaceholders(
    std::string& message,
    const std::string& target,
    const std::string& caster,
    const std::string& spell)
{
    // Step 1: Replace known placeholders.
    // Empty values get deterministic fallbacks
    // so the sentence still reads naturally.
    std::string safeTarget =
        target.empty() ? "that" : target;
    std::string safeCaster =
        caster.empty() ? "them" : caster;
    std::string safeSpell =
        spell.empty() ? "that" : spell;

    size_t pos;
    while ((pos = message.find("{target}"))
           != std::string::npos)
        message.replace(pos, 8, safeTarget);
    while ((pos = message.find("{caster}"))
           != std::string::npos)
        message.replace(pos, 8, safeCaster);
    while ((pos = message.find("{spell}"))
           != std::string::npos)
        message.replace(pos, 7, safeSpell);

    // Step 2: Strip any unresolved {tokens}
    // to prevent raw placeholders leaking
    // to player chat (e.g. LLM hallucinated
    // {location} or prompt drift).
    std::regex unresolvedRe("\\{[a-zA-Z_]+\\}");
    message = std::regex_replace(message, unresolvedRe, "");

    // Step 3: Clean up whitespace artifacts
    // from stripped tokens.
    while (message.find("  ") != std::string::npos)
    {
        pos = message.find("  ");
        message.replace(pos, 2, " ");
    }

    // Step 4: Clamp to 250 chars to stay within
    // VARCHAR(255) columns in chat history and
    // message tables (prevents truncation errors
    // in strict SQL mode).
    if (message.size() > 250)
        message.resize(250);
}
```

Called between `TryConsumeCachedReaction()` and `SendPartyMessageInstant()`.

Placeholder availability per category:

| Category | `{target}` | `{caster}` | `{spell}` | Fallback |
|----------|-----------|-----------|----------|----------|
| `combat_pull` | creature name | -- | -- | "that" |
| `spell_support` | spell target name | spell caster name | spell name | "them"/"that" |
| `state_low_health` | -- | -- | -- | N/A (no placeholders used) |
| `state_oom` | -- | -- | -- | N/A (no placeholders used) |
| `state_aggro_loss` | creature name | -- | -- | "that" |

Safety guarantees:

1. **No raw placeholder leakage**: unresolved `{tokens}` stripped via regex before send.
2. **Empty hook data handled**: null target/caster/spell get natural fallbacks ("that"/"them") so "I've got {target}" becomes "I've got that" instead of "I've got {target}" or "I've got ".
3. **Length clamped**: message truncated to 250 chars after replacement to stay within VARCHAR(255) columns.

### 7.3 Instant party send helper (UPDATED after investigation)

Implement `SendPartyMessageInstant(Player* bot, Group* group, const std::string& message, const std::string& emote)`:

```cpp
static void SendPartyMessageInstant(
    Player* bot, Group* group,
    const std::string& message,
    const std::string& emote)
{
    // Build chat packet once
    WorldPacket data;
    ChatHandler::BuildChatPacket(
        data,
        CHAT_MSG_PARTY,
        message,
        LANG_UNIVERSAL,
        CHAT_TAG_NONE,
        bot->GetGUID(),
        bot->GetName());

    // Broadcast to all group members
    group->BroadcastPacket(&data, false);

    // Optional emote animation
    if (!emote.empty())
    {
        uint32 emoteId = GetEmoteId(emote);
        if (emoteId)
            bot->HandleEmoteCommand(emoteId);
    }
}
```

Investigation findings:

1. **`Group::BroadcastPacket()`** is the native AzerothCore API for group-wide packet delivery. Iterates all members internally, handles null players and BG raid filtering. Much cleaner than manual `GetFirstMember()` iteration.
2. **Location:** `src/server/game/Groups/Group.h:283`, impl at `Group.cpp:1764`.
3. **Signature:** `void BroadcastPacket(WorldPacket const* packet, bool ignorePlayersInBGRaid, int group = -1, ObjectGuid ignore = ObjectGuid::Empty)`.
4. **ChatHandler::BuildChatPacket()** overload with string message at `src/server/game/Chat/Chat.h:51-55`.
5. **Farewell pattern** used manual iteration because the leaving bot was already removed from group. For pre-cache, the bot is still in the group, so `BroadcastPacket()` works perfectly.

### 7.4 Integrate into Phase 1 hooks (UPDATED with exact line references)

All integration points follow this pattern:

```
if (preCacheEnabled && categoryEnabled)
{
    if (TryConsumeCachedReaction(groupId, botGuid, category, msg, emote))
    {
        ResolvePlaceholders(msg, target, caster, spell);
        SendPartyMessageInstant(bot, group, msg, emote);
        // Record in chat history
        return;  // skip event INSERT
    }
    // Cache miss
    if (!_preCacheFallbackToLive)
        return;  // skip entirely when fallback disabled
}
// Fall through to existing event INSERT (live LLM path)
```

**A) Combat pull hook (~line 3489, just before INSERT):**

```
- Have: player (bot Player*), group (Group*), isBoss, isElite, creature->GetName()
- Category: "combat_pull"
- Placeholders: ResolvePlaceholders(msg, creatureName, "", "")
```

**B) Spell cast hook (~line 4530, just before INSERT):**

```
- Have: reactor (Player*), group (Group*), spellCategory, target->GetName(), player->GetName(), spellName
- Category: "spell_support" (unified in Phase 1)
- Placeholders: ResolvePlaceholders(msg, targetName, casterName, spellName)
- Note: resurrect category SKIPPED (always live -- too important for generic cached line)
```

**C) State callout hooks (periodic combat check, near line ~5037+):**

```
- Have: player (bot Player*), group (Group*), target name (for aggro_loss)
- Category: "state_low_health" / "state_oom" / "state_aggro_loss"
- Placeholders: aggro_loss gets ResolvePlaceholders(msg, targetName, "", ""), others no placeholders
```

### 7.5 Chat history recording

After instant send, record the message in chat history so Python sees it for conversation context. Must match the existing `llm_group_chat_history` schema:

```sql
-- Actual schema (from llm_chatter_tables.sql:165):
-- group_id INT, speaker_guid INT, speaker_name VARCHAR(64),
-- is_bot TINYINT(1), message VARCHAR(255), created_at TIMESTAMP
```

```cpp
// After SendPartyMessageInstant:
CharacterDatabase.Execute(
    "INSERT INTO llm_group_chat_history "
    "(group_id, speaker_guid, speaker_name, "
    "is_bot, message) "
    "VALUES ({}, {}, '{}', 1, '{}')",
    groupId, botGuid,
    EscapeString(bot->GetName()),
    EscapeString(msg));
```

Note: no `emote` or `source` column exists in this table. Emote is only stored in `llm_chatter_messages`. The `is_bot = 1` flag is sufficient for Python to distinguish cached vs live messages.

### 7.6 Cleanup hooks

1. On member removal (`OnRemoveMember`): `DELETE FROM llm_group_cached_responses WHERE group_id = {} AND bot_guid = {}`
2. On group disband / `CleanupGroupSession(groupId)`: `DELETE FROM llm_group_cached_responses WHERE group_id = {}`
3. On server startup: `DELETE FROM llm_group_cached_responses` (stale from previous session)

## 8) Python Bridge Implementation Tasks

Files:

1. `modules/mod-llm-chatter/tools/chatter_group.py`
2. `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`
3. optional shared helper in `modules/mod-llm-chatter/tools/chatter_shared.py`

### 8.1 Depth-based refill (UPDATED with exact insertion point)

Add `refill_precache_pool(db, client, config)`:

1. Find active grouped bots (`SELECT DISTINCT group_id FROM llm_group_bot_traits`).
2. For each group+bot+category, count `status='ready' AND (expires_at IS NULL OR expires_at > NOW())` rows.
3. If below target depth, generate new line and insert into cache with `expires_at = DATE_ADD(NOW(), INTERVAL {TTL} SECOND)` where TTL is `PreCacheTTLSeconds` (default 3600).
4. Respect per-loop generation cap: `PreCacheGeneratePerLoop`.

**Bridge main loop insertion point** (after idle check, before `db.close()`, ~line 2270):

```python
# After idle group chatter check, before db.close():
if (precache_enabled
        and current_time - last_cache_refill
        >= cache_refill_interval):
    last_cache_refill = current_time
    try:
        refill_precache_pool(db, client, config)
    except Exception as e:
        logger.debug(
            f"Cache refill error: {e}"
        )
```

Investigation findings:

1. **Bridge is 100% synchronous, single-threaded.** No async, no threading. Safe to add refill in main loop.
2. **1 event processed per loop iteration** (`LIMIT 1` at line 1017). Cache refill runs only when no events pending.
3. **3s poll interval** (configurable). Bridge sleeps only when no work was done. If events are pending, loops immediately.
4. **Active groups discovered via** `SELECT DISTINCT group_id FROM llm_group_bot_traits` (line 7138-7142).
5. **Refill runs at lowest priority** -- after regular requests, events, and idle checks. Only runs on the periodic timer, not every loop.

### 8.2 Refill priority/staggering

Priority order:

1. `state_low_health`
2. `state_oom`
3. `state_aggro_loss`
4. `combat_pull`
5. `spell_support`

Stagger rules:

1. Do not bulk-generate entire pool at join.
2. Generate gradually across loops (low priority background).
3. Keep normal event processing first; refill only after it.

### 8.3 Prompt builders

Add minimal builders:

1. `build_precache_combat_pull_prompt(...)`
2. `build_precache_state_prompt(...)` (takes state_type: low_health/oom/aggro_loss)
3. `build_precache_spell_support_prompt(...)`

Rules:

1. Very short lines (1 sentence, max_tokens=60).
2. Personality-aware (use bot traits from `llm_group_bot_traits`).
3. Use `{target}`, `{caster}`, `{spell}` placeholders for dynamic names. Prompt must instruct LLM to use these exact tokens (e.g. "Use {target} where you'd say the enemy's name"). C++ resolves them at delivery time.
4. Include race/class context via `build_race_class_context()`.
5. Include mood via `get_mood_label()` if available.
6. Anti-repetition: pass last 2-3 cached messages for this bot+category as "do not repeat" context.
7. State prompts (low_health/oom) use NO placeholders -- purely first-person ("I need healing!").
8. combat_pull and aggro_loss use `{target}` only.
9. spell_support uses `{target}`, `{caster}`, `{spell}` -- prompt distinguishes caster vs observer perspective.

### 8.4 Cache hygiene

1. Expire stale ready rows: `UPDATE llm_group_cached_responses SET status='expired' WHERE status='ready' AND expires_at IS NOT NULL AND expires_at < NOW()`
2. Purge used rows older than 1 hour: `DELETE FROM llm_group_cached_responses WHERE status='used' AND used_at < DATE_SUB(NOW(), INTERVAL 1 HOUR)`
3. Purge expired rows older than 1 hour: `DELETE FROM llm_group_cached_responses WHERE status='expired' AND created_at < DATE_SUB(NOW(), INTERVAL 1 HOUR)`
4. Run hygiene at start of each refill cycle (cheap, three queries).

Note: expired rows have `used_at = NULL` (never consumed), so purge #3 filters on `created_at` instead. This ensures expired rows don't grow unbounded.

## 9) Delivery + Fallback Behavior

1. **Cache hit**: instant C++ send via `BroadcastPacket()`, no live LLM, no event queue.
2. **Cache miss with `PreCacheFallbackToLive=1`** (default): use current event->bridge->LLM flow (existing behavior, 3-8s latency). This is the on-demand LLM fallback -- the bot still reacts, just not instantly.
3. **Cache miss with `PreCacheFallbackToLive=0`**: skip entirely (not recommended, only for testing cache hit rates).

With the default `PreCacheFallbackToLive=1`, **no silent drops** -- cache misses fall through to the normal LLM path. With `PreCacheFallbackToLive=0` (testing only), misses are intentionally dropped to measure cache hit rates.

## 10) Test Plan

### Correctness

1. Migration works on fresh and upgrade DB.
2. Cache consume returns one row exactly once (verify via bridge logs + DB status column).
3. Cleanup works on remove member and disband.
4. Fallback path unchanged on cache miss.
5. Chat history recorded for cached messages (Python can see them for conversation context).

### Gameplay (Phase 1)

1. Pull cry appears instantly (no 3-8s delay).
2. Low health/OOM/aggro callouts appear instantly.
3. Support spell reaction appears instantly.
4. Disable pre-cache toggle -> old behavior returns with no errors.
5. Cache miss -> normal delayed reaction still works.

### Metrics

Track via bridge logs:

1. hit rate per category
2. miss rate per category
3. refill generation count per loop
4. cache row count (ready/used/expired)

## 11) Rollout Plan

1. Ship behind `PreCacheEnable`.
2. Enable in test realm with minimal Phase 1 categories.
3. Tune depth/TTL/generation-per-loop from real metrics.
4. Promote to production.
5. Re-plan Phase 2 based on observed gaps.

## 12) Definition of Done (Phase 1)

1. Instant cached delivery works for combat pull, state callouts, and support spell reactions.
2. No regressions on cache miss fallback (on-demand LLM still works).
3. Cache tables do not grow unbounded (expiry + cleanup verified).
4. Hit rate materially reduces combat-time latency.
5. Farewell flow remains unchanged.
6. Chat history recorded for cached messages.

## Appendix A: Investigation Findings (2026-02-15)

### A.1 AzerothCore SQL API Summary

| Method | Sync/Async | Returns | Use Case |
|--------|-----------|---------|----------|
| `CharacterDatabase.Query(sql)` | Sync (blocks) | `QueryResult` | Reading data |
| `CharacterDatabase.Execute(sql)` | Async (queued) | void | Fire-and-forget writes |
| `CharacterDatabase.DirectExecute(sql)` | Sync (blocks) | void | Immediate writes |
| `CharacterDatabase.BeginTransaction()` | N/A | `Transaction` | Multi-statement writes only |
| `CharacterDatabase.CommitTransaction(t)` | Async | void | Queued transaction |
| `CharacterDatabase.DirectCommitTransaction(t)` | Sync | void | Immediate transaction |

Key constraint: **Transactions are write-only** -- no SELECT with results inside a transaction. `SELECT FOR UPDATE` requires manual connection management (`GetFreeConnection()` + `Unlock()`), which is unnecessary for single-threaded world hooks.

### A.2 Party Broadcast API

`Group::BroadcastPacket(WorldPacket const* packet, bool ignorePlayersInBGRaid, int group = -1, ObjectGuid ignore = ObjectGuid::Empty)` -- native AzerothCore method that iterates all group members and calls `SendDirectMessage()`. Preferred over manual iteration when the sending bot is still in the group.

### A.3 Hook Short-Circuit Points

| Hook | Line | Available At Short-Circuit | Cache Category |
|------|------|---------------------------|----------------|
| Combat pull | ~3489 | bot Player*, Group*, isBoss/isElite | `combat_pull` |
| Spell cast | ~4530 | reactor Player*, Group*, spellCategory | `spell_support` |
| Low health | ~5037+ | bot Player*, Group* | `state_low_health` |
| OOM | ~5037+ | bot Player*, Group* | `state_oom` |
| Aggro loss | ~5037+ | bot Player*, Group* | `state_aggro_loss` |

All hooks have bot Player* and Group* available at the short-circuit point, which is everything needed for cache lookup + instant send.

### A.4 Bridge Main Loop Order

1. DB connect
2. Periodic event cleanup (60s)
3. Process regular chatter requests
4. Process event-driven chatter (1 event per loop, LIMIT 1)
5. Periodic idle group chatter check
6. **[CACHE REFILL INSERTION POINT]** -- lowest priority
7. DB close
8. Sleep 3s if idle (immediate re-loop if work was done)
