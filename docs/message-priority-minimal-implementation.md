# mod-llm-chatter Message Priority - Minimal Implementation

## Goal

Make important messages reach the LLM quickly and reach the player
quickly, without a large refactor of the current bridge architecture.

This note assumes the current design remains in place:

- one bridge coordinator loop
- event workers in a `ThreadPoolExecutor`
- background timer-style jobs using the same executor
- `llm_chatter_events` for reactive/event work
- `llm_chatter_queue` for legacy ambient work
- `llm_chatter_messages` for final delivery

## Design Intent

Not all chatter should be treated equally.

The system should prefer:

- messages tied to short-lived or perishable game state
- direct player interaction
- tactical or combat-relevant reactions
- events where late delivery looks obviously wrong

The system should de-prioritize:

- ambient filler
- idle chatter
- non-urgent world flavor
- legacy General-channel chatter that exists mainly for atmosphere

## Current Reality

Today, the system already has some priority behavior, but only in part:

- `llm_chatter_events` is fetched by `priority DESC, created_at ASC`
- `llm_chatter_queue` is FIFO
- final delivery from `llm_chatter_messages` is ordered by
  `deliver_at ASC`
- background jobs like idle chatter, bot questions, pre-cache refill,
  and legacy ambient processing are launched separately from event fetch

That means high-priority event rows can be claimed first, but once a
message is generated, final speak order is still mostly time-based.

## What Should Be Fast

### Tier 1: Critical / perishable

These should have:

- no RNG gate
- very short `react_after`
- very short final `deliver_at`
- priority over filler in both processing and final delivery

Recommended event families:

- `bg_flag_picked_up`
- `bg_flag_dropped`
- `bg_flag_captured`
- `bg_flag_returned`
- urgent BG node events
- `transport_arrives`
- `weather_change`
- `bot_group_nearby_object`

Reason:

- the game state changes fast
- the group may move away
- the event can look stale within seconds

### Tier 2: High / interactive

These should be processed quickly and should not sit behind filler:

- `bot_group_player_msg`
- `player_general_msg`
- direct combat-state callouts
- `bot_group_spell_cast`
- `bot_group_combat`
- `bot_group_low_health`
- `bot_group_oom`
- `bot_group_aggro_loss`

Reason:

- the player expects responsiveness
- the group context changes quickly

### Tier 3: Normal reactive

These are still meaningful, but can tolerate a little delay:

- kills
- deaths
- resurrects
- wipe/corpse-run
- quest progress reactions
- level-up
- achievement
- discovery
- dungeon entry
- zone transition

### Tier 4: Filler

These should always lose to the tiers above:

- legacy ambient General chatter from `llm_chatter_queue`
- idle group chatter
- `weather_ambient`
- `minor_event`
- `bg_idle_chatter`
- other atmosphere-only messages

## Minimal-Change Implementation

## 1. Keep the current event queue

Do not replace `llm_chatter_events`.

It already has the right core fields:

- `priority`
- `react_after`
- `expires_at`

That is enough to build a much better priority system without changing
the whole architecture.

## 2. Centralize event priority assignment

Right now, priorities are effectively scattered at call sites.

Minimal fix:

- add one C++ helper such as `GetEventPriority(eventType)`
- call it everywhere events are queued
- stop hardcoding priority numbers inline except for true one-offs

This keeps the existing queue schema but makes behavior understandable.

Recommended numeric bands:

- 100 = critical / perishable
- 80 = high / interactive
- 60 = normal reactive
- 20 = filler

Exact numbers matter less than consistent bands.

## 3. Centralize reaction-delay policy by event family

Priority alone is not enough.

Important events also need short `react_after`.

Minimal fix:

- keep `GetReactionDelaySeconds(eventType)`
- rewrite it around event tiers
- ensure Tier 1 and Tier 2 use very short ranges

Suggested ranges:

- Tier 1: `0-1s`
- Tier 2: `0-2s`
- Tier 3: keep current short natural delays
- Tier 4: current/default delays are fine

This preserves the existing event insertion path and only changes delay
policy.

## 4. Make final delivery honor priority

This is the most important missing piece.

Right now, C++ delivers from `llm_chatter_messages` using only
`deliver_at ASC`.

Minimal fix:

- when selecting the next ready message to deliver, join
  `llm_chatter_events` by `event_id`
- order ready messages by:
  - event priority descending
  - then `deliver_at` ascending

That lets urgent event-backed messages overtake filler that happened to
get an earlier timestamp.

For legacy ambient messages with no `event_id`, treat them as low
priority by default.

This gives a large benefit without changing the whole message schema.

## 5. Stop low-value background jobs from competing with urgent work

Do not refactor the bridge into multiple services yet.

Minimal fix:

- before launching idle chatter, legacy ambient processing, bot
  questions, or pre-cache refill, check whether urgent event backlog
  exists
- if critical/high pending events exist, skip launching filler jobs this
  loop and try again next loop

Practical rule:

- Tier 1 and Tier 2 events always win
- filler background jobs run only when urgent backlog is empty or small

This change belongs in the bridge coordinator, not in every handler.

## 6. Remove flat global queue caps from the main design

Do not rely on a flat global cap such as:

- `MaxPendingRequests`
- `GlobalMessageCap`

Those make the system fragile because filler can block meaningful work.

Instead:

- let priority control service order
- let RNG/cooldowns control filler volume
- let only emergency provider-safety logic suppress traffic

## 7. Add one provider safety circuit breaker

The safety goal is not "normal throttling."
It is "rare protection against runaway cost."

Minimal fix:

- add a rolling LLM call counter in the bridge
- define a soft threshold and a hard threshold

Soft threshold behavior:

- suppress Tier 4 filler only
- log a warning

Hard threshold behavior:

- suppress Tier 3 and Tier 4
- continue allowing Tier 1 and Tier 2
- log loudly

This matches the real requirement better than a queue cap.

## 8. Keep pre-cache as the fast path for repeatable tactical reactions

Pre-cache is already the right answer for reactions like:

- spell cast
- combat/state callouts
- cached farewell-style content

Do not replace that.

Instead:

- treat cache hit paths as the fastest lane
- reserve live LLM calls for cases where pre-cache misses or the event is
  too context-specific

If you later extend pre-cache, extend it only for repeatable,
high-frequency, low-variance reactions.

## Recommended First Pass

If the goal is to improve behavior quickly with minimal code churn,
implement in this order:

1. Centralize event priority mapping.
2. Tighten `GetReactionDelaySeconds()` for urgent tiers.
3. Change final delivery query to respect event priority.
4. Stop idle/pre-cache/legacy filler jobs from launching while urgent
   backlog exists.
5. Replace flat caps with a provider-safety circuit breaker.

That sequence should already produce a large improvement without
rewriting the bridge architecture.

## What Not To Do First

Avoid these as the first step:

- replacing all queues with a brand new queueing system
- splitting the bridge into separate processes
- adding many per-event config keys before the tiers are stable
- trying to solve cost control with broad caps that hit urgent traffic

The current system is close enough that a tiered scheduling pass should
be enough.

## Summary

The correct minimal-change direction is:

- use event type -> tier mapping
- make urgent tiers short in both reaction delay and final delivery
- make final delivery priority-aware
- prevent filler jobs from competing with urgent backlog
- use provider safety only as an emergency brake

That gives you "important things appear fast, filler waits" without
throwing away the current bridge loop.
