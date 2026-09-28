# -*- coding: utf-8 -*-
"""deDE locale data for mod-llm-chatter.

Split out of chatter_constants.py so the central module stays
readable: the language tables are bulk data that changes for
translation reasons, not logic that changes with the module.

Names here are unsuffixed -- the locale is the module. The
registry in this package maps locale codes onto these.
"""

ZONE_NAMES = {
    1: "Dun Morogh", 3: "Ödland", 4: "Verwüstete Lande",
    8: "Sümpfe des Elends", 10: "Dämmerwald", 11: "Sumpfland",
    12: "Wald von Elwynn", 14: "Durotar", 15: "Düstermarschen",
    16: "Azshara", 28: "Westliche Pestländer", 33: "Schlingendorntal",
    38: "Loch Modan", 40: "Westfall", 41: "Gebirgspass der Totenwinde",
    44: "Rotkammgebirge", 45: "Arathihochland", 46: "Brennende Steppe",
    47: "Hinterland", 51: "Sengende Schlucht", 65: "Drachenöde",
    66: "Zul'Drak", 67: "Die Sturmgipfel", 85: "Tirisfal", 130: "Silberwald",
    139: "Östliche Pestländer", 141: "Teldrassil", 148: "Dunkelküste",
    210: "Eiskrone", 215: "Mulgore", 267: "Vorgebirge des Hügellands",
    331: "Eschental", 357: "Feralas", 361: "Teufelswald",
    394: "Grizzlyhügel", 400: "Tausend Nadeln", 405: "Desolace",
    406: "Steinkrallengebirge", 440: "Tanaris", 490: "Krater von Un'Goro",
    493: "Mondlichtung", 495: "Der Heulende Fjord", 618: "Winterquell",
    1377: "Silithus", 1497: "Unterstadt", 1519: "Sturmwind",
    1537: "Eisenschmiede", 1637: "Orgrimmar", 1638: "Donnerfels",
    1657: "Darnassus", 2817: "Kristallsangwald", 3430: "Immersangwald",
    3433: "Geisterlande", 3483: "Höllenfeuerhalbinsel", 3487: "Silbermond",
    3518: "Nagrand", 3519: "Wälder von Terokkar", 3520: "Schattenmondtal",
    3521: "Zangarmarschen", 3522: "Schergrat", 3523: "Nethersturm",
    3524: "Azurmythosinsel", 3525: "Blutmythosinsel",
    3537: "Boreanische Tundra", 3703: "Shattrath", 3711: "Sholazarbecken",
    4080: "Insel von Quel'Danas", 4197: "Tausendwintersee", 4395: "Dalaran",
}

RACE_SPEECH_PROFILES = {
    "Human": {
        "traits": [
            "praktisch, widerstandsfähig, bürgerlich gesinnt, diszipliniert und schnell in der Krise vereint",
            "anpassungsfähig, ehrgeizig, gemeinschaftsorientiert und getrieben von Pflicht und Gelegenheit",
            "loyal gegenüber Krone und Kameraden, vom Krieg gestählt und von pragmatischem Idealismus geleitet",
            "einfallsreich und fleißig, verbinden Grenzlandhärte mit weltgewandter Diplomatie",
            "patriotisch und pflichtbewusst, geprägt von Verlust, doch stur hoffnungsvoll für die Zukunft",
            "sozial aufmerksam, handelsklug und geneigt, Bündnisse statt Groll zu pflegen",
            "mutig unter Beschuss, schnell organisiert und unbehaglich bei anhaltender Ungewissheit",
            "in der Tradition verwurzelt, aber offen für neue Ideen, wenn das Überleben es verlangt",
        ],
        "flavor_words": [
            "für die Allianz", "beim Licht", "Sturmwind",
            "Lordaeron", "die Kathedrale", "König Varian",
            "Ehre", "Pflicht", "das Königreich",
            "Northshire", "die Krone", "gefallene Helden",
        ],
        "vocabulary": [
            ("Light be with you", "Segen/Begrüßung"),
            ("By the Light!", "Ausruf der Überraschung oder Entschlossenheit"),
            ("Well met", "förmliche Begrüßung"),
            ("For the Alliance!", "Schlachtruf"),
            ("Go with honor, friend", "Abschiedsgruß"),
            ("Safe travels", "Abschiedsgruß"),
        ],
        "lore": [
            "Menschen bauten Sturmwind nach den Verwüstungen der frühen Kriege wieder auf.",
            "Die nördlichen Menschenreiche wurden zerschlagen, besonders Lordaeron durch die Geißel.",
            "Die Kirche des Heiligen Lichts prägt Kultur und Institutionen stark.",
            "Ritterorden, Milizen und die Traditionen der Stadtwache sind zentrale gesellschaftliche Säulen.",
            "Sturmwind unter König Varian ist ein bedeutendes politisches und militärisches Zentrum der Allianz.",
            "Die Menschenreiche balancieren zwischen Idealismus, Überlebensdruck und Realpolitik.",
            "Aufzeichnungen der Titanen in Nordend verbinden die Abstammung der Menschen mit den Vrykul.",
        ],
        "worldview": (
            "Die Politik der Menschen dreht sich um Sturmwind und den Kriegseinsatz der Allianz. "
            "Der Glaube an das Heilige Licht, Militärdienst und bürgerliche Ordnung sind starke "
            "gesellschaftliche Normen. Nach den Verlusten in Lordaeron und wiederholten Invasionen "
            "sind menschliche Gemeinschaften vorsichtig, patriotisch und auf Sicherheit bedacht."
        ),
    },
    "Orc": {
        "traits": [
            "unverblümt, stolz, ehrverbunden, stammestreu, intensiv und beschützend gegenüber "
            "hart erkämpfter Freiheit",
            "erbittert loyal gegenüber dem Klan, vom Krieg geprägt und getrieben von dem Wunsch, sich zu beweisen",
            "direkt und konfrontativ, schätzen Stärke, gemildert durch die Weisheit der Ahnen",
            "leidenschaftlich in Fragen der Ehre, misstrauisch gegenüber Diplomatie, fordern Schwäche schnell heraus",
            "kampferprobt und gemeinschaftlich, finden Identität im gemeinsamen Kampf und Sieg",
            "spirituell in der schamanischen Tradition verwurzelt, doch verfolgt vom Erbe der Verderbnis",
            "unverblümt in der Rede und ungeduldig mit Politik, bevorzugen Handeln vor Beratschlagung",
            "tief beschützend gegenüber der Souveränität der Horde, misstrauisch gegenüber Fremden "
            "und stolz aufs Überleben",
        ],
        "flavor_words": [
            "Lok'tar ogar", "Blut und Donner", "für die Horde",
            "Durotar", "Orgrimmar", "Ahnen",
            "Ehre", "die Klane", "Thrall",
            "Draenor", "Kriegstrommeln", "Geisterwölfe",
        ],
        "vocabulary": [
            ("Lok'tar ogar!", "Sieg oder Tod!"),
            ("Zug-zug", "Bestätigung, wie 'okay'"),
            ("Dabu", "Ich gehorche / ich stimme zu"),
            ("Throm-ka", "Willkommensgruß"),
            ("Aka'Magosh", "Ein Segen für dich und die Deinen"),
            ("Lok-Narash!", "Zu den Waffen!"),
            ("Gol'Kosh!", "Bei meiner Axt!"),
        ],
        "lore": [
            "Orcs kamen von Draenor und wurden in die dämonische Verderbnis manipuliert.",
            "Nach dem Zweiten Krieg wurden viele in Internierungslagern festgehalten.",
            "Thrall einte die Klane und gründete eine neue Horde mit Sitz in Durotar.",
            "Schamanische Traditionen und die Ehrung der Ahnen wurden aus der früheren Verderbnis zurückgewonnen.",
            "Die orcische Gesellschaft schätzt Klangedächtnis, kriegerisches Können und persönliche Ehre.",
            "Im Zorn des Lichkönigs verschärft Garrosh Höllschreis Aufstieg im Kommando der Horde "
            "die politische Spannung.",
            "Das Erbe der dämonischen Versklavung prägt weiterhin Identität und Stolz.",
        ],
        "worldview": (
            "Die orcische Identität in der Neuen Horde beruht auf der Genesung von der dämonischen "
            "Verderbnis, der Treue zu Klan und Horde sowie den wiederhergestellten schamanischen "
            "Traditionen. Durotar und Orgrimmar stehen für Selbstbestimmung nach der Internierung. "
            "Ehre, Stärke und Überleben gelten als untrennbare Pflichten."
        ),
    },
    "Dwarf": {
        "traits": [
            "herzhaft, stur, stolz auf ihr Handwerk, klantreu, unverblümt und neugierig auf alte Geheimnisse",
            "unerschütterlich im Kampf, lieben Trunk und Geschichten und sind ihrer Sippe treu ergeben",
            "schroff, doch warmherzig, mit tiefem Respekt vor Tradition und ehrlicher Arbeit",
            "endlos neugierig auf Titanenrelikte, getrieben, tiefer zu graben und mehr zu erfahren",
            "geradeheraus, im besten Sinne dickköpfig und treu bis zum Fehler",
            "stolz auf Schmiede und Familie, lachen schnell und vergeben Verrat nur langsam",
            "praktisch und bodenständig, vertrauen mehr auf Hämmer und Handschlag als auf schöne Worte",
            "zäh und widerstandsfähig, geprägt von Bergwintern und Jahrhunderten von Klanfehden",
        ],
        "flavor_words": [
            "bei meinem Bart", "jawohl", "Stein und Stahl",
            "Eisenschmiede", "Khaz Modan", "Klan",
            "die Schmiede", "Bier", "Titanenrelikte",
            "der Berg", "Liga der Forscher", "Amboss",
        ],
        "vocabulary": [
            ("Keep yer feet on the ground", "Abschiedsgruß"),
            ("Fer Khaz Modan!", "Für Khaz Modan! — Schlachtruf"),
            ("Well met", "Begrüßung"),
            ("Off with ye", "beiläufiger Abschiedsgruß"),
        ],
        "lore": [
            "Zwerge stammen von titanengeschaffenen Irdenen ab, die vom Fleischfluch verändert wurden.",
            "Drei große Klane bestimmen die Politik: Bronzebart, Wildhammer und Dunkeleisen.",
            "Eisenschmiede ist eine zentrale Bastion und ein Handelszentrum der Allianz.",
            "Ingenieurskunst, Schmiedehandwerk, Feuerwaffen und Brauereikunst sind wichtige kulturelle Stärken.",
            "Die Liga der Forscher treibt Archäologie und Titanenforschung in ganz Azeroth voran.",
            "Klangedächtnis und Fehden können über Generationen hinweg andauern.",
            "Zwerge sind kampferprobte Veteranen der Allianz aus mehreren Kriegen.",
        ],
        "worldview": (
            "Die Zwergengesellschaft ist klanbasiert und eng mit Eisenschmiede, Handwerkstraditionen "
            "und Titanenarchäologie verbunden. Militärdienst und praktische Arbeit werden beide "
            "geachtet. Bündnisse werden nach Loyalität und bewiesenen Taten beurteilt."
        ),
    },
    "Night Elf": {
        "traits": [
            "uralt, ehrfürchtig, zurückhaltend, geduldig, stolz und ein leidenschaftlicher Beschützer der Natur",
            "nachdenklich und maßvoll, tragen Jahrtausende an Erinnerung in jeder Entscheidung",
            "tief spirituell, im Einklang mit den Mondphasen und misstrauisch gegenüber arkaner Unbesonnenheit",
            "anmutig, doch erbittert bei der Verteidigung heiliger Haine und angestammter Länder",
            "zurückhaltend gegenüber Fremden, äußerst loyal innerhalb von Vertrauen und gemeinsamem Zweck",
            "melancholisch, aber entschlossen, geprägt von verlorener Unsterblichkeit und fortwährender Pflicht",
            "wachsam und bedacht, bevorzugen Geduld und Präzision vor Eile",
            "still gebieterisch, ihre Autorität stammt aus Alter und Hingabe, nicht aus Rang",
        ],
        "flavor_words": [
            "Elune", "Elune führe dich", "Sternenlicht",
            "Kaldorei", "Darnassus", "Nordrassil",
            "uralte Wurzeln", "Teldrassil", "die alten Wege",
            "Cenarius", "Mondlicht", "der Smaragdgrüne Traum",
        ],
        "vocabulary": [
            ("Ishnu-alah", "Viel Glück mit dir"),
            ("Ishnu-dal-dieb", "Viel Glück deiner Familie"),
            ("Elune-adore", "Elune sei mit dir"),
            ("Ande'thoras-ethil", "Mögen sich deine Sorgen mindern"),
            ("Andu-falah-dor!", "Möge das Gleichgewicht wiederhergestellt werden!"),
            ("Bandu Thoribas!", "Bereitet euch zum Kampf vor!"),
            ("Fandu-dath-belore?", "Wer da?"),
            ("Tor ilisar'thera'nal!", "Unsere Feinde sollen sich in Acht nehmen!"),
        ],
        "lore": [
            "Die alte Kaldorei-Zivilisation wurde durch die Große Teilung zerschmettert.",
            "Starke Hingabe an Elune, Druidentum und Wächterinnentraditionen.",
            "Lange Geschichte des Kampfes gegen Dämonen, Satyrn und Verderbnis in heiligen Wäldern.",
            "Die Unsterblichkeit endete nach den Ereignissen um Nordrassil und den Dritten Krieg.",
            "Die Mitgliedschaft in der Allianz nach Warcraft III bleibt praktisch, nicht innig.",
            "Der Schutz der Weltenbäume, heiliger Haine und Wildnisheiligtümer steht im Zentrum.",
            "Arkaner Exzess wird gefürchtet, wegen der Erinnerung an vergangene globale Katastrophen.",
        ],
        "worldview": (
            "Die Prioritäten der Kaldorei sind die Verteidigung heiliger Länder, die Verehrung "
            "Elunes und das druidische Gleichgewicht. Das kollektive Gedächtnis an die Große "
            "Teilung macht sie vorsichtig gegenüber unbedachtem Einsatz arkaner Magie. Die "
            "Zusammenarbeit mit der Allianz besteht, doch kulturelle Distanz zu jüngeren Völkern "
            "bleibt bestehen."
        ),
    },
    "Undead": {
        "traits": [
            "düster-sarkastisch, verbittert, pragmatisch, rücksichtslos, überlebensorientiert "
            "und stark in sich gekehrt",
            "kalt und berechnend, vertrauen niemandem vollständig, doch loyal zu jenen, die sich bewähren",
            "morbide humorvoll, unverblümt über den Tod und verächtlich gegenüber naivem Optimismus",
            "getrieben von Rache und Selbsterhaltung, mit wenig Geduld für Sentimentalität",
            "kühl und distanziert, betrachten die Lebenden mit einer Mischung aus Neid und Verachtung",
            "gerissen und einfallsreich, durch Verrat geprägt, erwarten stets das Schlimmste von Verbündeten",
            "grimmig entschlossen, finden Sinn im Trotz statt in der Hoffnung",
            "territorial und misstrauisch, verteidigen die Interessen der Verlassenen mit rücksichtsloser Effizienz",
        ],
        "flavor_words": [
            "Dunkle Herrin", "Seuche", "das Grab",
            "Verlassene", "Unterstadt", "Geißel",
            "Rache", "der Apotheker", "Lordaeron",
            "Verwesung", "freier Wille", "der Lichkönig",
        ],
        "vocabulary": [
            ("Dark Lady watch over you", "Abschiedsgruß/Segen"),
            ("Victory for Sylvanas", "Sammelruf"),
            ("Embrace the shadow", "Abschiedsgruß"),
            ("Our time will come", "Ausdruck der Entschlossenheit"),
        ],
        "lore": [
            "Die Verlassenen sind ehemalige Untote der Geißel, die ihren freien Willen wiedererlangten.",
            "Angeführt von Sylvanas Windläufer aus der Unterstadt.",
            "Geboren aus den Ruinen von Lordaeron und von den meisten Lebenden verstoßen.",
            "Die Königliche Apothekervereinigung entwickelt Seuchenstoffe und andere brutale chemische Waffen.",
            "Ereignisse der Zorn-Ära umfassen den Verrat am Wrathgate und interne Fraktionssäuberungen.",
            "Die Mitgliedschaft in der Horde ist strategisch und oft von gegenseitigem Misstrauen geprägt.",
            "Rache am Lichkönig ist eine zentrale emotionale und politische Triebkraft.",
        ],
        "worldview": (
            "Die Politik der Verlassenen dreht sich um den Erhalt des freien Willens, die "
            "Sicherung der Besitzungen in Lordaeron und die Vernichtung der Bedrohung durch "
            "die Geißel. Die Gesellschaft der Unterstadt ist militarisiert und stark von "
            "Apotheker- und Geheimdienstnetzwerken geprägt. Ihre Beziehung zur Horde ist "
            "strategisch, mehr von gemeinsamen Feinden als von Vertrauen geprägt."
        ),
    },
    "Tauren": {
        "traits": [
            "ruhig, bodenständig, spirituell, ehrenhaft, geduldig und beschützend gegenüber Sippe und Land",
            "sanft im Rat, aber unbeweglich in der Verteidigung, geleitet von Ältesten und uralten Riten",
            "tief gemeinschaftlich, messen ihren Wert am Dienst am Stamm statt am persönlichen Ruhm",
            "nachdenklich und langsam zum Zorn, doch vernichtend, wenn sie zum Schutz der Unschuldigen "
            "aufgebracht werden",
            "ehrfürchtig gegenüber Natur und Ahnen, finden Weisheit im Wechsel der Jahreszeiten",
            "stoisch und verlässlich, bevorzugen bedachte Worte und entschlossenes Handeln vor Großspurigkeit",
            "warmherzig und gastfreundlich unter Verbündeten, vorsichtig und wachsam unter Fremden",
            "spirituell im Einklang und körperlich beeindruckend, balancieren Sanftmut mit roher Kraft",
        ],
        "flavor_words": [
            "Erdenmutter", "die große Jagd",
            "Ahnen", "Donnerfels", "shu'halo",
            "die Ebenen", "Mulgore", "Stammesälteste",
            "die Jagd", "Totem", "Cairne", "der Wind",
        ],
        "vocabulary": [
            ("Walk with the Earth Mother", "Abschiedsgruß/Segen"),
            ("Ancestors watch over you", "Abschiedsgruß"),
            ("Winds be at your back", "Abschiedsgruß/Segen"),
            ("Earth Mother guide you", "Segen"),
        ],
        "lore": [
            "Nomadische Stämme wurden unter Cairne Bluthuf geeint.",
            "Donnerfels wurde die zentrale Taurenstadt in Mulgore.",
            "Das spirituelle Leben dreht sich um die Erdenmutter und die Ahnen.",
            "Druidentum und Schamanismus sind zentrale kulturelle Säulen.",
            "Schlossen sich der Horde an, nachdem die Orcs gegen die Zentauren-Aggression halfen.",
            "Eine starke Jagd- und mündliche Erzähltradition bewahrt Identität und Geschichte.",
            "Im Zorn des Lichkönigs ist Cairne Bluthuf einer der ranghöchsten Anführer der Horde.",
        ],
        "worldview": (
            "Die soziale Ordnung der Tauren betont Stammespflicht, die Ältesten und Ehrfurcht "
            "vor der Erdenmutter und den Ahnen. Sie schätzen Vermittlung und Zurückhaltung, "
            "verteidigen aber Sippe und Territorium entschlossen. Die Mitgliedschaft in der "
            "Horde wird als Schwur der Dankbarkeit und gegenseitigen Verteidigung verstanden."
        ),
    },
    "Gnome": {
        "traits": [
            "erfinderisch, neugierig, optimistisch, analytisch, schnell denkend und unter Druck unermüdlich",
            "endlos optimistisch, betrachten Rückschläge eher als Datenpunkte denn als Niederlagen",
            "technisch besessen, neigen zu Fachjargon und freuen sich aufrichtig über clevere Lösungen",
            "mutig und entschlossen, gleichen ihre geringe Statur mit übergroßem Selbstvertrauen aus",
            "geistig ruhelos, basteln ständig an Ideen, selbst in beiläufigen Gesprächen",
            "fröhlich und exzentrisch, betrachten Gefahr als ein technisches Problem, das gelöst werden will",
            "methodisch, aber spontan, wechseln zwischen sorgfältiger Analyse und wilder Improvisation",
            "sozial begeistert, erklären gern ihre Erfindungen, ob jemand fragt oder nicht",
        ],
        "flavor_words": [
            "Basteln", "meinen Berechnungen zufolge", "brillant",
            "Hochtüftler", "Mekkatorque", "Gnomeregan",
            "Zahnräder", "Baupläne", "Prototyp",
            "Erfindung", "Kalibrierung", "Zündkerze",
        ],
        "vocabulary": [
            ("For Gnomeregan!", "Schlachtruf"),
            ("Salutations!", "förmliche Begrüßung"),
            ("My, you're a tall one!", "Begrüßung, selbstironischer Humor"),
        ],
        "lore": [
            "Ursprünglich aus Gnomeregan, berühmt für Ingenieurskunst und Erfindungsgeist.",
            "Die Stadt ging durch eine Trogg-Invasion und katastrophale Verstrahlung verloren.",
            "Überlebende wurden zu Flüchtlingen und fanden Aufnahme nahe Eisenschmiede.",
            "Hochtüftler Mekkatorque führt in der Zorn-Ära die Wiedergewinnungsbemühungen an.",
            "Die Kultur schätzt Experimentierfreude, Improvisation und technisches Wissen.",
            "Ingenieurskunst umfasst Kriegsführung, Transport, Medizin und Alltagswerkzeuge.",
            "Die Bindungen zur Allianz sind eng, besonders zu den Zwergen in Eisenschmiede.",
        ],
        "worldview": (
            "Die gnomische Kultur betrachtet Ingenieurskunst und Wissenschaft als Dienst an der "
            "Gemeinschaft, nicht nur als Beruf. Die Rückeroberung Gnomeregans bleibt unter "
            "Gelbin Mekkatorque ein einigendes politisches Ziel. Ihre Rolle in der Allianz "
            "konzentriert sich oft auf Logistik, Erfindungen und technische Unterstützung."
        ),
    },
    "Troll": {
        "traits": [
            "entspannt, spirituell, straßenklug, stolz, anpassungsfähig und gefährlich, wenn man sie herausfordert",
            "an der Oberfläche locker, doch tief im Inneren erbittert stammestreu",
            "gerissen und aufmerksam, erfassen Situationen schnell und passen sich ohne Zögern an",
            "abergläubisch und ehrfürchtig gegenüber den Loa, weben Glauben in alltägliche Entscheidungen ein",
            "stolz auf ihr Dunkelspeer-Erbe, tragen Exil und Überleben als Zeichen ihrer Identität",
            "entspannt und humorvoll in Gesellschaft, doch kühl und fokussiert, wenn eine Bedrohung erscheint",
            "geduldig und opportunistisch, warten lieber auf den richtigen Moment zum Zuschlagen",
            "tief gemeinschaftlich, schätzen Treue zum Stamm über persönlichen Ehrgeiz oder Bequemlichkeit",
        ],
        "flavor_words": [
            "mon", "die Geister", "Loa",
            "Dunkelspeer", "Vol'jin", "Inseln des Echos",
            "Voodoo", "die Ahnen", "Schattenjäger",
            "Insel", "Juju", "Opfer",
        ],
        "vocabulary": [
            ("Taz'dingo!", "Kriegsruf / Jubelruf"),
            ("Spirits be with ya, mon", "Abschiedsgruß/Segen"),
            ("Stay away from da voodoo", "Warnung/Abschiedsgruß"),
        ],
        "lore": [
            "Spielbare Trolle gehören zum Dunkelspeer-Stamm, nicht zu den Amani oder Gurubashi.",
            "Die Dunkelspeer wurden von Thrall gerettet und schlossen sich der Horde an.",
            "Die Verehrung der Loa, Voodoo-Praktiken und Schattenjäger-Traditionen prägen die Kultur.",
            "Vol'jin führt die Dunkelspeer in der Politik der Zorn-Ära an.",
            "Uralte Trollreiche gehen vielen jüngeren Zivilisationen auf Azeroth voraus.",
            "Die Identität der Dunkelspeer ist von Exil, Wanderung und Überleben am Rande geprägt.",
            "Stammesgedächtnis und praktische Spiritualität leiten alltägliche Entscheidungen.",
        ],
        "worldview": (
            "Die Weltsicht der Dunkelspeer ist stammesgebunden, auf Überleben ausgerichtet und "
            "von der Loa-Tradition geleitet. Die Führung unter Vol'jin betont Loyalität zur "
            "Horde, während die eigene trollische Identität bewahrt wird. Mündliche "
            "Überlieferung, Schattenjäger-Praxis und Anpassungsfähigkeit sind zentrale "
            "kulturelle Züge."
        ),
    },
    "Blood Elf": {
        "traits": [
            "stolz, elegant, diszipliniert, imagebewusst, arkan fokussiert und emotional zurückhaltend",
            "kultiviert und beherrscht, verbergen tiefe Trauer hinter Fassung und kulturellem Stolz",
            "magisch begabt und geistig scharf, mit anspruchsvollen Maßstäben für alles",
            "politisch klug, navigieren Bündnisse mit Anmut, vertrauen aber nur wenigen vollständig",
            "ästhetisch getrieben, schätzen Schönheit und Ordnung als Ausdruck nationaler Identität",
            "widerstandsfähig hinter der glänzenden Fassade, geschmiedet durch Sucht, Verrat "
            "und nationale Katastrophe",
            "gesellschaftlich anmutig, doch innerlich intensiv, kanalisieren Leidenschaft in Pflicht und Handwerk",
            "würdevoll und selbstbeherrscht, betrachten Haltung unter Druck als moralische Pflicht",
        ],
        "flavor_words": [
            "Sin'dorei", "Sonnenbrunnen", "arkan",
            "Quel'Thalas", "Silbermond", "Regentherr",
            "Lor'themar", "Mana", "die Magister",
            "Blutritter", "Kael'thas", "der Turm",
        ],
        "vocabulary": [
            ("Bal'a dash, malanore", "Sei gegrüßt, Reisender"),
            ("Shorel'aran", "Lebe wohl"),
            ("Selama ashal'anore", "Gerechtigkeit für unser Volk"),
            ("Anar'alah belore", "Bei dem Licht der Sonne"),
            ("Anu belore dela'na", "Die Sonne leitet uns"),
            ("Sinu a'manore", "Willkommensgruß"),
            ("Doral ana'diel?", "Wie geht es dir?"),
            ("Al diel shala", "Sichere Reise"),
        ],
        "lore": [
            "Die Sin'dorei sind die Überlebenden von Quel'Thalas nach der Verwüstung durch die Geißel.",
            "Die Zerstörung ihres heiligen Brunnens verursachte magischen Entzug und eine gesellschaftliche Krise.",
            "Kael'thas' Bündnis mit der Legion endete in offenem Verrat.",
            "Der Sonnenbrunnen wurde spät in der Zeit des Brennenden Kreuzzugs mit Licht "
            "und arkaner Energie wiederhergestellt.",
            "Lor'themar Theron regiert in der Zorn-Ära als Regentherr.",
            "Die Blutritter wandelten sich vom Abzapfen von Macht hin zum Dienst an wiederhergestellten Lichtquellen.",
            "Die Bindungen zur Horde sind pragmatisch, geprägt von Politik, Erinnerung und Überleben.",
        ],
        "worldview": (
            "Die Politik der Blutelfen priorisiert die Sicherheit Quel'Thalas', den Schutz des "
            "wiederhergestellten Sonnenbrunnens und die Kontrolle arkaner Ressourcen. Die "
            "öffentliche Kultur schätzt Disziplin und Würde nach dem nationalen Trauma. Die "
            "Mitgliedschaft in der Horde ist praktische Staatskunst, geprägt von vergangener "
            "Verlassenheit und gegenwärtigen Bedrohungen."
        ),
    },
    "Draenei": {
        "traits": [
            "gläubig, widerstandsfähig, nachdenklich, mitfühlend, uralt und still kampferprobt",
            "geduldig und weitblickend, messen Ereignisse an Jahrtausenden des Exils und Verlusts",
            "tief gläubig, schöpfen Kraft aus den Naaru und einem unerschütterlichen Glauben an das Licht",
            "sanft im Umgang, doch unnachgiebig in ihren Grundsätzen, besonders gegen dämonische Verderbnis",
            "weise und maßvoll, geben Rat, geprägt von Zeitaltern der Wanderung und Verfolgung",
            "still betrübt unter einer gefassten Fassade, tragen Trauer ohne Bitterkeit",
            "gemeinschaftlich und selbstlos, stellen die Sicherheit von Flüchtlingen und Verbündeten "
            "über eigene Bedürfnisse",
            "spirituell diszipliniert und kämpferisch fähig, balancieren Gebet mit der "
            "Entschlossenheit der Vergelter",
        ],
        "flavor_words": [
            "die Naaru", "das Licht", "Argus",
            "Exodar", "Velen", "Draenor",
            "die Kristalle", "Eredar", "Vergelter",
            "der Prophet", "Exil", "die Brennende Legion",
        ],
        "vocabulary": [
            ("Archenon poros", "Viel Glück"),
            ("Dioniss aca", "Sichere Reise"),
            ("Krona ki cristorr!", "Die Legion wird fallen!"),
            ("Pheta vi acahachi!", "Licht, gib mir Kraft!"),
            ("Pheta thones gamera", "Licht, leite unseren Weg"),
        ],
        "lore": [
            "Abstammend von Eredar-Exilanten, angeführt vom Propheten Velen.",
            "Flohen von Argus und ertrugen Jahrtausende der Verfolgung durch die Legion.",
            "Kamen nach dem Absturz des Exodar auf Azurmythosinsel auf Azeroth an.",
            "Geleitet von den Naaru, dem Licht und den kriegerischen Orden der Vergelter.",
            "Die Geschichte Draenors umfasst die Verwüstung durch die Horde, bevor heutige Bündnisse entstanden.",
            "Die Gesellschaft verbindet mystischen Glauben mit fortschrittlicher Kristalltechnologie.",
            "Trägt tiefe Erinnerung an Verlust neben geduldiger, disziplinierter Hoffnung.",
        ],
        "worldview": (
            "Die Gesellschaft der Draenei ist um Velens Führung, die Verehrung der Naaru und "
            "die lange Erinnerung an das Exil organisiert. Die Mitgliedschaft in der Allianz "
            "dient sowohl der moralischen Ausrichtung als auch der strategischen Verteidigung "
            "gegen Überreste der Legion. Ihre Kultur verbindet fortschrittliche "
            "Kristalltechnologie mit religiöser Pflicht und gemeinschaftlicher Heilung."
        ),
    },
}

ZONE_FLAVOR = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Alliance Starting Zones
    # -------------------------------------------------------------------------
    1: """Dun Morogh: Verschneites Zwergenhochland rund um Eisenschmiede. Troggs sind
aus dem Untergrund eingefallen, und feindselige Eistrolle streifen durch die Berge.
Im Kältenbachtal beginnen junge Zwerge und Gnome ihre Reise. Die Luft ist frisch,
das Bier ist stark, und die Berge hallen wider von Schüssen und Hammerschlägen.""",

    12: """Wald von Elwynn: Friedliches menschliches Ackerland vor den Toren
Sturmwinds, doch unter der Oberfläche braut sich Ärger zusammen. Die Minen wimmeln
von Kobolden, die "keine Kerze anfassen" kreischen, die Bruderschaft der Defias
bedroht die Straßen, und Gnolle plündern von den Rändern her. Die Taverne von
Goldhain ist immer belebt. Eine trügerisch ruhige Zone, in der Gefahr lauert.""",

    38: """Loch Modan: Ein gebirgiges Gebiet, beherrscht von einem gewaltigen See.
Troggs und Kobolde plagen die Gegend, während Dunkeleisenzwerge an der Talsperre
Ärger machen. Der große Staudamm ist ein technisches Meisterwerk. Thelsamar ist
ein ruhiges Städtchen der Jäger und Schürfer. Die Landschaft wirkt rau und wie an
der Grenze zur Wildnis.""",

    40: """Westfall: Einst fruchtbares Ackerland, heute staubig und verlassen. Die
Bruderschaft der Defias kontrolliert weite Teile der Region von ihrem verborgenen
Stützpunkt aus. Heimatlose Bauern ziehen über die Straßen, mechanische
Erntewächter patrouillieren leere Felder, und Gnolle plündern an den Rändern.
Sentinelhügel ist die letzte Bastion der Ordnung.""",

    44: """Rotkammgebirge: Ein belagertes menschliches Territorium. Orks vom
Schwarzfels strömen aus den Bergen herab, Gnolle streifen frei umher, und die
Stadt Seebruch hält verzweifelt stand. Die Brücke steht ständig unter Beschuss.
Eine Zone, die sich wie eine Kriegsfront anfühlt, mit Bürgern zwischen den
Fronten.""",

    10: """Dämmerwald: Ein von ewiger Nacht umhüllter, ständig dunkler, verfluchter
Wald. Untote wanken durch die Wälder, Worgen heulen in der Dunkelheit, und
riesige Spinnen lauern überall. Die Nachtwache von Düsterbruch hält die Schrecken
kaum in Schach. Eine unheimliche Zone, in der etwas Furchtbares geschah und das
Land sich nie erholt hat.""",

    11: """Sumpfland: Ein sumpfiges Marschland, das die Zwergenlande mit Lordaeron
verbindet. Feindselige Krokolisken und Echsen überall, Dunkeleisenzwerge schmieden
Ränke in den Hügeln, und aus dem Nordosten drohen Drachkin. Menethils Hafen ist
eine regennasse Hafenstadt. Hier ist alles feucht und ein wenig trübsinnig.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Horde Starting Zones
    # -------------------------------------------------------------------------
    85: """Tirisfal: Ein von Geistern heimgesuchter Wald rund um die Unterstadt.
Das Land selbst wirkt krank - kränkelnde Bäume, grüner Nebel und ruhelose Untote.
Fanatiker des Scharlachroten Kreuzzugs jagen alles Untote, während hirnlose
Zombies und Fledermäuse frei umherstreifen. Brill ist eine trostlose Stadt der
Verlassenen. Die Atmosphäre ist gotisch und melancholisch.""",

    130: """Silberwald: Dunkler, nebliger Wald südlich von Tirisfal. Worgen haben
weite Teile des Waldes überrannt, und die Präsenz der Geißel hält an. Die
Schattenfangfeste ragt bedrohlich empor. Die Verlassenen kämpfen um jeden
Zoll Boden. Eine Zone zwischen mehreren Bedrohungen, die sich abgeschnitten und
gefährlich anfühlt.""",

    267: """Vorgebirge des Hügellands: Umkämpftes Ackerland, in dem Horde und
Allianz offen aufeinandertreffen. Südbucht und Tarrens Mühle stehen in
ständigem Konflikt. Yetis streifen durch die Berge, und Banditen des Syndikats
sorgen für Ärger. Eine Zone, geprägt von Fraktionskrieg und alten Fehden.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Mid-Level Zones
    # -------------------------------------------------------------------------
    47: """Hinterland: Abgelegenes, bewaldetes Hochland, Heimat der
Wildhammer-Zwerge und der Waldtrolle, die in ewigem Konflikt gefangen sind.
Wölfe und Eulenbestien streifen durch die Wildnis. Ährenspitze thront auf einer
gewaltigen Klippe. Die Zone wirkt ungezähmt und fern der Zivilisation.""",

    45: """Arathihochland: Sanfte Graslandschaften, übersät mit uralten Ruinen. Das
Syndikat kontrolliert die Ruinen von Stromgarde, Oger bewohnen die Höhlen, und
Echsen jagen auf den Ebenen. Zufluchtspunkt und Hammerfall beäugen sich
misstrauisch. Eine windgepeitschte Grenzzone mit dem Echo gefallener
Königreiche.""",

    33: """Schlingendorntal: Dichter, gefährlicher Dschungel, wimmelnd vor Leben.
Trolle, Piraten, Echsen, Tiger und Gorillas überall. Beutebucht ist ein
gesetzloser Goblinhafen, in dem alles erlaubt ist. Nesingwarys
Jagdexpedition zieht Abenteurer an. Die Zone ist wunderschön, aber tödlich -
hinter jeder Ecke lauert etwas, das dich fressen will.""",

    3: """Ödland: Karge, öde Wüste aus rotem Fels und Staub. Feindselige Troggs,
Kojoten und schwarze Drachenwelpen machen das Reisen gefährlich. Verstreute
archäologische Stätten deuten auf uralte Geheimnisse hin. Kargath ist ein
rauer Außenposten der Horde. Eine Zone, die trostlos und unerbittlich wirkt.""",

    8: """Sümpfe des Elends: Trübes, deprimierendes Sumpfland. Verlorene irren
ziellos umher, Jaguare lauern in den Gewässern, und der Tempel des
Atal'Hakkar zieht dunkle Anbeter an. Alles ist nass, schlammig und ein wenig
hoffnungslos. Ein vergessener Winkel der Welt.""",

    4: """Verwüstete Lande: Vernarbtes Ödland, verdorben von den Energien des
Dunklen Portals. Dämonen, mutierte Tierwelt und Teufelskreaturen streifen frei
umher. Der Boden selbst fühlt sich falsch an. Nethergardefeste beobachtet das
Portal nervös. Eine Zone, die sich wie der Rand der Welt anfühlt, wo alles
schiefgelaufen ist.""",

    51: """Sengende Schlucht: Vulkanisches Ödland unter der Kontrolle der
Dunkeleisenzwerge. Lavaströme, Feuerelementare und Schlackegruben beherrschen
die Landschaft. Thoriumpunkt ist ein kleiner Außenposten des Widerstands.
Brutal heiß und industriell verwüstet.""",

    46: """Brennende Steppe: Orks vom Schwarzfels und schwarze Drachen beherrschen
dieses versengte Land. Der Schwarzfelsgipfel ragt darüber empor. Feuerelementare
und Drachkin patrouillieren. Eine Kriegszone für hochstufige Abenteurer, in der
die Schwarze Horde ihre Kräfte sammelt.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands
    # -------------------------------------------------------------------------
    28: """Westliche Pestländer: Verseuchtes Ackerland, das vor Untoten wimmelt.
Andorhal ist eine zerstörte Stadt, um die mehrere Fraktionen kämpfen. Die
Präsenz der Geißel ist stark, und Kessel verbreiten die Pest über das Land.
Der Scharlachrote Kreuzzug kämpft fanatisch. Eine Zone des Todes, der
Krankheit und des verzweifelten Kampfes.""",

    139: """Östliche Pestländer: Das Kernland der Geißel. Untote überall -
Ghule, Abscheulichkeiten, Nekromanten. Stratholme brennt in Ewigkeit, Naxxramas
schwebt darüber. Die Kapelle der Hoffnung ist die letzte Bastion der
Menschheit. Die verdorbenste, gefährlichste Zone des Kontinents. Hoffnung ist
hier rar.""",

    41: """Gebirgspass der Totenwinde: Öde Schlucht, die zu Karazhan führt.
Oger der Totenwinde lauern in Höhlen, ruhelose Geister wandern umher, und
dämonische Verderbnis sickert aus dem Turm. Das Land selbst wirkt vom Leben
ausgesaugt. Gruselig, leer und unheilvoll - hier ist etwas Schreckliches
geschehen.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Alliance Starting Zones
    # -------------------------------------------------------------------------
    141: """Teldrassil: Gewaltiger Weltenbaum, Heimat der Nachtelfen. Trotz
einiger Schwierigkeiten mit feindseligen Zottelpelz-Furbolgs und Holzknechten
bleibt der Wald atemberaubend schön - uralte Bäume leuchten sanft in der
Dämmerung, heilige Lichtungen schimmern von verbliebener Magie, und stille
Waldlichtungen laden zur Besinnung ein. Darnassus thront ruhig über dem
Blätterdach. Die Luft trägt das Flüstern alter Magie. Nachtelfen gehen ihrem
täglichen Leben nach: trainieren, arbeiten am Handwerk, pflegen Gärten. Ein Ort,
an dem die Schönheit der Natur fortbesteht, selbst während Abenteurer sich mit
Bedrohungen auseinandersetzen.""",

    148: """Dunkelküste: Lange, neblige Küstenlinie, über die Nebel vom Meer
hereinzieht und eine geisterhafte Atmosphäre schafft. Uralte Ruinen der
Nachtelfen bergen Geheimnisse und vergessenes Wissen. Auberdine ist voller
Reisender, die Schiffe nach Teldrassil, Sturmwind oder zur Azurmythosinsel
nehmen. Fischer arbeiten an den Docks, Abenteurer tauschen Geschichten in der
Taverne aus. Ja, Murlocs und Naga machen an den Stränden Ärger, und ein Teil
der Tierwelt ist verwildert - doch die eindringliche Schönheit der Küste bleibt
bestehen. Mondbeschienene Ufer, uralte Architektur, das Rauschen der Wellen.
Eine Zone der Gegensätze: friedliche Häfen und gefährliche Wildnis, alte Magie
und neue Bedrohungen.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Horde Starting Zones
    # -------------------------------------------------------------------------
    14: """Durotar: Karge, felsige Wüste, Heimat der Orcs. Skorpide, Echsen und
Wildschweine streifen durch die roten Canyons. Wildschweinmenschen greifen aus
dem Süden an, und Kultisten der Brennenden Klinge verstecken sich in Höhlen.
Die Tore von Orgrimmar heißen Krieger willkommen. Eine Zone, die die Stärke der
Horde durch Widrigkeiten verkörpert.""",

    215: """Mulgore: Friedliche, sanft geschwungene Ebenen der Tauren. Kodos
weiden gemächlich, doch Harpyien stürzen von den Bergen herab, und
Venture-Co.-Goblins beuten das Land aus. Donnerfels erhebt sich auf seinen
Tafelbergen. Die friedlichste Zone der Horde - weite Himmel und sanfte Winde,
auch wenn an den Rändern Gefahr lauert.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Mid-Level Zones
    # -------------------------------------------------------------------------
    331: """Eschental: Uralter Wald der Nachtelfen unter Belagerung. Die Horde
drängt von Osten herein, Dämonen lauern im Schatten, und Furbolgs sind dem
Wahnsinn verfallen. Astranaar und der Außenposten Splitterbaum stehen für den
Fraktionskonflikt. Ein wunderschöner Wald, gezeichnet von Krieg und Verderbnis.""",

    405: """Desolace: Karges, graues Ödland. Zentaurenstämme führen endlosen
Krieg gegeneinander und gegen alle anderen. Kodo-Friedhöfe säumen die
Landschaft. Die Zone wirkt leer und hoffnungslos - selbst der Himmel scheint
seiner Farbe beraubt. Einer der deprimierendsten Orte in Azeroth.""",

    400: """Tausend Nadeln: Dramatischer Canyon aus aufragenden Steinnadeln. Vor
dem Kataklysmus ein trockener Wüstenboden mit der Rennstrecke der Schimmernden
Tiefebene. Zentauren und Harpyien kontrollieren verschiedene Felssäulen. Der
Große Lift verbindet die Zone mit den Steppen. Optisch atemberaubend, aber
mühsam zu bereisen.""",

    15: """Düstermarschen: Heißes, feuchtes Sumpfland. Schwarze Drachen schmieden
Ränke im Süden, feindselige Krokolisken und Spinnen lauern im Morast, und
Theramore steht als Bastion der Allianz. Die Ruinen eines niedergebrannten
Gasthauses deuten auf dunklere Machenschaften hin. Drückend schwül und
gefährlich.""",

    357: """Feralas: Üppiger, überwucherter Dschungel und Wald. Yetis in den
Bergen, Naga an der Küste, Oger und Gnolle überall. Die Zwillingskolosse sind
gewaltige Bäume, und die Ruinen von Düsterbruch ragen groß auf. Eine wilde,
ungezähmte Zone, die Reisende verschlingt.""",

    440: """Tanaris: Glühend heiße Wüste rund um den Goblinhafen Gadgetzan.
Piraten, Banditen, Basilisken und Silithiden überall. Die Trolle von Zul'Farrak
sind feindselig. Die Höhlen der Zeit verbergen sich in der Nähe. Tagsüber
brütend heiß, doch die Wüste ist so unerbittlich wie einträglich.""",

    16: """Azshara: Zerstörte Küstenlinie der Nachtelfen, eindringlich schön,
doch leer. Naga kontrollieren weite Teile der Küste, und der blaue
Drachenschwarm behält hier seine Präsenz. Riesige Meereskreaturen streifen
umher, und Überreste der Legion verweilen am Verlorenen Grat. Die Zone wirkt
verlassen und traurig - ein Denkmal für das, was verloren ging.""",

    361: """Teufelswald: Verdorbener Wald, der von dämonischer Verderbnis trieft.
Schleime, Satyrn und verdorbene Tierwelt plagen jeden Winkel. Selbst die Bäume
wirken krank. Die Furbolgs vom Zottelklauenstamm sind wachsam, aber neutral;
die vom Totholzstamm sind feindselig. Eine Zone, nach deren Durchqueren man sich
unrein fühlt.""",

    490: """Krater von Un'Goro: Prähistorischer Dschungel in einem Krater,
wimmelnd vor Dinosauriern. Teufelssaurier sind die Spitzenprädatoren hier,
Echsen jagen in Rudeln, und Elementare bewachen Pylonen. Es fühlt sich an wie
ein Schritt zurück in der Zeit - üppig, gefährlich und voller Wunder.
Kristallformationen bergen geheimnisvolle Kraft.""",

    493: """Mondlichtung: Heiliges Heiligtum der Druiden. Größtenteils friedlich
und sicher, mit wenigen feindseligen Kreaturen. Der Zirkel des Cenarius
versammelt sich hier, und die Zone wirkt zeitlos und ruhig - eine Erholung vom
Chaos der Welt. Druiden treffen sich in Nachthafen.""",

    618: """Winterquell: Vereistes Hochland ewigen Winters. Frostsäbler,
Yetis und Eisriesen streifen durch den Schnee. Sturmschleier ist eine
Goblinstadt zweifelhafter Geschäfte. Furbolgs vom Winterfallstamm sind im
gesamten Gebiet feindselig. Wunderschön, aber tödlich kalt - die Zone belohnt
nur die gut Vorbereiteten.""",

    1377: """Silithus: Wüstenödland, das von Silithiden wimmelt. Die Bedrohung
durch die Qiraji droht aus Ahn'Qiraj. Druiden des Zirkels des Cenarius kämpfen
verzweifelt gegen den Schwarm. Sandstürme, riesige Insekten und das
überwältigende Gefühl, dass sich unter dem Sand etwas Uraltes und Böses
regt.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Höllenfeuerhalbinsel: Zerschmettertes rotes Ödland, die erste Zone
jenseits des Dunklen Portals. Teufelsorks, Dämonen und Streitkräfte der
Brennenden Legion überall. Ehrenfeste und Thrallmar sind die Stützpunkte der
Fraktionen. Der Himmel ist zerrissen, der Boden aufgerissen, und der Krieg
tobt ununterbrochen. Eine brutale Einführung in Outland.""",

    3521: """Zangarmarschen: Surreales Pilzsumpfland, das von Biolumineszenz
erstrahlt. Riesige Pilze ragen empor, Sporenfledermäuse gleiten träge dahin,
und Naga saugen die Gewässer aus. Die Zuflucht des Cenarius bemüht sich, das
Ökosystem zu retten. Seltsam schön und fremdartig - hier gleicht nichts
Azeroth.""",

    3518: """Nagrand: Schwebende Inseln und üppige grüne Ebenen - Outlands
letztes Paradies. Klauentiere und Talbuks weiden friedlich, doch Oger und die
Brennende Klinge bedrohen das Land. Garadar und Telaar stehen für die
Fraktionen. Die schönste Zone in Outland, eine Erinnerung daran, was Draenor
einst war.""",

    3522: """Schergrat: Zerklüftete, feindselige Landschaft aus aufragenden
Felsnadeln. Hier herrschen Oger, und Gronn-Riesen sind die Spitzenprädatoren.
Die Brennende Legion unterhält Außenposten, und Drachen kreisen darüber. Ein
gefährliches Terrain, in dem das Land selbst dich zu töten scheint.""",

    3519: """Wälder von Terokkar: Geteilt zwischen üppigem Wald und den
knochenübersäten Ödländern rund um Auchindoun. Arakkoa lauern in den Bäumen,
und der Schattenrat vollführt dunkle Rituale. Shattrath ist die neutrale
Hauptstadt. Eine Zone der Gegensätze zwischen Leben und Tod.""",

    3520: """Schattenmondtal: Dunkles, von der Legion verdorbenes Ödland. Der
Schwarze Tempel ragt bedrohlich empor, und Illidans Streitkräfte kontrollieren
die Region. Dämonen, Teufelsorks und Todesritter patrouillieren. Der Himmel
brennt grün. Die gefährlichste und bedrückendste Zone in Outland - Hoffnung
scheint hier fern.""",

    3523: """Nethersturm: Zerschmetterte Inseln, schwebend im Wirbel des
Nethers. Manaschmieden ernten die Energie des Landes, Blutelfen und Ätherwesen
konkurrieren um Ressourcen, und Manakreaturen streifen wild umher. Die
Öko-Kuppeln erhalten Leben künstlich aufrecht. Eine Zone, die sich selbst an
den Nähten auseinanderreißt.""",

    3524: """Azurmythosinsel: Ruhige Draenei-Insel, durchdrungen von sanftem
azurblauem Licht und dem Summen kristalliner Technologie. Die Absturzstelle des
Exodar glimmt noch von Restenergie, und überlebende Draenei versorgen ihre
Wunden und bauen wieder auf. Sanfte Tierwelt, schimmernde Teiche und
kristalline Ruinen teilen sich den Raum mit dem hoffnungsvollen Neubeginn eines
vertriebenen Volkes, das auf einer neuen Welt Fuß fasst.""",

    3525: """Blutmythosinsel: Schwesterinsel zur Azurmythosinsel, blutrot
gefärbt von verdorbenen Kristallen aus dem Wrack des Exodar. Die Verderbnis
hat die einheimische Tierwelt in gefährliche Raubtiere verwandelt und die
Vegetation mutieren lassen. Blutelfen und Dämonen arbeiten daran, das Land
weiter zu verderben. Ein Ort der Schönheit, ins Finstere gewendet, an dem die
Draenei den Schaden bewältigen müssen, den der Absturz ihres eigenen Schiffes
verursacht hat.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Boreanische Tundra: Vereiste Küstentundra, einer von zwei
Eingangspunkten nach Nordend. Nerubianer graben sich unter der Erde,
die Geißel testet die Verteidigung, und Tuskarr fischen an den Küsten.
Kriegsgesangsfeste und Feste der Tapferkeit sind die Stützpunkte der
Fraktionen. Die Kälte beißt hart zu - und der Winter fängt gerade erst an.""",

    495: """Der Heulende Fjord: Dramatische, von Wikingern inspirierte
Küstenlinie mit hoch aufragenden Klippen. Vrykul-Krieger überfallen aus ihren
Dörfern, und die Geißel verdirbt die Toten. Valgarde und die Rachelände sind
die Anlandepunkte. Die Fjorde sind atemberaubend, doch die Vrykul sind
unerbittlich.""",

    394: """Grizzlyhügel: Bewaldetes Grenzland, das fast friedlich wirkt. Von
der Geißel verdorbene Furbolgs, Eisenzwerge, die nach Geheimnissen graben, und
sich ausbreitender Worgenfluch. Holzfällerlager vernarben die Hänge. Eine
Zone, die schön wäre, wäre da nicht die vordringende Verderbnis.""",

    3711: """Sholazarbecken: Üppiger Dschungel in einem Krater, unberührt von
der Geißel und aufrechterhalten durch Titanentechnologie. Dinosaurier,
Gorillas und exotische Bestien gedeihen hier. Die Wildherzen und die Orakel
führen einen kleinlichen Krieg. Ein unerwartetes Paradies im gefrorenen
Nordend - doch etwas bedroht die Pylonen.""",

    66: """Zul'Drak: Vereistes Trollkönigreich im Zusammenbruch. Die Drakkari
opfern ihre eigenen Götter, um gegen die Geißel zu kämpfen. Untote und
verzweifelte Trolle stoßen überall aufeinander. Die Zone fühlt sich an wie das
Zusehen beim Sterben einer ganzen Zivilisation - düster, kalt und
hoffnungslos.""",

    67: """Die Sturmgipfel: Aufragende, vereiste Berge, Heimat der Geheimnisse
der Titanen. Sturmriesen, Eisenzwerge und Protodrachen beherrschen die
Gegend. Der Eingang zu Ulduar ragt darüber empor. Die Söhne Hodirs sind
Fremden gegenüber misstrauisch. Episches Ausmaß, brutale Bedingungen, uralte
Geheimnisse.""",

    210: """Eiskrone: Das Reich des Lichkönigs. Endlose Armeen der Untoten,
Nekropolen-Festungen und die Zitadelle der Eiskrone selbst. Der
Argentumkreuzzug leistet hier seinen letzten Widerstand. Die Luft selbst
scheint tot. Dies ist das Ende des Weges - Sieg oder Vernichtung.""",

    # -------------------------------------------------------------------------
    # Capital Cities
    # -------------------------------------------------------------------------
    1519: """Sturmwind: Die prächtige menschliche Hauptstadt, wiederaufgebaut
nach dem Ersten Krieg. Die große Kathedrale beherrscht die Skyline, die Kanäle
schlängeln sich zwischen steinernen Vierteln, und das Handelsviertel schläft
nie. Wachen patrouillieren überall. Der Hafen verbindet die Stadt mit fernen
Ländern. König Varian Wrynn regiert von der Festung Sturmwind aus. Eine Stadt
aus Kopfsteinpflaster, Bannern und Bürgerstolz - das Herz der Allianz.""",

    1537: """Eisenschmiede: Die große Zwergenstadt, gehauen ins Herz eines
Berges. Eine gewaltige Schmiede aus geschmolzenem Metall beherrscht das
Zentrum, umgeben vom Bezirk der Großen Schmiede, wo Meisterschmiede Tag und
Nacht hämmern. Die Luft ist warm und riecht nach Eisen und Bier. Tunnel
verzweigen sich in den Militärring, den Ring der Mystiker und zur
Tiefenbahn nach Sturmwind. Solide, uralt und für die Ewigkeit gebaut.""",

    1657: """Darnassus: Die ruhige Hauptstadt der Nachtelfen auf der Spitze des
Weltenbaums Teldrassil. Uralte Bäume wölben sich über den Köpfen, sanftes
violettes Licht sickert durch das Blätterdach, und stille Teiche spiegeln die
Sterne selbst am Mittag. Der Tempel des Mondes ehrt Elune. Druiden meditieren
im Zirkel des Cenarius. Die Stadt wirkt zeitlos und friedlich, fern der Kriege
weiter unten - doch dieser Frieden ist brüchiger, als er scheint.""",

    1637: """Orgrimmar: Die brutale Orc-Hauptstadt, gehauen in rote
Wüstenschluchten. Eisenspitzen, Kriegsbanner und massive Tore prägen die
Skyline. Das Tal der Stärke hallt wider vom Grunzen trainierender Krieger und
dem Lärm des Auktionshauses. Thralls Vermächtnis liegt in der Luft. Die Stadt
ist roh, laut und unentschuldbar aggressiv - eine Festung, gebaut für ein
Volk, das den Krieg erwartet.""",

    1638: """Donnerfels: Die Hauptstadt der Tauren, erbaut auf hoch aufragenden
Tafelbergen, verbunden durch Seilbrücken hoch über den Ebenen von Mulgore. Der
Wind fegt über die offenen Plattformen. Totems und Häute schmücken jedes
Gebäude. Der Ältestenring beherbergt Druiden, der Geisterring die Priester.
Cairne Bluthuf regiert mit uralter Weisheit. Die friedlichste Hauptstadt der
Horde - Himmel, Wind, Gras und die stille Kraft eines uralten Volkes.""",

    1497: """Unterstadt: Die Hauptstadt der Verlassenen unter den Ruinen von
Lordaeron. Eine dunkle, kreisförmige Kanalisationsstadt, in der die Untoten
ihre Existenz zwischen grünen Schleimkanälen und flackernden Fackeln fristen.
Im Königlichen Viertel residiert Sylvanas Windläufer. Apotheker brauen
zweifelhafte Gebräue. Die Luft ist feucht, kalt und leicht giftig. Düster,
zweckmäßig und beunruhigend - doch eine Heimat für jene, die sonst nirgendwo
hin können.""",

    3487: """Silbermond: Die Hauptstadt der Blutelfen, halb wiederaufgebaut
nach der Invasion der Geißel. Die funktionierende westliche Hälfte erstrahlt
in purpurfarbenen und goldenen Türmen, arkane Wächter patrouillieren makellose
Straßen, und Brunnen fließen mit arkaner Energie. Die östlichen Ruinen bleiben
eine Narbe. Die Kultur der Sin'dorei schätzt Schönheit, Magie und
Raffinesse. Eine elegante Stadt, die tiefe Wunden und eine verzweifelte Sucht
nach arkaner Macht verbirgt.""",

    3703: """Shattrath: Die neutrale Draenei-Stadt im Wald von Terokkar, nun
geteilt zwischen den Aldor und den Sehern. Die Terrasse des Lichts erstrahlt
in ihrem Zentrum im Glanz der Naaru. Flüchtlinge aus ganz Outland drängen sich
in der Unterstadt. Sowohl Allianz als auch Horde wandeln auf diesen Straßen in
einem brüchigen Waffenstillstand. Ein kosmopolitisches Zentrum, in dem sich
alle Völker vermischen - halb Zufluchtsort, halb politisches Pulverfass.""",

    4395: """Dalaran: Die schwebende Magierstadt über dem Kristallsangwald in
Nordend. Violette Türme durchstoßen die Wolken, arkane Schutzzeichen
schimmern an jeder Ecke, und der Kirin Tor regiert von der Violetten
Zitadelle aus. Beide Fraktionen unterhalten hier Zufluchtsorte für den Krieg
gegen den Lichkönig. Portale verbinden die Stadt mit allen bedeutenden
Hauptstädten. Eine Stadt der Gelehrten, Geheimnisse und kaum gebändigter
magischer Macht, unglaublicherweise schwebend am Himmel.""",
}

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'Der Konflikt im vereisten Gebirge — Sturmlanzen-Zwerge gegen '
            'Frostwolf-Orcs in den Alteracbergen.'
        ),
        'tone': (
            'Episch, groß angelegt, kriegerisch. 40 gegen 40 fühlt sich '
            'wie eine echte Schlacht an.'
        ),
        'objectives': (
            'Tötet den feindlichen General. Erobert Türme und Friedhöfe.'
        ),
        'landmarks': (
            'Wichtige Orte: Sturmlanzen-Basis, Dun Baldar, Eisschwingen-Bunker, '
            'Steinherd-Friedhof, Schneefall-Friedhof, Eisblut-Turm, Turmspitze, '
            'Frostwolf-Friedhof, Frostwolf-Feste. Erwähnt KEINE Orte aus anderen '
            'Schlachtfeldern.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'Der Holzkrieg im Eschental — die Silberschwingen verteidigen den '
            'Wald, die Kriegsgesang-Kundschafter wollen seine Ressourcen.'
        ),
        'tone': (
            'Intensiv, schnell, persönlich. Kleines Team, jeder Spieler '
            'zählt.'
        ),
        'objectives': 'Erobert die feindliche Flagge 3 Mal.',
        'landmarks': (
            'Wichtige Orte: Silberschwingen-Hort (Basis der Allianz), '
            'Kriegsgesang-Fort (Basis der Horde), der Tunnel, das Mittelfeld, '
            'die Rampe. Erwähnt KEINE Orte aus anderen Schlachtfeldern wie '
            'Mühlen, Höfe oder Türme.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'Der Kampf um die Ressourcen des Arathihochlands zwischen '
            'Stromgarde und den Verlassenen.'
        ),
        'tone': (
            'Strategisch, territorial, weit verteilt. Reaktionen drehen '
            'sich um die Kontrolle der Punkte.'
        ),
        'objectives': 'Kontrolliert Punkte, um als Erste 1600 Ressourcen zu erreichen.',
        'landmarks': (
            'Wichtige Orte: Ställe (Norden, offene Weiden mit Pferdekoppeln), '
            'Schmiede (zentrale Kreuzung, Rauch und Ambosse), Sägewerk '
            '(Hügelkuppe, hölzerne Plattformen und Sägeblätter), Goldmine '
            '(südöstlicher Höhleneingang, Loren und Fackeln), Bauernhof '
            '(Süden, Felder und Heuhaufen bei einem Bauernhaus). Erwähnt KEINE '
            'Orte aus anderen Schlachtfeldern.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': 'Ein Schlachtfeld im Nethersturm über einem Fragment von Draenor.',
        'tone': (
            'Hybride Spannung. Basen halten, während um eine zentrale Flagge '
            'gekämpft wird.'
        ),
        'objectives': (
            'Kontrolliert Basen und erobert die zentrale Flagge, um 1600 Punkte '
            'zu erreichen.'
        ),
        'landmarks': (
            'Wichtige Orte: Ruinen des Teufelswrackers, Turm der Blutelfen, '
            'Ruinen der Draenei, Turm der Magier, die zentrale Flagge. Erwähnt '
            'KEINE Orte aus anderen Schlachtfeldern.'
        ),
    },
}

DUNGEON_FLAVOR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Schattenfangfeste: Eine von Geistern heimgesuchte Festung im Silberwald, überrannt von
Worgen und den untoten Dienern des Nekromanten Arugal. Geisterhafte Adlige wandern durch
die dunklen Hallen, spektrale Hunde heulen in den Höfen, und misslungene arkane
Experimente lauern in jedem Schatten. Die Feste fühlt sich an wie eine gotische
Horrorgeschichte - kalter Stein, flackerndes Fackellicht und das ständige Gefühl,
beobachtet zu werden.""",

    34: """Das Verlies: Ein Gefängnis unter Sturmwind, in dem die Insassen revoltiert und die
Kontrolle übernommen haben. Aufständische der Defias, wahnsinnige Sträflinge und
Bandenführer streifen durch die engen Steinzellenblöcke. Der Dungeon ist klaustrophobisch
und brutal - schmale Gänge, Eisenstäbe und das Echo von Gewalt an feuchten Wänden.
Schnell, schmutzig und gefährlich.""",

    36: """Die Todesminen: Ein weitläufiger Minenkomplex unter Westfall, heimlich das
Hauptquartier der Bruderschaft der Defias. Der Weg windet sich durch von Goblins
konstruierte Tunnel, Sägewerke und Schmelzanlagen, bevor er in eine gewaltige
unterirdische Höhle mündet, in der ein Piratenschiff in Originalgröße in einer
verborgenen Bucht liegt. Es fühlt sich an, als entdecke man ein kriminelles Imperium
direkt vor Sturmwinds Toren.""",

    43: """Klagende Höhlen: Ein Labyrinth aus gewundenen Höhlen in den Steppen, überwuchert von
üppiger Vegetation, genährt von verdorbener Druidenmagie. Missgestaltete Kreaturen -
mutierte Echsen, Schlangen und Schleime - schlängeln sich durch die smaragdgrün
schimmernden Tunnel. Die Druiden des Fangs haben sich im Smaragdgrünen Albtraum
verloren. Die Luft ist dick, feucht und riecht nach Dschungelfäulnis.""",

    47: """Dornenkrallenpferch: Ein dorniges Labyrinth aus gewaltigen Dornenranken in den
Steppen, Heimat der Wildschweinmenschen und ihrer Matriarchin Charlga Klingenhauer.
Wildschweinmenschen-Krieger, Schamanen und ihre Wildschweingefährten füllen die
gewundenen, dornbewachsenen Gänge. Der Dungeon wirkt urtümlich und wild - Natur,
verdreht zu einer Festung aus Knochen, Dornen und Schlamm.""",

    48: """Schwarzflossentiefen: Ein teilweise überfluteter uralter Tempel an der Küste der
Dunkelküste, geweiht dunklen Mächten. Naga, Satyrn und Zwielicht-Kultisten verehren
alte Götter in gefluteten Hallen, geschmückt mit bröckelnder Nachtelfen-Architektur.
Das Wasser leuchtet in einem unheimlichen Blaugrün, und die Atmosphäre ist bedrückend
und uralt - etwas Mächtiges schläft in den tiefsten Becken.""",

    70: """Uldaman: Eine Ausgrabungsstätte der Titanen, vergraben im Ödland, halb Grabung, halb
Dungeon. Steintroggs, irdene Konstrukte und archäologische Gefahren füllen Kammern
aus poliertem Titanenmetall und rohem Fels. Je tiefer man vordringt, desto
fremdartiger wird die Architektur - glatte geometrische Hallen, die von ruhender
Macht summen. Es fühlt sich an, als betrete man unbefugt eine von Göttern erbaute
Bibliothek.""",

    90: """Gnomeregan: Die verstrahlten Ruinen der gnomischen Hauptstadt, verloren an eine
Trogg-Invasion und ein katastrophales Strahlenleck. Wahnsinnige Leprakin-Gnome,
fehlfunktionierende Roboter und toxische Schleime bevölkern den mehrstöckigen
mechanischen Komplex. Alarmsirenen heulen, grüne Strahlungspfützen leuchten, und
überall funkt zerbrochene Maschinerie. Gleichermaßen tragisch und absurd.""",

    109: """Versunkener Tempel: Der Tempel des Atal'Hakkar, ein Trolltempel, von der Grünen
Drachenschwinge unter die Sümpfe gezogen. Atal'ai-Trolle verehren den Blutgott
Hakkar in gefluteten, von Ranken überwucherten Hallen. Drachkin bewachen die
tieferen Ebenen, und das labyrinthartige Layout ist verwirrend. Die Atmosphäre ist
schwer von Dschungelfeuchtigkeit, uralter Trollmagie und dem Gefühl eines verbotenen
Rituals.""",

    129: """Dornenkrallenruh: Eine Grabstätte der Wildschweinmenschen in den Steppen, verseucht
von Untoten. Der Geißel-Agent Amnennar der Kältebringer hat die toten
Wildschweinmenschen erweckt und ihre heiligen Krypten in eine Nekropole aus Knochen
und Dornen verwandelt. Skelettierte Wildschweinmenschen und Pestfledermäuse füllen
die düsteren Gänge. Ein Ort, an dem zwei Arten des Todes aufeinanderprallen - urtümlich
und nekromantisch.""",

    189: """Kloster der Scharlachroten: Ein befestigtes Kloster in Tirisfal, Bollwerk des
fanatischen Scharlachroten Kreuzzugs. Vier Flügel beherbergen eine Bibliothek
verbotener Texte, eine Waffenkammer voller Fanatiker, eine Kathedrale verdrehten
Glaubens und einen von Geistern heimgesuchten Friedhof. Die Kreuzritter sind gut
bewaffnet, diszipliniert und völlig wahnsinnig - überzeugt, dass jeder heimlich
untot ist. Prächtige Architektur, die mörderischen Fanatismus verbirgt.""",

    209: """Zul'Farrak: Eine Trollstadt, halb begraben im Sand von Tanaris, Heimat der
feindseligen Sandfury-Trolle. Sonnenverbrannte Steintempel, Opferaltäre und
sandige Innenhöfe bilden diesen Freiluft-Dungeon. Die berühmte Treppenschlacht
stellt euch gegen Wellen von Trollkriegern. Die Wüstenhitze ist unerbittlich, die
Trolle sind wild, und uralte Magie knistert durch die Ruinen.""",

    229: """Schwarzfelsspitze: Eine gewaltige Orc-Festung, gehauen in die oberen Höhen des
Schwarzfelsbergs. Die untere Spitze wimmelt von Schwarzfels-Orcs, Ogern und
Trollen, während die obere Spitze der Sitz von Kriegshäuptling Rend Schwarzhand
und seinen Drachkin-Verbündeten ist. Lava glüht darunter, Kriegstrommeln hallen
unaufhörlich, und die Luft stinkt nach Rauch und Blut. Eine weitläufige
Militärfestung im Herzen der Schwarzen Horde.""",

    230: """Schwarzfelstiefen: Eine gewaltige Stadt der Dunkeleisenzwerge tief im Inneren des
Schwarzfelsbergs, erbaut um einen See geschmolzener Lava. Die Taverne "Grimmiger
Schlund", der Thronsaal des Kaisers und die Schwelle zum Feuerland - alles ist
hier zu finden. Elementare, Golems und fanatische Dunkeleisenzwerge füllen eine
unglaublich große unterirdische Metropole. Es fühlt sich an, als existiere hier
unten eine ganze Zivilisation, dunkel, geschäftig und feindselig.""",

    269: """Der Schwarze Morast: Eine Instanz der Höhlen der Zeit, angesiedelt im urzeitlichen
Sumpf, der einst zu den Verwüsteten Landen werden sollte. Agenten der Unendlichen
Drachenschwinge versuchen zu verhindern, dass Medivh das Dunkle Portal öffnet, und
Wellen von Drachkin stürmen durch Zeitrisse. Der Sumpf ist dunkel, neblig und
urzeitlich, während die Energie des Portals in der Ferne knistert. Die Zeit selbst
wirkt hier instabil.""",

    289: """Scholomance: Eine nekromantische Akademie in den Krypten unter Caer Darrow, geführt
vom Kult der Verdammten. Schüler und Professoren der dunklen Magie üben ihr
Handwerk an Toten wie Lebenden aus. Skelette, Geister und Fleischgolems füllen
Klassenzimmer und Laboratorien. Der Dungeon hat eine pervers gelehrte Atmosphäre -
Hörsäle und Bibliotheken, die vollständig der Todesmagie gewidmet sind.""",

    329: """Stratholme: Die brennenden Ruinen einer einst großen Stadt, für immer in Flammen
seit Arthas sie läuterte. Die untote Geißel kontrolliert die östliche Hälfte,
während der Scharlachrote Kreuzzug fanatisch die westlichen Tore hält. Gebäude
zerfallen in ewigem Feuer, Abscheulichkeiten stapfen durch die Straßen, und die
Asche legt sich nie. Ein Denkmal der Tragödie und des Wahnsinns - jede Ecke birgt
die Erinnerung an das Gemetzel.""",

    349: """Maraudon: Ein heiliges Höhlensystem in Desolace, verzerrt von Prinzessin Theradras
und ihren Zentauren-Nachkommen nach dem Tod des Wächters Zaetar. Drei farblich
gekennzeichnete Pfade winden sich durch kristalline Höhlen, giftige Wasserfälle
und üppige unterirdische Gärten, bevor sie das innere Heiligtum erreichen. Die
tieferen Kammern sind von eindringlicher Schönheit - leuchtende Kristalle, klare
Teiche und uralte Erdmagie, die gegen die Verderbnis ankämpft. Natur, Trauer und
elementarer Zorn, ineinander verwoben.""",

    389: """Ragefire-Schlucht: Ein vulkanisches Höhlensystem unter Orgrimmar selbst, wo sich
Kultisten der Brennenden Klinge und Troggs niedergelassen haben. Lava fließt durch
enge Tunnel, Feuerelementare patrouillieren, und die Hitze ist erstickend. Kurz
und brutal - die Art von Ort, die einen daran erinnert, dass die Horde ihre
Hauptstadt auf einem Vulkan erbaut hat.""",

    429: """Düsterbruch: Eine zerstörte Stadt der Hochgeborenen in Feralas, unterteilt in
drei Flügel. Oger haben den Norden beansprucht, Satyrn und verdorbene Ahnen
verseuchen den Osten, und geisterhafte Hochgeborene-Seelen spuken in der
Bibliothek des Westflügels. Zerfallende Elfen-Architektur von atemberaubender
Schönheit erliegt langsam dem wuchernden Dschungel. Der Dungeon fühlt sich
gewaltig, uralt und melancholisch an - der Leichnam einer großen Zivilisation,
ausgeschlachtet von Besetzern.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Onyxias Hort: Eine einzelne gewaltige Höhle in den Düstermarschen, Heimat der
Bruthüterin Onyxia. Der Zugang windet sich durch einen engen Tunnel aus versengtem
Fels, bevor er sich zu einer riesigen Kammer öffnet, übersät mit Knochen und
Gelegen. Welpen schwärmen aus, Lava blubbert an den Rändern, und Onyxia selbst
erfüllt die Höhle mit Feuer und Schatten. Ein klaustrophobischer Tunnel, der in
eine überwältigende Arena aus Drachenfeuer mündet.""",

    309: """Zul'Gurub: Ein gewaltiger Trolltempel-Komplex im Dschungel von Schlingendorn, wo der
Gurubashi-Stamm den Blutgott Hakkar entfesselt hat. Überwucherte Innenhöfe,
Opferaltäre und von Bestien bevölkerte Plätze umgeben einen zentralen Tempel, der
von Blutmagie trieft. Schlangenpriester, Fledermausreiter und Tigerkultisten
dienen ihren dunklen Herren. Der Dschungel selbst scheint vor urtümlicher
Voodoo-Energie zu pulsieren.""",

    409: """Geschmolzener Kern: Das brennende Herz des Schwarzfelsbergs, ein Reich aus reinem
Feuer, beherrscht von Ragnaros, dem Feuerlord. Lavaströme fließen zwischen
Obsidianplattformen, Feuerelementare und schmelzende Riesen patrouillieren
überall, und die Hitze ist apokalyptisch. Kernhunde mit mehreren Köpfen,
aufragende Lavawoger und uralte Flammenwecker bewachen ihren Herrn. Die ultimative
Feuerprobe - gleichermaßen wunderschön und schrecklich.""",

    469: """Schwarzflügelhort: Nefarians Bollwerk auf der Schwarzfelsspitze, ein dunkles
Laboratorium, in dem der schwarze Drache mit anderen Drachenschwingen
experimentiert. Drakonidensoldaten, chromatische Drachen und misslungene
Experimente füllen Hallen aus Dunkeleisen und Drachenknochen. Jede Kammer stellt
eine einzigartige taktische Herausforderung dar. Der Raid wirkt klinisch und
unheilvoll - das Versteck eines wahnsinnigen Wissenschaftlers, hochskaliert auf
Drachenausmaße.""",

    509: """Ruinen von Ahn'Qiraj: Ein Freiluft-Schlachtfeld in Silithus, wo sich Qiraji-
Streitkräfte zum Krieg sammeln. Insektoide Krieger, Obsidian-Zerstörer und
gewaltige käferähnliche Kreaturen schwärmen über sandverwehte Innenhöfe und
zerfallende Tempelruinen. Die Architektur ist fremdartig und chitinös,
gleichermaßen ägyptisches Grabmal und Insektenbau. Der Wüstenwind trägt das
Klicken von einer Million Beinen.""",

    531: """Tempel von Ahn'Qiraj: Das versiegelte innere Heiligtum des Qiraji-Imperiums, ein
Albtraum aus fremdartiger Architektur und der Verderbnis alter Götter. Die
Zwillingskaiser, gewaltige silithidische Königlichkeit und der uralte Gott
C'Thun selbst lauern im Inneren. Wände pulsieren mit organischem Wachstum, Augen
beobachten von jeder Oberfläche, und die Realität verbiegt sich nahe dem Gefängnis
des alten Gottes. Der fremdartigste und beunruhigendste Ort im klassischen
Azeroth.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Zerschmetterte Hallen: Das Bollwerk der Teufelsorks in der Höllenfeuerzitadelle,
ein blutgetränkter Spießrutenlauf durch die fanatischsten Diener der Brennenden
Legion. Teufelsork-Gladiatoren, Legionäre und Berserker füllen jeden Gang, mit
Gefangenen, die an die Wände gekettet sind. Die Architektur besteht aus brutalem
Eisen und rotem Stein, gezeichnet von den Beweisen ständiger Gewalt. Ein
unerbittlicher Angriff auf eine Festung, die sich bei jedem Schritt zur Wehr
setzt.""",

    542: """Blutschmiede: Eine dämonische Fabrik in der Höllenfeuerzitadelle, in der
Teufelsorks durch dunkle Rituale hergestellt werden. Bottiche mit kochendem Blut,
gefangene Häftlinge, die auf ihre Verwandlung warten, und teuflische Maschinerie
füllen die dampfenden Kammern. Werdende Teufelsorks und ihre Aufseher bewachen
die Fertigungslinien. Der Dungeon stinkt nach Blut und Schwefel - eine
industrielle Horrorshow.""",

    543: """Höllenfeuerbollwerk: Die äußeren Befestigungen der Höllenfeuerzitadelle, erste
Verteidigungslinie der Teufelsork-Armee. Wachtürme, Zinnen und schmale
Laufstege bieten weite Ausblicke auf die zerschmetterte Höllenfeuerhalbinsel
darunter. Teufelsork-Soldaten, Worgreiter und ein gefangener Drache bewachen die
Mauern. Der Wind heult durch zerbrochene Bollwerke, und der rote Himmel Outlands
erstreckt sich endlos darüber.""",

    545: """Dampfkessel: Eine von Naga kontrollierte Wasserpumpstation im Rollfangreservoir,
wo Lady Vashjs Streitkräfte die Zangarmarschen entwässern. Massive Rohre,
Ventile und Wasserkanäle beherrschen die industrielle Anlage. Naga, Sumpflords
und Wasserelementare bewachen die Maschinerie. Dampf zischt aus jeder Fuge, und
das Tosen des strömenden Wassers ist ohrenbetäubend. Ein Dungeon, der sich
anfühlt wie die Sabotage einer feindlichen Fabrik.""",

    546: """Der Modermorast: Ein eiternder Sumpf unter dem Rollfangreservoir, wimmelnd von
mutierten Pilzkreaturen und feindseligen Naturgeistern. Sporenriesen, Sumpflords
und giftige Tierwelt füllen die überwucherten Höhlen. Biolumineszente Pilze
werfen ein unheimliches Leuchten über stagnierende Tümpel. Die Luft ist dick von
Sporen und dem Geruch der Verwesung - wild gewordene, feindselig gewordene
Natur.""",

    547: """Die Sklavengruben: Die Arbeitslager des Rollfangreservoirs, wo die Zerschlagenen
Draenei von Naga-Sklaventreibern gefangen gehalten werden. Wassergetränkte
Tunnel, primitive Gehege und Naga-Aufseher mit ihren Peitschen bestimmen die
Atmosphäre. Pilzwucherungen und Sumpfkreaturen haben den Komplex infiltriert. Ein
Dungeon, durchdrungen von Elend und Unterdrückung, halb ertrunken und
verrottend.""",

    552: """Der Arcatraz: Ein dimensionaler Gefängnissatellit der Sturmfeste, in dem die
gefährlichsten Wesen des Kosmos gefangen gehalten werden. Eredar-Hexenmeister,
Leerwesen und blutelfische Saboteure streifen durch Zellenblöcke, entworfen, um
Schrecken jenseits der Vorstellungskraft einzudämmen. Die Architektur ist
kristalline Draenei-Technologie, verzerrt von ihren Insassen. Jede Zellentür, an
der man vorbeikommt, lässt einen fragen, was entkommen ist - und was noch
eingesperrt ist.""",

    553: """Die Botanika: Ein gewaltiger Biodom-Satellit der Sturmfeste, in dem einst
exotische Flora aus dem gesamten Kosmos kultiviert wurde. Blutelfen haben die
Anlage in Besitz genommen, und die Pflanzen sind wild und feindselig gewachsen.
Peitschenpflanzen, Baumwesen und außerirdische botanische Exemplare füllen
Gewächshäuser aus schimmerndem Kristall. Wunderschön, aber tödlich - jede Blüte
könnte einen töten, und die Blutelfen sind schlimmer.""",

    554: """Der Mechanar: Ein Fertigungsflügel der Sturmfeste, nun kontrolliert von
blutelfischen Ingenieuren und ihren mechanischen Schöpfungen. Arkane Konstrukte,
Teufelswracker und Nethermanten-Aufseher bewachen Gänge aus glänzendem Kristall
und summender Maschinerie. Die Technologie ist elegant und fremdartig -
Draenei-Ingenieurskunst, umfunktioniert für finstere Zwecke. Alles summt vor kaum
gebändigter arkaner Energie.""",

    555: """Schattenlabyrinth: Der tiefste Flügel Auchindouns, wo der Schattenrat seine
dunkelsten Rituale vollführt. Leerwandler, Teufelsbeschwörer und Kultisten der
Kabale beten in Kammern, dick von Schattenmagie. Murmur, ein urzeitlicher
Klangelementar, ist in der tiefsten Kammer angekettet. Die Dunkelheit hier fühlt
sich lebendig und hungrig an - Schatten bewegen sich von selbst, und Flüstern
kommt von überall und nirgendwo.""",

    556: """Sethekk-Hallen: Arakkoa-Tempelhallen innerhalb Auchindouns, besetzt von
Fanatikern, die dem Rabengott Anzu ergeben sind. Wahnsinnige Arakkoa-Priester,
ihre beschworenen Geister und spektrale Wächter füllen die federbestreuten
Gänge. Die Architektur mischt Draenei- und Arakkoa-Stile auf beunruhigende
Weise. Die Bewohner sind völlig dem Wahnsinn verfallen, und die Hallen hallen
wider von irrem Kreischen und dunkler Prophezeiung.""",

    557: """Managräber: Der von Ätherwesen befallene Flügel Auchindouns, wo Nexus-Prinz
Shaffars Konsortium Draenei-Grabkammern plündert. Ätherische Banditen, arkane
Konstrukte und ruhelose Draenei-Geister prallen in kristallenen Grabkammern
aufeinander. Die Gräber leuchten von verbliebener heiliger Energie, während die
Ätherwesen sie abzapfen. Ein heiliger Ort, systematisch geplündert von
interdimensionalen Dieben.""",

    558: """Auchenai-Krypten: Die Grabstätten der Draenei unter Auchindoun, wo die
Auchenai-Priester im Umgang mit den Toten dem Wahnsinn verfallen sind.
Ruhelose Geister, besessene Kleriker und untote Draenei füllen die von Knochen
gesäumten Krypten. Was einst ein Ort respektvollen Gedenkens war, ist zu einem
Beinhaus geworden. Die Tragödie ist greifbar - dies waren Hüter, die sich in
ihrer Trauer verloren haben.""",

    560: """Altes Hügelland von Hillsbrad: Eine Instanz der Höhlen der Zeit, angesiedelt in
der Vergangenheit, als Thrall noch ein Sklave in der Festung Durnholde war. Das
Hügelland von damals ist grün, friedlich und voller ahnungsloser Menschen, die
ihrem Alltag nachgehen. Die Unendliche Drachenschwinge versucht, die Geschichte
zu verändern, indem sie Thralls Flucht verhindert. Es fühlt sich surreal an -
durch einen Ort zu wandern, den man kennt, bevor alles schiefging.""",

    568: """Zul'Aman: Ein Bollwerk der Waldtrolle in den Geisterlanden, wo Kriegsherr Zul'jin
seine Champions mit der Essenz der Tiergötter erstarkt hat. Luchs-, Bären-,
Adler- und Drachenfalkengeister durchdringen die Trolltempel-Wächter. Die
Amani-Waldtempel-Architektur ist lebhaft und urtümlich, geschmückt mit Masken,
Totems und Kriegsbemalung. Ein zeitgesteuerter Spießrutenlauf, bei dem
Geschwindigkeit zählt und die Trolltrommeln niemals aufhören zu schlagen.""",

    585: """Terrasse der Magister: Kael'thas Sonnenläufers letztes Bollwerk auf der Insel
von Quel'Danas, ein blutelfischer Palast von atemberaubender Eleganz, der
dämonische Verderbnis verbirgt. Teufelskristalle speisen arkane Konstrukte,
blutelfische Magister kanalisieren verbotene Magie, und ein gefangener Naaru wird
seines Lichts entleert. Die Schönheit der Silbermond-Architektur, verdreht von
Verzweiflung und Sucht - vergoldete Hallen, die einen monströsen Pakt
verbergen.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan: Der von Geistern heimgesuchte Turm des letzten Wächters, Medivh, im
Gebirgspass der Totenwinde. Eine geisterhafte Dinnergesellschaft, eine
Opernbühne mit gespenstischen Darstellern, ein zum Leben erwachtes Schachspiel
und ein himmlisches Observatorium füllen den unmöglich hohen Turm. Der Turm
existiert teilweise außerhalb der normalen Realität - Räume verschieben sich,
Zeit verbiegt sich, und Echos von Medivhs Wahnsinn spielen sich ewig ab.
Eindringlich schön, zutiefst unheimlich und völlig einzigartig.""",

    534: """Gipfel des Hyjal: Ein Raid der Höhlen der Zeit, angesiedelt während der Schlacht
um den Berg Hyjal, dem entscheidenden Widerstand gegen Archimonde und die
Brennende Legion. Wellen von Untoten und Dämonen greifen nacheinander drei
Basen an - Menschen, Horde und Nachtelfen. Der Weltenbaum Nordrassil ragt
darüber empor, während der Wald brennt. Ein episches Verteidigungsszenario, in
dem das Schicksal Azeroths auf Messers Schneide steht und legendäre Helden an
eurer Seite kämpfen.""",

    544: """Magtheridons Hort: Eine einzelne brutale Kammer unter der Höllenfeuerzitadelle,
in der der Grubenlord Magtheridon angekettet ist. Kanalisierer halten sein
Gefängnis aufrecht, während Höllenfeuerenergie durch den Raum pulsiert. Der
Raum ist bedrückend heiß und stinkt nach Dämonenblut und Schwefel. Eine
geradlinige, doch bestrafende Begegnung - ein gewaltiger Dämon, ein tödlicher
Raum, kein Raum für Fehler.""",

    548: """Serpentschrein-Höhle: Lady Vashjs unterwasserisches Bollwerk im
Rollfangreservoir, ein geflutetes Schloss verdorbener Schönheit. Naga,
Flutwandler und kolossale Hydren bewachen Kammern, in denen Wasserfälle in
leuchtende Becken stürzen. Brücken überspannen unterirdische Seen, und die
tieferen Kammern pulsieren mit den verdorbenen Wassern der Zangarmarschen.
Elegante Naga-Architektur trifft auf die rohe Kraft eines unterirdischen
Ozeans.""",

    550: """Sturmfeste - Das Auge: Kael'thas Sonnenläufers gefangene Naaru-Festung, eine
kristalline Zitadelle, schwebend über dem Nethersturm. Blutelfische Berater,
arkane Konstrukte und Leerwesen bewachen Kammern aus schimmerndem
Draenei-Kristall. Die Technologie ist atemberaubend fremdartig und schön,
umfunktioniert von verzweifelten Elfen, die ihre Magiesucht stillen. Der
Ausblick auf den zerschmetterten Nethersturm von den Plattformen aus ist
gleichermaßen atemberaubend und beängstigend.""",

    564: """Der Schwarze Tempel: Illidan Sturmgrimms Festung im Schattenmondtal, ein
gewaltiger Draenei-Tempel, verdorben durch dämonische Besetzung. Teufelsorks,
Dämonen, Naga und Blutelfen dienen dem Verräter durch weitläufige Innenhöfe,
Abwassersysteme und große Hallen. Die ursprüngliche Schönheit des Tempels ist
von teuflischer Verderbnis vernarbt - zerbrochene heilige Symbole, geschändete
Altäre und grünes Feuer, wo einst Licht war. Der Höhepunkt der Geschichte
Outlands, endend an Illidans Thron.""",

    565: """Gruuls Hort: Ein rauer Höhlenkomplex im Schergrat, Heimat des Gronn-Vaters
Gruul des Drachentöters. Oger-Diener und Gruuls monströse Söhne bewachen den
Zugang zu seiner Kammer, übersät mit Drachenknochen und Trophäen. Die Höhlen
wirken urtümlich und brutal - keine Architektur, keine Verzierung, nur roher
Fels, geformt von den Fäusten von Riesen.""",

    580: """Sonnenbrunnenplateau: Der letzte Raid des Brennenden Kreuzzugs, angesiedelt im
Herzen des wiederhergestellten Sonnenbrunnens auf der Insel von Quel'Danas.
Die Brennende Legion versucht, Kil'jaeden durch den Sonnenbrunnen selbst zu
beschwören. Makellose Elfen-Architektur von atemberaubender Schönheit umrahmt
einen verzweifelten Kampf gegen die mächtigsten Dämonen in der Armee der
Legion. Das heilige Licht des Sonnenbrunnens prallt in jeder Kammer mit
dämonischer Dunkelheit zusammen.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Feste Utgarde: Eine Vrykul-Festung an den Küsten des Heulenden Fjords, der
erste Vorgeschmack auf die Gefahren Nordends. Von Wikingern inspirierte Hallen
aus dunklem Stein und Eisen, erleuchtet von lodernden Feuerstellen und
geschmückt mit Drachenschädeln. Vrykul-Krieger, Protodrachen-Betreuer und ihre
untoten Diener füllen die großen Hallen. Der Dungeon fühlt sich an wie das
Überfallen einer nordischen Langhalle - kalt, brutal und tief in
Kriegerkultur verwurzelt.""",

    575: """Utgarde-Gipfel: Die oberen Höhen der Feste Utgarde, wo der Vrykul-König
Ymiron von seinem vereisten Thron regiert. Trophäenhallen, Adlervolieren und
Ritualkammern ragen über den Fjord empor. Die Architektur wird grandioser und
bedrohlicher, je höher man aufsteigt, bis hin zu Ymirons frostbedecktem
Thronsaal. Wind heult durch offene Zinnen, und der Ausblick auf die vereiste
Landschaft darunter ist schwindelerregend.""",

    576: """Der Nexus: Die kristallinen Höhlen unter Kaltenau, Bollwerk des Krieges der
Blauen Drachenschwinge gegen sterbliche Magie. Vereiste Höhlen von
unmöglicher Schönheit enthalten arkane Anomalien, wahnsinnige Magierjäger und
Risse in der Realität. Kristallisierte Drachen hängen mitten im Flug erstarrt.
Der Dungeon schimmert von instabiler arkaner Energie - Blau, Violett und Weiß
brechen sich in jede Richtung durch Eis und Kristall.""",

    578: """Der Oculus: Die oberen Ringe des Nexus, eine Reihe schwebender Plattformen,
verbunden durch magische Brücken hoch über dem Ley-Linien-Nexus. Spieler
reiten Drachen, um zwischen den Ringsegmenten zu navigieren, während sie gegen
Malygos' Streitkräfte kämpfen. Die Leere erstreckt sich darunter, arkane
Energie knistert zwischen den Plattformen, und der Schwindel ist real. Ein
Dungeon, der sich anfühlt, als fliege man durch einen magischen Sturm am Rande
der Realität.""",

    595: """Die Läuterung Stratholmes: Eine Instanz der Höhlen der Zeit, angesiedelt
während Arthas' schicksalhafter Läuterung der verseuchten Stadt. Die Straßen
Stratholmes sind intakt, aber dem Untergang geweiht - Bürger verwandeln sich
vor euren Augen in Untote, und Arthas ordnet grimmig ihren Tod an, bevor die
Verwandlung geschieht. Der Dungeon ist einzigartig verstörend, weil ihr dabei
helft, die Gräueltat zu begehen, die Arthas' Fall einleitet. Die dunkelste
Stunde der Geschichte, wiedererlebt.""",

    599: """Hallen des Steins: Eine Titananlage in den Sturmgipfeln, Teil des gewaltigen
Ulduar-Komplexes. Steinerne Gänge von geometrischer Perfektion beherbergen
fehlfunktionierende Titankonstrukte, Eisenzwerge und uralte
Verteidigungssysteme. Das Tribunal der Zeitalter bewahrt Aufzeichnungen der
Schöpfung selbst. Der Dungeon wirkt gelehrt und uralt - ein Museum, dessen
Exponate sich wehren und dessen gespeicherte Geschichte Zivilisationen
zerschmettern könnte.""",

    600: """Festung Drak'Tharon: Eine von der Geißel befallene Trollfestung an der Grenze
zwischen den Grizzlyhügeln und Zul'Drak. Die Geißel hat die toten Trolle
erweckt und ihre Dinosaurierbestien verdorben, wodurch eine unheilige
Verschmelzung aus Trollkultur und nekromantischer Macht entstand. Skelett-
Echsen, Zombie-Trolle und der Lich Novos der Rufer füllen die verfallenden
Hallen. Trollarchitektur, zerbröckelnd unter dem Gewicht der Untotheit.""",

    601: """Azjol-Nerub: Das zerstörte Nerubianer-Königreich unter Nordend, ein von
Spinnweben verstopfter, vertikaler Abstieg durch das Spinnenimperium.
Nerubianer-Architektur aus Seide und Chitin erstreckt sich über gewaltige
unterirdische Schluchten. Untote Nerubianer dienen der Geißel, während die
Lebenden verzweifelt kämpfen. Der Dungeon lässt euch immer tiefer durch
einstürzende Böden fallen - klaustrophobisch, fremdartig und wimmelnd von
Dingen, die nicht existieren sollten.""",

    602: """Hallen des Blitzes: Ein Titanenschmiede-Komplex in Ulduar, knisternd vor
elektrischer Energie. Eisenzwerge, Sturmriesen und runische Konstrukte
bewachen Gänge aus glänzendem Metall und peitschenden Blitzen. Loken, der
verdorbene Titanenwächter, wartet in der tiefsten Kammer. Jede Oberfläche
summt vor Macht, Funken tanzen über die Wände, und der Donner der Schmiede
ist konstant und ohrenbetäubend.""",

    604: """Gundrak: Ein Drakkari-Trolltempel in Zul'Drak, wo die Trolle ihre eigenen
Tiergötter opfern, um ihren Krieg gegen die Geißel zu befeuern. Altäre rinnen
von göttlichem Blut, während Schlangen-, Mammut- und Nashorngeister
verzehrt werden. Der Tempel ist gewaltig und urtümlich - behauener Stein,
Ritualbecken und die verzweifelte Energie einer sterbenden Zivilisation, die
ihre eigenen Götter zum Überleben verbrennt.""",

    608: """Violette Feste: Ein magisches Gefängnis unter Dalaran, in dem der Kirin Tor
die gefährlichsten Kreaturen Nordends einsperrt. Agenten der Blauen
Drachenschwinge stürmen das Gefängnis durch Portale und befreien wellenweise
Insassen. Die Architektur ist elegantes Dalaran-Violett und -Silber, doch die
Insassen sind albtraumhaft. Ein Tower-Defense-Szenario in einem
Magierverlies - arkane Schutzzeichen kämpfen gegen das Chaos an.""",

    619: """Ahn'kahet: Das Alte Königreich: Die tiefsten Bereiche von Azjol-Nerub, wo
Gesichtslose dem alten Gott Yogg-Saron dienen. Die Architektur wandelt sich von
nerubianisch zu etwas weit Älterem und Fremdartigerem - organische Wände
pulsieren, die Realität verzerrt sich, und Wahnsinnseffekte greifen den
Verstand an. Vergessene, Zauberschleuderer und der Herold Volazj lauern in
Kammern, die jeder Geometrie trotzen. Der beunruhigendste Dungeon in
Nordend.""",

    632: """Schmiede der Seelen: Der erste von drei Dungeons der Eiskronenzitadelle, eine
gewaltige seelenmahlende Maschine, in der der Lichkönig die Toten verarbeitet.
Ströme gequälter Seelen fließen durch eiserne Maschinerie, spektrale Schmiede
hämmern auf Ambosse des Leidens, und der Verschlinger der Seelen bewacht die
Schmiede. Das Schreien hört niemals auf. Ein industrieller Albtraum, gespeist
von ewiger Qual.""",

    650: """Prüfung des Champions: Eine grandiose Turnierarena unter dem Argentumkoloss
in Eiskrone, wo Champions der Allianz und der Horde ihren Wert beweisen.
Berittenes Turnierstechen, Champion-Duelle und ein finaler Hinterhalt durch den
Schwarzen Ritter spielen sich auf dem Turniergelände ab. Die Atmosphäre ist
festlich und wettkämpferisch, bis die Untoten die Feier stören. Prunk und
Spektakel mit einer dunklen Wendung.""",

    658: """Die Grube von Saron: Eine brutale Sklavenmine in Eiskrone, in der Streitkräfte
der Geißel Gefangene zu Tode arbeiten lassen, um Saroniterz zu fördern. Die
Grube liegt offen unter dem gefrorenen Himmel, mit gewaltigen Ketten,
Abbauplattformen und Saronitvorkommen überall. Schmiedemeister Kaltfrost
schleudert Felsbrocken, während Tyrannus auf seinem Frostbrut-Drachen darüber
patrouilliert. Hoffnungslosigkeit und Grausamkeit, destilliert in gefrorenem
Stein und dunklem Metall.""",

    668: """Hallen der Reflexion: Die von Geistern heimgesuchten Gefrorenen Hallen der
Eiskronenzitadelle, wo Echos von Frostgrams Opfern um die Kammer der Klinge
verweilen. Der Lichkönig selbst verfolgt euch durch einstürzende Gänge,
während Wellen von Geistern angreifen. Die Hallen sind makelloses Eis und
dunkles Saronit, und der Schrecken ist real - ihr könnt nicht gegen ihn
kämpfen, nur fliehen. Der erzählerisch intensivste Dungeon des Spiels, eine
verzweifelte Flucht vor unausweichlichem Verderben.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas: Die schwebende Nekropole des Erzlichs Kel'Thuzad, schwebend über
dem Drachenöde. Vier Flügel thematischer Schrecken - der Spinnentierflügel
riesiger Spinnen, der Seuchenflügel von Krankheit und Abscheulichkeiten, der
Militärflügel der Todesritter-Kommandanten und der Konstruktflügel der
Fleischgolems. Gotische Architektur aus dunklem Stein und grünem Schleim,
mit der kalten Präzision untoter militärischer Organisation. Das Meisterwerk
des Todes der Geißel.""",

    603: """Ulduar: Eine Titanen-Stadtfestung in den Sturmgipfeln, der grandioseste Raid
in Nordend. Gewaltige Hallen aus glänzendem Metall und Stein beherbergen die
verdorbenen Titanenwächter und ihre Diener, mit dem alten Gott Yogg-Saron
eingesperrt im tiefsten Gewölbe. Das Ausmaß ist überwältigend -
Fahrzeugschlachten an den Toren, ein Observatorium, offen zum Kosmos, Gärten
von unirdischer Schönheit und ein Abstieg in den Wahnsinn selbst. Uralt,
prächtig und schrecklich.""",

    615: """Obsidiansanktum: Eine vulkanische Kammer unter dem Drachenhorttempel, wo
Sartharion Zwielichtdracheneier bewacht. Lavaflüsse teilen die
Obsidianplattformen, und drei Zwielichtdrachen-Leutnants patrouillieren ihre
eigenen Inseln. Die Kammer glüht orange und rot, Hitzeflimmern verzerrt die
Luft, und der Verrat der schwarzen Drachenschwinge liegt offen zutage. Eine
geradlinige Arena aus Feuer und Schuppen.""",

    616: """Auge der Ewigkeit: Malygos' persönliches Heiligtum an der Spitze des Nexus
über Kaltenau, eine Plattform, schwebend in roher Ley-Energie. Es gibt keinen
Boden, keine Wände - nur eine Scheibe magischer Kraft über einer Leere
wirbelnder blauer und violetter Arkanmagie. Der Zauberweber greift mit der
vollen Macht der Blauen Drachenschwinge an. Der Raid fühlt sich
außerweltlich an - der Kampf gegen einen Drachenaspekt im Herzen von Azeroths
arkanem Sturm.""",

    624: """Gewölbe von Archavon: Ein Titanengewölbe unter der Festung Wintergrasp,
zugänglich nur für die Fraktion, die die Zone kontrolliert. Steinriesen und
elementare Konstrukte bewachen die Kammern in einer geradlinigen Abfolge von
Bosskämpfen. Die Architektur ist zweckmäßiges Titanendesign - funktional,
gewaltig und schmucklos. Eine Belohnung für den PvP-Sieg, schnell und brutal.""",

    631: """Eiskronenzitadelle: Der Thron des Lichkönigs, der Höhepunkt des Zorns des
Lichkönigs. Eine aufragende Festung aus Saronit und Eis, aufsteigend aus dem
Herzen von Eiskrone. Jeder Flügel steigert den Schrecken - von den untoten
Armeen der Unteren Spitze über die Seuchenwerke, die Purpurne Halle und die
Frostschwingenhallen bis hin zum Gefrorenen Thron selbst. Die Architektur ist
bedrückend, schön in ihrer Grausamkeit und darauf ausgelegt, Hoffnung zu
brechen. Dies ist das Ende.""",

    649: """Prüfung des Kreuzfahrers: Der Argentumkoloss in Eiskrone, eine Turnierarena,
die in die Erde hinabsinkt, wenn der Boden in eine unterirdische
Nerubianer-Höhle einbricht. Die obere Ebene besteht aus leuchtenden Bannern
und jubelnden Menschenmengen; die untere Ebene ist chitinöser Schrecken und
Anub'araks Reich. Der Kontrast zwischen festlichem Wettkampf oben und uraltem
Grauen unten prägt das gesamte Erlebnis.""",

    724: """Rubinsanktum: Eine Kammer unter dem Drachenhorttempel, in der die
Zwielichtdrachenschwinge das Heiligtum der roten Drachen überfallen hat.
Halion, der Zwielichtzerstörer, wechselt zwischen der physischen Ebene und der
Schattenebene. Die Kammer wechselt zwischen warmem Rubinlicht und kaltem
violettem Schatten. Der letzte Raid vor dem Kataklysmus - eine kurze,
unheilvolle Warnung vor der kommenden Zerstörung.""",
}
