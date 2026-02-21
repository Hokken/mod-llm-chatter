# Battleground Chatter Vision

A concept document describing what immersive battleground chatter should feel and sound like, what events drive it, and what must never appear.

---

## The Fantasy

You queue into Warsong Gulch with your group of bots. The gates open. Instead of silent NPCs running preset paths, your teammates come alive:

> "Let's go! For the Alliance!"

The enemy grabs your flag. A warrior in your group reacts:

> "Flag's gone! They've got it!"

Your team picks up the enemy flag:

> "We've got their flag, don't let them take ours!"

A mage in your group gets a killing blow on the enemy flag carrier:

> "Dropped him! Flag's on the ground!"

Your team scores. The mood shifts:

> "That's two. One more and we've got this."

This is the goal. Bots that feel like real PvP players reacting to a live match in real time. They observe, they react, they cheer — but they never claim actions that might contradict what the playerbots AI is actually doing.

---

## Core Principles

### Urgency Above All
Every message must feel like it belongs in a battle. BGs are fast-paced, high-stakes, and chaotic. The tone is sharp, reactive, and in-the-moment. No contemplation, no poetry, no small talk.

### Tactical Awareness
Bots should sound like they know what's happening. They reference the score, the objectives, the enemy, and the flow of the match. When Blacksmith gets contested in Arathi Basin, a bot doesn't say "nice fight" — they say "They're hitting BS!"

### Brevity
BG messages should be short. In the heat of PvP, nobody writes paragraphs. One sentence, sometimes two. Callouts, reactions, taunts, encouragement. Get in, get out.

### Faction Pride
Bots should feel allegiance to their faction. Alliance bots fight for the Alliance. Horde bots fight for the Horde. This comes through in their language — pride when winning, defiance when losing, trash talk about the enemy.

### Personality Still Matters
Even in the chaos of a BG, different classes and personalities react differently. A holy priest might say "I can't heal through this, we need to peel!" while a fury warrior says "Charging in, focus the healer!" The bot's class, role, and traits still shape HOW they react, but the urgency is universal.

### Observation Only — Never Claim Actions
This is a critical constraint. The LLM has **no visibility into what a bot is actually doing**. Bot strategy, movement, target selection, and objective decisions are all managed internally by the playerbots module. The chatter system is completely disconnected from that decision-making.

This means bots must **never claim they are doing or about to do something**, because their actual behavior might contradict the message. A bot saying "I'm going for the flag!" while the playerbots AI sends it to defend a node would shatter immersion worse than silence.

**All messages must be reactive observations or generic encouragement, never action declarations.**

Safe (reacting to an event we detected):
- "Flag's down!" (we detected the flag state change)
- "Nice kill!" (we hooked the PvP kill event)
- "They capped again, that's 2-1." (we tracked the score change)
- "Here we go!" (match start event)

Safe (generic, no action claims):
- "We need to hold this!"
- "Don't let up!"
- "Their healer is keeping them alive."
- "Come on, we've got this!"

NOT safe (claims about the bot's own actions):
- "I'm going for the flag" (might not be)
- "Cover me, heading through tunnel" (might go elsewhere)
- "I'll defend Stables" (might attack Gold Mine)
- "Focusing their healer" (might target a warrior)
- "Heading left" (might go right)
- "I'll grab the flag when it drops" (might not)

The rule is simple: **react to what happened, never promise what will happen.**

---

## What We Want to See

### Match Flow Reactions

**Match Start**
- Battle cries, generic encouragement, faction pride
- "For the Alliance! Let's do this!"
- "Stay together, don't let them pick us off."
- "Here we go, give them everything!"

**Score Changes**
- Reactions to scoring or being scored on
- "We're up 2-1, keep it up!"
- "They capped again. Come on, we can't let that happen."
- Increasing desperation when behind, growing confidence when ahead

**Match End**
- Victory celebration or defeat reaction
- "That's what I'm talking about! Well played everyone."
- "We almost had it. Their healer carried them."
- Short, emotional, authentic

### Objective Events

**Flag Picked Up (WSG/EY)**
- Observation of who picked it up (we detect the state change and know the carrier)
- Excitement when your team grabs it: "We've got their flag!"
- Alarm when the enemy grabs yours: "They've got our flag!"

**Flag Dropped**
- Observation that the flag hit the ground
- "Flag's down!" / "Their carrier is dead, flag's loose!"

**Flag Captured**
- Celebration or frustration depending on which team scored
- Score awareness: "That ties it up!" / "One more cap!"

**Node Assaulted (AB/AV)**
- Observation that a node is being contested (we detect state change)
- "Farm is under attack!" / "They're hitting Blacksmith!"
- Never "I'm going to defend X" — the bot may or may not be heading there

**Node Captured**
- Observation that ownership changed
- Satisfaction when team secures a point: "Stables is ours!"
- Frustration when losing one: "We lost Lumber Mill."
- Strategic awareness: "We've got three nodes, just hold!"

**Tower Burned / Gate Destroyed (AV/SotA)**
- Big moment reactions for major objective completions
- "South tower is down!" / "The gate's breached!"

### Combat Events

**PvP Kills**
- Quick reactions to observed kills (we hook the event)
- "Got one!" / "One down!"
- Acknowledgment of teammate kills: "Nice one!"

**Deaths**
- Frustration, determination
- "They got me. Don't let up."
- No melodrama, just the acknowledgment and move on

**Killing Streaks / Multi-Kills**
- Escalating excitement when a teammate is on a tear
- "That's three, keep it going!"

### Situational Awareness

**Score-Based Tension**
- Close matches should generate more intense chatter
- Blowouts should generate resignation or dominance
- Comebacks should generate rising excitement

**Time Pressure**
- Awareness of match timer when relevant
- "Running out of time, we need this!"

**Team Strength**
- General morale observations
- "We're getting overwhelmed!" / "We've got the numbers!"

### Lore and Faction Context

**Battleground Lore**
- Each BG has rich lore that adds depth when referenced in context
- WSG: Silverwing Sentinels vs Warsong Outriders, the lumber war in Ashenvale
- AB: League of Arathor vs The Defilers, the fight for Arathi Highlands resources
- AV: Stormpike Expedition vs Frostwolf Clan, the frozen mountain conflict
- "The Warsong will never take this forest!" (Night Elf in WSG)
- "For the Frostwolf Clan!" (Orc in AV)
- "The Defilers won't hold these lands." (Human in AB)

**Faction Pride**
- Alliance and Horde bots should express faction loyalty in the heat of battle
- References to the enemy faction as a whole, not just individual players
- "The Horde won't take this one!" / "For Thrall and the Horde!"
- Racial flavor: Dwarves, Orcs, Elves etc. each have their own way of expressing battle spirit

### Weather and Time of Day

The LLM will know we're in a battleground, so weather and time references are fine — they add atmosphere when delivered with battle urgency rather than peaceful contemplation.

- "Fighting in the rain, can barely see them coming." (not "What lovely rain")
- "Night's falling, watch the shadows." (not "Beautiful sunset tonight")
- "This fog is perfect for an ambush." (not "The mist is so serene")

The key is that weather/time observations serve the battle context, adding tension or tactical flavor rather than breaking immersion with peaceful tone.

### Immersion Amplifiers

These features elevate BG chatter from functional callouts to screenshot-worthy moments. They're particularly important for roleplayers.

**Acknowledge the Real Player by Name**
- When the player gets a PvP kill, a bot reacting with "Nice one, Calwen!" is far more immersive than generic "Got one!"
- Makes the player feel seen by their teammates, like they're part of a real squad
- We get the player name from the PvP kill hook — this is safe data

**Score Trajectory, Not Just Current Score**
- The LLM should know if the team is on a comeback (was 0-2, now 1-2) vs cruising (was 2-0, now 3-0)
- The emotional arc is completely different: "We're back in this!" vs "They can't stop us!"
- Close matches should generate the most intense chatter

**First Blood**
- The very first kill of the match sets the tone
- A reaction to the first PvP kill feels electric — the battle just became real

**Match Phase Awareness**
- Early match: fresh energy, battle cries, faction pride
- Mid match: tactical observations, score awareness, momentum reads
- Late match with close score: desperate intensity, urgency, do-or-die energy
- The LLM should know approximate match duration to shift tone naturally

**The Blowout Shift**
- If it's 0-3 or the team is getting stomped, bots shouldn't keep cheerleading
- Resignation, frustration, gallows humor — that's what real players do
- "Well... that happened." feels more authentic than forced optimism

### Roleplay Depth

These are specifically designed for the RP audience — the kind of messages that make a roleplayer screenshot the chat and share it.

**Racial Grudges and Lore Connections**
- A Night Elf in WSG isn't just fighting "the enemy" — she's fighting the Orcs who destroyed Ashenvale's forests
- A Forsaken fighting humans has complicated feelings about their former kin
- Draenei vs Blood Elves carry the weight of Tempest Keep and the Exodar
- Orcs in AV feel the Frostwolf Clan's fight for their ancestral home
- These deep racial tensions are what RP players live for
- The RACE_SPEECH_PROFILES already in mod-llm-chatter can be extended with faction-enemy context per BG

**Class Fantasy in Battle**
- A Paladin invoking the Light mid-fight: "The Light protects!"
- A Shaman calling on the ancestors: "The spirits guide my hand!"
- A Warlock's dark satisfaction: "Their souls feed my power."
- A Death Knight's cold detachment: "Death comes for them all."
- A Druid channeling nature's fury: "Elune, give me strength!"
- A Priest's desperate prayer: "Light, shield us!"
- RP players love when class identity shines through in the heat of battle

**Spiritual and Religious Flavor**
- Priests and Paladins reference the Light
- Druids invoke Elune, Cenarius, or the wild gods
- Shamans call on the elements or the ancestors
- Tauren reference the Earth Mother
- Forsaken have a bleak, nihilistic edge
- Blood Elves reference the Sunwell or Quel'Thalas
- This adds enormous depth for RP players and it's all expression, not action claims

**The Enemy as THE ENEMY**
- Not "they scored" but "The Horde has our flag!"
- Not "someone's at Stables" but "Alliance dogs are at the Stables!"
- RP players want factions to feel like factions with real weight and hatred
- The enemy team isn't just opponents — they're the ancestral foe

**Honor and Gravitas in Defeat**
- When losing, RP players don't want "gg we suck"
- They want dignity: "We fought with honor. The Gulch will see us again."
- Or defiance: "This isn't over. We'll be back."
- Or solemn acceptance: "The Light tests us. We will endure."
- Defeat with grace is a deeply RP concept

**Sense of Purpose Beyond the Battle**
- Characters who fight for something bigger than the score
- "I fight so Darnassus may know peace."
- "For Orgrimmar! For the Warchief!"
- "The Highlands belong to the people of Arathor."
- A fleeting reference to home, to their people, to what's at stake
- This transforms a game match into a story moment

**Victory with Meaning**
- Not "GG" but "Glory to the Alliance! The Silverwing stand victorious!"
- Not "ez" but "Lok'tar Ogar! The Warsong claim this land!"
- Victory should feel earned, celebrated with faction and racial pride
- The weight of the lore should be present in the triumph

---

## Dual-Worker Delivery Model (Added Review Session)

BG chatter is delivered through two separate processing layers, each serving a different purpose:

### Raid Worker — "The Crowd"

This worker creates the feeling of being in a large, living team. It reacts to major BG events by picking random bots from **across the entire raid** (outside the player's sub-group) to speak.

- **Events**: match start, match end, flag captures, node captures, boss kills, wipes, epic loot
- **Channel**: `CHAT_MSG_RAID` (visible to full team) or `CHAT_MSG_BATTLEGROUND` (0x2C)
- **Frequency**: Low — these are rare, high-impact moments
- **Bot selection**: Random bots from other sub-groups, so the player hears "the crowd" reacting
- **Personality**: Lightweight — race/class identity is enough, no full trait generation
- **Tone**: Epic, faction-proud, urgent callouts

Example: A boss dies in AV. A Dwarf warrior from sub-group 3 shouts in raid chat: "The beast is down! Push forward, lads!"

### Group Worker — "The Squad"

This is the existing group chatter system, scoped to the player's sub-group. It handles both normal group events AND reacts to raid/BG events with a more personal, intimate tone.

- **Events**: kills, deaths, loot, spells, player chat responses, AND the same big events the raid worker handles (but with personal flavor)
- **Channel**: `CHAT_MSG_PARTY` via `SayToParty()` (reaches sub-group only)
- **Frequency**: Normal group chatter rates, dynamically scaled by sub-group size (not raid size)
- **Bot selection**: Only bots in the player's sub-group
- **Personality**: Full trait system — the same bots the player has been playing with all session
- **Tone**: Personal, familiar, squad-level banter

Example: Same boss dies. The Priest in the player's sub-group says in party chat: "That was close. Thought we were going to wipe for a second there."

### The Combined Effect

The same event can produce **two complementary reactions**: someone across the raid shouting in raid chat, and a bot next to you in party chat making a personal comment. This is exactly how real raids and BGs feel — the crowd cheers while your friend leans over and says something just to you.

**Coordination rules:**
- A bot picked by the raid worker for an event must NOT also react via the group worker for the same event
- Separate cooldowns per worker, with a shared "big event" cooldown to prevent message floods
- The raid worker stays subtle — 1-2 messages per major event, never more

This model applies to both normal PvE raids AND battlegrounds. In BGs, the raid worker additionally handles BG-specific events (flag state changes, node contests, score milestones) while the group worker handles combat events (PvP kills, deaths, heals) scoped to the sub-group.

---

## What We DO NOT Want

The core rule is simple: **no overworld event types should fire during a battleground.** If the only events reaching the LLM are BG events, and the LLM knows it's in a battleground, it will naturally produce the right tone. We don't need to over-constrain its creativity — just make sure the wrong triggers never fire.

### Suppressed Event Types in BGs

These mod-llm-chatter events must be completely suppressed when a player is in a battleground. They are disconnected from the BG context and would break immersion:

- **Loot reactions** — no item drop excitement mid-battle (exception: AV turn-in items like Armor Scraps, Storm Crystals, Frostwolf Medallions are BG objectives and could warrant reactions)
- **Quest objective/completion messages** — irrelevant in BG context
- **Trade / crafting references** — not the time or place
- **Holiday / seasonal event messages** — "Happy Brewfest!" during a flag fight is absurd
- **Transport arrival messages** — no zeppelin chatter in a warzone
- **Idle banter / ambient chatter** — the general chatter trigger loop should not fire
- **Bot greeting messages** — the OnAddMember spam when bots join the BG raid

### Bot Action Claims

As described in the Observation Only principle above, bots must never claim actions they may or may not be performing. This is the only hard constraint on the LLM's output — beyond that, give it creative freedom within the BG context.

### LLM Creative Freedom

Beyond suppressing the wrong event types and the action-claim rule, the LLM should have creative margin. If it knows it's in Warsong Gulch, it might reference the Ashenvale lumber war, comment on fighting in the rain, or express faction pride — all of that is welcome. The BG context in the prompt is enough to keep it on track.

---

## Tone by Battleground

### Warsong Gulch
Intense, fast, personal. Small team (10v10) means every player matters. Flag runs create moments of individual heroism. Tunnel fights are chaotic. The tone is scrappy and competitive.

### Arathi Basin
Strategic, territorial, spread out. Teams split across 5 nodes. Reactions are about node status and team momentum. The tone is tactical and aware. "They took LM!" / "We've got three, hold steady!"

### Alterac Valley
Epic, large-scale, war-like. 40v40 feels like an actual battle. Pushing through Iceblood, burning towers, the final boss pull. The tone is grand and military. "Tower's burning, push forward!"

### Eye of the Storm
Hybrid tension. Holding bases while fighting over a central flag creates constant decision-making. The tone reflects the split focus between bases and the flag. "We lost Mage Tower!" / "Someone grabbed the flag!"

### Strand of the Ancients
Siege warfare. Attackers are desperate to break through gates. Defenders are holding the line. The tone shifts between rounds — attacking is aggressive and urgent, defending is resolute and tense.

### Isle of Conquest
Full-scale war with vehicles. Airship drops, siege engines crashing gates, workshop control. The tone is chaotic and explosive. "Get on the glaives! Break their gate!"

---

## Message Frequency

BG chatter should be event-driven, not time-driven. Messages fire in response to meaningful events, not on a timer. This means:

- **High-impact events** (flag captured, match start/end, boss killed): Always generate a reaction
- **Medium-impact events** (flag picked up, node contested, PvP kill): Chance-based, but frequent enough to feel alive
- **Low-impact events** (individual deaths, respawns): Occasional, not every time

The goal is a steady stream of contextual chatter that makes the match feel alive without flooding the chat. A typical 15-20 minute WSG might have 15-25 bot messages total — enough to feel present, not enough to annoy.

---

## Module Structure

This is NOT a separate AzerothCore module. It lives within mod-llm-chatter as a new Python file: `chatter_battlegrounds.py`, alongside the existing `chatter_group.py`, `chatter_events.py`, etc.

- **C++ hooks**: New `AllBattlegroundScript` class in `LLMChatterScript.cpp` — inserts BG events into the existing `llm_chatter_events` table
- **Python processing**: `chatter_battlegrounds.py` — BG-specific prompts, handlers, flavor data, state interpretation
- **Bridge dispatch**: New entries in `llm_chatter_bridge.py` routing `bg_*` events to the battleground handlers
- **Delivery**: Same `llm_chatter_messages` table and `DeliverPendingMessages()` system
- **Config**: New BG section in the existing `mod_llm_chatter.conf`

All shared infrastructure (LLM calling, message delivery, config parsing, bot trait system) is reused. The separation is purely in the Python logic layer where the BG-specific tone, context, and event handling live.

When a player enters a BG, mod-llm-chatter's existing group/ambient chatter should be suppressed (`player->InBattleground()` check) and only BG events should fire.

---

## Gaps and Enrichments (Added Session 40)

These were identified during review as missing from the original vision. None are blockers for Phase 1 — they're Phase 2-3 enrichments that would deepen the experience.

### Pre-Gate Waiting Room

There's a 1-2 minute period before gates open where everyone's buffing and waiting. This is prime chatter time — tension, anticipation, pre-match banter.

- "Ready up, here we go."
- "I've got a good feeling about this one."
- "Buff up, they won't wait for us."
- A warrior flexing confidence, a priest checking mana, a rogue sizing up the enemy team

**Detection**: `OnBattlegroundAddPlayer` fires when they enter the instance. `bg->GetStatus()` returns `STATUS_WAIT_JOIN` before gates open, `STATUS_IN_PROGRESS` after. The waiting room phase is the window between these two states.

### Respawn Reactions

The vision covers deaths well but not the respawn run back. In BGs you die, wait at the graveyard, respawn, and charge back into the fight. Real players say things like:

- "Back up, let's go again."
- "That rogue is camping our GY."
- "Alright, round two."

This is a natural chatter moment. We already have the `OnPlayerReleasedGhost` hook from the corpse run feature — it could detect BG respawns and generate quick reactions instead of ghost-run commentary.

### Mood System Integration

The existing per-bot mood drift system (Session 36) evolves mood based on kills, deaths, loot, and wipes. It's already built but not mentioned in the BG vision. It's a perfect fit:

- Early match: all bots start neutral/content
- Killing spree: mood rises to cheerful/ecstatic — bot sounds fired up
- Death streak: mood drops to gloomy/miserable — bot sounds frustrated
- By late match, a bot who's been dying all game sounds genuinely defeated while a bot on a tear sounds unstoppable

This requires zero new code — just wire `_bot_mood_scores` into BG prompt builders the same way group chatter does.

### Stalemate / Turtle Detection

When a match stalls — WSG stuck at 1-1 for 10 minutes, AB hovering at 3 nodes each with no progress — real players get frustrated. Bots should too.

- "This is going nowhere."
- "Someone needs to make a play."
- "We've been stuck at two caps forever."

**Detection**: Poll score deltas over time in `OnBattlegroundUpdate`. If score hasn't changed in N minutes and match is past a threshold duration, fire a stalemate event. Frequency: rare (one message per stalemate detection, long cooldown).

### BG Emotes

The existing emote system (17 types, LLM-selected for conversations, keyword-matched for statements) isn't mentioned in the BG vision but would add significant physicality:

- `/charge` or `/roar` at gates opening
- `/cheer` after a flag capture or big kill
- `/salute` at match end (win or loss)
- `/cry` or `/sigh` after a frustrating death

The emote system is already built into message delivery (`HandleEmoteCommand` in C++). BG prompts just need to request an emote field in the LLM response, same as group chatter does.

### Consecutive Match Memory

If the player runs multiple BGs in a session, bots could reference earlier games:

- "Better start than last match."
- "Don't let them do what they did last time."
- "Two wins in a row, let's make it three."

**Implementation**: Lightweight static map keyed by player GUID tracking win/loss count and last BG type. Reset on logout (`OnPlayerLogout`). Passed to prompts as optional context. This is session-only memory — no database needed.

---

## Summary

Battleground chatter is a completely different beast from ambient world chatter. It's fast, tactical, emotional, and event-driven. Every message should make the player feel like they're fighting alongside real teammates who care about winning. No fluff, no filler, no flowers — just the battle.
