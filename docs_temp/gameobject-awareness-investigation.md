# GameObject Awareness Chatter — Feasibility Investigation

As you walk through zones, dungeons, and cities with your group, a bot is occasionally picked at random. Nearby GameObjects within ~20 meters are detected around that bot, and the object data is fed to the LLM, which crafts a creative, in-character comment about what the bot notices. The message is assigned to that bot and displayed in party chat.

A Dwarf warrior passing a forge might say: "Now that's a proper anvil. Reminds me of the Great Forge back home."
A Night Elf druid near a moonwell: "I can feel Elune's presence here. The waters still hold her blessing."
A Warlock glancing at a skull pile: "Lovely décor. I should take notes."

---

## Verdict: Highly Feasible

AzerothCore and playerbots both have mature, battle-tested APIs for finding and inspecting nearby GameObjects. The grid search is efficient, the data model is rich, and playerbots already uses these exact patterns for loot detection, RPG behavior, and trap avoidance. No engine modifications needed — everything can be done from our module's C++ hooks.

---

## Core APIs

### Finding Nearby GameObjects

All methods live on `WorldObject` (which `Player` inherits from). Since bot players are `Player*`, we call these directly.

**Option A: All GOs in radius (what we want)**

The playerbots-proven pattern using `Cell::VisitObjects`:

```cpp
#include "CellImpl.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"

std::list<GameObject*> targets;
AnyGameObjectInObjectRangeCheck check(bot, radius);
Acore::GameObjectListSearcher<AnyGameObjectInObjectRangeCheck> searcher(bot, targets, check);
Cell::VisitObjects(bot, searcher, radius);
// targets now contains all spawned GOs with valid GOInfo within radius
```

The `AnyGameObjectInObjectRangeCheck` filter (from playerbots `NearestGameObjects.h`) accepts any GO that is:
- Within distance (`IsWithinDistInMap`)
- Spawned (`isSpawned()`)
- Has valid template data (`GetGOInfo()`)

**Option B: Convenience methods (for specific lookups)**

```cpp
// Find nearest single GO by type
GameObject* forge = bot->FindNearestGameObjectOfType(GAMEOBJECT_TYPE_SPELL_FOCUS, 22.0f);

// Find nearest single GO by entry ID
GameObject* go = bot->FindNearestGameObject(entryId, 22.0f);

// Find all GOs of specific entry in range
std::list<GameObject*> list;
bot->GetGameObjectListWithEntryInGrid(list, entryId, 22.0f);
```

**For our feature, Option A is the right choice** — we want to discover ALL interesting GOs nearby, not search for specific entries.

### Distance Units

WoW uses **yards** internally. 1 yard ≈ 0.9144 meters.

- 20 real meters ≈ **22 yards** — this is our target scan radius
- For reference: `INTERACTION_DISTANCE` is ~5 yards, playerbots `lootDistance` is 15 yards, `sightDistance` is 100 yards

22 yards is a small search radius that will typically touch only 1-4 grid cells. Very cheap.

---

## Data Available on Each GameObject

Once we have a `GameObject*`, we can extract:

### Identity

```cpp
go->GetEntry()                                    // uint32 — template/entry ID
go->GetGUID()                                     // ObjectGuid — unique instance ID
go->GetNameForLocaleIdx(sWorld->GetDefaultDbcLocale())  // string — localized display name
go->GetGOInfo()->name                             // string — English template name
go->GetDisplayId()                                // uint32 — visual model ID
```

### Type Classification

```cpp
go->GetGoType()                                   // GameobjectTypes enum
go->GetGOInfo()->type                             // Same as above, from template
go->GetGOInfo()->IconName                         // "Gear", "Point", "", etc.
```

### State

```cpp
go->isSpawned()                                   // bool — visible in world
go->GetGoState()                                  // GO_STATE_ACTIVE, GO_STATE_READY, GO_STATE_ACTIVE_ALTERNATIVE
go->getLootState()                                // GO_NOT_READY, GO_READY, GO_ACTIVATED, GO_JUST_DEACTIVATED
go->HasFlag(GAMEOBJECT_FLAGS, GO_FLAG_IN_USE)     // Currently being used
go->HasFlag(GAMEOBJECT_FLAGS, GO_FLAG_LOCKED)     // Locked (key/skill needed)
go->HasFlag(GAMEOBJECT_FLAGS, GO_FLAG_NOT_SELECTABLE)  // Invisible/non-interactive
```

### Template Details

```cpp
GameObjectTemplate const* info = go->GetGOInfo();
info->size                                        // float — scale factor
info->IsForQuests                                 // bool — quest-related

// Type-specific union fields (examples):
info->spellFocus.focusId                          // SPELL_FOCUS type: forge, anvil, campfire, etc.
info->chest.lootId                                // Chest: loot table reference
info->chest.lockId                                // Chest: lock requirement
info->trap.spellId                                // Trap: what spell it casts
info->chair.slots                                 // Chair: number of seats
info->chair.height                                // Chair: seat height
info->goober.spellId                              // Goober: spell on click
info->door.lockId                                 // Door: lock requirement
```

### Spatial

```cpp
bot->GetDistance(go)                               // float — 3D distance in yards
bot->GetDistance2d(go)                             // float — 2D (XY) distance
go->GetPositionX/Y/Z()                            // World coordinates
bot->IsWithinLOSInMap(go)                         // bool — line of sight check
```

---

## GameobjectTypes Enum (Full List)

These are the 36 GO types. The **bolded** ones are the most interesting for ambient chatter.

| Value | Type | Examples | Chatter Interest |
|-------|------|----------|-----------------|
| 0 | `DOOR` | Instance doors, gates | Low — mostly mechanical |
| 1 | `BUTTON` | Levers, switches | Low |
| 2 | `QUESTGIVER` | Quest boards, stones | Medium — "Wonder what's posted here" |
| **3** | **`CHEST`** | **Treasure chests, herb nodes, mining nodes** | **High — loot/gathering fantasy** |
| 4 | `BINDER` | Inn binding stones | Low |
| **5** | **`GENERIC`** | **Statues, banners, decorations, shrines** | **High — lore, atmosphere** |
| 6 | `TRAP` | Hidden traps | Medium — danger awareness |
| **7** | **`CHAIR`** | **Chairs, benches, thrones** | **Medium — "Take a seat" moments** |
| **8** | **`SPELL_FOCUS`** | **Forges, anvils, campfires, cooking fires, moonwells, altars** | **High — class/profession fantasy** |
| **9** | **`TEXT`** | **Plaques, books, signs, gravestones, monuments** | **High — lore, reading** |
| **10** | **`GOOBER`** | **Clickable objects: levers, crystals, ritual objects, relics** | **High — mystery, curiosity** |
| 11 | `TRANSPORT` | Elevators | Low |
| 12 | `AREADAMAGE` | Area damage zones | Low |
| 13 | `CAMERA` | Cinematic triggers | None |
| 14 | `MAP_OBJECT` | Map decorations | None |
| 15 | `MO_TRANSPORT` | Ships, zeppelins | Medium — travel flavor |
| 16 | `DUEL_ARBITER` | Duel flags | Low |
| **17** | **`FISHINGNODE`** | **Fishing bobbers, pools** | **Medium — fishing flavor** |
| 18 | `SUMMONING_RITUAL` | Summoning stones | Low |
| **19** | **`MAILBOX`** | **Mailboxes** | **Medium — "Expecting a letter?"** |
| 20 | `DO_NOT_USE` | — | None |
| 21 | `GUARDPOST` | Guard spawn points | None — invisible |
| 22 | `SPELLCASTER` | Teleporters, portals | Medium — travel |
| **23** | **`MEETINGSTONE`** | **Instance meeting stones** | **Medium — dungeon anticipation** |
| 24 | `FLAGSTAND` | BG flag stands | BG-specific |
| **25** | **`FISHINGHOLE`** | **Fishing school spots** | **Medium — fishing flavor** |
| 26 | `FLAGDROP` | Dropped BG flags | BG-specific |
| 27 | `MINI_GAME` | Minigames | Low |
| 28 | `DO_NOT_USE_2` | — | None |
| 29 | `CAPTURE_POINT` | BG capture points | BG-specific |
| 30 | `AURA_GENERATOR` | Passive aura sources | None — invisible |
| 31 | `DUNGEON_DIFFICULTY` | Raid difficulty changers | Low |
| **32** | **`BARBER_CHAIR`** | **Barber chairs** | **Low — city flavor** |
| 33 | `DESTRUCTIBLE_BUILDING` | Siege targets | BG/raid specific |
| 34 | `GUILD_BANK` | Guild bank vaults | Low |
| 35 | `TRAPDOOR` | Floor traps | Low |

### SpellFocus Sub-Types (Type 8)

`GAMEOBJECT_TYPE_SPELL_FOCUS` is the richest category for chatter. The `spellFocus.focusId` field references `SpellFocusObject.dbc` which identifies what kind of focus it is:

| focusId | Object | Chatter Potential |
|---------|--------|-------------------|
| 1 | Anvil | Blacksmithing, crafting |
| 2 | Loom | Tailoring |
| 3 | Forge | Metalwork, heat, crafting |
| 4 | Cooking Fire / Campfire | Warmth, rest, food |
| 6 | Moonwell | Elune, Night Elf lore |
| 7 | Altar | Religion, rituals, sacrifices |
| 8 | Cauldron | Alchemy, potions |
| 15 | Runeforge | Death Knight |

---

## Filtering: What's Interesting vs What's Noise

Not all GOs are worth commenting on. Many are invisible markers, spell triggers, or mechanical objects.

### Must Filter Out

```cpp
// Invisible markers — "Point" icon means non-visible game logic object
if (go->GetGOInfo()->IconName == "Point")
    continue;

// Non-selectable objects — player can't see or click them
if (go->HasFlag(GAMEOBJECT_FLAGS, GO_FLAG_NOT_SELECTABLE))
    continue;

// Trap objects — don't reveal hidden traps (immersion breaking)
if (go->GetGoType() == GAMEOBJECT_TYPE_TRAP)
    continue;

// BG/arena mechanical objects
if (go->GetGoType() == GAMEOBJECT_TYPE_FLAGSTAND ||
    go->GetGoType() == GAMEOBJECT_TYPE_FLAGDROP ||
    go->GetGoType() == GAMEOBJECT_TYPE_CAPTURE_POINT)
    continue;

// System objects
if (go->GetGoType() == GAMEOBJECT_TYPE_DO_NOT_USE ||
    go->GetGoType() == GAMEOBJECT_TYPE_DO_NOT_USE_2 ||
    go->GetGoType() == GAMEOBJECT_TYPE_CAMERA ||
    go->GetGoType() == GAMEOBJECT_TYPE_MAP_OBJECT ||
    go->GetGoType() == GAMEOBJECT_TYPE_AURA_GENERATOR ||
    go->GetGoType() == GAMEOBJECT_TYPE_GUARDPOST ||
    go->GetGoType() == GAMEOBJECT_TYPE_DUEL_ARBITER ||
    go->GetGoType() == GAMEOBJECT_TYPE_AREADAMAGE ||
    go->GetGoType() == GAMEOBJECT_TYPE_BINDER)
    continue;
```

### High-Interest Types (Prioritize)

```cpp
static const std::set<GameobjectTypes> highInterestTypes = {
    GAMEOBJECT_TYPE_SPELL_FOCUS,   // Forges, anvils, campfires, moonwells, altars
    GAMEOBJECT_TYPE_TEXT,          // Plaques, books, signs, gravestones
    GAMEOBJECT_TYPE_GENERIC,       // Statues, banners, decorations, shrines
    GAMEOBJECT_TYPE_GOOBER,        // Clickable objects, crystals, relics
    GAMEOBJECT_TYPE_CHEST,         // Treasure chests (not lootable by us, just noticed)
    GAMEOBJECT_TYPE_CHAIR,         // Chairs, benches, thrones
};

static const std::set<GameobjectTypes> mediumInterestTypes = {
    GAMEOBJECT_TYPE_QUESTGIVER,    // Quest boards
    GAMEOBJECT_TYPE_MAILBOX,       // Mailboxes
    GAMEOBJECT_TYPE_FISHINGNODE,   // Fishing spots
    GAMEOBJECT_TYPE_FISHINGHOLE,   // Fishing schools
    GAMEOBJECT_TYPE_MEETINGSTONE,  // Dungeon meeting stones
    GAMEOBJECT_TYPE_SPELLCASTER,   // Portals, teleporters
    GAMEOBJECT_TYPE_MO_TRANSPORT,  // Ships, zeppelins
    GAMEOBJECT_TYPE_DOOR,          // Interesting only in specific contexts (dungeon doors)
};
```

### Size Filter

Many tiny decorative GOs have `size < 0.5`. These are typically invisible/ambient clutter. Consider a minimum size threshold, though this needs testing — some interesting objects (books, candles) can be small.

---

## Proposed Architecture

### C++ Side: The Scan Trigger

This runs inside our existing WorldScript or a timer-based approach in `OnWorldUpdate`:

```
Every N seconds (configurable, e.g., 30-90s):
  1. For each real player with a bot group:
     a. Check they're not in combat, not in a BG, not mounted/flying
     b. Pick a random bot from the group
     c. Run the GO scan around that bot (22 yard radius)
     d. Filter results to interesting types
     e. If interesting GOs found, pick 1-3 of them
     f. Build JSON payload with GO data
     g. Insert event into llm_chatter_events table
```

### Event Data Sent to Python

```json
{
    "event_type": "nearby_object",
    "bot_guid": 12345,
    "bot_name": "Thaldrin",
    "bot_class": "Warrior",
    "bot_race": "Dwarf",
    "zone_name": "Ironforge",
    "subzone_name": "The Great Forge",
    "extra_data": {
        "objects": [
            {
                "name": "Anvil",
                "type": "SPELL_FOCUS",
                "type_id": 8,
                "spell_focus_id": 1,
                "distance_yards": 8.3,
                "entry": 1234
            },
            {
                "name": "Forge",
                "type": "SPELL_FOCUS",
                "type_id": 8,
                "spell_focus_id": 3,
                "distance_yards": 12.1,
                "entry": 5678
            }
        ],
        "context": "group_travel",
        "in_city": true,
        "in_dungeon": false
    }
}
```

### Python Side: Prompt Building

The LLM receives the bot's identity, their nearby objects, and the zone context. It produces a short, in-character observation.

**Prompt pattern:**
> You are Thaldrin, a Dwarf Warrior. You're walking through The Great Forge in Ironforge with your group. You notice an Anvil nearby and a Forge. Make a brief, in-character observation about what you see. Stay in character — Dwarves love metalwork and forges. One sentence, maybe two. Don't claim any action — just observe or comment.

**Expected output:**
> "Aye, now that's a proper forge. Could temper a blade to cut through dragon scale on that beauty."

### Delivery

Same pipeline as all other chatter: `llm_chatter_messages` table → `DeliverPendingMessages()` → `SayToParty()`.

---

## Performance Analysis

### Grid Search Cost

`Cell::VisitObjects` with a 22-yard radius:
- Touches 1-4 grid cells (grids are ~533 yards across, cells within are ~33 yards)
- Iterates only GOs in those cells, checking phase mask compatibility
- In a dense city like Ironforge, there might be 20-50 GOs in range
- In wilderness, typically 0-10
- Cost: **negligible** — playerbots does this at 100-yard range every second for every bot

### Scan Frequency

If we scan once every 30-90 seconds, and only for one random bot at a time:
- 1 grid search per 30-90 seconds per real player
- This is orders of magnitude less than what playerbots already does (every bot, every second, 100yd range)
- **Zero performance concern**

### LLM Call Cost

One LLM call per scan that finds interesting objects:
- Many scans will find nothing interesting (especially in wilderness)
- In cities/towns, maybe 1 call per minute
- This is well within the existing LLM budget — less frequent than group event reactions

---

## Anti-Repetition

### Per-Object Cooldown

The same GO entry should not trigger chatter twice in a short window. Use a cooldown map:

```
Key: (bot_guid, go_entry) → last_triggered_timestamp
Cooldown: 10-15 minutes per object per bot
```

This prevents a bot from commenting on the same forge every time they pass it.

### Per-Zone Cooldown

In addition to per-object, have a per-zone cooldown for this event type. Walking through Ironforge shouldn't produce 20 forge comments — maybe 1-2 per zone visit.

```
Key: (player_guid, zone_id) → last_go_chatter_timestamp
Cooldown: 2-5 minutes per zone
```

### Object Variety

When multiple interesting GOs are found, prefer objects the bot hasn't commented on recently. Track a rolling window of recently-mentioned GO entries per bot.

### Movement-Based Triggering

Instead of pure timer-based triggering, consider a movement threshold: only scan when the group has moved at least N yards since the last scan. This prevents spam when the group is stationary (resting, AFK) and ensures comments happen during travel — which is the intended use case.

```cpp
float distanceSinceLastScan = bot->GetDistance2d(lastScanPosition);
if (distanceSinceLastScan < 50.0f)
    return;  // Haven't moved enough, skip
```

---

## Context Awareness

### Where This Feature Should Fire

- **Overworld travel** — walking between quests, exploring zones
- **Cities and towns** — passing through crafting areas, taverns, monuments
- **Dungeons** — noticing environmental details, lore objects, decorations
- **NOT in combat** — suppress when any group member is in combat
- **NOT in BGs** — BG chatter handles BG environments separately
- **NOT while mounted/flying** — moving too fast to notice details

### Zone/Subzone Context

The zone and subzone provide critical context for the LLM. "An anvil in Ironforge" evokes very different commentary than "an anvil in a remote Outland camp." Pass both `zone_name` and `subzone_name` to the prompt.

### Class/Profession Affinity

Some GOs are more interesting to specific classes or professions:

| Object | Who Cares Most |
|--------|---------------|
| Forge, Anvil | Warriors, Paladins, Death Knights, Blacksmiths |
| Moonwell | Night Elves, Druids |
| Altar, Shrine | Priests, Paladins, Warlocks (dark altars) |
| Herb node | Herbalists, Alchemists |
| Mining node | Miners, Blacksmiths, Engineers |
| Campfire | Anyone (rest, warmth), Cooks |
| Books, Plaques | Mages, Priests, lore-interested personalities |
| Fishing spots | Anyone with the Fishing skill |
| Mailbox | Anyone (casual, everyday flavor) |

This affinity could be used for bot selection weighting — when a forge is nearby, prefer to pick the group's warrior or blacksmith for the comment. This creates natural "expertise" moments.

### Dungeon Atmosphere

In dungeons, this feature becomes especially immersive. Dungeon GOs include:
- Torture devices, skull piles, altars (Scarlet Monastery, Scholomance)
- Ancient machinery, titan artifacts (Uldaman, Ulduar)
- Crystals, portals, summoning circles (various)
- Prison cells, cages, chains (Stockades, BRD)
- Books and scrolls (Scarlet Monastery library)

These are exactly the kind of environmental details that make a dungeon feel alive when a bot comments on them.

---

## Edge Cases and Gotchas

### Phase Mask

`Cell::VisitObjects` already checks phase compatibility (`InSamePhase`). GOs in a different phase won't appear in results. This is handled automatically.

### Dynamic Spawns

Some GOs spawn/despawn dynamically (gathering nodes, quest objects, seasonal decorations). The `isSpawned()` check in the filter handles this — we only see what's currently visible.

### Transport GOs

Ships and zeppelins (`GAMEOBJECT_TYPE_MO_TRANSPORT`) are special — they move. A bot on a boat might detect the boat itself as a nearby GO. Filter these by checking `go->GetGoType() == GAMEOBJECT_TYPE_MO_TRANSPORT` and either skip them or handle them as a special "travel" flavor event.

### Duplicate Names

Many GOs share the same name across different entries (e.g., "Campfire" appears hundreds of times with different entries). The anti-repetition system should use the GO **name** (not entry) for cooldown keys to avoid commenting on "Campfire" repeatedly even when the entries differ.

### Dense Decoration Areas

Cities and some dungeons have very high GO density. The scan might return 30+ objects. Always limit the objects sent to the LLM (pick 1-3 most interesting) and summarize the rest as context ("among various other crafting tools and furnishings").

### Instanced vs Open World

In instances (dungeons/raids), GO spawns are per-instance. In the open world, they're shared. This doesn't affect our scanning, but it matters for the LLM context — dungeon GOs are more "special" and worth commenting on, while open-world GOs might be more mundane.

---

## Implementation Complexity

| Component | Scope | Difficulty |
|-----------|-------|-----------|
| C++ GO scan + filter | New function in LLMChatterScript.cpp | Low — proven patterns |
| C++ timer/trigger logic | Extension of existing WorldScript | Low |
| C++ event insertion | Same pattern as all other events | Low |
| Python prompt builder | New function in chatter_group.py | Low-Medium |
| Anti-repetition system | Extension of existing cooldown maps | Low |
| GO type classification | Static config/map | Low |
| Class/profession affinity | Optional enhancement | Low |
| Movement-based triggering | Small addition to timer logic | Low |

**Total: Low complexity.** This feature reuses existing infrastructure end-to-end and adds only the scan logic and a new prompt builder. No schema changes needed beyond a new event type ENUM value.

---

## Summary

This feature is a natural fit for mod-llm-chatter. The APIs exist, the patterns are proven, the performance cost is negligible, and the creative output would add significant life to travel and exploration. Bots that notice their surroundings transform silent travel into an immersive experience where your group feels aware and present in the world.
