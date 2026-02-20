# Investigation: Bot Item* Use-After-Free in OnPlayerLootItem

## Objective

Determine whether it is possible to **safely obtain item data** (entry, name,
quality) when a **playerbot** loots an item, without crashing due to the
use-after-free `Item*` pointer.

Currently, accessing `item->GetTemplate()` (or any `item->` method that reads
`m_uint32Values`) causes a SIGSEGV when the looter is a playerbot. The
workaround skips `Item*` access entirely for bots, losing item details.

The goal is to find a way to get item info for bot loot events so the group
chatter module can react to specific items (quality, name, etc.).

---

## The Crash

### Symptoms

- **Signal**: SIGSEGV (segmentation fault)
- **When**: A playerbot loots any item while in a group with a real player
- **Where**: `Object::GetUInt32Value(3)` called from `Item::GetTemplate()`
- **Root cause**: `Item*` pointer is non-null but `m_uint32Values` array
  points to freed/deallocated memory

### GDB Backtrace (abbreviated)

```
Thread 1 "worldserver" received signal SIGSEGV, Segmentation fault.
Object::GetUInt32Value(index=3) at Object.cpp:297
  return m_uint32Values[index];   // <-- m_uint32Values is freed

#0  Object::GetUInt32Value(this=0x7f3c40609500, index=3)
#1  Object::GetEntry(this=0x7f3c40609500)
#2  Item::GetTemplate(this=0x7f3c40609500)
#3  LLMChatterPlayerScript::OnPlayerLootItem(player=0x7f3c8c93a000,
        item=0x7f3c40609500) at LLMChatterScript.cpp:2147
#4  ScriptMgr::OnPlayerLootItem at PlayerScript.cpp:360
#5  Player::StoreLootItem at Player.cpp (line near 13619)
#6  WorldSession::HandleAutostoreLootItemOpcode at LootHandler.cpp:99
#7  PlayerbotHolder::HandleBotPackets at PlayerbotMgr.cpp:269
#8  PlayerbotHolder::UpdateSessions at PlayerbotMgr.cpp:251
#12 ScriptMgr::OnPlayerbotUpdate at PlayerbotsScript.cpp:77
#13 World::Update at World.cpp:1175
```

### Key GDB Variables at Crash

```
item       = 0x7f3c40609500     (non-null, but memory is freed)
player     = 0x7f3c8c93a000     (valid, Player* works fine)
group      = 0x7f3d49f17000     (valid, non-null = bot IS in a group)
looters    = set{105, 1410, 2003}  (3 players = player's group with 2 bots)
newitem    = 0x7f3c40609500     (same as item - this IS the newly created Item)
rax        = 0x0                (m_uint32Values[3] read returned 0 / faulted)
```

### Critical Observation

`newitem` (frame #5) has the **same address** as `item` (frame #3). This means
the hook receives the exact `Item*` that `StoreNewItem()` created. The item was
valid when created but its `m_uint32Values` array became invalid by the time
our hook reads it.

---

## The Code Path

### 1. Bot queues a loot packet

**File**: `modules/mod-playerbots/src/Ai/Base/Actions/LootAction.cpp:441-443`

```cpp
WorldPacket* packet = new WorldPacket(CMSG_AUTOSTORE_LOOT_ITEM, 1);
*packet << itemindex;
bot->GetSession()->QueuePacket(packet);
```

The bot does NOT call `HandleAutostoreLootItemOpcode` directly. It queues the
packet for later processing. Note: at this point the bot's `LootAction` has
access to the `ItemTemplate* proto` (line 431 uses `proto->BuyPrice`), which
means the item template IS available during the action — just not in the hook.

### 2. Packet is processed on next update cycle

**File**: `modules/mod-playerbots/src/Bot/PlayerbotMgr.cpp:236-270`

```cpp
void PlayerbotHolder::UpdateSessions()
{
    for (auto itr = GetPlayerBotsBegin(); ...; ++itr)
    {
        Player* const bot = itr->second;
        if (bot->IsInWorld())
            HandleBotPackets(bot->GetSession());
    }
}

void PlayerbotHolder::HandleBotPackets(WorldSession* session)
{
    WorldPacket* packet;
    while (session->GetPacketQueue().next(packet))
    {
        OpcodeClient opcode = static_cast<OpcodeClient>(packet->GetOpcode());
        ClientOpcodeHandler const* opHandle = opcodeTable[opcode];
        opHandle->Call(session, *packet);  // dispatches to handler
        delete packet;
    }
}
```

This runs on the **world thread** during `World::Update()` via the
`OnPlayerbotUpdate` script hook. Single-threaded — no race conditions.

### 3. HandleAutostoreLootItemOpcode resolves loot source

**File**: `src/server/game/Handlers/LootHandler.cpp:33-111`

```cpp
void WorldSession::HandleAutostoreLootItemOpcode(WorldPacket& recvData)
{
    Player* player = GetPlayer();
    ObjectGuid lguid = player->GetLootGUID();
    Loot* loot = nullptr;
    uint8 lootSlot = 0;
    recvData >> lootSlot;

    // Resolves loot source (creature, GO, item, corpse)
    if (lguid.IsGameObject()) { loot = &go->loot; }
    else if (lguid.IsItem())  { loot = &pItem->loot; }
    else if (lguid.IsCorpse()){ loot = &bones->loot; }
    else                      { loot = &creature->loot; }

    sScriptMgr->OnPlayerAfterCreatureLoot(player);  // line 95

    InventoryResult msg;
    LootItem* lootItem = player->StoreLootItem(lootSlot, loot, msg);  // line 98
    // ...
}
```

**Important**: `OnPlayerAfterCreatureLoot` fires at line 95 BEFORE
`StoreLootItem`. At that point the loot source is resolved but the item hasn't
been created yet. This hook receives only `Player*`, no item info.

### 4. StoreLootItem creates the Item and fires the hook

**File**: `src/server/game/Entities/Player/Player.cpp:13526-13627`

```cpp
LootItem* Player::StoreLootItem(uint8 lootSlot, Loot* loot, InventoryResult& msg)
{
    LootItem* item = loot->LootItemInSlot(lootSlot, this, ...);  // line 13534
    // ... validation checks ...

    ItemPosCountVec dest;
    msg = CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, item->itemid, item->count);
    if (msg == EQUIP_ERR_OK)
    {
        AllowedLooterSet looters = item->GetAllowedLooters();         // line 13577
        Item* newitem = StoreNewItem(dest, item->itemid, true,        // line 13578
                                     item->randomPropertyId, looters);

        // ... mark as looted, send notifications ...

        sScriptMgr->OnPlayerLootItem(this, newitem, item->count,     // line 13619
                                     this->GetLootGUID());
    }
    return item;
}
```

**The hook call at line 13619 passes `newitem`** — the freshly created `Item*`
from `StoreNewItem()`. The `LootItem* item` (from the loot table) contains
`item->itemid` (the entry ID) — this is a simple `uint32`, not an Object.

### 5. What GetTemplate() does

**File**: `src/server/game/Entities/Item/Item.cpp:544-547`

```cpp
ItemTemplate const* Item::GetTemplate() const
{
    return sObjectMgr->GetItemTemplate(GetEntry());
}
```

`GetEntry()` calls `GetUInt32Value(OBJECT_FIELD_ENTRY)` which reads
`m_uint32Values[3]`. This is where the crash occurs.

### 6. How m_uint32Values works

**File**: `src/server/game/Entities/Object/Object.h` and `Object.cpp`

```cpp
// Object.h - the values array (union of int32/uint32/float)
union {
    int32*  m_int32Values;
    uint32* m_uint32Values;
    float*  m_floatValues;
};

// Object.cpp:294-298
uint32 Object::GetUInt32Value(uint16 index) const
{
    ASSERT(index < m_valuesCount || PrintIndexError(index, false));
    return m_uint32Values[index];  // CRASH: m_uint32Values points to freed memory
}
```

**OBJECT_FIELD_ENTRY = 0x0003** (from `UpdateFields.h`).

### 7. Other available loot-related hooks

From `PlayerScript.h`:

| Hook | Signature | When it fires | Has item info? |
|------|-----------|---------------|----------------|
| `OnPlayerLootItem` | `(Player*, Item*, uint32, ObjectGuid)` | After item stored | Yes but Item* is unsafe for bots |
| `OnPlayerStoreNewItem` | `(Player*, Item*, uint32)` | After item stored (incl. master loot) | Same Item* problem |
| `OnPlayerAfterCreatureLoot` | `(Player*)` | Before StoreLootItem | No item info at all |
| `OnPlayerBeforeLootMoney` | `(Player*, Loot*)` | Before money looted | Only money, not items |

There is no hook that fires between item creation and the point where the
`Item*` becomes unsafe. Both `OnPlayerLootItem` and `OnPlayerStoreNewItem`
receive the same `Item*` created by `StoreNewItem()`.

---

## Why the Item* is Corrupt

### The puzzle

The call chain is:
```
StoreLootItem()
  → StoreNewItem() creates Item* (valid here)
  → OnPlayerLootItem(newitem)  ← hook fires, Item* should still be valid
```

This is **synchronous, single-threaded** code. There's no opportunity for
another thread to free the item between creation and hook invocation.

### Possible explanations to investigate

1. **StoreNewItem internal behavior for bots**: Does `StoreNewItem()` do
   something different when the player is a bot? Does it allocate the item
   differently, use a pool allocator that recycles memory, or immediately
   destroy/recreate items?

2. **Item relocation during storage**: When `StoreNewItem()` stores the item
   in inventory, it might trigger bag reorganization that moves/destroys the
   original `Item*` and creates a new one at a different address. If the
   returned pointer is stale after reorganization, this would explain the crash.

3. **Observer/event cascade**: Does `StoreNewItem()` or `SendNewItem()` trigger
   other scripts/handlers that might destroy the item before our hook runs?
   For example, playerbots AI might react to receiving an item by immediately
   equipping, selling, or destroying it.

4. **Bot inventory is full / item bounced**: If the bot's inventory management
   causes the item to be mailed, deleted, or moved during `StoreNewItem`, the
   returned pointer could be invalidated.

5. **Memory allocator behavior**: The `m_uint32Values` array is allocated via
   `new uint32[m_valuesCount]` in `Object::_Create()`. If the allocator reuses
   memory aggressively (jemalloc, tcmalloc), the array could be freed by an
   unrelated deallocation happening inside `StoreNewItem()`.

6. **Deferred destruction**: Playerbots might have hooks that fire during item
   storage that queue the item for destruction, and the destruction happens
   before our hook in the same call chain.

### What to look at in the codebase

- `Item::Create()` and `Item::_Create()` — how m_uint32Values is allocated
- `Player::StoreNewItem()` — does it call anything that could trigger item
  destruction for bots?
- `Player::_StoreItem()` — the actual inventory placement, does it send
  packets or trigger AI?
- `PlayerbotAI` — does it have any `OnItemAdded` / inventory management hooks
  that fire synchronously during item storage?
- Search for `Item::~Item()` and `Object::~Object()` — where is
  `m_uint32Values` freed?
- Search for `delete item` or `DestroyItem` calls that might fire during the
  loot processing chain

---

## Potential Solutions to Investigate

### A. Get item entry from LootItem instead of Item*

In `StoreLootItem()`, the `LootItem* item` variable at line 13534 contains
`item->itemid` (a plain `uint32`). This is the item entry ID and it's
perfectly safe to read. However, `OnPlayerLootItem` doesn't receive this —
it only gets the `Item*`.

**Could we modify the hook signature?** Adding `uint32 itemEntry` to
`OnPlayerLootItem` would be an AzerothCore core change. Not ideal for a
module, but possible if the project maintains its own fork.

**Could we add a custom hook?** A module-specific hook called from a patched
`StoreLootItem()` that passes `item->itemid` alongside the `Item*`.

### B. Use sObjectMgr to look up by entry without touching Item*

If we could get the item entry from somewhere safe, we could call
`sObjectMgr->GetItemTemplate(entry)` directly. The question is: where
can we get the entry?

Options:
- The `ObjectGuid lootguid` parameter identifies the loot source (creature
  corpse, chest, etc.). We could potentially look up what items that source
  drops, but this doesn't tell us WHICH item was looted.
- Query the character database for recently added inventory items. Fragile
  and async.

### C. Read item entry from the Item's GUID

Every `Item*` has a GUID. The GUID is stored in `m_uint32Values[0]` and
`m_uint32Values[1]` (OBJECT_FIELD_GUID is at index 0). So `GetGUID()` would
also crash.

However, the GUID counter is also stored separately in the `ObjectGuid`
member of the Object class. **Investigate whether `GetGUID()` reads from
`m_uint32Values` or from a separate member.** If it's separate, we could
use the GUID to look up the item in `sObjectMgr` or the character database.

### D. Validate m_uint32Values before access

**Object members NOT stored in m_uint32Values** (stored directly on Object):
- `m_objectTypeId` (uint8) — accessible via `GetTypeId()`
- `m_objectType` (uint16)
- `m_inWorld` (bool) — accessible via `IsInWorld()`
- `m_valuesCount` (uint16)
- `m_uint32Values` (the pointer itself)

If the Item object structure is still in memory (only the values array is
freed), we could potentially:
```cpp
// Check if the values array pointer looks valid
if (item->IsInWorld() && item->GetTypeId() == TYPEID_ITEM)
{
    // Might be safe to access m_uint32Values
    ItemTemplate const* tmpl = item->GetTemplate();
}
```

**WARNING**: This is fragile. If the entire Item object is freed (not just
the values array), even reading `m_objectTypeId` is undefined behavior.
Need to determine whether the Object itself or just its values array is freed.

### E. Hook into LootAction directly (playerbots module)

The bot's `LootAction` (LootAction.cpp:430-453) already has access to the
`ItemTemplate* proto` before it queues the packet. We could potentially:
- Store the item template info in a shared map keyed by bot GUID + timestamp
- Read it from our hook

This requires modifying the playerbots module code or using a shared data
structure between modules.

### F. Intercept at OnPlayerAfterCreatureLoot + track pending loot

`OnPlayerAfterCreatureLoot(Player*)` fires at LootHandler.cpp:95, BEFORE
`StoreLootItem()`. At this point, we could:
1. Get the player's `GetLootGUID()` to find the loot source
2. Access the `Loot*` object to see what items are available
3. Store this info keyed by player GUID
4. When `OnPlayerLootItem` fires, use the stored info instead of Item*

**This approach avoids touching Item* entirely.** The `Loot*` object and its
`LootItem` entries are safe to read at hook time. Each `LootItem` has:
- `itemid` (uint32) — the item entry
- `itemIndex` (uint8)
- `count` (uint8)
- `randomPropertyId` (int32)

The challenge: `OnPlayerAfterCreatureLoot` fires once before ALL items are
looted in a session, not per-item. And we'd need to figure out WHICH item
was actually taken.

### G. Use a WorldScript::OnUpdate poll instead of a hook

Instead of reacting to loot events, periodically scan group members'
inventories for new items. This completely avoids the Item* issue.

Downsides: polling overhead, delay, complexity of diffing inventory.

### H. Accept the limitation — bot loot events without item details

Current workaround: queue `bot_group_loot` events with `item_quality=-1` and
no item name. Python generates generic loot chatter. Real player loot
events still have full details.

This is the safest approach and the one currently implemented.

---

## Files to Read for Investigation

| File | What to look for |
|------|-----------------|
| `src/server/game/Entities/Object/Object.cpp` | `_Create()`, `~Object()`, how m_uint32Values is allocated/freed |
| `src/server/game/Entities/Object/Object.h` | Member layout, which fields are NOT in m_uint32Values |
| `src/server/game/Entities/Item/Item.cpp` | `Item::Create()`, `Item::~Item()` |
| `src/server/game/Entities/Player/Player.cpp` | `StoreNewItem()`, `_StoreItem()`, `MoveItemToInventory()` |
| `src/server/game/Handlers/LootHandler.cpp` | Full `HandleAutostoreLootItemOpcode` (lines 33-111) |
| `modules/mod-playerbots/src/Ai/Base/Actions/LootAction.cpp` | Bot loot action (lines 380-464), how proto is accessed |
| `modules/mod-playerbots/src/Bot/PlayerbotMgr.cpp` | `HandleBotPackets()`, `UpdateSessions()` (lines 236-270) |
| `src/server/game/Scripting/ScriptDefines/PlayerScript.h` | All loot-related hooks |
| `src/server/game/Entities/Player/Player.cpp:13526-13627` | Full `StoreLootItem()` method |

---

## Current Workaround in LLMChatterScript.cpp

```cpp
void OnPlayerLootItem(Player* player, Item* item, ...) override
{
    // ... rate limiter, config gate ...

    bool isBot = IsPlayerBot(player);

    // For real players, validate Item* normally
    if (!isBot && !item)
        return;

    Group* group = player->GetGroup();
    if (!group) return;
    if (!GroupHasRealPlayer(group)) return;

    if (isBot)
    {
        // Bot path: NO Item* access, queue lightweight event
        // with item_quality=-1, item_entry=0, item_name=""
        // Python handles generically
        // 120s cooldown, 10% chance
        // ... INSERT bot_group_loot event ...
        return;
    }

    // Real player path: full Item* access (safe)
    ItemTemplate const* tmpl = item->GetTemplate();
    // ... quality filtering, INSERT with full item details ...
}
```

---

## Success Criteria

A successful investigation would find a way to obtain at minimum the **item
entry ID** (uint32) for bot loot events without touching `Item*`'s
`m_uint32Values` array, allowing us to then call
`sObjectMgr->GetItemTemplate(entry)` to get the full item template (name,
quality, etc.) safely.
