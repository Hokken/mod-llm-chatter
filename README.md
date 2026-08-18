<p align="center">
  <img src="images/banner.jpg" alt="The Chatters" width="100%">
</p>

# mod-llm-chatter

**Every hero has a story. Your companions are ready to tell theirs.**

A fantasy roleplay conversation engine for [AzerothCore](https://www.azerothcore.org/) WotLK (3.3.5a) and [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots). It replaces the silence of automated bots with personality-driven, lore-grounded dialogue, giving every companion a voice shaped by their race, class, and the world around them. Whether you're soloing through the cursed woods of Duskwood, descending into the titan halls of Ulduar with a full raid, or clashing over flags in Warsong Gulch, your party feels like a band of adventurers sharing a journey through Azeroth.

Built from the ground up for **fantasy roleplay immersion**. Every system, personalities, memories, prompts, spatial awareness, is designed to keep bots speaking as inhabitants of Azeroth, not as AI assistants breaking the fourth wall.

---

<p align="center"><a href="https://discord.gg/9UBW7ZDZvY"><img src="https://img.shields.io/badge/Discord-Join%20the%20Community-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join Discord"></a></p>

> See my other module: **[mod-llm-guide](https://github.com/Hokken/mod-llm-guide)** — AI-powered in-game assistant

---

### Chatter Companion Addon

<table>
<tr>
<td width="340"><img src="images/chatter-companion.png" alt="Chatter Companion addon" width="340"></td>
<td valign="top"><a href="https://github.com/Hokken/Chatter-Companion"><strong>Chatter Companion</strong></a><br><br>A lightweight WoW addon that lets you view and edit your bots' personality traits, tone, and background story directly from the game UI. Open it with <code>/chatter</code> or <code>/llmc</code>, pick a bot from your roster, tweak their personality, read their origin story, or regenerate it with a click. Changes are reflected in their dialogue immediately. No server restart required.</td>
</tr>
</table>

---


## Features

* **Roleplay-First Personalities**: Every bot is a distinct character in Azeroth's story. Their dialogue is deeply rooted in their race, class, and assigned personality traits, dynamically enhanced by their specialized talent builds. Bots stay in character, a Forsaken warlock speaks nothing like a Draenei paladin, and both draw from the lore and culture of their people to feel like living, breathing inhabitants of the world.
* **Persistent Personality & Memories**: Your companions remember you. Each bot carries a unique, permanent personality. Every dungeon you clear together, every boss you defeat, every achievement you earn, every level milestone, all of it is written into that bot's memory as a personal journal entry. The next time you group up, they might reference that time you wiped in Shadowfang Keep, or fondly recall discovering a hidden corner of Teldrassil together. Your relationship with each companion deepens over time, building the kind of shared history that makes a party of adventurers feel like old friends reunited at an inn.
* **Background Stories**: Every bot has an origin. When a companion first joins your group, the LLM generates a short background story rooted in their race, class, and personality traits — where they were born, who raised them, and the events that shaped who they are. A blood elf mage might carry the scars of Silvermoon's fall; a dwarf warrior might have learned to fight in the pits beneath Ironforge. These backstories are persistent, surviving across sessions, and are occasionally woven into idle chatter and ambient dialogue, giving bots a subtle sense of personal history without ever breaking the flow of conversation. View and regenerate backstories anytime through the Chatter Companion addon.
* **Deep Spatial & Lore Awareness**: Bots possess an intimate understanding of their surroundings, maintaining full awareness of both the broader world zones and the specific subzones within them. Whether you are wandering the vibrant paths of Elwynn Forest, traversing the vast snows of Dragonblight, or delving into the ancient mysteries of the Ruins of Mathystra in Darkshore, bots draw from over 3,000 unique descriptions to comment on the history, magic, and atmosphere of your exact location. In cities, they notice when you enter a new district, walking into the Cenarion Enclave or Krasus' Landing prompts a natural comment about the surroundings.
* **Conscious World Sensing**: The world is alive, and your companions notice it. Bots dynamically react to everything in their vicinity, from wildlife and rare creatures to NPCs, ancient ruins, weathered statues, and eerie altars. They also observe functional points of interest like moonwells, crackling fireplaces, and bustling forges, while adapting to weather changes, the time of day, arriving zeppelins, and seasonal holidays.
* **Organic Party Interactivity**: Your companions don't just follow; they interact. They will strike up multi-bot conversations, ask you unprompted questions about your journey, and react authentically to combat, loot, and quest milestones. Seamlessly integrated with the game's emote and voice systems, bots punctuate their dialogue with physical gestures and audible character voices, bringing an extra layer of life to everything from the thrill of an achievement to quiet banter by the campfire.
* **A Living, Breathing World**: The immersion extends beyond your immediate party. The open world's General channel hums with ambient bot chatter, reacting to real player messages and world events. Guards, vendors, trainers, and citizens engage in proximity `/say` conversations as you walk past, your party bots join in too, slipping naturally between party chat and the world around them. In battlegrounds, bots shout tactical callouts rooted in faction pride, while in raids, they brace for encounters across 148 iconic bosses, sharing lore and rallying morale between pulls.
* **Guild Hall Camaraderie**: Beyond the party and the open world,
  your guild feels like a real group of adventurers instead of a silent
  roster. Guildmates share stories, trade jokes, voice their opinions,
  and fall into conversations of their own. Speak in Guild Chat and
  they answer as familiar companions, remembering what has been said
  and carrying shared threads forward naturally. When you return to
  Azeroth, a warm welcome from your guild helps make the channel feel
  like a community that was already alive before you arrived.
* **Seamless Fantasy Immersion**: Designed to preserve the roleplay atmosphere, the module features smart pacing, multi-character conversation flow, and natural reading delays. No repetitive robotic spam, no fourth-wall breaks, just natural, in-character dialogue that deepens the fantasy of adventuring through Azeroth.
* **Zero Server Impact**: All LLM processing runs in a separate bridge service with a thread-pool worker model. The game server simply drops event rows into the database and moves on, never waiting on an API call. Responses flow back through the same queue and are delivered on the next world tick, keeping your server performance completely unaffected.

---

## Changelog

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

* **Screenshot Vision (Experimental)**: Bots can now see the actual game world through periodic screenshot analysis. A lightweight host-side agent captures your screen, sends it to a vision AI, and bots comment on what they see, from ancient ruins to glowing flora to approaching storms. Supports both GPT-4o-mini and Claude Haiku. See [Screenshot Vision](#screenshot-vision) for setup.
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

---

## Quick Start

1. Clone into `modules/` and build AzerothCore
2. Copy `conf/mod_llm_chatter.conf.dist` to your config directory and name it `mod_llm_chatter.conf`
3. Set your LLM provider and the matching API key (`LLMChatter.Anthropic.ApiKey`, `LLMChatter.OpenAI.ApiKey`, `LLMChatter.Google.ApiKey`, `LLMChatter.OpenRouter.ApiKey`, or no key when using Ollama)
4. Start worldserver once, or run `dbimport`, so AzerothCore applies the module's character database schema
5. Start the Python bridge
6. Play, bots start chatting when grouped with players

See [Setup](#setup) below for detailed Docker, non-Docker, and SQL preparation steps.

## Compatibility

This module requires a working AzerothCore server with mod-playerbots. If you don't have one yet, start here:

- [AzerothCore Docker install guide](https://www.azerothcore.org/wiki/install-with-docker)
- [AzerothCore Playerbot branch](https://github.com/mod-playerbots/azerothcore-wotlk/tree/Playerbot)
- [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots)

| Requirement | Version |
|-------------|---------|
| AzerothCore | [Playerbot branch](https://github.com/mod-playerbots/azerothcore-wotlk/tree/Playerbot) (WotLK 3.3.5a) |
| mod-playerbots | [liyunfan1223/mod-playerbots](https://github.com/mod-playerbots/mod-playerbots) |
| Python | 3.8+ |
| LLM Provider | Anthropic, OpenAI, Google Gemini, OpenRouter, or Ollama |

### Recommended Models

Tested extensively with excellent results:
- **Claude Haiku 4.5** (Anthropic),  fast, affordable, excellent quality
- **GPT-4o-mini** (OpenAI),  great alternative, similar cost
- **Gemini 3.1 Flash-Lite** (Google),  fast, cheap, tested with
  structured chatter and pre-cache JSON
- **Gemini 2.5 Flash** (Google),  reliable with
  `LLMChatter.Google.ThinkingBudget = 0`
- **GPT-4.1-mini** (OpenAI),  a little more expensive, but tested with
  fantastic quality and speed
- **OpenRouter model slugs** such as `anthropic/claude-haiku-4.5`,
  `openai/gpt-4o-mini`, and `openai/gpt-4.1-mini`, useful when users
  want OpenRouter routing while keeping OpenAI-compatible calls

OpenAI-compatible gateways do not all use the same reasoning control
or request API. Set the matching profile explicitly:

| Endpoint and model | Base URL | Request mode | Disable style |
|---|---|---|---|
| DeepSeek V4 Flash, official | `https://api.deepseek.com` | `chat` | `thinking` |
| DeepSeek V4 Flash, OpenCode Zen | `https://opencode.ai/zen/v1` | `chat` | `thinking` |
| DeepSeek V4 Flash, OpenCode Go | `https://opencode.ai/zen/go/v1` | `chat` | `reasoning` |
| GPT-5.6 Luna, OpenCode Go | `https://opencode.ai/zen/go/v1` | `responses` | `reasoning` |

Use `LLMChatter.OpenAICompatible.RequestMode`, enable
`LLMChatter.OpenAICompatible.DisableThinking`, and set
`LLMChatter.OpenAICompatible.DisableThinkingStyle` to the values above.
For Claude Haiku 4.5 through OpenCode Zen, use the Anthropic provider,
base URL `https://opencode.ai/zen`, and
`LLMChatter.Anthropic.DisableThinking = 1`.

Ollama is supported for local/free inference, but the module's advanced prompt architecture (structured JSON responses, system/user message separation, emote and action fields) demands strong instruction-following capabilities that smaller open-source models may not consistently deliver. For the best experience, we recommend Claude Haiku, GPT-4o-mini, GPT-4.1-mini, Gemini 3.1 Flash-Lite, or equivalent fast OpenRouter-hosted models such as Claude Haiku 4.5, GPT-4o-mini, or GPT-4.1-mini. See the config file header for provider setup details.

### Tuning the Chattiness

The default config ships on the **chatty side** so you can
experience all the features out of the box. If you prefer a
quieter, more immersive atmosphere, the key knobs are below.

**Reducing General channel chatter** (ambient bot conversations
in zone-wide chat):

```ini
# How often each zone is checked for ambient chatter
LLMChatter.TriggerIntervalSeconds = 60  # default 30, try 60-90

# Chance per check that bots start talking unprompted
LLMChatter.TriggerChance = 10            # default 15, try 5-10

# Chance that ambient chatter becomes a multi-bot conversation
LLMChatter.ConversationChance = 30      # default 40, try 15-20

# World event reactions (weather, transports, holidays)
LLMChatter.EventReactionChance = 10     # default 25, try 10-15
```

**Reducing party chatter** (group chat while questing):

```ini
# Idle chatter frequency and cooldown
LLMChatter.GroupChatter.IdleCheckInterval = 60  # default 30
LLMChatter.GroupChatter.IdleChance = 10          # default 15
LLMChatter.GroupChatter.IdleCooldown = 90       # default 40

# Quest reactions (accept, objectives, turn-in)
LLMChatter.GroupChatter.QuestAcceptChance = 30    # default 50
LLMChatter.GroupChatter.QuestObjectiveChance = 30 # default 50
LLMChatter.GroupChatter.QuestCompleteChance = 30  # default 50

# Combat reactions
LLMChatter.GroupChatter.KillChanceNormal = 5    # default 20
LLMChatter.GroupChatter.SpellCastChance = 10    # default 30

# Nearby object/creature comments
LLMChatter.GroupChatter.NearbyObjectChance = 5  # default 20
```

All values are percentages (0-100) unless noted. Setting any
chance to `0` disables that trigger entirely. See the config
file comments for the full list of tunable keys.

### Known Limitations
- **Ollama / open-source models**: Local inference requires fast hardware (sub-5s responses). Models below 8B frequently produce malformed JSON, ignore length constraints, or echo prompt instructions. Cloud-hosted Ollama models vary in quality — reasoning models (deepseek, qwen3.5, glm) are incompatible. For reliable results, use Claude Haiku or GPT-4o-mini
- Ollama cloud models add routing overhead compared to direct Anthropic/OpenAI APIs

---

## Setup

### Important: Disable Default Bot Chat

This module **replaces** built-in playerbot chat. Add to `playerbots.conf`:

```ini
AiPlayerbot.EnableBroadcasts = 0
AiPlayerbot.RandomBotTalk = 0
AiPlayerbot.RandomBotEmote = 0
AiPlayerbot.RandomBotSuggestDungeons = 0
AiPlayerbot.EnableGreet = 0
AiPlayerbot.GuildFeedback = 0
AiPlayerbot.RandomBotSayWithoutMaster = 0
```

### Docker

**1. Configure**

Copy `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` to `env/dist/etc/modules/` and rename it to `mod_llm_chatter.conf`. Open it in a text editor and set at minimum:
- `LLMChatter.Provider`,  choose `anthropic`, `openai`, `google`, `openrouter`, or `ollama`
- the matching provider API key, for example `LLMChatter.OpenRouter.ApiKey` when using OpenRouter (not needed for Ollama)

**2. Add bridge to docker-compose.override.yml**
```yaml
services:
  ac-llm-chatter-bridge:
    container_name: ac-llm-chatter-bridge
    image: python:3.11-slim
    networks:
      - ac-network
    working_dir: /app
    environment:
      - PYTHONUNBUFFERED=1
    command: >
      bash -c "
        pip install --quiet -r /app/requirements.txt &&
        python llm_chatter_bridge.py --config /config/mod_llm_chatter.conf
      "
    volumes:
      - ./modules/mod-llm-chatter/tools:/app:ro
      - ./env/dist/etc/modules:/config:ro
    restart: unless-stopped
    depends_on:
      ac-database:
        condition: service_healthy
    profiles: [dev]
```

**3. Initialize character tables**

The chatter bridge does not create database tables. AzerothCore imports
the module SQL automatically when worldserver or `dbimport` runs, but
the bridge can fail on a fresh database if it starts first.

On a fresh install, either start worldserver once before starting the
bridge, or import the base character schema manually after the database
container is running:

```bash
docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/base/00000000_llm_chatter_tables.sql
```

**4. Load talent data (optional)**

Populates talent and spell lookup tables that give the LLM richer context
about each bot's specialization. Worldserver treats `talenttab_dbc` rows as
runtime DBC overrides, so the included masks and ordering match the WotLK
3.3.5a client DBC.

```bash
docker exec -i ac-database mysql -uroot -ppassword acore_world < \
  modules/mod-llm-chatter/data/sql/world/base/llm_chatter_talent_dbc.sql
```

**5. Start**
```bash
docker compose --profile dev up -d
```

### Non-Docker

**1. Build**,  place this repo under `modules/` and rebuild AzerothCore.

**2. Configure**

Copy `conf/mod_llm_chatter.conf.dist` to your server's config directory (typically `etc/modules/`) and rename it to `mod_llm_chatter.conf`. Open it in a text editor and set at minimum:
- `LLMChatter.Provider`,  choose `anthropic`, `openai`, `google`, `openrouter`, or `ollama`
- the matching provider API key, for example `LLMChatter.OpenRouter.ApiKey` when using OpenRouter (not needed for Ollama)

**3. Initialize character tables**

The chatter bridge does not create database tables. AzerothCore imports
the module SQL automatically when worldserver or `dbimport` runs, but
the bridge can fail on a fresh database if it starts first.

On a fresh install, either start worldserver once before starting the
bridge, or import the base character schema manually:

```bash
mysql -uroot -ppassword acore_characters < \
  data/sql/characters/base/00000000_llm_chatter_tables.sql
```

**4. Start the bridge**
```bash
cd tools/
pip install -r requirements.txt
python llm_chatter_bridge.py --config /path/to/mod_llm_chatter.conf
```

**5. Load talent data (optional)**

Populates talent and spell lookup tables that give the LLM richer context
about each bot's specialization. Worldserver treats `talenttab_dbc` rows as
runtime DBC overrides, so the included masks and ordering match the WotLK
3.3.5a client DBC.

```bash
mysql -uroot -ppassword acore_world < \
  data/sql/world/base/llm_chatter_talent_dbc.sql
```

**6. Start or keep worldserver running.**

---

## Screenshot Vision

> This feature is **experimental** and **optional**. Everything else works without it.

Screenshot Vision lets your bots react to what's actually on your screen. A small helper program runs alongside your game, takes a screenshot every now and then, and asks a cheap AI model to describe what it sees. The description is then fed to your bots so they can comment on the scenery in party chat.

### What you need

- **Windows** (the helper runs on the same machine as your WoW client)
- **Python 3.10+** installed on your machine (not inside Docker)
- **An OpenAI API key** (GPT-4o-mini is recommended — extremely cheap) or an Anthropic key

### Step-by-step setup

**1. Install the required Python packages**

Open a terminal (PowerShell or Command Prompt) and run:

```
pip install mss Pillow openai mysql-connector-python pywin32
```

If you want to use Claude instead of GPT-4o-mini, also install `anthropic`:
```
pip install anthropic
```

**2. Run the database migration**

If you're upgrading from a previous version (fresh installs can skip this):

```bash
# Docker
docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260329_screenshot_event_type.sql
```

**3. Add the screenshot settings to your config**

Open your `mod_llm_chatter.conf` and add these lines at the bottom (or copy them from `mod_llm_chatter.conf.dist`):

```ini
# Enable the feature
LLMChatter.Screenshot.Enable = 1

# How often to capture (seconds). Default: every 45-120 seconds
LLMChatter.Screenshot.IntervalMinSeconds = 45
LLMChatter.Screenshot.IntervalMaxSeconds = 120

# Chance (1-100) to actually process each capture. Default: 90
LLMChatter.Screenshot.Chance = 90

# Which AI to use for analyzing screenshots
# Options: "openai" (recommended), "anthropic", "google", or "openrouter"
LLMChatter.Screenshot.VisionProvider = openai

# Which model to use. GPT-4o-mini is fast and very cheap
LLMChatter.Screenshot.VisionModel = gpt-4o-mini

# Chance (1-100) that a screenshot triggers a multi-bot
# conversation instead of a single comment. Default: 40
LLMChatter.Screenshot.ConversationChance = 40

# Database host override for the host-side agent.
# Your bridge uses a Docker hostname (like ac-database) that
# your Windows machine can't reach. Set this to 127.0.0.1
LLMChatter.Screenshot.DBHost = 127.0.0.1
```

Make sure your config also has the matching API key set (`LLMChatter.OpenAI.ApiKey`, `LLMChatter.Anthropic.ApiKey`, `LLMChatter.Google.ApiKey`, or `LLMChatter.OpenRouter.ApiKey`).

**4. Restart the chatter bridge**

```bash
docker restart ac-llm-chatter-bridge
```

**5. Start the screenshot agent**

Open a new terminal window and run:

```
python modules/mod-llm-chatter/tools/screenshot_agent.py --config env/dist/etc/modules/mod_llm_chatter.conf
```

Keep this window open while you play. The agent will quietly capture screenshots in the background and your bots will start making observations about the scenery.

**6. Play the game!**

Make sure WoW is in the foreground (the agent only captures when WoW is the active window). Group up with some bots, and within a couple of minutes you should see them commenting on what they see around them.

### Tips

- The agent saves screenshots to `modules/mod-llm-chatter/logs/screenshots/` so you can see exactly what the AI is analyzing
- If bots aren't saying anything, check that the agent terminal shows `Queued observation:` messages
- Cost is roughly **$0.05-0.10 per hour** of play with GPT-4o-mini
- You can stop the agent at any time (Ctrl+C) — the rest of the module continues working normally

---

## Upgrading

> **First-time installing the module? Skip this section.**
> The base schema in
> `data/sql/characters/base/00000000_llm_chatter_tables.sql`
> already contains everything every migration adds. Fresh installs do
> **not** need the dated migration files below after the base schema has
> been applied. That can happen automatically through worldserver or
> `dbimport`, or manually with the setup command above if the bridge is
> started before worldserver.

**Existing installs** must apply migration scripts manually
when updating to a newer version. Migrations live in
`data/sql/characters/updates/` and are named by date:

```bash
# Docker
docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260320_bot_memory_system.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260328_emote_event_types.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260329_screenshot_event_type.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260403_proximity_chatter.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260405_proximity_player_say.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260406_chatter_addon_identity_tone.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260416_bot_backstory.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260508_group_travel_state.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260508_party_chat_pacing.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260511_general_to_party_reaction.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260601_guild_chat.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260619_owner_subsystem.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260621_guild_chatter.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260724_guild_player_sessions.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260725_guild_login_greeting.sql

# Non-Docker
mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260320_bot_memory_system.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260328_emote_event_types.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260329_screenshot_event_type.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260403_proximity_chatter.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260405_proximity_player_say.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260406_chatter_addon_identity_tone.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260416_bot_backstory.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260508_group_travel_state.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260508_party_chat_pacing.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260511_general_to_party_reaction.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260601_guild_chat.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260619_owner_subsystem.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260621_guild_chatter.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260724_guild_player_sessions.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260725_guild_login_greeting.sql
```

Migrations are idempotent — safe to run on an already
up-to-date database. Run them in date order after each
`git pull` that includes new migration files.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No chatter appearing | Check `Enable = 1`, API key set, bots in zone with player |
| Group chat not working | Set `GroupChatter.Enable = 1`, must have bots in party |
| BG chatter not working | Set `BGChatter.Enable = 1`, join WSG/AB/EY with bots |
| Raid chatter not working | Set `RaidChatter.Enable = 1`, raid group in supported instance |
| Too much / too little chatter | Tune chance and cooldown settings in config |
| Ollama slow responses | Try a smaller model or use a cloud provider |

### Bots won't chat? Check the health report

You don't need to run anything. Every time the bridge starts, it
runs a built-in health check and prints a simple **PASS / FAIL**
report. Just look at the bridge's startup output:

- **Docker:** the bridge window, or run `docker logs ac-llm-chatter-bridge`
- **Non-Docker:** the bridge's console output

A copy of the report is also saved to
`modules/mod-llm-chatter/logs/healthcheck.log`, so you can open it
like a normal text file.

If something is misconfigured, the report names the problem in plain
language and tells you how to fix it. It checks:

- the config file loads and the module is enabled
- the database connection — wrong username/password, unreachable
  host, or wrong database name
- the required tables exist
- the LLM provider and API key — missing key, a leftover example
  placeholder, an invalid key, or an unreachable local model

A failing check looks like this:

```
[FAIL] LLM provider config
      The anthropic API key is still the example placeholder.
      -> Replace the placeholder in LLMChatter.Anthropic.ApiKey with your real key.
```

Fix the items marked `[FAIL]`, restart the bridge, and check that
every line now shows `[PASS]`. If they all pass and bots still don't
talk, see the table above.

> The check runs automatically by default. It can be turned off with
> `LLMChatter.HealthCheck.Enable = 0`, and the live LLM test call can
> be disabled with `LLMChatter.HealthCheck.LLMProbe = 0`.

**Check logs:** `docker logs ac-llm-chatter-bridge --since 5m`

---

## On the Horizon

- More battlegrounds and deeper raid integration
- New features that deepen the fantasy roleplay experience and bring more of Azeroth's lore to life

---

## License

GNU AGPL v3, same as AzerothCore.

## Credits

- Uses [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots) for bot characters
- Powered by [Anthropic Claude](https://anthropic.com), [OpenAI GPT](https://openai.com), [Google Gemini](https://ai.google.dev/gemini-api), [OpenRouter](https://openrouter.ai), or [Ollama](https://ollama.ai)
