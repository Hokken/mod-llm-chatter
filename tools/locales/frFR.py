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
    # Eastern Kingdoms - Khaz Modan
    # -------------------------------------------------------------------------
    1: """Dun Morogh : Des hautes terres enneigées parmi les sommets de Khaz
Modan, patrie des nains de Forgefer et des gnomes exilés de Gnomeregan. La
neige recouvre les collines rocheuses, les lacs gelés scintillent sous un pâle
soleil et des forêts de pins silencieuses ploient sous de lourdes congères.
L'air sent le givre, la fumée de bois et la forge. Les villages nains
entretiennent leurs feux contre le froid sans fin, tandis que troggs, trolls
des glaces, loups et ours rendent la nature sauvage dangereuse.""",

    1537: """Forgefer : L'antique capitale des nains, une ville immense taillée
au cœur d'une montagne de Dun Morogh. Des salles éclairées de torches et des
passages de pierre entourent la Grande Forge, alimentée par des rivières de
roche en fusion, où le roi Magni Barbe-de-bronze règne sur Khaz Modan depuis le
Haut trône. Les gnomes exilés de Gnomeregan vivent à Brikabrok, la Ligue des
explorateurs cherche les secrets des origines naines dans la salle des
Explorateurs, et le Tram des profondeurs file sous terre jusqu'à Hurlevent.
L'air est chaud, enfumé et résonne de marteaux et de rires.""",

    38: """Loch Modan : Des collines rudes et des vallées verdoyantes dans
l'est de Khaz Modan, autour d'un grand lac retenu par un immense barrage,
chef-d'œuvre de l'ingénierie naine. Le climat est frais et humide, avec des
brumes sur l'eau, des pluies fréquentes et des matins glacés. Les nains pêchent
dans le lac, creusent les falaises et coupent du bois autour de Thelsamar. Des
engins de siège brisés de la Horde, vestiges de la Deuxième Guerre, rouillent
encore sur les îles. Des troggs infestent les vallées, des kobolds tiennent une
mine, des ogres un fort au nord-est, et des nains Sombrefer menacent le
barrage.""",

    330: """Passage de Thandol : Un gigantesque pont nain enjambant le profond
détroit entre Khaz Modan et Lordaeron, reliant les Paluns aux Hautes-terres
d'Arathi. Pendant des siècles, armées et marchandises l'ont franchi entre les
nains et les royaumes humains du nord. Le Fléau l'a endommagé pendant la
Troisième Guerre, et une attaque des nains Sombrefer a presque détruit l'une de
ses arches, dont de grands pans gisent désormais sous les vagues. Il reste la
seule route terrestre entre Lordaeron et le sud. Le vent et les embruns
fouettent ses hauteurs.""",

    269: """Dun Algaz : Un col percé dans la montagne et une vieille forteresse
naine entre le Loch Modan et les Paluns, gardé au sud par la porte d'Algaz.
Pendant la Deuxième Guerre, ce fut le dernier bastion de la Horde en Khaz
Modan. Il reste la grande route entre les terres naines et le port de Menethil,
mais des orcs du clan Gueule-de-dragon ont submergé l'avant-poste au milieu du
col, et les gardes de montagne nains ne tiennent plus que le tunnel supérieur.
Les tunnels sont sombres, froids et sonores, et la route qui les traverse est
devenue dangereuse.""",

    11: """Les Paluns : De vastes marais froids au nord de Khaz Modan,
sillonnés de rivières, de tourbières et de chenaux étouffés de roseaux entre
les montagnes et la baie de Baradin. La brume couvre le sol, le ciel est d'un
gris uniforme et il pleut souvent. Jadis terre de forteresses Marteau-Hardi, la
région fut ravagée pendant les Deuxième et Troisième Guerres, quand le clan
Gueule-de-dragon tenait Grim Batol et asservissait la Reine des dragons
Alexstrasza. Le port de Menethil, sur la côte ouest, relie par la mer Khaz
Modan à Kalimdor et au Norfendre. Restes du clan Gueule-de-dragon, nains
Sombrefer, gnolls, murlocs, raptors et crocilisques rendent les marais
dangereux.""",

    3: """Terres ingrates : Un désert brûlé par le soleil, fait de terre rouge
craquelée, de mesas et de canyons sinueux au sud de Khaz Modan. L'eau est rare,
les journées sont torrides et des tempêtes de poussière balaient les plaines
nues, où seuls survivent coyotes, vautours, scorpides, basilics et élémentaires
de roche. Au nord se trouve Uldaman, un caveau des titans mis au jour par des
fouilles naines et désormais défendu par les troggs qu'elles ont réveillés. Les
nains Sombrefer y creusent pour leur maître Ragnaros, des ogres errent dans la
région, des dragons noirs nichent dans les canyons de l'est et la Horde tient
la forteresse de Kargath.""",

    51: """Gorge des Vents brûlants : Une désolation volcanique de cendres, de
scories et de lave entre les Terres ingrates et le mont Rochenoire, autrefois
partie des verdoyantes Carmines, jusqu'à ce que l'invocation de Ragnaros par
Thaurissan déchire la terre. L'air est chaud, sec et chargé de fumée, et des
élémentaires de feu errent parmi les roches calcinées. Les nains Sombrefer
règnent sur la gorge et font travailler des captifs dans l'immense excavation
du Chaudron. Au bord nord, les artisans de la Confrérie du thorium, qui ont
rompu avec leur clan, tiennent le comptoir neutre de Thorium.""",

    25: """Mont Rochenoire : Un volcan immense et toujours actif entre la gorge
des Vents brûlants et les Steppes ardentes, né quand le thane-sorcier Sombrefer
Thaurissan invoqua Ragnaros, le seigneur du Feu. Les nains Sombrefer ont creusé
une ville immense dans ses profondeurs, et au-dessus s'élève le pic de
Rochenoire. La montagne est âprement disputée : Ragnaros et ses serviteurs
Sombrefer règnent sur les profondeurs et le cœur en fusion, tandis que le
dragon noir Nefarian commande orcs, ogres et draconiens depuis les hauteurs du
pic. Chaînes et plates-formes enjambent une salle de roche en fusion, et la
chaleur, la fumée et le grondement ne cessent jamais.""",

    46: """Steppes ardentes : Une terre volcanique calcinée au sud du mont
Rochenoire, seul passage terrestre entre Hurlevent et Khaz Modan. Terre
carbonisée, contreforts escarpés et rivières de lave s'étendent sous un ciel
rougeoyant des feux de la montagne, et l'air chaud et sec charrie des cendres.
Abandonnées par Hurlevent, les steppes appartiennent aux serviteurs du Vol noir
et aux agents de Ragnaros : orcs Rochenoire qui rejettent Thrall, ogres,
dragons noirs et nains Sombrefer. C'est ici qu'Anduin Lothar tomba à la fin de
la Deuxième Guerre. L'Alliance s'accroche au Guet de Morgan.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Azeroth
    # -------------------------------------------------------------------------
    12: """Forêt d'Elwynn : Le cœur verdoyant du royaume de Hurlevent, une
terre douce de forêts de chênes et de pins, de prairies, de lacs et de fermes
au sud de la capitale, avec le village de Comté-de-l'Or en son centre et
l'abbaye de Comté-du-Nord dans une vallée au nord. La Horde la ravagea pendant
la Première Guerre, et les tailleurs de pierre impayés qui rebâtirent Hurlevent
devinrent la Confrérie défias. La paix y est fragile : des bandits défias
occupent des fermes, des kobolds infestent les mines, des gnolls campent à la
frontière ouest et des murlocs hantent les lacs, tandis que la garde est
épuisée par des guerres lointaines.""",

    1519: """Hurlevent : La capitale du royaume de Hurlevent et la plus grande
cité humaine du monde, rebâtie après la Première Guerre avec ses murailles de
pierre blanche, ses tours aux toits bleus et ses quartiers séparés par des
canaux. Le roi Varian Wrynn règne depuis le donjon de Hurlevent après sa longue
absence. La cathédrale de la Lumière est le cœur de la foi en la Lumière
sacrée, et la ville abrite le quartier commerçant, la vieille ville avec le
SI:7, le quartier des Mages, le district des Nains avec le Tram des profondeurs
vers Forgefer, et le parc avec son puits de lune. Humains, nains, gnomes, elfes
de la nuit et draeneï arpentent ses rues.""",

    40: """Marche de l'Ouest : Des terres agricoles vallonnées sur la côte
ouest de Hurlevent, autrefois le grenier du royaume, aujourd'hui tombées en
ruine. Les champs sont en friche, l'herbe a jauni et le vent marin charrie la
poussière sur des fermes abandonnées. La Confrérie défias, des hors-la-loi nés
des tailleurs de pierre impayés de Hurlevent, a chassé de nombreux fermiers,
tient le village fantôme de Ruisseau-de-la-Lune et a lâché des gardiens des
moissons détraqués dans les champs. Des gnolls razzient la région depuis le sud
et des murlocs rôdent sur la côte. La Milice du peuple tient la colline des
Sentinelles, et les fermiers se sentent oubliés de la couronne.""",

    44: """Les Carmines : Des pics rougeâtres, de grands ormes et des rivières
tumultueuses à l'est de la forêt d'Elwynn, autour des eaux bleues du lac
Placide et de l'ancienne bourgade de Comté-du-Lac. Ses habitants robustes et
autonomes fournissent Hurlevent en bois, en poisson et en grain. La chaîne fut
brisée il y a longtemps par l'invocation de Ragnaros. Aujourd'hui, c'est une
région frontalière : des orcs Rochenoire venus des Steppes ardentes ont pris la
forteresse de Guet-de-Pierre et campent dans les collines, des gnolls
revendiquent les canyons, des murlocs infestent le lac et des dragonnets noirs
errent sur les hauteurs. Comté-du-Lac ne compte que sur sa petite garde.""",

    10: """Bois de la Pénombre : Une sombre forêt maudite au sud d'Elwynn,
jadis claire et belle, désormais engloutie par un crépuscule éternel et contre
nature. Un brouillard noir flotte entre les arbres tordus, et l'air est froid
et sent la pourriture. Certains accusent le mal de Karazhan, d'autres un ancien
artefact et les worgens venus avec la malédiction. Les morts se lèvent des
cimetières, worgens et araignées géantes rôdent dans les bois, et l'on dit que
les Cavaliers noirs surgissent de la nuit. Les habitants têtus de Sombre-Comté,
protégés par le Guet de nuit, se sentent abandonnés par Hurlevent.""",

    41: """Défilé de Deuillevent : Un canyon désolé et maudit entre le bois de
la Pénombre et le marais des Chagrins, où les arbres se dressent nus et
pétrifiés, où l'herbe est grise et où un vent fétide et hurlant ne s'arrête
jamais. Les orages menacent sans cesse et la foudre frappe les rochers nus. Au
sud se dresse Karazhan, la tour de Medivh, le dernier Gardien de Tirisfal, qui
ouvrit la Porte des ténèbres ; une magie maléfique s'en échappe encore et
draine la vie de la terre. Ogres, esprits sans repos et charognards hantent le
défilé, et l'on murmure qu'une nouvelle présence obscure s'est emparée de la
tour.""",

    8: """Marais des Chagrins : Un marécage stagnant et brumeux de tourbières,
de saules pleureurs et de mares saumâtres à l'est du défilé de Deuillevent,
autrefois la partie nord du Marais Noir. L'air est humide et lourd, et
crocilisques, jaguars, araignées et bêtes des marais guettent dans les roseaux.
Les Atal'ai y bâtirent un temple au dieu du sang Hakkar, et l'Aspect Ysera le
noya sous la plus grande tourbière, où ses dragons montent encore la garde. La
Horde tient Pierrêche, rebâtie. Des Égarés et des Roués, draeneï échoués sur
Azeroth, vivent dans le marais, et des murlocs peuplent la côte.""",

    4: """Terres foudroyées : Un désert calciné d'argile écarlate au sud du
marais des Chagrins, autrefois le sud du Marais Noir, déformé par la magie de
la Porte des ténèbres. La foudre frappe souvent, rien de fertile ne pousse, les
journées sont chaudes et les nuits glaciales. Basilics, scorpides et hyènes
mutants errent dans la région. La Porte des ténèbres se dresse dans un immense
cratère au sud-est, de nouveau ouverte sur l'Outreterre, et les armées de
l'Alliance et de la Horde gardent son pied. Le Rempart-du-Néant, fondé par
Khadgar, veille au nord ; ogres et restes de la Légion rôdent dans la
désolation.""",

    33: """Vallée de Strangleronce : Une immense jungle fumante à la pointe sud
des royaumes de l'Est, pleine d'arbres gigantesques, de lianes et de sous-bois
épineux, peuplée de tigres, de panthères, de raptors, de gorilles et de
crocilisques. Ce fut le cœur de l'empire troll des Gurubashi, jusqu'à ce que
l'invocation d'Hakkar le déchire ; des ruines couvrent aujourd'hui la terre,
les tribus Scalp-rouge et Brise-crâne combattent les étrangers, et Zul'Gurub
est retombé sous l'emprise d'Hakkar. Gobelins, pirates, ogres, nagas et
rebelles réclament leur part. Baie-du-Butin est le port neutre animé du cap
sud, et la Horde tient Grom'gol sur la côte.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Lordaeron
    # -------------------------------------------------------------------------
    85: """Clairières de Tirisfal : Des collines boisées sur la côte nord de
Lordaeron, autrefois le cœur du royaume humain et désormais la patrie des
Réprouvés de Sylvanas Coursevent. Le ciel est morne et teinté de vert, une
brume froide flotte sur les fermes abandonnées, les lacs silencieux et les
moulins en ruine, mais la terre garde une beauté mélancolique, surtout autour
du village de Brill. C'est ici que Kel'Thuzad répandit d'abord la peste, et
qu'Arthas tua son père. Sous la capitale en ruine s'étend Fossoyeuse. Le Fléau
hante encore les fermes, la Croisade écarlate tient son monastère, et le
Rempart fait face aux Maleterres.""",

    1497: """Fossoyeuse : La capitale des Réprouvés, une immense cité
souterraine sous les ruines de la capitale royale de Lordaeron, née des
anciennes cryptes royales, des cachots et des égouts. Arthas commença à
l'agrandir, Sylvanas acheva l'ouvrage après avoir chassé les seigneurs de
l'effroi. La ville est sombre, froide et labyrinthique, bâtie en anneaux autour
du quartier commerçant, avec les quartiers des Mages, des Voleurs et de la
Guerre et l'Apothicarium, où la Société royale des apothicaires concocte pestes
et poisons. Une boue verte coule dans les canaux, de grands ascenseurs mènent
aux ruines de la surface, et Sylvanas règne depuis le quartier Royal.""",

    130: """Forêt des Pins-Argentés : Une forêt ancienne de grands pins à
l'écorce argentée le long de la côte ouest de Lordaeron, hantée et malade
depuis que le Fléau l'a traversée par le fer et le feu pendant la Troisième
Guerre. Des brumes spectrales flottent entre les arbres, et fermes incendiées
et mines abandonnées parsèment la terre. Les Réprouvés tiennent le nord depuis
le Sépulcre et combattent des gnolls pestiférés. Au sud, les mages de Dalaran
gardent un village de meuniers, les habitants de Bois-du-Bûcher portent une
malédiction qui les change en worgens la nuit, Arugal rumine au donjon
d'Ombrecroc, et le mur de Grisetête isole Gilnéas.""",

    170: """Lac Lordamere : L'un des plus grands lacs des royaumes de l'Est,
une vaste étendue d'eau froide et grise au cœur du royaume déchu de Lordaeron,
dont la capitale se dressait autrefois sur la rive nord. Autour s'étendaient
Lordaeron, Dalaran et Alterac, les grands royaumes de l'ancienne Alliance.
Aujourd'hui, il sépare les terres des Réprouvés des montagnes d'Alterac. L'île
de Fenris et son sinistre donjon occupent son centre, les îles de l'Aube
forment le bord d'un ancien volcan, et une vieille peste a laissé ses eaux
étrangement vides de vie. La brume flotte souvent sur le lac, et des murlocs
campent sur ses rives.""",

    267: """Contreforts de Hautebrande : Collines verdoyantes, prairies,
bosquets de pins et terres agricoles au sud de Lordaeron, la région la mieux
préservée du royaume déchu. Une rivière issue du lac Darrowmere traverse les
collines et de petites îles bordent la côte sud. C'est aussi l'un des champs de
bataille les plus sanglants d'Azeroth : la première bataille de la Deuxième
Guerre s'y livra, et Fort-de-Durn abritait les camps d'internement où le jeune
Thrall vécut en esclave. La ville humaine d'Austrivage et les Réprouvés de
Moulin-de-Tarren se livrent une lutte acharnée, tandis que le Syndicat tient
les ruines de Fort-de-Durn.""",

    36: """Montagnes d'Alterac : Des pics enneigés au nord de Hautebrande,
jadis le royaume humain d'Alterac, détruit par l'Alliance après que lord
Perenolde l'eut livré à la Horde. Les nobles exilés fondèrent le Syndicat, qui
tient les hautes terres et des camps au-dessus de Hautebrande, tandis que des
ogres occupent les ruines de la cité d'Alterac. Sur la rive du lac Lordamere
s'ouvre le cratère où se dressait Dalaran avant de s'envoler vers le Norfendre.
Dans une vallée cachée, les orcs Loup-de-givre combattent les nains de
l'expédition Foudrepique, et le mystérieux manoir de Ravenholdt se cache parmi
les sommets. Yétis et lions des montagnes errent dans la neige.""",

    45: """Hautes-terres d'Arathi : Des hautes terres grises et venteuses
d'herbe ondulante et de rochers au sud-est de Lordaeron, berceau de la
civilisation humaine, où Thoradin fonda l'empire d'Arathor et où humains et
hauts-elfes s'allièrent pour la première fois contre les Amani. Plus tard
naquit ici le royaume de Stromgarde, mais le Syndicat et des ogres prirent sa
capitale, et son armée tient désormais le Refuge de l'Ornière. La Horde tient
Trépas-d'Orgrim, l'ancien camp d'internement. Ogres, trolls des forêts, raptors
et kobolds errent dans la région, et d'anciens cercles de pierre retiendraient
quelque chose prisonnier.""",

    293: """Mur de Thoradin : Une immense muraille de pierre à la frontière
entre Hautebrande et les Hautes-terres d'Arathi, élevée jadis par le roi
Thoradin, fondateur de l'empire d'Arathor, contre les trolls Amani. Plus tard,
elle protégea Stromgarde de l'avancée du Fléau. Aujourd'hui, elle est effondrée
et béante, sa grande porte est ouverte et des pans entiers sont tombés en
gravats. La route principale entre Hautebrande et Arathi passe dans son ombre,
souvenir de la gloire du premier empire humain et de la chute de ses héritiers.""",

    47: """Les Hinterlands : Une région sauvage et montagneuse de forêts
luxuriantes, de vallées profondes et de falaises abruptes au nord des royaumes
de l'Est, épargnée par la peste et au climat doux. Ce fut le cœur de l'empire
des trolls des forêts Amani, dont les ruines colossales se dressent encore
parmi les arbres. Les nains Marteau-Hardi du haut thane Falstad vivent à ciel
ouvert au Nid-de-l'Aigle, une ville taillée en forme de tête de griffon, et
chevauchent les griffons sauvages au combat. Des tribus trolles rivales
tiennent Jintha'Alor et Shadra'Alor, tandis que les trolls Vengebroche se sont
alliés à la Horde. Au nord, l'arbre de Seradane est une porte vers le Rêve
d'émeraude.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands, Quel'Thalas and southern isles
    # -------------------------------------------------------------------------
    28: """Maleterres de l'Ouest : Une terre infestée au nord de Lordaeron,
autrefois le grenier boisé du nord du royaume. C'est ici que Kel'Thuzad et le
Culte des damnés empoisonnèrent le grain d'Andorhal avec la peste de la
non-mort. Une brume grise et enfumée flotte sur la terre, les arbres portent
des excroissances tumorales et les bêtes survivantes sont malades et féroces.
Les morts-vivants infestent Andorhal, les champs de chaudrons et les
cimetières, et le Fléau forme des nécromanciens à la Scholomance, sur l'île de
Caer Darrow. La Croisade écarlate tient Âtreval, l'Aube d'argent le camp du
Noroît, et le tombeau d'Uther le Porteur de Lumière est l'un des rares lieux
paisibles.""",

    139: """Maleterres de l'Est : La moitié la plus dévastée des Maleterres,
autrefois une terre de fermes et de villages gouvernée depuis Stratholme, où
fut fondé l'ordre de la Main d'argent et où Arthas mena sa purge. Le règne du
Fléau y est presque absolu : le sol est brun et malade, les arbres se sont
tordus en champignons géants et des brumes orange et vertes étouffent l'air.
Stratholme brûle comme capitale du Fléau en Lordaeron, et le bois de la Peste
est hérissé de ziggourats. La Croisade écarlate tient la Main de Tyr, l'Aube
d'argent garde la chapelle de l'Espoir-de-Lumière ouverte à tous ceux qui
combattent le Fléau, et à l'est flotte Achérus, la demeure des chevaliers de la
mort.""",

    3430: """Bois des Chants éternels : La forêt enchantée au cœur de
Quel'Thalas, figée dans un automne éternel sous un feuillage d'or et de
pourpre, parsemée de flèches gracieuses, de tours flottantes et de cristaux
arcaniques. Pendant la Troisième Guerre, Arthas mena le Fléau à travers le
royaume jusqu'au Puits de soleil et laissa la Malebrèche, une bande de terre
sans vie qui fend la forêt et Lune-d'argent elle-même. Les survivants prirent
le nom d'elfes de sang et, sous le régent seigneur Lor'themar Theron,
rejoignirent la Horde et rebâtirent beaucoup. Mais les Misérables hantent les
ruines, des créations arcaniques échappent à tout contrôle, des trolls rôdent
dans les collines et les pierres runiques qui contiennent la souillure
faiblissent.""",

    3487: """Lune-d'argent : La capitale des elfes de sang dans le bois des
Chants éternels, fondée il y a des millénaires et peut-être la plus ancienne
capitale encore debout. Pendant la Troisième Guerre, Arthas mena le Fléau à
travers ses portes et tua le roi. Les elfes de sang ont rebâti la moitié est
presque dans sa splendeur d'antan, avec ses flèches dorées, ses plates-formes
flottantes, ses cristaux enchaînés gorgés de magie et ses jardins luxuriants,
tandis que la moitié ouest gît encore en ruine au-delà de la Malebrèche. Le
régent seigneur Lor'themar Theron règne depuis la flèche de Haut-Soleil, des
gardiens arcaniques patrouillent dans les rues, et un orbe de translocation
relie la ville à Fossoyeuse.""",

    3433: """Terres fantômes : Le sud de Quel'Thalas, une terre sombre d'arbres
noirs et desséchés, de ciel morne et de froid mortel, dévastée par la marche du
Fléau vers le Puits de soleil et jamais remise. La Malebrèche part de
Mortholme, la citadelle du Fléau gouvernée par le traître Dar'Khan Drathir, qui
aida Arthas à percer les défenses du royaume. Les fantômes des elfes massacrés
hantent les villages en ruine. Les elfes de sang et leurs alliés réprouvés
tiennent Tranquillien et veulent reconquérir la terre, tandis que des trolls
Amani rôdent près de Zul'Aman, à l'est. Le col Thalassien mène au sud, par une
antique porte elfique, jusqu'aux Maleterres.""",

    4080: """Île de Quel'Danas : Une île au large de la côte nord du bois des
Chants éternels, où les fondateurs de Quel'Thalas créèrent il y a sept mille
ans le Puits de soleil, une source d'une puissance immense. Arthas le souilla
pour ressusciter Kel'Thuzad. Récemment, l'île fut le théâtre d'une lutte
désespérée, quand Kael'thas Haut-Soleil et la Légion ardente voulurent faire du
Puits une porte, et l'opération Soleil brisé, unissant Aldor et Clairvoyants,
établit sa base au port des Confins du Soleil. Les cicatrices des combats
marquent la terre, mais ses forêts dorées, ses plages blanches et ses flèches
élégantes restent magnifiques, et en son cœur s'élève le plateau du Puits de
soleil.""",

    408: """Île de Gillijim : Une île de jungle reculée des mers du Sud, au
large de la côte sud de la vallée de Strangleronce. Les vieilles cartes la
signalent comme une ancienne île troll, mais rares sont les marins vivants à
avoir foulé ses rivages, et elle se trouve loin des routes commerciales
habituelles. La mer qui l'entoure est chaude, profonde et bleue, peuplée de
requins et d'autres créatures du grand large, et les courants peuvent emporter
les imprudents loin de toute terre. On parle de ruines trolles antiques cachées
dans ses jungles, mais ses secrets restent inconnus de la plupart.""",

    409: """Île du docteur Lapidis : Une île de jungle reculée des mers du Sud,
au large de la côte sud-ouest de la vallée de Strangleronce. Les vieilles
cartes y signalent les ruines croulantes des anciens trolls de la jungle, mais
presque personne ne l'a visitée de mémoire d'homme, et peu connaissent le sens
de son nom. Les eaux qui l'entourent sont profondes, chaudes et vides de
navires, peuplées seulement de requins et de créatures du grand large. Elle
reste un mystère, un point sombre à l'horizon que la plupart des marins
préfèrent éviter.""",

    # -------------------------------------------------------------------------
    # Kalimdor - North
    # -------------------------------------------------------------------------
    141: """Teldrassil : Un Arbre-Monde colossal qui s'élève de la mer Voilée
au large du nord-ouest de Kalimdor, si vaste qu'une contrée de forêts, de
collines et de lacs pousse sur ses branches au-dessus des nuages. L'archidruide
Fandral Forteramure le fit croître après que les elfes de la nuit eurent perdu
leur immortalité, et leur capitale, Darnassus, se dresse dans ses branches
ouest. La terre baigne dans un éternel crépuscule violet, pleine d'arbres
anciens, de puits de lune, de feux follets et de sabres-de-nuit. Mais les
Aspects dragons ne bénirent jamais l'arbre, et une corruption rampante s'étend
: les furbolgs sont devenus sauvages, les sylvins enragent et des satyres
rôdent dans les grottes. Rut'theran, à son pied, est le port vers le monde.""",

    1657: """Darnassus : La capitale des elfes de la nuit, bâtie dans les
branches ouest de Teldrassil et baignée d'un éternel crépuscule violet. De
gracieuses terrasses de bois vivant et de pierre blanche entourent un lac
central, reliées par des ponts arqués. La grande prêtresse Tyrande Murmevent
guide les elfes de la nuit depuis le temple de la Lune, tandis que
l'archidruide Fandral Forteramure dirige le Cercle cénarien depuis l'enclave
cénarienne, souvent en désaccord avec elle. Malfurion Hurlorage reste perdu
dans le Rêve d'émeraude. Sentinelles et anciens gardent la ville paisible et un
peu mélancolique, et un portail descend jusqu'au village de Rut'theran.""",

    148: """Sombrivage : Une longue côte rocheuse au nord-ouest de Kalimdor,
faite de bois ombragés, de plages brumeuses et de ruines croulantes, où le
temps est froid et orageux et le brouillard fréquent. Jadis région prospère de
l'ancien empire kaldorei, elle fut ravagée par la Fracture, et ses cités sont
vides depuis des millénaires. Les elfes de la nuit ont rebâti le port
d'Auberdine, lien vers Teldrassil, les îles de Brume-Azur et les royaumes de
l'Est. Au-delà, nagas, satyres et fantômes de Bien-nés hantent les ruines, des
cultistes se cachent dans des lieux secrets, et les furbolgs ont été rendus
fous par la corruption qui descend du Gangrebois.""",

    3524: """Île de Brume-Azur : La plus grande des îles de Brume-Azur, au
large de l'ouest de Kalimdor, longtemps peuplée seulement de furbolgs, de
sélénides et de bêtes sauvages, jusqu'à ce que l'Exodar, le vaisseau
dimensionnel des draeneï, s'écrase sur ses rivages. Les survivants menés par le
prophète Velen ont bâti leur capitale dans la plus grande partie intacte de
l'épave. L'île est une terre de forêts persistantes, de fleurs violettes et de
douces collines, mais d'étranges cristaux de l'épave parsèment le paysage, des
tempêtes arcaniques traversent le ciel et l'écrasement a altéré certaines
plantes et bêtes. Les furbolgs amicaux vivent au nord, des nagas rôdent dans de
vieilles ruines et des saboteurs elfes de sang se cachent dans les collines.""",

    3557: """L'Exodar : La capitale des draeneï, bâtie dans la plus grande
partie intacte du vaisseau dimensionnel écrasé sur l'île de Brume-Azur.
Autrefois satellite du donjon de la Tempête, il fut capturé en Outreterre par
le prophète Velen et ses fidèles avec l'aide des naaru, saboté par des elfes de
sang et projeté à travers le Néant distordu. C'est désormais une cité de salles
de cristal étincelantes et de conduits lumineux qui portent la lumière sacrée
et la chaleur. Velen réside dans le Siège des naaru auprès d'un naaru, et la
ville résonne du chant des naaru et de la dévotion tranquille d'un peuple qui a
erré pendant des millénaires.""",

    3525: """Île de Brume-Sang : La plus septentrionale des îles de Brume-Azur,
autrefois appelée Ventargent, corrompue quand des débris de l'Exodar écrasé y
répandirent des cristaux rouge sang. Un liquide semblable à du sang suinte des
cristaux dans le sol, altérant plantes et bêtes et emplissant l'air d'une
inquiétante brume pourpre ; même les pins ont rougi. Les draeneï étudient et
soignent la terre depuis le Guet-du-Sang, face à des elfes de sang avides du
pouvoir des cristaux, à des satyres, des nagas, des furbolgs corrompus et des
créatures échappées du vaisseau. D'anciennes ruines elfes de la nuit parsèment
l'île, et les esprits de dragons verts hantent la Balafre du Wyrm.""",

    331: """Orneval : Une vaste forêt ancienne du nord de Kalimdor et la patrie
ancestrale des elfes de la nuit, une étendue sauvage primitive d'arbres
gigantesques, de clairières profondes, de lacs et de rivières sous une épaisse
canopée. Pendant des millénaires, les elfes de la nuit l'ont soignée sans
jamais l'abattre, gardée par les Sentinelles, les druides et les anciens.
Pendant la Troisième Guerre, les orcs de Grom Hurlenfer vinrent pour son bois
et tuèrent le demi-dieu Cénarius. Depuis, elle est âprement disputée : les
elfes de la nuit tiennent Astranaar à l'ouest, le clan Chanteguerre coupe le
bois à l'est, et les Sentinelles d'Aile-argent et les Voltigeurs Chanteguerre
s'affrontent sans cesse. Démons, satyres et furbolgs corrompus s'attardent.""",

    361: """Gangrebois : Une forêt corrompue du nord de Kalimdor, autrefois un
paradis luxuriant protégé par Cénarius, souillée par la Légion ardente avec le
Crâne de Gul'dan pendant la Troisième Guerre. Arbres tordus, prairies calcinées
et ruisseaux bouillonnant de boue toxique emplissent la terre, et les anciens
qui la gardaient errent aveugles en saignant un poison gangrené. Furbolgs
corrompus, satyres, démons et démonistes du Conseil des ombres infestent les
bois, et les bêtes affamées s'entre-dévorent. Les druides du Cercle cénarien
s'efforcent de la purifier, et les furbolgs Grumegueules, restés purs, tiennent
les tunnels du nord vers Reflet-de-Lune et Berceau-de-l'Hiver.""",

    493: """Reflet-de-Lune : Une vallée sacrée sur les pentes inférieures du
mont Hyjal, abritée par de hautes montagnes et drapée d'une nuit éternelle, où
la lune baigne la terre d'argent et où l'air est un soir d'été tiède et sans
fin. C'est le foyer du Cercle cénarien, où elfes de la nuit et taurens vivent
en paix et où les conflits entre les races ne sont pas tolérés. Pendant des
millénaires, les druides ont dormi ici dans les Tertres tandis que leurs
esprits arpentaient le Rêve d'émeraude ; Malfurion Hurlorage y est toujours
perdu. Le village de Havrenuit s'étend sur les rives du lac Elune'ara, sous la
garde des Gardiens du bosquet.""",

    618: """Berceau-de-l'Hiver : Une vallée froide et enneigée haut sur le mont
Hyjal, dans un hiver presque éternel au-dessus des nuages de Reflet-de-Lune. La
neige couvre les collines, les lacs gelés scintillent et l'air est pur et vif.
Les elfes de la nuit s'y installèrent après la Fracture, et leurs ruines se
dressent encore dans la neige, tandis que les racines dénudées de l'Arbre-Monde
s'élèvent comme des arches. Le Vol bleu de Mazthoril dispute depuis longtemps
la vallée aux elfes de la nuit. La ville gobeline de Long-Guet est ouverte à
tous, des furbolgs corrompus, des yétis et des sabres-de-givre errent dans la
région, et des démons tiennent la gorge du Sombre-murmure au sud.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Center and East
    # -------------------------------------------------------------------------
    14: """Durotar : Une terre de sol rouge cuit par le soleil, de canyons
escarpés et de collines sur la côte est de Kalimdor, dont la beauté rude
rappelle Draenor. Thrall en fit la nouvelle patrie des orcs et des trolls
Sombrelance après la Troisième Guerre et la nomma d'après son père Durotan,
fondant Orgrimmar à sa limite nord. C'est le cœur de la Horde, avec
Tranchecolline au carrefour et le village troll de Sen'jin sur la côte sud. Les
dangers demeurent : des huran razzient depuis l'ouest, des centaures rôdent au
sud, des harpies nichent dans les canyons, la Lame ardente se cache dans des
grottes et un fort kultirassien se dresse encore sur la côte.""",

    1637: """Orgrimmar : La capitale des orcs et le siège de la Horde, une
puissante ville-forteresse bâtie dans un canyon à la limite nord de Durotar,
fondée par le chef de guerre Thrall après la Troisième Guerre et nommée d'après
Orgrim Marteau-du-Destin. De solides murailles, des portes massives et de
hautes tours la gardent, et ses quartiers sont des vallées : la vallée de la
Force, cœur commerçant ; la vallée des Esprits, foyer des trolls et des chamans
; la vallée de la Sagesse, où se dresse le fort Grommash de Thrall ; et la
vallée de l'Honneur. La Herse mène à la sombre Faille de l'ombre. Ses
constructions rustiques de bois, de peau et de pierre sont ornées de pointes et
de bannières, et des zeppelins la relient aux royaumes de l'Est et au
Norfendre.""",

    2917: """Hall des Légendes : La grande salle des officiers de la Horde dans
la vallée de la Force à Orgrimmar, un bâtiment massif de bois, de pierre et de
peaux orné de bannières, de trophées et des armes d'ennemis tombés. Il sert de
caserne et de lieu de rassemblement aux guerriers les plus illustres de la
Horde, et son arsenal secret renferme des armes de tous les continents
d'Azeroth et de Draenor, beaucoup prises comme butin de guerre et chargées
d'une fière histoire. C'est un lieu d'honneur et de fierté, où l'on raconte la
gloire autour de grands feux et où l'on se souvient des légendes de la Horde.""",

    377: """Fleuve Furie-du-Sud : L'un des grands fleuves de Kalimdor, qui naît
dans les hautes terres du mont Hyjal et coule vers le sud en un large courant
rapide. Il sépare Orneval d'Azshara et, plus au sud, les Tarides de Durotar,
passant près des murailles d'Orgrimmar. Ses eaux sont froides et rapides au
nord, tièdes et troubles au sud, où des crocilisques guettent dans les roseaux.
Il se jette dans la Grande mer par une cascade près du port gobelin de
Cabestan. Des ponts ne le franchissent qu'en quelques points, et des voyageurs
de toutes sortes traversent ses eaux.""",

    16: """Azshara : Une terre côtière belle mais maudite au nord-est de
Kalimdor, drapée d'un automne éternel, aux arbres d'un orange et d'un rouge
éclatants, aux grandes falaises et aux plages blanches. Il y a dix mille ans,
elle faisait partie de Zin-Azshari, la capitale de la reine Azshara, jusqu'à ce
que la Fracture engloutisse une grande partie de la ville. Les elfes de la nuit
la tiennent pour maudite ; des ruines se dressent sur les falaises et gisent
parmi les coraux, et les légendes disent que la reine règne désormais sur les
nagas sous les vagues. Fantômes de Bien-nés, satyres, nagas et dragons bleus
hantent la terre, les Grumegueules amicaux tiennent les montagnes ouest, et des
tempêtes arrivent souvent de la mer.""",

    17: """Les Tarides : Une vaste savane chaude d'herbe jaune, d'arbres
épineux et de plaines poussiéreuses au centre de Kalimdor, entre Orneval et
Mille pointes, avec quelques oasis luxuriantes au nord. Des cités elfes de la
nuit s'y dressaient avant la Fracture, et l'antique route de l'Or mène encore
les caravanes entre Cabestan et le nord. La Croisée de la Horde est le grand
carrefour, tandis que l'Alliance tient le Guet du Nord et les fouilles de Bael
Modan. Centaures et huran pillent les caravanes, des harpies nichent dans les
collines, la KapitalRisk fore du pétrole et la Lame ardente se cache au pic de
Morne-Effroi. Cabestan, sur la côte, est ouvert à tous.""",

    215: """Mulgore : Des plaines vertes et des mesas balayées par le vent au
centre de Kalimdor, la patrie ancestrale des taurens, ceinte de montagnes avec
un seul col vers les Tarides à l'est. Pendant des siècles, les taurens vécurent
en nomades en luttant contre les centaures, jusqu'à ce que la Horde de Thrall
les aide à les chasser et que Cairne Sabot-de-Sang bâtisse les
Pitons-du-Tonnerre sur les mesas. C'est une terre pastorale et abritée de
prairies, de lacs clairs et de brises parfumées de pin, avec des villages
taurens, des moulins à vent et des totems sculptés. Des huran tiennent les
sacrés Rochers rouges, la KapitalRisk a saisi les puits sacrés et des harpies
nichent au nord.""",

    1638: """Les Pitons-du-Tonnerre : La capitale des taurens, bâtie au sommet
de quatre hautes mesas au nord de Mulgore, très haut au-dessus des Plaines
dorées, la première ville permanente d'un peuple qui erra des siècles durant.
De grandes tentes, des maisons longues et des mâts totémiques couronnent les
mesas, reliées par des ponts de corde qui se balancent, et des ascenseurs de
bois hissent les visiteurs depuis les plaines. Le grand chef Cairne
Sabot-de-Sang règne depuis la mesa centrale, les druides se réunissent sur le
Promontoire des Anciens, les chamans sur le Promontoire des Esprits au-dessus
des brumeux Bassins de la vision, et les chasseurs sur le Promontoire des
Chasseurs. Le temps est chaud et ensoleillé, et la vue sur Mulgore est
saisissante.""",

    406: """Les Serres-Rocheuses : Une chaîne escarpée au centre de Kalimdor,
soulevée par la Fracture et creusée par la rivière Loup-Noir en canyons et en
falaises. Les basses pentes sont chaudes, sèches et venteuses, la pluie se
brise sur les sommets ouest et de violents vents mauvais fouettent les canyons.
Le pic des Serres-Rocheuses, sacré pour les elfes de la nuit et les taurens,
fut jadis la demeure de l'Oracle. Les gobelins de la KapitalRisk abattent les
forêts anciennes et souillent les eaux, la vallée calcinée est une ruine brûlée
pleine d'élémentaires de feu, des harpies tiennent des places fortes dans les
canyons et des taurens renégats Totem-sinistre attaquent leurs propres frères.""",

    # -------------------------------------------------------------------------
    # Kalimdor - South
    # -------------------------------------------------------------------------
    405: """Désolace : Une désolation grise et rocailleuse à l'ouest de
Kalimdor qui semble frappée d'une malédiction : le ciel est toujours sombre et
orageux, éclairs et vents violents balaient la terre, des mares jaunes et
souillées parsèment la cendre et les crânes d'anciens kodos fixent le vide
depuis leurs tombes. C'est la patrie des centaures, nés selon la légende dans
les profondeurs de Maraudon, et quatre tribus rivales s'y battent entre elles
aussi férocement que contre les étrangers. Des ruines de Bien-nés sont
éparpillées, des nagas hantent la côte nord-ouest et la Lame ardente y a
invoqué des démons. Par un triste contraste, la côte ouest est ensoleillée et
luxuriante.""",

    357: """Feralas : Une forêt tropicale ancienne et luxuriante au sud-ouest
de Kalimdor, aux arbres immenses, aux vallées brumeuses, aux rivières
tumultueuses et aux lacs clairs, abritée par de hautes montagnes. Elle faisait
partie de l'empire elfe de la nuit, et la vaste cité de Bien-nés
d'Eldre'Thalas, aujourd'hui appelée Hache-Tripes, gît en ruine parmi les
arbres. Les elfes de la nuit tiennent la forteresse de Pennelune sur l'île de
Sardor, et les taurens le camp Mojache à l'est. Les sanguinaires ogres Gordunni
contrôlent de nombreuses ruines, des renégats Totem-sinistre tiennent un camp,
des nagas infestent les îles de l'ouest et un grand arbre au nord-ouest est un
portail vers le Rêve d'émeraude.""",

    400: """Mille pointes : Un immense canyon sec au sud de Kalimdor, empli de
hautes aiguilles de grès qui se dressent comme une forêt d'aiguilles, sculptées
par l'eau avant que la Fracture ne soulève la terre. À l'est, il s'ouvre sur
les Salines Scintillantes, une étendue de sel où ingénieurs gobelins et gnomes
font la course avec leurs machines, et les levers de soleil depuis les mesas
sont spectaculaires. Des tribus taurens vécurent longtemps dangereusement au
sommet des mesas et ripostent désormais depuis le poste de Librevent. Les
centaures Galak patrouillent au fond du canyon, des renégats Totem-sinistre
tiennent le pic de Sombrenuée, et des ponts de corde relient les aiguilles
au-dessus des dangers.""",

    15: """Marécage d'Âprefange : Un vaste marais chaud et fétide sur la côte
est du centre de Kalimdor, affaissé lors de la Fracture, où bourdonnent les
moustiques, où les arbres trempent leurs palmes dans des mares stagnantes et où
des bancs de boue séparent des chenaux étouffés d'algues. Raptors, araignées,
crocilisques et murlocs rôdent partout, et au sud, la dragonne noire Onyxia
demeurerait dans le Bourbier aux wyrms. Jaina Portvaillant fonda Theramore sur
une île au large, les ogres Rochecime accueillent la Horde à Fortrenard, et
c'est ici que l'amiral Daelin Portvaillant trouva la mort. Des escarmouches
discrètes se poursuivent malgré la trêve, et les gobelins de Gué-de-Boue
accueillent tout le monde.""",

    2159: """Repaire d'Onyxia : Une grotte volcanique dans le Bourbier aux
wyrms, au sud du marécage d'Âprefange, le repaire d'Onyxia, grande dragonne
noire et fille d'Aile-de-mort, mère du Vol noir. La grotte s'enfonce
profondément dans la terre chaude, et la salle principale abrite son immense
couvée, gardée par des dragonnets et des draconiens. Le sol n'est qu'une fine
croûte au-dessus de la roche en fusion, l'air est chargé de fumée, de soufre et
de la puanteur de ses victimes, et ossements et trésors gisent parmi les
rochers. Les voyageurs racontent de sombres histoires sur ceux qu'enlève sa
progéniture, et rares sont ceux qui en reviennent.""",

    440: """Tanaris : Un immense désert au sud-est de Kalimdor, une mer infinie
de dunes sous un ciel sans nuages, brûlant le jour et balayé de dangereuses
tempêtes de sable, avec des montagnes et des cavernes profondes au sud. C'est
la patrie ancestrale du Vol de bronze, dont l'Aspect Nozdormu réside dans les
grottes du Temps, et au sud se trouve la porte scellée de la cité titanesque
d'Uldum. Les gobelins du cartel Gentepression tiennent la ville neutre de
Gadgetzan et le port du cartel. Les trolls Furie-des-sables règnent depuis
Zul'Farrak, des ogres tiennent des ruines au sud, des bandits saisissent les
châteaux d'eau et des pirates se cachent sur la côte.""",

    1941: """Grottes du temps : Un vaste réseau de grottes à l'est de Tanaris,
demeure du Vol de bronze et de son Aspect Nozdormu, gardiens du cours du temps.
Des portails mènent à des moments clés de l'histoire du monde, comme
l'ouverture de la Porte des ténèbres, la fuite de Thrall de Fort-de-Durn, la
bataille du mont Hyjal et l'épuration de Stratholme. Le sable fait place à une
végétation luxuriante, de grands sabliers tournent et des statues colossales de
dragons de bronze se dressent. Récemment, le Vol infini a commencé à s'immiscer
dans l'histoire, et les dragons de bronze cherchent de l'aide. On dit que ceux
qui entrent sans y être invités en ressortent changés.""",

    490: """Cratère d'Un'Goro : Un immense cratère luxuriant au sud de
Kalimdor, entre Tanaris et Silithus, isolé par de hautes parois. Une jungle
fumante de plantes exotiques et de créatures géantes l'emplit : diablosaures,
stégodons et ptérrordax errent librement, des gorilles vivent dans les grottes
et des silithides creusent des ruches au sud. Le volcan actif de la Crête de
feu s'élève en son centre, sources chaudes et fosses de goudron bouillonnent,
et d'étranges cristaux et de mystérieux pylônes parsèment la terre. Beaucoup de
savants pensent que ce fut un lieu des titans. Des explorateurs de toutes les
races se réunissent au Refuge de Marshal sur la paroi nord, et la jungle ne se
tait jamais.""",

    1377: """Silithus : Un désert rude de roche et de sable à l'angle sud-ouest
de Kalimdor, hérissé des hautes ruches des silithides insectoïdes. Il y a mille
ans, leurs maîtres qiraji menèrent la guerre des Sables changeants, jusqu'à ce
que les elfes de la nuit et les Vols draconiques les enferment derrière le mur
du Scarabée, à Ahn'Qiraj. Récemment, les portes ont été rouvertes, et les
armées de l'Alliance et de la Horde ont marché contre les qiraji. Le Cercle
cénarien veille depuis le fort Cénarien, le Vol de bronze est revenu et le
Marteau du crépuscule campe dans toute la région. La chaleur est implacable, et
le vent charrie un sable cinglant.""",

    3478: """Portes d'Ahn'Qiraj : Les grandes portes du mur du Scarabée, à la
limite sud de Silithus, qui gardent Ahn'Qiraj, l'antique forteresse des qiraji
et de leurs silithides. Il y a mille ans, les elfes de la nuit et les Vols
draconiques enfermèrent les qiraji derrière le mur ; récemment, les portes
furent rouvertes grâce au Sceptre des Sables changeants, et les armées de
l'Alliance et de la Horde y entrèrent. Au-delà s'étendent les Ruines et le
Temple d'Ahn'Qiraj, où demeureraient les véritables maîtres des qiraji. Le
sable devant les portes porte les cicatrices des batailles, et un silence
inquiétant pèse sur elles.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Péninsule des Flammes infernales : Une désolation aride, rouge
sang, à l'est de l'Outreterre, vestige de Draenor et première terre au-delà de
la Porte des ténèbres. Les démonistes orcs en ont drainé la vie il y a
longtemps, le sol rouge et craquelé crache des geysers de feu, et des fragments
de terre flottent à ses bords sur le ciel tourbillonnant du Néant. C'est ici
que l'expédition de l'Alliance combattit la Horde de Draenor et scella la
Porte. Aujourd'hui, la citadelle des Flammes infernales est la forteresse des
gangr'orcs, la Légion ardente assaille la Marche de la Destinée depuis ses
forges, l'Alliance tient le bastion de l'Honneur et la Horde Thrallmar.""",

    3521: """Marécage de Zangar : Un marais d'une beauté envoûtante à l'ouest
de l'Outreterre, couvert d'une forêt de champignons géants qui dominent ses
lacs comme de grands arbres. Champignons luisants, spores scintillantes et
créatures bioluminescentes emplissent son crépuscule éternel de lueurs bleues
et vertes, et il échappa largement à la corruption qui ravagea Draenor. Son
équilibre vacille désormais : les nagas de dame Vashj assèchent ses eaux avec
de grandes pompes au réservoir de Glissecroc, des ogres abattent les
champignons, et le marais se meurt. L'expédition cénarienne le défend depuis le
refuge Cénarien, et les paisibles sporelins, un peuple de champignons doués de
raison, vivent à Sporeggar.""",

    3519: """Forêt de Terokkar : Une forêt sombre et ancienne au sud de
l'Outreterre, aux hauts pins de cristal, à l'épaisse canopée verte et aux
clairières brumeuses, patrie des arakkoa à l'apparence d'oiseaux, dont la
capitale cachée, Skettis, se trouve dans les montagnes du sud-est. Au
nord-ouest se dresse Shattrath, refuge des exilés de toutes les races. La
moitié sud forme les Terres désolées, ravagées quand le Conseil des ombres
invoqua une entité terrible dans la nécropole draeneï d'Auchindoun et ouvrit
une faille qui attira les éthériens en Outreterre. L'Alliance tient le bastion
d'Allerian et la Horde le poste de Brise-pierre, tandis que gangr'orcs et
démonistes du Conseil des ombres rôdent dans la forêt.""",

    3703: """Shattrath : La Cité de la Lumière, l'antique capitale draeneï au
nord-ouest de la forêt de Terokkar, tombée devant les orcs corrompus par les
démons et rebâtie par les Sha'tar, des naaru nés de la lumière, avec les
prêtres draeneï de l'Aldor. Les elfes de sang envoyés par Kael'thas pour la
détruire déposèrent les armes et devinrent les Clairvoyants, rivaux acharnés de
l'Aldor dans la même ville. Le naaru A'dal règne depuis la terrasse de la
Lumière, où réside aussi l'archimage Khadgar. La Ville basse regorge de
réfugiés de toutes les races, la violence entre l'Alliance et la Horde y est
interdite, et des portails relient la ville aux capitales d'Azeroth.""",

    3917: """Auchindoun : La nécropole brisée des draeneï au cœur des Terres
désolées de la forêt de Terokkar, pendant des millénaires leur lieu le plus
sacré, où ils inhumaient leurs morts honorés. Des agents du Conseil des ombres
y invoquèrent un ancien élémentaire du son, et le rituel fit éclater le temple,
ravagea la forêt et ouvrit une faille qui attira les éthériens en Outreterre.
Les morts draeneï errent désormais dans les ruines en esprits sans repos. Ses
salles sont revendiquées par diverses puissances : éthériens dans les
Tombes-mana, démons dans les cryptes Auchenaï, arakkoa dans les salles des
Sethekk et Conseil des ombres dans le labyrinthe des Ombres.""",

    3518: """Nagrand : La dernière terre intacte de l'Outreterre, des prairies
ondulantes vertes et dorées, des lacs étincelants et des îles flottantes sous
un ciel teinté de rose. Son nom signifie Terre des vents ; ce fut la patrie du
clan Loup-de-givre et le lieu de rassemblement des orcs au pied de la montagne
sacrée d'Oshu'gun. Les élémentaires y parlent aux mortels au Trône des
éléments. Les orcs mag'har, restés purs, vivent à Garadar sous la conduite de
la Matriarche Geyah, et les Roués kurenaï à Telaar. Des ogres menacent la
terre, la Légion a des forges à l'ouest, et la ville de Halaa est disputée par
l'Alliance et la Horde.""",

    3522: """Les Tranchantes : Des crêtes acérées comme des lames et des
vallées taillées à la hache au nord de l'Outreterre, usées par des vents
violents en pointes semblables à des dagues sous la lueur verte du Néant. C'est
la terre des ogres des clans Lamecime et Mâcheroc, qui s'affrontent pour la
faveur des gronns, des géants menés par Gruul le Tue-dragon depuis son repaire
au nord ; les ossements de dragons noirs tués pendent empalés sur les pics. La
Légion a des forges sur les plateaux, et des cultistes des dragons noirs rôdent
au nord. Les elfes de la nuit tiennent Sylvanaar, la Horde le bastion
Tonnerre-des-Lames, et les ogres éclairés d'Ogri'la vivent sur un plateau à
l'ouest.""",

    3523: """Raz-de-Néant : De vastes fragments de terre et d'innombrables
éclats de roche flottant dans le Néant distordu au nord-est de l'Outreterre,
autrefois les champs de Farahlon. Une tempête arcanique incessante déforme la
terre : le sol est d'un violet maladif, des éclairs magiques zèbrent une brume
violette et des rubans d'énergie se tordent dans le ciel tandis que la région
se désagrège lentement. Des elfes de sang fidèles à Kael'thas puisent dans le
Néant au moyen de grandes manaforges bâties avec la technologie du donjon de la
Tempête, qu'ils tiennent, et la Légion ardente a des bases sur les îles. Les
éthériens du Consortium tiennent la Foudreflèche et leurs écodômes, et des
gobelins dirigent la Zone 52.""",

    3520: """Vallée d'Ombrelune : Une terre sinistre et dévastée au sud-est de
l'Outreterre, où jour et nuit jaillit une énergie gangrenée en fusion qui
embrase le ciel de flammes vertes. Roche noire et cendre couvrent le sol, et le
volcan appelé Main de Gul'dan crache une lave verte en son centre. À l'est se
dresse le Temple noir, autrefois le temple de Karabor des draeneï, aujourd'hui
la citadelle d'Illidan Hurlorage, autoproclamé seigneur de l'Outreterre, et de
ses Illidari, qui repoussent la Légion ardente depuis le bastion de la Légion.
Des gangr'orcs Gueule-de-dragon asservissent les drakes de l'Aile-du-Néant. Le
bastion Marteau-Hardi, le village d'Ombrelune et les camps de l'Aldor et des
Clairvoyants font la guerre à Illidan.""",

    3540: """Néant distordu : Le royaume astral chaotique entre les mondes, une
dimension de magie sauvage qui relie les mondes de l'univers et abrite les
démons de la Légion ardente. Quand Draenor fut déchiré, ses restes furent
attirés dans le Néant, et aux bords de l'Outreterre la terre s'arrête tout
simplement sur un vide sans fin de nuages irisés, de rubans d'énergie colorée
et de rochers à la dérive. Des mondes lointains se devinent dans le ciel
tourbillonnant, les lois de la nature semblent incertaines, et l'esprit peine à
comprendre ce que voient les yeux. Ceux qui s'aventurent trop loin pourraient
ne jamais revenir.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Toundra Boréenne : Une vaste plaine balayée par les vents au bord
sud-ouest du Norfendre, pour beaucoup la première terre aperçue dans la guerre
contre le roi-liche. Terre brun-rouge, lichens et glace s'étendent sous un vent
capable d'arracher la barbe d'un nain ; des geysers fument au centre, et l'est
enneigé est le plus rude. Mammouths et rhinocéros laineux parcourent les
plaines, et les paisibles rohart pêchent et chassent la baleine sur la côte,
leurs villages ravagés par des pillards kvaldir. Malygos et le Vol bleu règnent
sur l'île de Frimarra, le Fléau tient En'kilah, et le donjon de la Bravoure de
l'Alliance et le bastion Chanteguerre de la Horde font face au nord.""",

    495: """Fjord Hurlant : Une région rude au sud-est du Norfendre, faite de
prairies vertes, de rivières glacées, de sombres forêts de pins et de hauts
fjords dont les falaises plongent dans la mer froide. Au fond de la baie de
Daguechape, le donjon d'Utgarde domine le lac Cauldros. Ce fut le siège
ancestral des vrykuls, des guerriers géants sortis d'un long sommeil ; beaucoup
servent désormais le roi-liche et attaquent quiconque s'approche. L'Alliance
tient le vieux port de Valgarde et le Guet de l'Ouest, les Réprouvés de la Main
de la vengeance tiennent le Havre de la Vengeance et Nouvelle-Agamand, et la
Ligue des explorateurs fouille des ruines titanesques là où sont apparus des
nains de fer.""",

    65: """Désolation des dragons : Le cœur du sud du Norfendre, une désolation
arctique de glaciers d'un blanc éblouissant jonchée des ossements luisants de
dragons, le lieu où les dragons viennent mourir. C'est ici que les gardiens des
titans créèrent les premiers Aspects, et les ossements de Galakrond sortent
encore de la glace. En son centre s'élève le temple du Repos du ver, où se
réunissent les Vols draconiques, entouré des cinq sanctuaires draconiques. Le
Fléau assiège les sanctuaires et lève des wyrms de givre à partir des
ossements, Naxxramas flotte au-dessus des plaines de l'est et l'Assaut écarlate
tient une forteresse sur la côte. L'Alliance et la Horde ont élevé des places
fortes devant le Portail du courroux, l'entrée barrée de la Couronne de glace.""",

    394: """Les Grisonnes : Une région boisée au sud-est du Norfendre, de
douces collines vertes couvertes de pins qui montent vers des montagnes
escarpées, où l'épaisse forêt arrête le vent et où les collines semblent
presque tièdes. Ours, loups, cerfs et harfangs peuplent les bois. C'est la
patrie des furbolgs, dont la cité de Gueule-de-Grisonne se dresse dans la
souche de Vordrassil, un Arbre-Monde que les druides détruisirent en le
découvrant corrompu, et une folie rampante se répand parmi leurs tribus. Des
trappeurs tiennent des comptoirs dans la forêt, le Fléau tient le donjon de
Drak'Tharon au nord, et l'Alliance et la Horde se disputent les camps de
bûcherons.""",

    4201: """Larmes de Vordrassil : L'un des grands fragments tombés de
l'Arbre-Monde Vordrassil, dans les Grisonnes. Il y a longtemps, Fandral
Forteramure planta des branches de Nordrassil dans tout le Norfendre, et la
plus grande, Andrassil, la Couronne des neiges, domina ces collines pendant des
décennies. Mais ses racines atteignirent la prison d'un mal ancien, et la folie
se répandit parmi les créatures de la région, si bien que le Cercle cénarien
détruisit l'arbre et le nomma Vordrassil, la Couronne brisée. Ses morceaux
gisent encore dans la forêt, et la terre autour de ce fragment est couverte
d'une vase vivante, signe de la corruption qui le condamna.""",

    3477: """Azjol-Nerub : Un immense royaume souterrain sous la moitié du
Norfendre, l'antique royaume des nérubiens arachnides, un peuple voué à
l'érudition, aux arts et à la philosophie, aux couloirs polis, aux salles
sculptées et aux grandes bibliothèques éclairées de champignons luminescents.
Le roi-liche voyait en eux la plus grande menace pour son pouvoir et envahit le
royaume lors de la guerre de l'Araignée ; chaque nérubien tombé se relevait
pour combattre pour le Fléau, et leur propre roi Anub'arak le sert désormais.
Des nérubiens morts-vivants gardent les couvées du royaume Supérieur, des
survivants mènent une guerre cachée, et dans l'Ancien royaume d'Ahn'kahet
s'agitent les Sans-visage.""",

    66: """Zul'Drak : La patrie des trolls des glaces Drakkari à l'est du
Norfendre, une vallée qui est à elle seule une immense cité-temple de places,
de ziggourats, de murailles et d'aqueducs bâtis en terrasses, avec des arbres
épineux, des mares gelées et de la neige entre les ruines. Les Drakkari sont
parmi les plus anciennes races d'Azeroth et règnent depuis Gundrak, mais leur
empire s'effondre. Le Fléau tient le donjon de Drak'Tharon et ses nécropoles
relèvent les trolls tombés contre leur propre peuple. Désespérés, les prophètes
Drakkari ont tué leurs propres dieux, les loas, et boivent leur sang pour en
tirer du pouvoir, ce qui en a rendu beaucoup fous. La Croisade d'argent et les
Zandalari sont venus intervenir.""",

    3711: """Bassin de Sholazar : Un bassin de jungle tropicale au milieu du
Norfendre, ceint de hautes montagnes, chaud, humide et grouillant de vie après
le froid mordant du dehors. La gardienne Freya en fit un berceau de vie, et des
pylônes titanesques couronnés de cristaux tourbillonnants y maintiennent la
chaleur et le protègent des créatures impures. Quatre rivières se rejoignent au
Cœur-du-Fleuve, dans la dense Mangrove sauvage. Rhinocéros, gorilles,
crocilisques et hydres peuplent la jungle, et les gorlocs Oracles affrontent
les wolvars Frénécœur. Le Fléau a pénétré dans le bassin par l'est, et l'Avatar
de Freya lutte pour contenir la souillure qui s'étend.""",

    2817: """Forêt du Chant de cristal : Une terre au milieu du Norfendre où
chaque arbre, chaque brin d'herbe et une grande partie du sol sont devenus un
cristal vivant et lumineux, qui vibre au vent si bien que la forêt joue une
musique douce et sans fin. Ce fut autrefois Chant-de-Lune, où les Bien-nés
tenaient l'avant-poste de Shandaral ; quand les dragons bleus vinrent se venger
de reliques volées, le sort imprudent des sorciers cristallisa toute la forêt,
et leurs esprits y errent encore. Dalaran flotte désormais au-dessus de l'ouest
de la forêt, le Concordat argenté et les Saccage-soleil tiennent des tours en
ruine de part et d'autre, et le Vol bleu mène la guerre du Nexus au sud.""",

    4395: """Dalaran : La cité des mages et la demeure du Kirin Tor, dont les
flèches violettes se dressaient jadis au bord du lac Lordamere, jusqu'à ce que
le Fléau la détruise pendant la Troisième Guerre. Le Kirin Tor a soulevé toute
la ville dans le ciel et l'a transportée au Norfendre, où elle flotte au-dessus
de la forêt du Chant de cristal pour s'opposer au roi-liche et à l'Aspect bleu
Malygos, dont la guerre contre les lanceurs de sorts fait d'elle une cible de
choix. Le Conseil des Six, mené par l'archimage Rhonin, gouverne depuis la
citadelle Pourpre. Dalaran accueille l'Alliance et la Horde : le Concordat
argenté et les Saccage-soleil y tiennent leurs propres enclaves et s'observent
avec méfiance.""",

    4197: """Joug-d'hiver : Une vallée gelée au centre du Norfendre, surélevée
par rapport aux terres voisines, le lit d'un lac rétréci qui a révélé des
ruines titanesques, des forêts sombres, des marais gelés et un chaudron
volcanique. En son cœur se dresse la forteresse de Joug-d'hiver, un complexe
titan qui garde l'entrée du caveau d'Archavon, où reposent des reliques
titanesques d'une puissance inouïe sous la garde d'anciens géants qui détestent
tout intrus. Depuis le début de la guerre contre le roi-liche, l'Alliance et la
Horde se battent sans fin pour la forteresse et le caveau, martelant ses murs
d'engins de siège tandis que le contrôle change de mains encore et encore.""",

    67: """Les pics Foudroyés : Une haute chaîne de montagnes au nord-est du
Norfendre, rude et dangereuse, où des vents violents peuvent arracher un nain
d'une falaise, où les avalanches grondent sur les pentes et où l'éclat de la
glace aveugle les imprudents. Les pics furent la demeure des gardiens des
titans, et presque chaque montagne cache temples, terrasses et machines
immenses ; le temple des Tempêtes couronne le plus haut sommet, et au nord
s'étend Ulduar, le plus grand complexe titan d'Azeroth. Son gardien Loken s'est
tourné vers les ténèbres, et ses nains et géants de fer chassent les terrestres
de leur foyer. Les géants du givre des Fils de Hodir tiennent les vallées de
l'est.""",

    210: """La Couronne de glace : Le cœur sombre du Norfendre et le siège du
roi-liche, une terre de montagnes et de glacier où la glace a noirci de
corruption. Depuis le Trône de glace, le roi-liche asservit les peuples du
Norfendre et leva le Fléau, et autour du trône se dresse la citadelle de la
Couronne de glace, une cathédrale de lames de saronite visible de presque
partout sur le continent. Murailles et passerelles de saronite relient
forteresses, nécropoles et mines, et les morts-vivants dépassent en nombre tout
le reste. La guerre est désormais à sa porte : la Croisade d'argent et les
Chevaliers de la Lame d'ébène frappent depuis des places fortes conquises, et
les canonnières de l'Alliance et de la Horde combattent dans le ciel.""",

    4742: """Accostage de Hrothgar : Une petite île noyée de brume au large de
la côte nord de la Couronne de glace, au-delà du détroit appelé passage des
Écumeurs. Un village rohart s'y dressait autrefois, jusqu'à ce que les kvaldir,
les vrykuls des mers maudits, viennent sous leur chef Hrothgar, tuent ou
chassent ses habitants et rebaptisent l'île de son nom. C'est désormais une
base pour les raids kvaldir contre les navires du détroit, où ils appellent de
grands kraken des profondeurs, tandis que les flottes du Concordat argenté et
des Saccage-soleil luttent pour les repousser.""",

    # -------------------------------------------------------------------------
    # Seas
    # -------------------------------------------------------------------------
    308: """La mer Interdite : Une mer vaste, froide et à peine cartographiée
le long de la côte est des royaumes de l'Est, du marais des Chagrins jusqu'au
bois des Chants éternels. Ses eaux grises sont agitées et souvent noyées de
brouillard, de forts courants et des tempêtes soudaines rendent la navigation
dangereuse, et une grande partie de la côte est barrée de falaises et de
montagnes. Peu de navires s'éloignent du rivage, et les marins parlent de
terres inconnues et de créatures terribles au-delà de l'horizon. Requins et
serpents de mer vivent dans ses profondeurs, et murlocs et nagas rôdent sur ses
rives.""",

    214: """La Grande mer : L'immense océan entre les continents d'Azeroth, né
quand le Puits d'éternité fut détruit et que l'ancien Kalimdor se brisa lors de
la Fracture ; toutes les mers du monde s'y rattachent. Ses eaux d'un bleu
profond s'étendent au-delà de l'horizon, et les marins parlent d'îles perdues,
de cités englouties et du grand tourbillon du Maelström en son cœur, là où se
trouvait le Puits. Les tempêtes se lèvent soudainement, et serpents de mer,
requins géants et nagas guetteraient dans ses profondeurs. Les navires de
l'Alliance, de la Horde, des gobelins et des pirates la traversent sans cesse
entre les continents.""",

    332: """La Grande mer : Le grand large entre les continents d'Azeroth, né
quand le Puits d'éternité implosa lors de la Fracture. Loin de toute côte,
seule une eau bleue infinie s'étend dans toutes les directions, rompue par une
île lointaine ou un navire de passage. La houle monte et descend, les oiseaux
de mer tournoient haut dans le ciel, et dans les profondeurs nagent des
créatures que peu ont jamais vues. Les marins évoquent avec crainte le
Maelström, le tourbillon colossal au centre de la mer, et les innombrables
navires perdus dans les tempêtes et les abysses. C'est un lieu de solitude et
de danger, où règnent le vent et les vagues.""",

    457: """La mer Voilée : Le grand océan au large des côtes ouest de
Kalimdor, qui s'étend depuis Sombrivage, Orneval, Désolace et Feralas vers
l'ouest inconnu. Souvent voilée de brume, d'où son nom, elle a des eaux
profondes, froides au nord et plus chaudes au sud. Teldrassil s'en élève au
large de la côte nord-ouest, et les îles de Brume-Azur s'y trouvent. Nagas,
géants des mers et serpents de mer vivent dans ses profondeurs, et les ruines
englouties d'antiques cités elfes de la nuit gisent sous ses vagues. Au-delà
des côtes connues, elle est presque inexplorée.""",

    3479: """La mer Voilée : Les eaux autour des îles de Brume-Azur, au large
du nord-ouest de Kalimdor, où s'est écrasé le vaisseau draeneï appelé l'Exodar.
La mer y est profonde et souvent voilée de brume, et les débris et cristaux du
vaisseau donnent à certaines eaux côtières une étrange lueur, surtout autour de
l'île de Brume-Sang, dont les rivages rougissent. Murlocs et nagas vivent le
long des côtes, des ruines elfes de la nuit englouties gisent sous les vagues,
et des navires font la navette entre l'Exodar et les terres des elfes de la
nuit, tandis qu'à l'est Teldrassil s'élève de la mer.""",

    3455: """La mer du Nord : Les eaux froides au large des côtes nord de
Quel'Thalas, qui s'étendent depuis le bois des Chants éternels vers le nord, en
direction du Norfendre. L'île de Quel'Danas s'en élève au large de la côte
nord, et les navires elfiques qui les parcourent relient depuis longtemps la
patrie des elfes au reste du monde. Les eaux sont froides et grises, et les
vents qui les balaient portent le froid du grand nord gelé.""",

    4258: """La mer du Nord : Les eaux froides le long des côtes sud-est du
Norfendre, au large des Grisonnes et du Fjord Hurlant, qui s'étendent au sud
jusqu'aux côtes nord de Lordaeron. Des îles comme l'île de la Lune de sang et
les ruines de Tethys parsèment l'eau grise. Des navires de l'Alliance et des
Réprouvés la traversent vers les ports du fjord, tandis que drakkars vrykuls et
pillards kvaldir rôdent dans les brumes.""",

    4630: """La mer du Nord : Les eaux glaciales autour des côtes est et nord
du Norfendre, grises et pleines de glaces flottantes sous des vents mordants.
Peu de navires s'aventurent loin dans ces eaux, car icebergs et brouillard
cachent les côtes, et l'on dit que les kvaldir maudits et d'autres pillards des
mers surgissent des brumes.""",

    3979: """La mer Gelée : La mer froide au sud du Norfendre, partie de la
Grande mer, qui s'étend des côtes sud de la toundra Boréenne, de la Désolation
des dragons et du Fjord Hurlant jusqu'au Maelström. Banquise et icebergs
dérivent sur ses eaux grises. Les flottes de l'Alliance et de la Horde la
traversent pour atteindre le continent, les rohart voyagent sur des tortues
géantes entre leurs villages côtiers, et les colonnes sculptées de l'antique
Sentier des titans émergent des vagues. Pillards kvaldir et monstres marins
hantent ses profondeurs.""",
}

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'Une vallée cachée au cœur des montagnes d\'Alterac, foyer '
            'des orcs Loup-de-givre depuis que Gul\'dan les y exila '
            'avant la Première Guerre. Les nains de l\'expédition '
            'Foudrepique sont venus fouiller la vallée à la recherche '
            'de ressources et de reliques titanesques et la '
            'revendiquent pour Forgefer, et les Loups-de-givre ont '
            'juré de les chasser. La guerre fait désormais rage de la '
            'forteresse de Dun Baldar au nord jusqu\'au donjon '
            'Loup-de-givre au sud.'
        ),
        'tone': (
            'Épique et immense, une véritable guerre entre deux '
            'armées dans la neige.'
        ),
        'objectives': (
            'Tuez le général ennemi. Prenez les tours et les '
            'cimetières.'
        ),
        'landmarks': (
            'Lieux clés : Dun Baldar et les fortins Foudrepique au '
            'nord, Gîte-de-Pierre et Chute-des-Neiges au centre, la '
            'tour de la Halte glacée et la Tour de la pointe, le '
            'cimetière et le donjon Loup-de-givre au sud. Neige, '
            'forêts de pins, cols de montagne et grottes de glace. Ne '
            'mentionnez AUCUN lieu d\'un autre champ de bataille.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'Un ravin forestier au sud d\'Orneval, où les orcs de Grom '
            'Hurlenfer abattirent de vastes pans de forêt pendant la '
            'Troisième Guerre. Les orcs des Voltigeurs Chanteguerre y '
            'coupent toujours du bois pour la Horde, et les '
            'Sentinelles d\'Aile-argent des elfes de la nuit ont juré '
            'de ne pas connaître de repos tant que le dernier orc ne '
            'sera pas chassé du goulet.'
        ),
        'tone': (
            'Intense, rapide et personnel, une lutte acharnée pour la '
            'forêt.'
        ),
        'objectives': 'Capturez trois fois le drapeau ennemi.',
        'landmarks': (
            'Lieux clés : le bastion d\'Aile-argent (place forte des '
            'elfes de la nuit), le fort Chanteguerre (place forte des '
            'orcs), les tunnels sous chaque base, le terrain central '
            'à découvert, les rampes et les cimetières. Grands '
            'arbres, souches et piles de bois. Ne mentionnez AUCUN '
            'lieu d\'un autre champ de bataille, comme des scieries, '
            'des fermes ou des tours.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'Un bassin fertile au cœur des Hautes-terres d\'Arathi, '
            'riche en minerai, en bois et en terres agricoles. La '
            'Ligue d\'Arathor, ce qui reste de Stromgarde, se bat pour '
            'reprendre les ressources de la région, tandis que les '
            'Profanateurs réprouvés cherchent à s\'en emparer pour la '
            'Horde.'
        ),
        'tone': (
            'Stratégique et territorial, disputé sur tout le bassin à '
            'la fois.'
        ),
        'objectives': (
            'Tenez des points pour atteindre 1600 ressources en '
            'premier.'
        ),
        'landmarks': (
            'Lieux clés : Écuries (nord, pâturages ouverts avec '
            'enclos à chevaux), Forge (carrefour central, fumée et '
            'enclumes), Scierie (point de vue sur la colline, '
            'plates-formes en bois et lames de scie), Mine d\'or '
            '(entrée de grotte au sud-est, wagonnets et torches), '
            'Ferme (sud, champs et meules de foin près d\'une ferme). '
            'Ne mentionnez AUCUN lieu d\'un autre champ de bataille.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'Un fragment de Draenor flottant dans le Néant distordu à '
            'la lisière de Raz-de-Néant, où quatre ruines se dressent '
            'sur une grande île autour d\'une source d\'énergie pure en '
            'son centre. L\'Alliance et la Horde se battent pour '
            'contrôler l\'île et sa puissance.'
        ),
        'tone': (
            'Tendu et chaotique, avec le vide du Néant juste au-delà '
            'des bords.'
        ),
        'objectives': (
            'Tenez des bases et capturez le drapeau central pour '
            'atteindre 1600 points.'
        ),
        'landmarks': (
            'Lieux clés : Ruines du Saccageur gangrené, Tour des '
            'elfes de sang, Ruines draeneï, Tour des mages, les ponts '
            'et le drapeau central. Pierre violette, énergie '
            'crépitante et Néant sans fin tout autour. Ne mentionnez '
            'AUCUN lieu d\'un autre champ de bataille.'
        ),
    },
    9: {  # SA (BATTLEGROUND_SA = 9)
        'name': 'Strand of the Ancients',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'Une île au large de la côte sud de la Désolation des '
            'dragons, où une relique des titans repose derrière les '
            'murs croulants d\'une antique citadelle. L\'Alliance et la '
            'Horde la convoitent toutes deux pour le savoir des '
            'titans qu\'elle renfermerait : un camp assaille les murs '
            'depuis la mer tandis que l\'autre les défend.'
        ),
        'tone': (
            'Un siège éprouvant, vague après vague contre des murs '
            'antiques.'
        ),
        'objectives': (
            'Percez les portes et capturez la relique, ou défendez-la '
            'le plus longtemps possible.'
        ),
        'landmarks': (
            'Lieux clés : la plage et les quais où débarquent les '
            'assaillants, la porte de l\'Émeraude verte et la porte du '
            'Saphir bleu, la porte du Soleil rouge et la porte de '
            'l\'Améthyste violette, la porte de la Lune jaune, la '
            'chambre des Reliques anciennes, démolisseurs, canons et '
            'cimetières. Sable scintillant, pierre titanesque et '
            'vagues qui se brisent. Ne mentionnez AUCUN lieu d\'un '
            'autre champ de bataille.'
        ),
    },
    30: {  # IC (BATTLEGROUND_IC = 30)
        'name': 'Isle of Conquest',
        'alliance_faction': '7th Legion',
        'horde_faction': 'Warsong Offensive',
        'lore': (
            'Une île d\'une grande valeur stratégique pour la guerre '
            'au Norfendre, avec des quais, une carrière, une '
            'raffinerie, un atelier de siège et un hangar à '
            'canonnières. L\'Alliance, sous le haut commandant Halford '
            'Wyrmbane, et la Horde, sous le suzerain Agmar, tiennent '
            'chacune une forteresse sur l\'île et se battent pour la '
            'contrôler.'
        ),
        'tone': (
            'Immense et mécanisé, engins de siège et canonnières en '
            'guerre ouverte.'
        ),
        'objectives': (
            'Tuez le général ennemi. Prenez les quais, l\'atelier et '
            'le hangar pour percer la forteresse ennemie.'
        ),
        'landmarks': (
            'Lieux clés : la forteresse de l\'Alliance à l\'ouest, la '
            'forteresse de la Horde à l\'est, les Quais, l\'Atelier, le '
            'Hangar et ses canonnières, la Carrière et la Raffinerie. '
            'Engins de siège, canons et murs de fer. Ne mentionnez '
            'AUCUN lieu d\'un autre champ de bataille.'
        ),
    },
}

DUNGEON_FLAVOR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Donjon d'Ombrecroc : Un donjon hanté sur une falaise au-dessus de Bois-du-Bûcher, au sud de la forêt des Pins-Argentés, autrefois le siège du baron Silverlaine. Pendant la Troisième Guerre, l'archimage Arugal invoqua les worgens contre le Fléau, mais ils se retournèrent contre tous ; rendu fou par la culpabilité, il les adopta comme ses enfants et fit du donjon son repaire. Des worgens rôdent dans les cours et les tours, des serviteurs morts-vivants arpentent les salles, et l'on dit que le fantôme vengeur du baron s'y attarde. Pierre froide, torches vacillantes et hurlements de loups emplissent la nuit.""",

    34: """La Prison : Une prison de haute sécurité cachée sous le quartier des canaux de Hurlevent, où sont enfermés petits escrocs, agitateurs politiques, meurtriers et certains des criminels les plus dangereux du pays, beaucoup d'entre eux défias. Une révolte récente a chassé les gardes, et les détenus errent désormais librement dans les cellules et les couloirs sous la conduite du rusé criminel qui mena le soulèvement. L'air est humide et confiné, l'eau goutte de la pierre et les cris des prisonniers résonnent dans les couloirs étroits.""",

    36: """Les Mortemines : Une vieille mine d'or sous le village fantôme de Ruisseau-de-la-Lune, en Marche de l'Ouest, la forteresse cachée de la Confrérie défias, des hors-la-loi nés des tailleurs de pierre impayés de Hurlevent. Mineurs défias, ingénieurs gobelins et ogres travaillent dans les galeries, et les passages débouchent sur une vaste crique cachée où la Confrérie construit un grand navire de guerre, pièce maîtresse de ses plans contre le royaume. Les galeries sont sombres et étroites, sentent la poussière, l'huile et la poudre, et partout craquent les étais et cliquettent les machines.""",

    43: """Cavernes des Lamentations : Un réseau de grottes sous le cœur des Tarides, nommé d'après les longs gémissements plaintifs des fissures de vapeur qui s'en échappent. Le druide elfe de la nuit Naralex espérait se servir de leurs sources et du pouvoir du Rêve d'émeraude pour faire reverdir les Tarides, mais son rêve devint un cauchemar. Les eaux devinrent fétides, les bêtes qui y vivaient se changèrent en prédateurs féroces et ses propres disciples devinrent les Druides du Croc. On dit que Naralex repose quelque part dans les profondeurs, prisonnier de son cauchemar éveillé.""",

    47: """Kraal de Tranchebauge : Le grand terrier d'épines des huran à la limite sud des Tarides, né des lianes qui poussèrent là où coula le sang du demi-dieu Agamaggan pendant la guerre des Anciens. Les huran le vénèrent comme la patrie de leur peuple. La vieille mégère Charlga Trancheflanc y règne, ses chamans attaquent les tribus rivales et les villages de la Horde, et certains murmurent qu'elle traite avec des émissaires du Fléau. D'énormes lianes épineuses se referment au-dessus des têtes, et les galeries sont boueuses, étroites et pleines de sangliers.""",

    48: """Profondeurs de Brassenoire : Jadis un temple glorieux de la déesse lunaire Élune sur la grève de Zoram, en Orneval, brisé par la Fracture et englouti sous les vagues de la mer Voilée. Ses grottes inondées et ses ruines brisées mènent profondément vers un sanctuaire des Dieux très anciens. Nagas et satyres sondent ses secrets, le culte du Marteau du crépuscule travaille à leurs côtés, et l'on dit que l'antique bête Aku'mai, favorite des Dieux très anciens, demeure dans les profondeurs. Eau froide, pierre glissante et lueur faible et inquiétante emplissent les lieux.""",

    70: """Uldaman : Un ancien caveau des titans enfoui profondément dans le nord des Terres ingrates, récemment percé par des fouilles naines qui libérèrent les troggs, les premières créations ratées des titans. Les légendes affirment que le caveau consigne les secrets de la création des nains sur les fabuleux Disques de Norgannon. Les nains Sombrefer y creusent pour leur maître Ragnaros, tandis que des gardiens de pierre vivante écrasent tout intrus. De vastes salles de pierre sculptée, des passages effondrés et de silencieuses machines titanesques reposent sous le poids des montagnes.""",

    90: """Gnomeregan : La merveille technologique qui fut la capitale des gnomes sous les neiges de Dun Morogh, perdue quand des troggs envahirent la ville depuis les profondeurs et que les gnomes, en désespoir de cause, libérèrent les déchets radioactifs de la cité. Irradiés mais invaincus, les troggs errent encore dans ses salles, et les gnomes survivants ont fui à Forgefer. Le traître mekgénieur Thermojoncteur règne sur les ruines en techno-seigneur fou. Machines cliquetantes, tuyaux qui fuient, boue toxique et sentinelles d'alarme emplissent les couloirs tortueux.""",

    109: """Le temple d'Atal'Hakkar : Le temple élevé par les prêtres atal'ai exilés dans le marais des Chagrins pour préparer le retour du dieu du sang Hakkar l'Écorcheur d'âmes. L'Aspect dragon Ysera l'engloutit sous le marais, et ses dragons verts gardent toujours les ruines noyées, certains déjà corrompus. Mais des Atal'ai fanatiques ont survécu à l'intérieur et servent toujours Hakkar. Salles inondées, pierre croulante et idoles trolles gisent dans une eau trouble, et l'air est lourd de pourriture et d'ancienne magie du sang.""",

    129: """Souilles de Tranchebauge : Les tertres funéraires ancestraux et capitale traditionnelle des huran, un vaste labyrinthe d'épines à la limite sud des Tarides, né des mêmes puissantes lianes que le kraal de Tranchebauge. Une ombre menaçante s'est abattue sur les lieux : on dit que le Fléau s'est emparé des souilles, qu'une liche commande les grands prêtres de la Tête-de-mort et que les morts des tertres se relèvent. Une brume froide s'accroche aux ronces, et la puanteur de la mort se mêle à la boue et aux épines.""",

    189: """Monastère Écarlate : Jadis un fier centre d'étude du clergé de Lordaeron au nord-est des clairières de Tirisfal, aujourd'hui une forteresse de la fanatique Croisade écarlate, qui ne se fie à personne qui ne soit pas humain et voit en chaque étranger un porteur de la peste. Son cimetière, sa bibliothèque, son armurerie et sa cathédrale sont tenus par des guerriers zélés sous le commandant écarlate Mograine, tandis que la grande inquisitrice Blanchetête, dont on dit qu'elle relève les morts pour les renvoyer au combat, est la véritable maîtresse du monastère. Bannières rouges, encens et cris des fidèles emplissent ses salles.""",

    209: """Zul'Farrak : La cité fortifiée des trolls Furie-des-sables dans les déserts du nord-ouest de Tanaris, pierre brûlée par le soleil et pyramides qui surgissent des dunes. Ses guerriers, prêtres et sorciers-docteurs la défendent farouchement et relèvent les morts pour la protéger. Les légendes parlent d'une puissante épée trolle brisée en deux qui se trouverait quelque part à l'intérieur, de mercenaires égarés dans la ville et jamais revus, et d'une créature ancienne endormie dans le bassin sacré en son cœur. Chaleur, sable et scorpides sont partout.""",

    229: """Pic Rochenoire : La forteresse taillée dans les hauteurs du mont Rochenoire par le maître maçon Sombrefer Franclorn Forgebrise, symbole de leur puissance. La Horde orque en fit sa capitale pendant la Deuxième Guerre. Elle est aujourd'hui tenue par la Horde noire du chef de guerre Rend Main-Noire, avec orcs, ogres et trolls, et par le dragon noir Nefarian et ses draconiens, qui règnent sur le haut du pic et font la guerre à Ragnaros dans les profondeurs. Lave, chaînes, portes de fer et drakes tournoyant dans la fumée en font une forteresse immense et mortelle.""",

    230: """Profondeurs de Rochenoire : L'ancienne grande capitale des nains Sombrefer, un labyrinthe volcanique au plus profond du mont Rochenoire, aujourd'hui gouvernée par l'empereur Dagran Thaurissan comme siège du pouvoir de Ragnaros, le seigneur du Feu. Les forges flamboient, la lave coule dans les salles, des golems de pierre vivante sont construits pour l'armée du seigneur du Feu, et une arène, une prison et une taverne s'ouvrent parmi les vastes salles. Soldats Sombrefer, élémentaires de feu et captifs réduits en esclavage peuplent la cité. La chaleur est écrasante, et le martèlement ne cesse jamais.""",

    269: """Le Noir Marécage : Un voyage à travers les grottes du Temps vers les marais du Noir Marécage, le jour où Medivh, le dernier Gardien de Tirisfal, ouvrit la Porte des ténèbres et laissa la Horde orque entrer en Azeroth. Le Vol de bronze garde ce moment, car le Vol infini envoie vague après vague à travers des failles temporelles pour tuer Medivh et changer l'histoire. Brouillard, eau stagnante et arbres tordus entourent le portail qui grandit, et le temps lui-même semble trembler.""",

    289: """Scholomance : Une école de nécromancie dans les cryptes sous Caer Darrow, un vieux château sur une île du lac Darrowmere. La noble famille Barov céda le château au Culte des damnés de Kel'Thuzad en échange d'une immortalité promise, et le culte fit de ses cryptes une académie qui forma ceux qui répandirent la peste. Les Barov hantent désormais ses salles en morts-vivants, la liche Ras Murmegivre la garde pour le Fléau et le nécromancien sombre maître Gandling la dirige en directeur. Bougies, ossements et grimoires interdits emplissent ses salles de classe.""",

    329: """Stratholme : La deuxième cité de Lordaeron, où fut fondé l'ordre de la Main d'argent et où le prince Arthas massacra la population atteinte par la peste. C'est aujourd'hui la capitale du Fléau en Lordaeron, et elle brûle encore. La ville est divisée entre la Croisade écarlate, qui tient le bastion Écarlate sous le grand croisé Dathrohan, et le Fléau, dont le chevalier de la mort baron Vaillefendre règne sur les ziggourats des quartiers est. Les cendres flottent sur des rues détruites, et les places sont pleines de morts.""",

    349: """Maraudon : Un lieu saint des centaures dans la vallée des Lances, en Désolace, le tombeau de Zaetar, fils de Cénarius, et la demeure de la princesse élémentaire de terre Theradras, mère de la race des centaures. Leurs enfants maudits tuèrent leur père, et Theradras garde son corps dans ses cavernes de cristal. La bénédiction de la nature fit de sa dernière demeure un paradis souterrain de fleurs et de bassins, tandis que des grottes tachées de pourpre, des élémentaires de terre et les esprits des khans centaures emplissent le labyrinthe. Les centaures maraudine le gardent farouchement.""",

    389: """Gouffre de Ragefeu : Un réseau de grottes volcaniques sous Orgrimmar, plein de lave et de feu. Des troggs sont remontés des profondeurs et repoussent toute tentative de paix, et un culte fidèle à la Lame ardente et au Conseil des ombres s'est réfugié dans le gouffre, complotant pour détruire tout ce que la Horde a bâti en Durotar. Les tunnels sont brûlants, la lumière est rouge et le sifflement de la roche en fusion ne s'arrête jamais, un danger tapi juste sous la capitale.""",

    429: """Hache-Tripes : Les ruines d'Eldre'Thalas, une cité de Bien-nés bâtie il y a douze mille ans au nord de Feralas pour garder les secrets arcaniques les plus précieux de la reine Azshara. Ravagée par la Fracture, une grande partie de la cité est encore debout. Les ogres Gordunni règnent sur le quartier nord, satyres et anciens corrompus hantent les jardins de l'est, et les derniers Bien-nés, les secrets Shen'dralar, tiennent les salles de l'ouest et leur grande bibliothèque, gardant les maux anciens enfermés dans les caveaux. Marbre brisé, arches elfiques et cours envahies emplissent la cité.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Repaire d'Onyxia : Une grotte volcanique dans le Bourbier aux wyrms, au sud du marécage d'Âprefange, le repaire d'Onyxia, mère du Vol noir et fille d'Aile-de-mort. Un tunnel étroit de roche brûlée descend, au milieu des dragonnets et des draconiens, vers une salle immense jonchée d'os et de couvées. Le sol de la grotte n'est qu'une fine croûte au-dessus de la roche en fusion, et l'air est chargé de fumée et de soufre. Onyxia elle-même emplit la salle de feu et d'ombre, et rares sont ceux qui entrent dans son repaire et en reviennent.""",

    309: """Zul'Gurub : L'antique capitale de l'empire gurubashi au nord-est de la vallée de Strangleronce, une immense cité trolle de temples et de ziggourats envahie par la jungle. Il y a plus de mille ans, les Atal'ai invoquèrent Hakkar l'Écorcheur d'âmes et brisèrent l'empire ; le dieu du sang est désormais revenu au cœur des ruines. Les grands prêtres envoyés par les tribus pour l'arrêter, champions de la Chauve-souris, de la Panthère, du Tigre, de l'Araignée et du Serpent, sont tombés sous son emprise et nourrissent sa puissance. Rituels sanglants, tambours et cris des bêtes de la jungle emplissent l'air.""",

    409: """Cœur du Magma : Le cœur brûlant du mont Rochenoire, tout au fond des profondeurs, là où Thaurissan invoqua Ragnaros, le seigneur du Feu, en ce monde. Le seigneur du Feu demeure ici dans un lac de feu qui sert de faille vers le plan élémentaire, et ses serviteurs, les attise-flammes et leur majordome Executus, commandent les élémentaires et les nains Sombrefer asservis. Des rivières de lave coulent entre des plates-formes d'obsidienne, chiens du Magma et géants en fusion errent dans les grottes, et la chaleur est accablante.""",

    469: """Repaire de l'Aile noire : Le repaire du dragon noir Nefarian au sommet du pic Rochenoire, où il complote pour écraser Ragnaros et s'emparer de tout le mont Rochenoire. Comme son père Aile-de-mort, il élève une nouvelle armée en expérimentant sur le sang de tous les Vols draconiques pour créer des guerriers invincibles. Laboratoires, salles de suppression et couvoirs de drakes emplissent le repaire, gardés par des draconiens noirs et ses créations les plus terribles. Chaleur, fumée et puanteur de sang de dragon flottent dans les salles.""",

    509: """Ruines d'Ahn'Qiraj : Les ruines extérieures de la cité d'Ahn'Qiraj derrière le mur du Scarabée, au sud de Silithus, où les qiraji et leurs silithides furent enfermés il y a mille ans à la fin de la guerre des Sables changeants. Les portes sont rouvertes, et les armées de l'Alliance et de la Horde ont repoussé les qiraji dans les ruines. Des structures de pierre colossales et des piliers surgissent du sable parmi les ruches silithides, et les généraux qiraji et leurs essaims défendent farouchement les ruines.""",

    531: """Temple d'Ahn'Qiraj : Le grand temple au cœur d'Ahn'Qiraj, au sud de Silithus, forteresse des empereurs qiraji et de leurs essaims silithides. De sombres murmures disent qu'en dessous, un Dieu très ancien s'agite dans son antre et reprend des forces après des millénaires, et que les dragons qui se sacrifièrent pour l'emprisonner gisent à l'intérieur, affaiblis ou asservis. De vastes salles insectoïdes, des ruches palpitantes et des chambres tordues mènent toujours plus profond, et une terreur étrangère et oppressante grandit à chaque pas.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Les Salles brisées : L'aile la plus profonde de la citadelle des Flammes infernales, sur la péninsule du même nom, terrain d'entraînement et caserne des gangr'orcs. Ici, le chef de guerre Kargath Lamepoing commande la Horde gangrenée, des démonistes du Conseil des ombres pratiquent leur magie noire, des gladiateurs combattent dans l'arène et des archers font pleuvoir le feu sur les couloirs étroits. Les salles sont brutales, exiguës et pleines du fracas des armes, chacune imprégnée de sang et d'énergie gangrenée.""",

    542: """La Fournaise du sang : Une aile de la citadelle des Flammes infernales où les gangr'orcs saignent le seigneur des abîmes Magtheridon emprisonné et se servent de son sang pour engendrer une nouvelle Horde gangrenée, imprégnée de puissance démoniaque. Cuves de sang corrompu, cellules de prisonniers et démonistes enchaînés bordent les salles de la fournaise. Les sorciers gangr'orcs canalisent l'énergie du démon captif en dessous, et l'air est épais de vapeurs gangrenées, de chaleur et de cris.""",

    543: """Remparts des Flammes infernales : Les murailles et les tours fortifiées de la citadelle des Flammes infernales, première ligne de défense des gangr'orcs. Des gangr'orcs patrouillent sur les remparts, leurs gardes-guetteurs commandent les murs, et un champion gangr'orc chevauche un dragon du Néant au-dessus des tours. Les remparts dominent la désolation rouge, la Porte des ténèbres et les forges de la Légion. Vent, feu gangrené et rugissements de drakes emplissent l'air.""",

    545: """Le caveau de la Vapeur : Le cœur du réservoir de Glissecroc, dans le marécage de Zangar, où les nagas de dame Vashj font tourner de grandes machines et pompes à vapeur qui drainent les eaux du marais. Guerriers nagas, sirènes et élémentaires d'eau gardent le caveau, et des Roués asservis peinent dans les salles. Tuyaux qui sifflent, turbines rugissantes et nuages de vapeur emplissent l'air, et les murs ruissellent de condensation. Le bourdonnement des machines ne cesse jamais.""",

    546: """La Basse-tourbière : Une aile du réservoir de Glissecroc, dans le marécage de Zangar, refuge de la dernière vie naturelle du marais que les nagas n'ont pas encore anéantie. Champignons géants, seigneurs des tourbières, chauves-souris des spores et bêtes affamées prospèrent dans ses grottes, tandis que les nagas défendent un temple où ils gardent leur dieu hydre Ghaz'an. Champignons luisants, eau trouble et air épais chargé de spores en font un lieu sauvage et indompté.""",

    547: """Les enclos aux esclaves : La première aile du réservoir de Glissecroc, dans le marécage de Zangar, où les nagas de dame Vashj tiennent des Roués et des seigneurs des tourbières réduits en esclavage pour travailler à leurs grandes pompes. Des maîtres d'esclaves nagas et leurs serviteurs patrouillent dans les enclos, tandis que les esclaves peinent dans les chaînes. Passerelles de bois, cages de fer et eau qui goutte emplissent les salles, et les cris des captifs résonnent au-dessus du réservoir.""",

    552: """L'Arcatraz : Un satellite du donjon de la Tempête, à Raz-de-Néant, où les naaru emprisonnèrent les créatures les plus dangereuses rencontrées lors de leurs voyages : démons, agents du Vol noir et même serviteurs des Dieux très anciens. Les elfes de sang de Kael'thas le gardent désormais, mais ils sont corruptibles, et les prisonniers s'évadent. Cellules de force chatoyante, couloirs de cristal et hurlements d'horreurs échappées emplissent la prison.""",

    553: """La Botanica : Un satellite du donjon de la Tempête, à Raz-de-Néant, où des savants elfes de sang fidèles à Kael'thas utilisent la technologie naaru volée pour expérimenter sur les plantes et les créatures de l'Outreterre, en quête de nouveaux pouvoirs. Des jardins d'une flore étrange poussent sous des dômes de cristal, mais les expériences ont échappé à tout contrôle, et des plantes mutantes et des tréants enragés emplissent désormais les salles. L'air est humide et chargé de pollen.""",

    554: """Le Méchanar : Un satellite du donjon de la Tempête, à Raz-de-Néant, transformé par Kael'thas en usine qui exploite la technologie naaru pour produire d'immenses quantités d'énergie, stockée dans des cellules de mana empilées en murs et en tas. Des elfes de sang sous les ordres de Pathaleon le Calculateur font tourner les machines, aidés par des démons de la Légion ardente. Moteurs bourdonnants, conduits arcaniques et créations cliquetantes emplissent les salles de cristal violet.""",

    555: """Labyrinthe des Ombres : L'aile la plus profonde d'Auchindoun, dans la forêt de Terokkar, où le Conseil des ombres invoqua un ancien élémentaire du son dont le rituel fit éclater la nécropole. Le Conseil y complote encore, luttant pour contenir et maîtriser l'entité qu'il a libérée, servi par des gangr'orcs et des démons. Longs couloirs, salles rituelles et écho constant et assourdissant emplissent le labyrinthe, et l'air lui-même tremble.""",

    556: """Les salles des Sethekk : Une aile d'Auchindoun, dans la forêt de Terokkar, tenue par les Sethekk, des arakkoa renégats qui ont rompu avec Skettis sous le fou roi-serre Ikiss. Ils croient que la destruction d'Auchindoun annonçait le retour de leur maître et le cherchent dans les ruines. Idoles de plumes, feux rituels et magie noire emplissent les antiques salles draeneï, et les cris des arakkoa y résonnent.""",

    557: """Tombes-mana : Une aile d'Auchindoun, dans la forêt de Terokkar, où des éthériens renégats menés par le prince-nexus Shaffar pillent les cryptes et siphonnent l'énergie arcanique des ruines. Des protections tiennent à l'écart leurs rivaux du Consortium. Énergie chatoyante, débris flottants et esprits sans repos des morts draeneï emplissent les tombes, et les salles bourdonnent de puissance volée.""",

    558: """Cryptes Auchenaï : Une aile d'Auchindoun, dans la forêt de Terokkar, les cryptes funéraires des draeneï, où les prêtres auchenaï veillaient sur leurs morts honorés. Depuis que la nécropole a été brisée, les cryptes sont tombées dans les ténèbres : des démons de la Légion ardente y récoltent des âmes, et les morts draeneï se relèvent en esprits sans repos et en morts-vivants. Pierre froide, lumière sacrée éteinte et murmures des morts emplissent les salles.""",

    560: """Contreforts de Hautebrande d'antan : Un voyage à travers les grottes du Temps vers Hautebrande, des années avant la Troisième Guerre, quand le jeune orc Thrall était l'esclave d'Aedelas Blackmoore à Fort-de-Durn et que les orcs dépérissaient dans les camps d'internement. Le Vol de bronze garde le moment de son évasion, car le Vol infini cherche à le changer. Collines vertes, fermes paisibles, la ville d'Austrivage et les murailles de pierre de Fort-de-Durn apparaissent tels qu'ils étaient jadis.""",

    568: """Zul'Aman : La cité-temple des trolls des forêts Amani, à l'est des Terres fantômes, dernier vestige de l'empire qui s'étendait autrefois sur Lordaeron avant que les humains et les hauts-elfes ne le brisent ensemble. Le seigneur de guerre Zul'jin, qui n'a jamais pardonné aux elfes, a rassemblé ses trolls et, avec l'aide du Seigneur des maléfices, scellé la puissance des dieux animaux amani, l'ours, l'aigle, le lynx et le faucon-dragon, dans ses plus puissants champions. Ziggourats à degrés, totems vaudous et tambours emplissent la forêt sombre et primitive.""",

    585: """Terrasse des Magistères : Un élégant complexe elfe de sang à l'angle nord-est de l'île de Quel'Danas, doté d'un observatoire tourné vers le Puits de soleil. Il est tenu par des fidèles de Kael'thas Haut-Soleil, qui s'y serait retiré, et les salles bourdonnent de puissance arcanique volée et de l'énergie des cristaux de mana. Flèches dorées, jardins et dômes d'observatoire emplissent la terrasse, belle et dangereuse.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan : La tour d'ivoire de Medivh, le dernier Gardien de Tirisfal, dans le défilé de Deuillevent, dressée sur un nœud de lignes telluriques où la réalité est mince. Après la mort de Medivh, une terrible malédiction s'abattit sur la tour et les terres alentour. Elle s'est désormais réveillée : une présence maléfique s'en est emparée, ses salles grouillent d'esprits et de démons, des nobles spectraux de Sombre-Comté revivent un festin sans fin, et des échos du passé se jouent dans ses bibliothèques, son opéra et sa ménagerie. Grandeur poussiéreuse et magie froide emplissent chaque pièce.""",

    534: """Sommet d'Hyjal : Un voyage à travers les grottes du Temps vers les pentes du mont Hyjal à la fin de la Troisième Guerre, quand humains, orcs et elfes de la nuit se dressèrent ensemble contre la Légion ardente et le Fléau. Le seigneur démon Archimonde gravit la montagne pour drainer la puissance de l'Arbre-Monde Nordrassil. Le Vol de bronze préserve la bataille telle qu'elle fut, tandis que les défenseurs se replient de camp en camp. Forêts anciennes, le grand arbre au-dessus et les armées enflammées de la Légion en contrebas.""",

    544: """Le repaire de Magtheridon : Une salle profonde sous la citadelle des Flammes infernales où le seigneur des abîmes Magtheridon, ancien maître de l'Outreterre, gît enchaîné depuis qu'Illidan l'a vaincu. Son sang est récolté pour engendrer la Horde gangrenée, et des canaliseurs des Flammes infernales maintiennent ses liens. La caverne tremble de sa rage, le plafond se fissure sous sa puissance, et le feu gangrené vacille autour de sa cage. C'est un lieu de fureur démoniaque à l'état brut.""",

    548: """Caverne du sanctuaire du Serpent : Le repaire de dame Vashj, la sorcière naga au service d'Illidan, au plus profond du réservoir de Glissecroc, dans le marécage de Zangar, où s'accumulent les eaux pompées du marais. Ses lieutenants les plus puissants, d'un élémentaire d'eau corrompu à une créature tapie dans les profondeurs, gardent le sanctuaire, et les eaux grouillent de nagas. De vastes cavernes inondées, des piliers de corail et des bassins chatoyants baignent dans une étrange lueur bleue.""",

    550: """Donjon de la Tempête - L'Œil : Le palais intérieur du donjon de la Tempête, la forteresse naaru de Raz-de-Néant, prise par les elfes de sang de Kael'thas Haut-Soleil, le Roi-soleil, qui y règne avec ses phénix et ses conseillers les plus puissants. Salles de cristal, machineries arcaniques et plates-formes flottantes brillent d'une énergie naaru volée, et un naaru captif est drainé de sa puissance. L'Œil domine les tempêtes tourbillonnantes du Néant, magnifique et froid.""",

    564: """Le Temple noir : Autrefois le temple de Karabor, lieu le plus sacré des draeneï et refuge du prophète Velen, conquis par Gul'dan pour en faire le quartier général du Conseil des ombres, puis tenu par la Légion ardente. C'est aujourd'hui la citadelle d'Illidan Hurlorage, autoproclamé seigneur de l'Outreterre, gardée par ses Illidari : nagas, elfes de sang, Roués, démons et gangr'orcs. Le feu gangrené brûle dans ses sanctuaires, l'ombre emplit ses salles, et les cris d'âmes tourmentées montent de ses profondeurs.""",

    565: """Repaire de Gruul : Un repaire caverneux au nord des Tranchantes, demeure de Gruul le Tue-dragon, impitoyable seigneur des gronns, et de son fils, le haut roi ogre Maulgar, qui règnent sur les ogres des montagnes. Les ossements de dragons tués pendent aux parois, et le sol tremble sous les pas des géants. Bannières ogres grossières, trophées et pierre brute emplissent l'immense grotte, un lieu de force brute et de violence.""",

    580: """Plateau du Puits de soleil : Le lieu le plus sacré des elfes sur l'île de Quel'Danas, où le Puits de soleil, la source de puissance qui nourrissait Quel'Thalas, se dresse au cœur de cours et de salles gracieuses. Récemment, la Légion ardente a voulu en faire une porte pour le seigneur érédar Kil'jaeden, et les serviteurs de la Légion, démons et elfes de sang qui leur sont fidèles, tiennent le plateau. Flèches dorées, naaru captifs et énergie gangrenée entourent le puits profané.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Donjon d'Utgarde : La grande forteresse vrykule sur les falaises dominant le lac Cauldros, dans le Fjord Hurlant, bâtie dans le fjord avec des cascades qui dévalent de chaque côté, foyer du clan Écorche-dragon. Longtemps silencieuse, elle s'est réveillée, et ses guerriers attaquent toutes les colonies voisines, au service, dit-on, du roi-liche, qui relève les plus dignes d'entre eux d'outre-tombe. Proto-drakes, worgs et morts-vivants servent les vrykuls, et plus on monte dans le donjon, plus ses habitants sont puissants.""",

    575: """Cime d'Utgarde : Les plus hauts niveaux du donjon d'Utgarde, dans le Fjord Hurlant, où vivent les plus puissants des vrykuls et où le roi Ymiron tient son trône, avide de prouver que son peuple mérite la faveur du roi-liche. Grandes salles de pierre et de bois, crânes sculptés et trophées d'ennemis tombés emplissent la cime, et des proto-drakes tournoient au-dessus des hauteurs glacées du fjord.""",

    576: """Le Nexus : L'antique demeure du Vol bleu sous l'île de Frimarra, au large de la toundra Boréenne, une forteresse arcanique de glace et de cristaux flottants où l'Aspect de la magie, Malygos, mène sa guerre contre tous les lanceurs de sorts mortels. Les dragons bleus et leurs serviteurs gardent ses salles gelées, et les ennemis capturés sont enfermés dans des prisons de glace. L'énergie arcanique crépite dans l'air, et la glace luit de magie.""",

    578: """L'Oculus : La grande tour d'anneaux flottants au-dessus du Nexus, sur Frimarra, où Malygos canalise les lignes telluriques d'Azeroth, détournant la magie du monde à travers le Nexus vers le Néant distordu. Le Kirin Tor et le Vol rouge luttent pour l'arrêter. Les anneaux dérivent haut dans le ciel, crépitant de puissance arcanique, et seuls des drakes permettent de passer de l'un à l'autre. La magie brute déchire l'air, et des failles lointaines lacèrent la réalité.""",

    595: """L'Épuration de Stratholme : Un voyage à travers les grottes du Temps vers le jour où la peste atteignit Stratholme dans du grain contaminé et où le prince Arthas, refusant de laisser ses habitants se relever en morts-vivants, ordonna la purge de la ville. Le seigneur de l'effroi Mal'Ganis veille sur la cité mourante, et le Vol infini cherche à altérer ce moment. Les rues sont pleines de citoyens effrayés, de maisons en flammes et des premiers morts qui marchent, un jour qui marqua le début de la chute d'Arthas.""",

    599: """Les salles de Pierre : Une aile de la cité titanesque d'Ulduar, dans les pics Foudroyés, abritant le Tribunal des âges, l'immense archive de pierre de l'histoire des titans, et la Forge des volontés. Des nains de fer et des géants de pierre, corrompus par le gardien déchu Loken, tiennent désormais ses salles et gardent leurs secrets. Statues imposantes, bas-reliefs sculptés et machines titanesques emplissent les vastes salles de pierre, silencieuses hormis le grondement des machines.""",

    600: """Donjon de Drak'Tharon : Une vieille forteresse des trolls des glaces aux flèches et aux murs sculptés, à la frontière des Grisonnes et de Zul'Drak, prise par le Fléau, qui relève les Drakkari tombés pour combattre leur propre empire. Son ancien chef, le prophète Tharon'ja, a été changé en une monstrueuse forme morte-vivante, et des trolls morts-vivants se déversent de ses portes dans les collines. Ossements, bannières du Fléau et sculptures trolles gelées emplissent la forteresse.""",

    601: """Azjol-Nérub : Le royaume Supérieur des nérubiens sous la Désolation des dragons, un grandiose royaume souterrain d'érudition et d'art, envahi par le Fléau lors de la guerre de l'Araignée. Des nérubiens morts-vivants patrouillent désormais dans ses salles polies, gardant des couvées d'où naîtront de nouveaux guerriers du Fléau, et leur roi déchu Anub'arak sert le roi-liche. Toiles, fresques sculptées et champignons luminescents emplissent les vastes cavernes, tandis que des nérubiens vivants mènent une guerre cachée et perdue.""",

    602: """Les salles de Foudre : L'aile est de la cité titanesque d'Ulduar, dans les pics Foudroyés, où le gardien déchu Loken siège sur son trône et produit en masse des vrykuls de fer et des créations pour ses sombres desseins. Élémentaires de tempête, géants de fer et gardiens forgés par la foudre le servent, et de grandes forges et machines tonnent partout. Des éclairs crépitent à travers les vastes salles de pierre et de métal.""",

    604: """Gundrak : La capitale des trolls des glaces Drakkari à Zul'Drak, une immense cité de murs épais, de hautes tours et de bâtiments à degrés enchevêtrés comme un nid. Désespérés face au Fléau, ses grands prophètes ont tué leurs propres dieux, les loas, et boivent leur sang pour en tirer du pouvoir, imprégnant les sanctuaires sacrés de la puissance des dieux tués. Des idoles de rhinocéros, de serpent et de mammouth se dressent dans les cours, et les tambours résonnent dans les rues à degrés.""",

    608: """Le fort Pourpre : La prison du Kirin Tor à Dalaran, dont les cellules protégées par la magie retiennent des prisonniers puissants et dangereux. Le Vol bleu de Malygos y a fait irruption par une grande fissure du toit et se déverse par des portails à l'intérieur, éprouvant les défenses de la prison et libérant ses détenus. Les protections arcaniques vacillent, la pierre violette luit, et les gardes du Kirin Tor luttent pour tenir la ligne.""",

    619: """Ahn'kahet : L'Ancien royaume, les profondeurs les plus reculées d'Azjol-Nérub sous la Désolation des dragons, une immense cité souterraine de l'antique empire nérubien. Des nérubiens du Fléau et les mystérieux Sans-visage la tiennent, ces derniers servant, dit-on, une puissance maléfique tapie sous le Norfendre, et le Marteau du crépuscule s'agite parmi eux. Forêts de champignons, grandes salles drapées de toiles et ténèbres oppressantes emplissent les profondeurs.""",

    632: """La Forge des Âmes : La première des Salles gelées de la citadelle de la Couronne de glace, une immense usine où l'on construit des broyeurs d'âmes, les plus récentes créations immondes du roi-liche. Des âmes tourmentées sont liées aux machines parmi des piliers de saronite et des chaînes spectrales. L'air est lourd de désespoir et des gémissements des morts.""",

    650: """L'épreuve du champion : Le terrain de tournoi de la Croisade d'argent sous le Colisée d'argent, dans la Couronne de glace, où les champions de l'Alliance et de la Horde joutent et s'affrontent en duel pour prouver leur valeur dans la guerre contre le roi-liche. Montures, lances, bannières et clameur de la foule emplissent l'arène, festive et fière, même si le Fléau n'est jamais loin.""",

    658: """Fosse de Saron : La grande mine de saronite sous la citadelle de la Couronne de glace, où le Fléau force des prisonniers de l'Alliance et de la Horde à extraire le minerai de ses forteresses sous le fouet du seigneur du Fléau Tyrannus. Des veines de saronite palpitent dans les parois, des esclaves peinent dans les chaînes et les morts sont relevés pour continuer à travailler. Le froid, l'obscurité et les claquements de fouet emplissent la fosse.""",

    668: """Salles des Reflets : Les appartements privés du roi-liche dans la citadelle de la Couronne de glace, le seul lieu où il baisse sa garde, une réplique sombre et déformée de la salle du trône de Lordaeron. Deuillelame, la lame runique du roi-liche, attend ici, et les esprits prisonniers de l'épée hantent les salles. Glace, silence et souvenirs du passé emplissent les appartements.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas : Une nécropole du Fléau flottant au-dessus de la Désolation des dragons, autrefois une ziggourat nérubienne envahie par le Fléau et soulevée dans le ciel par la magie noire du roi-liche. C'est le siège de l'archiliche Kel'Thuzad, qui l'a ramenée au Norfendre pour assiéger Hivernale. Ses quatre quartiers abritent des horreurs de toutes sortes : seigneurs des cryptes arachnides, laboratoires de peste et abominations, légions de chevaliers de la mort et créations de chair cousue. Vase verte, chair pourrissante et froid de la tombe emplissent ses salles.""",

    603: """Ulduar : Le plus grand complexe titan d'Azeroth, parfaitement préservé dans les neiges des pics Foudroyés, caché derrière la roche et la glace, un dédale de tunnels, d'escaliers et de balcons taillés dans une immense caverne. Ce fut la demeure des gardiens des titans et de leurs machines de création, mais on murmure qu'un grand mal se cache derrière sa chute, et ses gardiens corrompus se retournent contre tout intrus. Statues colossales, machines titanesques et observatoires étoilés emplissent ses salles.""",

    615: """Le sanctum Obsidien : La salle du Vol noir sous le temple du Repos du ver, dans la Désolation des dragons, partie de la salle des Aspects, où Sartharion le Gardien d'onyx garde une couvée d'œufs de dragons du crépuscule. Trois drakes du crépuscule veillent sur leurs propres îles parmi les rivières de lave entre des plates-formes d'obsidienne. La salle rougeoie d'orange et de rouge, et la chaleur fait trembler l'air.""",

    616: """L'Œil de l'éternité : Le domaine personnel de l'Aspect bleu Malygos, très haut au-dessus du Nexus sur Frimarra, d'où il mène sa guerre pour reprendre le contrôle des énergies arcaniques d'Azeroth. C'est une immense plate-forme flottant dans un vide sans fin d'énergie arcanique tourbillonnante et d'étoiles, où coule la magie du monde. Une puissance brute emplit l'air.""",

    624: """Caveau d'Archavon : Un caveau titan sous la forteresse de Joug-d'hiver, abritant des reliques d'une puissance inouïe sous la garde d'anciens gardiens de pierre qui détestent tout intrus. Ses salles ne s'ouvrent qu'à ceux qui tiennent la forteresse au-dessus. Pierre sculptée, machines titanesques et silence inquiétant emplissent le caveau.""",

    631: """Citadelle de la Couronne de glace : La forteresse du roi-liche, qui s'élève de la glace noire de la Couronne de glace, une cathédrale de lames et de flèches de saronite autour du Trône de glace. Ses salles grouillent des serviteurs les plus fidèles et les plus immondes du Fléau : chevaliers de la mort, cultistes, abominations et wyrms de givre. La Flèche inférieure, la Pesterie, la salle Cramoisie et les salles de l'Aile de givre mènent au trône. Le Verdict des cendres mène l'assaut, et le froid transperce jusqu'aux os.""",

    649: """L'épreuve du croisé : Le grand Colisée d'argent dans la Couronne de glace, bâti par la Croisade d'argent pour éprouver les champions dignes de l'assaut final contre le roi-liche. Les bannières de l'Alliance et de la Horde flottent au-dessus de tribunes en liesse, et de redoutables bêtes et champions sont amenés dans l'arène sous les yeux du généralissime Tirion Fordring. Faste et spectacle se déploient aux portes mêmes du roi-liche, et la vieille rivalité des deux factions brûle dans les tribunes.""",

    724: """Le sanctum Rubis : Le sanctuaire du Vol rouge sous le temple du Repos du ver, dans la Désolation des dragons, partie de la salle des Aspects, un refuge paisible d'œufs de dragons rouges, de lumière chaude et de verdure. Ses gardiens se sont tus et les gardes du portail ont été tués ; une force obscure a pénétré dans le sanctum, et des dragons du crépuscule menacent désormais les œufs du Vol rouge.""",

    # -------------------------------------------------------------------------
    # Arenas
    # -------------------------------------------------------------------------
    559: """Arène de Nagrand : L'Anneau des épreuves, dans les prairies de Nagrand, un antique lieu d'épreuves des orcs bâti dans le style de l'ancien empire ogre. Des gladiateurs de toutes les races s'y affrontent pour la gloire. Un cercle de piliers de pierre érodés se dresse à ciel ouvert, le vent balaie l'herbe et les spectateurs regardent depuis les collines.""",

    562: """Arène des Tranchantes : Le Cercle du sang, dans les Tranchantes, une arène bâtie par les ogres où des gladiateurs combattent pour la gloire devant une foule rugissante. Un pont de bois enjambe une fosse en son centre, cordes et piliers traversent l'anneau et des pics déchiquetés se dressent tout autour. Bois grossier, ossements et bannières lui donnent un air brutal et sauvage.""",

    572: """Ruines de Lordaeron : Une arène au milieu des ruines brisées de la capitale de Lordaeron, dans les clairières de Tirisfal, au-dessus de Fossoyeuse, où le grand palais se dresse encore comme un triste rappel de la chute de la ville. Murs brisés, statues renversées et tombeau en ruine entourent le terrain de combat, et le souvenir de la fin tragique du royaume plane sur les pierres.""",

    617: """Égouts de Dalaran : Une arène cachée dans les Entrailles, les égouts sous la cité flottante de Dalaran, où des gladiateurs combattent dans une fosse entourée de canaux et de tuyaux. Pierre humide, ruissellement de l'eau et murmure d'une foule rude emplissent l'arène, loin de la splendeur de la cité violette au-dessus.""",

    618: """L'arène des valeureux : La grande arène de la vallée de l'Honneur à Orgrimmar, où s'entraînent et combattent les gladiateurs de l'Anneau cramoisi. Des colonnes s'élèvent du sol, les spectateurs rugissent dans les gradins, et la chaleur de Durotar s'abat sur le sable. C'est un lieu d'honneur, de force et de spectacle.""",
}
