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

* **Roleplay-first characters**: Bots speak as distinct inhabitants of
  Azeroth, shaped by race, class, talents, personality, and lore. Natural
  pacing, multi-character flow, emotes, and voices keep conversations
  immersive.
* **Persistent personalities and histories**: Each companion keeps a stable
  identity, generated backstory, and memories of shared dungeons, bosses,
  achievements, and milestones. Backstories can be viewed or regenerated
  through the Chatter Companion addon.
* **Location and world awareness**: More than 3,000 zone and subzone
  descriptions ground dialogue in the surrounding lore. Bots notice nearby
  creatures, NPCs, objects, points of interest, weather, time, transports,
  and holidays.
* **Interactive parties**: Companions banter with one another, ask the player
  questions, and react to combat, loot, quests, achievements, and travel.
* **Living public channels**: Ambient General chat, proximity `/say`, player
  replies, battleground callouts, and encounter-aware raid dialogue make the
  wider world feel populated.
* **Social guild chat**: Guildmates greet returning players, answer messages,
  hold conversations, and carry shared context forward during a session.
* **Non-blocking architecture**: LLM work runs in a separate, concurrent
  bridge service. Worldserver queues events and delivers completed responses
  without waiting on provider calls.

---

## Quick Start

1. Clone into `modules/` and build AzerothCore
2. Copy `conf/mod_llm_chatter.conf.dist` to your config directory and name it `mod_llm_chatter.conf`
3. Set `LLMChatter.Provider`, `LLMChatter.Model`, and the matching API
   key (Ollama does not need a key)
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
| Python | 3.10+ |
| LLM Provider | Anthropic, OpenAI, Google Gemini, OpenRouter, or Ollama |

Install the Python bridge dependencies from `tools/requirements.txt`.
Anthropic deployments use the supported 1.x SDK; installing provider
packages individually can bypass the module's compatibility constraints.

### Recommended Models

Tested extensively with excellent results:
- **Claude Haiku 4.5** (Anthropic),  fast, affordable, excellent quality
- **GPT-5.6 Luna** (OpenAI), fast and inexpensive; use
  `LLMChatter.OpenAI.ReasoningEffort = none` for short-form chatter
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

Ollama is supported for local/free inference, but the module's structured
JSON, system/user messages, emotes, and actions demand strong instruction
following. Smaller open-source models may not deliver it consistently. For
the best experience, use Claude Haiku, GPT-5.6 Luna, GPT-4o-mini,
GPT-4.1-mini, Gemini 3.1 Flash-Lite, or an equivalent fast model through
OpenRouter. See the config header for more provider guidance.

### Provider and Model Setup

Configuration uses unquoted `Key = value` lines. Copy model IDs exactly:
direct-provider IDs look like `gpt-5.6-luna`, OpenRouter IDs use
`vendor/model`, and Ollama IDs use the name and tag shown by `ollama list`.
Leave an optional value empty after `=`. Keep comments on separate lines;
the chatter parser treats an inline comment as part of the value.

| Provider | Provider value | Model setting | Credential |
|----------|----------------|---------------|------------|
| Anthropic | `anthropic` | Exact Anthropic model ID | `LLMChatter.Anthropic.ApiKey` |
| OpenAI | `openai` | Exact OpenAI API model ID | `LLMChatter.OpenAI.ApiKey` |
| Google | `google` | Exact Gemini API model ID | `LLMChatter.Google.ApiKey` |
| OpenRouter | `openrouter` | A `vendor/model` slug | `LLMChatter.OpenRouter.ApiKey` |
| Ollama | `ollama` | A name/tag from `ollama list` | None |

Ready-to-copy examples (replace only the placeholder key):

```ini
# Anthropic
LLMChatter.Provider = anthropic
LLMChatter.Model = claude-haiku-4-5-20251001
LLMChatter.Anthropic.ApiKey = sk-ant-xxxxx

# OpenAI Luna
LLMChatter.Provider = openai
LLMChatter.Model = gpt-5.6-luna
LLMChatter.OpenAI.ApiKey = sk-xxxxx
LLMChatter.OpenAI.ReasoningEffort = none
LLMChatter.OpenAI.MaxTokensMultiplier = 4

# Google Gemini
LLMChatter.Provider = google
LLMChatter.Model = gemini-3.1-flash-lite
LLMChatter.Google.ApiKey = AIza-xxxxx

# OpenRouter
LLMChatter.Provider = openrouter
LLMChatter.Model = anthropic/claude-haiku-4.5
LLMChatter.OpenRouter.ApiKey = sk-or-v1-xxxxx

# Local Ollama from a Docker bridge
LLMChatter.Provider = ollama
LLMChatter.Model = qwen3:8b
LLMChatter.Ollama.BaseUrl = http://host.docker.internal:11434
```

Use only one provider recipe at a time. Existing credentials for inactive
providers can remain in the file. Restart `ac-llm-chatter-bridge` after a
provider or model change. The bridge chooses compatible token, temperature,
and reasoning parameters automatically, then caches any explicit
unsupported-parameter correction for the rest of that process.

### Ignoring Visible Protocol Chat

If a server-specific addon or command sends machine-readable data through
visible player chat, Chatter can ignore it without blocking the message from
the game's normal chat system:

```ini
LLMChatter.PlayerChat.IgnoredPrefixes = !addon:,.custom:
```

The comma-separated list applies to real-player Party, General, Guild, and
`/say` input. Matching ignores leading whitespace and ASCII letter case and
runs before Chatter stores history or queues LLM work. Use distinctive
punctuation-bearing prefixes: configured entries are trimmed, and matching is
literal rather than word-aware. Normal `SendAddonMessage` traffic already
arrives as `LANG_ADDON` and does not need an entry. After the supporting C++
version is installed, apply list changes with `.reload config`.

For OpenAI Luna, `none` gives the lowest-latency behavior and permits the
configured temperature. Higher reasoning efforts can consume more of the
output budget, so the bridge applies `OpenAI.MaxTokensMultiplier` whenever
hidden reasoning may be active. It omits temperature where the model does
not support it. See the [official Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna).

For Ollama, run `ollama pull <model>` on the Ollama host first. A host-run
bridge normally uses `http://localhost:11434`; a Docker bridge normally uses
`http://host.docker.internal:11434`. Do not append `/v1` to the configured
base URL.

Ollama's OpenAI-compatible endpoint does not accept a per-request context
size. Set `OLLAMA_CONTEXT_LENGTH` before starting Ollama, or create a custom
model whose Modelfile contains `PARAMETER num_ctx 4096`. Confirm the loaded
value in the `CONTEXT` column from `ollama ps`. `Ollama.DisableThinking = 1`
uses both the supported `reasoning_effort = none` request and `/no_think`
fallback for compatible local models.

### Tuning the Chattiness

The default config ships on the **chatty side** so you can
experience all the features out of the box. If you prefer a
quieter, more immersive atmosphere, the key knobs are below.

An optional lower-volume template is available at
[`conf/presets/mod_ll_chatter_quieter.conf.dist`](conf/presets/mod_ll_chatter_quieter.conf.dist).
It is not automatically installed or loaded. To use it, back up your active
config, then copy the preset to your server's module-config directory as
`mod_llm_chatter.conf` and configure its database and provider credentials.
Keep alternate presets in `conf/presets/`: files directly under
`conf/*.conf.dist` are registered as required config filenames at build time.

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
- **Ollama / open-source models**: Local inference needs fast hardware and
  strong instruction following. Small or reasoning-heavy models can be slow,
  return malformed JSON, or spend the output budget before producing visible
  chat. Prefer an instruct/tool-capable 8B-or-larger model and enable
  `LLMChatter.Ollama.DisableThinking` for compatible thinking models.
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
- `LLMChatter.Model`, using the exact ID format shown in
  [Provider and Model Setup](#provider-and-model-setup)
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
- `LLMChatter.Model`, using the exact ID format shown in
  [Provider and Model Setup](#provider-and-model-setup)
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
The screenshot agent uses the same model-aware token-field negotiation as the
bridge, so direct OpenAI reasoning/vision model IDs do not require a separate
`max_tokens` workaround.

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
- Vision cost varies with the provider, model, image size, and current pricing
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
when updating to a newer version. Migrations live under
`data/sql/*/updates/` and are named by date.

### Required spell override repair

Installations that loaded the optional talent data before April 9, 2026
must apply the following world-database migration. Older versions inserted
incomplete `spell_dbc` overrides that could cause spell-script validation
warnings and hide real client spell effects. The migration only removes
rows that still match that legacy placeholder shape and is safe to rerun.

```bash
# Docker
docker exec -i ac-database mysql -uroot -ppassword acore_world < \
  modules/mod-llm-chatter/data/sql/world/updates/20260913_remove_legacy_spell_dbc_placeholders.sql

# Non-Docker
mysql -uroot -ppassword acore_world < \
  data/sql/world/updates/20260913_remove_legacy_spell_dbc_placeholders.sql
```

Restart worldserver after applying this repair so it reloads the restored
client DBC records. Fresh installations using the current talent-data SQL
do not create the incomplete rows and do not need this repair.

### Character-database migrations

Apply the relevant character migrations when upgrading:

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

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260827_widen_group_bot_traits.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260830_message_action_emote.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260908_instance_proximity_boss_events.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260914_npc_multidirectional_interactions.sql

docker exec -i ac-database mysql -uroot -ppassword acore_characters < \
  modules/mod-llm-chatter/data/sql/characters/updates/20260919_real_general_items.sql

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

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260827_widen_group_bot_traits.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260830_message_action_emote.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260908_instance_proximity_boss_events.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260914_npc_multidirectional_interactions.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260919_real_general_items.sql
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
