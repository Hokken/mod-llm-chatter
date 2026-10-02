# Arathi Basin chatter: implementation and gaps

Arathi Basin already has working source paths for node-change reactions,
resource milestones, match lifecycle, and shared combat chatter. Its main
gap is factual context: it lacks the persistent objective picture that
Warsong Gulch now has for flags. Several existing AB reactions can also
misdescribe what happened or attribute it to the wrong player.

This investigation concerns **mod-llm-chatter coverage**, using AzerothCore
rules and mod-playerbots behavior as dependencies. It does not propose
replacing the bots' tactical AI with LLM decisions.

## Evidence baseline

Source inspected on 2026-10-01, with these reproducible revision baselines:

| Repository | Revision |
|---|---|
| mod-playerbots/azerothcore-wotlk, Playerbot upstream base | `06234df3d5ab26c93f4f1f06f3edb828b73ecd3c` |
| mod-playerbots | `b6696bdbd3740e575598d167d69f39f68cc0b907` |
| mod-llm-chatter | `7638f6c61499473c06b26dcf7844701514f97d9a` |

The cited core battleground sources, configuration template and AB database
template match that upstream base. The module rows identify their checkout
HEADs; core and playerbots revisions are available in their public upstream
repositories.

The evidence is the inspected working-tree source, not confirmation of a
deployed binary, runtime-loaded configuration, database schema, or in-game
result. The local configuration file was checked only for the victory
target; it agrees with the 1600 source default.
Line references below locate that snapshot; symbol names remain useful
after line numbers change. AzerothCore is the rules authority throughout.
“Missing” means absent from the traced chatter contract, not absent from
the battleground implementation or client UI.

## 1. What the local core actually implements

The five nodes are Stables, Blacksmith, Farm, Lumber Mill, and Gold Mine.
The base battleground template allows up to **15 players per team**; this
is template evidence, not a check of live database overrides. Every occupied
node contributes equally to the controlled-base count: strategic location
differs, but there is no per-node resource multiplier. [C1][C2][C5]

They are territory-control objectives: interacting with their banners is
not picking up or carrying a WSG flag. The core represents neutral,
Alliance/Horde contested, and Alliance/Horde occupied states. It also
retains `_captured` to distinguish defence of a previously occupied node
from competing claims on an initially neutral node. [C1][C2]

| Transition | Core meaning | Important consequence |
|---|---|---|
| Neutral → team contested | Initial claim | Assault score credit; starts a 60-second capture timer. |
| Initially uncaptured contested → other team contested | Counter-assault | Changes claimant; restarts the 60-second timer. |
| Enemy occupied → team contested | Assault | Immediately removes the old owner's controlled base; schedules graveyard cleanup and starts the timer. |
| Previously captured contested → defending team occupied | Successful defence | Cancels the timer; restores occupation immediately; awards defence credit. |
| Contested → same team occupied on timer expiry | Completed capture | Adds a controlled base and spirit guide; broadcasts that the base was taken. |

The click handler requires an in-progress match, proximity within 10 yards
of the game object and less than 10 yards of a node position, and rejects
friendly occupied/contested interactions. Capture-spell completion and the
subsequent **60-second occupation timer are separate stages**. A nearby
player is not evidence of who completed the banner interaction. [C1][C2][P4]

Only occupied nodes produce resources. The scheduler uses these rates:

| Occupied bases | Resources per tick | Tick interval |
|---:|---:|---:|
| 0 | 0 | No resource award; scheduler checks again after 3 seconds |
| 1 | 10 | 12 seconds |
| 2 | 10 | 9 seconds |
| 3 | 10 | 6 seconds |
| 4 | 10 | 3 seconds |
| 5 | 30 | 1 second |

These are scheduled tick rules, not a promise of an instantaneous rate
change: tick execution reads the controlled-base count and schedules the
next interval. The default victory target is **1600**, but
`Battleground.Arathi.CapturePoints` can override it. The core's near-victory
warning remains **1400**. Chatter must distinguish the configured winning
score from the fixed warning. [C1][C2][C3]

Two bases do **not** earn twice the resources of one: the steady scheduled
rates are `10/9` versus `10/12` resources per second, a 4/3 ratio. A
1500-resource victory target would be a configured variant, not the
inspected default; any future chatter must read the actual target rather
than assume either 1500 or 1600. The local configuration file also specifies
1600, though a running world's loaded value was not queried.

Other AB-specific facts available in the core include:

- Base assault/defence scoreboard counters, separate from killing blows.
- Loss of a node's spirit guide and relocation of queued dead players;
  occupation creates a spirit guide again.
- Four/five-base quest reward spells, periodic honor/reputation, and match
  rewards. Honor tick thresholds are 260 normally/160 on weekends;
  reputation thresholds are 160/150, with the AB reputation rate applied.
- A historical “more than 500 resources behind” flag for achievement
  evaluation, not a continuously emitted tactical event.
- Premature-winner selection prefers controlled-base count, then delegates
  ties to the base battleground implementation. [C1][C2]

These are possible context inputs, not a recommendation to narrate every
reward or resource tick.

## 2. What playerbots already do

`AiFactory` installs `arathi` for AB, including resolving a Random
Battleground to its actual type. Generic battleground triggers drive
movement, objective checking, and death resets. `ArathiStrategy` adds
banner checks and buff use. `BGTactics::Execute` selects AB paths and banner
IDs and calls the relevant objective/interaction methods. [P1][P2][P3]

| Existing bot behavior | Verified implementation | Chatter implication |
|---|---|---|
| Team strategy | Match-start script randomly selects balanced, offensive, or defensive strategy per team for ordinary AB. | No corresponding strategy field reaches AB prompts. |
| Defender tendency | `selectObjective`: role threshold 3 normally, 1 offensive, 6 defensive; enemy defensive strategy overrides it to 2. Defender branch is further gated at 85%. | A strategy/role is a tendency, not proof the speaker is guarding a base. |
| Defensive destination | Chooses nearest friendly occupied or enemy-contested node in its defensive branch. This branch does not establish the contested node's former owner. | Do not invent “saving our base” from its selected destination alone. |
| Attack destination | Pool of up to three neutral, enemy-occupied, or friendly-contested nodes; usually nearest candidates, with a 20% farthest-candidate variation, then random selection from the pool. | No fixed “always attack Blacksmith” or guaranteed three-base strategy. |
| Diversions/fallback | 5% aggressive enemy-target branch; when no valid neutral/enemy target exists, enemy-target or enemy-graveyard camping fallback precedes defender selection. | Avoid promising a stable defender assignment from a role value. |
| Banner interaction | Checks spawned/ready objects, nearby enemy target, and friends already casting the capture spell; avoids duplicate capture attempts, dismounts, and casts `SPELL_CAPTURE_BANNER`. | Attempt, interrupted cast, completed assault, and final occupation must remain distinct. |
| Capture coordination | Keeps an active capture stationary; may move away from a friendly capturer and reset/reroute its objective. | “A friend is casting” does not prove a lasting escort/guard assignment. |
| Buffs and travel | AB paths, objective resets, speed/regen/berserk selection with health/mana and healer checks. | Lower-priority opportunities for observed contextual chatter. |

Sources: [P2][P3][P4][P5]. These are source branches, not measured live
frequencies or proof every selected action completes.

Chatter's existing `OBSERVATION_CONSTRAINT` forbids action promises and
movement plans because speech does not control the AI. Preserve that
boundary. The first useful improvement is richer observed AB state; direct
strategy integration would need a separate, current per-speaker contract
and must not disclose hidden enemy decisions. [M3]

One dependency caveat: the playerbots match-start strategy initializer
switches on `GetBgTypeID()` without resolving Random Battleground, although
its tactical executor and factory do resolve it. Do not assume randomized
AB team strategies are assigned in the random-queue case. This is separate
from chatter coverage and is not a request to change playerbots. [P1][P3][P5]

## 3. Current chatter flow and shared coverage

1. `LLMChatterBGScript` hooks match start/end, add-player, update, and
   destruction. Its update polls during `STATUS_IN_PROGRESS` and compares
   scores and node states. `PollABState` emits `bg_node_contested` or
   `bg_node_captured`. `DetectScoreEvents` emits resource milestones. [M1]
2. `QueueBGEventForAllPlayers` creates recipient-specific events for real
   players whose group has bots. `AppendBGContext` adds team, scores, alive
   counts, real teammates, instance ID, and subgroup/crowd roster. [M1][M6]
3. The event registry dispatches node/milestone events to
   `chatter_battlegrounds.py`. Its handlers use the BG prompt builders and
   subgroup worker. The SQL event enum already contains these types.
   [M2][M4][M10]
4. `fire_subgroup_worker` selects from `party_bot_guids`, supports lightweight
   identities when traits are absent, and queues Party speech tagged
   `owner_subsystem='bg'`. Node reactions use the urgent pacing policy;
   score milestones use the default contextual policy. [M5][M7]
5. C++ delivers Party speech to the speaker's current subgroup; BG-channel
   speech broadcasts to its group. Generation success/event `completed`
   therefore does not establish that a player heard the line. [M5][M8]

| Capability | AB status | Limits / evidence |
|---|---|---|
| Match start/end | Shared support | BG-wide; end includes result, final scores, player kills/damage/healing, but no AB assault/defence totals. [M1][M2] |
| Arrival / late join | Shared support | About 15-second batch; subgroup bots, live score and `match_in_progress`; greeting split between Party/BG. Arrival builds its own payload rather than calling `AppendBGContext`. [M1][M11] |
| Combat, death, low health, OOM, spell and achievement reactions | Shared support | BG prompt routing and speaker/subgroup handling carry over; AB objective snapshot does not. [M12][M5] |
| Node contest/capture | Partial | Real state polling, but compressed semantics, guessed actor, lossy selection and Party-only routing. [M1][M2][M3] |
| Score milestones | Partial | 500/1000/1500 thresholds; not the core warning or configurable victory target. [M1][M3] |
| Idle chatter | Shared support | Score-aware category selection, but no base picture or AB hold/contest-duration update. [M2][M3] |
| Mode, identity, brevity | Shared support | BG base context, normal/RP distinctions, anti-repetition, short replies and no fabricated action promises. [M3] |
| WSG carry timeline / stale-carry filtering | WSG only | No node timeline equivalent; cannot claim AB gained this protection. [M2][M13] |
| AB landmarks/objective text | Partial | `BG_LORE[3]` exists. Base context uses RP lore/landmarks, but does not consume its `objectives` or `tone` fields. Static lore is not live ownership. [M3][M14] |

Subgroup-only node chatter is the documented current policy, not inherently
a defect. It does mean an alarm about a base is **not a team-wide callout**.
Changing that policy is a product decision; preserve subgroup audibility
and avoid reintroducing duplicate Party/BG announcements. [M2][M15]

## 4. Confirmed gaps and correctness risks

### A. Random Battleground can bypass AB-specific chatter

`CreateNewBattleground` stores the original queue type with `SetBgTypeID`
and the selected map type with `SetRandomTypeID`. `GetBgTypeID()` returns
the former; `GetBgTypeID(true)` returns the latter. Thus an AB selected
through Random Battleground is type `BATTLEGROUND_RB` at the switches in
`DetectScoreEvents` and `OnBattlegroundUpdate`. Neither reaches the AB
branch. The same unresolved value is exported as `bg_type_id`, so lookup
of `BG_LORE[3]` also fails. Generic lifecycle/idle paths still run. [C4][M1]

This is shared infrastructure: Random→WSG also bypasses polled flag
pickup/drop/capture and carry updates, and Random→Eye of the Storm bypasses
its objective polling and milestones; both lose their specific lore lookup.
WSG flag context can still arrive through resolved `ToBattlegroundWS()`,
and its separate flag-return script checks `GetBgTypeID(true)`, so partial
WSG support is not evidence that random-queue dispatch works. [C4][M1][M3]

**Priority: correctness first.** Resolve actual battleground identity
consistently for rule-specific dispatch and prompts, while retaining queue
identity separately if needed. Reuse the pattern already present in
playerbots; test explicit AB and Random→AB side by side. [P1][P3]

### B. Defence, capture, initial claim and assault are conflated

`PollABState` classifies solely by the new state being contested or not.
Consequently a successful defence restoring occupation becomes
`bg_node_captured`, and `build_bg_node_prompt` says the team captured the
node. Initial neutral claims and assaults also share one event without
previous state/owner. For a contested node, `new_owner` is actually the
**claiming/assaulting team**, while the core owner can be neutral. [C2][M1][M3]

The prompt correctly uses that team for attack direction, but lacks the
history needed to justify its urgency: an enemy's first neutral claim is
framed as an attack requiring defenders. It cannot distinguish reclaiming
a held base from beginning occupation of a neutral one.

**Priority: correctness first.** Preserve transition semantics in the
payload and prompt. A sampled previous/current state helps, but cannot
recover every intermediate event or actor; use an authoritative transition
source where available, otherwise describe only the observed state change.
Do not infer successful banner interaction merely from a click attempt.

### C. Node actor attribution is a proximity guess

The producer picks the nearest **real player** within 15 yards, with no
check that their team matches the transition or that they interacted with
the banner. It runs this search on timer captures too. Bots are excluded.
The prompt then explicitly credits/names this person as assaulter or
capturer. A bystander, opponent, or newly arrived player can receive credit;
the actual bot actor cannot. The 15-yard heuristic is also wider than the
core's click checks. [M1: `PollABState`, lines 751-786][C2][M3]

**Priority: correctness first.** Omit personal credit when the actor is
unknown. If adding attribution, carry the authoritative actor, team and
action stage; keep the earlier assaulter distinct from timer completion.

### D. No persistent AB objective snapshot

`AppendBGContext` includes WSG-specific carriers/states but no AB nodes,
occupied-base counts, contested timers, resource tick information, or
configured winning score. Node events add only node name, new team and
optional guessed claimer. Ordinary combat, idle, arrival and end prompts
therefore cannot reliably say which bases the team holds, what is being
lost, or whether its current resource rate can overcome a score deficit.
The model knowing AB's rules is not evidence of this match's state. [M1][M3]

**Priority: next substantive feature.** Add a compact, team-relative AB
snapshot through the established BG context owner, including the separate
arrival payload. Keep factual state separate from computed tactical
inference. Timers need authoritative remaining time or an explicitly
approximate observation; a polling timestamp is not the capture deadline.

### E. Shared cooldown discards most simultaneous node transitions

Loaded defaults are `NodeEventChance=80`, `StatePollingIntervalMs=3000`,
and `BigEventCooldownSec=15`. Each changed node rolls independently, but
all nodes and score milestones share **one match-level** big-event clock.
Match start marks that clock when its `MatchStartChance` roll passes
(default 100%). Travel to the opening nodes can outlast that initial
cooldown; it should not be assumed to block every opening.
`lastNodeState` advances even if RNG
fails or cooldown blocks queueing; there is no deferred replay. Scores
are checked before nodes, so an accepted milestone can suppress nodes
on that poll. [M1][M9]

For an illustrative opening with all five claims observed on one poll,
an eligible real-player/bot group, and a clear cooldown:

- At most one node transition is accepted for queueing, not five.
- Assuming independent 80% rolls, the chance of accepting any is
  `1 - 0.2^5 = 99.968%`; expected accepted transitions are `0.99968`.
- Expected discarded transitions are `4.00032` out of five, about 80%.
- Selection favors earlier indices: Stables is first, Gold Mine last.
- If the start/milestone cooldown is already active, all five are lost.

This is a source-derived example, not a measured match. Claims spread over
more than 15 seconds can yield more reactions. An accepted transition can
fan out into several recipient events, and later delivery may still fail.
WSG flag transitions deliberately bypass chance/cooldown suppression;
that guarantee has not been generalized to AB nodes. [M1]

**Priority: policy decision after correctness.** Separate recording facts
from deciding which to voice. Consider coalescing simultaneous updates or
node-specific selection rather than blindly announcing every event. New
controls should be documented: these four loaded settings, including
`ScoreMilestoneChance`, are absent from the current module `.conf.dist`.
[M9]

### F. Score commentary ignores AB's resource race details

The producer rolls `ScoreMilestoneChance` once per changed-score poll,
then tests hardcoded 500/1000/1500 thresholds for both teams. The poll
always updates previous scores afterward. A failed roll or cooldown at a
crossing permanently loses that milestone. There is no dedicated reaction
to the core's 1400 warning, change in controlled-base count, resource-rate
lead, or historical 500-point disadvantage. [M1][C2]

At 1500 the prompt declares victory close without the configured maximum
or current base distribution. A score lead alone also drives “dominating”
language in node prompts. These are inadequate foundations for an AB
prediction; e.g. a trailing team holding more bases may be catching up.
`BG_LORE` contains a static 1600 objective string, but that field is not
currently rendered by the base prompt, so it is not an existing source of
maximum-score awareness. [M3][M14]

**Priority: context correctness, then optional enrichment.** Supply the
actual target and base counts before adding race projections. Distinguish
core warning, configured win proximity, and conditional “if bases stay
unchanged” calculations. Avoid declaring a mathematically guaranteed win
without accounting for tick timing and possible node changes.

### G. Node reactions lack freshness and match-bound delivery checks

The node handler consumes the queued snapshot without checking later
node events, unlike the WSG flag timeline. AB can be defended again while
an earlier assault reaction is waiting. Polling can also miss a full
occupied→contested→occupied sequence between observations. [M1][M2][M13]

`bg_instance_id` exists in common event context, but the traced generic
Party/BG delivery branches do not validate it or current node state.
They send through the bot's current group. The event `group_id` is used
for pacing, not an equality check against its current group. The delivery
code reads `instance_id` for other scoped paths; that does not establish
validation of BG's `bg_instance_id`. A subgroup move, match exit/requeue,
or delayed LLM completion can therefore make an otherwise valid snapshot
stale or change its audience. This is a shared transport risk with AB
impact, not a live-reproduced failure claim. [M5][M8]

**Priority: freshness with richer objective events.** Preserve match and
node revision through generation and delivery; reject or reframe superseded
reactions. Keep match-end speech's allowed lifecycle explicit rather than
requiring every message to remain in an in-progress match.

### H. Objective consequences and individual contributions are absent

No dedicated AB chatter contract exposes successful defence credit,
assault totals, graveyard gain/loss, capture protection/interruption,
or a periodic “holding three bases” picture. Match-end payloads include
generic performance but omit `BattlegroundABScore` objective counters.
Generic death/rez/achievement paths are not equivalent to these facts.
Core broadcasts and UI can still communicate them independently. [C2][M1]

**Priority: optional enrichment after A-G.** Start with base-control
context and accurate defence recognition; consider objective contributions
at match end next. Buffs, reward ticks and quest-credit narration are
lower-priority opportunities, not required parity with WSG.

## 5. Suggested implementation order and ownership

1. Correct actual-BG identity, transition wording and unsupported actor
   credit in the existing BG producer/prompt owners.
2. Define a compact AB snapshot and freshness contract in the BG subsystem.
   Reuse common transport, identity, mode and subgroup helpers; extend
   arrival context deliberately. If transition/timeline logic grows, give
   it a dedicated AB file rather than expanding unrelated group handlers.
3. Decide which AB facts warrant team-wide versus subgroup speech and how
   simultaneous changes should be selected/coalesced. Keep chance and
   timing configurable; do not couple fact retention to the speech roll.
4. Add resource-race context, periodic objective observations, and objective
   contribution summaries only on that factual foundation.

Any future payload/event change must update its registry, tests and
contributor documentation. New event names would also need the applicable
schema migration because `event_type` is an enum; this investigation does
not require new names rather than extending existing payloads. [M4][M10]

## 6. Verification needed for future changes

Current dedicated BG scripts cover WSG timeline/carry behavior and generic
arrival/subgroup cases; searches of `tools/tests` found no focused AB node
transition, AB score-race, or Random→AB dispatch regression. The existing
tests are useful shared protection, not evidence of AB semantic coverage.
[T1][T2]

| Scenario | Required evidence |
|---|---|
| Explicit AB and Random→AB, plus Random→WSG/EY regression checks | Same rule-specific producer/prompt paths and correct map identity; preserve WSG context/return behavior. |
| Initial claim, counter-claim, assault, defence, timed capture | Distinct factual descriptions for both teams, with correct occupied counts. |
| Bot actor, human actor, nearby opposing human, no actor known | No invented personal credit; timer completion does not credit a bystander. |
| Five simultaneous claims; score crossing plus node change | Measured selection/coalescing matches configured policy; dropped speech does not erase facts. |
| One through five occupied bases; contested base stops scoring | Snapshot and conditional rate commentary agree with core scheduling. |
| 1400 warning, 1500 milestone, changed victory target | No conflation of warning and winning score; reduced targets do not require unreachable milestones. |
| Trailing score with faster income; zero bases while ahead | No unsupported inevitable-win/defeat or dominance claims. |
| Late join, enabling chatter mid-match | Current ownership baseline without inventing five just-completed captures. |
| Fast assault/defence, delayed generation, simultaneous AB instances | No stale alarm, state reversal or cross-instance context. |
| Subgroup change, departure, requeue, match end | Correct audible audience and lifecycle; no old-match Party/BG leakage. |
| Normal and RP modes; traits present/absent | Same factual constraints, mode-appropriate wording and no AI action promises. |
| Match-end objective contribution | Assault/defence statistics come from the correct player's AB score. |

Static source tracing supports the findings above. These scenarios still
need targeted regressions and, for timing/audibility, controlled in-game
verification. No compilation or runtime result is implied by this report.

## Source index

Paths are relative to this document. Line spans identify the inspected
snapshot; the listed symbols describe exactly which evidence to revisit.

- **[C1]** [BattlegroundAB.h](../../../src/server/game/Battlegrounds/Zones/BattlegroundAB.h):
  lines 97-178, nodes/states/rates; 213-297, score and capture-point data.
- **[C2]** [BattlegroundAB.cpp](../../../src/server/game/Battlegrounds/Zones/BattlegroundAB.cpp):
  `PostUpdateImpl` 51-145; `NodeOccupied` 264 and `NodeDeoccupied` 290;
  `EventPlayerClickedOnFlag` 305-407; `GetPrematureWinner` 409;
  `Init` 464-487; `EndBattleground` and `GetClosestGraveyard` 489 onward.
- **[C3]** [worldserver.conf.dist](../../../src/server/apps/worldserver/worldserver.conf.dist):
  `Battleground.Arathi.CapturePoints`, lines 4032-4037.
- **[C4]** [BattlegroundMgr.cpp](../../../src/server/game/Battlegrounds/BattlegroundMgr.cpp):
  `CreateNewBattleground`, 379-415;
  [Battleground.h](../../../src/server/game/Battlegrounds/Battleground.h):
  `GetBgTypeID`, 330; setters 366-367; `ToBattlegroundAB`, 585.
- **[C5]** [battleground_template.sql](../../../data/sql/base/db_world/battleground_template.sql):
  AB row (ID 3), line 50, `MaxPlayersPerTeam=15`;
  [local worldserver configuration](../../../env/dist/etc/worldserver.conf):
  `Battleground.Arathi.CapturePoints`, line 3717. This file is a local
  configuration input and may not exist in another contributor's checkout.
- **[P1]** [AiFactory.cpp](../../mod-playerbots/src/Bot/Factory/AiFactory.cpp):
  combat/noncombat BG strategy setup, 461-471 and 688-698.
- **[P2]** [BattlegroundStrategy.cpp](../../mod-playerbots/src/Ai/Base/Strategy/BattlegroundStrategy.cpp):
  `BattlegroundStrategy::InitTriggers`, 19-25;
  `ArathiStrategy::InitTriggers`, 45-51.
- **[P3]** [BattleGroundTactics.cpp](../../mod-playerbots/src/Ai/Base/Actions/BattleGroundTactics.cpp):
  `Execute`, 1559-1717; `selectObjective` type resolution 1841-1859;
  AB branch 2312-2489; `resetObjective` 3361-3394.
- **[P4]** [BattleGroundTactics.cpp](../../mod-playerbots/src/Ai/Base/Actions/BattleGroundTactics.cpp):
  `atFlag`, 3561-3854; `useBuff`, 4014-4077.
- **[P5]** [Playerbots.cpp](../../mod-playerbots/src/Script/Playerbots.cpp):
  `PlayerBotsBGScript::OnBattlegroundStart`, 472-508;
  [BattleGroundTactics.h](../../mod-playerbots/src/Ai/Base/Actions/BattleGroundTactics.h):
  `ABBotStrategy`, 28-34; [BattleGroundTactics.cpp](../../mod-playerbots/src/Ai/Base/Actions/BattleGroundTactics.cpp):
  `GetBotStrategyForTeam`, 1433-1440.
- **[M1]** [LLMChatterBG.cpp](../src/LLMChatterBG.cpp):
  tracker 27-85; `AppendBGContext` 88-236; queue helpers 238-295;
  `DetectScoreEvents` 297-427; WSG bypass 449-452;
  `MaybeQueueFlagCarryChatter` 649-690; `PollABState` 692-797;
  lifecycle hooks 930-1071; arrival/update/polling 1073-1356.
- **[M2]** [chatter_battlegrounds.py](../tools/chatter_battlegrounds.py):
  match handlers; `process_bg_node_event` 396-423;
  score handler 512-536; idle/carry handler 539-618.
- **[M3]** [chatter_bg_prompts.py](../tools/chatter_bg_prompts.py):
  `OBSERVATION_CONSTRAINT` 41; `_bg_base_context` 71-242;
  node prompt 552-637; milestone prompt 702-762; idle prompt 1040-1076.
- **[M4]** [chatter_event_registry.py](../tools/chatter_event_registry.py):
  node, score and idle `EventSpec` entries, 863-935.
- **[M5]** [chatter_raid_base.py](../tools/chatter_raid_base.py):
  `dual_worker_dispatch` 173; `fire_subgroup_worker` 261-390;
  `fire_raid_worker` 393 onward.
- **[M6]** [LLMChatterShared.cpp](../src/LLMChatterShared.cpp):
  `AppendRaidContext` 2466-2555; `SendPartyMessageInstant` 2785-2789.
- **[M7]** [chatter_party_gate.py](../tools/chatter_party_gate.py):
  `_CRITICAL_EVENTS` 27-44; `policy_for_reason` 99-117.
- **[M8]** [LLMChatterDelivery.cpp](../src/LLMChatterDelivery.cpp):
  event/instance extraction 413-463; subsystem guards 477 onward;
  Party/BG send branches 1014-1074; pacing group ID 1514-1525.
- **[M9]** [LLMChatterConfig.cpp](../src/LLMChatterConfig.cpp):
  BG option defaults 874-902;
  [mod_llm_chatter.conf.dist](../conf/mod_llm_chatter.conf.dist):
  BG enable 686-691, idle settings 3029-3043; no declarations for the four
  node/score/polling/big-event settings named in section E.
- **[M10]** [base schema](../data/sql/characters/base/00000000_llm_chatter_tables.sql):
  event enum BG entries 54-64.
- **[M11]** [chatter_bg_prompts.py](../tools/chatter_bg_prompts.py):
  `build_bg_arrival_prompt`, 1171 onward;
  [mod-llm-chatter-documentation.md](mod-llm-chatter-documentation.md):
  BG arrival routing, 1502-1516.
- **[M12]** [chatter_group_handlers.py](../tools/chatter_group_handlers.py):
  BG combat/death routing 644/711; achievement path 1369-1403;
  spell/health/OOM builders 1553/2253/2284.
- **[M13]** [chatter_bg_flag_timeline.py](../tools/chatter_bg_flag_timeline.py):
  match-scoped WSG flag timeline; consumed by the flag/carry handlers in M2.
- **[M14]** [chatter_constants.py](../tools/chatter_constants.py):
  `BG_LORE[3]`, 1308-1329.
- **[M15]** [mod-llm-chatter-architecture.md](mod-llm-chatter-architecture.md):
  Battleground routing, 1683-1699;
  [mod-llm-chatter-documentation.md](mod-llm-chatter-documentation.md):
  current BG routing and subgroup audibility, 1435-1492.
- **[T1]** [test_battleground_flag_context.py](../tools/tests/test_battleground_flag_context.py):
  match isolation, delayed drop/return, regrab, carry safety and arrival tests.
- **[T2]** [test_battleground_carrier_messages.py](../tools/tests/test_battleground_carrier_messages.py):
  delivery reason and out-of-subgroup speaker tests.
