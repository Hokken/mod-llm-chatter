<p align="center">
  <img src="images/banner.jpg" alt="The Chatters" width="100%">
</p>

# mod-llm-chatter

AI-powered bot conversations for AzerothCore, built for roleplayers and immersion seekers. Bots don't just exist in your world — they live in it. They chat in General about quests and loot, react to weather and holidays, comment on ships pulling into port, and when grouped with you, they develop unique personalities and respond to everything that happens around them.

If you run a solo server or a small RP community and want your world to feel genuinely inhabited rather than populated by silent automatons, this is for you.

## What It Looks Like

**General chat, zone banter:**
```
[Dralidan]: The Gnarlpine grow bolder each night. Our forest turns
  against us through corruption.
[Nilaste]: Heard [Grimmaw] was spotted near the outer groves again.
[Dralidan]: Troubling. The wilds never truly rest.
[Welean]: We should patrol before dawn. The balance will hold.
```

**Party chat, your bots react to what's happening:**
```
[Seladan]: Pattern: [Red Linen Robe], well found. Practical gear.
  Could fetch decent coin if tailored right.
You: do we keep moving north?
[Uldamyr]: Lead on. These woods won't clear themselves.
[Seladan]: Shadow mend incoming, stay sharp.
```

**Weather reactions:**
```
[Seladan]: This rain's making me drowsy. Need something to keep
  me sharp in a fight.
[Uldamyr]: Sharp? You heal us from the back. What are you
  scheming, priest?
```

**Transport arrivals:**
```
[Dralidan]: The Moonspray arrives late. Darkshore waters grow
  restless at night.
[Nilaste]: Perhaps they'll have fresh supplies from Auberdine.
```

**Holiday reactions:**
```
[Orencer]: Love is in the Air again? I'd rather spend the evening
  sharpening my blade than chasing perfume vendors.
```

Every quest, item, and spell name becomes a clickable WoW link.

## Features

### General Chat (Zone Banter)
- **Multi-bot conversations** in General chat about quests, loot, weather, lore, the kind of chatter that made vanilla General chat feel alive
- **Zone-aware content**, bots know where they are. A dwarf in Dun Morogh talks about troggs and ale, not silithid and sand. Quests, mobs, and loot are pulled from the actual game database for the zone they're in
- **Handcrafted zone flavor**, rich atmospheric descriptions for ~45 open-world zones and ~50 dungeons and raids, from the gothic dread of Duskwood to the alien beauty of Zangarmarsh, giving the LLM deep world knowledge to draw from
- **No patterns, no repetition**, every message is shaped by a unique combination of tone, mood, creative twist, message category, zone atmosphere, race and class personality, time of day, and actual game data. The result is chat that feels human because no two prompts are ever the same
- **80+ message categories**, atmospheric, nostalgic, mystical, contemplative, humorous, and more. Bots don't just talk about gameplay, they notice the sunset, feel uneasy in the Plaguelands, or reminisce about old adventures
- **Race and class identity**, a Tauren Druid doesn't sound like an Undead Warlock. Each race has speech traits and cultural flavor words, each class has personality modifiers that shape how they speak
- **Clickable WoW links**, quest names, item names, and spell names are automatically converted into proper in-game links you can click, just like real player chat

### Player Interaction in General Chat
- **Bots react to you in General**, type anything in General channel and nearby bots respond naturally, zone-scoped with per-zone cooldowns
- **Smart bot selection**, address a bot by name ("Cylaea, eat some grass") and that specific bot responds. Misspell it? Fuzzy matching catches names within 2 characters. Don't mention anyone? An LLM analyzes context to pick the most relevant bot
- **Question detection**, questions (ending with `?`) get 100% reaction chance, non-questions get 80%, so asking something always gets an answer
- **Conversations**, 30% chance your message sparks a 2-bot conversation instead of a single reply

### Group Party Chat
- **Bots that feel like party members**, when grouped, your bots react to what's happening around you in party chat, just like real players would
- **Smart bot selection**, same 3-pass name matching works in party chat: exact name → fuzzy → LLM context analysis
- **Kill reactions**, your tank might brag about a clean pull, your healer might comment on a close call
- **Loot reactions**, genuine excitement over epic drops, friendly jealousy, "grats" that feel real
- **Combat cries**, battle shouts and war cries during engagements, flavored by race and class
- **Spell cast reactions**, bots comment when casting buffs, heals, shields, and crowd control on party members
- **Quest objectives**, bots react when quest objectives are completed, before turn-in
- **Level-up celebrations**, bots congratulate on level ups
- **Achievement reactions**, bots comment on achievements earned
- **You can talk to them**, type in party chat and your bots respond with context. They know what you just fought, where you are, and what happened recently
- **Multi-bot conversations**, bots build on each other's messages, creating natural back-and-forth between party members
- **Persistent personalities**, each bot gets 3 traits that stay consistent across the session. The grumpy dwarf stays grumpy, the optimistic paladin stays hopeful
- **Chat history**, bots remember recent conversation for coherent, contextual replies
- **Account bot support**, works with both random bots and your own account characters used as bots

### Event Reactions
- **Weather changes**, a sudden thunderstorm in Stranglethorn, snow in Dun Morogh, a sandstorm rolling through Tanaris, bots notice and react
- **Transport arrivals**, "boat to Auberdine just pulled in", bots announce boats and zeppelins with destination info
- **Holidays**, bots celebrate festivals like Love is in the Air. In capital cities, holiday mentions recur periodically so the festive mood stays alive
- **Day/night transitions**, bots comment on dawn breaking, dusk settling, or the eerie feel of midnight in a dangerous zone

### Modes
- **Normal**, casual MMO chat the way you remember it: abbreviations, game terms, "lol", "grats", and the occasional all-caps moment
- **Roleplay**, fully in-character speech shaped by race, class, and lore. Your Night Elf invokes Elune, your Orc speaks of honor, your Undead is darkly sardonic. No "Hark, fellow traveler!" nonsense, bots talk like actual people who happen to live in Azeroth, not drama students at a renaissance faire. A separate set of tones, moods, and categories built specifically for RP immersion

### Providers
- **Anthropic Claude**, Haiku recommended (fast, cheap, high quality)
- **OpenAI GPT**, GPT-4o-mini supported
- **Ollama**, run local models for free (Qwen3, Llama, Mistral)

## Requirements

- AzerothCore WotLK (3.3.5a)
- [mod-playerbots](https://github.com/liyunfan1223/mod-playerbots), **required**, this module generates chat for playerbot characters
- Python 3.8+
- An API key from [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/), or [Ollama](https://ollama.ai) installed locally

## Important: Playerbots Configuration

This module **replaces** the built-in playerbot chat with AI-generated conversations. For the best immersion, you **must** disable the default playerbot chat behaviors in your `playerbots.conf`:

```ini
# Disable all built-in bot chat -- mod-llm-chatter handles this now
AiPlayerbot.EnableBroadcasts = 0
AiPlayerbot.RandomBotTalk = 0
AiPlayerbot.RandomBotEmote = 0
AiPlayerbot.RandomBotSuggestDungeons = 0
AiPlayerbot.EnableGreet = 0
AiPlayerbot.GuildFeedback = 0
AiPlayerbot.RandomBotSayWithoutMaster = 0
```

Without these changes, bots will produce both the default scripted messages **and** the AI-generated ones, resulting in spam and breaking immersion.

## Docker Setup (Recommended)

### 1. Configure the module

```bash
cp modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist \
   env/dist/etc/modules/mod_llm_chatter.conf
```

Edit `env/dist/etc/modules/mod_llm_chatter.conf`:
```ini
LLMChatter.Enable = 1
LLMChatter.Anthropic.ApiKey = sk-ant-your-key-here
LLMChatter.Database.Host = ac-database
```

### 2. Add the bridge to docker-compose.override.yml

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

### 3. Start

```bash
docker compose --profile dev up -d
```

### 4. Check logs

```bash
docker logs ac-llm-chatter-bridge --since 5m
```

## Non-Docker Setup

### 1. Build the module

Place this repo under `modules/` in your AzerothCore source tree, then:

```bash
cd azerothcore/build
cmake .. -DCMAKE_INSTALL_PREFIX=/path/to/install
make -j$(nproc)
make install
```

### 2. Configure

```bash
cp conf/mod_llm_chatter.conf.dist /path/to/etc/modules/mod_llm_chatter.conf
```

Edit `mod_llm_chatter.conf` and set your provider + API key.

### 3. Start the bridge

```bash
cd tools/
pip install -r requirements.txt
python llm_chatter_bridge.py --config /path/to/mod_llm_chatter.conf
```

### 4. Start worldserver

Database tables are created automatically. Chatter begins once bots are in zones with players.

## Configuration Reference

All settings are in `mod_llm_chatter.conf`. Here are the most commonly tuned options:

### General

| Setting | Default | Description |
|---------|---------|-------------|
| `LLMChatter.Enable` | 0 | Enable the module |
| `LLMChatter.ChatterMode` | roleplay | `normal` or `roleplay` |
| `LLMChatter.TriggerIntervalSeconds` | 60 | Seconds between chatter checks |
| `LLMChatter.TriggerChance` | 30 | % chance per interval |
| `LLMChatter.ConversationChance` | 50 | % multi-bot conversation vs solo statement |

### Provider

| Setting | Default | Description |
|---------|---------|-------------|
| `LLMChatter.Provider` | anthropic | `anthropic`, `openai`, or `ollama` |
| `LLMChatter.Model` | haiku | Model alias or full name |
| `LLMChatter.Anthropic.ApiKey` | -- | Anthropic API key |
| `LLMChatter.OpenAI.ApiKey` | -- | OpenAI API key |
| `LLMChatter.Ollama.BaseUrl` | http://localhost:11434 | Ollama endpoint |
| `LLMChatter.MaxTokens` | 350 | Max response tokens |
| `LLMChatter.Temperature` | 0.8 | Creativity (0.0-1.0) |

### Message Delivery

| Setting | Default | Description |
|---------|---------|-------------|
| `LLMChatter.DeliveryPollMs` | 1000 | Check for messages (ms) |
| `LLMChatter.MessageDelayMin` | 1000 | Min delay between messages (ms) |
| `LLMChatter.MessageDelayMax` | 30000 | Max delay between messages (ms) |

### Events

| Setting | Default | Description |
|---------|---------|-------------|
| `LLMChatter.UseEventSystem` | 1 | Enable event-driven chatter |
| `LLMChatter.EventReactionChance` | 15 | % chance to react to events |
| `LLMChatter.Events.Weather` | 1 | React to weather changes |
| `LLMChatter.Events.Transports` | 1 | React to transport arrivals |
| `LLMChatter.Events.Holidays` | 1 | React to holidays |
| `LLMChatter.Events.DayNight` | 1 | React to time transitions |
| `LLMChatter.HolidayCooldownSeconds` | 1800 | Per-city holiday cooldown (seconds) |
| `LLMChatter.HolidayCityChance` | 10 | % holiday mention chance per city per check |
| `LLMChatter.EnvironmentCheckSeconds` | 60 | Environment check interval (seconds) |

### General Channel Reactions

| Setting | Default | Description |
|---------|---------|-------------|
| `LLMChatter.GeneralChat.Enable` | 0 | Enable bot reactions to player General chat |
| `LLMChatter.GeneralChat.ReactionChance` | 80 | % chance for non-question messages |
| `LLMChatter.GeneralChat.QuestionChance` | 100 | % chance for questions (ending with ?) |
| `LLMChatter.GeneralChat.Cooldown` | 15 | Per-zone cooldown in seconds |
| `LLMChatter.GeneralChat.ConversationChance` | 30 | % chance of 2-bot conversation vs single reply |

### Rate Limiting

| Setting | Default | Description |
|---------|---------|-------------|
| `LLMChatter.BotSpeakerCooldownSeconds` | 900 | Per-bot cooldown (15 min) |
| `LLMChatter.ZoneFatigueThreshold` | 3 | Max reactions per zone |
| `LLMChatter.ZoneFatigueCooldownSeconds` | 900 | Zone fatigue window (15 min) |
| `LLMChatter.GlobalMessageCap` | 8 | Max messages server-wide per window |
| `LLMChatter.GlobalCapWindowSeconds` | 300 | Global cap window (5 min) |

### Group Chatter

| Setting | Default | Description |
|---------|---------|-------------|
| `LLMChatter.GroupChatter.Enable` | 0 | Enable party chat when grouped with bots |
| `LLMChatter.GroupChatter.IdleChance` | 15 | % chance of idle banter per check |
| `LLMChatter.GroupChatter.IdleCheckInterval` | 60 | Seconds between idle checks |
| `LLMChatter.GroupChatter.IdleCooldown` | 30 | Min seconds between idle triggers per group |
| `LLMChatter.GroupChatter.ConversationBias` | 70 | % chance idle is multi-bot vs solo |
| `LLMChatter.GroupChatter.IdleHistoryLimit` | 5 | Recent messages in idle context |

### Database

| Setting | Default | Description |
|---------|---------|-------------|
| `LLMChatter.Database.Host` | localhost | `ac-database` for Docker |
| `LLMChatter.Database.Port` | 3306 | MySQL port |
| `LLMChatter.Database.User` | acore | MySQL user |
| `LLMChatter.Database.Password` | acore | MySQL password |

## Tuning for Your Server

**Solo play (make the world feel alive):**
```ini
LLMChatter.TriggerIntervalSeconds = 30
LLMChatter.TriggerChance = 20
```

**Busy server (real players + bots):**
```ini
LLMChatter.TriggerIntervalSeconds = 120
LLMChatter.TriggerChance = 10
```

**Testing:**
```ini
LLMChatter.TriggerIntervalSeconds = 15
LLMChatter.TriggerChance = 80
```

## Cost

**Cloud providers:**

| Provider | Model | Per 1000 messages |
|----------|-------|-------------------|
| Anthropic | Claude Haiku | ~$0.20 |
| OpenAI | GPT-4o-mini | ~$0.20 |

**Ollama:** Free, runs locally on your machine. Recommended models: `qwen3:4b` (fast), `qwen3:8b` (better quality).

The bridge logs token usage for monitoring.

## Architecture

```
Worldserver (C++)             Python Bridge
 |                              |
 | Trigger / Event fires        |
 | Select bots, build context   |
 |──── INSERT queue ──────────▶ |
 |                              |── build prompt (zone, bots,
 |                              |   weather, traits, history)
 |                              |── call LLM
 |                              |── parse response + links
 | ◀──── INSERT messages ──────|
 |                              |
 | Deliver with realistic       |
 | timing delays                |
 |                              |
 | Group events (kill, loot,    |
 | combat, player msg) ────────▶|── generate party chat
 |                              |── with personality traits
 | ◀──── INSERT party msgs ────|
```

## Files

```
mod-llm-chatter/
├── README.md
├── LICENSE
├── .gitignore
├── include.sh
├── conf/
│   └── mod_llm_chatter.conf.dist
├── data/sql/db-characters/base/
│   └── llm_chatter_tables.sql
├── src/
│   ├── llm_chatter_loader.cpp
│   ├── LLMChatterConfig.cpp
│   ├── LLMChatterConfig.h
│   └── LLMChatterScript.cpp
└── tools/
    ├── llm_chatter_bridge.py    # Main bridge (queue polling, LLM calls)
    ├── chatter_constants.py     # Zone flavors, message categories
    ├── chatter_shared.py        # Config parsing, DB helpers, link formatting
    ├── chatter_prompts.py       # Prompt building for all chatter types
    ├── chatter_events.py        # Event processing (weather, transport, etc.)
    ├── chatter_group.py         # Group chatter (party chat with bots)
    ├── chatter_general.py       # General channel player reactions
    ├── spell_names.py           # Spell ID-to-name lookup table
    └── requirements.txt
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No chatter appearing | Check `Enable = 1`, API key set, bots in zone with a player |
| Chatter only in open world | Intended, disabled in dungeons/raids |
| No clickable links | Check bridge logs for JSON parse errors |
| Too much chatter | Lower `TriggerChance` or raise `TriggerIntervalSeconds` |
| Too little chatter | Raise `TriggerChance` or lower `TriggerIntervalSeconds` |
| Group chat not working | Set `GroupChatter.Enable = 1`, must have bots in your party |
| Ollama slow responses | Try a smaller model (`qwen3:4b`) or increase `Ollama.ContextSize` |

**Check logs:**
- Docker: `docker logs ac-llm-chatter-bridge --since 5m`
- Non-Docker: check terminal output or redirect to a log file

## License

GNU AGPL v3, same as AzerothCore.

## Credits

- Uses [mod-playerbots](https://github.com/liyunfan1223/mod-playerbots) for bot characters
- Powered by [Anthropic Claude](https://anthropic.com), [OpenAI GPT](https://openai.com), or [Ollama](https://ollama.ai)
