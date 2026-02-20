# Current Progress

This file tracks the current state of development and any pending tasks.

**Last Updated**: 2026-02-19 (Session 52)

---

## Active Features

### mod-llm-guide (Azeroth Guide)
- **Status**: Fully functional with 29 game data tools, multi-turn context, all E2E tests passing
- **Provider**: Anthropic or OpenAI (configurable, both fully supported with tool calling)
- **Model**: Claude Haiku 4.5 (or GPT-4o-mini for OpenAI)
- **Bridge**: Running as Docker container (ac-llm-guide-bridge)
- **Git Repo**: `modules/mod-llm-guide/.git` (local, no remote yet)
- **E2E Tests**: 58/58 passing (100%)
- **Quest Lookup Fix (Session 35b)**: Multi-variant results (up to 5), faction tags, quest giver location, strengthened tool use instruction

Features working:
- `.ag <question>` command (renamed from `.ask` in Session 18)
- Character context (name, level, class, zone, quests, etc.)
- Conversation memory with summarization
- Sky blue label + response color scheme
- **Continuous polling** - Reliable response delivery (no race conditions)
- **Stale request cleanup** - Cancels old requests on server startup
- **Tool Use Architecture** - Claude calls 29 specialized database query tools:
  - **NPCs & Services**: `find_vendor`, `find_trainer`, `find_service_npc`, `find_npc`, `find_battlemaster`, `get_weapon_skill_trainer`
  - **Quests**: `get_quest_info`, `find_quest_giver`, `get_available_quests`, `get_class_quests`, `get_quest_chain`
  - **Spells**: `get_spell_info`, `list_spells_by_level`
  - **Items & Loot**: `get_item_info`, `find_item_upgrades`, `get_boss_loot`, `get_creature_loot`
  - **Creatures**: `find_creature`, `list_zone_creatures`, `find_hunter_pet`, `find_rare_spawn`
  - **Gathering**: `get_zone_fishing`, `get_zone_herbs`, `get_zone_mining`, `find_recipe_source`
  - **World**: `get_dungeon_info`, `get_flight_paths`, `get_zone_info`
  - **Reputation**: `get_reputation_info`
  - See `docs/mod-llm-guide/future-plans.md` for full tool inventory
- **Clickable Links** - Items, spells, quests converted to WoW hyperlinks
- **NPC Links** - NPC/creature names displayed in green
- **Markdown Stripping** - Removes **bold**/`*italic*` from responses
- **Multi-Turn Conversation Context** - Previous Q&A replayed as real message turns for pronoun resolution
- **Adaptive Response Length** - Short answers for simple questions, detailed for complex
- **Spell Names & Descriptions** - 49,839 spell names, 31,744 cleaned descriptions
- **E2E Test Suite** - Automated testing for all 29 tools
- **Zone Auto-Injection** - Tool calls automatically use player's current zone when not specified
- **Subzone Aliases** - Starting areas (Shadowglen, Coldridge Valley, etc.) map to parent zones
- **Rare Spawn Tool Fix** - Uses coordinate-based zone filtering for accurate results
- **OpenAI Tool Support** - Full function calling support for OpenAI provider (Session 20)
- **Zone Creatures/Herbs/Mining Fixes** - All use coordinate-based filtering (zoneId column unreliable)

### mod-llm-chatter (Ambient Bot Conversations)
- **Status**: ENABLED - Fully functional, transport and weather events working
- **Provider**: Anthropic (configurable: anthropic, openai, or ollama)
- **Model**: Haiku (configurable: haiku, sonnet, opus, gpt4o, gpt4o-mini, or Ollama model name)
- **Bridge**: Running as Docker container (ac-llm-chatter-bridge), v3.9
- **Git Repo**: `modules/mod-llm-chatter/.git` → https://github.com/Hokken/mod-llm-chatter.git

Features working:
- **ChatterMode** - `normal` (casual MMO chat) or `roleplay` (fully in-character with race/class personality, **default since Session 31**)
- **Multi-provider support** - Switch between Anthropic/OpenAI/Ollama via config
- **Simplified polling** - Always polls, no race conditions
- **Stricter placeholder prompts** - Better quest/item link generation
- Dynamic prompt building (random tone, mood, examples, guidelines)
- Mood sequences for conversations (each message follows scripted emotional arc)
- Zone mob queries from database (not LLM guessing)
- Class usability checks (AllowableClass bitmask)
- Quest and item links with proper WoW formatting
- **NPC Links** - Creature names in green when mentioned
- Weighted loot rarity (epics 3%)
- Overworld-only restriction (no chatter in dungeons)
- Party bot exclusion (grouped bots don't randomly chatter)
- Stale message cleanup on server startup
- Message type distribution: 50% plain, 15% quest, 12% loot, 8% quest+reward, 10% trade, 5% spell
- **Trade Messages** - WTS/WTB-style messages using zone loot items with item links
- Conversation vs statement: 50/50 split
- **Quest Deduplication** - Quest chains no longer over-represented in random selection
- **Bot Name Addressing** - Bots use each other's names when speaking directly in conversations
- **Fuzzy Name Matching** - Tolerates LLM typos in bot names (up to 2 character differences)
- **Loot Conversations** - Bots can discuss finding items with proper item links
- **Zone Flavor System** - Rich zone atmosphere descriptions (~45 zones) for immersive context
- **2-4 Bot Conversations** - Conversations now have 2-4 participants (50% 2-bot, 30% 3-bot, 20% 4-bot)
- **Varied Message Delays** - Delays now range naturally (12-30s) instead of fixed 8s
- **Weather Events** - Triggered by actual weather changes, zone-appropriate types (rain/snow/thunderstorm/sandstorm)
- **Zone-Filtered Loot** - Loot selection uses creature spawn coordinates (no more Kodo Leather in Teldrassil)
- **Transport Events** - Bots announce boat/zeppelin arrivals with destination info
- **CREATIVE_TWISTS System** - 50 normal + 18 RP random modifiers (30-40% chance) for unpredictable messages
- **Expanded TONES** - 23 normal + 22 RP tones for varied message personality
- **Expanded MESSAGE_CATEGORIES** - 80+ normal + 40 RP categories for varied statement topics
- **Prompt Logging** - Full prompt context logged before LLM calls (temporary, for tuning)
- **Weather Context Everywhere** - Weather passed to all prompts with guidance, LLM can reference naturally
- **Transport Direction Fix** - Boats correctly indicate where they go, zone-based origin/destination swap ensures correct direction regardless of travel path
- **Participant Enforcement** - 3+ bot conversations explicitly require every speaker to have at least one message (prevents LLM skipping participants)
- **Raw LLM Response Logging** - Full LLM response logged before parsing at all 3 conversation call sites for diagnostics
- **General Channel Pre-Check Filter** - `CanSpeakInGeneralChannel()` filters bot pool to only bots actually in the General channel before selecting conversation participants
- **Fail-Fast Delivery** - Messages always marked `delivered=1` immediately, LOG_WARN on failure, emotes gated on send success
- **Transport Verified Bots** - C++ collects channel-verified bot GUIDs in `CheckTransportZones()` and passes them in event extra_data; Python filters to only those bots, preventing LLM calls for bots that can't speak in General
- **Transport Single RNG Gate** - Removed duplicate Python-side transport chance roll; C++ handles the single 50% gate
- **Transport Cooldown Tuning** - Reduced per-route cooldown from 600s to 300s to match boat rotation timings
- **Grouped Bot Filtering (Events)** - Event-triggered chatter excludes bots grouped with real players
- **Randomized Environmental Context** - Time/weather randomly included (40%/30%/20%/10%) to reduce patterns
- **Em-Dash Fix** - Proper replacement with comma to avoid double-spacing
- **Emoji Removal** - Emojis stripped from output (don't render in WoW chat)
- **Roleplay Mode** - Race/class personality profiles (10 races, 10 classes), RP tones/moods/twists/categories, worldview context, lore facts (15% RNG)
- **Race/Class Speech Pools (Session 51)** - Traits and class modifiers expanded from single strings to pools of 8 variants each with `random.choice()`. Flavor words expanded to 12 per race with `random.sample()` subset of 3-4. Eliminates monotonous repetition when multiple bots share the same race/class (~31,680 personality combinations per race/class pair)
- **General Channel Emote Skip (Session 51)** - Emotes (SMSG_TEXT_EMOTE) are proximity-based, invisible to zone-wide General recipients. All General channel prompt paths omit the 244-emote list (saving ~200+ tokens per call). Three-layer protection: prompt (skip_emote=True / emote:null), DB (no emote stored), C++ (channel=="party" guard). `pick_emote_for_statement()` removed from all General paths
- **Conversation Prompt Refactor (Session 51)** - New `append_conversation_json_instruction()` shared helper replaces ~150 lines of duplicated inline JSON/emote/action formatting across 6 conversation builders in `chatter_prompts.py`. Future JSON format changes only need one edit
- **Humor Pool Enhancement (Session 52)** - Added 20 humor-oriented entries across all 6 creativity pools (TONES, MOODS, CREATIVE_TWISTS + RP variants). Humor frequency roughly doubled from ~10% to ~20%. Includes sarcasm, gallows humor, dry wit, self-deprecation, and absurdist comedy styles
- **Race/Class Text Conversion** - Numeric IDs properly converted to text names in all paths
- **Spell Messages** - Bots mention class-appropriate spells with clickable spell links
- **Group Chatter Stage 1** - Bots greet, react to kills (boss/rare/normal), react to deaths in party chat with personality traits
  - Greeting: tone/mood/twist system, RP race flavor, dedup prevention
  - Kill reactions: boss/rare (100% chance), normal mobs (20% chance), per-group cooldowns (30s boss/rare, 120s normal)
  - Death reactions: 40% chance, different bot reacts, 30s group cooldown for wipe protection
  - Startup cleanup: `llm_group_bot_traits` cleared on server restart
- **Group Chatter Stage 2** - Loot reactions and ambient idle party conversations
  - Loot reactions: quality-based chance (green=20%, blue=50%, epic+=100%), 60s per-group cooldown (epic+ bypasses cooldown)
  - Group roll rewards (need/greed) now trigger loot reactions via `OnPlayerGroupRollRewardItem`
  - Kill handler: real player kills now trigger bot reactions (random bot reacts)
  - Boss/rare kills bypass per-group kill cooldown entirely
  - Idle chatter: 50% single statement, 50% 2-bot conversation (2-4 messages)
  - 41 rich idle topics: environment, weather, class/race, lore, food/drink, travel, professions, gear, level progress, AFK humor (no items/quests/spells/trade)
  - 2-bot conversations use zone flavor, time of day, mood sequences, personality traits
  - Staggered message delivery with dynamic delays
  - Checks every 30s for active groups with no recent events (5min idle threshold, 5% chance, 3min cooldown)
  - 70% conversation / 30% single statement bias
  - Idle history capped at 5 messages to prevent echo chamber
  - Asterisk emotes stripped from LLM output
- **Group Chatter Stage 3** - Player interaction
  - Real player party chat detected via `OnPlayerBeforeSendChatMessage` hook
  - 100% chance a bot responds (15s per-group cooldown to prevent spam)
  - Bot replies contextually to what the player said, reflecting personality traits
- **Event Identity** - Quest complete, level-up, and achievement reactions correctly identify who did it (player or bot). Achievement prompt explicitly frames congratulation vs self-celebration (Session 50 fix)
- **Time-of-Day Always Passed** - Environmental time always included in prompts (was 60% RNG), prevents wrong time references
- **Config-Driven Group Chatter** - IdleChance, IdleCheckInterval, IdleCooldown, ConversationBias, IdleHistoryLimit + 9 RNG values all configurable
- **Spell Cast Reactions** - Bots react to ALL spell types in party (8 categories: heal, resurrect, shield, CC, dispel, buff, offensive, support)
  - Buff detection: Mark of the Wild, Blessing of Kings, resistance auras, attack power, regen, speed, haste (Bloodlust/Heroism), mana regen (Innervate)
  - Heal detection: direct heals + HoTs (Renew, Rejuvenation, Regrowth, Riptide, Earth Shield)
  - Dispel detection: Cleanse, Dispel Magic, Remove Curse, Abolish Poison
  - Shield detection: absorbs, immunity, damage reduction (Pain Suppression), split damage (Hand of Sacrifice)
  - **Offensive detection (Session 50)**: any negative spell while in combat (Fireball, Frostbolt, Flame Shock, etc.)
  - **Support catch-all (Session 50)**: positive spells not matching specific categories, with group-member target validation
  - Group-wide buffs: Prayer of Fortitude, Gift of the Wild, Greater Blessings, Bloodlust detected via `HasAreaAuraEffect()`
  - Caster-as-reactor: bot who casts the spell speaks about it (first-person perspective, mentions target by name)
  - Observer path: when real player casts, random bot reacts as observer
  - **Dynamic trigger scaling (Session 50)**: chance divided by number of bots in group (10% config / 5 bots = 2% each)
  - Pre-cache: `spell_support` + `spell_offensive` categories, offensive cache only for bot-caster (player-cast offensive → live LLM)
  - 10% base trigger chance (SpellCastChance), 10s per-group cooldown
- **Quest Objectives Completion** - Bot reacts when quest objectives are done (before turn-in), 100% chance, 30s cooldown
  - Uses `OnPlayerBeforeQuestComplete` hook (fires when objectives complete, not at NPC turn-in)
- **Holiday City Targeting** - Holiday events now target capital cities where real players are (not random zones). `QueueHolidayForCities()` shared by OnStart/OnStop/startup/periodic check
- **Recurring Holiday Chatter** - `CheckActiveHolidays()` runs during environment check, queues holiday events per capital city with per-city cooldowns
- **Capital City Mob/Loot Fix** - `CAPITAL_CITY_ZONES` set prevents wrong creatures/loot from appearing in city prompts
- **Holiday Prompt Enforcement** - Holiday events explicitly require mentioning the event by name (uses "event" not "festival" to avoid mischaracterizing PvP Call to Arms as celebrations)
- **Full Config Exposure** - 8 additional hardcoded values moved to config: EnvironmentCheckSeconds, WeatherCooldownSeconds, DayNightCooldownSeconds, HolidayCooldownSeconds, HolidayCityChance, TransportCheckSeconds, GroupQuestObjectiveChance, GroupSpellCastChance
- **Account Character Bot Support** - Works with both random bots and player's own account characters used as bots
  - Fixed `DeliverPendingMessages()` to use `ObjectAccessor::FindPlayer()` instead of `RandomPlayerbotMgr` only
- **Holiday Zone Expansion** - Holiday events trigger in all zones with real players (cities get higher chance, open-world zones get lower chance)
- **Event Expiration Fix** - `expires_at` accounts for reaction delay so events don't expire before firing
- **Item Links in Loot Reactions** - Loot reaction messages convert item names to clickable WoW item links
- **Playerbot Command Filter** - "do attack my target" added as exact match, "summon" confirmed filtered
- **Startup Config Display** - Bridge prints all config values (chatter, transport, holiday, group chatter) on startup
- **Non-Blocking Main Loop (Session 48)** - Pre-cache refill, idle chatter, and legacy requests all run in ThreadPoolExecutor worker threads. Main loop is a pure fast fetch-and-dispatch coordinator. Thread safety for `_bot_mood_scores` (RLock) and `_last_idle_chatter` (Lock + inflight set). DB connection leak fixed in main loop and startup.
- **Config Extraction (Session 48, compiled Session 49)** - 8 hardcoded values extracted to config: SpellCastCooldown, LowHealthThreshold, OOMThreshold, CombatStateCheckInterval, QuestDeduplicationWindow, MaxBotsPerZone, MaxMessageLength, GeneralChat.HistoryLimit. SpellCastChance bumped to 40%.
- **Two-Tier Weather System (Session 48b, compiled Session 49)** - `weather_change` always fires 100% (alwaysFire flag), new `weather_ambient` event for periodic ongoing-weather remarks between transitions (120s cooldown, 15% EventReactionChance). WeatherCooldownSeconds reduced to 300s (5 min).
- **Quest Accept Reactions (Session 48b, compiled Session 49)** - Bots react in party chat when a quest is accepted. Uses `AllCreatureScript::CanCreatureQuestAccept` hook. 100% chance, 30s per-quest dedup cooldown.
- **Subzone Discovery Reactions (Session 48b, compiled Session 49)** - Bots react when "Discovered: X" fires. Uses `OnPlayerGiveXP` with `xpSource == XPSOURCE_EXPLORE (3)`. 40% chance, 30s per-area dedup cooldown.
- **Spell Classification Expansion (Session 48b, compiled Session 49)** - HoTs (PERIODIC_HEAL), dispels (SPELL_EFFECT_DISPEL), damage reduction (MOD_DAMAGE_PERCENT_TAKEN), split damage (SPLIT_DAMAGE_PCT/FLAT), haste (MOD_MELEE_HASTE, HASTE_SPELLS), mana regen (MOD_POWER_REGEN_PERCENT). Group-wide buff targeting via `HasAreaAuraEffect()`. Self-cast bypass for area aura buffs. Target name = "the group" for area auras.
- **Quest Prompt Rewrites (Session 49)** - All 3 quest prompts rewritten with exclusive positive framing: accept="PREPARATION", objectives="PENDING TURN-IN", complete="TRANSACTION COMPLETE". Eliminates wrong-tense/completion language for non-complete quest stages.
- **Quest Description Injection (Session 49, compiled)** - C++ injects `quest_details` (200 chars) and `quest_objectives` (150 chars) from `Quest` object into extra_data JSON for all 3 quest hooks. Python surfaces in LLM prompts. Bots now know what the quest is actually about.
- **Resurrection Thanks** - Bot reacts with gratitude/relief after being rezzed in party chat (100% chance, 30s cooldown)
- **Zone Transition Comments** - Bot comments when entering a new zone with atmospheric flavor (100% chance, 120s cooldown)
  - Confirmed working in-game (Session 34)
- **Dungeon Entry Reactions** - Bot reacts when entering a dungeon/raid with context from dungeon flavor and boss info (100% chance, 300s cooldown)
- **Group Wipe Reactions** - Bot reacts when entire party dies with personality-appropriate humor/frustration (100% chance, 120s cooldown)
  - Wipe detection: checks if ALL group members dead, fires BEFORE death cooldown/RNG to avoid suppression
  - Wipe event replaces normal death event (no double messages)
- **General Channel Reactions** - Bots react to player messages in General channel with statements or conversations (zone-scoped, per-zone cooldown)
  - Question detection: messages ending with `?` get 100% reaction chance, non-questions get 80%
  - 30% chance of 2-bot conversation (one reacts to player, another follows up)
  - 15s per-zone cooldown, configurable via GeneralChat config section
  - Account bots prioritized over random bots in candidate list (Session 46)
  - `player_general_msg` priority bumped to 8 (highest regular event)
  - Event processing order fixed: `ORDER BY priority DESC` (was ASC)
- **Smart Bot Selection** - When player addresses a bot by name (General or party chat), that specific bot responds instead of random
  - 3-pass matching: exact name → fuzzy edit distance (2 chars tolerance) → LLM context analysis
  - `quick_llm_analyze()` reusable utility for fast Haiku pre-processing calls
  - Works in both General channel and party chat
- **Racial Language Vocabulary** - All 10 races have lore-accurate native language phrases (Thalassian, Darnassian, Orcish, etc.)
  - 15% chance per prompt to inject a vocabulary phrase with soft usage instruction
  - All phrases verified as WotLK-era canonical (no post-3.3.5a content)
- **Capital City Loot/Trade Skip** - Loot and trade messages suppressed in capital cities (quest messages preserved)
  - Prevents immersion-breaking loot/trade messages in areas without hostile mobs
- **Corpse Run Reactions** - Bot reacts in party chat when anyone dies and releases spirit (80% chance, 120s cooldown)
  - Triggers for both bot AND player deaths — bot shows concern when player dies, comments on own ghost run when bot dies
- **Player Death Reactions** - Bots react when the real player is killed by a creature (uses existing death handler, extended to include player)
  - Wipe detection also now works when the player is the last to die
- **Greeting Name Personalization** - In 2-person groups (player + bot), bot addresses player by name 80% of the time
- **Proportional Response Rule** - LLM instructed to keep responses proportional to input (short answer for "bye", detailed for complex questions)
- **Name Addressing in Conversations** - 40% chance bots address someone by name in party/general chat (player or other bots)
- **"Festival" → "Event" Fix** - Holiday prompts use neutral "event" wording to handle PvP Call to Arms correctly
- **Full Emote System** - Bots play WoW emote animations AND show orange chat text (e.g. "Sytarre smiles.") via `SMSG_TEXT_EMOTE` broadcasting. ~243 emotes from all `TEXT_EMOTE_*` values in 3.3.5a. LLM-selected for conversations, keyword-matched for statements
- **Chat History Limit Config** - `LLMChatter.ChatHistoryLimit` controls how many recent messages included in LLM prompts (default 10, was hardcoded 15). Applies to group party chat and General channel. Validated/clamped 1-50.
- **Session Mood Drift** - Per-bot mood evolves based on events (kill/death/loot/wipe), injected into prompts, 7 mood levels from miserable to ecstatic
- **Farewell Messages** - Pre-generated goodbye delivered via WorldPacket when bots leave group (gated behind FarewellEnable config)
- **Item Link Reactions** - Bots comment on items linked in party chat with class-aware equip analysis and weapon/armor subclass detail
- **Holiday Event Fix** - IsHolidayEvent() now strictly filters real holidays, excluding Call to Arms BG rotations, Darkmoon setup phases, fishing pools, and fireworks events
- **Minor Game Events** - New IsMinorGameEvent() for occasional Call to Arms/fishing/fireworks mentions with separate RNG chance (20%) and config toggle
- **Anti-Repetition System** - Two-layer system: prompt injection (recent zone messages fed to LLM with "DO NOT repeat") + post-processing n-gram rejection (shared 4-grams trigger silent drop)
- **Backslash Escape Fix** - SQL/JSON escape characters no longer leak into player-visible chat (Nature\'s -> Nature's)
- **Non-Asterisk Emote Stripping** - LLM action descriptions without asterisks (gazes, leans, nods, etc.) stripped from output
- **First-Person Prompt Enforcement** - RP mode prompts explicitly require first-person voice; narrator-style reactions ("gazes at", "adjusts pack") eliminated via guideline + rewritten style options
- **Log Level Cleanup** - Success output logs demoted from WARNING to INFO in group chatter handlers
- **Group Role Awareness** - Combat role perspective injected into all RP-mode prompts via `CLASS_ROLE_MAP` + `ROLE_COMBAT_PERSPECTIVES`. Tanks talk about aggro, healers about health bars, DPS about damage. Combat-language guard prevents role talk in ambient prompts.
- **Group Composition Commentary** - Bots comment on group composition after joining (10% chance via config, 8s delay, 2+ bots required). Notes missing tank/healer, includes player's class. `LLMChatter.GroupChatter.CompositionCommentChance` config key.
- **Reactive Bot State** - C++ `BuildBotStateJson()` injects real-time health%, mana%, role, combat target, AI state into 5 group event handlers. Python `build_bot_state_context()` converts to natural language prompt context. Replaces static CLASS_ROLE_MAP with PlayerbotAI talent-based role detection. State-triggered callouts for low HP/OOM/aggro.
- **API Error Context Logging** - `call_llm()` context parameter identifies what event type was lost on API errors (31+ call sites labeled across 4 files)
- **Emote Wrapping** - LLM `*emotes*` preserved in chat, bare narration wrapped in `*...*` instead of stripped. Phase 1 (leading narration) requires verb + narration follower word for false-positive safety. Phase 2 (mid-message) wraps after punctuation. RP prompt guideline allows 20% emote prefixes (2-4 words).
- **Quest Completion Team Spirit** - Quest reactions use "we" language, not individual names. Turn-in NPC name looked up from `creature_questender` and injected as friendly context (prevents LLM hallucinating kills on quest givers).
- **Normal Kill Chance Tuned** - `KillChanceNormal` reduced from 20% to 10% (boss/rare unchanged at 100%)
- **Structured JSON Action Field (Session 44)** - LLM returns `{"message", "emote", "action"}` JSON instead of plain text. Action assembled as `*action* message` in chat. `LLMChatter.ActionChance` config (0-100%, default 10) gates all contexts. Phase 1/2 regex kept as fallback for plain-text responses. All 38 prompt builders and 33 handler sites converted.
- **Pre-Cached Reactions (Session 41b/42)** - Background LLM pre-generates responses for predictable combat events, stored in `llm_group_cached_responses` table, consumed instantly from C++ via `TryConsumeCachedReaction()`. 5 categories: combat_pull, spell_support, state_low_health, state_oom, state_aggro_loss. Placeholder resolution ({target}, {caster}, {spell}) in C++. Cache miss falls back to live LLM. Python `refill_precache_pool()` replenishes on 30s interval. 10 new config variables for depth, TTL, and toggles.
- **Loot Reactor Randomization (Session 42)** - 50% self-react, 50% groupmate reacts. `looter_name` field distinguishes who looted vs who speaks. Prompt enforces correct perspective.
- **Quest Completion Dedup (Session 42)** - 30s dedup window per group+quest prevents multiple reactions when all bots complete same quest simultaneously.
- **Multi-Speaker Truncation (Session 42)** - Regex detects and truncates LLM artifacts where multiple speakers appear in single response.
- **OOM Class Filtering (Session 42)** - Pre-cache skips state_oom for Warriors, Rogues, Death Knights (non-mana classes).
- **Self-Cast Silence (Session 44b)** - Bots no longer comment on their own self-casts (e.g. PW:Shield on self). Early `return` before both pre-cache and live LLM paths.
- **Spell Pre-Cache Gate Fix (Session 44b)** - Changed from `isCasterReactor` to `isSelfCast` check. Caster buffing another player now gets instant pre-cached delivery instead of being blocked.

Configuration (mod_llm_chatter.conf):
- ChatterMode: roleplay (default, or normal)
- Provider: anthropic (or openai, ollama)
- Model: haiku (aliases: haiku, sonnet, opus, gpt4o, gpt4o-mini, or Ollama model name)
- QuickAnalyze.Provider: anthropic (for smart bot selection — independent of main provider)
- QuickAnalyze.Model: haiku (for fast pre-processing LLM calls)
- FarewellEnable: 1 (enable farewell messages on group leave)
- TriggerIntervalSeconds: 50
- TriggerChance: 10%
- ConversationChance: 50%
- MessageDelayMin: 1000ms
- MessageDelayMax: 45000ms
- MaxTokens: 350 (conversations: 700)
- TransportEventChance: 35% (C++ only, single gate)
- TransportCooldownSeconds: 300 (per route+zone)

---

## Pending Tasks

### mod-llm-bots (AI-Powered Bot Conversations)
- **Status**: Planning complete, implementation not started
- **Goal**: Natural language conversations with playerbots using Claude Haiku
- **Documentation**: `docs/mod-llm-bots/implementation-plan.md`

Key features planned:
- Whisper to bots naturally ("Hey, can you heal the tank?")
- Bots have unique personalities based on race/class
- Natural language → bot command translation
- Context-aware responses (remembers recent chat)
- Bot-to-bot conversations (future)

---

## Known Issues

**OnPlayerLootItem USE-AFTER-FREE (Sessions 26-28) — RESOLVED (Session 42):**
- Original crash: playerbots `HandleBotPackets` → `StoreLootItem` delivers corrupted Item*
- Session 27b fix: two-tier loot handler skipping Item* for all bots (quality=255)
- **Session 42 update**: `GroupHasRealPlayer()` filter already eliminates the crash vector (random-bot-only groups). Bots in player's group have valid Item* (StoreLootItem just stored it, hook fires synchronously). Bot Item* access restored with null checks — proper item names and quality filtering now work for bot loot.
- **Hypothesis**: If crashes recur, the bot-only-group filter may need tightening. Monitor for segfaults in `HandleGroupLootEvent`.
- **Investigation doc**: `docs/mod-llm-chatter/bot-loot-item-crash-investigation.md`

**Debug Tooling Status (cleaned up Session 39b):**
- GDB crash catcher: REMOVED from start-dev-servers.sh
- [TRACE] C++ logging: REMOVED from all group handlers
- Python WARNING promotions: REVERTED — remaining logger.warning() calls are legitimate error/skip conditions
- Log rotation to persistent `env/dist/logs/`: KEPT (useful)
- `EnableVerboseLogging` config key: exists in conf.dist but not wired to actual log control (low priority)

**Docker Timestamp Sync Issue:**
- Windows file edits don't update timestamps inside Docker container
- `make` doesn't detect changes without touching files first
- **Always use manual compilation workflow** (see CLAUDE.md or dev-server-guide.md)

---

## Future Enhancements (Not Started)

### mod-llm-guide
- [x] Tool use architecture (completed 2026-01-29)
- [x] Boss loot tool with clickable item links (completed 2026-01-29)
- [x] NPC/creature links in green (completed 2026-01-29)
- [x] Gathering tools: fishing, herbs, mining (completed 2026-01-30)
- [x] Rare spawn tool (completed 2026-01-31)
- [x] Zone info tool (completed 2026-01-31)
- [x] Battlemaster tool (completed 2026-01-31)
- [x] Weapon skill trainer tool (completed 2026-01-31)
- [x] Class quests tool (completed 2026-01-31)
- [x] Quest chain tool (completed 2026-01-31)
- [x] Reputation info tool (completed 2026-01-31)
- [x] Module rename mod-llm-chat → mod-llm-guide (completed 2026-02-02)
- [x] Spell tools database queries (completed 2026-02-02)
- [x] Dungeon info database queries (completed 2026-02-02)
- [ ] One-click install script for non-technical users
- [ ] Pre-built binaries to avoid recompilation
- [ ] `/llm history` command to view past conversations
- [ ] Whisper mode for private responses
- [ ] Connect EnableVerboseLogging to conditional logging
- [ ] See `docs/mod-llm-guide/future-plans.md` for remaining planned tools

### mod-llm-chatter
- [x] Bot name addressing in conversations (completed 2026-01-30)
- [x] Fuzzy name matching for LLM typos (completed 2026-01-30)
- [x] Loot conversation type (completed 2026-01-30)
- [x] Zone flavor system for immersive context (completed 2026-01-30)
- [x] 2-4 bot conversations (completed 2026-01-30)
- [x] Varied message delays (completed 2026-01-30)
- [x] Transport arrival chatter (completed 2026-02-04)
- [x] Weather event chatter (completed 2026-02-05)
- [x] Zone-appropriate weather types (completed 2026-02-05)
- [x] CREATIVE_TWISTS system for unpredictability (completed 2026-02-05)
- [x] Expanded MESSAGE_CATEGORIES (80+) (completed 2026-02-05)
- [x] Weather context in all prompts (completed 2026-02-05)
- [x] EnableVerboseLogging config option (completed 2026-02-05)
- [x] ChatterMode: normal/roleplay toggle (completed 2026-02-07)
- [x] Race/class personality system for RP mode (completed 2026-02-07)
- [x] Race worldview + lore context for RP mode (completed 2026-02-09)
- [x] Enriched CLASS_SPEECH_MODIFIERS (completed 2026-02-09)
- [x] Race/class speech pool randomization — traits/modifiers as 8-variant pools, flavor_words expanded to 12 with random subset (completed 2026-02-19)
- [x] General channel emote skip — all General paths omit emote list, three-layer protection (completed 2026-02-19)
- [x] Conversation prompt refactor — `append_conversation_json_instruction()` shared helper (completed 2026-02-19)
- [x] Default ChatterMode switched to roleplay (completed 2026-02-09)
- [x] Idle banter frequency tuning (completed 2026-02-09)
- [x] SQL escaping fix for level-up/quest/achievement hooks (completed 2026-02-09)
- [x] Event identity fix - completer/leveler/achiever name in extra_data (completed 2026-02-09)
- [x] Time-of-day always passed to LLM prompts (completed 2026-02-09)
- [x] Config abstraction for group chatter tuning values (completed 2026-02-09)
- [x] Spell cast reactions with buff detection (completed 2026-02-10)
- [x] Quest objectives completion hook (completed 2026-02-10)
- [x] Caster-perspective spell prompts (completed 2026-02-10)
- [x] Full config exposure of all hardcoded RNG values (completed 2026-02-10)
- [x] Account character bot support in message delivery (completed 2026-02-10)
- [x] Fixed numeric race/class ID bug in prompt builders (completed 2026-02-07)
- [x] Modularized bridge into 5 files: constants, shared, prompts, events, bridge (completed 2026-02-07)
- [x] Trade message type - WTS/WTB item messages (completed 2026-02-07)
- [ ] Connect EnableVerboseLogging to conditional logging
- [x] Emotes between bots (completed 2026-02-13)
- [x] Responding to real player chat (Stage 3, Session 25)
- [x] Time-of-day aware messages (completed 2026-02-09)
- [x] Trade channel integration (completed 2026-02-07)
- [x] Resurrection thanks — bot reacts after being rezzed (completed 2026-02-12)
- [x] Zone transition comments — bot comments when entering a new zone (completed 2026-02-12, confirmed working)
- [x] Dungeon entry reactions — bot reacts when entering an instance (completed 2026-02-12)
- [x] Group wipe reactions — bot reacts when entire party dies (completed 2026-02-12)
- [x] Seasonal/event-based chatter (completed 2026-02-11)
- [x] Holiday event city targeting fix (completed 2026-02-11)
- [x] Capital city creature/loot query fix (completed 2026-02-11)
- [x] Recurring holiday chatter in cities (completed 2026-02-11)
- [x] Full config exposure of all hardcoded event values (completed 2026-02-11)
- [x] Holiday zone expansion - events trigger in all zones (completed 2026-02-12)
- [x] Event expiration fix for long-delay events (completed 2026-02-12)
- [x] Item links in loot reactions (completed 2026-02-12)
- [x] Startup config display in bridge (completed 2026-02-12)
- [x] General channel player message reactions (completed 2026-02-12)
- [x] Smart bot selection — name matching + LLM context fallback (completed 2026-02-12)
- [x] Reusable quick_llm_analyze() utility for pre-processing (completed 2026-02-12)
- [x] Racial language vocabulary for all 10 races (completed 2026-02-13)
- [x] Capital city loot/trade message skip (completed 2026-02-13)
- [x] Corpse run reactions in party chat (completed 2026-02-13)
- [x] Greeting name personalization for 2-person groups (completed 2026-02-13)
- [x] Proportional response rule for party/general chat (completed 2026-02-13)
- [x] Name addressing in conversations — 40% RNG (completed 2026-02-13)
- [x] "Festival" → "event" holiday prompt fix (completed 2026-02-13)
- [ ] Guild recruitment messages
- [x] Anti-repetition guards -- prompt injection + n-gram rejection (completed 2026-02-14)
- [x] Holiday event fix -- strict IsHolidayEvent filtering (completed 2026-02-14)
- [x] Minor game event support (completed 2026-02-14)
- [x] Farewell messages when bots leave group — WorldPacket bypass (completed 2026-02-13)
- [x] Participant enforcement for 3+ bot conversations (completed 2026-02-14)
- [x] Raw LLM response logging at all parse sites (completed 2026-02-14)
- [x] Transport direction fix — zone-based origin/destination swap (completed 2026-02-14)
- [x] General channel pre-check filter — `CanSpeakInGeneralChannel()` + fail-fast delivery (compiled Session 39)
- [x] Locale fix — `area_name[sWorld->GetDefaultDbcLocale()]` instead of `area_name[0]` (compiled Session 39)
- [x] Transport verified bots — C++ passes channel-verified GUIDs, Python filters (compiled Session 39)
- [x] Transport single RNG gate — removed Python duplicate chance roll (Session 39)
- [x] Transport cooldown tuning — 600s → 300s per route (Session 39)
- [x] Group role awareness — CLASS_ROLE_MAP + ROLE_COMBAT_PERSPECTIVES in all RP prompts (Session 40)
- [x] Group composition commentary — bots comment on group comp after joining (Session 40)
- [ ] Mood-aware idle topics — topic selection weighted by bot mood state
- [ ] Delivery ORDER BY sequence — C++ delivery query needs `ORDER BY deliver_at, sequence, id`
- [x] Reactive bot state integration — C++ BuildBotStateJson() + Python prompt injection (Session 41, awaiting compilation)
- [x] Pre-cached reactions — 5 categories (combat_pull, spell_support, state_low_health, state_oom, state_aggro_loss), C++ TryConsumeCachedReaction + Python refill_precache_pool (Session 41b/42, awaiting compilation)
- [ ] Bot-initiated questions — bots ask player questions, creating two-way conversation
- [x] Force-join bots to General channel — EnsureBotInGeneralChannel() auto-joins on zone change (completed 2026-02-17, Session 46)
- [x] Parallel event processing — ThreadPoolExecutor with MaxConcurrent=3, plan reviewed by Gemini 3 Pro (completed Session 47)
- [x] Non-blocking main loop — pre-cache/idle/legacy offloaded to worker pool (completed Session 48)
- [x] Structured JSON action field — `{"message", "emote", "action"}` format replaces regex narration heuristic (completed 2026-02-16, Session 44)
- [x] Full emote system expansion — 243 emotes with SMSG_TEXT_EMOTE orange text broadcasting (completed 2026-02-16, Session 44b)
- [x] Chat history limit config — `LLMChatter.ChatHistoryLimit` with validation/clamping (completed 2026-02-16, Session 45)
- [x] Rotating personality spices — 96 normal + 96 RP spices, pick 2 per call, recency deque (completed 2026-02-17)
- [x] Narrator actions gated to RP mode only (completed 2026-02-17)
- [x] Quest accept reactions — `AllCreatureScript::CanCreatureQuestAccept` hook + Python handler (completed 2026-02-17, Session 48b)
- [x] Subzone discovery reactions — `OnPlayerGiveXP` XPSOURCE_EXPLORE + Python handler (completed 2026-02-17, Session 48b)
- [x] Spell classification expansion — HoTs, dispels, damage reduction, haste, mana regen, group buffs (completed 2026-02-17, Session 48b)
- [x] Weather ambient system — ongoing-weather remarks between transitions (completed 2026-02-17, Session 48b)
- [ ] Bot reacts to player emotes — `OnPlayerEmote` C++ hook + Python handler (C++ + Python)
- [ ] Quest link enrichment — parse `|Hquest:ID|` from player messages, inject quest description into prompt (Python only)

### mod-llm-bots (Planned)
- [ ] Phase 1: Basic whisper conversations
- [ ] Phase 2: Personality system
- [ ] Phase 3: Context & history
- [ ] Phase 4: Command parsing
- [ ] Phase 5: Party/guild chat
- [ ] Phase 6: Polish & testing

---

## Server Status

- **Dev Server**: Running via Docker (`docker compose --profile dev`)
- **Database**: ac-database (MySQL)
- **LLM Bridge (guide)**: ac-llm-guide-bridge
- **LLM Bridge (chatter)**: ac-llm-chatter-bridge

---

## Notes for Next Session

- **Session 52 — Humor Pools + RFC QA Testing**
  - Added 20 humor entries to 6 creativity pools in `chatter_constants.py` — Python-only, bridge restarted
  - RFC dungeon run verified all group chatter features: kills, boss kills (2/3), loot, spells, mood progression
  - Taragaman boss kill one-off miss — investigated, not a code regression (latency spike)
  - Low health pre-cache cached but never consumed (RFC too easy)
  - **Uncommitted C++ fixes still pending**: `std::string("state:")` at LLMChatterScript.cpp:6280 + channel=="party" emote guard — include in next compilation batch
  - **Review docs recommended for deletion**: `docs/reviews/` contains stale review files from completed work — user not yet confirmed

- **Session 51 — Speech Pools + Emote Skip + Prompt Refactor — DEPLOYED**
  - Python changes all deployed (bridge restarted), committed to mod-llm-chatter `196b7b8`
  - C++ change (channel=="party" emote guard) needs compilation — belt-and-suspenders, Python sufficient alone
  - Boss detection confirmed working by user
  - **Monitor**: response diversity with same-race/class bots — should see varied personality angles
  - **Monitor**: no "the wilds" repetition in Night Elf / Druid prompts
  - **Monitor**: General channel messages should have NO orange emote text
  - **Monitor**: Party chat emotes should still work normally
  - **Hypothesis**: per-bot personality persistence not implemented — same bot may get different trait variants across prompts. If this feels inconsistent, add a `{bot_guid: variant}` cache with TTL

- **Session 50 — Universal Spell Reactions + Dynamic Scaling — ALL COMPILED AND DEPLOYED**
  - All C++ compiled and live, Python bridge restarted
  - **Verified working**: Arcane Intellect (support catch-all), Flame Shock (offensive), death/resurrect sequence
  - **Verified working**: Achievement prompt fix — bots congratulate player instead of claiming achievement
  - **Needs testing**: weather_change cooldown bypass (bypassEventCooldown flag)
  - **Needs testing**: Dynamic trigger scaling in larger groups (5+ bots in dungeon)
  - **Needs testing**: Dungeon entry reactions, group wipe reactions in actual dungeon
  - **Future**: C++ priority restructure (all event types, see plan priority table)
  - **Future**: add emote target support (orange text says "Sytarre smiles at Calwen." instead of untargeted)
  - **Future**: Zone climate mapping system (discussed but not implemented)
  - **Future**: Class-specific pre-cache categories (warrior rage-themed, rogue stealth-themed, etc.)
  - **Playerbots bug FIXED & VERIFIED**: Quest link opens trade window — `ChatHelper::parseable()` changed `text.find("|H")` → `text.find("|Hitem:")` in `ChatHelper.cpp:603`. Fix applied locally and confirmed working. **Upstream PR submitted**: https://github.com/mod-playerbots/mod-playerbots/pull/2155 (targeting `test-staging`)

- **Session 40 — Role Awareness + Composition Commentary Deployed**
  - All Python-only, no compilation needed, bridge restarted
  - **Needs testing**: group join → observe composition comment at ~8s, check role-flavored combat reactions
  - **Monitor**: ambient prompts (transport, holiday) should NOT contain combat language thanks to guard clause
  - **Monitor**: same bot speaks greeting + composition comment — may feel like one bot dominating
  - **Resolved**: CompositionCommentChance now configurable (default 10%, was hardcoded 50%)
  - **Known**: `sequence` column stored but unused in C++ delivery ORDER BY — low priority fix
  - `/ri` command created for review doc generation

- **Session 39b -- Holiday Fix + Anti-Repetition Deployed**
  - Holiday detection now strict (excludes Call to Arms, fishing pools, building phases, fireworks)
  - Minor game events supported with separate event type and config
  - Anti-repetition system live: prompt injection + n-gram rejection
  - Config rebalanced: TriggerIntervalSeconds=50, HolidayCooldownSeconds=900
  - All C++ compiled and deployed, Python bridge restarted
  - **Needs testing**: holiday messages should now correctly reference "Love is in the Air", anti-repetition should reduce phrase convergence
  - **Monitor**: anti-repetition false positive rate (threshold=1 may be too strict for common 4-grams)
  - **Potential tuning**: if anti-repetition drops too many messages, increase threshold to 2

- **Session 39 — All Changes Compiled and Deployed**
  - Transport verified bots, single RNG gate, cooldown tuning — all compiled and live
  - 11/11 transport messages verified delivered via `/chatlog` cross-reference
  - Review docs: `docs/review-session39-transport-fixes.md`, `docs/review-session37-general-channel-delivery-fix.md`
  - `TransportCooldownSeconds` reduced to 300s in active config

- **Session 36 — 4 Immersion Features COMPILED AND DEPLOYED**
  - Emotes, mood drift, farewells, item links all live
  - SQL ALTERs run on live DB (emote column + farewell_msg column)
  - **Needs in-game testing**: emote animations visible, mood label in prompts, farewell message on group leave, item link detection in party chat
  - Review doc created: `docs/review-session36-immersion-features.md`

- **Session 32 — All changes compiled, deployed, and committed** to GitHub (mod-llm-chatter `0920b58`)
  - **Confirmed working**: Spell cast reactions (buff/PW:Fort), caster-perspective messages, account character bot support (greeting, player responses, idle chatter all tested with Hokken and Calwen)
  - **Needs in-game testing**: Quest objectives completion reactions (OnPlayerBeforeQuestComplete hook)
  - **Cleanup needed (when stable)**:
    - Revert `apps/docker/start-dev-servers.sh` to remove GDB wrapper (slows startup heavily)
    - Remove [TRACE] logging from C++ group handlers
    - Remove debug LOG_INFO from level-up/quest/achievement hooks (added Session 31)
    - Revert Python bridge log levels (WARNING → INFO)
    - Wire all logs to config flag (0=no logs, 1=critical/debug) before production
  - **Low priority**: Tag idle messages with source type to filter from idle context

- **Session 28 — Loot Crash Root Cause Found + Two-Tier Fix**
  - GDB backtrace confirmed exact crash: bot `Item*` use-after-free in `GetTemplate()` → `GetUInt32Value(3)` → SIGSEGV
  - Two-tier loot handler: real player loot (full Item* access), bot loot (no Item* access, lightweight event)
  - Investigation doc: `docs/mod-llm-chatter/bot-loot-item-crash-investigation.md`

- **Session 25 - Group Chatter Stages 2 & 3: Loot, Idle Chatter & Player Interaction**
  - Added `OnPlayerLootItem` hook in `LLMChatterPlayerScript`
  - Quality-based loot chance: gray/white=skip, green=20%, blue=50%, epic+=100%
  - 60s per-group loot cooldown to prevent spam
  - New `build_loot_reaction_prompt()` with quality-aware excitement levels
  - New `process_group_loot_event()` handler
  - Ambient idle chatter: bots say casual things during quiet moments
  - Idle chatter checks every 2 min, requires 5 min of group inactivity, 30% trigger chance
  - 15 idle topics (traveling, weather, gear, boredom, zone comments, etc.)
  - Idle messages go directly to `llm_chatter_messages` (no event needed)
  - Updated normal mob kill chance from skipped → 20% (user request)
  - Updated boss/rare kill chance from 50%/30% → 100%/100% (user request)
  - **Stage 3: Player Interaction**
  - `OnPlayerBeforeSendChatMessage` hook detects real player party chat (type==1)
  - 60% chance to trigger bot response, 30s per-group cooldown
  - Python picks a random bot from group, generates contextual reply to what player said
  - Player message text included in LLM prompt for natural responses
  - Bridge v3.9
  - SQL migration v3: `bot_group_loot`, v4: `bot_group_player_msg`
  - **C++ changes need compilation** (`OnPlayerLootItem` + `OnPlayerBeforeSendChatMessage` hooks)
  - **Python changes need bridge restart** (`docker restart ac-llm-chatter-bridge`)
  - SQL migrations already run
  - Code review fixes: `GetTemplate()` null check, JSON_EXTRACT for group_id, TIMESTAMPDIFF for timezone safety, int() casts for JSON fields

- **Session 24 - Group Chatter Stage 1 Improvements**
  - Improved greeting prompts: tone/mood/twist system from ambient chatter, RP race flavor words
  - Added `LLMChatterPlayerScript` with `OnPlayerCreatureKill` and `OnPlayerKilledByCreature` hooks
  - Kill reactions: filters bosses (rank 3, CREATURE_TYPE_FLAG_BOSS_MOB) and rares (rank 2, 4)
  - Per-group cooldowns, RNG gating, dedup prevention
  - Death reactions: a different bot from the dead one reacts
  - Cleaned up verbose debug LOG_INFO lines in GroupScript hooks
  - Startup cleanup: `DELETE FROM llm_group_bot_traits` on server start
  - Bridge v3.7, SQL migration v2
  - C++ compiled and deployed, SQL migration run, bridge restarted

- **Session 23 - Grouped Bot Chatter PoC**
  - Implemented full end-to-end group chatter: C++ GroupScript → DB event → Python traits + LLM → party chat
  - New `LLMChatterGroupScript` class with OnAddMember/OnRemoveMember/OnDisband hooks
  - New `chatter_group.py` module: personality traits (5 categories), greeting prompts, event handler
  - New `llm_group_bot_traits` table + `bot_group_join` event type
  - `DeliverPendingMessages()` now routes `channel='party'` via `ai->SayToParty()`
  - Config: `LLMChatter.GroupChatter.Enable` (default 0, set to 1 in active config)
  - Debug logging added to GroupScript hooks (can be removed later)
  - Successfully tested: 4 bots greeted with personality-driven messages in party chat
  - **Next steps**: combat events, conversation memory, player interaction, ambient group timer
  - C++ changes compiled and deployed, Python bridge restarted

- **Session 22 - Multi-Turn Conversation Context & Chatter Commits**
  - Fixed mod-llm-guide conversation context: full Q&A stored and replayed as real message turns
  - Enables natural follow-ups ("does that spell get upgraded?" after asking about Arcane Shot)
  - Added question/response TEXT columns to llm_guide_memory table
  - Committed mod-llm-chatter: spell messages, trade messages, bridge modularization, spell links
  - mod-llm-guide commit: `885f912` - multi-turn context
  - mod-llm-chatter commit: `593fcd6` - spell/trade/modularization
  - mod-llm-chatter C++ spell link changes still need compilation
  - Python-only changes for guide: restart bridge (`docker restart ac-llm-guide-bridge`)

- **Session 21 - Roleplay vs Normal Chatter Mode**
  - Implemented `LLMChatter.ChatterMode` config toggle (`normal` | `roleplay`)
  - Roleplay mode: race/class personality profiles, grounded RP tones/moods/twists/categories
  - Toned down RP from theatrical to "RP server casual" after testing
  - Expanded both TONES and RP_TONES from 9 → 20 entries each
  - Removed trail-off twists (looked like truncated output)
  - Added full prompt logging for tuning (temporary)
  - Fixed numeric race/class ID bug in `process_pending_requests()`
  - Switched back to Anthropic Haiku 4.5
  - Bridge version bumped to v3.5
  - Python-only changes: restart bridge to test (`docker restart ac-llm-chatter-bridge`)
  - No C++ compilation needed
  - Prompt logging still active - remove when done tuning

- **Session 20 - OpenAI Tool Support, Chatter Cleanup & ZoneId Fixes**
  - Implemented full OpenAI tool support for mod-llm-guide (was disabled)
  - Fixed mod-llm-chatter: em-dash double-spacing, emoji removal
  - Added randomized environmental context (40% time, 30% weather, 20% both, 10% neither)
  - Fixed 3 tools using empty zoneId column (list_zone_creatures, herbs, mining)
  - Discussed local LLM support - postponed (smaller models unreliable with tool calling)
  - User testing OpenAI tools - may find more issues

- **Session 19 - Transport Context Fix, Event Filtering & Rare Spawn Fix**
  - Fixed transport chatter to indicate correct travel direction
  - Added grouped bot filtering to Python event processing
  - Added mood logging for all statement types
  - Added weather guidance to prompts
  - Added EnableVerboseLogging config to both modules (placeholder for future)
  - Fixed rare spawn tool (zoneId→coordinate filtering, SQL syntax fix)
  - Local LLM support architecture confirmed (future: just add base_url config)

- **Session 18 - Command Rename: .ask → .ag**
  - Renamed mod-llm-guide command from `.ask` to `.ag` (Azeroth Guide)
  - Shorter, more convenient command for players
  - Requires compilation to take effect

- **IMPORTANT: Manual Compilation Required**
  - `compile.sh` does NOT work for incremental builds (Docker timestamp issue)
  - Must use manual workflow:
    1. Stop worldserver
    2. Touch source files inside container
    3. Run `make -j12 modules`
    4. Run `make -j12 worldserver`
    5. Run `make install`
    6. Restart container
  - See CLAUDE.md or dev-server-guide.md for exact commands

- **Rate Limiting Summary (mod-llm-chatter)**
  - TriggerChance: 30% (dev), will be 60% in prod
  - BotSpeakerCooldownSeconds: 900 (15 min per bot)
  - ZoneFatigueThreshold: 3 messages then cooldown
  - TransportCooldownSeconds: 300 (5 min per transport+zone)
  - TransportEventChance: 50%
  - WeatherChatterChance: REMOVED (weather context in all prompts now)
  - GlobalMessageCap: REMOVED

- **Compilation Workflow (MANUAL STEPS REQUIRED)**
  ```powershell
  # Step 1: Stop worldserver
  powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 pkill -9 worldserver"

  # Step 2: Touch source files (example for mod-llm-chatter)
  powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'find /azerothcore/modules/mod-llm-chatter/src -name \"*.cpp\" -o -name \"*.h\" | xargs touch'"

  # Step 3-5: Compile
  powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make -j12 modules 2>&1'"
  powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make -j12 worldserver 2>&1'"
  powershell.exe -Command "docker exec azerothcore-wotlk-ac-dev-server-1 bash -c 'cd /azerothcore/var/build/obj && make install 2>&1'"

  # Step 6: Restart
  docker compose --profile dev restart ac-dev-server
  ```

  For full rebuild (new modules): `compile.sh --full` still works

- **Database Backup Script**
  - Location: `apps/docker/backup-database.sh`
  - **ALWAYS backup before risky operations**
  - Run: `docker exec azerothcore-wotlk-ac-dev-server-1 bash /azerothcore/apps/docker/backup-database.sh`

- **CRITICAL: Never use `docker compose down -v`**
  - The `-v` flag deletes ALL volumes including the database
  - Always use `docker compose down` without `-v`

- **Branch Status**
  - Working branch: `Playerbot`
  - Module repos are local only (no remote origins yet)

- **Recommended startup order**:
  1. ac-database (MySQL)
  2. ac-dev-server (worldserver)
  3. ac-llm-guide-bridge (mod-llm-guide)
  4. ac-llm-chatter-bridge (mod-llm-chatter)

- Session management system is in place:
  - Read `CLAUDE.md` at start for project context
  - Read this file and `history.md` for session continuity
  - Run `/um` to update these files before ending a session
