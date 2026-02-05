# mod-llm-chatter

An AzerothCore module that generates dynamic, AI-powered conversations between playerbots in General chat.

Instead of static, repetitive database messages, bots chat naturally about the zone, quests, and loot drops - creating the illusion of a living, active world.

## Features

- **Dynamic AI conversations** - Bots chat naturally using Claude Haiku or GPT-4o-mini
- **2-4 bot conversations** - Conversations can include 2, 3, or 4 participants
- **Zone-aware content** - Messages reference actual quests and items from the player's zone
- **Zone flavor system** - Rich atmosphere descriptions for ~45 zones to inspire immersive chat
- **Clickable links** - Quest and item mentions become clickable WoW links
- **Natural timing** - Realistic, varied delays between messages (12-45 seconds)
- **Multiple message types** - Plain chat, quest discussions, loot drops, quest rewards
- **Conversation variety** - Both single statements and multi-message conversations
- **Anti-repetition** - Dynamic prompts with CREATIVE_TWISTS ensure varied, unpredictable messages
- **80+ message categories** - Atmospheric, mystical, nostalgic, and more for rich variety
- **Multi-provider support** - Works with Anthropic Claude or OpenAI GPT
- **Overworld only** - Chatter only happens in the open world, not in dungeons
- **Smart bot selection** - Only independent bots chat (not your party members)
- **Bot name addressing** - Bots use each other's names naturally in conversations
- **Fuzzy name matching** - Tolerates LLM typos in bot names
- **Weather events** - Bots react to actual weather changes (rain, snow, thunderstorms, sandstorms)
- **Transport arrivals** - Bots announce boat and zeppelin arrivals with destination info

## How It Works

1. Every 60 seconds, the module may trigger chatter in the player's zone
2. It selects 2-4 eligible bots (same faction, not in player's group)
3. Queries zone-specific quests/items from the database
4. Adds zone flavor context for immersive, atmosphere-aware messages
5. Sends context to the LLM to generate authentic-sounding chat
6. Delivers messages with realistic, varied timing delays (12-30 seconds)
7. Quest/item names become clickable links

**Example output in General chat (4-bot conversation):**
```
[Nylaenas]: been thinking about [Tharnariun's Hope] - there's something beautiful about restoring hope here
[Pelrith]: just finished that quest chain and it felt so good!
[Kerrandiir]: we handled it flawlessly yesterday, not to flex lol
[Eveline]: yeah it's a solid quest, decent rewards too
```

**Example weather reaction:**
```
[Thornbeard]: perfect weather for fishing, this rain
```

**Example transport arrival:**
```
[Miralynn]: boat to Auberdine just pulled in, anyone heading that way?
```

## Requirements

- AzerothCore WotLK (3.3.5a)
- mod-playerbots (for bot characters)
- Python 3.8+
- An API key from [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/)

## Docker Setup (Recommended)

The easiest way to run mod-llm-chatter is with Docker Compose.

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
LLMChatter.TriggerChance = 15
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
        if [ ! -f /app/llm_chatter_bridge.py ]; then
          echo 'mod-llm-chatter not installed - bridge not needed';
          sleep infinity;
        fi &&
        if [ ! -f /config/mod_llm_chatter.conf ]; then
          echo 'mod_llm_chatter.conf not found - copy from .dist and configure';
          sleep infinity;
        fi &&
        pip install --quiet anthropic openai mysql-connector-python &&
        echo 'LLM Chatter Bridge: Starting...' &&
        python llm_chatter_bridge.py --config /config/mod_llm_chatter.conf
      "
    volumes:
      - ./modules/mod-llm-chatter/tools:/app:ro
      - ./env/dist/etc/modules:/config:ro
    restart: unless-stopped
    depends_on:
      ac-database:
        condition: service_healthy
      ac-dev-server:
        condition: service_started
    profiles: [dev]
```

### 3. Start everything

```bash
docker compose --profile dev up -d
```

The bridge automatically:
- Detects if the module is installed
- Waits for the database to be ready
- Installs Python dependencies
- Starts generating chatter

### 4. Check logs

```bash
docker logs ac-llm-chatter-bridge --since 5m
```

## Non-Docker Setup

### 1. Build the module

```bash
cd azerothcore/build
cmake .. -DCMAKE_INSTALL_PREFIX=/path/to/install
make -j$(nproc)
make install
```

### 2. Configure

```bash
cp modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist /path/to/etc/modules/mod_llm_chatter.conf
```

Edit `mod_llm_chatter.conf`:
```ini
LLMChatter.Enable = 1
LLMChatter.Anthropic.ApiKey = sk-ant-your-key-here
```

### 3. Start the bridge

```bash
cd modules/mod-llm-chatter/tools
pip install anthropic openai mysql-connector-python
python llm_chatter_bridge.py --config /path/to/mod_llm_chatter.conf
```

### 4. Start worldserver

The module will begin generating chatter once bots are in zones with players.

## Configuration Reference

All settings are in `mod_llm_chatter.conf`:

### General Settings

| Option | Default | Description |
|--------|---------|-------------|
| `LLMChatter.Enable` | 0 | Enable/disable the module |
| `LLMChatter.TriggerIntervalSeconds` | 60 | Seconds between chatter checks |
| `LLMChatter.TriggerChance` | 30 | % chance per interval (lower = less frequent) |
| `LLMChatter.ConversationChance` | 50 | % chance for conversation vs single statement |
| `LLMChatter.MaxPendingRequests` | 5 | Max queued requests |

### Message Delivery

| Option | Default | Description |
|--------|---------|-------------|
| `LLMChatter.DeliveryPollMs` | 1000 | How often to check for messages (ms) |
| `LLMChatter.MessageDelayMin` | 1000 | Min delay between messages (ms) |
| `LLMChatter.MessageDelayMax` | 45000 | Max delay between messages (ms) |

### Event Settings

| Option | Default | Description |
|--------|---------|-------------|
| `LLMChatter.UseEventSystem` | 1 | Enable event-driven chatter |
| `LLMChatter.EventReactionChance` | 15 | % chance to react to events |
| `LLMChatter.TransportEventChance` | 50 | % chance to announce transport arrivals |
| `LLMChatter.TransportCooldownSeconds` | 300 | Cooldown per transport+zone (5 min) |
| `LLMChatter.Events.Weather` | 1 | React to weather changes |
| `LLMChatter.Events.Transports` | 1 | React to transport arrivals |
| `LLMChatter.Events.Holidays` | 1 | React to holiday events |
| `LLMChatter.Events.DayNight` | 1 | React to day/night transitions |

### Rate Limiting

| Option | Default | Description |
|--------|---------|-------------|
| `LLMChatter.BotSpeakerCooldownSeconds` | 900 | Cooldown per bot (15 min) |
| `LLMChatter.ZoneFatigueThreshold` | 3 | Max messages before zone cooldown |
| `LLMChatter.ZoneFatigueCooldownSeconds` | 900 | Zone fatigue cooldown (15 min) |

### LLM API Settings

| Option | Default | Description |
|--------|---------|-------------|
| `LLMChatter.Provider` | anthropic | "anthropic" or "openai" |
| `LLMChatter.Anthropic.ApiKey` | (empty) | Your Anthropic API key |
| `LLMChatter.Anthropic.Model` | claude-haiku-4-5-20251001 | Model to use |
| `LLMChatter.OpenAI.ApiKey` | (empty) | Your OpenAI API key |
| `LLMChatter.OpenAI.Model` | gpt-4o-mini | Model to use |
| `LLMChatter.MaxTokens` | 350 | Max response tokens (350 recommended for conversations) |
| `LLMChatter.Temperature` | 0.8 | Creativity (0.0-1.0) |

### Database Settings

| Option | Default | Description |
|--------|---------|-------------|
| `LLMChatter.Database.Host` | localhost | MySQL host (`ac-database` for Docker) |
| `LLMChatter.Database.Port` | 3306 | MySQL port |
| `LLMChatter.Database.User` | acore | MySQL user |
| `LLMChatter.Database.Password` | acore | MySQL password |
| `LLMChatter.Database.Name` | acore_characters | Database name |
| `LLMChatter.Bridge.PollIntervalSeconds` | 3 | Bridge polling interval |

## Message Types

The module generates different types of messages:

### Regular Chatter (triggered by interval)

| Type | Chance | Description |
|------|--------|-------------|
| Plain | 65% | General zone chat, no links |
| Quest | 15% | Mentions a zone quest with clickable link |
| Loot | 12% | Mentions an item drop with clickable link |
| Quest+Reward | 8% | Mentions quest completion and reward item |

### Event-Driven Chatter

| Event | Trigger | Description |
|-------|---------|-------------|
| Weather | Actual weather change | Reacts to rain, snow, thunderstorms, sandstorms (zone-appropriate) |
| Transport | Boat/zeppelin arrival | Announces transport with destination info |
| Holiday | Holiday start/end | Comments on seasonal events |
| Day/Night | Time transition | Reacts to dawn/dusk |

## Cost Estimates

Using Claude Haiku (recommended):
- ~$0.0002 per message
- ~1000 messages = ~$0.20

The bridge logs token usage for monitoring.

## Tuning for Your Server

### For a quiet server (solo play)

```ini
LLMChatter.TriggerIntervalSeconds = 30
LLMChatter.TriggerChance = 20
```

### For a busy server (many real players)

```ini
LLMChatter.TriggerIntervalSeconds = 120
LLMChatter.TriggerChance = 10
```

### For testing

```ini
LLMChatter.TriggerIntervalSeconds = 15
LLMChatter.TriggerChance = 80
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No chatter appearing | Check `Enable = 1`, API key set, bots in zone |
| Only works in open world | Chatter disabled in dungeons/raids by design |
| Messages but no clickable links | Check bridge logs for JSON errors |
| Too much chatter | Lower `TriggerChance` or raise `TriggerIntervalSeconds` |
| Too little chatter | Raise `TriggerChance` or lower `TriggerIntervalSeconds` |
| "mod-llm-chatter not installed" | Module directory not found - check path |
| "Config not found" | Copy `.conf.dist` to `mod_llm_chatter.conf` |

**Check logs:**
- Docker: `docker logs ac-llm-chatter-bridge --since 5m`
- Non-Docker: Check terminal output or redirect to log file

## Architecture

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Worldserver   │────▶│    MySQL    │◀────│   Python     │────▶│  LLM API    │
│  (C++ module)   │     │   Queue +   │     │   Bridge     │     │  (Claude/   │
│                 │◀────│  Messages   │     │              │     │   GPT)      │
└─────────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
        │                                           │
        │ Trigger                                   │ Generate
        │ Selection                                 │ Messages
        │ Delivery                                  │ Parse Links
        ▼                                           ▼
┌─────────────────┐                         ┌─────────────┐
│   Zone Bots     │                         │  Zone Data  │
│   Faction       │                         │  Quests     │
│   Party Check   │                         │  Items      │
└─────────────────┘                         └─────────────┘
```

## Files

```
mod-llm-chatter/
├── conf/
│   └── mod_llm_chatter.conf.dist    # Configuration template
├── data/sql/db-characters/base/
│   └── llm_chatter_tables.sql       # Database schema
├── src/
│   ├── llm_chatter_loader.cpp       # Script loader
│   ├── LLMChatterConfig.cpp/h       # Config handling
│   └── LLMChatterScript.cpp         # Trigger, selection, delivery
├── tools/
│   └── llm_chatter_bridge.py        # Python bridge with LLM integration
├── include.sh
└── README.md
```

## Documentation

For detailed implementation documentation, see:
- [mod-llm-chatter Documentation](../../docs/mod-llm-chatter/mod-llm-chatter-documentation.md)

## License

GNU AGPL v3 - Same as AzerothCore.

## Credits

- Uses [mod-playerbots](https://github.com/liyunfan1223/mod-playerbots) for bot characters
- Powered by [Anthropic Claude](https://anthropic.com) or [OpenAI GPT](https://openai.com)
