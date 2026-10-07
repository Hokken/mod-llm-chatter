"""Rumor sources for guild and General chat, gated by the listening player."""

EXPANSION_RUMORS = {'Outland': {'name': 'Outland',
             'min_level': 57,
             'max_level': 61,
             'facts': ['Beyond the Dark Portal lies a whole world. Once it was green and '
                       'beautiful, but now only wastelands are left of it',
                       'Those who return from Outland tell of floating islands, giant mushrooms '
                       'and forests where the very ground glows',
                       'The sky there is shattered, as if the world itself had been torn in half',
                       'Beyond the Portal there still live orcs who never drank the demon blood',
                       'In Outland you can find places where the land literally hangs in the void',
                       'Someone came back from there with crystals that glow even at night. '
                       'Alchemists are willing to pay a fortune for just one such crystal',
                       'There is a city there where members of almost all the peoples of Azeroth '
                       'live. They say even former enemies can sit peacefully at the same table '
                       'there',
                       'Dragons still live in Outland that remember Draenor before it was '
                       'destroyed',
                       'They say Illidan really is alive. And he has built himself an entire '
                       'fortress among the ruins of that world',
                       'Demon armies are pouring out of the Dark Portal, and they must be stopped '
                       'before they flood Azeroth. But to do that, you have to step through the '
                       'Dark Portal yourself',
                       'There are orcs serving the Burning Legion who look as if Hell itself had '
                       'burned them out from the inside',
                       'If you want to know what happened to the orcs after the First War, you '
                       'should look beyond the Portal',
                       'The marshes there are swarming with naga. They say they have dammed entire '
                       'rivers and are sucking the water out of the ground',
                       'One traveler said he saw a mushroom the size of a tower in the marshes. He '
                       'swore that entire settlements lived inside it',
                       'In Nagrand, beyond the Dark Portal, there still live those who remember '
                       'old Draenor. Perhaps they will tell you what this world was like before '
                       'the war',
                       'In Outland there is a place where even the sky is no longer real. The land '
                       'there hangs in the void, and elves are building huge machines to pump the '
                       'energy out of the world itself',
                       'They say the mountains there are so saturated with fel that even dragons '
                       'avoid them',
                       'If the stories are true, in the mountains of Outland there is a temple '
                       'that belongs to Illidan himself',
                       'They say that in Shattrath there is a prophet who has seen the future of '
                       'all Azeroth. But no one knows what exactly he saw there'],
             'required_tier': 8},
 'Northrend': {'name': 'Northrend',
               'min_level': 67,
               'max_level': 71,
               'facts': ['In the north there is an entire continent buried under ice',
                         'It is so cold there that a person can freeze to death in a matter of '
                         'minutes',
                         "They say the dead in the north don't stay dead",
                         'In the north there is an undead army commanded by a king who sits on a '
                         'throne of ice',
                         'Some say the Lich King sees everything that happens in Northrend',
                         'Giants live there who consider themselves descendants of the gods',
                         'In the northern mountains stand ancient structures built long before '
                         'humans appeared',
                         'They say dragons still live in Northrend that are older than most of the '
                         'kingdoms of Azeroth',
                         'In the north they have found an entire city that belongs to mages and '
                         'can fly',
                         'If you want to know what became of Arthas, go north. They say he is no '
                         'longer human there',
                         'They say that in the north entire cities belong to the dead',
                         'There are far more dead there than living',
                         'They say that in the middle of the icy desert stands a fortress so huge '
                         'that its walls can be seen from many miles away',
                         'At the center of Northrend stands an ice fortress. There sits the one '
                         'they call the Lich King',
                         "Paladins are going there in whole armies. Most of them don't come back",
                         'They say there is a temple in Northrend where all the great dragons of '
                         'Azeroth gather',
                         'In the north, the blue dragons have declared war on mortal mages. If you '
                         "wield magic, I wouldn't go there",
                         'There are things that have lived in Northrend longer than our kingdoms '
                         'have existed. And some of them can talk',
                         'In the far north there are fjords where giants live. They say they carve '
                         'faces for themselves out of wood and worship ancient gods',
                         'They say that in the icy wastes there is a place where dragons gather '
                         'around a huge temple',
                         'If you want to see the dragon graveyard, go to Dragonblight. They say '
                         'thousands of their ancestors rest there',
                         'In the north there is a troll tribe that has started sacrificing its own '
                         'gods to defeat the undead',
                         'Trolls killing their own gods? Then something very bad must be going on '
                         'there',
                         'In the middle of icy Northrend there is a place where, for some reason, '
                         'winter never comes',
                         'Hunters tell of a valley where beasts live that are found nowhere else',
                         'Dwarves have found a city in the north built not by humans, and not even '
                         'by elves. It was created by beings who may have been here long before '
                         'Azeroth itself',
                         'They say that in Icecrown the snow never melts because too many dead lie '
                         'beneath it'],
               'required_tier': 13}}

CAVERNS_OF_TIME_INTRO = 'Deep in the Tanaris desert lies a mysterious place, the Caverns of Time, which belongs to the bronze dragonflight. There one can travel into the past to witness the events of ancient times in person.'

DUNGEON_RUMORS = [{'name': 'Ragefire Chasm',
  'min_level': 10,
  'max_level': 21,
  'expansion': 'classic',
  'text': 'in a cave right beneath Orgrimmar, cultists are summoning demons. If the speaker '
          'belongs to the Alliance, condemn the Horde for having a nest of cultists right in their '
          'capital while being unable to do anything about it.',
  'caverns_of_time': False,
  'achievements': [629],
  'required_tier': 0},
 {'name': 'Wailing Caverns',
  'min_level': 12,
  'max_level': 25,
  'expansion': 'classic',
  'text': 'beneath the arid lands of The Barrens lies a vast network of caves filled with ancient '
          'creatures and plants. The druid Naralex is trying to restore the fertility of the '
          'Barrens, but his nightmarish magic has turned the caverns and his followers into '
          'something dangerous and deranged.',
  'caverns_of_time': False,
  'achievements': [630],
  'required_tier': 0},
 {'name': 'The Deadmines',
  'min_level': 12,
  'max_level': 25,
  'expansion': 'classic',
  'text': 'in a mine in Westfall, the Defias gang of bandits and pirates is preparing for war '
          'against everyone, because they believe the Alliance wronged them and did not pay for '
          'their labor in building Stormwind. If the speaker belongs to the Horde, mock the '
          'Alliance for not paying its own workers and creating new enemies.',
  'caverns_of_time': False,
  'achievements': [628],
  'required_tier': 0},
 {'name': 'Shadowfang Keep',
  'min_level': 13,
  'max_level': 26,
  'expansion': 'classic',
  'text': 'in Silverpine Forest, the mad mage Arugal, together with his half-man, half-wolf '
          'creatures (worgens), has seized a castle and is conducting his experiments there.',
  'caverns_of_time': False,
  'achievements': [631],
  'required_tier': 0},
 {'name': 'The Stockade',
  'min_level': 17,
  'max_level': 30,
  'expansion': 'classic',
  'text': 'in Stormwind a prison riot broke out and the prisoners killed all the guards. If the '
          'speaker belongs to the Horde, mock the Alliance for being unable to cope with its own '
          'prisoners.',
  'caverns_of_time': False,
  'achievements': [633],
  'required_tier': 0},
 {'name': 'Blackfathom Deeps',
  'min_level': 16,
  'max_level': 29,
  'expansion': 'classic',
  'text': 'on Zoram Strand (in the western part of Ashenvale), in a sunken former temple of Elune, '
          'Twilight’s Hammer cultists perform dark rituals and worship the naga.',
  'caverns_of_time': False,
  'achievements': [632],
  'required_tier': 0},
 {'name': 'Scarlet Monastery',
  'min_level': 24,
  'max_level': 45,
  'expansion': 'classic',
  'text': 'in Tirisfal Glades, the Scarlet Crusade, an organization of cruel fanatics, engages in '
          'torture and abductions of people. Before the Scourge plague ravaged Lordaeron, the '
          'complex in Tirisfal Glades served as a proud center for learning, enlightenment, and '
          'training for figures like Alexandros Mograine. Following the Third War and the '
          'fracturing of the Knights of the Silver Hand, the remaining zealots formed the Scarlet '
          'Crusade. They reclaimed the old monastery from lingering undead, renaming it the '
          'Scarlet Monastery. Consumed by absolute zealotry, the Scarlet Crusade came to believe '
          'that every outsider—regardless of race or faction—was infected or a carrier of the '
          'undead plague, leading them to slaughter the innocent and the non-human. If the speaker '
          'belongs to the Alliance, condemn the Horde for allying with the cruel undead Forsaken, '
          'who are one of the main reasons why the Scarlet Crusade continues to exist and attract '
          'new members. Members of the Alliance believe that through its actions the Horde keeps '
          'creating more and more organizations of fanatics and madmen.',
  'caverns_of_time': False,
  'achievements': [637],
  'required_tier': 0},
 {'name': 'Gnomeregan',
  'min_level': 20,
  'max_level': 33,
  'expansion': 'classic',
  'text': 'in Dun Morogh, the old city of the gnomes is now contaminated with radiation and '
          'inhabited by strange mutated creatures. The city itself is a marvel of engineering and '
          'is one big, complex mechanism. If the speaker belongs to the Alliance, express hope '
          'that the gnomes will get their city back. If the speaker belongs to the Horde, condemn '
          'the Alliance and the gnomes because their thoughtless, dangerous experiments lead to '
          'the deaths of thousands and the contamination of large areas of land.',
  'caverns_of_time': False,
  'achievements': [634],
  'required_tier': 0},
 {'name': 'Razorfen Kraul',
  'min_level': 19,
  'max_level': 32,
  'expansion': 'classic',
  'text': 'in the southern part of The Barrens lies a vast labyrinth made of the roots of an '
          'ancient thornbush. It has been seized by a quilboar tribe that worships the demigod '
          'Agamaggan, and their leaders are trying to use his power to restore their people. These '
          'Quilboar are no longer scattered tribes and are now a dangerous and organized force.',
  'caverns_of_time': False,
  'achievements': [635],
  'required_tier': 0},
 {'name': 'Razorfen Downs',
  'min_level': 29,
  'max_level': 42,
  'expansion': 'classic',
  'text': 'deep among the Razorfen thickets in The Barrens lies an ancient quilboar burial ground, '
          'which became a haven for the undead after the death of their chieftain. Necromancer '
          'Amnennar the Coldbringer is using the dead quilboar to create a new army.',
  'caverns_of_time': False,
  'achievements': [636],
  'required_tier': 0},
 {'name': 'Uldaman',
  'min_level': 32,
  'max_level': 45,
  'expansion': 'classic',
  'text': 'in the Badlands lies an ancient, buried Titan vault. Dark Iron dwarves later invaded '
          'the winding tunnels, hoping to claim the ancient relics and secrets for their fiery '
          'lord, Ragnaros.',
  'caverns_of_time': False,
  'achievements': [638],
  'required_tier': 0},
 {'name': "Zul'Farrak",
  'min_level': 38,
  'max_level': 51,
  'expansion': 'classic',
  'text': "in the Tanaris desert lies an ancient, sun-blasted Zul'Farrak troll city. It was once "
          'part of the Gurubashi Empire, but now it belongs to the Farraki tribe - a tribe of sand '
          'trolls that are very aggressive and prone to cannibalism and kidnapping people.',
  'caverns_of_time': False,
  'achievements': [639],
  'required_tier': 0},
 {'name': 'Maraudon',
  'min_level': 36,
  'max_level': 53,
  'expansion': 'classic',
  'text': 'in Desolace lies a vast sacred cave that was the birthplace of the centaur race. Now '
          'Princess Theradras dwells there - a huge earth elemental who drains the life from all '
          'the surrounding lands and has turned Desolace into a lifeless wasteland.',
  'caverns_of_time': False,
  'achievements': [640],
  'required_tier': 0},
 {'name': "Sunken Temple of Atal'Hakkar",
  'min_level': 42,
  'max_level': 55,
  'expansion': 'classic',
  'text': "in the Swamp of Sorrows lies an ancient sunken temple belonging to the cruel Atal'ai "
          'trolls. There, fanatical troll priests are trying to summon the Blood God, Hakkar the '
          'Soulflayer.',
  'caverns_of_time': False,
  'achievements': [641],
  'required_tier': 0},
 {'name': 'Blackrock Depths',
  'min_level': 44,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'deep inside Blackrock Mountain lies a vast underground city of the Dark Iron dwarves. '
          'It is ruled by Emperor Dagran Thaurissan, who, together with his subjects, worships '
          'Ragnaros and is trying to restore the might of his clan.',
  'caverns_of_time': False,
  'achievements': [642],
  'required_tier': 0},
 {'name': 'Lower Blackrock Spire',
  'min_level': 52,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'in the lower part of Blackrock Mountain lies a fortress of the clan of the Blackrock '
          'Orcs, seized by orcs and ogres under the command of General Drakkisath. They are using '
          'the fortress as a base to prepare a new war against Azeroth.',
  'caverns_of_time': False,
  'achievements': [643],
  'required_tier': 0},
 {'name': 'Upper Blackrock Spire',
  'min_level': 53,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'the upper halls of Blackrock Spire are controlled by Rend Blackhand, the '
          'self-proclaimed warchief of the orcs of the Dark Horde. He is trying to unite orcs, '
          'ogres and dragons under his command and restore the Horde to its former glory.',
  'caverns_of_time': False,
  'achievements': [1307],
  'required_tier': 0},
 {'name': 'Dire Maul',
  'min_level': 50,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'deep in Feralas lie the ruins of an ancient night elf city, turned by time into a vast '
          'labyrinth. Now parts of it have been seized by ogres, demons, satyrs and Prince '
          "Tortheldrin, who uses the city's magic to sustain his immortal life.",
  'caverns_of_time': False,
  'achievements': [644],
  'required_tier': 0},
 {'name': 'Stratholme',
  'min_level': 52,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'it was once one of the largest and richest cities of Lordaeron, but after the plague '
          'spread, Arthas slaughtered its inhabitants to keep them from turning into undead. Now '
          'the city is divided between the living followers of the Scarlet Crusade and the undead '
          'under the rule of Baron Rivendare.',
  'caverns_of_time': False,
  'achievements': [646],
  'required_tier': 0},
 {'name': 'Scholomance',
  'min_level': 52,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'on the island of Caer Darrow lies a former school of magic, turned by the necromancer '
          "Kel'Thuzad into an academy of the dark arts. Now its corridors are filled with undead, "
          'and its students study necromancy and create new servants of the Scourge.',
  'caverns_of_time': False,
  'achievements': [645],
  'required_tier': 0},
 {'name': 'Hellfire Ramparts',
  'min_level': 58,
  'max_level': 67,
  'expansion': 'tbc',
  'text': 'inside the ruined Hellfire Citadel lies a fortress of the Fel Horde orcs. Under the '
          'leadership of Nazgrel and demonic forces, the orcs are preparing a new war against '
          'those who try to pass through the Dark Portal.',
  'caverns_of_time': False,
  'achievements': [647, 667],
  'required_tier': 8},
 {'name': 'The Blood Furnace',
  'min_level': 58,
  'max_level': 68,
  'expansion': 'tbc',
  'text': 'deep beneath Hellfire Citadel lies a huge forge where demons and Fel Orcs turn '
          "prisoners into crazed warriors. The main power of this place is Keli'dan the Breaker, "
          'who serves the Burning Legion.',
  'caverns_of_time': False,
  'achievements': [648, 668],
  'required_tier': 8},
 {'name': 'The Slave Pens',
  'min_level': 58,
  'max_level': 69,
  'expansion': 'tbc',
  'text': "beneath the marshes of Zangarmarsh, Lady Vashj's naga are pumping water out of the "
          'region, threatening to dry it out completely. In huge underground reservoirs they keep '
          'captured creatures and use them as slaves.',
  'caverns_of_time': False,
  'achievements': [649, 669],
  'required_tier': 8},
 {'name': 'The Steamvault',
  'min_level': 65,
  'max_level': 70,
  'expansion': 'tbc',
  'text': "deep beneath Zangarmarsh lies a gigantic complex of reservoirs that Lady Vashj's naga "
          'use to pump water out of the marshes. Inside are huge machines, elementals and '
          'creatures captured by the naga to keep the complex running.',
  'caverns_of_time': False,
  'achievements': [656, 677],
  'required_tier': 8},
 {'name': 'The Underbog',
  'min_level': 61,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'in the depths of Zangarmarsh lies a huge system of caves where the naga conduct '
          'experiments on the local flora and fauna. Under the influence of their activities, the '
          'nature of the marshes is becoming ever more dangerous and alien.',
  'caverns_of_time': False,
  'achievements': [650, 670],
  'required_tier': 8},
 {'name': 'Mana-Tombs',
  'min_level': 61,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'deep in Terokkar Forest lies an ancient necropolis belonging to the ethereals. They '
          'explore the ruins of Auchindoun and guard them against marauders and rival groups.',
  'caverns_of_time': False,
  'achievements': [651, 671],
  'required_tier': 8},
 {'name': 'Auchenai Crypts',
  'min_level': 62,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'in the depths of Auchindoun lies a sacred draenei tomb that has been seized by the mad '
          'Auchenai. Their spiritual leaders are trying to summon the dead and use necromancy to '
          'commune with the spirits of the fallen.',
  'caverns_of_time': False,
  'achievements': [666, 672],
  'required_tier': 8},
 {'name': 'Sethekk Halls',
  'min_level': 63,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'in one part of Auchindoun, Arakkoa who worship the ancient god Anzu have settled. Their '
          'leader, Talon King Ikiss, is trying to restore the might of his people with the help of '
          'ancient magic.',
  'caverns_of_time': False,
  'achievements': [653, 674],
  'required_tier': 8},
 {'name': 'Shadow Labyrinth',
  'min_level': 62,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'deep inside Auchindoun lies an ancient labyrinth seized by the Shadow Council and '
          'demons. It is led by Murmur, a mysterious being of pure sonic energy, capable of '
          'destroying all living things with a single scream.',
  'caverns_of_time': False,
  'achievements': [654, 675],
  'required_tier': 8},
 {'name': 'The Shattered Halls',
  'min_level': 65,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'in the upper part of Hellfire Citadel lies a huge fortress seized by Fel Orcs under the '
          'command of Warchief Kargath Bladefist. The orcs use it as a military base and turn '
          'prisoners into new warriors, while Kargath himself is trying to prove his loyalty to '
          'the demons of the Burning Legion.',
  'caverns_of_time': False,
  'achievements': [657, 678],
  'required_tier': 8},
 {'name': 'The Mechanar',
  'min_level': 65,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'inside Tempest Keep lies a huge magical complex where the naaru and their adversaries '
          'use advanced technology and the energy of Netherstorm. Its defenders, led by Pathaleon '
          'the Calculator, are trying to keep control over the ship.',
  'caverns_of_time': False,
  'achievements': [658, 679],
  'required_tier': 8},
 {'name': 'The Botanica',
  'min_level': 65,
  'max_level': 70,
  'expansion': 'tbc',
  'text': "in one of the wings of Tempest Keep, Prince Kael'thas is growing artificial flora using "
          'the energy of Netherstorm. High Botanist Freywinn, who runs the complex, creates '
          'dangerous plants and creatures for the needs of the blood elves.',
  'caverns_of_time': False,
  'achievements': [659, 680],
  'required_tier': 8},
 {'name': 'The Arcatraz',
  'min_level': 66,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'the prison inside Tempest Keep holds the most dangerous creatures of Outland, including '
          'demons and creatures of the Nether. After the wards were breached, the prisoners broke '
          'out, and now the complex is controlled by creatures capable of destroying Tempest Keep '
          'itself.',
  'caverns_of_time': False,
  'achievements': [660, 681],
  'required_tier': 8},
 {'name': "Magisters' Terrace",
  'min_level': 66,
  'max_level': 70,
  'expansion': 'tbc',
  'text': "on the Isle of Quel'Danas lies a luxurious blood elf fortress, seized by followers of "
          "Kael'thas. They are trying to use the magical energy of the Sunwell to prepare for his "
          'return and open the way for the forces of the Burning Legion.',
  'caverns_of_time': False,
  'achievements': [661, 682],
  'required_tier': 12},
 {'name': 'Old Hillsbrad Foothills',
  'min_level': 62,
  'max_level': 70,
  'expansion': 'tbc',
  'text': "Thrall's escape from slavery.",
  'caverns_of_time': True,
  'achievements': [652, 673],
  'required_tier': 0},
 {'name': 'The Black Morass',
  'min_level': 66,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'Medivh opens the Dark Portal.',
  'caverns_of_time': True,
  'achievements': [655, 676],
  'required_tier': 0},
 {'name': 'Utgarde Keep',
  'min_level': 68,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'in a huge fortress in the Howling Fjord live the Vrykul, an ancient race of giants who '
          'serve Ymiron. They are preparing their warriors for war against the living and are '
          'trying to regain their former might.',
  'caverns_of_time': False,
  'achievements': [477, 489],
  'required_tier': 13},
 {'name': 'The Nexus',
  'min_level': 69,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'inside the magical Nexus in Borean Tundra, the dragons of the blue dragonflight under '
          'the command of Malygos are gathering the magical energy of Azeroth. Malygos has '
          'declared war on mortals, considering their reckless use of magic a threat to the world.',
  'caverns_of_time': False,
  'achievements': [478, 490],
  'required_tier': 13},
 {'name': 'Azjol-Nerub',
  'min_level': 70,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': "deep underground lies the ancient nerubian kingdom, destroyed by the Lich King's army. "
          "The remaining nerubians wage war against the Scourge, while their former king Anub'arak "
          'serves his new master.',
  'caverns_of_time': False,
  'achievements': [480, 491],
  'required_tier': 13},
 {'name': "Ahn'kahet: The Old Kingdom",
  'min_level': 71,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'beneath the ruins of Azjol-Nerub lie ancient cities inhabited by nerubians and '
          'mysterious creatures who worship the Old Gods. In the depths of the city dwells Herald '
          'Volazj, who serves the forces of the Old Gods.',
  'caverns_of_time': False,
  'achievements': [481, 492],
  'required_tier': 13},
 {'name': "Drak'Tharon Keep",
  'min_level': 71,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'an ancient troll fortress in Grizzly Hills has been seized by the Scourge. Drakuru, a '
          'former leader of the Drakkari, betrayed his people and is helping the Lich King create '
          'a new undead army.',
  'caverns_of_time': False,
  'achievements': [482, 493],
  'required_tier': 13},
 {'name': 'The Violet Hold',
  'min_level': 71,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'in Dalaran there is a magical prison holding the most dangerous creatures of Azeroth. '
          'After the protective barriers were breached, the prisoners broke out, and the mages '
          'have to fight them right inside the city. They need help and promise generous rewards.',
  'caverns_of_time': False,
  'achievements': [483, 494],
  'required_tier': 13},
 {'name': 'Gundrak',
  'min_level': 72,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': "the ancient Drakkari city in Zul'Drak has become the center of the trolls' desperate "
          'war against the Scourge. The trolls have begun sacrificing their own loa, trying to '
          'gain enough power to protect their people.',
  'caverns_of_time': False,
  'achievements': [484, 495],
  'required_tier': 13},
 {'name': 'Halls of Stone',
  'min_level': 73,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': "deep in the Storm Peaks lies a titan complex where part of Azeroth's ancient history is "
          'kept. Its keepers have turned hostile, and inside dwells Loken, a powerful titanic '
          'keeper who betrayed his creators.',
  'caverns_of_time': False,
  'achievements': [485, 496],
  'required_tier': 13},
 {'name': 'Halls of Lightning',
  'min_level': 74,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'one of the great titan fortresses in the Storm Peaks is under the rule of Loken. He '
          'uses titan-made creatures and ancient mechanisms to conceal his betrayal and keep '
          'control over the complex.',
  'caverns_of_time': False,
  'achievements': [486, 497],
  'required_tier': 13},
 {'name': 'The Oculus',
  'min_level': 75,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'in the magical fortress of the Nexus, Malygos is amassing huge reserves of energy for '
          'his war against mortal mages.',
  'caverns_of_time': False,
  'achievements': [487, 498],
  'required_tier': 13},
 {'name': 'Utgarde Pinnacle',
  'min_level': 75,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'at the top of the huge fortress of Utgarde Keep in the Howling Fjord lies a Vrykul '
          'sanctuary, where King Ymiron is preparing to lead his people in a war against the '
          'living. The Vrykul warriors worship death and serve the forces of the Lich King, and '
          'Ymiron himself has made a pact with the mighty forces of the Scourge to regain his life '
          'and keep his power over his people.',
  'caverns_of_time': False,
  'achievements': [488, 499],
  'required_tier': 13},
 {'name': 'The Culling of Stratholme',
  'min_level': 75,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'Arthas slaughters the inhabitants of Stratholme.',
  'caverns_of_time': True,
  'achievements': [479, 500],
  'required_tier': 0},
 {'name': 'Trial of the Champion',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'at the Argent Tournament (in Icecrown), the finest warriors of Azeroth undergo a series '
          'of trials to prove their strength and prepare for the campaign against the Lich King. '
          'Everyone who wishes is invited to take part.',
  'caverns_of_time': False,
  'achievements': [3778, 4296, 4297, 4298],
  'required_tier': 15},
 {'name': 'The Forge of Souls',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'in the depths of Icecrown Citadel lies a forge where the Scourge extracts the souls of '
          'the fallen and turns them into energy for its armies. It is guarded by powerful '
          'servants of the Lich King.',
  'caverns_of_time': False,
  'achievements': [4516, 4519],
  'required_tier': 16},
 {'name': 'Pit of Saron',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'a huge quarry beneath Icecrown Citadel is used by the Scourge as a place for mining the '
          'dark metal saronite and holding slaves. Under the direction of Scourgelord Tyrannus, '
          "the prisoners mine materials to strengthen the Lich King's army.",
  'caverns_of_time': False,
  'achievements': [4517, 4520],
  'required_tier': 16},
 {'name': 'Halls of Reflection',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': "sacred halls inside Icecrown Citadel hold Frostmourne, the Lich King's sword.",
  'caverns_of_time': False,
  'achievements': [4518, 4521],
  'required_tier': 16}]

RAID_RUMORS = [{'name': 'Molten Core',
  'min_level': 58,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'deep beneath Blackrock Mountain lies a vast underground realm of fire, inhabited by '
          'elementals and other creatures of Ragnaros. The Firelord was summoned by the Dark Iron '
          'dwarves and now seeks to destroy his enemies and subjugate all of Azeroth.',
  'achievements': [686],
  'required_tier': 0},
 {'name': "Onyxia's Lair",
  'min_level': 58,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'in a cave beneath Dustwallow Marsh lies the lair of Onyxia, daughter of Deathwing and a '
          'mighty black dragoness. She can take human form and for many years secretly meddled in '
          'the affairs of the kingdom of Stormwind, seeking to sow chaos among humans.',
  'achievements': [684],
  'required_tier': 0,
  'max_tier': 12},
 {'name': 'Blackwing Lair',
  'min_level': 58,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'deep inside Blackrock Mountain lies the stronghold of Nefarian, son of Deathwing and '
          'lord of the Black Dragonflight. He conducts monstrous experiments on dragons of other '
          'flights, trying to create new breeds of drakonids and raise an army capable of '
          'destroying the enemies of the black dragonflight.',
  'achievements': [685],
  'required_tier': 1},
 {'name': "Zul'Gurub",
  'min_level': 58,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'in the jungles of Stranglethorn lies the ancient city of the Gurubashi trolls, which '
          'has become the center of the cult of the blood god Hakkar the Soulflayer. The trolls '
          'are trying to bring Hakkar back into the world of the living, and his priests offer up '
          'the blood and souls of their enemies as sacrifices.',
  'achievements': [688],
  'required_tier': 'zul_gurub'},
 {'name': "Ruins of Ahn'Qiraj",
  'min_level': 58,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'in southern Silithus lie the ruins of an ancient qiraji city, recently opened after the '
          'thousand-year imprisonment of their army. The qiraji are gathering underground once '
          'more and preparing to resume the war against the peoples of Azeroth.',
  'achievements': [689],
  'required_tier': 4},
 {'name': "Temple of Ahn'Qiraj",
  'min_level': 58,
  'max_level': 60,
  'expansion': 'classic',
  'text': "beyond the Gates of Ahn'Qiraj lies an ancient temple where the qiraji worship C'Thun, "
          "one of the Old Gods. Despite a thousand years of imprisonment, C'Thun is still alive "
          'and uses the qiraji, the silithid and its own followers to regain influence over the '
          'surface of Azeroth.',
  'achievements': [687],
  'required_tier': 4},
 {'name': 'Naxxramas',
  'min_level': 58,
  'max_level': 60,
  'expansion': 'classic',
  'text': 'the vast Scourge citadel floats above the Eastern Plaguelands and serves as the '
          "stronghold of the archlich Kel'Thuzad. Inside are gathered the mightiest undead "
          "creatures, and Kel'Thuzad himself is creating a new Scourge army and preparing yet "
          'another offensive against the living.',
  'achievements': [],
  'required_tier': 6,
  'max_tier': 12},
 {'name': 'Karazhan',
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'in Deadwind Pass rises the ancient tower of Medivh, the last Guardian of Tirisfal. '
          'After his death, Karazhan remained filled with remnants of his magic, ghosts and '
          'creatures from other worlds, and some of its inhabitants are trying to get at the '
          'secrets hidden in the tower.',
  'achievements': [690],
  'required_tier': 8},
 {'name': "Gruul's Lair",
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': "in the caves of the Blade's Edge Mountains lies the lair of Gruul the Dragonkiller, a "
          'huge gronn whom numerous ogres obey. Gruul hunts dragons and holds them in slavery, and '
          'his servants use the surrounding mountains as a base for their forays.',
  'achievements': [692],
  'required_tier': 8},
 {'name': "Magtheridon's Lair",
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'deep inside Hellfire Citadel lies a prison holding the defeated Burning Legion lord '
          'Magtheridon. The Fel Orcs use his blood to create new demonic warriors, while keeping '
          'the demon himself captive and draining power from him.',
  'achievements': [693],
  'required_tier': 8},
 {'name': 'Serpentshrine Cavern',
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'deep beneath the waters of Zangarmarsh lies a vast reservoir seized by the nagas under '
          'the command of Lady Vashj. The naga are pumping water out of the marshes to change the '
          "region's ecosystem and secure a source of energy and water for Illidan's army.",
  'achievements': [694],
  'required_tier': 9},
 {'name': 'Tempest Keep: The Eye',
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': "in Netherstorm floats the ancient naaru fortress Tempest Keep, seized by Kael'thas "
          "Sunstrider and his blood elves. Kael'thas uses the fortress's technology and energy to "
          'prepare his plans, and within it dwell powerful creatures and lie magical artifacts.',
  'achievements': [696],
  'required_tier': 9},
 {'name': 'Battle for Mount Hyjal',
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'in the Caverns of Time one can travel back into the past and personally witness '
          'historical events. For example, witness the defense of Mount Hyjal during the Third '
          'War. The Burning Legion under the command of Archimonde is trying to destroy the World '
          'Tree, while the armies of humans, orcs and night elves unite to defend it.',
  'achievements': [695],
  'required_tier': 10},
 {'name': 'Black Temple',
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': 'the ancient temple in Shadowmoon Valley has been seized by Illidan Stormrage, who has '
          'turned it into a huge fortress for his forces. The Illidari, naga, blood elves and '
          'demons serve him, while Illidan himself prepares for his confrontation with the forces '
          'of Azeroth.',
  'achievements': [697],
  'required_tier': 10},
 {'name': "Zul'Aman",
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': "deep in the forests of the Ghostlands, in the south of Quel'Thalas, lies the ancient "
          "capital of the Amani trolls, led by Zul'jin. The trolls are trying to reclaim the lands "
          'they lost in their wars with the elves and humans, and they make pacts with the ancient '
          'loa spirits to gain enough power for a new war.',
  'achievements': [691],
  'required_tier': 'zul_aman'},
 {'name': 'Sunwell Plateau',
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'text': "on the Isle of Quel'Danas lies the Sunwell, the ancient source of the blood elves' "
          "magic. Kael'thas and the Burning Legion are trying to use its energy to summon the "
          "mighty demon Kil'jaeden into Azeroth and open his way into the world.",
  'achievements': [698],
  'required_tier': 12},
 {'name': 'Naxxramas',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'the ancient Scourge citadel has reappeared above Dragonblight, becoming one of the Lich '
          "King's main strongholds. Kel'Thuzad has returned and is gathering undead armies within, "
          'preparing to destroy the defenders of Northrend.',
  'achievements': [576, 577],
  'required_tier': 13},
 {'name': 'The Eye of Eternity',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'at the heart of the magical Nexus lies the lair of Malygos, the Aspect of Magic and '
          'ruler of the blue dragonflight. He has declared war on mortals for their reckless use '
          "of magic and is trying to seize control of Azeroth's magical energy.",
  'achievements': [622, 623],
  'required_tier': 13},
 {'name': 'The Obsidian Sanctum',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'beneath Wyrmrest Temple lies an ancient lair of black dragons commanded by Sartharion. '
          'He guards the eggs and young dragons, and together with the Twilight dragons he is '
          'trying to create a new generation of creatures bound to the powers of Deathwing.',
  'achievements': [1876, 625],
  'required_tier': 13},
 {'name': 'Vault of Archavon',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'beneath Wintergrasp Fortress lies an ancient titan vault, protected by powerful '
          'elementals and titan-made creatures. The Horde and the Alliance fight for control of '
          'this fortress. After the fortress is captured, its defenders gain access inside, where '
          'unknown creatures connected to the ancient powers of Azeroth dwell.',
  'achievements': [1722, 1721],
  'required_tier': 13},
 {'name': 'Ulduar',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'in the mountains of the Storm Peaks lies a gigantic titan complex, created to watch '
          'over Azeroth and to imprison the ancient Old God Yogg-Saron. After the betrayal of the '
          "keeper Loken, many of Ulduar's defenders have become enemies, and someone must fight "
          'their way through the ancient complex and stop Yogg-Saron from being freed.',
  'achievements': [2894, 2895],
  'required_tier': 14},
 {'name': 'Trial of the Crusader',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': "at the Argent Tournament Grounds, the Argent Crusade is gathering Azeroth's strongest "
          'warriors to prepare them for the assault on Icecrown Citadel. The trials are meant to '
          'determine the best fighters. All warriors in Northrend who stand against the Scourge '
          'are invited to take part. Besides the chance to test their strength and gain combat '
          'experience, the organizers offer valuable gifts to the best fighters to help them stand '
          'against the armies of the Lich King.',
  'achievements': [3917, 3916, 3918, 3812],
  'required_tier': 15},
 {'name': "Onyxia's Lair",
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'long after her first defeat, Onyxia returns to her lair, hiding in Dustwallow Marsh. '
          'She once again uses her drakonids and minions to restore the influence of the Black '
          'Dragonflight and prepare a new threat for mortals.',
  'achievements': [4396, 4397],
  'required_tier': 13},
 {'name': 'Icecrown Citadel',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': "at the center of Icecrown stands the Lich King's vast fortress, surrounded by Scourge "
          'armies. In its depths lie undead forges, prisons and sanctums, and atop the Frozen '
          'Throne Arthas Menethil awaits those who dare to challenge him. This citadel is the '
          'heart of the Scourge, from which Arthas controls countless undead armies throughout '
          'Azeroth. Only victory over him will eliminate the undead threat.',
  'achievements': [4530, 4597, 4583, 4584],
  'required_tier': 16},
 {'name': 'Ruby Sanctum',
  'min_level': 78,
  'max_level': 80,
  'expansion': 'wotlk',
  'text': 'beneath Wyrmrest Temple lies the sanctum of the red dragonflight, which guards the eggs '
          'and future offspring of the dragons. Twilight dragons under the command of Halion are '
          'attacking the sanctum, trying to destroy the red dragonflight and pave the way for the '
          "return of Deathwing's forces.",
  'achievements': [4817, 4815, 4816, 4818],
  'required_tier': 17}]

# text is keyed by the listener faction that may hear it.
LOCATION_RUMORS = [{'name': 'Darkshore',
  'min_level': 8,
  'max_level': 14,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'text': {'Alliance': 'Darkshore is an ancient night elf coast where dense forests give way to '
                       'misty coves and the ruins of old settlements. Since the cataclysm of '
                       'ancient times this land has kept many traces of destruction, and its '
                       'inhabitants face naga, satyrs, furbolgs and other threats. Auberdine '
                       'serves as an important stronghold for the night elves, maintaining their '
                       'link with the rest of Kalimdor. The night elves strive to keep the coast '
                       'from further corruption, while their scant forces try both to protect the '
                       'inhabitants and to investigate the mysterious events in the forests.'},
  'required_tier': 0},
 {'name': 'Loch Modan',
  'min_level': 8,
  'max_level': 14,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'text': {'Alliance': 'Loch Modan is a mountainous region guarding the eastern approaches to '
                       'Ironforge. At the heart of the region lies a huge reservoir, vital to the '
                       "dwarves. But the land's security is constantly disrupted by kobolds, "
                       'trolls and other enemies, and ancient ruins bear traces of far older '
                       'conflicts. Thelsamar and the neighboring settlements need protection, '
                       'since even the relatively peaceful life of the dwarves depends on the '
                       'safety of the mines, the roads and the dam. Any serious threat here could '
                       'affect the water supply of Ironforge itself.'},
  'required_tier': 0},
 {'name': 'Westfall',
  'min_level': 8,
  'max_level': 14,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'text': {'Alliance': 'Westfall was once one of the most fertile regions of Stormwind, but war '
                       'and ruin have left behind poverty and abandoned farms. The farmers try to '
                       'survive amid hunger, bandits and constant attacks. Especially dangerous is '
                       'the Defias Brotherhood - former builders of Stormwind who have turned into '
                       'an organized criminal force. Their presence turns the roads and farms into '
                       'a dangerous place, and the residents of Sentinel Hill face the '
                       'consequences of their activities almost every day. For the Alliance, '
                       'defending Westfall means not just fighting bandits but also restoring a '
                       'normal life for ordinary people.'},
  'required_tier': 0},
 {'name': 'Silverpine Forest',
  'min_level': 8,
  'max_level': 14,
  'expansion': 'classic',
  'factions': ('Horde',),
  'text': {'Horde': 'Silverpine Forest is a gloomy forest south of Tirisfal, where the Forsaken '
                    'are trying to strengthen their presence in the former lands of Lordaeron. '
                    'Here they are opposed by the humans of the kingdom of Gilneas, who refuse to '
                    'put up with undead neighbors, as well as by numerous wild creatures and '
                    'enemies. Shadowfang Keep and the surrounding lands hide threats of their own. '
                    'For the Forsaken the struggle for Silverpine is of special importance: it is '
                    'one of the few regions where they can expand the safe zone around Undercity. '
                    'Their confrontation with Gilneas is gradually turning into a struggle for the '
                    'very future of northern Lordaeron.'},
  'required_tier': 0},
 {'name': 'The Barrens',
  'min_level': 8,
  'max_level': 14,
  'expansion': 'classic',
  'factions': ('Horde',),
  'text': {'Horde': 'The Barrens is a vast, dry plain linking the main Horde settlements of '
                    'Kalimdor. Roads from Durotar, Mulgore and other lands converge here, and the '
                    'Crossroads is becoming the most important hub of trade and supply. The Horde '
                    'has to guard caravans, support settlements, fight the centaurs and repel '
                    'threats from the local tribes all at once. The huge distances make every road '
                    'vulnerable. Especially dangerous are the centaurs, who regard the new Horde '
                    'settlements as an invasion of their lands. For the young Horde, keeping the '
                    'routes through the Barrens safe is of vital importance.'},
  'required_tier': 0},
 {'name': 'Redridge Mountains',
  'min_level': 14,
  'max_level': 18,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'text': {'Alliance': 'Redridge Mountains is an important eastern region of Stormwind, where '
                       'small human settlements have been practically cut off from help. The war '
                       'left the region weakened, and the Blackrock Orcs exploit this weakness for '
                       'constant attacks. Lakeshire tries to maintain order while defending itself '
                       'against orcs, gnolls and bandits. For the people of Redridge, the '
                       'Blackrock presence is no abstract threat: enemy squads raid the roads and '
                       'settlements and kill civilians, seeking to gain a foothold in human lands. '
                       'Stormwind must support its citizens while the borderland gradually turns '
                       'into a new front line.'},
  'required_tier': 0},
 {'name': 'Stonetalon Mountains',
  'min_level': 14,
  'max_level': 19,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Stonetalon Mountains is a harsh mountainous region where the night elves '
                       'and their allies are trying to stop the destruction of the ancient '
                       'forests. Horde lumber camps are steadily advancing into the mountains, '
                       'harvesting timber for the growing Horde settlements. For the night elves '
                       'the forest is not a lifeless resource, but part of an ancient natural '
                       'heritage that they have protected for thousands of years. However, the '
                       'local Alliance forces are few, and numerous threats - from harpies to '
                       'aggressive tribes - keep them from focusing on the main conflict.',
           'Horde': 'For the Horde, Stonetalon Mountains is one of the few areas where timber and '
                    'other necessary resources can be obtained not far from the Barrens. The '
                    'growing settlements need houses, roads and fortifications, while the natural '
                    'resources of Durotar and the Barrens are limited. The Horde camps try to meet '
                    'this need while facing resistance from the night elves and the local tribes. '
                    'The Horde sees its presence as a necessary part of building a new home on '
                    'Kalimdor, while its opponents seek to prevent any further expansion of its '
                    'settlements.'},
  'required_tier': 0},
 {'name': 'Ashenvale',
  'min_level': 17,
  'max_level': 23,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'The ancient forests of Ashenvale are the sacred land of the night elves, '
                       'where they have lived for almost ten thousand years. Many night elves grew '
                       'up here, playing on the shores of shimmering pools and walking beneath the '
                       'spreading crowns of the local trees. The night elves are ready to defend '
                       'these sacred forests with their lives against logging, corruption and '
                       'invasion by outsiders. Horde loggers and their allies are pushing ever '
                       'deeper into the forest, ruthlessly cutting down thousand-year-old trees, '
                       'exterminating rare animals and turning beautiful groves into lifeless, '
                       'dead wastelands. The night elves are trying to save their ancient heritage '
                       'from destruction, but it is becoming ever harder for them to hold back the '
                       'countless streams of orcs pouring into Ashenvale. They desperately need '
                       'help.',
           'Horde': 'Ashenvale is a large forest west of Orgrimmar. The Horde did not come to '
                    'Ashenvale for senseless destruction: its settlements need timber for '
                    'construction and for the survival of the young nation. Orcs, trolls, tauren '
                    'and members of other races from all over Kalimdor are flocking to the booming '
                    'Orgrimmar. Many of them lost their homes elsewhere because of Alliance '
                    'attacks. The Horde must expand housing construction to meet the needs of all '
                    'the newcomers - that is why several settlements and lumber mills were founded '
                    'in Ashenvale to obtain vital resources. However, the night elves respond to '
                    "the Horde's presence with brutality - they carry out bloody raids, killing "
                    'civilians, loggers and traders, and entire caravans are wiped out. The Horde '
                    'urgently needs reinforcements to help it gain a foothold in Ashenvale, put an '
                    "end to the night elves' marauding raids and supply Orgrimmar with building "
                    'materials.'},
  'required_tier': 0},
 {'name': 'Duskwood',
  'min_level': 17,
  'max_level': 23,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'text': {'Alliance': 'Duskwood is a gloomy region south of Stormwind, once an ordinary forest '
                       'that has turned into a land of constant fear. After a huge number of '
                       'undead and other monsters appeared, the people of Darkshire found '
                       'themselves effectively cut off from safe territory. The forest is roamed '
                       'by undead, worgen, spiders and other creatures, and a mystery connected '
                       'with Raven Hill and ancient powers hangs over the whole region. The people '
                       'try to keep their homes and to bury the dead with dignity, but it becomes '
                       'harder every day. Darkshire needs defenders capable of standing against '
                       'threats that the local watch can no longer handle.'},
  'required_tier': 0},
 {'name': 'Hillsbrad Foothills',
  'min_level': 19,
  'max_level': 25,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Hillsbrad is the fertile land of a human kingdom, where Southshore remains '
                       'one of the few Alliance strongholds in the north. After the fall of '
                       'Lordaeron the region found itself surrounded by the forces of the '
                       'Forsaken, who seek to drive the humans out of their remaining settlements. '
                       'For the people of Southshore this is a fight to keep at least a small '
                       'patch of human land. Trade routes come under attack, and Forsaken squads '
                       'appear near the settlements more and more often. The people of Hillsbrad '
                       'are trying to hold on to their homeland and not let the undead erase the '
                       'last traces of human presence in the region for good.',
           'Horde': 'For the Forsaken, Hillsbrad is a land that once belonged to their people and '
                    'is now gradually returning to their control. After the destruction of '
                    'Lordaeron, the humans of Southshore continue to hold territory that the '
                    'Forsaken consider part of their heritage. Tarren Mill serves as an important '
                    'foothold of the Forsaken, but its inhabitants constantly face attacks by the '
                    'Alliance and the local humans. For the Forsaken the conflict is not just '
                    'about territorial expansion: they seek to reclaim land they regard as the '
                    'rightful heritage of their people, and to protect those who have found refuge '
                    "under Sylvanas's rule."},
  'required_tier': 0},
 {'name': 'Wetlands',
  'min_level': 19,
  'max_level': 25,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'text': {'Alliance': 'Wetlands is a marshy region between Dun Morogh and the sea, through which '
                       'important routes to the north pass. Menethil Harbor links the dwarven '
                       "lands with the rest of the world, so the region's security is of enormous "
                       'importance for trade and military transport. However, the marshes teem '
                       'with murlocs, crocolisks, dragons and other dangerous creatures, and the '
                       'local tribes constantly threaten travelers. On top of the natural dangers, '
                       'traces of old wars and of the conflict with the dragons remain here. For '
                       'the Alliance, defending the Wetlands means preserving one of the most '
                       'important sea routes of northern Khaz Modan.'},
  'required_tier': 0},
 {'name': 'Thousand Needles',
  'min_level': 23,
  'max_level': 29,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Thousand Needles is a vast system of canyons where a few Alliance '
                       'settlements try to keep order far from the main human lands. Dangerous '
                       'tribes, wild beasts and numerous bandits lurk deep in the canyons. A '
                       "particular threat is the region's constant instability: the roads run "
                       'through narrow gorges where it is easy to set up an ambush. The Alliance '
                       'has to maintain contact between the remote settlements and protect '
                       'peaceful traders from those who use the deserted canyons for robbery.',
           'Horde': 'For the Horde, Thousand Needles is a natural continuation of the southern '
                    'lands of the Barrens. The tauren and other members of the Horde use the '
                    "region's canyons and oases for trade and resource gathering, but face "
                    'numerous threats. Centaurs and other hostile tribes seek to control the '
                    'roads, and Freewind Post remains a vulnerable settlement amid the huge stone '
                    'walls. The security of these lands is important for the link between the '
                    "Horde's southern territories and the rest of Kalimdor."},
  'required_tier': 0},
 {'name': 'Arathi Highlands',
  'min_level': 28,
  'max_level': 35,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Arathi Highlands is the ancient land of the human kingdom of Arathor, '
                       'where Stromgarde recalls the times when humans united against the greatest '
                       'threats of the past. Now the region is divided among numerous forces, and '
                       'Stromgarde is trying to restore its influence. The Alliance seeks to '
                       'preserve the human heritage here and to protect the remaining settlements '
                       'from bandits, trolls and Horde troops. For humans this is not just another '
                       'border region: Arathi holds the memory of the birth of the human kingdoms, '
                       'and its fate matters far beyond the Highlands themselves.',
           'Horde': 'The Horde regards Arathi Highlands as an important territory for '
                    'strengthening its positions in the northern lands. Hammerfall serves as a '
                    'foothold for the orcs, while around it remain enemies capable of threatening '
                    'both the settlers themselves and the trade routes. Stromgarde and other '
                    "Alliance forces are not willing to put up with the Horde's presence. For the "
                    'orcs, defending Hammerfall means ensuring the safety of those who have '
                    "settled far from the Horde's main lands, and establishing a lasting presence "
                    'in a region where clashes constantly flare up.'},
  'required_tier': 0},
 {'name': 'Desolace',
  'min_level': 29,
  'max_level': 35,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Desolace is a once-fertile land of the centaurs, turned into a barren '
                       'wasteland. Ancient conflicts, the destruction of nature and the activities '
                       'of hostile tribes have made the region one of the grimmest places in '
                       'Kalimdor. The night elves and their allies are trying to restore the '
                       'broken balance, stand against the satyrs and deal with the centaurs, whose '
                       'raids threaten the few settlements. For the Alliance, helping in Desolace '
                       'is a chance to stop the further destruction of the land and to support '
                       'those trying to bring back to the wasteland at least part of its former '
                       'life.',
           'Horde': 'For the Horde, Desolace is a dangerous wasteland where a few settlements try '
                    'to survive amid constant attacks by centaurs and other enemies. Shadowprey '
                    "Village and Nijel's Point lie in a region where any journey can end in an "
                    'ambush. The Horde does not seek to destroy the nature of Desolace - on the '
                    'contrary, its settlements are trying to give their inhabitants the chance to '
                    'live and trade in a land where there is practically no safety. The local '
                    'centaur tribes constantly threaten these settlements, and without additional '
                    'protection their existence is becoming ever more precarious.'},
  'required_tier': 0},
 {'name': 'Stranglethorn Vale',
  'min_level': 29,
  'max_level': 35,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Stranglethorn Vale is a vast jungle where an Alliance expedition is trying '
                       'to explore rich but dangerous lands. Trolls, pirates, treasure hunters and '
                       'numerous monsters clash here. Booty Bay formally belongs to the neutral '
                       'goblins, but beyond its limits travelers constantly run into pirates and '
                       'troll tribes. The Alliance must protect traders and explorers, and also '
                       'help fight threats that could spread far beyond the jungle.',
           'Horde': "Grom'gol Base Camp is the most important Horde stronghold in the southern "
                    'part of the Eastern Kingdoms. The orcs have dug in here far from their main '
                    'lands and are trying to maintain a safe link with other settlements. Hostile '
                    'trolls, pirates and numerous dangerous creatures are active in the jungle, '
                    'and Alliance expeditionary forces are also seeking to strengthen their '
                    "presence. For the Horde, defending Grom'gol means defending its only major "
                    'foothold in the region, which allows its members to travel safely and keep up '
                    'trade routes.'},
  'required_tier': 0},
 {'name': 'Badlands',
  'min_level': 33,
  'max_level': 39,
  'expansion': 'classic',
  'factions': ('Horde',),
  'text': {'Horde': 'Badlands is a lifeless, rocky land where the Horde has built Kargath - an '
                    'important stronghold far from the main Horde territories. Traces of ancient '
                    'civilizations, golems, ogres and members of the Dark Iron clan are found '
                    'everywhere here. For the Horde, Kargath is of strategic importance: the '
                    'routes to Searing Gorge and Blackrock Mountain run through this region. But '
                    'the settlement is constantly under threat, and the exploration of ancient '
                    'ruins uncovers ever new dangers. Members of the Horde have to defend their '
                    'positions while also dealing with threats that may prove far older than the '
                    'current war.'},
  'required_tier': 0},
 {'name': 'Dustwallow Marsh',
  'min_level': 33,
  'max_level': 39,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Dustwallow Marsh is a vast swampland where Theramore serves as the most '
                       'important Alliance bastion in Kalimdor. The city is surrounded by swamps, '
                       'dragons, murlocs and aggressive tribes, and its position makes it both a '
                       'refuge for civilians and a military base. Theramore strives to maintain '
                       'stability and to keep up ties between the scattered Alliance settlements. '
                       'But the threats around the city keep growing, and the safety of this '
                       'island depends on the ability to protect the roads, supplies and '
                       'population from numerous enemies.',
           'Horde': 'For the Horde, Dustwallow Marsh is a territory where Brackenwall Village and '
                    'other settlements are trying to survive amid the swamps and constant '
                    'hostility with Theramore. Members of the Horde came here not just for '
                    'territory: the growing population of the Barrens needs new lands and sources '
                    "of resources. But the Alliance regards the Horde's presence as a threat to "
                    'its interests and maintains a military presence in Theramore. The Horde has '
                    'to defend its settlements from attacks while also standing against dangerous '
                    'dragons, murlocs and other denizens of the swamps.'},
  'required_tier': 0},
 {'name': 'Swamp of Sorrows',
  'min_level': 33,
  'max_level': 39,
  'expansion': 'classic',
  'factions': ('Horde',),
  'text': {'Horde': 'Swamp of Sorrows is a gloomy swamp right on the border with the Blasted '
                    'Lands, where Stonard is the most important Horde stronghold. Here lie the '
                    "ancient Temple of Atal'Hakkar, the dangerous Atal'ai trolls, dragons and "
                    'numerous swamp predators. For the Horde, Stonard is especially important '
                    'because of its location near the Dark Portal and the routes to other regions. '
                    'However, the land around the settlement remains extremely dangerous, and the '
                    "forces connected with the Atal'ai and ancient cults threaten all living "
                    'beings. The local members of the Horde have to defend their garrison while '
                    'also dealing with these ancient threats.'},
  'required_tier': 0},
 {'name': 'Feralas',
  'min_level': 38,
  'max_level': 44,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Feralas is a vast ancient forest where the night elves and other Alliance '
                       'forces are trying to save what remains of nature from destruction. '
                       'Feathermoon Stronghold is located on an island off the western coast and '
                       'serves as a base for expeditions into the interior of the continent. '
                       'Hostile ogres, centaurs and other creatures are active here, and ancient '
                       'ruins hold many secrets. For the Alliance, its presence in Feralas is tied '
                       'to protecting nature, exploring the ancient heritage and supporting those '
                       'trying to keep this vast forest from finally turning into a wasteland.',
           'Horde': 'Camp Mojache is a small but important Horde outpost amid the vast forests of '
                    'Feralas. The Horde has established itself here to ensure the safety of '
                    "travelers and gain access to the region's riches. But the forest is full of "
                    'dangers: ogres, centaurs, wild beasts and ancient ruins pose a threat to any '
                    'settlement. In addition, the presence of the Alliance heightens tensions. '
                    'Horde members must maintain Camp Mojache and protect their caravans so that '
                    'the isolated outpost is not cut off from the rest of the Horde.'},
  'required_tier': 0},
 {'name': 'The Hinterlands',
  'min_level': 38,
  'max_level': 44,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'The Hinterlands is an ancient land of the high elves, where Aerie Peak '
                       'serves as home to the Wildhammer dwarves. Here the Alliance simultaneously '
                       'faces trolls, dragons, forest beasts and ancient conflicts rooted in the '
                       "region's history. The high elves are trying to preserve their lands, while "
                       'the dwarves defend their mountain stronghold against numerous enemies. For '
                       'the Alliance, a presence here means protecting its allies and preventing '
                       'ancient powers and hostile tribes from gaining control over the '
                       'northeastern lands.',
           'Horde': 'For the Horde, the Hinterlands is a distant territory where Revantusk Village '
                    'serves as home to the allied forest trolls. The trolls are trying to rebuild '
                    'their strength after long years of wars and struggles against other tribes. '
                    'Their alliance with the Horde gives them the protection and support they had '
                    'long lacked. But hostile elves, dwarves and other tribes are nearby. The '
                    'Horde must support its allies and not allow its enemies to destroy the '
                    'Revantusk settlement.'},
  'required_tier': 0},
 {'name': 'Tanaris',
  'min_level': 38,
  'max_level': 44,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Tanaris is a vast desert where the goblin city of Gadgetzan serves as the '
                       'main neutral hub for travelers of both factions. Around the city, the '
                       'interests of the Steamwheedle Cartel, pirates, ogres, trolls and the '
                       'mysterious silithid insects clash. A particular threat is posed by '
                       "Zul'Farrak, where ancient sand trolls perform dangerous rituals and from "
                       'which they raid caravans and lone travelers. The desert also holds the '
                       'ruins of ancient civilizations and traces of powers capable of threatening '
                       "all of Kalimdor. The region's many threats require the intervention of "
                       'those capable of standing against them. Both the Horde and the Alliance '
                       'seek to strengthen their influence in the region and to keep it from '
                       'falling completely under the control of their rivals.',
           'Horde': 'Tanaris is a vast desert where the goblin city of Gadgetzan serves as the '
                    'main neutral hub for travelers of both factions. Around the city, the '
                    'interests of the Steamwheedle Cartel, pirates, ogres, trolls and the '
                    'mysterious silithid insects clash. A particular threat is posed by '
                    "Zul'Farrak, where ancient sand trolls perform dangerous rituals and from "
                    'which they raid caravans and lone travelers. The desert also holds the ruins '
                    'of ancient civilizations and traces of powers capable of threatening all of '
                    "Kalimdor. The region's many threats require the intervention of those capable "
                    'of standing against them. Both the Horde and the Alliance seek to strengthen '
                    'their influence in the region and to keep it from falling completely under '
                    'the control of their rivals.'},
  'required_tier': 0},
 {'name': 'Searing Gorge',
  'min_level': 42,
  'max_level': 48,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Searing Gorge is a scorching industrial wasteland where the Dark Iron '
                       'dwarves carry out large-scale mining operations using slave labor and '
                       'dangerous technologies. The enormous Cauldron is filled with mines, '
                       'golems, fire elementals and other threats. The Thorium Brotherhood has '
                       'built its own stronghold here and is trying to resist the Dark Iron. They '
                       'seek help from members of both factions, offering them the chance to step '
                       'into the conflict and help the Brotherhood in exchange for generous '
                       'rewards and greater Horde or Alliance influence in the region. Beyond the '
                       'mountain passes lies Blackrock Mountain, one of the most dangerous places '
                       'in Azeroth, and the events in Searing Gorge are directly tied to the '
                       'threat posed by the Dark Iron and their allies.',
           'Horde': 'Searing Gorge is a scorching industrial wasteland where the Dark Iron dwarves '
                    'carry out large-scale mining operations using slave labor and dangerous '
                    'technologies. The enormous Cauldron is filled with mines, golems, fire '
                    'elementals and other threats. The Thorium Brotherhood has built its own '
                    'stronghold here and is trying to resist the Dark Iron. They seek help from '
                    'members of both factions, offering them the chance to step into the conflict '
                    'and help the Brotherhood in exchange for generous rewards and greater Horde '
                    'or Alliance influence in the region. Beyond the mountain passes lies '
                    'Blackrock Mountain, one of the most dangerous places in Azeroth, and the '
                    'events in Searing Gorge are directly tied to the threat posed by the Dark '
                    'Iron and their allies.'},
  'required_tier': 0},
 {'name': 'Azshara',
  'min_level': 43,
  'max_level': 49,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Azshara is a wild coastal land that once belonged to the night elves. '
                       'Ancient ruins, towering cliffs and destroyed settlements recall the '
                       'catastrophes of the distant past. The Alliance outpost Talrendis Point '
                       "keeps watch on the Horde's activities while also trying to explore the "
                       "region's dangerous ruins. Here dwell naga, satyrs and other creatures, "
                       'many of whom wield ancient magic. For the Alliance, it is important to '
                       'keep dangerous forces from seizing the artifacts and knowledge hidden '
                       'among the ruins of Azshara, and also to keep these from falling into the '
                       'hands of the Horde.',
           'Horde': 'For the Horde, Azshara is a vast territory directly east of Ashenvale, where '
                    'Valormok serves as an important stronghold. The region is rich in ancient '
                    'artifacts and resources, but nearly every corner of it is dangerous. Naga, '
                    'satyrs and other creatures threaten the small Horde camp, while the Alliance '
                    "outpost Talrendis Point watches the Horde's advance and does not shy away "
                    'from attacking research expeditions and trade caravans. Horde members must '
                    'strengthen their presence in the region while protecting explorers and '
                    'warriors from numerous enemies.'},
  'required_tier': 0},
 {'name': 'Blasted Lands',
  'min_level': 43,
  'max_level': 49,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'The Blasted Lands is a magic-scarred desert surrounding the Dark Portal. '
                       'Nethergarde Keep literally stands guard over the gateway to Outland, '
                       'through which the orcish Horde once came, and now new demonic threats may '
                       'slip through the portal. For the Alliance, defending Nethergarde is not a '
                       'matter of expanding territory: the fortress exists to watch over the Dark '
                       'Portal and to keep the forces of the Burning Legion from getting into '
                       'Azeroth. The garrison constantly faces demons, ogres and other enemies and '
                       'needs help.',
           'Horde': 'For the Horde, the Blasted Lands is a place where its members are trying to '
                    'control their own patch of territory near the Dark Portal. Dreadmaul Hold and '
                    'other Horde forces simultaneously face the demons of the Burning Legion, '
                    'ogres and the Alliance garrison of Nethergarde Keep. For the Horde, being '
                    'here is not only about opposing the Alliance: the Dark Portal poses a threat '
                    'to all of Azeroth, and demons have already entrenched themselves in the '
                    'ruined land. Defending Horde positions makes it possible to keep watch over '
                    'what is happening at the portal and to prevent enemies from using this region '
                    'against the Horde.'},
  'required_tier': 0},
 {'name': 'Felwood',
  'min_level': 46,
  'max_level': 51,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Felwood is one of the most terrifying forests in Kalimdor. Its ancient '
                       'nature has been twisted by demonic corruption, and satyrs and demons are '
                       'spreading it ever deeper. Night elves and members of the Cenarion Circle '
                       'are trying to stop the corruption and find a way to restore at least part '
                       "of the land's former purity. Talonbranch Glade and other camps serve as "
                       'strongholds for those trying to explore the corrupted forest. The struggle '
                       'here is not for political influence but for the very chance to preserve '
                       'what remains of living nature.',
           'Horde': 'For the Horde, Felwood poses the same deadly threat: demonic corruption is '
                    'destroying the forest and gradually turning its inhabitants into monsters. '
                    'Bloodvenom Post serves as a stronghold for Horde members investigating what '
                    'is happening. The tauren and other defenders of nature are no less interested '
                    'in cleansing the land than the night elves are. But to do so, they have to '
                    'face satyrs, demons and corrupted creatures that turn every expedition into a '
                    'deadly undertaking.'},
  'required_tier': 0},
 {'name': "Un'Goro Crater",
  'min_level': 46,
  'max_level': 51,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': "Un'Goro Crater is an ancient valley lost among the mountains, where an "
                       'almost primeval world has survived. Enormous dinosaurs, elementals and '
                       'other creatures that can hardly be found anywhere else live here. Deep '
                       'within the crater lie mysterious sources of energy and traces of the '
                       "ancient titans. For members of both factions, Un'Goro is of interest not "
                       'only as a resource-rich territory: research suggests that what is '
                       'happening here may be connected to far more ancient powers. But '
                       'expeditions must first survive encounters with the local wildlife.',
           'Horde': "Un'Goro Crater is an ancient valley lost among the mountains, where an almost "
                    'primeval world has survived. Enormous dinosaurs, elementals and other '
                    'creatures that can hardly be found anywhere else live here. Deep within the '
                    'crater lie mysterious sources of energy and traces of the ancient titans. For '
                    "members of both factions, Un'Goro is of interest not only as a resource-rich "
                    'territory: research suggests that what is happening here may be connected to '
                    'far more ancient powers. But expeditions must first survive encounters with '
                    'the local wildlife.'},
  'required_tier': 0},
 {'name': 'Burning Steppes',
  'min_level': 48,
  'max_level': 54,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'The Burning Steppes is a scorching land around Blackrock Mountain, where '
                       "Alliance forces hold Morgan's Vigil. Beyond the fortress walls are Dark "
                       'Iron dwarves, Blackrock orcs, dragons and numerous fiery creatures. But '
                       'the main danger is Blackrock Mountain itself, within which entire armies '
                       "of enemies are hidden. Morgan's Vigil is effectively the Alliance's "
                       'forward post facing one of the most dangerous regions of Azeroth. Its '
                       'garrison constantly faces threats and needs help to keep the enemies from '
                       'breaking out of the mountains.',
           'Horde': 'Flame Crest serves as a Horde stronghold at the northern approach to '
                    'Blackrock Mountain. Wars rage all around between the Blackrock orcs, Dark '
                    'Iron dwarves and other forces, while deep within the mountain, powers tied to '
                    'Ragnaros are awakening. The Horde is interested both in defending its own '
                    'positions and in preventing its enemies from growing stronger. Flame Crest '
                    'lies practically at the very entrance to a territory where the fate of a huge '
                    "number of Azeroth's military forces is being decided, so even small "
                    'reinforcements matter greatly.'},
  'required_tier': 0},
 {'name': 'Western Plaguelands',
  'min_level': 48,
  'max_level': 54,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'The Western Plaguelands are the former lands of Lordaeron, turned by the '
                       'Scourge into a plague-ridden wasteland. Despite the plague, remnants of '
                       'life still survive here, and the Alliance, together with the Argent Dawn, '
                       'is trying to stop the contagion from spreading further. Chillwind Camp '
                       'serves as a base for expeditions to Andorhal, Hearthglen and the infected '
                       'farms. Every inch of cleansed land means a chance to return the region to '
                       'the living. But the Scourge still controls vast territories, and the '
                       'forces of the Argent Dawn are too few to deal with all the threats on '
                       'their own.',
           'Horde': 'For the Forsaken, the Western Plaguelands hold special significance: these '
                    "are the lands of former Lordaeron, which they consider part of their people's "
                    'heritage. The Bulwark serves as the gateway to the infected lands, and Horde '
                    'members, together with the Argent Dawn, are trying to destroy the Scourge and '
                    'prevent the plague from spreading further. However, the Alliance encampment '
                    'Chillwind Camp is nearby, so the fight against the undead is constantly '
                    'intertwined with the rivalry between the two factions. For the Forsaken, '
                    'cleansing these lands means regaining control of their own historical '
                    'homeland.'},
  'required_tier': 0},
 {'name': 'Eastern Plaguelands',
  'min_level': 52,
  'max_level': 58,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'The Eastern Plaguelands are one of the most devastated areas of Azeroth. '
                       'Here lies Stratholme, turned by the Scourge into a vast city of the dead, '
                       'and armies of undead, cultists and mutated creatures roam the entire '
                       "territory. Light's Hope Chapel remains the last island of light, where "
                       'members of both factions can unite in the face of a common threat. Even '
                       'the Scarlet Crusade, waging its own war against the undead, is unable to '
                       'cleanse the region on its own. The fate of the Eastern Plaguelands goes '
                       'far beyond the conflict between the Horde and the Alliance: what is being '
                       'decided here is whether the Scourge will be able to keep spreading across '
                       'Azeroth.',
           'Horde': 'The Eastern Plaguelands are one of the most devastated areas of Azeroth. Here '
                    'lies Stratholme, turned by the Scourge into a vast city of the dead, and '
                    'armies of undead, cultists and mutated creatures roam the entire territory. '
                    "Light's Hope Chapel remains the last island of light, where members of both "
                    'factions can unite in the face of a common threat. Even the Scarlet Crusade, '
                    'waging its own war against the undead, is unable to cleanse the region on its '
                    'own. The fate of the Eastern Plaguelands goes far beyond the conflict between '
                    'the Horde and the Alliance: what is being decided here is whether the Scourge '
                    'will be able to keep spreading across Azeroth.'},
  'required_tier': 0},
 {'name': 'Winterspring',
  'min_level': 51,
  'max_level': 57,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Winterspring is a snow-covered northern wasteland where furbolgs, ice '
                       'creatures and other dangerous inhabitants live among ancient forests. '
                       'Everlook, founded by goblins and owned by the Steamwheedle Cartel, becomes '
                       "the main neutral stronghold for both factions. But behind the town's "
                       'safety lies a harsh reality: the local furbolg tribes are gradually '
                       'sinking into madness, demonic forces threaten the forests, and the '
                       "region's ancient secrets attract more and more adventurers. Here, members "
                       'of the Horde and the Alliance face threats that are equally dangerous to '
                       'all living beings.',
           'Horde': 'Winterspring is a snow-covered northern wasteland where furbolgs, ice '
                    'creatures and other dangerous inhabitants live among ancient forests. '
                    'Everlook, founded by goblins and owned by the Steamwheedle Cartel, becomes '
                    "the main neutral stronghold for both factions. But behind the town's safety "
                    'lies a harsh reality: the local furbolg tribes are gradually sinking into '
                    "madness, demonic forces threaten the forests, and the region's ancient "
                    'secrets attract more and more adventurers. Here, members of the Horde and the '
                    'Alliance face threats that are equally dangerous to all living beings.'},
  'required_tier': 0},
 {'name': 'Silithus',
  'min_level': 54,
  'max_level': 59,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Silithus is a desert in the southwest of Kalimdor, where the Cenarion '
                       'Circle is trying to stop the spread of the insectoid silithid. Beneath the '
                       'sands lie the ruins of the ancient aqir empire and the sealed gates of '
                       "Ahn'Qiraj. Both factions are gradually discovering that silithid activity "
                       'poses a threat far beyond the desert itself. Cenarion Hold becomes a '
                       'shared base where members of the Horde and the Alliance can help in the '
                       "fight against the insects, the Twilight's Hammer and other dangerous "
                       'forces. Here the old rivalry between the factions takes a back seat to a '
                       'threat capable of affecting all of Kalimdor.',
           'Horde': 'Silithus is a desert in the southwest of Kalimdor, where the Cenarion Circle '
                    'is trying to stop the spread of the insectoid silithid. Beneath the sands lie '
                    "the ruins of the ancient aqir empire and the sealed gates of Ahn'Qiraj. Both "
                    'factions are gradually discovering that silithid activity poses a threat far '
                    'beyond the desert itself. Cenarion Hold becomes a shared base where members '
                    'of the Horde and the Alliance can help in the fight against the insects, the '
                    "Twilight's Hammer and other dangerous forces. Here the old rivalry between "
                    'the factions takes a back seat to a threat capable of affecting all of '
                    'Kalimdor.'},
  'required_tier': 0},
 {'name': 'Hellfire Peninsula',
  'min_level': 58,
  'max_level': 63,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Hellfire Peninsula in Outland is the first thing the defenders of Azeroth '
                       'see after passing through the Dark Portal. The once-green world has turned '
                       'into a crimson desert torn apart by demonic energy. The Alliance '
                       'Expedition has established itself at Honor Hold, seeking not merely to '
                       'conquer new lands but to prevent a repeat of the catastrophe that once '
                       'destroyed Draenor. The orcs of the Fel Horde, led by Kargath Bladefist, '
                       'threaten the garrison, while the Burning Legion uses the peninsula as a '
                       'staging ground for new invasions. Fighting rages constantly beyond the '
                       "walls of Honor Hold, and the garrison needs help to hold Azeroth's first "
                       'line of defense in Outland. To get here, you must pass through the Dark '
                       'Portal in the Blasted Lands.',
           'Horde': 'After the Dark Portal was opened, the Horde discovered that what awaited it '
                    'on the other side was not the Draenor of old but a shattered world, where '
                    'some of the orcs had renounced their kin and submitted to demons. Thrallmar '
                    "became the Horde's stronghold amid the burning wastes of Hellfire Peninsula. "
                    'The Fel Horde, led by Kargath Bladefist, has seized a significant part of the '
                    'region and threatens everyone who tries to oppose it. At the same time, the '
                    'Burning Legion continues to use Outland for its own purposes. The Horde '
                    'garrison has found itself at the very center of this war, and its survival '
                    'depends on its ability to stop the traitors and the demons. To get here, you '
                    'must pass through the Dark Portal in the Blasted Lands.'},
  'required_tier': 8},
 {'name': 'Zangarmarsh',
  'min_level': 60,
  'max_level': 62,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Zangarmarsh is a vast expanse of wetlands where a unique Outland ecosystem '
                       "has survived among giant mushrooms. Telredor serves as the Alliance's "
                       'stronghold, but the world here is rapidly being destroyed. Naga under the '
                       'command of Lady Vashj have begun draining the marshes, taking the water '
                       'for their own purposes. This threatens not only the local inhabitants but '
                       "the very existence of Zangarmarsh's ecosystem. Alliance expeditions are "
                       'trying to understand what is happening and to stop the destruction of the '
                       'marshes before the naga turn the entire region into a lifeless wasteland.',
           'Horde': "Cenarion Refuge and Zabra'jin become the Horde's strongholds in Zangarmarsh, "
                    'where members of different peoples are trying to get to the bottom of the '
                    'mysterious disappearance of the water. Naga are systematically draining the '
                    'marshes, upsetting the natural balance and leaving the local inhabitants '
                    'without sources of water. For the Horde, this is not just a territorial '
                    'conflict: the destruction of Zangarmarsh threatens everyone who lives in the '
                    "region. The local settlements need help while Lady Vashj's forces continue to "
                    'expand their network of pumps and channels.'},
  'required_tier': 8},
 {'name': 'Terokkar Forest',
  'min_level': 62,
  'max_level': 64,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Terokkar Forest surrounds the ancient city of Shattrath, which has become '
                       'a refuge for those who have turned away from demons and war. But outside '
                       'the city, the forest is far from safe. Arakkoa wield ancient magic, '
                       'cultists work for mysterious powers, and fallen draenei are trying to '
                       'regain their influence. The Alliance Expedition has settled at Allerian '
                       'Stronghold, from which it supports the locals and explores the ancient '
                       'mysteries of Terokkar. Especially troubling is the fate of Auchindoun — '
                       'once a sacred place of the draenei, now turned into an abode of the undead '
                       'and other dangerous forces.',
           'Horde': 'Terokkar Forest surrounds the ancient city of Shattrath, which has become a '
                    'refuge for those who have turned away from demons and war. But outside the '
                    'city, the forest is far from safe. Arakkoa wield ancient magic, cultists work '
                    'for mysterious powers, and fallen draenei are trying to regain their '
                    "influence. Stonebreaker Hold serves as the Horde's stronghold in Terokkar "
                    'Forest. Here, Horde forces find themselves drawn into confrontation with the '
                    'Arakkoa, the fallen draenei and other inhabitants of the region. However, the '
                    'main mystery concerns Auchindoun — an ancient complex where, after the '
                    'destruction of the draenei, numerous souls ended up imprisoned. The Horde '
                    'cannot allow these forces to spread unchecked across Terokkar. At the same '
                    'time, it must support its allies and defend its own garrison against those '
                    'who seek to use the ancient ruins for their own ends.'},
  'required_tier': 8},
 {'name': 'Nagrand',
  'min_level': 64,
  'max_level': 66,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Nagrand is one of the few corners of Outland where green meadows, clean '
                       'rivers and relatively untouched nature have survived. For the Draenei, '
                       'this land is especially important: their settlements and the memory of the '
                       'world before the catastrophe have been preserved here. Telaar has become '
                       "the Alliance's stronghold, but the peace of the region is constantly "
                       "disrupted by ogres, the Mag'har and other forces. Some orcs are trying to "
                       'rebuild a peaceful life, yet war and old conflicts continue to haunt them. '
                       'The Alliance has to protect the locals while also helping those who are '
                       'trying to preserve what remains of the old Nagrand.',
           'Horde': 'Nagrand is one of the few corners of Outland where green meadows, clean '
                    'rivers and relatively untouched nature have survived. Garadar is the home of '
                    "the Mag'har, orcs who never drank demon blood and have preserved the "
                    'traditions of their people. For the Horde, their existence is enormously '
                    "significant: it is a chance to learn the truth about the orcs' past and to "
                    'restore ties with those who did not succumb to the influence of the Burning '
                    "Legion. However, the Mag'har are surrounded by enemies — from hostile ogres "
                    "to members of other peoples laying claim to Nagrand. The Horde's presence "
                    "here is primarily about protecting the Mag'har and preserving the orcs' "
                    'heritage, not simply about seizing territory.'},
  'required_tier': 8},
 {'name': "Blade's Edge Mountains",
  'min_level': 65,
  'max_level': 67,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': "The Blade's Edge Mountains are a harsh land of gigantic cliffs where "
                       'ancient dragons, ogres and gronns hold sway over the local lands. The '
                       'Alliance has established itself at Sylvanaar, trying to help the night '
                       'elves and other allies survive amid these dangers. Especially troubling is '
                       'the activity of Gruul the Dragonkiller and his ogres, who have turned the '
                       'region into their own fiefdom. Local settlements are constantly under '
                       'threat, and the appearance of new draconic forces could upset the fragile '
                       'balance of Outland even further.',
           'Horde': "The Blade's Edge Mountains are a harsh land of gigantic cliffs where ancient "
                    'dragons, ogres and gronns hold sway over the local lands. Thunderlord '
                    "Stronghold and Mok'Nathal Village maintain the Horde's presence in the "
                    "Blade's Edge Mountains, where the local orcs are trying to survive among the "
                    'gronns and their minions. Gruul the Dragonkiller has turned many lands into a '
                    'territory of fear, and his sons and ogres hunt down those who dare to resist. '
                    'The Horde has to support its own settlements and help the local orc clans. '
                    'Their struggle here is closely tied to freeing their people from the '
                    'creatures that have kept them in fear for centuries.'},
  'required_tier': 8},
 {'name': 'Netherstorm',
  'min_level': 66,
  'max_level': 69,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Netherstorm is one of the most mutilated regions of Outland. Huge chunks '
                       'of land have literally been split apart and float in the Nether, while '
                       'magical anomalies make travel deadly. The Alliance has established itself '
                       'at Area 52 and other camps, trying to deal with the activities of the '
                       "Consortium, the Burning Legion and especially Prince Kael'thas Sunstrider. "
                       "The Blood elves who served him use Outland's magical energy to create ever "
                       'more dangerous devices. Behind all this lie experiments that could have '
                       'consequences far beyond Netherstorm.',
           'Horde': 'Netherstorm is one of the most mutilated regions of Outland. Huge chunks of '
                    'land have literally been split apart and float in the Nether, while magical '
                    'anomalies make travel deadly. For the Horde, Netherstorm represents an '
                    'extremely serious threat. The traitorous Blood elves who left Silvermoon and '
                    "refused to become part of the Horde, joining Kael'thas instead, have become "
                    "part of the forces that seek to use Outland's magic for their own purposes. "
                    'Horde forces operate out of Area 52 and other settlements, simultaneously '
                    "facing demons, ethereals and the region's unstable magic. For Blood elves, "
                    "dealing with Kael'thas's betrayal is especially important: the one who once "
                    'promised his people salvation now serves forces capable of destroying '
                    'Azeroth. The local forces need help to stop his plans.'},
  'required_tier': 8},
 {'name': 'Shadowmoon Valley',
  'min_level': 66,
  'max_level': 69,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Shadowmoon Valley is a grim land where almost nothing remains of the '
                       'Draenor of old. The remains of the Black Temple stand here, and the sky is '
                       'perpetually covered by dark clouds. Alliance forces have entrenched '
                       'themselves at Wildhammer Stronghold and are trying to deal with the '
                       'Illidari, the Burning Legion and corrupted orcs. The Black Temple poses a '
                       'special danger: there Illidan Stormrage has gathered a huge army and '
                       'turned the ancient fortress into the center of his power. The events in '
                       'Shadowmoon Valley could affect the fate of all Outland.',
           'Horde': 'Shadowmoon Valley is a grim land where almost nothing remains of the Draenor '
                    'of old. The remains of the Black Temple stand here, and the sky is '
                    'perpetually covered by dark clouds. For the Horde, Shadowmoon Valley holds '
                    'special significance because of the history of the orcs. It was here that one '
                    'of the most important lands of old orcish culture once lay, and now the '
                    "region has become the center of Illidan's power. Horde forces use Shadowmoon "
                    'Village as a stronghold and help the local orcs stand against their enemies. '
                    'Among these orcs are both those who have kept faith with the old traditions '
                    'and those who were enslaved by demonic forces. Meanwhile, the Black Temple is '
                    "becoming an ever more powerful center of the Illidari, and Illidan's plans "
                    'threaten not only his enemies but all of Outland.'},
  'required_tier': 8},
 {'name': 'Howling Fjord',
  'min_level': 68,
  'max_level': 72,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Howling Fjord is the first land of Northrend that many Alliance forces '
                       'encounter after landing on the continent. Valgarde becomes their main '
                       'stronghold, but war rages all around it. The Vrykul, an ancient race of '
                       'warriors, have awakened after a long slumber and begun attacking humans. '
                       'At the same time, the Scourge is spreading its influence, and Horde forces '
                       'are trying to gain a foothold on the peninsula. For the Alliance, Valgarde '
                       'is not just a military base: it is a settlement of people who find '
                       'themselves in the very heart of a hostile continent, where every day the '
                       'expedition has to be defended against superior forces. To get here, take '
                       'the ship from Menethil Harbor in the Wetlands.',
           'Horde': 'For the Horde, Howling Fjord becomes one of its first beachheads in '
                    'Northrend. New Agamand allows the Forsaken to establish themselves far from '
                    'Undercity and continue the fight against the Scourge. However, the vrykul '
                    'pose an enormous threat: these ancient warriors are hostile toward newcomers, '
                    'and the Scourge has already penetrated deep into the region. At the same '
                    'time, the Alliance is trying to build settlements of its own and drive out '
                    'the Horde Expedition. The Horde has to protect its people in a harsh land '
                    'where danger comes from several directions at once. To get here, take the '
                    'zeppelin near Undercity in Tirisfal Glades.'},
  'required_tier': 13},
 {'name': 'Borean Tundra',
  'min_level': 68,
  'max_level': 72,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Borean Tundra is a vast icy plain in the southwest of Northrend, where the '
                       'Alliance has built Valiance Keep. The expedition is trying to gain a '
                       'foothold on the new continent and, at the same time, investigate the '
                       'mysterious events around the region. Active here are naga, blue dragons, '
                       'the Scourge and hostile tuskarr tribes. Especially alarming are the '
                       "Scourge's activity and the strange events in Coldarra, where Malygos and "
                       'his dragonflight are pursuing their own plans. The Alliance Expedition has '
                       'found itself far from its homelands and needs to strengthen its positions. '
                       'To get here, take the ship in Stormwind.',
           'Horde': "Warsong Hold becomes the Horde's main stronghold in Borean Tundra. Here orcs, "
                    'tauren, Forsaken, blood elves and other members of the Horde Expedition are '
                    'trying to gain a foothold among the icy wastes. However, they have to stand '
                    'against the Scourge, the naga, the blue dragons and other forces. Coldarra is '
                    "especially dangerous, as there Malygos has begun interfering with mortals' "
                    'use of magic. The Horde is intent on keeping its presence in Northrend and on '
                    'not letting its enemies turn Borean Tundra into a staging ground against its '
                    'troops. To get here, take the zeppelin near Orgrimmar.'},
  'required_tier': 13},
 {'name': 'Dragonblight',
  'min_level': 71,
  'max_level': 73,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Dragonblight is the ancient heart of the dragon world, where the remains '
                       'of countless dragons lie beneath the snow. Wyrmrest Temple towers over the '
                       'plains as the place where the dragonflights are trying to unite in the '
                       'face of a common threat. But the region is torn apart by wars: the Scourge '
                       'is advancing, Azjol-Nerub hides armies of nerubians, and the Horde is '
                       'trying to drive the Alliance out of the region. Wintergarde Keep becomes '
                       "the Alliance's forward post. The threat at the Wrath Gate is especially "
                       'dangerous, as the Scourge is preparing new plans against the living there.',
           'Horde': 'Dragonblight is the ancient heart of the dragon world, where the remains of '
                    'countless dragons lie beneath the snow. For the Horde, Dragonblight has '
                    'strategic importance: the most important routes to the northern lands run '
                    "through it, and it holds many ancient secrets. Agmar's Hammer and other "
                    'settlements support the advance of the Horde Expedition while the Scourge '
                    'penetrates ever deeper into the region. Wyrmrest Temple unites the '
                    'dragonflights in the face of a common threat, and the conflict around the '
                    'Wrath Gate is becoming one of the most important events of the war against '
                    'the Lich King. The Horde has to support its allies, defend its positions and '
                    'stand against the Scourge all at the same time.'},
  'required_tier': 13},
 {'name': 'Grizzly Hills',
  'min_level': 73,
  'max_level': 74,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Grizzly Hills is an ancient forest that is the homeland of the furbolgs. '
                       'Amberpine Lodge is located here, where the Alliance supports the local '
                       'inhabitants and tries to deal with numerous threats. The Venture Company '
                       'is ruthlessly cutting down the forest, upsetting the natural balance, '
                       'while the Drakkari trolls and the Scourge are advancing from the north. In '
                       'addition, the Wolfcult, linked to the return of Arugal, is active in the '
                       'region. For the Alliance, defending Grizzly Hills means not only '
                       'preserving its own settlement but also helping peoples whose ancient '
                       'homeland has come under threat from several enemies at once.',
           'Horde': 'Grizzly Hills is an ancient forest that is the homeland of the furbolgs. '
                    "Conquest Hold becomes the Horde's main stronghold in Grizzly Hills. Members "
                    'of the Horde find themselves among ancient forests where the furbolgs are '
                    'trying to preserve their homeland, the Venture Company is destroying the '
                    'forest for profit, and the Drakkari and the Scourge threaten from the north. '
                    'The Horde is intent on preserving its own settlements and supporting its '
                    'allies, but the territory itself keeps turning into a battlefield. The '
                    "Scourge's approach from Drak'Tharon Keep, a fortress that has become a "
                    'bastion of the undead, is especially dangerous.'},
  'required_tier': 13},
 {'name': "Zul'Drak",
  'min_level': 74,
  'max_level': 76,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': "Zul'Drak is the ancient kingdom of the Drakkari trolls, which has found "
                       'itself on the brink of destruction. The desperate trolls have begun '
                       'sacrificing their own Loa, trying to gain enough power for the war against '
                       'the Scourge. But these rituals are gradually turning the trolls themselves '
                       'into monsters. The Argent Stand becomes the stronghold from which Alliance '
                       'forces try to get to the bottom of what is happening. At the same time, '
                       'the Scourge is seizing more and more territory, and the ancient troll '
                       'temples are becoming sources of new threats.',
           'Horde': "Zul'Drak is the ancient kingdom of the Drakkari trolls, which has found "
                    "itself on the brink of destruction. For the Horde, Zul'Drak is a complicated "
                    'problem. The Drakkari are an ancient troll people, related to the trolls who '
                    'are part of the Horde, but their desperate war against the Scourge has led '
                    'them to terrible sacrifices. Now even their own Loa are becoming victims of '
                    "their drive to survive. The Horde is gaining a foothold in Zul'Drak and "
                    'trying to understand whether the region can be saved from utter destruction. '
                    'Meanwhile, the Scourge is using the chaos among the Drakkari to push its '
                    'advance further.'},
  'required_tier': 13},
 {'name': 'Sholazar Basin',
  'min_level': 75,
  'max_level': 77,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Sholazar Basin looks almost like a piece of the ancient world that has '
                       'survived amid icy Northrend. Dinosaurs, primeval forests and mysterious '
                       'titan structures make the region utterly unlike the rest of the continent. '
                       'But behind the beauty lies the struggle between the Frenzyheart and the '
                       'Oracles, as well as the activity of powerful beings tied to ancient '
                       'secrets. Nesingwary Base Camp draws hunters and explorers, while scholars '
                       'try to understand the origin of the unusual ecosystem. For the Alliance, '
                       'this is an opportunity to explore one of the last untouched areas of '
                       'Northrend and to keep dangerous forces from seizing its secrets, as well '
                       'as to save the wondrous nature of this place from ruthless logging by the '
                       'Horde.',
           'Horde': 'Sholazar Basin looks almost like a piece of the ancient world that has '
                    'survived amid icy Northrend. Dinosaurs, primeval forests and mysterious titan '
                    'structures make the region utterly unlike the rest of the continent. '
                    'Nesingwary Base Camp becomes the center of expeditions, and the local '
                    'conflicts between the Frenzyheart and the Oracles gradually draw outsiders '
                    'into the war. But the main danger lies deeper: the secrets of Sholazar are '
                    'tied to ancient powers that may matter far beyond the region itself. That is '
                    'why the explorers of the Horde Expedition face tasks that go far beyond the '
                    'usual search for resources.'},
  'required_tier': 13},
 {'name': 'The Storm Peaks',
  'min_level': 76,
  'max_level': 79,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': 'Storm Peaks is a range of harsh mountains holding ancient titan complexes '
                       'and one of the greatest cities of Northrend: Ulduar. The Alliance '
                       'Expedition has established itself at Frosthold together with Wildhammer '
                       'dwarves, investigating the origins of the titans and the strange events in '
                       'the mountains. But Ulduar has turned out to be no abandoned relic: '
                       'Yogg-Saron is at work inside it, and Loken has subjugated many of the '
                       'keepers. Gnomes and explorers face a threat capable of affecting the very '
                       'structure of the world. For the Alliance, defending Frosthold is only part '
                       'of a far larger struggle.',
           'Horde': 'Storm Peaks is a range of harsh mountains holding ancient titan complexes and '
                    'one of the greatest cities of Northrend: Ulduar. The Horde Expedition is '
                    "based around the wreckage of the crashed airship Grom'arsh, and is also "
                    'setting up other strongholds among the mountains of Storm Peaks. Here members '
                    'of the Horde come up against ancient titan structures, iron dwarves and '
                    "forces tied to Ulduar. The deeper the explorers delve into the region's "
                    'history, the clearer it becomes that something far more dangerous than an '
                    'ordinary army lies hidden beneath the mountains. Loken and Yogg-Saron '
                    'threaten every living creature in Northrend, so even the traditional rivalry '
                    'between the Horde and the Alliance gives way before this threat.'},
  'required_tier': 13},
 {'name': 'Icecrown',
  'min_level': 77,
  'max_level': 79,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'text': {'Alliance': "Icecrown is the heart of the Lich King's domain and the final goal of the "
                       'campaign against the Scourge. The icy fortress of Icecrown Citadel towers '
                       'over the endless wasteland, and from it Arthas Menethil directs his undead '
                       'armies. The Alliance creates the Argent Vanguard and strengthens its '
                       "positions through Crusaders' Pinnacle, preparing for the decisive "
                       'offensive. There is almost no room for ordinary life here: the Scourge '
                       'constantly replenishes its armies, and every step forward comes at the '
                       'cost of huge losses. In Icecrown the fate of Northrend, and perhaps of all '
                       'Azeroth, is being decided.',
           'Horde': "Icecrown is the heart of the Lich King's domain and the final goal of the "
                    'campaign against the Scourge. The icy fortress of Icecrown Citadel towers '
                    'over the endless wasteland, and from it Arthas Menethil directs his undead '
                    'armies. For the Horde, Icecrown becomes the last and most dangerous stage of '
                    'the war against the Lich King. The Horde Expedition and the Argent Crusade '
                    'are establishing themselves in the region, gradually closing in on Icecrown '
                    "Citadel. The Horde's troops understand that the enemy here far surpasses "
                    'ordinary foes: the land itself is filled with undead, and the Scourge has '
                    'practically inexhaustible armies at its disposal. Garrosh and the other '
                    'leaders of the Horde Expedition are determined not to let the Lich King '
                    'continue his advance. In Icecrown it is no longer possible to speak only of a '
                    "struggle for influence: what is at stake is the survival of Azeroth's living "
                    'beings.'},
  'required_tier': 13}]

REGION_RUMORS = [{'name': 'Darkshore',
  'min_level': 5,
  'max_level': 12,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'rumors': ['They say that in the night forests of Darkshore, ghostly lights are sometimes seen '
             'that lead travelers far from the road.',
             'Old fishermen swear that singing rises from the depths off the shore, even though '
             'there is not a single living soul out there.',
             'Somewhere among the ruins on the coast, the treasures of an ancient people are '
             'supposedly hidden, and the sea still washes them ashore from time to time.',
             'Rumor has it that deep in the forest there are places where the trees grow far too '
             'quickly, as if someone were forcing the forest itself to move.',
             'Some travelers claim to have seen huge footprints on the shore that no creature they '
             'know of could have left.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Loch Modan',
  'min_level': 5,
  'max_level': 12,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'rumors': ['They say that beneath the lake in Loch Modan there are old tunnels that run far '
             'deeper than the maps show.',
             'Miners tell of a strange rumbling from deep within the mountains — as if someone '
             'underground were still digging.',
             'Rumor has it that the forgotten treasures of the first mountain kings can be found '
             'in the ancient tunnels.',
             'Some hunters insist that a beast lives in the mountains that no one has ever managed '
             'to corner.',
             'They say that if you stand by the dam long enough at night, you can hear the voices '
             'of those who died building it.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Westfall',
  'min_level': 5,
  'max_level': 12,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'rumors': ['They say there is still gold left in the old mines of Westfall that no one ever '
             'managed to haul away.',
             'Some farmers claim that at night little lights appear on the empty fields — as if '
             'someone were walking between the abandoned farms with a lantern.',
             'There is talk of secret bandit camps that hide their loot in the old cellars of '
             'burned-down houses.',
             'Sailors say that the wreckage of ships is sometimes found off the coast, and those '
             'ships were not among the ones recently lost.',
             'Sailors say that the wreckage of ships is sometimes found off the coast bearing '
             'identifying marks that belong to no nation of Azeroth.',
             'They say there is a place somewhere in Westfall with such a view of the sea that it '
             'is worth crossing the whole valley just to see it.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Bloodmyst Isle',
  'min_level': 5,
  'max_level': 12,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'rumors': ['They say the red haze of Bloodmyst has a strange, acrid smell, and whoever breathes '
             "it for too long starts coughing and seeing things that aren't there.",
             "Rumor has it that in the island's forests there are plants that change shape after "
             'sunset.',
             'Fishermen tell of strange creatures that can be seen underwater only at night.',
             'Some travelers claim that the crystals on the island sometimes begin to glow all at '
             'once, in rhythm.',
             'They say that deep in the island there are places where the fallen crystals have '
             'changed the local animals beyond recognition.',
             "There is talk of lost ruins built long before the island's current inhabitants "
             'appeared.',
             'Hunters tell of creatures that look as if nature itself were trying to push them out '
             'of this world.',
             'They say a strange blue glow sometimes appears over the island at night.',
             'Some sailors claim to have seen a huge shadow in the fog, far offshore.',
             'Rumor has it that the strangest crystals on the island can be heard before they are '
             'seen.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Silverpine Forest',
  'min_level': 5,
  'max_level': 12,
  'expansion': 'classic',
  'factions': ('Horde',),
  'rumors': ['Travelers say that in the fog of Silverpine a road sometimes appears that is not on '
             'any map.',
             'They say that some travelers who lost their way came back out of the forest several '
             'days later, even though they were sure they had spent only a few hours there.',
             'Near the old ruins, figures supposedly appear at night and vanish as soon as you '
             'draw near.',
             'Rumor has it that there are graves in the forest from which no one was ever meant to '
             'climb out.',
             'The old folk advise you not to answer if at night you hear someone calling your name '
             'from behind the trees.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'The Barrens',
  'min_level': 5,
  'max_level': 12,
  'expansion': 'classic',
  'factions': ('Horde',),
  'rumors': ['They say that on the endless plains of The Barrens you can walk in a straight line '
             'for days and still not meet a soul.',
             'Caravan drivers tell of forgotten oases that are not on any map.',
             'Rumor has it that somewhere in the savanna lie the ruins of an ancient city buried '
             'under the earth.',
             'Hunters insist that deep in the Barrens roam huge beasts, far larger than the ones '
             'found near the roads.',
             'Some travelers tell of strange lights at night far beyond the known settlements.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Ghostlands',
  'min_level': 5,
  'max_level': 12,
  'expansion': 'classic',
  'factions': ('Horde',),
  'rumors': ['They say there are villages in Ghostlands where the houses look as if their '
             'inhabitants left only a few hours ago.',
             'Rumor has it that among the dead forests there are still places where living flowers '
             'grow.',
             'Old travelers tell of wells from which whispers rise at night.',
             'Some hunters claim that a pale figure appears in the forest; it never comes closer, '
             'yet it is always somewhere ahead of the traveler.',
             'They say that in the old ruins there are still chests that no one dares to open.',
             'Rumor has it that somewhere in Ghostlands lies a forgotten tomb full of ancient '
             'artifacts.',
             'They say that the fog in Ghostlands sometimes moves against the wind.',
             'The old folk tell of a tree that is covered in white blossoms every night, and by '
             'morning is dead again.',
             'Travelers whisper that sometimes on the roads you meet the ghosts of high elves who '
             'do not know that they are dead.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Redridge Mountains',
  'min_level': 11,
  'max_level': 17,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'rumors': ['They say there are caves in the mountains whose walls are covered with ancient '
             'drawings of unknown origin.',
             'Old miners tell of deposits of rare ore so rich that a single vein could make a '
             'whole family wealthy.',
             'Rumor has it that an old hideout, left behind by a long-vanished orc clan, lies '
             'hidden in the mountains.',
             'Hunters tell of a giant beast that appears only during thunderstorms.',
             'They say some of the lakes of Redridge are so deep that no one has ever reached the '
             'bottom.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Stonetalon Mountains',
  'min_level': 11,
  'max_level': 17,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say there are places in Stonetalon where the stones change shape all by '
             'themselves.',
             'Druids tell of ancient groves that still remember the days when these mountains were '
             'covered by a far denser forest.',
             'There is talk of a cave where the air inside is so cold that torches go out on their '
             'own.',
             'Some travelers claim to have seen huge silhouettes in the mountains, moving right '
             'along the sheer cliff faces.',
             'They say that if you find the right trail, you can reach a place where a spring of '
             'the purest water gushes from the ground. The water has a faint fruity taste, and no '
             'one knows why.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Ashenvale',
  'min_level': 11,
  'max_level': 17,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that deep in Ashenvale there are still trails that the ancient elves used '
             'long before the current settlements appeared.',
             'Hunters tell of a white stag that never lets anyone come near, yet sometimes seems '
             'to lead travelers into the forest on purpose. Those who follow it do not come back.',
             'Rumor has it that the ruins of an ancient city, almost entirely swallowed by the '
             'forest, lie hidden among the trees.',
             'Some travelers have heard the sound of a horn at night where there was no camp at '
             'all.',
             'They say there are trees that have been growing for so long that things left behind '
             'long before the current wars lie hidden beneath their roots.',
             'They say that in the forest you can find white stones as tall as a man, on which '
             'someone carved words in an unknown language many thousands of years ago.',
             'They say that in the depths of the forest there are strange ruins made of bright red '
             'stone. If you put your ear to them, you can hear a scream inside the stone.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Duskwood',
  'min_level': 11,
  'max_level': 17,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'rumors': ['They say the fog of Duskwood rolls in even in clear weather, and sometimes it '
             'gathers around one single traveler.',
             'Old-timers tell of abandoned houses where candles light themselves at night.',
             'Rumor has it that somewhere among the graveyards there is a grave that can never be '
             'found twice.',
             'Some hunters claim that in the forest you can come across a huge black beast that '
             'leaves no tracks.',
             'They say that if you spend a night alone in the thick of Duskwood, by morning you '
             "may hear footsteps around your camp. But you won't find what is making them."],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Hillsbrad Foothills',
  'min_level': 12,
  'max_level': 19,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say old barrows lie hidden in the hills, far older than the local settlements.',
             'Farmers tell of strange lights that sometimes move across the fields after dark.',
             'Rumor has it that in the mountains there are abandoned mines with the richest silver '
             'deposits.',
             'Some wanderers claim to know a shortcut through the hills, but each of them '
             'describes it differently.',
             'They say the old ruins in Hillsbrad hold a secret that several generations have '
             'tried to unravel.',
             'A peasant told how his dog died and he buried it, and the very next night it came '
             'back home.',
             'They say that sometimes at night people on the roads meet a caravan heading for '
             'Alterac, even though that kingdom was burned to the ground decades ago'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Wetlands',
  'min_level': 12,
  'max_level': 19,
  'expansion': 'classic',
  'factions': ('Alliance',),
  'rumors': ['Sailors tell of shipwrecks after which the cargo was found deep in the marshes, even '
             'though the sea lies in quite the opposite direction.',
             'They say the ruins of an ancient fortress, long since swallowed by the water, lie '
             'hidden among the marshes.',
             'There is talk of caves where you can find traces of a long-vanished people.',
             'Hunters insist that the deepest waters are home to creatures that have never been '
             'seen near the shore.',
             'Some travelers tell of an old stone bridge that appears only when the water recedes.',
             'They say that when the water recedes, you can see the roof of an unknown castle '
             'sticking out of the mud in one of the marshes.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Thousand Needles',
  'min_level': 17,
  'max_level': 24,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that between the stone needles of Thousand Needles there are gorges where '
             'sunlight never reaches.',
             'Caravan drivers tell of lost campsites where the supplies of long-vanished travelers '
             'still lie.',
             'Rumor has it that some of the huge stone spires are hollow inside.',
             'Hunters tell of a creature that can climb the sheer walls of the canyons.',
             'They say that if you climb the highest of the needles, you can see lands that lie '
             'beyond the ordinary horizon.',
             'They say that if you climb the highest of the needles, you can see the sun even in '
             'the middle of the night.',
             'They say that sometimes, even in the driest parts of the region, travelers catch the '
             'smell of salt water.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Arathi Highlands',
  'min_level': 24,
  'max_level': 30,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say ancient stones still stand in Arathi, raised long before the current '
             'kingdoms appeared.',
             'Travelers tell of abandoned towers from which the whole valley could once be '
             'watched.',
             'Rumor has it that the weapons of ancient warriors are hidden in the old ruins.',
             'Hunters claim that the rarest of beasts can be found in the highlands.',
             'Some wanderers tell of an old road that leads to a place missing from modern maps.',
             'They say that in Arathi there are ruins of old internment camps for orcs, where they '
             "were held after the Horde's defeat in the Second War. After sunset you can hear in "
             'them the screams of orc prisoners being tortured by cruel overseers',
             'They say that in Arathi there are mass graves where orcs from the internment camps '
             "were buried, the camps where they were held after the Horde's defeat in the Second "
             'War. Most of them died of hunger, disease and torture at the hands of the overseers, '
             'so at night near these graves you can meet the ghosts of gaunt, maimed orcs.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Alterac Mountains',
  'min_level': 24,
  'max_level': 30,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the treasures of the old rulers are still hidden among the snows and ruins '
             'of Alterac.',
             'Rumor has it that sealed rooms that survived the war untouched are sometimes found '
             'in the ruined fortresses.',
             'Some hunters tell of ghosts that appear near the old roads after sunset.',
             'They say there are secret passages in the mountains that royal messengers once used.',
             "Old treasure hunters insist that Alterac's treasures have not all been found — far "
             'from it.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Desolace',
  'min_level': 24,
  'max_level': 30,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say Desolace was not always a barren land — dense forests once stood here.',
             'Druids say that in some places the land is still trying to win back its former life.',
             'There is talk of ancient ruins buried under the gray soil.',
             'Travelers tell of strange stones that glow at night after rain.',
             'Some old folk insist that far out in the wastes you can find a place where the grass '
             'never dies.',
             'They say that far out in the wastes you can find the colossal bones of unknown '
             'animals the size of an entire city. There is no record that such enormous animals '
             'ever existed'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Stranglethorn Vale',
  'min_level': 24,
  'max_level': 30,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['Sailors claim that somewhere in the jungle lies the hidden hoard of a famous pirate '
             'who never came back for it.',
             'They say the ancient ruins in the jungle hold gold that is thousands of years old.',
             'There is talk of lost temples where dead trolls still perform strange rituals.',
             'Hunters tell of the rarest beasts, which cannot be found anywhere else in Azeroth.',
             'Some captains insist that along the coast there are caves leading far underground.',
             'They say that underwater, not far from the shore, lies an entire sunken ancient '
             'city.',
             'They say that somewhere in the jungle there is a chest overgrown with grass, full of '
             'gold coins. But whoever takes even a single coin will be cursed and turned into a '
             'wild animal.',
             'They say that a strange ship of unknown design recently wrecked off the coast. On '
             'board were found the bodies of unknown creatures, fat and covered in fur.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Badlands',
  'min_level': 29,
  'max_level': 35,
  'expansion': 'classic',
  'factions': ('Horde',),
  'rumors': ['Miners say that in the Badlands there are ore deposits that could make any lucky '
             'prospector rich.',
             'They say ancient mechanisms are hidden among the rocks, and no one can explain where '
             'they came from.',
             'There is talk of an old laboratory, abandoned along with all of its experiments.',
             'Some travelers claim that at night the stone figures in the desert change position.',
             'Old treasure hunters insist that somewhere around here lies a treasure that several '
             'generations have searched for.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Dustwallow Marsh',
  'min_level': 29,
  'max_level': 35,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that in the foggy marshes you can stumble upon ruins older than most of the '
             'settlements here.',
             'Fishermen tell of gigantic creatures moving beneath the surface of the water.',
             'Rumor has it that some of the islets of Dustwallow appear only at certain times of '
             'the year.',
             'Hunters claim that the deepest bogs are home to creatures that cannot be seen by '
             'day.',
             'They say that among the marshes you can find old chests holding the cargo of ships '
             'that were lost far out at sea.',
             'They say a farmer found a bottle of strange wine with no label in the water. He '
             'drank it, and a few hours later he died in a terrible delirium.',
             'They say that some creatures deep in the marshes can imitate a cry for help to lure '
             'trusting travelers.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Swamp of Sorrows',
  'min_level': 29,
  'max_level': 35,
  'expansion': 'classic',
  'factions': ('Horde',),
  'rumors': ['They say the fog of the Swamp of Sorrows hides entire ruins that cannot be seen from '
             'the road.',
             'Rumor has it that some of the plants here can shoot up in a single night.',
             'Hunters tell of monsters that live in the deepest waters of the swamp.',
             'Travelers claim that they sometimes hear the tolling of a bell far from any '
             'settlement.',
             'They say the old temples among the swamps keep secrets far older than the current '
             'conflicts.',
             'They say poisonous plants grow there with thorns that can pierce any boot if you '
             'step on them.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Feralas',
  'min_level': 35,
  'max_level': 40,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the ruins of an ancient civilization lie hidden in the jungles of Feralas.',
             'Hunters tell of creatures so rare that some believe them to be extinct.',
             'Rumor has it that deep in the forest there is an ancient grove that chance travelers '
             'almost never see.',
             'Old travelers claim that some of the ruins of Feralas reach far underground.',
             'They say that in one of the caves you can find traces of an ancient ritual that no '
             'one is able to explain.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'The Hinterlands',
  'min_level': 35,
  'max_level': 40,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that in The Hinterlands there are ancient ruins left by a people who '
             'vanished long before the current wars.',
             'Hunters tell of the rarest birds and beasts, which cannot be found anywhere else.',
             'Rumor has it that old treasures, guarded by unliving sentinels, are hidden in the '
             'mountains.',
             'Some travelers claim that ancient stone circles can be found in the forests.',
             'They say that at night a green glow sometimes appears above the high peaks.',
             'Some claim to have seen a gigantic spider in the forest, as big as an entire lake.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Tanaris',
  'min_level': 35,
  'max_level': 40,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['Caravan drivers tell of cities buried beneath the sands that are sometimes uncovered '
             'after strong storms.',
             'They say a pirate treasure is hidden somewhere in the desert, big enough to buy an '
             'entire city.',
             'Rumor has it that deep in Tanaris one can find ancient mechanisms left behind by '
             'unknown craftsmen.',
             'Travelers tell of strange time anomalies near some of the ruins.',
             'Old cartographers insist that every year the sands uncover new parts of a '
             'long-forgotten city.',
             'They say someone recently met a man in the desert who claimed he lived in Lordaeron '
             'and did not know it had been destroyed many years ago.',
             'They say that in the desert you sometimes come across lost people who have no idea '
             'how they got there.',
             'Someone saw a man in the desert who looked exactly as he had forty years ago. He '
             'asked the way to a city that no longer exists'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Searing Gorge',
  'min_level': 39,
  'max_level': 45,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['Miners say that deep beneath Searing Gorge there are mines where the ore literally '
             'glows from within.',
             'They say the heat here grows stronger the closer you get to the old tunnels.',
             'There is talk of an underground road connecting the far reaches of the mountains.',
             'Some adventurers claim to have found ancient metal objects of unknown origin in the '
             'caves.',
             'They say that in the deepest mines you can hear the strike of pickaxes, though there '
             'is not a single miner nearby.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Azshara',
  'min_level': 39,
  'max_level': 45,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the shores of Azshara hold the ruins of an ancient age, when these lands '
             'looked completely different.',
             'Rumor has it there are sunken palaces that can sometimes be seen beneath the water '
             'in clear weather.',
             'Fishermen tell of unusual creatures living far offshore.',
             'Some wanderers claim to have found ancient magical artifacts on the coast.',
             'They say that deep in Azshara there are places where even the wind seems utterly '
             'still.',
             'Sometimes the ghost of a beautiful night elf woman is seen in the forest. But '
             'whoever followed her never came back.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Blasted Lands',
  'min_level': 39,
  'max_level': 45,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the earth of the Blasted Lands was scarred not by a single war, but by '
             'something far more ancient.',
             'Rumor has it there is a portal through which an army from another world once came.',
             'Some travelers say that at night in the wastes you can see the silhouettes of '
             'creatures that are not there by day.',
             'Old mages insist that traces of powerful magic still linger here.',
             'They say that amid the scorched earth you can find places where grass suddenly grows '
             'as if the catastrophe had never happened.',
             'They say that in the mountains you can find the sites of strange rituals, with the '
             'charred bodies of unknown people.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Felwood',
  'min_level': 43,
  'max_level': 48,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say Felwood was once one of the most beautiful forests in Kalimdor.',
             'Rumor has it that some trees here remember what happened to the forest long before '
             'the present generation.',
             'Hunters tell of animals changed so much that they are hard to recognize.',
             'Druids insist that small patches of untouched nature still survive amid the '
             'corrupted forest.',
             'They say some springs in Felwood can both heal and harm — depending on who touches '
             'them.',
             'They say some of the trees here have voices, and they beg for help.',
             'They say an elf once decided to bathe in a lake and dissolved in it.',
             'They say there is one tree that is untouched by the corruption. On its bark someone '
             'carved the names of people who lived long before the present age'],
  'general_region': None,
  'required_tier': 0},
 {'name': "Un'Goro Crater",
  'min_level': 43,
  'max_level': 48,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ["Hunters say that giant ancient beasts roam Un'Goro.",
             'They say some plants here grow so fast that you can watch them change before your '
             'very eyes.',
             'Rumor has it that ruins of unknown origin are hidden in the center of the crater.',
             'Scholars argue over why life here has remained so unusual and ancient.',
             'Travelers tell of places where the ground suddenly starts to shake underfoot.',
             'They say the silhouette of an enormous woman as tall as a three-story house has been '
             'seen in the jungle.',
             'A hunter swore he had found the egg of a creature that should have died out '
             'thousands of years ago. By morning the egg was gone'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Burning Steppes',
  'min_level': 45,
  'max_level': 50,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that above the Burning Steppes, even at night, you can see a red glow from '
             'a fire burning deep within the mountains.',
             'Rumor has it that beneath the ground here lie vast halls built long before the '
             'present fortresses.',
             'Travelers tell of old roads leading straight to the heart of the mountains.',
             'Some hunters claim that in the ash you can find things that were thought destroyed '
             'many years ago.',
             'They say the mountains hide traces of an ancient people who tried to bend fire '
             'itself to their will.',
             'A miner found a door deep underground. Someone on the other side knocked three '
             'times. He never went back there'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Western Plaguelands',
  'min_level': 46,
  'max_level': 51,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say some farms in the Western Plaguelands look as if their inhabitants left '
             'only a few days ago.',
             'There is talk of old graveyards where the graves open by themselves.',
             'Travelers say that at night processions appear on the roads and vanish with the '
             'first rays of the sun.',
             'Hunters insist that animals that have not succumbed to the corruption can still be '
             'found in the infected forests.',
             'Some wanderers claim to have heard bells ringing at night where no church has stood '
             'for a long time.',
             'They say some ruined villages still hold untouched houses with the belongings of '
             'their former residents.',
             'They say human figures wander the forests there, begging for help. From afar they '
             'look like ordinary people, but if you come close, they turn out to be rotting '
             'corpses.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Eastern Plaguelands',
  'min_level': 47,
  'max_level': 53,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the Eastern Plaguelands hold the ruins of one of the most dreadful cities '
             'of Lordaeron.',
             'Rumor has it there are chapels and crypts where candles still burn, though there is '
             'no one left to tend them.',
             'Travelers tell of roads where you can sometimes hear bells ringing from '
             'long-destroyed settlements.',
             'Old soldiers insist that some places here are so contaminated that the very earth '
             'seems dead.',
             'They say that deep in the plaguelands you can find relics that survived the fall of '
             'an entire kingdom.',
             'They say a wind sometimes blows here from the north with a strange, sweet smell. You '
             'must not breathe it, because it carries the plague.',
             'An old pilgrim claims he saw the city before it perished. According to him, its '
             'people still walked the streets, but none of them cast a shadow'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Winterspring',
  'min_level': 47,
  'max_level': 53,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the snow of Winterspring never melts, even in summer.',
             'Hunters tell of giant white beasts that are hardly afraid of people at all.',
             'There is talk of ancient ruins hidden beneath the snow and ice.',
             'Some travelers claim that in the mountains you can find caves with warm air and '
             'plants growing inside.',
             'They say that in the highest reaches of Winterspring you can see a radiance that '
             'appears nowhere else in the world.',
             'They say that despite all its dangers, it is a very beautiful and peaceful place.',
             'A traveler told of a cave where it was warm inside, flowers grew and there was no '
             'snow at all. He tried to go back, but never found it again'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Silithus',
  'min_level': 47,
  'max_level': 53,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the ruins of an ancient empire lie beneath the sands of Silithus.',
             'Rumor has it that deep underground there are enormous tunnels stretching for many '
             'miles.',
             'Travelers tell of a strange buzzing that can sometimes be heard even far from the '
             'hives.',
             'Some explorers claim that the desert hides traces of events that took place long '
             'before the present generation.',
             'They say that in the farthest corners of Silithus you can find places where the sand '
             'literally stirs on its own.',
             'They say huge insects hide in the sand and swallow any traveler who so much as steps '
             'there.',
             'Some priests say the buzzing beneath the sand is not insects. They believe it is the '
             'sound of something enormous that has not yet awakened'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Deadwind Pass',
  'min_level': 47,
  'max_level': 53,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that in Deadwind Pass the wind sometimes carries voices from the old ruins.',
             'Rumor has it that the tower at the end of the pass is not empty, even though it has '
             'long been considered abandoned.',
             'Some travelers claim that distances behave strangely here: the road back can turn '
             'out to be much longer than the road forward.',
             'They say there are old crypts in the mountains that no one has ever managed to open.',
             'Old mages say that Deadwind Pass is a place where the boundary between the ordinary '
             'world and something else is especially thin.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Moonglade',
  'min_level': 47,
  'max_level': 53,
  'expansion': 'classic',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['Druids say that Moonglade is one of the few places where the forest still keeps its '
             'ancient peace.',
             'They say the moonlight here can change the color of the water in the lakes.',
             'Rumor has it that some ancient beings come here only once every few years.',
             'Travelers say that at night in the forest you can hear songs that no one ever taught '
             'the living.',
             'They say that if you spend a night under the open sky in Moonglade, you can see '
             'unusually bright stars.'],
  'general_region': None,
  'required_tier': 0},
 {'name': 'Hellfire Peninsula',
  'min_level': 57,
  'max_level': 61,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the red lands of Hellfire Peninsula literally tremble from something '
             'happening deep underground.',
             'Rumor has it that among the ruined fortifications you can still find weapons from '
             'the days of the First Expedition.',
             'Travelers tell of old portals that sometimes flare up on their own.',
             'Some explorers claim that the land here has changed so much that old maps are almost '
             'useless.',
             'They say the mountains hide supply caches left by those who, long ago, were the '
             'first to cross the Dark Portal.',
             'Rumor has it that on the scorched plains you can find traces of creatures that exist '
             'nowhere else in Outland.',
             'Hunters tell of giant demonic beasts roaming far from the roads.',
             'Some veterans claim that at night the sounds of battle can be heard over the wastes, '
             'though there is not a single army nearby.',
             'They say the Dark Portal can be seen from much farther away than should be possible.',
             'Old travelers whisper that far beyond the front line there are ruins that almost no '
             'one ever reaches.',
             'They say a huge, clanking iron demon roams the wastes, crushing under its enormous '
             'boots anyone who fails to get away in time.'],
  'general_region': None,
  'required_tier': 8},
 {'name': 'Zangarmarsh',
  'min_level': 59,
  'max_level': 62,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the giant mushrooms of Zangarmarsh are so ancient that no one knows when '
             'they first appeared.',
             'Rumor has it that a whole network of caves and underground lakes lies beneath the '
             'marshes.',
             'Some hunters claim that the water in the deepest spots glows at night.',
             'Fishermen tell of creatures that can vanish right beneath the surface of the water.',
             'They say the fog in Zangarmarsh sometimes takes on strange shapes.',
             'Rumor has it that somewhere among the marshes there is a lake that appears on no '
             'map.',
             'Travelers tell of trees and mushrooms that grow literally before your eyes.',
             'Some explorers believe that the marshes hide traces of an ancient civilization.',
             'They say that deep in the marshes you can hear a rumble like distant thunder, even '
             'in perfectly clear weather.',
             'Old wanderers insist that some paths in Zangarmarsh change their course after a '
             'heavy rain.'],
  'general_region': None,
  'required_tier': 8},
 {'name': 'Terokkar Forest',
  'min_level': 60,
  'max_level': 62,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the ruins of Terokkar Forest were built by a people who vanished long '
             'before the Dark Portal was opened.',
             'Rumor has it that in the forest you can find ancient crypts whose entrances appear '
             'only at certain times.',
             'Travelers tell of birds that gather around the same ruins every night.',
             'Some explorers claim that the stones of the ancient buildings are covered in writing '
             'never seen anywhere else.',
             'They say there is a place in the forest where the wind always blows, even when all '
             'around is dead calm.',
             'Rumor has it that some ruins at times look completely intact, though by day nothing '
             'remains of them but rubble.',
             'Hunters tell of strange shadows moving between the trees.',
             'Some wanderers claim to have heard the voices of people long dead in the forest.',
             'They say the oldest trees of Terokkar grow right out of the stones of ancient '
             'structures.',
             'Rumor has it that in the sands and forests you can still find things left behind '
             'from before the destruction of Draenor.'],
  'general_region': None,
  'required_tier': 8},
 {'name': 'Nagrand',
  'min_level': 62,
  'max_level': 64,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say Nagrand is one of the few places in Outland where the land still resembles '
             'a real world.',
             'Travelers tell of floating islands that sometimes shift their position.',
             'Rumor has it that on the plains you can find ancient ruins almost completely '
             'swallowed by grass.',
             'Hunters insist that some of the beasts here are older than any generation now '
             'living.',
             'They say that at night you can see lights over the plains, far beyond any known '
             'settlements.',
             'Some wanderers tell of hidden springs whose water never runs dry.',
             'There is talk of places where the ground underfoot floats slightly above an abyss.',
             'They say that if you climb high enough, you can see far beyond Nagrand — all the way '
             'to other parts of Outland.',
             'Hunters whisper of a giant beast that appears only at dawn.',
             'Old draenei say there are places in Nagrand that somehow survived the destruction of '
             'Draenor almost unchanged.',
             'They say that in some parts of Nagrand the ground crumbles and falls away in chunks '
             'into the abyss right under your feet as you walk.',
             'They say that somewhere in Nagrand there is a huge gemstone the size of an entire '
             'city. Strange creatures have gnawed countless tunnels through it.'],
  'general_region': None,
  'required_tier': 8},
 {'name': "Blade's Edge Mountains",
  'min_level': 63,
  'max_level': 65,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ["They say the giant blades of the Blade's Edge Mountains were not made by nature.",
             'Rumor has it that deep in the mountains there are huge caves where ancient creatures '
             'once lived.',
             'Some travelers claim to have seen fire on the peaks, though it is impossible to '
             'climb up there.',
             'Hunters tell of rare beasts living on the sheerest cliffs.',
             'They say that in some gorges sound travels strangely — a single shout can be heard '
             'many miles away.',
             'There is talk of abandoned mines where ancient mechanisms are still running.',
             'Some explorers claim to have found stones in the mountains bearing the imprints of '
             'creatures no one has ever seen.',
             'They say the old trails between the peaks were laid long before the present '
             'settlements appeared.',
             'Travelers tell of valleys where the sun almost never shows because of the enormous '
             'mountain walls.',
             'Old hunters insist that sometimes at night they hear, overhead, the beating of wings '
             'the size of a small house.',
             'They say that in the mountains you can find the rotting bodies of gigantic dragons, '
             'impaled on sharp mountain peaks as if on spears.'],
  'general_region': None,
  'required_tier': 8},
 {'name': 'Netherstorm',
  'min_level': 65,
  'max_level': 69,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say Netherstorm is the only place where you can see the world itself literally '
             'falling apart.',
             'Rumor has it that among the floating rocks there are ancient ruins that belong to no '
             'known people.',
             'Mages tell of places where spells behave completely unpredictably.',
             'Some travelers claim to have seen islands vanish right before their eyes.',
             'They say the energy rifts sometimes spit out objects that could have been thousands '
             'of miles from here.',
             'There is talk of abandoned laboratories where experiments carried on even after '
             'their creators disappeared.',
             'Some explorers claim that at night in Netherstorm you can see stars that are not in '
             "Azeroth's sky.",
             'They say that deep in the void live creatures that can exist without any ground '
             'beneath their feet.',
             'Travelers tell of strange voices coming from the energy rifts.',
             'Old mages whisper that Netherstorm was once a completely different place.',
             'They say a mage spent a night near an energy rift and in the morning discovered that '
             'his watch had fallen three years behind.',
             'Someone saw their own reflection in the void — but it moved before they did.',
             'They say some of the floating islands were once part of a completely different '
             'world.',
             'One explorer claimed he heard a voice from a portal that called him by name.'],
  'general_region': None,
  'required_tier': 8},
 {'name': 'Shadowmoon Valley',
  'min_level': 66,
  'max_level': 69,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say Shadowmoon Valley holds ruins from the days when Draenor was still a whole '
             'world.',
             'Rumor has it that ancient sanctuaries are hidden beneath the black earth.',
             'Some travelers claim that at night green lights appear in the valley, moving on '
             'their own.',
             'They say caves have survived in the mountains where you can still find objects from '
             'the days of old Draenor.',
             'There is talk of ancient altars that still react to the presence of magic.',
             'Hunters tell of creatures altered by an energy that cannot be seen with the ordinary '
             'eye.',
             'Some wanderers claim that in the valley you can hear voices from the past.',
             'They say the oldest ruins of Shadowmoon hide passages into deep dungeons.',
             'Rumor has it that some stones here remember events that took place even before the '
             'destruction of Draenor.',
             'Old explorers insist that the true history of the valley lies hidden far beneath the '
             'surface.',
             'They say that in an old cave you can find a stone that grows warm when the name of '
             'an ancient chieftain is spoken nearby.',
             'One wanderer claimed he saw the destruction of Draenor in a dream, and in the '
             'morning found a piece of black stone under his tent.',
             'Rumor has it that green lights sometimes flare up in the oldest ruins, though there '
             'is no one inside.',
             'An old hunter swore he once saw a whole procession of shadows heading off into the '
             'mountains.'],
  'general_region': None,
  'required_tier': 8},
 {'name': "Isle of Quel'Danas",
  'min_level': 68,
  'max_level': 70,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ["They say the blood elves are returning to Quel'Danas after many long years.",
             "They say the once-beautiful Quel'Danas lies in ruins, its exquisite spires shattered "
             'and broken.',
             'Rumor has it that there lies a source of power capable of changing the fate of all '
             'Outland.',
             'Sailors tell of an incredibly bright light that can be seen at night many miles from '
             'shore.',
             'Some travelers claim that structures have been built on the island unlike anything '
             'found even among ancient ruins.',
             'They say mages and scholars from all over Azeroth and Outland gather there for an '
             'experiment they prefer not to talk about.',
             'Rumor has it that on the island you can meet creatures once thought to be nothing '
             'but legend.',
             'Sailors whisper that the water around the island has become unusually warm.',
             'They say the closer you get to the island, the brighter the sky becomes, even at '
             'night.',
             'Some claim that on the shore you can see enormous gates whose purpose no one '
             'understands.',
             'They say there is a place there where the sunlight never fades.',
             "One sailor returned from the island and said that the beautiful halls of Quel'Danas "
             'are occupied by demons and their foul rituals.',
             'Rumor has it that the warmth of the Sunwell can be felt many kilometers from the '
             'island.'],
  'general_region': None,
  'required_tier': 12},
 {'name': 'Borean Tundra',
  'min_level': 67,
  'max_level': 71,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that beneath the ice of Borean Tundra lie ruins far older than the first '
             'human settlements.',
             'Rumor has it that some of the ice fields here never melt, even during the strongest '
             'thaws.',
             'Hunters tell of gigantic creatures that emerge from the fog and vanish before anyone '
             'can get close to them.',
             'Sailors claim that far from shore they sometimes see enormous shadows beneath the '
             'water.',
             'They say that deep in the tundra there are hot springs surrounded by plants that '
             'should be impossible in such a cold climate.',
             'There is talk of ancient stone structures buried under many meters of snow.',
             'Some explorers believe that the strange mechanisms found here were left behind by '
             'those who lived in Northrend long before the peoples of today.',
             'Fishermen tell of creatures capable of breaking through the ice from below.',
             'They say that at night a green glow appears over certain stretches of the tundra.',
             'Travelers whisper that far to the north one can find traces of an ancient battle '
             'that took place long before the coming of the Lich King.',
             'Old seafarers tell of ships that vanished off the shores of Borean Tundra without a '
             'single survivor.',
             'Rumor has it that somewhere underground there is a vast network of tunnels '
             'connecting different parts of Northrend.',
             'One fisherman pulled a piece of metal out of the sea that was ice-cold on the '
             'outside and red-hot on the inside.',
             'They say someone walks beneath one of the ice fields. The footprints appear from '
             'below.',
             "A hunter claimed he saw a mountain on the horizon that isn't on any map."],
  'general_region': None,
  'required_tier': 13},
 {'name': 'Howling Fjord',
  'min_level': 67,
  'max_level': 71,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the wind of Howling Fjord can howl as if hundreds of people were screaming '
             'in the mountains.',
             'Rumor has it that high in the mountains there are still ancient settlements, '
             'abandoned long before the wars of today.',
             'Sailors tell of ships that disappear in the fog near the fjords.',
             'Some travelers claim that at night they have seen lights on peaks where there are no '
             'settlements at all.',
             'They say that deep in the mountains there are enormous halls carved right into the '
             'stone.',
             'There is talk of ancient stone gates that open only during a violent storm.',
             'Hunters tell of gigantic beasts that dwell on the highest slopes.',
             'Some explorers believe that the ruins here may be connected to the ancient history '
             'of all of Northrend.',
             'They say that ships buried here thousands of years ago lie hidden beneath the '
             'glaciers.',
             'Travelers tell of a strange echo: sometimes it repeats spoken words in a voice other '
             'than the one that spoke them.',
             'Old seafarers claim that in one of the bays you can see the outline of an enormous '
             'city beneath the water.',
             'Rumor has it that some of the mountain paths here appeared long before the people '
             'who now live in the fjords.',
             "One traveler swore he heard a dragon's roar in the mountains, yet found no trace of "
             'the beast.',
             'They say there is a door in one of the cliffs that can be opened neither by axe nor '
             'by magic.',
             'Someone saw enormous footprints in the snow that suddenly ended in the middle of an '
             'open field.'],
  'general_region': None,
  'required_tier': 13},
 {'name': 'Dragonblight',
  'min_level': 70,
  'max_level': 73,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that beneath the ice of Dragonblight rest the remains of dragons that died '
             'long before the present age.',
             'Rumor has it that some of the ancient dragon graveyards are so vast that they cannot '
             'be seen in their entirety from the ground.',
             'Old explorers claim that the ruins here are older than most of the known kingdoms of '
             'Azeroth.',
             'They say that at night ghostly silhouettes of dragons can be seen above the ancient '
             'burial grounds.',
             'Travelers tell of places where snow never settles on the ground, even though '
             'everything around them is covered in ice.',
             "Some hunters claim they have heard a dragon's roar in the wastes, though there "
             "wasn't a single living dragon nearby.",
             'Rumor has it that beneath the ancient structures there are tunnels leading deep '
             'underground.',
             'They say some of the stone monuments here were raised long before the modern '
             'dragonflights came to be.',
             'Explorers whisper that in Dragonblight one can find traces of events that happened '
             'before the peoples of today even learned to write.',
             'Some travelers tell of ice caves whose walls are covered with ancient images of '
             'dragons.',
             'Rumor has it that certain places in Dragonblight still draw dragons to them, even '
             'after thousands of years.',
             'They say that if you spend the night near an ancient graveyard, you can hear the '
             'sound of wings overhead.',
             'One explorer claimed he found a bone so enormous that he mistook it for part of a '
             'mountain.',
             'They say that in the snow you can find the tracks of a dragon that must be more than '
             'a thousand years old.',
             'An old shaman said that Dragonblight is not a graveyard. It is a place where the '
             'dragons themselves are waiting for something.'],
  'general_region': None,
  'required_tier': 13},
 {'name': 'Grizzly Hills',
  'min_level': 71,
  'max_level': 74,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that deep in Grizzly Hills there are forests that have barely changed in '
             'thousands of years.',
             'Hunters tell of bears so enormous that they can fell a tree with a single blow.',
             'Rumor has it that beneath the forest lie ancient stone structures, partly swallowed '
             'by roots.',
             'Some woodcutters claim they hear knocking from deep in the forest, though there '
             "isn't a single sawmill nearby.",
             'They say some of the trees here are so ancient that their roots reach deeper than '
             'the foundations of the old settlements.',
             'Travelers tell of places where the snow suddenly ends and green forest begins.',
             'There is talk of ancient caves whose walls are covered with images of enormous '
             'bears.',
             'Hunters claim that a white bear that cannot be killed lives in the forest.',
             'Some explorers believe that the forest hides the ruins of an unknown ancient '
             'civilization.',
             'They say that at night in the forest you can hear a low hum, like the distant '
             'breathing of the earth.',
             'Old folk say that the oldest trees of Grizzly Hills grow where something very '
             'important once happened.',
             'Rumor has it that deep in the forest there is a lake whose surface never freezes '
             'over.',
             'One hunter claimed he met a bear whose eyes glowed like two lanterns.',
             'They say that if you press your ear to certain trees, you can hear knocking.',
             'An old woodcutter said that he once saw a tree that moved.'],
  'general_region': None,
  'required_tier': 13},
 {'name': "Zul'Drak",
  'min_level': 72,
  'max_level': 75,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ["They say Zul'Drak was once one of the greatest centers of an ancient troll "
             'civilization.',
             'Rumor has it that among the snow-covered ruins there still stand temples that no one '
             'dares to enter.',
             'Some travelers claim that the statues of the ancient gods sometimes change position.',
             'Hunters tell of gigantic creatures that roam the most remote corners of the region.',
             'They say that beneath the temples lies an entire underground city.',
             'Rumor has it that the ancient trolls left weapons here capable of killing beings far '
             'stronger than ordinary warriors.',
             "Some explorers claim that the ruins of Zul'Drak hide evidence of events that the "
             'trolls themselves forgot long ago.',
             'They say that in one of the temples you can find a statue that whispers the names of '
             'the dead.',
             'Travelers tell of enormous paw prints that appear around the ancient shrines.',
             'Rumor has it that the snow around certain altars never melts.',
             "Old treasure hunters insist that the treasures of Zul'Drak remain practically "
             'untouched.',
             'They say that even some of the local inhabitants are afraid to enter the most '
             'ancient parts of the ruins.',
             "One hunter took a small golden figurine from Zul'Drak. Three nights later, he "
             'brought it back.',
             'They say some of the temples were built on top of even older temples.',
             'An old priest claimed he heard prayers coming from an empty shrine.'],
  'general_region': None,
  'required_tier': 13},
 {'name': 'Sholazar Basin',
  'min_level': 74,
  'max_level': 77,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say Sholazar Basin is one of the few places in Northrend that barely yields to '
             'the cold that rules these lands.',
             'Explorers tell of plants that can grow in a matter of hours.',
             "Rumor has it that the basin's huge waterfalls hide caves.",
             "Hunters claim that animals live here that you won't find anywhere else in the world.",
             'They say some of the creatures of Sholazar Basin have lived here since time '
             'immemorial.',
             'Travelers tell of strange stone structures hidden in the jungle.',
             'Rumor has it that the lakes here are fed by water from a spring located deep '
             'underground.',
             'Some explorers believe that the entire basin was once part of an enormous experiment '
             'by unknown creators.',
             'They say that in some places you can find metal objects that look nothing like the '
             'ordinary crafts of Azeroth.',
             'Hunters whisper of a gigantic beast that can stay hidden even out in the open.',
             'Rumor has it that at night some of the plants begin to glow.',
             'Old travelers claim that Sholazar Basin looks far too alive for a place lying so '
             'close to the icy wastes.',
             'They say one explorer found a stone door in the middle of the jungle. Behind it was '
             'nothing but solid, murky ice.',
             "A hunter claimed he saw a beast that he couldn't remember even after he returned "
             'home.',
             "Some believe that Sholazar Basin is not a natural place, but someone's enormous "
             'garden.'],
  'general_region': None,
  'required_tier': 13},
 {'name': 'Crystalsong Forest',
  'min_level': 74,
  'max_level': 77,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the trees of Crystalsong Forest turned to crystal through no ordinary '
             'magic.',
             'Rumor has it that at night the whole forest begins to ring softly.',
             'Some mages claim that the crystals react when spells are cast.',
             'Travelers tell of trees that glow from within.',
             'They say that beneath the forest lie huge deposits of an unknown crystal.',
             'Rumor has it that some of the crystals can preserve sounds spoken near them.',
             'Explorers tell of surges of magic that occur for no apparent reason.',
             'Some travelers claim they have seen the silhouettes of people inside the crystals.',
             'They say that at the heart of the forest there is a tree beside which you can see '
             'your own silhouette, and it will tell you what the future holds for you.',
             'Rumor has it that if you walk through the forest at night in complete silence, you '
             'can hear distant singing.',
             'One mage touched a tree and heard his own voice speaking words he had never said.',
             'They say some of the crystals show events that happened many years ago.',
             'A traveler claimed he saw himself in the crystal forest, only a few seconds older.'],
  'general_region': None,
  'required_tier': 13},
 {'name': 'The Storm Peaks',
  'min_level': 76,
  'max_level': 79,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say the summits of the Storm Peaks were built, not shaped by nature.',
             'Rumor has it that deep within the mountains lie ancient halls created by the '
             'mysterious titans.',
             'Some explorers claim that the stone walls are so enormous that they could never have '
             'been built with ordinary tools.',
             'Travelers tell of mechanisms that are still working after thousands of years.',
             "They say that a city that isn't on any map is hidden among the highest mountains.",
             'Rumor has it that some doors in the ancient structures open only during a '
             'thunderstorm.',
             'Hunters claim they have seen gigantic silhouettes moving among the clouds.',
             'Some mages believe that the storms of the Storm Peaks are not caused by nature.',
             'They say that in the mountains you can find ancient maps of all of Northrend carved '
             'right into the rock.',
             'Rumor has it that inside one of the peaks there is an enormous hall where entire '
             'races were once created.',
             'Explorers tell of stone mechanisms that go on carrying out some task unknown to '
             'them.',
             'Old travelers claim that some of the structures here are so vast that an ordinary '
             'person looks like an ant beside them.',
             'One explorer heard a voice coming from an ancient mechanism. The voice called him by '
             'a number.',
             'They say some of the titans still sleep deep beneath the mountains.',
             'An old miner claimed that he once broke through a wall and saw behind it not stone, '
             'but a starry sky.'],
  'general_region': None,
  'required_tier': 13},
 {'name': 'Icecrown',
  'min_level': 77,
  'max_level': 79,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that somewhere beyond the icy plains stands a fortress so enormous that its '
             "walls can be seen from several days' journey away.",
             'Rumor has it that the ice of Icecrown was never natural and came into being through '
             'a power that exists nowhere else.',
             'Old soldiers tell of roads along which, at night, armies march without any living '
             'commanders.',
             'Some travelers claim they have heard the clash of weapons far beyond the visible '
             'fortifications.',
             'They say that in the ice fields you can find the weapons of fallen heroes, frozen in '
             'the ice.',
             'There is talk of ancient crypts that existed even before the current Lich King '
             'appeared.',
             'Some explorers claim that entire cities lie beneath the icy plain.',
             'They say that on the coldest nights the ice walls begin to glow with a blue light.',
             'Travelers tell of ghostly figures that appear on the horizon during snowstorms.',
             'Rumor has it that some of the fortresses of Icecrown were built on top of even more '
             'ancient structures.',
             'Old warriors claim that sometimes you can find in the snow the tracks of an army '
             'that is not among the living.',
             'They say that the closer you get to the center of Icecrown, the quieter the wind '
             'becomes.',
             'One scout swore he saw his own army in the distance, even though he was there alone.',
             "They say the ice around some of the ruins doesn't freeze — it moves.",
             "The most frightening thing in Icecrown is not what you can see. It's what you hear "
             'while you sleep.'],
  'general_region': None,
  'required_tier': 13},
 {'name': 'General TBC rumors',
  'min_level': 60,
  'max_level': 70,
  'expansion': 'tbc',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that some orcs in Nagrand still hear the voices of their ancestors, though '
             'the shamans claim that by no means all of these voices belong to the dead.',
             'Rumor has it that some parts of Outland are slowly vanishing into the Nether. One '
             "day a person simply returns to a familiar place — and there's nothing there anymore.",
             'They say that in the old ruins of Draenor you can sometimes find objects that never '
             'existed on Azeroth: weapons, coins and books from a world that is no more.',
             'They say that some pieces of land in Outland still remember old Draenor. If you '
             'stand long enough in such a place, you can hear distant thunder, war drums or the '
             'voices of people who died long ago.',
             'They say that somewhere beyond the known islands there is an enormous fragment of '
             'Draenor, so large that whole forests and rivers have survived on it. But no roads '
             'lead there, and no one knows how to reach it.',
             'They say that after the Dark Portal was opened, some people began to see Draenor in '
             'their dreams as it was before its destruction. When they wake, they can sometimes '
             'draw places they have never been.',
             'They say that in Outland you can find trees that grow with their roots pointing '
             'upward. Some druids claim that this is perfectly natural for them.',
             'They say that the water in some places in Outland remembers the old world. If you '
             'draw it into a vessel and leave it for a few days, it sometimes takes on the taste '
             'of water from somewhere else entirely.',
             'They say that some sounds in Outland arrive with an enormous delay. You can hear a '
             'clap of thunder even though the lightning struck several hours ago.',
             'Rumor has it that demons avoid certain places in Outland not because there is some '
             'magical protection there, but because they remember what those places used to be.',
             'They say that after Draenor was destroyed, some elemental spirits stopped '
             "understanding where the earth is and where the sky is. That's why in Outland you "
             'might meet an elemental that thinks stone is water.',
             'They say that on one of the islands you can see the shadows of buildings that '
             "haven't stood there for several thousand years.",
             'They say that some old orcish songs must never be sung to the end in Outland. If you '
             'finish the song, the ancestor spirits sometimes begin to answer.',
             'They say that on old battlefields weapons sometimes become covered in frost, even '
             "when it's sweltering all around. The old folk claim that it isn't cold, but the "
             'memory of blood.',
             'They say that in Outland there are places where time flows a little differently. A '
             'traveler may spend an hour there, and on returning discover that several days have '
             'passed outside.',
             'They say that some children born in Outland draw Draenor as it was before its '
             'destruction, even though they have never heard of it.',
             'They say that if you gaze at the Dark Portal long enough, you can sometimes see on '
             'the other side not Azeroth and not Outland, but an entirely different world. They '
             'describe colossal buildings made of metal and gigantic war machines.',
             'They say that someone once went through the Dark Portal and came back a few minutes '
             'later — but claimed to have been gone for several years.',
             'Rumor has it that there are wanderers who appear on the roads of Outland, ask about '
             'Draenor and then disappear. No one knows where they came from — the past, the future '
             'or another world.',
             'They say that somewhere in Outland a piece of the old sky of Draenor has survived. '
             'Supposedly it hangs above the ground, even though there has long been nothing around '
             'it that could hold it up.',
             'Some claim that if you rise high enough above Outland, you can see that the '
             'fragments of the world are slowly moving and gradually drawing closer to one '
             'another.',
             'They say that someone once found footprints at the edge of an island leading '
             'straight into the void. The footprints began on the ground and went on further, as '
             'if an invisible person kept walking where there was no longer any land.',
             'Rumor has it that there is a caravan that appears in the wastes of Outland once '
             'every few years. Its drivers claim they are heading home. The problem is that their '
             '"home" was destroyed thousands of years ago.',
             'They say that some ruins in Outland change the placement of their doors and stairs '
             'after sunset.',
             'They say that if you leave a coin on the grave of an unknown orc, by morning you may '
             "find another coin beside it — made of a metal that doesn't exist on Azeroth.",
             'They say that somewhere among the ruins stands a house that looks completely intact. '
             'Inside, everything is covered in dust, but every evening a hot meal appears on the '
             'table.',
             'Rumor has it that there is a well from which you can hear the voices of people who '
             'stood beside it in the past.',
             "They say that some creatures of Outland don't understand at all that their world has "
             'been destroyed. They go on living as though Draenor still exists.',
             'They say that Outland is only a small part of what remains of Draenor. Other '
             'fragments of Draenor hang somewhere far away in the void.',
             'They say that in Outland there are places where you can still find traces of the '
             'first expeditions sent through the Dark Portal — and some of those traces belong to '
             'people who officially never passed through it.',
             "They say that someone found an old map of Draenor marking lands that don't exist "
             'even among the present fragments of Outland.',
             'They say that some orcs can tell by the smell of the soil which part of old Draenor '
             'it once belonged to.',
             'They say that in the caves of Outland you sometimes come across creatures that have '
             'never been seen on Azeroth and resemble no known creature of Draenor.',
             'They say that old draenei guidebooks contain the names of cities that no longer '
             'exist, not even as ruins.',
             'They say that some of the old portals in Outland still work, but they lead somewhere '
             'other than where they should.',
             'They say that someone once opened such a portal and saw on the other side Draenor as '
             'it was before its destruction.',
             'Some wise shamans say that if Outland keeps crumbling, one day the Dark Portal may '
             'be the only place left, floating in the void in the middle of nothing.'],
  'general_region': 'Outland',
  'required_tier': 8},
 {'name': 'General WotLK rumors',
  'min_level': 70,
  'max_level': 80,
  'expansion': 'wotlk',
  'factions': ('Alliance', 'Horde'),
  'rumors': ['They say that far away in the northern sea there are islands that almost no one ever '
             'visits.',
             'Sailors tell of ships that vanished without a trace near those shores.',
             'Word is that traces of ancient settlements can be found on the cliffs.',
             'Some hunters claim they have seen tracks in the snow left by creatures too large for '
             'any known beast.',
             'They say that the outlines of enormous ships sometimes appear in the fog.',
             'Travelers tell of ice caves that open only at low tide.',
             'Word is that ruins that appear on no map are hidden on the distant islands.',
             'Old sailors claim that they sometimes hear a muffled ringing from the northern '
             'shore, even though there are no bells there at all.',
             'They say that the ancient structures of the Storm Peaks and the ruins of '
             'Dragonblight were built by the same hands. Only no one knows who built them first.',
             'One explorer claimed that there is a single system of tunnels beneath Borean Tundra, '
             'Sholazar Basin and Icecrown. His notes were found, but the explorer himself was not.',
             'Word is that the crystals of Crystalsong are part of the same mechanism that makes '
             'the ancient machines in the Storm Peaks work.',
             'An old shaman said that all of Northrend stands on the bones of creatures that lived '
             'here long before the dragons.',
             'Some mages believe that the strange cold of Icecrown did not begin there. It is '
             'spreading from somewhere deep within the earth.',
             'They say that if you draw a line between the most ancient ruins of Northrend, they '
             'all turn out to surround a single place that is not on any map.',
             "One traveler claimed he saw the same symbol on the ruins of Zul'Drak, in the Storm "
             'Peaks and beneath the ice of Dragonblight.',
             'An old cartographer said that the maps of Northrend are constantly going out of '
             'date. Not because the roads change — it is just that some places start appearing '
             'where they never were before.',
             'One mad explorer claimed that the ancient titans left in Northrend not ruins, but a '
             'working machine. It is just that no one has yet figured out what it does.',
             'They say that beneath the ice of Northrend there is a place where time does not '
             'move. That is exactly why some creatures here live for thousands of years.',
             'They say that beneath the ice of Northrend there are whole cities older than humans, '
             'elves and even the present-day kingdoms.',
             "They say that some of Northrend's glaciers grow not because of the cold, but because "
             'something inside them keeps freezing everything around.',
             'There are rumors that in the deepest caves you can hear thuds, like the beating of '
             'an enormous heart. No one knows whether it belongs to a creature, a machine or '
             'Northrend itself.',
             'They say that if you leave a weapon in the snow near ancient ruins, by morning it is '
             'sometimes covered in frost shaped like unfamiliar runes.',
             'Some travelers claim that during a blizzard they saw enormous towers on the horizon '
             'that are not on any map. When the storm ends, the towers vanish.',
             'They say that some snowstorms in Northrend begin without any clouds at all. The sky '
             'stays clear, yet the snow keeps falling.',
             'Rumor has it that beneath the ice sheet lie hidden roads the titans once walked. '
             'Sometimes the snow above them caves in along a perfectly straight line, as if the '
             'road still exists.',
             'They say that the ancient mechanisms of the titans can recognize creatures that have '
             'never seen them before.',
             'Some dwarves claim that if you spend enough time near titan ruins, you can start '
             'seeing unfamiliar corridors and halls in your dreams. The strangest thing is that '
             'different people sometimes have the same dreams.',
             'They say that somewhere in Northrend there is a door that cannot be opened from the '
             'outside. It opens only when someone inside wants to get out.',
             'There are rumors of a cave where the snow does not melt even next to red-hot metal. '
             'They say that inside lies something that must not be warmed.',
             'They say that some frozen lakes are so clear that if you look into them at night, '
             'you can see not the bottom, but the stars.',
             'Some sailors tell of screams coming from beneath the ice far from shore. The screams '
             'sound as if someone is trying to get out.',
             'They say that in the northernmost waters a ship with no crew sometimes appears. It '
             'passes right through the ice fields and vanishes into the fog.',
             'Some hunters claim that in Northrend there are beasts that never leave tracks in the '
             'snow.',
             'They say that one such beast can walk straight through a camp without disturbing a '
             'single person and without leaving any tracks. The only proof of its existence is the '
             'food that has gone missing.',
             'There are rumors of a white bear that has lived for several hundred years. Old '
             'hunters claim they saw it when they were still children.',
             'They say that some Scourge ghouls keep returning to the places where they lived in '
             'life, even though they have long been unable to remember their past.',
             'There is a terrifying rumor about Scourge soldiers who sometimes stop in the middle '
             'of a battle, stare at something invisible and begin to retreat.',
             "They say that some of the Scourge's ice crypts were built not to keep the dead "
             'inside, but to keep the living from finding something in the depths.',
             'They say that in some places the dead do not rise after death — instead, the shadows '
             'of the living begin to move.',
             'Rumor has it that if you spend a night near an ancient Northrend graveyard, in the '
             'morning you may find footprints all around your camp. Every one of them will lead '
             'toward the camp, and not a single one away from it.',
             'They say that deep in Northrend there is ice that cannot be broken even with magic. '
             'And inside it, faces can sometimes be seen.',
             'Some treasure hunters claim that in ice caves they have seen frozen creatures that '
             'are still blinking.',
             'They say that somewhere there is an ice cave where time has almost stopped. Flames '
             'there never go out, water never freezes, and wounds barely heal.',
             'They say that some spirits of those who died in Northrend do not understand that '
             'they are dead. They keep waiting for their comrades to return.',
             'There is a legend about an old soldier who climbs out of his grave every night, '
             'walks several miles through the snow and returns before dawn.',
             'Some priests claim that in Northrend the Light feels different. As if even the '
             'darkness itself around them notices the presence of the Light.',
             'They say that somewhere there is a place where spells of the Light do not fade for '
             'hours after being cast and keep illuminating the snow even after the priest is no '
             'longer nearby.',
             'Rumor has it that the northern lights over Northrend are not a natural phenomenon at '
             'all. Some believe they are the trace of ancient magic that still holds something in '
             'the heavens.',
             'Some mages claim that if you watch the northern lights in the sky closely for long '
             'enough, you can see images of unfamiliar places in them.',
             'Rumor has it that there is an island that appears only in winter. Those who have set '
             'foot on it claim that there is not a single living creature there — yet there are '
             'footprints everywhere.'],
  'general_region': 'Northrend',
  'required_tier': 13}]
