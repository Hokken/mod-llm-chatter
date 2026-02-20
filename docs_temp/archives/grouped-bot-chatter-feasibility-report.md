# Grouped Bot Chatter - Design Document

**Date:** 2026-02-05
**Status:** Concept in progress (Part 1) | Technical draft (Part 2 - do not update yet)

---

# Part 1: Concept and Core Features

## 1.1 Goal

Enable immersive, context-aware chatter when one or more bots are **grouped with a real player**. The chatter should feel natural, realistic, and grounded in what the group is actually doing.

## 1.2 Design Philosophy: Side Entertainment, Not Spam

Group chatter is **background flavor**, not the main attraction. When a player forms a group to run a dungeon, they care about loot, boss mechanics, and progression — not reading a wall of bot chatter. The system must stay moderate and unobtrusive at all times.

**What group chatter should feel like:**
- A few natural reactions tied to what's actually happening: a loot drop, a death, a close call, drinking between pulls, a spell saving someone
- Occasional personality moments: a joke, a comment about another bot's gear, a quip directed at the player
- Emotes that fit the moment: bowing after receiving a protective spell, laughing at a bad pull, cheering after a boss kill

**What group chatter must never become:**
- A nonstop stream of messages that drowns out gameplay
- Bots talking for the sake of talking when nothing is happening
- So frequent that the player starts ignoring party chat entirely

The golden rule: **less is more**. A single well-timed "nice save" after a close call is worth more than ten generic ambient messages. Every message should feel like it earned its place in the chat window. If in doubt, stay silent — the player won't miss chatter that didn't happen, but they will notice spam.

## 1.3 Core Principles

- **Atmospheric**: Reflect the mood of the area (tense, calm, spooky, triumphant).
- **Context-aware**: Use only information the group could plausibly know.
- **Immersive**: Feels like real party chat, not random world chatter.
- **Realistic**: Short, occasional, and situational. No spam.
- **Conversational**: Bots remember what was said and can have follow-up discussions.

## 1.4 Scope Rules

**Chatter is allowed only when:**
- At least one bot is grouped with a real player.
- The message relates to the **current group context**.

**Chatter is NOT allowed to:**
- Reference unrelated quests or loot.
- Mention items not actually looted or rolled on.
- Invent bosses or events that did not occur.

### Truth Constraint: General Channel vs Group Channel

This is a fundamental design principle that separates the two chatter systems.

The constraint applies specifically to **in-game actions and events** - things the player can directly observe. Bots are still free to have casual personality-driven conversation: jokes, stories about "what they did yesterday", friends that visited them, opinions, banter, etc. That's flavor, not a verifiable claim.

| | General Channel | Group Channel |
|---|---|---|
| **Player proximity** | Player is elsewhere, cannot see the bots | Player is right there with the bots |
| **Game event fabrication?** | Yes - bots can invent loot, kills, etc. | No - game events must be real and verifiable |
| **Casual flavor/stories?** | Yes | Yes - jokes, reminiscing, banter are all fine |
| **Example (OK)** | "Just looted an amazing sword!" (even if they didn't) | "Nice drop!" (only if something actually dropped) |
| **Example (OK)** | "I visited my friend in Stormwind yesterday" | "I visited my friend in Stormwind yesterday" |
| **Why** | The player can never verify what bots are doing, so impersonation adds flavor | The player can see everything, so false game claims are immediately exposed |

**General channel** = "theater of the mind" - bots can roleplay, exaggerate, and fabricate game events freely. The player has no way to verify any of it.

**Group channel** = "grounded game events + free personality" - bots cannot fabricate in-game actions (loot, kills, combat), but they can still have rich casual conversation, tell stories, crack jokes, and express personality.

### Group Chatter Context Scoping

Group chatter is much more tightly scoped than general channel chatter. The context sources operate at two levels:

**Level 1: Environment context** (shared with general chatter)
- Current zone or dungeon
- Weather and time of day
- Dungeon/instance atmosphere (the module must be aware of the dungeon environment and use it for chat context)

**Level 2: Close proximity context** (unique to group chatter)
- Classes and races of other bots in the group
- The real player's class, race, and equipment (bots can inspect and comment with humor)
- Loot drops happening in the group
- Mob and boss kills
- Movement toward new objectives (e.g., approaching a boss)
- Group composition observations ("nice, we have two healers")

The key difference: general channel chatter draws from broad, ambient flavor. Group chatter is tightly bound to **what is happening right now, with these specific people, in this specific place**.

---

## 1.5 Bot Personality System

### Personality Traits (3 per bot)
When a bot joins a group, they are assigned **3 random personality traits** from a pool. These traits persist for the entire group session and influence all their messages.

**Trait Pool:**

| Category | Traits |
|----------|--------|
| Social | friendly, reserved, chatty, quiet, supportive, competitive |
| Attitude | optimistic, pessimistic, sarcastic, earnest, laid-back, intense |
| Focus | loot-focused, combat-focused, exploration-focused, efficiency-focused |
| Humor | jokey, serious, dry-wit, punny, deadpan |
| Energy | enthusiastic, tired, calm, hyper, steady |

**Example Bot Assignment:**
- Thylaleath (Paladin): `[friendly, optimistic, combat-focused]`
- Milunnik (Priest): `[quiet, earnest, supportive]`

### Trait Assignment & Persistence

**Order of operations when bot joins:**
1. Bot joins group
2. **3 personality traits assigned immediately**
3. Mandatory greeting generated (influenced by traits)
4. Greeting stored in conversation log

**Lifecycle:**
- Traits persist for the entire session
- Traits are cleared when session ends (real player leaves, group disbands)
- Stored in database alongside conversation memory

### Trait Influence on LLM Prompts

Traits are passed to the LLM in every prompt for that bot:

```
Bot: Thylaleath (Human Paladin, Tank)
Personality: friendly, optimistic, combat-focused

Generate a party chat message...
```

The LLM uses these traits to shape the bot's voice:
- `[sarcastic, pessimistic]` → "oh great, another wipe incoming"
- `[friendly, optimistic]` → "we got this! nice pull"
- `[quiet, combat-focused]` → "focus skull"
- `[chatty, jokey, loot-focused]` → "ooh shiny! hope something good drops"

---

## 1.6 Mandatory Bot Greeting

**When a bot joins a group, they MUST greet.** This is not optional - it's the first impression and establishes their personality for the session.

### Greeting Reflects Personality Traits

| Traits | Greeting Examples |
|--------|-------------------|
| friendly, enthusiastic | "hey! ready to go!" / "awesome, lets do this!" |
| quiet, tired | "hey" / "sup" |
| supportive, optimistic | "hi, happy to help!" / "lets do this team" |
| sarcastic, pessimistic | "oh great, another group" / "this should be fun..." |
| chatty, friendly | "heya everyone! :)" / "hi hi!" |
| reserved, serious | "hello" / "ready when you are" |
| jokey, laid-back | "reporting for duty lol" / "sup nerds" |

The greeting is stored in the conversation log. The traits persist for all future messages from this bot.

---

## 1.7 Conversation Memory System

### Single Conversation Log
All messages (bot chat, player chat, events) are stored in a single conversation log per group. This enables:
- Bots remembering what was discussed earlier
- Coherent follow-up conversations
- Meaningful player-bot interaction

### Memory Contents

| Entry Type | Example |
|------------|---------|
| Bot message | `[Party] Thylaleath: sounds good, I can tank` |
| Player message | `[You] Karaez: lets go to deadmines` |
| Event | `* Group killed Rhahk'Zor (boss)` |

### Summarization (Token Control)
To avoid massive input tokens, conversation context is summarized before passing to LLM:
- **Recent messages (last 8)**: Kept in full detail
- **Older messages**: Condensed to topic keywords ("Events: killed boss. Discussed: combat, loot")

### Memory Cleanup Rules
Memory is **immediately deleted** when:
- Real player leaves the group
- Group is disbanded
- Real player logs out
- Group no longer qualifies (no real player + bot)

When a bot leaves, their messages stay in the log (they're part of the conversation record).

---

## 1.8 Context Sources

Use only these sources for content:
- **Group roster**: player + bots (names, classes, roles).
- **Location**: current zone/dungeon/area.
- **Recent combat**: mobs killed, wipes, pulls.
- **Boss state**: upcoming or defeated bosses (if in a dungeon/raid).
- **Loot events**: real need/greed/pass outcomes.
- **Player actions**: heals, pulls, saves, deaths, resurrections.
- **Conversation history**: what has been said so far in this session.

---

## 1.9 Player Interaction

### Real Player Can Chat With Bots
When the real player types in party chat:
1. Message is stored in the conversation log
2. Bots may respond (chance-based, with cooldowns)
3. Response is contextually aware of the conversation

### Intelligent Responder Selection
The system selects which bot should respond based on:
- Relevance to the message (healer responds to "need heals?")
- Who hasn't spoken recently
- Role appropriateness

---

## 1.10 Combat Behavior

**Principle:** Chatter should be **very rare during combat** - bots are busy fighting, not chatting.

| Situation | Chatter Behavior |
|-----------|------------------|
| Out of combat | Normal chatter rate |
| In combat (trash) | 5% chance, VERY short messages only |
| In combat (boss) | Almost never, except kill celebration |
| Pull start | Rare short quip ("lets go", "pulling") |
| Boss dies | Always trigger celebration |
| Wipe | Always trigger reaction |

### Combat Quips (max 15-20 chars)
- "lets go!"
- "incoming"
- "focus adds"
- "nice"
- "oom soon"
- "need heals"

---

## 1.11 Event Priority & Triggers

### Priority Tiers

| Priority | Event Type | Cooldown | Notes |
|----------|------------|----------|-------|
| 0 (Mandatory) | **Bot join greeting** | 0s | **ALWAYS trigger** |
| 1 | Boss kill | 0s | Always trigger |
| 2 | Wipe/group death | 60s | Per group |
| 3 | Rare spawn kill | 30s | Per creature type |
| 4 | Loot roll win | 60s | Per bot |
| 5 | Bot death | 120s | Per bot |
| 6 | Regular mob kill | 300s | Very rare (5% chance) |
| 7 (Lowest) | Ambient | 120s | Per group |

### Trigger Ideas
- **Group join**: Bot joins → mandatory greeting with personality traits
- **Loot event**: An item is looted by a bot group member
- **Mob kill**: The group kills a mob (light, quick reactions)
- **Boss kill**: Celebratory or relieved reactions
- **Bot death**: Short reactions or encouragement
- **Player speaks**: Bot may respond to real player's party chat
- **Random ambient**: Occasional light statements/conversations for immersion

---

## 1.12 Example Themes

- **Coordination**: "mark skull", "ready for next pull", "mana break"
- **Atmosphere**: "this place feels cursed", "love the music here"
- **Progress**: "halfway there", "last boss next"
- **Loot reactions**: "grats on the drop", "rip my roll"
- **Recovery**: "good save", "that was close"
- **Greeting**: "hey! ready to go", "sup, need a tank?"

---

## 1.13 Reusing Ambient Chatter Infrastructure

A large portion of the existing ambient chatter infrastructure is directly reusable for group chatter. The two systems share the same flavor sources - the only difference is that group chatter scopes its **game event references** to verifiable context.

### Shared Components

| Component | Description | Used By |
|-----------|-------------|---------|
| `ZONE_FLAVOR` (~45 zones) | Zone atmosphere descriptions | Both |
| Weather context | Current weather conditions | Both |
| Time of day | Day/night cycle awareness | Both |
| Bot race/class data | Race and class of each bot | Both |
| `MOODS` (25 moods) | Mood selection for messages | Both |
| `TONES` | Tone selection for conversations | Both |
| `CREATIVE_TWISTS` (47 twists) | Creative direction for prompts | Both |
| Statement/Conversation pattern | Same 50/50 distribution | Both |
| ChatterMode (normal/roleplay) | Prompt style and flavor | Both |
| LLM calling infrastructure | API calls, response handling | Both |
| Link conversion | Item/spell link formatting | Both |

### What's Different in Group Chatter

| Component | Description |
|-----------|-------------|
| Conversation memory | Group chatter maintains a conversation log |
| Personality traits | 3 traits per bot, persisting for the session |
| Close proximity context | Group roster, player gear, drops, kills |
| Party channel delivery | Messages sent via SayToParty() not General |
| Bot count distribution | 2 bots: 50%, 3 bots: 30%, 4 bots: 20% |
| Event-driven triggers | GroupScript/PlayerScript hooks |

### Zone Flavor for Overworld Groups
When grouped in the overworld, the existing zone flavor system provides rich atmosphere context:
- Darkshore: "A somber, twilight coastline where ancient Night Elf ruins crumble..."
- Stranglethorn Vale: "Dense, dangerous jungle teeming with hostile wildlife..."

This gives bots context to make zone-appropriate comments ("this jungle is brutal", "love the eerie vibe here").

---

## 1.14 ChatterMode Alignment

Group chatter must respect the **ChatterMode** setting (`LLMChatter.ChatterMode`), exactly like ambient chatter does. The two modes are:

| Mode | Group Chatter Style |
|------|---------------------|
| **Normal** | Casual modern gamer talk. Bots chat like real players: abbreviations, slang, humor, emotes. "lol nice pull", "oom brb", "grats on the drop" |
| **Roleplay** | In-character, lore-appropriate speech. Bots speak as their race/class would in-universe. "By the Light, a worthy foe!", "The spirits guide my blade" |

The mode affects:
- Greeting style when joining the group
- Tone and vocabulary of all messages
- How personality traits are expressed (a "jokey" bot in RP mode tells in-universe jokes, not modern memes)
- Event reactions (boss kill in normal: "nice!", in RP: "Victory is ours!")

The mode is a server-wide config setting, shared with ambient chatter. No separate config needed for group chatter.

---

## 1.15 Frequency & Timing

- Low frequency; only when something happens or at natural breaks.
- Avoid overlaps with combat spam.
- Prefer short bursts after key events (boss kill, wipe, loot roll).
- Add cooldowns per trigger type to prevent spam during busy pulls.
- Very rare during combat (short quips only), fuller lines after combat.

## 1.16 Trigger & Lifetime

- Uses a **separate group-chat timer** from ambient chatter.
- The group timer starts when a group forms that includes:
  - at least 1 real player, and
  - at least 1 bot (minimum total group size = 2).
- The group timer runs only while that condition is true.
- The group timer stops immediately when the group is disbanded or the condition no longer holds.
- **Conversation memory and personality traits are deleted** when the group session ends.

---

## 1.17 Tone Guidelines

- Keep it grounded and in-universe.
- Avoid long multi-sentence messages.
- Use names sparingly and naturally.
- Stay consistent with the conversation flow.
- Don't repeat things that were already said.

---

## 1.18 Quality & Safety Controls

- **Conversation memory**: Bots remember what was said throughout the session.
- **Memory summarization**: Older messages condensed to control token usage.
- **Memory cleanup**: Immediate deletion when session ends (no stale context).
- **Role-aware bias**: Tank leads pulls, healer comments on mana, DPS reacts to loot.
- **Personality traits**: 3 traits per bot influence all their messages.
- **Server-wide toggle**: Admin can enable/disable grouped chatter via config (`LLMChatter.GroupChatter.Enable`).
- **Player opt-out**: Allow individual players to disable grouped chatter for themselves (e.g., via chat command).

---

## 1.19 Performance & Crash Safety

- **Aggregate events** instead of reacting to every event instantly.
- **Queue minimal data** in C++; do heavier logic in Python on a timer.
- **Rate limits** at group and bot level to prevent spam.
- **Early exit** when no real player + bot group exists.
- **Backpressure**: cap queue size and drop low-priority events if full.
- **No DB queries** directly inside hot event handlers.
- **Event priority tiers** (greeting > boss kill > wipe > loot roll > mob kill > ambient).
- **Stale event expiry**: drop events older than 30–60s.
- **Group state snapshot**: cache group members/roles, update on a slow timer.
- **Single source of truth**: only one chatter generator per group.

---

## 1.20 Future Considerations

- Separate profiles for **dungeon**, **raid**, and **open-world** groups.
- Role-specific chatter (tank leads, healer cautions, DPS impatience).
- **Dungeon/raid flavor text**: Similar to `ZONE_FLAVOR` but for instances.
- Instance boss awareness (mention upcoming boss names).
- Optional opt-out for players who prefer silence.

---

# Part 2: Technical Implementation

> **⚠️ DO NOT UPDATE THIS SECTION YET**
>
> The concept in Part 1 is still being refined. Technical implementation details
> in this section may change significantly once the concept is finalized.
> Wait until Part 1 is marked as complete before updating Part 2.

---

## 2.1 Feasibility Assessment

**Feasibility: HIGH** - The grouped bot chatter feature is technically feasible with
the existing AzerothCore and mod-playerbots infrastructure.

**Estimated Complexity:** Medium-High
**Key Dependencies:** GroupScript hooks, PlayerScript hooks, existing mod-llm-chatter
infrastructure, playerbots SayToParty() API

---

## 2.2 Current State Analysis

### How Grouped Bots Are Currently Handled

The current mod-llm-chatter module **explicitly excludes** bots that are grouped with
real players from ambient chatter via `IsGroupedWithRealPlayer()` in `LLMChatterScript.cpp`:

```cpp
bool IsGroupedWithRealPlayer(Player* bot)
{
    Group* group = bot->GetGroup();
    if (!group) return false;

    for (GroupReference* itr = group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        if (Player* member = itr->GetSource())
        {
            if (member != bot && !IsPlayerBot(member))
                return true;  // Found real player = EXCLUDED
        }
    }
    return false;
}
```

**Current Logic:**
- Bots NOT in any group → Eligible for General chat chatter
- Bots in all-bot groups → Eligible for General chat chatter
- Bots grouped with real players → **EXCLUDED** from all chatter

---

## 2.3 Available Infrastructure

### AzerothCore GroupScript Hooks

| Hook | When Fired | Data Available |
|------|------------|----------------|
| `OnGroupCreate` | Group is first created | Group*, Player* leader |
| `OnGroupAddMember` | Player joins a group | Group*, ObjectGuid of new member |
| `OnGroupRemoveMember` | Player leaves/kicked | Group*, ObjectGuid, RemoveMethod, kicker, reason |
| `OnGroupChangeLeader` | Leadership transfers | Group*, new leader GUID, old leader GUID |
| `OnGroupDisband` | Group disbands | Group* |
| `OnGroupInviteMember` | Invite is sent (before accept) | Group*, ObjectGuid of invited |

### PlayerScript Hooks for Group Context

| Hook | When Fired |
|------|------------|
| `OnPlayerCreatureKill` | Player kills creature |
| `OnPlayerJustDied` | Player dies |
| `OnPlayerLootItem` | Player receives item |
| `OnPlayerGroupRollRewardItem` | Player wins roll |
| `OnPlayerEnterCombat` | Player enters combat |
| `OnPlayerLeaveCombat` | Player exits combat |

### Bot Detection

```cpp
bool isBot = player->GetSession()->IsBot();
Player* player = ObjectAccessor::FindConnectedPlayer(guid);
```

### Group Iteration

```cpp
Group* group = player->GetGroup();
if (group) {
    for (GroupReference* itr = group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        if (Player* member = itr->GetSource())
        {
            // Access member data
        }
    }
}
```

### Playerbots Party Chat API

```cpp
// Location: PlayerbotAI.cpp
void PlayerbotAI::SayToParty(const std::string& msg);
void PlayerbotAI::SayToRaid(const std::string& msg);
```

---

## 2.4 Architectural Design

### Parallel System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        mod-llm-chatter                               │
├────────────────────────────┬────────────────────────────────────────┤
│   AMBIENT CHATTER          │   GROUPED CHATTER (NEW)                │
│   (Current System)         │                                         │
├────────────────────────────┼────────────────────────────────────────┤
│ Timer: TriggerInterval     │ Timer: GroupChatterInterval (NEW)      │
│ Bots: NOT grouped w/ real  │ Bots: IN group with real player        │
│ Channel: General           │ Channel: Party                          │
│ Context: Zone, weather     │ Context: Group members, events, memory  │
│ Hooks: WorldScript::Update │ Hooks: GroupScript, PlayerScript        │
└────────────────────────────┴────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │  Shared Infrastructure │
                    │  - Database tables     │
                    │  - Python bridge       │
                    │  - LLM calling         │
                    │  - Link conversion     │
                    └──────────────────────┘
```

---

## 2.5 Database Schema

### Tables

```sql
-- Conversation history table (messages, events)
CREATE TABLE llm_group_conversation (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    group_id INT UNSIGNED NOT NULL,
    speaker_name VARCHAR(64) NOT NULL,
    speaker_type ENUM('bot', 'player', 'event') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_group_time (group_id, created_at)
);

-- Bot personality traits (3 traits per bot, persist for session)
CREATE TABLE llm_group_bot_traits (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    group_id INT UNSIGNED NOT NULL,
    bot_guid INT UNSIGNED NOT NULL,
    bot_name VARCHAR(64) NOT NULL,
    trait1 VARCHAR(32) NOT NULL,
    trait2 VARCHAR(32) NOT NULL,
    trait3 VARCHAR(32) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_group_bot (group_id, bot_guid),
    INDEX idx_group (group_id)
);
```

### Example Data

```
-- Conversation:
| group_id | speaker_name | speaker_type | content                          |
|----------|--------------|--------------|----------------------------------|
| 12345    | Karaez       | player       | lets go to deadmines             |
| 12345    | Thylaleath   | bot          | sounds good, I can tank          |
| 12345    | [Event]      | event        | Group killed Rhahk'Zor (boss)    |

-- Traits:
| group_id | bot_guid | bot_name   | trait1     | trait2     | trait3         |
|----------|----------|------------|------------|------------|----------------|
| 12345    | 1001     | Thylaleath | friendly   | optimistic | combat-focused |
| 12345    | 1002     | Milunnik   | quiet      | supportive | earnest        |
```

---

## 2.6 C++ Implementation

### GroupScript for State Tracking

```cpp
class GroupedChatterGroupScript : public GroupScript
{
public:
    GroupedChatterGroupScript() : GroupScript("GroupedChatterGroupScript") {}

    void OnGroupAddMember(Group* group, ObjectGuid guid) override
    {
        Player* player = ObjectAccessor::FindConnectedPlayer(guid);
        if (!player) return;

        if (IsQualifyingGroup(group))
        {
            if (IsPlayerBot(player))
            {
                // Bot joined - assign traits and queue greeting
                QueueBotGreeting(group, player);
            }
        }
    }

    void OnGroupRemoveMember(Group* group, ObjectGuid guid,
                             RemoveMethod method, ObjectGuid kicker,
                             const char* reason) override
    {
        Player* player = ObjectAccessor::FindConnectedPlayer(guid);
        if (!player) return;

        // Real player left - clear all session data
        if (!IsPlayerBot(player))
        {
            ClearGroupSession(group);
            return;
        }

        // Check if group still qualifies
        if (!IsQualifyingGroup(group))
            ClearGroupSession(group);
    }

    void OnGroupDisband(Group* group) override
    {
        ClearGroupSession(group);
    }

private:
    bool IsQualifyingGroup(Group* group)
    {
        bool hasReal = false, hasBot = false;
        for (auto* itr = group->GetFirstMember(); itr; itr = itr->next())
        {
            if (Player* p = itr->GetSource())
            {
                if (IsPlayerBot(p)) hasBot = true;
                else hasReal = true;
            }
        }
        return hasReal && hasBot;
    }

    void ClearGroupSession(Group* group)
    {
        uint32 groupId = group->GetGUID().GetCounter();
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_conversation WHERE group_id = {}", groupId);
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_bot_traits WHERE group_id = {}", groupId);
    }
};
```

### PlayerScript for Event Detection

```cpp
class GroupedChatterPlayerScript : public PlayerScript
{
public:
    void OnPlayerCreatureKill(Player* killer, Creature* killed) override
    {
        Group* group = killer->GetGroup();
        if (!group || !IsQualifyingGroup(group)) return;

        if (ShouldReactToKill(killed))
            QueueGroupEvent(group, "creature_kill", killed);
    }

    void OnPlayerJustDied(Player* player) override
    {
        Group* group = player->GetGroup();
        if (!group || !IsQualifyingGroup(group)) return;

        if (IsPlayerBot(player))
            QueueGroupEvent(group, "bot_death", player);
    }

    void OnChat(Player* player, uint32 type, uint32 lang,
                std::string& msg, Group* group) override
    {
        if (type != CHAT_MSG_PARTY && type != CHAT_MSG_RAID)
            return;

        if (IsPlayerBot(player) || !group || !IsQualifyingGroup(group))
            return;

        // Store player message and maybe trigger response
        StorePlayerMessageInMemory(group, player, msg);
        if (ShouldBotRespondToPlayer(msg))
            QueuePlayerInteractionEvent(group, player, msg);
    }
};
```

---

## 2.7 Python Implementation

### Personality Trait System

```python
PERSONALITY_TRAITS = {
    'social': ['friendly', 'reserved', 'chatty', 'quiet', 'supportive', 'competitive'],
    'attitude': ['optimistic', 'pessimistic', 'sarcastic', 'earnest', 'laid-back', 'intense'],
    'focus': ['loot-focused', 'combat-focused', 'exploration-focused', 'efficiency-focused'],
    'humor': ['jokey', 'serious', 'dry-wit', 'punny', 'deadpan'],
    'energy': ['enthusiastic', 'tired', 'calm', 'hyper', 'steady']
}

def assign_bot_traits(group_id, bot_guid, bot_name):
    """Assign 3 random personality traits to a bot when they join."""
    categories = random.sample(list(PERSONALITY_TRAITS.keys()), 3)
    traits = [random.choice(PERSONALITY_TRAITS[cat]) for cat in categories]

    cursor.execute("""
        INSERT INTO llm_group_bot_traits
        (group_id, bot_guid, bot_name, trait1, trait2, trait3)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        trait1 = VALUES(trait1), trait2 = VALUES(trait2), trait3 = VALUES(trait3)
    """, (group_id, bot_guid, bot_name, traits[0], traits[1], traits[2]))

    return traits
```

### Bot Greeting with Traits

```python
def on_bot_join_group(group_id, bot_guid, bot_name, bot_class, bot_race, group_context):
    """Called when a bot joins a group with a real player."""
    # Step 1: Assign 3 personality traits immediately
    traits = assign_bot_traits(group_id, bot_guid, bot_name)

    # Step 2: Generate greeting influenced by traits
    greeting_prompt = build_bot_greeting_prompt(
        bot_name, bot_class, bot_race, traits, group_context
    )

    return greeting_prompt, traits


def build_bot_greeting_prompt(bot_name, bot_class, bot_race, traits, group_context):
    """Build prompt for mandatory greeting when bot joins group."""
    real_player = [m for m in group_context['members'] if not m['is_bot']][0]
    traits_str = ", ".join(traits)

    prompt = f"""A bot just joined a WoW party. Generate their greeting.

Bot: {bot_name} ({bot_race} {bot_class})
Personality: {traits_str}
Joined group led by: {real_player['name']}

Generate ONE short greeting (under 40 chars). The personality traits affect the style.
Just the greeting, nothing else.
"""
    return prompt
```

### Conversation Context

```python
RECENT_MESSAGES_FULL = 8
MAX_OLDER_SUMMARY_CHARS = 300

def get_conversation_context(group_id):
    """Get conversation history, summarized to control token usage."""
    cursor.execute("""
        SELECT speaker_name, speaker_type, content, created_at
        FROM llm_group_conversation
        WHERE group_id = %s
        ORDER BY created_at DESC
    """, (group_id,))
    all_messages = cursor.fetchall()

    if not all_messages:
        return ""

    recent = all_messages[:RECENT_MESSAGES_FULL][::-1]
    older = all_messages[RECENT_MESSAGES_FULL:][::-1]

    context_parts = []

    if older:
        summary = summarize_older_messages(older)
        context_parts.append(f"Earlier: {summary}")

    if recent:
        context_parts.append("Recent conversation:")
        for speaker, speaker_type, content, _ in recent:
            if speaker_type == 'event':
                context_parts.append(f"  * {content}")
            elif speaker_type == 'player':
                context_parts.append(f"  [You] {speaker}: {content}")
            else:
                context_parts.append(f"  [Party] {speaker}: {content}")

    return "\n".join(context_parts)
```

---

## 2.8 Message Delivery

```cpp
void DeliverGroupMessage(const std::string& message, Player* bot,
                         const std::string& channel)
{
    PlayerbotAI* ai = GET_PLAYERBOT_AI(bot);
    if (!ai) return;

    std::string processed = ConvertAllLinks(message);

    if (channel == "party")
        ai->SayToParty(processed);
    else if (channel == "raid")
        ai->SayToRaid(processed);
    else
        ai->SayToChannel(processed, ChatChannelId::GENERAL);
}
```

---

## 2.9 Session Cleanup

| Trigger | Action | Tables Affected |
|---------|--------|-----------------|
| Real player leaves group | DELETE all | `llm_group_conversation` + `llm_group_bot_traits` |
| Group disbands | DELETE all | `llm_group_conversation` + `llm_group_bot_traits` |
| Real player logs out | DELETE all | `llm_group_conversation` + `llm_group_bot_traits` |
| Group no longer qualifies | DELETE all | `llm_group_conversation` + `llm_group_bot_traits` |
| Session idle > 30 min | Optional cleanup | Both tables |

---

## 2.10 Configuration

```ini
# Group Chatter Settings
LLMChatter.GroupChatter.Enable = 1
LLMChatter.GroupChatter.AmbientIntervalSeconds = 120
LLMChatter.GroupChatter.AmbientChance = 40

# Event Reactions
LLMChatter.GroupChatter.Events.BossKill = 1
LLMChatter.GroupChatter.Events.RareKill = 1
LLMChatter.GroupChatter.Events.BotDeath = 1
LLMChatter.GroupChatter.Events.LootWin = 1
LLMChatter.GroupChatter.Events.BotJoin = 1

# Cooldowns
LLMChatter.GroupChatter.Cooldown.Ambient = 120
LLMChatter.GroupChatter.Cooldown.EventReaction = 30
LLMChatter.GroupChatter.Cooldown.BotSpeak = 60

# Combat Behavior
LLMChatter.GroupChatter.CombatChatterChance = 5
LLMChatter.GroupChatter.CombatMaxMessageLength = 20

# Conversation Context
LLMChatter.GroupChatter.RecentMessagesKept = 8
LLMChatter.GroupChatter.MaxOlderSummaryChars = 300
LLMChatter.GroupChatter.IdleCleanupMinutes = 30

# Player Interaction
LLMChatter.GroupChatter.PlayerInteraction.Enable = 1
LLMChatter.GroupChatter.PlayerInteraction.ResponseChance = 60
LLMChatter.GroupChatter.PlayerInteraction.Cooldown = 10
```

---

## 2.11 Implementation Phases

### Phase 1: Foundation
- [ ] Add GroupScript hooks for group state tracking
- [ ] Create group qualification checking with caching
- [ ] Create database tables (`llm_group_conversation`, `llm_group_bot_traits`)
- [ ] Add party channel delivery routing
- [ ] Implement session cleanup triggers
- [ ] Build conversation context retrieval with summarization

### Phase 2: Basic Events
- [ ] Implement **mandatory** bot join greeting with personality traits
- [ ] Implement boss kill reactions
- [ ] Implement bot death reactions
- [ ] Store events in conversation log
- [ ] Add cooldown system

### Phase 3: Loot Integration
- [ ] Track loot roll events
- [ ] Implement loot win reactions
- [ ] Add item quality awareness

### Phase 4: Player Interaction
- [ ] Hook into party chat to detect real player messages
- [ ] Store player messages in conversation log
- [ ] Implement bot response to player messages
- [ ] Add intelligent responder selection
- [ ] Add response cooldowns

### Phase 5: Ambient Group Chatter
- [ ] Implement group chatter timer
- [ ] Build group-aware prompts with conversation context
- [ ] Add role-based chatter bias

### Phase 6: Polish
- [ ] Combat quiet mode
- [ ] Event aggregation
- [ ] Dungeon/raid specific context
- [ ] Idle conversation cleanup

---

## 2.12 Estimated Effort

- **C++ GroupScript + PlayerScript:** 2-3 days
- **Database schema:** 0.5 days
- **Conversation context + summarization:** 1-2 days
- **Python bridge extensions:** 2-3 days
- **Player interaction hooks:** 1-2 days
- **Testing and tuning:** 2-3 days
- **Total:** ~9-14 days for full implementation

---

## Appendix A: Key File References

### AzerothCore Core
- `src/server/game/Scripting/ScriptDefines/GroupScript.h`
- `src/server/game/Groups/Group.h`
- `src/server/game/Scripting/ScriptDefines/PlayerScript.h`
- `src/server/game/Server/WorldSession.h`

### mod-llm-chatter
- `modules/mod-llm-chatter/src/LLMChatterScript.cpp`
- `modules/mod-llm-chatter/tools/llm_chatter_bridge.py`

### mod-playerbots
- `modules/mod-playerbots/src/Bot/PlayerbotAI.cpp`
- `modules/mod-playerbots/src/Ai/Base/Value/GroupValues.cpp`

---

## Appendix B: Example Event Flow

**Scenario:** Bot "Thylaleath" joins group and wins loot

```
1. [Bot joins group]
   ├── OnGroupAddMember fires
   ├── assign_bot_traits() → [friendly, optimistic, combat-focused]
   ├── build_bot_greeting_prompt() with traits
   └── Bot says: "hey! ready to go!"

2. [Group kills boss]
   ├── OnPlayerCreatureKill fires
   ├── Store event: "Group killed Rhahk'Zor (boss)"
   └── Bot says: "nice! first boss down"

3. [Bot wins loot roll]
   ├── OnPlayerGroupRollRewardItem fires
   ├── Store event: "Thylaleath won Staff of Jordan"
   ├── Other bot responds with traits [quiet, supportive]
   └── Milunnik says: "grats"

4. [Real player leaves]
   ├── OnGroupRemoveMember fires
   ├── DELETE FROM llm_group_conversation WHERE group_id = X
   └── DELETE FROM llm_group_bot_traits WHERE group_id = X
```
