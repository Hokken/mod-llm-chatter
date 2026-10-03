# mod-llm-chatter Architecture

Last updated: 2026-09-22 (transactional addon profile edits, custom emotes, action delivery, gear/pet context)

## Purpose

Reference architecture for humans and LLMs editing
`modules/mod-llm-chatter`.

This document reflects the current source architecture.

For new work, route by ownership first. If you are unsure where a
change belongs, use "Where To Edit What" in this file before touching
code.

## Guiding Principle: Separation of Concerns

New features or subsystems must go in their own file(s) — never dump
unrelated logic into an existing file just because it is convenient.
Shared utilities belong in the dedicated shared layer
(`LLMChatterShared.cpp/h` for C++, `chatter_shared.py` /
`chatter_constants.py` for Python). Each file should have one clear
ownership domain.

Keeping files focused allows AI agents to work on a single file without
loading the entire module into context.

## Repository Boundaries

- **AzerothCore root repo**: the parent AzerothCore server repo where
  this module is installed under `modules/mod-llm-chatter`
- **Module repo**: `modules/mod-llm-chatter` — all runtime Python and
  C++ code lives here
- Runtime code changes belong in the module repo
- This architecture doc lives in `docs/` inside the module repo

## Docker Bind Mounts

The chatter bridge container has two relevant volume mounts:

| Host path | Container path | Mode | Purpose |
|---|---|---|---|
| `modules/mod-llm-chatter/tools/` | `/app/tools/` | `:ro` | Python source (read-only) |
| `modules/mod-llm-chatter/logs/` | `/logs/` | `:rw` | LLM request log output |

The `/logs` mount is defined in `docker-compose.override.yml` under
`ac-llm-chatter-bridge`. The log path config key
`LLMChatter.RequestLog.Path` must point inside `/logs/` to write to
the host filesystem.

**Important**: adding or changing volume mounts requires container
recreation (`docker compose --profile dev up -d ac-llm-chatter-bridge`),
not just `docker restart`.

## High-Level Runtime Flow

1. C++ scripts queue ambient requests and event rows in MySQL.
2. Python bridge polls pending work and routes by event type.
3. Python generates messages and writes them to
   `llm_chatter_messages`.
4. C++ world tick delivers messages in game.
5. Party-channel delivery may play text emotes; General, Guild,
   Raid, and BG delivery does not.

### Screenshot vision data flow

The screenshot vision feature adds a second event source outside the
C++ server:

1. Host-side `screenshot_agent.py` captures the WoW game window.
2. Agent sends the JPEG to a vision LLM (OpenAI, Anthropic, Google,
   or OpenRouter).
3. Vision LLM returns structured JSON (description, atmosphere,
   canonical tags).
4. Agent inserts a `bot_group_screenshot_observation` row into
   `llm_chatter_events` via direct MySQL connection.
5. Bridge claims the event and routes to
   `chatter_screenshot_handler.py`.
6. Handler generates in-character bot comments using existing
   personality, zone context, and vision description.
7. Messages are written to `llm_chatter_messages` for normal C++
   delivery.

Screenshot descriptions and atmosphere serve as background for personal
reactions rather than a narrated inventory of the scene. A recognized
visual time of day takes precedence over clock-derived prompt context.
Roleplay conversations frame the observation as the speakers' surroundings.

The agent runs on the host machine (not in Docker) and connects to
MySQL directly. It is configured via the same `.conf` file and is
disabled by default.

### Proximity chatter data flow

Proximity chatter creates ambient `/say` conversations between bots,
NPCs, and real players as they move through the world:

1. C++ `CheckProximityChatter(bool instanceMaps)` runs on independent
   outdoor and dungeon/raid timers in `LLMChatterWorld.cpp`. Legacy
   configs without scoped values inherit `ScanIntervalSeconds`.
2. `LLMChatterProximity.cpp` scans around each alive, out-of-combat
   real player within a 40-yard radius for eligible NPCs and party bots.
   Outdoor, dungeon, and raid maps are supported; BG and arena maps are
   excluded. NPC qualification follows one global ordered policy:
   client visibility, non-selectable, fake-dead, trigger-creature, and
   internal-name-marker exclusions; denylist; boss exclusion;
   guard/interactive role; humanoid; configured non-humanoid allowlist;
   then reject.
3. One or more speakers are selected from the candidate pool. If all
   candidates are party bots, the scan is skipped (idle chat handles
   that case). Directed NPC interactions keep the addressed NPC first
   and can add zero to two compatible nearby NPCs. A direct interaction
   with an ungrouped playerbot keeps that bot first when it speaks and uses
   the same weighted selector to add zero to two compatible NPCs or ungrouped
   bots. A bot-directed emote can instead produce a witness-only scene with
   one or two nearby speakers while retaining the silent bot as the addressed
   subject outside the speaking roster.
4. A `proximity_say` (single statement) or `proximity_conversation`
   (multi-speaker) event is queued to `llm_chatter_events` with
   NPC spawn GUIDs and nearby entity names in `extra_data`.
5. Python `chatter_proximity.py` claims the event and uses
   `chatter_instance_context.py` for canonical map name, current area,
   and curated dungeon-lore grounding. NPC payloads also carry
   disposition, creature rank, creature type, and qualification reason.
6. Messages are written to `llm_chatter_messages` with channel
   `"say"` (for bots) or `"msay"` (for NPCs).
7. C++ delivery dispatches bot messages via `CHAT_MSG_SAY` and NPC
   messages via `CHAT_MSG_MONSTER_SAY` (speech bubbles). Movement never
   disqualifies a speaker. Only NPCs whose spawn never moves may rotate:
   a facing spline replaces an NPC's wander or patrol movement and the core
   generator may not resume it, so wanderers and patrollers speak unturned.
   A directed line uses its explicit addressee when present; otherwise
   the conversation sequence supplies the fallback. One facing lease is
   retained through the final line before the original orientation is
   restored. Scripted or controlled movement speaks without rotation.
8. When a real player speaks in `/say`, a selected eligible NPC or same-team
   ungrouped playerbot is the addressee unless another nearby candidate's
   name is explicitly marked with a comma or colon as a vocative. Without a
   selection, an unambiguous full name or unique meaningful token can direct
   the line anywhere it occurs. Ambiguous title/place tokens are rejected.
   A different named candidate is preferred as a joining speaker. An
   ineligible cross-faction named bot falls back only to an already selected
   eligible NPC or bot; otherwise the direct route is suppressed. A living
   selected player, party bot, boss, or runtime-ineligible speaking NPC
   suppresses random fallback; dead and non-speaking targets are ignored.
   With no direct addressee, recent-scene and ordinary nearby fallback
   behavior remains available.
9. A social emote directed at an eligible NPC has its own verbal-reaction
   chance and cooldown, independent of the separate 80% animation-mirroring
   roll. SmartAI and
   configured C++ scripted-emote ownership suppresses generated NPC and
   mirror reactions so scripted behavior remains authoritative. When a
   mirror animation is actually scheduled, its emote name is passed to the
   verbal prompt so generated speech cannot contradict the visible action.
10. A social emote directed at a same-team playerbot outside the player's
    group uses the same proximity eligibility boundary. A mapped emote has
    an independent 80% default mirror chance and the bot has an independent
    80% default chance to answer in local `/say`. When the bot's verbal roll
    fails, a separate 50% default witness-scene roll can select one or two
    compatible nearby NPCs or ungrouped bots to comment while the addressed
    bot remains silent. Target-speaking scenes may add zero to two joiners.
    Witness-only scenes retain the addressed bot as structured context but
    exclude it from the speaking roster, so no line is fabricated for it.
    One prompt receives the original player action, addressed subject, and
    full speaking roster, keeping the resulting chain coherent. An accepted
    direct route suppresses the grouped observer path; rejected targets and
    unmapped emotes with the verbal route disabled retain the existing
    external-player observer fallback.
11. Directed `/say` routing is deterministic after an eligible NPC or
    same-team ungrouped playerbot is resolved. It does not use a response
    chance: the addressee is always queued, while only the number of nearby
    joiners is randomized.

NPCs are identified by spawn GUID (`Creature::GetSpawnId()`) rather
than entry ID. Cooldowns, scene matching, and history include map and
instance IDs so parallel copies cannot share state. Ordinary hostile
humanoids may speak while safely out of combat. A hostile non-humanoid
must be deliberately approved by creature entry unless its established
guard or interactive NPC role independently qualifies it. Bosses remain
outside this ambient scanner. `SpeakerDenyEntries` overrides every
ordinary qualification, including humanoids and interactive NPCs.
Internal `[DND]`/`(DND)`, `[PH]`/`(PH)`, and
`[UNUSED]`/`(UNUSED)` templates and engine-marked trigger creatures are
excluded across ordinary and boss dialogue. Nearby-name prompt context
is case-insensitively deduplicated.
One conversation also cannot select two creatures with the same display
name because the JSON response contract identifies speakers by name.
Directed multi-NPC prompts choose either a player-inclusive exchange or
an NPC aside about the player's real words/action. They never generate
dialogue or actions for the real player.

Boss dialogue is a separate flow owned by
`LLMChatterBossDialogue.cpp` and `chatter_boss_dialogue.py`. A boss can
produce a paced sequence of original pre-aggro lines or answer an
explicitly targeted or named `/say` within its extended radius. Queueing
and delivery both require LOS, no combat, an instance map, the shared
boss classifier, and distance greater than calculated aggro range plus
the configured safety margin. Delivery uses the private `myell` queue
channel and monster yell; it never changes facing or threat.

Automatic speech is governed by one presence session per boss spawn and
instance, shared by every nearby real player. The first line follows a
short random delay. Later opportunities use random delays and a decaying
chance that stops decaying at a configurable floor. A missed chance
schedules a new delayed opportunity instead of rerolling each scan, so
the boss retains a small chance to speak throughout a long presence.
Open-ended opportunities are enabled by default; disabling them applies
the configured hard line cap. The session resets after no eligible player
has been nearby for the configured period.
Recent delivered lines are passed back to the prompt so later speech
continues the moment without repeating it. A directed `/say` uses its
separate per-player cooldown and postpones the next automatic opportunity
without consuming the automatic line allowance.

The same comprehensive classifier remains shared with group-kill chatter.
Consequently, an eligible registered-encounter kill, including an
ordinary-rank miniboss, follows the existing guaranteed boss-kill reaction
path instead of normal-trash chance and cooldown rules. This is one reaction
opportunity per actual encounter kill, not a recurring proximity trigger.
Enter-combat chatter deliberately retains its narrower legacy classifier and
probabilities.

The boss denylist limits interference with scripted encounters.
Automatic checks use one round-robin candidate per configured scan pass,
so no more than one expensive creature-grid search runs per interval and
later session-map entries cannot starve. Directed `/say` searches have a
separate per-player/map/instance throttle. Presence, cooldown, pending,
and scan state is synchronized across the world update and player `/say`
hooks, but persistent event queries run outside that mutex. The parsed
denylist is published as an immutable configuration snapshot on load or
reload.

### Guild chatter data flow

Guild chatter reuses shared conversation mechanics while keeping
Guild-specific selection and context in their owning layers:

1. `CheckGuildIdleChatter()` in `LLMChatterWorld.cpp` finds live,
   non-combat guild bots in a guild containing an online real player.
2. C++ rolls `GuildChatter.ConversationChance`, shuffles the live
   roster, and selects one statement speaker or two to three
   conversation participants.
3. One `guild_idle_chatter` event carries `mode` plus structured
   participant GUID, name, zone, and map data. Legacy single-speaker
   payloads remain valid.
4. `chatter_guild.py` selects one RP topic and one event-level zone
   policy. A separate event-level RNG roll may attach up to the latest
   15 visible Guild lines from the oldest active Guild session as
   optional continuity context.
5. The selected topic remains the creative direction. The prompt may
   connect compatible history naturally, but must ignore unrelated
   history and never force a recap or callback. The same context
   decision survives JSON repair and statement fallback.
6. Independent bridge RNG may mark zero, one, or several non-opening
   lines to name contextually relevant earlier speakers. The model
   selects the connection; deterministic cleanup inserts missing
   names when a selected line ignores the cue.
7. Conversation output must contain every selected speaker. Invalid
   JSON gets one repair attempt, then falls back to a primary-speaker
   statement.
8. Accepted lines use shared dynamic delays and are inserted with the
   actual speaker GUID, `channel='guild'`, and
   `owner_subsystem='guild'`.
9. `LLMChatterDelivery.cpp` broadcasts each row through the existing
   Guild delivery branch.

Player-driven Guild exchanges use a separate, session-owned path:

1. `LLMChatterGuild.cpp` owns Guild player chat capture and login/logout
   lifecycle. A login starts a fresh `llm_guild_chat_sessions` row;
   login and logout both delete any prior session transcript.
2. A real player's Guild line is copied into every active session for
   that Guild, then the speaking player's `turn_id` advances.
3. The newest turn cancels older pending events and undelivered reply
   lines for that player session. One high-priority
   `guild_player_message` event is queued after a short debounce with
   the live eligible Guild-bot candidates.
4. The shared LLM intent analysis may resolve either an explicit name or
   an implicit reply to the immediately prior speaker from recent history.
   If it returns no single target for a non-group turn, the bridge preserves
   visible turn-taking by selecting the eligible bot directly before the
   current player line in the stored transcript.
   It also classifies the conversational scale semantically rather than
   matching a fixed phrase list. `chatter_guild_player.py` selects that
   addressed bot first, applies a soft penalty only to other recent-speaker
   selection, and rolls between one reply, multiple independent replies,
   or a genuine multi-bot conversation. A brief single-addressee
   continuation stays with one responder when a reply is warranted; a
   group-directed message raises the independent multi-reply chance without
   forcing multiple bots.
5. Player-reply prompts combine a compact rolling summary with the
   latest 15 visible Guild lines: player messages, player-driven
   replies, ambient statements, and ambient conversation lines.
   Autonomous Guild statements and conversations may receive the same
   raw visible-line window through an independent configurable chance,
   but never receive the private compact player-interaction summary.
   Older ambient lines are not folded into that summary.
6. Callback, player-name, follow-up-question, and participant-reference
   decisions are bridge-side RNG choices. Prompt validation and
   deterministic name insertion keep those choices enforceable across
   different configured models. Brief casual continuations suppress the
   callback, name, and follow-up-question rolls.
7. Summary compaction calls the same `call_llm()` path with the user's
   configured provider and model. It runs only after the unsummarized
   interaction text crosses a configurable threshold.
8. Successful Guild delivery records the visible bot line into every
   active Guild session. Recent player exchanges suppress ambient Guild
   triggers briefly so ambient chatter does not interrupt the player.
   Initial replies use a Guild-specific delay range; later replies use
   the shared full reading, typing, and distraction pacing.

Guild login greetings share the same session boundary without pretending
that playerbots are ready synchronously:

1. The existing `PLAYERHOOK_ON_LOGIN` handler starts the real player's
   Guild session. No AzerothCore or `mod-playerbots` source is modified.
2. `LLMChatterGuild.cpp` rolls one weighted initial delay: quick
   (2-5 seconds), ordinary (8-20), or busy (25-45).
3. Guild-owned pending state waits until the delay expires, then reuses
   the live eligible-bot selector. Missing or still-loading bots cause a
   bounded retry rather than an immediate loss.
4. Logout, relogin, Guild change, module disablement, session staleness,
   or a real Guild message cancels the greeting.
5. One high-priority `guild_login_greeting` event carries the current
   session, target player, delay metadata, and live bot candidates.
6. `chatter_guild_login.py` normally selects one greeter and
   occasionally two or three. One LLM request generates the whole
   sequence as short, distinct, message-only Guild lines.
7. The first line has no extra bridge-side delay because the C++ pending
   timer already supplied the human pause. Additional greeters reuse
   shared dynamic conversation pacing.
8. The bridge validates `session_id` and the initial `turn_id=0` before
   generation and insertion. A player message therefore supersedes an
   obsolete greeting even if the event was already claimed.
9. Native Guild delivery records successful greetings as `reply`
   history, making them visible to later player-session continuity.

### Player-chat input filtering

`LLMChatterConfig` owns the reload-safe, server-side
`LLMChatter.PlayerChat.IgnoredPrefixes` denylist. Matching is literal,
case-insensitive for ASCII letters, and ignores leading whitespace. The
default is empty so existing installations retain their current behavior.

Party, General, Guild, and `/say` capture paths apply this shared filter
before any history write, cooldown/session mutation, or event queue
insertion. A matching Guild line also does not cancel a pending login
greeting. Existing `LANG_ADDON`, hidden-payload, and Playerbot-command
protections remain separate and continue to run. In particular,
`SendAddonMessage` protocol prefixes do not belong in this denylist because
their `LANG_ADDON` traffic is already rejected globally.

### Player-chat history windows

Party and General retain separate recent-line windows for prompt context.
`LLMChatter.ChatHistoryLimit` controls Party reads and defaults to 10 lines.
`LLMChatter.GeneralChat.HistoryLimit` controls General retention per zone
across both factions and ships with a 15-line default. Prompt reads are then
filtered to the reader's faction, so a faction can receive fewer than the
configured number of lines when both factions are active in the zone. Both
values are clamped to 1-50. If the General-specific key is absent, both the
server and bridge fall back to `ChatHistoryLimit`.

These settings are bridge-startup configuration for prompt reads and pruning.
General's server-side retention owner also reloads its value through
`LLMChatterConfig`. Apply a General limit change by reloading the server config
and restarting the bridge together, because both processes prune the same
table. Increasing either window raises prompt size and token use; neither
window is a rolling summary or persistent episodic memory.

### Player-response faction boundary

Playerbot responders to real-player General, Party, Guild, and proximity
messages must match the initiating player's Alliance/Horde team. Candidate
collection enforces this in C++, and the bridge rechecks database-backed
candidate rosters before generation. Delivery performs a final team check for
General, Party, Guild, and login-greeting events so a stale or malformed queued
row cannot speak through the wrong faction channel. An unavailable subject is
not treated as a faction mismatch; only a resolved, differing team is rejected.
General player cooldown keys and history reads are faction-scoped within the
zone. Proximity NPC eligibility remains a separate disposition-aware policy;
the team boundary here applies to playerbots.

General-to-Party relays require the General speaker, the group's real player,
and every responding party bot to share one faction.

## Chatter Mode Ownership

`tools/chatter_mode.py` owns the canonical playerbot identity boundary
and voice contract. In `normal` mode, playerbots speak as people playing
World of Warcraft; in `roleplay` mode, they speak as their characters in
Azeroth. General, Party, Guild, Battleground, Raid, screenshot, emote,
and playerbot `/say` prompt paths must use that shared contract rather
than defining independent versions of normal-mode behavior.

Player-responsive Guild, General, party, proximity-speech, and
proximity-emote prompts share one conversational-scale instruction from
`chatter_shared.py`. The model must answer brief casual input in kind and
must not inflate a lightweight message or action into a speech,
explanation, story, or new topic. This is prompt-level semantic guidance,
not a language-specific keyword list. For player speech, the shared semantic
analysis marks a turn as `brief_casual`; that hard mode suppresses incidental
multi-responder RNG, questions, callbacks, and creative expansion, limits
generated text to 2-8 words and 50 characters, and permits one
format-preserving rewrite when the first result exceeds the contract.
General picks a length tier per reply instead (`pick_brief_casual_tier()`:
tiny 1-4 words/30 chars, short 2-8/50, relaxed 5-14/85, weighted by
`PlayerChat.BriefCasualLengthWeights`); a follow-up bot avoids the first
reply's tier, and the relaxed tier may add one light question back. The
prompt, the fit check, and the rewrite all use the picked tier. Guild
can render a short third-person narrator action because guildmates may be
remote. General remains textual. Party and proximity speech can instead
deliver a valid structured emote with an empty message only while
`brief_casual` is true; C++ skips the blank chat packet and plays only the
emote. Directed player-emote events request the same short scale and may also
use emote-only output, but they retain their existing server reaction chance
and do not receive the semantic optional-reply roll or hard repair gate.

Player-message analysis judges what the turn invites using its meaning and
recent history, never an input-length threshold or phrase list. A terse
invitation for news, advice, an experience, or an explanation can deserve a
concrete answer. Acknowledgments and conversational closure remain brief.
The existing `brief_casual` and `requires_reply` decisions stay separate.
Reply necessity is judged from the whole exchange: silence is eligible only
when the turn clearly needs no further engagement. If silence would feel
like ignoring an ongoing contribution, or the intent is uncertain, the model
is instructed to favor a short acknowledgment unless the purpose clearly
calls for detail. A casual or
declarative message does not by itself signal conversational closure.
Channel length guidance and hard limits still apply; useful detail is
permitted, never mandatory, and replies should not be padded.

General reuses its configurable nonbrief length weights after classification.
Brief turns retain their existing limits and optional-silence policy; Party
continues to bypass optional silence. No additional LLM call is introduced.

The analysis separately marks `requires_reply`: every question must be true,
while statements are judged semantically in conversational context. The bridge
derives `reply_optional` only when the model says a `brief_casual` statement
does not require a reply. Before generation, Guild, General, proximity-speech,
and directed boss-speech handlers make one shared configurable RNG roll. A
failed roll marks the event skipped without calling the generation model; a
successful optional turn stays single-responder. Party player messages do not
use this silence gate: once queued, they continue to a concise response even
when classified as `reply_optional`. If the strict repair
still overruns, Party uses the shared deterministic bound for each selected
speaker instead of dropping the statement or conversation. A casual
multi-addressee classification therefore retains the forced conversation path
and every selected responder. Questions, requests, instructions, warnings,
important information, and other turns that clearly expect engagement are not
optional. This remains semantic and contextual, with no phrase, punctuation,
or keyword list.

Emote-only delivery resolves the emote name before consuming the row. Invalid
names receive a terminal `invalid_emote` drop instead of a retry, and party
rows delivered inside battlegrounds reuse `IsBGAllowedEmote()` before playing
the animation.

Actual NPCs do not follow `LLMChatter.ChatterMode`. Proximity payloads
already identify them with `is_npc`; `chatter_proximity.py` therefore
keeps NPC speakers in-world while routing nearby playerbots through the
configured player voice. A mixed scene applies the rule per speaker.

Persistent character backstories and race/class worldview context are
RP-only prompt inputs. Normal-mode memory callbacks are presented as
past gameplay events. Pre-cached group replies have no mode column, so
the bridge deletes only `ready` cache rows at startup before refilling
them under the current mode.

## Persona Ownership

`tools/chatter_persona.py` owns who is speaking and how they feel, for
Party, Guild and General prompts. Prompt builders never roll their own
tone, traits or mood.

- **Identity resolution**: `resolve_persona()` uses the bot's
  `llm_group_bot_traits` row (the given group, or the most recently
  assigned one when Guild/General pass no group), then the persistent
  `llm_bot_identities` row, then a deterministic fallback seeded from
  the bot's name (GUID only when no name is known). The fallback makes
  no DB writes or LLM calls, so any bot keeps the same traits and tone
  on every message and in every channel. `fallback_tone()` gives the
  same tone to single Party builders whose stored tone is missing.
  Normal mode always uses `chatter_mode.resolve_player_personality()`
  and never a stored backstory. Personas are resolved on every call
  (no cache), so group joins and leaves apply immediately.
- **Profile creation**: `chatter_identity.py` owns persistent trait,
  tone and backstory creation and explicit regeneration. Party's
  `chatter_group_state.py` keeps session/role/location assignment and
  re-exports the previous identity entry points. General and Guild call
  `prepare_channel_persona()` only for selected speakers; candidate
  lookup stays read-only. Per-bot locks serialize bridge work; short
  conditional persistence transactions reject LLM output made obsolete
  by profile edits. Provider calls never hold database write locks.
  Failed work has a bounded retry cache (`Profile.RetrySeconds`).
- **Guild preparation**: `chatter_identity_jobs.py` discovers missing
  profiles in guilds with a current online real-player Guild session.
  Membership and online state are rechecked before each ensure. The
  bridge schedules one bounded batch per configured interval, yielding
  to urgent events. Keyset paging prevents failed profiles from starving
  later members. This includes newly accepted invitations and existing
  members, without generating profiles for bot-only startup guilds.
  Selected Guild speakers also receive an ensure before their prompt.
  Discovery depends on the existing player-reply/login session lifecycle;
  with both session-producing features disabled, selected-speaker
  preparation still works but there is no membership prewarming.
- **General/Guild sampling**: `sample_channel_backstory()` copies the
  persona with or without backstory using independent per-speaker rolls
  (`Backstory.GeneralChance` / `GuildChance`, both 25 by default).
  The prepared cast, including omitted backstories, survives prompt
  repairs and continuation turns. Traits and tone are always retained;
  no roll changes the saved profile. All missing fields are prepared
  before sampling, so first-use speech may require two extra LLM calls.
  Normal mode never creates or injects roleplay backstories.
- **Mood**: `resolve_mood()` reads the real event mood from
  `chatter_group_state.get_bot_mood_label_by_guid()`, which uses the
  bot's most recent live entry in the existing group mood store. A bot
  that wiped in a party carries that mood into Guild and General.
  The score drifts toward neutral as further events arrive, and an
  entry older than two hours is ignored. A neutral or missing mood
  renders no mood line; no mood is ever invented.
- **Rendering**: `build_persona_block()` (one speaker) and
  `build_cast_lines()` (conversations) render personas for party idle
  chatter, party multi-bot conversations and General prompts. Both
  state that personality and tone are fixed while mood, topic,
  optional angles and background feelings only colour them.
  Conversations also state that emotions shift only in reaction to
  what is said. Single-event Party builders and Guild prompts keep
  their own identity lines, but take tone from the stored value or
  `fallback_tone()` and mood from `resolve_mood()`, never from a
  random roll.
- **Backstory**: `format_backstory_block()` is the one backstory
  wording (roleplay only), used by the persona block and by party
  reactions. `party_reaction_backstory()` gates it with
  `LLMChatter.Backstory.Enable` and `PartyReactionChance`.
  `run_group_handler()` appends it after `build_prompt()`, as does the
  zone-transition handler; `build_player_response_prompt(backstory=)`
  renders it for replies to the player (skipped for brief casual
  turns); multi-bot party conversations gate each speaker's
  `backstory` field (`_gate_conversation_backstories()`), which
  `_append_bots_with_rp()` renders through the cast block.
- **Flavor**: `chatter_prompts.py` owns the gates. Creative twists use
  `LLMChatter.Persona.TwistChance` and are labelled as optional angles.
  Spices must pass `LLMChatter.Persona.SpiceChance` before
  `LLMChatter.PersonalitySpiceCount` items are picked
  (`maybe_pick_personality_spices()` + `format_spices_line()`).
  Conversation prompts carry a per-message length sequence only; there
  is no random per-message mood sequence.

Bridge startup loads the flavor settings once from
`chatter_group.init_group_config()` (`configure_prompt_flavor()`).

## Conversation Thread Ownership

`tools/chatter_threads.py` owns conversational continuity for party
idle chatter, guild chat and the General channel: the thread store,
the soft nudge for each exchange, prompt rendering, and parsing of the
model's thread report.

- **Keys**: `('party', group_id)` (plain group ids are normalized),
  `guild_key(guild_id)` and `general_key(zone_id, faction)` (General is
  split by faction). `reconcile_active_groups()` prunes party keys only;
  guild and General threads end through the TTL/LRU limits and
  `cleanup_all_session_data()`. `threads_enabled(key)` applies
  `Threads.GuildEnable` / `Threads.GeneralEnable` under
  `Threads.Enable`.
- **General**: `chatter_ambient.process_statement()` and
  `process_conversation()` plan a turn for `plain` messages only (the
  other ambient types keep their own prompts), pass it to
  `build_plain_statement_prompt()` / `build_plain_conversation_prompt()`
  in place of the random topic, and record the queued row ids (the
  conversation marks the exchange incomplete when a line was dropped).
  `process_general_player_msg_event()` notes the player's line and
  gives the reply prompt read-only context.
- **Guild**: `process_guild_idle_chatter_event()` plans one turn and
  shares it with the statement fallback; `_build_guild_prompt()` and
  `_build_guild_conversation_prompt()` swap the topic idea / shared
  subject for the thread block and request the report through the
  message-only schemas (`extra_field` / `trailing_object`). A repaired
  conversation is never adopted. Guild player replies note the
  player's line and append read-only context after the session memory.

- **Store**: in memory, keyed by group id and guarded by one lock. It
  holds the current subject (topic label, energy 0-1, open point,
  exchange count), the last `LLMChatter.Threads.HistorySize` finished
  subjects, per-bot lingering feelings (visible for
  `FeelingTurns` exchanges, across subject changes), recent
  interruptions (`MaxInterruptions`), and pending exchanges. Each
  group state has a session id and a major-event revision.
- **Retention**: a state idle for `IdleTTLMinutes` expires on lookup,
  the store is capped at `MaxGroups` (least recently used first), and
  `check_idle_group_chatter()` calls `reconcile_active_groups()` with
  the current `llm_group_bot_traits` group ids every tick, so a party
  that ended through any path (last bot removed in C++, disband,
  logout) is forgotten even while other players stay online.
  `cleanup_stale_groups()` and `cleanup_all_session_data()` also
  clear it.
- **Planning**: `plan_idle_turn()` picks continue, drift, callback or
  new, weighted by the subject's effective energy (exchange decay plus
  cooling over `CoolMinutes` of silence) through the configurable
  energy bands (`HighEnergyThreshold`, `LowEnergyThreshold`) and move
  weights (`*EnergyMoveWeights`). With the defaults every move stays
  possible at any energy. Fresh subjects come from persona, surroundings or the
  topic pool (`*TopicWeight`; never the pool inside instances).
  `SurpriseChance` adds an explicit allowance for believable
  surprises. The rendered `<conversation_thread>` block calls itself
  "a nudge, not a script", contains no example lines, and replaces the
  random pool topic in both idle builders.
- **Report**: idle prompts ask for an optional `thread` object: a
  trailing field for single statements
  (`append_json_instruction(extra_field=...)`) and a trailing array
  element for conversations
  (`append_conversation_json_instruction(trailing_object=...)`, which
  `parse_conversation_response()` skips). The report is validated
  (real JSON booleans only, known speakers only, clipped text). A
  report without a usable topic never removes the current subject; it
  only applies safe updates (feelings, decay). If only the trailing
  report is malformed or cut off, `parse_conversation_response()`
  still returns the complete dialogue before it; broken dialogue is
  rejected as before. `ReportTokens` is added to the output budget.
- **Delivery confirmation**: `insert_chat_message()` returns the row
  id. `record_idle_exchange()` holds the parsed report against the
  ids actually queued and their speakers (none queued: nothing
  recorded). It is marked incomplete when any dialogue line the model
  wrote was filtered before queueing (`count_conversation_items()`
  versus queued rows). The next `plan_idle_turn(db=...)` or
  `render_for_player_reply(group_id, db)` checks
  `llm_chatter_messages`. A row counts as spoken only with
  `delivered = 1`, `delivered_at IS NOT NULL` and
  `drop_reason IS NULL`: C++ first claims a row (`delivered = 1`,
  no `delivered_at`) and stamps `delivered_at` only after the send,
  so claimed rows stay pending. When every row was spoken and the
  exchange is complete, the report is adopted, timed by the actual
  delivery (the database computes the age, so no timezone
  conversion). With a partial or incomplete exchange the exchange
  counts (decay) but the report is not adopted. When nothing was
  spoken, or after `PendingTimeoutSeconds`, it is discarded; the
  timeout also applies while the status lookup fails, and at most
  `MaxPending` exchanges wait per party.
- **Stale completions**: pending exchanges from an earlier session
  (after a clear or re-creation) are ignored, and a report planned
  before a wipe or death never overwrites the subject that event
  set. `run_group_handler()` captures the group's thread session with
  `capture_session()` before its LLM call and passes it to
  `note_event()`, so an event completing after the group was cleared
  or replaced is dropped. For a group with no thread yet,
  `capture_session()` creates the session up front, so a first event
  is guarded the same way and still starts the thread normally.
- **Interruptions**: `run_group_handler()` calls `note_event()` after
  storing a reaction, passing the reaction's `message_id` from
  `run_single_reaction()`. The event is a fact at once; the reaction
  line is quoted only after it was delivered. Minor events are shown
  to the next idle exchange, so the subject can resume. `bot_group_wipe` and `bot_group_death`
  take over as the subject and move the old one to history.
  `process_group_player_msg_event()` calls `note_player_message()`,
  and party replies get read-only context from
  `render_for_player_reply()` (skipped for brief casual replies and
  cold subjects).
- **Anti-repetition**: for continue, drift and callback moves
  (`IdleTurn.builds_on_subject`),
  `build_anti_repetition_context(allow_same_subject=True)` still bans
  repeated wording but allows developing the current or an earlier
  subject.
- Memory-recall idle exchanges keep their own focus: they neither see
  nor consume the thread.

## System Prompt Architecture

All prompt builders return a `PromptParts` object (defined in
`chatter_shared.py`). `PromptParts` subclasses `str` so it is
backward-compatible with code that treats prompts as plain strings.
It carries two extra attributes:

- `.system_prompt` — persona, rules, format instructions
- `.user_prompt` — event context, chat history, the actual task

### Flow

1. Prompt builder calls `PromptParts(system_prompt, user_prompt)`.
2. `call_llm()` or `quick_llm_analyze()` in `chatter_llm.py`
   auto-detects `PromptParts` via `_split_prompt()`.
3. Provider dispatch:
   - **Anthropic**: native `system=` parameter + user message;
     sampling temperature is sent through `extra_body` for Anthropic
     SDK v1 compatibility
   - **OpenAI / Google / OpenRouter / Ollama**: system role message +
     user role message; `llm_compat.py` selects the token field and
     optional parameters from a conservative model capability profile
     resolved through one ordered model-rule table; parameter selection
     and reasoning-token budgets consume the same resolved capabilities
   - **Modern OpenAI reasoning models**: use
     `max_completion_tokens`, coordinate temperature with reasoning
     effort, and apply `LLMChatter.OpenAI.ReasoningEffort` only when
     compatible; `_effective_max_tokens()` applies the OpenAI multiplier
     whenever hidden reasoning may consume the output budget
   - **New or unrecognized models**: start with safe parameters; an
     explicit provider rejection can remove `temperature` or
     `reasoning_effort`, or switch the token-limit field, retry the
     rejected call, and cache that correction for the process lifetime
   - **OpenRouter reasoning**: `_apply_openrouter_options()` adds the
     opt-in `reasoning` object to normal and quick-analysis requests;
     `_effective_max_tokens()` applies its multiplier only while an
     effort other than `none` is enabled
   - **Ollama**: context size is owned by the Ollama server because its
     OpenAI-compatible endpoint has no per-request context parameter;
     disabling thinking sends `reasoning_effort = none` and retains the
     `/no_think` prompt fallback
4. If a plain string is passed instead of `PromptParts`, the entire
   string is sent as a single user message (backward compatibility).

### Token-Saving Gates

Two config-driven RNG checks control optional prompt sections:

- `EmoteChance` - gates inclusion of the ~244-emote list (~500 tokens).
  Checked once per prompt build. Does NOT apply to General channel
  (emotes are proximity-based animations; General is zone-wide text,
  so emotes are intentionally suppressed via `skip_emote=True`).
- `ActionChance` - controls whether action narrations appear. Two
  strategies depending on path:
  - **Single statements**: pre-call RNG in `append_json_instruction()`
    decides before the LLM call whether to ask for an action (saves
    tokens when disabled).
  - **Conversations** (General, Proximity, Group idle, Group handlers,
    Screenshot vision): prompts always tell the LLM to include actions
    (in RP mode). `strip_conversation_actions()` in `chatter_shared.py`
    enforces ActionChance per-message post-parse. This avoids trusting
    the LLM to randomize naturally.

If the prompt/output parser yields `"emote": null`, Python insert paths
must preserve that null value. Do not synthesize a fallback emote during
DB insert. `LLMChatter.EmoteChance` is the source of truth for whether
the LLM is even asked for an emote.

## Queue Model, Timing, and Priority

The module currently uses three separate DB-backed queues. They do not
share one global scheduler.

### 1) `llm_chatter_queue` - ambient request queue

- used for ambient General chatter requests
- inserted by C++ in `LLMChatterAmbient.cpp`
- consumed by `process_pending_requests()` in
  `llm_chatter_bridge.py`
- fetched FIFO: `ORDER BY created_at ASC`
- gated by `LLMChatter.MaxPendingRequests`, which currently limits only
  this queue, not the event queue
- C++ stores the selected `message_type`; Python does not reroll it
- `item_context` is populated only for trade requests and contains a
  value-only snapshot of an eligible item in the first speaker's live
  inventory

### 2) `llm_chatter_events` - reactive/event queue

- used for `bot_group_*`, `bg_*`, `player_general_msg`, real
  `bot_loot_item`, weather, transport, holiday, and related event-driven
  work
- rows carry `priority`, `react_after`, and `expires_at`
- fetched by the bridge only when:
  - `status = 'pending'`
  - `react_after <= NOW()` or null
  - `expires_at > NOW()` or null
- claim order is:
  - `ORDER BY priority DESC, created_at ASC`
- workers claim via compare-and-swap update to `processing`

### 3) `llm_chatter_messages` - outbound delivery queue

- Python writes final chat rows here with a `deliver_at` timestamp
- C++ delivery polls one ready row at a time
- when `LLMChatter.PrioritySystem.Enable = 1` and
  `LLMChatter.PrioritySystem.DeliveryOrderEnable = 1`, delivery joins
  back to `llm_chatter_events` and orders by:
  `COALESCE(e.priority, 0) DESC, m.deliver_at ASC`
- ambient rows with `event_id = NULL` therefore remain lowest priority
- when the delivery-order feature is disabled, fallback order remains
  `deliver_at ASC`
- `delivered = 1` means the row was consumed, not necessarily spoken;
  `drop_reason IS NULL` distinguishes successful delivery from a drop
- directed rows carry optional player, bot, or NPC addressee IDs used for
  facing; dropping one directed line cancels its remaining queued lines

### Timing layers

There are two separate timing stages:

- **Event reaction delay**: C++ sets `react_after` when the event row is
  inserted. This delays when Python is allowed to process the event.
  The shared C++ implementation now uses table-driven priority and delay
  registries rather than long conditional chains.
- **Message delivery delay**: Python sets `deliver_at` when it inserts
  the final message row. This delays when C++ is allowed to speak it in
  game.

`calculate_dynamic_delay()` in `chatter_shared.py` controls the second
stage for most Python-generated messages. Player-directed replies use
`responsive=True`; ambient/group conversations can also include reading
time from the previous message length.
Player-triggered proximity say, active-scene reply, conversation, and emote
events use the high priority tier (0-2 second reaction delay by default) and
a short expiry, while ambient proximity events remain lower priority.

### General-Channel Pacing Gate

Automated General statements and conversations share a bridge-side,
per-zone reservation timeline. A producer calculates every relative
follow-up delay, then atomically reserves the full sequence through its
last scheduled line. The next ambient or world-event sequence begins
only after `GeneralChat.MinZoneGap` has elapsed from that endpoint. This
prevents independently processed ambient, transport, weather, and
holiday conversations from stacking their follow-ups into the same few
seconds. Player-directed General replies remain responsive and may
interrupt automated chatter, but extend the known zone endpoint so later
automation backs off.

### Party Chat Pacing Gate

Party-channel messages use a DB-backed pacing table,
`llm_party_chat_pacing`, keyed by `group_id`.

- Python-generated party messages reserve delivery slots through
  `tools/chatter_party_gate.py` before inserting into
  `llm_chatter_messages`.
- Final party rows carry `group_id`, `delivery_policy`, and
  `delivery_reason` so delivery can refresh the same pacing state when
  the line actually appears in game.
- C++ direct party paths that bypass Python delivery, such as
  pre-cached instant reactions and farewell packets, call
  `RecordPartyChatGateActivity()` after sending. They are not delayed,
  but they still make later filler chatter back off.
- Normal join handling pre-generates each bot's farewell after its greeting.
  A player-session rejoin deliberately skips another visible greeting, but
  still restores a persistent farewell or generates a missing one before the
  join event completes. `OnRemoveMember` can therefore send the stored line
  synchronously before deleting the session trait row.
- Policy names are `urgent`, `responsive`, `contextual`, `filler`, and
  `bypass`. Combat/state/BG/raid-critical feedback remains immediate;
  idle-style filler can defer before spending LLM tokens.

### Group serialization

The bridge processes many events in parallel, but it uses a per-group
lock so events sharing the same `group_id` do not run concurrently. This
avoids cross-talk and state races inside a single party.

Session 69 refined this with two lock lanes:

- urgent/high events and filler events for the same `group_id` no longer
  share the same queued lock lane
- this reduces the chance that queued filler work blocks queued urgent
  work for the same group

### Current priority behavior and remaining limits

The module now has meaningful end-to-end priority behavior, but it is
still not a perfect single global scheduler across every queue and
worker lane.

What priority now affects:

- event claim order from `llm_chatter_events`
- bridge scheduling, where urgent backlog suppresses or defers filler
  jobs
- pre-cache fairness during urgent backlog
- final in-game delivery ordering when priority delivery is enabled

What is still limited:

- `llm_chatter_queue` is FIFO and has no priority field
- same-executor saturation can still delay work even when claim order is
  correct
- same-group serialization still exists inside each urgency lane
- `GlobalMessageCap` and `TransportBypassGlobalCap` remain legacy config
  values and are not the main protection mechanism anymore
- provider-safety mode is bridge-side suppression logic, not a hard DB
  queue partitioning system

This is why future work should focus on validation and tuning more than
on inventing a first priority system from scratch.

## Main Bridge Loop

The bridge is **not** a single-threaded "process everything inline"
loop. It is a coordinator loop plus a worker pool.

### Coordinator thread

`llm_chatter_bridge.py` owns one long-running `while True` loop that:

- opens a DB connection for fast coordinator work
- harvests finished futures
- runs periodic cleanup SQL
- claims ready event rows from `llm_chatter_events`
- submits claimed work to worker threads
- launches background timer-like tasks when their intervals elapse
- sleeps for `LLMChatter.Bridge.PollIntervalSeconds` between iterations

### Worker pool

The bridge creates a `ThreadPoolExecutor` with:

- `max_concurrent = LLMChatter.Bridge.MaxConcurrent` for event workers
- `max_workers = max_concurrent + 4` total threads

Event rows claimed from `llm_chatter_events` run in worker threads via
`process_single_event()`, each with its own DB connection.

### Group serialization inside the worker model

Event processing is parallel by default, but group-scoped events are
submitted through `_run_with_group_lock(...)` so only one event per
`group_id` executes at a time.

### Background timer-style tasks

These are not processed inline in the same event loop body once due;
they are scheduled onto the worker pool as separate jobs:

- legacy ambient request processing from `llm_chatter_queue`
- idle group chatter checks
- bot-question checks
- pre-cache refills

So the current architecture is:

- one coordinator loop
- multiple event workers
- several interval-driven background jobs using the same executor

Session 69 added two scheduling controls around that model:

- **bridge yield mode**: legacy ambient requests, idle chatter, and bot
  questions can yield when urgent backlog exists
- **safety mode**: under sustained backlog, the bridge suppresses
  filler-first launches before sacrificing urgent work

## Current C++ Module Map

| File | Approx lines | Primary ownership |
|---|---:|---|
| `src/LLMChatterScript.cpp` | 17 | Registration coordinator only |
| `src/LLMChatterShared.cpp` | ~2500 | Shared helpers: SQL/JSON escaping, canonical lookups, queue insertion, cooldowns, priorities/delays, delivery helpers, spawn-GUID creature lookup, NPC role descriptions, and the shared named-boss cache/classifier |
| `src/LLMChatterReplyHold.cpp` | ~95 | `HoldBotForReply()`: a short stop-and-face hold (at most 4 s) for an ungrouped bot that owes a player a reply; released when the bot enters combat or one of its lines is delivered or dropped |
| `src/LLMChatterShared.h` | 83 | Shared declarations still used across domains; `class Unit` forward-declared for `SendUnitTextEmote()`; currently also declares world/player registration |
| `src/LLMChatterDelivery.cpp` | ~1000 | Outbound DB polling and channel dispatch, including instance-aware local revalidation for `say`/`msay` and safe boss `myell` delivery |
| `src/LLMChatterDelivery.h` | 4 | Narrow delivery extraction declaration used by `LLMChatterWorld.cpp` |
| `src/LLMChatterAmbient.cpp` | 963 | Ambient world/event ownership: day/night transitions, holiday start/stop routing, weather state tracking, weather reactions, zone-level ambient chatter selection, ambient request queue writes |
| `src/LLMChatterAmbient.h` | 24 | Narrow ambient declarations consumed by `LLMChatterWorld.cpp` |
| `src/LLMChatterLoot.cpp/.h` | Real ungrouped-playerbot loot capture, per-source reservoir sampling, bounded aggregation, audience/cooldown revalidation, and event queueing |
| `src/LLMChatterTrade.cpp/.h` | Demand-driven quality-weighted selection and value snapshots of tradeable items from the selected ambient seller's live inventory |
| `src/LLMChatterNearby.cpp` | 691 | Nearby-object and nearby-creature scanning, POI scoring, nearby direct event queueing, nearby-local cooldowns |
| `src/LLMChatterNearby.h` | 6 | Narrow nearby scan declaration consumed by `LLMChatterWorld.cpp` |
| `src/LLMChatterWorld.cpp` | ~1000 | WorldScript ownership, thin ambient/nearby/delivery/proximity/boss delegation, transport polling and route announcements, transport-private state, retained world-private `QueueEvent()` helper |
| `src/LLMChatterGuild.cpp` | ~750 | Player-driven Guild Chat capture, per-login session lifecycle, deferred login greetings, eligible-bot selection, stale-turn cancellation, recent-interaction suppression, and delivered-line history writes |
| `src/LLMChatterGuild.h` | ~20 | Guild registration and delivery/world cross-call declarations |
| `src/LLMChatterGroup.cpp` | ~1350 | Shared group state definitions, shared helpers (`GroupHasRealPlayer`, `GetRandomBotInGroup`, `CountBotsInGroup`, pre-cache helpers), disabled-by-default MultiBot-Chatless `MBOT` fallback handler, `CleanupGroupSession()` coordinator, thin `LLMChatterGroupPlayerScript` shell wrappers, registration |
| `src/LLMChatterGroupCombat.cpp` | ~2550 | Remaining group PlayerScript implementation bodies (kill/death/loot/combat/chat/level/quest/achievement/spell/resurrect/corpse-run/dungeon-entry/emote dispatch), text-emote target classification and group gating, zone transition handling, combat state callouts, `MBOT` debug-log suppression, file-local `QueueStateCallout()` |
| `src/LLMChatterGroupInternal.h` | ~235 | Shared group internal structs, cooldown/batch/mutex declarations, helper declarations, domain entry points, and `EmoteTargetType` |
| `src/LLMChatterGroupJoin.cpp` | 877 | Group join batching: `QueueBotGreetingEvent()`, `EnsureGroupJoinQueued()`, `FlushGroupJoinBatches()`, `LLMChatterGroupScript` (GroupScript: `OnAddMember`, `OnRemoveMember` with farewell, `OnDisband`) |
| `src/LLMChatterGroupEmote.cpp` | 780 | Emote reaction system: delayed bot/creature mirror events, emote static data, grouped and ungrouped playerbot mirroring, creature mirroring, observer reactions, and cooldown eviction |
| `src/LLMChatterGroupQuest.cpp` | 530 | Quest accept batching: `FlushQuestAcceptBatches()`, `LLMChatterCreatureScript` (AllCreatureScript: `CanCreatureQuestAccept` with debounce/immediate paths) |
| `src/LLMChatterGroupPvP.cpp` | ~630 | Overworld PvP: opposing-faction enemy resolution (players and their pets), the identity visibility gate, PvP reactor selection, enemy JSON fields, per-group and per-enemy PvP cooldowns, PvP pull, player-kill, and pet-kill entry points |
| `src/LLMChatterDuel.cpp` | ~300 | Duel start/end `PlayerScript`, duel reactor selection, duel cooldowns, and `bot_group_duel_start` / `bot_group_duel_end` queueing |
| `src/LLMChatterGroup.h` | 18 | World-to-group cross-call surface plus group registration |
| `src/LLMChatterPlayer.cpp` | 1105 | Player General-channel hooks, General cooldowns, subzone cooldowns, `EnsureBotInGeneralChannel()`, player registration |
| `src/LLMChatterRaid.cpp` | 767 | Raid boss hooks (pull/kill/wipe), boss lookup table (80+ entries across Classic/TBC/WotLK), `IsDatabaseBound() override`, raid registration |
| `src/LLMChatterProximity.cpp` | 2674 | Ordinary outdoor/instance proximity scans, curated NPC/playerbot eligibility and compatibility, selected/named `/say` routing, mixed bot-directed reaction chains, map/instance-aware scenes and cooldowns, and event payload construction |
| `src/LLMChatterProximity.h` | ~75 | Proximity scan and player-say hook declarations consumed by `LLMChatterWorld.cpp` and `LLMChatterGroupCombat.cpp`, plus the narrow fight onlooker helpers used by `LLMChatterProximityFight.cpp` |
| `src/LLMChatterProximityFight.cpp/.h` | ~1090 | Duel and overworld PvP onlooker reactions: own `PlayerScript` (duel request/start/end, PvP kill), duel-instance lifecycle and moment selection, one reaction per moment (proximity speech for same-faction bots, emotes for opposite-faction bots), staggered emote steps, and delivery-time revalidation |
| `src/LLMChatterBossDialogue.cpp/.h` | ~850 | Separate boss-only pre-aggro scanning, safe-band eligibility, selected/named `/say` routing, denylist, and boss-instance presence scheduling |
| `src/LLMChatterBG.cpp` | 1348 | Battleground hooks, BG state polling, BG queue helpers, BG registration |
| `src/LLMChatterBG.h` | 14 | BG registration declaration |
| `src/LLMChatterCommand.cpp` | ~1620 | Player command bridge for the Chatter Companion addon. `.llmc` subcommands `roster`, `get`, `set`, `setbackstory`, `regenbackstory`, `forget`, plus the chunked upload `put` / `commit` / `cancel` (per-player staging, 200-character chunks, up to 64 per field). Percent-encoding protocol and UTF-8 character limits (64 per trait, 1,000 per backstory). Every profile edit is validated as a whole and written as one `CharacterDatabaseTransaction` (identity, session traits, cache invalidation, optional backstory, and the tone/backstory regeneration events via `AppendChatterEvent()`); the session-owned commit callback only sends the addon's reply. The addon sends traits only; `setbackstory` and `bs` chunks are a server-side path for manual use. See [`chatter-addon-reference.md`](chatter-addon-reference.md) |
| `src/LLMChatterConfig.h/.cpp` | ~900 | Config loading, reload-safe creature-entry sets, and config struct |
| `src/llm_chatter_loader.cpp` | 11 | Module entry point, calls `AddLLMChatterScripts()` |

## Current Registration Shape

`llm_chatter_loader.cpp` calls:

- `AddLLMChatterScripts()`

`LLMChatterScript.cpp` is now the coordinator and calls:

- `AddLLMChatterWorldScripts()`
- `AddLLMChatterGuildScripts()`
- `AddLLMChatterGroupScripts()`
- `AddLLMChatterPlayerScripts()`
- `AddLLMChatterLootScripts()`
- `AddLLMChatterBGScripts()`
- `AddLLMChatterRaidScripts()`
- `AddLLMChatterCommandScripts()`

Current header topology is intentionally functional, not perfectly
uniform:

- `LLMChatterShared.h` declares shared helpers plus
  `AddLLMChatterWorldScripts()` and `AddLLMChatterPlayerScripts()`
- `LLMChatterGroup.h` declares `AddLLMChatterGroupScripts()` plus the
  explicit world-to-group cross-call surface
- `LLMChatterBG.h` declares BG registration

This asymmetry is known and acceptable in the shipped source state.

## Current Python Module Map

### Entry and orchestration

| File | Primary ownership |
|---|---|
| `tools/llm_chatter_bridge.py` | Main loops, event claiming, registry-driven routing, worker orchestration |
| `tools/chatter_event_registry.py` | Central Python event registry: handler module/function resolution, producer notes, payload field docs, dead-event tracking |
| `tools/chatter_ambient.py` | Ambient statement/conversation generation |
| `tools/chatter_loot.py` | Real `bot_loot_item` validation, exact-looter resolution, prompt generation, and General delivery |
| `tools/chatter_guild.py` | Guild prompts and insert orchestration |
| `tools/chatter_guild_player.py` | Player-driven Guild replies, reply topology, session-context prompts, and rolling summary compaction |
| `tools/chatter_guild_login.py` | Real-player login greetings, responder selection, short-message prompts, and greeting pacing |

### Group domain

| File | Primary ownership |
|---|---|
| `tools/chatter_group.py` | Group join, group player message flow, idle chatter, and group-side message inserts for those paths |
| `tools/chatter_group_handlers.py` | `bot_group_*` reaction handlers, `execute_player_msg_conversation()`, thin wrappers around the shared handler pipeline for most single-reaction group events |
| `tools/chatter_handler_pipeline.py` | Shared `run_group_handler()` pipeline: extra_data parsing, guard checks, traits lookup, context assembly, prompt dispatch, chat storage, mood update, event completion/failure handling |
| `tools/chatter_group_prompts.py` | Group prompt builders, nearby-object prompts, pre-cache prompt builders, `build_player_msg_conversation_prompt()`. All major party chatter builders accept `map_id=0` and inject `get_dungeon_flavor(map_id)` as location context when inside a dungeon instance, replacing zone/subzone lore. Excluded: OOM, low-health, level-up. |
| `tools/chatter_group_state.py` | Group mood/traits/history state; owns the event mood store, including the cross-channel `get_bot_mood_label_by_guid()` lookup |
| `tools/chatter_duel.py` | Duel start/end handlers and prompt builders for `bot_group_duel_start` and `bot_group_duel_end` |
| `tools/chatter_group_general_reaction.py` | General-to-party relay: queues and handles `bot_group_general_reaction` events when grouped bots react in party chat to bot-authored General lines |

### Shared and support layers

| File | Primary ownership |
|---|---|
| `tools/chatter_shared.py` | Shared prompt, parse, count, and delay helpers. Also owns gear/pet context: `build_gear_context()` describes a bot's equipped weapons and, for Hunters and Warlocks, its active pet (a stabled pet is ignored), second person for solo prompts; `attach_speaker_gear()` / `append_speaker_gear()` give multi-speaker prompts the third-person form. Gated by `LLMChatter.GearContext.Enable` |
| `tools/llm_compat.py` | Declarative OpenAI-compatible model capability profiles plus narrowly scoped parameter-rejection recovery and process-local learned overrides |
| `tools/chatter_mode.py` | Canonical normal/RP playerbot identity and channel voice rules, plus mode-invariant NPC guidance |
| `tools/chatter_text.py` | Parsing, sanitization, anti-repetition, and chat length limiting. Never slice LLM chat output by hand; use `shorten_chat_message()` or `shorten_chat_question()` from this file. |
| `tools/chatter_llm.py` | Provider/model calls for Anthropic, OpenAI, Google Gemini, OpenRouter, and Ollama; `get_llm_client()` shared client factory; `_split_prompt()`, `_build_chat_messages()`, `_ollama_user_msg()`, `_apply_google_options()`, `_apply_openrouter_options()`, `_openrouter_headers()` for system/user prompt separation and provider tuning; delegates cross-model parameter selection to `llm_compat.py`; `label=` param logs every call via `chatter_request_logger` |
| `tools/chatter_db.py` | DB access, inserts, zone/cache queries, `any_real_players_online()`, stale-group cleanup, and global group/Guild session cleanup |
| `tools/chatter_links.py` | WoW link parsing and prompt-side link enrichment for player messages |
| `tools/chatter_prompts.py` | Ambient/event prompt builders; twist and spice gating (`configure_prompt_flavor()`) |
| `tools/chatter_general_length.py` | Configurable player-driven General reply length bands and adjacent-turn avoidance; no other channel length policy |
| `tools/chatter_identity.py` | Shared persistent profile creation, guarded generation, explicit regeneration and selected-speaker preparation |
| `tools/chatter_identity_jobs.py` | Bounded Guild membership discovery and profile prewarming |
| `tools/chatter_persona.py` | Bot persona resolution (identity + real event mood) and the shared persona/cast renderers for Party, Guild and General |
| `tools/chatter_threads.py` | Party conversation threads: in-memory thread store, soft nudges for idle exchanges, thread prompt rendering, thread report parsing |
| `tools/chatter_general.py` | `player_general_msg` Python path |
| `tools/chatter_memory.py` | Persistent memory system: session tracking, background memory generation via `queue_memory()`, flush/activate on farewell, orphan recovery. Key helpers: `_resolve_location()`, `_ensure_cap_and_insert()`, `_count_active_memories()`, `_evict_one_used()`. Memory prompts thread `player_name` so the LLM references the player by name (DB fallback from `player_guid` when caller doesn't supply it). Memories are one plain, factual sentence (target 160 characters); `_clamp_memory_text()` bounds them at write time (hard cap 240, cut at a sentence or word boundary), so prompts carry the stored memory whole instead of cutting it at 200 characters |
| `tools/chatter_cache.py` | Mode-aware pre-cache refill and startup removal of ready rows generated under a previous mode |
| `tools/chatter_events.py` | Event context building and cleanup |
| `tools/chatter_constants.py` | Static constants and lore data: zone names/levels/flavor, race/class speech profiles, personality traits (16 categories, 264 traits), BG lore, item/weapon/armor classification maps, item quality names/colors, raid map IDs, dungeon flavor, emote keywords |
| `tools/talent_catalog.py` | Talent description catalog used by prompt-side talent injection |
| `tools/spell_names.py` | Spell name/description loader used by DB and link helpers |
| `tools/talent_data.py` | Loader for `talent_data.json`: talent spell to tree, rank and name, used by `get_character_talents()` |
| `tools/generate_talent_data.py` | Regenerates `talent_data.json` from the client `Talent.dbc` and `TalentTab.dbc` |
| `tools/chatter_class_style.py` | `class_style()`: class name with priests split into Light and Shadow by `get_character_talents()` (active spec aware) |

### Screenshot vision domain

| File | Primary ownership |
|---|---|
| `tools/screenshot_agent.py` | Host-side capture agent (runs outside Docker). Captures WoW window via Win32 API, crops UI clutter (bottom 20%, sides 12%), sends JPEG to vision LLM (OpenAI, Anthropic, Google, or OpenRouter), receives structured JSON with environment description, atmosphere, and canonical tags. Queues `bot_group_screenshot_observation` events directly into `llm_chatter_events`. Configurable interval, chance, and vision provider/model |
| `tools/chatter_screenshot_handler.py` | Bridge handler for `bot_group_screenshot_observation` events. Generates in-character bot comments using personality traits, zone/subzone context, and the vision description. Supports single statements via `run_single_reaction()` and multi-bot conversations via `append_conversation_json_instruction()` / `parse_conversation_response()`. Canonical tag dedup prevents repetitive observations |

### Development tools

| File | Primary ownership |
|---|---|
| `tools/chatter_request_logger.py` | Thread-safe JSONL logger; `init_request_logger(config)` + `log_request(label, prompt, response, model, provider, duration_ms, system_prompt)`; rotation at `MaxSizeMB`; writes to `/logs/llm_requests.jsonl` inside container |
| `tools/chatter_log_viewer.py` | Zero-dependency stdlib web UI (`python chatter_log_viewer.py --log PATH --port 5555`); routes `/`, `/api/logs`, `/api/stats`; semantic prompt-section parser with colored sections; draggable column/row dividers |

### Emote reaction domain

| File | Primary ownership |
|---|---|
| `tools/chatter_emote_reaction.py` | Directed verbal reaction handler (`bot_group_emote_reaction` event) — bot responds verbally when player emotes at them |
| `tools/chatter_emote_observer.py` | Observer comment handler (`bot_group_emote_observer` event) — random group bot remarks when player emotes at a creature, a stranger, nobody, or another party bot (`party_bot`, optionally a two-line exchange with that bot). Both emote handlers note their delivered line in the party conversation thread |

When the player emotes at a party bot, `HandleGroupPlayerTextEmoteImpl()`
also (out of combat) calls `HandleEmoteObserver()` with the other nearby party
bots and `HandleProximityPartyBotEmoteWitness()` (LLMChatterProximity.cpp) for
nearby NPCs and non-party bots, and calls `HandleEmoteMoodSpread()` for
contagious emotes (also for undirected ones).

Free-text emotes (`/e`, `/me`) arrive through the chat hook, not
`OnPlayerTextEmote`. `HandleGroupPlayerCustomEmoteImpl()` sanitizes the text
(clamped to `EmoteReactions.CustomMaxChars` UTF-8 characters), resolves the
target from the player's selection, and feeds the same dispatcher as named
emotes with `textEmote = 0`. A custom emote has no animation, so it never
mirrors; it only produces verbal reactions. Every payload carries the typed
text in the emote-name field plus `custom_emote: 1`: `bot_group_emote_reaction`
and `bot_group_emote_observer` for grouped bots, and `proximity_player_emote`
for an ungrouped playerbot. The Python handlers quote the text as an action
instead of rendering it as a `/slash` command.

### Proximity chatter domain

| File | Primary ownership |
|---|---|
| `tools/chatter_proximity.py` | Ordinary proximity event handlers and prompt builders. Applies NPC in-world voice and configured playerbot voice independently in single or mixed-speaker scenes |
| `tools/chatter_instance_context.py` | Shared canonical map/current-area and curated dungeon-lore context used by ordinary proximity and boss prompts |
| `tools/chatter_boss_dialogue.py` | Fail-closed, history-aware message-only generation and `myell` queue insertion for boss approach and directed boss events |

### Raid/BG domain

| File | Primary ownership |
|---|---|
| `tools/chatter_raid_base.py` | Dual-worker dispatch and suppression logic |
| `tools/chatter_raids.py` | PvE raid event handlers (boss, morale) |
| `tools/chatter_raid_prompts.py` | Raid prompt builders (boss, morale, battle cry, banter) |
| `tools/chatter_battlegrounds.py` | BG event handlers |
| `tools/chatter_bg_prompts.py` | BG prompt builders (lore tables moved to `chatter_constants.py`) |
| `tools/chatter_bg_flag_timeline.py` | Per-match WSG flag event timeline (drop/return/regrab/stale-carry decisions) |

## Ownership Boundaries That Matter

### Shared C++ ownership

`LLMChatterShared.cpp` owns cross-domain helpers such as:

- `EscapeString()`
- `JsonEscape()`
- `GetZoneName()`
- `GetChatterClassName()`
- `GetRaceName()`
- `BuildBotIdentityFields()`
- `QueueChatterEvent()`
- `BuildBotStateJson()`
- `AppendRaidContext()`
- `GroupHasBots()`
- `CanSpeakInGeneralChannel()`
- `GetTextEmoteName()` — reverse emote ID-to-name lookup (170+ entries)
- `SendUnitTextEmote(Unit*, uint32, const std::string&)` — consolidated
  emote packet helper; `SendBotTextEmote` overloads delegate to it
- `IsEventOnCooldown()` / `SetEventCooldown()` — shared event cooldown
  helper (cache-first, DB fallback) used by world, ambient, and nearby
- `FindCreatureBySpawnId(Map*, uint32)` — spawn-GUID creature lookup
  used by delivery and proximity
- `GetCreatureRoleName(Creature*)` — NPC role description from subname
  or NPC flags, used by proximity and nearby
- link conversion helpers
- emote/delivery helpers

Critical contract:

- direct callers of `QueueChatterEvent()` must pass `extraData` that is
  already valid JSON text and SQL-safe for insertion into a single-
  quoted SQL string literal

That contract is enforced by convention and comments, not by the type
system.

### Delivery ownership

`LLMChatterDelivery.cpp` owns:

- `DeliverPendingMessagesImpl()`
- outbound message polling from `llm_chatter_messages`
- facing selection before speech delivery
- final chat-channel dispatch for party, raid, BG, yell, General,
  say (bot `CHAT_MSG_SAY`), and msay (NPC `CHAT_MSG_MONSTER_SAY`
  with speech bubbles)
- spawn-GUID creature lookup for NPC delivery via
  `FindCreatureBySpawnId()`
- NPC orientation reset after speech via `BasicEvent`
- delivery success/retry marking
- action delivery: with `LLMChatter.ActionAsEmote.Enable = 1` a row's
  `action` column (split from a leading `*action*` by
  `split_action_prefix()`) goes out as a `CHAT_MSG_MONSTER_EMOTE`
  (`Unit::TextEmote`, which carries the sender name) right before the speech.
  Each send site calls `emitAction()` only once the send is known to be
  valid — for party, after the group has been confirmed — so an action never
  plays ahead of speech that fails. If speech is retried after the action has
  gone out, the `action` column is cleared so the retry does not replay it.
  With the option off, the action is rendered inline as `*action* text`

### Ambient ownership

`LLMChatterAmbient.cpp` owns:

- holiday processing
- day/night processing
- weather state and transitions
- ambient zone discovery and faction selection
- ambient message-family selection
- demand-driven live inventory snapshots when the selected family is
  trade
- ambient chatter request queue writes

### Real General loot ownership

`LLMChatterLoot.cpp` owns `OnPlayerLootItem` capture for ungrouped
playerbots. The map-thread hook performs player-local checks, consults a
read-only `(map, zone) -> faction mask` audience snapshot and the in-memory
cooldown cache, rolls once per loot source, and keeps only an active source
plus one completed source per bot. It never queries the database or reads
`RandomPlayerbotMgr` state. A reservoir sample chooses one item uniformly
when a source yields multiple callbacks. Because a stacked item can already
have been freed by the callback, `Item::IsInWorld()` is checked before any
template or entry access. The world-thread flush restricts delivery to
random bots and revalidates the bot, audience, General membership, and
persisted zone cooldown before queueing `bot_loot_item`.

The main world script rebuilds the audience snapshot independently of the
General-channel toggle and publishes it through a `shared_mutex`-protected
immutable `shared_ptr`; map workers never walk the live session map or
mutate channel membership. Python handling belongs to
`tools/chatter_loot.py` and resolves only the event's `subject_guid`.
There is no persistent loot listener queue beyond the bounded aggregation
slots and no inventory cache: trade ownership is sampled only after an
ambient request has selected trade. Trade selection uses a weighted
reservoir over eligible live bag slots. Common items remain eligible while
each quality tier above common receives the configured additional weight.

### Nearby ownership

`LLMChatterNearby.cpp` owns:

- nearby-object / nearby-creature scanning
- nearby POI helper structs and scoring helpers
- nearby-local cooldown state
- direct nearby event queue insertion path

### Proximity fight onlooker ownership

`LLMChatterProximityFight.cpp` owns reactions of bots outside the
player's group to a nearby duel or overworld PvP kill. Group duel and
PvP reactions stay in `LLMChatterDuel.cpp` and `LLMChatterGroupPvP.cpp`.

- Hooks (`PLAYERHOOK_ON_DUEL_REQUEST`, `_START`, `_END`, `_ON_PVP_KILL`)
  run on map worker threads and only record state under a mutex.
  `ProcessPendingFightMoments()` runs on the world thread from the
  existing delivery poll in `WorldScript::OnUpdate` and does all scene
  work.
- `LLMChatterJsonFields.h` holds the whitespace-tolerant readers used to
  revalidate fight rows read back from the MySQL JSON column; it is
  standard-library only and has a standalone test
  (`tools/tests/cpp/test_json_fields.cpp`).
- Each duel request creates a duel instance with a unique id, keyed by
  the duellist pair; a rematch replaces it. Phases are `Challenged`,
  `InProgress`, and `Completed`. Live duels never expire by age;
  completed instances are retired after `CompletedRetentionSeconds` once
  no pending work refers to them.
- The moment set (before/during/after) is rolled once per duel, with
  repeat throttling between duels keyed by anchor and location cell.
- Each moment produces exactly one reaction: a statement or a 2-3 bot
  conversation. Same-faction onlookers speak through `proximity_say` /
  `proximity_conversation` with `fight_kind` and a `fight_scene` object;
  opposite-faction onlookers only emote, without an LLM call.
- A real-player duellist can anchor the scene through
  `IsProximityFightAnchorEligible()`, which allows combat only with the
  recorded duel opponent.
- `LLMChatterDelivery.cpp` drops fight rows outside bot proximity `say`
  (`fight_scene_channel`) and revalidates each row with
  `IsProximityFightLineStillValid()` (`fight_scene_stale`), so lines for
  a cancelled challenge, a finished duel, or a rematch are never spoken.

### Proximity ownership

`LLMChatterProximity.cpp` owns:

- periodic ordinary proximity scans around alive real players
- outdoor, dungeon, and raid map policy (BGs/arenas excluded)
- humanoid NPC eligibility, disposition, rank, LOS, and delivery policy
- bot eligibility filtering (party bots for ordinary scans, explicitly
  targeted same-team ungrouped bots for directed `/say` and emotes,
  all-bot guard rail)
- mutually compatible candidate selection and ordinary event queueing
- map/instance-scoped `ProximityScene`, history, and cooldown state
- selected/named player `/say` routing before scene fallback
- directed social-emote verbal events and synchronized per-player/NPC or
  per-player/ungrouped-bot cooldowns
- mounted real players and mounted playerbots remain eligible for directed
  `/say`, emotes, and active-scene replies; mounting still suppresses
  automatic and untargeted new-scene selection, and an untargeted `/say`
  speaker that mounts after queueing is rejected again at delivery
- policy-scoped weighted selection with one universal two-joiner cap:
  zero to two NPC joiners for NPC-directed scenes, or zero to two compatible
  NPC/ungrouped-bot joiners when an ungrouped bot is addressed
- in-memory-only ordinary cooldown filtering for mixed-scope joiners; the
  addressed `/say` target is not throttled and no per-candidate persisted
  cooldown query runs inside the hook
- strict full-name/unique-token resolution and vocative detection

`LLMChatterGroupEmote.cpp` owns animation mirroring for grouped bots,
ungrouped bots, and creatures. It also owns the mirror-map availability
check and loads the SmartAI/configured C++ scripted-emote exclusions used by
the direct creature mirror and verbal-reaction paths. Delayed bot mirrors
share one execution-time safety check: the bot must remain out of combat and
the player must remain present, on the same map, and within the configured
player-say radius (with a one-yard minimum). This applies to grouped and
ungrouped bots; grouped verbal reactions are not range-gated by this check.

`LLMChatterBossDialogue.cpp` owns the distinct hostile-boss path:

- shared-classifier and denylist eligibility
- fair round-robin extended-radius safe approach scans, capped at one
  creature-grid search per configured scan pass
- calculated aggro distance plus configurable safety margin
- automatic approach and unambiguous selected/named player `/say` events
- shared per-boss-spawn/per-instance presence scheduling with randomized,
  decaying repeat opportunities and a persistent low-probability floor
- separate per-player, per-boss-spawn, per-instance directed cooldowns
- synchronized state reservations across world and map-thread hooks

`FindCreatureBySpawnId()`, `GetCreatureRoleName()`,
`LoadNamedBossCache()`, and `IsLLMChatterBoss()` live in
`LLMChatterShared.cpp` for proximity, group-kill, boss, and delivery
callers. The cache uses AzerothCore's registered creature encounters as
its authoritative dungeon/raid source, with rank, boss flag, and
single-spawn immunity metadata retained as fallbacks for unregistered
special bosses. Kill and enter-combat reactions share this classifier, so
a registered dungeon encounter boss of elite rank counts as a boss on the
pull as well as on the kill. `OnPlayerCreatureKilledByPet` routes pet and
totem killing blows through the same kill path, credited to the owner.
On the bridge side, `GroupChatter.KillBurstWindow` silences further
non-boss kill reactions for a group for a few seconds after one is
voiced, so a boss and its rare-flagged escorts produce one kill line, not
several. Only a voiced reaction starts the window; one still being
generated blocks others, and a failed one frees its slot.
`GroupChatter.PullBurstWindow` does the same for pulls: every bot that
enters combat raises its own `bot_group_combat` event, and only the first
one in the window speaks for the group.

### World ownership

`LLMChatterWorld.cpp` owns:

- `LLMChatterWorldScript`
- `LLMChatterGameEventScript`
- `LLMChatterALEScript`
- thin delivery tick delegation
- thin ambient delegation
- thin nearby delegation
- world-private `QueueEvent()`
- transport state and route announcements via transport-object zone
  transitions, but only when the destination zone currently contains a
  real player; eligible zone bots speak in General

`QueueEvent()` SQL-escapes its `extraData` before forwarding to
`QueueChatterEvent()`.

### Group ownership (seven TUs)

`LLMChatterGroupInternal.h` declares shared state across the group TUs:

- struct definitions: `GroupJoinEntry`, `GroupJoinBatch`,
  `QuestAcceptEntry`, `QuestAcceptBatch`
- extern declarations for all shared cooldown maps, batch containers,
  mutexes, and emote cooldowns
- `EmoteTargetType` enum
- shared helper and domain entry-point declarations

`LLMChatterGroup.cpp` retains:

- shared state variable definitions (all cooldown maps, batch containers,
  mutexes, and emote cooldowns)
- shared helpers: `GroupHasRealPlayer`, `GetRandomBotInGroup`,
  `CountBotsInGroup`, `IsLikelyPlayerbotControlCommand`, pre-cache
  helpers
- MultiBot-Chatless bridge coexistence. `mod-multibot-bridge` owns the
  `MBOT` protocol by default. The `LLMChatter.MultiBotCompat.Enable`
  fallback is disabled by default, so chatter does not consume or block
  the addon's hidden communication. When enabled, it answers only
  startup packets (`HELLO`, `PING`, `GET~ROSTER`, `GET~STATE(S)`,
  `GET~DETAIL(S)`) for installs without the bridge
- `LoadNamedBossCache()`
- `CleanupGroupSession()` coordinator
 - thin `LLMChatterGroupPlayerScript` wrappers
 - `AddLLMChatterGroupScripts()` registration

`LLMChatterGroupCombat.cpp` owns:

- the remaining `LLMChatterGroupPlayerScript` implementation bodies for
  kill, death, loot, combat, chat, level, quest objectives, quest
  complete, achievement, spell, resurrect, corpse run, dungeon entry,
  and emote dispatch
- text-emote target classification and the decision of which paths still
  require group/bot context
- direct acceptance for ungrouped playerbot targets and external-player
  observer fallback when no direct route applies
- `HandleGroupPlayerUpdateZone()`
- `CheckGroupCombatState()`
- file-local `QueueStateCallout()`

`LLMChatterGroupJoin.cpp` owns:

- `QueueBotGreetingEvent()`
- `EnsureGroupJoinQueued()`
- `FlushGroupJoinBatches()`
- `LLMChatterGroupScript` (GroupScript: `OnAddMember`, `OnRemoveMember`
  with farewell, `OnDisband`)

`LLMChatterGroupEmote.cpp` owns:

- `DelayedMirrorEmoteEvent`, `DelayedCreatureMirrorEmoteEvent`
- emote static data: `s_mirrorEmoteMap`, `s_ignoredEmotes`,
  `s_combatCalloutEmotes`, `s_contagiousEmotes`
- `HandleEmoteAtGroupBot()`, `HandleEmoteAtCreature()`,
  `HandleEmoteObserver()`
- `EvictEmoteCooldowns()`

Ownership boundary:

- `LLMChatterGroupCombat.cpp` decides who/what the text emote targeted
  and whether the follow-up path is group-gated
- `LLMChatterGroupEmote.cpp` owns the actual mirror execution,
  cooldowns, and observer event queueing
- creature mirror emotes can fire even when the player is solo;
  observer chatter still requires eligible grouped bots
- emote cooldown maps are mutex-protected because text-emote hooks can run
  concurrently on map worker threads

`LLMChatterGroupQuest.cpp` owns:

- `FlushQuestAcceptBatches()`
- `LLMChatterCreatureScript` (AllCreatureScript:
  `CanCreatureQuestAccept` with debounce/immediate paths)

Important: the creature quest-accept hook is group-owned, not in a
separate creature file.

`LLMChatterGroupPvP.cpp` owns overworld PvP against the opposing
faction. An enemy may be a real player or a playerbot; both are
`Player` objects and share every path. Battlegrounds and arenas stay
with `LLMChatterBG.cpp`.

- `ResolveOpposingFactionPlayer()` maps a unit (the player or its pet)
  to the opposing-faction player and excludes same-team players, duel
  opponents, and battleground/arena participants
- `IsPvPEnemyPerceivable()` is the single identity gate. It delegates to
  the shared `IsUnitPerceivableBy()`: same map and instance, within
  visibility range, and distance-aware `CanSeeOrDetect()`. The same
  helper gates `bot_state.target` in `BuildBotStateJson()`. Enemy
  identity reaches extra data, and the legacy `creature_name`,
  `killer_name`, and `target_name` fields, only after this gate. A pet
  and its owner are gated separately
- `SelectPvPReactor()` limits reactors to bots on the enemy's map and
  prefers bots that can perceive it
- `BuildPvPEnemyFields()` adds `enemy_kind: "player"` and, when
  perceivable, the enemy's name, race, class, gender, level, faction,
  `enemy_is_bot`, `level_gap`, and `is_gray_kill`; otherwise
  `enemy_identity_known: false`
- PvP reuses the existing `bot_group_combat`, `bot_group_kill`,
  `bot_group_death`, `bot_group_wipe`, `bot_group_spell_cast`, and state
  callout event types. PvP events never use the creature-oriented
  pre-cache, and the tank aggro-loss callout carries
  `callout_kind: "pvp_target_switch"`
- `LLMChatterGroupCombat.cpp` hands opposing-faction enemies to this
  file from the pull, creature-death (pet owner), spell, and state
  callout paths, and owns the shared `QueueGroupDeathOrWipe()` used by
  both creature and PvP deaths

`LLMChatterDuel.cpp` owns duel reactions. It queues
`bot_group_duel_start` and `bot_group_duel_end` for each distinct group
with a real player that contains a duellist. The reactor is a bot
duellist or a group bot that can see the duel.

### Player ownership

`LLMChatterPlayer.cpp` owns:

- `LLMChatterPlayerScript`
- `EnsureBotInGeneralChannel()`
- `_generalChatCooldowns`
- `_subzoneCommentCooldowns` — per-group cooldown keyed by group
  counter (not per-area), shared with `ZoneTransitionCooldown` config
- `OnPlayerCanUseChat(..., Channel*)`
- General-channel bot history storage

### BG ownership

`LLMChatterBG.cpp` owns battleground-specific hooks and BG queue
helpers. `LLMChatterAB.cpp/.h` owns AB observation, classification,
pending node changes, revisions, match-target caching and value snapshots.
`LLMChatterABPending.h` owns the value-only bounded pending policy. The BG
coordinator invokes AB batch evaluation on the speech polling cadence;
legacy WSG/EY routing and chance/cooldown behavior remain in the coordinator.

Map-specific polling, score detection and prompt context use
`GetBgTypeID(true)`, including matches entered through Random Battleground.
The payload's `bg_type_id` identifies the actual battleground; the separate
`queue_type_id` preserves `GetBgTypeID()` for queue provenance. Both common
context and arrival batches use this contract. Python lore lookups must use
the actual type, not the queue type.

AB observes all five nodes on each in-progress BG update before the speech
polling gate. Per-node initialized state and one pending window are
separate; chance/cooldown failure retains pending speech without
freezing observation. The pending window retains its first previous state
and latest result; more than one observed change degrades its label.
First/invalid baselines, disabled chatter and non-progress match states
clear or seed silently; destruction removes the tracker. Pre-start/end
snapshots remain available without generating node reactions. EY retains
its separate `lastNodeState` polling behavior.

AB node events add `prev_state`, `state`, `transition`, `evidence` and
`observation_gap_ms` (largest actual monotonic sample gap in the pending
window). States use the core values: 0 neutral, 1/2 Alliance/Horde occupied,
3/4 Alliance/Horde contested. Contested `new_owner` means claimant, not
occupied owner. Recognized pairs are claim (neutral to contested), assault
(opposing occupied to contested), counter_claim (opposing contested,
never occupied), defence (opposing contested to occupied, previously
captured) and capture (same-team contested to occupied). `_captured` is
checked in the producer; unknown pairs use `state_update`.

The source invariant is narrower than a world-tick claim: map updates run
before the BG manager, but `Battleground::Update` gates to 1000ms and
advances AB timers by exactly 1000ms per pass. Observation follows
`PostUpdateImpl`. Several banner actions can alternate between samples,
but a reset 60-second capture timer cannot expire in that one BG pass.
Recognized pairs therefore support net team transitions, not an exhaustive
action history or actor attribution. Ordinary spell cast time is not used
as a timing bound. This relies on the current core ordering and timer
semantics and must be rechecked if they change.

One changed pair within `AB.TransitionMaxGapMs` uses `evidence=sampled`.
Zero disables these labels. Long actual gaps, multiple pending changes or
unknown pairs use `transition=state_update`, `evidence=ambiguous`. First
baselines emit nothing. `chatter_bg_prompts.py` validates recognized
pair/label shapes and renders team-relative observations. Legacy/ambiguous
payloads render current state only; malformed explicit state becomes
unknown. Legacy `claimer_name` is ignored for AB, including old Random
rows identifiable by AB node name. These events use Party with an AB-only
attempt budget, independent of the shared big-event cooldown.

#### AB node batches

At most one latest revision per node is pending. Each retains its first
pending time, latest change time and baseline. An unsent return to baseline
cancels an obsolete alarm. A revision already submitted to any audience
cannot be cancelled that way because its older message may become visible;
the reversal becomes a newer fact. Expiry is measured from the latest
change. Disable, status changes and destruction reset pending work.

At each eligible polling opportunity, select oldest-pending-first with
rotating ties, capped by `AB.MaxNodesPerBatch`. Spend
`AB.NodeBatchCooldownSec` even when the one `NodeEventChance` roll fails.
No listeners or failed insertion retains the pending facts until expiry.
Score/start cooldowns cannot consume this AB attempt budget.

Eligible node listeners are deduplicated by BG team and group and
must have a bot in the same BG raid. The first insertion attempt
freezes that revision's eligible audience set. A new human in an existing
group may hear a retry; a newly eligible group waits for new changes,
rather than replaying older announcements. This bounds receipts to one
live audience snapshot per each of five pending nodes. Successful audiences
are skipped on retry; mixed failures retain only their outstanding receipts.

One existing `bg_node_captured` event transports bounded `node_changes`
and the current full snapshot. Each item has its own transition label;
the transport category does not assert a capture for every item. The
prompt renders only the referenced nodes as one reaction. Legacy single
node payloads remain supported. The final guard checks every referenced
live node/revision and rejects duplicate, empty or oversized batches;
unrelated node changes do not invalidate a batch.

Insertion uses existing `AppendChatterEvent` in one async transaction per
audience. World-thread callbacks acknowledge only matching revisions on
successful commit. Pending selection pauses while any transaction remains
unacknowledged, so a slow DB cannot create duplicate insertion retries.
Callbacks belong to the tracker; resetting it discards them, while old
committed rows remain subject to match/status/token/age delivery checks.
Insertion acknowledgement is not speech delivery. Once an audience's row
is committed, later generation or delivery suppression is not retried.

#### AB resource race and objective status

`LLMChatterABScore.h` owns the value-only threshold, score-pending and
status-clock policy. The AB owner observes scores every BG update, before
speech polling or chance. Thresholds come from the verified match target:
configured percentages are rounded up, deduplicated and restricted to
positive values below target. The core warning is included only below
target and wins a collision with a percentage. Invalid percentage lists
use 30,60,90; reload, late enable and delayed target discovery seed current
scores silently instead of replaying history.

High-water scores record reached thresholds independently of speech.
Only the newest crossing remains pending across both teams; when several
cross in one observation the highest threshold wins. Pending score facts
expire using `AB.PendingMaxAgeSec`. `AB.ScoreCooldownSec` budgets attempts,
including chance failures, independently of node batches. All eligible
team/group/subgroup milestone rows are appended to one atomic transaction;
failure retains the pending revision and successful acknowledgement clears
only that exact revision. Outstanding score and node callbacks do not gate
each other's selection. Match-end/status/disable reset score work.

AB score events include the full snapshot and are validated like other
objective summaries. `chatter_ab.py` renders observed lead/trail, nonlinear
income, contested/occupied bases and resources remaining against the
verified target. The AB score prompt identifies percentage versus core
warning thresholds, prohibits guaranteed winners and exact finish estimates,
and does not use EY's fixed 1500-based urgency. EY retains its old behavior.

At an existing idle opportunity, `TryABObjectiveStatus` may select a
`bg_idle_chatter` row with `ab_objective_status=true`. It replaces the
ordinary choice for that audience; it never adds a second row. Status
chance failure spends the status interval but leaves ordinary idle chance
available. A zero status interval disables the specialization. Pending,
in-flight or recent node batches suppress status attempts, using the node
cooldown as the recent window. Existing idle audience/speaker selection,
Party filler gating and full-vector final validation remain in force.

#### AB snapshot publication and consumption

`ObserveABContext` runs on the world thread before arrival processing and
speech polling, including pre-start updates. It publishes a complete,
serialized value snapshot; partial/invalid node sets are not published.
`AppendABContext(instanceId, json)` copies that value under a short mutex.
Player/map hooks never access the mutable AB tracker or traverse AB nodes;
the lock is released before formatting/DB operations. Destruction and
feature disable clear both tracker and published value. Status changes
seed a new observation baseline and clear pending reactions/estimates.

Only objective producers attach the published snapshot; common
`AppendBGContext`, arrival batches and player replies carry the shared
match envelope without base facts. `ab_state` includes five nodes (`id`, `name`,
`state`, nullable `owner`/`claimant`, `captured`, `revision`), occupied counts,
core tick points/intervals, `max_score`, `max_score_verified` and
`warning_score`. Revisions advance on observed state/captured changes and
baseline initialization. They do not detect invisible change-and-return
sequences; lifecycle tokens and final-send validation are separate work.

The target is read from `BattlegroundAB::FillInitialWorldStates` on the
first valid read and cached for that match. Invalid/missing positive target
values keep the marked core fallback and retry next update. Config reload
cannot replace the match's actual target with the current world setting.
This constructs no sent packet and calls neither `Write()` nor a private API.

Optional `contest_estimate` values are internal bounds in `bg_update_time`,
not wall-clock countdowns. The lower remaining bound accounts for the BG
advance on the observed transition and subsequent BG advances. The upper
bound remains the full capture duration because an unseen same-state
re-claim can reset the timer. Omit intervals containing expiry or wider than
`AB.TimerEstimateMaxUncertaintySec`. Unknown baselines, ambiguous changes,
large observation gaps, status/enable resets and occupied/neutral states
have no estimate. These conservative bounds usually become unusable within
a few updates. **No numerical timer wording is rendered.**

`tools/chatter_ab.py` validates the bounded snapshot and renders factual
base-control/income/verified-target context for idle/objective-status
chatter. `QueueBGEvent` attaches `ab_state` only for `bg_node_captured`,
`bg_node_contested`, `bg_idle_chatter` and `bg_score_milestone`;
objective-status chatter uses the idle event with an `ab_objective_status`
marker. The AB owner attaches the same published snapshot on its async
node/score insertion paths. Node prompts
expose only their referenced objective, not the full snapshot.
Common BG context and arrival producers do not attach base snapshots.
Arrival, combat/state callouts and player replies (single, conversation,
and second speaker) never render them, even from legacy payloads. The
Python transport boundary strips incidental `ab_state` without changing
match identity, observation time or the original stored event.
Invalid snapshots are omitted; invalid target metadata only omits the
target. The renderer ignores all estimate numbers and does not forecast a
winner. WSG/EY prompts ignore the AB field.

#### Battleground final-delivery contract

`LLMChatterBGDelivery.cpp/.h` owns transient match identities, explicit
real-player recipients and the shared BG final-send guard. Lifecycle hooks
create a process-unique token and erase it on destruction or disabled
observation. An AB-enable change rotates the token on the next observation.
Producers add `bg_match_token`, monotonic `bg_observed_ms`,
`bg_recipient_guid` and `bg_map_id` to the existing actual type, instance,
team, group, subgroup and roster context. Bot-subject events use the same
eligible real listener for both the envelope and raid projection.
`chatter_bg_delivery.py` normalizes `raid_group_id` into `group_id`;
conflicting nonzero IDs are invalid. It never refreshes snapshots or times.

Every message retains its originating `event_id`. Delivery reads the
original event JSON through that link, including arrival and group replies.
Before facing, action text, emote-only output or speech, the guard checks
the token, age, actual map instance, both participants' BG teams, group and
channel. Party also requires both participants in the recorded subgroup.
Normal events require in-progress, arrival/start permit pre-start, and
match-end requires WAIT_LEAVE. Failure finalizes the row with a `bg_*`
drop reason rather than retrying or retargeting it.

The age budget is chosen by content, not by map: match-end rows use
`MatchEndMaxAgeSec`; AB rows carrying `ab_state` (node, idle/objective
status, score) use `AB.FactualMaxAgeSec`; every other BG row, including
incidental AB replies and callouts, uses `FactualMaxAgeSec`.

AB snapshots include monotonic `observed_at_ms`. The AB owner validates all
five live node states and captured bits, observed revisions, occupied
counts, income and verified target against the original snapshot. Full
snapshot consumers (idle/objective status and score milestones) check all five nodes because
their prompts expose the complete vector. Node-event prompts omit that
vector and expose only their referenced objective; `node_id` and
`node_revision` bind its state to the live node. Unrelated node changes
therefore do not suppress a node reaction. Score
increments alone do not invalidate a line; supplied scores are labeled as
observed snapshots. Observation and validation run on the world thread;
other producers only copy published values under short mutexes. Changes
that return to the same state entirely between observations remain a
sampling limitation. Numerical timer speech remains disabled.

#### AB banner actor attribution

Node changes name a player only from verified banner interactions.
`LLMChatterABActorPlayerScript::OnPlayerSpellCast` (capture-banner spell
21651, AB only) snapshots the target banner's node state into a small
`thread_local` ring keyed by the casting `Spell`, before `CheckCast(false)`.
`LLMChatterABActorSpellScript::OnSpellCast` runs after `handle_immediate()`,
where the open-lock effect has already called
`BattlegroundAB::EventPlayerClickedOnFlag`, and re-reads the node. Only a
change matching this caster's click (`ClickTransition`: claim, assault,
counter-claim, defence) becomes a record. Rejected casts never reach the
post hook, and spells in one map update run sequentially, so the change
belongs to this caster. Cancelled casts clear their slot, and a reused
`Spell` pointer replaces its old slot.

Records are written on BG map threads into a per-instance, per-node
summary under `_abActorMutex`: a click count plus the first record, so
saturation can only become ambiguous. The world-thread observer swaps the
summary out once per observation and calls `ResolveActor`
(`LLMChatterABActor.h`): exactly one verified click whose kind and team
match the observed transition names the actor. Zero clicks, two or more
clicks (including a same-state change-and-return), an observation gap, or
a mismatch name nobody. A verified claim, assault or counter-claim is
carried until its own timed capture (`actor_role: flag_held`). A quiet
unchanged observation keeps the carry; any other transition, gap or
ambiguity clears it. Payload fields `actor_name`, `actor_is_real_player`
and `actor_role` appear only on attributed node changes. Node prompts drop
the `real_players` roster, so the model cannot guess a name from it.

Incidental rows contain no base snapshot and retain match/audience/age
checks without node dependencies. An old incidental row still containing
`ab_state` is rejected as `bg_ab_context_unexpected`: its already-generated
prose may mention old facts, so changing the renderer alone cannot make
that queued prose safe. Drain or discard those rows at rollout.

Old queued BG rows without the envelope fail closed, including WSG/EY
rows. Ordinary Party, Raid and Guild rows without BG context bypass this
guard even when their event map is a BG map. See
the deployment notes in the module documentation for coordinated rollout.

#### AB verification boundaries

The standalone C++ harnesses `test_ab_pending.cpp`, `test_ab_score.cpp`
and `test_ab_integration.cpp` include the production policy headers.
The combined harness covers independent attempt budgets, simultaneous
pending node/score work, out-of-order acknowledgements, replacement
revisions, changed audience cohorts, expiry and lifecycle reseeding.
It does not instantiate a battleground or execute transaction callbacks.
Compile and execute these harnesses only as part of an explicitly
authorized validation build, with assertions enabled.

`test_arathi_integration.py` executes the actual AB handlers, BG-wide node
and subgroup score/idle dispatch, prompt construction and single-reaction
parsing through mocked
LLM and DB boundaries. A blocked generation overlaps a newer match event
and verifies that each inserted message retains its own event/group link.
Insertion is not proof of delivery: the C++ guard must still reject the
old match, changed subgroup or expired observation at send time.
The existing delivery source checks are structural checks, not executed
tests of game objects, observation clocks or final-send decisions.

Live validation must exercise stalled observation versus advancing wall
time, node changes after generation, subgroup moves, exit/requeue and
disable/re-enable. Inspect both visible output and finalized drop reasons;
queued or completed events alone do not establish audibility.

### Transport detection shape

The current transport path is intentionally an early-warning system, not
an exact dock-stop detector:

1. `LLMChatterWorld.cpp` polls live transport objects.
2. It tracks last-seen zone/map per live transport GUID.
3. A dispatch is considered only when a transport actually enters a new
   zone or map.
4. The new zone must currently contain at least one real player.
5. Eligible General-channel bot GUIDs in that zone are written into
   `extra_data.verified_bots`.
6. Cooldown is keyed by transport entry, not `transport + zone`, so one
   transport does not redispatch repeatedly during the same route cycle.

This is why transport chatter is both early enough to warn players and
cheap enough to avoid world-wide noise.

## World-To-Group Cross-Boundary

The world layer intentionally calls only a small group-owned surface via
`LLMChatterGroup.h`:

- `LoadNamedBossCache()`
- `CheckGroupCombatState()`
- `FlushQuestAcceptBatches()`
- `FlushGroupJoinBatches()`

Player-zone updates also cross from player to group via:

- `HandleGroupPlayerUpdateZone(Player*, uint32)`

Player updates also maintain live bot travel state for party prompts.
`LLMChatterPlayer.cpp` periodically calls
`UpdateGroupBotTravelState()` for grouped bots, and forced refreshes run
on zone/area changes. The persisted state is written to
`llm_group_bot_traits` (`travel_mode`, `travel_context`, mounted/flying
flags, mount display id, transport name). C++ event payloads also embed
the same state under `bot_state.travel_state` via
`BuildBotStateJson()`.

The world layer also delegates to the proximity subsystem via
`LLMChatterProximity.h`:

- `CheckProximityChatter(bool instanceMaps)` — scoped periodic scan

And `LLMChatterGroupCombat.cpp` calls into proximity via:

- `HandleProximityPlayerSay(Player*, const std::string&)` — player
  `/say` reply detection

That explicit boundary keeps the two domains easy to reason about.

## Event Routing Ownership

Bridge routing is registry-driven.

`tools/chatter_event_registry.py` is the Python-side source of truth for
live event routing metadata. At bridge startup,
`build_handler_map()` dynamically imports handler functions from that
registry and `llm_chatter_bridge.py` uses the resulting map at runtime.

- `bot_group_*` events route to group handlers
- `bot_group_emote_reaction` routes to `chatter_emote_reaction.py`
- `bot_group_emote_observer` routes to `chatter_emote_observer.py`
- `bot_group_screenshot_observation` routes to
  `chatter_screenshot_handler.py`
- `bot_group_general_reaction` routes to
  `chatter_group_general_reaction.py`
- ordinary `proximity_*` events route to `chatter_proximity.py`
- `proximity_boss_approach` and `proximity_boss_player_say` route to
  `chatter_boss_dialogue.py`
- `bg_*` events route to battleground handlers
- `player_general_msg` routes through the adapter path to
  `chatter_general.py`
- unmapped ambient work still flows through the ambient path

Signature trap that still matters:

- group handlers use `(db, client, config, event)`
- `process_general_player_msg_event` uses
  `(event, db, client, config)`
- `_dispatch_player_general_msg` exists to reorder arguments

Do not remove that adapter without standardizing the signatures.

### Player message conversation path

When a player speaks in party chat, the group player-message handler
may trigger a multi-bot conversation instead of a single-bot reply:

Known playerbot control commands do not enter this path in current
source:

- C++ `IsLikelyPlayerbotControlCommand()` in `LLMChatterGroup.cpp`
  blocks them before `bot_group_player_msg` is queued, including known
  commands following a valid Playerbot `@target` selector and
  `@command` shorthand
- Python `_is_playerbot_command()` in `chatter_group.py` remains as a
  fallback skip layer
- ordinary `@BotName` conversation and non-command text after a simple
  selector remain eligible for Chatter; valid aura and aggro selectors
  are always treated as unconditional Playerbot control traffic

1. `find_addressed_bot()` in `chatter_shared.py` always fires an LLM
   call to assess `multi_addressed` (boolean). When true and >=2 bots
   are available, the conversation path is forced (bypasses RNG).
2. Otherwise, `PlayerMsgConversationChance` (default 30%, scaled by
   bot count) gates whether a conversation fires.
3. `build_player_msg_conversation_prompt()` in
   `chatter_group_prompts.py` builds a prompt requesting a JSON array
   of 2-3 bot replies (Architecture B — single LLM call).
4. `execute_player_msg_conversation()` in `chatter_group_handlers.py`
   dispatches the call and inserts the resulting messages.
5. Delays use `calculate_dynamic_delay(responsive=True)` for faster
   player-directed timing (2s floor vs 4s ambient).

## Where To Edit What

| If you need to change... | Primary file |
|---|---|
| LLM request log format / rotation / config | `tools/chatter_request_logger.py` |
| LLM request log web viewer | `tools/chatter_log_viewer.py` |
| Main polling loops, event claim logic, worker behavior | `tools/llm_chatter_bridge.py` |
| Python event registry / handler resolution metadata | `tools/chatter_event_registry.py` |
| Ambient statement/conversation runtime logic | `tools/chatter_ambient.py` |
| Real General loot event handling | `tools/chatter_loot.py` |
| Group join/player-msg/idle behavior | `tools/chatter_group.py` |
| Group reaction runtime behavior | `tools/chatter_group_handlers.py` |
| Shared group-handler pipeline behavior | `tools/chatter_handler_pipeline.py` |
| Group prompt wording | `tools/chatter_group_prompts.py` |
| Bot persona resolution, mood lookup, persona prompt wording | `tools/chatter_persona.py` |
| Conversation continuity, subject changes, lingering feelings in party idle chatter | `tools/chatter_threads.py` |
| Twist/spice frequency and wording | `tools/chatter_prompts.py` |
| Group message insert behavior / preserve `emote: null` | `tools/chatter_group.py`, `tools/chatter_shared.py`, `tools/chatter_cache.py` |
| General-channel Python behavior | `tools/chatter_general.py` |
| General-to-party relay behavior | `tools/chatter_group_general_reaction.py` |
| DB inserts, history tables, zone/query cache behavior | `tools/chatter_db.py` |
| Shared parsing/sanitization | `tools/chatter_text.py` |
| Provider/model calls | `tools/chatter_llm.py` |
| Shared compatibility helpers | `tools/chatter_shared.py` |
| Python event-to-handler ownership map | `tools/chatter_event_registry.py` |
| Emote reaction verbal responses | `tools/chatter_emote_reaction.py` |
| Emote observer comments | `tools/chatter_emote_observer.py` |
| Proximity chatter Python handlers/prompts | `tools/chatter_proximity.py` |
| Proximity chatter C++ scan/scene logic | `src/LLMChatterProximity.cpp`, `src/LLMChatterProximity.h` |
| Duel/PvP onlooker reactions | `src/LLMChatterProximityFight.cpp`, `src/LLMChatterProximityFight.h`; fight topic in `tools/chatter_proximity.py` (`_fight_topic`) |
| C++ text-emote target classification / solo-vs-group pathing | `src/LLMChatterGroupCombat.cpp` |
| Emote C++ hooks, mirror maps, cooldowns | `src/LLMChatterGroupEmote.cpp` |
| BG event handling | `tools/chatter_battlegrounds.py` |
| BG prompt wording/lore | `tools/chatter_bg_prompts.py` |
| Raid event handling | `tools/chatter_raids.py` |
| Raid prompt wording | `tools/chatter_raid_prompts.py` |
| C++ raid boss hooks | `src/LLMChatterRaid.cpp` |
| C++ shared helper contracts | `src/LLMChatterShared.cpp`, `src/LLMChatterShared.h` |
| C++ delivery logic | `src/LLMChatterDelivery.cpp`, `src/LLMChatterDelivery.h` |
| C++ ambient world/event logic | `src/LLMChatterAmbient.cpp`, `src/LLMChatterAmbient.h` |
| C++ real General loot capture | `src/LLMChatterLoot.cpp`, `src/LLMChatterLoot.h` |
| C++ ambient trade inventory snapshots | `src/LLMChatterTrade.cpp`, `src/LLMChatterTrade.h` |
| C++ nearby scan logic | `src/LLMChatterNearby.cpp`, `src/LLMChatterNearby.h` |
| C++ world transport/dispatcher logic | `src/LLMChatterWorld.cpp` |
| C++ group batching/combat/state logic | `src/LLMChatterGroup.cpp`, `src/LLMChatterGroupCombat.cpp`, `src/LLMChatterGroupJoin.cpp`, `src/LLMChatterGroupEmote.cpp`, `src/LLMChatterGroupQuest.cpp`, `src/LLMChatterGroup.h`, `src/LLMChatterGroupInternal.h` |
| MultiBot-Chatless `MBOT` bridge coexistence and fallback | `src/LLMChatterGroup.cpp`; debug skip wording in `src/LLMChatterGroupCombat.cpp` |
| C++ General-channel player logic | `src/LLMChatterPlayer.cpp` |
| C++ BG logic | `src/LLMChatterBG.cpp`, `src/LLMChatterBG.h` |
| Screenshot vision capture agent (host-side) | `tools/screenshot_agent.py` |
| Screenshot vision bridge handler | `tools/chatter_screenshot_handler.py` |
| C++ registration wiring | `src/LLMChatterScript.cpp`, `src/llm_chatter_loader.cpp` |

## Common Pitfalls

### `chatter_shared.py` is partly a facade

Many helpers imported from `chatter_shared.py` are actually implemented
in:

- `chatter_text.py`
- `chatter_llm.py`
- `chatter_db.py`

Do not treat `chatter_shared.py` as the default place for new Python
features just because it is imported widely. New domain logic should
usually go in the owning domain file and only small cross-domain helpers
should live here.

### Bridge ambient wrappers are delegates

If ambient behavior changes, edit `chatter_ambient.py`, not the bridge
wrapper first.

### General chat handler signature is different

Keep `_dispatch_player_general_msg` unless you standardize signatures
everywhere.

### Pre-cache path is separate from live event path

Pre-cache generation does not use the same runtime path as live group
event reactions.

### `enabledHooks` still matters

Any new C++ hook override must add the correct enum to its constructor's
`enabledHooks` vector or it will silently never fire.

### `LLMChatterScript.cpp` is registration-only

- world transport/dispatcher logic lives in `LLMChatterWorld.cpp`
- ambient world/event logic lives in `LLMChatterAmbient.cpp`
- nearby scan logic lives in `LLMChatterNearby.cpp`
- group logic lives in `LLMChatterGroup.cpp`,
  `LLMChatterGroupCombat.cpp`, `LLMChatterGroupJoin.cpp`,
  `LLMChatterGroupEmote.cpp`, `LLMChatterGroupQuest.cpp`
- player General-channel logic lives in `LLMChatterPlayer.cpp`
- shared helpers live in `LLMChatterShared.cpp`

Do not edit `LLMChatterScript.cpp` for new features.

### Battleground routing

BG-wide only:
- match start / end
- all flag events
- all AB node transitions, including state-only updates

Subgroup/party only:
- kills, EY node chatter, score milestones, spell/state chatter,
  idle chatter, flag-carrier self-messages

This reduces duplicate near-identical lines across party and raid.

Party chat in a BG raid only reaches the speaker's sub-group, so
party-channel BG chatter is scoped to bots in the real player's
sub-group (`GetRandomBotInGroup()`, `AppendRaidContext()`, and the
Python `fire_subgroup_worker(speaker_guid=...)` guard). BG arrival
batches only list bots in the player's sub-group. Their Python handler
selects explicit `(bot, channel)` entries: one BG-wide greeting plus a
configurable second-greeting roll, independently of the Party count.
Each channel samples without replacement; a bot may appear in both.
Generation failures do not reassign later greetings to another channel.

## Database Tables

| Table | Producer | Consumer | Notes |
|---|---|---|---|
| `llm_chatter_events` | C++ / screenshot agent | Python | Event queue, including value-only real-loot payloads |
| `llm_chatter_queue` | C++ | Python | Ambient statement/conversation queue; C++-selected type and optional trade item snapshot |
| `llm_chatter_messages` | Python | C++ | Outbound message delivery queue |
| `llm_group_cached_responses` | Python | C++ | Instant reaction pre-cache |
| `llm_group_bot_traits` | Python + C++ travel refresh | Python | Group traits/state, location, and live travel context |
| `llm_group_chat_history` | Python | Python | Group anti-repetition history |
| `llm_general_chat_history` | C++/Python read path | Python/C++ | General-channel history |

## Known Gaps

- exhaustive in-game validation of every event path and tuning edge case
- hostile multi-target spell-attribution edge case not yet fully covered
- boss pull/kill/wipe events need live in-game testing via actual boss
  encounters
