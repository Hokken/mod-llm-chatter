# -*- coding: utf-8 -*-
"""frFR locale data for mod-llm-chatter.

Split out of chatter_constants.py so the central module stays
readable: the language tables are bulk data that changes for
translation reasons, not logic that changes with the module.

Names here are unsuffixed -- the locale is the module. The
registry in this package maps locale codes onto these.
"""

ZONE_NAMES = {
    1: "Dun Morogh", 3: "Terres Ingrates", 4: "Terres Foudroyées",
    8: "Marais des chagrins", 10: "Bois de la pénombre", 11: "Les Paluns",
    12: "Forêt d'Elwynn", 14: "Durotar", 15: "Marécage d'Aprefange",
    16: "Azshara", 28: "Maleterres de l'Ouest",
    33: "Vallée de Strangleronce", 38: "Loch Modan",
    40: "La Marche de l'Ouest", 41: "Défilé de Deuillevent",
    44: "Les Carmines", 45: "Hautes-terres d'Arathi", 46: "Steppes ardentes",
    47: "Les Hinterlands", 51: "Gorge des Vents brûlants",
    85: "Clairières de Tirisfal", 130: "Forêt des Pins argentés",
    139: "Maleterres de l'Est", 141: "Teldrassil", 148: "Sombrivage",
    215: "Mulgore", 267: "Contreforts de Hautebrande", 331: "Ashenvale",
    357: "Feralas", 361: "Gangrebois", 400: "Mille pointes", 405: "Desolace",
    406: "Les Serres-Rocheuses", 440: "Tanaris", 490: "Cratère d'Un'Goro",
    493: "Reflet-de-Lune", 618: "Berceau-de-l'Hiver", 1377: "Silithus",
    1497: "Les Fossoyeuses", 1519: "Hurlevent", 1537: "Forgefer",
    1637: "Orgrimmar", 1638: "Pitons-du-Tonnerre", 1657: "Darnassus",
    3483: "Péninsule des Flammes Infernales", 3518: "Nagrand",
    3519: "Forêt de Terokkar", 3520: "Vallée d'Ombrelune",
    3521: "Marécage de Zangar", 3522: "Les Tranchantes",
    3523: "Raz-de-néant", 3703: "Shattrath",
    65: "Désolation des Dragons",  # verified: official Blizzard fr-fr news source
    66: "Zul'Drak",  # verified: official Blizzard fr-fr news source
    67: "Pics Foudroyés",  # verified: official Blizzard fr-fr news source
    210: "Couronne de Glace",  # verified: official Blizzard fr-fr news source
    394: "Les Grisonnes",  # verified: official Blizzard fr-fr news source
    495: "Fjord Hurlant",  # verified: official Blizzard fr-fr news source
    3537: "Toundra Boréenne",  # verified: official Blizzard fr-fr news source
    3711: "Bassin de Sholazar",  # verified: official Blizzard fr-fr news source
    3525: "Île de Brume-Sang", 4080: "Île de Quel'Danas",
    3430: "Bois des Chants Éternels", 3524: "Île de Brume-Azur",
    3433: "Les Terres Fantômes", 4197: "Joug-d'Hiver",
    2817: "Forêt du Chant de Cristal", 3487: "Lune-d'Argent",
    3557: "L'Exodar", 4228: "L'Oculus",
}

RACE_SPEECH_PROFILES = {
    "Human": {
        "traits": [
            "pragmatiques, résilients, animés d'un esprit civique, disciplinés et prompts à se rallier en cas de crise",
            "adaptables, ambitieux, tournés vers la communauté, guidés par le devoir et l'opportunité",
            "loyaux envers la couronne et leurs compagnons, trempés par la guerre, guidés par un idéalisme pragmatique",
            "débrouillards et travailleurs, mêlant cran de la frontière et diplomatie cosmopolite",
            "patriotes et dévoués au devoir, marqués par la perte mais obstinément pleins d'espoir pour l'avenir",
            "socialement perspicaces, avisés en affaires et enclins "
            "à bâtir des alliances plutôt qu'à nourrir des rancunes",
            "courageux sous le feu, prompts à s'organiser, et mal à l'aise face à l'incertitude prolongée",
            "ancrés dans la tradition mais ouverts aux idées nouvelles quand la survie l'exige",
        ],
        "flavor_words": [
            "pour l'Alliance", "par la Lumière", "Hurlevent",
            "Lordaeron", "la cathédrale", "roi Varian",
            "honneur", "devoir", "le royaume",
            "Norsource", "la couronne", "héros déchus",
        ],
        "vocabulary": [
            ("Light be with you", "bénédiction/salutation"),
            ("By the Light!", "exclamation de surprise ou de résolution"),
            ("Well met", "salutation formelle"),
            ("For the Alliance!", "cri de guerre"),
            ("Go with honor, friend", "adieu"),
            ("Safe travels", "adieu"),
        ],
        "lore": [
            "Les humains ont reconstruit Hurlevent après les ravages des premières guerres.",
            "Les royaumes humains du nord ont été anéantis, en particulier Lordaeron par le Fléau.",
            "L'Église de la Sainte Lumière influence fortement la culture et les institutions.",
            "Les ordres de chevalerie, les milices et les traditions "
            "de la garde municipale sont des piliers sociaux centraux.",
            "Hurlevent, sous le roi Varian, est un centre politique et militaire majeur de l'Alliance.",
            "Les royaumes humains équilibrent idéalisme, pression de survie et realpolitik.",
            "Les archives des titans au Norfendre relient l'ascendance humaine aux vrykuls.",
        ],
        "worldview": (
            "La politique humaine gravite autour de Hurlevent et de l'effort de guerre de "
            "l'Alliance. La foi en la Lumière, le service militaire et l'ordre civique sont "
            "des normes sociales fortes. Après les pertes subies à Lordaeron et les invasions "
            "répétées, les communautés humaines sont prudentes, patriotes et centrées sur la "
            "sécurité."
        ),
    },
    "Orc": {
        "traits": [
            "directs, fiers, attachés à l'honneur, tribaux, intenses et protecteurs d'une liberté durement acquise",
            "farouchement loyaux envers leur clan, forgés par la guerre, animés par le besoin de prouver leur valeur",
            "directs et portés à l'affrontement, valorisant la force tempérée par la sagesse ancestrale",
            "passionnés par l'honneur, méfiants envers la diplomatie et prompts à défier la faiblesse",
            "endurcis par les batailles et communautaires, trouvant "
            "leur identité dans la lutte et la victoire partagées",
            "spirituellement ancrés dans la tradition chamanique mais hantés par un héritage de corruption",
            "francs et impatients face à la politique, préférant l'action à la délibération",
            "profondément protecteurs de la souveraineté de la Horde, "
            "méfiants envers les étrangers et fiers d'avoir survécu",
        ],
        "flavor_words": [
            "Lok'tar ogar", "sang et tonnerre", "pour la Horde",
            "Durotar", "Orgrimmar", "les ancêtres",
            "honneur", "les clans", "Thrall",
            "Draenor", "tambours de guerre", "loups-esprits",
        ],
        "vocabulary": [
            ("Lok'tar ogar!", "Victoire ou la mort !"),
            ("Zug-zug", "acquiescement, comme « d'accord »"),
            ("Dabu", "j'obéis / je suis d'accord"),
            ("Throm-ka", "bien trouvé"),
            ("Aka'Magosh", "une bénédiction sur toi et les tiens"),
            ("Lok-Narash!", "Aux armes !"),
            ("Gol'Kosh!", "Par ma hache !"),
        ],
        "lore": [
            "Les orcs venaient du Draenor et furent manipulés jusqu'à la corruption démoniaque.",
            "Après la Deuxième Guerre, beaucoup furent détenus dans des camps d'internement.",
            "Thrall unifia les clans et fonda une nouvelle Horde installée au Durotar.",
            "Les traditions chamaniques et le respect des ancêtres furent retrouvés après la corruption passée.",
            "La société orque valorise la mémoire du clan, la prouesse martiale et l'honneur personnel.",
            "À l'époque du Roi-liche, l'ascension de Garrosh Hurlenfer "
            "au commandement de la Horde attise les tensions politiques.",
            "L'héritage de l'asservissement démoniaque continue de façonner leur identité et leur fierté.",
        ],
        "worldview": (
            "L'identité orque au sein de la nouvelle Horde se construit sur la guérison de la "
            "corruption démoniaque, la loyauté envers le clan et la Horde, et les traditions "
            "chamaniques restaurées. Durotar et Orgrimmar représentent l'autonomie retrouvée "
            "après l'internement. Honneur, force et survie sont perçus comme des devoirs "
            "indissociables."
        ),
    },
    "Dwarf": {
        "traits": [
            "robustes, têtus, fiers de leur artisanat, loyaux à leur clan, francs et curieux des secrets anciens",
            "inébranlables au combat, amateurs de boisson et d'histoires, dévoués à leur famille jusqu'au bout",
            "bourrus mais chaleureux, avec un profond respect pour la tradition et le travail honnête",
            "sans cesse curieux des reliques des titans, toujours prêts à creuser plus profond et à en savoir plus",
            "au parler simple, têtus dans le meilleur sens du terme, et loyaux jusqu'à l'excès",
            "fiers de leur forge et de leur famille, prompts à rire et lents à pardonner une trahison",
            "pragmatiques et terre à terre, faisant plus confiance aux "
            "marteaux et aux poignées de main qu'aux belles paroles",
            "d'esprit robuste et résilient, forgés par les hivers montagnards et des siècles de querelles de clans",
        ],
        "flavor_words": [
            "par ma barbe", "ouais", "pierre et acier",
            "Forgefer", "Khaz Modan", "clan",
            "la forge", "la bière", "reliques des titans",
            "la montagne", "Ligue des explorateurs", "enclume",
        ],
        "vocabulary": [
            ("Keep yer feet on the ground", "adieu"),
            ("Fer Khaz Modan!", "Pour le Khaz Modan ! — cri de guerre"),
            ("Well met", "salutation"),
            ("Off with ye", "adieu informel"),
        ],
        "lore": [
            "Les nains descendent des terreux forgés par les titans, changés par la Malédiction de la Chair.",
            "Trois clans majeurs structurent la politique : Barbe-de-bronze, Marteau-hardi et Fer noir.",
            "Forgefer est un bastion clé de l'Alliance et un centre commercial.",
            "L'ingénierie, la forge, les armes à feu et le brassage sont des points forts culturels majeurs.",
            "La Ligue des explorateurs mène l'archéologie et la recherche sur les titans à travers Azeroth.",
            "La mémoire et les rancunes de clan peuvent durer des générations.",
            "Les nains sont des vétérans aguerris de l'Alliance, éprouvés par de multiples guerres.",
        ],
        "worldview": (
            "La société naine est organisée par clans et fortement liée à Forgefer, aux "
            "traditions artisanales et à l'archéologie des titans. Le service militaire et le "
            "travail concret sont tous deux respectés. Les alliances se jugent à la loyauté et "
            "aux actes accomplis."
        ),
    },
    "Night Elf": {
        "traits": [
            "anciens, révérencieux, réservés, patients, fiers et farouchement protecteurs de la nature",
            "contemplatifs et mesurés, portant des millénaires de mémoire dans chaque décision",
            "profondément spirituels, attentifs aux cycles lunaires et méfiants envers l'imprudence arcanique",
            "gracieux mais féroces dans la défense des bosquets sacrés et des terres ancestrales",
            "réservés envers les étrangers, intensément loyaux dans les liens de confiance et de but commun",
            "mélancoliques mais résolus, marqués par une immortalité perdue et un devoir qui perdure",
            "vigilants et posés, préférant la patience et la précision à la précipitation",
            "discrètement autoritaires, tirant leur autorité de l'âge et de la dévotion plutôt que du rang",
        ],
        "flavor_words": [
            "Elune", "qu'Elune te guide", "lumière des étoiles",
            "Kaldorei", "Darnassus", "Nordrassil",
            "racines antiques", "Teldrassil", "les anciennes voies",
            "Cenarius", "clair de lune", "le Rêve d'Émeraude",
        ],
        "vocabulary": [
            ("Ishnu-alah", "bonne fortune à toi"),
            ("Ishnu-dal-dieb", "bonne fortune à ta famille"),
            ("Elune-adore", "qu'Elune soit avec toi"),
            ("Ande'thoras-ethil", "que tes tourments s'apaisent"),
            ("Andu-falah-dor!", "que l'équilibre soit restauré !"),
            ("Bandu Thoribas!", "préparez-vous au combat !"),
            ("Fandu-dath-belore?", "qui va là ?"),
            ("Tor ilisar'thera'nal!", "que nos ennemis tremblent !"),
        ],
        "lore": [
            "L'ancienne civilisation kaldorei fut brisée par le Cataclysme originel (la Fracture).",
            "Dévotion profonde envers Elune, le druidisme et les traditions des sentinelles.",
            "Longue histoire de lutte contre les démons, les satyres et la corruption dans les forêts sacrées.",
            "L'immortalité prit fin après les événements entourant Nordrassil et la Troisième Guerre.",
            "L'appartenance à l'Alliance après Warcraft III demeure pratique plutôt qu'intime.",
            "La protection des arbres-mondes, des bosquets sacrés et des sanctuaires sauvages est centrale.",
            "L'excès arcanique inspire la crainte, souvenir d'une catastrophe mondiale passée.",
        ],
        "worldview": (
            "Les priorités kaldorei sont la défense des terres sacrées, le culte d'Elune et "
            "l'équilibre druidique. La mémoire collective de la Fracture les rend prudents face "
            "à un usage imprudent de la magie arcanique. La coopération avec l'Alliance existe, "
            "mais une distance culturelle avec les races plus jeunes demeure."
        ),
    },
    "Undead": {
        "traits": [
            "sombrement sarcastiques, amers, pragmatiques, impitoyables, "
            "tournés vers la survie et farouchement insulaires",
            "froids et calculateurs, ne faisant confiance à personne totalement, "
            "mais loyaux envers ceux qui ont fait leurs preuves",
            "morbidement humoristiques, francs sur la mort et méprisants envers l'optimisme naïf",
            "animés par la vengeance et la préservation de soi, avec peu de patience pour la sentimentalité",
            "cliniques et détachés, considérant les vivants avec un mélange d'envie et de mépris",
            "rusés et débrouillards, façonnés par la trahison à s'attendre au pire de leurs alliés",
            "sinistrement déterminés, trouvant un but dans le dépit plutôt que dans l'espoir",
            "territoriaux et méfiants, gardant les intérêts des Réprouvés avec une efficacité impitoyable",
        ],
        "flavor_words": [
            "Dame noire", "la peste", "la tombe",
            "Réprouvés", "les Fossoyeuses", "le Fléau",
            "vengeance", "l'apothicaire", "Lordaeron",
            "pourriture", "libre arbitre", "le Roi-liche",
        ],
        "vocabulary": [
            ("Dark Lady watch over you", "adieu/bénédiction"),
            ("Victory for Sylvanas", "cri de ralliement"),
            ("Embrace the shadow", "adieu"),
            ("Our time will come", "expression de détermination"),
        ],
        "lore": [
            "Les Réprouvés sont d'anciens morts-vivants du Fléau qui ont recouvré leur libre arbitre.",
            "Dirigés par Sylvanas Coursevent depuis les Fossoyeuses.",
            "Nés des ruines de Lordaeron et rejetés par la plupart des vivants.",
            "La Société royale des apothicaires développe la peste et d'autres armes chimiques brutales.",
            "Les événements de l'époque du Roi-liche incluent la trahison "
            "des Portes du Courroux et des purges internes de faction.",
            "L'appartenance à la Horde est stratégique et souvent marquée par une méfiance mutuelle.",
            "La vengeance contre le Roi-liche est un moteur émotionnel et politique central.",
        ],
        "worldview": (
            "La politique des Réprouvés se concentre sur la préservation du libre arbitre, la "
            "sécurisation des possessions à Lordaeron et l'anéantissement des menaces du Fléau. "
            "La société des Fossoyeuses est fortement militarisée et lourdement influencée par "
            "les réseaux d'apothicaires et de renseignement. Leur relation avec la Horde est "
            "stratégique, façonnée davantage par des ennemis communs que par la confiance."
        ),
    },
    "Tauren": {
        "traits": [
            "calmes, ancrés, spirituels, honorables, patients et protecteurs de leurs proches et de leur terre",
            "doux dans le conseil mais inébranlables dans la défense, guidés par les anciens et les rites ancestraux",
            "profondément communautaires, mesurant la valeur au service "
            "rendu à la tribu plutôt qu'à la gloire personnelle",
            "contemplatifs et lents à la colère, mais dévastateurs "
            "lorsqu'ils sont éveillés pour protéger les innocents",
            "révérencieux envers la nature et les ancêtres, trouvant "
            "la sagesse dans les saisons et le cours des années",
            "stoïques et fiables, préférant les paroles mesurées et l'action décisive à la fanfaronnade",
            "chaleureux et hospitaliers envers leurs alliés, prudents et vigilants envers les étrangers",
            "spirituellement en phase et physiquement imposants, alliant tendresse et force brute",
        ],
        "flavor_words": [
            "Terre-Mère", "la grande chasse",
            "les ancêtres", "Pitons-du-Tonnerre", "shu'halo",
            "les plaines", "Mulgore", "anciens de la tribu",
            "la chasse", "totem", "Cairne", "le vent",
        ],
        "vocabulary": [
            ("Walk with the Earth Mother", "adieu/bénédiction"),
            ("Ancestors watch over you", "adieu"),
            ("Winds be at your back", "adieu/bénédiction"),
            ("Earth Mother guide you", "bénédiction"),
        ],
        "lore": [
            "Les tribus nomades furent unifiées sous Cairne Sabot-de-sang.",
            "Les Pitons-du-Tonnerre devinrent la cité centrale des taurens à Mulgore.",
            "La vie spirituelle est centrée sur la Terre-Mère et les ancêtres.",
            "Druidisme et chamanisme sont des piliers culturels essentiels.",
            "Ils rejoignirent la Horde après l'aide des orcs contre l'agression des centaures.",
            "Une forte culture de la chasse et de la tradition orale préserve leur identité et leur histoire.",
            "À l'époque du Roi-liche, Cairne Sabot-de-sang est l'un des chefs les plus respectés de la Horde.",
        ],
        "worldview": (
            "L'ordre social taurène met l'accent sur le devoir tribal, les anciens et la "
            "révérence envers la Terre-Mère et les ancêtres. Ils valorisent la médiation et la "
            "retenue, mais défendent résolument leurs proches et leur territoire. L'appartenance "
            "à la Horde est présentée comme un serment de gratitude et de défense mutuelle."
        ),
    },
    "Gnome": {
        "traits": [
            "inventifs, curieux, optimistes, analytiques, à l'esprit vif et infatigables sous la pression",
            "sans cesse optimistes, considérant les revers comme des données plutôt que des défaites",
            "obsédés par la technique, portés au jargon et sincèrement ravis par les solutions ingénieuses",
            "vaillants et déterminés, compensant leur petite taille par une confiance démesurée",
            "intellectuellement infatigables, toujours en train de "
            "bricoler des idées même en conversation décontractée",
            "joyeux et excentriques, considérant le danger comme un problème d'ingénierie à résoudre",
            "méthodiques mais spontanés, passant d'une analyse minutieuse à une improvisation débridée",
            "socialement enthousiastes, prompts à expliquer leurs inventions qu'on le leur demande ou non",
        ],
        "flavor_words": [
            "bricolage", "d'après mes calculs", "brillant",
            "Grand Ingénieur", "Mekgineur Escaguette", "Gnomeregan",
            "engrenages", "schémas", "prototype",
            "invention", "calibrage", "bougie d'allumage",
        ],
        "vocabulary": [
            ("For Gnomeregan!", "cri de guerre"),
            ("Salutations!", "salutation formelle"),
            ("My, you're a tall one!", "salutation, humour autodérisoire"),
        ],
        "lore": [
            "Originaires de Gnomeregan, réputés pour leur ingénierie et leurs inventions.",
            "La cité fut perdue lors d'une invasion de trogs et d'une fuite radioactive catastrophique.",
            "Les survivants devinrent des réfugiés accueillis près de Forgefer.",
            "Le Grand Ingénieur Mekgineur Escaguette dirige les efforts de reconquête à l'époque du Roi-liche.",
            "La culture valorise l'expérimentation, l'improvisation et la maîtrise technique.",
            "L'ingénierie couvre la guerre, le transport, la médecine et les outils du quotidien.",
            "Les liens avec l'Alliance sont étroits, en particulier avec les nains de Forgefer.",
        ],
        "worldview": (
            "La culture gnome considère l'ingénierie et la science comme un service civique, pas "
            "seulement une profession. La reconquête de Gnomeregan demeure un objectif politique "
            "fédérateur sous la direction de Gelbin Escaguette. Leur rôle dans l'Alliance se "
            "concentre souvent sur la logistique, l'invention et le soutien technique."
        ),
    },
    "Troll": {
        "traits": [
            "décontractés, spirituels, débrouillards, fiers, adaptables et dangereux si on les provoque",
            "nonchalants en apparence mais farouchement tribaux sous cette attitude désinvolte",
            "rusés et perspicaces, cernant les situations rapidement et s'adaptant sans hésitation",
            "superstitieux et révérencieux envers les loas, tissant leur foi dans les choix du quotidien",
            "fiers de leur héritage Sanglebois, portant l'exil et la survie comme des marques d'identité",
            "détendus et pleins d'humour en compagnie, mais froids et concentrés face à une menace",
            "patients et opportunistes, préférant attendre le bon moment pour frapper",
            "profondément communautaires, valorisant la loyauté envers "
            "la tribu au-dessus de l'ambition ou du confort personnel",
        ],
        "flavor_words": [
            "l'ami", "les esprits", "loa",
            "Sanglebois", "Vol'jin", "Îles de l'Écho",
            "vaudou", "les ancêtres", "chasseur d'ombres",
            "île", "juju", "sacrifice",
        ],
        "vocabulary": [
            ("Taz'dingo!", "cri de guerre / acclamation"),
            ("Spirits be with ya, mon", "adieu/bénédiction"),
            ("Stay away from da voodoo", "avertissement/adieu"),
        ],
        "lore": [
            "Les trolls jouables sont les Sanglebois, non les Amani ni les Gurubashi.",
            "Les Sanglebois furent secourus par Thrall et rejoignirent la Horde.",
            "Le culte des loas, la pratique vaudoue et les traditions de chasseur d'ombres façonnent leur culture.",
            "Vol'jin dirige les Sanglebois dans la politique de l'époque du Roi-liche.",
            "D'anciens empires trolls précèdent nombre des civilisations plus jeunes d'Azeroth.",
            "L'identité sanglebois est façonnée par l'exil, la migration et la survie en marge du monde.",
            "La mémoire tribale et la spiritualité pratique guident les décisions quotidiennes.",
        ],
        "worldview": (
            "La vision du monde des Sanglebois est tribale, tournée vers la survie et guidée par "
            "la tradition des loas. La direction de Vol'jin insiste sur la loyauté envers la "
            "Horde tout en préservant une identité trolle distincte. L'histoire orale, la "
            "pratique de chasseur d'ombres et l'adaptabilité sont des traits culturels essentiels."
        ),
    },
    "Blood Elf": {
        "traits": [
            "fiers, élégants, disciplinés, soucieux de leur image, "
            "tournés vers l'arcanique et émotionnellement réservés",
            "raffinés et posés, masquant un chagrin profond derrière leur maîtrise et leur fierté culturelle",
            "magiquement sensibles et intellectuellement acérés, avec des exigences rigoureuses en tout",
            "politiquement avisés, naviguant les alliances avec grâce tout en accordant peu leur confiance totale",
            "esthétiquement portés, valorisant la beauté et l'ordre comme expressions de l'identité nationale",
            "résilients sous le vernis, forgés par la dépendance, la trahison et la catastrophe nationale",
            "socialement gracieux mais intérieurement intenses, canalisant leur passion dans le devoir et l'artisanat",
            "dignes et maîtres d'eux-mêmes, considérant le calme sous pression comme une obligation morale",
        ],
        "flavor_words": [
            "Sin'dorei", "le Puits de Soleil", "arcanique",
            "Quel'Thalas", "Lune-d'Argent", "seigneur régent",
            "Lor'themar", "mana", "les magistres",
            "chevaliers du sang", "Kael'thas", "la Flèche",
        ],
        "vocabulary": [
            ("Bal'a dash, malanore", "salutations, voyageur"),
            ("Shorel'aran", "adieu"),
            ("Selama ashal'anore", "justice pour notre peuple"),
            ("Anar'alah belore", "par la lumière du soleil"),
            ("Anu belore dela'na", "le soleil nous guide"),
            ("Sinu a'manore", "bien trouvé"),
            ("Doral ana'diel?", "comment te portes-tu ?"),
            ("Al diel shala", "bon voyage"),
        ],
        "lore": [
            "Les Sin'dorei sont les survivants de Quel'Thalas après les ravages du Fléau.",
            "La destruction de leur source sacrée provoqua un sevrage magique et une crise sociale.",
            "L'alliance de Kael'thas avec la Légion s'acheva par une trahison ouverte.",
            "Le Puits de Soleil fut restauré par la Lumière et l'énergie "
            "arcanique vers la fin de l'ère de la Croisade ardente.",
            "Lor'themar Theron gouverne en tant que seigneur régent à l'époque du Roi-liche.",
            "Les chevaliers du sang sont passés de la ponction de "
            "pouvoir au service des sources de Lumière restaurées.",
            "Les liens avec la Horde sont pragmatiques, façonnés par la politique, la mémoire et la survie.",
        ],
        "worldview": (
            "La politique des elfes de sang privilégie la sécurité de Quel'Thalas, la protection "
            "du Puits de Soleil restauré et le contrôle des ressources arcaniques. La culture "
            "publique valorise la discipline et la dignité après le traumatisme national. "
            "L'appartenance à la Horde relève d'une politique d'État pragmatique, façonnée par "
            "l'abandon passé et les menaces actuelles."
        ),
    },
    "Draenei": {
        "traits": [
            "dévots, résilients, contemplatifs, compatissants, anciens et discrètement endurcis par les batailles",
            "patients et clairvoyants, mesurant les événements à l'aune de millénaires d'exil et de perte",
            "profondément croyants, puisant leur force dans les naaru et une foi inébranlable en la Lumière",
            "doux dans leurs manières mais inflexibles sur leurs principes, surtout face à la corruption démoniaque",
            "sages et mesurés, offrant des conseils façonnés par des âges d'errance et de persécution",
            "discrètement affligés sous un extérieur posé, portant leur deuil sans amertume",
            "communautaires et altruistes, plaçant la sécurité des réfugiés "
            "et des alliés au-dessus de leurs besoins personnels",
            "spirituellement disciplinés et martialement compétents, "
            "alliant la prière à la résolution des vindicateurs",
        ],
        "flavor_words": [
            "les naaru", "la Lumière", "Argus",
            "l'Exodar", "Velen", "Draenor",
            "les cristaux", "eredars", "vindicateurs",
            "le Prophète", "l'exil", "la Légion ardente",
        ],
        "vocabulary": [
            ("Archenon poros", "bonne fortune"),
            ("Dioniss aca", "bon voyage"),
            ("Krona ki cristorr!", "la Légion tombera !"),
            ("Pheta vi acahachi!", "Lumière, donne-moi la force !"),
            ("Pheta thones gamera", "Lumière, guide notre chemin"),
        ],
        "lore": [
            "Descendants des eredars exilés menés par le Prophète Velen.",
            "Ils fuirent Argus et endurèrent des millénaires de traque par la Légion.",
            "Arrivés sur Azeroth après le crash de l'Exodar sur Brume-Azur.",
            "Guidés par les naaru, la Lumière et les ordres martiaux des vindicateurs.",
            "L'histoire du Draenor inclut la dévastation causée par "
            "la Horde avant la formation des alliances actuelles.",
            "La société combine foi mystique et technologie cristalline avancée.",
            "Ils portent une mémoire profonde de la perte alliée à un espoir patient et discipliné.",
        ],
        "worldview": (
            "La société draeneï est organisée autour de la direction de Velen, de la vénération "
            "des naaru et de la longue mémoire de l'exil. L'appartenance à l'Alliance sert à la "
            "fois un alignement moral et une défense stratégique contre les vestiges de la "
            "Légion. Leur culture allie technologie cristalline avancée, devoir religieux et "
            "guérison communautaire."
        ),
    },
}

ZONE_FLAVOR = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Alliance Starting Zones
    # -------------------------------------------------------------------------
    1: """Dun Morogh : hautes terres enneigées des nains autour de Forgefer. Des trogs ont
envahi les lieux depuis les profondeurs, et de hostiles trolls des glaces rôdent dans les
montagnes. La vallée de Coldridge est l'endroit où les jeunes nains et gnomes entament leur
voyage. L'air est vif, la bière est forte, et les montagnes résonnent de coups de feu et de
marteaux.""",

    12: """Forêt d'Elwynn : paisibles fermes humaines aux portes de Hurlevent, mais le trouble
couve sous la surface. Les mines grouillent de kobolds qui crient « pas toucher bougie »,
la Confrérie Defias menace les routes, et des gnolls pillent depuis les frontières.
L'auberge de Rive-d'Or est toujours animée. Une zone trompeusement calme où le danger guette.""",

    38: """Loch Modan : région montagneuse dominée par un immense lac. Trogs et kobolds
infestent le secteur, tandis que les nains de Fer noir sèment le trouble près du barrage.
Le grand barrage est une merveille d'ingénierie. Thelsamar est une ville tranquille de
chasseurs et de fouilleurs. Le paysage respire l'atmosphère rude d'une terre frontalière.""",

    40: """La Marche de l'Ouest : autrefois terres fertiles, aujourd'hui poussiéreuses et
abandonnées. La Confrérie Defias contrôle une grande partie de la région depuis sa base
cachée. Des fermiers sans-abri errent sur les routes, des gardiens de récolte mécaniques
patrouillent des champs vides, et des gnolls pillent les abords. La colline des Sentinelles
demeure le dernier bastion de l'ordre.""",

    44: """Les Carmines : territoire humain assiégé. Les orcs de la Roche noire déferlent des
montagnes, des gnolls errent librement, et la ville de Lakeshire tient désespérément bon.
Le pont est constamment menacé. Une zone qui ressemble à un front de guerre, où les
habitants se retrouvent pris entre deux feux.""",

    10: """Bois de la pénombre : forêt maudite, plongée en permanence dans une nuit
éternelle. Des morts-vivants errent dans les bois, des worgens hurlent dans l'obscurité, et
d'immenses araignées guettent partout. La Garde de Nuit de Sombrelune contient à peine ces
horreurs. Une zone troublante où quelque chose de terrible s'est produit et où la terre ne
s'en est jamais remise.""",

    11: """Les Paluns : marécages détrempés reliant les terres naines à Lordaeron. Des
crocolisques et raptors hostiles pullulent partout, les nains de Fer noir complotent dans
les collines, et des draconiens menacent depuis le nord-est. Port-Menethil est une ville
portuaire trempée de pluie. Tout ici est humide et un peu misérable.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Horde Starting Zones
    # -------------------------------------------------------------------------
    85: """Clairières de Tirisfal : forêt hantée entourant les Fossoyeuses. La terre
elle-même semble malade — arbres chétifs, brume verte et morts-vivants agités. Les zélotes
de la Croisade écarlate traquent tout ce qui est mort-vivant, tandis que des zombies
hébétés et des chauves-souris errent librement. Brill est une ville sinistre des
Réprouvés. L'atmosphère est gothique et mélancolique.""",

    130: """Forêt des Pins argentés : bois sombres et brumeux au sud de Tirisfal. Les
worgens ont envahi une grande partie de la forêt, et la présence du Fléau persiste. La
Citadelle de Croc-Ombrageux se dresse, menaçante. Les Réprouvés se battent pour chaque
pouce de territoire. Une zone prise entre plusieurs menaces, qui semble isolée et
dangereuse.""",

    267: """Contreforts de Hautebrande : terres fermières disputées où la Horde et
l'Alliance s'affrontent ouvertement. Rives-Australes et Moulin-Taure sont en conflit
permanent. Des yétis rôdent dans les montagnes, et les bandits du Syndicat causent des
ennuis. Une zone définie par la guerre des factions et de vieilles rancunes.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Mid-Level Zones
    # -------------------------------------------------------------------------
    47: """Les Hinterlands : hautes terres boisées et reculées, foyer des nains
Marteau-hardi et des trolls des forêts pris dans un conflit éternel. Loups et chouettes
géantes parcourent ces contrées sauvages. Pic-de-l'Aire se dresse au sommet d'une falaise
massive. La zone semble indomptée et loin de toute civilisation.""",

    45: """Hautes-terres d'Arathi : prairies vallonnées parsemées de ruines antiques. Le
Syndicat contrôle les ruines de Stromgarde, des ogres habitent les grottes, et des
raptors chassent dans les plaines. Pointe-du-Refuge et Hammerfall s'observent avec
méfiance. Une zone frontalière balayée par le vent, hantée par l'écho de royaumes déchus.""",

    33: """Vallée de Strangleronce : jungle dense et dangereuse, grouillante de vie. Trolls,
pirates, raptors, tigres et gorilles partout. Baie-du-Butin est un port gobelin sans loi
où tout est permis. L'expédition de chasse de Nesingwary attire les aventuriers. La zone
est magnifique mais mortelle — quelque chose veut vous dévorer à chaque détour.""",

    3: """Terres Ingrates : désert âpre et aride de roche rouge et de poussière. Trogs,
coyotes et dragonnets noirs hostiles rendent le voyage périlleux. Des sites
archéologiques épars laissent deviner d'anciens secrets. Kargath est un rude avant-poste
de la Horde. Une zone qui semble désolée et impitoyable.""",

    8: """Marais des chagrins : marécage sombre et déprimant. Des Éperdus errent sans but,
des jaguars traquent dans les eaux, et le Temple d'Atal'Hakkar attire de sombres
adorateurs. Tout ici est mouillé, boueux et légèrement désespéré. Un coin oublié du
monde.""",

    4: """Terres Foudroyées : terre balafrée, corrompue par les énergies de la Porte des
Ténèbres. Démons, faune mutée et créatures démoniaques errent librement. Le sol lui-même
semble contre nature. La forteresse de Nethergarde surveille la Porte avec nervosité. Une
zone qui semble être le bout du monde, là où tout a mal tourné.""",

    51: """Gorge des Vents brûlants : terre volcanique désolée sous le contrôle des nains
de Fer noir. Coulées de lave, élémentaires de feu et fosses de scories dominent le
paysage. Pointe-du-Thorium est un petit avant-poste de résistance. Une chaleur brutale et
un ravage industriel.""",

    46: """Steppes ardentes : les orcs de la Roche noire et les dragons noirs règnent sur
cette terre calcinée. Le Pic de la Roche noire domine les environs. Élémentaires de feu et
draconiens patrouillent. Une zone de guerre de haut niveau où la Horde noire rassemble ses
forces.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands
    # -------------------------------------------------------------------------
    28: """Maleterres de l'Ouest : terres fermières malades, grouillantes de morts-vivants.
Andorhal est une cité en ruines disputée par plusieurs factions. La présence du Fléau est
lourde, et les chaudrons répandent la peste sur la terre. La Croisade écarlate se bat
avec un acharnement fanatique. Une zone de mort, de maladie et de luttes désespérées.""",

    139: """Maleterres de l'Est : le cœur des terres du Fléau. Des morts-vivants partout —
goules, abominations, nécromanciens. Stratholme brûle éternellement, Naxxramas plane
au-dessus. La Chapelle de l'Espoir de la Lumière est le dernier rempart de l'humanité. La
zone la plus corrompue et dangereuse du continent. L'espoir y est rare.""",

    41: """Défilé de Deuillevent : canyon désolé menant à Karazhan. Des ogres de
Deuillevent se tapissent dans les grottes, des esprits agités errent, et la corruption
démoniaque suinte de la tour. La terre elle-même semble vidée de toute vie. Sinistre,
vide et menaçant — quelque chose de terrible s'est produit ici.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Alliance Starting Zones
    # -------------------------------------------------------------------------
    141: """Teldrassil : immense arbre-monde, foyer des elfes de la nuit. Malgré quelques
ennuis avec les farfadets Griffe-Noueuse et les entrelaceurs hostiles, la forêt demeure
d'une beauté à couper le souffle — les arbres anciens rougeoient doucement au crépuscule,
des clairières sacrées scintillent d'une magie persistante, et de tranquilles clairières
invitent à la réflexion. Darnassus repose sereinement au-dessus de la canopée. L'air
porte les murmures d'une magie ancienne. Les elfes de la nuit vaquent à leurs occupations
quotidiennes : entraînement, artisanat, entretien des jardins. Un lieu où la beauté de la
nature persiste même face aux menaces auxquelles les aventuriers doivent faire face.""",

    148: """Sombrivage : long littoral brumeux où le brouillard roule depuis la mer,
créant une atmosphère éthérée. D'anciennes ruines des elfes de la nuit recèlent des
mystères et des légendes oubliées. Auberdine grouille de voyageurs prenant le bateau
pour Teldrassil, Hurlevent ou l'Île de Brume-Azur. Des pêcheurs travaillent sur les
quais, des aventuriers échangent des histoires à l'auberge. Certes, murlocs et naga
sèment le trouble sur les plages, et une partie de la faune est devenue agressive — mais
la beauté envoûtante du littoral demeure. Rivages baignés de lune, architecture antique,
bruit des vagues. Une zone de contrastes : ports paisibles et étendues sauvages
dangereuses, magie ancienne et menaces nouvelles.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Horde Starting Zones
    # -------------------------------------------------------------------------
    14: """Durotar : désert rocailleux et âpre, foyer des orcs. Scorpides, raptors et
sangliers parcourent les canyons rouges. Les quilbêtes pillent depuis le sud, et des
cultistes de la Lame ardente se cachent dans les grottes. Les portes d'Orgrimmar
accueillent les guerriers. Une zone qui incarne la force de la Horde face à l'adversité.""",

    215: """Mulgore : plaines paisibles et vallonnées des taurens. Les kodos paissent
tranquillement, mais des harpies fondent des montagnes et les gobelins de la Compagnie
d'Expédition exploitent la terre. Les Pitons-du-Tonnerre s'élèvent sur leurs mesas. La
zone la plus sereine de la Horde — vastes cieux et vents doux, bien que le danger guette
aux frontières.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Mid-Level Zones
    # -------------------------------------------------------------------------
    331: """Ashenvale : forêt ancienne des elfes de la nuit assiégée. La Horde progresse
depuis l'est, des démons se tapissent dans les ombres, et les farfadets ont sombré dans
la folie. Astranaar et l'avant-poste de l'Arbre-Fendu incarnent le conflit des factions.
Une belle forêt marquée par la guerre et la corruption.""",

    405: """Desolace : désolation grise et aride. Les tribus centaures se font
inlassablement la guerre entre elles et à tout le reste. Des cimetières de kodo
parsèment le paysage. La zone semble vide et sans espoir — même le ciel semble privé de
couleur. L'un des endroits les plus déprimants d'Azeroth.""",

    400: """Mille pointes : canyon spectaculaire d'imposants pics rocheux. Avant le
Cataclysme, un fond désertique aride avec le circuit des Plaines Scintillantes. Centaures
et harpies contrôlent divers piliers. Le Grand Ascenseur relie la zone aux Tarides.
Visuellement saisissant mais rude à traverser.""",

    15: """Marécage d'Aprefange : marécage chaud et humide. Des dragons noirs complotent
au sud, crocolisques et araignées hostiles se tapissent dans la vase, et Theramore se
dresse en bastion de l'Alliance. Les ruines d'une auberge incendiée laissent deviner de
sombres complots. Étouffant et dangereux.""",

    357: """Feralas : jungle et forêt luxuriante et envahissante. Yétis dans les
montagnes, naga sur la côte, ogres et gnolls partout. Les Jumeaux Colossaux sont
d'immenses arbres, et les ruines de Dfirmaul se dressent au loin. Une zone sauvage et
indomptée qui engloutit les voyageurs.""",

    440: """Tanaris : désert brûlant entourant le port gobelin de Gadgetzan. Pirates,
bandits, basilics et silithides partout. Les trolls de Zul'Farrak sont hostiles. Les
Cavernes du Temps se cachent à proximité. Torride le jour, ce désert est impitoyable
mais rentable.""",

    16: """Azshara : littoral en ruines des elfes de la nuit, d'une beauté envoûtante mais
désert. Les naga contrôlent une grande partie de la côte, et le clan draconique Bleu y
maintient une présence. D'immenses créatures marines rôdent, et des vestiges de la
Légion s'attardent au Rebord de l'Oubli. La zone semble abandonnée et triste — un
monument à ce qui a été perdu.""",

    361: """Gangrebois : forêt corrompue suintant de souillure démoniaque. Limons, satyres
et faune corrompue infestent chaque recoin. Les arbres eux-mêmes semblent malades. Les
farfadets Poil-des-Bois se méfient mais restent neutres ; les farfadets Bois-mort sont
hostiles. Une zone qui donne l'impression de se salir rien qu'en la traversant.""",

    490: """Cratère d'Un'Goro : jungle préhistorique en cratère grouillant de dinosaures.
Les diablosaures sont les prédateurs suprêmes, les raptors chassent en meute, et des
élémentaires gardent des pylônes. C'est comme remonter le temps — luxuriant, dangereux
et plein d'émerveillement. Des formations cristallines recèlent un pouvoir mystérieux.""",

    493: """Reflet-de-Lune : sanctuaire sacré des druides. Largement paisible et sûr, avec
peu de créatures hostiles. Le Cercle Cénarien s'y rassemble, et la zone semble
intemporelle et sereine — un répit loin du chaos du monde. Les druides se retrouvent à
Havre-Nocturne.""",

    618: """Berceau-de-l'Hiver : hautes terres gelées d'un hiver éternel. Chats-frimas,
yétis et géants de glace parcourent la neige. Guet-Nordique est une ville gobeline aux
affaires douteuses. Les farfadets Feuille-de-Givre sont hostiles sur tout le territoire.
Magnifique mais mortellement froid, la zone ne récompense que les bien préparés.""",

    1377: """Silithus : désert désolé grouillant de silithides. La menace qiraji plane
depuis Ahn'Qiraj. Les druides du Cercle Cénarien luttent désespérément contre l'essaim.
Tempêtes de sable, insectes géants et une sensation écrasante que quelque chose d'ancien
et de maléfique s'agite sous les sables.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Péninsule des Flammes Infernales : terre rouge brisée, première zone
franchie après la Porte des Ténèbres. Orcs corrompus, démons et forces de la Légion
ardente partout. Fort de l'Honneur et Thrallmar sont les bases des factions. Le ciel est
déchiré, le sol est fissuré, et la guerre fait rage sans relâche. Une introduction
brutale à l'Outreterre.""",

    3521: """Marécage de Zangar : marais champignonnesque surréaliste, luisant de
bioluminescence. D'immenses champignons dominent les lieux, des sporebêtes volent
paresseusement, et les naga drainent les eaux. Le Refuge Cénarien œuvre à sauver
l'écosystème. Étrangement magnifique et étranger — rien ici ne ressemble à Azeroth.""",

    3518: """Nagrand : îles flottantes et plaines vertes luxuriantes — le dernier paradis
de l'Outreterre. Fendragons et talbukins paissent paisiblement, mais des ogres et la Lame
ardente menacent cette terre. Garadar et Telaar incarnent les factions. La plus belle
zone de l'Outreterre, un rappel de ce que le Dranor fut jadis.""",

    3519: """Forêt de Terokkar : partagée entre forêt luxuriante et étendues jonchées
d'ossements autour d'Auchindoun. Des arakkoas se tapissent dans les arbres, et le Conseil
des Ombres mène de sombres rituels. Shattrath est la capitale neutre. Une zone de
contrastes entre vie et mort.""",

    3522: """Les Tranchantes : paysage escarpé et hostile de pics vertigineux. Les ogres y
règnent, et les géants gronn sont les prédateurs suprêmes. La Légion ardente y maintient
des avant-postes, et des dragons décrivent des cercles au-dessus. Un terrain dangereux où
la terre elle-même semble vouloir vous tuer.""",

    3520: """Vallée d'Ombrelune : terre sombre, corrompue par la Légion. Le Temple noir se
dresse, menaçant, et les forces d'Illidan contrôlent la région. Démons, orcs corrompus et
chevaliers de la mort patrouillent. Le ciel brûle d'un vert malsain. La zone la plus
dangereuse et oppressante de l'Outreterre — l'espoir y semble lointain.""",

    3523: """Raz-de-néant : îles brisées flottant dans le Néant Distordu. Des forges de
mana récoltent l'énergie de la terre, elfes de sang et éthérés se disputent les
ressources, et des créatures de mana errent en liberté. Les éco-dômes préservent la vie
artificiellement. Une zone qui se déchire elle-même aux coutures.""",

    3524: """Île de Brume-Azur : île paisible des draeneï, baignée d'une douce lumière
azur et du bourdonnement de la technologie cristalline. Le site du crash de l'Exodar
luit encore d'une énergie résiduelle, et les survivants draeneï pansent leurs blessures
et rebâtissent. Faune douce, bassins scintillants et ruines cristallines côtoient les
débuts pleins d'espoir d'un peuple déplacé qui reprend pied dans un monde nouveau.""",

    3525: """Île de Brume-Sang : île jumelle de Brume-Azur, teintée de rouge par les
cristaux corrompus de l'épave de l'Exodar. L'énergie démoniaque a transformé la faune
locale en prédateurs dangereux et muté la végétation. Elfes de sang et démons œuvrent à
corrompre davantage la terre. Un lieu de beauté devenu sinistre, où les draeneï doivent
affronter les dégâts causés par le crash de leur propre vaisseau.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Toundra Boréenne : toundra côtière gelée, l'un des deux points d'entrée au
Norfendre. Des nérubiens creusent sous terre, le Fléau sonde les défenses, et des tuskarr
pêchent le long des côtes. Fort-Chant-de-Guerre et Fort Valeur sont les bastions des
factions. Le froid mord fort — et l'hiver ne fait que commencer.""",

    495: """Fjord Hurlant : littoral spectaculaire d'inspiration viking aux falaises
imposantes. Des guerriers vrykuls attaquent depuis leurs villages, et le Fléau corrompt
les morts. Valgarde et le Débarcadère de la Vengeance sont les points d'accostage. Les
fjords coupent le souffle mais les vrykuls sont implacables.""",

    394: """Les Grisonnes : frontière boisée presque paisible. Farfadets corrompus par le
Fléau, nains de fer fouillant pour des secrets, et la malédiction des worgens qui se
propage. Des exploitations forestières balafrent les collines. Une zone qui serait belle
sans la corruption rampante.""",

    3711: """Bassin de Sholazar : jungle luxuriante en cratère, épargnée par le Fléau et
entretenue par la technologie des titans. Dinosaures, gorilles et bêtes exotiques y
prospèrent. Les Cœurs Frénétiques et les Oracles se livrent une guerre mesquine. Un
paradis inattendu dans le Norfendre glacé — mais quelque chose menace les pylônes.""",

    66: """Zul'Drak : royaume troll gelé en pleine chute. Les Drakkari sacrifient leurs
propres dieux pour combattre le Fléau. Morts-vivants et trolls désespérés s'affrontent
partout. La zone donne l'impression d'assister à l'agonie d'une civilisation — sombre,
froide et sans espoir.""",

    67: """Pics Foudroyés : montagnes gelées et imposantes, gardiennes des secrets des
titans. Géants des tempêtes, nains de fer et proto-drakes y dominent. L'entrée d'Ulduar
se dresse au-dessus. Les Fils de Hodir se méfient des étrangers. Échelle épique,
conditions brutales, mystères anciens.""",

    210: """Couronne de Glace : le domaine du Roi-liche. Armées interminables de
morts-vivants, forteresses nécropoles et la Citadelle de la Couronne de Glace
elle-même. La Croisade argentée fait son dernier combat. L'air lui-même semble mort.
C'est le bout du chemin — victoire ou néant.""",

    # -------------------------------------------------------------------------
    # Capital Cities
    # -------------------------------------------------------------------------
    1519: """Hurlevent : la grande capitale humaine, reconstruite après la Première
Guerre. La grande cathédrale domine l'horizon, les canaux serpentent entre les quartiers
de pierre, et le quartier marchand ne dort jamais. Des gardes patrouillent partout. Le
port relie la ville à des terres lointaines. Le roi Varian Wrynn règne depuis le Château
de Hurlevent. Une ville de pavés, de bannières et de fierté civique — le cœur de
l'Alliance.""",

    1537: """Forgefer : la grande cité naine taillée dans le cœur d'une montagne. Une
immense forge de métal en fusion domine le centre, entourée du quartier de la Grande
Forge où des maîtres forgerons martèlent jour et nuit. L'air est chaud et embaume le fer
et la bière. Des tunnels mènent au Quartier militaire, au Quartier mystique et au tramway
souterrain vers Hurlevent. Solide, ancienne, et bâtie pour durer toujours.""",

    1657: """Darnassus : la sereine capitale des elfes de la nuit, au sommet de
l'arbre-monde Teldrassil. D'anciens arbres se voûtent au-dessus, une douce lumière
violette filtre à travers la canopée, et des bassins immobiles reflètent les étoiles même
en plein midi. Le Temple de la Lune honore Elune. Les druides méditent dans l'Enclave
Cénarienne. La ville semble intemporelle et paisible, loin des guerres d'en bas — bien
que cette paix soit plus fragile qu'il n'y paraît.""",

    3557: """L'Exodar : le vaisseau interdimensionnel écrasé des draeneï, désormais
reconverti en leur capitale. Des pylônes de cristal bourdonnent d'une énergie
d'un autre monde, une lumière pourpre et bleue baigne des corridors géométriques, et un
sanctuaire radieux luit en son cœur. L'architecture est étrangère et magnifique — mi-
cathédrale, mi-vaisseau spatial. Les draeneï poursuivent leur vie avec une dignité
tranquille, se reconstruisant après un long voyage de plus.""",

    1637: """Orgrimmar : la brutale capitale orque taillée dans des canyons désertiques
rouges. Piques de fer, bannières de guerre et portes massives définissent l'horizon. La
Vallée de la Force résonne des grognements de guerriers en entraînement et du vacarme de
l'hôtel des ventes. L'héritage de Thrall imprègne l'air. La ville est brute, bruyante et
sans excuses agressive — une forteresse bâtie pour un peuple qui s'attend toujours à la
guerre.""",

    1638: """Pitons-du-Tonnerre : la capitale taurène bâtie sur d'imposantes mesas reliées
par des ponts de corde au-dessus des plaines de Mulgore. Le vent balaie les plateformes
à ciel ouvert. Totems et peaux décorent chaque structure. L'Élévation des Anciens
accueille les druides, l'Élévation des Esprits les prêtres. Cairne Sabot-de-sang règne
avec une sagesse ancestrale. La capitale la plus paisible de la Horde — ciel, vent, herbe
et la force tranquille d'un peuple ancien.""",

    1497: """Les Fossoyeuses : la capitale des Réprouvés sous les ruines de Lordaeron.
Une cité souterraine sombre et circulaire où les morts-vivants mènent leur existence
parmi des canaux de vase verte et des torches vacillantes. Le Quartier royal abrite
Sylvanas Coursevent. Les apothicaires concoctent de douteux breuvages. L'air est humide,
froid et légèrement toxique. Sinistre, fonctionnelle et troublante — mais un foyer pour
ceux qui n'ont nulle part ailleurs où aller.""",

    3487: """Lune-d'Argent : la capitale des elfes de sang, à moitié reconstruite après
l'invasion du Fléau. La moitié occidentale, en activité, brille de flèches cramoisies et
dorées, des gardiens arcaniques patrouillent des rues impeccables, et des fontaines
coulent d'énergie magique. Les ruines orientales demeurent une cicatrice. La culture
sin'dorei prise la beauté, la magie et le raffinement. Une ville élégante masquant de
profondes blessures et une dépendance désespérée au pouvoir arcanique.""",

    3703: """Shattrath : la cité neutre des draeneï dans la Forêt de Terokkar, désormais
partagée entre les factions Aldor et Voyants. La Terrasse de Lumière brille en son
centre de la radiance des naaru. Des réfugiés venus de toute l'Outreterre affluent dans
la Cité basse. Alliance et Horde arpentent ces rues dans une trêve précaire. Un carrefour
cosmopolite où toutes les races se mêlent — mi-sanctuaire, mi-poudrière politique.""",
}

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'Le conflit des montagnes gelées — les nains de l\'Expédition Pic-de-Tempête '
            'contre les orcs du clan Loup-de-givre dans les montagnes d\'Alterac.'
        ),
        'tone': (
            'Épique, à grande échelle, guerrier. Le 40 contre 40 ressemble à une '
            'véritable bataille.'
        ),
        'objectives': (
            'Tuez le général ennemi. Capturez les tours et les cimetières.'
        ),
        'landmarks': (
            'Lieux clés : Base de Pic-de-Tempête, Dun Baldar, Bunker Aile-de-glace, '
            'Cimetière du Foyer-de-Pierre, Cimetière de Chute-de-neige, Tour de '
            'Sang-glacé, Pointe de la Tour, Cimetière du Loup-de-givre, Fort du '
            'Loup-de-givre. NE mentionnez PAS de lieux appartenant à d\'autres '
            'champs de bataille.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'La guerre du bois dans Ashenvale — les Sentinelles Aile-d\'argent défendent la '
            'forêt, les Éclaireurs Cri-de-guerre convoitent ses ressources.'
        ),
        'tone': (
            'Intense, rapide, personnel. Petite équipe, chaque joueur compte.'
        ),
        'objectives': 'Capturez le drapeau ennemi 3 fois.',
        'landmarks': (
            'Lieux clés : Bastion Aile-d\'argent (base de l\'Alliance), Fort Cri-de-guerre '
            '(base de la Horde), le tunnel, le milieu du terrain, la rampe. NE mentionnez '
            'PAS de lieux appartenant à d\'autres champs de bataille comme les moulins, '
            'les fermes ou les tours.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'La lutte pour les ressources des Hautes-terres d\'Arathi entre Stromgarde et '
            'les Réprouvés.'
        ),
        'tone': (
            'Stratégique, territorial, dispersé. Des réactions centrées sur le contrôle '
            'des points.'
        ),
        'objectives': 'Contrôlez les points pour atteindre 1600 ressources en premier.',
        'landmarks': (
            'Lieux clés : les Écuries (au nord, pâturages ouverts avec des enclos à '
            'chevaux), la Forge (carrefour central, fumée et enclumes), la Scierie '
            '(surplomb au sommet d\'une colline, plateformes en bois et scies), la Mine '
            'd\'or (entrée de grotte au sud-est, wagonnets et torches), la Ferme (au sud, '
            'champs et meules de foin près d\'une ferme). NE mentionnez PAS de lieux '
            'appartenant à d\'autres champs de bataille.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': 'Un champ de bataille de Raz-de-néant au-dessus d\'un fragment du Draenor.',
        'tone': (
            'Tension hybride. Tenir les bases tout en se battant pour un drapeau central.'
        ),
        'objectives': (
            'Contrôlez les bases et capturez le drapeau central pour atteindre 1600 points.'
        ),
        'landmarks': (
            'Lieux clés : Ruines du Ravageur ardent, Tour des elfes de sang, Ruines '
            'draeneï, Tour des mages, le drapeau central. NE mentionnez PAS de lieux '
            'appartenant à d\'autres champs de bataille.'
        ),
    },
}

DUNGEON_FLAVOR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Château de Croc-Ombrageux : forteresse hantée dans la Forêt des Pins argentés, envahie par
les worgens et les serviteurs morts-vivants du nécromancien Arugal. Des nobles
fantomatiques errent dans les couloirs obscurs, des chiens spectraux hurlent dans les
cours, et des expériences arcaniques ratées se tapissent dans chaque ombre. Le château
évoque un roman d'épouvante gothique — pierre froide, lueur vacillante des torches, et
l'impression constante d'être observé.""",

    34: """La Prison : geôle sous Hurlevent où les détenus se sont révoltés et en ont pris le
contrôle. Émeutiers Defias, forçats déments et chefs de gang errent dans les blocs
cellulaires exigus. Le donjon est claustrophobe et brutal — couloirs étroits, barreaux de
fer, et les bruits de violence qui résonnent sur les murs humides. Rapide, sale et
dangereux.""",

    36: """Les Mines de Fer : vaste complexe minier sous la Marche de l'Ouest, secrètement le
quartier général de la Confrérie Defias. Le chemin serpente à travers des tunnels aménagés
par des gobelins, des scieries et des fonderies avant de déboucher dans une immense
caverne souterraine où un navire pirate grandeur nature repose dans une crique cachée. On
a l'impression de découvrir un empire criminel juste sous le nez de Hurlevent.""",

    43: """Cavernes des Lamentations : labyrinthe de cavernes sinueuses dans les Tarides, envahi
d'une végétation luxuriante nourrie par une magie druidique corrompue. Des créatures
dévoyées — raptors mutés, serpents et vases — se faufilent dans les tunnels aux teintes
émeraude. Les Druides du Croc se sont perdus dans le Cauchemar d'Émeraude. L'air est
épais, humide, et sent la pourriture de la jungle.""",

    47: """Les Épines de Razorfen : labyrinthe épineux né d'immenses ronciers dans les Tarides, foyer
des quilbêtes et de leur matriarche Charlga Griffedéchirante. Guerriers et chamans
quilbêtes, accompagnés de leurs sangliers, remplissent les couloirs sinueux tapissés
d'épines. Le donjon semble primitif et féral — la nature tordue en une forteresse d'os,
d'épines et de boue.""",

    48: """Les Profondeurs de Fangelombre : temple ancien partiellement submergé sur la côte de
Sombrivage, consacré à de sombres puissances. Naga, satyres et cultistes du crépuscule
vénèrent d'anciens dieux dans des salles inondées, ornées d'une architecture elfique en
ruine. L'eau luit d'un bleu-vert inquiétant, et l'atmosphère est oppressante et ancienne —
quelque chose de puissant dort dans les bassins les plus profonds.""",

    70: """Uldaman : site de fouilles des titans enfoui dans les Terres Ingrates, à mi-chemin entre
le chantier archéologique et le donjon. Trogs de pierre, golems terreux et dangers
archéologiques emplissent des chambres de métal titanesque poli et de roche brute. Plus on
descend, plus l'architecture devient étrangère — salles géométriques lisses bourdonnant
d'une puissance endormie. On a l'impression de s'introduire dans une bibliothèque bâtie
par des dieux.""",

    90: """Gnomeregan : les ruines irradiées de la capitale gnome, perdue lors d'une invasion de
trogs et d'une fuite radioactive catastrophique. Des gnomes lépreux déments, des robots
défaillants et des vases toxiques peuplent le complexe mécanique à niveaux multiples. Les
sirènes d'alarme retentissent, des flaques de radiations vertes luisent, et des machines
brisées étincellent partout. À la fois tragique et absurde.""",

    109: """Temple immergé : le Temple d'Atal'Hakkar, un temple troll entraîné sous les marais par le
clan draconique Vert. Les trolls Atal'ai vénèrent le dieu du sang Hakkar dans des salles
inondées et envahies de lianes. Des draconiens gardent les niveaux profonds, et
l'agencement labyrinthique désoriente. L'atmosphère est saturée d'humidité de jungle,
d'ancienne magie trolle et d'un sentiment de rituel interdit.""",

    129: """Nécropole de Razorfen : cimetière quilbête dans les Tarides, infesté de morts-vivants.
L'agent du Fléau Amnennar le Porteur-de-froid a relevé les quilbêtes morts, transformant
leurs cryptes sacrées en une nécropole d'os et d'épines. Quilbêtes squelettiques et
chauves-souris pestiférées remplissent les couloirs lugubres. Un lieu où deux formes de
mort entrent en collision — primitive et nécromantique.""",

    189: """Monastère écarlate : monastère fortifié dans les Clairières de Tirisfal, bastion de la
fanatique Croisade écarlate. Quatre ailes abritent une bibliothèque de textes interdits,
un arsenal grouillant de zélotes, une cathédrale d'une foi dévoyée, et un cimetière hanté.
Les croisés sont bien armés, disciplinés et complètement fous — convaincus que tout le
monde est secrètement mort-vivant. Une architecture magnifique dissimulant un fanatisme
meurtrier.""",

    209: """Zul'Farrak : cité trolle à moitié ensevelie dans les sables de Tanaris, foyer des trolls
Sablefurie hostiles. Temples de pierre baignés de soleil, autels sacrificiels et cours
sablonneuses composent ce donjon à ciel ouvert. La célèbre bataille de l'escalier vous
oppose à des vagues de guerriers trolls. La chaleur du désert est implacable, les trolls
sont sauvages, et une magie ancienne crépite à travers les ruines.""",

    229: """Spire de la Roche noire : immense forteresse orque taillée dans les hauteurs de la
montagne de la Roche noire. La spire basse grouille d'orcs de la Roche noire, d'ogres et
de trolls, tandis que la spire haute est le siège du chef de guerre Rend Main-Noire et de
ses alliés draconiques. La lave luit en contrebas, les tambours de guerre résonnent sans
cesse, et l'air empeste la fumée et le sang. Un vaste bastion militaire au cœur de la
Horde noire.""",

    230: """Profondeurs de Roche noire : vaste cité des nains de Fer noir au cœur de la montagne de la
Roche noire, bâtie autour d'un lac de lave en fusion. La taverne du Gargouillis lugubre,
la salle du trône de l'Empereur et le seuil du Cœur du Magma se trouvent tous ici.
Élémentaires, golems et nains de Fer noir fanatiques peuplent une métropole souterraine
d'une ampleur incroyable. On croirait qu'une civilisation entière existe là, sombre,
industrieuse et hostile.""",

    269: """Le Marais Trouble-Temps : instance des Cavernes du Temps se déroulant dans le marécage
primordial qui deviendra les Terres Foudroyées. Des agents du clan draconique Infini
tentent d'empêcher Medivh d'ouvrir la Porte des Ténèbres, et des vagues de draconiens
attaquent à travers des failles temporelles. Le marais est sombre, embrumé et primitif, et
l'énergie de la Porte crépite au loin. Le temps lui-même semble instable ici.""",

    289: """Salle d'Examen de la Mort : académie nécromantique dans les cryptes sous Caer Darrow,
dirigée par le Culte des Damnés. Étudiants et professeurs de magie noire pratiquent leur
art sur les morts comme sur les vivants. Squelettes, fantômes et golems de chair
remplissent salles de classe et laboratoires. Le donjon dégage une atmosphère
universitaire perverse — amphithéâtres et bibliothèques entièrement voués à la magie de la
mort.""",

    329: """Stratholme : les ruines embrasées d'une cité jadis grande, à jamais en flammes depuis
qu'Arthas l'a purgée. Le Fléau mort-vivant contrôle la moitié orientale tandis que la
Croisade écarlate tient fanatiquement les portes occidentales. Les bâtiments s'effondrent
dans un feu perpétuel, des abominations traînent dans les rues, et les cendres ne se
déposent jamais. Un monument à la tragédie et à la folie — chaque coin de rue porte le
souvenir du massacre.""",

    349: """Maraudon : système de cavernes sacrées à Desolace, altéré par la princesse Theradras et
ses descendants centaures après la mort du gardien Zaetar. Trois voies codées par couleur
serpentent à travers des grottes de cristal, des cascades empoisonnées et de luxuriants
jardins souterrains avant d'atteindre le sanctuaire intérieur. Les chambres les plus
profondes sont d'une beauté envoûtante — cristaux luminescents, bassins limpides, et une
ancienne magie terrestre luttant contre la corruption. Nature, deuil et fureur élémentaire
s'y entremêlent.""",

    389: """Gouffre de Cendre-brûlante : réseau de cavernes volcaniques sous Orgrimmar même, où
cultistes de la Lame ardente et trogs se sont installés. La lave coule à travers d'étroits
tunnels, des élémentaires de feu patrouillent, et la chaleur est suffocante. Court et
brutal — le genre d'endroit qui rappelle que la Horde a bâti sa capitale sur un volcan.""",

    429: """Donjon de Feu-Sombre : cité en ruines des Éveillés dans Feralas, divisée en trois ailes.
Les ogres ont revendiqué le nord, satyres et anciens corrompus infestent l'est, et des
esprits Éveillés fantomatiques hantent la bibliothèque de l'aile ouest. Une architecture
elfique en ruine, d'une beauté saisissante, succombe lentement à l'envahissement de la
jungle. Le donjon semble vaste, ancien et mélancolique — le cadavre d'une grande
civilisation dépecé par des squatteurs.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Repaire d'Onyxia : une unique et vaste caverne dans le Marécage d'Aprefange, foyer de la
reine-mère Onyxia. L'approche serpente à travers un étroit tunnel de roche calcinée avant
de s'ouvrir sur une chambre immense, jonchée d'ossements et de couvées d'œufs. Les
dragonnets pullulent, la lave bouillonne sur les bords, et Onyxia elle-même emplit la
caverne de feu et d'ombre. Un tunnel claustrophobe menant à une arène écrasante de feu
draconique.""",

    309: """Zul'Gurub : vaste complexe de temples trolls dans les jungles de Strangleronce, où la
tribu Gurubashi a déchaîné le dieu du sang Hakkar. Cours envahies de végétation, autels
sacrificiels et places grouillantes de bêtes entourent un temple central suintant de magie
sanglante. Prêtres serpents, monteurs de chauves-souris et cultistes-tigres servent leurs
sombres maîtres. La jungle elle-même semble pulser d'une énergie vaudou primitive.""",

    409: """Le Cœur du Magma : le cœur ardent de la montagne de la Roche noire, un royaume de feu pur
gouverné par Ragnaros le Seigneur du Feu. Des rivières de lave coulent entre des
plateformes d'obsidienne, élémentaires de feu et géants de magma patrouillent partout, et
la chaleur est apocalyptique. Des molosses du Cœur à plusieurs têtes, d'imposants geysers
de lave et d'anciens éveilleurs de flammes gardent leur maître. L'ultime épreuve du feu —
belle et terrifiante à parts égales.""",

    469: """Repaire de l'Aile Noire : le bastion de Nefarian au sommet de la Spire de la Roche noire,
un laboratoire ténébreux où le dragon noir expérimente sur d'autres clans draconiques.
Soldats draconides, drakes chromatiques et expériences ratées emplissent des salles de fer
noir et d'os de dragon. Chaque chambre présente un défi tactique unique. Le raid dégage
une atmosphère clinique et sinistre — le repaire d'un savant fou à l'échelle d'un dragon.""",

    509: """Ruines d'Ahn'Qiraj : champ de bataille à ciel ouvert à Silithus où les forces qiraji se
rassemblent pour la guerre. Guerriers insectoïdes, destructeurs d'obsidienne et créatures
géantes en forme de scarabée déferlent sur des cours balayées par le sable et des ruines
de temples effondrées. L'architecture est étrangère et chitineuse, à mi-chemin entre
tombeau égyptien et ruche d'insectes. Le vent du désert porte le cliquetis d'un million de
pattes.""",

    531: """Temple d'Ahn'Qiraj : le sanctuaire intérieur scellé de l'empire qiraji, un cauchemar
d'architecture étrangère et de corruption des dieux anciens. Les empereurs jumeaux, une
royauté silithide massive, et le dieu ancien C'Thun lui-même se tapissent en son sein. Les
murs pulsent d'une croissance organique, des yeux observent depuis chaque surface, et la
réalité se déforme près de la prison du dieu ancien. L'endroit le plus étranger et le plus
dérangeant de l'Azeroth classique.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Salles brisées : le bastion des orcs corrompus au sein de la Citadelle des Flammes
Infernales, un parcours sanglant à travers les serviteurs les plus fanatiques de la Légion
ardente. Gladiateurs, légionnaires et berserkers orcs corrompus emplissent chaque couloir,
avec des prisonniers enchaînés aux murs. L'architecture est faite de fer brutal et de
pierre rouge, marquée par les traces d'une violence constante. Un assaut incessant contre
une forteresse qui riposte à chaque pas.""",

    542: """Fournaise ardente : une usine démoniaque au sein de la Citadelle des Flammes Infernales où
l'on fabrique des orcs corrompus par de sombres rituels. Cuves de sang bouillonnant,
prisonniers enchaînés attendant leur transformation, et machinerie démoniaque emplissent
des chambres fumantes. De jeunes orcs corrompus et leurs surveillants gardent les chaînes
de production. Le donjon empeste le sang et le soufre — un spectacle d'horreur
industrielle.""",

    543: """Remparts des Flammes Infernales : les fortifications extérieures de la Citadelle des
Flammes Infernales, première ligne de défense de l'armée des orcs corrompus. Tours de
guet, créneaux et passerelles étroites offrent une vue panoramique sur la Péninsule des
Flammes Infernales brisée en contrebas. Soldats orcs corrompus, monteurs de worgs et un
dragon captif gardent les murailles. Le vent hurle à travers les remparts brisés, et le
ciel rouge de l'Outreterre s'étend à l'infini au-dessus.""",

    545: """La Cuve à Vapeur : une station de pompage contrôlée par les naga dans le Réservoir de
Nasseau, où les forces de Dame Vashj drainent le Marécage de Zangar. D'immenses tuyaux,
vannes et canaux d'eau dominent cette structure industrielle. Naga, seigneurs des marais
et élémentaires d'eau gardent la machinerie. La vapeur siffle à chaque jointure et le
grondement des eaux vives est assourdissant. Un donjon qui donne l'impression de saboter
une usine ennemie.""",

    546: """Le Marais souterrain : marécage en putréfaction sous le Réservoir de Nasseau, grouillant
de créatures fongiques mutées et d'esprits de la nature hostiles. Géants sporifères,
seigneurs des marais et faune venimeuse emplissent les cavernes envahies de végétation.
Des champignons bioluminescents projettent une lueur inquiétante sur les eaux stagnantes.
L'air est chargé de spores et d'une odeur de décomposition — la nature devenue sauvage et
hostile.""",

    547: """Les Enclos des esclaves : les camps de travail du Réservoir de Nasseau où les draeneï
Corrompus sont retenus captifs par des maîtres esclavagistes naga. Tunnels détrempés,
enclos rudimentaires et surveillants naga armés de fouets définissent l'atmosphère. Des
croissances fongiques et des créatures des marais ont infiltré le complexe. Un donjon
empreint de misère et d'oppression, à moitié noyé et putréfié.""",

    552: """L'Arcatraz : une prison dimensionnelle satellite de la Citadelle des Tempêtes, retenant
les entités les plus dangereuses du cosmos. Des démonistes eredars, des créatures du Néant
et des saboteurs elfes de sang rôdent dans des blocs cellulaires conçus pour contenir des
horreurs indescriptibles. L'architecture est une technologie cristalline draeneï dévoyée
par ses détenus. Chaque porte de cellule dépassée vous fait vous demander ce qui s'est
échappé — et ce qui est encore enfermé à l'intérieur.""",

    553: """La Botanique : un vaste biodôme satellite de la Citadelle des Tempêtes, où l'on cultivait
jadis une flore exotique venue de tout le cosmos. Les elfes de sang se sont emparés de
l'installation, et les plantes ont poussé à l'état sauvage et hostile. Fouettards,
chênerons et spécimens botaniques étrangers emplissent des serres de cristal scintillant.
Magnifique mais mortel — chaque fleur pourrait vous tuer, et les elfes de sang sont pires
encore.""",

    554: """Le Mécanar : une aile de fabrication de la Citadelle des Tempêtes, désormais contrôlée par
des ingénieurs elfes de sang et leurs créations mécaniques. Constructs arcaniques,
ravageurs corrompus et surveillants némancien gardent des couloirs de cristal étincelant
et de machinerie bourdonnante. La technologie est élégante et étrangère — une ingénierie
draeneï détournée à des fins sinistres. Tout bourdonne d'une énergie arcanique à peine
contenue.""",

    555: """Labyrinthe des Ombres : l'aile la plus profonde d'Auchindoun, où le Conseil des Ombres
mène ses rituels les plus sombres. Marcheurs du Néant, incantateurs corrompus et cultistes
de la Cabale vénèrent dans des chambres saturées de magie des ombres. Murmure, un
élémentaire du son primordial, est enchaîné dans la chambre la plus profonde. L'obscurité
y semble vivante et affamée — les ombres bougent d'elles-mêmes, et des chuchotements
viennent de partout et de nulle part.""",

    556: """Salles de Sethekk : salles-temples arakkoa au sein d'Auchindoun, occupées par des
fanatiques dévoués au Dieu-corbeau Anzu. Prêtres arakkoa déments, esprits invoqués et
gardiens spectraux emplissent des couloirs jonchés de plumes. L'architecture mêle les
styles draeneï et arakkoa de façon troublante. Les habitants ont sombré dans une folie
totale, et les salles résonnent de cris déments et de sombres prophéties.""",

    557: """Les Tombeaux de Mana : l'aile infestée d'éthérés d'Auchindoun, où le consortium du
prince-nexus Shaffar pille les caveaux funéraires draeneï. Bandits éthérés, constructs
arcaniques et esprits draeneï agités s'affrontent dans des chambres funéraires
cristallines. Les tombeaux luisent d'une énergie sacrée résiduelle tandis que les éthérés
la siphonnent. Un lieu sacré systématiquement pillé par des voleurs interdimensionnels.""",

    558: """Cryptes des Auchenaï : les lieux funéraires draeneï sous Auchindoun, où les prêtres
auchenaï ont sombré dans la folie en communiant avec les morts. Esprits agités, clercs
possédés et draeneï morts-vivants emplissent les cryptes tapissées d'ossements. Ce qui fut
jadis un lieu de recueillement respectueux est devenu un charnier. La tragédie est
palpable — ces gardiens se sont perdus dans le chagrin.""",

    560: """Contreforts de Hautebrande d'antan : instance des Cavernes du Temps se déroulant dans le
passé, quand Thrall était encore esclave au fort de Durnholde. Le Hautebrande d'autrefois
est verdoyant, paisible et peuplé d'humains insouciants vaquant à leur vie. Le clan
draconique Infini tente d'altérer l'histoire en empêchant l'évasion de Thrall. C'est
surréaliste — traverser un lieu qu'on connaît avant que tout ne tourne mal.""",

    568: """Zul'Aman : bastion des trolls des forêts dans les Terres fantômes, où le seigneur de
guerre Zul'jin a doté ses champions de l'essence de dieux animaux. Esprits de lynx,
d'ours, d'aigle et de dracochevaux imprègnent les gardiens du temple troll. L'architecture
du temple-forêt amani est vive et primitive, décorée de masques, de totems et de peintures
de guerre. Un parcours chronométré où la vitesse compte et où les tambours trolls ne
cessent jamais de battre.""",

    585: """Terrasse des Magistres : le dernier bastion de Kael'thas Soleil-filant sur l'Île de
Quel'Danas, un palais elfe de sang d'une élégance saisissante dissimulant une corruption
démoniaque. Des cristaux corrompus alimentent des constructs arcaniques, des magistres
elfes de sang canalisent une magie interdite, et un naaru captif est vidé de sa Lumière.
La beauté de l'architecture de Lune-d'Argent, tordue par le désespoir et la dépendance —
des salles dorées dissimulant un pacte monstrueux.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan : la tour hantée du dernier Gardien, Medivh, dans le Défilé de Deuillevent. Un
dîner spectral, une scène d'opéra aux interprètes fantomatiques, une partie d'échecs
prenant vie, et un observatoire céleste emplissent cette tour d'une hauteur impossible. La
tour existe partiellement hors de la réalité normale — les pièces se déplacent, le temps
se distord, et les échos de la folie de Medivh se rejouent éternellement. D'une beauté
envoûtante, profondément troublante, et absolument unique.""",

    534: """Sommet du Mont Hyjal : un raid des Cavernes du Temps se déroulant durant la Bataille du
Mont Hyjal, l'affrontement final contre Archimonde et la Légion ardente. Des vagues de
morts-vivants et de démons assaillent trois bases successives — humaine, de la Horde, et
elfe de la nuit. L'arbre-monde Nordrassil se dresse au-dessus tandis que la forêt brûle.
Un scénario de défense épique où le destin d'Azeroth est en jeu et où des héros
légendaires combattent à vos côtés.""",

    544: """Repaire de Magtheridon : une unique chambre brutale sous la Citadelle des Flammes
Infernales où le seigneur de la fosse Magtheridon est enchaîné. Des canalisateurs
maintiennent sa prison tandis que l'énergie des flammes infernales pulse dans la pièce.
L'espace est oppressivement chaud, empestant le sang de démon et le soufre. Une
confrontation directe mais impitoyable — un démon massif, une salle mortelle, aucune place
pour l'erreur.""",

    548: """Caverne de l'Écume-de-serpent : le bastion sous-marin de Dame Vashj dans le Réservoir de
Nasseau, un palais inondé d'une beauté corrompue. Naga, ondemarcheurs et hydres colossales
gardent des chambres où des cascades se déversent dans des bassins luminescents. Des ponts
enjambent des lacs souterrains, et les chambres les plus profondes pulsent des eaux
corrompues du Marécage de Zangar. Une architecture naga élégante rencontre la puissance
brute d'un océan souterrain.""",

    550: """La Citadelle des Tempêtes - L'Œil : la forteresse naaru capturée de Kael'thas
Soleil-filant, une citadelle cristalline flottant au-dessus de Raz-de-néant. Conseillers
elfes de sang, constructs arcaniques et créatures du Néant gardent des chambres de cristal
draeneï scintillant. La technologie est à la fois étrangère et magnifique à couper le
souffle, détournée par des elfes désespérés nourrissant leur dépendance à la magie. La vue
sur Raz-de-néant brisé depuis les plateformes est aussi saisissante que terrifiante.""",

    564: """Temple noir : la forteresse d'Illidan Hurlorage dans la Vallée d'Ombrelune, un immense
temple draeneï corrompu par une occupation démoniaque. Orcs corrompus, démons, naga et
elfes de sang servent le Traître à travers de vastes cours, des égouts et de grandes
salles. La beauté originelle du temple est balafrée par la corruption démoniaque —
symboles sacrés fissurés, autels profanés, et feu vert là où brillait jadis la Lumière.
L'aboutissement de l'histoire de l'Outreterre, se terminant devant le trône d'Illidan.""",

    565: """Repaire de Gruul : un rude complexe de cavernes dans les Tranchantes, foyer du père gronn
Gruul le Tueur-de-dragons. Serviteurs ogres et fils monstrueux de Gruul gardent l'approche
de sa chambre, jonchée d'ossements de dragons et de trophées. Les grottes semblent
primitives et brutales — aucune architecture, aucun ornement, seulement de la roche brute
façonnée par les poings de géants.""",

    580: """Plateau du Puits de Soleil : le raid final de la Croisade ardente, situé au cœur du Puits
de Soleil restauré sur l'Île de Quel'Danas. La Légion ardente tente d'invoquer Kil'jaeden
à travers le Puits de Soleil lui-même. Une architecture elfique immaculée d'une beauté à
couper le souffle encadre une bataille désespérée contre les démons les plus puissants de
l'armée de la Légion. La lumière sacrée du Puits de Soleil s'oppose aux ténèbres
démoniaques dans chaque chambre.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Fort d'Utgarde : forteresse vrykul sur les rives du Fjord Hurlant, premier avant-goût des
dangers du Norfendre. Des salles d'inspiration viking en pierre sombre et fer, éclairées
par des âtres rugissants et ornées de crânes de dragons. Guerriers vrykuls, dresseurs de
proto-drakes et leurs serviteurs morts-vivants emplissent les grandes salles. Le donjon
donne l'impression de mettre à sac une longère nordique — froid, brutal, et empreint d'une
culture guerrière.""",

    575: """Pinacle d'Utgarde : les hauteurs du Fort d'Utgarde, où le roi vrykul Ymiron règne depuis
son trône gelé. Salles de trophées, volières d'aigles et chambres rituelles dominent le
fjord. L'architecture devient plus grandiose et plus menaçante à mesure qu'on s'élève,
culminant dans la salle du trône givré d'Ymiron. Le vent hurle à travers les créneaux
ouverts, et la vue sur le paysage gelé en contrebas donne le vertige.""",

    576: """Le Nexus : les grottes cristallines sous Coldarra, bastion de la guerre du clan draconique
Bleu contre la magie mortelle. Des cavernes gelées d'une beauté impossible renferment des
anomalies arcaniques, des chasseurs de mages déments et des failles dans la réalité. Des
dragons cristallisés restent figés en plein vol. Le donjon scintille d'une énergie
arcanique instable — bleus, violets et blancs se réfractant à travers la glace et le
cristal dans toutes les directions.""",

    578: """L'Oculus : les anneaux supérieurs du Nexus, une série de plateformes flottantes reliées
par des ponts magiques loin au-dessus du nexus de lignes telluriques. Les joueurs montent
des drakes pour naviguer entre les segments d'anneau tout en combattant les forces de
Malygos. Le vide s'étend en contrebas, l'énergie arcanique crépite entre les plateformes,
et le vertige est bien réel. Un donjon qui donne l'impression de voler à travers une
tempête magique au bord de la réalité.""",

    595: """L'Épuration de Stratholme : instance des Cavernes du Temps se déroulant durant la purge
fatidique de la cité pestiférée par Arthas. Les rues de Stratholme sont intactes mais
condamnées — les citoyens se transforment en morts-vivants sous vos yeux, et Arthas
ordonne froidement leur mise à mort avant la transformation. Le donjon est singulièrement
troublant, car vous contribuez à l'atrocité qui amorce la chute d'Arthas. Le moment le
plus sombre de l'histoire, revécu.""",

    599: """Salles de Pierre : une installation des titans dans les Pics Foudroyés, faisant partie du
vaste complexe d'Ulduar. Des couloirs de pierre à la perfection géométrique abritent des
constructs des titans défaillants, des nains de fer et d'anciens systèmes de défense. Le
Tribunal des Âges conserve les archives de la création elle-même. Le donjon dégage une
atmosphère érudite et ancienne — un musée où les expositions ripostent et où l'histoire
qui y est conservée pourrait briser des civilisations.""",

    600: """Fort de Drak'Tharon : forteresse trolle infestée par le Fléau, à la frontière des
Grisonnes et de Zul'Drak. Le Fléau a relevé les trolls morts et corrompu leurs bêtes
dinosaures, créant une fusion impie de culture trolle et de pouvoir nécromantique. Raptors
squelettiques, trolls zombifiés et la liche Novos l'Invocatrice emplissent les salles
délabrées. Une architecture trolle s'effondrant sous le poids de la non-mort.""",

    601: """Azjol-Nerub : le royaume nérubien en ruines sous le Norfendre, une descente verticale
étouffée de toiles à travers l'empire des araignées. L'architecture nérubienne de soie et
de chitine s'étend à travers de vastes gouffres souterrains. Des nérubiens morts-vivants
servent le Fléau tandis que les vivants se battent désespérément. Le donjon vous entraîne
toujours plus profond à travers des sols qui s'effondrent — claustrophobe, étranger, et
grouillant de choses qui ne devraient pas exister.""",

    602: """Salles de la Foudre : un complexe de forges des titans dans Ulduar, crépitant d'énergie
électrique. Nains de fer, géants des tempêtes et constructs runiques gardent des couloirs
de métal étincelant traversés d'éclairs. Loken, le gardien titan corrompu, attend dans la
chambre la plus profonde. Chaque surface bourdonne de puissance, des étincelles dansent
sur les murs, et le tonnerre de la forge est constant et assourdissant.""",

    604: """Gundrak : temple troll des Drakkari à Zul'Drak, où les trolls sacrifient leurs propres
dieux animaux pour alimenter leur guerre contre le Fléau. Le sang divin coule sur les
autels tandis que les esprits du serpent, du mammouth et du rhinocéros sont consumés. Le
temple est massif et primitif — pierre sculptée, bassins rituels, et l'énergie désespérée
d'une civilisation mourante brûlant ses propres dieux pour survivre.""",

    608: """Antre Violet : prison magique sous Dalaran, où le Kirin Tor retient les créatures les plus
dangereuses du Norfendre. Des agents du clan draconique Azur assaillent la prison depuis
des portails, libérant des détenus par vagues. L'architecture est un élégant violet et
argent typique de Dalaran, mais les détenus sont cauchemardesques. Un scénario de défense
de tour dans le donjon d'un mage — les protections arcaniques peinent à contenir le chaos.""",

    619: """Ahn'kahet : l'Ancien Royaume : les profondeurs les plus reculées d'Azjol-Nerub, où les
Sans-Visage servent le dieu ancien Yogg-Saron. L'architecture passe du nérubien à quelque
chose de bien plus ancien et plus étranger — les murs organiques pulsent, la réalité se
déforme, et des effets de folie assaillent l'esprit. Oubliés, jeteurs de sorts et le
héraut Volazj se tapissent dans des chambres qui défient toute géométrie. Le donjon le
plus troublant du Norfendre.""",

    632: """Forge des Âmes : le premier des trois donjons de la Citadelle de la Couronne de Glace, une
machine broyeuse d'âmes où le Roi-liche traite les morts. Des fleuves d'âmes torturées
coulent à travers une machinerie de fer, des forgerons spectraux martèlent des enclumes de
souffrance, et le Dévoreur d'Âmes garde la forge. Les hurlements ne s'arrêtent jamais. Un
cauchemar industriel alimenté par un tourment éternel.""",

    650: """Épreuve du Champion : une grande arène de tournoi sous le Colisée argenté en Couronne de
Glace, où les champions de l'Alliance et de la Horde prouvent leur valeur. Joutes à
cheval, duels de champions et une ultime embuscade du Chevalier noir se déroulent sur le
terrain du tournoi. L'atmosphère est festive et compétitive jusqu'à ce que les
morts-vivants ne fassent irruption dans la fête. Faste et spectacle avec un revirement
sombre.""",

    658: """Fosse de Saron : une mine d'esclaves brutale en Couronne de Glace où les forces du Fléau
font travailler des prisonniers jusqu'à la mort pour extraire du saronite. La fosse est
ouverte au ciel gelé, avec d'immenses chaînes, des plateformes minières et des gisements
de saronite partout. Le maître-forgeron Frimasfort lance des rochers tandis que Tyrannus
patrouille au-dessus sur son drake du couvoir givré. Désespoir et cruauté distillés dans
la pierre gelée et le métal sombre.""",

    668: """Salles de Réflexion : les Salles gelées hantées de la Citadelle de la Couronne de Glace,
où les échos des victimes de Frostmourne s'attardent autour de la chambre de la lame. Le
Roi-liche lui-même vous poursuit à travers des couloirs qui s'effondrent tandis que des
vagues de fantômes attaquent. Les salles sont de glace immaculée et de saronite sombre, et
la terreur est bien réelle — vous ne pouvez pas le combattre, seulement fuir. Le donjon le
plus intense narrativement du jeu, une fuite désespérée devant un destin inévitable.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas : la nécropole flottante de l'archiliche Kel'Thuzad, planant au-dessus de la
Désolation des Dragons. Quatre ailes d'horreurs thématiques — le Quartier Arachnéen des
araignées géantes, le Quartier de la Peste de la maladie et des abominations, le Quartier
Militaire des commandants chevaliers de la mort, et le Quartier des Constructs des golems
de chair. Une architecture gothique de pierre sombre et de vase verte, avec la froide
précision d'une organisation militaire morte-vivante. Le chef-d'œuvre de mort du Fléau.""",

    603: """Ulduar : une cité-prison des titans dans les Pics Foudroyés, le plus grandiose raid du
Norfendre. D'immenses salles de métal et de pierre étincelants abritent les gardiens
titans corrompus et leurs serviteurs, tandis que le dieu ancien Yogg-Saron est emprisonné
dans le caveau le plus profond. L'ampleur est stupéfiante — batailles de véhicules aux
portes, un observatoire ouvert sur le cosmos, des jardins d'une beauté surnaturelle, et
une descente dans la folie elle-même. Ancien, magnifique et terrifiant.""",

    615: """Sanctuaire d'Obsidienne : une chambre volcanique sous le Temple du Repos-des-Dragons où
Sartharion garde des œufs de dragons crépusculaires. Des rivières de lave divisent les
plateformes d'obsidienne, et trois lieutenants drakes crépusculaires patrouillent leurs
propres îlots. La chambre luit d'orange et de rouge, la chaleur déforme l'air en ondulant,
et la trahison du clan draconique Noir est mise à nu. Une arène directe de feu et
d'écailles.""",

    616: """Sanctuaire de l'Éternité : le sanctuaire personnel de Malygos au sommet du Nexus au-dessus
de Coldarra, une plateforme suspendue dans une énergie tellurique brute. Il n'y a ni sol
ni murs — seulement un disque de force magique au-dessus d'un vide d'arcane bleu et violet
tourbillonnant. Le Tisse-sorts attaque avec toute la puissance du clan draconique Bleu. Le
raid semble surnaturel — affronter un aspect draconique au cœur de la tempête arcanique
d'Azeroth.""",

    624: """Caveau d'Archavon : un caveau des titans sous la forteresse de Grognard, accessible
uniquement à la faction contrôlant la zone. Géants de pierre et constructs élémentaires
gardent les chambres dans une série directe de combats de boss. L'architecture est un
design titan utilitaire — fonctionnel, massif et dépourvu d'ornement. Une récompense pour
une victoire en JcJ, rapide et brutale.""",

    631: """Citadelle de la Couronne de Glace : le trône du Roi-liche, l'aboutissement de l'ère du
Roi-liche. Une forteresse imposante de saronite et de glace s'élevant au cœur de la
Couronne de Glace. Chaque aile intensifie l'horreur — des armées mortes-vivantes de la
Spire basse, en passant par les Ouvroirs de la Peste, la Salle cramoisie et les Salles de
l'Aile givrée, jusqu'au Trône gelé lui-même. L'architecture est oppressante, belle dans sa
cruauté, et conçue pour briser l'espoir. C'est la fin.""",

    649: """Épreuve du Croisé : le Colisée argenté en Couronne de Glace, une arène de tournoi qui
s'enfonce dans la terre lorsque le sol s'effondre dans une caverne nérubienne souterraine.
Le niveau supérieur est fait de bannières éclatantes et de foules en liesse ; le niveau
inférieur est une horreur chitineuse, domaine d'Anub'arak. Le contraste entre la
compétition festive au-dessus et la terreur ancienne en dessous définit toute
l'expérience.""",

    724: """Sanctuaire Rubis : une chambre sous le Temple du Repos-des-Dragons où le clan draconique
Crépusculaire a envahi le sanctuaire des dragons rouges. Halion, le destructeur
crépusculaire, oscille entre le plan physique et le plan des ombres. La chambre alterne
entre une chaude lumière rubis et une froide ombre violette. Le dernier raid avant le
Cataclysme — un bref et sinistre avertissement de la destruction à venir.""",
}
