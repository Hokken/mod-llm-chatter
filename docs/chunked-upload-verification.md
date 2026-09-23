# Chunked Upload — Manual Verification Matrix

There is no automated harness for the C++ `.llmc` commands or for addon Lua,
so the profile-upload path (`Chatter-Companion` client, `put` / `commit` /
`cancel` on the server — see [`chatter-addon-reference.md`](chatter-addon-reference.md))
is checked by hand against this matrix instead. Each row exercises one axis
that can fail independently of the others: payload size decides which code
path runs at all, encoding decides whether a chunk boundary can land inside
an escape, interruption decides whether staged state is ever left behind or
applied after it's stale, and persistence decides whether a write failure
can leave half an edit behind.

Reload the addon (`/reload`) between rows so `loadedTraits` and any staged
upload from a previous row cannot mask the one under test.

## 1. Payload size — which path runs

| Payload | Expected path | Pass looks like |
|---|---|---|
| Three short English traits (well under 64 chars each) | Single-line `set` | One `.llmc set` line in the chat log; save completes immediately; no `put`/`commit` traffic |
| Three traits at exactly 64 characters | Chunked (`put` × N, `commit`) | Save button disables, `put` lines stream at one every 0.3 s, `commit` follows, then tone/backstory regenerate |
| One trait at 64 chars, two short | Chunked | Only the long trait's field produces `put` chunks; the short fields still ride in the same `commit` |
| A 1,000-character backstory of 4-byte UTF-8 characters sent as `bs` chunks by hand | Chunked, 60 chunks | Every chunk is accepted (the cap is 64); `commit` saves the whole story and `get` returns it intact |
| The same backstory split into 65 chunks | Rejected | `ERROR chunk Malformed chunk header`; nothing is staged past the cap |

The boundary for traits is the assembled `.llmc set <guid> <t1> <t2> <t3>`
line against the client's 255-character chat limit, not the 64-character
per-trait box limit — so the exact traits that flip from single-line to
chunked will drift if the trait content changes. Re-check the boundary case
(row 2) after any change to the command prefix or encoding.

## 2. Encoding — where a chunk boundary can land

| Payload | Why it stresses `SplitEncoded()` | Pass looks like |
|---|---|---|
| Cyrillic text at 64 characters | Every character costs 6 characters once percent-encoded (`%D0%A1...`), so a naive split at a fixed offset will land inside a `%XX` escape roughly 2 times out of 3 | Saved trait round-trips through `get` with every Cyrillic character intact — no `%` literal, no replacement character |
| Emoji or other 4-byte UTF-8 at 64 characters | Same escape-boundary risk, plus the multi-byte source character itself can straddle a chunk if the split lands between two encoded triplets that belong to the same codepoint | Round-trips intact through `get`; the server reassembles all chunks before decoding, so a split codepoint is harmless — the only requirement is to *not corrupt the escape* |
| A trait whose encoded length is an exact multiple of `CHUNK_BUDGET` (200) | Boundary sits exactly on a chunk edge — the off-by-one case for the `stop >= total` check in `SplitEncoded()` | Splits into the expected number of chunks with no empty trailing chunk and no dropped last character |

## 3. Interruption — what happens to state mid-upload

| Action | What it exercises | Pass looks like |
|---|---|---|
| `/reload` after the first `put` lands but before `commit` | The server's `PendingProfileEdit` must not leak or be committed by the next session | `get` on that bot shows the pre-save traits; `.llmc commit <guid>` sent by hand afterwards is rejected or reapplies nothing meaningful, since the client no longer has the staged text |
| Select a different bot mid-upload | `SelectBot()`'s cancel path | The send queue is flushed and `cancel <oldGuid>` is sent; polling `get <oldGuid>` afterwards shows the old traits, not a half-applied set |
| A second player edits the same bot's traits while your upload is in flight | Whether a stale `PROFILE`/`BACKSTORY` payload can revert boxes you're mid-save on | Your Save button stays disabled and your typed traits stay in the boxes until your own `commit` resolves — `ApplyProfile()` and `HandleBackstoryPayload()` must ignore payloads for `self.uploadGuid` |
| Server sends `ERROR` mid-upload (e.g. edit a trait to exceed `kMaxChunkLength` after the fact) | The abandon path | Save button re-enables (`UnlockSave()`), the send queue is dropped rather than continuing to stream, and the status line shows the decoded server error text |
| Wait out `SAVE_LOCK_TIMEOUT` (20s) with no server response at all | The save-lock's own timeout, independent of any server `ERROR` | Save button re-enables on the client after 20s even though no message ever arrived, so a dead server cannot permanently strand the UI |

## 4. Persistence — one transaction per edit

| Action | What it exercises | Pass looks like |
|---|---|---|
| Commit traits and a backstory together, then inspect `llm_bot_identities`, `llm_group_bot_traits` and `llm_group_cached_responses` | All writes share one transaction | Traits, backstory and cache invalidation are all present; `UPDATED` and `BACKSTORY_SAVED` arrive only after that |
| Make the write fail (e.g. temporarily `REVOKE UPDATE` on `llm_group_bot_traits` for the worldserver user) and commit traits plus a backstory | The rollback path | `ERROR save ...` arrives, no `UPDATED`/`PROFILE` lines, no `bot_tone_regen`/`bot_backstory_regen` rows in `llm_chatter_events`, and none of the tables changed. Restore the grant afterwards |

## Notes for future changes

- `CHUNK_BUDGET` (200), `SEND_INTERVAL` (0.3s) and `SAVE_LOCK_TIMEOUT` (20s)
  live in `Chatter-Companion/Chatter.lua`; `kMaxChunkLength` (200) and
  `kMaxChunksPerField` (64) live in `src/LLMChatterCommand.cpp`. The client
  and server chunk-size constants are independent values that happen to
  agree — if either changes, re-run the boundary rows of the size matrix.
- This file, `chatter-addon-reference.md`'s protocol table, and
  `CHANGES-Chatter-Companion.md` should stay consistent with each other
  whenever the chunking protocol changes; they describe the same wire
  format from three angles (test plan, protocol reference, PR rationale).
