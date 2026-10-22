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
    4080: "Insel von Quel'Danas", 4298: "Pestländer: Die Scharlachrote Enklave", 4197: "Tausendwintersee", 4395: "Dalaran",
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
    # Eastern Kingdoms - Khaz Modan
    # -------------------------------------------------------------------------
    1: """Dun Morogh: Verschneites Hochland zwischen den Gipfeln von Khaz Modan, Heimat der Zwerge von Eisenschmiede und der vertriebenen Gnome von Gnomeregan. Schnee bedeckt die felsigen Hügel, gefrorene Seen glitzern unter einer blassen Sonne, und stille Kiefernwälder stehen unter schweren Verwehungen. Die Luft riecht nach Frost, Holzrauch und Schmiedefeuer. Die Zwergendörfer halten ihre Feuer gegen die endlose Kälte am Brennen, während Troggs, Frosttrolle, Wölfe und Bären die Wildnis gefährlich machen.""",

    1537: """Eisenschmiede: Die uralte Hauptstadt der Zwerge, eine gewaltige Stadt im Herzen eines Berges in Dun Morogh. Fackelbeleuchtete Hallen und steinerne Gänge umgeben die Große Schmiede, die von Strömen geschmolzenen Gesteins gespeist wird und an der König Magni Bronzebart vom Hohen Sitz aus über Khaz Modan herrscht. Die vertriebenen Gnome von Gnomeregan leben in der Tüftlerstadt, die Forscherliga sucht in der Halle der Forscher nach den Geheimnissen der Zwergenherkunft, und die Tiefenbahn fährt unter der Erde nach Sturmwind. Die Luft ist warm, rauchig und erfüllt von Hämmern und Gelächter.""",

    38: """Loch Modan: Raue Hügel und grüne Täler im östlichen Khaz Modan rund um einen großen See, den ein gewaltiger Staudamm hält, ein Meisterwerk zwergischer Baukunst. Das Klima ist kühl und feucht, mit Nebel über dem Wasser, häufigem Regen und frostigen Morgen. Die Zwerge fischen im See, schürfen in den Klippen und schlagen Holz rund um die Siedlung Thelsamar. Zerbrochene Belagerungsmaschinen der Horde aus dem Zweiten Krieg rosten noch auf den Inseln. Troggs verseuchen die Täler, Kobolde halten eine Mine, Oger eine Festung im Nordosten, und Dunkeleisenzwerge bedrohen den Damm.""",

    330: """Thandolübergang: Eine gewaltige Zwergenbrücke über die tiefe Meerenge zwischen Khaz Modan und Lordaeron, die das Sumpfland mit dem Arathihochland verbindet. Jahrhundertelang zogen Heere und Handel über sie zwischen den Zwergen und den nördlichen Menschenreichen. Die Geißel beschädigte sie im Dritten Krieg, und ein Angriff der Dunkeleisenzwerge hat einen ihrer Bögen fast zerstört, sodass große Teile nun unter den Wellen liegen. Sie bleibt der einzige Landweg zwischen Lordaeron und dem Süden. Wind und Gischt peitschen über ihre Höhen.""",

    269: """Dun Algaz: Ein durch die Berge getriebener Pass und eine alte Zwergenfestung zwischen Loch Modan und dem Sumpfland, im Süden vom Tor von Algaz bewacht. Im Zweiten Krieg war er die letzte Bastion der Horde in Khaz Modan. Er ist noch immer die Hauptstraße zwischen den Zwergenlanden und dem Hafen von Menethil, doch Orcs des Drachenmalklans haben den Außenposten in der Mitte des Passes überrannt, und die zwergischen Bergwächter halten nur noch den oberen Tunnel. Die Tunnel sind dunkel, kalt und hallend, und der Weg hindurch ist gefährlich geworden.""",

    11: """Sumpfland: Ein weites, kaltes Marschland im nördlichen Khaz Modan, durchzogen von Flüssen, Mooren und schilfverstopften Kanälen zwischen den Bergen und der Bucht von Baradin. Nebel bedeckt den Boden, der Himmel ist einheitlich grau, und es regnet oft. Einst standen hier Festungen der Wildhämmer, doch das Land wurde im Zweiten und Dritten Krieg verwüstet, als der Drachenmalklan Grim Batol hielt und die Drachenkönigin Alexstrasza versklavte. Der Hafen von Menethil an der Westküste verbindet Khaz Modan auf dem Seeweg mit Kalimdor und Nordend. Reste des Drachenmalklans, Dunkeleisenzwerge, Gnolle, Murlocs, Raptoren und Krokilisken machen die Sümpfe gefährlich.""",

    3: """Ödland: Eine sonnenverbrannte Einöde aus rissiger roter Erde, Tafelbergen und gewundenen Schluchten im südlichen Khaz Modan. Wasser ist knapp, die Tage sind glühend heiß, und Staubstürme fegen über die kahlen Ebenen, wo nur Kojoten, Geier, Skorpide, Basilisken und Felselementare überleben. Im Norden liegt Uldaman, ein Gewölbe der Titanen, das zwergische Grabungen freigelegt haben und das nun die erweckten Troggs verteidigen. Dunkeleisenzwerge graben dort für ihren Herrn Ragnaros, Oger streifen umher, schwarze Drachen nisten in den östlichen Schluchten, und die Horde hält die Festung Kargath.""",

    51: """Sengende Schlucht: Eine vulkanische Einöde aus Asche, Schlacke und Lava zwischen dem Ödland und dem Schwarzfels, einst Teil des grünen Rotkammgebirges, bis Thaurissans Beschwörung des Ragnaros das Land zerriss. Die Luft ist heiß, trocken und voller Rauch, und Feuerelementare streifen zwischen verbranntem Gestein umher. Die Dunkeleisenzwerge beherrschen die Schlucht und lassen Gefangene in der gewaltigen Grube des Kessels schuften. An ihrem Nordrand halten die Handwerker der Thoriumbruderschaft, die sich von ihrem Klan losgesagt haben, die neutrale Siedlung Thoriumspitze.""",

    25: """Der Schwarzfels: Ein hoch aufragender, noch tätiger Vulkan zwischen der Sengenden Schlucht und der Brennenden Steppe, entstanden, als der Dunkeleisen-Zauberthan Thaurissan den Feuerfürsten Ragnaros beschwor. Die Dunkeleisenzwerge schlugen eine gewaltige Stadt in seine Tiefen, und darüber erhebt sich die Schwarzfelsspitze. Der Berg ist erbittert umkämpft: Ragnaros und seine Dunkeleisendiener herrschen über die Tiefen und den geschmolzenen Kern, während der schwarze Drache Nefarian von den Höhen der Spitze aus Orcs, Oger und Drachkin befehligt. Ketten und Plattformen überspannen eine Halle aus geschmolzenem Gestein, und Hitze, Rauch und Grollen hören nie auf.""",

    46: """Brennende Steppe: Ein verbranntes vulkanisches Land südlich des Schwarzfels, der einzige Landweg zwischen Sturmwind und Khaz Modan. Verkohlte Erde, schroffe Hügel und Lavaströme liegen unter einem vom Berg rot glühenden Himmel, und heiße, trockene Luft trägt Asche heran. Von Sturmwind aufgegeben, wird die Steppe von den Dienern des schwarzen Drachenschwarms und den Handlangern des Ragnaros gehalten: Schwarzfelsorcs, die Thrall ablehnen, Oger, schwarze Drachen und Dunkeleisenzwerge. Hier fiel Anduin Lothar am Ende des Zweiten Krieges. Die Allianz klammert sich an Morgans Wacht.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Azeroth
    # -------------------------------------------------------------------------
    12: """Wald von Elwynn: Das grüne Herz des Königreichs Sturmwind, ein mildes Land aus Eichen- und Kiefernwäldern, Wiesen, Seen und Höfen südlich der Hauptstadt, mit dem Dorf Goldhain in der Mitte und der Abtei von Nordhain in einem Tal im Norden. Die Horde verwüstete ihn im Ersten Krieg, und die unbezahlten Steinmetze, die Sturmwind wiederaufbauten, wurden zur Defiasbruderschaft. Der Frieden ist brüchig: Banditen der Defias besetzen Höfe, Kobolde verseuchen die Minen, Gnolle lagern an der Westgrenze und Murlocs bevölkern die Seen, während die Wache von fernen Kriegen ausgezehrt ist.""",

    1519: """Sturmwind: Die Hauptstadt des Königreichs Sturmwind und die prächtigste Menschenstadt der Welt, nach dem Ersten Krieg mit weißen Steinmauern, blau gedeckten Türmen und durch Kanäle getrennten Vierteln wiederaufgebaut. König Varian Wrynn herrscht nach langer Abwesenheit von der Burg Sturmwind aus. Die Kathedrale des Lichts ist das Herz des Glaubens an das Heilige Licht, und die Stadt umfasst das Handelsdistrikt, die Altstadt mit SI:7, das Magierviertel, das Zwergendistrikt mit der Tiefenbahn nach Eisenschmiede und den Park mit seinem Mondbrunnen. Menschen, Zwerge, Gnome, Nachtelfen und Draenei gehen durch ihre Straßen.""",

    40: """Westfall: Hügeliges Ackerland an der Westküste von Sturmwind, einst die Kornkammer des Königreichs, nun verfallen. Die Felder liegen brach, das Gras ist gelb, und der Seewind trägt Staub über verlassene Höfe. Die Defiasbruderschaft, Gesetzlose aus den unbezahlten Steinmetzen Sturmwinds, hat viele Bauern vertrieben, hält das Geisterdorf Mondbruch und hat verwilderte Erntewächter auf die Felder losgelassen. Gnolle überfallen das Land vom Süden aus, Murlocs streifen die Küste entlang. Die Volksmiliz hält die Späherkuppe, und die Bauern fühlen sich von der Krone vergessen.""",

    44: """Rotkammgebirge: Rötliche Gipfel, hohe Ulmen und reißende Flüsse östlich des Waldes von Elwynn, rund um den blauen Immerruhsee und die alte Siedlung Seenhain. Ihre zähen, selbstverwalteten Bewohner beliefern Sturmwind mit Holz, Fisch und Getreide. Das Gebirge wurde vor langer Zeit durch die Beschwörung des Ragnaros zerrissen. Heute ist es Grenzland: Schwarzfelsorcs aus der Brennenden Steppe haben die Feste Steinwacht genommen und lagern in den Hügeln, Gnolle beanspruchen die Schluchten, Murlocs verseuchen den See und schwarze Welpen streifen über die Höhen. Seenhain ist auf seine kleine Wache angewiesen.""",

    10: """Dämmerwald: Ein dunkler, verfluchter Wald südlich von Elwynn, einst hell und schön, nun von einer unnatürlichen, ewigen Dämmerung verschlungen. Schwarzer Nebel hängt zwischen verkrümmten Bäumen, und die Luft ist kalt und riecht nach Fäulnis. Manche geben dem Bösen von Karazhan die Schuld, andere einem uralten Artefakt und den Worgen, die mit dem Fluch kamen. Die Toten erheben sich aus den Friedhöfen, Worgen und Riesenspinnen streifen durch den Wald, und aus der Nacht sollen die Schwarzen Reiter kommen. Die sturen Bewohner von Dunkelhain, bewacht von der Nachtwache, fühlen sich von Sturmwind im Stich gelassen.""",

    41: """Gebirgspass der Totenwinde: Eine öde, verfluchte Schlucht zwischen dem Dämmerwald und den Sümpfen des Elends, in der die Bäume kahl und versteinert stehen, das Gras grau ist und ein fauliger, heulender Wind nie verstummt. Ständig ziehen Stürme auf, und Blitze schlagen in die kahlen Felsen. Im Süden steht Karazhan, der Turm Medivhs, des letzten Wächters von Tirisfal, der das Dunkle Portal öffnete; noch immer sickert böse Magie aus ihm und saugt dem Land das Leben aus. Oger, ruhelose Geister und Aasvögel bevölkern den Pass, und man flüstert, eine neue dunkle Macht habe den Turm beansprucht.""",

    8: """Sümpfe des Elends: Ein stehendes, nebelverhangenes Sumpfland aus Mooren, Trauerweiden und brackigen Tümpeln östlich des Passes der Totenwinde, einst der nördliche Teil des Schwarzen Morasts. Die Luft ist feucht und schwer, und im Schilf lauern Krokilisken, Jaguare, Spinnen und Sumpfbestien. Die Atal'ai errichteten hier einen Tempel für den Blutgott Hakkar, und der Drachenaspekt Ysera versenkte ihn unter dem größten Moor, wo ihre Drachen noch immer Wache halten. Die Horde hält das wiederaufgebaute Steinard. Verlorene und Zerschlagene, auf Azeroth gestrandete Draenei, leben im Sumpf, und Murlocs bevölkern die Küste.""",

    4: """Verwüstete Lande: Eine verbrannte Wüste aus karminrotem Lehm südlich der Sümpfe des Elends, einst der südliche Schwarze Morast, verzerrt von der Magie des Dunklen Portals. Blitze schlagen oft ein, nichts Fruchtbares wächst, die Tage sind heiß und die Nächte bitterkalt. Mutierte Basilisken, Skorpide und Hyänen streifen umher. Das Dunkle Portal steht in einem riesigen Krater im Südosten, wieder offen nach der Scherbenwelt, und Heere der Allianz und der Horde bewachen seinen Fuß. Burg Nethergarde, von Khadgar gegründet, wacht im Norden; Oger und Reste der Legion lauern in der Einöde.""",

    33: """Schlingendorntal: Ein riesiger, dampfender Dschungel an der Südspitze der Östlichen Königreiche, voller gewaltiger Bäume, Lianen und dornigem Unterholz, bewohnt von Tigern, Panthern, Raptoren, Gorillas und Krokilisken. Es war das Herz des Trollimperiums der Gurubashi, bis die Beschwörung Hakkars es zerriss; heute bedecken Ruinen das Land, die Stämme der Blutskalpe und Schädelspalter bekämpfen Fremde, und Zul'Gurub ist erneut unter Hakkars Bann geraten. Goblins, Piraten, Oger, Naga und Rebellen wollen ihren Anteil. Beutebucht ist der geschäftige neutrale Hafen am Südkap, und die Horde hält Grom'gol an der Küste.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Lordaeron
    # -------------------------------------------------------------------------
    85: """Tirisfal: Hügelige Wälder an der Nordküste Lordaerons, einst das Herz des Menschenreiches und heute die Heimat der Verlassenen unter Sylvanas Windläufer. Der Himmel ist düster und grünlich getönt, kalter Nebel zieht über verlassene Höfe, stille Seen und zerstörte Mühlen, doch das Land bewahrt eine wehmütige Schönheit, besonders rund um das Dorf Brill. Hier verbreitete Kel'Thuzad zuerst die Seuche, und hier erschlug Arthas seinen Vater. Unter der zerstörten Hauptstadt liegt Unterstadt. Die Geißel spukt noch auf den Höfen, der Scharlachrote Kreuzzug hält sein Kloster, und das Bollwerk blickt auf die Pestländer.""",

    1497: """Unterstadt: Die Hauptstadt der Verlassenen, eine riesige unterirdische Stadt unter den Ruinen der Königsstadt Lordaerons, entstanden aus den alten königlichen Grüften, Kerkern und Abwasserkanälen. Arthas begann mit dem Ausbau, Sylvanas vollendete ihn, nachdem sie die Schreckenslords vertrieben hatte. Die Stadt ist dunkel, kalt und verwinkelt, in Ringen um das Handelsviertel angelegt, mit Magier-, Schurken- und Kriegsviertel und dem Apothekarium, in dem die Königliche Apothekervereinigung Seuchen und Gifte braut. Grüner Schlamm fließt in den Kanälen, große Aufzüge bringen Reisende zu den Ruinen hinauf, und Sylvanas herrscht aus dem Königsviertel.""",

    130: """Silberwald: Ein uralter Wald hoher, silberrindiger Kiefern entlang der Westküste Lordaerons, verwunschen und kränklich, seit die Geißel im Dritten Krieg mit Feuer und Schwert hindurchzog. Geisterhafte Nebel treiben zwischen den Bäumen, und niedergebrannte Höfe und verlassene Minen übersäen das Land. Die Verlassenen halten den Norden vom Grabmal aus und bekämpfen seuchenverseuchte Gnolle. Im Süden bewachen Magier Dalarans ein Mühlendorf, die Bewohner von Pyrewood tragen einen Fluch, der sie nachts zu Worgen macht, Arugal brütet in Burg Schattenfang, und der Graumähnenwall schließt Gilneas ab.""",

    170: """Lordamere-See: Einer der größten Seen der Östlichen Königreiche, eine weite Fläche kalten, grauen Wassers im Herzen des gefallenen Lordaeron, an dessen Nordufer einst seine Hauptstadt stand. Rund um ihn lagen Lordaeron, Dalaran und Alterac, die großen Reiche der alten Allianz. Heute trennt er die Länder der Verlassenen vom Alteracgebirge. Die Insel Fenris mit ihrer düsteren Festung liegt in der Mitte, die Morgendämmerungsinseln bilden den Rand eines uralten Vulkans, und eine alte Seuche hat das Wasser seltsam leblos hinterlassen. Oft hängt Nebel über dem See, und Murlocs lagern an seinen Ufern.""",

    267: """Vorgebirge des Hügellands: Grüne Hügel, Wiesen, Kiefernhaine und Ackerland im Süden Lordaerons, die am besten erhaltene Gegend des gefallenen Königreichs. Ein Fluss aus dem Darrowmere-See durchzieht die Hügel, und kleine Inseln säumen die Südküste. Es ist aber auch eines der blutigsten Schlachtfelder Azeroths: Hier wurde die erste Schlacht des Zweiten Krieges geschlagen, und in Burg Durnholde lagen die Internierungslager der Orcs, in denen der junge Thrall als Sklave lebte. Die Menschenstadt Süderstade und die Verlassenen von Tarrens Mühle führen einen erbitterten Kampf, während das Syndikat die Ruinen von Durnholde hält.""",

    36: """Alteracgebirge: Schneebedeckte Gipfel nördlich des Hügellands, einst das Menschenreich Alterac, das die Allianz zerstörte, nachdem Lord Perenolde es an die Horde verraten hatte. Die vertriebenen Adligen gründeten das Syndikat, das das Hochland und Lager über dem Hügelland hält, während Oger die Ruinen der Stadt Alterac besetzt haben. Am Ufer des Lordamere-Sees liegt der Krater, in dem Dalaran stand, bevor es nach Nordend flog. In einem verborgenen Tal kämpfen die Frostwolforcs gegen die Zwerge der Sturmlanzenexpedition, und das geheimnisvolle Anwesen Rabenholdt versteckt sich zwischen den Gipfeln. Yetis und Berglöwen streifen durch den Schnee.""",

    45: """Arathihochland: Graues, windgepeitschtes Hochland aus wogendem Gras und Felsen im Südosten Lordaerons, die Wiege der menschlichen Zivilisation, wo Thoradin das Imperium von Arathor gründete und Menschen und Hochelfen sich zuerst gegen die Amani verbündeten. Später entstand hier das Königreich Stromgarde, doch das Syndikat und Oger eroberten seine Hauptstadt, und sein Heer hält nun die Zuflucht. Die Horde hält Hammerfall, das alte Internierungslager. Oger, Waldtrolle, Raptoren und Kobolde streifen umher, und uralte Steinkreise sollen etwas Gefangenes binden.""",

    293: """Thoradinswall: Eine gewaltige Steinmauer an der Grenze zwischen dem Hügelland und dem Arathihochland, in alter Zeit von König Thoradin, dem Gründer des Imperiums von Arathor, gegen die Amanitrolle errichtet. Später schützte sie Stromgarde vor der vorrückenden Geißel. Nun ist sie eingestürzt und klafft auf, ihr großes Tor steht offen, und ganze Abschnitte sind zu Schutt zerfallen. Die Hauptstraße zwischen Hügelland und Arathi führt in ihrem Schatten hindurch, eine Erinnerung an den Ruhm des ersten Menschenreiches und daran, wie tief seine Erben gefallen sind.""",

    47: """Hinterland: Ein wildes, bergiges Land aus üppigen Wäldern, tiefen Tälern und steilen Klippen im Norden der Östlichen Königreiche, von der Seuche unberührt und mild im Klima. Es war das Herz des Imperiums der Amani-Waldtrolle, deren riesige Ruinen noch zwischen den Bäumen stehen. Die Wildhammerzwerge unter Hochthan Falstad leben unter freiem Himmel im Nistgipfel, einer Stadt in Gestalt eines Greifenkopfes, und reiten auf wilden Greifen in die Schlacht. Verfeindete Trollstämme halten Jintha'Alor und Shadra'Alor, während der Stamm der Bruchhauer sich der Horde angeschlossen hat. Im Norden ist der Baum von Seradane ein Tor zum Smaragdgrünen Traum.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands, Quel'Thalas and southern isles
    # -------------------------------------------------------------------------
    28: """Westliche Pestländer: Ein verseuchtes Land im Norden Lordaerons, einst die bewaldete Kornkammer des Nordens. Hier vergifteten Kel'Thuzad und der Kult der Verdammten das Getreide von Andorhal mit der Seuche des Untodes. Ein rauchiger grauer Nebel hängt über dem Land, die Bäume tragen geschwulstartige Wucherungen, und die überlebenden Tiere sind krank und wild. Untote verseuchen Andorhal, die Kesselfelder und die Friedhöfe, und die Geißel bildet in der Scholomance auf der Insel Caer Darrow Nekromanten aus. Der Scharlachrote Kreuzzug hält Herdweiler, die Argentumdämmerung das Lager Kühlwind, und das Grabmal Uthers des Lichtbringers ist einer der wenigen friedlichen Orte.""",

    139: """Östliche Pestländer: Die am stärksten verwüstete Hälfte der Pestländer, einst ein Land der Höfe und Dörfer, regiert von Stratholme, wo der Orden der Silbernen Hand gegründet wurde und Arthas seine Säuberung durchführte. Die Herrschaft der Geißel ist hier nahezu vollständig: Der Boden ist braun und krank, Bäume sind zu riesigen Pilzen verdreht, und orangefarbene und grüne Nebel erfüllen die Luft. Stratholme brennt als Hauptstadt der Geißel in Lordaeron, und der Pestwald ist voller Zikkurate. Der Scharlachrote Kreuzzug hält Tyrs Hand, die Argentumdämmerung hält die Kapelle des Hoffnungsvollen Lichts für alle offen, die gegen die Geißel kämpfen, und im Osten schwebt Acherus, die Heimat der Todesritter.""",

    3430: """Immersangwald: Der verzauberte Wald im Herzen von Quel'Thalas, erstarrt in ewigem Herbst unter goldenem und purpurnem Laub, übersät mit anmutigen Türmen, schwebenden Spitzen und arkanen Kristallen. Im Dritten Krieg führte Arthas die Geißel durch das Königreich zum Sonnenbrunnen und hinterließ die Todesschneise, einen Streifen leblosen Bodens, der den Wald und Silbermond selbst durchschneidet. Die Überlebenden nannten sich Blutelfen, traten unter Regent-Lord Lor'themar Theron der Horde bei und bauten vieles wieder auf. Doch die Elendigen spuken in den Ruinen, arkane Konstrukte laufen frei herum, Trolle lauern in den Hügeln, und die Runensteine, die die Verderbnis zurückhalten, werden schwächer.""",

    3487: """Silbermond: Die Hauptstadt der Blutelfen im Immersangwald, vor Jahrtausenden gegründet und vielleicht die älteste noch stehende Hauptstadt. Im Dritten Krieg führte Arthas die Geißel durch ihre Tore und tötete den König. Die Blutelfen haben die östliche Hälfte fast in alter Pracht wiederaufgebaut, mit goldenen Türmen, schwebenden Plattformen, magiegeladenen Kristallen an Ketten und üppigen Gärten, während die westliche Hälfte jenseits der Todesschneise noch in Trümmern liegt. Regent-Lord Lor'themar Theron herrscht vom Sonnenwanderturm aus, arkane Wächter patrouillieren in den Straßen, und eine Kugel der Translokation verbindet die Stadt mit Unterstadt.""",

    3433: """Geisterlande: Der südliche Teil von Quel'Thalas, ein düsteres Land verdorrter schwarzer Bäume, trüben Himmels und tödlicher Kälte, verwüstet, als die Geißel zum Sonnenbrunnen zog, und nie erholt. Die Todesschneise beginnt an der Todesfestung, der Zitadelle der Geißel unter dem Verräter Dar'Khan Drathir, der Arthas half, die Verteidigung des Königreichs zu durchbrechen. Die Geister erschlagener Elfen spuken in den zerstörten Dörfern. Blutelfen und ihre verlassenen Verbündeten halten Tristessa und wollen das Land zurückgewinnen, während Amanitrolle nahe Zul'Aman im Osten lauern. Der Thalassische Pass führt durch ein uraltes Elfentor nach Süden zu den Pestländern.""",

    4080: """Insel von Quel'Danas: Eine Insel vor der Nordküste des Immersangwaldes, auf der die Gründer von Quel'Thalas vor siebentausend Jahren den Sonnenbrunnen schufen, eine Quelle gewaltiger Macht. Arthas schändete ihn, um Kel'Thuzad zu erwecken. In jüngerer Zeit wurde die Insel zum Schauplatz eines verzweifelten Kampfes, als Kael'thas Sonnenwanderer und die Brennende Legion den Brunnen als Tor nutzen wollten und die Offensive der Zerschmetterten Sonne aus Aldor und Sehern den Hafen von Sonnenweiten zu ihrer Basis machte. Kampfspuren zeichnen das Land, doch ihre goldenen Wälder, weißen Strände und anmutigen Türme sind noch immer schön, und in ihrem Herzen erhebt sich das Sonnenbrunnenplateau.""",
    4298: """Die Scharlachrote Enklave: Der äußerste Osten der Pestländer, ein Küstenstreifen jenseits von Tyrs Hand, den der Scharlachrote Kreuzzug zu seiner letzten Zuflucht vor der Seuche machte, mit der Stadt Neu-Avalon, den Höfen, Mühlen und der Mine von Havenau, der Kapelle der Purpurflamme und dem Ankerplatz des Königshafens. Lange von der Seuche verschont, ernährten ihre Obstgärten und Felder die Soldaten des Kreuzzugs und die Überlebenden unter seinem Schutz. Über den westlichen Höhen schwebt Acherus, eine gewaltige fliegende Nekropole und die Heimat der Todesritter, und von der kargen Hochebene der Todesbresche unter ihr liegt die ganze Enklave offen vor dem Blick.""",

    408: """Gillijims Insel: Eine abgelegene Dschungelinsel in der Südsee vor der Südküste des Schlingendorntals. Alte Karten verzeichnen sie als ehemalige Trollinsel, doch kaum ein lebender Seefahrer hat ihre Ufer betreten, und sie liegt fern der üblichen Handelswege. Das umgebende Meer ist warm, tief und blau, Heimat von Haien und anderen Geschöpfen des offenen Ozeans, und die Strömungen können Unvorsichtige weit vom Land forttragen. Erzählungen berichten von uralten Trollruinen in ihren Dschungeln, doch ihre Geheimnisse bleiben dem Großteil der Welt verborgen.""",

    409: """Insel des Doktor Lapidis: Eine abgelegene Dschungelinsel in der Südsee vor der Südwestküste des Schlingendorntals. Alte Karten verzeichnen dort bröckelnde Ruinen der alten Dschungeltrolle, doch kaum jemand hat sie seit Menschengedenken besucht, und die Bedeutung ihres Namens kennen nur wenige. Die Gewässer ringsum sind tief, warm und schiffsleer, nur Haie und Geschöpfe der offenen See leben dort. Sie bleibt ein Rätsel, ein dunkler Fleck am Horizont, den die meisten Seefahrer lieber meiden.""",

    # -------------------------------------------------------------------------
    # Kalimdor - North
    # -------------------------------------------------------------------------
    141: """Teldrassil: Ein gewaltiger Weltenbaum, der sich vor dem nordwestlichen Kalimdor aus dem Verhüllten Meer erhebt, so riesig, dass auf seinen Ästen über den Wolken ein Land aus Wäldern, Hügeln und Seen wächst. Erzdruide Fandral Hirschhaupt ließ ihn wachsen, nachdem die Nachtelfen ihre Unsterblichkeit verloren hatten, und ihre Hauptstadt Darnassus steht in seinen westlichen Ästen. Das Land liegt in ewiger violetter Dämmerung, voller uralter Bäume, Mondbrunnen, Irrlichter und Nachtsäbler. Doch die Drachenaspekte segneten den Baum nie, und eine schleichende Verderbnis breitet sich aus: Furbolgs sind verwildert, Holzschlundlinge rasen, und Satyrn lauern in Höhlen. Rut'theran an seinem Fuß ist der Hafen zur Welt.""",

    1657: """Darnassus: Die Hauptstadt der Nachtelfen in den westlichen Ästen Teldrassils, in ewige violette Dämmerung getaucht. Anmutige Terrassen aus lebendem Holz und weißem Stein umgeben einen zentralen See, verbunden durch geschwungene Brücken. Hohepriesterin Tyrande Wisperwind führt die Nachtelfen vom Tempel des Mondes aus, während Erzdruide Fandral Hirschhaupt den Zirkel des Cenarius von der Enklave des Cenarius aus leitet und oft mit ihr uneins ist. Malfurion Sturmgrimm ist noch immer im Smaragdgrünen Traum verloren. Schildwachen und Uralte bewachen die stille, etwas schwermütige Stadt, und ein Portal führt hinab nach Rut'theran.""",

    148: """Dunkelküste: Eine lange, felsige Küste im nordwestlichen Kalimdor mit schattigen Wäldern, nebligen Stränden und bröckelnden Ruinen, wo das Wetter kalt und stürmisch und Nebel häufig ist. Einst eine blühende Gegend des alten Kaldorei-Reiches, wurde sie von der Großen Teilung verwüstet, und ihre Städte stehen seit Jahrtausenden leer. Die Nachtelfen bauten den Hafen Auberdine wieder auf, die Verbindung nach Teldrassil, zu den Azurmythosinseln und den Östlichen Königreichen. Darüber hinaus spuken Naga, Satyrn und Geister der Hochgeborenen in den Ruinen, Kultisten verstecken sich an geheimen Orten, und Furbolgs sind durch die Verderbnis aus dem Teufelswald wahnsinnig geworden.""",

    3524: """Azurmythosinsel: Die größere der Azurmythosinseln vor dem westlichen Kalimdor, lange nur Heimat von Furbolgs, Mondkin und wilden Tieren, bis die Exodar, das Dimensionsschiff der Draenei, an ihren Ufern zerschellte. Die Überlebenden unter dem Propheten Velen bauten ihre Hauptstadt im größten erhaltenen Teil des Wracks. Die Insel ist ein Land immergrüner Wälder, violetter Blumen und sanfter Hügel, doch seltsame Kristalle aus dem Wrack übersäen die Landschaft, arkane Stürme ziehen über den Himmel, und der Absturz hat manche Pflanzen und Tiere verändert. Die freundlichen Furbolgs leben im Norden, Naga lauern in alten Ruinen, und Saboteure der Blutelfen verstecken sich in den Hügeln.""",

    3557: """Die Exodar: Die Hauptstadt der Draenei, erbaut im größten erhaltenen Teil des Dimensionsschiffes, das auf der Azurmythosinsel abstürzte. Einst ein Satellit der Festung der Stürme, wurde es in der Scherbenwelt vom Propheten Velen und seinen Anhängern mit Hilfe der Naaru gekapert, von Blutelfen sabotiert und durch den Wirbelnden Nether geschleudert. Heute ist es eine Stadt aus schimmernden Kristallhallen und leuchtenden Leitungen, die heiliges Licht und Wärme tragen. Velen weilt in der Halle der Naaru neben einem Naaru, und die Stadt erklingt vom Lied der Naaru und der stillen Hingabe eines Volkes, das Jahrtausende umhergewandert ist.""",

    3525: """Blutmythosinsel: Die nördliche der beiden Azurmythosinseln, einst Silbersturm genannt, verdorben, als Trümmer der abgestürzten Exodar blutrote Kristalle über sie verstreuten. Eine blutähnliche Flüssigkeit sickert aus den Kristallen in den Boden, verändert Pflanzen und Tiere und erfüllt die Luft mit einem unheimlichen purpurnen Nebel; selbst die Kiefern sind rot geworden. Die Draenei erforschen und heilen das Land von der Blutwacht aus und stellen sich Blutelfen, die die Macht der Kristalle wollen, Satyrn, Naga, verderbten Furbolgs und aus dem Schiff entkommenen Kreaturen. Uralte Nachtelfenruinen übersäen die Insel, und die Geister grüner Drachen spuken auf der Drachennarbe.""",

    331: """Eschental: Ein weiter, uralter Wald im Norden Kalimdors und die angestammte Heimat der Nachtelfen, eine urtümliche Wildnis aus gewaltigen Bäumen, tiefen Lichtungen, Seen und Flüssen unter einem dichten Blätterdach. Jahrtausendelang pflegten die Nachtelfen ihn, ohne ihn zu fällen, bewacht von Schildwachen, Druiden und Uralten. Im Dritten Krieg kamen die Orcs Grom Höllschreis wegen seines Holzes und erschlugen den Halbgott Cenarius. Seitdem ist er erbittert umkämpft: Die Nachtelfen halten Astranaar im Westen, der Kriegshymnenklan schlägt Holz im Osten, und die Silberschwingen-Schildwachen und die Vorreiter des Kriegshymnenklans geraten ständig aneinander. Dämonen, Satyrn und verderbte Furbolgs bleiben.""",

    361: """Teufelswald: Ein verderbter Wald im Norden Kalimdors, einst ein üppiges Paradies unter dem Schutz des Cenarius, im Dritten Krieg von der Brennenden Legion mit dem Schädel von Gul'dan entweiht. Verkrümmte Bäume, verkohlte Wiesen und Bäche voll kochendem Giftschlamm füllen das Land, und die Uralten, die es einst bewachten, irren blind umher und bluten Teufelsgift. Verderbte Furbolgs, Satyrn, Dämonen und Hexenmeister des Schattenrats verseuchen den Wald, und hungernde Tiere fallen übereinander her. Die Druiden des Zirkels des Cenarius versuchen ihn zu reinigen, und die unverdorbenen Holzschlundfurbolgs halten die nördlichen Tunnel zur Mondlichtung und nach Winterquell.""",

    493: """Mondlichtung: Ein heiliges Tal an den unteren Hängen des Berges Hyjal, von hohen Bergen geschützt und in ewige Nacht gehüllt, wo der Mond das Land in Silber taucht und die Luft ein warmer, endloser Sommerabend ist. Es ist die Heimat des Zirkels des Cenarius, wo Nachtelfen und Tauren in Frieden zusammenleben und Streit zwischen den Völkern nicht geduldet wird. Jahrtausendelang schliefen die Druiden hier in den Hügelgräbern, während ihre Geister den Smaragdgrünen Traum durchwandelten; Malfurion Sturmgrimm ist dort noch immer verloren. Das Dorf Nachthafen liegt am Ufer des Sees Elune'ara, bewacht von den Bewahrern des Hains.""",

    618: """Winterquell: Ein kaltes, verschneites Tal hoch am Berg Hyjal, in fast ewigem Winter über den Wolken der Mondlichtung. Schnee bedeckt die Hügel, gefrorene Seen glitzern, und die Luft ist klar und rein. Nachtelfen siedelten hier nach der Großen Teilung, und ihre Ruinen stehen noch im Schnee, während die freigelegten Wurzeln des Weltenbaums sich wie Bögen über den Köpfen wölben. Der blaue Drachenschwarm von Mazthoril streitet seit langem mit den Nachtelfen. Die Goblinstadt Ewige Warte steht allen offen, verderbte Furbolgs, Yetis und Frostsäbler streifen umher, und Dämonen halten die Schlucht des Flüsterns im Süden.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Center and East
    # -------------------------------------------------------------------------
    14: """Durotar: Ein Land roter, sonnengebackener Erde, schroffer Schluchten und Hügel an der Ostküste Kalimdors, dessen raue Schönheit an Draenor erinnert. Thrall machte es nach dem Dritten Krieg zur neuen Heimat der Orcs und der Dunkelspeertrolle und benannte es nach seinem Vater Durotan; an seinem Nordrand gründete er Orgrimmar. Es ist das Herz der Horde, mit Klingenhügel an der Wegkreuzung und dem Trolldorf Sen'jin an der Südküste. Gefahren bleiben: Stacheleber überfallen das Land vom Westen, Zentauren lauern im Süden, Harpyien nisten in den Schluchten, die Brennende Klinge versteckt sich in Höhlen, und an der Küste steht noch eine Festung aus Kul Tiras.""",

    1637: """Orgrimmar: Die Hauptstadt der Orcs und der Sitz der Horde, eine mächtige Festungsstadt in einer Schlucht am Nordrand von Durotar, nach dem Dritten Krieg von Kriegshäuptling Thrall gegründet und nach Orgrim Schicksalshammer benannt. Starke Mauern, gewaltige Tore und hohe Türme bewachen sie, und ihre Viertel sind Täler: das Tal der Stärke, das Handelsherz; das Tal der Geister, Heimat der Trolle und Schamanen; das Tal der Weisheit mit Thralls Feste Grommash; und das Tal der Ehre. Der Durchgang führt in die düstere Kluft der Schatten. Ihre schlichten Bauten aus Holz, Fell und Stein sind mit Stacheln und Bannern geschmückt, und Zeppeline verbinden sie mit den Östlichen Königreichen und Nordend.""",

    2917: """Halle der Legenden: Die große Offiziershalle der Horde im Tal der Stärke in Orgrimmar, ein massiver Bau aus Holz, Stein und Fell, behängt mit Bannern, Trophäen und den Waffen gefallener Feinde. Sie dient als Kaserne und Versammlungsort der angesehensten Krieger der Horde, und ihre geheime Waffenkammer birgt Waffen von jedem Kontinent Azeroths und von Draenor, viele davon Kriegsbeute mit stolzer Geschichte. Es ist ein Ort der Ehre und des Stolzes, wo an großen Feuern vom Ruhm erzählt und der Legenden der Horde gedacht wird.""",

    377: """Südstrom: Einer der großen Flüsse Kalimdors, der im Hochland des Berges Hyjal entspringt und als breiter, schneller Strom nach Süden fließt. Er trennt das Eschental von Azshara und weiter südlich das Brachland von Durotar und fließt nahe an den Mauern Orgrimmars vorbei. Im Norden ist sein Wasser kalt und reißend, im Süden warm und trüb, wo Krokilisken im Schilf lauern. Er mündet in einem stufigen Wasserfall beim Goblinhafen Ratschet ins Große Meer. Nur an wenigen Stellen überqueren ihn Brücken, und Reisende aller Art ziehen über sein Wasser.""",

    16: """Azshara: Ein schönes, aber verfluchtes Küstenland im Nordosten Kalimdors, in ewigen Herbst gehüllt, mit leuchtend orangefarbenen und roten Bäumen, hohen Klippen und weißen Stränden. Vor zehntausend Jahren war es Teil von Zin-Azshari, der Hauptstadt Königin Azsharas, bis die Große Teilung einen Großteil der Stadt versenkte. Die Nachtelfen halten es für verflucht; Ruinen thronen auf den Klippen und liegen zwischen Korallen, und Legenden sagen, die Königin herrsche nun unter den Wellen über die Naga. Geister der Hochgeborenen, Satyrn, Naga und blaue Drachen bevölkern das Land, die freundlichen Holzschlundfurbolgs halten die westlichen Berge, und oft ziehen Stürme vom Meer herein.""",

    17: """Brachland: Eine weite, heiße Savanne aus gelbem Gras, Dornenbäumen und staubigen Ebenen im Zentrum Kalimdors zwischen dem Eschental und Tausend Nadeln, mit einigen üppigen Oasen im Norden. Vor der Teilung standen hier Städte der Nachtelfen, und die uralte Goldstraße führt noch immer Karawanen zwischen Ratschet und dem Norden. Das Wegekreuz der Horde ist der Knotenpunkt, während die Allianz die Nordwacht und die Grabung von Bael Modan hält. Zentauren und Stacheleber überfallen Karawanen, Harpyien nisten in den Hügeln, die Venture Company bohrt nach Öl, und die Brennende Klinge versteckt sich auf dem Gipfel des Nebelgrauens. Ratschet an der Küste steht allen offen.""",

    215: """Mulgore: Grüne Ebenen und windumtoste Tafelberge im Zentrum Kalimdors, die angestammte Heimat der Tauren, von Bergen umschlossen mit einem einzigen Pass nach Osten ins Brachland. Jahrhundertelang zogen die Tauren als Nomaden umher und kämpften gegen die Zentauren, bis Thralls Horde half, sie zu vertreiben, und Cairne Bluthuf Donnerfels auf den Tafelbergen erbaute. Es ist ein geschütztes, ländliches Land aus Weiden, klaren Seen und nach Kiefern duftenden Winden, mit Taurendörfern, Windmühlen und geschnitzten Totems. Stacheleber halten die heiligen Roten Felsen, die Venture Company hat die heiligen Brunnen besetzt, und Harpyien nisten im Norden.""",

    1638: """Donnerfels: Die Hauptstadt der Tauren, erbaut auf vier hoch aufragenden Tafelbergen im Norden von Mulgore weit über den Goldenen Ebenen, die erste dauerhafte Stadt eines Volkes, das jahrhundertelang umherzog. Große Zelte, Langhäuser und Totempfähle krönen die Gipfel, verbunden durch schwankende Seilbrücken, und hölzerne Aufzüge heben Besucher von den Ebenen herauf. Hochhäuptling Cairne Bluthuf herrscht vom zentralen Berg aus, die Druiden versammeln sich auf der Anhöhe der Ältesten, die Schamanen auf der Anhöhe der Geister über den nebligen Teichen der Visionen und die Jäger auf der Anhöhe der Jäger. Das Wetter ist warm und sonnig, und der Blick über Mulgore ist atemberaubend.""",

    406: """Steinkrallengebirge: Ein schroffes Gebirge im Zentrum Kalimdors, von der Großen Teilung emporgehoben und vom Schwarzwolffluss zu Schluchten und Klippen zerschnitten. Die unteren Hänge sind heiß, trocken und windig, Regen bricht an den westlichen Gipfeln, und heftige Winde peitschen durch die Schluchten. Der Gipfel des Steinkrallengebirges, Nachtelfen und Tauren heilig, war einst die Heimat des Orakels. Die Goblins der Venture Company holzen die uralten Wälder ab und verschmutzen das Wasser, das verkohlte Tal ist eine Brandruine voller Feuerelementare, Harpyien halten Schluchtfestungen, und abtrünnige Grimmtotem-Tauren greifen ihre eigenen Verwandten an.""",

    # -------------------------------------------------------------------------
    # Kalimdor - South
    # -------------------------------------------------------------------------
    405: """Desolace: Eine graue, steinige Einöde im Westen Kalimdors, die unter einem Fluch zu liegen scheint: Der Himmel ist stets dunkel und stürmisch, Blitze und heftige Winde fegen über das Land, gelbe, verschmutzte Tümpel übersäen die Asche, und die Schädel uralter Kodos starren aus ihren Gräbern. Es ist die Heimat der Zentauren, die der Legende nach in den Tiefen von Maraudon geboren wurden, und vier verfeindete Stämme bekämpfen einander ebenso erbittert wie Fremde. Ruinen der Hochgeborenen liegen verstreut, Naga bevölkern die Nordwestküste, und die Brennende Klinge hat hier Dämonen beschworen. Im traurigen Gegensatz dazu ist die Westküste sonnig und üppig.""",

    357: """Feralas: Ein üppiger, uralter Regenwald im Südwesten Kalimdors mit riesigen Bäumen, nebligen Tälern, reißenden Flüssen und klaren Seen, von hohen Bergen geschützt. Er war Teil des Nachtelfenreiches, und die gewaltige Stadt der Hochgeborenen Eldre'Thalas, heute Düsterbruch genannt, liegt in Ruinen zwischen den Bäumen. Die Nachtelfen halten die Mondfederfeste auf der Insel Sardor und die Tauren das Lager Mojache im Osten. Die blutrünstigen Gordunni-Oger beherrschen viele Ruinen, Grimmtotem-Abtrünnige halten ein Lager, Naga verseuchen die westlichen Inseln, und ein großer Baum im Nordwesten ist ein Portal zum Smaragdgrünen Traum.""",

    400: """Tausend Nadeln: Eine riesige, trockene Schlucht im Süden Kalimdors voller hoch aufragender Sandsteinsäulen, die wie ein Wald aus Nadeln emporragen, vom Wasser geformt, bevor die Teilung das Land anhob. Im Osten öffnet sie sich zu den Schimmernden Ebenen, einer Salzpfanne, auf der Goblin- und Gnomeningenieure ihre Maschinen um die Wette fahren, und die Sonnenaufgänge von den Tafelbergen sind spektakulär. Taurenstämme lebten lange gefährlich auf den Gipfeln und schlagen nun von Freiwindposten aus zurück. Galakzentauren patrouillieren auf dem Schluchtgrund, Grimmtotem-Abtrünnige halten den Dunkelwolkengipfel, und Seilbrücken verbinden die Säulen hoch über den Gefahren.""",

    15: """Düstermarschen: Ein weiter, heißer und fauliger Sumpf an der Ostküste des zentralen Kalimdor, bei der Großen Teilung abgesunken, wo Mücken summen, Bäume ihre Wedel in stehende Tümpel tauchen und Schlammbänke algenverstopfte Kanäle trennen. Raptoren, Spinnen, Krokilisken und Murlocs lauern überall, und im Süden soll der schwarze Drache Onyxia im Drachensumpf hausen. Jaina Prachtmeer gründete Theramore auf einer Insel vor der Küste, die Steinbrecher-Oger empfangen die Horde in Brackenwall, und hier fand Admiral Daelin Prachtmeer sein Ende. Heimliche Scharmützel gehen trotz des Waffenstillstands weiter, und die Goblins von Schlammsprocket heißen alle willkommen.""",

    2159: """Onyxias Hort: Eine vulkanische Höhle im Drachensumpf der südlichen Düstermarschen, der Hort Onyxias, des großen schwarzen Drachen und Tochter Todesschwinges, Brutmutter des schwarzen Drachenschwarms. Die Höhle windet sich tief in die warme Erde, und die Haupthalle birgt ihr gewaltiges Gelege, bewacht von Welpen und Drachkin. Der Boden ist nur eine dünne Kruste über geschmolzenem Gestein, und die Luft ist dick von Rauch, Schwefel und dem Gestank ihrer Opfer, mit Knochen und Schätzen zwischen den Felsen. Reisende erzählen düstere Geschichten von jenen, die ihre Brut verschleppt hat, und nur wenige, die eintreten, kehren zurück.""",

    440: """Tanaris: Eine riesige Wüste im Südosten Kalimdors, ein endloses Meer aus Dünen unter wolkenlosem Himmel, glühend heiß am Tag und von gefährlichen Sandstürmen heimgesucht, mit Bergen und tiefen Höhlen im Süden. Es ist die angestammte Heimat des bronzenen Drachenschwarms, dessen Aspekt Nozdormu in den Höhlen der Zeit weilt, und im Süden liegt das versiegelte Tor zur Titanenstadt Uldum. Die Goblins des Dampfdruckkartells halten die neutrale Stadt Gadgetzan und den Hafen des Kartells. Die Sandwuttrolle herrschen von Zul'Farrak aus, Oger halten südliche Ruinen, Banditen besetzen die Wassertürme, und Piraten verstecken sich an der Küste.""",

    1941: """Höhlen der Zeit: Ein riesiges Höhlensystem im Osten von Tanaris, Heimat des bronzenen Drachenschwarms und seines Aspekts Nozdormu, der Hüter des Zeitstroms. Portale im Inneren führen zu Schlüsselmomenten der Weltgeschichte, wie der Öffnung des Dunklen Portals, Thralls Flucht aus Durnholde, der Schlacht um den Hyjal und der Läuterung Stratholmes. Sand weicht üppigem Grün, große Sanduhren drehen sich, und gewaltige Statuen bronzener Drachen ragen auf. In jüngster Zeit hat der Ewige Drachenschwarm begonnen, sich in die Geschichte einzumischen, und die bronzenen Drachen suchen Hilfe. Wer ungebeten eintritt, soll verändert wieder herauskommen.""",

    490: """Krater von Un'Goro: Ein riesiger, üppiger Krater im Süden Kalimdors zwischen Tanaris und Silithus, von hohen Wänden abgeschnitten. Ein dampfender Dschungel exotischer Pflanzen und riesiger Kreaturen füllt ihn: Teufelssaurier, Stegodone und Pterrordaxe streifen frei umher, Gorillas leben in den Höhlen, und Silithiden graben im Süden Bauten. Der tätige Vulkan des Feuerbergs erhebt sich in seiner Mitte, heiße Quellen und Teergruben brodeln, und seltsame Kristalle und geheimnisvolle Pylonen übersäen das Land. Viele Gelehrte halten ihn für einen Ort der Titanen. Forscher aller Völker versammeln sich in Marshals Zuflucht an der Nordwand, und der Dschungel verstummt nie.""",

    1377: """Silithus: Eine raue Wüste aus Fels und Sand in der Südwestecke Kalimdors, durchbrochen von den hohen Bauten der insektenartigen Silithiden. Vor tausend Jahren führten ihre Herren, die Qiraji, den Krieg der Treibsande, bis die Nachtelfen und die Drachenschwärme sie hinter dem Skarabäuswall in Ahn'Qiraj einschlossen. In jüngerer Zeit wurden die Tore wieder geöffnet, und die Heere der Allianz und der Horde zogen gegen die Qiraji. Der Zirkel des Cenarius wacht von der Burg Cenarius aus, der bronzene Drachenschwarm ist zurückgekehrt, und der Schattenhammer lagert im ganzen Land. Die Hitze ist erbarmungslos, und der Wind trägt stechenden Sand.""",

    3478: """Tore von Ahn'Qiraj: Die großen Tore im Skarabäuswall am Südrand von Silithus, die Ahn'Qiraj bewachen, die uralte Festung der Qiraji und ihrer Silithiden. Vor tausend Jahren schlossen die Nachtelfen und die Drachenschwärme die Qiraji hinter dem Wall ein; in jüngerer Zeit wurden die Tore mit dem Szepter der Treibsande wieder geöffnet, und die Heere der Allianz und der Horde zogen hinein. Dahinter liegen die Ruinen und der Tempel von Ahn'Qiraj, wo die wahren Herren der Qiraji hausen sollen. Der Sand vor den Toren ist von Schlachten gezeichnet, und eine unheilvolle Stille liegt über ihnen.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Höllenfeuerhalbinsel: Eine karge, blutrote Einöde im Osten der Scherbenwelt, ein Überrest Draenors und das erste Land hinter dem Dunklen Portal. Orcische Hexenmeister haben ihr vor langer Zeit das Leben ausgesaugt, der rissige rote Boden speit Feuergeysire, und an ihren Rändern treiben Landbrocken vor dem wirbelnden Himmel des Nethers. Hier kämpfte die Expedition der Allianz gegen die Horde von Draenor und versiegelte das Portal. Heute ist die Höllenfeuerzitadelle die Festung der Teufelsorcs, die Brennende Legion stürmt von ihren Schmieden aus die Stufen des Schicksals, die Allianz hält die Ehrenfeste und die Horde Thrallmar.""",

    3521: """Zangarmarschen: Ein gespenstisch schöner Sumpf im Westen der Scherbenwelt, bedeckt von einem Wald riesiger Pilze, die sich wie gewaltige Bäume über seine Seen erheben. Leuchtende Pilze, schimmernde Sporen und biolumineszente Geschöpfe füllen seine ewige Dämmerung mit blauem und grünem Licht, und er entging weitgehend der Verderbnis, die Draenor verwüstete. Nun gerät sein Gleichgewicht ins Wanken: Die Naga Lady Vashjs legen mit großen Pumpen im Echsenkessel das Wasser trocken, Oger fällen die Pilze, und der Sumpf stirbt. Die Expedition des Cenarius verteidigt ihn von der Zuflucht des Cenarius aus, und die friedlichen Sporlinge, ein Volk vernunftbegabter Pilze, leben in Sporeggar.""",

    3519: """Wälder von Terokkar: Ein dunkler, uralter Wald im Süden der Scherbenwelt mit hohen Kristallkiefern, dichtem grünem Blätterdach und nebligen Lichtungen, Heimat der vogelartigen Arakkoa, deren verborgene Hauptstadt Skettis in den südöstlichen Bergen liegt. Im Nordwesten steht Shattrath, eine Zuflucht für Flüchtlinge aller Völker. Die südliche Hälfte sind die Knochenwüsten, verwüstet, als der Schattenrat im Nekropolis der Draenei, Auchindoun, ein schreckliches Wesen beschwor und einen Riss schlug, der die Astralen in die Scherbenwelt zog. Die Allianz hält Allerias Feste und die Horde die Steinbrecherfeste, während Teufelsorcs und Hexenmeister des Schattenrats im Wald lauern.""",

    3703: """Shattrath: Die Stadt des Lichts, die uralte Hauptstadt der Draenei im Nordwesten der Wälder von Terokkar, gefallen vor den dämonisch verderbten Orcs und wiederaufgebaut von den Sha'tar, aus Licht geborenen Naaru, zusammen mit den Priestern der Draenei, den Aldor. Blutelfen, die Kael'thas zu ihrer Zerstörung sandte, legten die Waffen nieder und wurden zu den Sehern, erbitterten Rivalen der Aldor in derselben Stadt. Der Naaru A'dal herrscht von der Terrasse des Lichts aus, wo auch Erzmagier Khadgar weilt. Das Unteres Viertel ist voller Flüchtlinge aller Völker, Gewalt zwischen Allianz und Horde ist verboten, und Portale verbinden die Stadt mit den Hauptstädten Azeroths.""",

    3917: """Auchindoun: Die zerstörte Nekropole der Draenei im Herzen der Knochenwüsten in den Wäldern von Terokkar, jahrtausendelang ihr heiligster Ort, an dem sie ihre geehrten Toten bestatteten. Agenten des Schattenrats beschworen darin ein uraltes Elementar des Klangs, und das Ritual sprengte den Tempel, verwüstete den Wald und riss einen Spalt, der die Astralen in die Scherbenwelt zog. Die toten Draenei wandeln nun als ruhelose Geister durch die Ruinen. Ihre Hallen werden von verschiedenen Mächten beansprucht: Astrale in den Managräbern, Dämonen in den Auchenaikrypten, Arakkoa in den Sethekkhallen und der Schattenrat im Schattenlabyrinth.""",

    3518: """Nagrand: Das letzte unversehrte Land der Scherbenwelt, sanfte grüne und goldene Grasebenen, funkelnde Seen und schwebende Inseln unter einem rosa getönten Himmel. Sein Name bedeutet Land der Winde; es war die Heimat des Frostwolfklans und der Versammlungsort der Orcs am Fuß des heiligen Berges Oshu'gun. Elementare sprechen am Thron der Elemente mit Sterblichen. Die unverderbten Mag'har-Orcs leben in Garadar unter Großmutter Geyah und die Zerschlagenen der Kurenai in Telaar. Oger bedrohen das Land, die Legion hat Schmieden im Westen, und um die Stadt Halaa kämpfen Allianz und Horde.""",

    3522: """Schergrat: Messerscharfe Klippen und wie mit der Axt geschlagene Täler im Norden der Scherbenwelt, von rauen Winden zu dolchartigen Spitzen geschliffen unter dem grünen Schimmer des Nethers. Es ist das Land der Oger der Schergrat- und Blutschlägerklans, die einander um die Gunst der Gronn bekämpfen, Riesen unter Gruul dem Drachenschlächter in seinem Hort im Norden; die Knochen erschlagener schwarzer Drachen hängen aufgespießt auf den Gipfeln. Die Legion hat Schmieden auf den Hochebenen, und Kultisten der schwarzen Drachen lauern im Norden. Die Nachtelfen halten Sylvanaar, die Horde die Donnerfeste, und die erleuchteten Oger von Ogri'la leben auf einer westlichen Hochebene.""",

    3523: """Nethersturm: Gewaltige Landbrocken und unzählige Felssplitter, die im Wirbelnden Nether im Nordosten der Scherbenwelt treiben, einst die Felder von Farahlon. Ein ständiger arkaner Sturm verzerrt das Land: Der Boden ist kränklich violett, magische Blitze zucken durch violetten Dunst, und Energiebänder winden sich über den Himmel, während die Gegend langsam zerfällt. Blutelfen, die Kael'thas treu sind, zapfen den Nether mit großen Manaschmieden an, gebaut mit der Technik der Festung der Stürme, die sie halten, und die Brennende Legion hat Stützpunkte auf den Inseln. Die Astralen des Konsortiums halten die Sturmsäule und ihre Ökodome, und Goblins betreiben Area 52.""",

    3520: """Schattenmondtal: Ein düsteres, verwüstetes Land im Südosten der Scherbenwelt, wo Tag und Nacht geschmolzene Teufelsenergie ausbricht und den Himmel mit grünen Flammen erhellt. Schwarzer Fels und Asche bedecken den Boden, und der Vulkan namens Hand von Gul'dan speit in seiner Mitte grüne Lava. Im Osten steht der Schwarze Tempel, einst der Tempel von Karabor der Draenei, heute die Zitadelle Illidan Sturmgrimms, des selbsternannten Herrschers der Scherbenwelt, und seiner Illidari, die die Brennende Legion von der Legionsfeste aus abwehren. Teufelsorcs des Drachenmalklans versklaven die Drachen des Netherschwingenschwarms. Die Wildhammerfeste, das Dorf Schattenmond und die Lager der Aldor und Seher führen Krieg gegen Illidan.""",

    3540: """Wirbelnder Nether: Das chaotische Astralreich zwischen den Welten, eine Dimension wilder Magie, die die Welten des Universums verbindet und die Heimat der Dämonen der Brennenden Legion ist. Als Draenor zerrissen wurde, wurden seine Überreste in den Nether gezogen, und an den Rändern der Scherbenwelt endet das Land einfach in einer endlosen Leere aus schillernden Wolken, Bändern farbiger Energie und treibenden Felsen. Ferne Welten sind im wirbelnden Himmel zu erahnen, die Naturgesetze wirken unsicher, und der Verstand müht sich, das Gesehene zu begreifen. Wer sich zu weit hinauswagt, kehrt vielleicht nie zurück.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Boreanische Tundra: Eine weite, windgepeitschte Ebene am Südwestrand Nordends, für viele das erste Land im Krieg gegen den Lichkönig. Rotbraune Erde, Flechten und Eis erstrecken sich unter einem Wind, der einem Zwerg den Bart vom Gesicht reißen könnte; in der Mitte dampfen Geysire, und der verschneite Osten ist am härtesten. Mammuts und Wollnashörner ziehen über die Ebenen, und die friedlichen Tuskarr fischen und jagen Wale an der Küste, ihre Dörfer von Kvaldir-Plünderern verwüstet. Malygos und der blaue Drachenschwarm beherrschen die Insel Kaltarra, die Geißel hält En'kilah, und die Valianzfeste der Allianz und die Kriegshymnenfeste der Horde blicken nach Norden.""",

    495: """Der Heulende Fjord: Ein raues Land im Südosten Nordends aus grünen Wiesen, eisigen Flüssen, dunklen Kiefernwäldern und hohen Fjorden, deren Klippen ins kalte Meer stürzen. Am Ende der Dolchkappenbucht erhebt sich Burg Utgarde über dem Cauldrossee. Es war der uralte Sitz der Vrykul, riesenhafter Krieger, die aus ihrem langen Schlaf erwacht sind; viele dienen nun dem Lichkönig und überfallen jeden, der sich nähert. Die Allianz hält den alten Hafen Valgarde und die Westwacht, die Verlassenen der Hand der Rache halten den Rachehafen und Neu-Agamand, und die Forscherliga gräbt nach Titanenruinen, wo Eisenzwerge aufgetaucht sind.""",

    65: """Drachenöde: Das Herz des südlichen Nordend, eine arktische Einöde aus gleißend weißen Gletschern, übersät mit den schimmernden Knochen von Drachen, der Ort, an den Drachen zum Sterben kommen. Hier schufen die Hüter der Titanen die ersten Drachenaspekte, und die Knochen Galakronds ragen noch aus dem Eis. In der Mitte erhebt sich der Wyrmruhtempel, wo sich die Drachenschwärme versammeln, umgeben von den fünf Drachenschreinen. Die Geißel belagert die Schreine und erweckt Frostwyrms aus den Knochen, Naxxramas schwebt über den östlichen Ebenen, und die Scharlachrote Offensive hält eine Festung an der Küste. Allianz und Horde haben Festungen vor der Pforte des Zorns errichtet, dem verschlossenen Eingang zur Eiskrone.""",

    394: """Grizzlyhügel: Ein bewaldetes Land im Südosten Nordends, sanfte grüne Vorberge voller Kiefern, die zu schroffen Bergen ansteigen, wo der dichte Wald den Wind abhält und die Hügel fast warm wirken. Bären, Wölfe, Hirsche und Schneeeulen füllen die Wälder. Es ist die Heimat der Furbolgs, deren Stadt Grizzlemaw im Stumpf von Vordrassil steht, einem Weltenbaum, den die Druiden zerstörten, als sie ihn verderbt fanden, und ein schleichender Wahnsinn breitet sich unter ihren Stämmen aus. Fallensteller unterhalten Handelsposten im Wald, die Geißel hält Feste Drak'Tharon im Norden, und Allianz und Horde streiten um die Holzfällerlager.""",

    4201: """Vordrassils Tränen: Eines der großen gestürzten Bruchstücke des Weltenbaums Vordrassil in den Grizzlyhügeln. Vor langer Zeit pflanzte Fandral Hirschhaupt Zweige Nordrassils in ganz Nordend, und der größte davon, Andrassil, die Krone des Schnees, überragte diese Hügel jahrzehntelang. Doch seine Wurzeln erreichten das Gefängnis eines uralten Übels, und Wahnsinn breitete sich unter den Geschöpfen des Landes aus, sodass der Zirkel des Cenarius den Baum zerstörte und ihn Vordrassil nannte, die Zerbrochene Krone. Seine Stücke liegen noch im Wald, und das Land um dieses Bruchstück ist von lebendem Schlamm bedeckt, einem Zeichen der Verderbnis, die ihn verdammte.""",

    3477: """Azjol-Nerub: Ein riesiges unterirdisches Königreich unter halb Nordend, das uralte Reich der spinnenartigen Neruber, eines Volkes der Gelehrsamkeit, Kunst und Philosophie, mit polierten Gängen, gemeißelten Hallen und großen Bibliotheken im Licht leuchtender Pilze. Der Lichkönig sah in ihnen die größte Bedrohung seiner Macht und überrannte das Reich im Spinnenkrieg; jeder gefallene Neruber erhob sich, um für die Geißel zu kämpfen, und ihr eigener König Anub'arak dient ihm nun. Untote Neruber bewachen Gelege im Oberen Königreich, lebende Überlebende führen einen verborgenen Krieg, und im Alten Königreich Ahn'kahet regen sich die Gesichtslosen.""",

    66: """Zul'Drak: Die Heimat der Eistrolle der Drakkari im Osten Nordends, ein Tal, das selbst eine einzige riesige Tempelstadt ist, aus Plätzen, Zikkuraten, Mauern und Aquädukten in Terrassen, mit Dornenbäumen, gefrorenen Teichen und Schnee zwischen den Ruinen. Die Drakkari gehören zu den ältesten Völkern Azeroths und herrschen von Gundrak aus, doch ihr Reich zerfällt. Die Geißel hält Feste Drak'Tharon, und ihre Nekropolen erheben gefallene Trolle gegen ihr eigenes Volk. In ihrer Verzweiflung haben die Propheten der Drakkari ihre eigenen Götter, die Loa, erschlagen und trinken ihr Blut für Macht, was viele in den Wahnsinn treibt. Der Argentumkreuzzug und die Zandalari sind gekommen, um einzugreifen.""",

    3711: """Sholazarbecken: Ein tropisches Dschungelbecken mitten in Nordend, von hohen Bergen umringt, heiß, feucht und voller Leben nach der bitteren Kälte draußen. Die Hüterin Freya machte es zu einer Wiege des Lebens, und Titanenpylonen mit wirbelnden Kristallen halten seine Wärme und schützen es vor üblen Kreaturen. Vier Flüsse treffen sich am Herz des Flusses im dichten Wildwuchs. Nashörner, Gorillas, Krokilisken und Hydren bevölkern den Dschungel, und die Gorlocs des Orakelstammes kämpfen gegen die Wolvar der Wildherzen. Die Geißel ist vom Osten her in das Becken eingedrungen, und der Avatar Freyas kämpft darum, die sich ausbreitende Seuche einzudämmen.""",

    2817: """Kristallsangwald: Ein Land mitten in Nordend, in dem jeder Baum, jeder Grashalm und ein Großteil der Erde zu leuchtendem, lebendem Kristall geworden ist, der im Wind summt, sodass der Wald eine leise, endlose Musik spielt. Einst war er Mondgesang, wo die Hochgeborenen den Außenposten Shandaral unterhielten; als die blauen Drachen wegen gestohlener Relikte Rache nahmen, ließ der leichtsinnige Zauber der Magier den ganzen Wald kristallisieren, und ihre Geister wandern noch immer dort. Dalaran schwebt nun über dem westlichen Wald, der Silberbund und die Sonnenhäscher halten zerstörte Türme auf entgegengesetzten Seiten, und der blaue Drachenschwarm führt im Süden den Nexuskrieg.""",

    4395: """Dalaran: Die Stadt der Magier und Heimat der Kirin Tor, deren violette Türme einst am Lordamere-See standen, bis die Geißel sie im Dritten Krieg zerstörte. Die Kirin Tor haben die ganze Stadt in den Himmel gehoben und nach Nordend gebracht, wo sie über dem Kristallsangwald schwebt, um dem Lichkönig und dem blauen Aspekt Malygos zu trotzen, dessen Krieg gegen Zauberkundige sie zu einem Hauptziel macht. Der Rat der Sechs unter Erzmagier Rhonin herrscht von der Violetten Zitadelle aus. Dalaran empfängt Allianz und Horde gleichermaßen: Der Silberbund und die Sonnenhäscher unterhalten eigene Enklaven und beäugen einander misstrauisch.""",

    4197: """Tausendwintersee: Ein gefrorenes Tal im Zentrum Nordends, über die umliegenden Länder erhoben, das Bett eines geschrumpften Sees, das Titanenruinen, dunkle Wälder, gefrorene Sümpfe und einen vulkanischen Kessel freigelegt hat. In seinem Herzen steht die Festung Tausendwinter, eine Titanenanlage, die den Eingang zum Gewölbe von Archavon bewacht, das Relikte unvorstellbarer Macht birgt, gehütet von uralten Riesen, die jeden Eindringling verabscheuen. Seit Beginn des Krieges gegen den Lichkönig kämpfen Allianz und Horde ohne Ende um die Festung und das Gewölbe, berennen ihre Mauern mit Belagerungsmaschinen, und die Herrschaft wechselt immer wieder.""",

    67: """Die Sturmgipfel: Ein hoch aufragendes Gebirge im Nordosten Nordends, rau und gefährlich, wo heftige Winde einen Zwerg von der Klippe reißen, Lawinen die Hänge hinabdonnern und das Gleißen des Eises Unvorsichtige blendet. Die Gipfel waren die Heimat der Hüter der Titanen, und fast jeder Berg birgt Tempel, Terrassen und gewaltige Maschinen; der Tempel der Stürme krönt den höchsten Gipfel, und im Norden liegt Ulduar, die größte Titanenanlage Azeroths. Sein Hüter Loken hat sich der Dunkelheit zugewandt, und seine Eisenzwerge und Riesen vertreiben die Irdenen aus ihrer Heimat. Die Frostriesen der Söhne Hodirs halten die östlichen Täler.""",

    210: """Eiskrone: Das dunkle Herz Nordends und Sitz des Lichkönigs, ein Land aus Bergen und Gletschern, in dem das Eis vor Verderbnis schwarz geworden ist. Vom Frostthron aus versklavte der Lichkönig die Völker Nordends und erhob die Geißel, und um den Thron steht die Eiskronenzitadelle, eine Kathedrale aus Saronitklingen, fast von überall auf dem Kontinent sichtbar. Saronitmauern und Laufwege verbinden Festungen, Nekropolen und Minen, und die Untoten sind allem anderen zahlenmäßig überlegen. Nun ist der Krieg vor seiner Tür angekommen: Der Argentumkreuzzug und die Ritter der Schwarzen Klinge schlagen von eroberten Festungen aus zu, und die Kanonenschiffe der Allianz und der Horde kämpfen am Himmel.""",

    4742: """Hrothgars Landestelle: Eine kleine, nebelverhangene Insel vor der Nordküste der Eiskrone, jenseits der Meerenge, die Seeräuberpassage genannt wird. Einst stand hier ein Dorf der Tuskarr, bis die Kvaldir, die verfluchten Seevrykul, unter ihrem Häuptling Hrothgar kamen, seine Bewohner töteten oder vertrieben und die Insel nach ihm benannten. Nun ist sie ein Ausgangspunkt für Überfälle der Kvaldir auf Schiffe in der Meerenge, wo sie große Kraken aus der Tiefe rufen, während die Flotten des Silberbunds und der Sonnenhäscher darum kämpfen, sie zurückzudrängen.""",

    # -------------------------------------------------------------------------
    # Seas
    # -------------------------------------------------------------------------
    308: """Das Verbotene Meer: Ein weites, kaltes und kaum kartiertes Meer entlang der Ostküste der Östlichen Königreiche, von den Sümpfen des Elends bis hinauf zum Immersangwald. Sein graues Wasser ist rau und oft nebelverhangen, starke Strömungen und plötzliche Stürme machen die Seefahrt gefährlich, und ein Großteil der Küste ist von Klippen und Bergen versperrt. Nur wenige Schiffe wagen sich weit vom Ufer fort, und Seeleute erzählen von unbekannten Ländern und schrecklichen Kreaturen jenseits des Horizonts. Haie und Seeschlangen leben in seinen Tiefen, und Murlocs und Naga lauern an seinen Ufern.""",

    214: """Das Große Meer: Der weite Ozean zwischen den Kontinenten Azeroths, entstanden, als der Brunnen der Ewigkeit zerstört wurde und das alte Kalimdor bei der Großen Teilung zerbrach; jedes Meer der Welt ist mit ihm verbunden. Sein tiefblaues Wasser reicht bis über den Horizont, und Seeleute erzählen von verlorenen Inseln, versunkenen Städten und dem großen Strudel des Mahlstroms in seinem Herzen, wo einst der Brunnen lag. Stürme ziehen plötzlich auf, und Seeschlangen, Riesenhaie und Naga sollen in seinen Tiefen lauern. Schiffe der Allianz, der Horde, der Goblins und der Piraten überqueren es ständig zwischen den Kontinenten.""",

    332: """Das Große Meer: Der offene Ozean zwischen den Kontinenten Azeroths, geboren, als der Brunnen der Ewigkeit bei der Großen Teilung implodierte. Fern jeder Küste erstreckt sich in alle Richtungen nur endloses blaues Wasser, unterbrochen von einer fernen Insel oder einem vorbeiziehenden Schiff. Die Dünung hebt und senkt sich, Seevögel kreisen hoch oben, und in der Tiefe schwimmen Geschöpfe, die kaum jemand je gesehen hat. Seeleute sprechen ehrfürchtig vom Mahlstrom, dem gewaltigen Strudel in der Mitte des Meeres, und von den unzähligen Schiffen, die Stürmen und der Tiefe zum Opfer fielen. Es ist ein Ort der Einsamkeit und Gefahr, wo Wind und Wellen herrschen.""",

    457: """Das Verhüllte Meer: Der große Ozean vor den Westküsten Kalimdors, der sich von der Dunkelküste, dem Eschental, Desolace und Feralas in den unbekannten Westen erstreckt. Oft ist er in Nebel gehüllt, was ihm seinen Namen gab; sein Wasser ist tief, im Norden kalt und im Süden wärmer. Teldrassil erhebt sich vor der Nordwestküste aus ihm, und die Azurmythosinseln liegen in ihm. Naga, Meeresriesen und Seeschlangen leben in seinen Tiefen, und die versunkenen Ruinen uralter Nachtelfenstädte liegen unter seinen Wellen. Jenseits der bekannten Küsten ist er kaum erforscht.""",

    3479: """Das Verhüllte Meer: Die Gewässer um die Azurmythosinseln vor dem nordwestlichen Kalimdor, wo das Draeneischiff namens Exodar abstürzte. Das Meer ist tief und oft in Nebel gehüllt, und Trümmer und Kristalle des gestürzten Schiffes verleihen manchen Küstengewässern ein seltsames Leuchten, vor allem um die Blutmythosinsel, deren Ufer sich rot färben. Murlocs und Naga leben an den Küsten, versunkene Nachtelfenruinen liegen unter den Wellen, und Schiffe fahren zwischen der Exodar und den Ländern der Nachtelfen, während sich im Osten Teldrassil aus dem Meer erhebt.""",

    3455: """Das Nördliche Meer: Die kalten Gewässer vor der Nordküste von Quel'Thalas, die sich von den Küsten des Immersangwaldes nach Norden in Richtung Nordend erstrecken. Die Insel von Quel'Danas erhebt sich vor der Nordküste aus ihnen, und die Elfenschiffe, die sie befahren, verbinden seit langem die Heimat der Elfen mit der übrigen Welt. Das Wasser ist kalt und grau, und die Winde darüber tragen die Kälte des gefrorenen Nordens.""",

    4258: """Das Nördliche Meer: Die kalten Gewässer entlang der Südostküsten Nordends, vor den Grizzlyhügeln und dem Heulenden Fjord, die bis an die Nordküsten Lordaerons reichen. Inseln wie die Blutmondinsel und die Ruinen von Tethys liegen im grauen Wasser. Schiffe der Allianz und der Verlassenen überqueren es auf dem Weg zu den Häfen des Fjords, während Langschiffe der Vrykul und Kvaldir-Plünderer im Nebel lauern.""",

    4630: """Das Nördliche Meer: Die eisigen Gewässer um die Ost- und Nordküsten Nordends, grau und voller Treibeis unter beißenden Winden. Nur wenige Schiffe wagen sich weit hinaus, denn Eisberge und Nebel verbergen die Küsten, und die verfluchten Kvaldir und andere Seeräuber sollen aus den Nebeln aufsteigen.""",

    3979: """Die Gefrorene See: Das kalte Meer südlich von Nordend, ein Teil des Großen Meeres, das sich von den Südküsten der Boreanischen Tundra, der Drachenöde und des Heulenden Fjords bis zum Mahlstrom erstreckt. Packeis und Eisberge treiben auf seinem grauen Wasser. Flotten der Allianz und der Horde überqueren es, um den Kontinent zu erreichen, Tuskarr reiten auf riesigen Schildkröten zwischen ihren Küstendörfern, und die gemeißelten Säulen des uralten Pfads der Titanen ragen aus den Wellen. Kvaldir-Plünderer und Seeungeheuer lauern in seinen Tiefen.""",
}

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'Ein verborgenes Tal tief im Alteracgebirge, Heimat der '
            'Frostwolforcs, seit Gul\'dan sie vor dem Ersten Krieg '
            'dorthin verbannte. Die Zwerge der Sturmlanzenexpedition '
            'kamen, um nach Rohstoffen und Titanenrelikten zu graben, '
            'und beanspruchen das Tal für Eisenschmiede, und die '
            'Frostwölfe haben geschworen, sie zu vertreiben. Nun tobt '
            'der Krieg von der Festung Dun Baldar im Norden bis zur '
            'Frostwolfburg im Süden.'
        ),
        'tone': (
            'Episch und gewaltig, ein echter Krieg zweier Heere im '
            'Schnee.'
        ),
        'objectives': (
            'Tötet den feindlichen General. Erobert Türme und '
            'Friedhöfe.'
        ),
        'landmarks': (
            'Wichtige Orte: Dun Baldar und die Bunker der Sturmlanzen '
            'im Norden, Steinbruchfriedhof und Schneewehenfriedhof in '
            'der Mitte, der Eisblutturm und die Turmstellung, der '
            'Frostwolffriedhof und die Frostwolfburg im Süden. '
            'Schnee, Kiefernwälder, Gebirgspässe und Eishöhlen. '
            'Erwähne KEINE Orte aus anderen Schlachtfeldern.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'Eine Waldschlucht im südlichen Eschental, wo die Orcs '
            'Grom Höllschreis im Dritten Krieg große Schneisen in den '
            'Wald schlugen. Die Orcs der Vorreiter des '
            'Kriegshymnenklans schlagen hier noch immer Holz für die '
            'Horde, und die Silberschwingen-Schildwachen der '
            'Nachtelfen haben geschworen, nicht zu ruhen, bis der '
            'letzte Orc aus der Schlucht vertrieben ist.'
        ),
        'tone': (
            'Intensiv, schnell und persönlich, ein erbitterter Kampf '
            'um den Wald.'
        ),
        'objectives': 'Erobert die feindliche Flagge dreimal.',
        'landmarks': (
            'Wichtige Orte: die Silberschwingenfeste (Festung der '
            'Nachtelfen), das Fort des Kriegshymnenklans (Festung der '
            'Orcs), die Tunnel unter jeder Basis, das offene '
            'Mittelfeld, die Rampen und die Friedhöfe. Hohe Bäume, '
            'Baumstümpfe und Holzstapel. Erwähne KEINE Orte aus '
            'anderen Schlachtfeldern wie Mühlen, Höfe oder Türme.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'Ein fruchtbares Becken im Herzen des Arathihochlands, '
            'reich an Erz, Holz und Ackerland. Der Bund von Arathor, '
            'der Rest von Stromgarde, kämpft darum, die Rohstoffe des '
            'Landes zurückzugewinnen, während die Entweihten der '
            'Verlassenen sie für die Horde an sich reißen wollen.'
        ),
        'tone': (
            'Strategisch und territorial, im ganzen Becken '
            'gleichzeitig ausgefochten.'
        ),
        'objectives': (
            'Haltet Stützpunkte, um als Erste 1600 Ressourcen zu '
            'erreichen.'
        ),
        'landmarks': (
            'Wichtige Orte: Ställe (Norden, offene Weiden mit '
            'Pferdekoppeln), Schmiede (zentrale Kreuzung, Rauch und '
            'Ambosse), Sägewerk (Aussicht auf dem Hügel, '
            'Holzplattformen und Sägeblätter), Goldmine '
            '(Höhleneingang im Südosten, Lorenwagen und Fackeln), Hof '
            '(Süden, Felder und Heuhaufen bei einem Bauernhaus). '
            'Erwähne KEINE Orte aus anderen Schlachtfeldern.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'Ein Bruchstück Draenors, das am Rand des Nethersturms im '
            'Wirbelnden Nether treibt, wo vier Ruinen auf einer '
            'großen Insel um eine Quelle reiner Energie in ihrer '
            'Mitte stehen. Allianz und Horde kämpfen beide um die '
            'Herrschaft über die Insel und ihre Macht.'
        ),
        'tone': (
            'Angespannt und chaotisch, mit der Leere des Nethers '
            'gleich hinter den Rändern.'
        ),
        'objectives': (
            'Haltet Basen und erobert die Flagge in der Mitte, um '
            '1600 Punkte zu erreichen.'
        ),
        'landmarks': (
            'Wichtige Orte: Teufelshäscherruinen, Blutelfenturm, '
            'Draeneiruinen, Magierturm, die Brücken und die Flagge in '
            'der Mitte. Violetter Stein, knisternde Energie und der '
            'endlose Nether ringsum. Erwähne KEINE Orte aus anderen '
            'Schlachtfeldern.'
        ),
    },
    9: {  # SA (BATTLEGROUND_SA = 9)
        'name': 'Strand of the Ancients',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'Eine Insel vor der Südküste der Drachenöde, wo hinter '
            'den bröckelnden Mauern einer uralten Zitadelle ein '
            'Relikt der Titanen ruht. Allianz und Horde wollen es '
            'beide wegen des Wissens der Titanen, das es bergen soll: '
            'Eine Seite stürmt die Mauern vom Meer aus, während die '
            'andere sie hält.'
        ),
        'tone': (
            'Eine zermürbende Belagerung, Welle um Welle gegen uralte '
            'Mauern.'
        ),
        'objectives': (
            'Durchbrecht die Tore und erobert das Relikt, oder '
            'verteidigt es so lange wie möglich.'
        ),
        'landmarks': (
            'Wichtige Orte: der Strand und die Docks, an denen die '
            'Angreifer landen, das Tor des Grünen Smaragds und das '
            'Tor des Blauen Saphirs, das Tor der Roten Sonne und das '
            'Tor des Violetten Amethysts, das Tor des Gelben Mondes, '
            'die Kammer der Uralten Relikte, Zerstörer, Kanonen und '
            'Friedhöfe. Glitzernder Sand, Titanenstein und brechende '
            'Wellen. Erwähne KEINE Orte aus anderen Schlachtfeldern.'
        ),
    },
    30: {  # IC (BATTLEGROUND_IC = 30)
        'name': 'Isle of Conquest',
        'alliance_faction': '7th Legion',
        'horde_faction': 'Warsong Offensive',
        'lore': (
            'Eine Insel von großem strategischem Wert für den Krieg '
            'in Nordend, mit Docks, einem Steinbruch, einer '
            'Ölraffinerie, einer Belagerungswerkstatt und einem '
            'Hangar für Kanonenschiffe. Die Allianz unter '
            'Hochkommandant Halford Wyrmbann und die Horde unter '
            'Oberanführer Agmar halten je eine Festung auf der Insel '
            'und kämpfen um ihre Kontrolle.'
        ),
        'tone': (
            'Gewaltig und mechanisiert, Belagerungsmaschinen und '
            'Kanonenschiffe im offenen Krieg.'
        ),
        'objectives': (
            'Tötet den feindlichen General. Erobert Docks, Werkstatt '
            'und Hangar, um die feindliche Festung zu brechen.'
        ),
        'landmarks': (
            'Wichtige Orte: die Festung der Allianz im Westen, die '
            'Festung der Horde im Osten, die Docks, die Werkstatt, '
            'der Hangar mit seinen Kanonenschiffen, der Steinbruch '
            'und die Raffinerie. Belagerungsmaschinen, Kanonen und '
            'eiserne Mauern. Erwähne KEINE Orte aus anderen '
            'Schlachtfeldern.'
        ),
    },
}

DUNGEON_FLAVOR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Burg Schattenfang: Eine verwunschene Burg auf einer Klippe über dem Dorf Pyrewood im südlichen Silberwald, einst der Sitz Baron Silberlains. Im Dritten Krieg beschwor der Erzmagier Arugal die Worgen gegen die Geißel, doch sie wandten sich gegen alle; vor Schuld wahnsinnig geworden, nahm er sie als seine Kinder an und machte die Burg zu seinem Unterschlupf. Worgen streifen durch Höfe und Türme, untote Diener wandeln durch die Hallen, und der rachsüchtige Geist des Barons soll noch umgehen. Kalter Stein, flackernde Fackeln und Wolfsgeheul füllen die Nacht.""",

    34: """Das Verlies: Ein streng bewachtes Gefängnis unter dem Kanalviertel von Sturmwind, in dem kleine Gauner, politische Aufrührer, Mörder und einige der gefährlichsten Verbrecher des Landes sitzen, viele von ihnen Defias. Ein jüngster Aufstand hat die Wachen vertrieben, und die Häftlinge streifen nun frei durch Zellen und Gänge unter dem gerissenen Verbrecher, der die Revolte anführte. Die Luft ist feucht und stickig, Wasser tropft vom Stein, und die Rufe der Gefangenen hallen durch die engen Gänge.""",

    36: """Die Todesminen: Eine alte Goldmine unter dem Geisterdorf Mondbruch in Westfall, die verborgene Festung der Defiasbruderschaft, Gesetzloser aus den unbezahlten Steinmetzen Sturmwinds. Bergleute der Defias, Goblin-Ingenieure und Oger arbeiten in den Stollen, und die Gänge münden in eine riesige verborgene Bucht, in der die Bruderschaft ein großes Kriegsschiff baut, das Herzstück ihrer Pläne gegen das Königreich. Die Stollen sind dunkel und eng, riechen nach Staub, Öl und Schießpulver, und überall knarren Balken und rattern Maschinen.""",

    43: """Die Höhlen des Wehklagens: Ein Höhlennetz unter dem Herzen des Brachlands, benannt nach dem langen, klagenden Heulen der Dampfspalten, die durch sie entweichen. Der Nachtelfendruide Naralex hoffte, mit ihren Quellen und der Macht des Smaragdgrünen Traums das Brachland wieder ergrünen zu lassen, doch sein Traum wurde zum Albtraum. Das Wasser wurde faulig, die Tiere darin wurden zu bösartigen Räubern, und seine eigenen Jünger verwandelten sich in die Druiden des Giftzahns. Naralex soll irgendwo in der Tiefe liegen, gefangen in seinem wachen Albtraum.""",

    47: """Kral der Klingenhauer: Der große Dornenbau der Stacheleber am Südrand des Brachlands, gewachsen aus den Ranken, die dort sprossen, wo im Krieg der Ahnen das Blut des Halbgottes Agamaggan floss. Die Stacheleber verehren ihn als Heimat ihres Volkes. Die alte Vettel Charlga Klingenflanke herrscht über ihn, ihre Schamanen überfallen rivalisierende Stämme und Dörfer der Horde, und manche flüstern, sie verhandle mit Gesandten der Geißel. Gewaltige Dornenranken wölben sich über den Köpfen, und die Gänge sind schlammig, eng und voller Eber.""",

    48: """Tiefschwarze Grotte: Einst ein prächtiger Tempel der Mondgöttin Elune an der Zoramküste des Eschentals, von der Großen Teilung zerschmettert und unter die Wellen des Verhüllten Meeres versunken. Seine überfluteten Höhlen und zerbrochenen Ruinen führen tief hinab zu einem Schrein der Alten Götter. Naga und Satyrn ergründen seine Geheimnisse, der Kult des Schattenhammers arbeitet an ihrer Seite, und in der Tiefe soll das uralte Ungeheuer Aku'mai hausen, ein Liebling der Alten Götter. Kaltes Wasser, glitschiger Stein und ein trübes, unheimliches Licht füllen die Grotte.""",

    70: """Uldaman: Ein uraltes Gewölbe der Titanen tief im nördlichen Ödland, kürzlich von zwergischen Grabungen geöffnet, die die Troggs freiließen, die ersten misslungenen Schöpfungen der Titanen. Legenden zufolge birgt das Gewölbe die Geheimnisse der Erschaffung der Zwerge auf den sagenhaften Scheiben von Norgannon. Dunkeleisenzwerge graben hier für ihren Herrn Ragnaros, während lebende Steinwächter jeden Eindringling zermalmen. Gewaltige Hallen aus gemeißeltem Stein, eingestürzte Gänge und stille Titanenmaschinen liegen unter der Last der Berge.""",

    90: """Gnomeregan: Das technologische Wunder, das einst die Hauptstadt der Gnome unter dem Schnee von Dun Morogh war, verloren, als Troggs aus der Tiefe eindrangen und die Gnome in ihrer Verzweiflung den radioaktiven Abfall der Stadt freisetzten. Die verstrahlten, aber ungebrochenen Troggs streifen noch durch die Hallen, und die überlebenden Gnome flohen nach Eisenschmiede. Der Verräter Robogenieur Thermadrahts herrscht als wahnsinniger Technoherr über die Ruinen. Ratternde Maschinen, undichte Rohre, giftiger Schlamm und Alarmroboter füllen die verwinkelten Gänge.""",

    109: """Tempel von Atal'Hakkar: Der Tempel, den die verbannten Atal'ai-Priester in den Sümpfen des Elends errichteten, um die Rückkehr des Blutgottes Hakkar des Seelenschinders vorzubereiten. Der Drachenaspekt Ysera versenkte ihn im Moor, und ihre grünen Drachen bewachen noch immer die versunkenen Ruinen, einige von ihnen bereits verderbt. Doch fanatische Atal'ai haben im Inneren überlebt und dienen Hakkar weiterhin. Überflutete Hallen, bröckelnder Stein und Trollgötzen liegen in trübem Wasser, und die Luft ist schwer von Fäulnis und alter Blutmagie.""",

    129: """Hügel der Klingenhauer: Die angestammten Grabhügel und traditionelle Hauptstadt der Stacheleber, ein ausgedehntes Dornenlabyrinth am Südrand des Brachlands, gewachsen aus denselben mächtigen Ranken wie der Kral der Klingenhauer. Ein drohender Schatten ist auf ihn gefallen: Man sagt, die Geißel habe sich der Hügel bemächtigt, ein Lich befehle den Hohepriestern der Totenköpfe, und die Toten der Grabhügel erhöben sich wieder. Kalter Nebel hängt in den Dornen, und der Gestank des Todes mischt sich mit Schlamm und Gestrüpp.""",

    189: """Das Scharlachrote Kloster: Einst ein stolzes Zentrum der Gelehrsamkeit der Priesterschaft Lordaerons im Nordosten von Tirisfal, heute eine Festung des fanatischen Scharlachroten Kreuzzugs, der niemandem traut, der kein Mensch ist, und in jedem Fremden einen Träger der Seuche sieht. Friedhof, Bibliothek, Waffenkammer und Kathedrale werden von eifrigen Kriegern unter Scharlachrotkommandant Mograine gehalten, während Hochinquisitorin Weißsträhne, von der es heißt, sie erwecke Gefallene erneut zum Kampf, die wahre Herrin des Klosters ist. Rote Banner, Weihrauch und die Rufe der Gläubigen füllen seine Hallen.""",

    209: """Zul'Farrak: Die ummauerte Stadt der Sandwuttrolle in den Wüsten des nordwestlichen Tanaris, sonnenverbrannter Stein und Pyramiden, die aus den Dünen ragen. Ihre Krieger, Priester und Hexendoktoren verteidigen sie erbittert und erwecken die Toten zu ihrem Schutz. Legenden erzählen von einem mächtigen Trollschwert, das in zwei Teile zerbrochen irgendwo im Inneren liegt, von Söldnern, die in die Stadt gerieten und nie wieder gesehen wurden, und von einem uralten Wesen, das im heiligen Teich in ihrem Herzen schläft. Hitze, Sand und Skorpide sind überall.""",

    229: """Schwarzfelsspitze: Die Festung in den oberen Bereichen des Schwarzfels, erbaut vom Dunkeleisen-Baumeister Franclorn Schmiedevater als Symbol ihrer Macht. Die orcische Horde machte sie im Zweiten Krieg zu ihrer Hauptstadt. Heute wird sie von der Dunklen Horde unter Kriegshäuptling Rend Schwarzfaust mit Orcs, Ogern und Trollen gehalten, und vom schwarzen Drachen Nefarian und seinen Drachkin, die die obere Spitze beherrschen und gegen Ragnaros in der Tiefe Krieg führen. Lava, Ketten, eiserne Tore und im Rauch kreisende Drachen machen sie zu einer gewaltigen, tödlichen Festung.""",

    230: """Schwarzfelstiefen: Die einst große Hauptstadt der Dunkeleisenzwerge, ein vulkanisches Labyrinth tief im Schwarzfels, heute von Imperator Dagran Thaurissan als Machtsitz des Feuerfürsten Ragnaros regiert. Schmieden lodern, Lava fließt durch die Hallen, Golems aus lebendem Stein werden für das Heer des Feuerfürsten gebaut, und eine Arena, ein Gefängnis und eine Taverne liegen zwischen den gewaltigen Kammern. Soldaten der Dunkeleisenzwerge, Feuerelementare und versklavte Gefangene füllen die Stadt. Die Hitze ist erdrückend, und das Hämmern hört nie auf.""",

    269: """Der Schwarze Morast: Eine Reise durch die Höhlen der Zeit in die Sümpfe des Schwarzen Morasts, an den Tag, an dem Medivh, der letzte Wächter von Tirisfal, das Dunkle Portal öffnete und die orcische Horde nach Azeroth ließ. Der bronzene Drachenschwarm bewacht diesen Augenblick, denn der Ewige Drachenschwarm schickt Welle um Welle durch Risse in der Zeit, um Medivh zu töten und die Geschichte zu ändern. Nebel, stehendes Wasser und verkrümmte Bäume umgeben das wachsende Portal, und die Zeit selbst scheint zu beben.""",

    289: """Scholomance: Eine Schule der Nekromantie in den Grüften unter Caer Darrow, einer alten Burg auf einer Insel im Darrowmere-See. Die Adelsfamilie Barov überließ die Burg dem Kult der Verdammten Kel'Thuzads gegen versprochene Unsterblichkeit, und der Kult machte ihre Grüfte zu einer Akademie, die jene ausbildete, die die Seuche verbreiteten. Die Barovs wandeln nun als Untote durch ihre Hallen, der Lich Ras Frostraunen bewacht sie für die Geißel, und der Nekromant Dunkelmeister Gandling herrscht als Direktor. Kerzen, Knochen und verbotene Folianten füllen ihre Unterrichtsräume.""",

    329: """Stratholme: Die zweite Stadt Lordaerons, in der der Orden der Silbernen Hand gegründet wurde und in der Prinz Arthas die von der Seuche befallene Bevölkerung niedermachte. Heute ist sie die Hauptstadt der Geißel in Lordaeron und brennt bis heute. Die Stadt ist geteilt zwischen dem Scharlachroten Kreuzzug, der die Scharlachrote Bastion unter Großkreuzfahrer Dathrohan hält, und der Geißel, deren Todesritter Baron Totenschwur über die Zikkurate der östlichen Viertel herrscht. Asche treibt über zerstörte Straßen, und die Plätze sind voller Toter.""",

    349: """Maraudon: Ein heiliger Ort der Zentauren im Tal der Speere in Desolace, das Grab Zaetars, eines Sohnes des Cenarius, und die Heimat der Erdelementarprinzessin Theradras, der Mutter des Zentaurenvolkes. Ihre verfluchten Kinder töteten ihren Vater, und Theradras bewahrt seinen Leichnam in ihren Kristallhöhlen auf. Der Segen der Natur verwandelte seine Ruhestätte in ein unterirdisches Paradies aus Blumen und Teichen, während purpurfleckige Höhlen, Erdelementare und die Geister der Zentaurenkhane das Labyrinth füllen. Die Maraudine-Zentauren bewachen es erbittert.""",

    389: """Der Flammenschlund: Ein Netz vulkanischer Höhlen unter Orgrimmar, voller Lava und Feuer. Troggs sind aus der Tiefe heraufgekrochen und weisen jeden Friedensversuch zurück, und ein Kult, der der Brennenden Klinge und dem Schattenrat treu ist, hat im Schlund Zuflucht gesucht und plant, alles zu zerstören, was die Horde in Durotar aufgebaut hat. Die Tunnel sind glühend heiß, das Licht ist rot, und das Zischen geschmolzenen Gesteins verstummt nie, eine Gefahr direkt unter der Hauptstadt.""",

    429: """Düsterbruch: Die Ruinen von Eldre'Thalas, einer Stadt der Hochgeborenen, vor zwölftausend Jahren im Norden von Feralas erbaut, um die kostbarsten arkanen Geheimnisse Königin Azsharas zu hüten. Von der Großen Teilung verwüstet, steht doch noch vieles. Gordunni-Oger beherrschen das nördliche Viertel, Satyrn und verderbte Uralte bevölkern die östlichen Gärten, und die letzten Hochgeborenen, die verschwiegenen Shen'dralar, halten die westlichen Hallen und ihre große Bibliothek und hüten die uralten Übel, die in den Gewölben eingeschlossen sind. Zerbrochener Marmor, elfische Bögen und überwucherte Höfe füllen die Stadt.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Onyxias Hort: Eine vulkanische Höhle im Drachensumpf der südlichen Düstermarschen, der Hort Onyxias, der Brutmutter der schwarzen Drachen und Tochter Todesschwinges. Ein enger Tunnel aus versengtem Fels führt an Welpen und Drachkin vorbei in eine riesige Halle voller Knochen und Gelege. Der Boden der Höhle ist nur eine dünne Kruste über geschmolzenem Gestein, und die Luft ist dick von Rauch und Schwefel. Onyxia selbst erfüllt die Halle mit Feuer und Schatten, und nur wenige, die ihren Hort betreten, kehren zurück.""",

    309: """Zul'Gurub: Die uralte Hauptstadt des Gurubashi-Reiches im Nordosten des Schlingendorntals, eine riesige Trollstadt aus Tempeln und Zikkuraten, vom Dschungel überwuchert. Vor über tausend Jahren beschworen die Atal'ai Hakkar den Seelenschinder und zerbrachen das Reich; nun ist der Blutgott im Herzen der Ruinen zurückgekehrt. Die Hohepriester, die die Stämme sandten, um ihn aufzuhalten, Verfechter der Fledermaus, des Panthers, des Tigers, der Spinne und der Schlange, sind seinem Bann verfallen und nähren seine Macht. Blutrituale, Trommeln und die Schreie der Dschungeltiere erfüllen die Luft.""",

    409: """Geschmolzener Kern: Das brennende Herz des Schwarzfels, ganz unten in den Tiefen, wo Thaurissan den Feuerfürsten Ragnaros in die Welt beschwor. Der Feuerfürst haust hier in einem Feuersee, der als Riss zur Elementarebene dient, und seine Diener, die Flammenschuppen und ihr Majordomus Exekutus, befehligen die Elementare und die versklavten Dunkeleisenzwerge. Lavaströme fließen zwischen Obsidianplattformen, Kernhunde und geschmolzene Riesen streifen durch die Höhlen, und die Hitze ist überwältigend.""",

    469: """Pechschwingenhort: Der Hort des schwarzen Drachen Nefarian ganz oben auf der Schwarzfelsspitze, wo er plant, Ragnaros zu vernichten und den ganzen Schwarzfels an sich zu reißen. Wie sein Vater Todesschwinge züchtet er ein neues Heer und experimentiert mit dem Blut aller Drachenschwärme, um unaufhaltsame Krieger zu erschaffen. Laboratorien, Unterdrückungskammern und Drachenbrutstätten füllen den Hort, bewacht von schwarzen Drachkin und seinen schrecklichsten Schöpfungen. Hitze, Rauch und der Gestank von Drachenblut hängen in den Hallen.""",

    509: """Ruinen von Ahn'Qiraj: Die äußeren Ruinen der Stadt Ahn'Qiraj hinter dem Skarabäuswall im südlichen Silithus, wo die Qiraji und ihre Silithiden vor tausend Jahren am Ende des Krieges der Treibsande eingeschlossen wurden. Die Tore sind wieder geöffnet, und die Heere der Allianz und der Horde haben die Qiraji in die Ruinen zurückgedrängt. Gewaltige Steinbauten und Säulen ragen zwischen Silithidenbauten aus dem Sand, und die Generäle der Qiraji und ihre Schwärme verteidigen die Ruinen erbittert.""",

    531: """Tempel von Ahn'Qiraj: Der große Tempel im Herzen von Ahn'Qiraj im südlichen Silithus, Festung der Kaiser der Qiraji und ihrer Silithidenschwärme. Dunkles Flüstern sagt, unter ihm rege sich ein Alter Gott in seinem Hort und gewinne nach Jahrtausenden seine Kraft zurück, und die Drachen, die sich einst für seine Einkerkerung opferten, lägen geschwächt oder versklavt darin. Riesige insektenartige Hallen, pulsierende Bauten und verdrehte Kammern führen immer tiefer, und mit jedem Schritt wächst ein fremdartiges, bedrückendes Grauen.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Die Zerschmetterten Hallen: Der innerste Flügel der Höllenfeuerzitadelle auf der Höllenfeuerhalbinsel, Übungsplatz und Kaserne der Teufelsorcs. Hier befehligt Kriegshäuptling Kargath Messerfaust die Teufelshorde, Hexenmeister des Schattenrats wirken dunkle Magie, Gladiatoren kämpfen in der Arena, und Bogenschützen lassen Feuer auf die engen Gänge regnen. Die Hallen sind brutal, eng und erfüllt vom Klirren der Waffen, und jede ist getränkt von Blut und Teufelsenergie.""",

    542: """Der Blutkessel: Ein Flügel der Höllenfeuerzitadelle, in dem die Teufelsorcs den gefangenen Grubenlord Magtheridon zur Ader lassen und mit seinem Blut eine neue Teufelshorde züchten, durchdrungen von dämonischer Macht. Bottiche voll verderbten Blutes, Zellen mit Gefangenen und angekettete Hexenmeister säumen die Hallen. Zauberer der Teufelsorcs lenken die Energie des darunter gefangenen Dämons, und die Luft ist schwer von Teufelsdämpfen, Hitze und Schreien.""",

    543: """Höllenfeuerbollwerk: Die befestigten Außenmauern und Türme der Höllenfeuerzitadelle, die erste Verteidigungslinie der Teufelsorcs. Teufelsorcs patrouillieren auf den Zinnen, ihre Wachmeister befehligen die Mauern, und ein Verfechter der Teufelsorcs reitet auf einem Netherdrachen über die Türme. Das Bollwerk überblickt die rote Einöde, das Dunkle Portal und die Schmieden der Legion. Wind, Teufelsfeuer und das Brüllen der Drachen erfüllen die Luft.""",

    545: """Die Dampfkammer: Das Herz des Echsenkessels in den Zangarmarschen, wo die Naga Lady Vashjs gewaltige dampfbetriebene Maschinen und Pumpen betreiben, die das Wasser des Sumpfes ablassen. Nagakrieger, Sirenen und Wasserelementare bewachen die Kammer, und versklavte Zerschlagene schuften in den Hallen. Zischende Rohre, dröhnende Turbinen und Dampfwolken füllen die Luft, und von den Wänden rinnt Kondenswasser. Das Summen der Maschinen hört nie auf.""",

    546: """Der Tiefensumpf: Ein Flügel des Echsenkessels in den Zangarmarschen, Heimat des letzten natürlichen Lebens des Sumpfes, das die Naga noch nicht ausgelöscht haben. Riesenpilze, Sumpflords, Sporenfledermäuse und hungrige Tiere gedeihen in seinen Höhlen, während die Naga einen Tempel verteidigen, in dem sie ihren Hydragott Ghaz'an halten. Leuchtende Pilze, trübes Wasser und dicke, sporenschwere Luft machen ihn zu einem wilden, ungezähmten Ort.""",

    547: """Die Sklavenunterkünfte: Der erste Flügel des Echsenkessels in den Zangarmarschen, wo die Naga Lady Vashjs versklavte Zerschlagene und Sumpflords an ihren großen Pumpen arbeiten lassen. Nagaaufseher und ihre Diener patrouillieren durch die Pferche, während die Versklavten in Ketten schuften. Holzstege, Eisenkäfige und tropfendes Wasser füllen die Hallen, und die Schreie der Gefangenen hallen über den Kessel.""",

    552: """Die Arkatraz: Ein Satellit der Festung der Stürme im Nethersturm, in dem die Naaru die gefährlichsten Wesen einsperrten, denen sie auf ihren Reisen begegneten: Dämonen, Agenten des schwarzen Drachenschwarms und sogar Diener der Alten Götter. Die Blutelfen Kael'thas' bewachen sie nun, doch sie sind bestechlich, und die Gefangenen brechen aus. Zellen aus schimmernder Kraft, Kristallgänge und das Heulen entflohener Schrecken füllen das Gefängnis.""",

    553: """Die Botanika: Ein Satellit der Festung der Stürme im Nethersturm, in dem Blutelfenforscher, die Kael'thas treu sind, mit gestohlener Naarutechnik an den Pflanzen und Kreaturen der Scherbenwelt experimentieren, auf der Suche nach neuen Kräften. Gärten seltsamer Flora wachsen unter Kristallkuppeln, doch die Experimente sind außer Kontrolle geraten, und mutierte Pflanzen und wütende Baumwesen füllen nun die Hallen. Die Luft ist feucht und dick von Pollen.""",

    554: """Die Mechanar: Ein Satellit der Festung der Stürme im Nethersturm, von Kael'thas zu einer Fabrik umgebaut, die mit Naarutechnik gewaltige Energiemengen erzeugt, gespeichert in Manazellen, die sich zu Wänden und Haufen türmen. Blutelfen unter dem Befehl von Pathaleon dem Kalkulator bedienen die Maschinen, unterstützt von Dämonen der Brennenden Legion. Summende Motoren, arkane Leitungen und ratternde Konstrukte füllen die violetten Kristallhallen.""",

    555: """Schattenlabyrinth: Der tiefste Flügel von Auchindoun in den Wäldern von Terokkar, wo der Schattenrat ein uraltes Elementar des Klangs beschwor, dessen Ritual die Nekropole sprengte. Der Rat schmiedet hier noch immer Ränke und versucht, das entfesselte Wesen einzudämmen und zu nutzen, unterstützt von Teufelsorcs und Dämonen. Lange Hallen, Ritualkammern und ein ständiges, ohrenbetäubendes Echo füllen das Labyrinth, und die Luft selbst bebt.""",

    556: """Sethekkhallen: Ein Flügel von Auchindoun in den Wäldern von Terokkar, gehalten von den Sethekk, abtrünnigen Arakkoa, die sich unter dem wahnsinnigen Klauenkönig Ikiss von Skettis lossagten. Sie glauben, die Zerstörung Auchindouns habe die Rückkehr ihres Meisters angekündigt, und suchen ihn in den Ruinen. Federgötzen, Ritualfeuer und dunkle Magie füllen die alten Hallen der Draenei, und die Schreie der Arakkoa hallen durch sie.""",

    557: """Managruft: Ein Flügel von Auchindoun in den Wäldern von Terokkar, in dem abtrünnige Astrale unter Nexusprinz Shaffar die Grüfte plündern und den Ruinen arkane Energie entziehen. Schutzzauber halten ihre Rivalen vom Konsortium fern. Schimmernde Energie, schwebende Trümmer und die ruhelosen Geister der toten Draenei füllen die Gruft, und die Hallen summen vor gestohlener Macht.""",

    558: """Auchenaikrypta: Ein Flügel von Auchindoun in den Wäldern von Terokkar, die Grabgewölbe der Draenei, in denen die Priester der Auchenai ihre geehrten Toten pflegten. Seit die Nekropole zerstört wurde, sind die Krypten der Finsternis anheimgefallen: Dämonen der Brennenden Legion ernten hier Seelen, und die toten Draenei erheben sich als ruhelose Geister und Untote. Kalter Stein, verblasstes heiliges Licht und das Flüstern der Toten füllen die Hallen.""",

    560: """Vorgebirge des Alten Hügellands: Eine Reise durch die Höhlen der Zeit ins Hügelland Jahre vor dem Dritten Krieg, als der junge Orc Thrall ein Sklave Aedelas Schwarzmoores in Burg Durnholde war und die Orcs in Internierungslagern dahinsiechten. Der bronzene Drachenschwarm bewacht den Augenblick seiner Flucht, denn der Ewige Drachenschwarm will ihn ändern. Grüne Hügel, friedliche Höfe, die Stadt Süderstade und die Steinmauern von Durnholde erscheinen, wie sie einst waren.""",

    568: """Zul'Aman: Die Tempelstadt der Amani-Waldtrolle in den östlichen Geisterlanden, der letzte Rest des Reiches, das sich einst über Lordaeron erstreckte, bevor Menschen und Hochelfen es gemeinsam zerschlugen. Kriegsherr Zul'jin, der den Elfen nie vergab, hat seine Trolle gesammelt und mit Hilfe des Hexlords die Macht der Tiergötter der Amani, Bär, Adler, Luchs und Drachenfalke, in seine stärksten Verfechter gebannt. Stufenzikkurate, Voodoototems und Trommeln füllen den dunklen, urtümlichen Wald.""",

    585: """Terrasse der Magister: Eine elegante Anlage der Blutelfen an der Nordostecke der Insel von Quel'Danas, mit einem Observatorium, das auf den Sonnenbrunnen blickt. Sie wird von Anhängern Kael'thas Sonnenwanderers gehalten, der sich hierher zurückgezogen haben soll, und die Hallen summen vor gestohlener arkaner Macht und der Energie von Manakristallen. Goldene Türme, Gärten und Observatoriumskuppeln füllen die Terrasse, schön und gefährlich.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan: Der Elfenbeinturm Medivhs, des letzten Wächters von Tirisfal, im Gebirgspass der Totenwinde, errichtet auf einem Knotenpunkt von Kraftlinien, wo die Wirklichkeit dünn ist. Nach Medivhs Tod legte sich ein schrecklicher Fluch über den Turm und das umliegende Land. Nun ist er erwacht: Eine böse Macht hat ihn beansprucht, seine Hallen wimmeln von Geistern und Dämonen, geisterhafte Adlige aus Dunkelhain erleben ein endloses Festmahl, und Echos der Vergangenheit spielen sich in seinen Bibliotheken, seinem Opernsaal und seiner Menagerie ab. Staubige Pracht und kalte Magie füllen jeden Raum.""",

    534: """Hyjalgipfel: Eine Reise durch die Höhlen der Zeit an die Hänge des Berges Hyjal am Ende des Dritten Krieges, als Menschen, Orcs und Nachtelfen gemeinsam gegen die Brennende Legion und die Geißel standen. Der Dämonenfürst Archimonde zieht den Berg hinauf, um dem Weltenbaum Nordrassil seine Macht zu entziehen. Der bronzene Drachenschwarm bewahrt die Schlacht, wie sie war, während die Verteidiger von Lager zu Lager zurückweichen. Uralte Wälder, der große Baum oben und die brennenden Heere der Legion unten.""",

    544: """Magtheridons Kammer: Eine Kammer tief unter der Höllenfeuerzitadelle, in der der Grubenlord Magtheridon, einst Herr der Scherbenwelt, angekettet liegt, seit Illidan ihn besiegte. Sein Blut wird geerntet, um die Teufelshorde zu züchten, und Kanalisierer des Höllenfeuers halten seine Fesseln aufrecht. Die Höhle bebt unter seinem Zorn, die Decke bekommt Risse unter seiner Macht, und Teufelsfeuer flackert um den Käfig. Es ist ein Ort roher dämonischer Wut.""",

    548: """Höhle des Schlangenschreins: Der Unterschlupf Lady Vashjs, der Nagazauberin in Illidans Diensten, tief im Echsenkessel in den Zangarmarschen, wo sich das aus dem Sumpf gepumpte Wasser sammelt. Ihre mächtigsten Diener, von einem verderbten Wasserelementar bis zu einem Lauerer in der Tiefe, bewachen den Schrein, und die Gewässer wimmeln von Naga. Riesige überflutete Höhlen, Korallensäulen und schimmernde Becken leuchten in einem unheimlichen blauen Licht.""",

    550: """Festung der Stürme - Das Auge: Der innere Palast der Festung der Stürme, der Naarufestung im Nethersturm, erobert von den Blutelfen Kael'thas Sonnenwanderers, des Sonnenkönigs, der hier mit seinen Phönixen und mächtigsten Beratern herrscht. Kristallhallen, arkane Maschinen und schwebende Plattformen leuchten mit gestohlener Naaruenergie, und ein gefangener Naaru wird für seine Macht ausgezehrt. Das Auge blickt über die wirbelnden Stürme des Nethers, prächtig und kalt.""",

    564: """Der Schwarze Tempel: Einst der Tempel von Karabor, der heiligste Ort der Draenei und Zuflucht des Propheten Velen, von Gul'dan als Hauptquartier des Schattenrats erobert und später von der Brennenden Legion gehalten. Heute ist er die Festung Illidan Sturmgrimms, des selbsternannten Herrschers der Scherbenwelt, bewacht von seinen Illidari: Naga, Blutelfen, Zerschlagene, Dämonen und Teufelsorcs. Teufelsfeuer brennt in seinen Heiligtümern, Schatten füllt seine Hallen, und aus seinen Tiefen hallen die Schreie gequälter Seelen.""",

    565: """Gruuls Unterschlupf: Ein höhlenartiger Unterschlupf im nördlichen Schergrat, Heimat Gruuls des Drachenschlächters, des gnadenlosen Herrn der Gronn, und seines Sohnes, des Ogerkönigs Maulgar, die über die Oger der Berge herrschen. Die Knochen erschlagener Drachen hängen an den Wänden, und der Boden bebt unter den Schritten der Riesen. Grobe Ogerbanner, Trophäen und roher Fels füllen die riesige Höhle, ein Ort roher Kraft und Gewalt.""",

    580: """Sonnenbrunnenplateau: Der heiligste Ort der Elfen auf der Insel von Quel'Danas, wo der Sonnenbrunnen, die Kraftquelle, die Quel'Thalas nährte, im Herzen anmutiger Höfe und Hallen steht. In jüngerer Zeit wollte die Brennende Legion ihn als Tor für den Eredarfürsten Kil'jaeden nutzen, und die Diener der Legion, Dämonen und ihnen treue Blutelfen, halten das Plateau. Goldene Türme, gefangene Naaru und Teufelsenergie umgeben den geschändeten Brunnen.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Burg Utgarde: Die große Festung der Vrykul auf den Klippen über dem Cauldrossee im Heulenden Fjord, in den Fjord gebaut, mit Wasserfällen, die zu beiden Seiten herabstürzen, Heimat des Drachenschinderklans. Lange still, ist sie erwacht, und ihre Krieger überfallen alle Siedlungen ringsum, angeblich im Dienst des Lichkönigs, der die würdigsten von ihnen aus dem Grab erhebt. Protodrachen, Worgs und Untote dienen den Vrykul, und je höher man in der Burg steigt, desto mächtiger sind ihre Bewohner.""",

    575: """Turm Utgarde: Die höchsten Bereiche von Burg Utgarde im Heulenden Fjord, wo die mächtigsten Vrykul wohnen und König Ymiron seinen Thron hat, begierig zu beweisen, dass sein Volk der Gunst des Lichkönigs würdig ist. Große Hallen aus Stein und Holz, gemeißelte Schädel und die Trophäen gefallener Feinde füllen den Turm, und Protodrachen kreisen über den kalten Höhen des Fjords.""",

    576: """Der Nexus: Die uralte Heimat des blauen Drachenschwarms unter der Insel Kaltarra vor der Boreanischen Tundra, eine arkane Festung aus Eis und schwebenden Kristallen, in der der Aspekt der Magie, Malygos, seinen Krieg gegen alle sterblichen Zauberkundigen führt. Die blauen Drachen und ihre Diener bewachen seine gefrorenen Hallen, und gefangene Feinde werden in Eisgefängnissen gehalten. Arkane Energie knistert in der Luft, und das Eis leuchtet vor Magie.""",

    578: """Das Oculus: Der große Turm aus schwebenden Ringen über dem Nexus auf Kaltarra, in dem Malygos die Kraftlinien Azeroths kanalisiert und die Magie der Welt durch den Nexus in den Wirbelnden Nether leitet. Die Kirin Tor und der rote Drachenschwarm kämpfen, um ihn aufzuhalten. Die Ringe treiben hoch am Himmel und knistern vor arkaner Macht, und nur Drachen tragen von einem zum anderen. Rohe Magie zerreißt die Luft, und ferne Risse reißen an der Wirklichkeit.""",

    595: """Das Ausmerzen von Stratholme: Eine Reise durch die Höhlen der Zeit an den Tag, an dem die Seuche mit verseuchtem Getreide nach Stratholme kam und Prinz Arthas, der nicht zulassen wollte, dass die Bewohner als Untote auferstehen, die Säuberung der Stadt befahl. Der Schreckenslord Mal'Ganis wacht über die sterbende Stadt, und der Ewige Drachenschwarm will den Augenblick verzerren. Die Straßen sind voller verängstigter Bürger, brennender Häuser und der ersten wandelnden Toten, ein Tag, der den Beginn von Arthas' Fall markierte.""",

    599: """Hallen des Steins: Ein Flügel der Titanenstadt Ulduar in den Sturmgipfeln, Heimat des Tribunals der Zeitalter, des gewaltigen steinernen Archivs der Geschichte der Titanen, und der Schmiede des Willens. Eisenzwerge und Steinriesen, verderbt vom gefallenen Hüter Loken, halten nun ihre Hallen und bewachen ihre Geheimnisse. Hohe Statuen, gemeißelte Reliefs und Titanenmaschinen füllen die riesigen Steinhallen, still bis auf das Grollen der Maschinen.""",

    600: """Feste Drak'Tharon: Eine alte Eistrollfestung aus Türmen und gemeißelten Mauern an der Grenze zwischen den Grizzlyhügeln und Zul'Drak, von der Geißel erobert, die die gefallenen Drakkari erhebt, um gegen ihr eigenes Reich zu kämpfen. Ihr einstiger Anführer, der Prophet Tharon'ja, wurde in eine ungeheuerliche untote Gestalt verwandelt, und untote Trolle strömen aus ihren Toren in die Hügel. Knochen, Banner der Geißel und gefrorene Trollschnitzereien füllen die Festung.""",

    601: """Azjol-Nerub: Das Obere Königreich der Neruber unter der Drachenöde, ein großartiges unterirdisches Reich der Gelehrsamkeit und Kunst, im Spinnenkrieg von der Geißel überrannt. Untote Neruber patrouillieren nun durch seine polierten Hallen und bewachen Gelege, aus denen neue Krieger der Geißel schlüpfen werden, und ihr gefallener König Anub'arak dient dem Lichkönig. Netze, gemeißelte Wandbilder und leuchtende Pilze füllen die riesigen Höhlen, während lebende Neruber einen verborgenen, verlorenen Krieg führen.""",

    602: """Hallen der Blitze: Der östliche Flügel der Titanenstadt Ulduar in den Sturmgipfeln, wo der gefallene Hüter Loken auf seinem Thron sitzt und massenhaft eiserne Vrykul und Konstrukte für seine dunklen Zwecke erschafft. Sturmelementare, Eisenriesen und blitzgeschmiedete Wächter dienen ihm, und große Schmieden und Maschinen donnern überall. Blitze knistern durch die riesigen Hallen aus Stein und Metall.""",

    604: """Gundrak: Die Hauptstadt der Drakkari-Eistrolle in Zul'Drak, eine riesige Stadt aus dicken Mauern, hohen Türmen und gestuften Bauten, ineinander verschlungen wie ein Nest. In ihrer Verzweiflung gegen die Geißel haben ihre Hohepropheten die eigenen Götter, die Loa, erschlagen und trinken ihr Blut für Macht, sodass die heiligen Schreine von der Kraft erschlagener Götter durchtränkt sind. Götzen von Nashorn, Schlange und Mammut stehen in den Höfen, und Trommeln hallen durch die gestuften Straßen.""",

    608: """Die Violette Festung: Das Gefängnis der Kirin Tor in Dalaran, dessen magisch geschützte Zellen mächtige und gefährliche Gefangene festhalten. Der blaue Drachenschwarm des Malygos ist durch einen großen Riss im Dach eingebrochen und strömt durch Portale ins Innere, prüft die Verteidigung des Gefängnisses und befreit seine Insassen. Arkane Schutzzauber flackern, violetter Stein leuchtet, und die Wachen der Kirin Tor kämpfen, um die Linie zu halten.""",

    619: """Ahn'kahet: Das Alte Königreich, die tiefsten Bereiche von Azjol-Nerub unter der Drachenöde, eine riesige unterirdische Stadt des uralten Nerubianerreiches. Neruber der Geißel und die geheimnisvollen Gesichtslosen halten sie, letztere sollen einer bösen Macht dienen, die unter Nordend lauert, und der Schattenhammer regt sich unter ihnen. Pilzwälder, große, von Netzen verhangene Kammern und eine bedrückende Finsternis füllen die Tiefe.""",

    632: """Die Seelenschmiede: Die erste der Gefrorenen Hallen in der Eiskronenzitadelle, eine riesige Produktionsstätte, in der Seelenmühlen gebaut werden, die neuesten üblen Konstrukte des Lichkönigs. Gequälte Seelen werden zwischen Saronitsäulen und geisterhaften Ketten in die Maschinen gebunden. Die Luft ist schwer von Verzweiflung und dem Stöhnen der Toten.""",

    650: """Prüfung des Champions: Der Turnierplatz des Argentumkreuzzugs unter dem Argentumkolosseum in der Eiskrone, wo Verfechter der Allianz und der Horde tjosten und sich duellieren, um ihren Wert für den Krieg gegen den Lichkönig zu beweisen. Reittiere, Lanzen, Banner und das Brüllen der Menge füllen die Arena, festlich und stolz, auch wenn die Geißel nie weit ist.""",

    658: """Grube von Saron: Die große Saronitmine unter der Eiskronenzitadelle, in der die Geißel Gefangene der Allianz und der Horde unter der Peitsche des Geißelfürsten Tyrannus das Erz für ihre Festungen schürfen lässt. Saronitadern pulsieren in den Wänden, Sklaven schuften in Ketten, und die Toten werden erweckt, um weiterzuarbeiten. Kälte, Dunkelheit und das Knallen der Peitschen füllen die Grube.""",

    668: """Hallen der Reflexion: Die privaten Gemächer des Lichkönigs in der Eiskronenzitadelle, der einzige Ort, an dem er seine Wachsamkeit sinken lässt, ein dunkles, verzerrtes Abbild des Thronsaals von Lordaeron. Frostgram, die Runenklinge des Lichkönigs, wartet hier, und die in ihr gefangenen Geister spuken durch die Hallen. Eis, Stille und Erinnerungen an die Vergangenheit füllen die Gemächer.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas: Eine Nekropole der Geißel, die über der Drachenöde schwebt, einst ein Zikkurat der Neruber, von der Geißel überrannt und durch die dunkle Magie des Lichkönigs in den Himmel gehoben. Sie ist der Sitz des Erzlichs Kel'Thuzad, der sie nach Nordend zurückgebracht hat, um Wintergarde zu belagern. Ihre vier Viertel bergen Schrecken aller Art: spinnenartige Gruftlords, Seuchenlaboratorien und Monstrositäten, Legionen von Todesrittern und aus Fleisch genähte Konstrukte. Grüner Schleim, verwesendes Fleisch und die Kälte des Grabes füllen ihre Hallen.""",

    603: """Ulduar: Die größte Titanenanlage Azeroths, vollkommen erhalten im Schnee der Sturmgipfel, verborgen hinter Fels und Eis, ein Gewirr aus Tunneln, Treppen und Balkonen, aus einer riesigen Höhle gehauen. Es war die Heimat der Hüter der Titanen und ihrer Schöpfungsmaschinen, doch man flüstert von einem großen Übel hinter seinem Fall, und seine verderbten Wächter wenden sich gegen alle Eindringlinge. Gewaltige Statuen, Titanenmaschinen und sternenvolle Observatorien füllen seine Hallen.""",

    615: """Das Obsidiansanktum: Die Kammer des schwarzen Drachenschwarms unter dem Wyrmruhtempel in der Drachenöde, Teil der Kammer der Aspekte, in der Sartharion der Onyxwächter ein Gelege von Zwielichtdracheneiern bewacht. Drei Zwielichtdrachen hüten ihre eigenen Inseln zwischen Lavaströmen und Obsidianplattformen. Die Kammer glüht orange und rot, und Hitze flimmert in der Luft.""",

    616: """Das Auge der Ewigkeit: Das persönliche Reich des blauen Aspekts Malygos hoch über dem Nexus auf Kaltarra, von dem aus er seinen Krieg führt, um die Herrschaft über die arkanen Energien Azeroths zurückzugewinnen. Es ist eine riesige schwebende Plattform in einer endlosen Leere aus wirbelnder arkaner Energie und Sternen, wo die Magie der Welt fließt. Rohe Macht erfüllt die Luft.""",

    624: """Archavons Kammer: Ein Gewölbe der Titanen unter der Festung Tausendwinter, das Relikte unvorstellbarer Macht birgt, bewacht von uralten steinernen Wächtern, die jeden Eindringling verabscheuen. Seine Hallen öffnen sich nur jenen, die die Festung darüber halten. Gemeißelter Stein, Titanenmaschinen und eine unheimliche Stille füllen das Gewölbe.""",

    631: """Eiskronenzitadelle: Die Festung des Lichkönigs, die sich aus dem schwarzen Eis der Eiskrone erhebt, eine Kathedrale aus Saronitklingen und -türmen rund um den Frostthron. Ihre Hallen wimmeln von den treuesten und abscheulichsten Dienern der Geißel: Todesritter, Kultisten, Monstrositäten und Frostwyrms. Die Untere Spitze, die Seuchenwerke, die Purpurrote Halle und die Frostschwingenhallen führen zum Thron. Das Äscherne Verdikt führt den Angriff, und die Kälte dringt bis in die Knochen.""",

    649: """Prüfung des Kreuzfahrers: Das große Argentumkolosseum in der Eiskrone, vom Argentumkreuzzug erbaut, um die Verfechter zu prüfen, die des letzten Angriffs auf den Lichkönig würdig sind. Banner der Allianz und der Horde wehen über jubelnden Rängen, und furchterregende Bestien und Verfechter werden unter den Augen von Hochlord Tirion Fordring in die Arena geführt. Prunk und Schauspiel entfalten sich direkt vor der Tür des Lichkönigs, und auf den Rängen lodert die alte Rivalität der beiden Fraktionen.""",

    724: """Das Rubinsanktum: Das Heiligtum des roten Drachenschwarms unter dem Wyrmruhtempel in der Drachenöde, Teil der Kammer der Aspekte, eine friedliche Zuflucht für die Eier der roten Drachen, voll warmen Lichts und grünen Wachstums. Seine Wächter sind verstummt, und die Wachen am Portal wurden erschlagen; eine dunkle Macht ist in das Sanktum eingedrungen, und Zwielichtdrachen bedrohen nun die Eier des roten Schwarms.""",

    # -------------------------------------------------------------------------
    # Arenas
    # -------------------------------------------------------------------------
    559: """Arena von Nagrand: Der Ring der Prüfungen in den Graslanden von Nagrand, ein uralter Prüfungsort der Orcs, im Stil des alten Ogerreiches erbaut. Gladiatoren aller Völker treffen sich hier, um um Ruhm zu kämpfen. Ein Ring verwitterter Steinsäulen steht unter offenem Himmel, der Wind streicht über das Gras, und Zuschauer sehen von den Hügeln zu.""",

    562: """Arena des Schergrats: Der Kreis des Blutes im Schergrat, eine von Ogern erbaute Arena, in der Gladiatoren vor brüllender Menge um Ruhm kämpfen. Eine Holzbrücke überspannt eine Grube in ihrer Mitte, Seile und Säulen durchziehen den Ring, und ringsum ragen gezackte Gipfel auf. Grobes Holz, Knochen und Banner verleihen ihr ein brutales, wildes Aussehen.""",

    572: """Ruinen von Lordaeron: Eine Arena inmitten der zerschmetterten Ruinen der Hauptstadt Lordaerons in Tirisfal, über Unterstadt, wo der große Palast noch als traurige Erinnerung an den Fall der Stadt steht. Zerbrochene Mauern, umgestürzte Statuen und ein zerstörtes Grabmal umgeben den Kampfplatz, und die Erinnerung an das tragische Ende des Königreichs liegt über den Steinen.""",

    617: """Kanalisation von Dalaran: Eine Arena, verborgen in der Schattenseite, der Kanalisation unter der schwebenden Stadt Dalaran, in der Gladiatoren in einer Grube kämpfen, umgeben von Wasserrinnen und Rohren. Feuchter Stein, das Rauschen des Wassers und das Murmeln einer rauen Menge füllen die Arena, fern der Pracht der violetten Stadt darüber.""",

    618: """Der Ring der Ehre: Die große Arena im Tal der Ehre in Orgrimmar, in der die Gladiatoren des Purpurroten Rings trainieren und kämpfen. Säulen ragen aus dem Boden, die Zuschauer brüllen auf den Rängen, und die Hitze Durotars brennt auf den Sand. Es ist ein Ort der Ehre, der Stärke und des Schauspiels.""",
}
