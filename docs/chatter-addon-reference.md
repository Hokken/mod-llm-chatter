# Chatter Addon — Reference for Code Review

## Purpose

Chatter is a WoW 3.3.5a client-side addon that provides a UI for managing
**bot personality profiles** used by the `mod-llm-chatter` server module.

Players can:
- View bots they have met in-world (the Known Bots roster)
- Read and edit the three personality traits assigned to each bot
- View LLM-generated tone and background story for each bot
- Trigger background story regeneration on demand
- Forget a bot (wipe their shared memories, preserving global identity)

The addon does **not** contain any AI logic. It is a thin UI bridge that
sends `.llmc` dot-commands to the worldserver via SAY chat and listens for
structured responses prefixed with `CHATTER_ADDON `.

---

## Architecture

### Communication Channel

Commands flow in one direction: **addon → server** via
`SendChatMessage(".llmc <command>", "SAY")`.

Responses flow back as `CHAT_MSG_SYSTEM` messages prefixed with
`"CHATTER_ADDON "`. A `ChatFrame_AddMessageEventFilter` intercepts these
before they reach the chat frame, routes them to `HandleSystemMessage`, and
suppresses display. Players never see these messages in chat.

### Server-Side Handler

All commands are handled in `LLMChatterCommand.cpp`. The C++ module:
- Validates commands and bot ownership
- Reads/writes `llm_bot_identities` and `llm_group_bot_traits` in MySQL
- Queues async Python events for LLM generation tasks
- Sends structured `CHATTER_ADDON <COMMAND> <payload>` responses via
  `SendChatMessage` back to the player

### Python Bridge

LLM generation (tone, backstory) runs asynchronously in the Python bridge
(`chatter_group_state.py`). The C++ layer queues events; Python picks them
up, calls the LLM, writes results to MySQL. The addon polls for results.

---

## Command Protocol

| Addon sends | Server responds |
|---|---|
| `.llmc roster` | `ROSTER_BEGIN`, `ROSTER <guid> <name>` × N, `ROSTER_END` |
| `.llmc get <guid>` | `PROFILE <guid> <name> <t1> <t2> <t3> <tone>` then `BACKSTORY <guid> <encoded>` |
| `.llmc set <guid> <t1> <t2> <t3>` — traits **changed** | `UPDATED <guid> <name> changed`, then `PROFILE` with empty tone (regen queued); **no BACKSTORY** |
| `.llmc set <guid> <t1> <t2> <t3>` — traits **unchanged** | `UPDATED <guid> <name> unchanged`, then `PROFILE` with existing tone, then `BACKSTORY` |
| `.llmc regenbackstory <guid>` | `BACKSTORY_REGEN <guid> <name>` (immediate ack); result arrives later via `get` polling |
| `.llmc forget <guid>` | `FORGOTTEN <guid> <name>` |

All string fields are percent-encoded. `-` is the sentinel for an empty
string. The addon uses `Encode()`/`Decode()` for all string values crossing
this boundary.

---

## Data Model

### Known Bots Roster (`llm_bot_memories`)
A bot appears in the roster if at least one memory row exists for this
player + bot pair. The C++ `roster` command queries this table. Forgetting a
bot deletes all memory rows for that player/bot pair, removing them from the
roster.

### Bot Identity (`llm_bot_identities`)
Global persistent record keyed on `bot_guid`. Stores:
- `trait1`, `trait2`, `trait3` — personality adjectives
- `tone` — short LLM-generated style description (e.g. "wry and guarded,
  with quiet curiosity")
- `backstory` — 3-4 sentence LLM-generated character history
- `farewell_msg`, `identity_version`

Forgetting a bot does **not** touch this table. The global identity
persists; only the per-player memories are erased.

### Session Traits (`llm_group_bot_traits`)
Per-group shadow of identity data, used during active group sessions.
Cleared/synced when traits change.

---

## UI Layout

There are two panels with identical content and behavior:

### Panel A — Floating Window (`/chatter` or `/llmc`)
A 480×620 draggable frame that appears in the game world. Position is
persisted across sessions via `ChatterDB`.

### Panel B — Interface Options Panel
Registered under Interface → Addons → Chatter → Bot Traits. Embedded in
the standard WoW options UI. Useful when the floating window would block
gameplay.

Both panels share all state via the `Chatter` singleton — selecting a bot
in one panel immediately reflects in the other.

### Layout (top to bottom, both panels)

```
Title: "Bot Traits"
Subtitle: "Edit persistent bot traits and view generated tone"

[Known bots ▼ dropdown (260px)]  [Refresh]  [Forget]

Trait 1: [single-line edit box, 64 char max]
Trait 2: [single-line edit box, 64 char max]
Trait 3: [single-line edit box, 64 char max]

Tone (generated): [read-only single-line box]

Background Story: [read-only multi-line box, 130px tall, scrollable]
[Regenerate Story]

[status line]                          [Save Traits]
```

The floating window also has a Close button and an X button (UIPanelCloseButton).

---

## UI Component Behaviors

### Trait Edit Boxes
- Editable, 64 character limit enforced both client-side and server-side
- `sanitizeInput()` strips control characters and collapses whitespace on
  save
- All three must be non-empty before the server command is sent

### Tone Box
- Read-only: `EnableMouse(false)` prevents focus and interaction
- Populated by PROFILE responses
- Shows grey "Generating tone..." placeholder while LLM is running
- Normal color (0.7, 0.7, 0.7) restored when real content arrives
- `ApplyProfileToPanel` preserves the placeholder while a tone poll is
  active — does not overwrite with empty string during polling

### Background Story Box
- Read-only: `EnableMouse(false)`
- Multi-line with a thin scrollbar (shown only when content overflows)
- Mouse-wheel scrolling enabled on the holder frame
- Shows grey "Creating background story..." placeholder while LLM is running
- `HandleBackstoryPayload` only writes to the box when text is non-empty —
  preserves placeholder during polling

### Dropdown
- Alphabetically sorted by bot name
- Selecting a bot issues `get <guid>` immediately
- Checkmark shows currently selected bot
- Shared state: selecting in one panel reflects in both

### Refresh Button
- Issues `roster` command, rebuilds the dropdown
- Auto-triggered when the options panel is shown (`OnShow`)
- Also triggered after FORGOTTEN to remove the bot from the list

### Forget Button
- Shows a confirmation popup naming the bot
- On confirm: sends `forget <guid>`, server deletes per-player memories
- After FORGOTTEN response: clears both panels, re-requests roster

### Save Traits Button
1. Sanitizes and validates all three traits
2. Compares against `self.loadedTraits` (snapshot taken when profile was last loaded)
3. **Unchanged**: Shows "Traits unchanged." immediately — no server call
4. **Changed**: Shows confirmation popup warning that tone and backstory
   will be regenerated
5. On confirm: sends `set <guid> <t1> <t2> <t3>`
6. Server responds `UPDATED <guid> <name> changed|unchanged`
7. On `changed`: starts both polls, shows placeholders in both boxes
8. On `unchanged`: shows "Traits saved for <name>."

### Regenerate Story Button
- Disabled while a backstory poll is in progress
- On click: sends `regenbackstory <guid>`, immediately starts backstory
  poll and shows placeholder
- Re-enabled by `StopBackstoryPoll()`

---

## Polling System

Because LLM generation is asynchronous (Python bridge), the addon polls for
results after triggering generation.

### Tone Poll
- Triggered: when `UPDATED changed` is received
- Interval: every 1.5 seconds, sends `get <guid>`
- Timeout: 60 seconds (LLM tone generation can take ~5-30s under load)
- On arrival: `ApplyProfile` detects non-empty tone with `awaitingTone`
  flag, calls `StopTonePoll()`, shows "Generated tone for <name>" in green
- On timeout: shows "Tone generation is still pending. Use Refresh." in orange

### Backstory Poll
- Triggered: when `UPDATED changed` is received, or when Regenerate Story
  is clicked
- Interval: every 2.0 seconds, sends `get <guid>`
- Timeout: 30 seconds
- On arrival: `HandleBackstoryPayload` detects non-empty text, calls
  `StopBackstoryPoll()`, re-enables Regenerate Story button
- On timeout: shows "Backstory generation still pending. Use Refresh."
- Status "Backstory generated." only shown if tone poll is also done
  (avoids overwriting "Generating tone..." status)

### Coordination
Both polls fire `get <guid>` independently. Each `get` triggers both a
`PROFILE` and a `BACKSTORY` response from the server. The handlers check
their respective `pending*Guid` fields to decide whether to stop polling.
There is no explicit coordination between the two polls — they converge
naturally via the same endpoint.

### awaitingTone Flag
`ApplyProfile` captures `awaitingTone = (self.pendingToneGuid == profile.guid)`
before calling `ApplyProfileToPanel`. This lets it distinguish between:
- A poll response arriving mid-generation (tone still empty → keep "Generating
  tone..." status)
- A normal profile load (tone populated or legitimately empty → show "Loaded
  <name>")

---

## State Machine (per bot selection)

```
[bot selected]
    → SelectBot() → get <guid>
    → PROFILE arrives → ApplyProfile()
        → loadedTraits snapshot taken
        → tone/backstory populated in boxes
        → status: "Loaded <name>"

[user edits traits, clicks Save Traits]
    → traits unchanged → "Traits unchanged." [end]
    → traits changed → popup
        → cancelled [end]
        → confirmed → DoSaveProfile() → set <guid> <t1> <t2> <t3>
            → UPDATED changed
                → StartTonePoll: tone box shows "Generating tone..."
                → StartBackstoryPoll: story box shows "Creating background story..."
                → status: "Saved. Regenerating tone and backstory..."
                → polls run every 1.5s / 2.0s
                    → tone arrives → StopTonePoll → status "Generated tone for <name>"
                    → backstory arrives → StopBackstoryPoll → Regen button re-enabled

[user clicks Regenerate Story]
    → RegenBackstory() → regenbackstory <guid>
    → StartBackstoryPoll: story box shows "Creating background story..."
    → Regen button disabled
    → backstory arrives → StopBackstoryPoll → Regen button re-enabled

[user clicks Forget]
    → popup → confirmed → ForgetBot() → forget <guid>
    → FORGOTTEN → panels cleared → RequestRoster()
    → roster re-loaded → first bot auto-selected
```

---

## UX Principles Applied

### Immediate Feedback
Every user action produces a status message within one frame:
- Buttons show status before the server round-trip completes
- Generation placeholders appear before LLM finishes

### Optimistic UI
Polls start immediately on action. The placeholder content ("Generating
tone...", "Creating background story...") signals activity without waiting
for server acknowledgment of the queued task.

### Destructive Action Protection
Two actions require confirmation popups:
1. **Save Traits with changed values** — warns that tone and backstory will
   be regenerated (visible cost to the user)
2. **Forget** — names the bot explicitly in the confirmation text; clarifies
   that personality is preserved, only memories are erased

### No Silent No-ops
"Traits unchanged." is shown explicitly when nothing changed, rather than
silently doing nothing. The user always knows whether their action had
an effect.

### Consistent Read-only Styling
Read-only fields (tone, backstory) use `EnableMouse(false)` — no cursor
flash on click, no text selection, no accidental focus. Placeholder text
uses grey (0.5, 0.5, 0.5); real content uses lighter grey (0.7, 0.7, 0.7).

### Button State Reflects System State
The Regenerate Story button is disabled while backstory generation is in
progress (`SetRegenStoryEnabled(false)`). Re-enabled by `StopBackstoryPoll()`
on success or timeout. Prevents double-submissions.

### Dual Panel Consistency
Both panels (floating window and options panel) share the same `Chatter`
singleton. `SetStatus`, `StartTonePoll`, `StartBackstoryPoll`, and
`SetRegenStoryEnabled` all iterate both panels unconditionally, keeping them
always in sync regardless of which is visible.

### Graceful Timeout Handling
Polls time out with an actionable message ("Use Refresh") rather than
silently failing or looping forever. The user is never left wondering why a
box is empty.

---

## Known Limitations

- Both polls fire independently when both are active simultaneously (after
  trait change), sending up to ~70 `get` requests to the server over the
  combined poll window. This is bounded and harmless but inefficient.
- The `BACKSTORY_REGEN` server command exists in the handler but is never
  sent by the current C++ implementation — it is effectively dead code in
  the Lua handler.
- Polls continue running even when both panels are hidden (the `OnUpdate`
  script is always active). They time out normally, so this is bounded.
- Window position is persisted in `ChatterDB` but only for the floating
  window, not the options panel (which is managed by WoW's interface
  options system).
