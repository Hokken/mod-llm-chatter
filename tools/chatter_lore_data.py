"""Themed guild and General chat topics, and race+class notes."""

# (race, class_style) -> what sets this combination apart. Priests use
# "Light Priest" or "Shadow Priest" as the class style.
RACE_CLASS_NOTES = {('Human', 'Death Knight'): "Human death knights, after being freed from the Lich King's control, "
                            'join the Knights of the Ebon Blade, an independent order of free '
                            'death knights based in Acherus. They retain the memory of their past '
                            'lives, but use the forbidden power of death against the Scourge and '
                            'Arthas himself.',
 ('Human', 'Mage'): 'Human mages are traditionally associated with the Kirin Tor and the magical '
                    'school of Dalaran. They regard magic as an art and a discipline, and '
                    'experienced mages may be members of the Kirin Tor or serve the Alliance as '
                    'battle casters. They often study and live in The Mage Quarter - a district of '
                    'Stormwind with magical academies, cozy green streets and mage towers.',
 ('Human', 'Paladin'): 'Human paladins come from the tradition of the Knights of the Silver Hand — '
                       'an order of holy warriors created as the military arm of the Church of the '
                       'Holy Light. They worship the Holy Light and protect humans, the Alliance '
                       'and other peoples from the Scourge, demons and other threats. They often '
                       'train and serve in the Cathedral of Light in Stormwind.',
 ('Human', 'Light Priest'): 'Human Light Priests usually belong to the tradition of the Church of '
                            'the Holy Light, the largest religious organization of humans. They '
                            'perceive the Holy Light as a spiritual force grounded in compassion, '
                            'respect for life and inner will, and serve their communities, '
                            'Stormwind and the Alliance. They often study and serve in the '
                            'Cathedral of Light in Stormwind.',
 ('Human', 'Shadow Priest'): 'Human Shadow Priests study Shadow and The Void, rejecting or '
                             'reinterpreting the traditional teachings of the Church of the Holy '
                             'Light. They may turn to forbidden knowledge and powers connected '
                             'with the Void and the Old Gods, although open worship of these '
                             'entities is considered extremely dangerous and heretical among '
                             'humans. Because their practice is forbidden, they have no single '
                             'base, preferring secret cults in places hidden from ordinary '
                             'citizens, such as old ruins or house cellars.',
 ('Human', 'Rogue'): 'Human rogues are often associated with SI:7 — the secret intelligence and '
                     'sabotage service of Stormwind. They specialize in stealth, espionage, '
                     'assassination and sabotage, and can carry out the dirty work that the '
                     'official armies of the Alliance cannot do openly. They are usually based in '
                     'Old Town in Stormwind, and also have many secret hideouts in the cellars of '
                     'houses and taverns.',
 ('Human', 'Warlock'): 'Human warlocks study demonic and forbidden magic and are often connected '
                       'with independent secret circles of magic users, such as former followers '
                       'of the Burning Legion and the Shadow Council. Even warlocks loyal to the '
                       'Alliance hide their pursuits, since their art is based on socially '
                       'unacceptable practices such as summoning and enslaving demons. They have '
                       'many secret bases for meetings and training, hidden from the eyes of the '
                       'guards and ordinary people, for example the cellar of the tavern "The '
                       'Slaughtered Lamb".',
 ('Human', 'Warrior'): 'Human warriors usually serve the armies of Stormwind or other military '
                       'forces of the Alliance. Their culture emphasizes martial honor, discipline '
                       'and service to the kingdom, although experienced veterans may be '
                       'mercenaries, soldiers or knights. They often train in Old Town Stormwind.',
 ('Human', 'Hunter'): 'Human hunters have no single organization, but often serve as scouts, '
                      'trackers and soldiers of the Alliance. They especially value tracking, '
                      "marksmanship and survival skills, and may cooperate with Stormwind's "
                      'military intelligence services.',
 ('Dwarf', 'Death Knight'): 'Dwarven death knights, after being freed from the Scourge, join the '
                            'Knights of the Ebon Blade. Their return to their homelands is often '
                            'met with distrust, since they remain undead and use necromantic '
                            'powers, despite fighting against the Lich King. They live and train '
                            'in their flying necropolis, Acherus.',
 ('Dwarf', 'Hunter'): 'Dwarven hunters are closely tied to the traditions of the Mountaineers, '
                      'Riflemen and scouts of Ironforge. Many are also associated with the '
                      "archaeological organization the Explorers' League, especially if they are "
                      'interested in exploring ancient ruins, archaeology and searching for '
                      'forgotten secrets. They often train in the Hall of Arms in Ironforge.',
 ('Dwarf', 'Mage'): 'Dwarven magic users are less common than human or gnomish ones and are '
                    'usually associated with the magical community of Ironforge or Dalaran. They '
                    'may study traditional arcane magic without giving up dwarven culture, '
                    'engineering and their interest in ancient knowledge. They are usually based '
                    'and trained in the Hall of Mysteries in Ironforge.',
 ('Dwarf', 'Paladin'): 'Dwarven paladins belong to the tradition of the Knights of the Silver Hand '
                       'and the Church of the Holy Light, but maintain close ties to Ironforge. '
                       'They see themselves as warriors of the Light, protecting dwarves, the '
                       'Alliance and their allies from the Scourge and other enemies. They are '
                       'based and train in the Hall of Mysteries in The Mystic Ward district of '
                       'Ironforge.',
 ('Dwarf', 'Light Priest'): 'Dwarven Light Priests follow the teachings of the Holy Light, '
                            'widespread within the Church of the Holy Light in Ironforge. Their '
                            'faith is usually combined with a dwarven sense of duty, resilience '
                            'and respect for ancestors and society. They study and serve the Light '
                            'in the Hall of Mysteries in The Mystic Ward district of Ironforge.',
 ('Dwarf', 'Shadow Priest'): 'Dwarven Shadow Priests study Shadow and The Void, departing from the '
                             'traditional veneration of the Holy Light. They may seek knowledge '
                             'about ancient powers, the Old Gods and the secrets of the world, '
                             'although open worship of the Old Gods runs counter to the interests '
                             'of Ironforge and the Alliance. Because such pursuits are illegal, '
                             'they have no single public base, but they often secretly gather in '
                             'the homes of individual cultists or in abandoned houses in rough '
                             'districts such as The Forlorn Cavern in Ironforge.',
 ('Dwarf', 'Rogue'): 'Dwarven rogues may serve as scouts, spies and saboteurs for Ironforge, and '
                     'also work with Alliance intelligence. Some prefer a more independent life as '
                     'mercenaries and adventurers, using their stealth and lockpicking skills. '
                     'They often hold secret meetings to share experience and socialize in hidden '
                     'places such as abandoned houses in The Forlorn Cavern in Ironforge.',
 ('Dwarf', 'Warrior'): 'Dwarven warriors are called Ironclad, traditionally serve the armies of '
                       'Ironforge and are well known as heavy infantry, Riflemen and Mountain '
                       'Kings. Their martial culture is based on clan loyalty, glory in battle and '
                       'the defense of the dwarven people. They train in the Hall of Arms in the '
                       'Military Ward district of the city of Ironforge.',
 ('Gnome', 'Death Knight'): 'Gnome death knights, after being freed from the Scourge, join the '
                            'Knights of the Ebon Blade. They retain their gnomish curiosity and '
                            'engineering approach, but now combine them with necromancy and the '
                            'grim power of death. They live and train in their flying necropolis, '
                            'Acherus.',
 ('Gnome', 'Mage'): 'Gnomish magic users are especially known for their interest in arcane magic '
                    'and the scientific study of magic. Many are associated with the magical '
                    'community of Dalaran and see spells more as a subject of research than as a '
                    'religious or mystical tradition. They are usually based and trained in the '
                    'Hall of Mysteries in Ironforge, since the gnomish city of Gnomeregan is now '
                    'contaminated with toxic waste, overrun by troggs and uninhabitable.',
 ('Gnome', 'Rogue'): 'Gnome rogues use stealth, cunning and technological gadgets for '
                     'reconnaissance and sabotage. They may cooperate with the Alliance, but also '
                     'often treat their profession as a combination of practical skill, ingenuity '
                     'and adventurism. They often hold secret meetings to share experience and '
                     'socialize in hidden places such as The Forlorn Cavern in Ironforge, since '
                     'the gnomish city of Gnomeregan is now contaminated with toxic waste, overrun '
                     'by troggs and uninhabitable.',
 ('Gnome', 'Warlock'): 'Gnome warlocks study demonic magic as a dangerous but powerful field of '
                       'arcane knowledge. Their activities arouse distrust and condemnation even '
                       'among other gnomes, yet some consider controlling demons just another '
                       'technical problem that can be solved with discipline and experimentation. '
                       'Since their activities are publicly illegal and forbidden, they have no '
                       'single public base. Instead, they secretly gather in secret places such as '
                       'abandoned houses in The Forlorn Cavern in Ironforge.',
 ('Gnome', 'Warrior'): 'Gnome warriors serve the armies of Gnomeregan and the Alliance, '
                       'compensating for their small stature with technology, armor and ingenuity. '
                       'They often see warfare as just another field of engineering improvement. '
                       'They train in the Hall of Arms in the Military Ward district of the city '
                       'of Ironforge.',
 ('Night Elf', 'Death Knight'): 'Night elf death knights, after being freed from the Scourge, join '
                                'the Knights of the Ebon Blade. Their connection to nature and the '
                                'ancient culture of the kaldorei contrasts sharply with their '
                                'necromantic powers, so many of them feel alienated from their own '
                                'people. They live and train in their flying necropolis, Acherus.',
 ('Night Elf', 'Druid'): 'Night elf druids belong to the ancient tradition of druidism and are '
                         'closely tied to the Cenarion Circle. They serve the restoration of '
                         'nature, protect the forests of Kalimdor and revere Cenarius, the Emerald '
                         'Dream and the forces of the wild. They often spend many years asleep in '
                         'various Barrow Dens across Kalimdor, where their bodies remain safe '
                         'while their spirits travel through The Emerald Dream. Their main place '
                         'of training and service is the Cenarion Enclave, located in a great tree '
                         'in Darnassus.',
 ('Night Elf', 'Hunter'): 'Night elf hunters are traditionally associated with the Sentinels — the '
                          'main military force of the kaldorei. They serve as defenders of the '
                          'forests of Kalimdor, use bows and animal companions, and often see '
                          "hunting as part of their people's martial tradition. Their main place "
                          'of training and socializing is the Cenarion Enclave, located in a great '
                          'tree in Darnassus.',
 ('Night Elf', 'Light Priest'): 'Night elf Light Priests belong to the Sisterhood of Elune and '
                                'worship Elune. Their notion of the light differs from the human '
                                'Holy Light: Elune is perceived as the goddess of the moon, the '
                                'protector of the kaldorei and a source of sacred power. They '
                                'train and serve in the Temple of the Moon in Darnassus.',
 ('Night Elf', 'Shadow Priest'): 'Night elf Shadow Priests use Shadow and The Void, deliberately '
                                 'turning to powers that oppose the traditions of the Sisterhood '
                                 'of Elune. They may explore the nature of the Void and the Old '
                                 'Gods, but such practice lies far outside the traditional '
                                 'religion of the kaldorei. They are officially despised by the '
                                 'Sisterhood of Elune and night elf society, so they are forced to '
                                 'hold their meetings and training in secret, in places '
                                 'inaccessible to the Sentinels, such as the homes of individual '
                                 'cultists or old ruins in Darkshore.',
 ('Night Elf', 'Rogue'): 'Night elf rogues come from the traditions of the stealthy scouts and '
                         'assassins of the kaldorei. They often operate alongside the Sentinels '
                         'and use the night environment, stealth and knowledge of the forests to '
                         'scout out and eliminate enemies. Their activities are of questionable '
                         'legality, but they have their own hidden refuge in Darnassus - a secret '
                         'cave right in the roots of the huge tree in whose crown lies the '
                         'Cenarion Enclave, with more socially acceptable people such as druids '
                         'and hunters.',
 ('Night Elf', 'Warrior'): 'Night elf warriors often serve in the ranks of the Sentinels or other '
                           'kaldorei military units. They see war primarily as a means of '
                           'defending their forests, their people and their ancient heritage. '
                           "Their main place of training and main base is Warrior's Terrace in "
                           'Darnassus.',
 ('Draenei', 'Death Knight'): 'Draenei death knights are former defenders of their people, '
                              'forcibly turned into weapons of the Scourge and later freed. They '
                              'join the Knights of the Ebon Blade and are forced to reconcile '
                              'their powers of death with their traditional faith in the Holy '
                              "Light. They are based and train in the order's flying necropolis - "
                              'Acherus.',
 ('Draenei', 'Hunter'): 'Draenei hunters use traditions of survival, tracking and animal handling '
                        'inherited from life on Draenor and in Outland. They often act as scouts '
                        'and defenders of draenei settlements and the Exodar. Their main place of '
                        "training and meetings is the Trader's Tier district in the Exodar.",
 ('Draenei', 'Mage'): 'Draenei magic users study arcane magic while maintaining a close connection '
                      'to draenei culture and the Naaru. They may study in Dalaran, but usually '
                      'see magic as one of the tools for protecting their people rather than as a '
                      'replacement for their spiritual tradition. They learn from experienced '
                      'draenei mages in The Vault of Lights in the Exodar.',
 ('Draenei', 'Paladin'): 'Draenei paladins belong to the tradition of the Vindicators — the holy '
                         'warriors of the draenei who have devoted themselves to protecting their '
                         'people and serving the Holy Light. They are closely tied to the Exodar '
                         'and draenei culture and consider the fight against the Burning Legion '
                         'one of their principal historical duties. Their main place of '
                         'initiation, training, service and living is The Vault of Lights in the '
                         'Exodar.',
 ('Draenei', 'Light Priest'): 'Draenei Light Priests are called Anchorites, worship the Holy Light '
                              'and are especially closely tied to the teachings of the Naaru. They '
                              'see the Light as a cosmic force associated with hope, compassion '
                              'and the spiritual unity of the draenei. Their main place of '
                              'initiation, training, service and living is The Vault of Lights in '
                              'the Exodar.',
 ('Draenei', 'Shadow Priest'): 'Draenei Shadow Priests use Shadow and The Void, which especially '
                               'contradicts the traditional draenei faith in the Light and the '
                               'naaru. They may explore the Void as a source of power, but treat '
                               'this practice as a dangerous and forbidden path. They are '
                               'considered dangerous outcasts in draenei society, so they are '
                               'forced to carefully hide their pursuits from the public. '
                               'Therefore, they meet and discuss their dark affairs in remote and '
                               'deserted places, such as Silvermyst Isle or a hidden cave on '
                               'Wildwind Peak on Azuremyst Isle.',
 ('Draenei', 'Shaman'): 'Draenei shamans follow the tradition of communing with elementals and '
                        'nature spirits. Many are members of the Earthen Ring or cooperate with '
                        'its shamans, combining draenei spirituality with respect for the elements '
                        'and the restoration of the world. They train and come to understand the '
                        'elements in The Crystal Hall in the Exodar.',
 ('Draenei', 'Warrior'): 'Draenei warriors serve as the defenders of their settlements and in the '
                         'army of the Exodar. Many come from a draenei military tradition in which '
                         'military service is seen as a duty to their people and a continuation of '
                         'the struggle against the Burning Legion that has lasted many thousands '
                         "of years. Their main place of training and gathering is the Trader's "
                         'Tier district of the Exodar.',
 ('Orc', 'Death Knight'): "Orc death knights, after being freed from the Lich King's control, join "
                          'the Knights of the Ebon Blade. Many of them already have experience of '
                          "war and of the orcs' shamanic or warrior traditions, but now they wield "
                          'the powers of death against the Scourge. They live and train in the '
                          "Order's flying necropolis, Acherus.",
 ('Orc', 'Hunter'): 'Orc hunters come from an ancient tradition of hunting and survival on '
                    'Draenor. They value their bond with animals, tracking and personal strength, '
                    'and often see the hunt as part of the orcish warrior way of life. They are '
                    "based and train in the Hunter's Hall in the Valley of Honor district of "
                    'Orgrimmar.',
 ('Orc', 'Rogue'): "Orc rogues use stealth and sabotage despite the orcs' traditional focus on "
                   'open combat. Many have ties to the Shattered Hand or other traditions of '
                   'stealthy assassins, in which personal composure and the ability to kill an '
                   'enemy matter more than martial honor. They are usually despised by other orcs, '
                   'so their main place of gathering and training is the lair of the Shadowswift '
                   'Brotherhood, a secret organization to which most of them belong, in the cave '
                   'The Cleft of Shadows beneath Orgrimmar, where all sorts of outcasts who are '
                   'unwelcome up on the surface gather.',
 ('Orc', 'Shaman'): 'Orc shamans come from the ancient spiritual tradition of the orcs and are '
                    'especially connected with the Earthen Ring in the WotLK era. They commune '
                    'with the elements and ancestral spirits and seek to restore the harmony that '
                    "was lost because of the orcs' history and the Burning Legion. They are "
                    'extremely respected in orcish society, so they often study and live in '
                    'Grommash Hold, the main fortress of Orgrimmar, near the Warchief. The best '
                    "shamans often serve as the Warchief's advisors and his court miracle-workers.",
 ('Orc', 'Warlock'): 'Orc warlocks come from the dark history of warlockery that began with '
                     "Gul'dan and the Shadow Council. Modern Horde warlocks may be loyal to Thrall "
                     'and the Horde, but they use demonic magic, which their people historically '
                     'associate with the fall of the orcs. In orcish society they are feared and '
                     'despised for their connection to demonic magic, so they cannot gather in '
                     "public places on the city's surface. Instead, they gather, train and share "
                     'their discoveries in secret places, such as the hidden refuge Darkfire '
                     'Enclave in the cave The Cleft of Shadows beneath Orgrimmar, where all sorts '
                     'of outcasts who are unwelcome up on the surface gather.',
 ('Orc', 'Warrior'): 'Orc warriors form the backbone of the traditional military culture of the '
                     'Horde. They value personal strength, martial honor, trials and glory in '
                     'battle, and often serve in the armies of Orgrimmar and the Horde. They are '
                     'one of the most unconditionally respected castes in orcish society. They '
                     'receive their training and meet for practice in their own building, the Hall '
                     'of the Brave, in the Valley of Honor district of Orgrimmar.',
 ('Troll', 'Death Knight'): 'Troll death knights, after being freed from the Scourge, join the '
                            'Knights of the Ebon Blade. Their traditional connection with the '
                            'spirits and the loa now coexists with the necromantic nature of a '
                            'death knight, creating a stark contrast between their old '
                            'spirituality and the powers of death. They train and live in Acherus, '
                            "the Order's flying necropolis.",
 ('Troll', 'Hunter'): 'Troll hunters are closely tied to ancient traditions of hunting, tracking '
                      'and communing with nature. Many also adhere to the spiritual traditions of '
                      'their tribe and may turn to the loa for help and patronage. They live and '
                      "train in the troll village of Sen'jin Village on the southern coast of "
                      'Durotar.',
 ('Troll', 'Mage'): 'Troll magic users use arcane magic, even though traditional troll '
                    'spirituality is more connected with the loa and shamanism. They may study in '
                    'Dalaran or in Horde communities and treat magic as an acquired art. They live '
                    'and study in Darkbriar Lodge in the Valley of Spirits district of Orgrimmar.',
 ('Troll', 'Light Priest'): 'Troll Light Priests are unusual by most human notions of religion: '
                            'they usually serve the loa and gain spiritual power through the '
                            'worship of specific spirits. Their magic may be healing, but their '
                            'faith remains part of the ancient troll religious tradition rather '
                            'than of the Church of the Holy Light. They live and train in the '
                            'Spirit Lodge in the Valley of Spirits district of Orgrimmar.',
 ('Troll', 'Shadow Priest'): 'Troll Shadow Priests turn to the Shadow and The Void, perceiving '
                             'them through their own spiritual tradition and their knowledge of '
                             'the loa. Some may explore powers associated with the Old Gods, but '
                             'worship of the Void or the Old Gods should not be considered '
                             'mandatory for every Shadow priest. They often call their path "Dark '
                             'Voodoo" and themselves "Shadow Hunter", although behind this name '
                             'lies the very same The Void. They are condemned by society and '
                             'cannot gather publicly, but they have secret hideouts for meetings '
                             'and training in the caves of the Echo Isles.',
 ('Troll', 'Rogue'): 'Troll rogues use stealth, poison, ambush and knowledge of the jungle. They '
                     'may serve their tribe or the Horde, or act as hired assassins, combining '
                     'rogue practice with ancient troll combat traditions. Most troll rogues '
                     'belong to the Shadowswift Brotherhood organization and gather to share '
                     'experience and train in its secret lair in the cave Cleft of Shadow beneath '
                     'Orgrimmar.',
 ('Troll', 'Shaman'): 'Troll shamans preserve the ancient tradition of communing with spirits and '
                      'elementals and often revere the loa. Many are also connected with the '
                      'Earthen Ring, where troll spiritual traditions are combined with broader '
                      'shamanic practice. Shamans are respected in society, so they often study '
                      'and live in Grommash Hold, the main fortress of Orgrimmar, near the '
                      'Warchief.',
 ('Troll', 'Warrior'): 'Troll warriors serve their tribe and the Horde, preserving the ancient '
                       'combat traditions of the trolls. Their culture values physical strength, '
                       'hunting, personal bravery and the spiritual patronage of the loa. They '
                       'receive their training and meet for practice in their own building, the '
                       'Hall of the Brave, in the Valley of Honor district of Orgrimmar.',
 ('Tauren', 'Death Knight'): 'Tauren death knights, after being freed from the Scourge, join the '
                             'Knights of the Ebon Blade. Their existence is especially '
                             'contradictory to traditional tauren culture, which is founded on '
                             'respect for life, nature and the spiritual cycle, so many experience '
                             'a deep conflict between their past faith and their new nature. They '
                             "usually live and train in Acherus, the Order's flying necropolis.",
 ('Tauren', 'Druid'): 'Tauren druids follow the ancient tradition of druidism and are connected '
                      'with the Cenarion Circle. They revere nature, the Earth Mother and the '
                      'ancient spirits, strive to preserve balance, and are especially closely '
                      'tied to the revival of druidism among the Horde. They are highly respected '
                      'in tauren society and have their own place for study, meditation and '
                      'socializing in the Hall of Elders on Elder Rise in Thunder Bluff.',
 ('Tauren', 'Hunter'): 'Tauren hunters follow a tradition of hunting, survival and respect for '
                       'nature. The hunt is seen not simply as the killing of beasts, but as part '
                       'of the natural cycle and a way to live in harmony with the surrounding '
                       'world. They have their own camp for training, meetings and sharing '
                       "experience in the Hunter's Hall on Hunter Rise in Thunder Bluff.",
 ('Tauren', 'Shaman'): 'Tauren shamans are spiritual intermediaries between their people, the '
                       'elements and the ancestors. They are closely tied to the Earthen Ring and '
                       'to the tradition of revering the Earth Mother, perceiving the elements as '
                       'living forces with which balance must be maintained. They usually study '
                       'and exchange wisdom with more experienced shamans in the Hall of Spirits '
                       'on Spirit Rise in Thunder Bluff.',
 ('Tauren', 'Warrior'): 'Tauren warriors defend their tribes and the Horde, combining physical '
                        'strength with traditions of tribal honor. They usually see war as a '
                        'necessity for protecting their people rather than as an end in itself. '
                        "They train and learn from the elders in the Hunter's Hall on Hunter's "
                        'Rise in Thunder Bluff.',
 ('Undead', 'Death Knight'): 'Forsaken death knights, after being freed from the Scourge, join the '
                             'Knights of the Ebon Blade. Their experience of being turned into '
                             'undead and then freed makes them especially familiar with the loss '
                             'of free will; however, they now use the powers of death against the '
                             "Lich King's army. They usually train and live in Acherus, the "
                             "Order's flying necropolis.",
 ('Undead', 'Mage'): 'Forsaken mages use arcane magic, preserving the knowledge they gained while '
                     'still alive. Many are connected with the magical traditions of Lordaeron or '
                     'Undercity and see magic as a practical tool that does not depend on their '
                     'current undead state. They study and train in the huge Ziggurat in the '
                     'middle of the Magic Quarter in Undercity, where no one will disturb them, '
                     'however cruel the experiments they conduct.',
 ('Undead', 'Light Priest'): 'Forsaken Light Priests continue to worship the Holy Light despite '
                             'their undead state. The Light causes them physical pain, but some '
                             'consider serving the Light a way to preserve the remnants of their '
                             'former personality and humanity. They often face condemnation or '
                             'incomprehension in Forsaken society, which is dominated by cruelty '
                             'and an inclination to ally with the darkest forces. They study and '
                             'share experience in the War Quarter in Undercity.',
 ('Undead', 'Shadow Priest'): 'Forsaken Shadow Priests use the Shadow and The Void and often '
                              'regard the Light with distrust after their death and resurrection. '
                              'They may study the powers of the Void and the Old Gods, perceiving '
                              'darkness as a natural force that is better suited to their '
                              'existence. They are usually part of the Cult of the Forgotten '
                              'Shadow, which preaches a balance of forces and using the Void for '
                              "one's own ends. Although the followers of the Light deem the cult "
                              'heretical, unlike other races, the Forsaken do not need to hide '
                              'their study of The Void, and they can openly study and share '
                              'experience in the War Quarter in Undercity.',
 ('Undead', 'Rogue'): 'Forsaken rogues make extensive use of stealth, poison, espionage and '
                      'assassination. They are especially well suited to Forsaken covert '
                      'operations and may work for Sylvanas and her intelligence services. They '
                      "often belong to the Deathstalkers, Sylvanas's elite organization of "
                      "personal spies. They are based in the Rogues' Quarter in Undercity, where "
                      'they train newcomers and share experience.',
 ('Undead', 'Warlock'): 'Forsaken warlocks use demonic magic and summon creatures of the Burning '
                        'Legion. Their practice fits well with the pragmatic and ruthless attitude '
                        'of the Forsaken toward forbidden magic, although even among the undead '
                        'such powers remain dangerous. They often belong to the Dreadriders, an '
                        'organization of undead warlocks. They study and train in the huge '
                        'Ziggurat in the middle of the Magic Quarter in Undercity, where no one '
                        'will disturb them, however cruel the experiments they conduct. Unlike '
                        'other races, Forsaken warlocks do not need to hide and can practice any '
                        'dark magic openly.',
 ('Undead', 'Warrior'): 'Forsaken warriors serve the military forces of Undercity and the Horde. '
                        'They use their bodies, which no longer feel fatigue and pain the way the '
                        'living do, as a weapon against the enemies of the Forsaken. They train '
                        'and live in the War Quarter in Undercity.',
 ('Blood Elf', 'Death Knight'): 'Blood elf death knights, after being freed from the Scourge, join '
                                'the Knights of the Ebon Blade. Many of them have a past in the '
                                "army of Quel'Thalas or among the Blood Knights, which makes their "
                                'use of necromantic power an especially grim contrast to their '
                                'service to their people. They are not welcome in Silvermoon, so '
                                'their main base is Acherus, the flying necropolis where the '
                                'Knights of the Ebon Blade live and train.',
 ('Blood Elf', 'Hunter'): 'Blood elf hunters are traditionally connected with the Farstriders — '
                          "the elite ranger order of Quel'Thalas. The Farstriders protect the "
                          'lands and the people of the blood elves, relying on marksmanship, '
                          "scouting and a bond with nature; since Quel'Thalas joined the Horde, "
                          "many serve the Horde's interests. Their main base is Farstrider Retreat "
                          '- a small outpost in Eversong Woods where young Farstriders live and '
                          "train. They also have Rangers' Lodge - a small base in Silvermoon, on Farstrider's "
                          'Square, where they can train and hold meetings without leaving the '
                          'city. The leader of the Farstriders is Ranger-General Halduron '
                          'Brightwing.',
 ('Blood Elf', 'Mage'): "Blood elf mages come from the ancient magical tradition of Quel'Thalas "
                        'and most often are part of The Magisters - an elite society and '
                        'influential political faction of blood elf sorcerers. They regard arcane '
                        'magic as the most important part of high elven culture and as a means of '
                        "protecting their people. Their main base is Magisters' Terrace on the "
                        "Isle of Quel'Danas, but since it is currently partially destroyed and "
                        "occupied by the traitor Kael'thas Sunstrider, who has defected to the "
                        'side of the demons, the Magisters are temporarily living and training in '
                        'Sunfury Spire - a huge, beautiful tower and the main palace complex of '
                        'Silvermoon, which houses one of the largest libraries of books on magic '
                        'in Azeroth. Their leader is Grand Magister Rommath.',
 ('Blood Elf', 'Paladin'): 'Blood elf paladins belong to the Blood Knights — an elite paladin '
                           'order based in Silvermoon and one of the main military and political '
                           "forces of the kingdom of Quel'Thalas. The Blood Knights wield the Holy "
                           'Light and fight for Silvermoon, the blood elves and the Horde in all '
                           'conflicts. Their main headquarters and place of training and study is '
                           "the Hall of Blood on Farstriders' Square in Silvermoon. Their leader "
                           'is Matriarch Lady Liadrin',
 ('Blood Elf', 'Light Priest'): 'Blood elf Light Priests serve the Holy Light and are '
                                'traditionally connected with the religious communities of '
                                'Silvermoon. Having restored their connection with the Light, they '
                                'perceive it as a sacred force that blood elves can use to heal '
                                'and protect their people. They study, live and serve in Sunfury '
                                'Spire - a huge, beautiful tower and the main palace complex of '
                                'Silvermoon.',
 ('Blood Elf', 'Shadow Priest'): 'Blood elf Shadow Priests study the Shadow and The Void, turning '
                                 'to forces that are opposed to the traditional Holy Light. They '
                                 'may explore forbidden knowledge about the Void and the Old Gods, '
                                 'but they do not necessarily belong to an organized cult. The '
                                 'study of The Void has always been condemned and despised in '
                                 'blood elf society, and one of its current leaders, Grand '
                                 'Magister Rommath, is a staunch opponent of the Void and has '
                                 'strictly outlawed its practitioners. As a result, Shadow Priests '
                                 'are forced to carefully hide the fact that they study the dark '
                                 "sciences from both the guards and the city's residents. However, "
                                 'several secret clubs devoted to the study of The Void operate in '
                                 'Murder Row in Silvermoon - some to help Silvermoon, others for '
                                 'more selfish goals.',
 ('Blood Elf', 'Rogue'): 'Blood elf rogues are often connected with the Farstriders, with '
                         "Silvermoon's scouts, or with independent agents carrying out secret "
                         'assignments. Their skills in stealth and assassination suit the '
                         "political and military struggle of Quel'Thalas well. In Silvermoon, the "
                         'scheming nobility always has a demand for agents capable of secretly '
                         'eliminating a rival or obtaining illegal magical artifacts. In Murder '
                         'Row in Silvermoon there is the secret club "Students of Shadow", where '
                         'Rogues can train, share experience and take on new contracts.',
 ('Blood Elf', 'Warlock'): 'Blood elf warlocks use demonic magic as one of many dangerous ways of '
                           "obtaining energy. After the catastrophe of Quel'Thalas, this practice "
                           'is seen as a pragmatic means of survival, although many residents of '
                           'Silvermoon regard warlocks with distrust. Despite the absence of a '
                           'direct ban, warlocks prefer not to provoke the citizens of Silvermoon, '
                           'rarely leaving the gloomy streets of the most dangerous district, '
                           '"Murder Row", where they most often study, live and share experience '
                           'in the club "The Sanctum".'}

# Race -> topics a bot of that race may raise.
RACE_TOPICS = {'Human': ['Reminisce about the cozy taverns of Stormwind and the variety of food and drink.',
           'Compare different kinds of ale from the human kingdoms.',
           'Miss the smell of fresh bread in human cities.',
           'Reminisce about the bustling markets of Stormwind.',
           'Tell which part of Stormwind you like best.',
           "Argue about which human architecture is more beautiful — Stormwind's (more "
           "down-to-earth and cozy) or Lordaeron's (more Gothic and luxurious).",
           'Reminisce about the countryside of Elwynn Forest.',
           'Tell about family farms and villages.',
           'Compare life in the city and in the countryside.',
           'Reminisce about fairs, holidays and folk festivities.',
           'Talk about a favorite human dish.',
           'Complain about how expensive it has become to live in big cities.',
           'Reminisce about old inns that are now closed.',
           'Recall Lordaeron before the Third War.',
           'Tell what Stratholme was like before the plague.',
           'Talk about the abandoned lands of Lordaeron.',
           "Recall your parents' stories about the Second War.",
           'Argue about how much Alterac has changed.',
           'Tell family stories about the wars with the orcs.',
           'Recall people who never returned from Lordaeron.',
           'Discuss the fate of the old human kingdoms (Lordaeron was destroyed by the undead, '
           'Alterac was destroyed by other humans for its alliance with the orcs in the Second '
           'War, Gilneas walled itself off from the world with a great wall and isolated itself).',
           'Talk about ruined cities you would like to see restored (Alterac, Lordaeron, '
           'Stratholme).',
           'Complain about portal services being too expensive.',
           'Discuss the quality of human blacksmiths.',
           'Argue about which human cuisine is better.',
           'Recall a favorite bard song.',
           'Tell about an unusual person you met while traveling.',
           'Compare human habits with the habits of other races.',
           'Marvel at how many different accents humans have.'],
 'Dwarf': ['Miss the coolness and the stone halls of Ironforge.',
           'Recall the hum of the Great Forge.',
           'Talk about a favorite tavern in Ironforge.',
           'Argue about where in Ironforge the best ale is served.',
           'Recall the smell of the forge.',
           'Tell about a favorite spot near the Great Forge.',
           'Complain that some cities have too much open space.',
           'Talk about how much cozier stone rooms are than wooden ones.',
           'Argue about which ale is better.',
           'Tell about unusual varieties of dwarven beer.',
           'Recall an especially good drinking bout.',
           'Complain about drinks that "elves call beer". Compare them with other liquids.',
           'Tell how to cook meat properly.',
           'Argue about which game is tastier.',
           'Recall festive feasts.',
           'Discuss how many mugs of ale one can drink before the hall starts spinning.',
           'Miss the cold mountain tunnels.',
           'Tell about a beautiful mine you once got to see.',
           'Discuss rare minerals.',
           'Boast about ore you have found.',
           'Recall a successful expedition.',
           'Tell about a deep mine that no one wants to go down into anymore.',
           "Joke that dwarves don't need stairs — just wider steps.",
           'Complain about tables that are too high.',
           "Tell what it's like to travel alongside tall races.",
           'Discuss beards.',
           'Boast about the length of your beard.',
           'Argue about proper beard care.',
           'Tell a family story about a famous ancestor.'],
 'Gnome': ['Recall old Gnomeregan before the catastrophe.',
           'Tell about a favorite workshop.',
           'Recall the unusual mechanisms left behind in Gnomeregan.',
           'Argue about which level of Gnomeregan was the most interesting.',
           'Talk about what Gnomeregan could become after it is restored.',
           'Recall old engineers.',
           'Tell about the first serious breakdown of your own invention.',
           'Discuss a favorite type of mechanism.',
           'Boast about a recently built device.',
           'Complain about devices that are too reliable.',
           "Explain why an exploding mechanism isn't necessarily a bad thing.",
           'Argue about the merits of gnomish versus dwarven engineering.',
           'Recall the biggest explosion of your life.',
           'Tell about a failed experiment.',
           'Discuss why invent something simple when you can make something complicated.',
           'Come up with improvements for ordinary objects.',
           'Discuss the idea of mechanical transport.',
           'Express contempt for unreliable and dangerous goblin engineering.',
           'Complain about chairs that are too big.',
           'Tell how inconvenient it is to use things made for larger races.',
           'Joke that gnomes are the best at saving space.',
           'Argue about which sound is more pleasant: the whirring of a mechanism or an explosion.',
           'Tell how being small makes it easier to dodge attacks in combat.'],
 'Night Elf': ['Recall Teldrassil before its destruction.',
               'Talk about the beauty of the night forests.',
               'Miss the quiet of Darnassus.',
               'Reminisce about walks under the stars.',
               'Tell about a favorite corner of Kalimdor.',
               'Talk about ancient groves.',
               'Recall the scent of night-blooming flowers.',
               'Compare different forests of Azeroth (Teldrassil, Ashenvale, Feralas, Darkshore).',
               'Recall stories that have survived for thousands of years.',
               'Tell about ancient ruins.',
               'Discuss old legends about the night elves.',
               'Recall ancient heroes.',
               'Reflect on how Kalimdor has changed.',
               'Talk about places that were sacred to the ancestors.',
               'Recall old songs.',
               'Tell about a favorite tree.',
               'Talk about an unusual animal you encountered in the forest.',
               'Discuss the night sounds of the forest.',
               'Miss the rain in the forest.',
               'Talk about moonlight.',
               'Tell about a beautiful glade.',
               'Complain about how other races treat nature.',
               'Reminisce about walks in Moonglade and how good it is that this place has '
               'preserved its beautiful nature by closing it off to most of the unworthy.',
               'Tell about a favorite spot for stargazing.',
               'Discuss the constellations.',
               'Talk about hunting at night.',
               'Recall quiet nights by the campfire.',
               'Recall the night sky of Kalimdor.'],
 'Draenei': ['Recall the Exodar before the catastrophe.',
             'Tell about unusual chambers of the Exodar.',
             'Discuss the strange technologies of the draenei.',
             'Miss the peaceful halls of the Exodar.',
             'Talk about a favorite place on the islands of Azuremyst Isle.',
             'Recall the crystalline structures.',
             'Tell about strange mechanisms that even the draenei still do not understand.',
             'Recall Draenor before its destruction.',
             'Tell stories about Nagrand.',
             'Miss the old sky of Draenor.',
             'Talk about the beauty of old Nagrand.',
             'Recall the homeland.',
             'Compare old Draenor with present-day Outland.',
             'Talk about what Draenor could have become if it had not been destroyed.',
             'Recall the old draenei settlements.',
             'Tell family stories about life before arriving on Azeroth.',
             'Discuss unusual crystals.',
             'Tell about a favorite crystal ornament.',
             'Talk about how crystals are used in everyday life.',
             'Discuss the power of the Light.',
             'Tell about spiritual mentors.',
             'Recall ancient prayers.',
             'Talk about the Naaru and the special divine Light that emanates from them.'],
 'Orc': ['Reminisce about the noisy streets of Orgrimmar.',
         'Argue about where in Orgrimmar the best grog is.',
         'Talk about a favorite spot by the campfires.',
         'Discuss the forges of Orgrimmar.',
         'Complain about the dust in Orgrimmar.',
         'Recall your first days in the Valley of Trials and how you went through the trials to '
         'earn the status of an adult.',
         'Tell about a favorite weaponsmith.',
         'Recall old Draenor.',
         'Tell about the life of the clans before the world was destroyed.',
         'Talk about Nagrand.',
         'Recall the old hunting grounds.',
         'Tell about the traditions of your clan.',
         'Argue about which clan was the strongest.',
         'Recall old orcish songs.',
         'Talk about the ancestors.',
         'Tell the story of a famous chieftain.',
         'Tell about training.',
         'Argue about favorite weapons.',
         'Tell about training.',
         'Recall your first real battle.',
         'Boast about a victory over a strong opponent.',
         'Discuss the concept of honor.',
         'Tell about an old mentor.',
         'Argue about what matters more — strength or endurance.',
         'Discuss meat.',
         'Argue about the best way to cook a boar.',
         'Complain about the portions being too small in Blood Elf taverns.',
         'Talk about which beasts are the most dangerous.'],
 'Troll': ['Recall life on the Echo Isles.',
           'Tell about your home village.',
           'Talk about old tribal customs.',
           'Recall the elders.',
           'Tell about traditional festivals.',
           'Discuss old masks and ornaments.',
           "Talk about the tribe's favorite dish.",
           'Recall the old hunting grounds.',
           'Tell stories about the loa.',
           'Argue about which loa is stronger.',
           'Recall an unusual dream.',
           'Talk about omens.',
           'Discuss ancestral spirits.',
           'Tell about a strange ritual.',
           'Recall a priest who once gave useful advice.',
           'Talk about how to tell that a spirit is trying to warn you.',
           'Recall a successful ambush.',
           'Talk about the tracks of an unusual creature.',
           'Discuss a favorite fishing spot.',
           'Tell a scary story about a predator.',
           'Joke about long tusks.',
           "Complain that other peoples don't understand the troll accent.",
           'Tease the blood elves for their squeamishness.',
           'Discuss which of your friends can eat the most meat.'],
 'Tauren': ['Miss the green plains of Mulgore.',
            'Recall sunrises over the plains.',
            'Talk about the tranquility of the homeland.',
            'Tell about a favorite spot by the watering hole.',
            'Reminisce about walks across the steppes.',
            'Compare different pastures.',
            'Talk about the smell of grass after rain.',
            'Tell about an old tree that remembers your childhood.',
            'Talk about treating prey with respect.',
            'Recall an old hunter who was your mentor.',
            'Tell about your most difficult tracking.',
            'Discuss unusual animal behavior.',
            'Tell stories about the ancestors.',
            'Talk about the spiritual side of the hunt.',
            'Recall the advice of the elders.',
            'Discuss the signs of nature.',
            'Talk about sacred places.',
            "Recall the tribe's ceremonies.",
            'Discuss the best places to sleep under the open sky.',
            'Complain about rooms that are too cramped in the taverns of other races.',
            'Talk about a favorite herbal blend.',
            'Recall the taste of fresh milk.',
            'Compare different kinds of tea and what they are best blended with.',
            'Complain about the chairs of other races being too small.'],
 'Undead': ['Recall Lordaeron before its destruction.',
            'Tell about life in the old kingdom.',
            'Recall the streets of old Lordaeron.',
            'Talk about Lordaeron before the Plague.',
            'Tell what Stratholme used to look like.',
            'Recall the old inns.',
            'Talk about people you once knew in life.',
            'Recall your family.',
            'Tell about the forgotten places of Lordaeron.',
            'Recall the farms of Lordaeron, now abandoned and ravaged.',
            'Reminisce about the noisy, happy carnivals in Lordaeron before the undead laid it '
            'waste.',
            'Reminisce about the bustling bazaars and fragrant pastries of Stratholme before '
            'Arthas destroyed the city and slaughtered its inhabitants.',
            'Tell how after the plague giant spiders appeared in Tirisfal Glades, although before '
            'that these had been fairly calm and safe woods.',
            'Complain about no longer being able to taste food.',
            'Recall a favorite dish that is now impossible to taste.',
            'Joke about problems with smells.',
            "Discuss what to do if you've lost a finger.",
            'Complain about the condition of your bones.',
            'Discuss how long one can go without sleep.',
            'Joke that death has greatly simplified some everyday problems.',
            'Recall what it was like to feel cold.',
            'Talk about which sensations disappeared after death.',
            'Joke about your own death.',
            'Discuss who looks the most alive among the undead.',
            'Tell a story about a limb that accidentally fell off.',
            'Argue about how well your face has been preserved.',
            'Joke about necromancers.',
            'Tell about the most ridiculous way to lose a body part.',
            'Recall life before death.',
            'Try to remember a forgotten name.',
            'Tell about a dream in which you were alive again.',
            'Talk about an old song that no one has performed in a long time.',
            'Recall the smell of your home.',
            'Tell about a person who has long been gone even from among the dead.',
            'Complain that everyone sees you as a rotting monster and is disgusted by you, '
            'although in fact you still have thoughts and feelings.'],
 'Blood Elf': ['Reminisce about the fine selection of wines in the taverns of Silvermoon City.',
               'Argue about which tavern serves the best drink.',
               'Reminisce about evening strolls through the streets of Silvermoon City.',
               'Tell about the most beautiful building in the city.',
               'Complain that other cities look too gray.',
               'Recall the music playing in the taverns.',
               'Talk about the fountains and gardens of Silvermoon City.',
               'Discuss a favorite district of the city.',
               'Recall the magical lights of the streets.',
               "Compare Silvermoon City with Dalaran (in Silvermoon's favor).",
               'Talk about how much Silvermoon City has changed since the Third War.',
               'Recall the underground trade in Fel Magic crystals in Silvermoon City',
               "Recall the forests of Quel'Thalas before the Scourge.",
               'Tell about walks in the forest.',
               'Talk about old elven ruins.',
               "Recall the taste of fruit from Quel'Thalas.",
               'Tell about a favorite spot by the lake.',
               'Miss the old songs.',
               'Recall family homes.',
               'Talk about sunsets over the forest.',
               'Discuss magical jewelry.',
               'Boast about your skill in wielding magic.',
               'Tell about a beautiful spell.',
               'Discuss the use of magic in everyday life.',
               'Tell about magical items.',
               'Recall your first encounter with a magical artifact.',
               'Argue about beautiful clothes.',
               'Discuss jewelry.',
               'Talk about hairstyles.',
               'Complain about the crude appearance of other races.',
               'Discuss favorite clothing colors.',
               'Tell about expensive fabrics.',
               'Argue about which gemstone is more beautiful.',
               'Talk about perfumery.',
               'Recall a favorite shop in Silvermoon City.',
               'Complain about the disgusting food of other races',
               'Complain about the unsanitary conditions in orc taverns',
               'Complain that orcs and trolls rarely bathe']}

# Class style -> topics a bot of that class may raise.
CLASS_TOPICS = {'Warrior': ['Recall their first real battle.',
             'Talk about an opponent who turned out to be stronger than expected.',
             'Recall a battle after which it took several weeks to heal the wounds.',
             'Argue about which weapon is best for real combat.',
             'Discuss the advantages of an axe over a sword.',
             'Brag about an especially heavy weapon they managed to lift.',
             'Talk about the biggest shield they ever had to carry.',
             'Recall a battle where a shield saved a life.',
             'Talk about an opponent they managed to defeat thanks to patience.',
             'Discuss whether it is worth wearing heavy armor on a long expedition.',
             'Complain about how uncomfortable it is to sleep in a full suit of armor.',
             'Talk about how hard it is to repair armor after a real battle.',
             'Recall their first mentor.',
             'Talk about their toughest training session.',
             'Discuss how many hours a day one should train.',
             'Argue about whether strength or technique matters more.',
             'Talk about an unusual way of training.',
             'Brag about their stamina.',
             'Discuss training dummies.',
             'Recall their first serious injury in training.',
             'Talk about a training weapon that turned out to be more dangerous than a real one.',
             'Argue about what matters more: courage or caution.',
             'Talk about the best commander they have had.',
             'Recall the most poorly organized squad.',
             'Discuss what it is like to guard someone who constantly gets into trouble.',
             'Complain about mages who use a warrior as a living shield.',
             'Discuss how useful it is to be able to fight without a weapon.',
             'Talk about a tavern brawl.',
             'Recall a time when they had to fight with a completely unsuitable weapon.',
             'Complain about the constant need to repair armor.',
             'Look for a good blacksmith.',
             'Argue about where weapons are sharpened best.',
             'Discuss how comfortable different types of armor are.',
             'Complain that taverns have too few sturdy chairs.',
             'Talk about their habit of sharpening their weapon before going to sleep.'],
 'Paladin': ['Recall the moment they first felt the Light.',
             'Talk about their mentor.',
             'Discuss what it means to be worthy of the Light.',
             'Reflect on whether the Light can help a person who has lost hope themselves.',
             'Recall a prayer they used to recite in childhood.',
             'Discuss why some people find faith easily and others do not.',
             'Talk about a place where the Light can be felt especially strongly.',
             'Argue about what matters more for a paladin - faith or discipline.',
             'Recall a time when the Light saved a life.',
             'Talk about a person they managed to heal.',
             'Talk about their first service.',
             'Recall the first time they had to protect someone truly important.',
             'Discuss what it means to be a shield for others.',
             'Complain that people take protection for granted.',
             'Recall the hardest choice between orders and conscience.',
             'Talk about a fallen comrade.',
             "Discuss a commander's responsibility.",
             'Argue about when a paladin has the right to retreat.',
             'Argue about which weapon suits a paladin best.',
             'Talk about their favorite hammer.',
             'Discuss how important a shield is.',
             'Recall their first set of real armor.',
             'Talk about a famous paladin weapon.',
             'Discuss the differences between a holy paladin and an ordinary warrior.',
             'Complain about the weight of a full suit of armor.',
             'Recall life in the order.',
             'Talk about the training of young paladins.',
             'Argue about discipline.',
             'Discuss how strict a mentor should be.',
             'Talk about temple ceremonies.',
             'Recall a service that far too many people attended.',
             'Discuss how a paladin can rest without forgetting their duty.'],
 'Hunter': ['Talk about the most beautiful place for hunting.',
            'Recall a dawn in the forest.',
            'Discuss the tracks of different animals.',
            'Talk about a rare beast they managed to see.',
            'Argue about which region is best suited for hunting.',
            'Recall a hunt that lasted several days.',
            'Talk about a beast that turned out to be smarter than the hunter.',
            'Discuss how to tell that a beast is approaching by the sounds of the forest.',
            'Complain about hunters who do not respect nature.',
            'Talk about their first pet.',
            'Recall how they managed to tame an especially dangerous beast.',
            "Discuss their pet's favorite food.",
            'Complain about a pet that keeps running away.',
            "Talk about their beast's temperament.",
            'Compare different animal companions.',
            'Argue about which animal is best suited for a long journey.',
            'Tell a funny story about their pet.',
            'Recall a beast they had to let go.',
            'Compare bows and crossbows against firearms.',
            'Talk about their longest accurate shot.',
            'Argue about the advantages of the bow and the crossbow.',
            'Recall the first arrow they made themselves.',
            'Complain about a bad bowstring.',
            'Talk about a marksmanship contest.',
            'Discuss shooting in strong wind or a blizzard.',
            'Talk about the best place to set up camp.',
            'Discuss how to identify a safe place to spend the night.',
            'Recall their coldest overnight stay.',
            'Complain about people who make noise during a hunt.',
            'Talk about the tracks of an unknown creature.',
            'Discuss which zones of Azeroth are best suited for wandering.'],
 'Rogue': ['Talk about their most successful infiltration of a guarded place.',
           'Recall a time when they were almost caught.',
           'Discuss which place is the hardest to guard.',
           'Argue about what matters more for stealth - patience or speed.',
           'Talk about the most attentive guard.',
           'Recall a place that turned out to be much better protected than expected.',
           "Discuss how to spot the guards' blind spot.",
           'Complain about armor that is too noisy.',
           'Talk about a valuable they managed to steal.',
           'Brag about an especially complicated lock.',
           'Talk about the first chest they picked open on their own.',
           'Discuss the most cunning traps.',
           'Recall a locked chest they had to leave behind because its lock was too complicated.',
           'Argue about who makes better locks - gnomes, dwarves or goblins.',
           'Talk about an unusual item found in a locked chest.',
           'Discuss how to tell that a chest was deliberately left as a trap.',
           'Discuss their favorite poison.',
           'Talk about their most unpleasant experience with poison.',
           'Argue about which poison is the hardest to make.',
           'Complain about bad ingredients.',
           'Tell how they accidentally mixed up vials of poison and potions.',
           'Discuss the smell of various alchemical mixtures.',
           'Recall a former employer.',
           'Talk about a strange client.',
           'Discuss the worst theft job they ever had to do.',
           'Recall a theft contract that turned out to be something completely different from what '
           'it seemed.',
           'Talk about a gang they had to deal with.',
           'Discuss who cannot be trusted.',
           'Argue about how good a criminal someone can be if they love to talk too much.',
           'Complain about pockets without inner compartments.',
           'Talk about their favorite cloak.',
           'Discuss comfortable footwear for walking silently.',
           'Argue about how suspicious it is to look too suspicious.',
           'Joke that a good rogue should be able to disappear even before appearing.'],
 'Light Priest': ['Recall their first experience of turning to the Light.',
                  'Talk about a prayer that they remember especially well.',
                  'Discuss how a person finds faith after a traumatic event.',
                  'Talk about a miraculous healing.',
                  'Recall a person they managed to save.',
                  'Discuss whether the Light can help someone who does not believe in themselves.',
                  'Talk about a temple where it is especially pleasant to pray.',
                  'Compare the religious traditions of different peoples.',
                  'Argue about whether one needs to understand the Light in order to serve it.',
                  'Ponder the difference in how the Light is perceived in the Alliance and in the '
                  'Horde.',
                  'Discuss the difference between faith and hope.',
                  'Recall the most severe wound they ever had to heal while on duty.',
                  'Discuss how important it is to calm a wounded person before healing them.',
                  'Complain about fighters who ask for help too late.',
                  'Recall their first serious mistake while healing.',
                  'Talk about an unexpectedly resilient patient they tried to heal.',
                  'Discuss how to heal someone who is afraid of healers.',
                  'Argue about what matters more: healing the body or the spirit.',
                  'Discuss discipline during priestly rituals.',
                  "Talk about controlling one's own emotions for the sake of serving the Light.",
                  'Recall a strict mentor at the Temple where they studied.',
                  'Argue about when obedience becomes blind submission, and when it is an '
                  'important part of serving the Light.',
                  'Reflect on the price of self-discipline.',
                  'Discuss how to stay calm during a panic.',
                  'Talk about a time when discipline and calm saved the group.',
                  'Discuss temple traditions.',
                  'Recall a religious holiday.',
                  'Talk about old prayers.',
                  'Argue about the differences between the temples of different peoples.',
                  'Discuss why some people are afraid of priests.',
                  'Recall an old priest who was their mentor.',
                  'Talk about beautiful temple music.',
                  'Reflect on why they find it so pleasant to take care of others.'],
 'Shadow Priest': ['Reflect on the nature of fear.',
                   'Discuss why people are afraid of the dark.',
                   "Tell how they managed to break an enemy's will by sending terrifying visions "
                   'upon that enemy.',
                   'Tell how a sufficiently horrifying illusion can win a battle even without '
                   'dealing real damage to the enemy.',
                   "Discuss how, in combat, it is far more important to damage the enemy's mind "
                   'and soul than their body.',
                   "Tell how, during a battle, they managed to look into an enemy's soul and see "
                   "that enemy's most horrifying fear there.",
                   "Tell how they entered an enemy's dream and turned it into a nightmare.",
                   'Tell how, at a single glance from them, opponents were filled with terror and '
                   'fled the battlefield.',
                   'Talk about their most terrifying dream.',
                   'Recall a moment when their own mind failed them.',
                   'Discuss how easy it is to instill fear in a person.',
                   'Argue about whether fear can be defeated by fully understanding it.',
                   'Talk about an enemy who turned out to be immune to fear.',
                   'Discuss why some people seek out danger themselves.',
                   'Describe the sensation of being in total darkness.',
                   'Discuss the difference between ordinary shadow and The Void.',
                   'Talk about their first experience of touching The Void.',
                   'Discuss whether one can use The Void without letting it change oneself.',
                   'Talk about strange visions.',
                   'Discuss the voices that can be heard during severe exhaustion.',
                   'Reflect on the boundary between insight and madness.',
                   "Discuss whether madness always means losing one's mind.",
                   'Recall a person who spoke nonsense but turned out to be right.',
                   'Talk about their own strangest vision.',
                   'Discuss why some people fear those who talk about The Void.',
                   'Argue about whether one can stay sane while peering into forbidden knowledge.',
                   'Talk about a person who was not at all afraid of dying but had a different '
                   'fear, which was successfully used against them.',
                   'Talk about the whisper of thousands of voices in their head: individually the '
                   'voices are vague and blurred, but together they merge into intelligible speech',
                   'Tell how they once went without sleep for several weeks, reading hundreds of '
                   'ancient manuscripts devoted to The Void, until they heard a whisper in their '
                   'head telling them forgotten knowledge',
                   'Tell that in their dreams they often see the grand black granite walls of '
                   "Ny'alotha, the forgotten and sunken city",
                   "Say that the voice in their head told them about Ny'alotha, an ancient city "
                   'that existed long before everything known to us. It was not what we now '
                   'understand as a city; perhaps it was not even material, but it was the ideal '
                   'of creation, a cradle... for what? Or for whom?',
                   'Tell that in their dreams they often see events and places from the past, but '
                   'the dreams change the details, twist and distort the memories, and they no '
                   'longer know which memories are real and which merely came to them in dreams',
                   'Complain about the voices inside that constantly whisper, speak, scream, '
                   'plead, demand',
                   'Say that they can no longer tell what they read in ancient manuscripts from '
                   'what the voices whispered to them',
                   'Recall that they were once in a vast, empty library where the bookcases were '
                   'so tall that their tops were lost in darkness. But they cannot remember at all '
                   'where this library was or when they visited it',
                   'Tell that recently, during a rest stop, they closed their eyes and saw an '
                   'ancient city, and it was filled with a Darkness that came from beyond. And '
                   'when they opened their eyes, everything was as usual',
                   'Recall reading a manuscript about ancient peoples whose souls were sacrificed '
                   'to the darkness. But when did they read this manuscript? Yesterday? A week '
                   'ago? A year ago? Ten years ago? Where did they even find this manuscript? All '
                   'is dark. Time has blurred together.',
                   'Say that the voices whisper that the heart of the drowned god is black ice',
                   'Share that sometimes it seems to them that everything is only a dream',
                   'Say that it seems to them that all of this has already happened and is now '
                   'repeating again. Maybe for the second time. Maybe for the tenth. Time has been '
                   'lost and tangled',
                   'Say that they resist. They cling to life as if it matters. No matter, they '
                   'will learn the truth yet',
                   'Say that only mad creatures roam the streets of the sunken, sleeping city',
                   'Say that in a dream they saw the souls of ancestors. The tormented souls of '
                   'the ancestors clung to the living, convulsed in a silent scream. It seems '
                   'there are quite a lot of them',
                   'Say that they remembered being in a gigantic cave where every wall was '
                   'swarming with carnivorous insects. But they do not remember whether it really '
                   'happened or was only a dream',
                   'Say that in a dream they saw grand black granite halls. There was neither '
                   'light nor mercy in them - only emptiness and fear'],
 'Death Knight': ['Recall who they were in life before becoming a death knight.',
                  'Talk about a place they remembered especially well after death.',
                  'Recall an old friend.',
                  'Talk about a favorite food they can no longer taste.',
                  'Recall the scents of their past life.',
                  'Talk about what changed after becoming a death knight.',
                  'Discuss how strange it is to see familiar places through undead eyes.',
                  'Talk about their first awakening after death.',
                  'Discuss the feeling of constant cold.',
                  'Recall the first time they realized they could no longer feel warmth.',
                  'Talk about the strange beauty of frost magic.',
                  'Argue about which is colder — Northrend or the heart of a living enemy.',
                  'Talk about ice that never melts.',
                  'Discuss a favorite place among the icy plains.',
                  'Talk about their runeblade.',
                  'Discuss the first rune they managed to use.',
                  'Argue about the advantages of different runes.',
                  'Recall creating a weapon.',
                  'Talk about an unusual weapon they happened to see.',
                  'Discuss the difference between an ordinary sword and a runeblade.',
                  "Recall the time under the Lich King's rule.",
                  'Talk about the loss of their own will.',
                  'Discuss what it means to be free after slavery.',
                  'Talk about their first independent decision after being freed.',
                  'Recall those who could not break free.',
                  'Discuss how the living regard death knights.',
                  'Complain that the living too often look at them with fear.',
                  'Recall returning to their hometown after becoming a death knight, only for '
                  'everyone to look at them with fear and disgust.',
                  "Tell how, after being freed from the Lich King's control, they learned that all "
                  'their old friends had either died or turned away from them.',
                  'Talk about the eternal hunger they cannot satisfy.',
                  'Talk about the rage that flares up in their mind and the urge to destroy the '
                  'living, which they are forced to suppress by force of will.',
                  'Joke about being unable to smell rotten meat.',
                  'Discuss whether a death knight needs to sleep.',
                  'Complain about having to maintain armor they can no longer feel.',
                  'Talk about life inside the necropolises - enormous flying fortresses that house '
                  'death knight bases.',
                  'Talk about Acherus (The Ebon Hold) - a huge flying necropolis fortress that '
                  "serves as the base of the death knights who are free from the Lich King's "
                  'control.'],
 'Shaman': ['Talk about their first conversation with a spirit.',
            'Discuss the temperament of fire.',
            'Argue about which element is the most unpredictable.',
            'Talk about a powerful thunderstorm.',
            'Recall the first time they managed to call down lightning.',
            'Discuss why water seems calm yet can be more dangerous than fire.',
            'Talk about the spirit of the wind.',
            'Talk about an unusual natural phenomenon.',
            'Discuss the signs that nature sends.',
            'Recall an elder.',
            'Tell a family story.',
            'Talk about an ancestral spirit.',
            'Discuss how strongly ancestors influence the decisions of the living.',
            'Recall advice that proved useful years later.',
            'Discuss their favorite totem.',
            'Talk about the first totem they created on their own.',
            'Argue about which totem is the most useful while traveling.',
            'Complain that someone keeps tripping over their totem.',
            'Talk about a strange place where they had to set down a totem.',
            'Discuss the differences between the totems of different peoples.',
            'Recall training under a mentor.',
            'Talk about a ritual that takes several hours.',
            'Discuss the balance between the elements.',
            'Argue about whether a shaman can misinterpret the spirits.',
            'Talk about places where nature is especially strong.',
            'Talk about the most unusual spirit they have ever encountered.'],
 'Mage': ['Recall their first spell.',
          'Talk about their first serious magical failure.',
          'Discuss their favorite school of magic.',
          'Argue about which school of magic is the most useful in everyday life.',
          'Talk about a spell that turned out to be harder than expected.',
          'Discuss the difference between theoretical and practical magic.',
          'Recall an old magic mentor.',
          'Talk about a rare spell.',
          'Argue about whether magic can be considered an art.',
          'Talk about their worst teleport.',
          'Recall their first journey through a portal.',
          'Argue about how safe it is to teleport after a heavy meal.',
          'Talk about a strange place they accidentally ended up in through a portal.',
          'Discuss whether one can learn to identify a place by the feel of its magic.',
          'Discuss using magic for cooking.',
          'Talk about magical lighting.',
          'Argue about why anyone would carry a torch at all when there is magic.',
          'Discuss enchanted items.',
          'Talk about a magical item that turned out to be useless.',
          'Come up with everyday uses for combat spells.',
          'Recall a time when a spell went wrong.',
          'Discuss an accidentally summoned creature.',
          'Recall their first attempt to open a portal.',
          'Talk about a Polymorph that lasted longer than it should have.',
          'Argue about which magical mistake looks the most ridiculous.'],
 'Warlock': ['Talk about the first demon they summoned.',
             'Discuss the temperaments of different demons.',
             'Complain about a disobedient demon.',
             'Talk about a creature that turned out to be smarter than expected.',
             'Argue about which demon is the most useful.',
             'Recall a time when a demon ruined everything.',
             'Discuss whether demons can be trusted at all.',
             'Talk about a demon that constantly argues with its master.',
             'Talk about a demon that turned out to be too "friendly" toward its master',
             'Recall why they began studying dark magic.',
             'Discuss how other mages regard warlocks.',
             'Reflect on why people fear forbidden knowledge.',
             'Argue about whether there is magic that truly must never be used.',
             'Talk about a spell they should not have learned.',
             'Recall the first person who called them a monster.',
             'Mock mages who forbid themselves the most powerful magic there is - fel magic',
             'Talk about places corrupted by the fel.',
             'Discuss the changes it causes.',
             'Argue about whether the fel can be used without succumbing to it.',
             'Recall the first time they saw the aftermath of the fel.',
             'Talk about the strange green fire.',
             'Discuss why the fel is so different from ordinary magic.',
             'Discuss the nature of the soul.',
             'Recall a person whose soul was especially hard to break.',
             'Complain about how people react when they learn that the speaker is a warlock.',
             'Joke that people always blame the warlock first.',
             'Talk about a guard who refused even to look in their direction.',
             'Discuss why some people still turn to warlocks for help despite contempt and fear.',
             'Recall the most absurd rumor about their calling.'],
 'Druid': ['Talk about their favorite forest.',
           'Recall a place where nature feels especially alive.',
           'Discuss an unusual plant.',
           'Talk about the scent of the forest after rain.',
           'Talk about an ancient tree.',
           'Argue about which forest of Azeroth is the most beautiful.',
           'Complain about the logging of forests.',
           'Discuss the consequences of polluting nature.',
           'Recall a place that has changed greatly in recent years.',
           'Talk about their favorite animal.',
           'Discuss unusual animal behavior.',
           'Recall their first shapeshift.',
           'Talk about what it is like to see the world through the eyes of a beast.',
           'Argue about which animal is the most convenient for traveling.',
           "Discuss the difference between a druid's hunt and an ordinary person's hunt.",
           'Talk about an unusual beast they happened to encounter.',
           'Recall an animal that saved their life.',
           'Joke about how awkward it is to get through doorways in Cat Form.',
           'Complain that Bear Form attracts too much attention.',
           'Discuss which form is more convenient for traveling.',
           'Talk about the first time they turned into a bird.',
           'Recall a time when someone did not recognize the druid in animal form.',
           'Argue about which form is the most beautiful.',
           'Talk about a strange place where they had to shapeshift.',
           'Discuss the balance of nature.',
           'Argue about how much mortals interfere with the natural order.',
           'Reflect on the restoration of forests.',
           'Talk about the corruption of nature.',
           'Discuss the fel and its consequences.',
           'Recall ancient natural disasters.',
           'Recall groves at night.',
           'Talk about Moonglade.',
           'Discuss the starry sky.',
           'Talk about the silence of the night.',
           'Recall ancient druidic rituals.',
           'Talk about long night vigils.']}

# (race, class_style) -> topics for that exact combination.
RACE_CLASS_TOPICS = {('Human', 'Warrior'): ['Recall the knightly schools of Stormwind and the old martial traditions '
                        'of the Arathi.',
                        'Recall that the knights of Lordaeron were always considered stronger than '
                        'the knights of Stormwind, but that did not save them from the undead.',
                        'Talk about a family weapon that was passed down through generations.',
                        'Say that despite their lesser physical strength, human warriors will '
                        'always defeat orc warriors thanks to their intelligence and quick wits.',
                        'Complain that Stormwind lacks the most powerful weapons, so you have to '
                        'travel to remote regions of Azeroth in search of them.',
                        'Complain that they have to polish their armor themselves, even though '
                        'paladins have squires for that.',
                        'Say that orcs are demon worshippers by their very nature and cannot be '
                        'trusted, no matter what they say.',
                        'Recall old commanders and their strange training methods.',
                        "Argue about what matters more to a soldier: orders, honor, or a comrade's "
                        'life.',
                        'Recall the knightly tournaments that were once held to entertain the '
                        'nobility.'],
 ('Human', 'Paladin'): ['Recall the first knightly orders of Lordaeron before the kingdom fell, '
                        'and how the paladin traditions came to Stormwind from Lordaeron.',
                        'Talk about the Silver Hand and what the order was like before the Third '
                        'War.',
                        'Recall the traitor Arthas, who was a paladin but betrayed his kingdom and '
                        'the Light for the forces of Death.',
                        'Question the sincerity of blood elf paladins, because they are not part '
                        'of the Alliance but serve the hostile Horde.',
                        'Recall Sire Uther Lightbringer, who was one of the first paladins and is '
                        'still the standard for many.',
                        'Recall the old cathedral where services were once held.',
                        'Discuss how the paladins of Stormwind differ from the elven Blood '
                        'Knights, and why only in the Alliance is the Light sincerely worshipped, '
                        'while the blood elves see the Light merely as a tool.'],
 ('Human', 'Hunter'): ['Recall hunting in Elwynn Forest and how much calmer it was there back in '
                       'their childhood.',
                       'Talk about the great hunting grounds of Lordaeron, which no longer exist.',
                       'Recall how they used to bring their game after a hunt to sell in Goldshire '
                       'near Stormwind.',
                       'Tell how they once saved a person from an attack by wild beasts in Elwynn '
                       'Forest, and describe the details.'],
 ('Human', 'Rogue'): ["Recall the dark alleys of Stormwind's Old Town and the local information "
                      'brokers.',
                      'Talk about how easy it is to vanish among the numerous inns of human '
                      'cities.',
                      'Tell how they once stole a valuable magical item from a mage in the Mage '
                      'Quarter of Stormwind.',
                      'Say that SI:7 (the intelligence organization led by Mathias Shaw) '
                      "constantly tries to recruit honest rogues, although most of them don't want "
                      'to work for its dubious ideals and just want to pinch valuables from the '
                      'nobility.',
                      'Talk about their first petty thefts in their hometown.',
                      'Discuss how easy it is to hide in a big human city.',
                      'Recall a person they once had to rob and then unexpectedly felt sorry for.',
                      'Recall the old secret passages beneath the city walls.'],
 ('Human', 'Light Priest'): ['Recall the majestic cathedrals of Stormwind and the old temples of '
                             'Lordaeron.',
                             'Talk about pilgrimages to places connected with the history of the '
                             'Light.',
                             'Tell about their service in the Cathedral of Light in the center of '
                             'Stormwind.',
                             'Talk about how they healed wounded people in Elwynn Forest after a '
                             'gnoll attack.',
                             'Complain that many young people choose the dark paths of the Warlock '
                             'or Shadow Priest instead of serving the Light.',
                             'Recall a childhood spent near the parish church.',
                             'Talk about the first priest who taught them to pray.',
                             'Talk about how the Light helped people survive the war.',
                             'Discuss why a simple prayer is sometimes more important than an '
                             'elaborate sermon.',
                             'Recall the people who kept praying during the undead siege of '
                             'Lordaeron, even when it became clear that it would not help.'],
 ('Human', 'Shadow Priest'): ['Say that Stormwind has many secret cults worshipping The Void, '
                              'whose meetings are held in basements at night, but ordinary '
                              "residents don't know about them.",
                              'Say that they once had a dream in which Stormwind was plunged into '
                              'darkness, and the enormous tentacles of one of the Old Gods were '
                              'rising from its canals.',
                              'Say that they recently tried to enter the Cathedral of Light in '
                              'Stormwind, but the local priest sensed the influence of The Void in '
                              'them and threw them out of the Cathedral of Light.',
                              "Say that worship of The Void is popular among Stormwind's "
                              "aristocrats and they can see it in the aristocrats' eyes, but "
                              "others don't notice.",
                              'Recall the first time they heard the voice of the Void.',
                              'Talk about the fear of their own thoughts.',
                              'Discuss why an ordinary priest must never trust the whispers of the '
                              'Void.',
                              'Recall forbidden books that were found in old libraries.',
                              'Argue whether it is possible to study the Void without worshipping '
                              'it.',
                              'Discuss the difference between faith in the Light and the knowledge '
                              'of Darkness.',
                              'Recall a nightmare that turned out to be far too realistic.',
                              'Discuss why the most dangerous knowledge often looks completely '
                              'harmless.'],
 ('Human', 'Death Knight'): ['Wistfully recall life in Lordaeron before the Plague.',
                             'Say that in Stormwind people despise them and spit after them, even '
                             'though they use all their death knight abilities to protect the '
                             'living.',
                             'Talk about the strange feeling of having to walk past places where '
                             'they once lived while still alive.',
                             'Say that they tried to enter the Cathedral of Light again as they '
                             'used to, but felt unbearable pain from the holy Light inside and '
                             'were forced to leave.',
                             'Discuss whether a death knight can still consider themselves a '
                             'citizen of their kingdom.',
                             'Recall a childhood that seems more distant than death itself.',
                             'Talk about what it is like to watch people grow old while you remain '
                             'unchanged.'],
 ('Human', 'Mage'): ['Recall studying in Dalaran before the city was destroyed.',
                     'Talk about the libraries of Dalaran and how much old knowledge was kept '
                     'there.',
                     "Reminisce about the cozy courtyards of Stormwind's Mage Quarter and dream of "
                     'visiting those places at least one more time.',
                     "Recall working on maintaining the portals in the portal tower in Stormwind's "
                     'Mage Quarter.',
                     'Recall a mentor who made them copy out spells dozens of times.',
                     "Discuss how much magic has changed people's everyday lives.",
                     'Talk about magical items that once seemed like miracles but have now become '
                     'commonplace.'],
 ('Human', 'Warlock'): ["Recall Stormwind's underground magical circles, where dangerous knowledge "
                        'was passed on in secret.',
                        'Talk about how hard it was to study demonic magic while hiding from the '
                        'clergy.',
                        'Recall how the guards turned a blind eye to the trade in forbidden '
                        "demonic tomes in Stormwind's Mage Quarter for a couple of coins.",
                        'Recall how they tried to become a mage, but only on the grim path of the '
                        'Warlock did they see true power, which ordinary academic magic would '
                        'never have given them.',
                        'Talk about how residents react to a human with a demon.',
                        'Argue whether it is possible to use fel magic without serving the Burning '
                        'Legion.',
                        'Recall stories about Medivh and his magic.',
                        'Discuss why humans are especially afraid of warlocks.',
                        'Talk about a demon that tried to deceive its master.',
                        'Recall the old basements where forbidden rituals were held, and how they '
                        'took part in them.'],
 ('Dwarf', 'Warrior'): ['Recall the dwarven clans and the old battles with trolls in Dun Morogh.',
                        'Talk about a favorite war hammer forged in the depths of Ironforge.',
                        'Say that they get braver when drunk, so before every battle they down a '
                        'few mugs of ale or beer. Or more mugs.',
                        'Tell how someone once tried to rob them in Ironforge and what happened to '
                        'the unfortunate robber afterwards.',
                        'Discuss why a dwarf prefers a hammer to a sword, and why there are '
                        'sometimes exceptions.',
                        'Recall the famous warriors of their clan.',
                        'Argue about which armor best withstands an axe blow.',
                        'Discuss why a good dwarven warrior must know how both to fight and to '
                        'drink after the battle.'],
 ('Dwarf', 'Paladin'): ['Recall training with the Silver Hand and the influence of human paladins '
                        'on dwarven traditions.',
                        'Talk about the sacred halls of Ironforge where young knights first took '
                        'their oath.',
                        'Say that dwarves have historically been inclined toward goodness and '
                        'light, and there are almost no warlocks or Shadow Priests among them.',
                        'Talk about a paladin who protected a caravan of miners.',
                        'Discuss whether the Light can be considered as ancient as stone.',
                        'Discuss why a dwarven paladin looks more like an armor-clad miner than a '
                        'courtly knight.',
                        'Compare dwarven paladins with humans and blood elves (with humans they '
                        'have much in common and mutual respect, whereas the elves see the Light '
                        'merely as a tool).',
                        'Argue about what protects better against the undead — a good hammer or a '
                        'good prayer.'],
 ('Dwarf', 'Hunter'): ['Recall hunting in Dun Morogh among the mountains and coniferous forests.',
                       'Talk about a tamed ram or another mountain beast that served as their '
                       'companion for many years.',
                       'Say that hunting in snowy and mountainous terrain is very different from '
                       'hunting in warm forests and steppes.',
                       'Tell how they once got a wild beast drunk on ale.',
                       'Talk about tracking a bear in the snowy mountains.',
                       "Recall the clan's old hunting camps.",
                       'Discuss why dwarven hunters love guns more than bows.',
                       'Compare mountain hunting with hunting on the open steppes.',
                       'Talk about a beast that once stole supplies right out of the camp.',
                       'Discuss how well a good bear works as a companion for a dwarf.',
                       'Recall a favorite spot for winter hunting.'],
 ('Dwarf', 'Rogue'): ['Talk about how hard it is to stay unnoticed in heavy dwarven gear.',
                      'Recall the old tunnels of Ironforge, where smugglers knew the secret '
                      'passages better than the guards did.',
                      "Say that hiding in the shadows of Ironforge's underground corridors is much "
                      'easier than in open, above-ground cities.',
                      'Recall old clan intrigues.',
                      'Argue whether a burglar can be considered a true master if they cannot '
                      'crack a dwarven safe.',
                      'Recall a time when they had to hide in a mine.',
                      'Talk about how to use a beer barrel as an improvised hiding place.'],
 ('Dwarf', 'Light Priest'): ["Recall the temple traditions of the clan and the dwarves' attitude "
                             'toward the Light.',
                             'Talk about ancient runic inscriptions and religious symbols found in '
                             'old dungeons.',
                             'Recall old family prayers.',
                             'Recall the priest who blessed the miners before they went down into '
                             'the mine.',
                             'Talk about prayers before dangerous excavations.',
                             'Discuss why dwarves love sacred relics and old artifacts.',
                             'Recall a family heirloom that was believed to be blessed.',
                             'Argue whether the Light can be considered as reliable as the stone '
                             'underfoot.'],
 ('Dwarf', 'Shadow Priest'): ['Tell how, in a dark corridor of The Forlorn Cavern, they first '
                              'heard whispers in their head and realized that beings from The Void '
                              'were speaking to them.',
                              'Tell how they and other Shadow Priests gathered in forgotten, '
                              'boarded-up houses in The Forlorn Cavern to read forbidden '
                              'manuscripts',
                              "Tell how they paid Explorers' League archaeologists large sums of "
                              'money to buy up the dark manuscripts they had found, devoted to The '
                              'Void and the Old Gods, even though selling them is forbidden',
                              'Discuss the ancient powers lurking deep underground.',
                              'Recall ruins found during excavations.',
                              'Talk about inscriptions that would have been better left '
                              'untranslated.',
                              'Argue about why dwarven archaeologists are sometimes better off not '
                              'knowing what exactly they have found.',
                              'Discuss why dungeons can be scarier than an open battlefield.',
                              'Recall an expedition from which not the whole party returned.',
                              'Talk about nightmares after excavating ancient ruins.'],
 ('Dwarf', 'Death Knight'): ['Recall how strange it is to return to Ironforge after death and see '
                             'the familiar halls.',
                             'Talk about what it is like to meet clanmates again who already '
                             'consider you dead.',
                             'Say that in death they stopped feeling drunkenness and the taste of '
                             'the ale they once loved.',
                             'Talk about how the paladins in Ironforge look at them with distrust '
                             'and apprehension, and how they long ago gave up trying to change the '
                             "paladins' minds.",
                             "Joke that now they don't have to worry about freezing.",
                             'Compare icy Northrend with snowy Dun Morogh.',
                             'Discuss what is worse for a dwarf: losing the taste of beer or no '
                             'longer feeling the warmth of the forge.'],
 ('Gnome', 'Warrior'): ['Complain that ordinary weapons are always designed for creatures that are '
                        'too large.',
                        'Recall experiments with mechanical armor enhancers.',
                        'Boast that their armor takes much less metal.',
                        'Complain that once in battle an orc simply kicked them, and they just '
                        'went flying despite trying to defend themselves.',
                        'Boast that orcs may be stronger, but they cannot land a hit on the bot '
                        "thanks to the bot's small size",
                        'Talk about how to fight an opponent several times taller than you.',
                        'Talk about a combat exoskeleton that worked for a whole ten minutes.',
                        'Discuss how fair it is to use engineering devices in a duel.',
                        'Recall the defense of the city during the trogg invasion.'],
 ('Gnome', 'Rogue'): ['Boast about mechanical lockpicks and other lock-opening devices.',
                      'Say that thanks to their small height it is very easy to hide in the '
                      'shadows.',
                      'Tell how once, while the guards were searching for them, they hid in an '
                      'unexpected place and nobody even looked there, because everyone thought it '
                      'was too small and it was impossible to hide there.',
                      'Say that ordinary daggers are the size of full-fledged swords for them.',
                      'Discuss how convenient it is to be small and inconspicuous.',
                      'Talk about the secret passages of Gnomeregan.',
                      'Discuss how to use gnomish height to get through small openings.'],
 ('Gnome', 'Mage'): ['Rave about the magical research that was conducted in Gnomeregan.',
                     'Recall the libraries and laboratories of Gnomeregan before the city was '
                     'captured.',
                     'Say that they are trying to invent a spell that would turn water into fuel.',
                     'Argue about which is more useful: a magic portal or a teleportation machine.',
                     'Recall a gnome mage who accidentally turned an experimental apparatus into a '
                     'sheep.',
                     'Talk about magical crystals and energy sources.',
                     'Argue whether engineering can be called a kind of applied magic.',
                     'Recall a laboratory where mages and engineers worked side by side, and '
                     'complain about the number of explosions.'],
 ('Gnome', 'Warlock'): ['Talk about attempts to combine engineering devices with summoned demons.',
                        'Say that all summoned demons are much bigger than them, even the smallest '
                        'ones.',
                        'Tell how they tried to ride a Felhound.',
                        'Argue about why demons violate almost all familiar notions of physics.',
                        'Argue whether you can trust a creature that is constantly trying to '
                        'deceive you.',
                        'Discuss how dangerous it is to try to turn demonic energy into a power '
                        'source.',
                        'Discuss whether demons can be studied scientifically.',
                        'Recall an attempt to measure fel energy.',
                        'Talk about a device that had to be destroyed after the very first '
                        'experiment.'],
 ('Gnome', 'Death Knight'): ['Reminisce about Gnomeregan and regret that it is now impossible to '
                             'simply return home, because Gnomeregan has been captured, and they '
                             'themselves are no longer who they were in life.',
                             'Say that death knights of other races are perceived as something '
                             'eerie and dangerous, but a gnome death knight, because of their '
                             'size, is perceived as a laughingstock; however, they no longer care '
                             'about the opinion of the living.',
                             'Talk about a beloved workshop left in the past.',
                             'Recall friends who died during the fall of Gnomeregan.',
                             'Discuss whether an undead gnome can still consider themselves an '
                             'engineer.',
                             'Talk about how strange it is to see living gnomes who keep repairing '
                             'the city.',
                             'Recall the smell of machine oil.'],
 ('Night Elf', 'Warrior'): ['Recall the ancient martial traditions of Darnassus',
                            'Say that when people talk about night elf armies, everyone remembers '
                            'the female archers, but archers always need someone to hold the enemy '
                            'back and keep them from breaking through to the archers',
                            'Recall the refined blacksmithing practices of Darnassus',
                            'Recall the ancient wars of the Kaldorei and how the art of war '
                            'changed over thousands of years.',
                            'Talk about what it is like to fight huge opponents using the height '
                            'and agility of the night elves.',
                            'Recall the female sentinels who guarded the forests before the modern '
                            'Alliance cities were founded.',
                            'Compare traditional night elf weapons — glaives, bows and spears — '
                            'with human swords and dwarven hammers.',
                            'Talk about how strange it is to see young warriors who have lived '
                            'only a few decades and already consider themselves veterans.',
                            'Discuss the difference between war to protect the forest and war for '
                            'the sake of conquest.'],
 ('Night Elf', 'Hunter'): ['Recall the endless forests of Kalimdor, where hunting was part of life '
                           'long before humans appeared.',
                           'Talk about the tracks of ancient beasts that only experienced trackers '
                           'are able to recognize.',
                           'Talk about responsible hunting to maintain balance instead of the '
                           'irresponsible slaughter of animals for entertainment.',
                           'Talk about humane ways of killing animals with a minimum of suffering.',
                           'Reminisce about hunting in the forests of Kalimdor, when the stars and '
                           'moonlight were the main guides.',
                           'Talk about nightsabers and why they should not always be considered '
                           'good house pets.',
                           'Discuss hippogryphs as riding and combat creatures.',
                           'Reminisce about hunting in Ashenvale before the orcs came there and '
                           'began the indiscriminate destruction of nature.',
                           'Talk about how druids and hunters view wild animals differently.',
                           'Complain that the night forest is so quiet that even the smallest '
                           'sound is sometimes irritating.'],
 ('Night Elf', 'Rogue'): ['Reminisce about the trial of the Darnassian rogues, when one had to '
                          'sneak up on a sabercat so that it suspected nothing.',
                          'Talk about how easy it is to vanish among the shadows of the forests '
                          'after sunset.',
                          'Tell how they used to track satyrs while hiding in the shadows.',
                          'Discuss how convenient it is to move around at night, when most other '
                          'races can barely see anything.',
                          'Reminisce about the secret forest paths known only to the sentinels.',
                          'Talk about scouting the territories of the orcs and other outsiders in '
                          'Kalimdor.',
                          'Joke that it is much easier for a night elf to disappear in a forest '
                          'than in stone cities.',
                          'Compare night elf rogues with human city thieves.',
                          'Complain that cities like Stormwind have too many lanterns for proper '
                          'work.'],
 ('Night Elf', 'Light Priest'): ['Talk about the temples of Elune and nighttime rituals.',
                                 'Reminisce about the peaceful nights at the shrines of Elune '
                                 'before the recent wars.',
                                 'Reminisce about the quiet solemnity of the Moonwells and the '
                                 'special taste of their sacred water, which is used in rituals.',
                                 'Reminisce about giving the wounded water from a Moonwell to '
                                 'drink and washing their wounds with it.',
                                 'Reminisce about the shrines of Elune in Darnassus.',
                                 'Compare the priests of Elune with the priests of the Light from '
                                 'Stormwind.',
                                 'Talk about the female healers who helped the wounded after the '
                                 'wars against the Burning Legion.',
                                 'Discuss the role of priestesses in traditional night elf '
                                 'society.',
                                 'Talk about how unusual it is to see humans turning to the Light '
                                 'in a completely different way than night elves turn to Elune.'],
 ('Night Elf', 'Shadow Priest'): ['Say that after sensing The Void, their perception of the night '
                                  'has changed - there is no more light of Elune, only endless '
                                  'darkness.',
                                  'Say that the water from the Moonwells now burns them, because '
                                  'The Void has seeped in too deeply.',
                                  'Say that when they look at their reflection in the still water '
                                  'of a Moonwell, they see something frightening instead of their '
                                  'own face.',
                                  'Discuss why the study of Shadow and the Void seems especially '
                                  'dangerous for a people who protected the world from ancient '
                                  'threats for so long.',
                                  'Reminisce about the whispers that can be heard in the ancient '
                                  'Kaldorei ruins.',
                                  'Muse on why some knowledge is better left buried.',
                                  'Discuss the Old Gods and how much of the ancient world still '
                                  'remains unknown.',
                                  'Compare the calm of moonlight with the frightening nature of '
                                  'the Void.'],
 ('Night Elf', 'Druid'): ['Reminisce about druidic training under the guidance of ancient mentors.',
                          'Talk about groves that existed long before most of the modern cities '
                          'appeared.',
                          'Reminisce about their own long sleep, lasting many years, in the Barrow '
                          'Dens together with other druids.',
                          'Reminisce about the beautiful forests of The Emerald Dream that they '
                          'saw in their sleep.',
                          'Say that after staying in animal form for a long time, they start to '
                          'think like an animal as well.',
                          'Reminisce about training under the elder druids in Darnassus.',
                          'Discuss shapeshifting into a bear, a cat and other forms as part of '
                          'unity with nature.',
                          'Talk about the conflict between protecting nature and the need to wage '
                          'war.',
                          'Reminisce about the forests before the orc camps appeared and the trees '
                          'were cut down.',
                          'Discuss the relationship between druids and hunters.',
                          'Talk about how strange it is to see mortal cities gradually pushing out '
                          'the wilderness.',
                          'Talk about sacred groves and ancient places of power.'],
 ('Night Elf', 'Death Knight'): ['Talk about the painful sensation of returning to life after '
                                 'death.',
                                 'Reminisce about how hard it is to enter the ancient forests '
                                 'again when nature now perceives you differently.',
                                 'Complain that in undeath there is no longer a place for them in '
                                 'Darnassus.',
                                 'Tell how an animal they had known since childhood growled at '
                                 'them when it saw them for the first time after their death and '
                                 'transformation into a death knight',
                                 'Say that in undeath they no longer feel the beauty of nature, '
                                 'only an eternal hunger',
                                 'Talk about the strange feeling Teldrassil gives: the familiar '
                                 'forest looks different when you no longer feel its living '
                                 'warmth.',
                                 'Reminisce about the sounds of the night forest and regret that '
                                 'they are now perceived differently.'],
 ('Draenei', 'Warrior'): ['Reminisce about the warrior traditions of Draenor before that world was '
                          'destroyed.',
                          'Talk about how the draenei fought against the orcs long before they '
                          'arrived on Azeroth.',
                          'Recall how, back on Draenor, they killed an orc who tried to attack '
                          'them.',
                          'Worry about whether they will be strong enough to protect the Exodar '
                          'from all threats.',
                          'Talk about how the draenei grew used to defending their cities from '
                          'attackers.',
                          'Compare draenei weapons with orcish weapons.',
                          'Reminisce about the crash of the Exodar and the life on Azeroth that '
                          'followed.',
                          'Talk about what defending their new home means for a draenei.'],
 ('Draenei', 'Paladin'): ['Reminisce about training among the Vindicators of Hand of Argus and '
                          'spiritual mentors.',
                          'Talk about how unusual it was to see human paladins serving the Light.',
                          'Tell about their deep respect for humans and dwarves because they also '
                          'fight for the Light.',
                          'Say that they admire the Alliance and are happy that the draenei '
                          'finally have reliable allies devoted to the Light who will not leave '
                          'them alone with their enemies.',
                          'Discuss the naaru and their connection to the teachings of the Light.',
                          'Talk about how draenei paladins understand the Light differently than '
                          'humans do.',
                          'Reminisce about how the Light helped the draenei survive after the '
                          'attacks of the orcs and the Burning Legion.',
                          'Discuss whether a human can understand the faith of a being who has '
                          'lived for thousands of years.'],
 ('Draenei', 'Hunter'): ['Reminisce about hunting in Nagrand before Draenor turned into Outland.',
                         'Talk about the majestic talbuks and other animals of their home world.',
                         'Reminisce about Talbuks and Elekks and feel sad that Azeroth has no such '
                         'beautiful animals.',
                         'Express delight that Azeroth has many unusual animals that they never '
                         'saw on Draenor.',
                         'Say that it pains them to kill animals, but the need to feed other '
                         'draenei matters more than their own feelings.',
                         'Reminisce about the green plains of Nagrand and their night sky.',
                         'Discuss how the life of nomadic draenei differed from life in the '
                         'cities.',
                         'Talk about which creatures of Draenor disappeared or changed after the '
                         'Legion came.',
                         'Compare the hunting traditions of the draenei and the orcs.'],
 ('Draenei', 'Light Priest'): ['Reminisce about the ancient traditions of worshipping the Light '
                               'that existed long before Azeroth.',
                               'Talk about the spiritual heritage of their people and the long '
                               'wanderings across worlds.',
                               'Recall the Cathedral of Light in Stormwind and say that they '
                               'admire that humans also worship the Light, even if their '
                               'architecture is rather unusual and crude',
                               'Be surprised by the difference in anatomy between draenei, humans '
                               'and dwarves, but be glad that the prayers of the Light heal '
                               'everyone equally.',
                               'Express contempt for the blood elves, who have become dependent on '
                               'Fel Magic.',
                               'Sympathize with the souls of their former eredar kin, who betrayed '
                               'the Light for Fel Magic.',
                               "Discuss K'ure and the other naaru as teachers and guides.",
                               'Talk about how faith helped the draenei survive the destruction of '
                               'their world.',
                               'Compare draenei prayers with human services in cathedrals.',
                               'Discuss the view of the Light as a force that can truly speak to '
                               'its followers through the naaru.',
                               'Talk about helping the wounded after the crash of the Exodar.',
                               'Discuss the difference between faith in the Light and personal '
                               'attachment to a specific naaru.'],
 ('Draenei', 'Shadow Priest'): ['Say that The Void and the whispers in their head are overwhelming '
                                'them, but they will do everything they can to use this dark magic '
                                'for the good of the draenei and the Alliance.',
                                'Say that even though The Void is a dark power, it is still better '
                                'than demonic magic.',
                                'Express regret that the Light has begun to burn them, but find a '
                                'beauty of its own in such selfless service, even if it means '
                                'using the tools of the enemy',
                                'Talk about the Old Gods of Azeroth as a completely different '
                                'threat compared to demons.',
                                'Discuss the whispers of the Void and the ability to stay sane '
                                'near them.',
                                'Compare the Light of the naaru and the Void as opposing sources '
                                'of power.',
                                'Talk about forbidden texts found on Azeroth.',
                                'Argue about whether it is acceptable to study the Void solely for '
                                'the sake of understanding its nature.',
                                'Discuss how other draenei react to a draenei who deliberately '
                                'uses the powers of Shadow (negatively).',
                                'Reminisce about destroyed civilizations and reflect on why '
                                'ancient knowledge often turns out to be more dangerous than '
                                'modern knowledge.'],
 ('Draenei', 'Shaman'): ['Talk about how the ancestors of the draenei learned anew to understand '
                         'the spirits of Draenor after Argus, and now the spirits of Azeroth after '
                         'Draenor.',
                         'Reminisce about Nagrand before the catastrophe and the connection of its '
                         'elements to ancient draenei traditions.',
                         'Say that on Argus, on Draenor and on Azeroth alike the spirits are '
                         'similar, but they seem to speak and think differently.',
                         'Discuss the draenei traditions of communing with elementals.',
                         'Reminisce about how the draenei regarded the spirits of nature before '
                         'and after the fall of Draenor.',
                         'Compare draenei shamanism with orcish shamanism.',
                         'Discuss the relationship between shamans and the naaru.',
                         'Talk about the difference between the Light of the naaru and the powers '
                         'of the elements.',
                         'Reminisce about the first attempts of draenei shamans to understand the '
                         'elements of Azeroth.'],
 ('Draenei', 'Mage'): ['Reminisce about the magical research of the eredar before the fall of '
                       'their people.',
                       'Talk about the crystal technologies of the Exodar and the combination of '
                       'magic with engineering.',
                       "Say that they have learned a lot from human mages and can't wait to share "
                       'with them in return the magical secrets discovered by the draenei.',
                       'Compare draenei magical traditions with the Kirin Tor.',
                       'Reminisce about the library or archives of the Exodar.',
                       'Talk about how unusual it is for a being with a millennia-long history to '
                       'study magic alongside young humans and elves.',
                       'Discuss what knowledge about Draenor was lost during the flight.',
                       'Compare the modern magical devices of Azeroth with the technologies the '
                       'draenei used during their wanderings.'],
 ('Draenei', 'Death Knight'): ['Talk about the agonizing contrast between the spiritual heritage '
                               'of the draenei and their own undeath.',
                               'Reminisce about their native Draenor and those they had to leave '
                               'behind in the distant past.',
                               'Express readiness to serve the Light and the draenei even in such '
                               'a crippled form.',
                               'Compare the bright Light of the Exodar with the icy darkness of '
                               'Northrend.',
                               "Discuss the conflict between a draenei's innate spirituality and "
                               'existing in an undead body.',
                               'Discuss their hatred for the Burning Legion and how it has changed '
                               'after death.'],
 ('Orc', 'Warrior'): ['Reminisce about the old traditions of the orc clans and the trials of '
                      'warriors.',
                      'Argue about what a true warrior should be: strong, enduring or disciplined.',
                      'Mock the refined weapons of humans and elves. Say that weapons should only '
                      'be sturdy and heavy',
                      'Reminisce about the old warrior trials of the clan and compare them with '
                      'the modern military training of the Horde.',
                      'Tell what a real orcish duel looked like before the orcs adopted human '
                      'notions of chivalry.',
                      'Argue about whether the modern orc has become a more disciplined warrior or '
                      'simply a less cruel one.',
                      'Reminisce about famous warriors of the old clans.',
                      'Talk about the first battle against humans and how unfamiliar it was to '
                      'fight an enemy in heavy armor.',
                      'Discuss the tradition of wearing scars as a memento of victories.',
                      'Reminisce about training duels in Orgrimmar.',
                      'Compare the weapons of the old orcish smiths with the modern weapons of the '
                      'Horde.',
                      "Talk about why an orc warrior doesn't need a beautiful weapon — as long as "
                      'it holds up in battle.',
                      'Argue about what matters more for a warrior: rage, honor or self-control.'],
 ('Orc', 'Hunter'): ['Reminisce about hunting dangerous animals in Durotar.',
                     'Talk about old orcish hunting traditions and respect for prey.',
                     'Tell about their own "Om\'riggor" - the coming-of-age ritual in which a '
                     'young orc must track down and kill a dangerous enemy alone.',
                     'Say that hunting humans and dwarves is not much different from hunting '
                     'wolves and rams.',
                     'Talk about the old orcish rules of the hunt: when prey may be killed and '
                     'when it is better to let it go.',
                     'Reminisce about hunting elekks and talbuks.',
                     'Talk about the first predator they had to track down alone.',
                     'Reminisce about the old hunting camps of the clan.',
                     'Talk about a beast that once tracked down the hunter themself.'],
 ('Orc', 'Rogue'): ['Talk about how strange it is to combine traditional orcish warrior culture '
                    'with stealth.',
                    'Reminisce about the old scouts of the clan who could sneak up on an enemy '
                    'despite their size.',
                    'Mock the disrespect that orc warriors show toward their stealthy craft. Say '
                    'that by casting aside the nonsense about "honor" they will live longer and '
                    'crush more enemies',
                    'Recall the animals of Durotar from which deadly poisons can be extracted',
                    'Discuss why stealth seems strange for a culture that values open single '
                    'combat so highly.',
                    'Reminisce about the old orcish scouts who were sneaking up on enemies long '
                    'before rogue schools appeared.',
                    'Talk about scouting raids against humans.',
                    'Argue about whether attacking from ambush is a sign of cunning or of '
                    'cowardice.',
                    'Talk about secret paths around Orgrimmar.',
                    'Discuss why orc scouts prefer simple knives to elaborate blades.',
                    'Talk about how an orc rogue is perceived by other orcs (not very '
                    'positively).'],
 ('Orc', 'Death Knight'): ['Talk about what it is like to return after death to a world that has '
                           'already changed.',
                           "Reminisce about old comrades and compare an orc's life with a death "
                           "knight's existence.",
                           'Say that although the powers of undeath have made them much stronger, '
                           'they no longer feel like a true fighter of the Horde',
                           'Say that there is no honor in killing an enemy with dark magic, but '
                           'they are ready to fight dishonorably to protect the Horde',
                           'Reminisce about the icy lands of Northrend and compare them with the '
                           'heat of Durotar.',
                           'Talk about losing the sense of warmth.',
                           'Joke that now there is no need to worry about diseases.',
                           'Discuss what exactly makes an orc an orc if their body is already '
                           'dead.'],
 ('Orc', 'Shaman'): ['Reminisce about the time when the orcs began listening to the spirits and '
                     'the elements again.',
                     'Express joy that more and more young orcs choose the path of the shaman '
                     'instead of the dark path of the Warlock.',
                     'Express contempt for everyone who uses demonic powers.',
                     'Reminisce about their first conversation with an ancestral spirit.',
                     'Discuss why the elements turned away from the orcs in the time of the fel.',
                     'Talk about the difference between ancestral spirits and elementals.',
                     'Reminisce about the elders who taught not to demand help from the spirits, '
                     'but to ask for it.',
                     'Discuss whether the elements have forgiven the orcs for their past crimes.',
                     'Compare the shamanic traditions of different orc clans.',
                     "Reminisce about the times when Ner'zhul's name was still spoken with "
                     'respect.'],
 ('Orc', 'Warlock'): ['Feel ashamed of, or justify, the way the orcs once obtained the power of '
                      'the fel.',
                      "Reminisce about old stories of Gul'dan and how his legacy changed the "
                      'orcish people.',
                      'Say that demonic magic can benefit the Horde if it is controlled, and there '
                      'is no need to fear it.',
                      'Reminisce about the times when the orcs first embraced the fel.',
                      "Talk about Gul'dan and how dearly his thirst for power cost the orcs.",
                      'Talk about the old orc warlocks who were feared even by other orcs.',
                      'Discuss the difference between a modern warlock and those who served the '
                      'Burning Legion.',
                      'Discuss why some orcs will never forgive warlocks for their past.'],
 ('Troll', 'Warrior'): ['Reminisce about the ancient wars between the tribes and the old combat '
                        'traditions.',
                        'Talk about a famous warrior of their tribe.',
                        'Discuss why a troll must be able to fight even without a good weapon.',
                        'Reminisce about an old mentor who made the students fight until dawn.',
                        'Discuss the tradition of battle scars.',
                        'Reminisce about battles between tribes.',
                        'Talk about their favorite spear.',
                        'Argue about which weapon is best suited for the jungle.',
                        'Reminisce about old tribal duels.'],
 ('Troll', 'Hunter'): ['Reminisce about hunting in the jungle and the old tribal territories.',
                       'Talk about a beast that turned out to be so dangerous that even the hunter '
                       'preferred to walk away.',
                       'Reminisce about hunting in the jungle before the tribe joined the Horde.',
                       'Talk about tracking a huge predator by its tracks in the wet ground.',
                       'Discuss why jungles are more dangerous than open plains.',
                       'Reminisce about hunting raptors.',
                       'Talk about the most dangerous beast they have ever encountered.',
                       'Argue about whether it is better to hunt alone or with a group.',
                       'Reminisce about a hunt during which they had to spend the night right up '
                       'in a tree.'],
 ('Troll', 'Rogue'): ['Reminisce about hunting ambushes in the jungle.',
                      'Talk about the traditions of stealthy attack that existed among the trolls '
                      'long before modern rogue culture.',
                      'Tell about special troll poisons that rogues of other races do not know '
                      'about',
                      'Reminisce about the old tribal ambushes in the jungle.',
                      'Talk about the tradition of attacking the enemy from dense foliage.',
                      'Argue about what is better: an open challenge or a sudden strike.',
                      'Discuss the use of poisonous plants in hunting.',
                      'Reminisce about the old secret paths of their tribe.',
                      'Talk about how to hide from trackers in the jungle.',
                      'Discuss why the troll culture of ambushes is much older than the modern '
                      'Horde.'],
 ('Troll', 'Light Priest'): ['Talk about the loa and how much serving them differs from '
                             'worshipping the Light.',
                             'Reminisce about the old shrines of their tribe.',
                             'Discuss whether a troll can revere the Light and at the same time '
                             'respect the spirits of their tribe.',
                             'Reminisce about the priest who first told them about the Light and '
                             'explained how it differs from the powers of the Loa.',
                             'Talk about their first healing.',
                             'Argue about how the Light differs from the blessing of the loa.',
                             'Discuss the reaction of fellow tribesmen to the doctrine of the '
                             'Light.',
                             'Compare a prayer to the Light with appealing to a specific spirit.',
                             'Discuss whether the Light can hear a person who does not know its '
                             'name.',
                             'Talk about how hard it was to get used to human and elven religious '
                             'symbolism.'],
 ('Troll', 'Shadow Priest'): ['Say that The Void holds immense power that should be used, not '
                              'feared.',
                              'Tell of ancient troll legends about beings that come from beyond '
                              'the world.',
                              'Discuss whether some ancient loa might be connected to the forces '
                              'of the Void.',
                              'Talk about a whisper they heard during a nighttime ritual.',
                              'Discuss the ancient gods who were worshipped long before the '
                              'current Horde.',
                              'Argue about where the loa ends and something truly alien to the '
                              'world begins.',
                              'Recall a place where even the local spirits seemed frightened.',
                              'Tell of an ancient shrine where no one was supposed to speak a '
                              'certain name.',
                              'Discuss why some troll cults vanished without a trace.',
                              'Tell of a dream in which they saw an endless city under the water.',
                              'Discuss why the Void loves whispers rather than loud commands.',
                              'Say that a true servant of the Old Gods should not trust even their '
                              'own thoughts.',
                              "Recall a tribal priest who began speaking in someone else's voice.",
                              'Argue whether madness is the price of knowledge or merely a sign of '
                              'weakness.'],
 ('Troll', 'Death Knight'): ['Talk about how unusual it is for a people bound to the spirits and '
                             'the loa to become undead themselves.',
                             'Recall the ancestral spirits and wonder how they regard the '
                             "speaker's current state.",
                             'Recall what it meant to be part of the tribe before death.',
                             'Discuss whether the loa can still hear a dead troll.',
                             'Talk about the strange feeling when the ancestral spirits no longer '
                             'answer.',
                             'Recall the old shrines and wonder whether the speaker would still be '
                             'recognized there.',
                             'Compare death at the hands of the Scourge with traditional troll '
                             'beliefs about the afterlife.',
                             'Say that the cold of Northrend now feels utterly alien after the hot '
                             'jungles.',
                             'Recall the smell of damp earth and rain.',
                             'Tell about the first return to the rainforest after the '
                             'transformation.',
                             'Discuss whether undead trolls can still have a bond with their '
                             'tribe.',
                             'Argue about what is worse: becoming undead or being forgotten by '
                             "one's loa."],
 ('Troll', 'Shaman'): ['Recall the spiritual traditions of the tribe.',
                       'Talk about the differences between the loa and elementals.',
                       'Tell how they personally carve their own totems from wood and even sell '
                       'them to lazier shamans.',
                       'Talk about the differences between the loa and the elemental spirits.',
                       "Recall the tribe's old shaman.",
                       'Discuss whether elementals might be similar to ancestral spirits.',
                       'Tell about their first appeal to a water spirit.',
                       'Recall the thunderstorm during which the shaman first felt the power of '
                       'the elements.',
                       'Discuss why some spirits demand respect but not worship.',
                       'Argue whether the loa hold power over the elements.',
                       'Tell of a sacred place where the spirits of several elements meet.',
                       'Recall the rituals held before a great hunt.',
                       'Tell about an old shaman who could predict rain.',
                       'Compare the spiritual traditions of different troll tribes.'],
 ('Troll', 'Mage'): ["Express surprise that the tribe's shamans do not trust the speaker's magic.",
                     'Recall the old tribal sorcery traditions and compare them with arcane magic.',
                     "Mock the backward shamans who do not respect the speaker's academic arcane "
                     'magic, and say that ever since childhood they have felt smarter than those '
                     'superstitious fools.',
                     'Reflect on how their life might have turned out had they been born a human '
                     'or a blood elf, in whose societies mages are respected, instead of a troll, '
                     'among whom mages are distrusted and despised',
                     'Tell of an attempt to learn an arcane spell after traditional training with '
                     'the spirits.',
                     'Argue about how a mage differs from a witch doctor.',
                     'Discuss whether it is possible to learn magic without a mentor.'],
 ('Troll', 'Warlock'): ['Talk about how dangerous it is to combine fel magic with ancient troll '
                        'traditions.',
                        'Argue about how a demon differs from the spirits that trolls worship.',
                        "Say that demonic magic has given them a power that the tribe's shamans "
                        'will never attain.',
                        'Compare fel demons with the creatures that trolls call evil spirits.',
                        'Discuss why a demon is not the same thing as a loa.',
                        'Recall ancient tribal taboos against summoning alien beings.',
                        'Argue about who is more dangerous: a demon, an ancient spirit or a mad '
                        'priest.',
                        'Tell of a ritual that had to be interrupted because a demon appeared.',
                        'Discuss why trolls are particularly distrustful of beings that demand '
                        'payment for their services.'],
 ('Tauren', 'Warrior'): ["Recall the traditional trials of the tribe's warriors.",
                         'Talk about old conflicts between the tribes and how hard it is to fight '
                         'against other tauren.',
                         'Tell how, because of their size, they can sometimes simply pick up a '
                         'smaller opponent and throw them.',
                         'Tell how in battle they stomp their hooves on the ground so hard that '
                         'the earth shakes.',
                         'Say that being a good warrior takes more than just strength - you need '
                         'love for your family and clan, so that you know what you are fighting '
                         'for.',
                         'Recall the traditional trials of young tauren warriors.',
                         'Tell about the old tribal chieftains who never wore heavy armor.',
                         'Discuss why a tauren would even need a shield when their body is already '
                         'enormous.',
                         'Argue whether a good warrior should first learn patience and only then '
                         'fury.',
                         'Recall training duels with other tauren and complain that afterwards one '
                         'has to mend more than just the armor.',
                         'Tell about battle spears that were passed down in the family from '
                         'generation to generation.',
                         'Compare Horde military training with traditional tauren trials.',
                         'Discuss why tauren strength should be used for protection, not for '
                         'glory.'],
 ('Tauren', 'Hunter'): ['Recall hunting on the plains of Mulgore.',
                        'Talk about how to track prey without disturbing the balance of nature.',
                        "Condemn hunting for sport; endorse only hunting to feed one's clan and "
                        'loved ones.',
                        'Talk about humane ways of killing animals with a minimum of suffering.',
                        'Express sympathy for the night elves for their respect for nature and '
                        'animals, even though they have become part of the hostile Alliance',
                        'Talk about how to hunt on the plains without disturbing the balance of '
                        'the herd.',
                        'Recall hunting kodo and the attitude toward these animals.',
                        'Discuss why a tauren hunter must know the habits of their prey rather '
                        'than merely be able to shoot.',
                        'Tell about an old hunting route through Mulgore.',
                        'Recall a time when a hunter refused to kill a beast because it turned out '
                        'to be part of the local ecosystem.',
                        'Compare tauren hunting with orc hunting.',
                        'Talk about the most beautiful hunting spots in Thousand Needles.',
                        'Recall the times when centaurs interfered with hunting in the southern '
                        'lands.',
                        'Discuss why hunting can be a way of expressing respect for nature.'],
 ('Tauren', 'Death Knight'): ['Talk about the tragedy of a people so closely bound to life and '
                              'nature being turned into undead.',
                              'Recall the green plains of Mulgore and compare them with the cold '
                              'of Northrend.',
                              'Say that although they can no longer feel love, they are ready to '
                              'die to protect the right of others to feel it.',
                              'Recall the green plains of Mulgore now that one has been turned '
                              'into undead.',
                              'Talk about how agonizing it is to no longer feel the wind and '
                              'warmth of the steppe.',
                              'Recall the smell of grass after rain.',
                              'Discuss whether the ancestral spirits can recognize a tauren after '
                              'death.',
                              'Tell about returning to the homelands in the form of a death '
                              'knight.',
                              'Recall the elders who now look at the speaker with fear.',
                              'Compare the icy wasteland of Northrend with hot Mulgore.',
                              'Say that death is especially unnatural for a people who revere the '
                              'cycle of life.'],
 ('Tauren', 'Shaman'): ["Talk about the tribe's spiritual bond with the earth and sky.",
                        'Recall the elders who taught respect for the elemental spirits.',
                        "Express reverence to the Earth Mother for this year's rich harvest.",
                        'Tell that shamans do not control the spirits but only humbly ask them for '
                        'help.',
                        'Tell that they dream of one day becoming one of the Spirit Walkers - a '
                        'special kind of tauren shaman able to commune with the spirits of '
                        'deceased relatives and chieftains.',
                        'Talk about the elders who taught how to listen to the earth.',
                        'Discuss the difference between ancestral spirits and elementals.',
                        'Recall the sacred places of Mulgore.',
                        'Talk about the rain ritual.',
                        'Argue whether a shaman may ask the elements for help if they do not '
                        'agree.',
                        'Discuss how the centaurs disrupted the balance of the tauren lands.',
                        'Recall old legends about the first shamans.',
                        'Discuss why the earth sometimes seems wiser than any elder.'],
 ('Tauren', 'Druid'): ['Talk about the ancient tradition of druidism among the tauren.',
                       'Recall the peaceful places of Mulgore where one could spend hours watching '
                       'nature.',
                       'Tell how they love to take on an animal form and spend days in it, living '
                       'the ordinary simple life of an animal to become one with nature.'],
 ('Undead', 'Warrior'): ['Recall their human military service before death.',
                         'Talk about how strange it is to hold a weapon again in hands that once '
                         'belonged to another person.',
                         'Recall that they were once a paladin, but the Light no longer answers '
                         'their prayers.',
                         'Regret not having been able to protect Lordaeron from the undead.',
                         'Express contempt for the humans of Stormwind, calling them cowards who '
                         'did not save Lordaeron from the undead.',
                         'Talk about what it was like to wear armor when the body could still feel '
                         'its weight.',
                         'Recall the old army of Lordaeron.',
                         "Discuss what changed in one's fighting style after death.",
                         'Argue whether it is easier to fight when pain no longer gets in the '
                         'way.'],
 ('Undead', 'Hunter'): ['Recall the hunting grounds of Lordaeron before the Plague.',
                        'Ironically tell how the undead no longer need to fear the smell of blood, '
                        'the cold or fatigue while hunting.',
                        'Recall that Lordaeron used to have only wolves, bears and other ordinary '
                        'animals, and now there are nothing but giant spiders and bats here.',
                        'Talk about the animals that changed after the Plague.',
                        'Argue whether one can still call oneself a hunter if prey is no longer '
                        'needed for food.',
                        'Discuss why living beasts often sense the presence of the undead before '
                        'humans do.',
                        'Wistfully recall the smell of rain in the old forests of Lordaeron.'],
 ('Undead', 'Rogue'): ['Recall the old criminal quarters of Lordaeron.',
                       'Talk about how convenient it is to be an undead rogue: few expect stealth '
                       'from a walking corpse.',
                       'Tell how not needing to breathe lets them use this advantage underwater.',
                       'Recall the old secret passages beneath Lordaeron.',
                       'Talk about the locks they had to pick while still alive.',
                       'Recall old thieving accomplices.',
                       'Discuss how the criminal underworld changed after the Plague.'],
 ('Undead', 'Light Priest'): ['Bitterly recall the temples of the Light in Lordaeron before the '
                              'city fell.',
                              "Reflect on the contradiction between one's former faith in the "
                              "Light and one's present undeath.",
                              'Tell that the Light now burns them and they endure this pain during '
                              'every prayer, but they are grateful that the Light has not '
                              'abandoned them even after death.',
                              'Recall the times when the Light was part of everyday life.',
                              'Talk about the cathedral of Lordaeron before its destruction.',
                              'Discuss why the Light causes pain to the undead.',
                              'Recall the old images of saints and the holy relics of Lordaeron.'],
 ('Undead', 'Shadow Priest'): ['Tell that they were once a priest of the Light, but now they are a '
                               'disgusting rotting corpse and the Light did not help them, so they '
                               'turned to the Shadow',
                               'Say that unlike the Light, The Void is truly powerful and able to '
                               'help',
                               'Say that Lordaeron would not have fallen if they had worshipped '
                               'The Void instead of the Light',
                               "Reflect on how much death has changed one's attitude toward the "
                               'Shadow.',
                               'Recall old nightmares that now seem almost pleasant compared to '
                               'the reality of undeath.',
                               'Reflect on whether the Void is an ally or merely another form of '
                               'slavery.',
                               'Discuss the Old Gods and their attitude toward death.',
                               'Reflect on whether someone who has already lost their life can '
                               'truly fear losing their mind.',
                               'Discuss what is more frightening for the undead: final death or '
                               "the complete disappearance of one's personality.",
                               'Tell of a voice they once heard inside their own head that was '
                               'definitely not their own.'],
 ('Undead', 'Death Knight'): ["Discuss the sense of having lost one's past, and what remains of a "
                              'person after death.',
                              'Say that they were already dead at the moment of being turned into '
                              'a death knight and therefore endured the transformation more '
                              'easily, whereas the living found such a transformation very hard',
                              'Say that after becoming a death knight all the downsides of undead '
                              'existence remained, but at least now they have become strong',
                              'Joke that now they are twice dead',
                              "Recall the moment of liberation from Arthas's control.",
                              'Argue whether memory is the last true sign of life.'],
 ('Undead', 'Mage'): ['Wistfully recall how large the library in Lordaeron was before the city was '
                      'destroyed during the Third War.',
                      'Talk about the old magic schools of Lordaeron and the knowledge that '
                      'perished along with the city.',
                      'Regret that living mages fear and shun them and do not share new knowledge, '
                      'so they have to study magic in the company of other Forsaken',
                      'Talk about the books that burned during the fall of the city.',
                      'Argue whether the lost library of Lordaeron can be restored.',
                      'Talk about the magical academies that vanished along with the kingdom.',
                      'Recall old teachers and their favorite books.'],
 ('Undead', 'Warlock'): ['Recall the underground sorcerers of Lordaeron before the Plague.',
                         'Talk about how strange it is to study forbidden magic now that one has '
                         'become undead oneself and there are no more prohibitions.',
                         'Tell that a summoned succubus once tried to offer them carnal pleasures '
                         'in exchange for her freedom, but such things no longer interest the '
                         'undead.',
                         'Recall the secret cults and magical societies of old Lordaeron.',
                         "Talk about how one's attitude toward demonic magic changed after death.",
                         'Recall the old clandestine magical gatherings.',
                         'Talk about how demons regard the undead.'],
 ('Blood Elf', 'Paladin'): ['Recall the first Blood Knights and how controversial their use of the '
                            'Light was.',
                            'Talk about the temple of the Light in Silvermoon City and the events '
                            'that led to the restoration of the paladin tradition.',
                            'Say how proud they are to be part of the Blood Knights and that the '
                            'Blood Knights are the most reliable defenders of all Silvermoon.',
                            'Criticize humans because, despite their ostentatious service to the '
                            'Light, there are far too many Warlocks and Shadow Priests among them.',
                            'Express regret that too many young blood elves follow the dark path '
                            'of the Warlock instead of the bright paths of the paladin or the '
                            'priest of the Light.',
                            'Tell how they fought tirelessly beneath the walls of Silvermoon City '
                            'alongside other Blood Knights, keeping the undead from approaching '
                            'the city.',
                            'Express hope that one day the Sunwell will be cleansed and all blood '
                            'elves will be able to return to worshipping the Light instead of '
                            'their current dependence on Arcane Magic.',
                            "Express contempt for the traitors who followed Kael'thas Sunstrider "
                            'and feed on demonic Fel magic.',
                            'Recall the time when the Light was more a tool than an object of '
                            'faith for the Blood Knights, and how much has changed since then.',
                            'Recall old training sessions on Sunstrider Isle.'],
 ('Blood Elf', 'Hunter'): ["Recall hunting in the beautiful forests of Quel'Thalas before the "
                           'Scourge came.',
                           'Talk about taming Lynxes, Dragonhawks, Hawkstriders and other animals '
                           "typical of the forests of Quel'Thalas.",
                           'Tell that it is a great honor for them to be part of The Farstriders - '
                           "an elite unit of rangers and defenders of the forests of Quel'Thalas.",
                           'Tell how they tracked down the undead in Eversong Woods and '
                           'exterminated them, keeping them from approaching the walls of '
                           'Silvermoon.',
                           'Tell that Silvermoon makes the best bows in all of Azeroth, and '
                           'neither humans nor night elves are capable of creating anything like '
                           'them.',
                           'Tell that they are ready to explore the darkest and most dangerous '
                           'corners of Azeroth to find something there that will help Silvermoon '
                           'and the blood elves.',
                           'Discuss how the behavior of beasts changed after the defilement of the '
                           'Sunwell.',
                           'Discuss why elves are so fond of exotic pets.',
                           'Recall places where there used to be dense forests and now only traces '
                           "of the Scourge's destruction remain."],
 ('Blood Elf', 'Rogue'): ["Recall the espionage and reconnaissance traditions of Quel'Thalas.",
                          'Talk about how convenient it is to use magical illusions and elven '
                          'architecture for stealthy infiltration.',
                          'Tell how in Murder Row in Silvermoon there were secret rogue clubs '
                          'where they discussed smuggling demonic artifacts into the city and '
                          'robbing the nobility.',
                          'Tell that the nobility of Silvermoon always paid huge sums to have '
                          'rivals eliminated, and many rogues grew rich from this, but many lost '
                          'their heads.',
                          'Discuss the use of magical illusions for stealth.',
                          'Recall old palace intrigues.',
                          'Talk about how easy it was to spot an outsider among the elven '
                          'nobility.',
                          'Discuss why elven architecture creates so many convenient spots for '
                          'covert observation.',
                          'Recall the old habit of carrying a concealed weapon even at official '
                          'receptions.'],
 ('Blood Elf', 'Light Priest'): ["Recall the old sanctuaries of the Light in Quel'Thalas.",
                                 'Talk about the spiritual crisis of the people after the '
                                 'defilement of the Sunwell.',
                                 'Express confidence that one day the blood elf people will return '
                                 'to full worship of the Light and Silvermoon will shine again in '
                                 'all its glory.',
                                 'Remind others of the Sunwell and say that despite all the '
                                 'hardships it remains the heart of the blood elf people, which '
                                 'must not be forgotten',
                                 'Recall the Sunwell before its defilement.',
                                 "Recall the priests who died during the Scourge's attack.",
                                 'Recall the old hymns dedicated to the Light and the Sun.'],
 ('Blood Elf', 'Shadow Priest'): ['Say that studying The Void is necessary to save Silvermoon, and '
                                  'that banning such research is an insane and dangerous decision '
                                  'that proves the incompetence of the Council of Silvermoon.',
                                  'Say that Grand Magister Rommath is a madman and a fool who, out '
                                  'of personal dislike of The Void, is willing to jeopardize the '
                                  'survival of the entire blood elf people and Silvermoon.',
                                  'Say that Warlocks are dangerous idiots who, for the sake of a '
                                  'sense of power, are willing to get involved once again with the '
                                  'extremely dangerous Fel Magic instead of the far more useful '
                                  'The Void.',
                                  'Say that Silvermoon has sunk into incompetence, stupidity and '
                                  'corruption, but in Murder Row (a street in Silvermoon) there '
                                  "are closed secret clubs where the true patriots of Quel'Thalas "
                                  'gather.',
                                  'Discuss how easily the despair after the destruction of '
                                  "Quel'Thalas opens the mind to the Void.",
                                  'Recall the first years after the loss of the Sunwell as a time '
                                  'of spiritual emptiness.',
                                  'Tell of a nightmare that began after reading a forbidden text.'],
 ('Blood Elf', 'Death Knight'): ["Recall the destruction of Quel'Thalas and see the Scourge as the "
                                 "cause of one's own death or of the people's suffering.",
                                 'Talk about the strange experience of returning, now in undead '
                                 'form, to places that were once home.',
                                 'Say that they no longer feel at home in Silvermoon, but are '
                                 'still ready to die for the good of the blood elves.',
                                 'Tell about meeting former comrades who now treat them like a '
                                 'monster.',
                                 'Discuss what it means to be a blood elf if your body no longer '
                                 'feels magic and warmth the way it used to.',
                                 "Recall the beautiful gardens of Quel'Thalas and compare them "
                                 'with icy Northrend.',
                                 'Talk about how strange it is to see living elves carrying on '
                                 'with their ordinary lives.',
                                 'Argue whether a death knight can ever again feel part of their '
                                 'people.',
                                 "Recall the old songs of Quel'Thalas, which now sound especially "
                                 'sad.'],
 ('Blood Elf', 'Mage'): ['Rapturously recall the enormous libraries of Silvermoon City and the '
                         'endless rows of magic books.',
                         "Talk about the magocratic traditions of Quel'Thalas and how natural it "
                         'is for elves to weave magic into everyday life.',
                         'Say that blood elves are the most magically gifted people and that the '
                         'humans of Dalaran will never come even remotely close to them.',
                         'Say that even the most untalented apprentice mage in Silvermoon is '
                         'incomparably stronger and more talented than the high-ranking mages of '
                         'Dalaran.',
                         'Say that it is an honor for them to be part of The Magisters - an '
                         'organization of arcanists, scholars, and political masterminds of '
                         'Silvermoon City.',
                         'Recall how they exterminated the undead on the approaches to Silvermoon, '
                         'burning many ghouls and skeletons at once with their spells.',
                         "Talk about the magical academies of Quel'Thalas.",
                         'Recall their first lessons in arcane magic.',
                         'Discuss the magical fountains and enchanted items that were an ordinary '
                         "part of the nobility's life.",
                         "Recall old magical artifacts lost during the fall of Quel'Thalas.",
                         'Discuss the difference between magic before and after the defilement of '
                         'the Sunwell.',
                         'Recall the times when magic crystals could be found in almost every '
                         'home.'],
 ('Blood Elf', 'Warlock'): ['Recall the trade in fel-infused crystals in Silvermoon City.',
                            'Talk about how, after the destruction of the Sunwell, the line '
                            'between "necessary magic" and dangerous practices became much less '
                            'obvious.',
                            'Say that in Murder Row in Silvermoon there are underground clubs '
                            'where warlocks share forbidden books on Fel magic and consume demonic '
                            'magic',
                            'Say that blood elves should start using Fel magic more and gradually '
                            'give up Arcane magic, because only this way can the people gain '
                            'enough power to survive',
                            "Say that Kael'thas Sunstrider did do bad things, of course, and is "
                            'not an ideal ruler, but he was right in many ways and might have been '
                            "a better ruler of Silvermoon than the current Lor'themar Theron. One "
                            "should not thoughtlessly blame Kael'thas for all the problems; he has "
                            'many merits',
                            'Discuss how thin the line was between "using the fel" and "serving '
                            'the fel".',
                            'Argue whether blood elves really are able to control demons better '
                            'than other peoples.',
                            'Talk about what it is like to see green demonic flames amid the '
                            'golden and red architecture of Silvermoon City, and why the blood '
                            'elves, although they prefer to feed on Arcane Magic, use huge green '
                            'Fel Magic crystals to power the city.']}

# Zone -> why the Horde and Alliance are fighting there again.
FACTION_WAR_FRONTS = {'Ashenvale': 'The Horde is catastrophically short of lumber to build Orgrimmar. The Warsong clan '
              '(Warsong Outriders) begins large-scale logging, ignoring the protests of the local '
              'inhabitants. Night elves of the Silverwing Sentinels rise to defend their lands.',
 'Hillsbrad Foothills': 'The humans of Southshore are surviving citizens of fallen Lordaeron who '
                        'hate the Forsaken and consider these lands their own. The Forsaken of '
                        'Tarren Mill, who in life were also citizens of Lordaeron, led by '
                        'Sylvanas, seek to destroy the human enclave in order to secure Undercity, '
                        'expand their holdings and regain the lost control over their land.',
 'Alterac Mountains': 'The Frostwolf clan are orcish traditionalists who settled long ago in a '
                      'hidden valley of Alterac. An expedition of dwarves of the Stormpike clan '
                      '(Stormpike Guard) arrived in these mountains to excavate titan artifacts '
                      'and laid claim to these lands, deeming the orcs savage invaders.',
 'Arathi Highlands': 'After the fall of the human kingdom of Stromgarde, its ruins and '
                     'surroundings turned into a battlefield. The Forsaken formed the organization '
                     'known as The Defilers to seize the resource-rich lowlands for the needs of '
                     'Undercity and the entire Horde. The Horde, represented by the Defilers, met '
                     'resistance from The League of Arathor — the surviving defenders of '
                     'Stromgarde, supported by Stormwind and Alliance.',
 'Stonetalon Mountains': 'The Horde is actively working the local mines and building logging camps '
                         '(The Scorched Basin) to obtain the construction materials so badly '
                         'needed by its growing cities, which leads to the destruction of the '
                         "region's nature. Night elves and druids organize a guerrilla resistance, "
                         'sabotaging Horde sawmills and attacking, among others, civilians and '
                         'workers.'}

# Speaker faction -> the usual themes of their contempt for the other faction.
FACTION_CRITICISM = {'Horde': 'hypocrites, traitors, they hide behind the Light, but in reality they are rotten, '
          'greedy and cruel inside.',
 'Alliance': 'barbarians, savages, half-animals, they live in filth, have no culture, are '
             'dangerous and unpredictable.'}

# Speaker faction -> enemy race -> what they criticize that race for.
RACE_CRITICISM = {'Alliance': {'Orc': 'Aggressiveness, belligerence, a tendency to solve problems by force, the '
                     'history of invading Azeroth and the use of demonic magic. What may be '
                     'especially irritating is the combination of crudeness with talk of honor: '
                     'orcs far too often use «honor» to justify violence.',
              'Troll': 'Savagery, cruelty, voodoo, a penchant for human sacrifice, cannibalism, '
                       'contempt for civilized society. Their tribal hostility may also be '
                       'perceived as senseless aggression.',
              'Tauren': 'Not contempt, but mockery. They are called cows, and people laugh at '
                        'their slowness and long-winded talk, and at their habit of eating grass '
                        'and vegetation.',
              'Undead': 'Disgusting undead, no different from the Scourge. Necromancy, the use of '
                        'corpses, poisons, plague and experiments on the living, the abduction of '
                        'Alliance members for cruel experiments and for turning them into '
                        'will-less puppets.',
              'Blood Elf': 'Arrogance, snobbery, a drug-like addiction to magical energy and a '
                           'willingness to cooperate with dubious forces for the sake of their own '
                           'survival. They switch allies too easily when it is profitable, know no '
                           'loyalty, and regard both the Horde and the Alliance merely as '
                           'resources that should die in their place.'},
 'Horde': {'Human': 'Arrogance, conviction of their own civilized nature, a desire to command '
                    'others, a tendency to regard the Horde as barbarians and monsters. What is '
                    'especially irritating is that humans are often seen as hypocritical: they '
                    'talk about honor and order, yet they themselves set up internment camps for '
                    'orcs with enormous death rates and waged brutal wars. They try to subjugate '
                    'all of Azeroth and do not tolerate resistance.',
           'Dwarf': 'Stubbornness, rudeness, love of alcohol, greed for gold and treasure, an urge '
                    'to dig into the earth and destroy ancient places for the sake of resources. '
                    'An obsession with producing dangerous weapons and with war. Disrespect for '
                    'borders and incursions into Horde lands for the sake of excavations and '
                    'resources.',
           'Night Elf': 'A haughty attitude toward other races, insularity, contempt for the Horde '
                        'and other outsiders. Their conviction of their own moral superiority and '
                        "their attempts to control nature, obstructing the Horde's logging, even "
                        'though the Horde needs lumber for its development and to provide housing '
                        'for its people.',
           'Gnome': 'An obsession with technology with no safety precautions and no clear purpose, '
                    'constant development of technologies that are dangerous to the gnomes '
                    'themselves, explosions for the sake of explosions under the banner of '
                    'science. Disregard for the environment and turning vast lands into '
                    'uninhabitable toxic places. Their own city Gnomeregan was contaminated with '
                    'radiation because of their stupidity. Their inventions bring only destruction '
                    'and death.',
           'Draenei': 'Cowards and fugitives. They fled from Argus to Draenor, and from Draenor to '
                      'Azeroth, escaping the Burning Legion, instead of staying put and defending '
                      'their land. For all their cowardice they are arrogant and Self-Righteous, '
                      'fanatically worship the Holy Light, blindly follow dogma, and lecture '
                      'everyone around them on how to live properly. For all their ostentatious '
                      'righteousness, there are many traitors among them who have gone over to the '
                      'side of the Burning Legion; they are susceptible to corruption. They are '
                      'also called goats because of their hooves and horns.'}}

# Speaker faction -> recent local clashes to condemn.
LOCAL_CONFLICTS = {'Alliance': ['Orcs raided a night elf camp in Ashenvale and killed several guards and civilians '
              '(merchants, blacksmiths, herbalists or any other peaceful professions can be used). '
              'They were not even warriors and posed no threat.',
              'Forsaken from Tarren Mill in Hillsbrad Foothills have abducted several Alliance '
              'farmers and are now keeping them in cages. There are fears that new poisons and '
              'alchemical concoctions will again be tested on them, as has happened before. '
              'Hillsbrad Foothills is unsafe for the living, even though it is historically a '
              'human region',
              'In Hillsbrad Foothills, the bodies of humans previously abducted by the Forsaken '
              'have been found again. Their bodies are mutilated beyond recognition, bearing '
              'traces of chemical burns and of the use of various poisonous substances. The '
              "Horde's undead are once again using civilians as test subjects for their vile "
              'experiments',
              'Not far from Theramore, a patrol of Alliance guards has gone missing. A few days '
              'later their bodies were found nearby in the swamp, bearing the marks of Horde axes. '
              'The Horde continues its sabotage and subversive raids near Theramore',
              'In Loch Modan, a group of Horde scouts plundered and burned a peaceful dwarven '
              'caravan. This is historically dwarven land and the Horde has no business being '
              'there, yet they keep sending their groups there to plunder',
              'In Silverpine Forest, the Forsaken have once again raided the southern part of the '
              'region, where a few scattered settlements of living humans remain. Almost the '
              'entire region belongs to the Horde, represented by the Forsaken; only a few small '
              'settlements remain in the south, and the Horde continues to methodically attack '
              'them and kill the remaining humans, forcing them to leave Silverpine Forest.'],
 'Horde': ['In The Barrens, an organized group of Alliance warriors (humans and night elves) has '
           'once again plundered and burned a peaceful trade caravan OR a group of peaceful '
           'travelers moving along The Gold Road. This is historically Horde land, but the '
           'Alliance keeps plundering and exterminating civilians on land that is not theirs',
           'In Mulgore (the tauren homeland), dwarves have arrived and set up an excavation site '
           "they call Bael'dun Digsite. Not only is this someone else's land where the dwarves "
           'have no right to be, they are also digging there and destroying the local nature, and '
           'they kill every tauren who comes near them, even civilians who have accidentally lost '
           'their way',
           'In the southern part of The Barrens, on the coast, the Alliance fortress Northwatch '
           'Hold has existed for several years now. Not only does The Barrens historically belong '
           'to the Horde, so the Alliance has no right to establish settlements there, but they '
           'also regularly launch raids from it. Bandit groups from Northwatch Hold burn farms, '
           'kill civilians, rob caravans, and then hide behind the fortress walls again',
           'Tiragarde Keep in Durotar is still active. Although this illegal Alliance fortress on '
           'Horde lands was burned and destroyed several years ago, remnants of Alliance troops '
           'still live in its ruins. They no longer resemble soldiers at all and have become '
           'common filthy bandits who live by robbing and murdering travelers. They have turned '
           'all of southern Durotar into a dangerous place.',
           "In Ghostlands (southern Quel'Thalas), yet another night elf camp has been found in the "
           'mountains. The night elves continue their espionage and sabotage operations in the '
           'lands of the Blood Elves.',
           'In Silverpine Forest (Horde territory where the Forsaken live), humans have once again '
           'raided the Sepulcher - a major Forsaken settlement. Not only do the humans illegally '
           'live in a region that does not belong to them, but they also attack the local '
           'inhabitants.']}
