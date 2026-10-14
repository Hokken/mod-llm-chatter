# mod-llm-chatter Development Philosophy

## Purpose: immersion

mod-llm-chatter aims to evoke the activity of consciousness: individuals
noticing, feeling, remembering, speaking, and responding to one another.
Its quality depends on whether their presence feels believable over time.
Balance, subtlety, harmony, and unpredictability create that immersion and
the occasional "wow" moment.

Every new feature and its implementation must uphold this intent. These
principles are a design and review standard, not a claim that every current
code path already satisfies them. Use the architecture and runtime docs
for implementation ownership and existing behavior.

## 1. Begin with the individual and the situation

Ask: how would this being react here, given their personality, experience,
relationships, surroundings, and current circumstances? Then ask whether
the event would naturally invite a statement, an exchange, or silence.
An available game hook is not, by itself, a reason to speak.

Choose speakers who have a reason to notice and care. Let the importance
of the event shape their reaction; avoid turning every occurrence into an
announcement or having everyone react alike.

## 2. Preserve personality

Reuse the established persona lifecycle when bots enter group or Guild
contexts or are selected for General statements and conversations.
Existing traits, tone, and backstory must inform new features. Do not
regenerate or override a personality to make a feature's scene work.

The situation can influence mood and expression without replacing identity.
Backstory should surface when relevant, with subtlety; it is not a required
recital in every reply. Choosing not to include it in one prompt must not
alter the stored character.

## 3. Let conversations develop between individuals

Participants should respond to what others actually said. Allow different
perspectives, uneven contributions, brief acknowledgments, follow-up
questions, and natural changes of subject. Avoid rigid speaker rotations,
repeated introductions, compulsory questions, and identical story arcs.

Use appropriate recent history and supported memory for continuity. Do not
force callbacks or invent shared experiences. Leave the real player's
dialogue, decisions, emotions, and actions to the player.

## 4. Vary both expression and rhythm

Message length should match conversational purpose and vary naturally.
A short player message can invite a detailed answer; a long exchange can
end with a few words. Longer lines generally need more reading and response
time, but a fixed length-to-delay formula soon becomes recognizable.

Use bounded RNG to vary timing and appropriate choices such as participation,
length, and ambient opportunities. Preserve variation at the limits, too.
Randomness should make behavior less predictable while keeping it coherent
and responsive. It must never randomize facts, personality, or whether an
eligible player request is ignored. Reuse shared pacing and selection
mechanisms, and make tunable probabilities and limits configurable.

## 5. Protect responsiveness

Player participation takes priority over ambient output. Avoid cooldowns
that discard eligible player messages, especially direct addresses and
ongoing exchanges. Ambient frequency controls must not become a reason to
ignore someone who is speaking to a character.

When work must be paced, preserve the player's conversational intent instead
of silently dropping it. Account for generation latency before adding delay.
Natural silence at a genuine conversational ending differs from losing a
message to a timer. Any silence decision must respect meaning, recent
history, and the channel's response contract.

## 6. Give the LLM context and creative responsibility

Do not create arrays of words or phrases to filter natural-language messages
in or out of behavioral conditions. Keyword lists cannot reliably determine
intent, emotion, conversational closure, or the appropriate reaction.

Build dynamic prompts from structured facts, the speaker's persona, relevant
history, and the current situation. Let the LLM interpret meaning and create
the expression within those constraints. Keep deterministic validation for
structured contracts, factual eligibility, and protocol handling; it must
not become a substitute for understanding natural language.

## 7. Ground roleplay in the world

The module supports non-roleplay modes, but roleplay is its foundation.
Supply accurate lore relevant to the message type, place, event, and speaker.
Respect the configured mode and avoid inserting unrelated lore merely
because it is available.

Distinguish world lore from live facts. Characters must not invent who
performed an action, what happened, or what another person knows. Keep
unknowns unknown. Respect who can witness an event or hear a channel,
including group and subgroup boundaries. Creativity belongs in the reaction,
while the underlying situation remains true.

## 8. Balance presence, silence, and continuity

Too much speech overwhelms the world; too little makes its inhabitants feel
absent. Judge each feature alongside existing chatter, especially when
several triggers compete. Leave space for the player and for quiet moments.
Neither constant novelty nor constant repetition feels natural.

Immersion depends on what reaches the player. Recheck that delayed reactions
still fit the current scene and audience. Base visible conversational
continuity on speech actually delivered, not merely generated or queued.
Retries must not create duplicate speech or memories of unheard exchanges.

## Before accepting a feature

- Would these individuals plausibly react this way to this situation?
- Are personality, lore, live facts, and the player's agency preserved?
- Does the exchange build on what was actually heard?
- Are wording, participation, and timing varied without becoming arbitrary?
- Can a player engage without their message being lost to ambient controls?
- Does this improve the overall balance after repeated exposure?

Review the full path from trigger through prompt and delivery. Static tests
can check contracts; repeated in-game observation is needed to judge rhythm,
responsiveness, repetition, and the experience of immersion.
