# Chatter Mode: Normal vs Roleplay

## The Config Toggle

```ini
LLMChatter.ChatterMode = normal    # casual MMO chat (default)
LLMChatter.ChatterMode = roleplay  # fully in-character RP speech
```

Change it, restart the bridge, and all bot chatter switches style. Everything else (timing, rate limits, events, links) stays the same.

---

## What Changes Between Modes

### Normal Mode

Bots sound like real MMO players - casual, abbreviated, sometimes sarcastic. They use game terms freely and talk like they're behind a keyboard.

```
[Pelrith]: just finished that quest chain and it felt so good!
[Kerrandiir]: we handled it flawlessly yesterday, not to flex lol
[Eveline]: yeah decent rewards too, got a nice green out of it
```

**Personality style:**
- Abbreviations OK ("lol", "imo", "ngl", "tbh")
- Game terms OK ("aggro", "proc", "AoE", "DPS")
- Can reference real-world stuff ("just got back from dinner", "my UI is bugged")
- May include typos or lazy grammar
- Bots do NOT mention their own race or class (breaks immersion)

### Roleplay Mode

Bots speak as their character would - a Night Elf Druid talks differently than an Orc Warrior. Their race and class color everything they say.

```
[Thornbeard]: By the Light, these lands bear the scars of old wars.
[Miralynn]: The spirits whisper of things long buried here.
[Grukash]: Bah. Let the dead rest. We have work to do, not riddles.
```

**Personality style:**
- Fully in-character at all times
- No game terms, no abbreviations, no OOC references
- Race shapes their speech (Orcs are blunt, Elves are formal, Undead are dark)
- Class influences their perspective (Paladins talk about duty, Rogues are pragmatic)
- Speech can be slightly longer and more expressive
- Bots stay in character even when discussing quests and loot

---

## How Personality Works in RP Mode

Each bot gets a personality built from two layers:

### Race Personality

Each of the 10 races has speech traits and flavor words:

| Race | Traits | Flavor Words |
|------|--------|-------------|
| Human | practical, earnest | "Light", "by the Alliance", "honor" |
| Orc | blunt, proud, values strength | "Lok'tar", "blood and thunder" |
| Night Elf | ancient, melancholic, nature-reverent | "Elune", "ancient", "balance" |
| Undead | darkly humorous, detached | "Darkness", "the grave", "freedom" |
| Dwarf | hearty, stubborn, loves ale | "By me beard", "the forge" |
| Gnome | clever, curious, tinkering | "Fascinating", "hypothesis" |
| Tauren | calm, spiritual, nature-bound | "Earth Mother", "the winds" |
| Troll | laid-back, superstitious | "Mon", "da spirits", "voodoo" |
| Blood Elf | proud, refined, magic-obsessed | "Sin'dorei", "the Sunwell" |
| Draenei | wise, devout, slightly alien | "The Light", "the Naaru" |

### Class Modifier

The bot's class adds another layer on top of race:

| Class | Speech Influence |
|-------|-----------------|
| Warrior | direct, values courage and combat |
| Paladin | righteous, speaks of duty and the Light |
| Hunter | observant, references tracking and beasts |
| Rogue | cautious, streetwise, pragmatic |
| Priest | compassionate, speaks of faith and healing |
| Shaman | speaks of spirits, elements, and balance |
| Mage | intellectual, references arcane knowledge |
| Warlock | brooding, dark humor, power-focused |
| Druid | nature-focused, speaks of cycles and growth |
| Death Knight | grim, haunted, references undeath |

So a **Tauren Shaman** would speak calmly about spirits and the Earth Mother, while an **Undead Warlock** would be darkly humorous and power-obsessed.

---

## What the LLM Receives Differently

Both modes send the same zone data, quest info, item info, and weather context. The difference is in the **creative direction** the LLM gets.

### The Prompt Ingredients

Each message is built from randomized ingredients. The mode determines which pool they're drawn from:

| Ingredient | Normal Pool | RP Pool |
|-----------|------------|---------|
| **Tone** | "casual and relaxed", "a bit bored", "just vibing" | "reverent and thoughtful", "weary from the road", "wary and alert" |
| **Mood** | "sarcastic", "showing off", "distracted" | "solemn", "fierce", "contemplative", "devout" |
| **Category** | "lfg", "mentioning bag space", "referencing AFK" | "greeting a fellow traveler formally", "noting the state of the land" |
| **Creative Twist** | "Use ALL CAPS for emphasis", "Reference a UI element" | "Use a proverb from your culture", "Reference a deity or spirit" |
| **Length Hint** | "very short (3-7 words)" | "brief but evocative (5-10 words)" |

### The Guidelines

Normal mode guidelines tell the LLM to "sound like a real player" with optional typos and abbreviations.

RP mode guidelines tell the LLM to "speak fully in-character" and forbid game terms, abbreviations, and out-of-character references. It also adds the race/class personality context described above.

---

## What Stays the Same in Both Modes

- Quest and item links still work identically (`{quest:Name}` / `{item:Name}`)
- Message type distribution unchanged (65% plain, 15% quest, 12% loot, 8% quest+reward)
- Conversation vs statement split unchanged (50/50)
- All rate limiting, cooldowns, and timing unchanged
- Weather and transport events unchanged
- Bot selection logic unchanged
- Zone flavor context unchanged

---

## Switching Modes

1. Edit `mod_llm_chatter.conf`: change `LLMChatter.ChatterMode` to `normal` or `roleplay`
2. Restart the bridge: `docker restart ac-llm-chatter-bridge`
3. New chatter will use the new mode immediately

No compilation needed. No database changes. Just a config change and bridge restart.
