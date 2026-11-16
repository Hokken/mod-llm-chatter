# Chatter Addon — Reference for Code Review

## Purpose

Chatter is a WoW 3.3.5a client-side addon that provides a UI for managing
**bot personality profiles** used by the `mod-llm-chatter` server module.

Players can:
- View bots that hold memories of them (the Known Bots roster)
- Read and edit the three personality traits assigned to each bot
- View the LLM-generated tone for each bot
- Read, rewrite and save each bot's background story
- Trigger background story regeneration on demand
- Forget bots (wipe their shared memories, preserving global identity)

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
(`chatter_identity.py`). The C++ layer queues events; Python picks them
up, calls the LLM, writes results to MySQL. The addon polls for results.

---

## Command Protocol

| Addon sends | Server responds |
|---|---|
| `.llmc roster` | `ROSTER_BEGIN`, `ROSTER <guid> <name>` × N, `ROSTER_END` |
| `.llmc get <guid>` | `PROFILE <guid> <name> <t1> <t2> <t3> <tone>` then `BACKSTORY <guid> <encoded>` |
| `.llmc set <guid> <t1> <t2> <t3>` — traits **changed** | `UPDATED <guid> <name> changed`, then `PROFILE` with empty tone (regen queued); **no BACKSTORY** |
| `.llmc set <guid> <t1> <t2> <t3>` — traits **unchanged** | `UPDATED <guid> <name> unchanged`, then `PROFILE` with existing tone, then `BACKSTORY` |
| `.llmc setbackstory <guid> <backstory>` | `BACKSTORY_SAVED <guid> <name>`, then `PROFILE`, then `BACKSTORY` with the saved text |
| `.llmc put <guid> <field> <seq> <total> <chunk>` | nothing on success; `ERROR chunk <text>` on a protocol fault |
| `.llmc commit <guid>` | same responses as the matching `set` / `setbackstory`, sent only after the edit has been persisted; `ERROR save <text>` if the write failed |
| `.llmc cancel <guid>` | nothing; drops the staged edit |
| `.llmc regenbackstory <guid>` | `BACKSTORY_REGEN <guid> <name>` (immediate ack); result arrives later via `get` polling. With `LLMChatter.Backstory.Enable = 0`: `ERROR disabled <text>`, and the stored story is left in place |
| `.llmc forget <guid>` | `FORGOTTEN <guid> <name>` |

With `LLMChatter.Backstory.Enable = 0` a trait change regenerates the tone
only. Its reply is then `UPDATED <guid> <name> changed nostory`, no story
job is queued, and the addon does not wait for a story. Addons that predate
the extra word ignore it.

All string fields are percent-encoded. `-` is the sentinel for an empty
string. The addon uses `Encode()`/`Decode()` for all string values crossing
this boundary.

One exception applies to addon-to-server text. The 3.3.5 client replaces
`%f` (focus name) and `%t` (target name) in every outgoing chat line,
upper case included, so an escape such as `%F0` would arrive as the focus
name. The addon therefore writes bytes `0xF0`–`0xFF`, which only occur in
4-byte UTF-8 characters such as emoji, as `~FX` (for example `~F0`), and
always escapes a literal `~` as `%7E`. The server's `PercentDecode()`
accepts both forms. Server-to-addon text stays plain `%XX`, because the
client does not rewrite incoming lines.

**What the addon actually sends.** Chatter Companion 1.2.0 and later edits
traits and the background story, as two separate saves. A trait save sends
`set`, or `put` / `commit` with the `t1`–`t3` fields. A story save sends
`setbackstory`, or `put` / `commit` with the `bs` field. The addon never
combines the two in one upload, although the server accepts a commit that
stages both. Earlier addon versions edit traits only and show the story
read-only. All of these share the validation, limits and transaction
described below, and are covered by
[`chunked-upload-verification.md`](chunked-upload-verification.md).

`BACKSTORY_SAVED` names the bot but not the text. The addon therefore
treats a story save as settled only when the `BACKSTORY` line that follows
carries exactly the text it sent, so the acknowledgement of an earlier save
that was given up on cannot be taken for the save in flight.

### Chunked Upload (`put` / `commit` / `cancel`)

The 3.3.5 client truncates an outgoing chat line at 255 characters, and
percent-encoding costs three characters per non-alphanumeric byte — six per
Cyrillic character. Three sentence-length traits therefore do not always fit
in one `.llmc set` line, and a truncated line fails to parse, losing the
save silently. `put` streams the same payload in pieces instead.

- `<field>` is `t1`, `t2`, `t3` or `bs` (backstory); `<seq>` is 1-based
  and must be `<= <total>`.
- `<chunk>` is percent-encoded text, at most 200 characters, and never cuts
  a `%XX` or `~FX` escape in half, so on fully escaped text a chunk holds at most
  198 characters (66 whole escapes). At most 64 chunks per field: enough
  for a 1,000-character backstory even if every character is 4-byte UTF-8
  (12,000 encoded characters, 61 chunks; 64 chunks carry up to 12,672). A
  `static_assert` in `LLMChatterCommand.cpp` ties the two limits together.
- Chunks are staged per player, addressed by `seq`, so a resend overwrites
  in place. A `put` for a different bot discards the whole staged edit; so
  does a logout or 60 seconds of inactivity.
- `commit` reassembles the fields in `seq` order, rejects gaps, decodes, and
  validates traits and backstory together. Fields that were not staged keep
  their stored values. The staged edit is dropped whether the commit
  succeeded or failed.

### Persistence

`set`, `setbackstory` and `commit` share one write path. After validation,
every write of the edit goes into a single `CharacterDatabaseTransaction`
committed with `AsyncCommitTransaction`: identity upsert, session-trait
update, cache invalidation, the backstory when present, and, when the traits
changed, the `bot_tone_regen` / `bot_backstory_regen` rows in
`llm_chatter_events` (no story regeneration if the edit brings its own
story). The regeneration jobs therefore exist exactly when the cleared
profile does.

The completion callback belongs to the player's session and only sends the
addon's answer:

- success: the usual `UPDATED` / `PROFILE` / `BACKSTORY_SAVED` / `BACKSTORY`
  lines;
- failure: `ERROR save <text>` and nothing else. The transaction rolled
  back, so the bot is untouched and no regeneration was queued, and the
  addon hands the edit back to the player as it does for any `ERROR`.

If the player disconnects before the commit finishes, the session drops the
callback unrun. Only the reply is lost: the edit and its regeneration jobs
still commit. An edit is therefore applied whole, jobs included, or not at
all.

A regeneration job never clears a story. The worldserver clears the stored
story in the step that queues the job (changed traits, or
`regenbackstory`), so a story the bridge finds when the job runs was
written after it was queued, by a `setbackstory` / `bs` save or by another
generation, and the job keeps it. A story saved while the provider call is
running wins as well: the generated text is only written against the exact
profile snapshot the call started from.

The addon builds the single-shot `set` or `setbackstory` line first and
only falls back to chunks when that line would exceed 255 characters, so
short ASCII text still takes exactly one message. Chunks are drained from a
FIFO at one message per 0.3 s, and the save buttons stay disabled until the
server answers. Only one upload is open at a time, traits or story.

[`chunked-upload-verification.md`](chunked-upload-verification.md) in this
folder is the in-game test plan for this path.

---

## Data Model

### Known Bots Roster (`llm_bot_memories`)
A bot appears in the roster if at least one memory row exists for this
player + bot pair. The C++ `roster` command queries this table. Forgetting a
bot deletes all memory rows for that player/bot pair, removing them from the
roster.

A bot can also leave the roster without being forgotten: memories of a
session too short to keep are discarded when the session settles. A `get`
for such a bot answers `ERROR access`, which the addon shows and treats as
the end of whatever it was waiting for.

### Bot Identity (`llm_bot_identities`)
Global persistent record keyed on `bot_guid`. Stores:
- `trait1`, `trait2`, `trait3` — personality adjectives
- `tone` — short LLM-generated style description (e.g. "wry and guarded,
  with quiet curiosity")
- `backstory` — 3-4 sentence character history, LLM-generated or written
  by the player, at most 1,000 characters
- `farewell_msg`, `identity_version`

Forgetting a bot does **not** touch this table. The global identity
persists; only the per-player memories are erased.

### Session Traits (`llm_group_bot_traits`)
Per-group shadow of identity data, used during active group sessions.
Cleared/synced when traits change.

---

## Addon Structure

| File | Owns |
|---|---|
| `Chatter.lua` | Protocol, encoding, the send queue, the upload lifecycle for traits and story, polling, profile and story state |
| `ChatterRoster.lua` | Roster filtering, checked bots, the paced forget batch |
| `ChatterUI.lua` | Widgets and layout only; no protocol behaviour of its own |
| `tests/` | Lua 5.1 regression tests against a stubbed client (not loaded by the game) |

## UI Layout

One editor layout is built three times and shares all state through the
`Chatter` singleton, so selecting a bot or typing in one place shows in the
others.

### Floating Window (`/chatter` or `/llmc`)
A 680×640 draggable frame, scaled down to fit small screens. Position is
persisted across sessions via `ChatterDB`. Shows everything: bot list,
traits, tone and story.

### Interface Options
Interface → AddOns → Chatter has an overview page with an **Open full
editor** button and two sections:

- **Bot Traits** — bot list, traits, tone, forgetting
- **Background Stories** — bot list and the story, filling the panel

### Layout (floating window)

```
Bot Traits
Click a name to edit. Check bots to forget their memories.

Search known bots        <selected bot name>            [Refresh]
[ search box      ]
[x] Botname              Trait 1: [single-line, 64 char max]
[ ] Botname              Trait 2: [single-line, 64 char max]
[ ] Botname              Trait 3: [single-line, 64 char max]
 ...scrollable...
                         Tone (generated): [read-only, multi-line]
3/12 bots | 1 checked
[Check all] [Clear]      Background Story: [editable, multi-line,
                                            scrollable]
                         [Regenerate Story] [Save Story]  412/1000

[Forget selected]                                   [Save Traits]
[status line]
```

---

## UI Component Behaviors

### Bot List
- Alphabetically sorted, filtered by the search box, scrolls independently
  of the profile
- Clicking a name selects the bot and issues `get <guid>`; the selected
  name is highlighted
- Checkboxes mark bots for **Forget selected** and do not change the
  selection. **Check all** checks every bot matching the search; **Clear**
  unchecks all

### Trait Edit Boxes
- Editable, 64 character limit enforced both client-side and server-side.
  Characters, not bytes, everywhere: `SetMaxLetters(64)` on the box, a UTF-8
  count in `SaveProfile()` and in the server's `ValidateField()`, and
  `VARCHAR(64)` in MySQL
- `sanitizeInput()` strips control characters and collapses whitespace on
  save
- All three must be non-empty before the server command is sent
- Once a profile is loaded the boxes belong to the player: a repeated
  `PROFILE` (a poll reply, a late answer) leaves edited boxes alone. Only
  selecting a bot starts them over

### Tone Box
- Read-only, multi-line
- Populated by PROFILE responses
- Shows grey "Generating tone..." placeholder while LLM is running
- `ApplyProfileToPanel` preserves the placeholder while a tone poll is
  active — does not overwrite with empty string during polling

### Background Story Box
- Multi-line with a thin scrollbar (shown only when content overflows) and
  mouse-wheel scrolling
- Editable once a profile and its story have loaded, and not while a save,
  a forget batch or a story generation without a pending edit is running
  (`UpdateStoryControls`)
- Typing creates an unsaved edit (`storyEdit`) as soon as the text differs
  from the server's story. While it exists, nothing the server sends
  replaces the text in the box: not `PROFILE`, not `BACKSTORY`, not the
  generation placeholder. Refresh and forgetting other bots keep it;
  clicking a bot in the list, or forgetting its own bot, drops it
- Shows grey "Creating background story..." placeholder while the LLM is
  running and no edit exists
- A counter shows the edit's length against the 1,000 character limit.
  Line breaks are saved as spaces

### Refresh Button
- Issues `roster`, rebuilds the list and reloads the selected bot
- Auto-triggered when a panel is first shown and after a forget batch
- A roster request that gets no answer within 10 seconds times out

### Forget Selected
- Confirmation popup with the count and names of the checked bots; the
  popup owns that snapshot
- On confirm, `forget <guid>` is sent for one bot at a time, 0.3 s apart,
  each waiting for its `FORGOTTEN` acknowledgement. An `ERROR` or 10 seconds
  of silence stops the rest of the batch
- Ends by re-requesting the roster

### Save Traits Button
1. Sanitizes and validates all three traits
2. Compares against `self.loadedTraits` (snapshot taken when profile was last loaded)
3. **Unchanged**: Shows "Traits unchanged." immediately — no server call
4. **Changed**: Shows confirmation popup warning that tone and backstory
   will be regenerated
5. On confirm: sends `set <guid> <t1> <t2> <t3>`, or the chunked upload
6. The editor stays locked until `UPDATED <guid> <name> changed|unchanged`
   or an `ERROR` arrives, or 20 seconds pass after the last line was sent.
   On rejection or timeout the upload is cancelled (`cancel <guid>`) and the
   typed traits are put back
7. On `changed`: starts both polls, shows placeholders
8. On `unchanged`: shows "Traits saved for <name>."

### Save Story Button
1. Enabled when an unsaved story edit exists and nothing else is in flight
2. Refuses an empty story and one over 1,000 characters before sending;
   an unchanged story is reported as such with no server call
3. No confirmation popup: a story save regenerates nothing
4. Sends `setbackstory <guid> <story>`, or `put <guid> bs ...` chunks and
   `commit`
5. The editor stays locked until the `BACKSTORY` line carrying the sent
   text arrives, an `ERROR` arrives, or the 20 second wait runs out. On
   rejection or timeout the text stays in the box and can be saved again
6. Held while a story generation the addon asked for may still run (see
   Save hold below)

### Regenerate Story Button
- Disabled while a backstory poll is in progress
- With an unsaved story edit it asks first, since the new story replaces
  the typed one. The popup keeps the bot it asked about
- On click: sends `regenbackstory <guid>`, immediately starts backstory
  poll and shows placeholder
- Re-enabled by `StopBackstoryPoll()`

---

## Polling System

Because LLM generation is asynchronous (Python bridge), the addon polls for
results after triggering generation.

- One request serves both waits. Every `get <guid>` is answered with a
  `PROFILE` and a `BACKSTORY` line, so while tone, story or both are
  awaited the addon sends a single `get` every 2 seconds (`HandlePolls`)
- Each wait gives up after 120 seconds with "... still pending. Use
  Refresh."
- Nothing is asked while an upload is open: the replies would be discarded
  as stale and the requests would share the chat line budget with the paced
  chunks. `UPDATED changed` restarts both waits with a fresh clock
- An `ERROR` outside an upload ends both waits and any pending profile
  load, instead of repeating a refused request until the timeout

### Tone wait
- Triggered when a trait save is sent, and restarted on `UPDATED changed`
- Ends when a `PROFILE` with a non-empty tone arrives; status "Generated
  tone for <name>"

### Backstory wait
- Triggered with the tone wait, or when Regenerate Story is clicked
- Ends when a `BACKSTORY` with a non-empty story arrives that is not the
  story being replaced (a reply to a request made before the generation was
  asked for can still carry the old one)
- Status "Backstory generated." only shown if the tone wait is also done
- Not started, or ended at once, when the server says no story is coming:
  `UPDATED ... changed nostory` after a trait change, `ERROR disabled`
  after Regenerate Story. The story box goes back to the stored story

### Save hold
A regeneration queued by a server older than 2026-11-16 cleared the stored
story when its job ran, so a story saved before that would be lost. The
addon therefore holds **Save Story** after everything that queues a story
generation (a trait save from the moment it is sent, `UPDATED changed`,
Regenerate Story) until a story other than the replaced one is seen for
that bot, or 150 seconds pass. With a current server the hold is no longer
needed for correctness; it stays for older ones.

---

## State Machine (per bot selection)

```
[bot selected]
    → SelectBot() → get <guid>
    → PROFILE arrives → ApplyProfile()
        → loadedTraits snapshot taken, tone shown
        → status: "Loaded <name>"
    → BACKSTORY arrives → loadedBackstory set, story shown

[user edits traits, clicks Save Traits]
    → traits unchanged → "Traits unchanged." [end]
    → traits changed → popup
        → cancelled [end]
        → confirmed → DoSaveProfile() → set / put...commit
            → editor locked, placeholders shown
            → ERROR or 20 s silence → cancel, traits put back [end]
            → UPDATED changed
                → status: "Saved. Regenerating tone and backstory..."
                → one get every 2 s
                    → tone arrives → status "Generated tone for <name>"
                    → backstory arrives → Regen button re-enabled

[user types in the story box, clicks Save Story]
    → storyEdit exists from the first differing keystroke
    → SaveStory() → setbackstory / put bs...commit
        → editor locked
        → ERROR or 20 s silence → cancel, text stays, retry possible [end]
        → BACKSTORY with the sent text → "Story saved for <name>."

[user clicks Regenerate Story]
    → unsaved story edit? → popup → cancelled [end]
    → DoRegenBackstory() → regenbackstory <guid>
    → story box shows "Creating background story...", Regen disabled
    → backstory arrives → Regen button re-enabled

[user checks bots, clicks Forget selected]
    → popup → confirmed → StartForgetBatch()
    → forget <guid> → FORGOTTEN → next ... → RequestRoster()
    → roster re-loaded → previous selection kept if still present
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

### Nothing Typed Is Lost Silently
A save is finished when the server says so, not when the addon stops
sending. Until then the typed traits or story are the only copy, and a
rejection, a timeout or a late reply cannot roll the boxes back. The player
gets the text back with a message and can save again.

### Destructive Action Protection
Three actions require confirmation popups:
1. **Save Traits with changed values** — warns that tone and backstory will
   be regenerated (visible cost to the user)
2. **Regenerate Story over an unsaved story** — the typed text would be
   replaced
3. **Forget selected** — names the bots in the confirmation text; clarifies
   that personality is preserved, only memories are erased

### No Silent No-ops
"Traits unchanged." and "Story unchanged." are shown explicitly when
nothing changed, rather than silently doing nothing.

### Button State Reflects System State
Save Traits, Save Story and Regenerate Story are enabled only when the
action can go through: nothing in flight, something to save, no generation
that would undo it.

### Panel Consistency
All three editors share the same `Chatter` singleton. Status, placeholders
and button states are applied to every panel that has the widget, keeping
them in sync regardless of which is visible.

### Graceful Timeout Handling
Uploads, polls, roster requests and forget batches all time out with an
actionable message rather than silently failing or looping forever.

---

## Known Limitations

- Results are polled: the server has no push for a finished generation.
  A full two-minute wait sends about 60 `get` requests, each costing the
  worldserver a few synchronous queries.
- A server older than 2026-11-16 gives the addon no signal when
  `LLMChatter.Backstory.Enable = 0`, so there Regenerate Story waits out
  its two minutes for nothing.
- `BACKSTORY_SAVED` carries no text and no correlation to a particular
  save; the addon works around it by matching the `BACKSTORY` text.
- Polls continue running even when all panels are hidden (the `OnUpdate`
  script is always active). They time out normally, so this is bounded.
- Window position is persisted in `ChatterDB` but only for the floating
  window, not the options panels (which are managed by WoW's interface
  options system).
