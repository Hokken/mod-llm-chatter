# Reactive Bot State — In-Game Testing Guide

## Setup

1. Log in as CALWEN, form a group with 2-3 bots (mix of specs: tank warrior, healer priest, DPS rogue/mage)
2. Have two windows open:
   - WoW game client
   - Bridge logs: `powershell.exe -Command "docker logs -f ac-llm-chatter-bridge"`
3. Look for `bot_state` in bridge log output — this confirms C++ is injecting state data

---

## What Changed (TL;DR)

Bots now know their own health %, mana %, role, combat target, and AI state when reacting to events. Previously all reactions were generic. Now a wounded healer at 10% mana says things like "I need to drink" instead of "Good fight!"

Additionally, bots will **proactively call out** when critically low on health, out of mana, or losing aggro (tanks).

---

## Tests by Priority

### 1. Kill Reaction (easiest to trigger)

**Do**: Kill a mob with your group.

**Look for in party chat**: Response that feels aware of the bot's situation. A bot at full health might say something confident. A bot that took heavy damage might reference being hurt.

**Look for in bridge logs**: `"bot_state":{"health_pct":XX,"mana_pct":XX,"role":"tank",...}` inside the event's extra_data.

**Pass criteria**: `bot_state` appears in logs. Response tone loosely matches the bot's actual condition.

### 2. Low Health Callout (Phase 2C — new)

**Do**: Pull several mobs at once so a bot drops below ~25% HP while still in combat.

**Look for in party chat**: An urgent message from the wounded bot — something like "I need healing!" or "I'm going down!" Should appear within 5-10 seconds of dropping low.

**Look for in bridge logs**: Event type `bot_group_low_health` with the bot's state data.

**Pass criteria**: Callout fires, tone is urgent/panicked, only the low-HP bot speaks.

### 3. OOM Callout (Phase 2C — new)

**Do**: Extended combat so the healer/mage runs low on mana (below ~15%). Chain-pull without letting them drink.

**Look for in party chat**: The mana user warns the group — "Out of mana, need to drink" or "Can't keep healing."

**Look for in bridge logs**: Event type `bot_group_oom`.

**Pass criteria**: Only fires for mana-using classes (NOT warriors/rogues). Tone matches OOM urgency.

### 4. Aggro Loss Callout (Phase 2C — new, tanks only)

**Do**: Have a DPS pull aggro off the tank (attack before tank establishes threat, or pull a second pack).

**Look for in party chat**: Tank reacts — "Get behind me!" or "I've lost aggro on that one!"

**Look for in bridge logs**: Event type `bot_group_aggro_loss`.

**Pass criteria**: Only fires for tank-role bots. References the mob or the party member who has aggro.

### 5. Death Reaction (Phase 2A — improved)

**Do**: Let one bot die while others are alive.

**Look for in party chat**: A living bot reacts to the death. Should reference the dead bot by name.

**Look for in bridge logs**: Event type `bot_group_death`. The `subject_guid`/`subject_name` should be the **living reactor**, not the dead bot. Extra_data should contain `dead_name` and the reactor's `bot_state`.

**Pass criteria**: Dead bots never speak. Living reactor's response references own state (e.g., "I couldn't save them, I was out of mana").

### 6. Wipe Reaction

**Do**: Pull way too many mobs, let entire group die.

**Look for in party chat**: Wipe reaction from the last bot to die.

**Look for in bridge logs**: Event type `bot_group_wipe` with `bot_state`.

### 7. Role in Idle Banter (Phase 2B)

**Do**: Stay in group, wait for idle banter to trigger (30-60 seconds of no combat).

**Look for in bridge logs**: The idle prompt should include `actual_role` passed to `build_race_class_context()`. Check that a warrior tank gets tank-perspective context, not generic DPS.

**Verify in DB** (optional):
```sql
SELECT bot_name, role FROM llm_group_bot_traits WHERE group_id = <your_group_id>;
```
Role column should be populated (tank/healer/melee_dps/ranged_dps).

---

## Quick Sanity Checks

| What | Where to check | Expected |
|------|---------------|----------|
| bot_state in kill events | Bridge logs | `"bot_state":{...}` in extra_data |
| mana_pct = -1 for warrior/rogue | Bridge logs | Non-mana classes show -1 |
| No callouts out of combat | Party chat | Callouts only during combat |
| Cooldown works | Party chat | Same bot doesn't callout twice within 60s |
| Player loot has no bot_state | Bridge logs | When YOU loot, no `bot_state` in loot event |
| Bot loot has bot_state | Bridge logs | When a BOT loots, `bot_state` present |

---

## Red Flags (Something Is Wrong)

- **No `bot_state` in any bridge logs** → C++ injection not working, check compilation succeeded
- **Dead bot speaks** after dying → `IsAlive()` filter not applied (check the fix compiled in)
- **Callouts firing outside combat** → `CheckGroupCombatState` not checking `IsInCombat()`
- **OOM callout on a warrior** → Mana check `GetMaxPower(POWER_MANA) > 0` not working
- **Callouts every 5 seconds nonstop** → Cooldown map not working, check `_stateCalloutCooldown` config
- **No callouts at all** → Check `StateCalloutEnable = 1` in active config, check bridge logs for the event types
- **Bridge crash on startup** → Import error for new functions, check `docker logs ac-llm-chatter-bridge`
