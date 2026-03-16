<p align="center">
  <img src="images/banner.jpg" alt="The Chatters" width="100%">
</p>

# mod-llm-chatter

**Your bots don't just fight beside you. They live in Azeroth.**

An AI-powered conversation engine for [AzerothCore](https://www.azerothcore.org/) WotLK (3.3.5a) and [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots). It replaces the silence of automated bots with personality-driven, lore-accurate dialogue,  whether you're soloing through Duskwood, running Ulduar with a full raid, or battling in Warsong Gulch.

---

## Hear the World Come Alive

**General chat buzzes with life:**
```
[Dralidan]: The Gnarlpine grow bolder each night. Our forest turns
  against us through corruption.
[Nilaste]: Heard Grimmaw was spotted near the outer groves again.
[Dralidan]: Troubling. The wilds never truly rest.
```

**Your party reacts to everything:**
```
[Seladan]: Pattern: [Red Linen Robe], well found. Practical gear.
You: do we keep moving north?
[Uldamyr]: Lead on. These woods won't clear themselves.
```

**Battlegrounds come alive:**
```
[Korthak]: FOR THE HORDE! Push mid, don't let them regroup!
[Maulgar]: Thraza picked up their flag,  cover her!
```

**Bots notice what's around them:**
```
[Glona]: Would you look at that, a moonwell. Perfect spot for
  some meditation.
```

**Bots know where they are — zone and subzone:**
```
[Uldamyr]: These ruins... Mathystra fell long before any of us
  drew breath. The magic here still lingers.
```

**Weather, transports, holidays,  bots notice it all:**
```
[Seladan]: This rain's making me drowsy. Need something to keep
  me sharp in a fight.
```

---

## Quick Start

1. Clone into `modules/` and build AzerothCore
2. Copy `conf/mod_llm_chatter.conf.dist` to your config directory and name it `mod_llm_chatter.conf`
3. Set your LLM provider and the matching API key (`LLMChatter.Anthropic.ApiKey`, `LLMChatter.OpenAI.ApiKey`, or no key when using Ollama)
4. Start the Python bridge
5. Play, bots start chatting when grouped with players

See [Setup](#setup) below for detailed Docker, non-Docker, and SQL preparation steps.

## Config notes

- The config file separates providers. Use `LLMChatter.Anthropic.ApiKey` when `LLMChatter.Provider` is `anthropic`, `LLMChatter.OpenAI.ApiKey` when `openai`, and leave both blank when pointing at a local Ollama instance with `LLMChatter.Provider = ollama`.
- Feature toggles such as `LLMChatter.GroupChatter.Enable` and `LLMChatter.RaidChatter.Enable` live in `mod_llm_chatter.conf.dist` around lines 241–394, and the same file documents every remaining option you might tune.
- Optional steps (talent data load, weather tuning, transport guards) are described by the comments inside `conf/mod_llm_chatter.conf.dist`; follow those when you need finer control.

---

## Features

* **Roleplay-first**: Every prompt blends race, class, lore, and assigned personality traits so bots feel like living companions. Roleplay mode keeps speech grounded in lore while Normal mode lets them relax into MMO-style chatter.
* **Spatial awareness**: Bots always know exactly where they are — both the parent zone and the specific subzone. Walking into "Ruins of Mathystra" within Darkshore gives bots rich lore context about that specific place, sourced from ~3,000 subzone descriptions. Zone transitions, idle chatter, nearby object comments, discovery reactions, and player conversations all reflect the current location.
* **Conscious world sensing**: Bots mind moonwells, forges, transports, holidays, weather, time of day, rare creatures, and zone lore. That context follows through to prompts so each message references the right place, event, and faction.
* **Dynamic prompt engine**: The bridge stitches together randomized tones, moods, creative twists, humor nudges, and optional talent lore. Messages stay varied while still sounding like the same cast of bots.
* **Party interactivity**: Loot, combat (pulls, heals, CC, deaths, wipes), quests, nearby objects, and player chat all trigger the same narrative-aware path. Idle chatter, multi-bot conversations, and bot-initiated questions flow out of that system.
* **Event-grade delivery**: Combat hooks use pre-cached responses for instant delivery; ambient/world events respect delay tuning, priority ordering, and per-group locks so raid, battleground, holiday, and transport chatter stay cohesive.
* **Ambient chatter ecosystems**: Living General chat, battleground callouts (flags, nodes, scores, arrivals), and faction intrusion alerts sustain world chat without flooding players. Bots call you by name when relevant and optionally use emotes from the 3.3.5a set.
* **Raid consciousness**: Boss pull/kill/wipe reactions now cover 148 bosses across 22 raid instances plus between-pull morale chatter, wider zone lore, and verified raid-speaker delivery in party and raid channels.
* **Immersion-first tuning**: Everything from weather effects to transport timing, talent data, and lore references stays configurable in `mod_llm_chatter.conf.dist`. Transport alerts only fire where real players exist and use verified bot voices.

---

## Compatibility

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

Ollama works for local/free inference but requires fast hardware (sub-5s response times). See the config file header for details.

### Known Limitations
- Local Ollama on consumer hardware produces 15-70s latency, causing stale reactions
- Models below 4B parameters frequently fail to produce valid JSON

---

## Prerequisites

This module requires a working AzerothCore server with mod-playerbots. If you don't have one yet, start here:

- [AzerothCore Docker install guide](https://www.azerothcore.org/wiki/install-with-docker)
- [AzerothCore Playerbot branch](https://github.com/mod-playerbots/azerothcore-wotlk/tree/Playerbot)
- [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots)

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
- Bot memory and relationships that persist across sessions
- Open-world proximity encounters between bots and players
- New immersive features that deepen the living-world experience

---

## License

GNU AGPL v3, same as AzerothCore.

## Credits

- Uses [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots) for bot characters
- Powered by [Anthropic Claude](https://anthropic.com), [OpenAI GPT](https://openai.com), or [Ollama](https://ollama.ai)
