# Development History

This file tracks significant development sessions and changes made to the project.

---

## 2026-02-19 (Session 52) - Humor Pool Enhancement & RFC Dungeon Testing

### Summary

Two changes: (1) Added humor-oriented entries to all 6 creativity pools in `chatter_constants.py` — humor frequency roughly doubled from ~10% to ~20% across normal and RP modes. (2) Full RFC dungeon run QA testing verified all group chatter features firing correctly (kills, boss kills, loot, spells, mood progression).

### Humor Pool Enhancement (Python)

Analysis showed humor was underrepresented (~10% of pool entries). Added 20 entries across 6 pools:
- **TONES** +3: sarcastically amused, playfully mocking, cheerfully absurd
- **MOODS** +3: finding everything hilarious, cracking wise, dry and snarky
- **CREATIVE_TWISTS** +5: Make a joke, sarcastically obvious, exaggerate wildly, self-deprecating joke, absurd silver lining
- **RP_TONES** +2: wryly sarcastic, mischievously cheerful
- **RP_MOODS** +3: wisecracking, gallows humor, playfully smug
- **RP_CREATIVE_TWISTS** +4: wry joke, deadpan understatement, dark humor in danger, mock with dry wit

Verified in live logs: new humor entries appearing within minutes (gallows humor, dry wit, playfully smug, etc.).

### RFC Dungeon Testing

Full Ragefire Chasm run with group of bots:
- **Boss kills**: Jergosh and Bazzalan both triggered correctly (`boss=True`), mood boosted to ecstatic (5.5)
- **Taragaman miss**: First boss kill event didn't fire — investigated thoroughly (bridge logs, DB, C++ code, creature template). Concluded one-off latency miss (201ms spike), not a code regression
- **Mood progression**: Confirmed per-bot mood evolving correctly across events
- **Low health pre-cache**: Cached but never consumed (RFC too easy for 25% HP threshold)
- **Zone fatigue**: Correctly limiting messages in high-activity zones

### Files Changed

- `modules/mod-llm-chatter/tools/chatter_constants.py` — Added humor entries to 6 creativity pools

### Status
- Python-only change — bridge restarted, no compilation needed
- All group chatter features verified working in dungeon content

---

## 2026-02-19 (Session 51b) - Next-Pass Refactoring Review (N14-N17 Complete)

### Summary

Completed the N1-N17 next-pass refactoring review of mod-llm-chatter. This session reviewed and approved steps N14-N17 (the final 4 steps), completing the entire structural decomposition. Also reviewed the post-refactor architecture doc rewrite, updated CLAUDE.md and `/um` command with architecture doc references, and added implementation status checkmarks to the immersion hooks report.

### Refactoring Steps Reviewed (N14-N17)

- **N14**: Extract LLM call layer to `chatter_llm.py` — 4 functions (`resolve_model`, `call_llm`, `_get_quick_analyze_client`, `quick_llm_analyze`) + 3 globals moved from `chatter_shared.py`. Lazy provider imports preserved. PASS.
- **N15**: Extract DB foundation to `chatter_db.py` — 4 functions (`get_db_connection`, `wait_for_database`, `validate_emote`, `insert_chat_message`) moved. `mysql.connector` and `EMOTE_LIST` imports cleaned from shared. PASS.
- **N16**: Extract 8 query helpers + `ZoneDataCache` to `chatter_db.py` — all zone/spell/item/quest query functions plus `zone_cache` instance. Private `_get_zone_level_range` copy to avoid circular import. PASS.
- **N17**: Dead import cleanup — removed unused `import re` from `chatter_group.py`, removed 6 dead imports from `chatter_group_prompts.py`. PASS.

### Post-Refactor Architecture

Three decomposed leaf modules now exist under `chatter_shared.py` facade:
- `chatter_text.py` — parsing/sanitization/anti-repetition (~474 lines)
- `chatter_llm.py` — provider/model calls (~327 lines)
- `chatter_db.py` — DB connections, queries, zone cache (~700 lines)

`chatter_shared.py` reduced from ~2632 to ~1218 lines, serving as stable facade with re-exports.

### Architecture Doc Review

Reviewed full post-refactor rewrite of `docs/development/mod-llm-chatter-architecture.md` (~336 lines). Found 3 minor issues (grammar, missing import topology for prompts/events, zone cache trap clarity). All fixed by other LLM, plus optional function-level pointers section added.

### Documentation Updates

- `CLAUDE.md` — Added architecture doc as item 3 in Session Startup Checklist
- `.claude/commands/um.md` — Added architecture doc to always-update list
- `docs/development/immersion-hooks-report.md` — Added Status column to Part 3 (Prioritized Opportunities) showing implemented vs not-implemented features
- `docs/reviews/refactor-next-pass-review-status.md` — Rewrote to COMPLETE status with all 17 steps

### Deferred Phase Assessment

- Phase 2b (ambient extraction): completed by next-pass
- Phase 3b (prompt decomposition): completed by next-pass
- Phase 6 (dead import cleanup): completed by N17
- Phase 7 (prompt signature normalization): optional/cosmetic, skipped

### Files Changed

- `docs/reviews/refactor-next-pass-review-status.md` — Rewrote to COMPLETE
- `CLAUDE.md` — Added architecture doc to startup checklist
- `.claude/commands/um.md` — Added architecture doc requirement
- `docs/development/immersion-hooks-report.md` — Added implementation status checkmarks

### Status
- All N1-N17 steps reviewed and committed (by other LLM)
- Python-only changes throughout — no compilation needed
- Structural refactoring of mod-llm-chatter is COMPLETE
- Architecture doc is up to date

---

## 2026-02-19 (Session 51) - Speech Pools, General Emote Skip, Prompt Refactor

### Summary

Three changes: (1) Race/class speech pool randomization — expanded personality data to pools of 8 variants with random selection, ~31,680 combinations per race/class pair. (2) General channel emote skip — emotes are proximity-based in 3.3.5a, invisible to zone-wide General recipients. All General channel paths now omit the 244-emote list, saving ~200+ tokens per call, with three-layer protection (prompt, DB, C++ delivery). (3) Conversation prompt refactor — extracted `append_conversation_json_instruction()` shared helper, replacing ~150 lines of duplicated inline JSON/emote/action formatting across 6 conversation builders.

Also created `docs/development/mod-llm-chatter-architecture.md` — comprehensive architecture doc with file map, event dispatch, channel routing, data flow, and 6 refactoring candidates.

Boss detection confirmed working (user-reported fix from prior session).

### Race/Class Speech Pools (Python)
- `CLASS_SPEECH_MODIFIERS`: all 10 classes expanded from 1 string to list of 8 variants
- `RACE_SPEECH_PROFILES["traits"]`: all 10 races expanded from 1 string to list of 8 variants
- `flavor_words`: all 10 races expanded from ~6 to 12 entries
- Night Elf: "the wilds" removed entirely from flavor_words
- Druid: no variant contains "the wilds"
- `build_race_class_context()`: `random.choice()` for traits/modifiers, `random.sample(4)` for flavor words
- 6 direct flavor word injection sites: `[:3]` deterministic slices → `random.sample(3)`
- Total personality fingerprints per race/class: 8 × 8 × 495 = ~31,680 combinations

### General Channel Emote Skip (C++ + Python)
- All General channel prompt paths use `skip_emote=True` or `append_conversation_json_instruction()` (emote always null)
- `pick_emote_for_statement()` fallback removed from all General paths, dead imports cleaned
- C++ `DeliverPendingMessages()`: emote delivery guarded behind `channel == "party"`
- Three-layer protection: prompt (LLM never sees emote list), DB (no emote stored), C++ (party-only guard)
- Token savings: ~200+ input tokens per General channel prompt

### Conversation Prompt Refactor (Python)
- New `append_conversation_json_instruction()` in `chatter_shared.py` — handles conversation JSON array format
- All 6 conversation builders in `chatter_prompts.py` now use it instead of inline formatting
- `EMOTE_LIST_STR` import removed from `chatter_prompts.py` (no longer needed)
- Net reduction: ~120 lines of duplicated code

### Files Changed
- `modules/mod-llm-chatter/tools/chatter_constants.py` — expanded traits/modifiers to lists, expanded flavor_words
- `modules/mod-llm-chatter/tools/chatter_shared.py` — random.choice/sample, skip_emote param, append_conversation_json_instruction()
- `modules/mod-llm-chatter/tools/chatter_group.py` — 4 `[:3]` → random.sample()
- `modules/mod-llm-chatter/tools/chatter_general.py` — 2 `[:3]` → random.sample(), skip_emote=True, removed emote fallbacks
- `modules/mod-llm-chatter/tools/chatter_prompts.py` — skip_emote=True on statements, conversation builders refactored to shared helper
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` — skip_emote=True, removed emote fallbacks from process_statement/conversation
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` — channel == "party" guard on emote delivery
- `modules/mod-llm-chatter/README.md` — updated race/class identity description
- `docs/development/mod-llm-chatter-architecture.md` — NEW architecture document

### Status
- C++ change needs compilation (channel == "party" guard) — belt-and-suspenders, Python changes are sufficient alone
- Python changes deployed (bridge restarted)
- Committed to mod-llm-chatter repo: `196b7b8`
- Review docs: `docs/reviews/session-51-review.md`, `docs/reviews/race-class-speech-pool-randomization-review.md`

---

## 2026-02-18 (Session 50) - Universal Spell Reactions, Dynamic Trigger Scaling, Achievement Prompt Fix

### Summary

Extended the spell reaction system from 6 specific categories to catch ALL combat/support spells via two new catch-all categories (`offensive` and `support`). Added `spell_offensive` pre-cache category for instant delivery of bot battle cries. Implemented dynamic trigger chance scaling — spell and idle chatter chances now divide by number of bots in group so total output stays constant regardless of group size. Fixed achievement prompt so bots congratulate the player instead of claiming achievements as their own. Improved punctuation cleanup for empty placeholder substitution. All defaults aligned across C++, Python, and config files.

### Universal Spell Reactions (C++ + Python)
- Extended `OnPlayerSpellCast` classification: `offensive` (negative + in-combat) and `support` (positive catch-all with group-member target check)
- Offensive gate: `!spellInfo->IsPositive() && player->IsInCombat()` — prevents mounts/food/professions from triggering
- Support catch-all: same group-member target validation as existing 6 categories
- Pre-cache dual key: `spell_offensive` (caster-perspective, bot-only) and `spell_support`
- `canUseCache = false` when player casts offensive (observer bots skip cache → live LLM)
- Python: `build_precache_spell_offensive_prompt()` with `{target}` and `{spell}` placeholders, `{target}` documented as optional
- Python: explicit `offensive` and `support` branches in `build_spell_cast_reaction_prompt()` for both caster and observer
- All 8 categories now have dedicated prompt branches (no more fallback-only for new types)

### Dynamic Trigger Chance Scaling (C++ + Python)
- C++ `CountBotsInGroup()` helper counts bots in group
- Spell cast RNG: `effectiveChance = configChance / numBots` (floor of 1%)
- Python idle chatter: `effective_chance = idle_chance // num_bots` (floor of 1)
- With `SpellCastChance = 10`: 2 bots → 5% each, 5 bots → 2% each
- Total group output stays roughly constant regardless of group size

### Achievement Prompt Fix (Python)
- Split prompt into `bot_is_achiever` (celebrate own) vs congratulate (someone else's)
- When congratulating: "Your groupmate X just earned...", "This is THEIR achievement, not yours"
- Explicit rules: "Address X by name" and "congratulate them"
- Fixed Jelesia claiming Karaez's 100 Quests Completed achievement

### Config Changes
- `SpellCastChance`: 15 → 10 (all 4 locations aligned: conf.dist, active, C++ default, Python log fallback)
- `PreCacheGeneratePerLoop`: 2 → 3 (all 4 locations aligned)
- `PreCacheFallbackToLive` comment: documents player-cast offensive always uses live LLM
- Punctuation cleanup: handles `", !"` → `"!"`, `", ."` → `"."`, trailing commas

### Weather Cooldown Bypass (by other LLM)
- `weather_change` events bypass `QueueEvent()` cooldown entirely via `bypassEventCooldown` flag
- Ensures rare weather transitions always get queued

### Files Changed
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` — offensive/support categories, CountBotsInGroup, dynamic spell RNG, pre-cache dual key, punctuation cleanup
- `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` — SpellCastChance 15→10, PreCacheGeneratePerLoop 2→3
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` — updated defaults and comments
- `env/dist/etc/modules/mod_llm_chatter.conf` — aligned active config
- `modules/mod-llm-chatter/tools/chatter_cache.py` — spell_offensive category, routing, import
- `modules/mod-llm-chatter/tools/chatter_group.py` — offensive pre-cache prompt, live prompt branches, achievement fix, dynamic idle scaling
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` — logging fallback defaults aligned

### Status
- All C++ compiled and deployed
- Python bridge restarted
- Tested: Arcane Intellect (support catch-all), Flame Shock (offensive), achievement reactions
- Entering first dungeon test

---

## 2026-02-18 (Session 49) - Quest Prompt Rewrites, Quest Description Injection, Weather Cooldown Tuning

### Summary

Fixed quest event prompts that were generating wrong-tense/completion language for quest accept and objectives stages. Rewrote all 3 quest prompt builders with exclusive positive framing (Gemini 3 Pro insight: LLMs struggle with negation). Added quest description/objectives injection from C++ `Quest` object into all 3 quest event paths. Reduced weather cooldown from 30min to 5min. Discovered and documented a playerbots bug (quest link opens trade window). Compiled all accumulated C++ from Sessions 48, 48b, and 49.

### Quest Prompt Rewrites (Python)
- **Stage 1 (Accept)**: "Status: PREPARATION" — focus on task ahead, travel required, plan of attack
- **Stage 2 (Objectives)**: "Status: PENDING TURN-IN" — focus on relief, heading back to quest giver
- **Stage 3 (Complete)**: "TRANSACTION COMPLETE" — focus on XP, gold, reward, team celebration
- Key insight from Gemini 3 Pro review: "Do NOT use completion language" causes LLMs to focus on completion. Replace negation with exclusive positive framing
- All prompts use "we" team language consistently

### Quest Description Injection (C++ + Python)
- C++ hooks inject `quest_details` (200 chars from `Quest::GetDetails()`) and `quest_objectives` (150 chars from `Quest::GetObjectives()`) into `extra_data` JSON
- All 3 hooks updated: `OnPlayerBeforeQuestComplete`, `OnPlayerCompleteQuest`, `CanCreatureQuestAccept`
- Python prompt builders accept `quest_details=""` and `quest_objectives=""` kwargs, inject only when non-empty
- Python event processors extract via `extra_data.get('quest_details', '')` — backwards compatible (empty if C++ not compiled yet)
- `JsonEscape()` handles `\n`, `\r`, `\t`, quotes, apostrophes in quest text

### Weather Cooldown Tuning
- `WeatherCooldownSeconds` reduced from 1800 (30 min) to 300 (5 min) in both active config and conf.dist

### Bug Fix: Race/Class ID Resolution in Quest Accept
- `process_group_quest_accept_event()` was passing raw numeric IDs — added `int()` cast + `get_class_name()`/`get_race_name()` conversion

### Playerbots Bug Discovery
- Quest links (`|Hquest:123|h`) in chat open trade window — root cause: `ChatHelper::parseable()` checks `|H` generically instead of `|Hitem:`
- Documented in `docs/playerbots/quest-link-opens-trade-window.md` for upstream PR

### Compilation
- All accumulated C++ from Sessions 48, 48b, and 49 compiled and deployed
- Includes: config extractions, weather ambient, quest accept hooks, discovery hooks, spell classification expansion, quest description injection
- `libmodules.a` corruption issue during build (concurrent make) — resolved by deleting corrupt archive and rebuilding

### Files Changed
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` — quest_details/quest_objectives in 3 hooks
- `modules/mod-llm-chatter/tools/chatter_group.py` — quest prompt rewrites, quest description injection, race/class ID fix
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` — WeatherCooldownSeconds 1800→300
- `env/dist/etc/modules/mod_llm_chatter.conf` — WeatherCooldownSeconds 1800→300
- `docs/playerbots/quest-link-opens-trade-window.md` — new (playerbots bug doc)
- `docs/reviews/quest-description-injection-review.md` — new (review doc)

### Status
- All C++ compiled and deployed
- Python bridge restarted
- Ready for in-game testing of quest description injection

---

## 2026-02-17 (Session 48b) - Weather Ambient, Quest Accept, Discovery, Spell Classification Expansion

### Summary

Extended weather system with ambient remarks between transitions, added quest accept and subzone discovery reactions, and expanded spell classification to catch HoTs, dispels, damage reduction, haste buffs, mana regen, and group-wide buff targeting. C++ + Python changes. All C++ awaiting compilation.

### Two-Tier Weather System (C++ + Python)
- `weather_change` events now have `alwaysFire` flag — bypasses 15% EventReactionChance RNG, always triggers 100%
- New `weather_ambient` event type: periodic remarks about ongoing weather between transitions
- `CheckAmbientWeather()` iterates `_zoneWeatherState`, queues events for zones with active weather + real player
- `WeatherAmbientCooldownSeconds = 120` config (user chose 120 over initial 300)
- Python `ambient_descriptions` dict maps 13 weather types to ongoing-weather descriptions
- Reaction delay: 120-600s for ambient weather events

### Quest Accept Reactions (C++ + Python)
- New `LLMChatterCreatureScript` class using `AllCreatureScript::CanCreatureQuestAccept` hook
- No PlayerScript hook exists for quest accept — must use creature script
- `QuestAcceptChance = 100` (user requested, was initially 20)
- `QuestAcceptCooldown = 30` per-group dedup using `(groupId << 32) | questId` composite key
- Python `process_group_quest_accept_event()` + `build_quest_accept_reaction_prompt()`
- Acceptor is bot vs player handled: "we" language for bots, "they" language for player

### Subzone Discovery Reactions (C++ + Python)
- Uses `OnPlayerGiveXP` hook with `xpSource == 3` (XPSOURCE_EXPLORE)
- Critical fix: initially coded as `xpSource == 2` (wrong), corrected to `3` per Player.h:1002
- `DiscoveryChance = 40`, `DiscoveryCooldown = 30`
- Per-group dedup using `(groupId << 32) | areaId` composite key (all bots discover simultaneously)
- Only areas with `area_level > 0` (skips city sub-zones)
- Python `process_group_discovery_event()` + `build_discovery_reaction_prompt()`

### Quest Objective Chance Bump
- `QuestObjectiveChance` changed from 30% to 100% (user requested)

### Spell Classification Expansion (C++)
- **Heal**: Added `SPELL_AURA_PERIODIC_HEAL` for HoTs (Renew, Rejuvenation, Regrowth, Riptide, Earth Shield)
- **Dispel**: New category using `SPELL_EFFECT_DISPEL` (Cleanse, Dispel Magic, Remove Curse, Abolish Poison)
- **Shield**: Added `SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN` (Pain Suppression, Guardian Spirit), `SPELL_AURA_SPLIT_DAMAGE_PCT/FLAT` (Hand of Sacrifice)
- **Buff**: Added `SPELL_AURA_MOD_POWER_REGEN_PERCENT` (Innervate), `SPELL_AURA_MOD_MELEE_HASTE` + `SPELL_AURA_HASTE_SPELLS` (Bloodlust/Heroism)
- **Group buff targeting fix**: `spellInfo->HasAreaAuraEffect()` detects party/raid-wide buffs, skips non-self target check
- **Self-cast filter bypass**: `isAreaBuff` guard prevents area aura buffs from being dropped by `isSelfCast` return
- **Target name fix**: `targetName = "the group"` for area aura effects (was empty/self)
- Python dispel category added to spell prompt builder (caster + observer perspectives)

### Bug Fixes
- Fixed `QuestAcceptCooldown` config dead — was loaded but hook used `_questDeduplicationWindow` instead
- Fixed cooldown consumed before reactor validation — timestamp write moved AFTER `GetRandomBotInGroup()`
- Fixed static `_questAcceptCd` scope issue — moved declaration out of inner block scope
- Fixed unicode arrow corruption in config comments (`clear→rain` → `clear->rain`)
- Fixed stale comment `xpSource == 2` → `xpSource == 3`

### Files Changed
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` — Weather ambient, quest accept hook, discovery hook, spell classification expansion
- `modules/mod-llm-chatter/src/LLMChatterConfig.h` — New config member variables
- `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` — Config loading for new settings
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` — New config entries
- `env/dist/etc/modules/mod_llm_chatter.conf` — Active config entries
- `modules/mod-llm-chatter/tools/chatter_group.py` — Quest accept, discovery, dispel prompt handlers
- `modules/mod-llm-chatter/tools/chatter_events.py` — Weather ambient handler
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` — New dispatch entries
- `docs/mod-llm-chatter/future-plans.md` — Updated #17 proximity chatter vision, marked items done
- `docs/reviews/quest-accept-discovery-reactions-review.md` — Review doc
- `docs/reviews/spell-classification-expansion-review.md` — Review doc

### Status
- All C++ changes awaiting compilation (scheduled for next session)
- Python changes need bridge restart (new handlers for weather_ambient, quest_accept, discovery, dispel)

---

## 2026-02-17 (Session 48) - Non-Blocking Main Loop + Config Extraction

### Summary

Implemented the non-blocking main loop plan: moved pre-cache refill, idle group chatter, and legacy general chat processing from the main thread to the ThreadPoolExecutor worker pool. Added thread safety for shared state in chatter_group.py. Fixed DB connection leak in both main loop and startup. Extracted 8 hardcoded C++ values to config variables.

### Non-Blocking Worker Pool (Python)
- Pre-cache refill, idle chatter, legacy requests all submit to executor via `_run_in_worker()` helper
- Each background task gets its own DB connection (same pattern as `process_single_event`)
- At-most-one execution: futures tracked (`precache_future`, `idle_chatter_future`, `legacy_future`), only submit when `None`
- Executor pool size increased to `max_concurrent + 3` to prevent starving event workers
- Pre-cache no longer gated behind `not active_futures` — runs on schedule regardless of event activity
- `_harvest_future()` helper prunes completed background task futures

### Thread Safety (Python)
- `_bot_mood_scores`: `threading.RLock()` wrapping 4 functions (evict, update, get_label, cleanup)
- RLock needed because `update_bot_mood()` calls both `_evict_stale_moods()` and `get_bot_mood_label()`
- `_last_idle_chatter`: `threading.Lock()` + `_idle_inflight` set for atomic cooldown check + inflight reservation
- Cooldown timestamp only updates on successful LLM response (preserved existing behavior)
- `try/finally` releases inflight reservation on any exit path

### DB Connection Leak Fix (Python)
- Main loop: `db` wrapped in `try/finally` (was skipped on exception)
- Startup: `reset_stuck_processing_events` wrapped in `try/finally` (was skipped on exception)

### Config Extraction (C++ — needs compilation)
- `LLMChatter.GroupChatter.SpellCastCooldown = 10` (was hardcoded 45s)
- `LLMChatter.GroupChatter.LowHealthThreshold = 25` (was hardcoded 25%)
- `LLMChatter.GroupChatter.OOMThreshold = 15` (was hardcoded 15%)
- `LLMChatter.GroupChatter.CombatStateCheckInterval = 5` (was hardcoded 5s)
- `LLMChatter.GroupChatter.QuestDeduplicationWindow = 30` (was hardcoded 30s)
- `LLMChatter.MaxBotsPerZone = 8` (was hardcoded 8)
- `LLMChatter.MaxMessageLength = 250` (was hardcoded 250)
- `LLMChatter.GeneralChat.HistoryLimit = 15` (was hardcoded 15)
- `LLMChatter.GroupChatter.SpellCastChance` bumped from 15% to 40% in active config

### Files Changed
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` — Worker pool offload, DB leak fix, `_run_in_worker()` helper
- `modules/mod-llm-chatter/tools/chatter_group.py` — Thread safety for mood scores and idle chatter
- `modules/mod-llm-chatter/src/LLMChatterConfig.h` — 8 new member variables
- `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` — Config loading + startup logging
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` — Replace hardcoded values with config references
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` — 8 new config entries
- `env/dist/etc/modules/mod_llm_chatter.conf` — Active config entries + SpellCastChance bump

### Status
- Python changes deployed (bridge restarted, running cleanly)
- C++ changes awaiting compilation

---

## 2026-02-17 (Session 46) - General Channel Zone-Swap Fixes + Parallel Processing Plan

### Summary

Debugged and fixed General channel bot responses after zone transitions. Account bots were being excluded from candidate lists, event priority was backwards (ASC instead of DESC), and player_general_msg had too-low priority. Created and got review approval for a parallel event processing plan.

### Account Bot Priority Fix (C++)
- `sRandomPlayerbotMgr.GetAllBots()` filled all 8 slots before account bots were checked
- Swapped collection order: account bots (via sessions) checked FIRST, random bots fill remaining slots
- Both Garea and Seladan now appear in candidate lists

### Event Priority Fix (C++ + Python)
- `player_general_msg` had priority 2 while transport events had priority 6
- Bumped `player_general_msg` to priority 8 (highest regular event)
- Fixed SQL sort from `ORDER BY e.priority ASC` to `DESC` in both bridge queries
- Player messages now processed before ambient events

### Debug Log Cleanup (C++)
- Removed all LOG_INFO calls from `EnsureBotInGeneralChannel()`
- Kept only LOG_WARN for channel creation failure
- Eliminated dozens of "leaving"/"joining" lines per zone change

### Parallel Event Processing Plan
- Created plan at `docs/mod-llm-chatter/plans/parallel-event-processing-plan.md`
- ThreadPoolExecutor with atomic claiming, configurable `MaxConcurrent = 3`
- Thread-safe ZoneDataCache, split process_pending_events into fetch+process
- Reviewed by Gemini 3 Pro — verdict: architecturally sound
- Implementation pending (Python-only, no compilation needed)

### Files Changed
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` — Account bot priority, priority 8, debug log removal
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` — Priority sort ASC→DESC
- `docs/mod-llm-chatter/plans/parallel-event-processing-plan.md` — New plan file

### Compiled & Deployed
- C++ compiled successfully, server running
- Python bridge restarted
- Both account bots confirmed responding in General chat after zone transition

---

## 2026-02-16 (Session 45) - Chat History Config + Review Cleanup

### Summary

Made chat history limit configurable and reduced default from 15 to 10 messages for both group party chat and General channel. Added input validation with clamping. Cleaned up old review files and added "Rotating Personality Spices" to future plans.

### Chat History Limit Config
- New config key `LLMChatter.ChatHistoryLimit = 10` (was hardcoded 15)
- Module-level variable pattern in `chatter_group.py` and `chatter_general.py` — avoids updating 22+ call sites
- `init_group_config(config)` and `init_general_config(config)` called from bridge startup
- Input validation: `try/except` for malformed values, clamped to `max(1, min(val, 50))`
- General channel prune query updated to use config value instead of hardcoded 15
- Startup log reports effective (clamped) value, not raw config string
- C++ prune in `LLMChatterScript.cpp:3026` still hardcoded at 15 (acceptable — Python fetches fewer)

### Review Cleanup
- Deleted 7 pre-session-43 review files from `docs/reviews/`
- Kept 5 session 43/44 reviews as reference

### Future Plans
- Added "Rotating Personality Spices" concept to `future-plans.md`: core traits always sent, 2-3 random "spices" per LLM call from a pool of 15-20 (mood/situational coloring), saves tokens while increasing variety

### Files Changed
- `modules/mod-llm-chatter/tools/chatter_group.py` — `_chat_history_limit` var, `init_group_config()`
- `modules/mod-llm-chatter/tools/chatter_general.py` — `_chat_history_limit` var, `init_general_config()`, prune query
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` — imports, init calls, startup log
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` — new `LLMChatter.ChatHistoryLimit`
- `docs/mod-llm-chatter/future-plans.md` — added Rotating Personality Spices

### Python-Only Change
- No C++ compilation needed
- Bridge restart applies changes

---

## 2026-02-16 (Session 44b) - Emote System Expansion + Session Fixes

### Summary

Expanded the bot emote system from 25 curated emotes to ~243 emotes covering all `TEXT_EMOTE_*` values in WotLK 3.3.5a. Changed C++ emote delivery from animation-only (`HandleEmoteCommand` with `EMOTE_ONESHOT_*`) to full text emote broadcasting (`SMSG_TEXT_EMOTE` + animation lookup from `sEmotesTextStore`), producing both visual animation AND orange chat text. Multiple bug fixes from session testing.

### Emote System Expansion
- `EMOTE_LIST` expanded from 25 to ~243 entries in `chatter_constants.py`
- `EMOTE_KEYWORDS` expanded from ~100 to ~185 keyword→emote mappings
- Old emote names remapped: `exclamation`→`gasp`, `question`→`curious`, `yes`→`nod`
- New C++ `GetTextEmoteId()` maps emote names to `TEXT_EMOTE_*` IDs (was `GetEmoteId()` → `EMOTE_ONESHOT_*`)
- New C++ `SendBotTextEmote()` function: looks up animation from `sEmotesTextStore`, plays animation, broadcasts `SMSG_TEXT_EMOTE` packet for orange chat text
- Dance emote special-cased to use `EMOTE_ONESHOT_DANCESPECIAL` (one-shot, not looping `EMOTE_STATE_DANCE`)
- Both call sites updated (pre-cache broadcast + message delivery loop)

### Bug Fixes
- **Self-cast early return**: Bots no longer comment on their own self-casts (e.g. PW:Shield on self). Added `if (isSelfCast) return;` before both pre-cache and live LLM paths
- **Pre-cache spell_support gate**: Changed from `isCasterReactor` to `isSelfCast` check — caster buffing another player now gets instant pre-cached delivery
- **Composition comment player class**: Fixed hallucination where LLM guessed player's class. Now queries `characters` table for actual player class
- **Greeting/welcome message length**: Changed from `_pick_length_hint(mode)` to 70% short / 30% medium RNG for rapid bot invite scenarios

### Config Changes
- `LLMChatter.ActionChance`: default changed from 20 to 10 (reduced action frequency)
- `LLMChatter.GroupChatter.CompositionCommentChance`: new config key (default 10, was hardcoded 50%)
- `LLMChatter.GroupChatter.StateCalloutCooldown`: default changed from 60 to 30

### Files Changed
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` — Emote system rewrite, self-cast fix, pre-cache gate fix
- `modules/mod-llm-chatter/tools/chatter_constants.py` — Expanded EMOTE_LIST, EMOTE_KEYWORDS
- `modules/mod-llm-chatter/tools/chatter_shared.py` — ActionChance default 20→10
- `modules/mod-llm-chatter/tools/chatter_group.py` — Composition player class lookup, greeting length, precache spell perspective
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` — Config logging for CompositionCommentChance, ActionChance default
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` — New CompositionCommentChance, updated defaults
- `docs/mod-llm-chatter/future-plans.md` — Added quest accept reactions future plan

### Compiled & Deployed
- C++ compiled successfully, server running
- Python bridge restarted

---

## 2026-02-16 (Session 44) - Structured JSON Action Field

### Summary

Replaced brittle Phase 1/2 regex narration detection with structured LLM output. All prompt builders now instruct the LLM to respond with `{"message": "...", "emote": "...", "action": "..."}` instead of plain text. The action field is assembled as `*action* message` in WoW chat. Phase 1/2 regex detection kept as fallback for plain-text responses. This is the feature described in Session 43's future plans.

### Core Helpers (chatter_shared.py)

- `append_json_instruction(prompt, allow_action)` — appends structured JSON format block to any prompt
- `parse_single_response(response)` — parses JSON with ```json stripping, emote validation, action sanitization; falls back to plain text
- `_sanitize_action(raw_action)` — strips `*"'`, validates 2-80 chars
- `set_action_chance(pct)` / `get_action_chance()` — module-level config variable
- `cleanup_message(message, action=None)` — when action provided, prepends `*{action}*` and skips Phase 1/2 regex via `_skip_narration_detection` flag
- `parse_conversation_response()` — now extracts action field from multi-message JSON

### Config

- `LLMChatter.ActionChance = 20` (0-100%, default 20) — applies to ALL contexts (group, general, ambient, conversations)
- Added to both `.conf.dist` and active config

### Scope

- 24 prompt builders + 23 handler sites in `chatter_group.py`
- 6 statement builders + 6 conversation builders in `chatter_prompts.py`
- 2 builders + 2 handlers in `chatter_general.py`
- 3 handler paths in `llm_chatter_bridge.py` (statement, conversation, pending events)
- Pre-cache pool in `chatter_cache.py`
- `_build_composition_comment_prompt()` also converted (was missed in initial pass)

### Post-Review Fixes

- Event-conv delivery path was dropping action (now passes `action=msg.get('action')`)
- General channel cleanup/strip ordering fixed (strip prefix BEFORE cleanup)
- Idle conversation strip ordering fixed (same)
- Conversation builders now accept `allow_action` and gate action instructions (config-authoritative)
- Hardcoded "about 20%" in conversation prompts replaced with "only when it adds character"
- `strip_speaker_prefix` added to both conversation delivery loops in bridge
- RP guideline updated: "actions go in the action JSON field, not in the message"

### Files Changed

- `modules/mod-llm-chatter/tools/chatter_shared.py` — Core helpers, cleanup_message modification
- `modules/mod-llm-chatter/tools/chatter_group.py` — 24 builders + 23 handlers + idle conversation
- `modules/mod-llm-chatter/tools/chatter_prompts.py` — 6+6 builders + RP guideline
- `modules/mod-llm-chatter/tools/chatter_general.py` — 2 builders + 2 handlers
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` — Config init, 3 handler paths, conversation delivery
- `modules/mod-llm-chatter/tools/chatter_cache.py` — Pre-cache refill
- `env/dist/etc/modules/mod_llm_chatter.conf.dist` — ActionChance config
- `env/dist/etc/modules/mod_llm_chatter.conf` — ActionChance config
- `docs/reviews/session44-structured-json-action-field-review.md` — Review doc

---

## 2026-02-16 (Session 43) - Compilation + Emote Wrapping + Quest Team Spirit + Kill Tuning

### Summary

Completed the Session 41/42 compilation that was interrupted by Docker Desktop restart. Then implemented four Python-only improvements: emotes are now wrapped in `*...*` instead of stripped, quest completion prompts use team-spirit "we" language with turn-in NPC lookup, normal kill reaction chance halved, and RP prompt guideline updated to allow occasional emote prefixes.

### Compilation (Session 41/42 C++ deployed)

- Resumed from where Session 42 left off (modules compiled, linking/install/restart pending)
- Full pipeline: touch sources → make modules → make worldserver → make install → chmod +x → restart
- All Session 41 reactive bot state + Session 42 bugfixes now live and running

### Emote Wrapping (Python)

- **Asterisk emotes preserved**: Previously `*action*` was stripped to `action` — now kept as-is for RP flavor in WoW chat
- **Phase 1 (leading narration)**: Bare narration like "glances over, Keep your distance" now wrapped as `*glances over* Keep your distance` instead of stripped
- **Phase 2 (mid-message emotes)**: Clauses like ", sighs heavily" now wrapped as `*sighs heavily*` instead of removed
- **False positive protection**: Phase 1 requires emote verb + narration follower word (directional prepositions or -ly adverbs) — prevents wrapping normal speech like "Nods are important"
- **Prompt guideline**: Changed from "NEVER use third person" to "occasionally (20%) prefix with brief *action* (2-4 words), always followed by speech"
- **Future plan noted**: Current heuristic is brittle — structured JSON `"action"` field would be cleaner (added to future plans)

### Quest Completion Team Spirit (Python)

- Quest completion prompt rewritten: "Your group just completed" with "use 'we' language, not 'you' or single names"
- **Turn-in NPC lookup**: New `query_quest_turnin_npc()` queries `creature_questender` + `creature_template` from acore_world
- NPC name injected into prompt as friendly context ("You turned it in to Starweave the Elder") with guard: "FRIENDLY NPC — never imply you fought or killed them"
- Fixes: bot was hallucinating "Starweave the Elder goes down" for quest turn-ins

### Kill Chance Reduction (Config)

- `KillChanceNormal` reduced from 20% to 10% in both active config and conf.dist
- Boss/rare remain at 100% (rare encounters, always worth reacting to)
- Addresses "bots too chatty" during normal grinding

### Files Changed

- `modules/mod-llm-chatter/tools/chatter_shared.py` — Emote wrapping (Phase 1/2), `_NARRATION_FOLLOWERS`, `query_quest_turnin_npc()`
- `modules/mod-llm-chatter/tools/chatter_prompts.py` — RP guideline allowing occasional emotes
- `modules/mod-llm-chatter/tools/chatter_group.py` — Quest team spirit prompt, NPC lookup integration, import
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` — KillChanceNormal 20→10
- `env/dist/etc/modules/mod_llm_chatter.conf` — KillChanceNormal 20→10
- `docs/current_progress.md` — Future plan for structured emote system
- `docs/reviews/session43-emote-wrapping-quest-tuning-review.md` — Review doc

### Status

- All Python changes deployed (bridge restarted)
- Config change requires server restart (pending)
- No C++ changes this session — compilation was for prior sessions
- Review doc created and updated with findings

---

## 2026-02-15 (Session 42) - Pre-Cache In-Game Testing: 7 Bugfixes

### Summary

In-game testing of the pre-cached reactions system (implemented Session 41b) revealed 7 bugs across loot, quest, and spell subsystems. All fixed in C++ and Python. Three rounds of review caught 5 additional issues (all fixed). Compilation started but Docker Desktop needed restart due to memory leak from concurrent orphan compilers.

### Bug Fixes

**1. Bot loot reactions missing item context (C++)**
- `HandleGroupLootEvent` had `isBot` branch that set `quality=255` / `itemName="something"` (Session 27b safety measure)
- Root cause: `GroupHasRealPlayer()` filter already eliminates the dangerous random-bot-only-group crash vector
- Fix: all players (bot or real) now access `Item*` directly with null checks
- Removed all `quality == 255` special-case branches

**2. Spell self-congratulation via pre-cache (C++)**
- Cached spell_support messages use `{caster}` placeholder (observer perspective)
- When caster == reactor, this resolves to bot's own name ("Good timing with that MotW, Cylaea!")
- Fix: `isCasterReactor` check skips pre-cache, falls through to live LLM (first-person perspective)

**3. White/grey items triggering loot reactions (C++)**
- Side effect of fix #1: quality filter now works properly (was bypassed when quality=255)

**4. Loot reactor always self-reacting (C++ + Python)**
- Looter was always the reactor — no groupmate commentary
- Fix: 50% self-react, 50% another bot via `GetRandomBotInGroup(group, player)`
- Added `looter_name` field to extra_data, Python reads it for prompt perspective
- Prompt rule: "NEVER say the item will serve YOU if someone else looted it"

**5. Duplicate quest completion events (C++)**
- `OnPlayerCompleteQuest` fires per player/bot — 3+ reactions for one quest
- Fix: static dedup map with composite key `(groupId << 32) | questId`, 30s window
- Reactor changed to random bot (not self)

**6. Multi-speaker in single LLM response (Python)**
- LLM sometimes embedded second speakers mid-message ("...Cylaea: Hold. Do you smell that?")
- Fix: regex `\b[A-Z][a-z]{2,}:\s` after position 20 detects and truncates

**7. OOM callouts for non-mana classes (Python)**
- Pre-cache generated `state_oom` for Warriors/Rogues/Death Knights
- Fix: `_NON_MANA_CLASS_IDS = {1, 4, 6}` skip in cache refill loop

### Review Findings (3 rounds, 5 issues)

- `isBot` undefined after refactor — replaced with hardcoded `"is_bot":1` + new `completer_is_bot`
- Quest reactor/completer semantics mismatch between C++ and Python — aligned Python to trust C++ reactor
- Spell pre-cache prompt still randomized caster/observer — forced observer-only perspective
- Python `is_bot` NameError in quest handler — reads `completer_is_bot` from extra_data
- `is_bot` hardcoded to 1 mislabels real player completions — `completer_is_bot` field distinguishes

### Files Changed

- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` — Item* access restored, loot reactor randomization, spell caster-as-reactor skip, quest dedup, completer_is_bot field
- `modules/mod-llm-chatter/tools/chatter_group.py` — Loot handler reactor/looter distinction, quest handler aligned with C++ reactor, spell pre-cache observer-only
- `modules/mod-llm-chatter/tools/chatter_shared.py` — Multi-speaker truncation in `cleanup_message()`
- `modules/mod-llm-chatter/tools/chatter_cache.py` — OOM skip for non-mana classes
- `docs/reviews/loot-quest-precache-bugfixes-review.md` — Review doc

### Status

- C++ modules compiled (`Built target modules`) but linking/install/restart not completed
- Docker Desktop restarted due to memory leak from concurrent orphan compilers
- Python bridge restart needed after compilation

---

## 2026-02-15 (Session 41) - Reactive Bot State + QA Cross-Reference + Error Logging + Narration Fix

### Summary

Implemented reactive bot state injection (C++ + Python), performed comprehensive QA cross-reference of WoW chat log vs bridge log (verified 20+ features), added API error context logging to all 31+ call_llm() sites, and built a two-phase third-person narration stripper. Fixed Phase 2 emote regex bug (false-positive speech stripping) and case-sensitive continuer check found during LLM review.

### Reactive Bot State (New Feature - C++ + Python)

- **C++ `BuildBotStateJson(Player*)`** static helper in `LLMChatterScript.cpp`:
  - Reads real-time state: `GetHealthPct()`, `GetPowerPct(POWER_MANA)`, `IsInCombat()`, `GetVictim()->GetName()`
  - PlayerbotAI role detection: `IsTank()`/`IsHeal()`/`IsRangedDps()` for accurate role (tank/healer/ranged_dps/melee_dps)
  - `ai->GetState()` for bot AI state (combat/non_combat/dead)
  - Injected into 5 handlers: kill, wipe, loot, combat, spell (death skipped - reactor unknown in C++)
- **Death handler enrichment**: enriches dead bot's state (always health=0, state=dead) for LLM context
- **Role stored in bot traits**: `actual_role` column added to `llm_group_bot_traits`, populated on group join
- **State-triggered callouts**: low HP (<30%), OOM (<20%), aggro warnings as new event types
- **Python `build_bot_state_context(extra_data)`** in `chatter_shared.py`:
  - Converts bot_state dict to natural language (role, health status, mana status, combat target)
  - Threaded through 5 prompt builders + 5 caller sites in `chatter_group.py`
  - `actual_role` overrides `CLASS_ROLE_MAP` fallback for accurate role identity

### QA Cross-Reference Analysis

- Compared 796-line WoW `/chatlog` against 6600-line bridge log
- **20+ features verified working**: General chat, transport, greetings, farewells, kill/combat/loot/spell reactions, quest objectives/completion, level up, zone transitions, idle banter, player msg responses, death, low health callout, resurrect, anti-repetition, mood drift, playerbot command filtering
- **7 dropped messages found**: Anthropic API connection errors at 12:58 (2) and 13:29-13:30 (5)
- **User insight**: more retries make combat messages stale - better to drop than deliver late

### Fix #5 - API Error Context Logging

- `call_llm()` gains `context: str = ''` parameter in `chatter_shared.py`
- Error log now shows what was lost: `LLM API error (anthropic) [grp-kill]: ConnectionError...`
- 28+ call sites updated across 4 files: `chatter_group.py` (25), `chatter_general.py` (2), `llm_chatter_bridge.py` (4)
- 22 silent `if not response: return` blocks now emit `logger.warning()`

### Fix #6 - Third-Person Narration Stripping

- Phase 1 (new): Strips leading third-person narration from LLM output
  - Detects emote verbs at string start (21 verbs: gazes, glances, nods, sighs, etc.)
  - Finds speech boundary after separator, skipping continuer words (then, and, while, before, as)
  - `"glances back at the Oracle, then refocuses. Keep your distance..."` -> `"Keep your distance..."`
- Phase 2 (fixed): Removed `^|` anchor that could strip valid speech starting with emote verbs
  - e.g. "Nods are important in orcish culture" was being incorrectly stripped
- Case-sensitivity fix: `_speech_re` now uses `re.IGNORECASE` so ", Then..." matches continuer check

### Review Findings Addressed

- **High**: Phase 2 `^` anchor stripped valid speech at string start - fixed by removing `^|`
- **Medium**: Case-sensitive continuer check missed capitalized words - fixed with `re.IGNORECASE`
- **Low**: Review doc had wrong context labels and file references - corrected
- **Low**: Encoding artifacts (mojibake) in review doc - replaced with ASCII

### Files Changed

- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` - `BuildBotStateJson()`, 5 handler injections, death enrichment, role storage, state callouts
- `modules/mod-llm-chatter/tools/chatter_shared.py` - `call_llm()` context param, `build_bot_state_context()`, `cleanup_message()` narration strip
- `modules/mod-llm-chatter/tools/chatter_group.py` - 25 call_llm context labels, 22 warning logs, 5 prompt builders + callers with extra_data
- `modules/mod-llm-chatter/tools/chatter_general.py` - 2 call_llm context labels
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` - 4 call_llm context labels
- `docs/reviews/api-error-logging-narration-strip-review.md` - new review doc

---

## 2026-02-14 (Session 40b) - First-Person Prompt Fix, Reactive State Plan, Future Vision

### Summary

Fixed narrator-voice bug in RP mode prompts (bots were writing "gazes at" and "adjusts pack" instead of first-person speech). Drafted implementation plan for reactive bot state integration. Added three new features to future plans: pre-cached reactions, bot-initiated questions, force-join General channel.

### First-Person Prompt Fix (Bug Fix)

- **Root cause**: RP-mode reaction/style options in prompt builders used theatrical stage-direction language ("examining the item with a practiced eye", "hawking your find to passers-by") which nudged the LLM into third-person narrator voice
- **Fix**: Added explicit first-person rule to `build_dynamic_guidelines()` for RP mode: "ALWAYS write in first person... NEVER write in third person or narrator voice"
- Rewrote 4 sets of RP reaction/style options across loot, trade, quest reward, and spell prompt builders to use first-person compatible language
- Emote animation system (Session 36) confirmed unrelated — works correctly with keyword-matched `HandleEmoteCommand()`

### Reactive Bot State Plan (Drafted, Not Implemented)

- Saved to `docs/mod-llm-chatter/reactive-bot-state-plan.md`
- C++ `BuildBotStateJson()` helper reads real-time state via PlayerbotAI: health%, mana%, actual role (IsTank/IsHeal/IsDps), combat target, BotState
- Injects `bot_state` object into all 6 handler extra_data JSON blobs
- Python `build_bot_state_context()` converts state to natural-language prompt context
- Replaces static `CLASS_ROLE_MAP` guessing with talent-based role from PlayerbotAI
- Phase 1: core state injection, Phase 2: state-triggered events (OOM/low HP callouts), Phase 3: strategy awareness

### Future Plans Added

- **Pre-Cached Reactions**: Same pattern as farewell messages — pre-generate messages for predictable events (spells, combat cries, loot, zone transitions), deliver instantly, replenish in background
- **Bot-Initiated Questions**: Bots occasionally ask the player questions in party chat, creating two-way conversation and making bots feel interested in others
- **Force-Join General Channel**: Auto-join bots to General channel in `TryTriggerChatter()` when they fail `CanSpeakInGeneralChannel()` check (C++ fix for future compile)

### Files Changed

- `modules/mod-llm-chatter/tools/chatter_prompts.py` — first-person rule + 4 rewritten RP style/reaction lists
- `docs/mod-llm-chatter/reactive-bot-state-plan.md` — new plan doc
- `docs/mod-llm-chatter/future-plans.md` — 3 new future items

---

## 2026-02-14 (Session 40) - Group Role Awareness, Composition Commentary, Review Command

### Summary

Added combat role perspective to bot chatter prompts and group composition commentary on join. Three Python-only features, no compilation needed. Created `/ri` slash command for generating review instruction docs.

### Group Role Awareness (New Feature)

- **`CLASS_ROLE_MAP`** in `chatter_constants.py` — maps all 10 WoW classes to 6 roles (tank, healer, melee_dps, ranged_dps, hybrid_tank, hybrid_healer)
- **`ROLE_COMBAT_PERSPECTIVES`** — 3-4 sentence combat perspective per role, injected into all RP-mode prompts via `build_race_class_context()` in `chatter_shared.py`
- Propagates automatically to all 19+ prompt builders (group, ambient, General channel) — zero call-site changes
- **RP-mode only** — every call site gates behind `is_rp` check, normal mode unaffected
- Combat-language guard: "Only reference your role during combat situations" appended to each perspective to prevent combat talk in ambient prompts (transport, holiday, etc.)

### Group Composition Commentary (New Feature)

- When a bot joins a group, 50% chance to comment on group composition at 8s delay (staggered after greeting at 2s, welcome at 5s)
- `_get_group_role_summary()` JOINs `llm_group_bot_traits` with `characters` table, maps classes to roles, returns readable summary + has_tank/has_healer flags
- `_build_composition_comment_prompt()` builds short prompt with pointed observations (e.g. "There is no dedicated healer")
- Requires 2+ bots in group, one short sentence only, no duplicate greetings
- Wired as step 7b in `process_group_event()` between welcome and farewell

### Review Command

- Created `/ri` slash command (`.claude/commands/ri.md`) for generating review instruction markdown files
- Outputs to `docs/reviews/<feature-name>-review.md`
- Template covers: summary, changed files, architecture context, review checklist, potential concerns, testing steps, file references
- Applies to any AzerothCore module, not just AI modules

### Review Findings Addressed

- Scope/mode-gating accuracy in review docs (RP-only, all prompt families)
- Sentence count corrected (3-4, not 2)
- Ambient prompt impact framed as hypothesis needing validation
- Docstring fix: "3+ bots" → "2+ bots" to match code
- Noted: `sequence` column unused in C++ delivery ORDER BY — future fix to add `ORDER BY deliver_at, sequence, id`

### Files Changed

- `modules/mod-llm-chatter/tools/chatter_constants.py` — added `CLASS_ROLE_MAP`, `ROLE_COMBAT_PERSPECTIVES`
- `modules/mod-llm-chatter/tools/chatter_shared.py` — import + 4 lines in `build_race_class_context()`
- `modules/mod-llm-chatter/tools/chatter_group.py` — 3 new functions + wiring in process_group_event step 7b, `CLASS_ROLE_MAP` import
- `.claude/commands/ri.md` — new review instructions command
- `docs/reviews/group-role-awareness-review.md` — review doc
- `docs/reviews/group-composition-commentary-review.md` — review doc

---

## 2026-02-14 (Session 39b) - Holiday Fix, Minor Events, Anti-Repetition, Bug Fixes

### Summary

Fixed holiday event misidentification (Call to Arms BG rotations detected as holidays), added minor game event support, implemented two-layer anti-repetition system, fixed text cleanup bugs, and rebalanced config settings. All changes compiled and deployed.

### Holiday Event Fix (High Priority Bug)

- **Root cause**: `IsHolidayEvent()` only checked `HolidayId != HOLIDAY_NONE`, but Call to Arms BG rotations (eventEntry 18-21, 53-54) also have non-zero HolidayIds. In a 4-hour play session, 7 of 8 "holiday" events were actually "Call to Arms: Warsong Gulch" instead of "Love is in the Air".
- **Fix**: `IsHolidayEvent()` now excludes events with descriptions containing "Call to Arms", "Building" (Darkmoon setup phases), "Fishing Pools", or "Fireworks"
- **Review finding fixed**: Periodic re-queue gate checked only `_eventsHolidays`, blocking minor events when holidays disabled. Fixed to `_eventsHolidays || _eventsMinor`.

### Minor Game Event Support (New Feature)

- New `IsMinorGameEvent()` identifies Call to Arms, fishing derbies, fireworks as worth occasional mention
- New event type `minor_event` -- separate from `holiday_start`, with its own RNG chance
- Config: `LLMChatter.Events.MinorEvents = 1`, `LLMChatter.Events.MinorEventChance = 20`
- Python handler in `chatter_events.py` with event-appropriate context wording
- DB ENUM updated (base schema + live DB ALTER)
- Minor events NOT in `alwaysFire` list (go through normal RNG unlike holidays)

### Anti-Repetition System (New Feature)

- **Layer 1 - Prompt injection**: Queries last 15 delivered messages from the zone (30 min window), injects into LLM prompt with "DO NOT repeat" instruction. Zone-scoped via JOIN on queue/event tables.
- **Layer 2 - N-gram rejection**: After LLM response, extracts 4-word sequences and compares against recent messages. Any shared 4-gram triggers silent drop (returns True so caller marks as completed, not failed).
- Integrated into all 12 ambient prompt builders (chatter_prompts.py), 2 General channel builders (chatter_general.py), 2 group idle builders (chatter_group.py), and bridge statement/conversation/event processing.
- Review findings fixed: zone-scoping via JOIN (was global), drop returns True (was False causing failed status), threshold parameter now actually used.

### Text Cleanup Bug Fixes

- **Backslash escape leaking**: `Nature\'s Grasp` appeared in chat. Fixed with `replace("\\'", "'")` etc. in `cleanup_message()`.
- **Non-asterisk emote stripping**: LLM embedded "gazes toward the horizon" without asterisks, bypassing existing `*action*` regex. Added 21 unambiguous emote verb pattern matching at sentence boundaries. Removed 10 dual-use verbs (looks, turns, waves, etc.) after review.

### Config Rebalancing

- `TriggerIntervalSeconds`: 40 -> 50 (~60 msgs/hr instead of ~75)
- `HolidayCooldownSeconds`: 1800 -> 900 (holiday mentions every ~15min instead of ~30min)

### Log Level Cleanup

- Demoted 20 success-output logs from `logger.warning` to `logger.info` in `chatter_group.py`
- Error/skip logs kept as `logger.warning` (12+ instances)

### Files Changed

**C++ (compiled)**:
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` - IsHolidayEvent fix, IsMinorGameEvent, OnStart/OnStop/CheckActiveHolidays for minor events, minor_event chance in QueueEvent
- `modules/mod-llm-chatter/src/LLMChatterConfig.h` - `_eventsMinor`, `_minorEventChance`
- `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` - config loading

**Config**:
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` - MinorEvents, MinorEventChance
- `env/dist/etc/modules/mod_llm_chatter.conf` - all config changes

**Python (bridge restart)**:
- `modules/mod-llm-chatter/tools/chatter_shared.py` - anti-repetition helpers, backslash fix, emote stripping
- `modules/mod-llm-chatter/tools/chatter_prompts.py` - recent_messages param on 12 builders
- `modules/mod-llm-chatter/tools/chatter_general.py` - recent_messages wiring
- `modules/mod-llm-chatter/tools/chatter_group.py` - recent_messages wiring, log level cleanup
- `modules/mod-llm-chatter/tools/chatter_events.py` - minor_event handler
- `modules/mod-llm-chatter/tools/chatter_constants.py` - EVENT_DESCRIPTIONS entry
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` - anti-repetition wiring + post-processing

**SQL**:
- `modules/mod-llm-chatter/data/sql/db-characters/base/llm_chatter_tables.sql` - minor_event ENUM

**Docs**:
- `docs/review-session39b-holiday-minor-events.md` - Holiday/minor event review
- `docs/review-session39c-balance-bugs-antirepetition.md` - Balance/bugs/anti-rep review

### Technical Notes

- `game_event` table: Call to Arms events have HolidayIds (283-285, 353, 400, 420) but are NOT real holidays
- "Building" events (Darkmoon Faire setup) are excluded from BOTH holiday and minor -- they're invisible setup phases
- Anti-repetition zone-scoping requires JOIN through `llm_chatter_queue.zone_id` or `llm_chatter_events.zone_id` since `llm_chatter_messages` has no zone_id column
- `is_too_similar()` threshold=1 means any single shared 4-gram triggers rejection. May need tuning if too strict.
- Emote verb list carefully curated: removed "looks", "turns", "waves", "points", "shakes", "pauses", "shifts", "crosses", "cracks", "laughs" as dual-use in normal speech

---

## 2026-02-14 (Session 39) - Transport Verified Bots, Double RNG Fix, Live Monitoring

### Summary

Live monitoring session in Auberdine revealed three transport conversation bugs. All three fixed, compiled, deployed, and verified with 100% message delivery (11/11 messages confirmed via WoW `/chatlog` cross-reference against bridge logs).

### Bug 1: Missing Messages — Unverified Bot Selection (High)

- **Root cause**: Event-triggered conversations (transport, holiday) selected bots in Python via SQL query, with NO channel membership check. Bots not in the General channel were included, their messages generated by LLM but silently dropped by `SayToChannel()`.
- **Fix (C++)**: `CheckTransportZones()` now collects bots in the zone, filters through `CanSpeakInGeneralChannel()`, and includes their GUIDs as `verified_bots` in the event's `extra_data` JSON.
- **Fix (Python)**: After SQL bot query, filters against `verified_bots` from extra_data. Only channel-verified bots participate. Empty `[]` is authoritative — causes early skip, no fallback to unfiltered query.
- **extra_data normalization**: Added `if not isinstance(extra_data, dict): extra_data = {}` to handle NULL/non-object JSON safely.

### Bug 2: Double RNG Gate (Medium)

- **Root cause**: Both C++ `QueueEvent()` (50%) and Python `process_pending_events()` (50%) rolled independent chance for transport events, making effective trigger rate 25%.
- **Fix**: Removed Python-side transport chance roll entirely. C++ handles the single 50% gate.
- Also removed Python-side per-zone transport cooldown (300s) — redundant with C++ per-route cooldown (600s, now 300s).

### Bug 3: Transport Cooldown Too Long (Low)

- **Root cause**: `TransportCooldownSeconds = 600` (10 min per route) exceeded some boat round-trip times (~5 min), suppressing every other arrival.
- **Fix**: Reduced to 300s in active config. Already a config variable, no code change needed.

### Review Process

- Review doc created: `docs/review-session39-transport-fixes.md`
- External agent review found 3 findings:
  1. **High**: Empty `verified_bots: []` didn't enforce filtering (falsy in Python) — fixed
  2. **Medium**: `extra_data` not normalized to dict before `.get()` calls — fixed
  3. **Low**: Startup log default 300 didn't match conf.dist default 600 — fixed
- Second review pass: clean, no findings

### Monitoring Results

- 11/11 transport messages delivered correctly (0 discards)
- Verified bot filter working: "Filtered to 4 verified bots (of 8 GUIDs)" — 4 bots excluded
- Multiple transport routes tested: The Bravery (Stormwind), Elune's Blessing (Azuremyst), The Moonspray (Rut'theran)
- Both statements and 2-4 bot conversations verified

### Files Changed

| File | Change |
|------|--------|
| `src/LLMChatterScript.cpp` | Verified bot collection + `CanSpeakInGeneralChannel()` filter in `CheckTransportZones()`, `verified_bots` JSON in extra_data |
| `tools/llm_chatter_bridge.py` | Removed transport double RNG + zone cooldown, early extra_data parsing, verified_bots filtering, extra_data dict normalization |
| `env/dist/etc/modules/mod_llm_chatter.conf` | `TransportCooldownSeconds` 600 → 300 |
| `docs/review-session39-transport-fixes.md` | Review doc for all three fixes |

### Technical Notes
- `verified_bots` in extra_data uses `GetGUID().GetCounter()` values — matches Python `c.guid` from characters table
- Empty `verified_bots: []` is authoritative (skip event), not a fallback signal
- Account bots collected via WorldSession iteration (same pattern as OnPlayerCanUseChat)
- WoW `/chatlog` flushes on logout, not real-time — useful for post-session cross-referencing

---

## 2026-02-14 (Session 38) - General Channel Pre-Check Filter, Locale Fix, Review Doc Update

### Summary

Continued from Session 37. Applied review findings to the General channel delivery fix. The core change: instead of retry-on-failure, implemented a **pre-check filter** (`CanSpeakInGeneralChannel()`) that removes bots not in the General channel from the candidate pool BEFORE selecting them for conversations. Also fixed a locale mismatch found during external review, and switched delivery to fail-fast strategy.

### Pre-Check Filter (C++ — PENDING COMPILATION)

- Root cause of silent message drops: `SayToChannel()` returns `true` even when bot isn't a channel member — `Channel::Say()` silently fails via private `IsOn()` check
- **Fix**: `CanSpeakInGeneralChannel()` static helper checks if bot is actually in a General channel for its zone
  - Uses `ChannelMgr::GetChannels()` to find General channel matching zone name
  - Uses `Player::IsInChannel(channel)` (PUBLIC) to verify bot membership
  - Applied in both `TryTriggerChatter()` and `OnPlayerCanUseChat()` via `std::remove_if`
  - If zone has 4 bots but only 2 in General, conversations limited to those 2

### Locale Fix (C++ — PENDING COMPILATION)

- External review (agent) found locale mismatch: our code used `area->area_name[0]` (hardcoded English) while `SayToChannel()` uses `GetLocalizedAreaName()` with `sWorld->GetDefaultDbcLocale()`
- **Fix**: Changed to `area->area_name[sWorld->GetDefaultDbcLocale()]` with `LOCALE_enUS` fallback, matching `SayToChannel()`'s approach
- On enUS servers (this project), no behavioral change — but now correct for non-enUS setups

### Fail-Fast Delivery (C++ — PENDING COMPILATION)

- Retry approach (Session 37) replaced with fail-fast: always mark `delivered=1` immediately
- Rationale: pre-check filter eliminates the primary failure mode; remaining failures are edge cases not worth blocking the queue over
- Retry would block queue via `LIMIT 1 ORDER BY deliver_at ASC` — a stuck message blocks all later messages for up to 60s
- 60s staleness expiry preserved as safety net for zombie rows

### Review Doc Update

- Updated `docs/review-session37-general-channel-delivery-fix.md` to reflect final implementation (pre-check + fail-fast replacing retry)
- Added detailed locale analysis (3 locale sources: session, world default, enUS)
- Fixed timing statement: 4s → 3s for 4-message conversation delivery
- External review verified: all 6 participant enforcement locations correct, raw logging at all 3 sites, fail-fast behavior matches doc

### Files Changed

| File | Change |
|------|--------|
| `src/LLMChatterScript.cpp` | `CanSpeakInGeneralChannel()` helper, bot pool filter in 2 locations, fail-fast delivery, locale fix (`area_name[0]` → `sWorld->GetDefaultDbcLocale()`), `#include <algorithm>` |
| `docs/review-session37-general-channel-delivery-fix.md` | Full rewrite for final implementation (4 issues, locale analysis, rejected approaches) |

### Technical Notes
- `Channel::IsOn(ObjectGuid)` is PRIVATE (`Channel.h:272`) — can't check membership externally
- `Player::IsInChannel(const Channel*)` is PUBLIC (`Player.h:2064`) — compares by `GetChannelId()`, not channel pointer
- `IsInChannel()` returns true for ANY General channel (not zone-specific) — but `SayToChannel()` separately matches by zone name, so delivery is zone-correct
- Three locale sources: channel names use session locale, `SayToChannel()` uses world default locale, we now match world default locale
- `ChannelMgr::GetChannels()` returns `const ChannelMap&` — safe to iterate on world thread

---

## 2026-02-14 (Session 37) - General Channel Delivery Fix, Participant Enforcement, Transport Direction Fix

### Summary

Investigated missing messages in General channel conversations (2 of 5 messages from Valnorion not appearing in Stormwind). Found two separate issues: (1) LLM skipping participants in 3+ bot conversations (root cause), and (2) bots not in General channel silently failing delivery. Added participant enforcement to all 7 conversation prompt builders, raw LLM response logging, transport direction fix for reversed origin/destination.

### Issue 1: LLM Skipping Participants (Root Cause — Python Fix, LIVE)

- In 3+ bot conversations, the LLM sometimes generated fewer messages than requested, completely skipping some participants
- Evidence: Auberdine test — 3 bots requested (Yladros, Lilya, Morlanna), only Yladros and Morlanna spoke, Lilya skipped entirely
- The earlier Stormwind "delivery failure" (2 of 5 messages missing) was likely the same issue
- **Fix**: Added "EVERY speaker MUST have at least one message — do NOT skip any participant" to all 7 conversation prompt builders, gated behind `bot_count > 2` / `num_bots > 2`
- Added raw LLM response logging before `parse_conversation_response()` at all 3 call sites for future diagnostics
- **Verified working**: 3-bot conversation in Auberdine (Reraeth, Yladros, Shalsia) — all 3 spoke correctly

### Issue 2: Silent Delivery Drops — Root Cause Identified

- `SayToChannel()` returns `true` even when bot isn't a channel member — `Channel::Say()` silently fails via private `IsOn()` check
- Root cause confirmed: bots not in the General channel can't speak in it, but delivery code thinks it succeeded
- C++ pre-check filter implemented in Session 38

### Transport Direction Fix (Python — LIVE)

- Transport event context showed reversed direction — said "bots are AT Rut'theran Village" when user was in Auberdine
- Root cause: `ParseTransportName()` in C++ always takes second stop as destination from static DB name, regardless of travel direction
- **Fix**: Python `build_event_context()` compares event `zone_id` name against origin/destination, swaps if zone matches origin
- **Verified working**: "The Bravery" event correctly showed "arrived here at Auberdine, Darkshore from Stormwind Harbor"

### Other Changes

- `TransportEventChance` changed from 0% to 50% in active config (was accidentally set to 0)
- Bridge stuck issue observed — bridge silently stopped processing after ~6 minutes, required restart. Root cause unknown.
- External LLM review process (3 rounds) caught: sub-zone root cause incorrect, queue starvation risk, idle conversations can be 2-4 bots not always 2, raw logging needed in all paths, fuzzy match can also drop messages
- Review document created: `docs/review-session37-general-channel-delivery-fix.md`

### Files Changed

| File | Change |
|------|--------|
| `tools/chatter_prompts.py` | Participant enforcement in 6 General conversation prompt builders (bot_count > 2) |
| `tools/chatter_group.py` | Participant enforcement in idle prompt (num_bots > 2), raw LLM response logging |
| `tools/llm_chatter_bridge.py` | Raw LLM response logging in process_conversation() and event-conversation path |
| `tools/chatter_events.py` | Transport direction fix — zone-based origin/destination swap |
| `env/dist/etc/modules/mod_llm_chatter.conf` | TransportEventChance 0→50 |

### Technical Notes
- `SayToChannel()` returns true when it finds a matching General channel and calls `Say()`, false when no channel matched
- `Channel::Say()` is void and can still silently fail (not-member, muted) — so `delivered=true` means channel found, not guaranteed broadcast
- `Map::GetZoneId()` already resolves sub-zones to parent zones (`Map.cpp:1279`) — sub-zone mismatch was NOT the root cause
- `parse_conversation_response()` has a custom fuzzy name match heuristic (not Levenshtein) with max edit distance 2 — can also silently drop messages with misspelled speaker names
- Transport DB names format: `"StopA, ZoneA and StopB, ZoneB (Type, Faction ("ShipName"))"` — static, doesn't change with direction
- C++ `TransportCooldownSeconds = 600` (10 min per transport route) combined with Python 50% chance means ~1-2 transport reactions per hour at Auberdine (3 routes)

---

## 2026-02-13 (Session 36) - 4 Immersion Features: Emotes, Mood Drift, Farewells, Item Links

### Summary

Implemented 4 immersion features from the future plans doc: emotes between bots (LLM-selected for conversations, keyword-matched for statements), session mood drift (per-bot mood evolves based on events), farewell messages (pre-generated on join, delivered via WorldPacket on leave), and item link reactions (bots comment on items linked in party chat). Centralized all INSERT statements into a single `insert_chat_message()` helper. Two-phase LLM review caught and fixed: non-string emote crash, mood memory leak, acore_world connection leak, missing item subclass detail, and missing emote instruction in idle conversation prompt.

### Feature 1: Emotes Between Bots
- **Conversations (JSON)**: LLM picks an emote per message from curated list of 17 (talk, bow, wave, cheer, laugh, etc.)
- **Statements (plain text)**: Python keyword-matches emote after response via `pick_emote_for_statement()` with 60% RNG gate
- C++ `GetEmoteId()` maps string to `EMOTE_ONESHOT_*` enum, `HandleEmoteCommand()` plays animation after message delivery
- Emote stored in `llm_chatter_messages.emote` VARCHAR(32) column
- Works for both party chat and General channel bots

### Feature 2: Session Mood Drift
- In-memory `_bot_mood_scores` dict: `(group_id, bot_guid)` -> `(score, timestamp)` tuple
- Events shift score: kill +1, boss +2, death -2, wipe -3, loot +1, epic loot +2, resurrect +1, quest +1, level up +2, achievement +1.5
- Slow drift toward neutral (0.5 per event)
- Score maps to label: miserable / gloomy / tired / neutral / content / cheerful / ecstatic
- Mood injected into all group prompt builders when not neutral
- Automatic stale entry eviction (2 hours TTL, triggers when dict > 50 entries)

### Feature 3: Farewell Messages
- On group join: after greeting, second LLM call generates farewell stored in `llm_group_bot_traits.farewell_msg`
- On group leave: C++ `OnRemoveMember()` queries farewell, builds `CHAT_MSG_PARTY` WorldPacket, sends to remaining members
- Bypasses `ai->SayToParty()` limitation (bot already removed from group)
- Gated behind `LLMChatter.GroupChatter.FarewellEnable` config (default: enabled)

### Feature 4: Item Link Reactions
- Detects `|Hitem:ENTRY:...|h[Item Name]|h|r` in player party messages
- Queries `acore_world.item_template` for quality, type (with weapon/armor subclass detail), level, AllowableClass
- Bot comments from class/role perspective ("Warrior CAN equip", "Priest CANNOT equip")
- Connection opened in try/finally for exception safety

### Centralized INSERT Refactor
- New `insert_chat_message()` helper replaces ~25 individual INSERT statements across 4 files
- Handles emote column, parameterized queries, commit
- 29 total call sites: chatter_group.py (21), llm_chatter_bridge.py (4), chatter_general.py (3), chatter_shared.py (1 definition)

### Review Findings Fixed
1. `validate_emote()` type check — `isinstance(emote_str, str)` guard before `.strip()` (prevents crash on non-string LLM output)
2. Mood memory leak — changed to `(score, timestamp)` tuples with 2-hour TTL eviction
3. acore_world connection leak — moved to `try/finally` with safe close
4. Item subclass detail — added `_WEAPON_SUBCLASS` (16 types) and `_ARMOR_SUBCLASS` (6 types) maps
5. Idle conversation emotes — added emote instruction + JSON field to `build_idle_conversation_prompt()`

### Files Changed

| File | Change |
|------|--------|
| `tools/chatter_constants.py` | Added EMOTE_LIST (17+none), EMOTE_LIST_STR, EMOTE_KEYWORDS (~60 mappings) |
| `tools/chatter_shared.py` | Added validate_emote, pick_emote_for_statement, detect_item_links, query_item_details, format_item_context, insert_chat_message; added _WEAPON_SUBCLASS, _ARMOR_SUBCLASS maps |
| `tools/chatter_prompts.py` | Emote field added to all 6 conversation prompt JSON schemas |
| `tools/chatter_group.py` | Mood drift system, farewell generation, item link handling, INSERT refactor (21 replacements), emote in idle prompt, EMOTE_LIST_STR import |
| `tools/chatter_general.py` | 2 INSERT replacements with emote support |
| `tools/llm_chatter_bridge.py` | 3 INSERT replacements with emote support |
| `src/LLMChatterScript.cpp` | GetEmoteId() static mapper, emote execution in DeliverPendingMessages, farewell WorldPacket in OnRemoveMember, Chat.h include |
| `src/LLMChatterConfig.h` | Added _useFarewell bool |
| `src/LLMChatterConfig.cpp` | Loads FarewellEnable config |
| `conf/mod_llm_chatter.conf.dist` | Added FarewellEnable entry |
| `data/sql/.../llm_chatter_tables.sql` | Added emote column to messages, farewell_msg to traits |

### Technical Notes
- `HandleEmoteCommand()` takes EMOTE_ONESHOT_* enums (one-shot animations, not looping state emotes)
- "dance" maps to EMOTE_ONESHOT_DANCESPECIAL (402), not EMOTE_STATE_DANCE (looping)
- Farewell uses raw WorldPacket because bot is already removed from group when OnRemoveMember fires
- `ChatHandler::BuildChatPacket()` takes WorldObject* sender — Player* implicitly converts
- Mood drift applies drift-toward-neutral BEFORE event delta (so delta is the fresh impact)
- Idle conversation emote was caught by LLM reviewer — prompt was missing emote instruction
- `query_item_details()` uses fully-qualified `acore_world.item_template` (cross-database query)

---

## 2026-02-13 (Session 35b) - Quest Lookup Fix, Greeting Names, Prompt Tuning

### Summary

Continued from Session 35. Compiled and deployed Session 35's C++ changes (greeting name personalization). Fixed mod-llm-guide quest lookup (LLM was hallucinating quest data instead of using tools). Improved general/party chat prompts with proportional response rule, name addressing, and "festival" → "event" wording fix. Verified SQL schema alignment, updated dev-server-guide, pushed mod-llm-chatter to GitHub, removed superseded SQL migrations.

### mod-llm-guide Changes (Python only, bridge restart)

1. **Strengthened tool use instruction** — System prompt now explicitly lists quests among tool-required topics. Uses forceful language: "ALWAYS use them", "NEVER answer from memory". Prevents LLM from hallucinating quest data instead of querying the database.

2. **Multi-variant quest lookup** — `_get_quest_info()` rewritten to return up to 5 matching quests instead of `LIMIT 1`. Adds `AllowableRaces` bitmask faction detection (`[Alliance only]`/`[Horde only]`/`[Both factions]` tags). Includes quest giver location via LEFT JOIN on creature table. Fixed variable shadowing bug where `result = cursor.fetchone()` in objectives loop overwrote the output string.

### mod-llm-chatter Changes

#### C++ (compiled and deployed)
1. **Greeting name personalization** — `QueueBotGreetingEvent` now includes `player_name` and `group_size` in extra_data JSON. When group has only 2 members (player + bot), 80% chance the bot addresses player by name.

#### Python (bridge restart)
1. **Proportional response rule** — Added "Keep your response proportional to what was said" to `build_player_response_prompt` (party) and `_build_general_response_prompt` (general). Prevents long replies to simple messages like "bye".

2. **Name addressing in conversations (40% RNG)** — Bots may address someone by name in party chat, general channel responses, and general channel followups. Picks randomly from player or party members/first bot.

3. **"Festival" → "event" prompt wording** — Changed `chatter_events.py`, `chatter_prompts.py`, and `llm_chatter_bridge.py` to use "event" instead of "festival" in holiday prompts. Prevents LLM from treating PvP Call to Arms events as celebrations.

### Infrastructure Changes

1. **SQL alignment** — Changed `extra_data` column in `llm_chatter_events` from `text` to `JSON` to match base schema.
2. **Dev server guide** — Updated `docs/development/dev-server-guide.md`: removed compile.sh references, added pre-flight Docker check, chmod +x after install, never-touch-other-modules warning.
3. **Removed superseded SQL migrations** — Deleted `group_chatter_migration_v8.sql`, `20260212_general_chat_history.sql`, `20260213_corpse_run_event.sql` (all superseded by base schema).
4. **mod-llm-chatter pushed to GitHub** — Commits `ee4e7a4` (11 files, 783 insertions) and `c930971` (migration cleanup).

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-guide/tools/game_tools.py` | Rewrote `_get_quest_info()`: LIMIT 5, faction tags, quest giver location, variable shadowing fix |
| `modules/mod-llm-guide/tools/llm_guide_bridge.py` | Strengthened tool use instruction in system prompt |
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | Added player_name + group_size to greeting extra_data |
| `modules/mod-llm-chatter/tools/chatter_group.py` | Proportional response rule, 40% name addressing, greeting name params |
| `modules/mod-llm-chatter/tools/chatter_general.py` | Proportional response rule, 40% name addressing in responses + followups |
| `modules/mod-llm-chatter/tools/chatter_events.py` | "festival" → "event" in holiday context strings |
| `modules/mod-llm-chatter/tools/chatter_prompts.py` | Updated holiday detection + conversation instruction wording |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | "festival" → "event" in solo event reaction prompt |
| `docs/development/dev-server-guide.md` | Removed compile.sh, added pre-flight check, chmod+x, module safety |
| `docs/mod-llm-chatter/future-plans.md` | Updated Trade Channel entry with city frequency notes |

### Technical Notes

- Wowhead has no free public API — decided to keep DB-only approach for mod-llm-guide
- `AllowableRaces=0` means neutral/both factions (not missing data)
- "Call to Arms: Warsong Gulch" is a PvP bonus weekend event that was incorrectly presented as a "festival" in prompts
- Holiday `is_holiday` detection in `chatter_prompts.py` now keys off event context string ("event has just begun"/"event is coming to an end") instead of the word "festival"
- Bridge `is_holiday` detection in `llm_chatter_bridge.py` already used `event_type.startswith('holiday')` (correct, unchanged)

---

## 2026-02-13 (Session 35) - Racial Vocabulary, City Loot Skip, Corpse Run Reactions

### Summary

Implemented three quick-win features from the future plans document: (1) Racial language vocabulary with lore-accurate phrases for all 10 races, injected 15% of the time into prompts. (2) Skip loot/trade messages in capital cities (quest messages preserved since cities have quest givers). (3) Corpse run commentary when a bot dies and releases spirit — party members react with personality-appropriate humor/sympathy. Also cleaned up future-plans.md, deleted the now-obsolete new-features-implementation-plan.md, and had changes reviewed by another LLM which caught a non-existent hook name and post-WotLK lore phrases.

### C++ Changes (compiled and deployed)

1. **Corpse run hook** — Added `OnPlayerReleasedGhost(Player* player)` to `LLMChatterPlayerScript`. Detects bot death+release, checks group has real player, applies RNG (80% default) and per-group cooldown (120s default). Inserts `bot_group_corpse_run` event with full context (bot name, class, race, level, group_id, zone_id, zone_name).

2. **Config fields** — Added `_groupCorpseRunChance` (default 80) and `_groupCorpseRunCooldown` (default 120) to `LLMChatterConfig`.

3. **Cooldown management** — Added `_groupCorpseRunCooldowns` static map, cleaned up in `CleanupGroupSession()`.

### Python Changes (bridge restart)

1. **Racial vocabulary** — Added `vocabulary` field to all 10 races in `RACE_SPEECH_PROFILES` (chatter_constants.py). Each vocabulary is a list of tuples: `(phrase, meaning)`. All phrases verified as WotLK-era lore-accurate (Thalassian, Darnassian, Orcish, Gutterspeak, etc.).

2. **Vocabulary injection** — Updated `build_race_class_context()` in chatter_shared.py to inject a random vocabulary phrase 15% of the time with soft instruction ("Use it only if it fits — never force it").

3. **City loot skip** — Added early check in `process_statement()` (llm_chatter_bridge.py) that converts `loot` and `trade` message types to `plain` when `zone_id in CAPITAL_CITY_ZONES`. Quest messages preserved since cities have quest givers.

4. **Corpse run handler** — Added `process_group_corpse_run_event()` in chatter_group.py following exact pattern of `process_group_wipe_event()`. Parses extra_data, gets bot traits, builds prompt with ghost/corpse run context, calls LLM, delivers to party chat.

5. **Corpse run prompt** — Added `build_corpse_run_reaction_prompt()` with zone-aware ghost commentary, tone/mood/twist system, RP mode support, and chat history context.

### SQL Changes

- Added `bot_group_corpse_run` to `event_type` ENUM in base schema (`llm_chatter_tables.sql`)
- Migration: `data/sql/db-characters/updates/20260213_corpse_run_event.sql`

### Config Changes

- **mod_llm_chatter.conf.dist**: Added `CorpseRunChance = 80` and `CorpseRunCooldown = 120`
- **LLMChatterConfig.h/.cpp**: 2 new config fields

### LLM Review Fixes

- **OnPlayerRepop is not a valid hook** — Discovered by LLM reviewer. Changed to `OnPlayerReleasedGhost(Player*)` which is the correct AzerothCore hook (`PlayerScript.h:232`).
- **"Shaha lor'ma" is post-WotLK** — Patch 8.2 content, not in 3.3.5a. Replaced with `Fandu-dath-belore?` ("Who goes there?") and `Tor ilisar'thera'nal!` ("Let our enemies beware!").
- **Missing canonical phrases** — Added `Doral ana'diel?` and `Al diel shala` (Blood Elf), `Pheta thones gamera` (Draenei).

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/tools/chatter_constants.py` | Vocabulary lists for all 10 races |
| `modules/mod-llm-chatter/tools/chatter_shared.py` | Vocabulary injection in build_race_class_context() |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | CAPITAL_CITY_ZONES import, loot/trade skip, corpse run dispatch |
| `modules/mod-llm-chatter/tools/chatter_group.py` | process_group_corpse_run_event(), build_corpse_run_reaction_prompt() |
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | OnPlayerReleasedGhost hook, cooldown map, cleanup |
| `modules/mod-llm-chatter/src/LLMChatterConfig.h` | _groupCorpseRunChance, _groupCorpseRunCooldown |
| `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` | Config loading for corpse run |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | CorpseRunChance, CorpseRunCooldown entries |
| `modules/mod-llm-chatter/data/sql/db-characters/base/llm_chatter_tables.sql` | bot_group_corpse_run ENUM |
| `modules/mod-llm-chatter/data/sql/db-characters/updates/20260213_corpse_run_event.sql` | Migration |
| `docs/mod-llm-chatter/future-plans.md` | Updated completed sections |
| `docs/mod-llm-chatter/new-features-implementation-plan.md` | Deleted (all implemented) |
| `docs/session35_review_instructions.md` | Created for LLM review |

### Player Death Extensions (post-/um)

After initial deployment, extended two hooks to also trigger on real player deaths (not just bot deaths):

1. **Corpse run** — `OnPlayerReleasedGhost` now fires for both bot and player deaths. When player dies, a random bot reacts with concern/encouragement. When bot dies, a different bot reacts. Added `dead_name` and `is_player_death` to extra_data. Prompt differentiates: "Your party leader {name}" vs "You just died".

2. **Death reactions** — `OnPlayerKilledByCreature` now fires for both bot and player deaths. Bots react when the player gets killed by a creature ("Your party leader just died!"). Added `is_player_death` to extra_data. Prompt uses urgency/concern for player deaths vs sympathy/humor for bot deaths. Bonus: wipe detection now works when the player is the last to die.

### Technical Notes

- `OnPlayerReleasedGhost` fires when a player (or bot) releases spirit — different from `OnPlayerRepop` which doesn't exist as an AzerothCore hook.
- Vocabulary injection uses 15% RNG (same rate as lore injection) with soft prompting to avoid forced usage.
- City loot skip only affects ambient General chat statements, not group loot reactions (which are always relevant).
- Corpse run uses 5s react_after and 120s expiration, 80% trigger chance with 120s per-group cooldown.
- LLM review process proved valuable — caught a non-existent hook name and non-canonical lore phrases before deployment.
- `GetRandomBotInGroup(group, exclude)` reused for both corpse run and death — picks a bot excluding the dead entity.

---

## 2026-02-12 (Session 34) - General Channel Player Message Reactions + Smart Bot Selection

### Summary

Implemented bot reactions to player messages in General channel. When a real player types in General, nearby bots react with statements or conversations (zone-scoped). Added smart bot selection: if a player addresses a specific bot by name, that bot responds (works in both General and party chat). Added 3-pass name matching: exact, fuzzy, LLM context analysis. Added reusable `quick_llm_analyze()` utility for fast Haiku pre-processing calls. Split reaction chance into question (100%) vs non-question (80%) based on trailing `?`.

### C++ Changes (compile pending)

1. **OnPlayerCanUseChat(Channel*) hook** — Detects player messages in General channel (channelId=1). Filters addon messages, link-only messages. Stores in `llm_general_chat_history`. Selects 1-4 bots in same zone. Inserts `player_general_msg` event.

2. **Question detection** — Messages ending with `?` use `_generalChatQuestionChance` (100%), others use `_generalChatChance` (80%).

3. **Bot message history** — `DeliverPendingMessages()` stores bot General channel messages in `llm_general_chat_history` for context.

4. **Per-zone cooldowns** — `_generalChatCooldowns` static map, configurable via `LLMChatter.GeneralChat.Cooldown`.

5. **Config fields** — 5 new: `_useGeneralChatReact`, `_generalChatChance`, `_generalChatQuestionChance`, `_generalChatCooldown`, `_generalChatConversationChance`.

### Python Changes (bridge restart)

1. **`chatter_general.py`** — NEW module: prompt builders and event handler for General channel reactions. Statement and conversation modes with staggered delays.

2. **`chatter_shared.py`** — Added `quick_llm_analyze()` reusable fast Haiku utility. Added `find_addressed_bot()` with 3-pass matching (exact name, fuzzy edit distance, LLM context analysis).

3. **`chatter_group.py`** — Updated `process_group_player_msg_event` to use `find_addressed_bot` with LLM fallback instead of random-only selection.

4. **`llm_chatter_bridge.py`** — Added import and dispatch for `player_general_msg` event type.

### SQL Changes

- New `llm_general_chat_history` table (zone_id, speaker_name, is_bot, message)
- Added `player_general_msg` to `event_type` ENUM in `llm_chatter_events`
- Migration: `data/sql/db-characters/updates/20260212_general_chat_history.sql`
- Live DB already migrated

### Config Changes

- **LLMChatterConfig.h/.cpp**: 5 new fields for General chat
- **conf.dist**: New "General Channel Reactions" section
- **Active config**: Enable=1, ReactionChance=80, QuestionChance=100, Cooldown=60, ConversationChance=30

### Bug Fixed

- `calculate_dynamic_delay(msg1)` needed `(len(msg1), config)` — fixed in chatter_general.py

### Compile State

- C++ compiled successfully but hit `AddModulesScripts()` linker error (known issue — need to delete ModulesLoader.cpp.o and rebuild)
- Build was stopped due to user memory leak — needs resume next session

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | OnPlayerCanUseChat hook, bot history in DeliverPendingMessages |
| `modules/mod-llm-chatter/src/LLMChatterConfig.h` | 5 new General chat config fields |
| `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` | Load 5 config values + startup log |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | General Chat section |
| `modules/mod-llm-chatter/tools/chatter_general.py` | NEW: General channel event handler |
| `modules/mod-llm-chatter/tools/chatter_shared.py` | quick_llm_analyze(), find_addressed_bot() |
| `modules/mod-llm-chatter/tools/chatter_group.py` | Smart bot selection in player msg handler |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | Dispatch for player_general_msg |
| `modules/mod-llm-chatter/data/sql/db-characters/base/llm_chatter_tables.sql` | New table + ENUM |
| `modules/mod-llm-chatter/data/sql/db-characters/updates/20260212_general_chat_history.sql` | Migration |
| `env/dist/etc/modules/mod_llm_chatter.conf` | Active config with General chat settings |
| `docs/session34_general_chat_progress.md` | Session progress file for context preservation |

### Technical Notes

- General channel uses `OnPlayerCanUseChat(Player*, uint32, uint32, std::string&, Channel*)` overload — the Channel* parameter distinguishes it from party/say/whisper hooks.
- 3-pass name matching: (1) exact case-insensitive match in bot list, (2) fuzzy edit distance for misspellings, (3) LLM context analysis via `quick_llm_analyze()` using Haiku for ambiguous cases.
- `quick_llm_analyze()` is a reusable utility — takes a prompt and returns the LLM response string. Used for bot name matching and potentially other pre-processing tasks.
- Question detection uses simple trailing `?` heuristic — cheap and effective for chat messages.
- Per-zone cooldowns prevent spam: one General chat reaction event per zone per cooldown period.
- `AddModulesScripts()` linker error is the known issue from CLAUDE.md — delete `ModulesLoader.cpp.o` and rebuild modules.

---

## 2026-02-12 (Session 34b) - General Channel Reactions Compilation, Duplicate History Fix, Smart Bot Selection Refinement

### Summary

Completed Session 34 General Channel Reactions feature compilation and deployment. Fixed critical duplicate bot message storage bug (Python + C++ both inserting). Fixed bot candidate limiting issue that prevented conversation mode from working (urand(1,4) gate removed). Added configurable provider/model selection for quick_llm_analyze() Haiku speedup calls. Tuned cooldown from 60s to 15s for conversational flow. Fixed worldserver binary permission issue after make install. Updated README with General Channel Reactions section. Cleaned duplicate history rows from database.

### C++ Changes (compiled and deployed)

1. **Removed duplicate history INSERT** — `DeliverPendingMessages()` was storing bot messages in `llm_general_chat_history`. Python's `chatter_general.py` already stores them immediately after LLM response. Removed C++ side INSERT to prevent duplicates and because Python needs the message in history immediately for conversation mode followups.

2. **Fixed bot candidate limiting** — `urand(1, 4)` in `OnPlayerCanUseChat()` was randomly gating bot candidate count to 1-4 even when more bots existed in zone. This broke conversation mode which needs >= 2 bots to decide between statement and conversation. Changed to send ALL discovered bots (up to 8 cap in original code) so Python always has full pool.

3. **Compilation workflow** — Hit `AddModulesScripts()` linker error during `make worldserver` step. Fixed by deleting `var/build/obj/modules/CMakeFiles/modules.dir/gen_scriptloader/static/ModulesLoader.cpp.o` and rebuilding modules (known issue per CLAUDE.md).

4. **Binary permission fix** — After `make install`, the worldserver binary lost execute permission (exit code 126 "Permission denied"). Added explicit `chmod +x /azerothcore/var/build/obj/bin/worldserver` after install step.

### Python Changes (bridge restart)

1. **Configurable quick_llm_analyze() provider** — Added `LLMChatter.QuickAnalyze.Provider` and `LLMChatter.QuickAnalyze.Model` config keys in `chatter_shared.py`. If empty/not set, defaults to fastest model on main provider (Haiku for Anthropic, gpt-4o-mini for OpenAI). If set to different provider name, lazily creates and caches separate LLM client. Allows fast pre-processing on cheaper model without main conversation impact.

2. **Quick Analyze config display** — Updated `llm_chatter_bridge.py` startup log to display Quick Analyze provider and model config.

### Config Changes

- **mod_llm_chatter.conf.dist**: Added `[LLMChatter.QuickAnalyze]` section with `Provider` and `Model` keys (both optional, empty by default)
- **Active config** (`env/dist/etc/modules/mod_llm_chatter.conf`): Added Quick Analyze section, changed Cooldown from 60→15 for natural conversation flow (matches party chat PlayerMsgCooldown)

### Database Changes

- **Cleaned duplicate rows** — Deleted duplicate entries in `llm_general_chat_history` caused by pre-fix double storage (Python + C++)

### Deployment

- Compiled Session 34 C++ changes (OnPlayerCanUseChat hook, bot message history in DeliverPendingMessages)
- Restarted worldserver successfully
- Restarted ac-llm-chatter-bridge with Quick Analyze config
- Feature fully deployed and tested

### Bugs Fixed

- **Duplicate bot messages** — Python + C++ were both inserting into `llm_general_chat_history`. Python insertion happens immediately after LLM responds (needed for conversation mode). C++ insertion happens in DeliverPendingMessages. Kept Python-only, removed C++.
- **Bot candidate pool gating** — `urand(1, 4)` limited bots to random 1-4 count even when 5+ existed. Broke conversation mode RNG. Removed random limiting, send all bots.
- **Worldserver permission denied** — `make install` didn't preserve execute bit on new binary. Added chmod +x.

### Files Modified

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | Removed duplicate history INSERT, changed urand(1,4) to send all zone bots |
| `modules/mod-llm-chatter/tools/chatter_shared.py` | Added `_get_quick_analyze_client()`, updated `quick_llm_analyze()` config reading |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | Added Quick Analyze config display at startup |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | Added QuickAnalyze section with Provider/Model keys |
| `env/dist/etc/modules/mod_llm_chatter.conf` | Added QuickAnalyze keys, changed Cooldown 60→15 |
| `modules/mod-llm-chatter/README.md` | Added General Channel Reactions and Smart Bot Selection sections, config table, file listing |
| `llm_general_chat_history` (DB) | Cleaned duplicate rows |

### Technical Notes

- **Cooldown design**: Cooldown only triggers after successful reaction (bot responded), not on failed RNG. This prevents "silence begetting silence" — if no bot reacted, next message can still try.
- **Quick Analyze caching**: `_quick_analyze_client` stored at module level (global) for reuse across calls within same Python process.
- **Provider fallback**: If QuickAnalyze.Provider is empty/not set, code uses the main LLMConfig's provider. If set to "openai" or "anthropic", creates dedicated client for that provider.
- **Duplicate message fix**: C++ defers to Python for history storage. Python stores immediately after LLM response, which is necessary for conversation mode's dynamic followup selection.

---

## 2026-02-12 (Session 33b) - Holiday Zone Expansion, Item Links in Loot, Event Expiration Fix, Config Display

### Summary

Extended holiday events to trigger in all zones with real players (not just capital cities). Fixed critical event expiration bug where holiday events expired before their reaction delay elapsed. Added clickable item links to loot reactions. Added playerbot command filtering for "do attack my target". Added comprehensive config display at bridge startup. Tuned group idle chatter frequency. Updated README with RP/immersion focus and real session dialog examples.

### C++ Changes (compiled)

1. **Holiday zone expansion**: Renamed `QueueHolidayForCities()` to `QueueHolidayForZones()`, removed `IsCapitalCity()` gate. Cities use `HolidayCityChance` (10%), open-world zones use new `HolidayZoneChance` (5% default). Added `_holidayZoneChance` config field.

2. **Event expiration fix**: `expires_at` now set to `reactionDelay + eventExpirationSeconds` instead of just `eventExpirationSeconds`. Holiday events (300-900s delay) were expiring before they could fire (600s expiration window). Affects all event types but only holidays were broken.

### Python Changes (bridge restart)

1. **Item links in loot reactions**: After LLM generates loot response, item name is replaced with clickable WoW item link via `format_item_link()`. Uses `re.sub` with `re.IGNORECASE` for case-tolerant matching.

2. **Playerbot command filter**: Added "do attack my target" as exact multi-word match to `PLAYERBOT_COMMANDS` set.

3. **Startup config display**: Bridge now prints all config values on startup in organized sections: chatter settings, transport, holiday (new), and group chatter (new) with all chances, cooldowns, and intervals.

4. **Idle chatter tuning**: Reduced IdleChance from 10% to 5%, IdleCheckInterval from 60s to 30s (~1/4 frequency).

5. **Conversation chance**: Bumped ConversationChance from 40% to 50% (equal split with statements).

### Config Changes

- **LLMChatterConfig.h**: Added `_holidayZoneChance` field
- **LLMChatterConfig.cpp**: Added `LLMChatter.HolidayZoneChance` loading (default 5)
- **conf.dist**: Added `HolidayZoneChance` entry with documentation
- **Active config**: `HolidayZoneChance=10`, `HolidayCityChance=10`, `IdleChance=5`, `IdleCheckInterval=30`, `ConversationChance=50`

### Documentation

- **README.md**: Updated intro with RP/immersion focus, replaced example dialogs with actual session conversations (Dralidan, Nilaste, Seladan, Uldamyr, Orencer)
- **future-plans.md**: Added "Enemy Territory PvP Alert" (yell in hostile zones) and "Trade Channel in Cities" items

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | QueueHolidayForZones rename, expiration fix |
| `modules/mod-llm-chatter/src/LLMChatterConfig.h` | _holidayZoneChance field |
| `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` | HolidayZoneChance loading |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | HolidayZoneChance entry |
| `modules/mod-llm-chatter/tools/chatter_group.py` | Item links in loot, "do attack my target" filter |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | Startup config display sections |
| `modules/mod-llm-chatter/README.md` | RP/immersion intro, real dialog examples |
| `docs/mod-llm-chatter/future-plans.md` | PvP alert + trade channel items |
| `env/dist/etc/modules/mod_llm_chatter.conf` | HolidayZoneChance, IdleChance, IdleCheckInterval, ConversationChance |

### Technical Notes

- Event expiration bug was causing ALL holiday events to silently expire — `react_after` exceeded `expires_at` because reaction delay (300-900s) could exceed the flat expiration window (600s).
- The `QueueHolidayForZones` change is backward compatible — cities still get their own chance rate, open-world just gets added as a new path.
- Playerbot "do" commands are tricky: "do attack my target" is a bot command but reads like natural language. Filtering as exact match avoids false positives on genuine messages starting with "do".
- `libmodules.a` corruption occurred during compilation — fixed by deleting and rebuilding (known issue from Session 32).

---

## 2026-02-11 (Session 33) - Holiday City Targeting Fix, Capital City Creature Bug, Competitor Analysis

### Summary

Fixed two bugs: holiday event messages appearing in wrong zones (random bot in Bloodmyst Isle instead of player's city), and wrong creatures listed in capital city prompts (Stitches from Duskwood showing in Darnassus). Refactored holiday event queuing to always target capital cities where real players are. Added `CAPITAL_CITY_ZONES` set to skip mob/loot queries in cities. Updated future-plans.md with competitive features after analyzing competitor module. Added Docker health pre-flight check to compilation protocol. Moved 8 hardcoded C++ values to config. Made holiday prompts explicitly mention the festival.

### C++ Changes (compiled)

1. **Holiday city targeting refactor**: Extracted `IsCapitalCity()`, `IsInOverworld()`, `GetZonesWithRealPlayers()`, and `QueueHolidayForCities()` from WorldScript class members into static free functions. All 3 holiday paths (OnStart, startup detection, periodic CheckActiveHolidays) now use `QueueHolidayForCities()` which targets capital cities where real players are. OnStart/OnStop call the free function directly. Eliminates zone_id=0 global events that picked random bots anywhere.

2. **Holiday RNG bypass**: Added `alwaysFire` flag for `holiday_start`, `holiday_end`, and `day_night_transition` events in `QueueEvent()` — these bypass the 15% `_eventReactionChance` RNG roll since they're rare one-time events.

3. **Recurring holiday chatter in cities**: New `CheckActiveHolidays()` method runs during periodic environment check. Scans active game events with `HolidayId != HOLIDAY_NONE`, queues per capital city with per-city cooldowns (key: `holiday:{eventId}:zone:{zoneId}`).

4. **Environment check configurable**: Moved hardcoded 60000ms environment check interval to `LLMChatter.EnvironmentCheckSeconds` config.

5. **8 hardcoded values moved to config**: `WeatherCooldownSeconds` (1800), `DayNightCooldownSeconds` (7200), `HolidayCooldownSeconds` (1800), `HolidayCityChance` (10), `TransportCheckSeconds` (5), `GroupQuestObjectiveChance` (50), `GroupSpellCastChance` (15), `EnvironmentCheckSeconds` (60).

### Python Changes (bridge restart)

1. **Capital city creature/loot fix**: Added `CAPITAL_CITY_ZONES` set (11 cities) to `chatter_constants.py`. Both `query_zone_mobs()` and `query_zone_loot()` return empty for capital cities — no hostile creatures or loot drops in city prompts.

2. **Holiday event zone fix**: Added `OR e.zone_id = 0` to event query in bridge so global events (zone_id=0) are picked up. Previously only `zone_id IS NULL` was handled.

3. **Holiday prompt explicit mentions**: Updated both statement prompt (bridge.py) and conversation prompt (chatter_prompts.py) to explicitly require mentioning the holiday by name. Was "you don't HAVE to mention it" — now "React to this festival! Mention the holiday by name."

### Config Changes

- **LLMChatterConfig.h**: Added 6 new fields (`_transportCheckSeconds`, `_weatherCooldownSeconds`, `_dayNightCooldownSeconds`, `_holidayCooldownSeconds`, `_holidayCityChance`, `_environmentCheckSeconds`)
- **LLMChatterConfig.cpp**: Added loading for all 8 new config values
- **conf.dist**: Added 8 new config entries with documentation
- **Active config**: Added all 8 entries, HolidayCooldownSeconds=300 (5min for testing)

### Documentation

- **future-plans.md**: Added items 12-20 (PvP/Duel reactions, Corpse Run Commentary, Item Link Reactions, Group Role Awareness, Farewell Messages, Proximity-Based General Chatter, Session Mood Drift, Racial Language Flavor, Contextual Surroundings Awareness). Updated delivery phases from 3 to 4.
- **CLAUDE.md**: Added Docker health pre-flight check section before compilation steps
- **Farewell message investigation**: Traced AzerothCore source — `OnGroupRemoveMember` fires AFTER `m_memberSlots.erase()` at `Group.cpp:645`. Pre-generate-on-join approach documented in future-plans.md.

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | Holiday city targeting refactor, free functions, RNG bypass, CheckActiveHolidays, config values |
| `modules/mod-llm-chatter/src/LLMChatterConfig.h` | 6 new config fields |
| `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` | Load 8 new config values |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | 8 new config entries |
| `env/dist/etc/modules/mod_llm_chatter.conf` | 8 new config entries (active) |
| `modules/mod-llm-chatter/tools/chatter_constants.py` | CAPITAL_CITY_ZONES set |
| `modules/mod-llm-chatter/tools/chatter_shared.py` | Import CAPITAL_CITY_ZONES, skip mobs/loot in cities |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | zone_id=0 fix, holiday prompt explicit mentions |
| `modules/mod-llm-chatter/tools/chatter_prompts.py` | Holiday conversation prompt explicit mentions |
| `docs/mod-llm-chatter/future-plans.md` | Items 12-20, delivery phases 3→4 |
| `CLAUDE.md` | Docker health pre-flight check |

### Technical Notes

- `QueueHolidayForCities()` is a static free function callable from both `GameEventScript` (OnStart/OnStop) and `WorldScript` (CheckActiveHolidays). Previously holiday queuing was split across 3 paths with inconsistent zone targeting.
- `zone_id = 0` (global events) vs `zone_id IS NULL` in MySQL — Python event query now handles both with `OR e.zone_id = 0`.
- Holiday reaction delay is 300-900 seconds (5-15 min) — designed for natural feel. Can be tuned later.
- Capital cities: 1519 (Stormwind), 1537 (Ironforge), 1657 (Darnassus), 3557 (Exodar), 1637 (Orgrimmar), 1638 (Thunder Bluff), 1497 (Undercity), 3487 (Silvermoon), 3524/3703 (Shattrath), 4395 (Dalaran).
- `query_zone_mobs()` level-based fallback (no zone filter) was returning random world mobs for any zone not in `ZONE_COORDINATES`. Capital city early-return prevents this.

---

## 2026-02-09 (Session 31) - Idle Banter Tuning, RP Enrichment, SQL Escaping & Event Identity Fix

### Summary

Major tuning session for group party chat. Increased idle banter frequency, expanded topics, softened "gamer slang" in normal mode, enriched RACE_SPEECH_PROFILES with worldview and lore context for RP mode, updated CLASS_SPEECH_MODIFIERS with richer descriptions, switched default ChatterMode to roleplay. Fixed critical SQL escaping bug and ENUM mismatch preventing level-up/quest/achievement events. Fixed event identity bug where LLM didn't know who completed a quest/leveled/earned achievement. Added config abstraction for group chatter tuning values. Fixed time-of-day always passed to LLM. Increased WSL2 memory from 13 GB to 24 GB for faster compilation.

### Python Changes (bridge restart)

1. **Idle banter tuning**: Expanded GROUP_IDLE_TOPICS from 20 to 41 immersion-safe topics (food/drink, travel, professions, gear, level progress, AFK humor). Changed RNG from 3%→15%, idle check interval from 120s→60s, conversation bias from 50%→70%. Net effect: fires ~once per 7 minutes instead of ~67 minutes.

2. **Idle history cap**: Limited idle chat context from 15 to 5 messages to prevent echo chamber effect where bots repeat each other's themes.

3. **Asterisk emote stripping**: Added `re.sub(r'\*([^*]+)\*', r'\1', result)` to `cleanup_message()` in chatter_shared.py. LLM was generating `*poof*`, `*toss*`, `*chomp chomp*` despite prompt instructions.

4. **Avoid rules in idle prompts**: Both `build_idle_chatter_prompt()` and `build_idle_conversation_prompt()` now include: "NEVER claim to have killed a creature, looted an item, completed a quest, or made a trade."

5. **Softened normal mode style**: Changed all 12+ "Sound like a real MMO player, use abbreviations" instructions to "casual but natural, no excessive slang". Toned down personality traits: blunt→thoughtful, reckless→easygoing, no-nonsense→warmhearted, hyper→relaxed, intense→steady. Softened TONES: hyped up→pleasantly surprised, distracted and rambling→thoughtful and quiet, etc.

6. **RACE_SPEECH_PROFILES enriched**: Added `worldview` field to all 10 races capturing faction identity nuances (e.g., Tauren = peaceful Horde through gratitude, Blood Elf = pragmatic Horde, not evil). Added `lore` arrays with race-specific lore facts, gated at 15% RNG and RP-mode only. Updated `build_race_class_context()` to inject both.

7. **CLASS_SPEECH_MODIFIERS expanded**: All 10 classes updated from short strings to detailed multi-line descriptions.

8. **Default ChatterMode changed**: `mod_llm_chatter.conf.dist` default changed from `normal` to `roleplay`.

9. **Time-of-day always passed**: Changed `get_environmental_context()` to always include time-of-day in prompts (was 60% RNG). Weather remains 50% RNG. Fixes bots saying "tonight" during daytime.

10. **Config abstraction for idle chatter**: Five hardcoded values moved to `mod_llm_chatter.conf.dist`: `IdleChance` (15), `IdleCheckInterval` (60), `IdleCooldown` (30), `ConversationBias` (70), `IdleHistoryLimit` (5).

11. **Event identity fix (Python)**: Quest complete, level-up, and achievement handlers now read `completer_name`/`leveler_name`/`achiever_name` from extra_data, with fallback to `bot_name` for backward compatibility.

### C++ Changes (compiling)

1. **Debug logging for event hooks**: Added LOG_INFO at every early-return point in `OnPlayerLevelChanged`, `OnPlayerCompleteQuest`, and `OnPlayerAchievementComplete` hooks.

2. **SQL escaping fix**: Added `EscapeString()` calls to all three event hooks' extra_data JSON and SQL INSERT parameters. Quest names with apostrophes (e.g., "Tharnariun's Hope") were causing SQL syntax errors, silently preventing events from being stored.

3. **Event identity fix (C++)**: All three hooks now store the actual completer/leveler/achiever name in extra_data as `completer_name`/`leveler_name`/`achiever_name`, separate from `bot_name` (the reactor). Previously only `bot_name` was stored, so the LLM didn't know who actually completed the quest.

### Other Fixes

- **docker-compose.override.yml**: Fixed guide bridge script reference `llm_bridge.py` → `llm_guide_bridge.py` (file was renamed in Session 7 but docker CMD wasn't updated).

### Database Fix

- **ENUM mismatch**: C++ hooks insert `bot_group_quest_complete`, `bot_group_levelup`, `bot_group_achievement` but the live DB ENUM only had the older `bot_quest_complete`, `bot_level_up`, `bot_achievement` values. MySQL silently rejected the INSERTs.
- **Migration v8**: Added the three missing ENUM values to `llm_chatter_events.event_type`.
- The base schema (`llm_chatter_tables.sql`) already had the correct values — only the live database was out of sync from an older migration.
- This was the *actual* root cause of quest/level/achievement events never appearing — the SQL escaping fix from earlier was also needed but the ENUM rejection happened first.
- **Confirmed working**: Quest complete events verified in DB (status=completed) after ENUM fix.

### Documentation

- **QA Testing Guide**: Created `docs/mod-llm-chatter/qa-testing-guide.md` — exhaustive checklist (100+ items) covering all testable features: ambient chatter, group chatter stages 1-3, event system, environmental context, output quality, rate limiting, config overrides, edge cases. Checkbox-based for systematic verification.

### Compilation & Deployment

- **Full compilation completed** (including accidental playerbots rebuild) with -j12 and 23GB RAM
- `make install` required killing worldserver first (binary locked by running process)
- Server restarted, chatter bridge restarted — all Session 31 changes deployed

### Infrastructure

- **WSL2 memory increase**: Created `C:\Users\Calwen\.wslconfig` with `memory=24GB`, `swap=8GB`. Container RAM went from 13 GB to 23 GB. Eliminates swap thrashing during `-j12` compilation.
- **CLAUDE.md updated**: Added prominent warning about NEVER touching files in unrelated modules (especially playerbots). Added `AddModulesScripts()` linker fix (touch only `ModulesLoader.cpp.o`).

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/tools/chatter_group.py` | Topics, frequency, bias, style, traits, avoid rules, config abstraction, event identity fix |
| `modules/mod-llm-chatter/tools/chatter_shared.py` | Asterisk stripping, worldview+lore in build_race_class_context() |
| `modules/mod-llm-chatter/tools/chatter_constants.py` | RACE_SPEECH_PROFILES (worldview, lore), CLASS_SPEECH_MODIFIERS, tones |
| `modules/mod-llm-chatter/tools/chatter_prompts.py` | Softened abbreviation encouragement, time always included |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | idle_check_interval from config |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | ChatterMode default, 5 new GroupChatter settings |
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | Debug logging, SQL escaping, event identity (completer/leveler/achiever name) |
| `modules/mod-llm-chatter/sql/group_chatter_migration_v8.sql` | Add 3 missing ENUM values |
| `docker-compose.override.yml` | Guide bridge script path fix |
| `CLAUDE.md` | Critical warning about module touch scope |
| `C:\Users\Calwen\.wslconfig` | WSL2 memory 24GB, swap 8GB |
| `docs/mod-llm-chatter/qa-testing-guide.md` | New: exhaustive QA checklist (100+ items) |

### Technical Notes

- `CharacterDatabase.Execute()` uses `fmt::format`, NOT parameterized queries — must `EscapeString()` all user-derived strings
- `JsonEscape()` handles JSON escaping (quotes/newlines), `EscapeString()` handles SQL escaping (apostrophes/backslashes) — both needed
- Worldview/lore callers are already inside `if is_rp:` blocks — only inject in roleplay mode
- Lore context gated at 15% RNG to avoid token waste
- **ENUM mismatch lesson**: Always verify live DB schema matches base schema after migrations — base SQL can be ahead of the live DB if migrations were incomplete
- **Event identity**: `extra_data` JSON now has separate fields for the actor (completer/leveler/achiever) and the reactor (bot_name). Python reads actor field first, falls back to bot_name.
- **Compilation pitfall**: NEVER `find /azerothcore/modules` — always scope to specific module. Touching playerbots triggers 1-2 hour rebuild.
- WSL2 default memory is 50% of host RAM. 13 GB was causing swap thrashing with `-j12`. 24 GB resolves it.

---

## 2026-02-10 (Session 32b) - New Feature Planning & Documentation Cleanup

### Summary

Planning session for 4 new group chatter features. Created detailed implementation plan for resurrection thanks, zone transition comments, dungeon entry reactions, and group wipe reactions. Updated future-plans.md to reflect current state (many planned features were already implemented). No code changes this session.

### Documentation

- **Implementation plan**: Created `docs/mod-llm-chatter/new-features-implementation-plan.md` with full C++/Python/SQL/config design for all 4 features
- **Future plans**: Updated `docs/mod-llm-chatter/future-plans.md` — moved all implemented features to Completed section, trimmed Planned section to remaining ideas + 4 new features

### Hooks Identified

| Feature | Hook | Notes |
|---------|------|-------|
| Resurrection thanks | `OnPlayerResurrect(Player*, float, bool)` | PlayerScript, fires after rez complete |
| Zone transition | `OnPlayerUpdateZone(Player*, uint32, uint32)` | PlayerScript, fires on zone change |
| Dungeon entry | `OnPlayerMapChanged(Player*)` | PlayerScript, check `GetMap()->IsDungeon()` |
| Group wipe | Extend `OnPlayerKilledByCreature` | Check all group members `!IsAlive()` |

### Files Changed

| File | Change |
|------|--------|
| `docs/mod-llm-chatter/new-features-implementation-plan.md` | Created - full implementation plan for 4 features |
| `docs/mod-llm-chatter/future-plans.md` | Rewritten - moved implemented features to Completed |

---

## 2026-02-10 (Session 32) - Spell Cast Reactions, Buff Detection, Quest Objectives, Account Bot Support & Config Exposure

### Summary

Added spell cast reactions (buff category), quest objectives completion hook, caster-perspective prompt redesign, exposed all hardcoded RNG values to config, and fixed account character bot support. Investigated playerbots module to understand random bots vs account character bots — root cause was `DeliverPendingMessages()` only searching `RandomPlayerbotMgr` (misses account bots). Fixed with `ObjectAccessor::FindPlayer()`. Also fixed Docker Desktop crash from console spam, DB ENUM mismatches, removed example responses from prompts to reduce repetition, and tuned general/idle chatter frequencies.

### C++ Changes (compiling)

1. **Buff spell category**: Extended `OnPlayerSpellCast` to detect buff spells via `HasAura()` for `MOD_STAT`, `MOD_TOTAL_STAT_PERCENTAGE`, `MOD_RESISTANCE`, `MOD_ATTACK_POWER`, `MOD_POWER_REGEN`, `MOD_INCREASE_SPEED`. Self-buffs filtered (target must be different group member). Category = "buff".

2. **Caster-as-reactor pattern**: When a bot casts a spell, the caster bot is now the reactor (speaks about the spell they cast). Previously a random different bot would react. When a real player casts, a random bot still reacts as observer.

3. **Quest objectives completion hook**: New `OnPlayerBeforeQuestComplete` handler — fires when quest objectives are done (before turn-in). 50% trigger chance, 30s cooldown per group, event type `bot_group_quest_objectives`. Always returns true (non-blocking).

4. **Config-driven RNG values**: 9 new config variables loaded in `LLMChatterConfig.cpp/.h`: `GroupKillChanceNormal`, `GroupDeathChance`, `GroupLootChanceGreen`, `GroupLootChanceBlue`, `GroupKillCooldown`, `GroupDeathCooldown`, `GroupLootCooldown`, `PlayerMsgCooldown`, `RaceLoreChance`.

5. **Account bot support**: `DeliverPendingMessages()` was using `sRandomPlayerbotMgr.GetAllBots()` which only finds random bots. Account character bots (player's own alt characters used as bots) were never found, so messages were never delivered. Fixed by replacing with `ObjectAccessor::FindPlayer()` which finds any player in the world.

6. **Removed noisy logs**: Commented out frequently-firing transport, weather, and time transition log lines.

### Python Changes (bridge restart)

1. **Spell cast prompt redesign**: `build_spell_cast_reaction_prompt()` now checks `is_caster = (bot['name'] == caster_name)`. Caster gets first-person prompt ("You just cast {spell_name} on {target_name}"), observer gets third-person prompt. Explicit instruction to mention target by name for creative output.

2. **Quest objectives handler**: New `build_quest_objectives_reaction_prompt()` and `process_group_quest_objectives_event()` — frames as group effort, casual satisfaction tone ("Great, let's hand in the quest now").

3. **Race lore chance from config**: `_race_lore_chance` module variable in `chatter_shared.py` with `set_race_lore_chance()` setter, initialized from config.

4. **strip_speaker_prefix()**: New utility function in `chatter_shared.py` to fix double bot name prefix in messages.

5. **Removed example responses**: Stripped example phrases from spell cast prompts (both caster and observer paths) to reduce repetitive LLM output patterns.

### Config Changes

- **conf.dist**: Added 9 Group Chatter RNG settings + RP Enrichment section with `RaceLoreChance`. Improved comments on 10 existing settings for clarity.
- **Active config**: Updated with all new entries + `IdleChance = 10`.
- **TriggerChance**: Reduced from 30% to 20% (general chatter was too frequent).
- **GroupChatter.IdleChance**: Added to active config, set to 10% (was 15% default).
- **Console.Enable = 0**: Fixed Docker Desktop crash caused by AC> prompt spam when console enabled in backgrounded container.
- **Log.Async.Enable = 1**: Async logging to avoid world thread blocking.
- **Logger.playerbots = 3**: Reduced playerbots log verbosity.

### Database Fixes

- **`bot_group_spell_cast` ENUM missing from live DB**: C++ was inserting events but MySQL silently dropped them. Fixed via ALTER TABLE + migration v8 update.
- **`bot_group_quest_objectives` ENUM**: Added to live DB, migration v8, and base schema before deploying.

### QA Testing Guide Updates

- Updated 6 checkboxes: race lore facts (3.2), all 4 achievement items (9.3), asterisk emotes stripped (11.1).

### Compilation & Deployment

- Compiled twice: once for quest objectives + buff detection, once for caster-perspective redesign.
- Linker hiccup: corrupted `libmodules.a` — build agent auto-fixed by removing and rebuilding.
- Chatter bridge restarted after each Python change round.

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | Buff detection, caster-as-reactor, quest objectives hook, config-driven RNG, noisy log removal |
| `modules/mod-llm-chatter/src/LLMChatterConfig.h` | 9 new member variables for RNG config |
| `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` | Config loading for 9 new variables |
| `modules/mod-llm-chatter/tools/chatter_group.py` | Quest objectives handler/prompt, spell cast caster-perspective redesign |
| `modules/mod-llm-chatter/tools/chatter_shared.py` | strip_speaker_prefix(), race lore chance variable |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | Imports, event routing for quest_objectives, race lore chance init |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | 9 new RNG entries, RP section, improved comments |
| `env/dist/etc/modules/mod_llm_chatter.conf` | New config entries |
| `modules/mod-llm-chatter/sql/group_chatter_migration_v8.sql` | Added spell_cast + quest_objectives ENUM values |
| `modules/mod-llm-chatter/data/sql/db-characters/base/llm_chatter_tables.sql` | Added quest_objectives ENUM value |
| `env/dist/etc/worldserver.conf` | Console.Enable=0, Log.Async.Enable=1, Logger.playerbots=3 |
| `docs/mod-llm-chatter/qa-testing-guide.md` | Updated 6 checkboxes |

### Technical Notes

- **Caster-as-reactor**: C++ sets `reactor = player` when `IsPlayerBot(player)` is true (bot is caster). Python detects `is_caster` via name comparison to choose first-person vs observer prompt.
- **Buff detection auras**: `SPELL_AURA_MOD_STAT` covers Mark of the Wild, `MOD_TOTAL_STAT_PERCENTAGE` covers Kings, `MOD_RESISTANCE` covers resistances, etc.
- **Quest objectives vs completion**: `OnPlayerBeforeQuestComplete` fires when objectives done (before NPC turn-in). `OnPlayerCompleteQuest` fires at actual turn-in. Both are now hooked.
- **ENUM mismatch lesson reinforced**: Third time hitting this pattern (quest/level/achievement, spell_cast, quest_objectives). Always verify live DB ENUM matches C++ event_type strings.
- **Docker Console.Enable**: Must be 0 in containers without TTY — otherwise AC> prompt spam causes Docker Desktop to become unresponsive.

---

## 2026-02-08 (Session 30) - Stage 2 Ambient Group Conversations + Bug Fixes

### Summary

Implemented Stage 2 ambient group conversations: bots in a party now have natural 2-bot idle conversations about environment, lore, class/race, and general banter. Also added cooldown bypasses for boss/rare kills and epic+ loot, plus C++ fixes for kill handler (real player kills) and loot handler (group roll rewards).

### C++ Changes (pending compile)

1. **Kill handler — real player kills**: `OnPlayerCreatureKill` no longer requires `IsPlayerBot(killer)`. If the real player gets the killing blow, a random bot from the group reacts. Uses new `GetRandomBotInGroup()` helper.

2. **Loot handler — group roll rewards**: Extracted loot logic into shared `HandleGroupLootEvent()`. Both `OnPlayerLootItem` and new `OnPlayerGroupRollRewardItem` delegate to it. Rolled items (need/greed) now trigger loot reactions.

3. **Cooldown bypasses**: Boss/rare kills bypass the per-group kill cooldown entirely (normal mobs still have 120s cooldown). Epic+ loot (quality >= 4) bypasses the per-group loot cooldown (green/blue still have 60s cooldown).

### Python Changes (restart bridge)

1. **Enhanced idle topics**: Replaced 14 generic `IDLE_TOPICS` with 20 richer `GROUP_IDLE_TOPICS` focused on environment/zone, weather/time, class/race, lore/world, and general party banter. Excluded: items, quests, rewards, spells, trade.

2. **2-bot idle conversations**: New `build_idle_conversation_prompt()` generates a short 2-4 message exchange between two bots. Uses zone flavor, time of day, mood sequences, tone/twist system, and personality traits.

3. **Enhanced idle chatter**: `check_idle_group_chatter()` now splits 50/50 between single idle statements (original behavior) and 2-bot conversations (new). Conversations use `parse_conversation_response()` for JSON parsing and `calculate_dynamic_delay()` for staggered delivery timing.

4. **New imports**: `get_zone_flavor`, `parse_conversation_response`, `calculate_dynamic_delay`, `get_time_of_day_context`, `generate_conversation_mood_sequence`

### Files Changed

| File | Change |
|------|--------|
| `LLMChatterScript.cpp` | Kill fix, loot fix, cooldown bypasses |
| `chatter_group.py` | Enhanced topics, conversation prompt, 2-bot idle chatter |

---

## 2026-02-08 (Session 26) - Group Chatter Bug Fixes & Crash Investigation

### Summary

Fixed multiple bugs in the group chatter system and investigated a recurring segfault crash. Key fixes: `CHAT_MSG_PARTY_LEADER` type filtering (player chat was silently discarded), internal message tab character bypass, `GetCreatureTemplate()` null dereferences, and MySQL ENUM mismatch. The loot handler (`OnPlayerLootItem`) was confirmed as the crash source — theory is that massive floods of loot events from dozens of bots overwhelm the system.

### Bugs Fixed

1. **CHAT_MSG_PARTY_LEADER (type=51) not accepted** — Real player party chat was filtered because the handler only checked `CHAT_MSG_PARTY` (type=1). Party leaders send type=51. Fixed by accepting both types. Confirmed working: player messages now reach handler, get stored in chat history, and trigger bot responses.

2. **Tab character bypass in internal message filter** — Playerbot internal messages like `LOOT_OPENED\t` passed through the filter because it only checked `c != ' '`. Added `\t`, `\n`, `\r` to the filter.

3. **GetCreatureTemplate() null dereference** — Both `OnPlayerCreatureKill` and `OnPlayerEnterCombat` called `creature->GetCreatureTemplate()->rank` without null-checking the template pointer. Fixed with local `tmpl` variable and null guard.

4. **MySQL ENUM missing 'cancelled'** — C++ startup code sets `status='cancelled'` on stale queue entries, but the ENUM only had `pending/processing/completed/failed`. Fixed via SQL migration v7.

5. **Message whitespace trimming** — Added trimming of leading/trailing whitespace before processing chat messages.

### Crash Investigation

- **OnPlayerLootItem confirmed as crash source**: Disabling the handler (early return) eliminates all crashes. Re-enabling causes segfault 139.
- **Crashes even when player is solo (not in group)** — handler exits at `GetGroup() == nullptr` check, yet crash still occurs.
- **Theory**: Massive flood of loot events from all bots (hundreds per second) overwhelms the system, causing deadlocks (`[1213] Deadlock` seen in Errors.log) or memory issues.
- **Logging challenge**: `LOG_INFO` is buffered and lost on crash. `fprintf(stderr)` goes to worldserver.log which gets overwritten on restart. Solution: write to `/tmp/loot_trace.log` with open/flush/close per entry.
- **Diagnostic build prepared** (not yet compiled): numbered stderr breadcrumbs at every line of the loot handler + persistent file logging.
- **Fix plan**: Add debounce/rate limiter at the very top of the handler before any work.

### Other Findings

- **OnPlayerBeforeSendChatMessage hook IS firing** — investigation confirmed the hook chain is solid (ChatHandler.cpp → ScriptMgr → PlayerScript override). The earlier "not working" was due to the type=51 filtering issue.
- **PlayerScript constructor with empty enabledHooks enables ALL hooks** — no need to explicitly list hooks.
- **Chat history system working** — `llm_group_chat_history` table stores bot messages (4 entries confirmed). Player messages will now be stored with the party leader fix.
- **Playerbot internal messages visible**: type=7 whisper commands ("ss ?", "who", "co ?") and type=1 internal messages (always 12 chars, all-caps with underscores) are correctly filtered.

### Log Noise Reduction

- Changed Python bridge `logging.basicConfig` from `INFO` to `WARNING` (temporary for debugging)
- Promoted 7 key group output logs in `chatter_group.py` from `logger.info` to `logger.warning`
- Added comprehensive `[TRACE]` logging throughout all C++ group handlers (to be removed when stable)

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | Party leader fix, tab filter fix, null checks, loot handler diagnostics, TRACE logging |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | Log level WARNING, group event dispatch logs |
| `modules/mod-llm-chatter/tools/chatter_group.py` | Promoted key output logs to WARNING |
| `modules/mod-llm-chatter/sql/group_chatter_migration_v7.sql` | Added 'cancelled' to queue ENUM |
| `modules/mod-llm-chatter/data/sql/db-characters/base/llm_chatter_tables.sql` | Updated base schema |
| `docs/current_progress.md` | Updated with session progress |

---

## 2026-02-07 (Session 23) - Grouped Bot Chatter PoC

### Summary

Implemented the proof-of-concept for group chatter: when bots are grouped with a real player, they now greet the player in party chat with personality-driven messages. Previously, grouped bots were completely silent (excluded from ambient chatter by `IsGroupedWithRealPlayer()`). This proves the full end-to-end pipeline: C++ GroupScript hook detects bot joining group → queues event → Python assigns personality traits → LLM generates greeting → message delivered via party chat.

### Features Implemented

**C++ GroupScript (LLMChatterScript.cpp):**
- New `LLMChatterGroupScript` class with `OnAddMember`, `OnRemoveMember`, `OnDisband` hooks
- `GroupHasRealPlayer()` helper iterates group members to find non-bot players
- `QueueBotGreetingEvent()` direct INSERTs to `llm_chatter_events` (bypasses `QueueEvent()` to skip reaction chance/cooldowns)
- `DeliverPendingMessages()` now routes `channel='party'` messages via `ai->SayToParty()` instead of `SayToChannel(GENERAL)`
- Gated by `LLMChatter.GroupChatter.Enable` config (default: disabled)

**Personality Traits System (chatter_group.py):**
- New modular Python file following existing pattern (constants, shared, prompts, events, group)
- `PERSONALITY_TRAITS` dict: 5 categories (social, attitude, focus, humor, energy) with 4-6 traits each
- `assign_bot_traits()`: picks 3 random categories, selects 1 trait each, stores in `llm_group_bot_traits` table
- `build_bot_greeting_prompt()`: generates LLM prompt incorporating traits and normal/roleplay mode
- `process_group_event()`: full event handler (assign traits → LLM call → insert party message → mark complete)
- Traits stored per group+bot, refreshed on re-invite (ON DUPLICATE KEY UPDATE)

**Bridge Integration (llm_chatter_bridge.py):**
- Early intercept in `process_pending_events()` for `bot_group_join` events
- Bypasses zone-based bot/player checks since group context is already known from C++ hook

**Database:**
- New `llm_group_bot_traits` table (group_id, bot_guid, bot_name, trait1-3, assigned_at)
- Added `bot_group_join` to `llm_chatter_events.event_type` ENUM

**Config:**
- `LLMChatter.GroupChatter.Enable` in `mod_llm_chatter.conf.dist` (default: 0)

### Test Results

Successfully tested with 4 bots joining a group. Each bot received unique traits and generated personality-appropriate greetings in party chat:
- Melyell (reckless, no-nonsense, hyper): "Let's go let's go let's go, I'm ready to wreck stuff!"
- Sytarre (cynical, talkative, cheerful): "hey, ready to make some magic happen or what lol"
- Cylaea (dry wit, drowsy, optimistic): "sup, ready when you are... just woke up lol"
- Yladros (cynical, explorer, drowsy): "meh, alright let's see where this goes"

### Files Changed

| File | Change |
|------|--------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | GroupScript class, party delivery routing |
| `modules/mod-llm-chatter/src/LLMChatterConfig.h` | Added `_useGroupChatter` field |
| `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` | Load GroupChatter.Enable config |
| `modules/mod-llm-chatter/tools/chatter_group.py` | **New** - traits, greeting prompt, event handler |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | Import + early intercept for group events |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | GroupChatter.Enable setting |
| `modules/mod-llm-chatter/sql/group_chatter_migration.sql` | **New** - traits table + ENUM update |

---

## 2026-02-07 (Session 22) - Multi-Turn Conversation Context & Chatter Modularization

### Summary

Fixed mod-llm-guide losing conversational context between messages. Previous exchanges were stored as 150-char truncated summaries in the system prompt; now they're stored as full question/response text and replayed as real user/assistant message turns. This enables natural pronoun resolution and follow-ups. Also committed mod-llm-chatter's accumulated features: spell messages, trade messages, bridge modularization, and C++ spell link support.

### Features Implemented

**Multi-Turn Conversation Context (mod-llm-guide):**
- Added `question` TEXT and `response` TEXT columns to `llm_guide_memory` table
- `fetch_memories()` now returns full Q&A dicts for message replay
- `store_memory()` saves complete question and response text alongside summary
- `build_system_prompt()` only includes older topic summaries (not recent history)
- `call_anthropic()` and `call_openai()` prepend history as real user/assistant message turns
- `call_llm()` and `process_request()` pass memories through the call chain
- Legacy rows (pre-migration, empty Q&A) are gracefully skipped
- Backward compatible: summary field still populated for topic extraction

**Spell Messages (mod-llm-chatter):**
- New message type (5% of messages): bots mention class-appropriate spells
- Uses `spell_names.py` (49,839 spell names from spell_dbc) for trainer spell lookups
- Queries `trainer` + `trainer_spell` + `spell_dbc` tables (`Type=0` for class trainers)
- Generates clickable `[[spell:ID:Name]]` links

**Trade Messages (mod-llm-chatter):**
- New message type (10% of messages): WTS/WTB-style messages
- Uses zone loot items with proper item links

**C++ Spell Link Support (mod-llm-chatter):**
- Added `ConvertSpellLinks()` function to render `[[spell:ID:Name]]` as purple WoW spell hyperlinks
- Integrated into `ConvertAllLinks()` chain

**Bridge Modularization (mod-llm-chatter):**
- Split monolithic bridge into 5 files: constants, shared, prompts, events, bridge
- Added `spell_names.py` for spell data
- Bridge version bumped to v3.6

### Bugs Fixed

**Conversation Context Loss (mod-llm-guide):**
- Before: "does that spell get upgraded?" after asking about Arcane Shot would get "I need more context"
- After: Guide correctly understands "that spell" = Arcane Shot from previous turn
- Root cause: Summaries in system prompt don't enable LLM pronoun resolution; real message turns do

### Database Changes

```sql
ALTER TABLE llm_guide_memory
    ADD COLUMN question TEXT NOT NULL AFTER character_name,
    ADD COLUMN response TEXT NOT NULL AFTER question;
```

### Files Changed

**mod-llm-guide (Python):**
- `modules/mod-llm-guide/tools/llm_bridge.py`:
  - Added migration for question/response columns in `_ensure_table_exists()`
  - Updated `fetch_memories()` to return Q&A dicts
  - Updated `store_memory()` to accept and save full Q&A
  - Updated `build_system_prompt()` to exclude recent history
  - Updated `call_anthropic()`, `call_openai()`, `call_llm()` with `memories_recent` param
  - Updated `process_request()` to wire memories through

**mod-llm-chatter (C++):**
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp`:
  - Added `ConvertSpellLinks()` function
  - Added to `ConvertAllLinks()` chain

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` - Refactored to import from modules
- `modules/mod-llm-chatter/tools/chatter_constants.py` - Constants, tones, moods, categories (new)
- `modules/mod-llm-chatter/tools/chatter_shared.py` - Shared utilities, config, selection (new)
- `modules/mod-llm-chatter/tools/chatter_prompts.py` - All prompt builders (new)
- `modules/mod-llm-chatter/tools/chatter_events.py` - Event processing (new)
- `modules/mod-llm-chatter/tools/spell_names.py` - 49,839 spell names (new)

### Git Commits

- **mod-llm-guide** `885f912`: `feat: Multi-turn conversation context for proper follow-up questions`
- **mod-llm-chatter** `593fcd6`: `feat: Spell messages, trade messages, modularization, spell links`

### Technical Notes

- With `memory_context_count = 5`, up to 5 previous exchanges replayed as real turns
- Typical WoW Q&A is short: ~1500-2500 extra input tokens per request
- Haiku 4.5 has 200k context; cost impact is negligible
- No C++ compilation needed for guide changes (Python only)
- mod-llm-chatter C++ changes (spell links) need compilation

---

## 2026-02-07 (Session 21) - Roleplay vs Normal Chatter Mode

### Summary

Implemented a configurable `ChatterMode` toggle (`normal` | `roleplay`) for mod-llm-chatter. Normal mode preserves the existing casual MMO chat style, while roleplay mode makes bots speak in-character with race/class personality. Fixed a bug where numeric race/class IDs were passed to prompt builders. After initial testing, toned down RP mode from theatrical to "RP server casual" and expanded tone pools for more variety. Added full prompt logging for tuning. Switched provider back to Anthropic Haiku 4.5.

### Features Implemented

**ChatterMode Config Option:**
- Added `LLMChatter.ChatterMode = normal` to both config files
- Values: `normal` (casual MMO chat) | `roleplay` (in-character, not theatrical)
- `get_chatter_mode(config)` helper reads and validates the setting

**Race/Class Personality System (Roleplay Mode):**
- `RACE_SPEECH_PROFILES` dict - 10 races with `traits` and `flavor_words`
  - Human: practical, earnest; Orc: blunt, proud; Undead: darkly humorous, etc.
- `CLASS_SPEECH_MODIFIERS` dict - 10 classes with speech influence descriptions
  - Warrior: direct, values courage; Paladin: righteous, speaks of duty, etc.
- `build_race_class_context(race, class_name)` - builds RP personality fragment with "don't force it" instruction

**RP Constant Sets (parallel to existing normal constants):**
- `RP_TONES` (20): "relaxed but in-character", "tired from traveling", "dry and understated", "homesick", etc.
- `RP_MOODS` (20): "calm", "curious", "friendly", "dry humor", "matter-of-fact", etc.
- `RP_CREATIVE_TWISTS` (14): "Complain about something minor", "Reference food, drink, or rest", etc.
- `RP_MESSAGE_CATEGORIES` (40): "commenting on the area around you", "thinking about food or drink", etc.
- `RP_LENGTH_HINTS` (4): "short and casual", "a normal sentence", etc.

**Expanded Normal TONES (9 → 20):**
- Added: "hyped up", "distracted and rambling", "low-key bragging", "sarcastically amused", "deadpan and dry", "nostalgic about old content", "impatient and antsy", "chill but opinionated", "genuinely impressed", "sleepy and unfocused"

**Mode-Aware Selection Functions:**
- `pick_random_tone(mode)`, `pick_random_mood(mode)`, `maybe_get_creative_twist(chance, mode)`
- `pick_random_message_category(mode)` - new function
- `generate_conversation_mood_sequence(count, mode)`
- `build_dynamic_guidelines(include_humor, include_length, config, mode)` - RP-specific guidelines

**All 8 Prompt Builders + Event Statement Path Modified:**
- Each gets `mode = get_chatter_mode(config)` at top
- RP mode: race/class personality context, "stay in character but sound natural, not theatrical"
- Normal mode: unchanged behavior, "Do NOT mention your race or class"

**Prompt Logging:**
- Full prompt/context logged before every LLM call (both `call_llm()` and event statement path)
- Shows provider, model, max_tokens, and complete prompt text
- Temporary - for tuning purposes

**RP Tone-Down (after testing):**
- Initial RP was too pompous/theatrical - toned down across the board
- Guidelines: "Speak fully in-character" → "Stay in character but keep it natural and conversational, not dramatic or theatrical"
- Tones: replaced grand tones with grounded ones (e.g., "reverent and thoughtful" → "relaxed but in-character")
- Moods: replaced heavy moods with everyday ones (e.g., "solemn" → "calm", "fierce" → "friendly")
- Twists: replaced theatrical ones with casual ones (e.g., "Offer a blessing" → "Complain about something minor")
- Categories: replaced weighty topics with everyday topics (e.g., "musing on the nature of this conflict" → "thinking about food or drink")
- Extras: "Speak with the gravity of one who has seen battle" → "Casual and grounded, not poetic or flowery"

**Removed Trail-Off Twists:**
- Removed "End mid-thought with ...", "Trail off at the end" (normal), "Trail off mid-thought" (RP)
- These made output look truncated rather than stylistic

**Startup Logging:**
- Bridge version bumped to v3.5
- Logs `ChatterMode: normal/roleplay` at startup

### Bugs Fixed

**Numeric Race/Class IDs in Prompts:**
- `process_pending_requests()` was passing numeric IDs (e.g., `class=4` instead of `"Rogue"`)
- Only event processing converted them; statement/conversation paths did not
- Created `_make_bot()` helper that uses `get_class_name()` / `get_race_name()` for conversion
- Applied to statement bot dict and all 4 conversation bot dicts

**Pre-existing Syntax Error:**
- Line 1487 had `, LENGTH_HINTS = [` (stray leading comma)
- Fixed by removing the comma

**Operator Precedence Issue:**
- `_make_bot` helper had ambiguous ternary: `zone_override or request[...] if ... in request else ...`
- Rewrote with explicit if/elif/else block

### Configuration Changes

```ini
# Added to both config files:
LLMChatter.ChatterMode = normal

# Switched back to Haiku:
LLMChatter.Provider = anthropic
LLMChatter.Model = haiku
```

### Files Changed

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Added `get_chatter_mode()` helper
  - Added `RACE_SPEECH_PROFILES`, `CLASS_SPEECH_MODIFIERS`, `build_race_class_context()`
  - Added RP constant sets: `RP_TONES`, `RP_MOODS`, `RP_CREATIVE_TWISTS`, `RP_MESSAGE_CATEGORIES`, `RP_LENGTH_HINTS`
  - Expanded `TONES` from 9 → 20 entries
  - Updated all selection functions with `mode` parameter
  - Updated `build_dynamic_guidelines()` with grounded RP-specific guidelines
  - Modified all 8 prompt builders for mode threading
  - Modified event statement inline prompt for RP mode
  - Added `_make_bot()` helper with race/class text conversion
  - Added full prompt logging in `call_llm()` and event statement path
  - Removed 3 trail-off creative twists (normal + RP)
  - Fixed stray comma before `LENGTH_HINTS`
  - Bumped version to v3.5

**mod-llm-chatter (Config):**
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` - Added `ChatterMode` option with documentation
- `env/dist/etc/modules/mod_llm_chatter.conf` - Added `ChatterMode = normal`, switched to anthropic/haiku

**Documentation:**
- `docs/mod-llm-chatter/chatter-mode-guide.md` - New file: simple explanation of normal vs RP mode logic

### Technical Notes

- Normal mode behavior is completely unchanged (all new parameters default to `'normal'`)
- Quest/item link placeholder system (`{quest:Name}`, `{item:Name}`) is untouched
- RP mode always includes race/class context for all bots in conversations (vs 40% chance in normal)
- RP guidelines aim for "RP server casual" - in-character but natural, not theatrical
- RP mode gets slightly higher long-message chance (+5, max 30%)
- Prompt logging is temporary - remove when done tuning
- Weather grade < 0.27 reports as "clear" (normal WoW behavior, not a bug)

---

## 2026-02-06 (Session 20) - OpenAI Tool Support, Chatter Cleanup & ZoneId Fixes

### Summary

Implemented full OpenAI tool support for mod-llm-guide (was disabled). Fixed mod-llm-chatter output quality issues: em-dashes causing double spaces, emoji removal, and randomized time/weather context to reduce LLM pattern lock-in. Fixed 3 game data tools using empty zoneId column.

### Features Implemented

**OpenAI Tool Support (mod-llm-guide):**
- Implemented `convert_tools_to_openai_format()` to convert Anthropic tool format to OpenAI function calling format
- Rewrote `call_openai()` with full tool calling loop (max 3 rounds)
- Tool format conversion: `input_schema` → `parameters` inside `function` wrapper
- Added `GAME_TOOLS_OPENAI` pre-converted list for efficiency
- Updated startup logging: "Tools: 29 game data tools available"
- Users can now switch between Anthropic and OpenAI providers seamlessly

**Randomized Environmental Context (mod-llm-chatter):**
- Created `get_environmental_context()` helper function
- Distribution: 40% time only, 30% weather only, 20% both, 10% neither
- Prevents LLM from always referencing time/weather in every message
- Reduces output pattern lock-in

**Em-Dash Fix (mod-llm-chatter):**
- Changed simple replace to regex: `re.sub(r'\s*—\s*', ', ', result)`
- Handles surrounding whitespace to prevent double-spacing
- Em-dashes now become ", " consistently

**Emoji Removal (mod-llm-chatter):**
- Added comprehensive emoji regex pattern covering:
  - Emoticons, symbols, pictographs
  - Transport & map symbols, flags, dingbats
  - Enclosed characters, supplemental symbols
  - Chess symbols, misc symbols
- Emojis don't render in WoW chat, now stripped automatically

### Bugs Fixed

**ZoneId Column Empty in Database:**
- `list_zone_creatures`, `_get_zone_herbs`, `_get_zone_mining` tools used `c.zoneId` or `g.zoneId`
- Database has zoneId=0 for most entries (1808 creatures with zoneId=0 vs 2 with zoneId=141)
- Fixed all 3 tools to use coordinate-based filtering via `_get_zone_filter()`
- For herbs/mining, converted zone_filter to gameobject table prefix (`c.` → `g.`)

**Memory Caching Wrong Answer:**
- LLM used cached incorrect answer ("no creatures in Teldrassil") instead of calling tool
- Fixed by clearing bad memory: `DELETE FROM llm_guide_memory WHERE summary LIKE '%hunt%Teldrassil%'`

### Configuration Changes

**mod-llm-guide (for testing):**
```ini
# Temporarily switched to test OpenAI:
LLMGuide.Provider = openai
```

### Files Changed

**mod-llm-guide (Python):**
- `modules/mod-llm-guide/tools/llm_bridge.py`:
  - Added `convert_tools_to_openai_format()` function
  - Added `GAME_TOOLS_OPENAI` pre-converted list
  - Rewrote `call_openai()` with full tool calling loop
  - Added "Tools: X game data tools available" to startup logging

- `modules/mod-llm-guide/tools/game_tools.py`:
  - Fixed `_list_zone_creatures` to use coordinate filtering
  - Fixed `_get_zone_herbs` to use coordinate filtering with gameobject prefix
  - Fixed `_get_zone_mining` to use coordinate filtering with gameobject prefix

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Fixed `cleanup_message()` em-dash replacement with regex
  - Added comprehensive emoji removal pattern
  - Added `get_environmental_context()` helper function
  - Updated all 9 prompt builders to use randomized context

**Documentation:**
- `docs/mod-llm-guide/game-data-lookup-engine.md`:
  - Marked OpenAI tool compatibility as DONE (2026-02-06)

### Technical Notes

- OpenAI function calling format differs from Anthropic:
  - Anthropic: `{"name": "tool", "input_schema": {...}}`
  - OpenAI: `{"type": "function", "function": {"name": "tool", "parameters": {...}}}`
- Tool result format also differs:
  - Anthropic: Content block with `tool_use_id`
  - OpenAI: Message with `role: "tool"` and `tool_call_id`
- Environmental context randomization uses `random.random()` with threshold checks
- Zone coordinate filtering is more reliable than zoneId for all creature/object queries

---

## 2026-02-05 (Session 19) - Transport Context Fix, Event Filtering & Rare Spawn Fix

### Summary

Fixed transport arrival chatter to correctly indicate direction of travel (bots were saying "heading to" their current location). Added grouped bot filtering to Python event processing. Added weather guidance to prompts and mood logging for all statement types. Added EnableVerboseLogging config option to both modules. Fixed rare spawn tool returning incorrect results.

### Features Implemented

**Transport Context Fix:**
- Fixed confusing boat messages where bots said "heading to Rut'theran Village" while already at Rut'theran Village
- Updated `build_event_context()` to clearly explain:
  - Where the transport ARRIVED (current location of bots)
  - Where it CAME FROM (origin)
  - If bots board, they go TO the origin
- Updated `build_event_conversation_prompt()` with clearer direction instructions
- Example fixed output: "Anyone need passage to Auberdine?" (correct direction)

**Grouped Bot Filtering for Events:**
- C++ side already filtered grouped bots for statements/conversations
- Python event processing was missing this filter
- Added SQL subquery to exclude bots in groups with real (non-RNDBOT) players
- Prevents immersion break where grouped bots chat in General while adventuring with player

**Mood Logging for All Statement Types:**
- Plain statements already logged mood
- Added mood logging to: quest, loot, quest+reward statements
- Log format: `Quest statement creativity: tone=X, mood=Y, quest=Z`

**Weather Guidance in Prompts:**
- Added "Feel free to naturally reference the weather if it fits" to weather context
- Matches existing time-of-day guidance style
- May increase natural weather mentions in chatter

**EnableVerboseLogging Config Option:**
- Added `LLMChatter.EnableVerboseLogging = 1` to mod_llm_chatter.conf.dist
- Added `LLMGuide.EnableVerboseLogging = 1` to mod_llm_guide.conf.dist
- NOTE: Not yet connected to conditions - placeholder for future implementation
- Allows disabling verbose logging in production while keeping it for development

### Bugs Fixed

**Transport Direction Confusion:**
- Bots incorrectly mentioned destinations they were already at
- Root cause: Context said "heading to destination" but destination was current location
- Fix: Rewrote context to clearly indicate arrival point vs origin

**Rare Spawn Tool Not Working:**
- LLM (Haiku) was answering "no rare spawns in Teldrassil" from memory instead of using tool
- Three issues fixed:
  1. Strengthened tool description: "ALWAYS use this tool... Do NOT guess or answer from memory"
  2. Changed from `zoneId` column filtering to coordinate-based filtering (zoneId often unpopulated)
  3. Fixed SQL syntax error: `WHERE AND...` → `WHERE 1=1 {zone_filter}` (zone_filter starts with AND)
- Tool now correctly returns 6 rares in Teldrassil: Threggil, Uruson, Fury Shelda, Duskstalker, Grimmaw, Blackmoss the Fetid

### Configuration Changes

**mod-llm-chatter:**
```ini
# Added:
LLMChatter.EnableVerboseLogging = 1
```

**mod-llm-guide:**
```ini
# Added:
LLMGuide.EnableVerboseLogging = 1
```

### Files Changed

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Updated `build_event_context()` for transport_arrives - clearer direction info
  - Updated `build_event_conversation_prompt()` - better transport instructions
  - Added grouped bot filter to event bot selection queries (2 queries)
  - Added mood variables and logging to quest/loot/quest+reward statement builders
  - Added weather guidance to plain statement and conversation prompts

**mod-llm-chatter (Config):**
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist`:
  - Added `LLMChatter.EnableVerboseLogging` setting with documentation

**mod-llm-guide (Python):**
- `modules/mod-llm-guide/tools/game_tools.py`:
  - Strengthened `find_rare_spawn` tool description to force LLM usage
  - Changed rare spawn query from zoneId to coordinate-based filtering
  - Fixed SQL syntax: `WHERE 1=1 {zone_filter}` pattern

**mod-llm-guide (Config):**
- `modules/mod-llm-guide/conf/mod_llm_guide.conf.dist`:
  - Added `LLMGuide.EnableVerboseLogging` setting with documentation

### Technical Notes

- Transport context now explicitly states: "Bots are AT destination, transport arrived FROM origin"
- Grouped bot filter uses `NOT EXISTS` subquery checking `group_member` table
- Both zone-specific and global event queries now filter grouped bots
- Local LLM support discussed - both modules are architected to support it via `base_url` config (future enhancement)
- Rare spawn tool uses `_get_zone_filter()` which returns filter starting with `AND`, requiring `WHERE 1=1` base clause
- EnableVerboseLogging is a placeholder - actual conditional logging not yet implemented

---

## 2026-02-05 (Session 18) - Command Rename: .ask → .ag

### Summary

Renamed the mod-llm-guide chat command from `.ask` to `.ag` (Azeroth Guide) for a shorter, more convenient command.

### Changes Made

**Command Rename:**
- Changed primary command from `.ask` to `.ag`
- Changed subcommand from `.llm ask` to `.llm ag`
- Updated usage message to show `.ag <your question>`

### Files Changed

**mod-llm-guide (C++):**
- `modules/mod-llm-guide/src/LLMGuideScript.cpp`:
  - Line 897: Usage message `.ask` → `.ag`
  - Line 986: Subcommand `"ask"` → `"ag"`
  - Line 992: Shortcut command `"ask"` → `"ag"`

### Technical Notes

- Requires compilation to take effect
- No database changes required
- No configuration changes required

---

## 2026-02-05 (Session 17) - Compilation Workflow & Documentation Updates

### Summary

Successfully compiled mod-llm-chatter C++ changes using the manual compilation workflow. Updated documentation with the new manual compilation steps required due to Docker timestamp sync issues. Fixed Python bridge to stay running when disabled instead of exit-looping.

### Features Implemented

**Manual Compilation Workflow Documented:**
- Updated `CLAUDE.md` with step-by-step manual compilation instructions
- Updated `docs/development/dev-server-guide.md` with the same workflow
- Key insight: Windows Docker has timestamp sync issues - files edited on Windows don't update timestamps in the container, so `make` doesn't detect changes
- **MANDATORY**: Must touch source files inside container before running `make`

**Python Bridge Disable Behavior Fixed:**
- Bridge now stays running when `LLMChatter.Enable = 0` instead of exiting
- Logs "LLMChatter is disabled in config. Waiting... (checking every 60s)"
- Re-checks config every 60 seconds to allow enabling without restart
- No more container restart loops when module is disabled

### Bugs Fixed

**Docker State Issue Causing Server Crashes:**
- Server was being SIGKILL'd (exit 137) during startup
- Root cause: Docker state issue, not C++ code
- Fix: Full container restart (`docker compose --profile dev down` then `up`)
- The playerbots database connection error in logs was a red herring

**Compilation Not Detecting Changes:**
- `compile.sh` was returning instantly without actually compiling
- Root cause: Docker timestamp sync issue between Windows and container
- Fix: Manual workflow - touch files, then run make directly

### Configuration Changes

None (documentation only)

### Files Changed

**Documentation:**
- `CLAUDE.md`:
  - Added "CRITICAL: Docker Timestamp Issue" section
  - Replaced compile.sh instructions with manual 6-step workflow

- `docs/development/dev-server-guide.md`:
  - Added Docker timestamp issue warning
  - Updated Quick Reference with manual compilation steps
  - Updated Compilation Types section to reference manual workflow

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Changed disabled behavior from `sys.exit(0)` to wait loop
  - Re-checks config every 60 seconds when disabled

### Technical Notes

**Manual Compilation Workflow (required for incremental builds):**
```powershell
# Step 1: Stop worldserver
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 pkill -9 worldserver"

# Step 2: Touch source files
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'find /azerothcore/modules/MODULE/src -name \"*.cpp\" -o -name \"*.h\" | xargs touch'"

# Step 3: Compile modules
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make -j12 modules 2>&1'"

# Step 4: Link worldserver
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make -j12 worldserver 2>&1'"

# Step 5: Install
powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make install 2>&1'"

# Step 6: Restart container
docker compose --profile dev restart ac-dev-server
```

**Why compile.sh Doesn't Work:**
- The script runs `make` which checks timestamps to determine what needs recompiling
- Windows NTFS timestamps don't sync to the Docker container's view of the mounted files
- Result: `make` sees no changes and does nothing
- Full rebuild (`--full`) still works because it runs `cmake` which regenerates everything

---

## 2026-02-05 (Session 16) - Creativity System & WeatherChatterChance Removal

### Summary

Major creativity enhancements to prevent LLM repetitive patterns. Added CREATIVE_TWISTS system, expanded MESSAGE_CATEGORIES, cleaned up MOODS, removed all concrete examples from prompts. Removed the old WeatherChatterChance system in favor of passing weather context to all prompts naturally.

### Features Implemented

**CREATIVE_TWISTS System:**
- Added 47 creative twist modifiers organized by category:
  - Structure twists (7): "Start with an interjection", "End mid-thought with ...", etc.
  - Content twists (8): "Reference a made-up guild drama", "Mention a keybind or UI element", etc.
  - Tone twists (7): "Sound like you just woke up", "Be overly dramatic about something minor", etc.
  - Player behavior twists (7): "Reference being AFK", "Mention checking the auction house", etc.
  - Social twists (6): "Respond as if you misheard something", "Give unsolicited advice", etc.
  - Expression twists (7): "Trail off at the end", "Use excessive abbreviations", etc.
- Applied 30-40% of the time via `maybe_get_creative_twist()` function
- Adds unpredictability the LLM can't pattern-match

**MESSAGE_CATEGORIES Expansion:**
- Expanded from ~12 to 80+ categories for statement prompts
- Added atmospheric (8), mystical (8), nostalgic (9), contemplative (6) category groups
- Rebalanced for positivity - reduced complaints from 5 to 2 (made humorous)
- Categories now cover: observations, reactions, questions, social, humor, progress, creatures, gear, meta, advice, roleplay, atmospheric, mystical, nostalgic, contemplative

**MOODS Cleanup:**
- Cleaned all 25 moods to single words without examples
- Prevents LLM from copying example patterns
- Moods: questioning, complaining, happy, disappointed, joking around, slightly sarcastic, enthusiastic, confused, proud, neutral, dramatic, deadpan, roleplaying, nostalgic, impatient, grateful, showing off, self-deprecating, philosophical, surprised, helpful, geeky, tired, competitive, distracted

**Weather Context for All Prompts:**
- Weather state now passed to ALL prompt builders (plain, quest, loot, quest_reward, conversations)
- LLM can naturally reference any weather (clear, rain, snow, etc.) in any context
- Format: `"Current weather: {weather_type}"` in prompt

**Removed WeatherChatterChance System:**
- Removed `WeatherChatterChance` config option entirely
- Removed `build_weather_statement_prompt()` function
- Removed `build_weather_conversation_prompt()` function
- Removed `query_zone_weather_types()` function
- Removed `SCRIPTED_WEATHER_TYPES` and `DESERT_ZONES` dictionaries
- Removed weather cache methods from `ZoneDataCache`
- Weather is now integrated naturally, not as a separate message type

**Creativity Logging:**
- Added logging for all creative selections
- Statements: `Prompt creativity: tone=X, mood=Y, category=Z, twist=W`
- Conversations: `Conversation creativity: tone=X, moods=[...], twist=W`

**Compilation Workflow Fix:**
- Fixed Docker timestamp issue where `make` doesn't detect source changes
- Updated `.claude/agents/azerothcore-build-specialist.md` with manual workflow:
  1. Stop worldserver
  2. Touch source files inside container
  3. Run `make -j12 modules`
  4. Run `make -j12 worldserver`
  5. Run `make install`
  6. Restart server

### Bugs Fixed

**Removed Concrete Examples from Prompts:**
- Removed all example outputs that LLM was copying verbatim
- Removed `LOOT_EXAMPLE_SETS` and `pick_random_examples` function
- Simplified guidelines to abstract "Be creative and unpredictable"
- Prevents pattern lock-in from example copying

### Configuration Changes

```
# Removed entirely:
LLMChatter.WeatherChatterChance = 10  # DELETED
```

### Files Changed

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Added `CREATIVE_TWISTS` list (47 twists)
  - Added `maybe_get_creative_twist()` function
  - Expanded `MESSAGE_CATEGORIES` to 80+ entries
  - Cleaned `MOODS` to single words (25 moods)
  - Added `current_weather` parameter to all prompt builders
  - Removed weather-specific prompt functions
  - Removed weather cache and query functions
  - Added creativity logging
  - Removed concrete examples from all prompts

**mod-llm-chatter (Config):**
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist`:
  - Removed `WeatherChatterChance` setting and documentation

**Build Agent:**
- `.claude/agents/azerothcore-build-specialist.md`:
  - Rewrote with manual compilation workflow
  - Added mandatory workaround for Docker timestamp issue

### Technical Notes

- Weather types still tracked by C++ (`_zoneWeatherState` map) and passed to Python
- All 14 weather types preserved: clear, foggy, light rain, rain, heavy rain, light snow, snow, heavy snow, light sandstorm, sandstorm, heavy sandstorm, thunderstorm, black rain, black snow
- Creative twists are additive - they don't replace tone/mood, they add another layer
- Zone fatigue system unchanged - still prevents spam in busy zones

---

## 2026-02-05 (Session 15) - Transport & Weather Event Fixes

### Summary

Fixed transport event frequency issues (too many boat announcements), corrected weather type mapping (sandstorms only in desert zones), and removed the global message cap that was blocking weather events.

### Features Implemented

**Transport Event Rate Limiting:**
- Added `TransportCooldownSeconds = 300` (5 min) to prevent duplicate boat announcements
- Same transport entering same zone won't trigger again for 5 minutes
- Combined with 30% chance filter (`TransportEventChance`), gives ~1 transport message every 15-20 min per route

**Weather Type Correction:**
- Added `DESERT_ZONES` set: Tanaris (440), Silithus (1377), Thousand Needles (400), Badlands (3), Barrens (17), Orgrimmar (1637), Thunder Bluff (1638)
- Storm weather now correctly maps to:
  - "sandstorm" for desert zones only
  - "thunderstorm" for all other zones
- Fixes issue where bots mentioned sandstorms in coastal zones like Darkshore

**Disabled Random Weather Chatter:**
- Set `WeatherChatterChance = 0` to disable random weather talk
- Bots now only mention weather during actual `weather_change` events from C++
- Ensures weather context matches actual in-game weather

**Removed Global Message Cap:**
- Removed `GlobalMessageCap` check entirely from Python bridge
- Was blocking weather events and causing "Global message cap reached" spam in logs
- Other rate limits (per-bot cooldown, zone fatigue, trigger chance) are sufficient

### Bugs Fixed

**Weather Events Blocked by Global Cap:**
- Weather events were stuck in "pending" status due to global cap
- Root cause: Conversations generate 4-6 messages, quickly hitting the 8-message cap
- Fix: Removed global cap entirely

**Sandstorms in Non-Desert Zones:**
- `storm_*_chance` columns in `game_weather` were incorrectly mapped to "sandstorm" for all zones
- Now correctly maps to zone-appropriate weather type

### Configuration Changes

```
LLMChatter.TransportCooldownSeconds = 300    # Was 0
LLMChatter.WeatherChatterChance = 0          # Was 10
```

### Files Changed

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Added `DESERT_ZONES` set for zone-aware weather type mapping
  - Updated `query_zone_weather_types()` to map storm→sandstorm only for desert zones
  - Removed global message cap check from `process_pending_event()`

**Configuration:**
- `env/dist/etc/modules/mod_llm_chatter.conf`:
  - `TransportCooldownSeconds`: 0 → 300
  - `WeatherChatterChance`: 10 → 0

**Documentation Cleanup:**
- Deleted obsolete debug notes:
  - `docs/mod-llm-chatter/2026-02-04-fixes.md`
  - `docs/mod-llm-chatter/2026-02-04-boat-arrival-debug.md`

### Technical Notes

- Transport cooldown uses per-transport+zone key: `transport:{entry}:zone:{zoneId}`
- Weather events from C++ contain correct weather type in `extra_data` JSON
- Zone fatigue still applies to weather events (bypassed for transport events)
- Bridge restart required for Python changes (no C++ compilation needed)

---

## 2026-02-04 (Session 14) - Transport Chatter & JSON Escaping Fix

### Summary

Investigated and fixed boat arrival chatter not working in Darkshore. Transport chatter is now functional. Identified and fixed JSON escaping issues in C++ code, but compilation failed due to OOM (ccache was accidentally cleared). Python JSON repair function added as workaround.

### Features Implemented

**Transport Arrival Chatter (Working):**
- Bots now react to transport arrivals (boats, zeppelins, turtles)
- Tested successfully in Darkshore: "Hey! Just grabbed the transport to Rut'theran Village, Teldrassil"
- Transport events bypass bot speaker cooldown (high priority events)
- Specific transport type (boat/zeppelin/turtle) mentioned instead of generic "transport"

**Bot Detection Fix (Python):**
- Changed from queue-based detection to account-based detection
- Bots = accounts with username LIKE 'RNDBOT%'
- Real players = accounts NOT LIKE 'RNDBOT%'
- Fixes chicken-and-egg problem where bots needed to have chatted before being detected

**JSON Repair Function (Python):**
- Added `repair_json_string()` function to handle malformed JSON from C++
- Attempts multiple repair strategies for unescaped quotes
- Falls back to regex extraction of known fields
- Added `parse_extra_data()` wrapper for graceful degradation

**Database Schema Change:**
- Changed `extra_data` column from JSON to TEXT type
- Avoids MySQL JSON validation errors during INSERT

### Bugs Fixed

**IsPlayerBot Linker Error:**
- Function was forward-declared at line 47 but defined inside a class (line 1018)
- Moved full definition to global scope at line 47
- Removed duplicate class method definition
- **Status: Fixed in source, pending compilation**

**JSON Escaping in C++ (JsonEscape function):**
- Quotes inside transport names (e.g., `"The Moonspray"`) weren't escaped for JSON
- Fixed escaping: `"` → `\\"` for SQL string literals containing JSON
- **Status: Fixed in source, pending compilation**

### Compilation Issues

**OOM During Compilation:**
- Compiler (`cc1plus`) killed by OOM killer during module build
- Root cause: ccache was accidentally cleared + 12 parallel jobs
- **Solution: Use `--jobs 4` for reduced memory usage**
- Command: `docker exec azerothcore-wotlk-ac-dev-server-1 bash /azerothcore/apps/docker/compile.sh --jobs 4`

**ccache Accidentally Cleared:**
- `ccache -C` was run (documented as "NEVER do this" in dev guide)
- Cache is now empty (0.00 GB)
- Core libraries (libgame.a, libscripts.a) still intact
- Only modules need rebuilding, not full 2-hour rebuild

### Files Changed

**mod-llm-chatter (C++):**
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp`:
  - Fixed `IsPlayerBot()` - moved from class to global scope
  - Fixed `JsonEscape()` - proper escaping for quotes in SQL string literals

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Added `repair_json_string()` function for JSON repair
  - Added `parse_extra_data()` wrapper function
  - Changed bot detection from queue-based to account-based (RNDBOT% pattern)
  - Added transport event cooldown bypass
  - Added fallback parsing for transport context from target_name

**Database:**
- `llm_chatter_events.extra_data` column changed from JSON to TEXT

### Technical Notes

- Transport events use `GetZoneId()` on transport position for zone filtering
- Global message cap can be bypassed for high-priority transport events
- Transport type detection parses target_name for "Boat", "Zeppelin", "Turtle" keywords
- OOM occurs because empty ccache means all files compiled from scratch

### Next Steps for Future Agent

1. **Compile with reduced parallelism:**
   ```bash
   docker exec azerothcore-wotlk-ac-dev-server-1 bash /azerothcore/apps/docker/compile.sh --jobs 4
   ```

2. **After successful compilation:**
   - Restart worldserver
   - Test transport event JSON by checking `llm_chatter_events.extra_data` for new events
   - Verify no "Failed to parse extra_data JSON" warnings in bridge logs

3. **Verify fixes work:**
   - Go to Darkshore and wait for boat to arrive
   - Check bridge logs for transport event processing
   - Confirm bots mention specific transport type (boat) and destination

---

## 2026-02-03 (Session 13) - Weather Events & Zone-Filtered Loot

### Summary

Improved weather event handling to only trigger for zones with real players, added conversation support for weather events, and fixed loot selection to be zone-appropriate (no more Kodo Leather in Teldrassil).

### Features Implemented

**Weather Events - Real Player Check (C++):**
- Weather events now only fire for zones where a real (non-bot) player is present
- Added session iteration using `sWorldSessionMgr->GetAllSessions()`
- Uses `IsPlayerBot(player)` to distinguish real players from bots
- Fixes issue where bots in other zones would comment on weather players couldn't see

**Weather Events - Conversation Support (Python):**
- Added `build_event_conversation_prompt()` function for multi-bot weather discussions
- Weather events now randomly trigger: 60% conversation, 40% statement
- Conversations use 2-4 bots from the zone
- Falls back to statement if conversation generation fails

**Zone-Filtered Loot (Python):**
- Fixed `query_zone_loot()` to use coordinate-based filtering
- Joins to `creature` table and filters by spawn location coordinates
- Prevents items from wrong zones (e.g., Murloc Eye in Teldrassil where no murlocs exist)
- Falls back to level-based query for zones not in ZONE_COORDINATES

**Subzone Aliases (mod-llm-guide):**
- Added starting area aliases to `zone_coordinates.py`:
  - `shadowglen` → `teldrassil` (Night Elf)
  - `coldridge valley` → `dun morogh` (Dwarf/Gnome)
  - `valley of trials` → `durotar` (Orc/Troll)
  - `red cloud mesa` → `mulgore` (Tauren)
  - `camp narache` → `mulgore` (Tauren)
  - `sunstrider isle` → `eversong woods` (Blood Elf)
  - `ammen vale` → `azuremyst isle` (Draenei)

### Bugs Fixed

**Weather State Tracking:**
- Weather state was not updated when no real player present
- Could cause incorrect transition detection (e.g., "intensifying" vs "starting")
- Fixed: State now updates before real player check

**Duplicate Bots in Fallback Queries:**
- Fallback queries could return the same bot multiple times
- Added `DISTINCT` to both zone-specific and global event fallback queries

**Windows/Docker Compatibility:**
- Docker commands in Git Bash produce no stdout (known MSYS2 issue)
- Fixed `backup-database.sh` to use PowerShell for docker commands
- Updated documentation with workaround

### Files Changed

**mod-llm-chatter (C++):**
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp`:
  - Added real player check in `OnWeatherChange()`
  - Fixed weather state tracking order
  - Added thread safety comment

**mod-llm-chatter (Python):**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Added `build_event_conversation_prompt()` function
  - Modified event processing for 60/40 conversation/statement split
  - Fixed `query_zone_loot()` with coordinate filtering
  - Added DISTINCT to fallback queries

**mod-llm-guide (Python):**
- `modules/mod-llm-guide/tools/zone_coordinates.py` - Added 7 starting subzone aliases

**DevOps:**
- `apps/docker/backup-database.sh` - PowerShell compatibility fix
- `docs/development/dev-server-guide.md` - Docker/bash workaround documentation
- `CLAUDE.md` - Added compilation policy (never compile automatically)
- Deleted deprecated `apps/docker/recompile-module.sh`

**Documentation:**
- `docs/mod-llm-chatter/review-instructions-weather-events.md` - Review instructions for changes

### Technical Notes

- Weather state tracking must happen before real player check to avoid stale state
- `GetAllSessions()` is safe to iterate from ALEScript hooks (main thread)
- Zone-filtered loot uses same ZONE_COORDINATES as zone mobs query
- Event conversation/statement ratio (60/40) could be made configurable

### Compilation Status

- C++ changes require compilation (not yet done)
- Python changes require bridge restart

---

## 2026-02-03 (Session 12) - Code Review Fixes for Both LLM Modules

### Summary

Applied fixes from code review reports for both mod-llm-chatter and mod-llm-guide modules. All issues validated before fixing to avoid unnecessary changes.

### mod-llm-chatter Fixes

**Fix #1: Added `get_zone_name()` function**
- Added `ZONE_NAMES` dictionary with ~70 zone IDs mapped to human-readable names
- Added `get_zone_name()` function to convert zone IDs to names
- Prevents crashes when referencing zone names in event processing

**Fix #2: Queue completion check before marking complete**
- Changed to only mark queue entries as 'completed' if LLM processing succeeded
- Failed requests now marked as 'failed' instead of 'completed'
- Prevents silent data loss when LLM calls fail

**Fix #3: Updated transport config comment**
- Changed "future feature - not yet implemented" to accurate description
- Transport events are now fully implemented and working

**Fix #7: Improved bot presence detection**
- Changed from querying queue history to live `characters` table
- Added `CLASS_NAMES` and `RACE_NAMES` dictionaries
- Bots now selected based on actual online status in zone
- Expanded join to include bot1/2/3/4 guids (was only bot1)

**Fix #10: Added JSON parse error logging**
- Added warning log when `extra_data` JSON fails to parse
- Logs event ID, type, and parse error message
- Helps diagnose malformed event data

### mod-llm-guide Fixes

**Fix #1: SQL table name mismatch**
- Renamed SQL tables from `llm_chat_*` to `llm_guide_*`
- Renamed SQL file from `llm_chat_queue.sql` to `llm_guide_queue.sql`
- Tables now match C++ and Python code references

**Fix #2: Added 'cancelled' to status enum**
- Added 'cancelled' value to enum in SQL file
- Added 'cancelled' to Python bridge enum
- Prevents MySQL errors when C++ sets status to 'cancelled' on startup

**Fix #3: DELETE order fix**
- Moved DELETE statement after successful response delivery
- Responses no longer lost if player logs out before delivery
- Row remains in queue for retry when player logs back in

**Fix #4: Documentation clarification**
- Added note that memory is per-session (cleared on login)
- Updated Memory Settings section with session behavior
- Aligns documentation with actual implementation

### Files Changed

**mod-llm-chatter:**
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` - Zone names, class/race names, bot selection, JSON logging
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` - Transport comment fix

**mod-llm-guide:**
- `modules/mod-llm-guide/data/sql/db-characters/base/llm_guide_queue.sql` (renamed from llm_chat_queue.sql) - Table names, enum
- `modules/mod-llm-guide/tools/llm_bridge.py` - Enum fix
- `modules/mod-llm-guide/src/LLMGuideScript.cpp` - DELETE order fix
- `docs/mod-llm-guide/mod-llm-guide-documentation.md` - Memory behavior clarification

### Technical Notes

- SQL injection issue in mod-llm-chatter intentionally NOT fixed (local solo play use case)
- Memory reset on login is intentional design choice, just needed documentation
- Compilation not yet done - waiting for another review pass

---

## 2026-02-03 (Session 11) - Zone Auto-Injection & Server Stability

### Summary

Short session focused on completing zone auto-injection for mod-llm-guide tool calls and stabilizing the server after investigating crashes caused by mod-llm-chatter.

### Features Implemented

**Zone Auto-Injection (mod-llm-guide):**
- Tool calls now automatically inject the player's current zone when not specified
- Fixes issue where LLM (Haiku) wouldn't pass the zone parameter to tools like `find_npc`
- Implementation:
  - Added `extract_zone_from_context()` function to parse zone from character context
  - Added `set_player_zone()` method to `GameToolExecutor` class
  - Modified `execute_tool()` to inject zone for supported tools when not provided
  - Zone-aware tools: `find_vendor`, `find_trainer`, `find_service_npc`, `find_npc`, `find_quest_giver`, `get_available_quests`, `find_creature`, `find_hunter_pet`, `get_flight_paths`, `list_zone_creatures`

### Bugs Fixed

**mod-llm-chatter Causing Server Crashes:**
- Server was crashing with segmentation fault (exit code 139) during character creation cinematic
- Isolated by systematically disabling modules
- mod-llm-chatter identified as likely cause (kept disabled for stability)
- mod-llm-guide confirmed stable after re-enabling

**LLMChatter Config Warnings:**
- Added all missing config options to mod_llm_chatter.conf to silence startup warnings
- Added Event System Settings, Rate Limiting Settings, and Event Type Toggles

**Playerbots Native Chatter:**
- Disabled playerbots built-in chatter to avoid interference with mod-llm-chatter:
  - `AiPlayerbot.RandomBotSuggestDungeons = 0`
  - `AIPlayerbot.GuildFeedback = 0`
  - `AiPlayerbot.EnableBroadcasts = 0`

### Files Changed

- `modules/mod-llm-guide/tools/game_tools.py`:
  - Added `default_zone` attribute to `GameToolExecutor`
  - Added `set_player_zone()` method
  - Added zone auto-injection logic in `execute_tool()`
- `modules/mod-llm-guide/tools/llm_bridge.py`:
  - Added `extract_zone_from_context()` function
  - Modified `process_request()` to extract and set player zone before processing
- `env/dist/etc/modules/mod_llm_chatter.conf`:
  - Set `LLMChatter.Enable = 0` (disabled for stability)
  - Added Event System Settings section
  - Added Rate Limiting Settings section
  - Added Event Type Toggles section
- `env/dist/etc/modules/playerbots.conf`:
  - Disabled native chatter settings
- `CLAUDE.md` - Cleaned up and clarified container names
- `docs/development/dev-server-guide.md` - Fixed typos

### Technical Notes

- Zone extraction regex: `r' in ([^.]+?)(?:\.|,|\s+(?:Horde|Alliance))'`
- Character context format: "Name is a level X Race Class in ZoneName. Faction..."
- Zone auto-injection happens before tool execution, so logs show "Auto-injected zone 'X' into tool_name"
- mod-llm-chatter remains disabled pending investigation of segfault cause

---

## 2026-02-03 (Session 10) - Fresh Build, Database Recovery & Compilation Workflow

### Summary

Major infrastructure session focused on fixing stale CMake references and improving the development workflow. The module rename from `mod-llm-chat` to `mod-llm-guide` required a complete CMake reconfiguration. Unfortunately, a Docker volume deletion (`-v` flag) accidentally wiped the database, requiring account recreation.

### Features Implemented

**Compilation Workflow Improvements:**
- Created `apps/docker/compile.sh` - Main compilation script with:
  - Lock file mechanism (`/tmp/.compiling`) to prevent server auto-start during compilation
  - `--full` flag for cmake + make (new modules)
  - `--no-restart` flag to skip server restart
  - `--jobs N` for parallel compilation (default: 12)
  - Automatic server stop/restart handling
  - ccache configuration and stats display

- Updated `apps/docker/start-dev-servers.sh` with:
  - `COMPILE_ONLY=1` environment variable support
  - Lock file detection (waits for compilation to finish)
  - Crash handling (keeps container alive for debugging)

**Database Backup System:**
- Created `apps/docker/backup-database.sh`:
  - Backs up acore_auth, acore_characters, acore_playerbots
  - Saves to `/azerothcore/backups/` directory
  - Keeps last 5 backups per database
  - Run with: `docker exec azerothcore-wotlk-ac-dev-server-1 bash /azerothcore/apps/docker/backup-database.sh`

**Account Creation Tool:**
- Created `apps/docker/create_account.py`:
  - Creates accounts with proper SRP6 authentication (salt + verifier)
  - Generates cryptographically secure salt
  - Calculates verifier using SRP6 algorithm

### Bugs Fixed

**CMake Stale Reference:**
- CMakeCache.txt had reference to old `mod-llm-chat` module
- Fixed by full cmake reconfiguration with correct `mod-llm-guide` module name

**Corrupt Object File:**
- `cs_item.cpp.o` was 0 bytes, causing linker errors
- Fixed by deleting the corrupt file and recompiling

### Critical Mistakes Made (Documented for Prevention)

1. **`docker compose down -v` deleted ALL volumes including database**
   - Lost user account CALWEN and character Karaez
   - Had to recreate account using SRP6 credentials
   - **Prevention**: Added backup script, documented in CLAUDE.md

### Files Added

- `apps/docker/compile.sh` - Main compilation script with lock file mechanism
- `apps/docker/backup-database.sh` - Database backup script
- `apps/docker/create_account.py` - SRP6 account creation tool

### Files Changed

- `apps/docker/start-dev-servers.sh` - Added COMPILE_ONLY mode, lock file detection, crash handling
- `CLAUDE.md` - Added "CRITICAL MISTAKES TO AVOID" section
- `docs/development/dev-server-guide.md` - Updated compilation commands and added Scripts Reference

### Technical Notes

- Lock file mechanism: `compile.sh` creates `/tmp/.compiling`, `start-dev-servers.sh` waits for it
- SRP6 authentication: Uses 32-byte random salt, SHA1 hash, modular exponentiation with g=7
- Compilation workflow: Stop servers → Create lock → Compile → Install → Remove lock → Restart servers
- Account recreated: CALWEN with password calwen, gmlevel 0

---

## 2026-02-02 (Session 9) - Spell Names Fixed & E2E Testing Framework

### Features Implemented

**Spell Names & Descriptions - COMPLETE:**
- Extracted **49,839 spell names** from `Spell_kaev.sql` (from Kaev/AzerothcoreDBCToSQL)
- Extracted **31,744 spell descriptions** with placeholder cleaning
- Created `spell_names.py` with `SPELL_NAMES` and `SPELL_DESCRIPTIONS` dictionaries
- Updated `game_tools.py` to use new spell data in `list_spells_by_level` and `get_spell_info`

**Spell Description Placeholder Cleaning:**
- Added `clean_description()` function to handle WoW placeholders:
  - `$s1`, `$s2`, `$s3` → `[X]` (effect values)
  - `$d` → `[duration]`
  - `$o1`, `$o2` → `[total over time]`
  - `${$RAP*...}` → `[damage based on ranged attack power]`
  - `${$AP*...}` → `[damage based on attack power]`
  - `${$SP*...}` → `[damage/healing based on spell power]`
  - `$/10;s2` → `[X]` (division patterns)
  - `$?sID[if][else]` → `[X]` (conditionals)
  - `$g...:...;` → `his/her` (gender forms)
  - `$l...:...;` → `bottle/bottles` (plural forms)

**End-to-End Testing Framework:**
- Created `tests/test_questions.json` with 2 questions per tool (58 total for 29 tools)
- Created `tests/run_e2e_tests.py` - automated test runner using Haiku
- Tests check for:
  - Tool usage (expected tool called)
  - Uncleaned placeholders (`$s1`, `$RAP`, etc.)
  - Broken link markers
  - Tool errors
- **Final result: 58/58 tests passing (100%)**

### Bugs Fixed

**find_recipe_source SQL Error:**
- Column names were wrong: `Spell1`/`Spell2` → `spellid_1`/`spellid_2`
- Fixed SQL query in `game_tools.py` line 2001

**get_flight_paths Tool Description:**
- Description didn't mention listing flight points in a zone
- Updated to: "Get information about flight paths in a zone or from a location..."
- LLM now correctly uses tool for "List all flight points in Tanaris" type questions

**Test Questions Improved:**
- `find_item_upgrades` Q2: Changed to be more specific about what to upgrade
- `find_recipe_source` Q2: Changed to ask about a specific recipe
- `get_flight_paths` Q2: Changed from NPC location question to flight path listing

**Documentation Update:**
- Updated all references from `.llm ask` to `.ask` command format

### Files Added

- `modules/mod-llm-guide/tools/Spell_kaev.sql` - Complete spell data from Kaev repo (33MB)
- `modules/mod-llm-guide/tools/spell_names.py` - Auto-generated spell dictionaries (49,835 names, 31,744 descriptions)
- `modules/mod-llm-guide/tools/tests/test_questions.json` - E2E test questions for all 29 tools
- `modules/mod-llm-guide/tools/tests/run_e2e_tests.py` - E2E test runner

### Files Changed

- `modules/mod-llm-guide/tools/game_tools.py`:
  - Added import for `SPELL_NAMES`, `SPELL_DESCRIPTIONS`
  - Updated `_list_spells_by_level` to use spell descriptions
  - Updated `_get_spell_info` to include description
  - Fixed `_find_recipe_source` SQL column names
  - Updated `get_flight_paths` tool description
- `modules/mod-llm-guide/tools/extract_spell_names.py` - Updated for Kaev SQL format

### Technical Notes

- Spell_kaev.sql format: One INSERT per line, cleaner than dbc_335.sql
- `Name_Lang_enUS` at column 134, `Description_Lang_enUS` at column 168
- Multi-line INSERT handling added to parser for completeness
- E2E tests run against live LLM bridge container using Haiku model
- Test runner saves markdown report to `/tmp/tool-test-report.md`

---

## 2026-02-02 (Session 8) - Spell Name Fix Attempt

### Issue Identified

**Spell Names Showing as "SPELL" Instead of Actual Names:**
- When using the Azeroth Guide's `list_spells_by_level` tool, spell names display as "SPELL" instead of actual names like "Scorpid Sting" or "Raptor Strike"
- Root cause: The `spell_dbc` table in AzerothCore only contains ~4,492 internal/server-side spells, not player abilities
- The `SPELL_MAP` dictionary is incomplete (~150 spells) and doesn't cover all trainer spells
- Trainer spell IDs (e.g., 3043, 14323) don't have names available in the database

### Solution Approach

**Downloaded dbc_335.sql from wolfiestyle/dbc_browser:**
- URL: https://github.com/wolfiestyle/dbc_browser
- File: `modules/mod-llm-guide/tools/dbc_335.sql` (24MB)
- Contains complete WoW 3.3.5 DBC data extracted to SQL format
- The Spell table has columns: `Id` (spell ID) and `SpellName` (actual spell name)
- SpellName is at column position ~136 in the table

**Next Steps (Not Completed - Session Crashed):**
1. Parse `dbc_335.sql` to extract spell ID → name mappings
2. Create `spell_names.py` with `SPELL_NAMES` dictionary
3. Update `game_tools.py` to use the new spell name dictionary
4. Restart LLM bridge and test

### Files Added

- `modules/mod-llm-guide/tools/dbc_335.sql` - Full DBC dump from wolfiestyle repo (24MB)
- `modules/mod-llm-guide/tools/extract_spell_names.py` - Parser script (incomplete)

### Technical Notes

- The Spell table in dbc_335.sql has 173+ columns
- SpellName is around column 136 (after counting from CREATE TABLE)
- Need to parse SQL INSERT statements carefully (handle quoted strings with commas)
- Alternative attempted: User tried to extract Spell.dbc from WoW client but couldn't find it (it's inside MPQ archives)

---

## 2026-02-02 (Session 7) - Module Rename & Tool Improvements

### Features Implemented

**Module Rename: mod-llm-chat → mod-llm-guide**
- Renamed module directory: `modules/mod-llm-chat/` → `modules/mod-llm-guide/`
- Renamed C++ source files:
  - `LLMChatConfig.cpp/.h` → `LLMGuideConfig.cpp/.h`
  - `LLMChatScript.cpp` → `LLMGuideScript.cpp`
  - `llm_chat_loader.cpp` → `llm_guide_loader.cpp`
- Updated all class names: `LLMChat*` → `LLMGuide*`
- Updated all config keys: `LLMChat.*` → `LLMGuide.*`
- Updated database table names: `llm_chat_*` → `llm_guide_*`
- Renamed config file: `mod_llm_chat.conf` → `mod_llm_guide.conf`
- Updated docker-compose.override.yml volume paths
- Updated all documentation references

**Spell Tools Improvement:**
- Replaced static `CLASS_TRAINER_IDS` with `CLASS_IDS` mapping (class name → class ID)
- Updated `_list_spells_by_level` to dynamically query `trainer` table:
  - `trainer.Type = 0` identifies class trainers
  - `trainer.Requirement` stores class ID for Type 0
- Added try/except fallback for `spell_dbc` table (may not exist)
- Expanded `SPELL_MAP` from ~70 to ~150 spells (added Death Knight abilities)

**Dungeon Info Improvement:**
- Replaced static `DUNGEON_INFO` (10 Classic dungeons) with database queries
- Added `DUNGEON_LOCATIONS` mapping (~60 dungeons/raids including TBC/WotLK)
- Updated `_get_dungeon_info` to query:
  - `dungeon_access_template` for level ranges, difficulty modes, item level requirements
  - `dungeon_access_requirements` for entry prerequisites (attunements, keys)

### Bugs Fixed

**Code Review Fixes:**
- Fixed duplicate `'death coil'` key in SPELL_MAP (renamed warlock's to `'death coil warlock': 6789`)
- Fixed `get_dungeon_info` description (mentioned "bosses" but didn't return them)
- Fixed Naxxramas location (Eastern Plaguelands → Dragonblight for WotLK)
- Fixed Arathi Basin battlemaster duplicate entry IDs (Sir Maximus Adams: 19855, Donal Osgood: 857, Lady Hoteshem: 15008)

### Git Operations

- Committed module rename to `modules/mod-llm-guide/.git` (local repo)
- Merged `llm-modules` branch into `Playerbot` branch (5 commits)
- Playerbot branch now contains all LLM module documentation and tooling

### Files Changed

**C++ Source (renamed and updated):**
- `modules/mod-llm-guide/src/LLMGuideConfig.cpp`
- `modules/mod-llm-guide/src/LLMGuideConfig.h`
- `modules/mod-llm-guide/src/LLMGuideScript.cpp`
- `modules/mod-llm-guide/src/llm_guide_loader.cpp`

**Python:**
- `modules/mod-llm-guide/tools/game_tools.py` - CLASS_IDS, DUNGEON_LOCATIONS, spell/dungeon improvements
- `modules/mod-llm-guide/tools/llm_bridge.py` - Updated table names and config keys

**Configuration:**
- `modules/mod-llm-guide/conf/mod_llm_guide.conf.dist` (renamed)
- `env/dist/etc/modules/mod_llm_guide.conf` (active config)
- `docker-compose.override.yml` - Updated paths

**Documentation (all references updated):**
- `docs/mod-llm-guide/*.md`
- `docs/current_progress.md`
- `docs/history.md`
- `docs/development/dev-server-guide.md`

### Technical Notes

- Module rename requires CMake reconfiguration (not yet done)
- CMake reconfiguration will trigger rebuild (~30 min with ccache)
- Trainer table query: `Type = 0` means class trainer, `Requirement` = class ID
- Dungeon data comes from `dungeon_access_template` (121+ dungeon/raid entries)

---

## 2026-01-31 (Session 6) - Tool Expansion: 7 New Game Data Tools

### Features Implemented

**New Tools Added to mod-llm-guide (22 → 29 tools):**

1. **`find_rare_spawn`** - Find rare spawn mobs in a zone
   - Queries creature_template with rank=4 (Rare) and rank=2 (Rare Elite)
   - Shows spawn point count per mob
   - Includes NPC links for colored display

2. **`get_zone_info`** - Zone information lookup
   - Manual ZONE_INFO dictionary with ~55 zones
   - Covers all continents: Eastern Kingdoms, Kalimdor, Outland, Northrend
   - Returns level range, faction (Alliance/Horde/Contested), continent, nearby capital
   - Suggests adjacent zones based on level proximity

3. **`find_battlemaster`** - Find battleground queue NPCs
   - Manual BATTLEMASTERS dictionary for all 6 battlegrounds
   - WSG, AB, AV, EotS, SotA, IoC
   - Shows Alliance and Horde NPCs with locations
   - Includes NPC links

4. **`get_weapon_skill_trainer`** - Find weapon skill trainers
   - Manual WEAPON_TRAINERS dictionary for all 8 major cities
   - Shows trainer name, location, and teachable weapon skills
   - Filterable by weapon type and faction

5. **`get_class_quests`** - Class-specific quest chains
   - Database query using AllowableClasses bitmask
   - Shows quests exclusive to a specific class
   - Includes notable quest info (pet quests, form quests, mount quests)
   - Quest links included

6. **`get_quest_chain`** - Full quest chain traversal
   - Traverses backward via PrevQuestID to find chain start
   - Traverses forward via RewardNextQuest to build full chain
   - Shows quest giver names
   - Marks the searched quest's position in the chain
   - Quest links for all entries

7. **`get_reputation_info`** - Faction reputation information
   - Manual FACTION_NAMES dictionary with ~65 factions (Classic, TBC, WotLK)
   - Queries creature_onkill_reputation for mobs that give rep
   - Queries quest_template for quests that give rep (prioritizes repeatables)
   - Queries item_template + npc_vendor for faction rewards by standing
   - Shows standing cap for kill reputation
   - Item, quest, and NPC links included

### Technical Decisions

**Database vs Manual Data:**
- Zone info, battlemasters, weapon trainers, faction names: Manual dictionaries (data not in DB or in DBC files)
- Rare spawns, class quests, quest chains, reputation sources/rewards: Database queries

**Crafting Materials Tool Skipped:**
- Reagent data is stored in client-side Spell.dbc, not in database
- spell_dbc table exists but is mostly empty
- Would require DBC extraction or external data source

### Files Changed

- `modules/mod-llm-guide/tools/game_tools.py`:
  - Added 7 tool definitions to GAME_TOOLS list
  - Added 7 dispatcher entries in execute_tool()
  - Added ZONE_INFO dictionary (~55 zones)
  - Added BATTLEMASTERS dictionary (6 battlegrounds)
  - Added WEAPON_TRAINERS dictionary (8 cities)
  - Added FACTION_NAMES dictionary (~65 factions)
  - Added STANDING_RANKS dictionary
  - Added 7 implementation methods

- `docs/mod-llm-guide/future-plans.md`:
  - Updated tool count 22 → 29
  - Added new tools to Current Tool Inventory
  - Moved implemented tools from Planned to Recently Implemented
  - Added Reputation category
  - Updated priority order

### Configuration
- No configuration changes required
- Bridge restart loads new tools automatically

### Technical Notes

- Quest chains use both `PrevQuestID` (backward) and `RewardNextQuest` (forward) for traversal
- Negative `PrevQuestID` means "quest must NOT be completed" (faction alternatives)
- Reputation standing values: Neutral=0-3000, Friendly=3000-6000, Honored=6000-12000, Revered=12000-21000, Exalted=21000-42000
- Faction rewards query joins item_template with npc_vendor to show vendor names
- Kill reputation has MaxStanding cap (e.g., caps at Revered, need quests for Exalted)

---

## 2026-01-30 (Session 5) - Zone System Overhaul & 2-4 Bot Conversations

### Features Implemented

**Zone Coordinates System (mod-llm-guide):**
- Completely rewrote `ZONE_COORDINATES` dict with accurate WorldMapArea.dbc boundaries
- Fixed `_get_zone_filter()` in game_tools.py to use new coordinate format
- NPC location queries now return accurate coordinates (e.g., Nyoma at 57.2, 61.3)

**Zone Flavor System (mod-llm-chatter):**
- Created `ZONE_FLAVOR` dict with rich atmosphere descriptions for ~45 zones
- Each zone gets a paragraph describing atmosphere, dangers, and feel
- AI agent reviewed and corrected 6 inaccuracies:
  - Loch Modan: Removed ogres, added Dark Iron dwarves
  - Deadwind Pass: Added Deadwind ogres, demonic corruption
  - Azshara: Replaced blood elf emphasis with Blue Dragonflight
  - Felwood: Fixed Timbermaw (neutral) vs Deadwood (hostile)
  - Moonglade: Clarified as peaceful/safe
  - Winterspring: Removed blue dragons, added Winterfall furbolgs

**Zone Mobs Context Improvement:**
- Changed from passing 1 random mob (50% chance) to always passing 10 random mobs
- Added constraint: "Only mention creatures from the provided list"
- Prevents LLM hallucinating creatures (e.g., "spiders in Darkshore" when none exist)

**Message Delay Fix:**
- **Root cause**: `MessageDelayMax=8000` was capping all calculated delays to exactly 8.0s
- **Fix**: Increased to 30000ms (30s) so delays fall naturally below the cap
- Changed delay calculation from `random.triangular()` to `random.uniform()` for flatter distribution
- Delays now vary realistically: 12.7s, 14.5s, 17.0s, 23.0s, etc.

**2-4 Bot Conversations:**
- Conversations now support 2-4 participants (was always 2)
- Distribution: 50% 2-bot, 30% 3-bot, 20% 4-bot
- **Database**: Added `bot_count`, `bot3_guid/name/class/race/level`, `bot4_guid/name/class/race/level` columns
- **C++ (LLMChatterScript.cpp)**: Updated bot selection logic and `QueueChatterRequest()` function
- **Python (llm_chatter_bridge.py)**:
  - Updated `parse_conversation_response()` to handle variable speakers
  - Updated `build_plain_conversation_prompt()`, `build_quest_conversation_prompt()`, `build_loot_conversation_prompt()` to accept list of 2-4 bots
  - Updated `process_conversation()` to read bot3/bot4 from queue
  - Message count scales with participants (bot_count to bot_count+3 messages)
- Successfully tested: 4-bot conversation with 7 messages across all participants

### Configuration Changes

Production values restored:
- `LLMChatter.TriggerIntervalSeconds`: 60 (was 30 for testing)
- `LLMChatter.TriggerChance`: 30 (was 60 for testing)
- `LLMChatter.MessageDelayMax`: 30000 (permanent fix, was 8000)

### Files Changed

- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Added `ZONE_FLAVOR` dict (~45 zones)
  - Updated all conversation prompt builders for 2-4 bots
  - Updated `parse_conversation_response()` for variable speakers
  - Updated `process_conversation()` to read bot3/bot4
  - Changed delay calculation to use `random.uniform()`
  - Always pass 10 zone mobs (was 1 with 50% chance)
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp`:
  - Added bot selection logic (50%/30%/20% for 2/3/4 bots)
  - Updated `QueueChatterRequest()` to accept bot1-4
  - Updated SQL insert for bot3/bot4 columns
- `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` - Updated MessageDelayMax default to 30000
- `modules/mod-llm-guide/tools/zone_coordinates.py` - Rewrote with accurate WorldMapArea.dbc data
- `modules/mod-llm-guide/tools/game_tools.py` - Fixed `_get_zone_filter()` for new coordinate format
- `env/dist/etc/modules/mod_llm_chatter.conf` - Production values + delay fix
- Database: `llm_chatter_queue` table - Added bot3/bot4 columns

### Technical Notes

- Delay capping issue: When calculated delay (e.g., 32s) exceeds max_delay (8s), `min(32, 8) = 8` causes all delays to cluster at exactly 8.0s
- Zone flavor provides rich context without being templated - LLM uses it as creative inspiration
- 2-4 bot conversations generate more messages for more participants
- Zone mobs use coordinate-based queries for accuracy (ZONE_COORDINATES dict)

---

## 2026-01-30 (Session 4) - Diagnostic Monitoring & Conversation Improvements

### Features Implemented

**Conversation Improvements (mod-llm-chatter):**
- **Bot Name Addressing**: Prompts now instruct bots to address each other by name when speaking directly (e.g., "hey Thylaleath you need help?" instead of "hey you need help?")
- **Fuzzy Name Matching**: Parser tolerates 1-2 character typos in bot names (e.g., "Thylalaeth" → "Thylaleath")
- **Loot Conversations**: Conversations can now be about items/loot (25% chance), not just plain or quest topics
- **Nostalgia Mood**: Added "nostalgic" to the mood options

**Token Limit Fix:**
- Increased MaxTokens from 200 → 350 to prevent JSON truncation in multi-message conversations
- 12% of conversations were failing due to truncated JSON responses

**Context Memory Fix (mod-llm-guide):**
- Fixed bug where follow-up questions lost context about previous tool-based queries
- Memory storage was being skipped for tool queries; now stores condensed summary

**Item Quality Color Fix:**
- Changed `quality_names` from just names to include colors: "Uncommon" → "Uncommon/Green", "Rare" → "Rare/Blue", etc.
- Prevents LLM confusion about item colors (was calling green items "blue")

**Playerbots Broadcast Disabled:**
- Disabled native playerbots loot broadcast system (`BroadcastChanceLootingItem*` all set to 0)
- Prevents duplicate/conflicting item announcements with llm-chatter

**NPC Marker Cleanup:**
- Changed `[[npc:ID:Name]]` markers to display as plain creature names instead of markers
- Cleaner chat output without ID references

### Diagnostic Monitoring Session

**30-minute monitoring results:**
- ~120 requests processed (48% statements, 52% conversations)
- Type roll distributions matched expected thresholds perfectly
- LLM response times: 0.77s - 5.94s (average ~2s)
- Parse success rate: 88% (12% failed due to JSON truncation - now fixed)
- Issues found:
  - JSON truncation from MaxTokens=200 (fixed: now 350)
  - Bot name misspelling causing message drops (fixed: fuzzy matching)

### Configuration Changes

Production values restored after testing:
- `LLMChatter.TriggerIntervalSeconds`: 60
- `LLMChatter.TriggerChance`: 30%
- `LLMChatter.ConversationChance`: 50%
- `LLMChatter.MaxTokens`: 350 (was 200 - kept higher to prevent truncation)
- Statement distribution: 65% plain, 15% quest, 12% loot, 8% quest+reward

Model configurations:
- mod-llm-guide: `claude-haiku-4-5-20251001`
- mod-llm-chatter: `haiku` (alias for claude-haiku-4-5-20251001)

### Files Changed

- `modules/mod-llm-guide/tools/llm_bridge.py` - Memory storage fix for tool queries
- `modules/mod-llm-guide/tools/game_tools.py` - Quality names with colors (4 occurrences)
- `env/dist/etc/modules/mod_llm_chat.conf` - Model: claude-haiku-4-5-20251001
- `env/dist/etc/modules/mod_llm_chatter.conf` - MaxTokens: 350, production values
- `env/dist/etc/modules/playerbots.conf` - Disabled all BroadcastChanceLootingItem* settings
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`:
  - Added `fuzzy_name_match()` function
  - Added bot name addressing to conversation prompts
  - Added loot conversation type
  - Added "nostalgic" mood
  - NPC marker cleanup (plain names)
  - SQL GROUP BY fix for zone_quests
  - Removed diagnostic logging

### Technical Notes

- Haiku 4.5 model ID: `claude-haiku-4-5-20251001` (note: October date, not November)
- WoW item quality colors: Gray/Poor, White/Common, Green/Uncommon, Blue/Rare, Purple/Epic, Orange/Legendary
- Conversation type distribution: 50% plain, 25% quest, 25% loot
- Fuzzy matching uses simple character-by-character comparison with max distance of 2

---

## 2026-01-29 (Session 3) - Link System Expansion & Response Quality

### Features Implemented

**NPC Links (Green Colored Names):**
- Added `ConvertNpcLinks()` function to both mod-llm-guide and mod-llm-chatter
- NPC/creature names now display in green (`|cff00ff00Name|r`)
- Format: `[[npc:ID:Name]]` markers converted to colored text
- Updated 8 tools to output NPC markers: find_vendor, find_trainer, find_service_npc, find_npc, find_quest_giver, find_creature, find_hunter_pet, find_recipe_source

**Markdown Stripping:**
- Added `StripMarkdown()` function to remove `**bold**`, `*italic*`, `___`, `__` wrappers
- Prevents Claude from adding markdown formatting that displays as raw text in WoW
- Runs before link conversion in response processing

**Response Length Optimization:**
- Updated system prompt to match answer length to question complexity
- Simple questions (where to buy X) get 1-2 sentence answers
- Complex questions (builds, strategies) get longer explanations
- Removed unnecessary padding and context

**Tool Instructions for Link Markers:**
- Added "IMPORTANT: Include these [[...]] markers exactly as-is" to all tool descriptions
- Added reminder at end of tool results to include markers
- Fixes issue where Claude would summarize tool results instead of including markers

**Quest Deduplication (mod-llm-chatter):**
- Fixed quest chains appearing too frequently in random selection
- "Tower of Althalaxx" had 9 entries, heavily skewing random choice
- Added `GROUP BY q.LogTitle` to ensure unique quest names only
- Each quest name now has equal probability regardless of chain length

**NPC Links in mod-llm-chatter:**
- Added item, quest, and NPC link conversion functions to C++
- Updated `query_zone_mobs()` to return `[[npc:entry:name]]` markers
- Updated prompts to instruct Claude to include NPC markers when mentioning creatures

### Configuration Changes
- `LLMGuide.MaxTokens`: 300 → 800
- `LLMGuide.MaxResponseLength`: 800 → 1000
- System prompt character limit: 500 → 1200
- Updated system prompt for brevity

### Files Changed
- `modules/mod-llm-guide/src/LLMGuideScript.cpp` - Added StripMarkdown(), ConvertNpcLinks(), ConvertAllLinks()
- `modules/mod-llm-guide/tools/game_tools.py` - Added NPC markers to 8 tools, added IMPORTANT instructions
- `modules/mod-llm-guide/tools/llm_bridge.py` - (no changes this session)
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` - Added link conversion functions
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` - NPC markers in mob queries, quest deduplication
- `env/dist/etc/modules/mod_llm_chat.conf` - Updated token limits and system prompt

### Technical Notes
- WoW 3.3.5 doesn't support clickable NPC links, so we use colored text instead
- NPC color: `|cff00ff00` (green, like friendly NPCs)
- Link conversion order: Items → Spells → Quests → NPCs
- Quest chains share the same LogTitle, causing over-representation in random selection

---

## 2026-01-29 (Session 2) - mod-llm-guide Polling Fix

### Bugs Fixed

**mod-llm-guide Response Delivery Issue:**
- First `.ask` request wouldn't deliver response until a second request was sent
- Root cause: Same `s_expectingResponses` optimization bug as mod-llm-chatter
- After 2-minute timeout, polling would stop entirely
- Fix: Removed the optimization, now continuously polls for responses

### Features Implemented

**Stale Request Cleanup (mod-llm-guide):**
- Added `OnStartup()` to cancel pending/processing requests from previous session
- Prevents old unanswered questions from being processed after server restart

### Documentation Updated
- `docs/mod-llm-guide/mod-llm-guide-documentation.md` - Added stale cleanup, clarified polling behavior
- `docs/mod-llm-chatter/mod-llm-chatter-documentation.md` - Added multi-provider, stricter prompts, polling info

### Files Changed
- `modules/mod-llm-guide/src/LLMGuideScript.cpp` - Removed s_expectingResponses, added OnStartup cleanup

---

## 2026-01-29 - Polling Fix, Prompt Improvements & Module Git Repos

### Bugs Fixed

**Message Polling Race Condition:**
- Conversations were getting stuck - only 2 of 4 messages delivered
- Root cause: `_expectingMessages` optimization had race conditions
- Fix: Removed the optimization, now always polls for messages
- Simpler code, more reliable delivery

**Quest/Item Placeholder Issue:**
- GPT-4o-mini wasn't consistently using `{quest:Name}` placeholders
- Links were appearing as plain text instead of clickable
- Fix: Made prompts stricter with "REQUIRED: Include exactly {placeholder}"
- Added example output showing expected format

### Features Implemented

**Module Git Repositories:**
- Initialized separate git repos in `modules/mod-llm-guide/` and `modules/mod-llm-chatter/`
- Allows independent version control (AzerothCore's .gitignore excludes modules/)
- Can add remote origins later for GitHub publishing

**Natural Chat Interface Planning:**
- Added ideas to `docs/mod-llm-guide/future-plans.md` for removing `.ask` prefix
- Options: Whisper to NPC (recommended), custom channel, shorter prefix, client addon
- Whisper to NPC approach would be most immersive

### Configuration Changes
- Tested GPT-4o-mini successfully
- Switched back to Haiku (better instruction following)
- `LLMChatter.Provider = anthropic`
- `LLMChatter.Model = haiku`

### Files Changed
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` - Simplified polling (removed _expectingMessages)
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` - Stricter placeholder prompts
- `docs/mod-llm-guide/future-plans.md` - Natural chat interface ideas
- `env/dist/etc/modules/mod_llm_chatter.conf` - Switched to haiku

### Module Commits
- **mod-llm-chatter**: 3 commits (initial + polling fix + prompt fix)
- **mod-llm-guide**: 1 commit (initial)

---

## 2026-01-28 (Session 2) - Multi-Provider Support & Fixes

### Features Implemented

**mod-llm-chatter Multi-Provider Support:**
- Added support for both **Anthropic** and **OpenAI** providers
- Config-level switching via `LLMChatter.Provider` (anthropic/openai)
- Model aliases for simple config: haiku, sonnet, opus, gpt4o, gpt4o-mini
- Created `call_llm()` function that abstracts provider API differences
- Created `resolve_model()` for alias → full model name mapping
- Tested successfully with GPT-4o-mini

**Stale Message Cleanup:**
- Added cleanup in `OnStartup()` to clear old undelivered messages
- Deletes from `llm_chatter_messages WHERE delivered = 0`
- Cancels pending/processing queue entries
- Prevents old messages appearing after server restart/re-login

**Link Bracket Fix:**
- Fixed `cleanup_message()` incorrectly stripping brackets from WoW links
- Added check to detect `|h` prefix before brackets
- Quest/item links now display correctly: `|h[Quest Name]|h`

### Configuration Changes
- `LLMChatter.Provider = openai` (or `anthropic`)
- `LLMChatter.Model = gpt4o-mini` (aliases: haiku, sonnet, opus, gpt4o, gpt4o-mini)
- `LLMChatter.OpenAI.ApiKey` - New config option for OpenAI key
- Trigger settings: 30s interval, 15% chance

### Documentation Created
- `docs/mod-llm-guide/future-plans.md` - Planned enhancements for chat module
- `docs/mod-llm-chatter/future-plans.md` - Planned enhancements for chatter module

### Files Changed
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` - Multi-provider support, link fix
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` - OnStartup cleanup
- `docker-compose.override.yml` - Added openai to pip install
- `env/dist/etc/modules/mod_llm_chatter.conf` - New provider/model config
- `docs/mod-llm-guide/future-plans.md` (new)
- `docs/mod-llm-chatter/future-plans.md` (new)

### Technical Notes
- OpenAI uses `client.chat.completions.create()` vs Anthropic's `client.messages.create()`
- Response extraction differs: `response.choices[0].message.content` vs `response.content[0].text`
- Model quality varies: GPT-4o-mini sometimes produces RP-like speech despite instructions

---

## 2026-01-28 - mod-llm-chatter Dynamic Prompt System

### Features Implemented

**mod-llm-chatter (Ambient Bot Conversations):**
- **Dynamic Prompt Building**: Prompts are now constructed with randomized elements to prevent LLM pattern lock-in:
  - Random tone selection (casual, tired, cheerful, bored, helpful, frustrated, etc.)
  - Random mood selection (21 moods: questioning, complaining, happy, joking, roleplaying, nostalgic, etc.)
  - Rotating example sets (4 pools per message type)
  - Random guidelines and focus hints
  - Optional context inclusion (level, class, mob - randomly included/excluded)

- **Mood Sequences for Conversations**: Conversations follow a scripted emotional arc:
  - Bridge generates a mood for each message in the conversation
  - LLM must follow the sequence (e.g., confused → helpful → grateful → joking)
  - Creates natural-feeling story arcs in each exchange

- **Zone Mob Queries**: Real mobs from the database instead of LLM guessing:
  - Queries creature_template by level range matching zone
  - Filters for hostile creatures (various factions)
  - 50% chance to include a random mob in plain statements/conversations
  - Cached for 10 minutes

- **Class Usability Checks**: Accurate item/class fit info:
  - Queries AllowableClass bitmask from item_template
  - Maps class names to bitmask values (Warrior=1, Paladin=2, Hunter=4, etc.)
  - Passes accurate "can equip: yes/no" to LLM (randomly included 40% of time)

- **Quest/Item Links**: Clickable WoW links in chat:
  - Quest format: `|cFFFFFF00|Hquest:ID:LEVEL|h[Name]|h|r`
  - Item format: `|cFFCOLOR|Hitem:ID:0:0:0:0:0:0:0|h[Name]|h|r`
  - Colors by quality (gray, white, green, blue, purple)

- **Weighted Loot Rarity**: Epic items are rare (3% weight vs 30% for gray/white)

- **Overworld-Only Restriction**: Chatter disabled in dungeons/raids/BGs:
  - C++ check: `!player->GetMap()->Instanceable()`

- **Party Bot Exclusion**: Bots grouped with real players don't randomly chatter:
  - Iterates group members to check for non-bot players

### Technical Notes

- **Design Principle**: "We provide materials, the LLM crafts the message"
  - All context (bot, item, mob, quest) is optional material
  - LLM decides how to use it, not forced to mention everything

- **Anti-Repetition Strategy**: Dynamic prompts prevent pattern lock-in
  - Each prompt is unique due to random element combinations
  - 21 moods × 9 tones × 4 example sets = massive variation
  - Documented in mod-llm-chatter-documentation.md section 12

### Documentation Created
- `docs/mod-llm-chatter/mod-llm-chatter-documentation.md` - Comprehensive logic documentation including:
  - Trigger system, zone selection, bot selection
  - Message types and distribution
  - Zone data queries (quests, loot, mobs)
  - LLM context and prompt guidelines
  - Message delivery and timing
  - Complete flow example
  - Configuration summary
  - Section 12: Dynamic Prompt Building (anti-repetition)

### Files Changed
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` - Major refactor for dynamic prompts
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp` - Added overworld check, party exclusion
- `docs/mod-llm-chatter/mod-llm-chatter-documentation.md` - Full documentation (new)
- `env/dist/etc/modules/mod_llm_chatter.conf` - Tuned trigger settings

---

## 2026-01-27 - mod-llm-bots Planning & Playerbots Research

### Research Completed

**Playerbots Chat System Investigation:**
- Confirmed bot chat is 100% database-driven (hardcoded strings in `ai_playerbot_texts`)
- Bots broadcast independently - no actual conversations between bots
- Chat selection is random from category + probability roll
- Text supports placeholders (%s, %item_link, %zone_name, etc.)
- `ChatReplyAction` handles responses but uses pattern matching only

**Key Files Identified:**
- `PlayerbotTextMgr.cpp` - Text loading and selection
- `SayAction.cpp` - Chat execution and reply logic
- `BroadcastHelper.cpp` - Broadcast event handling
- `ai_playerbot_texts.sql` - 1000s of predefined chat strings

### Planning Completed

**mod-llm-bots Implementation Plan:**
- Created comprehensive plan at `docs/mod-llm-bots/implementation-plan.md`
- Decision: New module (no playerbots fork required)
- Uses Claude Haiku for cost efficiency (~$0.0002/message)
- 6-phase implementation roadmap

**Key Features Planned:**
1. Natural language whisper conversations with bots
2. Unique bot personalities based on race/class
3. Context-aware responses (health, mana, zone, group)
4. Natural language → bot command translation
5. Party/guild chat with @mention support
6. Future: Bot-to-bot AI conversations

### Documentation Created
- `docs/mod-llm-bots/implementation-plan.md` - Full technical plan
- Updated `docs/mod-llm-guide/mod-llm-guide-documentation.md` - Added "Wow Factor" enhancement ideas
- Updated `docs/current_progress.md` - Added mod-llm-bots tracking

### Architecture Decisions
- Separate module from playerbots (clean separation)
- Reuse existing ac-llm-bridge Python service
- Database queue pattern (same as mod-llm-guide)
- Hook into AzerothCore's PlayerScript::OnChat
- Call playerbots API for bot responses (no fork needed)

---

## 2026-01-27 - mod-llm-guide Enhancements & Session Management

### Features Implemented

**mod-llm-guide:**
- **Character Context**: Comprehensive player info sent to AI:
  - Name, level, class, race, zone, faction
  - Gold, honor points, arena points
  - Professions with skill levels
  - Guild and group status
  - All active quests (up to 25)

- **Conversation Memory**: Two-tier memory system
  - Recent memories (5) kept in detailed format
  - Older memories (10) condensed into topic keywords
  - Prevents context bloat while preserving history
  - Config: `LLMGuide.Memory.SummarizeThreshold`

- **Chat Colors**:
  - `[You]:` in yellow
  - `[Azeroth Guide]:` label in blue (#66AAFF)
  - Response content in yellow (default)

- **Docker Integration**: LLM bridge runs as separate container (ac-llm-bridge)

**Session Management:**
- Created `CLAUDE.md` with session startup instructions
- Created `docs/history.md` for tracking development sessions
- Created `docs/current_progress.md` for current state tracking
- Created `/um` command (`.claude/commands/um.md`) to update memory files
- Merged `AGENTS.md` content into `CLAUDE.md` and deleted `AGENTS.md`

### Model Configuration
- Switched from Claude Haiku to Claude Opus 4.5

### Documentation Created
- `CLAUDE.md` - Session instructions and project knowledge
- `docs/mod-llm-guide-documentation.md` - Comprehensive implementation guide
- `docs/history.md` - Development history tracking
- `docs/current_progress.md` - Current state and pending tasks
- `.claude/commands/um.md` - Update memory command
- Updated module README
- Added module development tips to `docs/development/dev-server-guide.md`

### Files Changed
- `modules/mod-llm-guide/src/LLMGuideScript.cpp`
- `modules/mod-llm-guide/tools/llm_bridge.py`
- `modules/mod-llm-guide/conf/mod_llm_chat.conf.dist`
- `docker-compose.override.yml`
- `CLAUDE.md` (new)
- `docs/history.md` (new)
- `docs/current_progress.md` (new)
- `.claude/commands/um.md` (new)
- `AGENTS.md` (deleted, merged into CLAUDE.md)

---

## 2026-01-26 - Karaez Bag Upgrade

### Changes
- Upgraded Karaez's bags to 16-slot Traveler's Backpack
- Created revert script: `docs/KARAEZ_BAG_REVERT.sql`

---

## Session Notes Format

When adding new entries, use this format:

```markdown
## YYYY-MM-DD - Brief Title

### Features Implemented
- Feature 1
- Feature 2

### Bugs Fixed
- Bug 1

### Technical Notes
- Any important technical details

### Files Changed
- path/to/file1
- path/to/file2
```
