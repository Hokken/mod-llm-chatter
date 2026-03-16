# Contributing to mod-llm-chatter

Thanks for your interest in making bots more alive. This guide covers
how to contribute, what to expect, and how to test your changes.

---

## Branch Model

- **`master`** — stable releases only. Do not submit PRs here.
- **`develop`** — active development. All PRs target this branch.

When `develop` is tested and ready, the maintainer merges it into
`master` and tags a release.

---

## Getting Started

1. Fork the repo and clone your fork
2. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git checkout -b my-feature
   ```
3. Make your changes
4. Test in-game (see [Testing](#testing) below)
5. Push and open a PR against `develop`

---

## What Needs What

| Change type | Recompile? | Restart bridge? | Restart server? |
|-------------|-----------|-----------------|-----------------|
| Python code (`tools/`) | No | Yes | No |
| C++ code (`src/`) | Yes | No | Yes |
| Config keys (`conf/`) | No | Yes or Yes | Depends |
| SQL schema (`data/sql/`) | No | No | Load manually |
| Prompts (in Python) | No | Yes | No |

**Python-only changes** are the fastest to iterate on — just restart the
bridge container and test in-game.

**C++ changes** require a full module recompile and server restart.

---

## Code Style

- **C++**: 4-space indentation, max 80 characters per line, follow
  existing AzerothCore patterns
- **Python**: 4-space indentation, max 80 characters per line
- **SQL**: uppercase keywords, lowercase identifiers
- **Config files**: WoW-style `Key = Value`, 2-space indentation for
  comments and section headers

### Separation of Concerns

Each file has a clear ownership domain. Don't dump unrelated
functionality into the same file. New features or subsystems get their
own file(s).

**C++ source files** (`src/`):
- `LLMChatterShared.cpp` — shared utilities, delivery, facing
- `LLMChatterWorld.cpp` — world events, weather, transport, holidays
- `LLMChatterGroup.cpp` — party/group chatter, kills, loot, quests
- `LLMChatterPlayer.cpp` — player chat, zone intrusion
- `LLMChatterBG.cpp` — battleground events and state polling
- `LLMChatterRaid.cpp` — raid boss events
- `LLMChatterConfig.cpp` — config loading
- `LLMChatterScript.cpp` — script registration only

**Python bridge files** (`tools/`):
- `llm_chatter_bridge.py` — main loop and startup
- `chatter_group.py` — group event handlers
- `chatter_general.py` — General channel handlers
- `chatter_events.py` — world event handlers
- `chatter_prompts.py` — statement prompt builders
- `chatter_group_prompts.py` — group conversation prompt builders
- `chatter_raids.py` — raid event handlers
- `chatter_raid_prompts.py` — raid prompt builders and lore
- `chatter_battlegrounds.py` — BG event handlers
- `chatter_bg_prompts.py` — BG prompt builders
- `chatter_db.py` — all database queries
- `chatter_shared.py` — shared utilities
- `chatter_constants.py` — constants and enums
- `chatter_cache.py` — pre-cache system

### Config Variables

Any tunable value (chances, cooldowns, thresholds, intervals, limits)
should be exposed as a config variable in `conf/mod_llm_chatter.conf.dist`
rather than hardcoded. Follow the existing pattern: define a config key,
load it in `LLMChatterConfig.cpp`, store it as a member variable, and
use the variable in code.

---

## Testing

There is no automated test suite yet. All testing is manual and
in-game.

### Before submitting a PR

1. Start the server and bridge with your changes
2. Log in and verify the feature works as expected
3. Check bridge logs for errors: `docker logs ac-llm-chatter-bridge`
4. Check worldserver logs for module errors
5. Verify you haven't broken existing features (group chatter, General
   chat, BG/raid if relevant)

### Common test scenarios

- **Group chatter**: invite a bot, kill mobs, loot items, complete
  quests, talk in party chat
- **General channel**: stand in a zone and wait for ambient chatter,
  type in General and verify bot responses
- **Battlegrounds**: queue for WSG/AB/EY with bots
- **Raids**: enter a supported raid instance with a group

---

## PR Guidelines

- Keep PRs focused — one feature or fix per PR
- Include a description of what changed and why
- If adding a new event type, include both the C++ hook and Python
  handler
- If adding config keys, include them in `conf/mod_llm_chatter.conf.dist`
  with description comments
- If changing SQL schema, include a migration file in
  `data/sql/db-characters/updates/`

### What we look for in reviews

- Does it work in-game?
- Does it follow separation of concerns?
- Are meaningful config values exposed (not hardcoded)?
- Is it immersion-positive? (bots should feel more alive, not less)
- Does it handle edge cases? (empty groups, dead bots, missing data)

---

## Bug Reports

When opening an issue, include:

- What happened vs what you expected
- Bridge logs (`docker logs ac-llm-chatter-bridge --since 10m`)
- Worldserver logs (any `LLMChatter:` lines)
- Your provider and model
- Whether it's reproducible

---

## Architecture Overview

The module has two halves:

**C++ (worldserver)** — hooks into AzerothCore's ScriptMgr to detect
game events (kills, loot, quests, spells, chat, weather, BG state,
boss encounters). Events are written to `llm_chatter_events` in the
database.

**Python bridge** — polls the events table, builds LLM prompts with
full context (personality, zone, lore, group composition, bot state),
calls the LLM provider, and writes responses back to
`llm_chatter_messages`. C++ picks up responses and delivers them as
chat messages in-game.

For detailed architecture, see `docs/` in the repo.

---

## License

By contributing, you agree that your contributions will be licensed
under the same license as the project (GNU AGPL v3).
