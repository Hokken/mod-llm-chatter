# Mod-Playerbots Command System Investigation

Investigation into triggering real bot actions from LLM output (function calling pattern). Goal: player says something natural → LLM interprets → maps to playerbot command → bot actually does it.

---

## Executive Summary

**Feasibility: HIGHLY FEASIBLE (9/10)**

The mod-playerbots command system is mature, well-designed, and directly accessible from C++ code. Commands can be invoked with a single function call: `PlayerbotAI::HandleCommand()`. No need for simulated whisper packets or database queues — direct execution is possible. 76+ supported commands, all documented.

---

## 1. Command Flow Architecture

```
Player whispers bot (e.g., "attack")
    → PlayerbotAI::HandleCommand(type, text, fromPlayer)
    → Queued in chatCommands deque (ChatCommandHolder)
    → Processed in PlayerbotAI::HandleCommands() (world thread)
    → Routed through ExternalEventHelper::ParseChatCommand()
    → Triggers looked up in AiObjectContext
    → Actions executed via Engine::ExecuteAction()
```

---

## 2. Programmatic Command Execution

### Method 1: HandleCommand (Queued, Recommended)

```cpp
#include "Playerbots.h"

PlayerbotAI* botAI = GET_PLAYERBOT_AI(botPlayer);
if (botAI && botAI->GetMaster()) {
    botAI->HandleCommand(
        CHAT_MSG_WHISPER, "attack",
        botAI->GetMaster()
    );
}
```

- **Safe**: queued on world thread, no race conditions
- **Non-blocking**: returns immediately, executes next tick (~100ms)
- **Supports all validation** and security checks

### Method 2: DoSpecificAction (Immediate, Advanced)

```cpp
PlayerbotAI* botAI = GET_PLAYERBOT_AI(botPlayer);
botAI->DoSpecificAction(
    "attack my target", Event(), false
);
```

- **Synchronous**: executes immediately
- **Bypasses queue** and some security checks
- Must call from world thread

---

## 3. Command Inventory (76+ Commands)

### Movement

| Command | Example | LLM Intent |
|---------|---------|------------|
| `follow` | `follow` | "Follow me" |
| `stay` | `stay` | "Stay here" / "Guard" |
| `go` | `go 100,200` or `go Thrall` | "Go to that spot" |
| `flee` | `flee` | "Run away" |

### Combat

| Command | Example | LLM Intent |
|---------|---------|------------|
| `attack` | `attack` | "Attack my target" |
| `tank attack` | `tank attack` | "Tank this" |
| `max dps` | `max dps` | "Go all out" |
| `pet attack` | `pet attack` | "Sic 'em" |

### Spellcasting

| Command | Example | LLM Intent |
|---------|---------|------------|
| `cast SPELL` | `cast Heal` | "Cast this spell" |
| `cast SPELL on TARGET` | `cast Heal on Tankbot` | "Heal that person" |
| `buff` | `buff` | "Give me buffs" |

### Inventory

| Command | Example | LLM Intent |
|---------|---------|------------|
| `u [ITEM]` | `u [Healing Potion]` | "Use this item" |
| `e [ITEM]` | `e [Sword]` | "Equip this" |
| `t [ITEM]` | `t [Mats]` | "Trade me this" |

### Information

| Command | Example | LLM Intent |
|---------|---------|------------|
| `target` | `target` | "What's your target?" |
| `attackers` | `attackers` | "Who's hitting you?" |
| `dps` | `dps` | "How much DPS?" |

### Full Supported String List (76+)

```
follow, stay, flee, go, attack, tank attack, max dps, pet attack,
cast, castnc, buff, quests, stats, leave, reputation, log, los,
rpg status, rpg do quest, aura, drop, share, release, teleport,
taxi, repair, talents, spells, co, nc, de, trainer, maintenance,
remove glyph, autogear, equip upgrade, chat, home, destroy,
reset botAI, emote, help, gb, bank, invite, lfg, spell, rti,
position, summon, who, save mana, formation, stance, sendmail,
mail, outfit, debug, cdebug, cs, wts, hire, craft, flag, range,
ra, give leader, cheat, ginvite, guild promote, guild demote,
guild remove, guild leave, rtsc, drink, calc, open items, qi,
unlock items, unlock traded item, tame, glyphs, glyph equip,
pet, pet attack, enter vehicle, leave vehicle, revive, roll, wipe
```

---

## 4. Spell Casting Details

### Parameter Parsing (CastCustomSpellAction)

```cpp
// Format: "cast SPELL_NAME on TARGET_NAME"
"cast Heal on Tankbot"  // → spell="Heal", target="Tankbot"
"cast Fireball"          // → spell="Fireball", target=master's target
"cast [Holy Wrath]"     // → parses WoW item/spell link
```

- Spell name resolved via `SpellMgr` lookup
- Target resolved via `ObjectAccessor::FindPlayerByName()`
- Falls back to master's target if no explicit target
- Validates range, cooldown, mana before casting

### Movement Parsing (GoAction)

```cpp
"go 100,200"             // → zone coordinates
"go Thrall"              // → find NPC by name, move near
"go travel Darnassus"    // → travel system destination
```

---

## 5. Command Safety

### Safe Commands (Any Time)

- `attack` / `tank attack` / `max dps` — combat-appropriate
- `stay` / `flee` / `follow` — movement control
- `cast SPELL` — validates range/cooldown/mana
- Information queries (`target`, `dps`, `attackers`)

### Dangerous Commands (Restrict from LLM)

- `reset botAI` — completely resets bot state
- `destroy` — deletes bot from game
- `teleport` — restricted, may not work
- `cheat` — admin-level commands
- `leave` — bot leaves group/party

### Rate Limiting

- No built-in rate limiter in HandleCommand()
- Commands execute per world tick (~100ms)
- **Recommendation**: max 2-3 commands per bot per second from Python

### Security

- `HandleCommand()` validates against `PlayerbotSecurityLevel`
- Must pass bot's master player as `fromPlayer` parameter
- If security check fails, command is silently dropped

---

## 6. Function Calling Tool Definitions

### Example Tool Definitions for LLM

```json
{
  "name": "bot_attack",
  "description": "Command bot to attack the current target",
  "parameters": {
    "bot_name": "string (required)"
  }
}

{
  "name": "bot_cast_spell",
  "description": "Command bot to cast a specific spell",
  "parameters": {
    "bot_name": "string (required)",
    "spell_name": "string (required, exact spell name)",
    "target_name": "string (optional, player/NPC name)"
  }
}

{
  "name": "bot_move",
  "description": "Command bot to move to a location or follow/stay",
  "parameters": {
    "bot_name": "string (required)",
    "action": "string (follow|stay|flee|go)",
    "destination": "string (optional, for 'go')"
  }
}

{
  "name": "bot_use_item",
  "description": "Command bot to use an item",
  "parameters": {
    "bot_name": "string (required)",
    "item_name": "string (required)"
  }
}
```

### Natural Language → Command Mapping Examples

| Player Says | LLM Tool Call | Playerbot Command |
|------------|---------------|-------------------|
| "Focus the healer" | `bot_attack(bot_name)` | `attack` (with healer targeted) |
| "Heal the tank" | `bot_cast_spell(bot, "Heal", "Tankbot")` | `cast Heal on Tankbot` |
| "Buff me please" | `bot_cast_spell(bot, "buff")` | `buff` |
| "Stay here and guard" | `bot_move(bot, "stay")` | `stay` |
| "Follow me" | `bot_move(bot, "follow")` | `follow` |
| "Go all out!" | `bot_attack(bot) + max dps` | `max dps` |
| "Use a health potion" | `bot_use_item(bot, "Healing Potion")` | `u [Healing Potion]` |

---

## 7. Recommended Architecture

```
┌─────────────────────┐
│   Player Message     │
│ "Heal the tank"     │
└──────────┬──────────┘
           │
┌──────────v──────────┐
│  Python LLM Bridge   │
│  - LLM with tools    │
│  - Validates command  │
│  - Resolves names     │
│  - INSERT to DB       │
└──────────┬──────────┘
           │
┌──────────v──────────────────┐
│  C++ Command Handler         │
│  (WorldScript::OnUpdate)     │
│  - Poll bot_command events   │
│  - HandleCommand() per bot   │
│  - Mark event processed      │
└──────────┬──────────────────┘
           │
┌──────────v──────────┐
│  PlayerbotAI          │
│  - Queue/execute cmd  │
│  - Validate & act     │
└───────────────────────┘
```

### Why DB Queue (not direct C++ → C++)

- Python bridge does the LLM call and tool resolution
- Result needs to cross the Python → C++ boundary
- Existing `llm_chatter_events` table already handles this pattern
- C++ polls events on world thread (thread-safe)
- Same architecture as all other chatter features

---

## 8. LLM Integration Pitfalls

| Pitfall | Impact | Mitigation |
|---------|--------|------------|
| Spell name mismatch | "Lightning Bolt" vs "Lightning Bolt Rank 1" | Query bot's spell list, show LLM exact names |
| Target disambiguation | "Heal the tank" but which tank? | LLM must resolve to exact player name from roster |
| Command invention | LLM invents nonexistent command | Restrict to predefined tool set |
| Feedback delay | Command queued, result ~100ms later | Log all commands for LLM context |
| Dangerous commands | LLM calls `destroy` or `reset botAI` | Whitelist safe commands only |

---

## 9. Integration Effort Estimate

| Phase | Scope | Effort | Risk |
|-------|-------|--------|------|
| Phase 1: Basic commands (attack, follow, stay) | 3 tools | ~50 lines C++ + Python | Low |
| Phase 2: Spell casting with targets | 1 complex tool | ~80 lines | Medium |
| Phase 3: Inventory/items | 3 tools | ~60 lines | Low |
| Phase 4: Advanced (go, formation, strategy) | 5+ tools | ~120 lines | Medium |

---

## 10. Key Files Reference

| File | Purpose |
|------|---------|
| `mod-playerbots/src/Bot/PlayerbotAI.h` | Core API — HandleCommand, DoSpecificAction |
| `mod-playerbots/src/Bot/PlayerbotAI.cpp` | Implementation — command queue, processing |
| `mod-playerbots/src/Ai/Base/Strategy/ChatCommandHandlerStrategy.cpp` | Command registry (76+ commands) |
| `mod-playerbots/src/Bot/Engine/ExternalEventHelper.cpp` | Command routing |
| `mod-playerbots/src/Ai/Base/Actions/CastCustomSpellAction.cpp` | Spell parsing ("cast X on Y") |
| `mod-playerbots/src/Ai/Base/Actions/GoAction.cpp` | Movement parsing |

---

## Conclusion

Triggering real bot actions from LLM output is **highly feasible and straightforward**. The command API is clean, well-documented, and safe. The function calling pattern (LLM tools → Python validation → DB event → C++ HandleCommand) fits perfectly into the existing mod-llm-chatter architecture. Phase 1 (basic attack/follow/stay) could be implemented in ~50 lines of code.
