<p align="center">
  <img src="images/banner.jpg" alt="The Chatters" width="100%">
</p>

# mod-llm-chatter

**Your bots don't just fight beside you. They live in Azeroth.**

An AI-powered conversation engine for [AzerothCore](https://www.azerothcore.org/) WotLK (3.3.5a) and [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots). It replaces the silence of automated bots with personality-driven, lore-accurate dialogue,  whether you're soloing through Duskwood, running Ulduar with a full raid, or battling in Warsong Gulch.

---

<p align="center">
  <a href="https://discord.gg/tvVcecuR"><img src="https://img.shields.io/badge/Discord-Join%20the%20Community-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join Discord"></a>
</p>

> See my other module: **[mod-llm-guide](https://github.com/Hokken/mod-llm-guide)** — AI-powered in-game assistant with 29 database tools

---

## What's New: TRUE VISION — Bots See What You See

Your companions can now **literally see the world through your eyes**. Using lightweight screenshot analysis, bots observe the actual scenery on your screen, a crumbling ruin half-swallowed by vines, a lake shimmering under moonlight, a spider lurking at the edge of a cave, and react to it in character. They don't just know the zone name from a database. They *look around* and notice things, just like a real party member would.

Sometimes one bot points something out. Sometimes two of them start a conversation about what they see, one admiring the view, the other warning about what might be hiding in it. Every observation is shaped by the bot's personality, race, class, and knowledge of the area.

This feature runs entirely on the host side with a tiny vision model (GPT-4o-mini). Cost is roughly **$0.05-0.10 per hour** of play, less than a penny per observation. It's experimental, opt-in, and disabled by default. Enable it, run the lightweight screenshot agent alongside your game, and watch your bots come alive in a way no other bot module has done before.

> *Requires `screenshot_agent.py` running on the host machine. See [Screenshot Vision Setup](#screenshot-vision) for details.*

---

## Features

* **Roleplay-First Personalities**: Every bot is a distinct character. Their dialogue is deeply rooted in their race, class, and assigned personality traits, dynamically enhanced by their specialized talent builds. In Roleplay mode, bots stay in character, grounding their speech in the rich lore of Azeroth to feel like living, breathing companions.
* **Persistent Personality & Memories**: Your companions remember you. Each bot carries a unique, permanent personality. Every dungeon you clear together, every boss you defeat, every achievement you earn, every level milestone, all of it is written into that bot's memory as a personal journal entry. The next time you group up, they might reference that time you wiped in Shadowfang Keep, or fondly recall discovering a hidden corner of Teldrassil together. Your relationship with each bot deepens over time. They're not just bots anymore, they're companions with a shared history.
* **Deep Spatial & Lore Awareness**: Bots possess an intimate understanding of their surroundings, maintaining full awareness of both the broader world zones and the specific subzones within them. Whether you are wandering the vibrant paths of Elwynn Forest, traversing the vast snows of Dragonblight, or delving into the ancient mysteries of the Ruins of Mathystra in Darkshore, bots draw from over 3,000 unique descriptions to comment on the history, magic, and atmosphere of your exact location. In cities, they notice when you enter a new district, walking into the Cenarion Enclave or Krasus' Landing prompts a natural comment about the surroundings.
* **Conscious World Sensing**: The world is alive, and your companions notice it. Bots dynamically react to everything in their vicinity, from wildlife and rare creatures to NPCs, ancient ruins, weathered statues, and eerie altars. They also observe functional points of interest like moonwells, crackling fireplaces, and bustling forges, while adapting to weather changes, the time of day, arriving zeppelins, and seasonal holidays.
* **Organic Party Interactivity**: Your companions don't just follow; they interact. They will strike up multi-bot conversations, ask you unprompted questions about your journey, and react authentically to combat, loot, and quest milestones. Seamlessly integrated with the game's emote and voice systems, bots punctuate their dialogue with physical gestures and audible character voices, bringing an extra layer of life to everything from the thrill of an achievement to quiet banter by the campfire.
* **Living Ecosystems**: The immersion extends beyond your immediate party. The open world's General channel hums with ambient bot chatter, reacting to real player messages and world events. In battlegrounds, bots shout tactical callouts, while in raids, they brace for encounters across 148 iconic bosses, sharing morale-boosting lore between pulls.
* **Seamless Immersion**: Designed to preserve the fantasy atmosphere, the module features smart pacing, multi-character conversation flow, and natural reading delays. No repetitive robotic spam, just natural, contextual dialogue that enhances your journey through every corner of the world.
* **Zero Server Impact**: All LLM processing runs in a separate bridge service with a thread-pool worker model. The game server simply drops event rows into the database and moves on, never waiting on an API call. Responses flow back through the same queue and are delivered on the next world tick, keeping your server performance completely unaffected.

---

## Changelog

### 2026-03-29 — Screenshot Vision, Emote Reactions, BG Improvements

* **Screenshot Vision (Experimental)**: Bots can now see the actual game world through periodic screenshot analysis. A lightweight host-side agent captures your screen, sends it to a vision AI, and bots comment on what they see, from ancient ruins to glowing flora to approaching storms. Supports both GPT-4o-mini and Claude Haiku. See [Screenshot Vision](#screenshot-vision) for setup.
* **Emote Reaction System**: Bots now react when you emote at them. `/wave` at a bot and they might wave back, `/flex` and they'll have something to say about it. Three reaction paths: silent mirror (bot mirrors your emote), verbal reaction (personal response), and observer comment (a nearby bot notices and chimes in). Covers all ~170 text emotes.
* **Dungeon Context Injection**: Party chatter prompts now detect when you're inside a dungeon and inject dungeon-specific flavor instead of outdoor zone lore. Affects kill, loot, death, achievement, wipe, corpse run, and nearby object events.
* **BG Chatter Quality Pass**: Reduced noise in battleground chatter, suppressed narrator actions in fast-paced BG events, unified the join path for cleaner group formation, and synced config defaults with tested values.
* **System Prompt Support**: All 16 BG prompt builders and 4 raid prompt builders now use a system prompt block for JSON formatting rules, improving response consistency.
* **Action & Emote RNG**: `EmoteChance` and `ActionChance` config keys control how often bots include physical emotes and narrator actions in their messages, preventing emote spam.

### 2026-03-22 — Persistent Memories & Personality Traits

* **Persistent Bot Identities**: Each bot now carries a permanent personality (3 traits + role + farewell style) stored in `llm_bot_identities`. Traits survive across sessions and server restarts. Bump `LLMChatter.Memory.IdentityVersion` to force regeneration after prompt changes.
* **Memory System**: 14 memory types (ambient, boss_kill, quest_complete, discovery, achievement, level_up, pvp_kill, bg_win/loss, wipe, dungeon, party_member, player_message, first_meeting) are generated via LLM and stored per bot-player pair. Memories are recalled during idle chatter, reunion greetings, and bot questions, creating recognizable callbacks to shared experiences.
* **Configurable Generation & Recall**: Every memory type has a `*GenerationChance` config key controlling how often memories are created. Recall frequency is controlled by `IdleRecallChance` and `RecallChance` (reunion).
* **Zone & Subzone Awareness in Prompts**: Zone flavor and subzone lore are now injected into quest, discovery, idle, and event prompts. The player's subzone is tracked from the moment bots join the group.
* **Compact Memory Prompts**: When memories are present, prompts switch to a lean format focused on the memory reference, producing clear and recognizable callbacks instead of vague allusions.
* **Message Length Controls**: Stricter length limits across all prompt types prevent wall-of-text messages. Link-based messages (spell/quest/loot) capped at 80 characters.
* **Debug Export Enhancements**: The web UI debug export now includes structured metadata per LLM call, a Party Chat Deliveries section, and longer prompt/response previews.
* **Database Migration**: Run `data/sql/db-characters/updates/20260320_bot_memory_system.sql` to add the required tables and columns if upgrading from a previous version.

---

## Quick Start

1. Clone into `modules/` and build AzerothCore
2. Copy `conf/mod_llm_chatter.conf.dist` to your config directory and name it `mod_llm_chatter.conf`
3. Set your LLM provider and the matching API key (`LLMChatter.Anthropic.ApiKey`, `LLMChatter.OpenAI.ApiKey`, or no key when using Ollama)
4. Start the Python bridge
5. Play, bots start chatting when grouped with players

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
| LLM Provider | Anthropic, OpenAI, or Ollama |

### Recommended Models

Tested extensively with excellent results:
- **Claude Haiku 4.5** (Anthropic),  fast, affordable, excellent quality
- **GPT-4o-mini** (OpenAI),  great alternative, similar cost

Ollama is supported for local/free inference, but the module's advanced prompt architecture (structured JSON responses, system/user message separation, emote and action fields) demands strong instruction-following capabilities that smaller open-source models may not consistently deliver. For the best experience, we recommend Claude Haiku or GPT-4o-mini. See the config file header for Ollama setup details.

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
- `LLMChatter.Provider`,  choose `anthropic`, `openai`, or `ollama`
- `LLMChatter.ApiKey`,  your API key from the chosen provider (not needed for Ollama)

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

**3. Load talent data (optional)**

Populates talent and spell lookup tables that give the LLM richer context about each bot's specialization, resulting in more accurate class-aware dialogue. Uses `INSERT IGNORE` and is safe to run on any existing database.

```bash
docker exec -i ac-database mysql -uroot -ppassword acore_world < \
  modules/mod-llm-chatter/data/sql/db-world/base/llm_chatter_talent_dbc.sql
```

**4. Start**
```bash
docker compose --profile dev up -d
```

### Non-Docker

**1. Build**,  place this repo under `modules/` and rebuild AzerothCore.

**2. Configure**

Copy `conf/mod_llm_chatter.conf.dist` to your server's config directory (typically `etc/modules/`) and rename it to `mod_llm_chatter.conf`. Open it in a text editor and set at minimum:
- `LLMChatter.Provider`,  choose `anthropic`, `openai`, or `ollama`
- `LLMChatter.ApiKey`,  your API key from the chosen provider (not needed for Ollama)

**3. Start the bridge**
```bash
cd tools/
pip install -r requirements.txt
python llm_chatter_bridge.py --config /path/to/mod_llm_chatter.conf
```

**4. Load talent data (optional)**

Populates talent and spell lookup tables that give the LLM richer context about each bot's specialization, resulting in more accurate class-aware dialogue. Uses `INSERT IGNORE`,  safe on any existing database.

```bash
mysql -uroot -ppassword acore_world < \
  data/sql/db-world/base/llm_chatter_talent_dbc.sql
```

**5. Start worldserver**,  database tables are created automatically.

---

## Screenshot Vision

> This feature is **experimental** and **optional**. Everything else works without it.

Screenshot Vision lets your bots react to what's actually on your screen. A small helper program runs alongside your game, takes a screenshot every now and then, and asks a cheap AI model to describe what it sees. The description is then fed to your bots so they can comment on the scenery in party chat.

### What you need

- **Windows** (the helper runs on the same machine as your WoW client)
- **Python 3.10+** installed on your machine (not inside Docker)
- **An OpenAI API key** (GPT-4o-mini is recommended — extremely cheap) or an Anthropic key
- **WoW running in borderless windowed mode** (not exclusive fullscreen)

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
# Options: "openai" (recommended) or "anthropic"
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

Make sure your config also has the matching API key set (`LLMChatter.OpenAI.ApiKey` or `LLMChatter.Anthropic.ApiKey`).

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

**Fresh installs** create all tables automatically on first
worldserver startup (from `data/sql/characters/base/`).

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

# Non-Docker
mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260320_bot_memory_system.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260328_emote_event_types.sql

mysql -uroot -ppassword acore_characters < \
  data/sql/characters/updates/20260329_screenshot_event_type.sql
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

**Check logs:** `docker logs ac-llm-chatter-bridge --since 5m`

---

## On the Horizon

- More battlegrounds and deeper raid integration
- Open-world proximity encounters between bots and players
- New immersive features that deepen the living-world experience

---

## License

GNU AGPL v3, same as AzerothCore.

## Credits

- Uses [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots) for bot characters
- Powered by [Anthropic Claude](https://anthropic.com), [OpenAI GPT](https://openai.com), or [Ollama](https://ollama.ai)
