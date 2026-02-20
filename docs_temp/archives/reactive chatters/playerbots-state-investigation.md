# Playerbots Bot State Investigation

Investigation into what bot state data is readable from external code (mod-llm-chatter hooks) to make chatter messages reflect what bots are actually doing.

---

## Executive Summary

**FEASIBILITY: HIGHLY FEASIBLE** — Nearly all desired bot state is accessible from external code with minimal complexity. PlayerbotAI provides clean public APIs, thread-safe access (world thread only), and low compilation coupling. Gradual integration possible starting with ~50 lines of code.

---

## 1. PlayerbotAI State Access

### Getting PlayerbotAI from Player*

```cpp
#include "Playerbots.h"

PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
// Safe macro, returns nullptr if not a bot
```

### Key Methods Available

| State | Method | Returns | Example |
|-------|--------|---------|---------|
| Combat state | `ai->GetState()` | `BotState` enum | `BOT_STATE_COMBAT`, `BOT_STATE_NON_COMBAT`, `BOT_STATE_DEAD` |
| Current target | `player->GetVictim()` | `Unit*` | What bot is attacking |
| Health % | `player->GetHealthPct()` | float 0-100 | "45.5% health" |
| Mana | `player->GetPower(POWER_MANA)` | uint32 | Current mana pool |
| Is alive | `player->IsAlive()` | bool | True = alive |
| In combat | `player->IsInCombat()` | bool | Engaged with enemy |

---

## 2. Bot Strategies (Role/Specialization)

```cpp
BotState state = ai->GetState();
std::vector<std::string> strategies = ai->GetStrategies(state);
// Returns: ["tank", "survivalist", "assault"] or similar

// Check specific strategy
bool staying = ai->HasStrategy("stay", state);

// Check strategy type mask
bool hasTankStrat = ai->ContainsStrategy(STRATEGY_TYPE_TANK);
bool hasHealStrat = ai->ContainsStrategy(STRATEGY_TYPE_HEAL);
```

### Role Detection (Static Methods)

```cpp
bool isTank = PlayerbotAI::IsTank(player, false);
bool isHealer = PlayerbotAI::IsHeal(player, false);
bool isDps = PlayerbotAI::IsDps(player, false);
bool isRanged = PlayerbotAI::IsRanged(player, false);
bool isMelee = PlayerbotAI::IsMelee(player, false);
bool isCaster = PlayerbotAI::IsCaster(player, false);

// Main tank status
bool isMainTank = PlayerbotAI::IsMainTank(player);
bool isAssistTank = PlayerbotAI::IsAssistTank(player);
```

### Key State Enums

```cpp
enum BotState {
    BOT_STATE_COMBAT = 0,
    BOT_STATE_NON_COMBAT = 1,
    BOT_STATE_DEAD = 2
};

enum StrategyType : uint32 {
    STRATEGY_TYPE_GENERIC = 0,
    STRATEGY_TYPE_COMBAT = 1,
    STRATEGY_TYPE_NONCOMBAT = 2,
    STRATEGY_TYPE_TANK = 4,
    STRATEGY_TYPE_DPS = 8,
    STRATEGY_TYPE_HEAL = 16,
    STRATEGY_TYPE_RANGED = 32,
    STRATEGY_TYPE_MELEE = 64
};
```

---

## 3. Battleground & Arena State

```cpp
if (player->InBattleground()) {
    uint32 bgId = player->GetBattlegroundId();
    BattlegroundTypeId bgType = player->GetBattlegroundTypeId();
}

// BG-specific strategies
if (ai->HasStrategy("warsong", state))  // WSG
if (ai->HasStrategy("arathi", state))   // AB
if (ai->HasStrategy("eye", state))      // EoS
if (ai->HasStrategy("arena", state))    // Arena
```

**Limitation**: Objective progress (flag carrying, base control) is NOT directly exposed through PlayerbotAI. Would require querying the `Battleground*` object directly (which is feasible via `player->GetBattleground()`).

---

## 4. Thread Safety

**EXCELLENT NEWS**: PlayerbotAI runs on the World thread exclusively.

```
PlayerScript hooks (OnPlayerSpellCast, OnPlayerChat, etc)
    ↓
World Thread (single-threaded)
    ↓
PlayerbotAI state access (NO MUTEXES NEEDED)
```

All bot state reads from hooks are automatically thread-safe. No special handling required.

---

## 5. How to Access from mod-llm-chatter

### Required Headers

```cpp
#include "Playerbots.h"     // GET_PLAYERBOT_AI macro
#include "Player.h"          // Player*, combat state
#include "Unit.h"            // Health, mana, victim
```

### Safe Check Pattern

```cpp
PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
if (ai == nullptr) {
    // Not a bot, skip bot-specific logic
    return;
}

// Safe to access all bot state now
BotState state = ai->GetState();
std::vector<std::string> strategies = ai->GetStrategies(state);
```

### Compilation Dependency

**EXCELLENT**: mod-llm-chatter has minimal playerbots dependency:

- `GET_PLAYERBOT_AI` is just a macro
- If playerbots not compiled, `GET_PLAYERBOT_AI` returns nullptr
- Code gracefully degrades (no hard linker dependency)
- Both modules truly optional for each other

---

## 6. What's NOT Easily Readable

| Feature | Status | Workaround |
|---------|--------|-----------|
| Current action being executed | Hard (internal queue) | Infer from state + target |
| BG objective progress | Not exposed via AI | Query `Battleground*` directly |
| Spell/item availability | Possible but complex | Use `Player::HasSpell()` |
| GCD/cooldown status | Not exposed | Time-based heuristics |
| Pet health/status | Not exposed | Get pet via player, read like normal unit |

---

## 7. Practical Examples for mod-llm-chatter

### Full Bot Context Struct

```cpp
struct BotContext {
    std::string name;
    std::string state_str;      // "combat", "dead", "idle"
    float health_pct;
    float mana_pct;
    std::string role;           // "tank", "healer", "dps"
    std::string target_name;
    std::vector<std::string> strategies;
};

BotContext GetBotContext(Player* bot) {
    BotContext ctx;
    ctx.name = bot->GetName();
    ctx.health_pct = bot->GetHealthPct();
    ctx.mana_pct = bot->GetMaxPower(POWER_MANA) > 0
        ? (bot->GetPower(POWER_MANA) * 100.0f
           / bot->GetMaxPower(POWER_MANA))
        : 100.0f;

    PlayerbotAI* ai = GET_PLAYERBOT_AI(bot);
    if (!ai) {
        ctx.state_str = "unknown";
        return ctx;
    }

    // State
    BotState state = ai->GetState();
    ctx.state_str = (state == BOT_STATE_COMBAT) ? "combat" :
                    (state == BOT_STATE_DEAD) ? "dead" : "idle";

    // Role (from playerbots talent-based detection)
    if (PlayerbotAI::IsTank(bot)) ctx.role = "tank";
    else if (PlayerbotAI::IsHeal(bot)) ctx.role = "healer";
    else ctx.role = "dps";

    // Target
    Unit* victim = bot->GetVictim();
    if (victim) ctx.target_name = victim->GetName();

    // Strategies
    ctx.strategies = ai->GetStrategies(state);

    return ctx;
}
```

### Add Combat Context to extra_data JSON

```cpp
std::string botStateJson = "";
if (isBot) {
    BotContext ctx = GetBotContext(bot);
    botStateJson = fmt::format(
        ",\"bot_state\":\"{}\""
        ",\"bot_health\":{:.0f}"
        ",\"bot_mana\":{:.0f}"
        ",\"bot_role\":\"{}\""
        ",\"bot_target\":\"{}\"",
        ctx.state_str, ctx.health_pct,
        ctx.mana_pct, ctx.role,
        JsonEscape(ctx.target_name));
}
```

### Group Role Analysis (Replaces CLASS_ROLE_MAP guessing)

```cpp
void AnalyzeGroupRoles(Group* group) {
    int tanks = 0, healers = 0, dps = 0;

    for (auto* ref = group->GetFirstMember();
         ref; ref = ref->next()) {
        Player* member = ref->GetSource();
        if (!member) continue;

        if (GET_PLAYERBOT_AI(member)) {
            if (PlayerbotAI::IsTank(member))
                tanks++;
            else if (PlayerbotAI::IsHeal(member))
                healers++;
            else
                dps++;
        }
    }
}
```

---

## 8. Integration Effort Estimate

| Phase | Effort | Benefit | Risk |
|-------|--------|---------|------|
| Phase 1: Basic state in extra_data | ~5 lines/hook | State-aware chatter | Very Low |
| Phase 2: Role from playerbots (not guessing) | ~20 lines | Accurate role identity | Low |
| Phase 3: Context-aware reactions | ~30 lines | Immersive responses | Low |
| Phase 4: Advanced (BG objectives, pet state) | ~100 lines | High fidelity | Medium |

**Total for Phase 1-2**: ~50 lines of C++ across existing hooks.

---

## 9. Impact on Existing Features

### Replaces CLASS_ROLE_MAP Guessing
Currently `CLASS_ROLE_MAP` maps Warrior → "tank", but a Warrior bot might be specced/geared as DPS. `PlayerbotAI::IsTank(player)` uses actual talent/gear analysis. This would make role detection accurate instead of assumed.

### Truthful Combat Messages
Instead of generic "Your group role is tanking" prompt hints, we could inject: "You are currently tanking Hogger (72% HP). Your health is at 45%. The healer behind you is at 80% mana." Every LLM response becomes grounded in reality.

### BG State Awareness
Combined with `player->GetBattleground()` for score/flag data, bots could make truthful BG callouts instead of observation-only reactions.

---

## 10. Recommended Next Steps

1. **Phase 1**: Add `GetBotContext()` helper to `LLMChatterScript.cpp`, inject state into `extra_data` for kill/death/loot events
2. **Phase 2**: Replace `CLASS_ROLE_MAP` class-based guessing with `PlayerbotAI::IsTank/IsHeal/IsDps` in C++, pass accurate role in events
3. **Phase 3**: Python prompts use real state ("You are at 30% mana" instead of generic "You manage your mana")
4. **Phase 4**: BG state integration, advanced combat context

### Key Files for Reference

| File | Purpose |
|------|---------|
| `modules/mod-playerbots/src/Bot/PlayerbotAI.h` | Main API — state, strategies, role detection |
| `modules/mod-playerbots/src/Script/Playerbots.h` | `GET_PLAYERBOT_AI` macro, singleton managers |
| `modules/mod-playerbots/src/Bot/Engine/Strategy/Strategy.h` | Strategy type enums |

---

## Conclusion

Injecting real bot state into LLM prompts is not just feasible — it's straightforward with minimal risk. The API is clean, thread-safe, and gracefully degrades if playerbots isn't compiled. Phase 1-2 (~50 lines) would immediately make every combat reaction truthful instead of generic.
