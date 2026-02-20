# mod-llm-chatter - Logic Documentation

This document explains the logic behind the LLM Chatter module, which generates dynamic bot conversations in General chat using AI.

---

## Overview

The module creates the illusion of a living world by having playerbots chat naturally in General chat. Instead of static database messages, an LLM generates contextual, varied conversations based on zone, quest, and loot data.

**Supported Providers:**
- **Anthropic**: Claude Haiku (default), Sonnet, Opus - cloud, requires API key
- **OpenAI**: GPT-4o, GPT-4o-mini - cloud, requires API key
- **Ollama**: Qwen3, Llama, Mistral, and other local models - runs locally, FREE

Configure via `LLMChatter.Provider` and `LLMChatter.Model` in the config file.

**Chatter Mode:**
- **Normal** (default): Casual MMO chat with abbreviations, game terms, OOC references
- **Roleplay**: In-character speech influenced by race and class - natural and conversational, not theatrical

Configure via `LLMChatter.ChatterMode` (`normal` or `roleplay`).

**Quick Provider Switch:**
```ini
# Cloud (Anthropic - best quality)
LLMChatter.Provider = anthropic
LLMChatter.Model = haiku

# Cloud (OpenAI - good alternative)
LLMChatter.Provider = openai
LLMChatter.Model = gpt4o-mini

# Local (Ollama - free, runs on your machine)
LLMChatter.Provider = ollama
LLMChatter.Model = qwen3:4b
```

---

## 1. Trigger System

### When Does Chatter Trigger?

The system checks for new chatter opportunities on a regular interval.

| Setting | Default | Description |
|---------|---------|-------------|
| TriggerIntervalSeconds | 60 | How often the system checks for chatter opportunities |
| TriggerChance | 30% | Probability that each check actually triggers chatter |
| MaxPendingRequests | 5 | Maximum queued requests (prevents backup if LLM is slow) |

**Flow:**
1. Every 30 seconds, the server checks if it should trigger chatter
2. Rolls a 60% chance - if it fails, nothing happens
3. If successful, proceeds to find bots in the player's zone

### Where Can Chatter Happen?

**Overworld Only** - Chatter only triggers in the open world, NOT in:
- Dungeons
- Raids
- Battlegrounds
- Arenas

This is enforced by checking if the player's map is "instanceable" - if yes, chatter is disabled.

---

## 2. Zone Selection

### Finding the Player's Zone

The system finds the zone where **you** (the logged-in player) are:

1. Scan all online players
2. Filter out playerbots (only count real players)
3. Filter out players in instances (dungeons, raids, etc.)
4. Get the zone ID where the real player is

**Result:** Since you can only be logged in with one character at a time, this returns YOUR current zone. Chatter will happen where you are, making it feel like the world is alive around you.

---

## 3. Bot Selection

### Which Bots Can Chat?

Once the zone is identified, the system finds eligible bots:

**Eligibility Requirements:**
1. Bot is in the same zone as the player
2. Bot is the same faction as the player
3. Bot is alive and in the world
4. **Bot is NOT grouped with a real player**
5. **Bot is a member of the General channel** for the current zone (verified via `CanSpeakInGeneralChannel()`)

Rule 4 is important: if you invite bots to your party, those bots won't randomly chatter. They're "your" bots. Only independent, roaming bots participate in ambient chatter.

Rule 5 prevents silent message drops: playerbots join/leave channels based on their own lifecycle, and not all bots in a zone are guaranteed to have joined that zone's General channel. `CanSpeakInGeneralChannel()` checks via `ChannelMgr` and `Player::IsInChannel()` that the bot is actually a member. If a zone has 4 bots but only 2 are in the General channel, conversations are limited to those 2.

**Note:** These exclusions apply to ALL chatter paths:
- **C++ triggered chatter** (statements/conversations): `TryTriggerChatter()` and `OnPlayerCanUseChat()` apply the channel membership filter directly.
- **Event-triggered chatter** (transport arrivals, weather events): C++ collects channel-verified bot GUIDs in the event handler (e.g., `CheckTransportZones()`) and includes them as `verified_bots` in the event's `extra_data` JSON. Python filters its bot SQL query results against this list, ensuring only verified bots participate in LLM conversations.

### Bot List Refresh

The bot list is **dynamically refreshed** every trigger cycle. If a new bot enters the zone, they become eligible for the next chatter opportunity.

---

## 4. Message Types

### Distribution

Each chatter event randomly selects a message type:

| Type | Chance | Description |
|------|--------|-------------|
| Plain | 65% | General chat, no links |
| Quest | 15% | Mentions a zone quest with clickable link |
| Loot | 12% | Mentions an item drop with clickable link |
| Quest + Reward | 8% | Mentions quest completion and item reward |

### Statement vs Conversation

Each trigger also decides between:
- **Statement** (1 bot, 1 message) - 50% chance
- **Conversation** (2-4 bots, multiple messages) - 50% chance

**Conversation Participant Distribution:**
- 2 bots: 50% of conversations
- 3 bots: 30% of conversations
- 4 bots: 20% of conversations

The number of messages scales with participants (minimum = bot count, maximum = bot count + 3), creating natural group discussions.

**Participant Enforcement (3+ bots):** For conversations with 3 or more bots, the prompt explicitly requires every speaker to have at least one message ("EVERY speaker MUST have at least one message — do NOT skip any participant"). This prevents the LLM from generating fewer messages than requested, which was observed to silently drop participants in 3-bot conversations. Applied to all 7 conversation prompt builders (6 General + 1 group idle). Raw LLM response is logged before parsing at all call sites for diagnostics.

If there aren't enough bots for a conversation, it falls back to a statement.

---

## 4.1 Weather Context

Weather is integrated naturally into all messages rather than being a separate message type.

**How it works:**
1. C++ tracks current weather state per zone in `_zoneWeatherState` map
2. Weather state is passed to Python with every queue entry
3. All prompt builders receive weather/time through `get_environmental_context()`
4. **Randomized inclusion** prevents LLM from always mentioning time/weather:
   - 40% chance: time context only
   - 30% chance: weather context only
   - 20% chance: both time and weather
   - 10% chance: neither (no environmental context)
5. LLM can naturally reference weather/time when provided in context

**Weather Types:**
The C++ `GetWeatherStateName()` function provides human-readable weather types:
- clear, foggy
- light rain, rain, heavy rain
- light snow, snow, heavy snow
- light sandstorm, sandstorm, heavy sandstorm
- thunderstorm
- black rain, black snow (special scripted weather)

**Weather Events (Two-Tier System):**

1. **Weather Change** (`weather_change`): Fires on actual weather transitions (e.g., clear -> rain). Always triggers 100% — the `alwaysFire` flag bypasses the normal `EventReactionChance` RNG gate. This ensures weather transitions are never silently dropped.

2. **Weather Ambient** (`weather_ambient`): Fires periodically during ongoing weather. `CheckAmbientWeather()` iterates `_zoneWeatherState` every `WeatherAmbientCooldownSeconds` (default 120s) and queues events for zones with active (non-clear) weather and a real player present. Subject to normal `EventReactionChance` (15%). Ambient descriptions differ from transition descriptions — they describe ongoing conditions rather than the moment of change.

**Config:**
- `LLMChatter.Events.Weather = 1` - Enable weather events (both change and ambient)
- `LLMChatter.WeatherAmbientCooldownSeconds = 120` - Seconds between ambient weather checks per zone

---

## 4.2 Transport Events

Bots can react to transport arrivals (boats, zeppelins) when they dock in a zone.

**Config:**
- `LLMChatter.Events.Transports = 1` - Enable transport events
- `LLMChatter.TransportEventChance = 50` - Chance (%) to trigger on arrival (single C++ gate)
- `LLMChatter.TransportCooldownSeconds = 300` - Cooldown per transport+zone (5 min)

**How it works:**
1. C++ tracks transport zone changes as they sail
2. When a transport enters a zone (from zone 0 or another zone), a 50% chance roll decides whether to queue an event
3. C++ collects bots in the zone, filters through `CanSpeakInGeneralChannel()`, and includes their GUIDs as `verified_bots` in the event's `extra_data`
4. Events only process for zones with both bots AND a real player present
5. Python filters bot candidates against `verified_bots` — only channel-verified bots participate
6. Per-route cooldown (300s) prevents the same boat announcing multiple times per trip

**Context provided to LLM:**
- Transport type (boat, zeppelin, turtle)
- Ship name (e.g., "The Moonspray", "The Bravery", "Elune's Blessing")
- Current location (where the transport arrived - where bots ARE)
- Origin (where it came from - where bots can GO if they board)

**Direction Clarity:**
The context explicitly explains that bots are AT the arrival location and if they want to board, they travel TO the origin. The C++ `ParseTransportName()` always assigns the second DB stop as "destination" regardless of travel direction, so Python `build_event_context()` compares the event's `zone_id` name against origin/destination and swaps them if the zone matches origin. This ensures correct direction at any stop along the route.

---

## 4.3 Holiday Events

Bots celebrate in-game holidays (Lunar Festival, Love is in the Air, etc.) with contextual chatter in all zones where real players are present.

**3 Unified Holiday Paths:**

All holiday detection funnels through the same `QueueHolidayForCities()` static free function:

1. **OnStart** -- a holiday begins while the server is running
2. **Startup detection** -- holidays already active when the bridge starts
3. **Periodic `CheckActiveHolidays()`** -- recurring check so the festive mood stays alive over time, not just at the moment a holiday starts

**How it works:**
1. `QueueHolidayForCities()` finds zones with real players present (capital cities and open-world)
2. For each qualifying zone:
   - **Capital cities** roll `HolidayCityChance` (default 10%) to decide whether to queue a holiday event
   - **Open-world zones** roll `HolidayZoneChance` (default 5%) to decide whether to queue a holiday event
3. Per-zone cooldowns prevent spam -- cooldown key format: `holiday:{eventId}:zone:{zoneId}`
4. Holiday reaction delay is 300-900 seconds (5-15 minutes) so messages feel organic, not instant
5. Holiday prompts explicitly require mentioning the event by name (uses "event" not "festival" to correctly handle PvP Call to Arms events alongside actual holidays)

**Capital City Filtering:**
- `CAPITAL_CITY_ZONES` set defined in `chatter_constants.py` lists the 11 capital city zone IDs
- Mob and loot queries return empty for capital cities (no hostile creatures to reference)
- This is intentional -- holiday chatter focuses on the event, not zone combat

**Config:**
- `LLMChatter.Events.Holidays = 1` -- Enable holiday events
- `LLMChatter.HolidayCooldownSeconds = 1800` -- Per-zone holiday cooldown (30 min)
- `LLMChatter.HolidayCityChance = 10` -- % chance per city per environment check
- `LLMChatter.HolidayZoneChance = 5` -- % chance per open-world zone per environment check
- `LLMChatter.EnvironmentCheckSeconds = 60` -- How often environment checks run

---

## 5. Zone Data Queries

### Quest Data

For quest-related messages, the system queries quests that:
- Belong to the current zone (via QuestSortID)
- Are appropriate for the bot's level (±5 levels)
- Have valid names (excludes "<UNUSED>" or "<NYI>" entries)

A random quest is picked from this pool to pass to the LLM.

**Data Retrieved:**
- Quest ID (for clickable link)
- Quest name
- Quest level
- Description (first 150 characters)
- Reward items (if any) with their quality

### Loot Data

For loot-related messages, the system retrieves items that could realistically drop in the zone:

**Gray/White Items (Common Drops):**
- Queried from creature loot tables
- Filtered by creature level matching zone level range
- Includes weapons, armor, and trade goods (cloth, leather, etc.)
- Only items with >5% drop chance (common drops)

**Green/Blue/Epic Items (World Drops):**
- Queried from reference loot tables (AzerothCore's world drop system)
- Reference table format: `102XXYY` = Green, `103XXYY` = Blue, `104XXYY` = Epic
- Filtered by RequiredLevel matching zone level range
- The database is the source of truth - epics can drop at any level where they exist

**Loot Reaction Messages:** Loot reaction messages post-process item names into clickable WoW item links via `format_item_link()`. This provides interactive feedback when bots comment on looted items.

### Mob Data (Zone-Specific Creatures)

For plain statements and conversations, the LLM may receive a random mob name from the zone for contextual flavor (e.g., "these Moonstalkers are everywhere").

**Hybrid Query Approach:**

The system uses a two-tier approach for maximum compatibility:

1. **Primary: Zone-specific query** - Uses `creature.zoneId` to find mobs actually spawned in the zone
   - Most accurate (only mobs from that specific zone)
   - Requires `Calculate.Creature.Zone.Area.Data = 1` in `worldserver.conf`
   - One-time server restart needed to populate zoneId data

2. **Fallback: Level-based query** - Uses creature level range matching zone levels
   - Works out of the box without config changes
   - May include mobs from other zones of similar level
   - Used automatically when zoneId data isn't populated

**For server administrators:** To get accurate zone-specific mobs, you can optionally populate zone data. This is **not required** - the module works without it using level-based fallback.

**Option 1: Enable zone calculation (recommended for non-Docker setups)**

1. Add to `worldserver.conf`:
   ```
   Calculate.Creature.Zone.Area.Data = 1
   ```

2. Restart the server once - startup will be slow (several minutes) as it calculates zones for ~150k creatures

3. After successful startup, disable the setting:
   ```
   Calculate.Creature.Zone.Area.Data = 0
   ```

4. Zone data persists in database - future startups are fast

**⚠️ Docker users: Important considerations**

Docker containers often have health checks or watchdog scripts that restart the server if startup takes too long. The zone calculation can trigger these timeouts, causing a restart loop.

**Workarounds for Docker:**

- **Multiple restart cycles**: Enable the setting and restart several times. Each cycle calculates more data before timing out. Eventually all zones get populated.

- **Increase timeouts**: Modify your Docker health check or entrypoint script to allow longer startup times (5+ minutes).

- **Run outside Docker once**: Start worldserver directly (not in Docker) with the setting enabled, let it complete, then return to Docker.

- **Accept the fallback**: The level-based fallback works fine - you may occasionally see mobs from similar-level zones, but it's not game-breaking.

**Checking progress:**
```sql
-- See how many creatures have zone data
SELECT COUNT(*) as total,
       COUNT(CASE WHEN zoneId > 0 THEN 1 END) as with_zone
FROM acore_world.creature;
```

**Mob Filtering:**
- Only hostile creatures (various hostile faction IDs)
- Only valid types: Beast, Dragonkin, Demon, Elemental, Giant, Undead, Humanoid, Mechanical
- Excludes triggers, invisible units, and system NPCs
- Name validation (excludes "(", "[", "<" prefixes, "DND", "Bunny", etc.)

### Zone Level Mapping

Each zone has a defined level range used for queries:

| Zone | Level Range |
|------|-------------|
| Darkshore | 10-20 |
| Westfall | 10-20 |
| Ashenvale | 18-28 |
| Stranglethorn Vale | 30-40 |
| ... | ... |

If a zone isn't mapped, the system falls back to bot level ±5.

### Caching

Zone data (quests, loot, and mobs) is cached for **10 minutes** to avoid repeated database queries. This improves performance without affecting variety. Mob data is cached by zone ID to ensure the same zone always gets the same mob pool during the cache window.

### Zone Flavor System

To create more immersive, atmosphere-aware messages, the module includes rich flavor descriptions for ~45 zones. These descriptions capture:
- The zone's atmosphere and mood
- Notable dangers and creatures
- Key landmarks and lore elements
- The "feel" of being in that zone

**Example (Darkshore):**
> "A somber, twilight coastline where ancient Night Elf ruins crumble into the sea. The corruption spreading from Felwood taints the northern forests while restless spirits and hostile wildlife make travel dangerous. Murlocs infest the beaches, furbolgs have turned aggressive, and the eternal dusk creates an atmosphere of faded glory and lurking danger."

The LLM uses this context as creative inspiration, producing messages that feel authentic to the zone rather than generic.

---

## 6. LLM Context

### What the LLM Receives

For each message type, the LLM receives specific context to generate authentic messages:

#### Plain Statement
```
- Bot level (e.g., 15)
- Bot race (e.g., Night Elf)
- Bot class (e.g., Hunter)
- Zone name (e.g., Darkshore)
```

#### Quest Statement
```
- Bot level, race, class, zone
- Quest name
- Quest level
- Quest description (150 chars)
```

#### Loot Statement
```
- Bot level
- Bot class (so LLM can react if item fits the class or not)
- Zone name
- Item name
- Item quality (gray/white/green/blue/purple)
```

#### Quest + Reward Statement
```
- Bot level, zone
- Bot class (so LLM can react to whether reward fits)
- Quest name, level
- Reward item name
- Reward item quality
```

#### Conversation (2-4 bots)
```
- Bot 1: name, level, race, class
- Bot 2: name, level, race, class
- Bot 3: name, level, race, class (if 3+ bots)
- Bot 4: name, level, race, class (if 4 bots)
- Zone name
- Zone flavor (rich atmosphere description)
- Zone mobs (10 random creatures from the zone)
- (Plus quest/item data if applicable)
```

Bot names are included so they can address each other naturally (e.g., "hey Milunnik, you done with that quest?").

**Bot Name Addressing:**
Prompts explicitly instruct the LLM to use bot names when addressing each other directly, creating more natural conversations.

**Fuzzy Name Matching:**
Since LLMs occasionally misspell names (e.g., "Thylalaeth" instead of "Thylaleath"), the bridge uses fuzzy matching with up to 2-character tolerance. This prevents messages from being dropped due to minor typos while still validating speaker identity.

### Prompt Guidelines

Each prompt includes:
1. **Examples** of good messages (short, casual, authentic)
2. **Critical rules** (length limits, placeholder usage, tone)
3. **Quality-specific guidance** (gray = meh, green = excited)
4. **Class awareness** (react if item fits class or not)

The LLM is instructed to:
- Keep messages SHORT (under 60 characters for statements)
- Sound like real players (casual, abbreviated, sometimes with typos)
- Use placeholders for links (`{quest:Name}`, `{item:Name}`)
- React appropriately to item quality AND class fit

### Strict Placeholder Enforcement

When quest or item links are required, the prompt uses strict language to ensure consistency:

```
REQUIRED: Include exactly {quest:Quest Name} in your message (this becomes a clickable link)
Example: anyone done {quest:Quest Name} yet? seems rough
```

This "REQUIRED" instruction with an explicit example ensures the LLM uses the exact placeholder format, which the bridge then converts to clickable WoW links.

---

## 7. Message Delivery

### Timing

Messages aren't delivered instantly. The system calculates realistic, varied delays:

**For Conversations:**
- Each reply has a delay based on message length + random "distraction" time
- Short replies can be quick (2-12 seconds)
- Longer messages have longer delays (typing time + distraction)
- Delays use uniform distribution for natural variation
- Maximum delay capped at 30 seconds (configurable)

| Message Length | Typical Delay |
|----------------|---------------|
| < 10 chars | 2-12 seconds |
| < 30 chars | 8-20 seconds |
| 30-80 chars | 12-25 seconds |
| 80+ chars | 15-30 seconds |

**Important:** The `MessageDelayMax` config setting caps all calculated delays. If set too low (e.g., 8000ms), all delays will cluster at that maximum, making conversations feel robotic. The default of 30000ms allows natural variation.

**Event Expiration:** Event expiration is calculated as `reactionDelay + eventExpirationSeconds` to ensure events with long reaction delays don't expire before firing. This guarantees that delayed reactions have adequate time to complete, even when the reaction delay is large.

### Link Replacement

Before delivery, placeholders are replaced with actual WoW links:

**Quest Link Format:**
```
{quest:Name} → |cFFFFFF00|Hquest:ID:LEVEL|h[Name]|h|r
```

**Item Link Format:**
```
{item:Name} → |cFFCOLOR|Hitem:ID:0:0:0:0:0:0:0|h[Name]|h|r
```

Item colors by quality:
- Gray: `FF9d9d9d`
- White: `FFffffff`
- Green: `FF1eff00`
- Blue: `FF0070dd`
- Purple: `FFa335ee`

**Message Cleanup:** The `cleanup_message()` function performs several post-processing steps:
- **Bracket Preservation**: Preserves brackets that are part of WoW links (checks for `|h` prefix)
- **Em-Dash Fix**: Replaces em-dashes (`—`) with comma-space (`, `) to avoid double-spacing
- **Emoji Removal**: Strips all emojis (they don't render in WoW chat) using comprehensive Unicode ranges

**NPC/Creature Links:**
```
[[npc:ID:Name]] → |cff00ff00Name|r
```
NPCs and creatures are displayed in green (friendly NPC color). These are not clickable in WoW 3.3.5 but provide visual highlighting. Zone mobs are queried with entry IDs to enable this formatting.

### Channel

All messages are sent to **General chat** in the zone, so the player will see them as ambient world activity.

### Stale Message Cleanup

When the server starts, any undelivered messages from a previous session are automatically cleaned up:
- Messages with `delivered = 0` are deleted
- Pending/processing queue entries are cancelled

This prevents old messages from appearing unexpectedly after a server restart or re-login.

### Polling Behavior

The C++ module continuously polls the database for messages to deliver (every `DeliveryPollMs` milliseconds). This simple approach ensures reliable message delivery without race conditions.

---

## 8. Complete Flow Example

**Scenario:** Real player Karaez is questing in Darkshore.

1. **Trigger Check** (every 60s)
   - Roll 30% chance → Success!

2. **Find Player's Zone**
   - Karaez is in Darkshore (zone 148) in the overworld
   - Zone confirmed as valid (not an instance)

3. **Determine Faction**
   - Karaez is Alliance
   - Look for Alliance bots

4. **Find Eligible Bots**
   - 4 Alliance bots in Darkshore
   - 1 is grouped with Karaez → excluded
   - 3 eligible bots remain

5. **Select Message Type**
   - Roll 1-100 → 78 → "Quest" type

6. **Statement or Conversation**
   - Roll → Conversation
   - Roll for bot count → 3 bots (30% chance)
   - Pick 3 bots: Milunnik (Druid), Velyell (Mage), Thylaleath (Hunter)

7. **Query Zone Data**
   - Get quests for Darkshore, level 10-20
   - Select "Beached Sea Turtle" quest
   - Get zone flavor (Darkshore atmosphere description)
   - Get 10 random zone mobs for context

8. **Generate with LLM**
   - Send context (names, classes, zone, quest, flavor, mobs) to Claude Haiku
   - Receive 5-message conversation (3-6 messages for 3 participants)

9. **Schedule Delivery**
   - Message 1: immediate
   - Message 2: +18 seconds
   - Message 3: +32 seconds
   - Message 4: +47 seconds
   - Message 5: +62 seconds

10. **Replace Links & Deliver**
    - `{quest:Beached Sea Turtle}` → clickable link
    - Bots speak in General chat

**Result in Chat:**
```
[General] Milunnik: hey anyone done [Beached Sea Turtle]?
[General] Velyell: yeah just found the last remains by the shore
[General] Thylaleath: same, the coastline is rough with all those Reef Crawlers tho
[General] Milunnik: nice ty for the tips
[General] Velyell: np, good luck out there
```

---

## 9. Configuration Summary

### Server Config (mod_llm_chatter.conf)

| Setting | Default | Description |
|---------|---------|-------------|
| Enable | 1 | Module on/off |
| ChatterMode | normal | `normal` (casual MMO chat) or `roleplay` (in-character RP) |
| EnableVerboseLogging | 1 | Detailed debug logging (disable in production) |
| TriggerIntervalSeconds | 60 | Check frequency |
| TriggerChance | 30 | % chance per check |
| ConversationChance | 50 | % for conversation vs statement |
| MaxPendingRequests | 5 | Queue limit |
| DeliveryPollMs | 1000 | How often to check for messages to deliver |
| MessageDelayMin | 1000 | Minimum delay between conversation messages |
| MessageDelayMax | 30000 | Maximum delay between conversation messages (keep high for varied delays) |

### Environment / Event Timing Config

| Setting | Default | Description |
|---------|---------|-------------|
| EnvironmentCheckSeconds | 60 | How often environment checks run (seconds) |
| HolidayCooldownSeconds | 1800 | Per-zone holiday event cooldown |
| HolidayCityChance | 10 | % chance per city per environment check |
| HolidayZoneChance | 5 | Chance (0-100) per check for holiday mention in open-world zones |
| DayNightCooldownSeconds | 7200 | Day/night transition cooldown |
| WeatherCooldownSeconds | 1800 | Weather transition event cooldown |
| WeatherAmbientCooldownSeconds | 120 | Ambient weather remark cooldown per zone |
| TransportCheckSeconds | 5 | Transport position check interval |

### LLM Config

| Setting | Default | Description |
|---------|---------|-------------|
| Provider | anthropic | LLM provider: `anthropic`, `openai`, or `ollama` |
| Model | haiku | Model alias or name (see below) |
| MaxTokens | 350 | Response length limit (350 needed to avoid JSON truncation in conversations) |
| Temperature | 0.8 | Creativity (0=focused, 1=creative) |

**Model Options:**
- **Anthropic aliases:** `haiku`, `sonnet`, `opus`
- **OpenAI aliases:** `gpt4o`, `gpt4o-mini`
- **Ollama:** Use exact model name from `ollama list` (e.g., `qwen3:4b`, `llama3.2:3b`)

### Ollama-Specific Config

| Setting | Default | Description |
|---------|---------|-------------|
| Ollama.BaseUrl | http://localhost:11434 | Ollama API endpoint |
| Ollama.ContextSize | 2048 | Context window size (smaller = faster) |
| Ollama.DisableThinking | 1 | Add /no_think to prompts (important for Qwen3) |

**Provider Notes:**
- **Claude Haiku** - Best instruction-following, recommended for quality
- **GPT-4o-mini** - Good alternative, may occasionally produce RP-style speech
- **Qwen3 (Ollama)** - Free local option, good quality with /no_think enabled

---

## 9.1 Bridge Startup Configuration Exposure

When the Python bridge starts, it prints all loaded configuration values to the logs, organized into logical sections:

**Startup Log Sections:**
1. **Chatter Configuration** - Core chatter settings (TriggerIntervalSeconds, TriggerChance, ChatterMode, etc.)
2. **Transport Configuration** - Transport event settings (TransportEventChance, TransportCooldownSeconds, etc.)
3. **Holiday Configuration** - Holiday event settings (HolidayZoneChance, HolidayCityChance, HolidayCooldownSeconds, etc.)
4. **Group Chatter Configuration** - Group event settings (group chat, kill, death, loot, spell cast, quest, etc.)

This organized output allows administrators to verify that all configuration values have loaded correctly and are set as expected. All hardcoded rate-limiting values have been exposed to the config file, so the startup log serves as a comprehensive verification checklist.

---

## 10. Design Principles

1. **Immersion** - Chatter should feel like real players, not NPCs
2. **Context-Aware** - Messages relate to the zone, quests, items, and class
3. **Non-Intrusive** - Happens in the background, doesn't spam
4. **Performance** - Caching, async processing, no game impact
5. **Realistic** - Appropriate items/quests for the zone level
6. **Respectful** - Your party bots don't randomly chatter
7. **Natural Variety** - Conversation length varies (2-5 messages)

---

## 11. General Channel Reactions

When a real player types in General channel, nearby bots react with statements or short conversations. This is entirely separate from group/party chatter — zone-scoped instead of group-scoped.

### Architecture

```
Player types in General → C++ OnPlayerCanUseChat(Channel*) hook
  → Store message in llm_general_chat_history
  → Per-zone cooldown check
  → RNG: 100% for questions (?), 80% for non-questions
  → Find 1-4 bots in same zone
  → INSERT player_general_msg event
  → Python bridge picks it up
    → Smart bot selection (name match → fuzzy → LLM context)
    → Build prompt with zone flavor, chat history, personality
    → Call LLM → queue response to llm_chatter_messages
    → DeliverPendingMessages() sends via SayToChannel(GENERAL)
    → Bot message stored in llm_general_chat_history
```

### Smart Bot Selection (3-Pass)

When a player addresses a specific bot, that bot should respond:

1. **Exact match** — Case-insensitive whole-word search (e.g., "Cylaea, eat some grass" → Cylaea)
2. **Fuzzy match** — Edit distance ≤ 2 for names ≥ 4 chars (e.g., "Thrandulion" → Thranduilion)
3. **LLM context analysis** — Quick Haiku call analyzes chat history to determine who the player is responding to contextually (e.g., player says "I'm sure you'll be fine" after a bot mentions eating poisonous food)

If no bot is identified, a random bot from the zone responds.

This same 3-pass system is used in both General channel and party chat.

### `quick_llm_analyze()` Utility

Reusable fast LLM call for pre-processing analysis. Always uses Haiku (fastest/cheapest) with low temperature (0.1) and small max_tokens. Located in `chatter_shared.py`.

Use cases:
- Determining which bot a player is addressing
- Classifying message intent or sentiment
- Summarizing context before building a full prompt

### Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `LLMChatter.GeneralChat.Enable` | `0` | Enable/disable General channel reactions |
| `LLMChatter.GeneralChat.ReactionChance` | `80` | % chance for non-question messages |
| `LLMChatter.GeneralChat.QuestionChance` | `100` | % chance for questions (ends with ?) |
| `LLMChatter.GeneralChat.Cooldown` | `15` | Per-zone cooldown in seconds |
| `LLMChatter.GeneralChat.ConversationChance` | `30` | % chance of 2-bot conversation vs single reply |

### Shared Settings

| Key | Default | Description |
|-----|---------|-------------|
| `LLMChatter.ChatHistoryLimit` | `10` | Max recent chat messages in LLM prompts (group + General). Clamped 1-50. |

### Quick Analyze Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `LLMChatter.QuickAnalyze.Provider` | (empty) | Provider for utility LLM calls (empty = use main provider) |
| `LLMChatter.QuickAnalyze.Model` | (empty) | Model for utility calls (empty = auto-select fastest) |

**Note on Lazy Client Caching:** When `QuickAnalyze.Provider` differs from the main `LLMChatter.Provider`, the Python bridge creates a separate LLM client instance with its own connection pool. This second client is lazily initialized on first use and persists for the lifetime of the bridge process, improving performance for repeated utility calls.

### C++ Bot Discovery

When General channel reactions are triggered, C++ discovers and sends **ALL eligible bots** (up to 8) to the Python bridge in the event queue. The Python code then applies intelligent bot selection (exact name match → fuzzy match → LLM context analysis) to determine which single bot responds. This design allows Python to make smart decisions about bot identity without requiring C++ to do name matching.

### Cooldown Timing

The per-zone cooldown only triggers **after a successful reaction** — if an RNG roll fails (e.g., TriggerChance check misses), the cooldown is NOT consumed. This allows the system to roll more frequently without excessive punishment for random failures.

### Database

**`llm_general_chat_history`** — Rolling chat history per zone (max configurable via `LLMChatter.ChatHistoryLimit`, default 10)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT UNSIGNED | Auto-increment PK |
| `zone_id` | INT UNSIGNED | Zone where message was sent |
| `speaker_name` | VARCHAR(64) | Bot or player name |
| `is_bot` | TINYINT(1) | 0=player, 1=bot |
| `message` | TEXT | Message content |
| `created_at` | TIMESTAMP | When message was sent |

### Files

| File | Purpose |
|------|---------|
| `LLMChatterScript.cpp` | OnPlayerCanUseChat hook + bot history storage |
| `LLMChatterConfig.h/.cpp` | 5 config fields |
| `chatter_general.py` | Prompt builders + event handler |
| `chatter_shared.py` | `find_addressed_bot()`, `quick_llm_analyze()` |
| `llm_chatter_bridge.py` | Dispatch entry |

---

## 12. Immersion Features (Session 36)

### 12.1 Emotes Between Bots

Bots play WoW emote animations (visible character model animations) when speaking.

**Two paths:**

| Path | When | How | Emote Source |
|------|------|-----|-------------|
| Conversation | JSON multi-message | LLM picks per message | `"emote"` field in JSON |
| Statement | Plain text single | Python keyword matching | `pick_emote_for_statement()` |

**Curated emote list (17 + "none"):**
talk, bow, wave, cheer, exclamation, question, laugh, roar, kneel, cry, applaud, shout, flex, shy, point, salute, dance

**Keyword matching** (`EMOTE_KEYWORDS` in `chatter_constants.py`):
~60 keywords mapped to emotes. Examples: "hello"→wave, "lol"→laugh, "nice"→cheer, "rip"→cry, "charge"→roar. 60% RNG gate — not every keyword match produces an emote.

**C++ delivery** (`DeliverPendingMessages`):
1. SELECT includes `emote` column
2. Fail-fast: message always marked `delivered=1` immediately (pre-check filter ensures bots can speak at selection time)
3. `SayToChannel()`/`SayToParty()` return value checked — `bool sent` tracks success
4. On failure: `LOG_WARN` with bot name and message ID (diagnostic only, no retry)
5. 60s staleness expiry: messages stuck undelivered >60s auto-expired as safety net
6. Emotes gated on send success: `GetEmoteId()` maps string to `EMOTE_ONESHOT_*` enum, `bot->HandleEmoteCommand(emoteId)` only fires if `sent == true`
7. Animation visible to all nearby players

**Validation chain:**
LLM output → `validate_emote()` (type check + strip + lowercase + EMOTE_LIST membership) → stored in DB → C++ `GetEmoteId()` → `HandleEmoteCommand()`

**Channel gating (Session 51):**
Emotes are proximity-based (`SMSG_TEXT_EMOTE` ~30-50 yard range), invisible to zone-wide General channel recipients. Three-layer protection ensures no emotes for General channel:
1. **Prompt layer**: All General channel prompt paths use `skip_emote=True` (statements) or `append_conversation_json_instruction()` which forces `"emote": null` (conversations). The 244-emote list is never shown to the LLM for General prompts, saving ~200+ input tokens per call.
2. **Database layer**: No `insert_chat_message()` call for General channel passes an `emote=` parameter. All stored emotes are NULL.
3. **C++ delivery layer**: `SendBotTextEmote()` only fires when `channel == "party"`. Even a hypothetical non-null emote in DB for General would be silently ignored.

**JSON format helpers (Session 51 refactor):**
- `append_json_instruction()` — single-message format `{message, emote, action}`, used by statement prompts and group handlers
- `append_conversation_json_instruction()` — array format `[{speaker, message, emote, action}, ...]`, used by all 6 conversation prompt builders. Emote always null (all conversations are General channel)

### 12.2 Session Mood Drift

Per-bot mood that evolves based on game events. Pure Python, no C++ changes.

**Data structure:** `_bot_mood_scores[(group_id, bot_guid)] = (score: float, timestamp: float)`

**Event deltas:**

| Event | Delta |
|-------|-------|
| kill | +1.0 |
| boss_kill | +2.0 |
| death | -2.0 |
| wipe | -3.0 |
| loot | +1.0 |
| epic_loot | +2.0 |
| resurrect | +1.0 |
| quest | +1.0 |
| levelup | +2.0 |
| achievement | +1.5 |

**Mood labels (score ranges):**
miserable (<-4), gloomy (-4 to -2), tired (-2 to -0.5), neutral (-0.5 to 0.5), content (0.5 to 2), cheerful (2 to 4), ecstatic (>4)

**Drift:** Each event applies MOOD_DRIFT_RATE (0.5) toward neutral before the event delta. Score clamped to [-6, 6].

**Prompt injection:** `if mood_label != 'neutral': prompt += f"\nCurrent mood: {mood_label}"`

**Cleanup:** Entries evicted after 2 hours (TTL). Eviction triggered when dict > 50 entries. `cleanup_group_moods(group_id)` available for explicit cleanup.

### 12.3 Farewell Messages

Pre-generated goodbye message delivered when a bot leaves the group.

**Generation (Python, `_generate_farewell()`):**
1. Called after greeting generation in `process_group_event()`
2. Small LLM call with bot's race, class, traits
3. Response cleaned and stored in `llm_group_bot_traits.farewell_msg` (VARCHAR 255)
4. Wrapped in try/except — failure doesn't affect greeting

**Delivery (C++, `OnRemoveMember()`):**
1. Gated behind `sLLMChatterConfig->_useFarewell`
2. Queries farewell_msg BEFORE deleting traits row
3. Builds `CHAT_MSG_PARTY` WorldPacket via `ChatHandler::BuildChatPacket()`
4. Sends to each remaining group member via `SendDirectMessage()`
5. Bypasses `ai->SayToParty()` (bot already removed from group at this point)

**Config:** `LLMChatter.GroupChatter.FarewellEnable = 1`

### 12.4 Item Link Reactions

Bots comment on items linked by players in party chat.

**Detection:** `detect_item_links(message)` regex extracts `(item_entry, item_name)` from WoW link format `|Hitem:ENTRY:...|h[Name]|h|r`

**Query:** `query_item_details(db, entry)` queries `acore_world.item_template` for:
- Quality, item class, subclass, ItemLevel, RequiredLevel
- AllowableClass bitmask, stat_type/value, damage, armor

**Formatting:** `format_item_context(items_info, bot_class)` builds human-readable context:
- Weapon subclass detail: "Two-Handed Sword", "Dagger", "Staff" (16 weapon types)
- Armor subclass detail: "Plate", "Cloth", "Shield" (6 armor types)
- Quality names: Poor/Common/Uncommon/Rare/Epic/Legendary
- Equipability: always shown for weapons/armor ("Warrior CAN equip")

**Prompt injection:** Added as `item_context` parameter to `build_player_response_prompt()` with instruction to comment from class/role perspective.

### 12.5 Centralized INSERT Helper

`insert_chat_message()` in `chatter_shared.py` replaces ~25 individual INSERT statements:

```python
insert_chat_message(
    db, bot_guid, bot_name, message,
    channel='party', delay_seconds=2.0,
    event_id=None, queue_id=None,
    sequence=0, emote=None,
)
```

- Handles emote column transparently via `validate_emote()`
- Parameterized queries (%s placeholders)
- Creates own cursor, commits transaction
- 29 call sites across 4 files

---

## 13. Racial Language Vocabulary

Each of the 10 playable races has a vocabulary of lore-accurate native language phrases stored in `RACE_SPEECH_PROFILES` (chatter_constants.py). These are injected into prompts to create authentic racial speech patterns.

### How It Works

1. `build_race_class_context()` in `chatter_shared.py` checks for a `vocabulary` field in the race profile
2. 15% of the time, a random phrase is selected and injected into the prompt
3. The injection uses soft language: "You may naturally weave in a phrase... Use it only if it fits — never force it."
4. This matches the existing 15% lore injection rate

### Vocabulary Format

Each vocabulary entry is a tuple of `(phrase, meaning)`:

```python
"vocabulary": [
    ("Bal'a dash, malanore", "Greetings, traveler"),
    ("Shorel'aran", "Farewell"),
    ("Selama ashal'anore", "Justice for our people"),
]
```

### Races and Languages

| Race | Language | Example Phrases |
|------|----------|-----------------|
| Human | Common | "Light be with you", "By the Light!" |
| Night Elf | Darnassian | "Ishnu-alah", "Elune-adore" |
| Dwarf | Dwarven/Common | "By Muradin's beard!", "Keep yer feet on the ground" |
| Gnome | Gnomish/Common | "By the cogs!", "Eureka!" |
| Draenei | Draenei | "Eredar manari, archimonde", "Dioniss aca" |
| Orc | Orcish | "Lok'tar ogar!", "Zug zug" |
| Troll | Zandali | "Jah mon", "Stay away from da voodoo" |
| Undead | Gutterspeak | "Dark Lady watch over you", "What joy is there in this curse?" |
| Tauren | Taur-ahe | "Earth Mother guide you", "Walk with the Earthmother" |
| Blood Elf | Thalassian | "Bal'a dash, malanore", "Selama ashal'anore" |

All phrases are verified as WotLK-era canonical (3.3.5a). No post-WotLK content (e.g., Patch 8.2 Shal'dorei phrases are excluded).

---

## 13.1 Capital City Loot/Trade Skip

Ambient loot and trade messages are suppressed in capital cities to avoid immersion-breaking content like bots discussing "finding [item] in the Trade District."

### How It Works

In `process_statement()` (llm_chatter_bridge.py), when the zone is in `CAPITAL_CITY_ZONES`:
- `loot` and `trade` message types are converted to `plain`
- `quest` messages are **preserved** since cities have quest givers
- This only affects ambient General chat, not group loot reactions

### Capital Cities

The `CAPITAL_CITY_ZONES` set (from chatter_constants.py) includes all 11 faction capitals: Stormwind, Ironforge, Darnassus, Exodar, Orgrimmar, Thunder Bluff, Undercity, Silvermoon, Shattrath, Dalaran, and the Crossroads area.

---

## 13.2 Corpse Run Reactions

When a bot in the player's party dies and releases spirit, another bot in the group reacts with personality-appropriate commentary about the ghost run.

### Architecture

```
Bot dies → releases spirit → OnPlayerReleasedGhost(Player*) fires
  → Check: bot is in group with real player
  → RNG: 80% chance (configurable)
  → Per-group cooldown: 120s (configurable)
  → INSERT bot_group_corpse_run event
  → Python picks up event
    → Get bot personality traits
    → Build zone-aware ghost/corpse run prompt
    → Call LLM → queue response to party chat
```

### Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `LLMChatter.GroupChatter.CorpseRunChance` | `80` | % chance to react to bot death+release |
| `LLMChatter.GroupChatter.CorpseRunCooldown` | `120` | Per-group cooldown in seconds |

### Prompt Context

The corpse run prompt includes:
- Who died (bot name, class, race)
- Zone name and atmosphere
- Ghost run context ("running back as a ghost to their corpse")
- Bot personality traits (tone, mood, creative twist)
- Recent chat history for continuity
- RP mode support with race/class personality

### Technical Notes

- Uses `OnPlayerReleasedGhost(Player*)` hook (NOT `OnPlayerRepop` which doesn't exist)
- Fires for both bot AND player deaths — when the player releases spirit, a bot reacts with concern
- `react_after` = 5 seconds, `expires_at` = 120 seconds
- A different bot from the dead entity reacts (uses `GetRandomBotInGroup` with exclude)
- Prompt differentiates: player death gets "Your party leader {name}" framing, bot death gets first-person "You just died"
- `is_player_death` and `dead_name` in extra_data distinguish the two paths

---

## 13.3 Group Role Awareness

Bots in RP mode now have combat role perspective injected into all prompts. Tanks talk about aggro and positioning, healers worry about health bars and mana, DPS brag about damage.

### Architecture

Two new constants in `chatter_constants.py`:

- **`CLASS_ROLE_MAP`** — maps all 10 WoW classes to 6 roles:
  - `tank`: Warrior, Death Knight
  - `healer`: Priest
  - `melee_dps`: Rogue
  - `ranged_dps`: Hunter, Mage, Warlock
  - `hybrid_tank`: Paladin, Druid
  - `hybrid_healer`: Shaman

- **`ROLE_COMBAT_PERSPECTIVES`** — 3-4 sentence combat perspective per role, appended to `build_race_class_context()` output

### How It Works

1. `build_race_class_context()` in `chatter_shared.py` looks up the class in `CLASS_ROLE_MAP`
2. If found, appends the matching `ROLE_COMBAT_PERSPECTIVES` entry to the prompt parts
3. Each perspective ends with "Only reference your role during combat situations" to suppress combat language in ambient prompts
4. Propagates to all 19+ prompt builders automatically — no call-site changes

### Mode Gating

- **RP mode only** — every call site gates `build_race_class_context()` behind `is_rp` check
- In normal mode, role perspectives are never injected

### Example Output

Tauren Warrior:
> As a Tauren, you tend to be calm and stoic... As a Warrior, you are direct and battle-tested... Your group role is to lead the charge and take hits so others don't have to. You think about positioning, threat, and keeping enemies focused on you.

Night Elf Priest:
> As a Night Elf, you tend to be ancient and contemplative... As a Priest, you are contemplative and empathetic... Your group role is keeping everyone alive. You watch health bars constantly, manage your mana carefully, and worry when someone takes unexpected damage.

---

## 13.4 Group Composition Commentary

When a bot joins a group, it has a 50% chance to make a one-sentence comment about the group's role composition (e.g. "No healer? This should be interesting.").

### Architecture

```
Bot joins group → process_group_event() step 7b
  → _maybe_comment_on_composition() (50% RNG)
  → _get_group_role_summary() queries traits+characters tables
  → Maps classes → roles via CLASS_ROLE_MAP
  → _build_composition_comment_prompt() with pointed observations
  → LLM call → insert message at 8s delay (sequence=2)
```

### Timing

| Step | Delay | Content |
|------|-------|---------|
| Greeting | 2s | Bot says hello |
| Welcome | 5s | Existing bot welcomes newcomer |
| Composition comment | 8s | Bot comments on group comp |

### Rules

- **50% chance** per join (hardcoded, not yet configurable)
- **2+ bots required** — single bot + player skips (nothing to comment on)
- **One short sentence** under 120 characters
- **No greeting** — prompt explicitly says "you already said hello"
- Missing tank/healer explicitly noted in prompt

---

## 14. Future Considerations

Potential enhancements:
- Guild recruitment messages

**Completed Enhancements:**
- ✅ Zone flavor system (~45 zones with rich atmosphere descriptions)
- ✅ 2-4 bot conversations (50% 2-bot, 30% 3-bot, 20% 4-bot)
- ✅ Varied message delays (uniform distribution, 45s max)
- ✅ Bot name addressing in conversations
- ✅ Fuzzy name matching for LLM typos
- ✅ Transport arrival chatter (boats, zeppelins with destination info)
- ✅ Weather event chatter (zone-appropriate weather types)
- ✅ Zone-filtered loot (coordinate-based creature queries)
- ✅ CREATIVE_TWISTS system (47 random modifiers for unpredictability)
- ✅ Expanded MESSAGE_CATEGORIES (80+ categories)
- ✅ Weather context in all prompts (natural integration with guidance)
- ✅ Transport direction clarity (bots correctly indicate travel direction)
- ✅ Grouped bot filtering for events (event chatter respects party membership)
- ✅ Mood logging for all statement types (quest, loot, quest+reward)
- ✅ EnableVerboseLogging config option (for production deployment)
- ✅ ChatterMode toggle: normal vs roleplay (configurable)
- ✅ Race/class personality profiles (10 races, 10 classes) for RP mode
- ✅ RP constant sets: tones (20), moods (20), twists (14), categories (40), length hints (4)
- ✅ Expanded normal TONES from 9 → 20 entries
- ✅ Toned down RP from theatrical to "RP server casual"
- ✅ Full prompt logging for tuning (temporary)
- ✅ Removed trail-off twists (looked like truncated output)
- ✅ Fixed numeric race/class ID bug in prompt builders
- ✅ Group chatter: greeting, kill, death, loot, idle, player response, level-up, quest, achievement reactions
- ✅ Spell cast reactions (heal, resurrect, shield, CC, buff) with caster-as-reactor pattern
- ✅ Quest objectives completion reactions (before turn-in)
- ✅ Race worldview + lore context for RP mode
- ✅ Enriched CLASS_SPEECH_MODIFIERS with detailed descriptions
- ✅ SQL escaping fix for event hooks
- ✅ Event identity fix (actor vs reactor distinction)
- ✅ Full config exposure of all hardcoded RNG values
- ✅ Account character bot support (ObjectAccessor::FindPlayer)
- ✅ Trade channel integration
- ✅ Responding to real player party chat
- ✅ Time-of-day always passed to prompts
- ✅ Racial language vocabulary for all 10 races (WotLK-era phrases)
- ✅ Capital city loot/trade message skip
- ✅ Corpse run reactions (ghost run commentary in party chat)
- ✅ Resurrection thanks — bot thanks the healer after being rezzed
- ✅ Zone transition comments — bot comments when entering a new zone
- ✅ Dungeon entry reactions — bot comments when entering an instance
- ✅ Group wipe reactions — bot reacts when entire party dies
- ✅ Seasonal/event-based chatter (holiday system)
- ✅ Greeting name personalization (80% in 2-person groups)
- ✅ Proportional response rule (short answers for simple messages)
- ✅ Name addressing in conversations (40% RNG, party + general)
- ✅ "Festival" → "event" holiday prompt fix
- ✅ Emote animations (LLM-picked for conversations, keyword matching for statements)
- ✅ Session mood drift (per-bot mood evolves from game events, influences tone)
- ✅ Farewell messages (pre-generated goodbye when bots leave group)
- ✅ Item link reactions (bots comment on items linked in party chat)
- ✅ Centralized INSERT helper (`insert_chat_message()` replaces ~25 individual INSERTs)
- ✅ Group role awareness (CLASS_ROLE_MAP + ROLE_COMBAT_PERSPECTIVES for all RP prompts)
- ✅ Group composition commentary (50% chance comment on group comp after joining)
- ✅ Reactive bot state (C++ BuildBotStateJson injects health/mana/role/target into prompts)
- ✅ API error context logging (call_llm context param across 31+ sites)
- ✅ Third-person narration stripping (two-phase post-processing)
- ✅ Pre-cached reactions (instant delivery for combat/spell/state events, Session 41b/42)
- ✅ Loot reactor randomization (50% self, 50% groupmate — Session 42)
- ✅ Quest completion dedup (30s window per group+quest — Session 42)
- ✅ Multi-speaker truncation in cleanup_message() (Session 42)
- ✅ OOM class filtering for non-mana classes in pre-cache (Session 42)

---

## 15. Dynamic Prompt Building (Anti-Repetition)

### The Problem

LLMs can fall into predictable patterns when given static prompts or concrete examples. If we show the LLM example messages, it will copy those patterns. This becomes noticeable and breaks immersion.

### The Solution: Randomized Prompt Construction + Creative Twists

Instead of static prompts with examples, we build prompts dynamically with randomized elements and NO concrete examples. The key insight: **we provide creative direction, not examples to copy**.

### Core Components

**1. MOODS (25 single-word moods)**

Each message gets a random mood that influences its emotional tone:

```python
MOODS = [
    "questioning", "complaining", "happy", "disappointed", "joking around",
    "slightly sarcastic", "enthusiastic", "confused", "proud", "neutral",
    "dramatic", "deadpan", "roleplaying", "nostalgic", "impatient",
    "grateful", "showing off", "self-deprecating", "philosophical", "surprised",
    "helpful", "geeky", "tired", "competitive", "distracted",
]
```

**Important:** Moods are single words with NO examples. Examples cause pattern copying.

**2. TONES (overall conversation feel)**

```python
TONES = [
    "casual and relaxed", "slightly tired from grinding", "focused on gameplay",
    "a bit bored", "curious about the zone", "just vibing", ...
]
```

**3. MESSAGE_CATEGORIES (80+ categories)**

For statements, a random category guides what the message is about:

```python
MESSAGE_CATEGORIES = [
    # Observations
    "commenting on zone atmosphere", "noticing something unusual", ...
    # Reactions - positive
    "celebrating a small victory", "appreciating the scenery", ...
    # Atmospheric
    "describing the ambient sounds", "noting the lighting or shadows", ...
    # Mystical
    "sensing something magical nearby", "pondering ancient mysteries", ...
    # Nostalgic
    "remembering an old guild", "thinking about early leveling days", ...
]
```

**4. CREATIVE_TWISTS (47 random modifiers)**

Applied 30-40% of the time to add unpredictable structure or content:

```python
CREATIVE_TWISTS = [
    # Structure twists
    "Start with an interjection",
    "End mid-thought with ...",
    "Use a single word or two-word reaction",

    # Content twists
    "Reference a made-up guild drama",
    "Mention a keybind or UI element",
    "Include a minor complaint about bag space",

    # Tone twists
    "Sound like you just woke up",
    "Be overly dramatic about something minor",

    # Player behavior twists
    "Reference being AFK",
    "Mention checking the auction house",

    # Social twists
    "Respond as if you misheard something",
    "Give unsolicited advice",

    # Expression twists
    "Trail off at the end",
    "Use excessive abbreviations",
]
```

### Why NO Concrete Examples

Previous approach had example messages like:
```
Examples: "nice drop!", "vendor trash lol", "finally got it"
```

**Problem:** The LLM copies these patterns verbatim, leading to repetitive messages.

**Solution:** Replace examples with abstract guidelines:
```
Guidelines: Be creative and unpredictable
```

The creativity comes from the combination of tone + mood + category + twist, not from copying examples.

### How Components Combine

Each message gets:
1. **Tone** (overall feel)
2. **Mood** (emotional state)
3. **Category** (topic/focus) - for statements
4. **Creative Twist** (30-40% chance) - structural modifier

Example logged output:
```
Prompt creativity: tone=focused on gameplay, mood=philosophical, category=talking about time played today, twist=Trail off at the end
```

This combination creates unique "personalities" per message without relying on copyable patterns.

### Chatter Mode (Normal vs Roleplay)

All prompt builders, selection functions, and dynamic guidelines are **mode-aware**. The mode is read from `LLMChatter.ChatterMode` at the start of each prompt build.

**Normal Mode** (default):
- Uses `TONES` (20), `MOODS`, `CREATIVE_TWISTS` (45), `MESSAGE_CATEGORIES` (80+), `LENGTH_HINTS`
- Casual MMO chat: abbreviations, game terms, OOC references allowed
- Guidelines: "Sound like a real player", can include typos, abbreviations
- Race/class context included 40% of the time for conversations
- Guideline: "Do NOT mention your race or class"

**Roleplay Mode:**
- Uses `RP_TONES` (20), `RP_MOODS` (20), `RP_CREATIVE_TWISTS` (14), `RP_MESSAGE_CATEGORIES` (40), `RP_LENGTH_HINTS`
- In-character speech influenced by race and class personality - natural and grounded, not theatrical
- Race/class personality built via `build_race_class_context(race, class_name)`:
  - `RACE_SPEECH_PROFILES`: 10 races with trait pools (8 variants each, `random.choice()`) and flavor_words (12 entries, `random.sample(4)`)
  - `CLASS_SPEECH_MODIFIERS`: 10 classes with modifier pools (8 variants each, `random.choice()`)
  - ~31,680 unique personality combinations per race/class pair
- Guidelines: "Stay in character but keep it natural and conversational, not dramatic or theatrical"
- Race/class context always included for all bots in conversations
- Guideline: "Stay in character but sound natural, not theatrical"
- Slightly higher long-message chance (+5, max 30%)

**Mode-Aware Functions:**
- `pick_random_tone(mode)` - selects from RP or normal tones
- `pick_random_mood(mode)` - selects from RP or normal moods
- `maybe_get_creative_twist(chance, mode)` - selects from RP or normal twists
- `pick_random_message_category(mode)` - selects from RP or normal categories
- `generate_conversation_mood_sequence(count, mode)` - mood pool from RP or normal
- `build_dynamic_guidelines(include_humor, include_length, config, mode)` - RP-specific guidelines

### Conversation Mood Sequences

For multi-bot conversations, each message gets its own mood, creating emotional arcs:

```python
mood_sequence = generate_conversation_mood_sequence(msg_count)
# Example: ['showing off', 'self-deprecating', 'neutral', 'distracted', 'helpful']
```

The LLM must follow the sequence, creating natural conversation flow.

### Logging for Monitoring

All creative selections are logged:
```
Prompt creativity: tone=X, mood=Y, category=Z, twist=W
Conversation creativity: tone=X, moods=[...], twist=W
```

This helps identify if certain combinations produce better results.

---

## 16. Community Distribution Goals

> **NOTE:** This section outlines requirements for when the module is ready for public release.

### Design Principles for Distribution

The target audience is **AzerothCore server administrators** - typically developers or technical users, but the setup process should still be straightforward and well-documented.

### Simplicity Requirements

**Installation should be simple:**
- Clone/copy module to `modules/` directory
- Run standard AzerothCore build process (no special flags or dependencies)
- Copy config template and add API key
- Start server - done

**Avoid:**
- Complex external dependencies beyond what AzerothCore already requires
- Convoluted multi-step setup processes
- Manual database modifications (use standard AC migration system)
- Custom build flags or cmake modifications
- Requiring users to install Python packages manually on the host

**Docker considerations:**
- The Python bridge should run as a simple container alongside the existing AC stack
- Provide ready-to-use docker-compose additions
- Document any timeout adjustments needed (e.g., for zone calculation)

### Required Documentation for Release

1. **README.md** - Quick start guide
   - Prerequisites (AzerothCore, Anthropic API key)
   - Installation steps (< 5 steps ideally)
   - Basic configuration
   - Troubleshooting common issues

2. **Configuration reference** - All settings explained with defaults

3. **Architecture overview** - For users who want to understand/modify

### Pre-Release Checklist

- [ ] Single-command installation where possible
- [ ] Clear error messages when API key missing or invalid
- [ ] Graceful fallback when Python bridge unavailable
- [ ] No compile-time warnings
- [ ] Config template well-commented
- [ ] SQL migrations follow AC conventions
- [ ] Docker setup tested on fresh environment
- [ ] README tested by someone unfamiliar with the module

### Cost Transparency

Users need to understand LLM API costs upfront:
- Document approximate cost per message (Claude Haiku is ~$0.0002/message)
- Provide recommended rate limiting settings
- Explain how to monitor usage

---

## 18. Non-Blocking Main Loop (Session 48)

### Architecture

The main loop in `llm_chatter_bridge.py` is now a pure fast fetch-and-dispatch coordinator. Three previously blocking operations were moved to the `ThreadPoolExecutor` worker pool:

| Operation | Previous | Now |
|-----------|----------|-----|
| `refill_precache_pool()` | Main thread (blocked 4+ minutes) | Worker thread via `precache_future` |
| `check_idle_group_chatter()` | Main thread (blocked 2-5s) | Worker thread via `idle_chatter_future` |
| `process_pending_requests()` | Main thread (blocked 2-5s) | Worker thread via `legacy_future` |

### Worker Wrapper

`_run_in_worker(fn_name, fn, client, config)` creates its own DB connection per invocation, matching the `process_single_event` pattern. Error logging happens only in the wrapper.

### At-Most-One Execution

Each background task tracks a single future. A new task is only submitted when the previous future is `None` (completed and harvested). This prevents concurrent refills, duplicate idle chatter, etc.

### Executor Pool Size

`ThreadPoolExecutor(max_workers=max_concurrent + 3)` — the +3 ensures background tasks don't starve event workers.

### Thread Safety

| Shared State | Lock Type | Why |
|-------------|-----------|-----|
| `_bot_mood_scores` | `threading.RLock()` | RLock because `update_bot_mood()` calls `_evict_stale_moods()` and `get_bot_mood_label()` — all access the dict |
| `_last_idle_chatter` | `threading.Lock()` + `_idle_inflight` set | Atomic cooldown check + inflight reservation. Cooldown only updates on success. `try/finally` releases inflight. |

### DB Connection Leak Fix

Main loop DB usage wrapped in `try/finally` — previously `db.close()` was skipped on exception. Startup `reset_stuck_processing_events` also wrapped.

---

## 19. Config Extraction (Session 48)

Eight hardcoded C++ values extracted to config variables:

| Config Key | Default | Was | What it controls |
|-----------|---------|-----|-----------------|
| `LLMChatter.GroupChatter.SpellCastCooldown` | 10 | 45 | Per-group cooldown between spell cast reactions |
| `LLMChatter.GroupChatter.LowHealthThreshold` | 25 | 25 | Health % for low-health callout |
| `LLMChatter.GroupChatter.OOMThreshold` | 15 | 15 | Mana % for OOM callout |
| `LLMChatter.GroupChatter.CombatStateCheckInterval` | 5 | 5 | Seconds between combat state checks |
| `LLMChatter.GroupChatter.QuestDeduplicationWindow` | 30 | 30 | Seconds to dedup quest completions |
| `LLMChatter.MaxBotsPerZone` | 8 | 8 | Max bots reacting in a zone |
| `LLMChatter.MaxMessageLength` | 250 | 250 | Chat message length cap |
| `LLMChatter.GeneralChat.HistoryLimit` | 15 | 15 | General chat history retention |

All values logged at startup and loaded via `sConfigMgr->GetOption<uint32>()`.

---

## 20. Quest Accept & Subzone Discovery Reactions (Session 48b)

### Quest Accept Reactions

When a player picks up a quest from an NPC, bots in the group comment on it.

**C++ Hook:** `AllCreatureScript::CanCreatureQuestAccept` — AzerothCore has no `PlayerScript::OnQuestAccepted` hook, so this uses the creature-side hook instead. Always returns `true` (non-blocking).

**Data flow:**
1. Player/bot accepts quest from NPC → `CanCreatureQuestAccept` fires
2. C++ extracts quest ID, name, level; checks group has real player
3. Dedup via `(groupId << 32) | questId` composite key, 30s window
4. INSERT `bot_group_quest_accept` event with quest context in `extra_data`
5. Python `process_group_quest_accept_event()` picks reactor bot
6. `build_quest_accept_reaction_prompt()` builds prompt — "we" language if bot accepted, observer language if player accepted
7. LLM generates reaction → party chat delivery

**Config:**
- `LLMChatter.GroupChatter.QuestAcceptChance = 100` — always fires
- `LLMChatter.GroupChatter.QuestAcceptCooldown = 30` — per-quest dedup window

### Quest Description Injection (Session 49)

All 3 quest hooks (accept, objectives, complete) now inject the quest's description and objectives text into `extra_data` so the LLM knows what the quest is actually about (not just name and level).

**C++ extraction:**
```cpp
"\"quest_details\":\"" +
    JsonEscape(quest->GetDetails().substr(0, 200)) + "\","
"\"quest_objectives\":\"" +
    JsonEscape(quest->GetObjectives().substr(0, 150)) + "\","
```

- `Quest::GetDetails()` returns the full description paragraph from the quest dialog
- `Quest::GetObjectives()` returns the short objectives list
- Both truncated to prevent prompt bloat (200/150 chars)
- `JsonEscape()` handles `\n`, `\r`, `\t`, quotes, backslashes, apostrophes
- Fields are empty string for quests without description/objectives — Python guards skip injection

**Python prompt injection:**
```python
quest_details = extra_data.get('quest_details', '')
quest_objectives = extra_data.get('quest_objectives', '')
# ... passed to prompt builder ...
if quest_details:
    quest_context += f" Quest description: {quest_details}"
if quest_objectives:
    quest_context += f" Objectives: {quest_objectives}"
```

**Quest prompt rewrites (Session 49):**
All 3 prompts were rewritten to use exclusive positive framing instead of negation:
- **Accept**: "Status: PREPARATION" — focus on task ahead, travel, plan of attack
- **Objectives**: "Status: PENDING TURN-IN" — focus on heading back, relief that hard work is done
- **Complete**: "TRANSACTION COMPLETE" — focus on XP, gold, reward, team celebration

### Subzone Discovery Reactions

When "Discovered: X" fires (exploration XP), bots react to the new area.

**C++ Hook:** `OnPlayerGiveXP` filtered by `xpSource == 3` (`XPSOURCE_EXPLORE` from Player.h:1002). Fires exactly when the "Discovered: X" message is sent to the client.

**Data flow:**
1. Player/bot enters new subzone → exploration XP fires
2. C++ extracts `areaId`, `area_name`, `area_level` from `AreaTableEntry`
3. Skip if `area_level == 0` (city sub-zones)
4. Dedup via `(groupId << 32) | areaId` composite key, 30s window (all bots discover simultaneously)
5. INSERT `bot_group_discovery` event
6. Python `process_group_discovery_event()` builds prompt with area context
7. LLM generates reaction → party chat delivery

**Config:**
- `LLMChatter.GroupChatter.DiscoveryChance = 40` — 40% chance
- `LLMChatter.GroupChatter.DiscoveryCooldown = 30` — per-area dedup window

---

## 21. Spell Classification Expansion (Session 48b)

The spell classification system in `OnPlayerSpellCast` was expanded to catch previously-missed support spell types.

### Categories

| # | Category | Effects/Auras | Example Spells |
|---|----------|---------------|---------------|
| 1 | Resurrect | `SPELL_EFFECT_RESURRECT`, `RESURRECT_NEW` | Resurrection, Rebirth |
| 2 | Heal | `SPELL_EFFECT_HEAL`, `HEAL_MAX_HEALTH`, `SPELL_AURA_PERIODIC_HEAL` | Flash Heal, Renew, Rejuvenation |
| 3 | Dispel | `SPELL_EFFECT_DISPEL` | Cleanse, Dispel Magic, Remove Curse |
| 4 | CC | Stun, root, fear, charm, confuse auras | Polymorph, Hammer of Justice |
| 5 | Shield | Absorb, immunity, `MOD_DAMAGE_PERCENT_TAKEN`, `SPLIT_DAMAGE_PCT/FLAT` | PW:Shield, Pain Suppression, Hand of Sacrifice |
| 6 | Buff | Stat, resistance, speed, haste, regen auras | MotW, Bloodlust, Innervate |

### Group-Wide Buff Targeting

Party/raid-wide buffs (Bloodlust, Prayer of Fortitude, Gift of the Wild, Greater Blessings, Arcane Brilliance) are self/area-targeted — `GetUnitTarget()` returns self or null. Previously these were silently rejected by the non-self target check.

**Fix:** `spellInfo->HasAreaAuraEffect()` detects spells using `SPELL_EFFECT_APPLY_AREA_AURA_PARTY`, `_RAID`, or `_FRIEND`. When true, the target check is skipped entirely. Single-target buffs still require a non-self groupmate target.

### Self-Cast Filter Bypass

After classification, a post-classification filter drops self-casts. Area aura buffs (where the caster IS the target) needed a bypass:

```cpp
bool isAreaBuff = spellInfo->HasAreaAuraEffect();
if (isAreaBuff) {
    targetName = "the group";
} else if (spellTarget) {
    targetName = spellTarget->GetName();
}
bool isSelfCast = (!isAreaBuff && spellTarget
    && spellTarget->GetGUID() == player->GetGUID());
if (isSelfCast) return;
```

### Python Dispel Category

New "dispel" case added to both caster and observer perspectives in the spell prompt builder (`chatter_group.py`).

---

*This document serves as the basis for the final README and user documentation.*
