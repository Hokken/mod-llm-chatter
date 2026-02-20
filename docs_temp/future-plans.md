# mod-llm-chatter - Future Plans

This document tracks planned and completed enhancements for the mod-llm-chatter module.

---

## Completed (Implemented)

### Multi-Provider/Model Support
- Provider selection (Anthropic/OpenAI/Ollama) via config
- Direct model names (full API model IDs, no aliases)
- Ollama local model support with configurable context size

### Time-of-Day Context
- Time-of-day description injected into conversation prompts
- Day/night transition events trigger bot reactions

### Zone Flavor System
- Zone-specific flavor text for ~45 open-world zones and ~50 dungeons/raids
- Atmospheric descriptions inform LLM prompts for immersive context

### Clickable WoW Links
- Quest, item, spell, and NPC names converted to clickable in-game links
- Automatic link resolution from game database

### Roleplay Mode
- Dual mode system: normal (casual MMO chat) and roleplay (in-character)
- Separate tone, mood, and category pools for each mode
- 80+ message categories across both modes

### Race & Class Identity
- Race speech profiles with cultural flavor, speech traits, worldview, and lore
- Class personality modifiers shaping how each class speaks
- `build_race_class_context()` injects identity into all prompts
- Racial language vocabulary (lore-accurate phrases with translations, 15% RNG injection)

### Event System
- Weather change reactions (rain, snow, storms, sandstorms)
- Day/night transition reactions
- Transport arrival announcements (boats, zeppelins)
- Configurable per-event toggles and reaction chances

### Group Party Chat
- Bot greeting on join with personality traits (3 per bot)
- Welcome messages from existing group members
- Kill reactions (boss/rare/normal with different chances)
- Death reactions (bot reacts to groupmate or player dying)
- Loot reactions (quality-gated: green/blue/epic/legendary)
- Item links in loot reactions (clickable WoW item links)
- Combat engagement cries (elite/boss encounters)
- Spell cast reactions (heals, buffs, shields, CC, resurrects)
- Caster-perspective spell prompts (first-person for caster, third-person for observer)
- Quest objective completion reactions
- Quest turn-in reactions
- Level-up celebrations
- Achievement reactions
- Player message responses (bots respond to your party chat)
- Smart bot selection (name matching + LLM context fallback)
- Idle banter (periodic casual conversation during lulls)
- Multi-bot conversations (bots build on each other's messages)
- Persistent chat history per group session
- Account character bot support (not just random bots)
- Resurrection thanks (bot reacts after being rezzed, 100% chance)
- Zone transition comments (bot comments on entering a new zone)
- Dungeon entry reactions (bot reacts to entering a dungeon/raid)
- Group wipe reactions (bot reacts when entire party dies, replaces normal death event)
- Corpse run commentary (bot comments when anyone in group releases spirit, zone-aware)

### General Channel Reactions
- Bots react to player messages in General channel (zone-scoped)
- Question detection (100% chance for questions, 80% for statements)
- 30% chance of 2-bot conversation (one reacts, another follows up)
- Smart bot selection with name matching + LLM fallback
- Configurable quick_llm_analyze() utility for fast pre-processing
- Per-zone cooldown (15s default)

### Holiday System
- Holiday start/stop reactions (seasonal events)
- Holiday zone expansion (triggers in all zones, higher chance in cities)
- Capital city targeting with per-city cooldowns
- Recurring holiday chatter via periodic environment checks
- Holiday prompt enforcement (must mention festival by name)
- Capital city creature/loot query fix (no wrong mobs in cities)
- Holiday event strict filtering (excludes Call to Arms, fishing pools, building phases, fireworks)
- Minor game event support (Call to Arms, fishing, fireworks with separate RNG chance)

### Rate Limiting & Performance
- Per-bot speaker cooldowns
- Per-group event cooldowns (kill, death, loot, combat, spell, quest)
- Zone fatigue system
- Global message cap
- C++ rate limiters at hook level (before any DB work)
- Event expiration and deduplication
- Event expiration fix for long-delay events (accounts for reaction delay)
- Config-driven tuning for all RNG values (chances, cooldowns, intervals)
- Startup config display in bridge (prints all config on boot)
- Skip loot/trade messages in capital cities (no zone creatures to reference)
- Group chatter and general chat enabled by default in conf.dist
- Transport verified bots: C++ passes channel-verified GUIDs in extra_data, Python filters (Session 39)
- Single RNG gate for transport events: removed duplicate Python chance roll (Session 39)
- Transport cooldown tuned to 300s per route to match boat rotation timings (Session 39)
- Reactive bot state: C++ `BuildBotStateJson()` injects health/mana/role/target/combat state into 5 group handlers, Python converts to natural language prompt context. Replaces static CLASS_ROLE_MAP with PlayerbotAI talent-based role. State-triggered callouts for low HP/OOM/aggro (Session 41)
- API error context logging: `call_llm()` context parameter identifies dropped events by type across 31+ call sites (Session 41)
- Emote wrapping: LLM `*emotes*` preserved, bare narration wrapped in `*...*` with false-positive protection via `_NARRATION_FOLLOWERS` whitelist (Session 43, replaces Session 41 stripping)
- Quest completion team spirit: "we" language, turn-in NPC lookup via `creature_questender` (Session 43)
- Normal kill chance tuned: 20% → 10% (Session 43)
- Structured JSON action field: LLM returns `{"message", "emote", "action"}` JSON, action assembled as `*action* message` in chat, `LLMChatter.ActionChance` config (0-100%, default 10) gates all contexts, Phase 1/2 regex kept as fallback (Session 44)
- Full emote system expansion: 243 emotes from all TEXT_EMOTE_* values in 3.3.5a, SMSG_TEXT_EMOTE broadcasting for orange chat text + animation, dance special-cased to EMOTE_ONESHOT_DANCESPECIAL (Session 44b)
- Self-cast silence: bots no longer comment on self-casts, early return before both pre-cache and live LLM paths (Session 44b)
- Pre-cache spell gate fix: changed from isCasterReactor to isSelfCast check, caster buffing another player gets instant delivery (Session 44b)
- Composition comment player class: queries characters table for actual player class, CompositionCommentChance config key (default 10%) (Session 44b)
- Force-join bots to General channel: `EnsureBotInGeneralChannel()` auto-joins on zone change (Session 46)
- Account bot priority: account bots checked first in General channel candidate list, random bots fill remaining (Session 46)
- Event priority fix: `player_general_msg` bumped to priority 8, SQL sort fixed ASC→DESC (Session 46)
- Non-blocking main loop: pre-cache/idle/legacy offloaded to worker pool, thread safety for shared state, DB leak fix (Session 48)
- Config extraction: 8 hardcoded C++ values exposed as config variables — SpellCastCooldown, LowHealthThreshold, OOMThreshold, CombatStateCheckInterval, QuestDeduplicationWindow, MaxBotsPerZone, MaxMessageLength, GeneralChat.HistoryLimit (Session 48)
- Two-tier weather: `weather_change` alwaysFire (100%), new `weather_ambient` event with 120s cooldown for ongoing-weather remarks (Session 48b)
- Quest accept reactions: `AllCreatureScript::CanCreatureQuestAccept` hook, 100% chance, 30s dedup (Session 48b)
- Subzone discovery reactions: `OnPlayerGiveXP` with XPSOURCE_EXPLORE=3, 40% chance, 30s dedup (Session 48b)
- Spell classification expansion: HoTs, dispels, damage reduction, split damage, haste, mana regen + group-wide buff targeting via `HasAreaAuraEffect()` + self-cast bypass for area auras (Session 48b)
- Quest objective chance bumped to 100% (Session 48b)
- Quest prompt rewrites: accept="PREPARATION", objectives="PENDING TURN-IN", complete="TRANSACTION COMPLETE" — exclusive positive framing, no negation (Session 49)
- Quest description injection: C++ injects `quest_details` (200 chars) + `quest_objectives` (150 chars) into extra_data, Python surfaces in prompts. Bots know what the quest is about (Session 49)
- Weather cooldown reduced to 300s (5 min) from 1800s (30 min) (Session 49)
- Race/class ID resolution fix in quest accept handler — `int()` cast + name conversion (Session 49)
- Universal spell reactions: 2 new catch-all categories (`offensive` + `support`), all 8 categories with dedicated prompt branches, `spell_offensive` pre-cache, dynamic dual cache key (Session 50)
- Dynamic trigger chance scaling: spell cast and idle chatter chances divide by bot count in group — total output stays constant regardless of group size (Session 50)
- Achievement prompt fix: split into self-celebration vs congratulation perspectives, explicit "this is THEIR achievement" framing (Session 50)
- Punctuation cleanup: handles `", !"` → `"!"`, `", ."` → `"."`, trailing commas from empty placeholder substitution (Session 50)
- Weather cooldown bypass: `weather_change` events bypass QueueEvent() cooldown via `bypassEventCooldown` flag (Session 50)
- Race/class speech pool randomization: traits and class modifiers expanded from single strings to pools of 8 variants with `random.choice()`, flavor_words expanded to 12 per race with `random.sample()` subset, 6 direct `[:3]` injection sites also randomized. ~31,680 personality combinations per race/class pair (Session 51)
- General channel emote skip: all General channel prompt paths omit 244-emote list (saves ~200+ tokens per call), `pick_emote_for_statement()` fallback removed from all General paths, C++ emote delivery guarded behind `channel == "party"`. Three-layer protection: prompt, DB, C++ (Session 51)
- Conversation prompt refactor: `append_conversation_json_instruction()` shared helper in `chatter_shared.py` replaces ~150 lines of duplicated inline JSON/emote/action formatting across 6 conversation builders in `chatter_prompts.py` (Session 51)
- Architecture documentation: `docs/development/mod-llm-chatter-architecture.md` with file map, event dispatch, channel routing, data flow, refactoring candidates (Session 51)
- N1-N17 structural refactoring complete: `chatter_shared.py` decomposed into 3 leaf modules (`chatter_text.py`, `chatter_llm.py`, `chatter_db.py`), group domain split into 4 modules (`chatter_group.py`, `chatter_group_handlers.py`, `chatter_group_prompts.py`, `chatter_group_state.py`), ambient processing extracted to `chatter_ambient.py`. Architecture doc updated to reflect new structure (Session 51b)

---

## Planned Enhancements

### Future

- ~~**Emotes Between Bots**~~ (COMPLETED - Session 36, expanded Session 44b) - LLM-selected emotes for conversations, keyword-matched for statements. Session 44b: expanded to 243 emotes with SMSG_TEXT_EMOTE orange text broadcasting + animation lookup from sEmotesTextStore
- **Social Features** - Guild recruitment messages, trade channel integration
- ~~**Repetition Monitoring**~~ (COMPLETED - Session 39b) - Two-layer anti-repetition: prompt injection of recent zone messages + post-processing 4-gram rejection
- **Enemy Territory PvP Alert** - Bot yells when entering hostile faction territory with PvP flag active. Conditions: `IsPlayerBot(player)`, bot faction opposite to zone owner, bot entered enemy zone/area, `IsPvP()` flag on. Use `/yell` channel for dramatic effect. Personality-driven: warriors shout battle cries, rogues warn about danger, priests invoke protection
- **Trade Channel in Cities** - Route trade-type bot messages to Trade channel (channel 2) when in capital cities instead of General. Trade channel is active by default in WoW 3.3.5a cities. Cities should have significantly higher trade chat frequency (it was the social hub). Occasional trade messages outside cities are fine (authentic to the era) but much rarer
- ~~**Force-Join Bots to General Channel**~~ (COMPLETED - Session 46) - `EnsureBotInGeneralChannel()` auto-joins bots on zone change. Account bots prioritized over random bots in candidate list. `player_general_msg` priority bumped to 8. Event sort fixed (DESC).
- ~~**Parallel Event Processing**~~ (COMPLETED - Session 47) - ThreadPoolExecutor with `MaxConcurrent=3` workers, atomic CAS claiming, per-group serialization locks, thread-safe ZoneDataCache, lease-based stale cleanup. Python-only change.
- **[IMPORTANT] Player Message Conversations (Multi-Bot Replies)** - When a player speaks in party chat, currently only one bot replies with a single statement. Add a conversation variant: roll a config chance (`LLMChatter.GroupChatter.PlayerMsgConversationChance`, default ~30%) to trigger a multi-bot exchange instead. Multiple bots react in sequence, building on what the player said and each other's responses — like the existing general chat conversation pattern. Consistent with the statement/conversation duality used in general chat and idle chatter. A `ConversationBias`-style config controls the ratio. Makes groups feel much more alive and socially dynamic. Python-only change (prompt builder + handler logic).
- ~~**[IMPORTANT] Non-Blocking Main Loop (Full Worker Pool Offload)**~~ (COMPLETED - Session 48) - Pre-cache refill, idle chatter, and legacy requests all offloaded to ThreadPoolExecutor workers. Main loop is now a pure fast fetch-and-dispatch coordinator. Thread safety added for `_bot_mood_scores` (RLock) and `_last_idle_chatter` (Lock + inflight set). DB connection leak fixed.
- **Bot-Initiated Questions (Social Interest)** - Bots occasionally ask the player questions in party chat, making them feel interested in others rather than only commenting on themselves. Triggers: after events (kill, loot, zone change) or during idle moments. Examples: "You okay? That hit looked rough", "Have you been through here before?", "Where'd you learn to fight like that?". When the player responds, the system detects it's an answer to a bot's question and routes the reply to that bot with the original question as context, creating natural back-and-forth. Makes bots feel socially aware and genuinely curious about the player. Could use pre-caching pattern to have questions ready instantly.
- ~~**Subzone Discovery Reactions**~~ (COMPLETED - Session 48b) - Uses `OnPlayerGiveXP` with `xpSource == XPSOURCE_EXPLORE (3)`. 40% chance, 30s per-area dedup cooldown via `(groupId << 32) | areaId` composite key. Only areas with `area_level > 0`.
- **Quest Conversations (Group Discussion)** - Currently `bot_group_quest_complete` and `bot_group_quest_objectives` only trigger single-statement reactions. Add a conversation mode: after a quest completion or significant objective, roll a config chance to trigger a 2-3 bot conversation instead of a single reaction. Python processor would route to a conversation prompt builder (similar to idle conversation pattern) with quest context. Natural topics: "What's next?", debriefing the quest, discussing where to go, commenting on the quest NPC or story. Config: `LLMChatter.GroupChatter.QuestConversationChance` (default ~30%). Keeps single statements as default, conversations as occasional elevated moments.
- ~~**Quest Accept Reactions (Party Chat)**~~ (COMPLETED - Session 48b) - Uses `AllCreatureScript::CanCreatureQuestAccept` hook (no PlayerScript hook exists). 100% chance, 30s dedup per quest via `(groupId << 32) | questId` composite key. Python `build_quest_accept_reaction_prompt()` with acceptor is-bot "we" language.
- **Environmental Awareness (Nearby Scan)** - Snapshot notable nearby entities using AzerothCore's `WorldObject` scan APIs (`GetNearestCreature()`, `GetCreatureListWithEntryInGrid()`, `GetNearestGameObject()`, `GetGameObjectListWithEntryInGrid()`) and inject as context into chatter prompts. A bot standing near a blacksmith could comment on repairing gear, one near a moonwell could make a Kaldorei remark, one near a campfire could suggest resting. Scan radius ~40-80 yards, filter to notable types (vendors, trainers, quest NPCs, profession objects, landmarks). Run periodically or on idle banter trigger. Inject as "You are near [NPC/object]" in prompt. Makes idle banter and zone reactions grounded in actual surroundings rather than generic. Low LLM cost (context only, no extra calls). C++ scan + Python prompt enrichment.
- ~~**Rotating Personality Spices (Token Optimization + Variety)**~~ (COMPLETED - Session 47) - Replace the static personality/RP guidelines block with a "spice rack" system. Split prompt guidelines into two tiers: **core traits** (always sent: race, class role, name — the bot's identity) and **rotating spices** (pick 2-3 per call from a pool of 15-20). Spice examples: "You're distracted, thinking about something else", "You're feeling competitive with the group", "You find this situation absurdly funny", "You're homesick for your starting zone", "You're trying to impress someone in the group", "You just remembered something embarrassing". Each LLM call rolls a different combo, so the same bot responding to two kills in a row sounds completely different — not because the prompt told it to vary, but because the underlying personality emphasis shifted. With 15-20 spices picking 2-3, you get hundreds of combinations. Each spice is ~10-15 tokens, so you save tokens vs a long static personality block while getting more variety. Self-balancing chaos that makes bots feel unpredictably alive. Config: `LLMChatter.PersonalitySpiceCount` (how many spices per call, default 2-3). Python-only change.
- ~~**Pre-Cached Reactions (Instant Delivery)**~~ (IMPLEMENTED - Session 41b/42) - Pre-generated LLM responses stored in `llm_group_cached_responses` table, consumed instantly from C++ hooks via `TryConsumeCachedReaction()`. Covers 5 categories: `combat_pull`, `spell_support`, `state_low_health`, `state_oom`, `state_aggro_loss`. Python `refill_precache_pool()` replenishes on 30s interval. Placeholder resolution (`{target}`, `{caster}`, `{spell}`) in C++. Cache miss falls back to live LLM. Session 42 bugfixes: bot Item* access restored, loot reactor randomization, spell caster-as-reactor skip, quest dedup, multi-speaker truncation, OOM class filtering. Awaiting compilation + in-game verification.

---

---

## Player-Facing Parity/Superiority Roadmap (vs mod-ollama-chat)

The items below are prioritized for player-visible impact first, then long-term differentiation.

### 1) Full Direct Chat Coverage Across Common Channels (Parity, Highest Priority)
- **Player value:** bots feel socially present everywhere, not only ambient/general + party.
- **Target behavior:** support AI replies in `say`, `yell`, `party`, `raid`, `guild`, `officer`, `whisper`, and `channel`.
- **Implementation suggestion (current code):**
  - Extend `OnPlayerBeforeSendChatMessage` handling in `src/LLMChatterScript.cpp` (currently party-focused) to map all supported `CHAT_MSG_*` types into event payloads.
  - Reuse `llm_chatter_events` + `bot_group_player_msg` style flow; add channel metadata to `extra_data` and route delivery by channel type instead of only `party/general`.
  - Add config gates/chances per channel in `src/LLMChatterConfig.cpp` + `conf/mod_llm_chatter.conf.dist`.

### 2) Per-Channel Tuning + Safety Toggles (Parity)
- **Player value:** better spam control and server personality (RP server vs casual server).
- **Target behavior:** per-channel reply chance, per-channel disable toggles, optional whisper enable toggle.
- **Implementation suggestion (current code):**
  - Add new config keys and wire into `LLMChatterConfig` fields.
  - Check channel toggles/rates before queue insertion (cheapest point) in `LLMChatterScript.cpp`.
  - Keep existing global caps/cooldowns as second-level safety net.

### 3) Command/AddOn Prefix Blacklist for Incoming Chat (Partially Done)
- **Player value:** bots stop reacting to add-on chatter and bot/admin command strings.
- **Status:** Playerbot command filtering is implemented in Python (`_is_playerbot_command()` in `chatter_group.py`). Remaining work is a configurable prefix blacklist for addon strings.
- **Implementation suggestion (current code):**
  - Add `LLMChatter.Chat.BlacklistPrefixes` config list.
  - In the player chat hook path, short-circuit before DB insert when message begins with a blacklisted prefix.
  - Reuse existing message sanitation path (ALL_CAPS addon-style filter + link-only checks) and keep this as an extra, explicit guard.

### 4) Persistent Bot↔Player Memory Across Sessions (Parity)
- **Player value:** bots remember recent exchanges with specific players, making interactions feel personal.
- **Target behavior:** bounded history per bot-player pair, persisted in `characters` DB.
- **Implementation suggestion (current code):**
  - Introduce a new table (e.g. `llm_bot_player_chat_history`) separate from `llm_group_chat_history`.
  - On direct chat responses, write both player line + bot line similarly to existing group history writes.
  - Extend Python prompt builders (`tools/chatter_group.py` and/or shared prompt functions) to inject this history when the request context is player-targeted, with strict max-history limits.

### 5) Sentiment/Relationship System with Romantic Progression (Parity → Superiority, Major Player Impact)
- **Player value:** bots become warmer/colder based on player tone; creates long-term relationship feel. Opposite-sex bots can develop romantic interest — progressing from friendly to flirty to openly affectionate based on sustained positive interactions.
- **Target behavior:** persistent relationship score per bot-player pair AND per bot-bot pair within groups, with relationship stage progression.
- **Relationship stages (bot→player):**
  1. **Neutral** (score 0-20) — standard polite interaction
  2. **Friendly** (score 21-50) — warmer tone, remembers past conversations, slight preference for this player
  3. **Fond** (score 51-75) — compliments, inside jokes, seeks player's attention in group
  4. **Flirty** (score 76-90, opposite-sex only) — playful teasing, subtle compliments on appearance/skill, bashful moments
  5. **Smitten** (score 91-100, opposite-sex only) — openly affectionate, protective in combat, jealousy if player talks to other bots, love confessions
  - Same-sex track: stages 4-5 become "Close Friend" and "Best Friend" instead (or configurable for RP servers)
- **Bot-to-bot romance (group context):**
  - During idle group chatter, two opposite-sex bots may develop a flirty dynamic over time
  - Stored as bot-bot relationship score in DB, evolves through shared group experiences (kills, quests, idle chatter)
  - Prompt injection: "You have a growing crush on {other_bot}" → "You and {other_bot} have been flirting openly"
  - Other group members react: teasing ("Get a room"), wingman behavior, eye-rolling
  - Breakup potential: if one bot dies repeatedly or leaves group, score decays
- **Score drivers:**
  - Player talks to bot directly: +2-5 per interaction (quick LLM classify tone: compliment +5, neutral +2, rude -5)
  - Shared combat victory: +1
  - Bot heals/protects player or vice versa: +2
  - Player ignores bot for extended period: slow decay (-1/hour)
  - Bot death while grouped with player: +3 (trauma bonding)
- **Implementation suggestion:**
  - New table `llm_bot_relationships` with columns: `bot_guid`, `target_guid`, `target_type` (player/bot), `score` (INT), `stage` (ENUM), `last_interaction` (TIMESTAMP)
  - Python: classify player tone via `quick_llm_analyze()` on each direct interaction
  - Python: inject relationship stage description into prompt builders (all group prompts + player message responses)
  - Config: `LLMChatter.Relationships.Enable`, `RelationshipDecayRate`, `FlirtingEnable` (separate toggle), `BotBotRomanceEnable`, `BotBotRomanceChance`
  - Gender check: `extra_data` already carries bot gender from C++ (`getGender()`), player gender from `characters` table
- **Complexity:** Medium. Mostly Python prompt injection + new DB table. Score classification reuses existing `quick_llm_analyze()`. No new C++ hooks needed — piggybacks on existing interaction events.

### 6) Personality Packs + Live Admin Controls (Parity -> Better Operability)
- **Player value:** more varied bot personas, fast iteration by staff without restart.
- **Target behavior:** GM commands for personality list/get/set and live reload.
- **Implementation suggestion (current code):**
  - Add a `CommandScript` in C++ (parallel to existing script registration) for `.llmchatter` commands.
  - Store personality templates in a DB table; assign/persist per bot.
  - Reuse existing config reload hook (`OnAfterConfigLoad`) and add explicit reload command path for config + personality cache + bridge-visible flags.

### 7) Guild-Aware Chatter and Guild Event Reactions (Parity+)
- **Player value:** guild chat feels alive when real players are online.
- **Target behavior:** optional guild ambient comments and reactions to guild-relevant events.
- **Implementation suggestion (current code):**
  - Add guild-focused event types to `llm_chatter_events` + handlers in bridge.
  - Route output to guild channel in delivery layer (currently mainly party/general routing).
  - Apply strict chance/cooldown caps to prevent guild spam.

### 8) Multi-Provider Smart Routing (Superiority)
- **Player value:** higher quality where it matters without high cost everywhere.
- **Target behavior:** provider/model selection by chatter type (ambient vs direct reply vs event importance), with fallback chain.
- **Implementation suggestion (current code):**
  - Build on existing provider abstraction in `tools/chatter_shared.py`.
  - Add policy config (e.g. direct-chat model, ambient model, fallback provider) and implement failover on timeout/errors.
  - Keep token-cost logging already present and expose per-type usage.

### 9) World-Accurate Knowledge Injection from Live DB (Superiority)
- **Player value:** responses stay grounded in your actual world data, not generic lore-only answers.
- **Target behavior:** richer “current-world” retrieval for quests, loot, NPCs, zone state, group state.
- **Implementation suggestion (current code):**
  - Expand existing query helpers in `tools/chatter_shared.py` and prompt inputs in `tools/chatter_prompts.py`.
  - Add light relevance filtering by player question intent before selecting data snippets.
  - Keep snippets compact to avoid prompt bloat and repetition.

### 10) Player Personalization Controls (Superiority)
- **Player value:** players can tune bot behavior around them (verbosity, RP/casual preference, opt-out).
- **Target behavior:** per-player preferences applied during trigger and prompt generation.
- **Implementation suggestion (current code):**
  - Add a per-player preferences table and simple GM/player commands.
  - Check preferences in trigger selection before enqueuing requests.
  - Feed preferences into prompt constraints (length, tone, RP strictness).

### ~~11) Quality Layer: Anti-Repetition + Toxicity/Consistency Guards~~ (PARTIALLY COMPLETED - Session 39b)
- **Player value:** less spammy, more believable, safer chat quality.
- **Status:** Anti-repetition implemented. Toxicity/consistency guards remain as future work.
- **Completed:** Extend recent-message caches and DB checks (similar spirit to loot recent cooldown) to include phrase-level dedupe windows via two-layer approach: prompt injection of recent zone messages + post-processing 4-gram rejection.
- **Remaining:** Add bridge-side toxicity validator before insert into `llm_chatter_messages`. Fail closed with safe fallback line if validation fails.

### 12) PvP and Duel Reactions (Parity)
- **Player value:** bots react to PvP kills and duels, making open-world PvP and social dueling feel alive.
- **Target behavior:** bot comments after killing or being killed by another player; reactions to duel win/loss/request.
- **Implementation suggestion (current code):**
  - Hooks: `OnPVPKill(Player* killer, Player* victim)` for world PvP, `OnPlayerDuelEnd/OnPlayerDuelRequest` for duels.
  - Follow existing group event pattern: C++ inserts `bot_group_pvp_kill` / `bot_group_duel` events, Python builds prompts.
  - Personality-driven: warriors boast, healers express regret, rogues taunt.

### ~~13) Corpse Run Commentary~~ (COMPLETED)

### ~~14) Item Link Reactions~~ (COMPLETED - Session 36)
- Detects `|Hitem:` patterns in player party messages, queries acore_world for item stats, bot comments from class/role perspective with equip analysis.

### ~~15) Group Role Awareness~~ (COMPLETED - Session 40)
- `CLASS_ROLE_MAP` maps 10 classes to 6 roles, `ROLE_COMBAT_PERSPECTIVES` provides per-role combat perspective hints. Injected via `build_race_class_context()` into all RP-mode prompts. Combat-language guard prevents role talk in ambient prompts. Also added group composition commentary (50% chance on join, 8s delay).

### ~~16) Farewell Messages~~ (COMPLETED - Session 36)
- Pre-generated farewell stored in `llm_group_bot_traits.farewell_msg` on group join, delivered via WorldPacket in `OnRemoveMember()`. Gated behind `FarewellEnable` config.

### 17) Proximity-Based Social Chatter (Superiority, Major)
- **Player value:** bots feel spatially aware — they notice who's physically nearby and interact with them through `/say`, creating organic social encounters in the open world. Players walking past a group of bots might overhear them chatting, get addressed directly, and reply naturally.
- **Target behavior:** Periodic proximity scan (~40 yards via `GetDistance2d()`) detects nearby bots and real players around each bot. When a bot finds someone nearby, it can:
  1. **Bot-to-bot /say conversation** — two nearby bots chat in `/say`, visible to any player in range. Topics driven by zone, surroundings, current activity.
  2. **Bot-to-player /say interaction** — bot addresses a nearby real player directly ("Hey, you heading to the Crossroads too?" or "Watch your step, I saw murlocs up ahead"). Personality-driven: warriors are blunt, rogues are sly, priests are warm.
  3. **Player reply handling** — when a player responds in `/say`, the system detects it's a reply to the bot's message and routes it back to that bot with context, enabling natural back-and-forth (similar to group `player_msg` pattern but for `/say` channel).
  4. **Multi-turn potential** — a nearby bot could also chime in on the exchange, creating spontaneous 3-way conversations between bots and players.
- **Delivery channel:** `/say` (CHAT_MSG_SAY = 0), not General channel. This is spatially local — only players/bots within `/say` range (~40 yards) see it.
- **Implementation suggestion (current code):**
  - **C++ periodic scan:** New `CheckProximityChatter()` called on a configurable interval. For each bot, use `GetDistance2d()` to find nearby bots and real players. Queue a `proximity_say` event with extra_data containing: initiator bot info, nearby entity list (names, classes, races, whether player or bot), zone/subzone context.
  - **C++ delivery:** Add `/say` channel routing in the delivery system (currently only party and General). Bot sends `CHAT_MSG_SAY` via `WorldPacket`.
  - **C++ player reply detection:** In the existing `OnPlayerBeforeSendChatMessage` hook, detect `/say` messages from real players and check if a bot recently spoke in `/say` nearby. If so, queue a `proximity_say_reply` event with the bot's original message as context.
  - **Python prompt builders:** New `build_proximity_say_prompt()` for initiating conversation (context: who's nearby, zone, time of day, weather). New `build_proximity_reply_prompt()` for responding to player /say replies.
  - **Config:** `LLMChatter.ProximityChatter.Enable`, `ProximityChatter.CheckIntervalSeconds` (default 60), `ProximityChatter.Chance` (default 10-15%), `ProximityChatter.Range` (default 40 yards), `ProximityChatter.PlayerAddressChance` (chance to talk TO a player vs another bot), `ProximityChatter.Cooldown` (per-bot cooldown to prevent spam).
  - **Rate limiting:** Per-bot speaker cooldown, per-zone fatigue, global message cap all apply. Bots in the same area shouldn't all trigger at once — pick one initiator per scan cycle.
- **Complexity:** Medium-high. New delivery channel (/say), new player reply detection path, new proximity scan logic. But follows established event queue pattern. Recommend implementing in phases: Phase A (bot-to-bot /say), Phase B (bot-to-player /say), Phase C (player reply handling).

### ~~18) Session Mood Drift~~ (COMPLETED - Session 36)
- Per-bot mood score evolves based on events (kill +1, death -2, wipe -3, epic loot +2, etc.), maps to 7 mood labels, injected into all group prompts. 2-hour TTL eviction prevents memory leaks.

### ~~19) Racial Language Flavor~~ (COMPLETED)

### 20) Contextual Surroundings Awareness (Superiority, Unique)
- **Player value:** bots notice and comment on what's physically around them (a nearby vendor, a rare mob, opposing faction players, a scenic overlook). Creates a feeling of genuine spatial awareness.
- **Target behavior:** C++ periodically scans nearby objects/creatures and includes notable ones in event context.
- **Implementation suggestion (current code):**
  - In `TryTriggerChatter()` or a new periodic check, use `GetCreaturesInRange()` / `GetPlayersInRange()` to detect notable nearby entities.

### ~~21) Universal Spell Reaction with RNG Gate~~ (COMPLETED - Session 50)
- Extended spell classification with 2 new catch-all categories: `offensive` (negative + in-combat) and `support` (positive catch-all with group-member target check). All 8 categories have dedicated prompt branches. Pre-cache: `spell_offensive` + `spell_support`, offensive cache only for bot-caster. Dynamic trigger scaling: chance divided by bot count. `SpellCastChance = 10`, `PreCacheGeneratePerLoop = 3`.

### ~~22) Enhanced Pre-Cache Pool Management~~ (COMPLETED - Session 50)
- `PreCacheGeneratePerLoop` bumped 2→3 to cover 6th category (`spell_offensive`). `spell_offensive` added to `_CATEGORIES` list. Offensive pre-cache prompt uses `{target}` (optional) and `{spell}` placeholders. `canUseCache = false` for player-cast offensive (observer bots skip cache → live LLM).

---

### Suggested Delivery Phases
- **Phase A (fast parity wins):** 1, 2, 3, 16
- **Phase B (player stickiness):** 4, 5, 12, 14
- **Phase C (group depth):** 6, 7, ~~13~~, 15
- **Phase D (server identity / superiority):** 8, 9, 10, 11, 17, 18, ~~19~~, 20

### Notes for Current Architecture
- Keep the existing split: C++ for low-latency hooks, cooldown gates, and delivery; Python bridge for prompt logic and model orchestration.
- Prefer adding new behavior through `llm_chatter_events`/`llm_chatter_messages` patterns already used, rather than one-off direct sends, to preserve observability and rate controls.
- Item 18 (session mood) is a Python-only change requiring no compilation.
- Items 15 (role awareness) and 17 (proximity) are low-risk C++ changes that build on existing iteration logic.

---

*Last updated: 2026-02-19 (Session 51b)*
