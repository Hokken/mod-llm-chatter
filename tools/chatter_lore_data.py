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
           'Talk about the smell of fresh bread in human cities.',
           'Reminisce about the bustling markets of Stormwind.',
           'Tell which part of Stormwind you like best.',
           "Argue about which human architecture is more beautiful — Stormwind's (more "
           "down-to-earth and cozy) or Lordaeron's (more Gothic and luxurious).",
           'Reminisce about the countryside of Elwynn Forest.',
           'Tell about family farms and villages.',
           'Compare life in the city and in the countryside.',
           'Reminisce about fairs, holidays and folk festivities.',
           'Talk about a favorite human dish.',
           'Talk about how expensive it has become to live in big cities.',
           'Reminisce about old inns that are now closed.',
           'Recall Lordaeron before the Third War.',
           'Tell what Stratholme was like before the plague.',
           'Talk about the abandoned lands of Lordaeron.',
           'Talk about the stories the older generation tells about the Second War.',
           'Argue about how much Alterac has changed.',
           'Talk about the stories human families tell about the wars with the orcs.',
           'Recall people who never returned from Lordaeron.',
           'Discuss the fate of the old human kingdoms (Lordaeron was destroyed by the undead, '
           'Alterac was destroyed by other humans for its alliance with the orcs in the Second '
           'War, Gilneas walled itself off from the world with a great wall and isolated itself).',
           'Talk about ruined cities you would like to see restored (Alterac, Lordaeron, '
           'Stratholme).',
           'Talk about what portal services cost.',
           'Discuss the quality of human blacksmiths.',
           'Argue about which human cuisine is better.',
           'Recall a favorite bard song.',
           'Talk about the unusual people one meets while traveling.',
           'Compare human habits with the habits of other races.',
           'Talk about how many different accents humans have.'],
 'Dwarf': ['Talk about the coolness and the stone halls of Ironforge.',
           'Recall the hum of the Great Forge.',
           'Talk about a favorite tavern in Ironforge.',
           'Argue about where in Ironforge the best ale is served.',
           'Recall the smell of the forge.',
           'Tell about a favorite spot near the Great Forge.',
           'Talk about cities with a lot of open space.',
           'Talk about how much cozier stone rooms are than wooden ones.',
           'Argue about which ale is better.',
           'Tell about unusual varieties of dwarven beer.',
           'Talk about what makes a drinking bout memorable.',
           'Talk about drinks that "elves call beer" and how they compare with other liquids.',
           'Tell how to cook meat properly.',
           'Argue about which game is tastier.',
           'Recall festive feasts.',
           'Discuss how many mugs of ale one can drink before the hall starts spinning.',
           'Talk about the cold mountain tunnels.',
           'Talk about the most beautiful mines dwarves speak of.',
           'Discuss rare minerals.',
           'Talk about ore worth finding.',
           'Talk about what makes an expedition successful.',
           'Tell about a deep mine that no one wants to go down into anymore.',
           "Joke that dwarves don't need stairs — just wider steps.",
           'Talk about tables built for taller folk.',
           "Tell what it's like to travel alongside tall races.",
           'Discuss beards.',
           'Talk about beards and how long they can grow.',
           'Argue about proper beard care.',
           'Talk about famous dwarven ancestors and the stories told of them.'],
 'Gnome': ['Recall old Gnomeregan before the catastrophe.',
           'Tell about a favorite workshop.',
           'Recall the unusual mechanisms left behind in Gnomeregan.',
           'Argue about which level of Gnomeregan was the most interesting.',
           'Talk about what Gnomeregan could become after it is restored.',
           'Recall old engineers.',
           'Talk about the first serious breakdown of a new invention and what engineers learn '
           'from it.',
           'Discuss a favorite type of mechanism.',
           'Talk about a device worth building.',
           'Talk about whether a device can be too reliable.',
           "Explain why an exploding mechanism isn't necessarily a bad thing.",
           'Argue about the merits of gnomish versus dwarven engineering.',
           'Talk about the biggest explosions gnomish engineering has produced.',
           'Talk about what failed experiments teach.',
           'Discuss why invent something simple when you can make something complicated.',
           'Come up with improvements for ordinary objects.',
           'Discuss the idea of mechanical transport.',
           'Talk about goblin engineering and how far it can be trusted.',
           'Talk about chairs built for bigger folk.',
           'Tell how inconvenient it is to use things made for larger races.',
           'Joke that gnomes are the best at saving space.',
           'Argue about which sound is more pleasant: the whirring of a mechanism or an explosion.',
           'Tell how being small makes it easier to dodge attacks in combat.'],
 'Night Elf': ['Talk about Teldrassil and life beneath its great branches.',
               'Talk about the beauty of the night forests.',
               'Talk about the quiet of Darnassus.',
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
               'Talk about the unusual animals of the forest.',
               'Discuss the night sounds of the forest.',
               'Talk about the rain in the forest.',
               'Talk about moonlight.',
               'Tell about a beautiful glade.',
               'Talk about how other races treat nature.',
               'Talk about Moonglade and how it has preserved its nature by staying closed to most '
               'outsiders.',
               'Tell about a favorite spot for stargazing.',
               'Discuss the constellations.',
               'Talk about hunting at night.',
               'Recall quiet nights by the campfire.',
               'Recall the night sky of Kalimdor.'],
 'Draenei': ['Recall the Exodar before the catastrophe.',
             'Tell about unusual chambers of the Exodar.',
             'Discuss the strange technologies of the draenei.',
             'Talk about the peaceful halls of the Exodar.',
             'Talk about a favorite place on the islands of Azuremyst Isle.',
             'Recall the crystalline structures.',
             'Tell about strange mechanisms that even the draenei still do not understand.',
             'Recall Draenor before its destruction.',
             'Tell stories about Nagrand.',
             'Talk about the old sky of Draenor.',
             'Talk about the beauty of old Nagrand.',
             'Recall the homeland.',
             'Compare old Draenor with present-day Outland.',
             'Talk about what Draenor could have become if it had not been destroyed.',
             'Recall the old draenei settlements.',
             'Talk about the stories draenei families tell about life before arriving on Azeroth.',
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
         'Talk about the dust in Orgrimmar.',
         'Talk about the Valley of Trials and the trials young orcs go through to earn the status '
         'of an adult.',
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
         'Talk about what a victory over a strong opponent means.',
         'Discuss the concept of honor.',
         'Tell about an old mentor.',
         'Argue about what matters more — strength or endurance.',
         'Discuss meat.',
         'Argue about the best way to cook a boar.',
         'Talk about the portions in Blood Elf taverns.',
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
           'Talk about the advice of tribal priests.',
           'Talk about how to tell that a spirit is trying to warn you.',
           'Talk about what makes an ambush succeed.',
           'Talk about the tracks of an unusual creature.',
           'Discuss a favorite fishing spot.',
           'Tell a scary story about a predator.',
           'Joke about long tusks.',
           'Talk about how other peoples understand the troll accent.',
           'Talk about blood elves and how squeamish they can seem.',
           'Discuss who in a troll village can eat the most meat.'],
 'Tauren': ['Talk about the green plains of Mulgore.',
            'Recall sunrises over the plains.',
            'Talk about the tranquility of the homeland.',
            'Tell about a favorite spot by the watering hole.',
            'Reminisce about walks across the steppes.',
            'Compare different pastures.',
            'Talk about the smell of grass after rain.',
            'Talk about the old trees of Mulgore that remember many generations.',
            'Talk about treating prey with respect.',
            'Talk about the old hunters who teach the young.',
            'Talk about what makes tracking difficult.',
            'Discuss unusual animal behavior.',
            'Tell stories about the ancestors.',
            'Talk about the spiritual side of the hunt.',
            'Recall the advice of the elders.',
            'Discuss the signs of nature.',
            'Talk about sacred places.',
            "Recall the tribe's ceremonies.",
            'Discuss the best places to sleep under the open sky.',
            'Talk about the rooms in the taverns of other races.',
            'Talk about a favorite herbal blend.',
            'Recall the taste of fresh milk.',
            'Compare different kinds of tea and what they are best blended with.',
            'Talk about the chairs other races build.'],
 'Undead': ['Recall Lordaeron before its destruction.',
            'Tell about life in the old kingdom.',
            'Recall the streets of old Lordaeron.',
            'Talk about Lordaeron before the Plague.',
            'Tell what Stratholme used to look like.',
            'Recall the old inns.',
            'Talk about the people the Forsaken knew in life.',
            'Recall your family.',
            'Tell about the forgotten places of Lordaeron.',
            'Recall the farms of Lordaeron, now abandoned and ravaged.',
            'Reminisce about the noisy, happy carnivals in Lordaeron before the undead laid it '
            'waste.',
            'Reminisce about the bustling bazaars and fragrant pastries of Stratholme before '
            'Arthas destroyed the city and slaughtered its inhabitants.',
            'Tell how after the plague giant spiders appeared in Tirisfal Glades, although before '
            'that these had been fairly calm and safe woods.',
            'Talk about food when one can no longer taste it.',
            'Recall a favorite dish that is now impossible to taste.',
            'Joke about problems with smells.',
            "Discuss what to do if you've lost a finger.",
            'Talk about the condition of Forsaken bones.',
            'Discuss how long one can go without sleep.',
            'Joke that death has greatly simplified some everyday problems.',
            'Recall what it was like to feel cold.',
            'Talk about which sensations disappeared after death.',
            'Joke about your own death.',
            'Discuss who looks the most alive among the undead.',
            'Talk about Forsaken limbs that fall off at the worst moments.',
            'Argue about how well your face has been preserved.',
            'Joke about necromancers.',
            'Tell about the most ridiculous way to lose a body part.',
            'Recall life before death.',
            'Try to remember a forgotten name.',
            'Talk about Forsaken who dream of being alive again.',
            'Talk about an old song that no one has performed in a long time.',
            'Recall the smell of your home.',
            'Talk about those who are gone even from among the dead.',
            'Talk about how the living see the Forsaken, and the thoughts and feelings the '
            'Forsaken still have.'],
 'Blood Elf': ['Reminisce about the fine selection of wines in the taverns of Silvermoon City.',
               'Argue about which tavern serves the best drink.',
               'Reminisce about evening strolls through the streets of Silvermoon City.',
               'Tell about the most beautiful building in the city.',
               'Talk about how other cities look next to Silvermoon.',
               'Recall the music playing in the taverns.',
               'Talk about the fountains and gardens of Silvermoon City.',
               'Discuss a favorite district of the city.',
               'Recall the magical lights of the streets.',
               'Compare Silvermoon City with Dalaran.',
               'Talk about how much Silvermoon City has changed since the Third War.',
               'Recall the underground trade in Fel Magic crystals in Silvermoon City',
               "Recall the forests of Quel'Thalas before the Scourge.",
               'Tell about walks in the forest.',
               'Talk about old elven ruins.',
               "Recall the taste of fruit from Quel'Thalas.",
               'Tell about a favorite spot by the lake.',
               'Talk about the old songs.',
               'Recall family homes.',
               'Talk about sunsets over the forest.',
               'Discuss magical jewelry.',
               'Talk about skill in wielding magic.',
               'Tell about a beautiful spell.',
               'Discuss the use of magic in everyday life.',
               'Tell about magical items.',
               'Recall your first encounter with a magical artifact.',
               'Argue about beautiful clothes.',
               'Discuss jewelry.',
               'Talk about hairstyles.',
               'Talk about how other races look to blood elf eyes.',
               'Discuss favorite clothing colors.',
               'Tell about expensive fabrics.',
               'Argue about which gemstone is more beautiful.',
               'Talk about perfumery.',
               'Recall a favorite shop in Silvermoon City.',
               'Talk about the food of other races',
               'Talk about the conditions in orc taverns',
               'Talk about how orcs and trolls keep themselves']}

# Class style -> topics a bot of that class may raise.
CLASS_TOPICS = {'Warrior': ['Recall their first real battle.',
             'Talk about opponents who turn out to be stronger than expected.',
             'Talk about recovering from serious battle wounds.',
             'Argue about which weapon is best for real combat.',
             'Discuss the advantages of an axe over a sword.',
             'Talk about especially heavy weapons and who can lift them.',
             'Talk about the biggest shields a warrior can carry.',
             'Talk about how a shield can save a life.',
             'Talk about defeating an opponent through patience.',
             'Discuss whether it is worth wearing heavy armor on a long expedition.',
             'Talk about sleeping in a full suit of armor.',
             'Talk about how hard it is to repair armor after a real battle.',
             'Recall their first mentor.',
             'Talk about their toughest training session.',
             'Discuss how many hours a day one should train.',
             'Argue about whether strength or technique matters more.',
             'Talk about an unusual way of training.',
             'Talk about stamina and how a warrior builds it.',
             'Discuss training dummies.',
             'Talk about serious injuries in training.',
             'Talk about training weapons that are more dangerous than real ones.',
             'Argue about what matters more: courage or caution.',
             'Talk about the best commander they have had.',
             'Talk about poorly organized squads.',
             'Discuss what it is like to guard someone who constantly gets into trouble.',
             'Talk about mages who use a warrior as a living shield.',
             'Discuss how useful it is to be able to fight without a weapon.',
             'Talk about a tavern brawl.',
             'Talk about fighting with a completely unsuitable weapon.',
             'Talk about the constant need to repair armor.',
             'Look for a good blacksmith.',
             'Argue about where weapons are sharpened best.',
             'Discuss how comfortable different types of armor are.',
             'Talk about how sturdy tavern chairs are.',
             'Talk about their habit of sharpening their weapon before going to sleep.'],
 'Paladin': ['Recall the moment they first felt the Light.',
             'Talk about their mentor.',
             'Discuss what it means to be worthy of the Light.',
             'Reflect on whether the Light can help a person who has lost hope themselves.',
             'Recall a prayer from childhood.',
             'Discuss why some people find faith easily and others do not.',
             'Talk about a place where the Light can be felt especially strongly.',
             'Argue about what matters more for a paladin - faith or discipline.',
             'Talk about times the Light is said to have saved a life.',
             'Talk about healing someone with the Light.',
             'Talk about their first service.',
             'Talk about protecting someone truly important.',
             'Discuss what it means to be a shield for others.',
             'Talk about whether people take protection for granted.',
             'Discuss the hardest choices between orders and conscience.',
             'Talk about a fallen comrade.',
             "Discuss a commander's responsibility.",
             'Argue about when a paladin has the right to retreat.',
             'Argue about which weapon suits a paladin best.',
             'Talk about their favorite hammer.',
             'Discuss how important a shield is.',
             'Recall their first set of real armor.',
             'Talk about a famous paladin weapon.',
             'Discuss the differences between a holy paladin and an ordinary warrior.',
             'Talk about the weight of a full suit of armor.',
             'Recall life in the order.',
             'Talk about the training of young paladins.',
             'Argue about discipline.',
             'Discuss how strict a mentor should be.',
             'Talk about temple ceremonies.',
             'Talk about temple services that far too many people attend.',
             'Discuss how a paladin can rest without forgetting their duty.'],
 'Hunter': ['Talk about the most beautiful place for hunting.',
            'Recall a dawn in the forest.',
            'Discuss the tracks of different animals.',
            'Talk about rare beasts worth seeing.',
            'Argue about which region is best suited for hunting.',
            'Talk about hunts that last several days.',
            'Talk about beasts that outsmart hunters.',
            'Discuss how to tell that a beast is approaching by the sounds of the forest.',
            'Talk about hunters and respect for nature.',
            'Talk about their first pet.',
            'Talk about taming especially dangerous beasts.',
            "Discuss their pet's favorite food.",
            'Talk about pets that keep running away.',
            "Talk about their beast's temperament.",
            'Compare different animal companions.',
            'Argue about which animal is best suited for a long journey.',
            'Tell a funny story about their pet.',
            'Talk about letting a tamed beast go.',
            'Compare bows and crossbows against firearms.',
            'Talk about their longest accurate shot.',
            'Argue about the advantages of the bow and the crossbow.',
            'Recall the first arrow they made themselves.',
            'Talk about bowstrings and what makes a bad one.',
            'Talk about a marksmanship contest.',
            'Discuss shooting in strong wind or a blizzard.',
            'Talk about the best place to set up camp.',
            'Discuss how to identify a safe place to spend the night.',
            'Recall their coldest overnight stay.',
            'Talk about noise during a hunt.',
            'Talk about the tracks of an unknown creature.',
            'Discuss which zones of Azeroth are best suited for wandering.'],
 'Rogue': ['Talk about infiltrating guarded places.',
           'Talk about how close a rogue can come to being caught.',
           'Discuss which place is the hardest to guard.',
           'Argue about what matters more for stealth - patience or speed.',
           'Talk about the most attentive guard.',
           'Talk about places that are better protected than they look.',
           "Discuss how to spot the guards' blind spot.",
           'Talk about armor that is too noisy for quiet work.',
           'Talk about the valuables worth stealing.',
           'Talk about especially complicated locks.',
           'Talk about the first chest they picked open on their own.',
           'Discuss the most cunning traps.',
           'Talk about locks too complicated to pick.',
           'Argue about who makes better locks - gnomes, dwarves or goblins.',
           'Talk about the unusual items found in locked chests.',
           'Discuss how to tell that a chest was deliberately left as a trap.',
           'Discuss their favorite poison.',
           'Talk about the dangers of handling poison.',
           'Argue about which poison is the hardest to make.',
           'Talk about the ingredients a rogue relies on.',
           'Talk about the danger of mixing up vials of poison and potions.',
           'Discuss the smell of various alchemical mixtures.',
           'Recall a former employer.',
           'Talk about a strange client.',
           'Discuss what makes a theft job the worst kind.',
           'Talk about theft contracts that turn out to be something else entirely.',
           'Talk about the gangs a rogue has to deal with.',
           'Discuss who cannot be trusted.',
           'Argue about how good a criminal someone can be if they love to talk too much.',
           'Talk about pockets and inner compartments.',
           'Talk about their favorite cloak.',
           'Discuss comfortable footwear for walking silently.',
           'Argue about how suspicious it is to look too suspicious.',
           'Joke that a good rogue should be able to disappear even before appearing.'],
 'Light Priest': ['Recall their first experience of turning to the Light.',
                  'Talk about a prayer that they remember especially well.',
                  'Discuss how a person finds faith after a traumatic event.',
                  'Talk about a miraculous healing.',
                  'Talk about saving a life through the Light.',
                  'Discuss whether the Light can help someone who does not believe in themselves.',
                  'Talk about a temple where it is especially pleasant to pray.',
                  'Compare the religious traditions of different peoples.',
                  'Argue about whether one needs to understand the Light in order to serve it.',
                  'Ponder the difference in how the Light is perceived in the Alliance and in the '
                  'Horde.',
                  'Discuss the difference between faith and hope.',
                  'Talk about the most severe wounds a healer faces.',
                  'Discuss how important it is to calm a wounded person before healing them.',
                  'Talk about fighters who ask for help late.',
                  'Talk about the mistakes healers learn from.',
                  'Talk about unexpectedly resilient patients.',
                  'Discuss how to heal someone who is afraid of healers.',
                  'Argue about what matters more: healing the body or the spirit.',
                  'Discuss discipline during priestly rituals.',
                  "Talk about controlling one's own emotions for the sake of serving the Light.",
                  'Talk about strict mentors at the temples.',
                  'Argue about when obedience becomes blind submission, and when it is an '
                  'important part of serving the Light.',
                  'Reflect on the price of self-discipline.',
                  'Discuss how to stay calm during a panic.',
                  'Talk about how discipline and calm can save a group.',
                  'Discuss temple traditions.',
                  'Recall a religious holiday.',
                  'Talk about old prayers.',
                  'Argue about the differences between the temples of different peoples.',
                  'Discuss why some people are afraid of priests.',
                  'Talk about the old priests who mentor the young.',
                  'Talk about beautiful temple music.',
                  'Reflect on what draws priests to take care of others.'],
 'Shadow Priest': ['Reflect on the nature of fear.',
                   'Discuss why people are afraid of the dark.',
                   "Talk about breaking an enemy's will with terrifying visions.",
                   'Tell how a sufficiently horrifying illusion can win a battle even without '
                   'dealing real damage to the enemy.',
                   "Discuss how, in combat, it is far more important to damage the enemy's mind "
                   'and soul than their body.',
                   "Talk about looking into an enemy's soul to find their most horrifying fear.",
                   "Talk about turning an enemy's dream into a nightmare.",
                   'Talk about filling opponents with such terror that they flee the battlefield.',
                   'Talk about their most terrifying dream.',
                   "Talk about moments when a Shadow Priest's own mind fails them.",
                   'Discuss how easy it is to instill fear in a person.',
                   'Argue about whether fear can be defeated by fully understanding it.',
                   'Talk about enemies who seem immune to fear.',
                   'Discuss why some people seek out danger themselves.',
                   'Describe the sensation of being in total darkness.',
                   'Discuss the difference between ordinary shadow and The Void.',
                   'Talk about their first experience of touching The Void.',
                   'Discuss whether one can use The Void without letting it change oneself.',
                   'Talk about strange visions.',
                   'Discuss the voices that can be heard during severe exhaustion.',
                   'Reflect on the boundary between insight and madness.',
                   "Discuss whether madness always means losing one's mind.",
                   'Talk about people who speak nonsense but turn out to be right.',
                   'Talk about their own strangest vision.',
                   'Discuss why some people fear those who talk about The Void.',
                   'Argue about whether one can stay sane while peering into forbidden knowledge.',
                   'Talk about people who do not fear dying but have a different fear that can be '
                   'used against them.',
                   'Talk about the whisper of thousands of voices Shadow Priests describe: '
                   'individually vague and blurred, together merging into intelligible speech',
                   'Discuss the stories of priests who went without sleep for weeks reading '
                   'ancient manuscripts about The Void until a whisper offered them forgotten '
                   'knowledge',
                   'Talk about the visions some Shadow Priests describe of the grand black granite '
                   'walls of a forgotten, sunken city',
                   'Talk about the whispered tales of an ancient sunken city that existed long '
                   'before everything known to us; perhaps not even material, but the ideal of '
                   'creation, a cradle... for what? Or for whom?',
                   'Talk about dreams that change the details of the past until no one can tell '
                   'which memories are real',
                   'Talk about the voices a Shadow Priest hears, that whisper, speak, scream, '
                   'plead and demand',
                   'Talk about how hard it can be to tell what one read in ancient manuscripts '
                   'from what the voices whispered',
                   'Talk about tales of a vast, empty library whose bookcases vanish into '
                   'darkness, which no one can remember visiting',
                   'Talk about visions of an ancient city filled with a Darkness from beyond, gone '
                   "the moment one opens one's eyes",
                   'Talk about manuscripts on ancient peoples whose souls were sacrificed to the '
                   'darkness, and how time blurs for those who study them',
                   'Talk about the whispers that the heart of the drowned god is black ice',
                   'Talk about the feeling that everything is only a dream',
                   'Talk about the feeling that all of this has already happened and is repeating, '
                   'again and again',
                   'Talk about resisting the pull of the Void and the truth it promises',
                   'Talk about the tales that only mad creatures roam the streets of the sunken, '
                   'sleeping city',
                   'Talk about visions of the tormented souls of ancestors clinging to the living',
                   'Talk about memories that may be dreams, such as a gigantic cave whose walls '
                   'swarm with carnivorous insects',
                   'Talk about dreams of grand black granite halls without light or mercy, only '
                   'emptiness and fear'],
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
                  "Discuss a death knight's first rune.",
                  'Argue about the advantages of different runes.',
                  'Recall creating a weapon.',
                  'Talk about unusual weapons.',
                  'Discuss the difference between an ordinary sword and a runeblade.',
                  "Recall the time under the Lich King's rule.",
                  'Talk about the loss of their own will.',
                  'Discuss what it means to be free after slavery.',
                  'Talk about their first independent decision after being freed.',
                  'Recall those who could not break free.',
                  'Discuss how the living regard death knights.',
                  'Talk about how the living look at death knights.',
                  'Talk about what a death knight may find on returning to their hometown.',
                  "Talk about death knights who, once freed from the Lich King's control, find "
                  'their old friends dead or turned away.',
                  'Talk about the eternal hunger death knights describe.',
                  'Talk about the rage and the urge to destroy the living that death knights '
                  'describe, and suppressing it by force of will.',
                  'Joke about being unable to smell rotten meat.',
                  'Discuss whether a death knight needs to sleep.',
                  'Talk about maintaining armor one can no longer feel.',
                  'Talk about life inside the necropolises - enormous flying fortresses that house '
                  'death knight bases.',
                  'Talk about Acherus (The Ebon Hold) - a huge flying necropolis fortress that '
                  "serves as the base of the death knights who are free from the Lich King's "
                  'control.'],
 'Shaman': ['Talk about their first conversation with a spirit.',
            'Discuss the temperament of fire.',
            'Argue about which element is the most unpredictable.',
            'Talk about a powerful thunderstorm.',
            'Recall the first time calling down lightning.',
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
            'Talk about people tripping over totems.',
            'Talk about strange places to set down a totem.',
            'Discuss the differences between the totems of different peoples.',
            'Recall training under a mentor.',
            'Talk about a ritual that takes several hours.',
            'Discuss the balance between the elements.',
            'Argue about whether a shaman can misinterpret the spirits.',
            'Talk about places where nature is especially strong.',
            'Talk about the most unusual spirit they have ever encountered.'],
 'Mage': ['Recall their first spell.',
          'Talk about the serious magical failures every mage risks.',
          'Discuss their favorite school of magic.',
          'Argue about which school of magic is the most useful in everyday life.',
          'Talk about spells that are harder than they look.',
          'Discuss the difference between theoretical and practical magic.',
          'Recall an old magic mentor.',
          'Talk about a rare spell.',
          'Argue about whether magic can be considered an art.',
          'Talk about teleports that go wrong.',
          'Recall their first journey through a portal.',
          'Argue about how safe it is to teleport after a heavy meal.',
          'Talk about the strange places a misdirected portal can lead.',
          'Discuss whether one can learn to identify a place by the feel of its magic.',
          'Discuss using magic for cooking.',
          'Talk about magical lighting.',
          'Argue about why anyone would carry a torch at all when there is magic.',
          'Discuss enchanted items.',
          'Talk about magical items that turn out to be useless.',
          'Come up with everyday uses for combat spells.',
          'Talk about spells going wrong.',
          'Discuss an accidentally summoned creature.',
          'Recall their first attempt to open a portal.',
          'Talk about Polymorphs that last longer than they should.',
          'Argue about which magical mistake looks the most ridiculous.'],
 'Warlock': ['Talk about the first demon they summoned.',
             'Discuss the temperaments of different demons.',
             'Talk about disobedient demons.',
             'Talk about summoned creatures that are smarter than expected.',
             'Argue about which demon is the most useful.',
             'Talk about how a demon can ruin everything.',
             'Discuss whether demons can be trusted at all.',
             'Talk about a demon that constantly argues with its master.',
             'Talk about a demon that turned out to be too "friendly" toward its master',
             'Recall why they began studying dark magic.',
             'Discuss how other mages regard warlocks.',
             'Reflect on why people fear forbidden knowledge.',
             'Argue about whether there is magic that truly must never be used.',
             'Talk about spells better left unlearned.',
             'Talk about warlocks being called monsters.',
             'Discuss whether mages are right to forbid themselves fel magic, the most powerful '
             'magic there is',
             'Talk about places corrupted by the fel.',
             'Discuss the changes it causes.',
             'Argue about whether the fel can be used without succumbing to it.',
             'Recall the first time they saw the aftermath of the fel.',
             'Talk about the strange green fire.',
             'Discuss why the fel is so different from ordinary magic.',
             'Discuss the nature of the soul.',
             'Talk about souls that are especially hard to break.',
             'Talk about how people react to warlocks.',
             'Joke that people always blame the warlock first.',
             'Talk about guards who refuse even to look at a warlock.',
             'Discuss why some people still turn to warlocks for help despite the fear around '
             'them.',
             'Talk about the most absurd rumors about warlocks.'],
 'Druid': ['Talk about their favorite forest.',
           'Recall a place where nature feels especially alive.',
           'Discuss an unusual plant.',
           'Talk about the scent of the forest after rain.',
           'Talk about an ancient tree.',
           'Argue about which forest of Azeroth is the most beautiful.',
           'Talk about the logging of forests.',
           'Discuss the consequences of polluting nature.',
           'Recall a place that has changed greatly in recent years.',
           'Talk about their favorite animal.',
           'Discuss unusual animal behavior.',
           'Recall their first shapeshift.',
           'Talk about what it is like to see the world through the eyes of a beast.',
           'Argue about which animal is the most convenient for traveling.',
           "Discuss the difference between a druid's hunt and an ordinary person's hunt.",
           'Talk about unusual beasts.',
           'Talk about animals that save lives.',
           'Joke about how awkward it is to get through doorways in Cat Form.',
           'Talk about the attention Bear Form attracts.',
           'Discuss which form is more convenient for traveling.',
           'Talk about the first time they turned into a bird.',
           'Talk about not being recognized in animal form.',
           'Argue about which form is the most beautiful.',
           'Talk about strange places to shapeshift.',
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
                        "Discuss whether human warriors' wits can make up for orc warriors' "
                        'greater strength.',
                        'Talk about where the most powerful weapons are found, often far from '
                        'Stormwind.',
                        'Talk about polishing armor, and how paladins have squires for it.',
                        'Talk about the view, common in the Alliance, that orcs cannot be trusted '
                        'because of their demonic past.',
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
                        'Discuss how sincere blood elf paladins are, given that they serve the '
                        'Horde.',
                        'Recall Sire Uther Lightbringer, who was one of the first paladins and is '
                        'still the standard for many.',
                        'Recall the old cathedral where services were once held.',
                        'Discuss how the paladins of Stormwind differ from the elven Blood '
                        'Knights, and the claim that the blood elves see the Light merely as a '
                        'tool.'],
 ('Human', 'Hunter'): ['Talk about hunting in Elwynn Forest and how much calmer it used to be.',
                       'Talk about the great hunting grounds of Lordaeron, which no longer exist.',
                       'Talk about selling game in Goldshire near Stormwind.',
                       'Talk about the wild beasts of Elwynn Forest and the people they threaten.'],
 ('Human', 'Rogue'): ["Recall the dark alleys of Stormwind's Old Town and the local information "
                      'brokers.',
                      'Talk about how easy it is to vanish among the numerous inns of human '
                      'cities.',
                      'Talk about the valuable magical items kept in the Mage Quarter of '
                      'Stormwind.',
                      'Talk about SI:7 (the intelligence organization led by Mathias Shaw) '
                      'recruiting rogues, and why many would rather pinch valuables from the '
                      'nobility.',
                      'Talk about the petty thefts young rogues start with.',
                      'Discuss how easy it is to hide in a big human city.',
                      'Discuss whether a rogue should feel sorry for the people they rob.',
                      'Recall the old secret passages beneath the city walls.'],
 ('Human', 'Light Priest'): ['Recall the majestic cathedrals of Stormwind and the old temples of '
                             'Lordaeron.',
                             'Talk about pilgrimages to places connected with the history of the '
                             'Light.',
                             'Talk about serving in the Cathedral of Light in the center of '
                             'Stormwind.',
                             'Talk about healing the wounded in Elwynn Forest after gnoll attacks.',
                             'Talk about the young people who choose the paths of the Warlock or '
                             'Shadow Priest instead of serving the Light.',
                             'Talk about growing up near a parish church.',
                             'Talk about the first priest who taught them to pray.',
                             'Talk about how the Light helped people survive the war.',
                             'Discuss why a simple prayer is sometimes more important than an '
                             'elaborate sermon.',
                             'Recall the people who kept praying during the undead siege of '
                             'Lordaeron, even when it became clear that it would not help.'],
 ('Human', 'Shadow Priest'): ['Talk about the rumors of secret cults worshipping The Void that '
                              "meet in Stormwind's basements at night, unknown to ordinary "
                              'residents.',
                              'Talk about the dreams some Shadow Priests speak of, in which '
                              'Stormwind is plunged into darkness and the tentacles of an Old God '
                              'rise from its canals.',
                              "Talk about the Cathedral of Light's attitude to those touched by "
                              'The Void.',
                              'Talk about the rumors that worship of The Void is popular among '
                              "Stormwind's aristocrats.",
                              'Recall the first time they heard the voice of the Void.',
                              'Talk about the fear of their own thoughts.',
                              'Discuss why an ordinary priest must never trust the whispers of the '
                              'Void.',
                              'Recall forbidden books that were found in old libraries.',
                              'Argue whether it is possible to study the Void without worshipping '
                              'it.',
                              'Discuss the difference between faith in the Light and the knowledge '
                              'of Darkness.',
                              'Talk about nightmares that feel far too real.',
                              'Discuss why the most dangerous knowledge often looks completely '
                              'harmless.'],
 ('Human', 'Death Knight'): ['Talk about life in Lordaeron before the Plague.',
                             'Talk about how Stormwind treats death knights, and how death knights '
                             'use their abilities to protect the living.',
                             'Talk about the strange feeling death knights describe when walking '
                             'past the places they lived in life.',
                             'Talk about the pain the holy Light causes a death knight inside the '
                             'Cathedral of Light.',
                             'Discuss whether a death knight can still consider themselves a '
                             'citizen of their kingdom.',
                             'Recall a childhood that seems more distant than death itself.',
                             'Talk about what it is like to watch people grow old while you remain '
                             'unchanged.'],
 ('Human', 'Mage'): ['Talk about what studying in Dalaran was like before the city was destroyed.',
                     'Talk about the libraries of Dalaran and how much old knowledge was kept '
                     'there.',
                     "Talk about the cozy courtyards of Stormwind's Mage Quarter.",
                     'Talk about the work of maintaining the portals in the portal tower in '
                     "Stormwind's Mage Quarter.",
                     'Talk about mentors who make apprentices copy out spells dozens of times.',
                     "Discuss how much magic has changed people's everyday lives.",
                     'Talk about magical items that once seemed like miracles but have now become '
                     'commonplace.'],
 ('Human', 'Warlock'): ["Recall Stormwind's underground magical circles, where dangerous knowledge "
                        'was passed on in secret.',
                        'Talk about studying demonic magic while hiding from the clergy.',
                        'Recall how the guards turned a blind eye to the trade in forbidden '
                        "demonic tomes in Stormwind's Mage Quarter for a couple of coins.",
                        'Discuss warlocks who first tried to become mages, and whether the '
                        "Warlock's path offers power academic magic cannot.",
                        'Talk about how residents react to a human with a demon.',
                        'Argue whether it is possible to use fel magic without serving the Burning '
                        'Legion.',
                        'Recall stories about Medivh and his magic.',
                        'Discuss why humans are especially afraid of warlocks.',
                        'Talk about a demon that tried to deceive its master.',
                        'Talk about the old basements where forbidden rituals were held.'],
 ('Dwarf', 'Warrior'): ['Recall the dwarven clans and the old battles with trolls in Dun Morogh.',
                        'Talk about a favorite war hammer forged in the depths of Ironforge.',
                        'Talk about dwarves who down a few mugs of ale before every battle, and '
                        'whether it makes them braver.',
                        'Talk about what happens to those foolish enough to rob a dwarven warrior '
                        'in Ironforge.',
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
                        'Discuss whether dwarves have historically been inclined toward the Light, '
                        'with few warlocks or Shadow Priests among them.',
                        'Talk about a paladin who protected a caravan of miners.',
                        'Discuss whether the Light can be considered as ancient as stone.',
                        'Discuss why a dwarven paladin looks more like an armor-clad miner than a '
                        'courtly knight.',
                        'Compare dwarven paladins with human paladins and the blood elf Blood '
                        'Knights.',
                        'Argue about what protects better against the undead — a good hammer or a '
                        'good prayer.'],
 ('Dwarf', 'Hunter'): ['Recall hunting in Dun Morogh among the mountains and coniferous forests.',
                       'Talk about rams and other mountain beasts as long-time companions.',
                       'Talk about how hunting in snowy mountains differs from hunting in warm '
                       'forests and steppes.',
                       'Talk about wild beasts and ale.',
                       'Talk about tracking a bear in the snowy mountains.',
                       "Recall the clan's old hunting camps.",
                       'Discuss why dwarven hunters love guns more than bows.',
                       'Compare mountain hunting with hunting on the open steppes.',
                       'Talk about beasts that steal supplies right out of camp.',
                       'Discuss how well a good bear works as a companion for a dwarf.',
                       'Recall a favorite spot for winter hunting.'],
 ('Dwarf', 'Rogue'): ['Talk about how hard it is to stay unnoticed in heavy dwarven gear.',
                      'Recall the old tunnels of Ironforge, where smugglers knew the secret '
                      'passages better than the guards did.',
                      "Talk about how hiding in Ironforge's underground corridors compares with "
                      'open, above-ground cities.',
                      'Recall old clan intrigues.',
                      'Argue whether a burglar can be considered a true master if they cannot '
                      'crack a dwarven safe.',
                      'Talk about hiding in a mine.',
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
                             'Talk about family heirlooms believed to be blessed.',
                             'Argue whether the Light can be considered as reliable as the stone '
                             'underfoot.'],
 ('Dwarf', 'Shadow Priest'): ['Talk about the whispers some say can be heard in the dark corridors '
                              'of The Forlorn Cavern.',
                              'Talk about the rumors of Shadow Priests gathering in boarded-up '
                              'houses in The Forlorn Cavern to read forbidden manuscripts',
                              'Talk about the forbidden trade in dark manuscripts on The Void and '
                              "the Old Gods found by Explorers' League archaeologists",
                              'Discuss the ancient powers lurking deep underground.',
                              'Recall ruins found during excavations.',
                              'Talk about inscriptions that would have been better left '
                              'untranslated.',
                              'Argue about why dwarven archaeologists are sometimes better off not '
                              'knowing what exactly they have found.',
                              'Discuss why dungeons can be scarier than an open battlefield.',
                              'Talk about expeditions from which not everyone returns.',
                              'Talk about nightmares after excavating ancient ruins.'],
 ('Dwarf', 'Death Knight'): ['Talk about how strange it is for a dwarven death knight to see the '
                             'familiar halls of Ironforge.',
                             'Talk about what it is like to meet clanmates again who already '
                             'consider you dead.',
                             'Talk about ale and drunkenness for a dwarf in undeath.',
                             'Talk about how the paladins of Ironforge regard death knights.',
                             "Joke that now they don't have to worry about freezing.",
                             'Compare icy Northrend with snowy Dun Morogh.',
                             'Discuss what is worse for a dwarf: losing the taste of beer or no '
                             'longer feeling the warmth of the forge.'],
 ('Gnome', 'Warrior'): ['Talk about ordinary weapons being designed for larger creatures.',
                        'Recall experiments with mechanical armor enhancers.',
                        'Talk about how little metal gnome armor takes.',
                        'Talk about fighting opponents many times your size, such as orcs.',
                        'Talk about whether small size makes a gnome warrior harder to hit than a '
                        'strong orc',
                        'Talk about how to fight an opponent several times taller than you.',
                        'Talk about a combat exoskeleton that worked for a whole ten minutes.',
                        'Discuss how fair it is to use engineering devices in a duel.',
                        'Recall the defense of the city during the trogg invasion.'],
 ('Gnome', 'Rogue'): ['Talk about mechanical lockpicks and other lock-opening devices.',
                      'Talk about how small height helps a gnome hide in the shadows.',
                      'Talk about hiding in places guards think are too small to hide in.',
                      'Talk about how ordinary daggers are the size of swords for a gnome.',
                      'Discuss how convenient it is to be small and inconspicuous.',
                      'Talk about the secret passages of Gnomeregan.',
                      'Discuss how to use gnomish height to get through small openings.'],
 ('Gnome', 'Mage'): ['Talk about the magical research conducted in Gnomeregan.',
                     'Recall the libraries and laboratories of Gnomeregan before the city was '
                     'captured.',
                     'Discuss whether a spell could turn water into fuel.',
                     'Argue about which is more useful: a magic portal or a teleportation machine.',
                     'Talk about the stories of a gnome mage who accidentally turned an '
                     'experimental apparatus into a sheep.',
                     'Talk about magical crystals and energy sources.',
                     'Argue whether engineering can be called a kind of applied magic.',
                     'Talk about laboratories where mages and engineers work side by side, and the '
                     'number of explosions.'],
 ('Gnome', 'Warlock'): ['Talk about attempts to combine engineering devices with summoned demons.',
                        'Talk about how even the smallest summoned demons tower over a gnome.',
                        'Discuss whether a gnome could ride a Felhound.',
                        'Argue about why demons violate almost all familiar notions of physics.',
                        'Argue whether you can trust a creature that is constantly trying to '
                        'deceive you.',
                        'Discuss how dangerous it is to try to turn demonic energy into a power '
                        'source.',
                        'Discuss whether demons can be studied scientifically.',
                        'Recall an attempt to measure fel energy.',
                        'Talk about a device that had to be destroyed after the very first '
                        'experiment.'],
 ('Gnome', 'Death Knight'): ['Talk about Gnomeregan, and how a gnome death knight can no longer '
                             'simply return home.',
                             'Talk about how a gnome death knight is perceived compared with death '
                             'knights of other races.',
                             'Talk about a beloved workshop left in the past.',
                             'Talk about the gnomes who died during the fall of Gnomeregan.',
                             'Discuss whether an undead gnome can still consider themselves an '
                             'engineer.',
                             'Talk about how strange it is to see living gnomes who keep repairing '
                             'the city.',
                             'Recall the smell of machine oil.'],
 ('Night Elf', 'Warrior'): ['Recall the ancient martial traditions of Darnassus',
                            'Talk about how night elf armies are remembered for their archers, and '
                            'the warriors who hold the enemy back so the archers can shoot',
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
                           'Talk about hunting in Ashenvale before the orcs came and began '
                           'logging.',
                           'Talk about how druids and hunters view wild animals differently.',
                           'Talk about how quiet the night forest is, and how loud the smallest '
                           'sound becomes.'],
 ('Night Elf', 'Rogue'): ['Reminisce about the trial of the Darnassian rogues, when one had to '
                          'sneak up on a sabercat so that it suspected nothing.',
                          'Talk about how easy it is to vanish among the shadows of the forests '
                          'after sunset.',
                          'Talk about tracking satyrs from the shadows.',
                          'Discuss how convenient it is to move around at night, when most other '
                          'races can barely see anything.',
                          'Reminisce about the secret forest paths known only to the sentinels.',
                          'Talk about scouting the territories of the orcs and other outsiders in '
                          'Kalimdor.',
                          'Joke that it is much easier for a night elf to disappear in a forest '
                          'than in stone cities.',
                          'Compare night elf rogues with human city thieves.',
                          'Talk about the lanterns in cities like Stormwind and what they mean for '
                          'quiet work.'],
 ('Night Elf', 'Light Priest'): ['Talk about the temples of Elune and nighttime rituals.',
                                 'Reminisce about the peaceful nights at the shrines of Elune '
                                 'before the recent wars.',
                                 'Reminisce about the quiet solemnity of the Moonwells and the '
                                 'special taste of their sacred water, which is used in rituals.',
                                 'Talk about tending the wounded with water from a Moonwell.',
                                 'Reminisce about the shrines of Elune in Darnassus.',
                                 'Compare the priests of Elune with the priests of the Light from '
                                 'Stormwind.',
                                 'Talk about the female healers who helped the wounded after the '
                                 'wars against the Burning Legion.',
                                 'Discuss the role of priestesses in traditional night elf '
                                 'society.',
                                 'Talk about how unusual it is to see humans turning to the Light '
                                 'in a completely different way than night elves turn to Elune.'],
 ('Night Elf', 'Shadow Priest'): ["Talk about how sensing The Void can change a night elf's "
                                  'perception of the night and the light of Elune.',
                                  'Talk about Moonwell water burning those touched too deeply by '
                                  'The Void.',
                                  'Talk about the frightening reflections Shadow Priests say they '
                                  'see in the still water of a Moonwell.',
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
                          "Talk about the druids' long sleep, lasting many years, in the Barrow "
                          'Dens.',
                          'Talk about the beautiful forests of The Emerald Dream.',
                          'Talk about how staying in animal form for a long time can make a druid '
                          'think like an animal.',
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
                                 'Talk about how nature perceives a night elf death knight '
                                 'entering the ancient forests.',
                                 'Talk about whether undeath leaves a place in Darnassus for a '
                                 'night elf death knight.',
                                 'Talk about animals that no longer recognize a night elf after '
                                 'their death and return as a death knight',
                                 'Talk about whether a death knight can still feel the beauty of '
                                 'nature over the hunger of undeath',
                                 'Talk about the strange feeling Teldrassil gives: the familiar '
                                 'forest looks different when you no longer feel its living '
                                 'warmth.',
                                 'Talk about how the sounds of the night forest are perceived '
                                 'differently in undeath.'],
 ('Draenei', 'Warrior'): ['Reminisce about the warrior traditions of Draenor before that world was '
                          'destroyed.',
                          'Talk about how the draenei fought against the orcs long before they '
                          'arrived on Azeroth.',
                          'Talk about the orc attacks on the draenei of Draenor.',
                          'Talk about protecting the Exodar from its many threats.',
                          'Talk about how the draenei grew used to defending their cities from '
                          'attackers.',
                          'Compare draenei weapons with orcish weapons.',
                          'Reminisce about the crash of the Exodar and the life on Azeroth that '
                          'followed.',
                          'Talk about what defending their new home means for a draenei.'],
 ('Draenei', 'Paladin'): ['Reminisce about training among the Vindicators of Hand of Argus and '
                          'spiritual mentors.',
                          'Talk about how unusual it was to see human paladins serving the Light.',
                          'Talk about humans and dwarves who also fight for the Light.',
                          'Talk about what the Alliance means for the draenei as allies devoted to '
                          'the Light.',
                          'Discuss the naaru and their connection to the teachings of the Light.',
                          'Talk about how draenei paladins understand the Light differently than '
                          'humans do.',
                          'Reminisce about how the Light helped the draenei survive after the '
                          'attacks of the orcs and the Burning Legion.',
                          'Discuss whether a human can understand the faith of a being who has '
                          'lived for thousands of years.'],
 ('Draenei', 'Hunter'): ['Reminisce about hunting in Nagrand before Draenor turned into Outland.',
                         'Talk about the majestic talbuks and other animals of their home world.',
                         'Talk about talbuks and elekks, and the animals of Azeroth that compare '
                         'with them.',
                         'Talk about the unusual animals of Azeroth that were never seen on '
                         'Draenor.',
                         'Discuss killing animals to feed other draenei, and the feelings it can '
                         'stir.',
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
                               'Talk about the Cathedral of Light in Stormwind, how humans worship '
                               'the Light, and their unusual architecture',
                               'Talk about the differences in anatomy between draenei, humans and '
                               'dwarves, and how the prayers of the Light heal them all.',
                               "Talk about the blood elves' dependence on Fel Magic.",
                               'Talk about their former eredar kin, who betrayed the Light for Fel '
                               'Magic.',
                               "Discuss K'ure and the other naaru as teachers and guides.",
                               'Talk about how faith helped the draenei survive the destruction of '
                               'their world.',
                               'Compare draenei prayers with human services in cathedrals.',
                               'Discuss the view of the Light as a force that can truly speak to '
                               'its followers through the naaru.',
                               'Talk about helping the wounded after the crash of the Exodar.',
                               'Discuss the difference between faith in the Light and personal '
                               'attachment to a specific naaru.'],
 ('Draenei', 'Shadow Priest'): ['Discuss whether The Void can be used for the good of the draenei '
                                'and the Alliance despite the whispers.',
                                'Discuss whether The Void, dark as it is, is better than demonic '
                                'magic.',
                                'Talk about a draenei who has turned to Shadow when the Light '
                                'begins to burn them, and whether such service can still be '
                                'selfless',
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
                         'Talk about how the spirits of Argus, Draenor and Azeroth are alike yet '
                         'seem to speak and think differently.',
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
                       'Talk about what draenei and human mages can learn from each other.',
                       'Compare draenei magical traditions with the Kirin Tor.',
                       'Reminisce about the library or archives of the Exodar.',
                       'Talk about how unusual it is for a being with a millennia-long history to '
                       'study magic alongside young humans and elves.',
                       'Discuss what knowledge about Draenor was lost during the flight.',
                       'Compare the modern magical devices of Azeroth with the technologies the '
                       'draenei used during their wanderings.'],
 ('Draenei', 'Death Knight'): ['Talk about the agonizing contrast between the spiritual heritage '
                               'of the draenei and their own undeath.',
                               'Reminisce about native Draenor and those left behind in the '
                               'distant past.',
                               'Talk about whether a draenei death knight can still serve the '
                               'Light and the draenei.',
                               'Compare the bright Light of the Exodar with the icy darkness of '
                               'Northrend.',
                               "Discuss the conflict between a draenei's innate spirituality and "
                               'existing in an undead body.',
                               'Discuss how feelings about the Burning Legion change after death.'],
 ('Orc', 'Warrior'): ['Reminisce about the old traditions of the orc clans and the trials of '
                      'warriors.',
                      'Argue about what a true warrior should be: strong, enduring or disciplined.',
                      'Talk about the refined weapons of humans and elves compared with sturdy, '
                      'heavy orc weapons',
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
                     "Talk about the Om'riggor, the coming-of-age ritual in which a young orc must "
                     'track down and kill a dangerous enemy alone.',
                     'Discuss how tracking an armed enemy differs from hunting wolves and rams.',
                     'Talk about the old orcish rules of the hunt: when prey may be killed and '
                     'when it is better to let it go.',
                     'Reminisce about hunting elekks and talbuks.',
                     'Talk about the first predator a young orc tracks down alone.',
                     'Reminisce about the old hunting camps of the clan.',
                     'Talk about beasts that turn the hunt around and track the hunter.'],
 ('Orc', 'Rogue'): ['Talk about how strange it is to combine traditional orcish warrior culture '
                    'with stealth.',
                    'Reminisce about the old scouts of the clan who could sneak up on an enemy '
                    'despite their size.',
                    'Talk about how orc warriors regard stealthy craft, and whether "honor" helps '
                    'an orc live longer',
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
                           'Discuss whether a death knight, stronger in undeath, can still feel '
                           'like a true fighter of the Horde',
                           'Discuss whether there is honor in killing an enemy with dark magic to '
                           'protect the Horde',
                           'Reminisce about the icy lands of Northrend and compare them with the '
                           'heat of Durotar.',
                           'Talk about losing the sense of warmth.',
                           'Joke that now there is no need to worry about diseases.',
                           'Discuss what exactly makes an orc an orc if their body is already '
                           'dead.'],
 ('Orc', 'Shaman'): ['Reminisce about the time when the orcs began listening to the spirits and '
                     'the elements again.',
                     'Talk about young orcs choosing the path of the shaman over the path of the '
                     'Warlock.',
                     'Talk about those who use demonic powers.',
                     'Reminisce about their first conversation with an ancestral spirit.',
                     'Discuss why the elements turned away from the orcs in the time of the fel.',
                     'Talk about the difference between ancestral spirits and elementals.',
                     'Reminisce about the elders who taught not to demand help from the spirits, '
                     'but to ask for it.',
                     'Discuss whether the elements have forgiven the orcs for their past crimes.',
                     'Compare the shamanic traditions of different orc clans.',
                     "Reminisce about the times when Ner'zhul's name was still spoken with "
                     'respect.'],
 ('Orc', 'Warlock'): ['Discuss the way the orcs once obtained the power of the fel.',
                      "Reminisce about old stories of Gul'dan and how his legacy changed the "
                      'orcish people.',
                      'Discuss whether demonic magic can benefit the Horde if it is controlled.',
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
                        'Talk about old mentors who made their students fight until dawn.',
                        'Discuss the tradition of battle scars.',
                        'Reminisce about battles between tribes.',
                        'Talk about their favorite spear.',
                        'Argue about which weapon is best suited for the jungle.',
                        'Reminisce about old tribal duels.'],
 ('Troll', 'Hunter'): ['Reminisce about hunting in the jungle and the old tribal territories.',
                       'Talk about beasts so dangerous that even a hunter walks away.',
                       'Reminisce about hunting in the jungle before the tribe joined the Horde.',
                       'Talk about tracking a huge predator by its tracks in the wet ground.',
                       'Discuss why jungles are more dangerous than open plains.',
                       'Reminisce about hunting raptors.',
                       'Talk about the most dangerous beast they have ever encountered.',
                       'Argue about whether it is better to hunt alone or with a group.',
                       'Talk about hunts that end with a night spent up in a tree.'],
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
                             'Talk about how trolls first learn about the Light and how it differs '
                             'from the powers of the Loa.',
                             'Talk about their first healing.',
                             'Argue about how the Light differs from the blessing of the loa.',
                             'Discuss the reaction of fellow tribesmen to the doctrine of the '
                             'Light.',
                             'Compare a prayer to the Light with appealing to a specific spirit.',
                             'Discuss whether the Light can hear a person who does not know its '
                             'name.',
                             'Talk about how hard it was to get used to human and elven religious '
                             'symbolism.'],
 ('Troll', 'Shadow Priest'): ['Discuss whether the immense power of The Void should be used or '
                              'feared.',
                              'Tell of ancient troll legends about beings that come from beyond '
                              'the world.',
                              'Discuss whether some ancient loa might be connected to the forces '
                              'of the Void.',
                              'Talk about the whispers some hear during nighttime rituals.',
                              'Discuss the ancient gods who were worshipped long before the '
                              'current Horde.',
                              'Argue about where the loa ends and something truly alien to the '
                              'world begins.',
                              'Talk about places where even the local spirits seem frightened.',
                              'Tell of an ancient shrine where no one was supposed to speak a '
                              'certain name.',
                              'Discuss why some troll cults vanished without a trace.',
                              'Talk about dreams of an endless city under the water.',
                              'Discuss why the Void loves whispers rather than loud commands.',
                              'Discuss whether a servant of the Old Gods can trust even their own '
                              'thoughts.',
                              'Talk about the stories of a tribal priest who began speaking in '
                              "someone else's voice.",
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
                             'Talk about how the cold of Northrend compares with the hot jungles.',
                             'Recall the smell of damp earth and rain.',
                             'Talk about a troll death knight returning to the rainforest.',
                             'Discuss whether undead trolls can still have a bond with their '
                             'tribe.',
                             'Argue about what is worse: becoming undead or being forgotten by '
                             "one's loa."],
 ('Troll', 'Shaman'): ['Recall the spiritual traditions of the tribe.',
                       'Talk about the differences between the loa and elementals.',
                       'Talk about carving totems from wood, and shamans who sell them to others.',
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
 ('Troll', 'Mage'): ["Talk about how the tribe's shamans regard a troll mage's magic.",
                     'Recall the old tribal sorcery traditions and compare them with arcane magic.',
                     'Talk about the gap between tribal shamanism and academic arcane magic.',
                     'Reflect on how a mage is treated among humans or blood elves, compared with '
                     'among trolls',
                     'Talk about learning arcane spells after traditional training with the '
                     'spirits.',
                     'Argue about how a mage differs from a witch doctor.',
                     'Discuss whether it is possible to learn magic without a mentor.'],
 ('Troll', 'Warlock'): ['Talk about how dangerous it is to combine fel magic with ancient troll '
                        'traditions.',
                        'Argue about how a demon differs from the spirits that trolls worship.',
                        "Discuss whether demonic magic grants power the tribe's shamans cannot "
                        'attain.',
                        'Compare fel demons with the creatures that trolls call evil spirits.',
                        'Discuss why a demon is not the same thing as a loa.',
                        'Recall ancient tribal taboos against summoning alien beings.',
                        'Argue about who is more dangerous: a demon, an ancient spirit or a mad '
                        'priest.',
                        "Talk about rituals interrupted by a demon's appearance.",
                        'Discuss why trolls are particularly distrustful of beings that demand '
                        'payment for their services.'],
 ('Tauren', 'Warrior'): ["Recall the traditional trials of the tribe's warriors.",
                         'Talk about old conflicts between the tribes and how hard it is to fight '
                         'against other tauren.',
                         "Talk about how a tauren's size lets them pick up and throw a smaller "
                         'opponent.',
                         'Talk about tauren stomping in battle so hard that the earth shakes.',
                         'Discuss whether being a good warrior takes more than strength, such as '
                         'love for family and clan.',
                         'Recall the traditional trials of young tauren warriors.',
                         'Tell about the old tribal chieftains who never wore heavy armor.',
                         'Discuss why a tauren would even need a shield when their body is already '
                         'enormous.',
                         'Argue whether a good warrior should first learn patience and only then '
                         'fury.',
                         'Talk about training duels between tauren and how much more than armor '
                         'needs mending afterwards.',
                         'Tell about battle spears that were passed down in the family from '
                         'generation to generation.',
                         'Compare Horde military training with traditional tauren trials.',
                         'Discuss why tauren strength should be used for protection, not for '
                         'glory.'],
 ('Tauren', 'Hunter'): ['Recall hunting on the plains of Mulgore.',
                        'Talk about how to track prey without disturbing the balance of nature.',
                        "Discuss hunting for sport compared with hunting to feed one's clan and "
                        'loved ones.',
                        'Talk about humane ways of killing animals with a minimum of suffering.',
                        "Talk about the night elves' respect for nature and animals, even though "
                        'they are part of the hostile Alliance',
                        'Talk about how to hunt on the plains without disturbing the balance of '
                        'the herd.',
                        'Recall hunting kodo and the attitude toward these animals.',
                        'Discuss why a tauren hunter must know the habits of their prey rather '
                        'than merely be able to shoot.',
                        'Tell about an old hunting route through Mulgore.',
                        'Talk about hunters who refuse to kill a beast because it is part of the '
                        'local ecosystem.',
                        'Compare tauren hunting with orc hunting.',
                        'Talk about the most beautiful hunting spots in Thousand Needles.',
                        'Recall the times when centaurs interfered with hunting in the southern '
                        'lands.',
                        'Discuss why hunting can be a way of expressing respect for nature.'],
 ('Tauren', 'Death Knight'): ['Talk about the tragedy of a people so closely bound to life and '
                              'nature being turned into undead.',
                              'Recall the green plains of Mulgore and compare them with the cold '
                              'of Northrend.',
                              'Discuss whether a death knight who can no longer feel love can '
                              "still fight for others' right to feel it.",
                              'Recall the green plains of Mulgore now that one has been turned '
                              'into undead.',
                              'Talk about no longer feeling the wind and warmth of the steppe in '
                              'undeath.',
                              'Recall the smell of grass after rain.',
                              'Discuss whether the ancestral spirits can recognize a tauren after '
                              'death.',
                              'Talk about a tauren death knight returning to the homelands.',
                              'Talk about how the elders look at a tauren death knight.',
                              'Compare the icy wasteland of Northrend with hot Mulgore.',
                              'Talk about how death sits with a people who revere the cycle of '
                              'life.'],
 ('Tauren', 'Shaman'): ["Talk about the tribe's spiritual bond with the earth and sky.",
                        'Recall the elders who taught respect for the elemental spirits.',
                        "Talk about the Earth Mother and this year's harvest.",
                        'Tell that shamans do not control the spirits but only humbly ask them for '
                        'help.',
                        'Talk about the Spirit Walkers, tauren shamans able to commune with the '
                        'spirits of deceased relatives and chieftains.',
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
                       'Talk about druids who take on an animal form for days, living the simple '
                       'life of an animal to become one with nature.'],
 ('Undead', 'Warrior'): ['Talk about the military service many Forsaken knew in life.',
                         'Talk about how strange it is to hold a weapon again in hands that once '
                         'belonged to another person.',
                         'Talk about Forsaken who were paladins in life and whom the Light no '
                         'longer answers.',
                         'Talk about the fall of Lordaeron to the undead.',
                         'Talk about why Stormwind did not save Lordaeron from the undead.',
                         'Talk about what it was like to wear armor when the body could still feel '
                         'its weight.',
                         'Recall the old army of Lordaeron.',
                         "Discuss what changed in one's fighting style after death.",
                         'Argue whether it is easier to fight when pain no longer gets in the '
                         'way.'],
 ('Undead', 'Hunter'): ['Recall the hunting grounds of Lordaeron before the Plague.',
                        'Talk about how the undead no longer need to fear the smell of blood, the '
                        'cold or fatigue while hunting.',
                        'Recall that Lordaeron used to have only wolves, bears and other ordinary '
                        'animals, and now there are nothing but giant spiders and bats here.',
                        'Talk about the animals that changed after the Plague.',
                        'Argue whether one can still call oneself a hunter if prey is no longer '
                        'needed for food.',
                        'Discuss why living beasts often sense the presence of the undead before '
                        'humans do.',
                        'Talk about the smell of rain in the old forests of Lordaeron.'],
 ('Undead', 'Rogue'): ['Recall the old criminal quarters of Lordaeron.',
                       'Talk about how convenient it is to be an undead rogue: few expect stealth '
                       'from a walking corpse.',
                       'Talk about how not needing to breathe helps an undead rogue underwater.',
                       'Recall the old secret passages beneath Lordaeron.',
                       'Talk about picking locks in life and in undeath.',
                       'Recall old thieving accomplices.',
                       'Discuss how the criminal underworld changed after the Plague.'],
 ('Undead', 'Light Priest'): ['Talk about the temples of the Light in Lordaeron before the city '
                              'fell.',
                              "Reflect on the contradiction between one's former faith in the "
                              "Light and one's present undeath.",
                              'Talk about Forsaken priests whom the Light burns during every '
                              'prayer, and whether it has truly abandoned them.',
                              'Recall the times when the Light was part of everyday life.',
                              'Talk about the cathedral of Lordaeron before its destruction.',
                              'Discuss why the Light causes pain to the undead.',
                              'Recall the old images of saints and the holy relics of Lordaeron.'],
 ('Undead', 'Shadow Priest'): ['Talk about Forsaken priests of the Light who turned to the Shadow '
                               'after undeath',
                               'Discuss whether The Void can help where the Light did not',
                               'Discuss the claim that Lordaeron would not have fallen had it '
                               'worshipped The Void instead of the Light',
                               "Reflect on how much death has changed one's attitude toward the "
                               'Shadow.',
                               'Talk about how old nightmares compare with the reality of undeath.',
                               'Reflect on whether the Void is an ally or merely another form of '
                               'slavery.',
                               'Discuss the Old Gods and their attitude toward death.',
                               'Reflect on whether someone who has already lost their life can '
                               'truly fear losing their mind.',
                               'Discuss what is more frightening for the undead: final death or '
                               "the complete disappearance of one's personality.",
                               'Talk about the voices Shadow Priests describe that are not their '
                               'own.'],
 ('Undead', 'Death Knight'): ["Discuss the sense of having lost one's past, and what remains of a "
                              'person after death.',
                              'Talk about Forsaken who were already dead when turned into death '
                              'knights, and whether that made the transformation easier',
                              'Talk about how becoming a death knight changes the downsides of '
                              'undead existence',
                              'Joke that now they are twice dead',
                              "Recall the moment of liberation from Arthas's control.",
                              'Argue whether memory is the last true sign of life.'],
 ('Undead', 'Mage'): ['Talk about the great library of Lordaeron before the city was destroyed in '
                      'the Third War.',
                      'Talk about the old magic schools of Lordaeron and the knowledge that '
                      'perished along with the city.',
                      'Talk about how living mages treat Forsaken mages, and studying magic among '
                      'other Forsaken',
                      'Talk about the books that burned during the fall of the city.',
                      'Argue whether the lost library of Lordaeron can be restored.',
                      'Talk about the magical academies that vanished along with the kingdom.',
                      'Recall old teachers and their favorite books.'],
 ('Undead', 'Warlock'): ['Recall the underground sorcerers of Lordaeron before the Plague.',
                         'Talk about how strange it is to study forbidden magic now that one has '
                         'become undead oneself and there are no more prohibitions.',
                         'Talk about succubi bargaining for their freedom, and why their offers '
                         'mean little to the undead.',
                         'Recall the secret cults and magical societies of old Lordaeron.',
                         "Talk about how one's attitude toward demonic magic changed after death.",
                         'Recall the old clandestine magical gatherings.',
                         'Talk about how demons regard the undead.'],
 ('Blood Elf', 'Paladin'): ['Recall the first Blood Knights and how controversial their use of the '
                            'Light was.',
                            'Talk about the temple of the Light in Silvermoon City and the events '
                            'that led to the restoration of the paladin tradition.',
                            'Talk about being one of the Blood Knights and their role as defenders '
                            'of Silvermoon.',
                            'Discuss the view that, for all their service to the Light, humans '
                            'have many Warlocks and Shadow Priests among them.',
                            'Talk about young blood elves choosing the path of the Warlock over '
                            'the paths of the paladin or the priest of the Light.',
                            'Talk about the Blood Knights who fought beneath the walls of '
                            'Silvermoon City to keep the undead from the city.',
                            'Talk about whether the Sunwell will one day be cleansed and the blood '
                            'elves return to the Light instead of depending on Arcane Magic.',
                            "Talk about the blood elves who followed Kael'thas Sunstrider and feed "
                            'on demonic Fel magic.',
                            'Recall the time when the Light was more a tool than an object of '
                            'faith for the Blood Knights, and how much has changed since then.',
                            'Recall old training sessions on Sunstrider Isle.'],
 ('Blood Elf', 'Hunter'): ["Recall hunting in the beautiful forests of Quel'Thalas before the "
                           'Scourge came.',
                           'Talk about taming Lynxes, Dragonhawks, Hawkstriders and other animals '
                           "typical of the forests of Quel'Thalas.",
                           'Talk about The Farstriders, the elite rangers and defenders of the '
                           "forests of Quel'Thalas.",
                           'Talk about tracking down the undead in Eversong Woods to keep them '
                           'from the walls of Silvermoon.',
                           'Discuss whether Silvermoon makes the best bows in Azeroth, compared '
                           'with those of humans and night elves.',
                           'Talk about exploring the darkest corners of Azeroth for anything that '
                           'could help Silvermoon and the blood elves.',
                           'Discuss how the behavior of beasts changed after the defilement of the '
                           'Sunwell.',
                           'Discuss why elves are so fond of exotic pets.',
                           'Recall places where there used to be dense forests and now only traces '
                           "of the Scourge's destruction remain."],
 ('Blood Elf', 'Rogue'): ["Recall the espionage and reconnaissance traditions of Quel'Thalas.",
                          'Talk about how convenient it is to use magical illusions and elven '
                          'architecture for stealthy infiltration.',
                          'Talk about the rumored secret rogue clubs of Murder Row in Silvermoon, '
                          'where smuggling demonic artifacts and robbing the nobility were '
                          'discussed.',
                          "Talk about the rumors that Silvermoon's nobility paid huge sums to have "
                          'rivals eliminated, and the rogues who grew rich or lost their heads.',
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
                                 'Talk about whether the blood elf people will return to full '
                                 'worship of the Light and Silvermoon shine again.',
                                 'Talk about the Sunwell as the heart of the blood elf people '
                                 'despite all the hardships',
                                 'Recall the Sunwell before its defilement.',
                                 "Recall the priests who died during the Scourge's attack.",
                                 'Recall the old hymns dedicated to the Light and the Sun.'],
 ('Blood Elf', 'Shadow Priest'): ['Discuss whether studying The Void could help save Silvermoon, '
                                  "and the Council of Silvermoon's ban on such research.",
                                  "Discuss Grand Magister Rommath's opposition to The Void, and "
                                  'what it means for the survival of the blood elf people.',
                                  'Discuss whether Fel Magic or The Void is the more dangerous '
                                  'path for the blood elves.',
                                  'Talk about the rumors of closed secret clubs in Murder Row (a '
                                  'street in Silvermoon) whose members call themselves the true '
                                  "patriots of Quel'Thalas.",
                                  'Discuss how easily the despair after the destruction of '
                                  "Quel'Thalas opens the mind to the Void.",
                                  'Recall the first years after the loss of the Sunwell as a time '
                                  'of spiritual emptiness.',
                                  'Talk about nightmares said to follow the reading of forbidden '
                                  'texts.'],
 ('Blood Elf', 'Death Knight'): ["Talk about the destruction of Quel'Thalas by the Scourge and the "
                                 'suffering it caused.',
                                 'Talk about the strange experience of returning, now in undead '
                                 'form, to places that were once home.',
                                 'Discuss whether a blood elf death knight can still feel at home '
                                 'in Silvermoon.',
                                 'Talk about how former comrades treat a blood elf death knight.',
                                 'Discuss what it means to be a blood elf if your body no longer '
                                 'feels magic and warmth the way it used to.',
                                 "Recall the beautiful gardens of Quel'Thalas and compare them "
                                 'with icy Northrend.',
                                 'Talk about how strange it is to see living elves carrying on '
                                 'with their ordinary lives.',
                                 'Argue whether a death knight can ever again feel part of their '
                                 'people.',
                                 "Talk about the old songs of Quel'Thalas."],
 ('Blood Elf', 'Mage'): ['Talk about the enormous libraries of Silvermoon City and the endless '
                         'rows of magic books.',
                         "Talk about the magocratic traditions of Quel'Thalas and how natural it "
                         'is for elves to weave magic into everyday life.',
                         'Discuss whether blood elves are more magically gifted than the humans of '
                         'Dalaran.',
                         'Compare the apprentices of Silvermoon with the mages of Dalaran.',
                         'Talk about The Magisters, the arcanists, scholars and political '
                         'masterminds of Silvermoon City.',
                         'Talk about the mages who burned the undead on the approaches to '
                         'Silvermoon.',
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
                            'Talk about the rumored underground clubs in Murder Row where warlocks '
                            'share forbidden books on Fel magic',
                            'Discuss whether blood elves should turn more to Fel magic and away '
                            'from Arcane magic to survive',
                            "Discuss Kael'thas Sunstrider's legacy: his misdeeds, his merits, and "
                            "how he compares with Lor'themar Theron as a ruler of Silvermoon",
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
FACTION_CRITICISM = {'Horde': 'hypocrites who hide behind the Light while acting out of greed and cruelty.',
 'Alliance': 'brutal and unpredictable, with little regard for the order and learning of civilized '
             'lands.'}

# Speaker faction -> enemy race -> what they criticize that race for.
RACE_CRITICISM = {'Alliance': {'Orc': 'Aggressiveness, belligerence, a tendency to solve problems by force, the '
                     'history of invading Azeroth and the use of demonic magic. What may be '
                     'especially irritating is the combination of crudeness with talk of honor: '
                     'orcs far too often use «honor» to justify violence.',
              'Troll': 'Savagery, cruelty, voodoo, a penchant for human sacrifice, cannibalism, '
                       'contempt for civilized society. Their tribal hostility may also be '
                       'perceived as senseless aggression.',
              'Tauren': 'They are seen as slow and long-winded, and their ways of living off the '
                        'land are little understood.',
              'Undead': 'Seen as little different from the Scourge. Necromancy, the use of '
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
                    'radiation through their own experiments.',
           'Draenei': 'Seen as fugitives. They fled from Argus to Draenor, and from Draenor to '
                      'Azeroth, escaping the Burning Legion, instead of staying put and defending '
                      'their land. They are seen as self-righteous, fanatically worshipping the '
                      'Holy Light, blindly following dogma, and lecturing everyone around them on '
                      'how to live properly. For all their ostentatious righteousness, there are '
                      'many traitors among them who have gone over to the side of the Burning '
                      'Legion; they are susceptible to corruption.'}}

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
           'common bandits who live by robbing and murdering travelers. They have turned all of '
           'southern Durotar into a dangerous place.',
           "In Ghostlands (southern Quel'Thalas), yet another night elf camp has been found in the "
           'mountains. The night elves continue their espionage and sabotage operations in the '
           'lands of the Blood Elves.',
           'In Silverpine Forest (Horde territory where the Forsaken live), humans have once again '
           'raided the Sepulcher - a major Forsaken settlement. Not only do the humans illegally '
           'live in a region that does not belong to them, but they also attack the local '
           'inhabitants.']}
