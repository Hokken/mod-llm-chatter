# WoW WotLK 3.3.5a — All Dungeon & Raid Instance Map IDs

Reference for AzerothCore module development. These are the **Map IDs** (InstanceMapID) from the `Map.dbc` — the same IDs used in AzerothCore's `map` field across various database tables (`instance`, `dungeon_access_template`, etc.).

---

## Classic Dungeons

| Map ID | Instance Name |
|--------|--------------|
| 33 | Shadowfang Keep |
| 34 | The Stockade |
| 36 | The Deadmines |
| 43 | Wailing Caverns |
| 47 | Razorfen Kraul |
| 48 | Blackfathom Deeps |
| 70 | Uldaman |
| 90 | Gnomeregan |
| 109 | The Temple of Atal'Hakkar (Sunken Temple) |
| 129 | Razorfen Downs |
| 189 | Scarlet Monastery |
| 209 | Zul'Farrak |
| 229 | Blackrock Spire (UBRS/LBRS) |
| 230 | Blackrock Depths |
| 269 | Opening of the Dark Portal (Caverns of Time) |
| 289 | Scholomance |
| 329 | Stratholme |
| 349 | Maraudon |
| 389 | Ragefire Chasm |
| 429 | Dire Maul |

## Classic Raids

| Map ID | Instance Name |
|--------|--------------|
| 249 | Onyxia's Lair |
| 309 | Zul'Gurub |
| 409 | Molten Core |
| 469 | Blackwing Lair |
| 509 | Ruins of Ahn'Qiraj (AQ20) |
| 531 | Temple of Ahn'Qiraj (AQ40) |
| 533 | Naxxramas |

## TBC Dungeons

| Map ID | Instance Name |
|--------|--------------|
| 540 | The Shattered Halls |
| 542 | The Blood Furnace |
| 543 | Hellfire Ramparts |
| 545 | The Steamvault |
| 546 | The Underbog |
| 547 | The Slave Pens |
| 552 | The Arcatraz |
| 553 | The Botanica |
| 554 | The Mechanar |
| 555 | Shadow Labyrinth |
| 556 | Sethekk Halls |
| 557 | Mana-Tombs |
| 558 | Auchenai Crypts |
| 560 | Old Hillsbrad Foothills (Caverns of Time) |
| 269 | The Black Morass (Caverns of Time) |
| 585 | Magisters' Terrace |

## TBC Raids

| Map ID | Instance Name |
|--------|--------------|
| 532 | Karazhan |
| 534 | Hyjal Summit (Battle for Mount Hyjal) |
| 544 | Magtheridon's Lair |
| 548 | Serpentshrine Cavern |
| 550 | Tempest Keep (The Eye) |
| 564 | Black Temple |
| 565 | Gruul's Lair |
| 580 | Sunwell Plateau |

## WotLK Dungeons

| Map ID | Instance Name |
|--------|--------------|
| 574 | Utgarde Keep |
| 575 | Utgarde Pinnacle |
| 576 | The Nexus |
| 578 | The Oculus |
| 595 | The Culling of Stratholme (Caverns of Time) |
| 599 | Halls of Stone |
| 600 | Drak'Tharon Keep |
| 601 | Azjol-Nerub |
| 602 | Halls of Lightning |
| 604 | Gundrak |
| 608 | The Violet Hold |
| 619 | Ahn'kahet: The Old Kingdom |
| 632 | The Forge of Souls |
| 650 | Trial of the Champion |
| 658 | Pit of Saron |
| 668 | Halls of Reflection |

## WotLK Raids

| Map ID | Instance Name |
|--------|--------------|
| 533 | Naxxramas (retuned for level 80) |
| 615 | The Obsidian Sanctum |
| 616 | The Eye of Eternity |
| 624 | Vault of Archavon |
| 603 | Ulduar |
| 649 | Trial of the Crusader |
| 631 | Icecrown Citadel |
| 724 | The Ruby Sanctum |

## Battlegrounds (for reference)

| Map ID | Instance Name |
|--------|--------------|
| 30 | Alterac Valley |
| 489 | Warsong Gulch |
| 529 | Arathi Basin |
| 566 | Eye of the Storm |
| 607 | Strand of the Ancients |
| 628 | Isle of Conquest |

## Arenas (for reference)

| Map ID | Instance Name |
|--------|--------------|
| 559 | Nagrand Arena |
| 562 | Blade's Edge Arena |
| 572 | Ruins of Lordaeron |
| 617 | Dalaran Sewers |
| 618 | The Ring of Valor |

---

## Notes

- **Naxxramas (533)** appears in both Classic Raids and WotLK Raids — same Map ID, retuned for level 80 in WotLK.
- **Onyxia's Lair (249)** was also retuned for level 80 in patch 3.2.2 (WotLK).
- The `dungeon_access_template` table in AzerothCore uses these Map IDs along with difficulty values: `0` = Normal (5-man), `1` = Heroic (5-man), `0` = 10-man (raid), `1` = 25-man (raid), `2` = 10-man Heroic, `3` = 25-man Heroic.
- All WotLK Heroic dungeons require average item level 180 via Dungeon Finder. Trial of the Champion, Pit of Saron, and Forge of Souls require ilvl 200. Halls of Reflection requires ilvl 219.

### Sources
- [Wowpedia InstanceID](https://wowpedia.fandom.com/wiki/InstanceID)
- [AzerothCore Wiki — map DBC](https://www.azerothcore.org/wiki/map)
- [AzerothCore Wiki — dungeon_access_template](https://www.azerothcore.org/wiki/dungeon_access_template)