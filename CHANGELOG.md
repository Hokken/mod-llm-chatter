# Changelog

### 2026-09-26 - Open-World PvP, Duels, and Nearby Onlookers

* **Party PvP reactions**: Companions react to opposing-faction players
  and their pets during open-world combat, kills, deaths, wipes, spells,
  and state callouts. Enemy context includes visible identity, level
  differences, and who started the fight; hidden enemies stay anonymous.
  PvP reactions use their own chances and cooldowns and bypass
  creature-oriented cached lines. Battlegrounds and arenas keep their
  existing chatter paths.
* **Group duel reactions**: Bot duellists and group spectators react to
  duel starts and results, including wins, fleeing, and interruptions.
  Declined challenges and cancelled countdowns do not produce group
  result reactions.
* **Nearby onlookers**: Bots outside the fight and the player's group can
  react before, during, or after a duel, or after an open-world PvP kill.
  Each selected moment uses one statement or a 2–3-bot conversation.
  Same-faction onlookers speak in `/say`; opposite-faction onlookers use
  emotes. Visibility checks, shared proximity cooldowns, zone fatigue,
  and delivery-time scene checks limit repetition and stale reactions.
* **Configuration**: Added `GroupChatter.PvP.*`, `GroupChatter.Duel.*`,
  and `ProximityChatter.FightReactions.*` settings, including conservative
  onlooker chances and quieter-preset values.
* **Upgrade**: Apply
  `data/sql/characters/updates/20260926_duel_events.sql` to the character
  database for the two new group-duel event types. Proximity onlookers
  reuse existing events and require no additional migration. Rebuild the
  server and restart the chatter bridge to load the new handlers.

### 2026-09-22 - Addon Profile Edits, Custom Emotes, and Action Delivery Fixes

* **Profile edits are atomic**: `.llmc set`, `setbackstory` and chunked
  `commit` write every part of an edit (identity, session traits, cache
  invalidation, optional backstory) in one database transaction, together
  with the tone/backstory regeneration jobs, so a player disconnecting
  mid-save can no longer leave a cleared profile with nothing queued to
  refill it. `UPDATED` / `PROFILE` responses are sent only after the commit
  succeeds; a failed write answers `ERROR save` and leaves the bot untouched.
* **Addon contract**: The docs now state that Chatter Companion uploads
  traits only; `setbackstory` and `bs` chunks remain a server-side path.
* **Observer fallback keeps custom emote text**: When a custom emote is
  aimed at an ungrouped playerbot and the direct route is unavailable,
  grouped observers now react to the typed action instead of `/wave`.
* **Emoji survive the chat line**: The 3.3.5 client replaces `%f` in
  outgoing chat with the focus name, which mangled the `%F0` lead byte of
  every 4-byte UTF-8 character. Chatter Companion now sends bytes
  `0xF0`–`0xFF` as `~FX`, and `PercentDecode()` accepts that form.
* **Larger upload capacity**: Chunked uploads accept up to 64 chunks per
  field, enough for any valid 1,000-character Unicode backstory.
* **Custom emotes at ungrouped playerbots**: The typed action (for example
  "slowly sheathes her sword") now reaches the proximity reaction instead of
  falling back to `/wave`.
* **Party action ordering**: The action emote is shown only after the bot's
  group is confirmed, so it can no longer appear ahead of speech that failed
  to send.
* **`CustomMaxChars` counts characters**: Non-ASCII emotes are no longer cut
  below the configured length.
* **Log Viewer stays responsive**: `chatter_log_viewer.py` now serves
  requests on threads, so one idle browser connection can no longer hang the
  viewer on port 5555.

### 2026-09-22 - Player-Initiated Chat Responsiveness

* **Required conversational replies**: Shared semantic intent analysis now
  reports whether player speech requires an answer. Questions and other
  answer-seeking messages always continue to response generation, while the
  LLM may still identify brief casual statements that need no reply without
  relying on phrase lists or punctuation matching.
* **Faster player-facing pacing**: Player-authored General messages now use
  full reply and reaction chances with no channel cooldown. Party, Guild, and
  directed proximity cooldowns are substantially shorter, while natural
  response delays remain so replies feel conversational rather than
  instantaneous.
* **Same-faction response routing**: General, Party, Guild, Guild login, and
  proximity reply paths now constrain eligible Playerbots to the player's
  faction. General history and relay context are faction-scoped as well, and
  final delivery rejects confirmed team mismatches without discarding valid
  replies when a player is briefly unavailable during a map transition.

### 2026-09-20 - Party Player Replies

* **Party replies no longer use optional silence**: Player-authored Party
  messages always continue to response generation once queued. Brief casual
  classification still keeps lightweight replies concise, while the optional
  silence chance remains available for Guild, General, proximity speech, and
  directed boss speech. If two generated brief replies exceed the output
  contract, Party uses a deterministic per-speaker bounded fallback instead
  of dropping the statement or conversation. Casual multi-addressee messages
  therefore retain every selected responder.

### 2026-09-20 - Configurable Player-Chat Prefix Filtering

* **Early visible-chat filtering**: Server owners can configure a
  comma-separated `LLMChatter.PlayerChat.IgnoredPrefixes` denylist for real
  player messages in Party, General, Guild, and `/say`. Matching ignores
  leading whitespace and ASCII letter case, and matched messages are skipped
  before Chatter writes history, changes conversation state or cooldowns,
  cancels Guild login greetings, or queues LLM work. The player's normal game
  chat remains unaffected.
* **Reload-safe and compatibility-preserving**: The default-empty list is
  published through the module's reload-safe configuration pattern and can be
  changed with `.reload config`. Existing `LANG_ADDON`, hidden-payload, and
  Playerbot-command protections remain independent. Documentation clarifies
  that normal `SendAddonMessage` prefixes do not belong in this list and that
  configured entries are trimmed, so distinctive punctuation-bearing
  prefixes are recommended.

### 2026-09-20 - Contextual Short Player Replies

* **Conversational scale matching**: Guild, General, party,
  proximity-speech, and proximity-emote prompts now answer brief casual
  player input in kind instead of expanding it into prose or a new topic.
  Semantically classified player-speech turns use one responder by default, a
  hard 2-8-word / 50-character contract, and one strict rewrite attempt if
  generation exceeds it. Directed player-emote prompts request the same short
  scale without adding a second semantic/RNG gate. Guild may use a tiny
  narrator action; nearby party/proximity reactions may use a real emote
  without an empty chat line.
* **Implicit reply routing**: Shared semantic intent analysis can resolve an
  unnamed reply to the immediately prior bot from recent chat context. Brief
  single-addressee Guild continuations stay with that speaker and suppress
  multi-bot, callback, name, and follow-up-question embellishments without a
  hardcoded phrase list.
* **Natural conversational silence**: The same semantic analysis can mark a
  brief casual turn as safe to leave unanswered. Guild, General, party, and
  proximity speech then make one configurable RNG roll, replying only 20% of
  the time by default and skipping generation otherwise. Questions, requests,
  warnings, and other turns that clearly expect a response bypass this gate.
* **Safe emote-only delivery**: Empty-text reactions are accepted only for
  semantically brief player speech or explicit player-emote events. Unknown
  emotes are dropped instead of retrying forever, `rofl` has a matching C++
  mapping, and party emotes retain battleground combat-emote restrictions.

### 2026-09-19 - Real General Loot and Trade Items

* **Real loot announcements**: General-channel loot chatter now comes from
  successful playerbot loot events instead of database-simulated drops. The
  bounded collector samples one item per loot source, limits announcements to
  zones with a same-team real-player audience, and defaults to uncommon or
  better items.
* **Real trade offers**: Ambient trade chatter now snapshots a tradable item
  from the selected bot's live backpack and equipped bags only when trade is
  chosen. Messages therefore reflect the item's current stack count, while a
  configurable quality bonus makes rarer eligible items more likely without
  excluding common items.
* **Safe queue contract**: C++ now selects the ambient message type and sends
  value-only item context through the chatter queue. The worker-thread loot
  path avoids database, session, channel, and random-bot-manager access; the
  world-thread flush performs authoritative eligibility and cooldown checks.
  The character-database migration adds the queue fields required by this
  contract, and the obsolete simulated-loot path has been removed.

### 2026-09-18 - Directed Playerbot Proximity Reactions

* **Ungrouped playerbot responses**: Eligible same-team playerbots outside the
  player's group can mirror directed emotes, answer them in local `/say`, and
  participate with nearby NPCs or other ungrouped bots in one shared scene.
  If the addressed bot stays silent, a separately gated witness scene may
  still let one or two nearby entities comment on the same real player action.
  Mounted playerbots remain eligible for these direct and responsive paths,
  while automatic and untargeted selection continues to exclude them at
  queue and delivery time. Delayed bot mirrors are revalidated for combat,
  player presence, map, and range before the packet is sent. The shared
  delayed event means grouped mirrors now use the same map/range safety rule,
  with a one-yard minimum radius; grouped speech remains unchanged.
* **Consistent reaction probabilities**: Distributed defaults are now 80% for
  direct emote mirroring and speech, and 50% for observer or silent-target
  witness scenes. Grouped-bot mirroring and speech are independent, including
  speech for emotes without a mirror animation mapping.
* **Bounded directed scenes**: Directed interactions now involve at most the
  addressed entity plus two joiners. Ordinary joiner counts use 60/30/10 for
  zero, one, or two joiners; witness-only scenes use 70/30 for one or two.
  This changes the defaults of `MirrorChance`, `ReactionChance`,
  `ObserverChance`, `DirectedMaxExtraReactors`, and
  `DirectedExtraReactorWeights`; explicitly configured installations retain
  their configured values.

### 2026-09-15 - Multidirectional NPC Interactions

* **Reliable direct NPC replies**: Eligible ordinary NPCs now receive a
  directed `/say` attempt when selected or unambiguously addressed by name.
  Vocative punctuation resolves explicit overrides without allowing casual
  name mentions to steal another selected NPC's reply. Direct interaction
  remains available while the player is mounted.
* **Nearby NPC participation**: Directed `/say` and emote interactions can
  select zero to three additional eligible NPCs using configurable descending
  weights. Conversations support player-inclusive reactions and NPC asides,
  require the addressed NPC to speak first, and never generate dialogue for
  the real player.
* **Verbal emote reactions**: Eligible NPCs have a configurable 80% chance to
  speak after a directed social emote, independently of their mirrored
  animation. SmartAI and known C++ emote handlers suppress duplicate chatter,
  and synchronized cooldown state keeps map-thread emotes safe.
* **Responsive interaction timing**: Directed work uses high priority and a
  short configurable expiry. Direct ordinary-NPC `/say` has no reply cooldown,
  while entity reuse, verbal emotes, and directed boss replies are
  configurable and capped at three seconds.
* **Context and delivery integrity**: Recent player lines, directed emotes,
  and successfully delivered NPC speech are scoped to the addressed NPC.
  Per-line addressee identifiers support NPC-to-player and NPC-to-NPC facing;
  unsafe scripted movement is never rotated. Directed delivery revalidation
  failures record a drop reason and cancel later lines in the affected scene.
* **Configuration and upgrade path**: The main template, quieter preset, and
  contributor documentation expose the new reaction, participant, timing,
  naming, and exclusion controls. Existing installations must apply
  `data/sql/characters/updates/20260914_npc_multidirectional_interactions.sql`
  before running the updated worldserver or bridge; fresh installs receive the
  matching base schema.

### 2026-09-14 - Model Compatibility and Provider Switching

* **Model-aware requests**: OpenAI-compatible calls now select the safe
  token-limit, temperature, and reasoning parameters for the configured
  provider and model. Explicit provider rejections receive narrowly scoped
  retries whose successful corrections are cached for the bridge process.
* **Reasoning-safe budgets**: Direct OpenAI reasoning models can use the new
  `LLMChatter.OpenAI.MaxTokensMultiplier`. Hidden reasoning receives a larger
  completion budget while models running with supported `none` effort retain
  the original low-cost limit.
* **Consistent call paths**: Normal chatter, quick analysis, startup health
  checks, screenshot vision, and offline lore generation use the shared
  compatibility layer. Fine-tuned OpenAI IDs inherit their base-model profile.
* **Portable providers**: Setup and configuration guidance now covers direct
  Anthropic, OpenAI, Google Gemini, OpenRouter, and local Ollama targets with
  explicit model-ID and parameter formats.
* **Ollama corrections**: Removed the ineffective per-request context option.
  Context is configured on the Ollama server, while thinking can be disabled
  through `reasoning_effort = none` with `/no_think` retained as a fallback.

### 2026-09-14 - Rejoin Farewell Reliability

* **Farewells survive bridge restarts**: Bots that silently rejoin an existing
  group session now prepare their farewell state even though their visible
  greeting remains suppressed. Removing those bots therefore still produces
  their expected farewell message after a bridge restart.
* **Single and batch coverage**: Regression tests protect both individual and
  batched rejoin paths without introducing duplicate greetings.

### 2026-09-13 - Existing-Install Spell DBC Repair

* **Legacy override cleanup**: Added an idempotent world-database
  migration that removes incomplete rank-one talent `spell_dbc` rows
  created by chatter versions before April 9, 2026. These placeholder
  overrides could hide the real client spell effects and trigger broad
  SpellScript validation warnings during worldserver startup.
* **Custom overrides preserved**: Cleanup requires the legacy
  all-default gameplay-field signature, so complete overrides supplied
  by other modules or administrators are retained.
* **Upgrade guidance**: Existing affected installations must apply
  `data/sql/world/updates/20260913_remove_legacy_spell_dbc_placeholders.sql`
  and restart worldserver. Fresh installations are unaffected.

### 2026-09-09 - Bots Know Their Own Gear and Pet

* **Equipped weapons reach the prompt**: a bot's identity line now names
  what it is actually holding, such as `Fist of Reckoning (one-handed
  mace), Zulian Defender (shield), Libram of Fervor (libram)`. The model
  previously had only race, class, and level, so a bot swinging a mace
  would happily talk about its sword. Main hand, off hand, and ranged
  slots are covered, including shields, held items, and class relics.
* **Hunters and warlocks know their companion**: the pet at the bot's side
  is introduced by name and species, as in `Kreenum, a Felhunter` (`an Imp`,
  not `a Imp`, for vowel-starting species), so bots stop treating their own
  pet as a stranger. Only the pet actually summoned counts — AzerothCore
  records that as slot 0, `PET_SAVE_AS_CURRENT` — so a hunter whose animals
  are all stabled or dismissed is described alone rather than talking to a
  companion that is not there. Only pet classes are looked up, and a pet
  named after its species reads as `Sporebat` rather than the doubled
  `Sporebat, a Sporebat`.
* **Reaches every conversation shape**: a bot speaking alone gets the
  second-person `You are wielding ...` / `Your pet is ...` phrasing, while
  a bot introduced inside a multi-speaker scene — idle party chatter, the
  nearby-object, player-message and quest conversations, and the ambient
  and world-event conversations — gets the third-person `Veliana wields
  Staff of the Sun (staff)` instead, so gear is never misattributed to
  whoever the model is currently speaking as. `attach_speaker_gear` fills
  every speaker in a bot list and `append_speaker_gear` places the line
  directly under its own speaker.
* **Cached per bot**: equipment is read from the character database and
  held for five minutes, so the cost is one small query every few minutes
  rather than one per message; gear swapped in game can take that long to
  show up in prompts. The pet is cached for one minute instead, because
  whether one is out is something a hunter changes mid-play.
* Controlled by `LLMChatter.GearContext.Enable` (default on).
* **Regression coverage**: focused tests protect weapon and relic naming,
  pet deduplication, the summoned-versus-stabled distinction, the pet-class
  gate, the config switch, the identity line itself, third-person
  rendering, the article rule, speakers skipped
  when a name or guid is missing, and gear-line ordering within a
  multi-speaker block. `manual_gear_prompt_check.py` prints a real speaker
  block from the live database for eyeball checks.

### 2026-09-09 - Emote Reactions Know the Room

* **Party roster in emote prompts**: a bot reacting to `/point` or to a
  typed `/e grabs hand` is now told who else is in the party, with the
  human marked as `(player)`. Bots previously answered emotes as though
  they were standing alone.
* **Recent chat history included**: emote prompts now carry the same
  recent party chat the dialogue prompts already used, so a gesture can
  be connected to what was just said instead of being read as an isolated
  event.
* **The target is described, not just named**: when a player emotes at
  someone outside the group, the observing bot is told who that is —
  `Soza, a level 28 female Troll Warrior` rather than `Soza, a stranger
  outside the group`. `HandleEmoteObserver` now receives the target player
  and sends race, class, level, and gender in the payload, so this one
  needs a recompile.
* **Regression coverage**: focused tests cover roster and history
  assembly, the target description, and the fallback used when the target
  is unknown.

### 2026-09-09 - General Channel Pacing

* **Cross-source conversation spacing**: Automated ambient, transport,
  weather, holiday, and minor-event General chatter now shares one
  per-zone delivery timeline. Multi-line exchanges reserve their full
  scheduled window, preventing independently generated follow-ups from
  arriving in a wall while keeping player-directed replies responsive.
* **Quieter production preset**: Added
  `conf/presets/mod_ll_chatter_quieter.conf.dist` as an optional lower-volume
  configuration. It preserves contextual combat and instance reactions while
  reducing cumulative ambient chatter. Credentials and local diagnostic
  settings are intentionally excluded or disabled.

### 2026-09-08 - Instance Proximity Chatter

* **Dungeon and raid parity**: Ordinary proximity chatter now runs in
  eligible dungeon and raid maps with canonical map/current-area data
  and the existing curated dungeon context supplied to every prompt.
* **Hostile humanoid voices**: Safe, out-of-combat hostile humanoids
  can participate or answer a selected/named player `/say`. Disposition,
  creature rank, LOS, participant compatibility, and delivery-time
  eligibility checks keep the result grounded without changing faction
  or combat behavior.
* **Curated non-humanoid voices**: Interactive guards, quest givers,
  vendors, trainers, innkeepers, and flight masters can qualify before
  creature-type filtering, while arbitrary non-humanoids require an
  explicit creature-entry allowlist. A separate denylist always wins;
  bosses and universal combat safety exclusions remain intact. Movement
  never excludes an otherwise eligible speaker; moving or pathing
  creatures simply skip optional facing during delivery.
  Prompts receive creature type and the reason each NPC qualified.
  Non-selectable, fake-dead, undetectable, trigger, `[DND]`, `[PH]`, and
  `[UNUSED]` internal helpers are rejected, preventing invisible event
  targets such as Valentine vial bunnies from leaking into ambient
  dialogue. Nearby-name prompt context now deduplicates repeated names,
  and one conversation cannot select ambiguous same-name speakers.
* **Instance isolation and direction**: Cooldowns, active scenes, and
  reply history include map and instance identity. Explicit names and
  selected targets take priority over recent-scene or nearby fallbacks.
* **Environment-specific pacing**: Ordinary proximity scans and trigger
  chances can now be tuned independently for outdoor maps and
  dungeons/raids. Existing installations without the scoped keys inherit
  their legacy global values, while the distributed instance chance is
  intentionally higher because combat and movement remove opportunities.
* **Pre-aggro boss moments**: A separate boss-only subsystem can emit
  a short, paced sequence of original approach lines or answer a
  directed `/say` through monster yell. A shared per-boss-instance
  presence session combines randomized delays, decaying repeat chances,
  a persistent low-probability floor, and recent-line prompt history so
  encounters feel less mechanical without becoming noisy. Automatic
  opportunities are open-ended by default rather than stopping after
  three lines; an explicit toggle can restore a configurable hard cap.
  Directed replies postpone the next automatic opportunity. The path
  requires the player to remain beyond calculated aggro range plus a
  configurable safety margin
  (zero by default so compact rooms retain a usable pre-pull band),
  revalidates before delivery, never changes boss facing or threat, and
  supports a creature-entry denylist. Per-player scans use a fair
  round-robin schedule that caps expensive creature-grid work in
  populated raids.
* **Shared contracts and coverage**: Group kill reactions and proximity
  now use one comprehensive boss classifier seeded from AzerothCore's
  registered dungeon/raid encounters, with metadata fallbacks for special
  bosses. This includes ordinary-rank encounter minibosses such as
  Rethilgore without misclassifying every elite. Enter-combat reactions
  preserve their established narrower classification and probabilities.
  Eligible registered-encounter kills use the established guaranteed boss-
  kill reaction path rather than normal-trash chance and cooldown rules.
  Focused tests protect instance context, NPC metadata, history isolation,
  boss prompt constraints, fail-closed safety data, registry routing, and
  boss delivery ownership.
* **Database migration**: Existing installations must apply
  `data/sql/characters/updates/20260908_instance_proximity_boss_events.sql`
  so the event queue accepts the two new boss event types. Fresh installs
  receive them from the base schema.

### 2026-09-07 - Normal Player Chat Mode

* **Player-side normal mode**: Playerbots now speak as people playing
  World of Warcraft across General, Party, Guild, Battleground, Raid,
  screenshot, emote, and playerbot `/say` prompts. The shared voice
  contract favors friendly, natural MMO chat with room for varied
  personalities and occasional mild bluntness.
* **NPC roleplay preserved**: Actual NPCs remain inhabitants of Azeroth
  in proximity chatter regardless of the configured playerbot mode,
  including mixed NPC and playerbot scenes.
* **Broader conversation variety**: Normal-mode Guild, proximity,
  ambient, Party-question, dungeon-question, and Battleground topic
  pools now provide substantially more distinct gameplay and social
  subjects without relying on in-world roleplay framing.
* **Mode-safe context and caching**: Normal prompts ignore legacy
  roleplay-shaped identity metadata, active group personalities are
  normalized at bridge startup, and ready pre-cache rows are discarded
  before mode-specific responses are refilled.
* **Configuration and regression coverage**: Normal mode is now the
  documented default, with focused tests protecting channel routing,
  roleplay preservation, topic diversity, prompt context, and startup
  cache behavior.

### 2026-09-07 - OpenRouter Reasoning Controls

* **Opt-in reasoning configuration**: OpenRouter requests can now send
  model-specific reasoning effort and optionally exclude returned
  reasoning text. Empty effort values preserve existing behavior, while
  `none` explicitly disables reasoning on hybrid models.
* **Reasoning-aware output budgets**: An optional multiplier protects
  normal and quick-analysis responses from being consumed entirely by
  reasoning tokens. It applies only while reasoning is enabled.
* **Request-shape regression coverage**: Focused tests protect default,
  explicitly disabled, and enabled reasoning behavior across both
  OpenRouter request paths.

### 2026-09-07 - Playerbot Selector Command Filtering

* **Selector commands excluded from chatter**: Party commands using
  Playerbot selectors, such as `@tank attack`, `@group1 follow`, and
  `@aura123 follow`, are now rejected before they can enter Chatter's
  group history, reply queue, or persistent player-message memories.
* **Conversation-safe matching**: Selector syntax and command tails are
  validated so ordinary messages such as `@Aurabelle hi` and
  `@tank nice save` remain eligible for conversation.
* **Cross-language regression coverage**: Focused tests cover selector
  grammar, false-positive names, malformed inputs, case and whitespace,
  and enforce parity between the C++ and Python selector tables.
* **Dedicated changelog**: Release history now lives in this file
  instead of the README.

### 2026-08-31 - Anthropic SDK v1 Compatibility

* **Anthropic request compatibility**: Normal generation and
  quick-analysis requests now send sampling temperature through
  `extra_body`, avoiding SDK v1's rejection of the direct argument.
* **Supported dependency range**: Bridge requirements now constrain
  Anthropic to `>=1.0.0,<2.0.0`, with Python 3.10+ documented as the
  supported runtime.
* **Regression coverage**: Focused tests protect both Anthropic request
  paths from future SDK argument regressions.

### 2026-08-31 - Bots Notice Custom Emotes

* **`/e` and `/me` now reach the bots**: previously only the ~244 named
  emotes (`/point`, `/salute`) triggered reactions, because those arrive on the
  `OnPlayerTextEmote` hook. A typed `/e grabs hand` is ordinary
  `CHAT_MSG_EMOTE` chat, which the module was discarding. It is now routed into
  the same reaction pipeline and the typed text is handed to the model as the
  action.
* **Targeting comes from your selection**: the client sends no target with a
  custom emote, so the bot you have selected is treated as the target, matching
  how the emote reads to a human. With nothing selected it becomes an
  undirected emote that a nearby bot may remark on.
* **Verbal only, by nature**: a custom emote has no emote id, so there is
  nothing to mirror. Bots answer in words; the mirrored animation and the NPC
  mirror remain named-emote features.
* Controlled by `LLMChatter.EmoteReactions.CustomEnable` (default on) and
  clamped by `LLMChatter.EmoteReactions.CustomMaxChars` (default 120).

### 2026-08-30 - Actions Are Real Emotes

* **The `action` field is now sent as `/e`**: a response like
  `{"message": "Fairbreeze burning again?", "action": "scans the treeline"}`
  used to arrive as one line, `*scans the treeline* Fairbreeze burning again?`.
  It is now delivered as two: a text emote (`Ennien scans the treeline`)
  immediately followed by the spoken line. Actions read as actions in the chat
  log instead of asterisks glued to speech.
* **The split happens at queue time**: `llm_chatter_messages` gained an
  `action` column, and `insert_chat_message()` peels the `*action*` prefix off
  the cleaned message into it, so every producer is covered without touching
  each call site. C++ delivery emits it via `TextEmote` immediately before the
  speech, at each send site rather than once up front, so it is tied to the
  same decision the speech is. A line that is withheld and retried — a yell
  from a bot that has died or left the zone — does not leave its action
  broadcast to an empty stage, and cannot replay it on every attempt.
* **Reversible**: set `LLMChatter.ActionAsEmote.Enable = 0` to restore the old
  inline rendering. Note that `/e` is proximity based, so on party, raid, guild
  and General messages only players standing near the bot see the emote, while
  the spoken line still reaches the whole channel.

### 2026-08-29 - Shorter Memories, Sent Whole

* **Memories reach the model intact**: `sanitize_memory_for_prompt()` no
  longer chops memories at 200 characters before injection. It now only
  strips control characters and normalises whitespace, so every prompt
  carries the memory exactly as the browser and the log viewer show it.
* **Length is bounded when the memory is written**: the generator asks for a
  single factual sentence of at most 160 characters, and `_clamp_memory_text()`
  trims anything past 240 at a sentence boundary before it is stored. Bounding
  the write side rather than the read side means a bot asked to "reference
  this naturally" is never building a line around a severed clause.
* **Drier, less florid journal entries**: the memory prompt now asks for a
  terse log entry recording who was involved, what was done and where, with
  no metaphors and at most a short clause of feeling. The `poetic` and
  `vivid` expression styles were replaced with `plain`, `matter_of_fact` and
  `observational`, and the chosen mood is passed as a subtle hint rather than
  an instruction to emote. Existing memories are untouched.

### 2026-08-25 - Lossless Trait Upload

* **Long traits reach the server intact**: the client cuts an outgoing chat
  line at 255 characters, so three sentence-length traits — and any Cyrillic
  ones, which cost six characters each once percent-encoded — overflowed the
  single `.llmc set` line and the save was silently lost. The addon now falls
  back to a chunked upload (`.llmc put` / `commit` / `cancel`) whenever the
  single-shot line would not fit, and keeps using `set` when it does.
* **A commit is all or nothing**: the whole staged edit is validated before
  any of it is written, so an invalid trait cannot leave a backstory saved and
  an invalid backstory cannot arrive after the traits have already changed.
  The player gets one error and the bot is untouched.
* **An explicit backstory is not regenerated over**: changing traits queues a
  backstory regeneration, and the worker starts by clearing whatever is
  stored. A commit that supplies its own story skips that regeneration, so the
  text the player wrote is not discarded minutes later. Tone still regenerates,
  since it has to follow the new traits.
* **Trait limits count characters everywhere**: the server counted bytes,
  which rejected a 64-character Cyrillic trait at 128 bytes even though the
  column is `VARCHAR(64)`. Server and addon now both count UTF-8 characters,
  matching the edit boxes and MySQL.
* Requires the updated Chatter Companion addon; the server accepts the old
  addon unchanged.

### 2026-08-25 - Longer Traits Accepted

* **Traits up to 64 characters are stored correctly**: The session table
  `llm_group_bot_traits` still capped each trait at 32 characters while
  `llm_bot_identities` and the `/chatter` panel already allowed 64. Traits
  longer than 32 characters broke the bridge with
  `Data too long for column 'trait1'` when a bot joined a group, and were
  silently truncated in the session row.
* **Database Migration**: Run
  `data/sql/characters/updates/20260827_widen_group_bot_traits.sql` if
  upgrading from a previous version. Fresh installs already have the wider
  columns from the base schema.

### 2026-08-16 - Korean Language and Unicode Cleanup

* **Korean language support**: `LLMChatter.Language = KO` now resolves
  to Korean and applies the existing localized prompt rules.
* **Unicode-safe emoji cleanup**: Emoji removal no longer treats the
  entire range from U+24C2 through U+1F251 as emoji. Hangul, CJK, and
  other scripts inside that former range are preserved.

### Guild Channel Chatter

* **Guild chatter**: Optional ambient Guild statements and
  two- or three-bot conversations. C++ selects live participants;
  the bridge gives the exchange one RP subject and cross-zone context,
  adds irregular participant-name references when useful, then
  delivers naturally staggered Guild lines. It is gated by
  `GuildChatter.Chance`, `ConversationChance`, and `Cooldown`. The
  master Guild Chat feature now defaults to enabled.
* **Player-driven Guild replies**: Every eligible player Guild message
  receives at least one bot reply. The response can be a single answer,
  multiple independent answers, or a Guild conversation. Per-login
  memory combines recent verbatim lines with a compact rolling summary,
  supports subtle callbacks and opinion continuity, and is cleared on
  both logout and login. Summary calls always reuse the configured
  chatter provider and model.
* **Guild login greetings**: A full real-player login schedules a
  session-safe greeting without assuming playerbots are immediately
  ready. Quick 2-5-second reactions remain possible, while ordinary and
  busy delay bands make later greetings more common. Player speech,
  logout, relogin, Guild changes, and stale sessions cancel the greeting.
  Delivered greetings join the current Guild session history so an
  immediate player reply retains the greeting as context.

### 2026-06-19 - Chat-Type Master Toggles & Subsystem Classifier

* **General channel master switch**: New
  `LLMChatter.GeneralChannel.Enable` (default 1) silences **all**
  General-channel chatter with a single value — ambient remarks, world
  event reactions (weather, holidays, day/night — including the ones
  that normally always fire), and replies to player General messages.
  It takes effect immediately on `.reload config`, and also stops any
  General messages already queued for delivery, not just new ones.
* **Config key renamed (action may be required)**:
  `LLMChatter.GeneralChat.Enable` is now
  `LLMChatter.GeneralChat.PlayerReplyEnable`. It only ever governed
  replies to player General messages; the new name makes that clear.
  The old key is no longer read — if your config sets
  `LLMChatter.GeneralChat.Enable`, rename it. To turn off *everything*
  in General at once, use `LLMChatter.GeneralChannel.Enable` instead.
* **GroupChatter toggle made authoritative**:
  `LLMChatter.GroupChatter.Enable = 0` now also silences
  emote-triggered party/raid reactions and drains already-queued group
  messages, and the bridge stops attempting idle chatter and bot
  questions while it is off. Raid-boss and Battleground chatter (which
  share the party/raid channels) are unaffected. The solo NPC
  emote-mirror stays governed by `LLMChatter.EmoteReactions.Enable`.
* **Proximity toggle made authoritative**:
  `LLMChatter.ProximityChatter.Enable = 0` now also drains already-
  queued open-world say/msay lines, matching the other toggles.
* **New `owner_subsystem` classifier**: Each row in
  `llm_chatter_messages` is tagged with its owning subsystem (group,
  raid, bg, general, proximity, ...). This lets the delivery layer
  honor each master toggle even for in-flight messages without
  affecting the other subsystems that share the same chat channel.
* **Database Migration**: This update **adds a database column**. If
  upgrading, apply
  `data/sql/characters/updates/20260619_owner_subsystem.sql` (it is
  idempotent and also runs automatically when worldserver starts).
  Fresh installs already have the column from the base schema.

### 2026-06-18 - Startup Health Check

* **Automatic Setup Diagnostic**: The bridge now runs a built-in health
  check at startup and prints a plain-language PASS/FAIL report to its
  logs. It surfaces the most common "bots won't chat" causes — wrong
  database credentials, a missing or leftover-placeholder API key, an
  invalid key, or an unreachable local LLM — instead of failing
  silently. On a critical failure the bridge logs a clear banner naming
  the problem and the fix.
* **Six Checks With Fix Hints**: Verifies the config loads and the module
  is enabled, the database connection (distinguishing wrong
  user/password, unreachable host, and wrong database name), the required
  tables exist, the provider/API key is set and not a placeholder, and a
  live LLM test call actually succeeds.
* **Saved Report File**: The same report is written to
  `logs/healthcheck.log` so it can be opened as a normal text file
  without scraping container logs.
* **Config Toggles**: `LLMChatter.HealthCheck.Enable` (default 1) and
  `LLMChatter.HealthCheck.LLMProbe` (default 1) control the startup check
  and whether it makes the live LLM test call. An optional
  `LLMChatter.HealthCheck.LogPath` overrides the report file location.

### 2026-06-05 - Addon Chat Ingestion Filter

* **Hidden Addon Traffic Ignored**: Party, proximity, and General chat
  ingestion now drops messages tagged `LANG_ADDON` before they can be
  stored in chat history or sent to the LLM. This prevents Questie,
  Multibot, DBM-style sync packets, and similar addon protocol payloads
  from polluting bot context or memories.
* **Party Hook Language Preservation**: The group chat hook now threads
  AzerothCore's language flag through the player-message handler instead
  of discarding it, allowing addon traffic to be filtered by the engine's
  authoritative tag rather than brittle text heuristics.
* **Debug Evidence Logging**: When `LLMChatter.DebugLog = 1`, ignored
  addon packets are logged with chat type, player, byte length, and an
  escaped preview so server owners can verify filtering without storing
  raw addon traffic in LLM-facing history tables.

### 2026-06-02 - Loot Reaction Chance Configuration

* **Configurable Epic and Legendary Loot Reactions**:
  `LLMChatter.GroupChatter.LootChancePurple` and
  `LLMChatter.GroupChatter.LootChanceOrange` now control party loot
  reaction chances for purple and orange items instead of treating both
  as hardcoded 100% triggers.
* **Quality-Specific Loot Gates**: Group loot reactions now use separate
  configured chances for green, blue, purple, and orange item quality.
  Artifact and heirloom quality loot still always triggers.
* **Config Visibility**: The chatter bridge startup summary now prints
  the purple and orange loot chance values alongside green and blue.

### 2026-06-02 - Language Configuration Reliability

* **German and Common Language Codes**: `LLMChatter.Language` now ships
  built-in support for `DE`, `ES`, `PT`, and `RU` in addition to
  English and French. German no longer requires manually editing the
  Python language map.
* **Unknown Language Warnings**: The bridge now logs the configured and
  resolved language at startup, and warns when an unknown language code
  falls back to English.
* **More Complete Language Prompting**: Group farewell generation and
  ambient JSON repair retries now preserve the configured language rule
  instead of falling back to plain English repair prompts.
* **Localized Action Narration**: Conversation action prompts no longer
  include an English action example for the model to copy. The prompt
  now asks for short physical narration in the configured language.
* **No Database Migration**: This update is Python/config-template only.
  Restart the chatter bridge after changing `LLMChatter.Language`.

### 2026-05-19 - Google Gemini and OpenRouter Provider Support

* **Google Gemini Support**: Chatter can now use Google's
  OpenAI-compatible Gemini endpoint. `gemini-3.1-flash-lite` is the
  recommended Google model, with Gemini-specific reasoning/thinking
  controls for reliable structured JSON output.
* **OpenRouter Support**: Chatter can now use OpenRouter through its
  OpenAI-compatible API. Recommended OpenRouter model slugs include
  `anthropic/claude-haiku-4.5`, `openai/gpt-4o-mini`, and
  `openai/gpt-4.1-mini`.
* **Provider Setup Docs**: README and config examples now cover
  Anthropic, OpenAI, Google, OpenRouter, and Ollama, including matching
  provider-specific API key settings.
* **Screenshot Vision Provider Coverage**: Screenshot vision setup now
  documents OpenAI, Anthropic, Google, and OpenRouter provider options.
* **Runtime Validation**: OpenRouter was tested live with both
  `openai/gpt-4o-mini` and `anthropic/claude-haiku-4.5` across
  pre-cache, ambient, proximity, group idle, player message, and
  General-to-party relay paths. No truncation or malformed response
  pattern was observed in the request log during testing.

### 2026-05-11 - Immersion, Pacing, and Party Awareness

* **General-to-Party Reactions**: Party bots can now react when they hear
  another bot speaking in General chat. A grouped companion may comment on
  what was said, naming the General speaker directly, and larger groups can
  turn that moment into a short party conversation.
* **Smoother Party Chat Flow**: Party chatter is now paced more carefully so
  bot lines do not land in a noisy burst. Conversations feel calmer during
  travel, idle moments, screenshots, nearby observations, and event reactions.
* **Travel-Aware Companions**: Bots better understand how the group is moving.
  They can account for walking, mounts, taxi flights, swimming, and transports,
  which helps avoid awkward lines about doing something impossible in the
  moment.
* **Richer Ambient Gossip**: World chatter has more variety and better local
  flavor. NPC gossip, bot gossip, weather, time of day, and seasonal context
  are blended more consistently into ambient conversations.
* **More Reliable Location Awareness**: Zone and subzone reactions now use the
  location from the moment the event happened, reducing stale or misplaced
  comments when the group is moving quickly.
* **Weather Feels More Grounded**: Weather reactions now track player context
  more carefully, so environmental comments are less likely to fire from the
  wrong place or at the wrong time.
* **Cleaner Emotes and Actions**: Bot gestures and physical actions are handled
  more consistently, keeping messages readable while still adding character
  when appropriate.
* **Screenshot Vision Targeting Fixes**: Screenshot observations now choose
  eligible grouped bots more accurately, improving who comments on what the
  player sees.

### 2026-04-17 — Background Stories

* **LLM-Generated Origin Stories**: Every bot now receives a unique background story when they first join your group. Generated by the LLM based on the bot's race, class, and personality traits, each backstory covers birthplace, upbringing, and formative events — all grounded in Warcraft lore.
* **Persistent Across Sessions**: Backstories are stored permanently alongside traits and tone. The same bot tells the same origin story every time they rejoin.
* **Ambient Backstory Influence**: During idle party chatter (25% chance) and proximity /say conversations (15% chance), the bot's backstory is fed to the LLM, subtly influencing their dialogue without forcing explicit references. A bot raised in Lakeshire might comment on a quiet lake; one hardened by war might be blunter during downtime.
* **Addon Integration**: The Chatter Companion addon now displays each bot's background story in a scrollable read-only panel below the tone field. Click "Regenerate Story" to request a fresh backstory from the LLM. Changing a bot's traits automatically clears and regenerates their backstory to stay consistent.
* **Configurable**: Three new config keys control the feature: `LLMChatter.Backstory.Enable` (master toggle), `LLMChatter.Backstory.IdleChance` (default 25%), and `LLMChatter.Backstory.ProximityChance` (default 15%). All are bridge-scope — restart the chatter bridge after changes.
* **Database Migration**: Run `data/sql/characters/updates/20260416_bot_backstory.sql` if upgrading from a previous version.

### 2026-04-03 — Multidirectional Proximity Chatter

* **Ambient `/say` Conversations**: NPCs and bots now talk to each other — and to you — via `/say` as you move through the world. Guards, vendors, trainers, citizens, and your party bots all participate. Conversations are brief and spatially grounded.
* **Multi-Speaker Scenes**: 2-4 speakers exchange short lines with natural pauses. Speakers face each other when talking; NPCs return to their original orientation afterward.
* **Player Reply**: Reply via `/say` within 30 seconds and the nearby speaker will respond. Up to 5 exchanges before the conversation winds down naturally.
* **Name Addressing**: Speakers can address nearby bots, NPCs, and you by name.
* **250+ Topic Pool**: Casual conversation seeds across 17 categories — weather, gossip, petty crime, food, travel, guard talk, children's chatter, and more.
* **Fully Configurable**: 15 config keys control scan interval, trigger chance, cooldowns, conversation length, reply limits, and more.

### 2026-04-01 — Raid Chatter Enhancements

* **Raid Battle Cries**: When engaging enemies in a raid instance, a bot shouts a short battle cry in raid chat — race and class flavored. Configurable via `RaidChatter.BattleCryChance` (default 70%).
* **Raid Banter**: Between-pull idle events now alternate 50/50 between motivational morale and casual banter (environment jokes, class jabs, loot drama commentary).
* **Raid Idle Boost**: Idle chatter fires twice as often inside raid instances with half the cooldown, keeping the conversation flowing during dungeon crawls.
* **Dead Bot Awareness**: Dead bots know they're dead. Their idle dialogue shifts to ghost humor, resurrection pleas, and floor commentary instead of pretending they're alive.
* **Zone Transitions in Raids**: Bots now comment on subzone changes inside raid instances (e.g., moving between wings in Naxxramas).
* **Morale Between Deaths**: Morale and banter chatter no longer gets blocked when party members are dead — only active combat suppresses it.
* **Reliability Improvements**: Fixed duplicate message delivery and improved handling of truncated AI responses.

### 2026-04-01 — State Callouts, Greeting Improvements, Parser Hardening

* **Low Health & OOM Callouts**: Bots now vocalize when they're low on health or running out of mana. Configurable thresholds (`LowHealthThreshold`, `OOMThreshold`), chance, and cooldown. Automatically scales in battlegrounds (halved chance, doubled cooldown) to avoid spam.
* **Time-of-Day Greetings**: Bot greetings now include the current time of day, preventing immersion-breaking lines like "good evening" when it's morning.
* **Greeting Anti-Repetition**: Bots no longer echo each other's greetings when multiple join at once. Each bot reads the recent chat history and avoids repeating what others already said.
* **Robust Response Handling**: Improved parser reliability — raw AI artifacts no longer leak into chat.
* **State Callout Config**: Five new config keys for tuning health and mana callout behavior.

### 2026-03-29 — Screenshot Vision, Emote Reactions, BG Improvements

* **Screenshot Vision (Experimental)**: Bots can now see the actual game world through periodic screenshot analysis. A lightweight host-side agent captures your screen, sends it to a vision AI, and bots comment on what they see, from ancient ruins to glowing flora to approaching storms. Supports both GPT-4o-mini and Claude Haiku. See [Screenshot Vision](README.md#screenshot-vision) for setup.
* **Emote Reaction System**: Bots now react when you emote at them. `/wave` at a bot and they might wave back, `/flex` and they'll have something to say about it. Three reaction paths: silent mirror (bot mirrors your emote), verbal reaction (personal response), and observer comment (a nearby bot notices and chimes in). Covers all ~170 text emotes.
* **Dungeon Context Injection**: Party chatter prompts now detect when you're inside a dungeon and inject dungeon-specific flavor instead of outdoor zone lore. Affects kill, loot, death, achievement, wipe, corpse run, and nearby object events.
* **BG Chatter Quality Pass**: Reduced noise in battleground chatter, suppressed narrator actions in fast-paced BG events, unified the join path for cleaner group formation, and synced config defaults with tested values.
* **Action & Emote Frequency**: `EmoteChance` and `ActionChance` config keys control how often bots include physical emotes and narrator actions in their messages. Actions are delivered as a separate `/e` text emote ahead of the spoken line; `LLMChatter.ActionAsEmote.Enable = 0` restores the old inline `*action*` form.

### 2026-03-22 — Persistent Memories & Personality Traits

* **Persistent Bot Identities**: Each bot now carries a permanent personality (3 traits + role + farewell style) stored in `llm_bot_identities`. Traits survive across sessions and server restarts. Bump `LLMChatter.Memory.IdentityVersion` to force regeneration after prompt changes.
* **Memory System**: 14 memory types (ambient, boss_kill, quest_complete, discovery, achievement, level_up, pvp_kill, bg_win/loss, wipe, dungeon, party_member, player_message, first_meeting) are generated via LLM and stored per bot-player pair. Memories are recalled during idle chatter, reunion greetings, and bot questions, creating recognizable callbacks to shared experiences.
* **Configurable Generation & Recall**: Every memory type has a `*GenerationChance` config key controlling how often memories are created. Recall frequency is controlled by `IdleRecallChance` and `RecallChance` (reunion).
* **Zone & Subzone Awareness in Prompts**: Zone flavor and subzone lore are now injected into quest, discovery, idle, and event prompts. The player's subzone is tracked from the moment bots join the group.
* **Focused Memory Callbacks**: When bots recall shared memories, the references are clear and recognizable — not vague allusions.
* **Message Length Controls**: Stricter length limits prevent wall-of-text messages.
* **Database Migration**: Run `data/sql/characters/updates/20260320_bot_memory_system.sql` if upgrading from a previous version.
