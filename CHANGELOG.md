# Changelog

### 2026-09-09 - General Channel Pacing

* **Cross-source conversation spacing**: Automated ambient, transport,
  weather, holiday, and minor-event General chatter now shares one
  per-zone delivery timeline. Multi-line exchanges reserve their full
  scheduled window, preventing independently generated follow-ups from
  arriving in a wall while keeping player-directed replies responsive.
* **Quieter production preset**: Added
  `conf/presets/mod_ll_chatter_quieter.conf.dist` as an optional lower-volume
  configuration. It preserves contextual combat and instance reactions while
  reducing cumulative ambient chatter. Credentials and local diagnostic
  settings are intentionally excluded or disabled.

### 2026-09-08 - Instance Proximity Chatter

* **Dungeon and raid parity**: Ordinary proximity chatter now runs in
  eligible dungeon and raid maps with canonical map/current-area data
  and the existing curated dungeon context supplied to every prompt.
* **Hostile humanoid voices**: Safe, out-of-combat hostile humanoids
  can participate or answer a selected/named player `/say`. Disposition,
  creature rank, LOS, participant compatibility, and delivery-time
  eligibility checks keep the result grounded without changing faction
  or combat behavior.
* **Curated non-humanoid voices**: Interactive guards, quest givers,
  vendors, trainers, innkeepers, and flight masters can qualify before
  creature-type filtering, while arbitrary non-humanoids require an
  explicit creature-entry allowlist. A separate denylist always wins;
  bosses and universal combat safety exclusions remain intact. Movement
  never excludes an otherwise eligible speaker; moving or pathing
  creatures simply skip optional facing during delivery.
  Prompts receive creature type and the reason each NPC qualified.
  Non-selectable, fake-dead, undetectable, trigger, `[DND]`, `[PH]`, and
  `[UNUSED]` internal helpers are rejected, preventing invisible event
  targets such as Valentine vial bunnies from leaking into ambient
  dialogue. Nearby-name prompt context now deduplicates repeated names,
  and one conversation cannot select ambiguous same-name speakers.
* **Instance isolation and direction**: Cooldowns, active scenes, and
  reply history include map and instance identity. Explicit names and
  selected targets take priority over recent-scene or nearby fallbacks.
* **Environment-specific pacing**: Ordinary proximity scans and trigger
  chances can now be tuned independently for outdoor maps and
  dungeons/raids. Existing installations without the scoped keys inherit
  their legacy global values, while the distributed instance chance is
  intentionally higher because combat and movement remove opportunities.
* **Pre-aggro boss moments**: A separate boss-only subsystem can emit
  a short, paced sequence of original approach lines or answer a
  directed `/say` through monster yell. A shared per-boss-instance
  presence session combines randomized delays, decaying repeat chances,
  a persistent low-probability floor, and recent-line prompt history so
  encounters feel less mechanical without becoming noisy. Automatic
  opportunities are open-ended by default rather than stopping after
  three lines; an explicit toggle can restore a configurable hard cap.
  Directed replies postpone the next automatic opportunity. The path
  requires the player to remain beyond calculated aggro range plus a
  configurable safety margin
  (zero by default so compact rooms retain a usable pre-pull band),
  revalidates before delivery, never changes boss facing or threat, and
  supports a creature-entry denylist. Per-player scans use a fair
  round-robin schedule that caps expensive creature-grid work in
  populated raids.
* **Shared contracts and coverage**: Group kill reactions and proximity
  now use one comprehensive boss classifier seeded from AzerothCore's
  registered dungeon/raid encounters, with metadata fallbacks for special
  bosses. This includes ordinary-rank encounter minibosses such as
  Rethilgore without misclassifying every elite. Enter-combat reactions
  preserve their established narrower classification and probabilities.
  Eligible registered-encounter kills use the established guaranteed boss-
  kill reaction path rather than normal-trash chance and cooldown rules.
  Focused tests protect instance context, NPC metadata, history isolation,
  boss prompt constraints, fail-closed safety data, registry routing, and
  boss delivery ownership.
* **Database migration**: Existing installations must apply
  `data/sql/characters/updates/20260908_instance_proximity_boss_events.sql`
  so the event queue accepts the two new boss event types. Fresh installs
  receive them from the base schema.

### 2026-09-07 - Normal Player Chat Mode

* **Player-side normal mode**: Playerbots now speak as people playing
  World of Warcraft across General, Party, Guild, Battleground, Raid,
  screenshot, emote, and playerbot `/say` prompts. The shared voice
  contract favors friendly, natural MMO chat with room for varied
  personalities and occasional mild bluntness.
* **NPC roleplay preserved**: Actual NPCs remain inhabitants of Azeroth
  in proximity chatter regardless of the configured playerbot mode,
  including mixed NPC and playerbot scenes.
* **Broader conversation variety**: Normal-mode Guild, proximity,
  ambient, Party-question, dungeon-question, and Battleground topic
  pools now provide substantially more distinct gameplay and social
  subjects without relying on in-world roleplay framing.
* **Mode-safe context and caching**: Normal prompts ignore legacy
  roleplay-shaped identity metadata, active group personalities are
  normalized at bridge startup, and ready pre-cache rows are discarded
  before mode-specific responses are refilled.
* **Configuration and regression coverage**: Normal mode is now the
  documented default, with focused tests protecting channel routing,
  roleplay preservation, topic diversity, prompt context, and startup
  cache behavior.

### 2026-09-07 - OpenRouter Reasoning Controls

* **Opt-in reasoning configuration**: OpenRouter requests can now send
  model-specific reasoning effort and optionally exclude returned
  reasoning text. Empty effort values preserve existing behavior, while
  `none` explicitly disables reasoning on hybrid models.
* **Reasoning-aware output budgets**: An optional multiplier protects
  normal and quick-analysis responses from being consumed entirely by
  reasoning tokens. It applies only while reasoning is enabled.
* **Request-shape regression coverage**: Focused tests protect default,
  explicitly disabled, and enabled reasoning behavior across both
  OpenRouter request paths.

### 2026-09-07 - Playerbot Selector Command Filtering

* **Selector commands excluded from chatter**: Party commands using
  Playerbot selectors, such as `@tank attack`, `@group1 follow`, and
  `@aura123 follow`, are now rejected before they can enter Chatter's
  group history, reply queue, or persistent player-message memories.
* **Conversation-safe matching**: Selector syntax and command tails are
  validated so ordinary messages such as `@Aurabelle hi` and
  `@tank nice save` remain eligible for conversation.
* **Cross-language regression coverage**: Focused tests cover selector
  grammar, false-positive names, malformed inputs, case and whitespace,
  and enforce parity between the C++ and Python selector tables.
* **Dedicated changelog**: Release history now lives in this file
  instead of the README.

### 2026-08-31 - Anthropic SDK v1 Compatibility

* **Anthropic request compatibility**: Normal generation and
  quick-analysis requests now send sampling temperature through
  `extra_body`, avoiding SDK v1's rejection of the direct argument.
* **Supported dependency range**: Bridge requirements now constrain
  Anthropic to `>=1.0.0,<2.0.0`, with Python 3.10+ documented as the
  supported runtime.
* **Regression coverage**: Focused tests protect both Anthropic request
  paths from future SDK argument regressions.

### 2026-08-16 - Korean Language and Unicode Cleanup

* **Korean language support**: `LLMChatter.Language = KO` now resolves
  to Korean and applies the existing localized prompt rules.
* **Unicode-safe emoji cleanup**: Emoji removal no longer treats the
  entire range from U+24C2 through U+1F251 as emoji. Hangul, CJK, and
  other scripts inside that former range are preserved.

### Guild Channel Chatter

* **Guild chatter**: Optional ambient Guild statements and
  two- or three-bot conversations. C++ selects live participants;
  the bridge gives the exchange one RP subject and cross-zone context,
  adds irregular participant-name references when useful, then
  delivers naturally staggered Guild lines. It is gated by
  `GuildChatter.Chance`, `ConversationChance`, and `Cooldown`. The
  master Guild Chat feature now defaults to enabled.
* **Player-driven Guild replies**: Every eligible player Guild message
  receives at least one bot reply. The response can be a single answer,
  multiple independent answers, or a Guild conversation. Per-login
  memory combines recent verbatim lines with a compact rolling summary,
  supports subtle callbacks and opinion continuity, and is cleared on
  both logout and login. Summary calls always reuse the configured
  chatter provider and model.
* **Guild login greetings**: A full real-player login schedules a
  session-safe greeting without assuming playerbots are immediately
  ready. Quick 2-5-second reactions remain possible, while ordinary and
  busy delay bands make later greetings more common. Player speech,
  logout, relogin, Guild changes, and stale sessions cancel the greeting.
  Delivered greetings join the current Guild session history so an
  immediate player reply retains the greeting as context.

### 2026-06-19 - Chat-Type Master Toggles & Subsystem Classifier

* **General channel master switch**: New
  `LLMChatter.GeneralChannel.Enable` (default 1) silences **all**
  General-channel chatter with a single value — ambient remarks, world
  event reactions (weather, holidays, day/night — including the ones
  that normally always fire), and replies to player General messages.
  It takes effect immediately on `.reload config`, and also stops any
  General messages already queued for delivery, not just new ones.
* **Config key renamed (action may be required)**:
  `LLMChatter.GeneralChat.Enable` is now
  `LLMChatter.GeneralChat.PlayerReplyEnable`. It only ever governed
  replies to player General messages; the new name makes that clear.
  The old key is no longer read — if your config sets
  `LLMChatter.GeneralChat.Enable`, rename it. To turn off *everything*
  in General at once, use `LLMChatter.GeneralChannel.Enable` instead.
* **GroupChatter toggle made authoritative**:
  `LLMChatter.GroupChatter.Enable = 0` now also silences
  emote-triggered party/raid reactions and drains already-queued group
  messages, and the bridge stops attempting idle chatter and bot
  questions while it is off. Raid-boss and Battleground chatter (which
  share the party/raid channels) are unaffected. The solo NPC
  emote-mirror stays governed by `LLMChatter.EmoteReactions.Enable`.
* **Proximity toggle made authoritative**:
  `LLMChatter.ProximityChatter.Enable = 0` now also drains already-
  queued open-world say/msay lines, matching the other toggles.
* **New `owner_subsystem` classifier**: Each row in
  `llm_chatter_messages` is tagged with its owning subsystem (group,
  raid, bg, general, proximity, ...). This lets the delivery layer
  honor each master toggle even for in-flight messages without
  affecting the other subsystems that share the same chat channel.
* **Database Migration**: This update **adds a database column**. If
  upgrading, apply
  `data/sql/characters/updates/20260619_owner_subsystem.sql` (it is
  idempotent and also runs automatically when worldserver starts).
  Fresh installs already have the column from the base schema.

### 2026-06-18 - Startup Health Check

* **Automatic Setup Diagnostic**: The bridge now runs a built-in health
  check at startup and prints a plain-language PASS/FAIL report to its
  logs. It surfaces the most common "bots won't chat" causes — wrong
  database credentials, a missing or leftover-placeholder API key, an
  invalid key, or an unreachable local LLM — instead of failing
  silently. On a critical failure the bridge logs a clear banner naming
  the problem and the fix.
* **Six Checks With Fix Hints**: Verifies the config loads and the module
  is enabled, the database connection (distinguishing wrong
  user/password, unreachable host, and wrong database name), the required
  tables exist, the provider/API key is set and not a placeholder, and a
  live LLM test call actually succeeds.
* **Saved Report File**: The same report is written to
  `logs/healthcheck.log` so it can be opened as a normal text file
  without scraping container logs.
* **Config Toggles**: `LLMChatter.HealthCheck.Enable` (default 1) and
  `LLMChatter.HealthCheck.LLMProbe` (default 1) control the startup check
  and whether it makes the live LLM test call. An optional
  `LLMChatter.HealthCheck.LogPath` overrides the report file location.

### 2026-06-05 - Addon Chat Ingestion Filter

* **Hidden Addon Traffic Ignored**: Party, proximity, and General chat
  ingestion now drops messages tagged `LANG_ADDON` before they can be
  stored in chat history or sent to the LLM. This prevents Questie,
  Multibot, DBM-style sync packets, and similar addon protocol payloads
  from polluting bot context or memories.
* **Party Hook Language Preservation**: The group chat hook now threads
  AzerothCore's language flag through the player-message handler instead
  of discarding it, allowing addon traffic to be filtered by the engine's
  authoritative tag rather than brittle text heuristics.
* **Debug Evidence Logging**: When `LLMChatter.DebugLog = 1`, ignored
  addon packets are logged with chat type, player, byte length, and an
  escaped preview so server owners can verify filtering without storing
  raw addon traffic in LLM-facing history tables.

### 2026-06-02 - Loot Reaction Chance Configuration

* **Configurable Epic and Legendary Loot Reactions**:
  `LLMChatter.GroupChatter.LootChancePurple` and
  `LLMChatter.GroupChatter.LootChanceOrange` now control party loot
  reaction chances for purple and orange items instead of treating both
  as hardcoded 100% triggers.
* **Quality-Specific Loot Gates**: Group loot reactions now use separate
  configured chances for green, blue, purple, and orange item quality.
  Artifact and heirloom quality loot still always triggers.
* **Config Visibility**: The chatter bridge startup summary now prints
  the purple and orange loot chance values alongside green and blue.

### 2026-06-02 - Language Configuration Reliability

* **German and Common Language Codes**: `LLMChatter.Language` now ships
  built-in support for `DE`, `ES`, `PT`, and `RU` in addition to
  English and French. German no longer requires manually editing the
  Python language map.
* **Unknown Language Warnings**: The bridge now logs the configured and
  resolved language at startup, and warns when an unknown language code
  falls back to English.
* **More Complete Language Prompting**: Group farewell generation and
  ambient JSON repair retries now preserve the configured language rule
  instead of falling back to plain English repair prompts.
* **Localized Action Narration**: Conversation action prompts no longer
  include an English action example for the model to copy. The prompt
  now asks for short physical narration in the configured language.
* **No Database Migration**: This update is Python/config-template only.
  Restart the chatter bridge after changing `LLMChatter.Language`.

### 2026-05-19 - Google Gemini and OpenRouter Provider Support

* **Google Gemini Support**: Chatter can now use Google's
  OpenAI-compatible Gemini endpoint. `gemini-3.1-flash-lite` is the
  recommended Google model, with Gemini-specific reasoning/thinking
  controls for reliable structured JSON output.
* **OpenRouter Support**: Chatter can now use OpenRouter through its
  OpenAI-compatible API. Recommended OpenRouter model slugs include
  `anthropic/claude-haiku-4.5`, `openai/gpt-4o-mini`, and
  `openai/gpt-4.1-mini`.
* **Provider Setup Docs**: README and config examples now cover
  Anthropic, OpenAI, Google, OpenRouter, and Ollama, including matching
  provider-specific API key settings.
* **Screenshot Vision Provider Coverage**: Screenshot vision setup now
  documents OpenAI, Anthropic, Google, and OpenRouter provider options.
* **Runtime Validation**: OpenRouter was tested live with both
  `openai/gpt-4o-mini` and `anthropic/claude-haiku-4.5` across
  pre-cache, ambient, proximity, group idle, player message, and
  General-to-party relay paths. No truncation or malformed response
  pattern was observed in the request log during testing.

### 2026-05-11 - Immersion, Pacing, and Party Awareness

* **General-to-Party Reactions**: Party bots can now react when they hear
  another bot speaking in General chat. A grouped companion may comment on
  what was said, naming the General speaker directly, and larger groups can
  turn that moment into a short party conversation.
* **Smoother Party Chat Flow**: Party chatter is now paced more carefully so
  bot lines do not land in a noisy burst. Conversations feel calmer during
  travel, idle moments, screenshots, nearby observations, and event reactions.
* **Travel-Aware Companions**: Bots better understand how the group is moving.
  They can account for walking, mounts, taxi flights, swimming, and transports,
  which helps avoid awkward lines about doing something impossible in the
  moment.
* **Richer Ambient Gossip**: World chatter has more variety and better local
  flavor. NPC gossip, bot gossip, weather, time of day, and seasonal context
  are blended more consistently into ambient conversations.
* **More Reliable Location Awareness**: Zone and subzone reactions now use the
  location from the moment the event happened, reducing stale or misplaced
  comments when the group is moving quickly.
* **Weather Feels More Grounded**: Weather reactions now track player context
  more carefully, so environmental comments are less likely to fire from the
  wrong place or at the wrong time.
* **Cleaner Emotes and Actions**: Bot gestures and physical actions are handled
  more consistently, keeping messages readable while still adding character
  when appropriate.
* **Screenshot Vision Targeting Fixes**: Screenshot observations now choose
  eligible grouped bots more accurately, improving who comments on what the
  player sees.

### 2026-04-17 — Background Stories

* **LLM-Generated Origin Stories**: Every bot now receives a unique background story when they first join your group. Generated by the LLM based on the bot's race, class, and personality traits, each backstory covers birthplace, upbringing, and formative events — all grounded in Warcraft lore.
* **Persistent Across Sessions**: Backstories are stored permanently alongside traits and tone. The same bot tells the same origin story every time they rejoin.
* **Ambient Backstory Influence**: During idle party chatter (25% chance) and proximity /say conversations (15% chance), the bot's backstory is fed to the LLM, subtly influencing their dialogue without forcing explicit references. A bot raised in Lakeshire might comment on a quiet lake; one hardened by war might be blunter during downtime.
* **Addon Integration**: The Chatter Companion addon now displays each bot's background story in a scrollable read-only panel below the tone field. Click "Regenerate Story" to request a fresh backstory from the LLM. Changing a bot's traits automatically clears and regenerates their backstory to stay consistent.
* **Configurable**: Three new config keys control the feature: `LLMChatter.Backstory.Enable` (master toggle), `LLMChatter.Backstory.IdleChance` (default 25%), and `LLMChatter.Backstory.ProximityChance` (default 15%). All are bridge-scope — restart the chatter bridge after changes.
* **Database Migration**: Run `data/sql/characters/updates/20260416_bot_backstory.sql` if upgrading from a previous version.

### 2026-04-03 — Multidirectional Proximity Chatter

* **Ambient `/say` Conversations**: NPCs and bots now talk to each other — and to you — via `/say` as you move through the world. Guards, vendors, trainers, citizens, and your party bots all participate. Conversations are brief and spatially grounded.
* **Multi-Speaker Scenes**: 2-4 speakers exchange short lines with natural pauses. Speakers face each other when talking; NPCs return to their original orientation afterward.
* **Player Reply**: Reply via `/say` within 30 seconds and the nearby speaker will respond. Up to 5 exchanges before the conversation winds down naturally.
* **Name Addressing**: Speakers can address nearby bots, NPCs, and you by name.
* **250+ Topic Pool**: Casual conversation seeds across 17 categories — weather, gossip, petty crime, food, travel, guard talk, children's chatter, and more.
* **Fully Configurable**: 15 config keys control scan interval, trigger chance, cooldowns, conversation length, reply limits, and more.

### 2026-04-01 — Raid Chatter Enhancements

* **Raid Battle Cries**: When engaging enemies in a raid instance, a bot shouts a short battle cry in raid chat — race and class flavored. Configurable via `RaidChatter.BattleCryChance` (default 70%).
* **Raid Banter**: Between-pull idle events now alternate 50/50 between motivational morale and casual banter (environment jokes, class jabs, loot drama commentary).
* **Raid Idle Boost**: Idle chatter fires twice as often inside raid instances with half the cooldown, keeping the conversation flowing during dungeon crawls.
* **Dead Bot Awareness**: Dead bots know they're dead. Their idle dialogue shifts to ghost humor, resurrection pleas, and floor commentary instead of pretending they're alive.
* **Zone Transitions in Raids**: Bots now comment on subzone changes inside raid instances (e.g., moving between wings in Naxxramas).
* **Morale Between Deaths**: Morale and banter chatter no longer gets blocked when party members are dead — only active combat suppresses it.
* **Reliability Improvements**: Fixed duplicate message delivery and improved handling of truncated AI responses.

### 2026-04-01 — State Callouts, Greeting Improvements, Parser Hardening

* **Low Health & OOM Callouts**: Bots now vocalize when they're low on health or running out of mana. Configurable thresholds (`LowHealthThreshold`, `OOMThreshold`), chance, and cooldown. Automatically scales in battlegrounds (halved chance, doubled cooldown) to avoid spam.
* **Time-of-Day Greetings**: Bot greetings now include the current time of day, preventing immersion-breaking lines like "good evening" when it's morning.
* **Greeting Anti-Repetition**: Bots no longer echo each other's greetings when multiple join at once. Each bot reads the recent chat history and avoids repeating what others already said.
* **Robust Response Handling**: Improved parser reliability — raw AI artifacts no longer leak into chat.
* **State Callout Config**: Five new config keys for tuning health and mana callout behavior.

### 2026-03-29 — Screenshot Vision, Emote Reactions, BG Improvements

* **Screenshot Vision (Experimental)**: Bots can now see the actual game world through periodic screenshot analysis. A lightweight host-side agent captures your screen, sends it to a vision AI, and bots comment on what they see, from ancient ruins to glowing flora to approaching storms. Supports both GPT-4o-mini and Claude Haiku. See [Screenshot Vision](README.md#screenshot-vision) for setup.
* **Emote Reaction System**: Bots now react when you emote at them. `/wave` at a bot and they might wave back, `/flex` and they'll have something to say about it. Three reaction paths: silent mirror (bot mirrors your emote), verbal reaction (personal response), and observer comment (a nearby bot notices and chimes in). Covers all ~170 text emotes.
* **Dungeon Context Injection**: Party chatter prompts now detect when you're inside a dungeon and inject dungeon-specific flavor instead of outdoor zone lore. Affects kill, loot, death, achievement, wipe, corpse run, and nearby object events.
* **BG Chatter Quality Pass**: Reduced noise in battleground chatter, suppressed narrator actions in fast-paced BG events, unified the join path for cleaner group formation, and synced config defaults with tested values.
* **Action & Emote Frequency**: `EmoteChance` and `ActionChance` config keys control how often bots include physical emotes and narrator actions in their messages.

### 2026-03-22 — Persistent Memories & Personality Traits

* **Persistent Bot Identities**: Each bot now carries a permanent personality (3 traits + role + farewell style) stored in `llm_bot_identities`. Traits survive across sessions and server restarts. Bump `LLMChatter.Memory.IdentityVersion` to force regeneration after prompt changes.
* **Memory System**: 14 memory types (ambient, boss_kill, quest_complete, discovery, achievement, level_up, pvp_kill, bg_win/loss, wipe, dungeon, party_member, player_message, first_meeting) are generated via LLM and stored per bot-player pair. Memories are recalled during idle chatter, reunion greetings, and bot questions, creating recognizable callbacks to shared experiences.
* **Configurable Generation & Recall**: Every memory type has a `*GenerationChance` config key controlling how often memories are created. Recall frequency is controlled by `IdleRecallChance` and `RecallChance` (reunion).
* **Zone & Subzone Awareness in Prompts**: Zone flavor and subzone lore are now injected into quest, discovery, idle, and event prompts. The player's subzone is tracked from the moment bots join the group.
* **Focused Memory Callbacks**: When bots recall shared memories, the references are clear and recognizable — not vague allusions.
* **Message Length Controls**: Stricter length limits prevent wall-of-text messages.
* **Database Migration**: Run `data/sql/characters/updates/20260320_bot_memory_system.sql` if upgrading from a previous version.
