# -*- coding: utf-8 -*-
"""esES locale data for mod-llm-chatter.

Split out of chatter_constants.py so the central module stays
readable: the language tables are bulk data that changes for
translation reasons, not logic that changes with the module.

Names here are unsuffixed -- the locale is the module. The
registry in this package maps locale codes onto these.
"""

ZONE_NAMES = {
    1: "Dun Morogh", 3: "Tierras Inhóspitas", 4: "Las Tierras Devastadas",
    8: "Pantano de las Penas", 10: "Bosque del Ocaso", 11: "Los Humedales",
    12: "Bosque de Elwynn", 14: "Durotar", 15: "Marjal Revolcafango",
    16: "Azshara", 28: "Tierras de la Peste del Oeste",
    33: "Vega de Tuercespina", 38: "Loch Modan", 40: "Páramos de Poniente",
    41: "Paso de la Muerte", 44: "Montañas Crestagrana",
    45: "Tierras Altas de Arathi", 46: "Las Estepas Ardientes",
    47: "Tierras del Interior", 51: "La Garganta de Fuego",
    85: "Claros de Trisfal", 130: "Bosque de Argénteos",
    139: "Tierras de la Peste del Este", 141: "Teldrassil",
    148: "Costa Oscura", 215: "Mulgore", 267: "Laderas de Trabalomas",
    331: "Vallefresno", 357: "Feralas", 361: "Frondavil",
    400: "Las Mil Agujas", 405: "Desolace", 406: "Sierra Espolón",
    440: "Tanaris", 490: "Cráter de Un'Goro", 493: "Claro de la Luna",
    495: "Fiordo Aquilonal",  # verified: official Blizzard es-es news source
    618: "Cuna del Invierno", 1377: "Silithus", 1497: "Entrañas",
    1519: "Ciudad de Ventormenta", 1537: "Forjaz", 1637: "Orgrimmar",
    1638: "Cima del Trueno", 1657: "Darnassus",
    3483: "Península del Fuego Infernal",  # verified: official Blizzard es-es news source
    3537: "Tundra Boreal",  # verified: official Blizzard es-es news source
    65: "Cementerio de Dragones",  # verified: official Blizzard es-es news source
    66: "Zul'Drak",  # verified: official Blizzard es-es news source
    67: "Cumbres Tormentosas",  # verified: official Blizzard es-es news source
    210: "Corona de Hielo",  # verified: official Blizzard es-es news source
    394: "Colinas Pardas",  # verified: official Blizzard es-es news source
    3711: "Cuenca de Sholazar",  # verified: official Blizzard es-es news source
    3522: "Montañas Filoespada", 3523: "Tormenta Abisal",
    3520: "Valle Sombraluna", 3519: "Bosque de Terokkar",
    3521: "Marisma de Zangar", 2817: "Bosque Canto de Cristal",
    4197: "Conquista del Invierno", 3524: "Isla Bruma Azur",
    3525: "Isla Bruma de Sangre", 3430: "Bosque Canción Eterna",
    3433: "Tierras Fantasma", 3487: "Ciudad de Lunargenta",
    17: "Los Baldíos", 3703: "Ciudad de Shattrath",
    3557: "El Exodar", 4228: "El Oculus",
    4080: "Isla de Quel'Danas",
}

RACE_SPEECH_PROFILES = {
    "Human": {
        "traits": [
            "prácticos, resilientes, cívicos, disciplinados y rápidos para unirse en una crisis",
            "adaptables, ambiciosos, orientados a la comunidad, guiados por el deber y la oportunidad",
            "leales a la corona y a los camaradas, forjados por la guerra y guiados por un idealismo pragmático",
            "ingeniosos y trabajadores, mezclan la aspereza de frontera con una diplomacia cosmopolita",
            "patriotas y entregados al deber, marcados por la pérdida pero tercamente esperanzados sobre el futuro",
            "socialmente perceptivos, hábiles en el comercio, e inclinados a forjar alianzas antes que rencores",
            "valientes bajo fuego, rápidos para organizarse, incómodos con la incertidumbre prolongada",
            "arraigados en la tradición pero abiertos a nuevas ideas cuando la supervivencia lo exige",
        ],
        "flavor_words": [
            "por la Alianza", "por la Luz", "Ciudad de Ventormenta",
            "Lordaeron", "la catedral", "el rey Varian",
            "honor", "deber", "el reino",
            "Northshire", "la corona", "héroes caídos",
        ],
        "vocabulary": [
            ("Light be with you", "bendición/saludo"),
            ("By the Light!", "exclamación de sorpresa o determinación"),
            ("Well met", "saludo formal"),
            ("For the Alliance!", "grito de guerra"),
            ("Go with honor, friend", "despedida"),
            ("Safe travels", "despedida"),
        ],
        "lore": [
            "Los humanos reconstruyeron Ciudad de Ventormenta tras la devastación de las primeras guerras.",
            "Los reinos humanos del norte fueron destrozados, especialmente Lordaeron por el Flagelo.",
            "La Iglesia de la Luz Sagrada influye fuertemente en la cultura y las instituciones.",
            "Las órdenes de caballería, las milicias y la tradición "
            "de la guardia urbana son pilares sociales centrales.",
            "Ciudad de Ventormenta bajo el rey Varian es un importante centro político y militar de la Alianza.",
            "Los reinos humanos equilibran idealismo, presión de supervivencia y realpolitik.",
            "Registros titánicos en Rasganorte vinculan la ascendencia humana con los vrykul.",
        ],
        "worldview": (
            "La política humana gira en torno a Ciudad de Ventormenta y el esfuerzo bélico de la "
            "Alianza. La fe en la Luz Sagrada, el servicio militar y el orden cívico son fuertes "
            "normas sociales. Tras las pérdidas en Lordaeron y las invasiones repetidas, las "
            "comunidades humanas son cautelosas, patriotas y centradas en la seguridad."
        ),
    },
    "Orc": {
        "traits": [
            "directos, orgullosos, apegados al honor, tribales, intensos y protectores de su libertad ganada",
            "fieramente leales al clan, forjados por la guerra y motivados por la necesidad de demostrar su valía",
            "directos y confrontativos, valoran la fuerza templada por la sabiduría ancestral",
            "apasionados por el honor, recelosos de la diplomacia, y rápidos para desafiar la debilidad",
            "curtidos en batalla y comunales, encuentran identidad en la lucha y la victoria compartidas",
            "espiritualmente arraigados en la tradición chamánica, aunque perseguidos por un legado de corrupción",
            "directos al hablar e impacientes con la política, prefieren la acción a la deliberación",
            "profundamente protectores de la soberanía de la Horda, recelosos de forasteros, orgullosos de sobrevivir",
        ],
        "flavor_words": [
            "Lok'tar ogar", "sangre y trueno", "por la Horda",
            "Durotar", "Orgrimmar", "los ancestros",
            "honor", "los clanes", "Thrall",
            "Draenor", "tambores de guerra", "lobos espirituales",
        ],
        "vocabulary": [
            ("Lok'tar ogar!", "¡Victoria o muerte!"),
            ("Zug-zug", "asentimiento, como 'de acuerdo'"),
            ("Dabu", "Obedezco / estoy de acuerdo"),
            ("Throm-ka", "Bien hallado"),
            ("Aka'Magosh", "Una bendición para ti y los tuyos"),
            ("Lok-Narash!", "¡Armaos!"),
            ("Gol'Kosh!", "¡Por mi hacha!"),
        ],
        "lore": [
            "Los orcos vinieron de Draenor y fueron manipulados hacia la corrupción demoníaca.",
            "Tras la Segunda Guerra, muchos fueron retenidos en campos de internamiento.",
            "Thrall unió a los clanes y fundó una nueva Horda con base en Durotar.",
            "Las tradiciones chamánicas y el respeto ancestral se recuperaron tras la corrupción anterior.",
            "La sociedad orca valora la memoria del clan, la destreza marcial y el honor personal.",
            "En la era de la Ira, el ascenso de Garrosh Grito Infernal en el mando de la Horda agudiza "
            "la tensión política.",
            "El legado de la esclavitud demoníaca sigue moldeando la identidad y el orgullo.",
        ],
        "worldview": (
            "La identidad orca en la Nueva Horda se construye sobre la recuperación de la corrupción "
            "demoníaca, la lealtad al clan y a la Horda, y las tradiciones chamánicas restauradas. "
            "Durotar y Orgrimmar representan el autogobierno tras el internamiento. El honor, la "
            "fuerza y la supervivencia se tratan como deberes inseparables."
        ),
    },
    "Dwarf": {
        "traits": [
            "robustos, tercos, orgullosos de su oficio, leales al clan, directos y curiosos por secretos antiguos",
            "inquebrantables en combate, aficionados a la bebida y las historias, y fieramente devotos de su gente",
            "toscos pero de buen corazón, con profundo respeto por la tradición y el trabajo honesto",
            "eternamente curiosos sobre las reliquias titánicas, impulsados a cavar más hondo y saber más",
            "de habla llana, cabezotas en el mejor sentido, y leales hasta la exageración",
            "orgullosos de la forja y la familia, rápidos para reír y lentos para perdonar una traición",
            "prácticos y con los pies en la tierra, confían más en martillos y apretones de manos que en palabras",
            "de espíritu recio y resiliente, forjados por inviernos de montaña y siglos de disputas de clanes",
        ],
        "flavor_words": [
            "por mi barba", "así es", "piedra y acero",
            "Forjaz", "Khaz Modan", "el clan",
            "la forja", "cerveza", "reliquias titánicas",
            "la montaña", "la Liga de Exploradores", "el yunque",
        ],
        "vocabulary": [
            ("Keep yer feet on the ground", "despedida"),
            ("Fer Khaz Modan!", "¡Por Khaz Modan! — grito de guerra"),
            ("Well met", "saludo"),
            ("Off with ye", "despedida informal"),
        ],
        "lore": [
            "Los enanos descienden de los terrígenos forjados por los titanes, alterados por la Maldición de la Carne.",
            "Tres grandes clanes definen la política: Barbabronce, Martillo Salvaje y Hierro Negro.",
            "Forjaz es un bastión clave de la Alianza y un centro comercial.",
            "La ingeniería, la herrería, las armas de fuego y la cervecería son grandes fortalezas culturales.",
            "La Liga de Exploradores impulsa la arqueología y la investigación titánica por todo Azeroth.",
            "La memoria y los rencores de clan pueden durar generaciones.",
            "Los enanos son veteranos curtidos en batalla de la Alianza en múltiples guerras.",
        ],
        "worldview": (
            "La sociedad enana está basada en clanes y fuertemente ligada a Forjaz, las tradiciones "
            "de oficio y la arqueología titánica. El servicio militar y el trabajo práctico se "
            "respetan por igual. Las alianzas se juzgan por lealtad y hechos demostrados."
        ),
    },
    "Night Elf": {
        "traits": [
            "ancestrales, reverentes, reservados, pacientes, orgullosos y fieramente protectores de la naturaleza",
            "contemplativos y mesurados, cargan milenios de memoria en cada decisión",
            "profundamente espirituales, sintonizados con los ciclos lunares, y recelosos de la imprudencia arcana",
            "gráciles pero feroces en defensa de arboledas sagradas y tierras ancestrales",
            "reservados con los forasteros, intensamente leales dentro de vínculos de confianza y propósito compartido",
            "melancólicos pero resueltos, marcados por una inmortalidad perdida y un deber que perdura",
            "vigilantes y deliberados, prefieren la paciencia y la precisión a la premura",
            "silenciosamente autoritarios, extraen su autoridad de la edad y la devoción, no del rango",
        ],
        "flavor_words": [
            "Elune", "que Elune te guíe", "luz de las estrellas",
            "Kaldorei", "Darnassus", "Nordrassil",
            "raíces ancestrales", "Teldrassil", "los viejos caminos",
            "Cenarius", "luz de luna", "el Sueño Esmeralda",
        ],
        "vocabulary": [
            ("Ishnu-alah", "Buena fortuna para ti"),
            ("Ishnu-dal-dieb", "Buena fortuna para tu familia"),
            ("Elune-adore", "Que Elune esté contigo"),
            ("Ande'thoras-ethil", "Que tus penas disminuyan"),
            ("Andu-falah-dor!", "¡Que se restaure el equilibrio!"),
            ("Bandu Thoribas!", "¡Preparaos para luchar!"),
            ("Fandu-dath-belore?", "¿Quién anda ahí?"),
            ("Tor ilisar'thera'nal!", "¡Que nuestros enemigos se cuiden!"),
        ],
        "lore": [
            "La antigua civilización Kaldorei fue destrozada por la Fragmentación.",
            "Fuerte devoción a Elune, el druidismo y las tradiciones de centinela.",
            "Larga historia de lucha contra demonios, sátiros y corrupción en bosques sagrados.",
            "La inmortalidad terminó tras los sucesos en torno a Nordrassil y la Tercera Guerra.",
            "La pertenencia a la Alianza tras Warcraft III sigue siendo práctica más que íntima.",
            "La protección de árboles del mundo, arboledas sagradas y santuarios silvestres es central.",
            "Se teme el exceso arcano debido a los recuerdos de una catástrofe global pasada.",
        ],
        "worldview": (
            "Las prioridades kaldorei son la defensa de tierras sagradas, la veneración de Elune y "
            "el equilibrio druídico. La memoria colectiva de la Fragmentación los hace cautelosos "
            "ante el uso imprudente de la magia arcana. La cooperación con la Alianza existe, pero "
            "persiste la distancia cultural con las razas más jóvenes."
        ),
    },
    "Undead": {
        "traits": [
            "oscuramente sarcásticos, amargados, pragmáticos, despiadados, "
            "orientados a la supervivencia y muy insulares",
            "fríos y calculadores, no confían plenamente en nadie, aunque leales a quienes demuestran su valía",
            "de humor mórbido, directos sobre la muerte y desdeñosos del optimismo ingenuo",
            "movidos por la venganza y la autopreservación, con poca paciencia para el sentimentalismo",
            "clínicos y distantes, ven a los vivos con una mezcla de envidia y desdén",
            "astutos y recursivos, marcados por la traición hasta esperar lo peor de sus aliados",
            "sombríamente decididos, hallan propósito en el desafío antes que en la esperanza",
            "territoriales y suspicaces, protegen los intereses de los Renegados con despiadada eficiencia",
        ],
        "flavor_words": [
            "Dama Oscura", "la peste", "la tumba",
            "Renegados", "Entrañas", "Flagelo",
            "venganza", "el boticario", "Lordaeron",
            "putrefacción", "libre albedrío", "el Rey Exánime",
        ],
        "vocabulary": [
            ("Dark Lady watch over you", "despedida/bendición"),
            ("Victory for Sylvanas", "grito de guerra"),
            ("Embrace the shadow", "despedida"),
            ("Our time will come", "expresión de determinación"),
        ],
        "lore": [
            "Los Renegados son antiguos no-muertos del Flagelo que recuperaron su libre albedrío.",
            "Liderados por Sylvanas Windrunner desde Entrañas.",
            "Nacidos de las ruinas de Lordaeron y rechazados por la mayoría de los vivos.",
            "La Real Sociedad de Boticarios desarrolla la plaga y otras brutales armas químicas.",
            "Los sucesos de la era de la Ira incluyen la traición de la Puerta de la Ira y purgas internas de facción.",
            "La pertenencia a la Horda es estratégica y a menudo marcada por la desconfianza mutua.",
            "La venganza contra el Rey Exánime es un motor emocional y político central.",
        ],
        "worldview": (
            "La política de los Renegados gira en torno a preservar el libre albedrío, asegurar los "
            "dominios de Lordaeron y destruir las amenazas del Flagelo. La sociedad de Entrañas está "
            "militarizada y fuertemente influida por redes de boticarios e inteligencia. Su relación "
            "con la Horda es estratégica, marcada más por enemigos comunes que por la confianza."
        ),
    },
    "Tauren": {
        "traits": [
            "tranquilos, con los pies en la tierra, espirituales, honorables, "
            "pacientes y protectores de su gente y su tierra",
            "amables en el consejo pero inamovibles en la defensa, guiados por ancianos y ritos ancestrales",
            "profundamente comunales, miden su valía por el servicio a la tribu antes que por la gloria personal",
            "contemplativos y lentos para la ira, pero devastadores cuando se alzan para proteger a los inocentes",
            "reverentes con la naturaleza y los ancestros, hallan sabiduría en las estaciones y el paso de los años",
            "estoicos y confiables, prefieren palabras medidas y acciones decisivas a la fanfarronería",
            "cálidos y hospitalarios con los aliados, cautelosos y vigilantes con los desconocidos",
            "espiritualmente sintonizados y físicamente imponentes, equilibran ternura con fuerza bruta",
        ],
        "flavor_words": [
            "Madre Tierra", "la gran cacería",
            "los ancestros", "Cima del Trueno", "shu'halo",
            "las llanuras", "Mulgore", "ancianos tribales",
            "la cacería", "tótem", "Cairne", "el viento",
        ],
        "vocabulary": [
            ("Walk with the Earth Mother", "despedida/bendición"),
            ("Ancestors watch over you", "despedida"),
            ("Winds be at your back", "despedida/bendición"),
            ("Earth Mother guide you", "bendición"),
        ],
        "lore": [
            "Las tribus nómadas fueron unificadas bajo Cairne Pezuña de Sangre.",
            "Cima del Trueno se convirtió en la ciudad central de los tauren en Mulgore.",
            "La vida espiritual se centra en la Madre Tierra y los ancestros.",
            "El druidismo y el chamanismo son pilares culturales centrales.",
            "Se unieron a la Horda tras la ayuda orca contra la agresión centauro.",
            "Una fuerte cultura de caza y tradición oral preserva la identidad y la historia.",
            "En la era de la Ira, Cairne Pezuña de Sangre es uno de los líderes veteranos de la Horda.",
        ],
        "worldview": (
            "El orden social tauren enfatiza el deber tribal, los ancianos y la reverencia por la "
            "Madre Tierra y los ancestros. Valoran la mediación y la contención, pero defienden a "
            "su gente y su territorio con decisión. La pertenencia a la Horda se enmarca como un "
            "juramento de gratitud y defensa mutua."
        ),
    },
    "Gnome": {
        "traits": [
            "inventivos, curiosos, optimistas, analíticos, de pensamiento rápido e implacables bajo presión",
            "eternamente optimistas, tratan los contratiempos como datos, no como derrotas",
            "técnicamente obsesivos, propensos a la jerga, y genuinamente encantados con las soluciones ingeniosas",
            "valientes y decididos, compensan su pequeña estatura con una confianza desmedida",
            "intelectualmente inquietos, siempre trasteando con ideas incluso en la conversación casual",
            "alegres y excéntricos, ven el peligro como un problema de ingeniería por resolver",
            "metódicos pero espontáneos, alternan entre el análisis cuidadoso y la improvisación desenfrenada",
            "socialmente entusiastas, ansiosos por explicar sus inventos aunque nadie pregunte",
        ],
        "flavor_words": [
            "trasteando", "según mis cálculos", "brillante",
            "Alto Ingeniero", "Mekkatorque", "Gnomeregan",
            "engranajes", "planos", "prototipo",
            "invento", "calibración", "bujía",
        ],
        "vocabulary": [
            ("For Gnomeregan!", "grito de guerra"),
            ("Salutations!", "saludo formal"),
            ("My, you're a tall one!", "saludo, humor autoconsciente"),
        ],
        "lore": [
            "Originarios de Gnomeregan, famosos por la ingeniería y la invención.",
            "La ciudad se perdió ante una invasión trogg y una catastrófica fuga de radiación.",
            "Los supervivientes se convirtieron en refugiados acogidos cerca de Forjaz.",
            "El Alto Ingeniero Mekkatorque lidera los esfuerzos de recuperación en la era de la Ira.",
            "La cultura valora la experimentación, la improvisación y la alfabetización técnica.",
            "La ingeniería abarca la guerra, el transporte, la medicina y las herramientas cotidianas.",
            "Los lazos con la Alianza son estrechos, especialmente con los enanos de Forjaz.",
        ],
        "worldview": (
            "La cultura gnoma trata la ingeniería y la ciencia como servicio cívico, no solo como "
            "profesión. La recuperación de Gnomeregan sigue siendo un objetivo político unificador "
            "bajo Gelbin Mekkatorque. Su papel en la Alianza suele centrarse en la logística, la "
            "invención y el apoyo técnico."
        ),
    },
    "Troll": {
        "traits": [
            "relajados, espirituales, avispados, orgullosos, adaptables y peligrosos cuando se los provoca",
            "despreocupados en la superficie pero fieramente tribales bajo su actitud casual",
            "astutos y perceptivos, leen las situaciones con rapidez y se adaptan sin dudar",
            "supersticiosos y reverentes con los loa, entretejen la fe en las decisiones cotidianas",
            "orgullosos de su herencia Lanza Negra, llevan el exilio y la supervivencia como insignias de identidad",
            "relajados y humorísticos en compañía, pero fríos y concentrados cuando aparece una amenaza",
            "pacientes y oportunistas, prefieren esperar el momento adecuado para actuar",
            "profundamente comunales, valoran la lealtad a la tribu por encima de la ambición o la comodidad personal",
        ],
        "flavor_words": [
            "mon", "los espíritus", "loa",
            "Lanza Negra", "Vol'jin", "Islas del Eco",
            "vudú", "los ancestros", "cazador de sombras",
            "isla", "juju", "sacrificio",
        ],
        "vocabulary": [
            ("Taz'dingo!", "grito de guerra / de júbilo"),
            ("Spirits be with ya, mon", "despedida/bendición"),
            ("Stay away from da voodoo", "advertencia/despedida"),
        ],
        "lore": [
            "Los trols jugables son Lanza Negra, no Amani ni Gurubashi.",
            "Los Lanza Negra fueron rescatados por Thrall y se unieron a la Horda.",
            "La veneración de los loa, la práctica del vudú y las tradiciones "
            "de cazador de sombras dan forma a la cultura.",
            "Vol'jin lidera a los Lanza Negra en la política de la era de la Ira.",
            "Antiguos imperios trols preceden a muchas civilizaciones más jóvenes de Azeroth.",
            "La identidad Lanza Negra está marcada por el exilio, la migración y la supervivencia en los márgenes.",
            "La memoria tribal y la espiritualidad práctica guían las decisiones cotidianas.",
        ],
        "worldview": (
            "La cosmovisión Lanza Negra es tribal, centrada en la supervivencia y guiada por la "
            "tradición de los loa. El liderazgo de Vol'jin enfatiza la lealtad a la Horda mientras "
            "preserva una identidad trol distintiva. La historia oral, la práctica de cazador de "
            "sombras y la adaptabilidad son rasgos culturales centrales."
        ),
    },
    "Blood Elf": {
        "traits": [
            "orgullosos, elegantes, disciplinados, conscientes de su imagen, "
            "centrados en lo arcano y emocionalmente reservados",
            "refinados y serenos, ocultan un dolor profundo tras la compostura y el orgullo cultural",
            "mágicamente sintonizados e intelectualmente agudos, con exigentes estándares para todo",
            "políticamente astutos, navegan alianzas con gracia mientras confían plenamente en pocos",
            "estéticamente motivados, valoran la belleza y el orden como expresiones de identidad nacional",
            "resilientes bajo el pulido, forjados por la adicción, la traición y la catástrofe nacional",
            "socialmente elegantes pero íntimamente intensos, canalizan la pasión hacia el deber y el oficio",
            "dignos y con dominio de sí mismos, tratan la compostura bajo presión como una obligación moral",
        ],
        "flavor_words": [
            "sin'dorei", "el Pozo de Sol", "arcano",
            "Quel'Thalas", "Ciudad de Lunargenta", "señor regente",
            "Lor'themar", "maná", "los magísteres",
            "caballeros de sangre", "Kael'thas", "la Aguja",
        ],
        "vocabulary": [
            ("Bal'a dash, malanore", "Saludos, viajero"),
            ("Shorel'aran", "Adiós"),
            ("Selama ashal'anore", "Justicia para nuestro pueblo"),
            ("Anar'alah belore", "Por la luz del sol"),
            ("Anu belore dela'na", "El sol nos guía"),
            ("Sinu a'manore", "Bien hallado"),
            ("Doral ana'diel?", "¿Cómo te va?"),
            ("Al diel shala", "Buen viaje"),
        ],
        "lore": [
            "Los sin'dorei son supervivientes de Quel'Thalas tras la devastación del Flagelo.",
            "La destrucción de su fuente sagrada causó abstinencia mágica y crisis social.",
            "La alianza de Kael'thas con la Legión terminó en traición abierta.",
            "El Pozo de Sol fue restaurado con energía de la Luz y arcana a finales de TBC.",
            "Lor'themar Theron gobierna como señor regente en el periodo de la Ira.",
            "Los Caballeros de Sangre pasaron de drenar poder a servir a fuentes restauradas de la Luz.",
            "Los lazos con la Horda son pragmáticos, moldeados por la política, la memoria y la supervivencia.",
        ],
        "worldview": (
            "La política de los elfos de sangre prioriza la seguridad de Quel'Thalas, la protección "
            "del Pozo de Sol restaurado y el control de los recursos arcanos. La cultura pública "
            "valora la disciplina y la dignidad tras el trauma nacional. La pertenencia a la Horda "
            "es estadismo práctico moldeado por el abandono pasado y las amenazas actuales."
        ),
    },
    "Draenei": {
        "traits": [
            "devotos, resilientes, contemplativos, compasivos, ancestrales y silenciosamente curtidos en batalla",
            "pacientes y de mirada larga, miden los sucesos frente a milenios de exilio y pérdida",
            "profundamente fieles, extraen fuerza de los naaru y una creencia inquebrantable en la Luz",
            "amables en el trato pero inflexibles en principios, especialmente contra la corrupción demoníaca",
            "sabios y mesurados, ofrecen consejo forjado por eras de errancia y persecución",
            "silenciosamente afligidos bajo un exterior compuesto, llevan el duelo sin amargura",
            "comunales y desinteresados, colocan la seguridad de refugiados y aliados sobre la necesidad personal",
            "espiritualmente disciplinados y marcialmente capaces, equilibran la oración con la resolución de vengador",
        ],
        "flavor_words": [
            "los Naaru", "la Luz", "Argus",
            "El Exodar", "Velen", "Draenor",
            "los cristales", "eredar", "vengadores",
            "el Profeta", "exilio", "la Legión Ardiente",
        ],
        "vocabulary": [
            ("Archenon poros", "Buena fortuna"),
            ("Dioniss aca", "Buen viaje"),
            ("Krona ki cristorr!", "¡La Legión caerá!"),
            ("Pheta vi acahachi!", "¡Que la Luz me dé fuerza!"),
            ("Pheta thones gamera", "Luz, guía nuestro camino"),
        ],
        "lore": [
            "Descienden de exiliados eredar liderados por el Profeta Velen.",
            "Huyeron de Argus y soportaron milenios de persecución de la Legión.",
            "Llegaron a Azeroth tras el accidente de El Exodar en Isla Bruma Azur.",
            "Guiados por los naaru, la Luz y las órdenes marciales de vengadores.",
            "La historia de Draenor incluye la devastación por la "
            "Horda antes de que se formaran las alianzas actuales.",
            "La sociedad combina la fe mística con tecnología cristalina avanzada.",
            "Cargan un profundo recuerdo de pérdida junto con una esperanza paciente y disciplinada.",
        ],
        "worldview": (
            "La sociedad draenei se organiza en torno al liderazgo de Velen, la veneración de los "
            "naaru y una larga memoria de exilio. La pertenencia a la Alianza sirve tanto a la "
            "alineación moral como a la defensa estratégica contra los remanentes de la Legión. "
            "Su cultura combina tecnología cristalina avanzada con deber religioso y sanación comunal."
        ),
    },
}

ZONE_FLAVOR = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Khaz Modan
    # -------------------------------------------------------------------------
    1: """Dun Morogh: Unas tierras altas nevadas entre las cumbres de Khaz Modan, hogar de los enanos de Forjaz y de los gnomos exiliados de Gnomeregan. La nieve cubre las colinas rocosas, los lagos helados brillan bajo un sol pálido y bosques de pinos silenciosos se alzan bajo pesados ventisqueros. El aire huele a escarcha, a humo de leña y a forja. Las aldeas enanas mantienen sus fuegos encendidos contra el frío interminable, mientras troggs, trols de hielo, lobos y osos hacen peligrosas las tierras salvajes.""",

    1537: """Forjaz: La antigua capital de los enanos, una inmensa ciudad excavada en el corazón de una montaña de Dun Morogh. Salas iluminadas con antorchas y pasadizos de piedra rodean la Gran Fundición, alimentada por ríos de roca fundida, donde el rey Magni Barbabronce gobierna Khaz Modan desde el Alto Trono. Los gnomos exiliados de Gnomeregan viven en Ciudad Manitas, la Liga de Expedicionarios busca los secretos del origen de los enanos en la Sala de los Expedicionarios y el Tranvía Subterráneo viaja bajo tierra hasta Ventormenta. El aire es cálido, humeante y resuena de martillos y risas.""",

    38: """Loch Modan: Colinas agrestes y valles verdes en el este de Khaz Modan, alrededor de un gran lago contenido por una enorme presa, una maravilla de la ingeniería enana. El clima es fresco y húmedo, con niebla sobre el agua, lluvias frecuentes y mañanas heladas. Los enanos pescan en el lago, extraen mineral de los acantilados y talan madera alrededor de Thelsamar. Máquinas de asedio rotas de la Horda, restos de la Segunda Guerra, aún se oxidan en las islas. Los troggs infestan los valles, los kóbolds ocupan una mina, los ogros una fortaleza al nordeste y los enanos Hierro Negro amenazan la presa.""",

    330: """Puente Thandol: Un gigantesco puente enano sobre el profundo estrecho que separa Khaz Modan de Lordaeron, que une los Humedales con las Tierras Altas de Arathi. Durante siglos lo cruzaron ejércitos y mercancías entre los enanos y los reinos humanos del norte. La Plaga lo dañó en la Tercera Guerra, y un ataque de los enanos Hierro Negro casi destruyó uno de sus tramos, cuyos grandes fragmentos yacen ahora bajo las olas. Sigue siendo la única ruta terrestre entre Lordaeron y el sur. El viento y la espuma del mar azotan sus alturas.""",

    269: """Dun Algaz: Un paso abierto a través de las montañas y una vieja fortaleza enana entre Loch Modan y los Humedales, custodiado al sur por la Puerta de Algaz. Durante la Segunda Guerra fue el último bastión de la Horda en Khaz Modan. Sigue siendo el camino principal entre las tierras enanas y el Puerto de Menethil, pero orcos del clan Faucedraco han tomado el puesto de avanzada en mitad del paso, y los guardias de montaña enanos solo mantienen el túnel superior. Los túneles son oscuros, fríos y resonantes, y el camino a través de ellos se ha vuelto peligroso.""",

    11: """Los Humedales: Unos vastos y fríos pantanos al norte de Khaz Modan, surcados de ríos, ciénagas y canales ahogados por los juncos entre las montañas y la bahía de Baradin. La niebla cubre el suelo, el cielo es de un gris uniforme y llueve a menudo. Antaño tierra de fortalezas Martillo Salvaje, fue arrasada en la Segunda y la Tercera Guerra, cuando el clan Faucedraco ocupaba Grim Batol y esclavizaba a la Reina de los Dragones Alexstrasza. El Puerto de Menethil, en la costa oeste, une por mar Khaz Modan con Kalimdor y Rasganorte. Restos del clan Faucedraco, enanos Hierro Negro, gnolls, múrlocs, raptores y crocoliscos hacen peligrosos los pantanos.""",

    3: """Tierras Inhóspitas: Un páramo abrasado por el sol, de tierra roja agrietada, mesetas y cañones sinuosos al sur de Khaz Modan. El agua escasea, los días son tórridos y las tormentas de polvo barren las llanuras desnudas, donde solo sobreviven coyotes, buitres, escórpidos, basiliscos y elementales de roca. Al norte se encuentra Uldaman, una cámara de los titanes desenterrada por excavaciones enanas y defendida ahora por los troggs que despertaron. Los enanos Hierro Negro excavan allí para su amo Ragnaros, los ogros recorren la región, dragones negros anidan en los cañones del este y la Horda mantiene la fortaleza de Kargath.""",

    51: """La Garganta de Fuego: Un páramo volcánico de ceniza, escoria y lava entre las Tierras Inhóspitas y la Montaña Roca Negra, antaño parte de las verdes Montañas Crestagrana, hasta que la invocación de Ragnaros por Thaurissan desgarró la tierra. El aire es caliente, seco y lleno de humo, y elementales de fuego vagan entre las rocas calcinadas. Los enanos Hierro Negro dominan la garganta y obligan a cautivos a trabajar en la gigantesca excavación del Caldero. En su borde norte, los artesanos de la Hermandad del Torio, que rompieron con su clan, mantienen el asentamiento neutral de Puesto del Torio.""",

    25: """Montaña Roca Negra: Un volcán imponente y aún activo entre la Garganta de Fuego y las Estepas Ardientes, nacido cuando el thane hechicero Hierro Negro Thaurissan invocó a Ragnaros, el Señor del Fuego. Los enanos Hierro Negro excavaron una inmensa ciudad en sus profundidades, y sobre ella se alza la Cumbre de Roca Negra. La montaña está ferozmente disputada: Ragnaros y sus sirvientes Hierro Negro dominan las profundidades y el núcleo fundido, mientras el dragón negro Nefarian manda sobre orcos, ogros y dracónidos desde las alturas de la cumbre. Cadenas y plataformas cruzan una sala de roca fundida, y el calor, el humo y el rugido nunca cesan.""",

    46: """Las Estepas Ardientes: Una tierra volcánica calcinada al sur de la Montaña Roca Negra, el único paso terrestre entre Ventormenta y Khaz Modan. Tierra carbonizada, estribaciones escarpadas y ríos de lava se extienden bajo un cielo enrojecido por la montaña, y el aire caliente y seco arrastra ceniza. Abandonadas por Ventormenta, las estepas pertenecen a los siervos del Vuelo Negro y a los agentes de Ragnaros: orcos Roca Negra que rechazan a Thrall, ogros, dragones negros y enanos Hierro Negro. Aquí cayó Anduin Lothar al final de la Segunda Guerra. La Alianza se aferra a la Vigía de Morgan.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Azeroth
    # -------------------------------------------------------------------------
    12: """Bosque de Elwynn: El corazón verde del reino de Ventormenta, una tierra apacible de bosques de robles y pinos, praderas, lagos y granjas al sur de la capital, con la aldea de Villadorada en su centro y la Abadía de Villanorte en un valle al norte. La Horda lo arrasó en la Primera Guerra, y los canteros no pagados que reconstruyeron Ventormenta se convirtieron en la Hermandad Defias. La paz es frágil: bandidos Defias ocupan granjas, los kóbolds infestan las minas, los gnolls acampan en la frontera oeste y los múrlocs habitan los lagos, mientras la guardia está agotada por guerras lejanas.""",

    1519: """Ventormenta: La capital del reino de Ventormenta y la ciudad humana más grandiosa del mundo, reconstruida tras la Primera Guerra con murallas de piedra blanca, torres de tejados azules y distritos separados por canales. El rey Varian Wrynn gobierna desde el Castillo de Ventormenta tras su larga ausencia. La Catedral de la Luz es el corazón de la fe en la Luz Sagrada, y la ciudad alberga el Distrito de Mercaderes, el Casco Antiguo con el IV:7, el Barrio de los Magos, el Distrito de los Enanos con el Tranvía Subterráneo hacia Forjaz y el Parque con su pozo de la luna. Humanos, enanos, gnomos, elfos de la noche y draenei recorren sus calles.""",

    40: """Páramos de Poniente: Tierras de cultivo onduladas en la costa oeste de Ventormenta, antaño el granero del reino y hoy caídas en la ruina. Los campos están yermos, la hierba amarillea y el viento del mar arrastra polvo sobre granjas abandonadas. La Hermandad Defias, forajidos nacidos de los canteros no pagados de Ventormenta, ha expulsado a muchos granjeros, ocupa la aldea fantasma de Arroyoluna y ha soltado guardianes de cosechas descontrolados en los campos. Los gnolls asaltan desde el sur y los múrlocs merodean la costa. La Milicia del Pueblo resiste en la Colina del Centinela, y los granjeros se sienten olvidados por la corona.""",

    44: """Montañas Crestagrana: Picos rojizos, altos olmos y ríos caudalosos al este del Bosque de Elwynn, alrededor de las aguas azules del Lago Sempiterno y del viejo pueblo de Villa del Lago. Sus habitantes, recios y autónomos, abastecen a Ventormenta de madera, pescado y grano. La cordillera quedó destrozada hace mucho por la invocación de Ragnaros. Hoy es tierra fronteriza: orcos Roca Negra de las Estepas Ardientes han tomado la fortaleza de Petravista y acampan en las colinas, los gnolls reclaman los cañones, los múrlocs infestan el lago y crías de dragón negro recorren las alturas. Villa del Lago depende de su pequeña guardia.""",

    10: """Bosque del Ocaso: Un bosque oscuro y maldito al sur de Elwynn, antaño luminoso y hermoso, hoy engullido por un crepúsculo eterno y antinatural. Una niebla negra flota entre árboles retorcidos, y el aire es frío y huele a podredumbre. Unos culpan al mal de Karazhan, otros a un antiguo artefacto y a los huargen que llegaron con la maldición. Los muertos se levantan de los cementerios, huargen y arañas gigantes acechan en el bosque, y se dice que los Jinetes Negros surgen de la noche. Los tozudos habitantes de Villa Oscura, protegidos por la Guardia Nocturna, se sienten abandonados por Ventormenta.""",

    41: """Paso de la Muerte: Un cañón desolado y maldito entre el Bosque del Ocaso y el Pantano de las Penas, donde los árboles se alzan desnudos y petrificados, la hierba es gris y un viento fétido y aullante nunca cesa. Las tormentas amenazan sin descanso y los rayos golpean las rocas desnudas. Al sur se alza Karazhan, la torre de Medivh, el último Guardián de Tirisfal, que abrió el Portal Oscuro; una magia maligna aún emana de ella y drena la vida de la tierra. Ogros, espíritus sin descanso y aves carroñeras pueblan el paso, y se susurra que una nueva presencia oscura se ha adueñado de la torre.""",

    8: """Pantano de las Penas: Un pantano estancado y envuelto en niebla, de ciénagas, sauces llorones y charcas salobres al este del Paso de la Muerte, antaño la parte norte de la Ciénaga Negra. El aire es húmedo y pesado, y crocoliscos, jaguares, arañas y bestias del pantano acechan entre los juncos. Los Atal'ai erigieron aquí un templo al dios de la sangre Hakkar, y el Aspecto Ysera lo hundió bajo la ciénaga más grande, donde sus dragones aún montan guardia. La Horda ocupa Rocal, reconstruida. Los Perdidos y los Tábidos, draenei varados en Azeroth, viven en el pantano, y los múrlocs pueblan la costa.""",

    4: """Las Tierras Devastadas: Un desierto calcinado de arcilla carmesí al sur del Pantano de las Penas, antaño el sur de la Ciénaga Negra, deformado por la magia del Portal Oscuro. Los rayos caen a menudo, nada fértil crece, los días son calurosos y las noches gélidas. Basiliscos, escórpidos y hienas mutados vagan por la región. El Portal Oscuro se alza en un enorme cráter al sudeste, abierto de nuevo hacia Terrallende, y ejércitos de la Alianza y de la Horda custodian su base. El Castillo de Nethergarde, fundado por Khadgar, vigila desde el norte; ogros y restos de la Legión acechan en el páramo.""",

    33: """Vega de Tuercespina: Una inmensa jungla humeante en la punta sur de los Reinos del Este, llena de árboles gigantescos, lianas y maleza espinosa, habitada por tigres, panteras, raptores, gorilas y crocoliscos. Fue el corazón del imperio trol Gurubashi hasta que la invocación de Hakkar lo desgarró; hoy las ruinas cubren la tierra, las tribus Sangrapellejo y Machacacráneos combaten a los forasteros y Zul'Gurub ha vuelto a caer bajo el dominio de Hakkar. Goblins, piratas, ogros, nagas y rebeldes reclaman su parte. Bahía del Botín es el bullicioso puerto neutral del cabo sur, y la Horda mantiene Grom'gol en la costa.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Lordaeron
    # -------------------------------------------------------------------------
    85: """Claros de Tirisfal: Colinas boscosas en la costa norte de Lordaeron, antaño el corazón del reino humano y hoy la patria de los Renegados de Sylvanas Brisaveloz. El cielo es lúgubre y teñido de verde, una niebla fría flota sobre granjas abandonadas, lagos silenciosos y molinos en ruinas, pero la tierra conserva una belleza melancólica, sobre todo alrededor de la aldea de Rémol. Aquí Kel'Thuzad propagó la peste por primera vez y Arthas mató a su padre. Bajo la capital en ruinas se extiende Entrañas. La Plaga aún ronda las granjas, la Cruzada Escarlata mantiene su monasterio y el Baluarte vigila las Tierras de la Peste.""",

    1497: """Entrañas: La capital de los Renegados, una inmensa ciudad subterránea bajo las ruinas de la capital real de Lordaeron, nacida de las antiguas criptas reales, mazmorras y alcantarillas. Arthas comenzó a ampliarla y Sylvanas terminó la obra tras expulsar a los señores del terror. La ciudad es oscura, fría y laberíntica, construida en anillos alrededor del Barrio Comercial, con los barrios de los Magos, de los Pícaros y de la Guerra y el Apothecarium, donde la Real Sociedad de Boticarios elabora pestes y venenos. Un limo verde corre por los canales, grandes elevadores llevan a los viajeros a las ruinas de la superficie y Sylvanas gobierna desde el Barrio Real.""",

    130: """Bosque de Argénteos: Un antiguo bosque de altos pinos de corteza plateada a lo largo de la costa oeste de Lordaeron, embrujado y enfermo desde que la Plaga lo atravesó a sangre y fuego en la Tercera Guerra. Nieblas fantasmales flotan entre los árboles, y granjas quemadas y minas abandonadas salpican la tierra. Los Renegados dominan el norte desde El Sepulcro y combaten a gnolls apestados. Al sur, los magos de Dalaran protegen una aldea molinera, los habitantes de Aldea Piroleña sufren una maldición que los convierte en huargen de noche, Arugal medita en el Castillo de Colmillo Oscuro y la Muralla de Cringris aísla Gilneas.""",

    170: """Lago Lordamere: Uno de los mayores lagos de los Reinos del Este, una vasta extensión de agua fría y gris en el corazón del caído reino de Lordaeron, cuya capital se alzaba en la orilla norte. A su alrededor se extendían Lordaeron, Dalaran y Alterac, los grandes reinos de la antigua Alianza. Hoy separa las tierras de los Renegados de las Montañas de Alterac. La Isla de Fenris y su sombrío torreón ocupan el centro, las Islas del Alba forman el borde de un antiguo volcán y una vieja peste dejó sus aguas extrañamente vacías de vida. La niebla flota a menudo sobre el lago, y los múrlocs acampan en sus orillas.""",

    267: """Laderas de Trabalomas: Colinas verdes, praderas, pinares y tierras de cultivo al sur de Lordaeron, la región mejor conservada del reino caído. Un río que nace en el lago Darrowmere atraviesa las colinas, y pequeñas islas salpican la costa sur. Es también uno de los campos de batalla más sangrientos de Azeroth: aquí se libró la primera batalla de la Segunda Guerra, y en el Castillo de Durnholde estaban los campos de internamiento donde el joven Thrall vivió como esclavo. La ciudad humana de Costasur y los Renegados de Molino Tarren libran una lucha encarnizada, mientras el Sindicato ocupa las ruinas de Durnholde.""",

    36: """Montañas de Alterac: Picos nevados al norte de Trabalomas, antaño el reino humano de Alterac, destruido por la Alianza después de que lord Perenolde lo entregara a la Horda. Los nobles exiliados fundaron el Sindicato, que ocupa las tierras altas y campamentos sobre Trabalomas, mientras los ogros ocupan las ruinas de la ciudad de Alterac. En la orilla del Lago Lordamere se abre el cráter donde se alzaba Dalaran antes de volar a Rasganorte. En un valle oculto, los orcos Lobo Gélido combaten a los enanos de la Expedición Pico Tormenta, y la misteriosa Mansión Ravenholdt se esconde entre las cumbres. Yetis y leones de montaña recorren la nieve.""",

    45: """Tierras Altas de Arathi: Tierras altas grises y ventosas de hierba ondulante y rocas al sudeste de Lordaeron, cuna de la civilización humana, donde Thoradin fundó el Imperio de Arathor y donde humanos y altos elfos se aliaron por primera vez contra los Amani. Más tarde nació aquí el reino de Stromgarde, pero el Sindicato y los ogros tomaron su capital, y su ejército resiste ahora en el Refugio de la Zaga. La Horda ocupa Sentencia, el antiguo campo de internamiento. Ogros, trols del bosque, raptores y kóbolds recorren la región, y antiguos círculos de piedra mantendrían algo prisionero.""",

    293: """Muralla de Thoradin: Una inmensa muralla de piedra en la frontera entre las Laderas de Trabalomas y las Tierras Altas de Arathi, levantada en tiempos antiguos por el rey Thoradin, fundador del Imperio de Arathor, contra los trols Amani. Más tarde protegió Stromgarde del avance de la Plaga. Hoy está derrumbada y abierta, su gran puerta está abierta y tramos enteros se han convertido en escombros. El camino principal entre Trabalomas y Arathi pasa a su sombra, recuerdo de la gloria del primer imperio humano y de lo bajo que han caído sus herederos.""",

    47: """Tierras del Interior: Una región salvaje y montañosa de bosques frondosos, valles profundos y acantilados escarpados al norte de los Reinos del Este, intacta por la peste y de clima suave. Fue el corazón del imperio de los trols del bosque Amani, cuyas ruinas colosales aún se alzan entre los árboles. Los enanos Martillo Salvaje del alto thane Falstad viven al aire libre en Pico Nidal, una ciudad tallada con forma de cabeza de grifo, y montan grifos salvajes en la batalla. Tribus trols rivales ocupan Jintha'Alor y Shadra'Alor, mientras los trols Sañadiente se han aliado con la Horda. Al norte, el árbol de Seradane es una puerta al Sueño Esmeralda.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands, Quel'Thalas and southern isles
    # -------------------------------------------------------------------------
    28: """Tierras de la Peste del Oeste: Una tierra infestada al norte de Lordaeron, antaño el granero boscoso del norte del reino. Aquí Kel'Thuzad y el Culto de los Malditos envenenaron el grano de Andorhal con la peste de la no-muerte. Una niebla gris y humeante flota sobre la tierra, los árboles tienen excrecencias tumorales y las bestias supervivientes están enfermas y feroces. Los no-muertos infestan Andorhal, los campos de calderos y los cementerios, y la Plaga forma nigromantes en Scholomance, en la isla de Caer Darrow. La Cruzada Escarlata ocupa la Vega del Amparo, el Alba Argenta el Campamento del Orvallo, y la tumba de Uther el Iluminado es uno de los pocos lugares en paz.""",

    139: """Tierras de la Peste del Este: La mitad más devastada de las Tierras de la Peste, antaño tierra de granjas y aldeas gobernada desde Stratholme, donde se fundó la Orden de la Mano de Plata y donde Arthas llevó a cabo su purga. El dominio de la Plaga es aquí casi absoluto: el suelo es pardo y enfermo, los árboles se han retorcido en hongos gigantes y nieblas naranjas y verdes ahogan el aire. Stratholme arde como capital de la Plaga en Lordaeron, y el Bosque de la Plaga está lleno de zigurats. La Cruzada Escarlata ocupa la Mano de Tyr, el Alba Argenta mantiene la Capilla de la Esperanza de la Luz abierta a todos los que combaten a la Plaga, y al este flota Acherus, el hogar de los caballeros de la Muerte.""",

    3430: """Bosque Canción Eterna: El bosque encantado en el corazón de Quel'Thalas, detenido en un otoño eterno bajo un follaje dorado y carmesí, salpicado de agujas elegantes, torres flotantes y cristales arcanos. En la Tercera Guerra, Arthas condujo a la Plaga a través del reino hasta la Fuente del Sol y dejó la Cicatriz Muerta, una franja de tierra sin vida que parte el bosque y la propia Lunargenta. Los supervivientes tomaron el nombre de elfos de sangre y, bajo el regente lord Lor'themar Theron, se unieron a la Horda y reconstruyeron gran parte. Pero los Desdichados rondan las ruinas, constructos arcanos escapan a todo control, los trols acechan en las colinas y las piedras rúnicas que contienen la corrupción se debilitan.""",

    3487: """Ciudad de Lunargenta: La capital de los elfos de sangre en el Bosque Canción Eterna, fundada hace milenios y quizá la capital más antigua que sigue en pie. En la Tercera Guerra, Arthas condujo a la Plaga a través de sus puertas y mató al rey. Los elfos de sangre han reconstruido la mitad este casi con su antiguo esplendor, con agujas doradas, plataformas flotantes, cristales encadenados rebosantes de magia y jardines exuberantes, mientras la mitad oeste sigue en ruinas más allá de la Cicatriz Muerta. El regente lord Lor'themar Theron gobierna desde la Aguja Caminante del Sol, guardianes arcanos patrullan las calles y un orbe de traslación une la ciudad con Entrañas.""",

    3433: """Tierras Fantasma: El sur de Quel'Thalas, una tierra sombría de árboles negros y secos, cielo plomizo y frío mortal, devastada por la marcha de la Plaga hacia la Fuente del Sol y nunca recuperada. La Cicatriz Muerta parte de la Ciudad de la Muerte, la ciudadela de la Plaga gobernada por el traidor Dar'Khan Drathir, que ayudó a Arthas a romper las defensas del reino. Los fantasmas de los elfos asesinados rondan las aldeas en ruinas. Los elfos de sangre y sus aliados Renegados ocupan Tranquilien y quieren recuperar la tierra, mientras los trols Amani acechan cerca de Zul'Aman, al este. El Paso Thalassiano lleva al sur, a través de una antigua puerta élfica, hasta las Tierras de la Peste.""",

    4080: """Isla de Quel'Danas: Una isla frente a la costa norte del Bosque Canción Eterna, donde los fundadores de Quel'Thalas crearon hace siete mil años la Fuente del Sol, un manantial de inmenso poder. Arthas la profanó para resucitar a Kel'Thuzad. Recientemente, la isla fue escenario de una lucha desesperada, cuando Kael'thas Caminante del Sol y la Legión Ardiente quisieron usar la Fuente como portal, y la Ofensiva Sol Devastado de los Aldor y los Arúspices estableció su base en el puerto del Tramo del Sol. Las cicatrices de la batalla marcan la tierra, pero sus bosques dorados, playas blancas y elegantes agujas siguen siendo hermosos, y en su corazón se alza la Meseta de la Fuente del Sol.""",

    408: """Isla de Gillijim: Una remota isla selvática en los Mares del Sur, frente a la costa sur de la Vega de Tuercespina. Los viejos mapas la señalan como una antigua isla trol, pero pocos marinos vivos han pisado sus orillas, y está lejos de las rutas comerciales habituales. El mar que la rodea es cálido, profundo y azul, hogar de tiburones y otras criaturas de mar abierto, y las corrientes pueden arrastrar a los incautos lejos de tierra. Se habla de antiguas ruinas trols ocultas en sus selvas, pero sus secretos siguen siendo desconocidos para la mayor parte del mundo.""",

    409: """Isla del Doctor Lapidis: Una remota isla selvática en los Mares del Sur, frente a la costa sudoeste de la Vega de Tuercespina. Los viejos mapas señalan allí las ruinas desmoronadas de los antiguos trols de la jungla, pero casi nadie la ha visitado en la memoria de los vivos, y pocos conocen el significado de su nombre. Las aguas que la rodean son profundas, cálidas y vacías de barcos, habitadas solo por tiburones y criaturas de mar abierto. Sigue siendo un misterio, una mancha oscura en el horizonte que la mayoría de los marinos prefieren evitar.""",

    # -------------------------------------------------------------------------
    # Kalimdor - North
    # -------------------------------------------------------------------------
    141: """Teldrassil: Un Árbol del Mundo colosal que se alza del Mar de la Bruma frente al noroeste de Kalimdor, tan inmenso que sobre sus ramas, por encima de las nubes, crece una tierra de bosques, colinas y lagos. El archidruida Fandral Corzocelada lo hizo crecer después de que los elfos de la noche perdieran su inmortalidad, y su capital, Darnassus, se alza en sus ramas occidentales. La tierra vive en un eterno crepúsculo violeta, llena de árboles antiguos, pozos de la luna, fuegos fatuos y sables de la noche. Pero los Aspectos dragón nunca bendijeron el árbol, y una corrupción rastrera se extiende: los fúrbolgs se han vuelto salvajes, los arbolitos se enfurecen y los sátiros acechan en las cuevas. Rut'theran, a su pie, es el puerto hacia el mundo.""",

    1657: """Darnassus: La capital de los elfos de la noche, construida en las ramas occidentales de Teldrassil y bañada por un eterno crepúsculo violeta. Elegantes terrazas de madera viva y piedra blanca rodean un lago central, unidas por puentes arqueados. La suma sacerdotisa Tyrande Susurravientos guía a los elfos de la noche desde el Templo de la Luna, mientras el archidruida Fandral Corzocelada dirige el Círculo Cenarion desde el Enclave Cenarion, a menudo en desacuerdo con ella. Malfurion Tempestira sigue perdido en el Sueño Esmeralda. Centinelas y ancestros protegen la ciudad tranquila y algo melancólica, y un portal desciende hasta la aldea de Rut'theran.""",

    148: """Costa Oscura: Una larga costa rocosa al noroeste de Kalimdor, de bosques sombríos, playas brumosas y ruinas desmoronadas, donde el tiempo es frío y tormentoso y la niebla es frecuente. Antaño una región próspera del antiguo imperio kaldorei, fue arrasada por la Gran Fractura, y sus ciudades llevan milenios vacías. Los elfos de la noche reconstruyeron el puerto de Auberdine, enlace con Teldrassil, las islas Bruma Azur y los Reinos del Este. Más allá, nagas, sátiros y fantasmas de los Altonato rondan las ruinas, sectarios se esconden en lugares secretos y los fúrbolgs han enloquecido por la corrupción que baja de Frondavil.""",

    3524: """Isla Bruma Azur: La mayor de las islas Bruma Azur, frente al oeste de Kalimdor, durante mucho tiempo hogar solo de fúrbolgs, lechúcicos y bestias salvajes, hasta que el Exodar, la nave dimensional de los draenei, se estrelló en sus orillas. Los supervivientes guiados por el profeta Velen construyeron su capital en la mayor sección intacta del pecio. La isla es una tierra de bosques perennes, flores violetas y colinas suaves, pero extraños cristales del pecio salpican el paisaje, tormentas arcanas cruzan el cielo y el impacto ha alterado algunas plantas y bestias. Los fúrbolgs amistosos viven en el norte, los nagas acechan en viejas ruinas y saboteadores elfos de sangre se esconden en las colinas.""",

    3557: """El Exodar: La capital de los draenei, construida en la mayor sección intacta de la nave dimensional que se estrelló en la Isla Bruma Azur. Antaño satélite del Castillo de la Tempestad, fue capturada en Terrallende por el profeta Velen y sus seguidores con ayuda de los naaru, saboteada por elfos de sangre y lanzada a través del Vacío Abisal. Hoy es una ciudad de relucientes salas de cristal y conductos luminosos que llevan luz sagrada y calor. Velen reside en el Trono de los Naaru junto a un naaru, y la ciudad resuena con el canto de los naaru y la devoción serena de un pueblo que ha vagado durante milenios.""",

    3525: """Isla Bruma de Sangre: La más septentrional de las islas Bruma Azur, antaño llamada Vientoplata, corrompida cuando restos del Exodar estrellado esparcieron sobre ella cristales rojo sangre. Un líquido parecido a la sangre rezuma de los cristales al suelo, altera plantas y bestias y llena el aire de una inquietante bruma carmesí; hasta los pinos han enrojecido. Los draenei estudian y sanan la tierra desde la Atalaya de Sangre, enfrentados a elfos de sangre ávidos del poder de los cristales, sátiros, nagas, fúrbolgs corrompidos y criaturas escapadas de la nave. Antiguas ruinas elfas de la noche salpican la isla, y los espíritus de dragones verdes rondan la Cicatriz del Vermis.""",

    331: """Vallefresno: Un vasto bosque antiguo al norte de Kalimdor y la patria ancestral de los elfos de la noche, una espesura primigenia de árboles gigantescos, claros profundos, lagos y ríos bajo un denso dosel. Durante milenios los elfos de la noche lo cuidaron sin talarlo, protegido por Centinelas, druidas y ancestros. En la Tercera Guerra, los orcos de Grom Grito Infernal llegaron por su madera y mataron al semidiós Cenarius. Desde entonces está ferozmente disputado: los elfos de la noche ocupan Astranaar al oeste, el clan Grito de Guerra tala al este, y las Centinelas Ala de Plata y los Escoltas Grito de Guerra chocan sin cesar. Demonios, sátiros y fúrbolgs corrompidos permanecen.""",

    361: """Frondavil: Un bosque corrompido al norte de Kalimdor, antaño un paraíso exuberante protegido por Cenarius, profanado por la Legión Ardiente con el Cráneo de Gul'dan en la Tercera Guerra. Árboles retorcidos, praderas calcinadas y arroyos que hierven de lodo tóxico llenan la tierra, y los ancestros que la protegían vagan ciegos sangrando veneno vil. Fúrbolgs corrompidos, sátiros, demonios y brujos del Concilio de la Sombra infestan el bosque, y las bestias hambrientas se atacan entre sí. Los druidas del Círculo Cenarion intentan purificarlo, y los fúrbolgs Fauces de Madera, aún puros, dominan los túneles del norte hacia el Claro de la Luna y Cuna del Invierno.""",

    493: """Claro de la Luna: Un valle sagrado en las laderas bajas del Monte Hyjal, protegido por altas montañas y envuelto en una noche eterna, donde la luna baña la tierra de plata y el aire es una tarde de verano cálida e interminable. Es el hogar del Círculo Cenarion, donde elfos de la noche y tauren viven en paz y no se toleran los conflictos entre razas. Durante milenios los druidas durmieron aquí en los Túmulos mientras sus espíritus recorrían el Sueño Esmeralda; Malfurion Tempestira sigue perdido allí. La aldea de Nighthaven se extiende a orillas del lago Elune'ara, bajo la vigilancia de los Guardianes del Bosque.""",

    618: """Cuna del Invierno: Un valle frío y nevado en lo alto del Monte Hyjal, en un invierno casi eterno por encima de las nubes del Claro de la Luna. La nieve cubre las colinas, los lagos helados resplandecen y el aire es limpio y puro. Los elfos de la noche se asentaron aquí tras la Gran Fractura, y sus ruinas aún se alzan en la nieve, mientras las raíces descubiertas del Árbol del Mundo se elevan como arcos sobre las cabezas. El Vuelo Azul de Mazthoril disputa desde hace mucho el valle a los elfos de la noche. La ciudad goblin de Vista Eterna está abierta a todos, fúrbolgs corrompidos, yetis y sables de hielo recorren la región y demonios ocupan la Garganta Negro Susurro al sur.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Center and East
    # -------------------------------------------------------------------------
    14: """Durotar: Una tierra de suelo rojo cocido por el sol, cañones escarpados y colinas en la costa este de Kalimdor, cuya belleza áspera recuerda a Draenor. Thrall la convirtió en la nueva patria de los orcos y de los trols Lanza Negra tras la Tercera Guerra y la llamó así por su padre Durotan, fundando Orgrimmar en su límite norte. Es el corazón de la Horda, con Cerrotajo en la encrucijada y la aldea trol de Sen'jin en la costa sur. Los peligros persisten: los jabaespines asaltan desde el oeste, los centauros acechan en el sur, las arpías anidan en los cañones, el Filo Ardiente se esconde en cuevas y un fuerte de Kul Tiras aún se alza en la costa.""",

    1637: """Orgrimmar: La capital de los orcos y sede de la Horda, una poderosa ciudad fortaleza construida en un cañón en el límite norte de Durotar, fundada por el jefe de guerra Thrall tras la Tercera Guerra y llamada así por Orgrim Martillo Maldito. Recias murallas, puertas enormes y altas torres la protegen, y sus barrios son valles: el Valle de la Fuerza, corazón comercial; el Valle de los Espíritus, hogar de trols y chamanes; el Valle de la Sabiduría, donde se alza el Fuerte Grommash de Thrall; y el Valle del Honor. La Calle del Arrastre lleva a la sombría Grieta de las Sombras. Sus construcciones rústicas de madera, piel y piedra están adornadas con púas y estandartes, y los zepelines la unen a los Reinos del Este y Rasganorte.""",

    2917: """Sala de las Leyendas: La gran sala de oficiales de la Horda en el Valle de la Fuerza de Orgrimmar, un edificio enorme de madera, piedra y pieles adornado con estandartes, trofeos y las armas de enemigos caídos. Sirve de cuartel y lugar de reunión de los guerreros más distinguidos de la Horda, y su arsenal secreto guarda armas de todos los continentes de Azeroth y de Draenor, muchas tomadas como botín de guerra y con una historia orgullosa. Es un lugar de honor y orgullo, donde se narra la gloria junto a grandes hogueras y se recuerdan las leyendas de la Horda.""",

    377: """Río Furia del Sur: Uno de los grandes ríos de Kalimdor, que nace en las tierras altas del Monte Hyjal y fluye hacia el sur como un caudal ancho y rápido. Separa Vallefresno de Azshara y, más al sur, Los Baldíos de Durotar, pasando cerca de las murallas de Orgrimmar. Sus aguas son frías y veloces en el norte, cálidas y turbias en el sur, donde los crocoliscos acechan entre los juncos. Desemboca en Mare Magnum en una cascada cerca del puerto goblin de Trinquete. Solo unos pocos puentes lo cruzan, y viajeros de toda clase atraviesan sus aguas.""",

    16: """Azshara: Una tierra costera hermosa pero maldita al nordeste de Kalimdor, envuelta en un otoño eterno, con árboles de un naranja y rojo brillantes, grandes acantilados y playas blancas. Hace diez mil años formaba parte de Zin-Azshari, la capital de la reina Azshara, hasta que la Gran Fractura hundió gran parte de la ciudad. Los elfos de la noche la consideran maldita; las ruinas se alzan en los acantilados y yacen entre los corales, y las leyendas dicen que la reina gobierna ahora a los nagas bajo las olas. Fantasmas de los Altonato, sátiros, nagas y dragones azules rondan la tierra, los amistosos Fauces de Madera ocupan las montañas del oeste y a menudo llegan tormentas del mar.""",

    17: """Los Baldíos: Una vasta sabana calurosa de hierba amarilla, árboles espinosos y llanuras polvorientas en el centro de Kalimdor, entre Vallefresno y Las Mil Agujas, con algunos oasis exuberantes en el norte. Antes de la Gran Fractura se alzaban aquí ciudades élficas, y el antiguo Camino del Oro aún guía caravanas entre Trinquete y el norte. El Cruce de la Horda es el gran centro, mientras la Alianza ocupa el Fuerte del Norte y la excavación de Bael Modan. Centauros y jabaespines asaltan las caravanas, las arpías anidan en las colinas, la Sociedad Ventura perfora en busca de petróleo y el Filo Ardiente se esconde en el Pico Nebuloso. Trinquete, en la costa, está abierto a todos.""",

    215: """Mulgore: Llanuras verdes y mesetas azotadas por el viento en el centro de Kalimdor, la patria ancestral de los tauren, rodeada de montañas con un único paso hacia Los Baldíos al este. Durante siglos los tauren vivieron como nómadas luchando contra los centauros, hasta que la Horda de Thrall los ayudó a expulsarlos y Cairne Pezuña de Sangre construyó Cima del Trueno sobre las mesetas. Es una tierra pastoril y protegida de praderas, lagos claros y brisas con aroma a pino, con aldeas tauren, molinos de viento y tótems tallados. Los jabaespines ocupan las sagradas Rocas Rojas, la Sociedad Ventura se ha apoderado de los pozos sagrados y las arpías anidan en el norte.""",

    1638: """Cima del Trueno: La capital de los tauren, construida sobre cuatro altas mesetas al norte de Mulgore, muy por encima de las Llanuras Doradas, la primera ciudad permanente de un pueblo que vagó durante siglos. Grandes tiendas, casas comunales y postes totémicos coronan las mesetas, unidas por puentes de cuerda que se balancean, y elevadores de madera suben a los visitantes desde las llanuras. El gran jefe Cairne Pezuña de Sangre gobierna desde la meseta central, los druidas se reúnen en el Alto de los Ancestros, los chamanes en el Alto de los Espíritus sobre los brumosos Estanques de la Visión y los cazadores en el Alto de los Cazadores. El clima es cálido y soleado, y la vista sobre Mulgore es impresionante.""",

    406: """Sierra Espolón: Una cordillera escarpada en el centro de Kalimdor, alzada por la Gran Fractura y tallada por el río Lobonegro en cañones y acantilados. Las laderas bajas son calurosas, secas y ventosas, la lluvia rompe en las cumbres del oeste y violentos vientos azotan los cañones. El Pico Espolón, sagrado para elfos de la noche y tauren, fue antaño el hogar del Oráculo. Los goblins de la Sociedad Ventura talan los bosques antiguos y contaminan las aguas, el Valle Calcinado es una ruina quemada llena de elementales de fuego, las arpías ocupan fortalezas en los cañones y los tauren renegados Tótem Siniestro atacan a sus propios hermanos.""",

    # -------------------------------------------------------------------------
    # Kalimdor - South
    # -------------------------------------------------------------------------
    405: """Desolace: Un páramo gris y pedregoso al oeste de Kalimdor que parece sufrir una maldición: el cielo siempre está oscuro y tormentoso, rayos y fuertes vientos barren la tierra, charcas amarillas y contaminadas salpican la ceniza y los cráneos de antiguos kodos miran desde sus tumbas. Es la patria de los centauros, nacidos según la leyenda en las profundidades de Maraudon, y cuatro tribus enfrentadas luchan entre sí con la misma ferocidad que contra los forasteros. Ruinas de los Altonato yacen dispersas, los nagas rondan la costa noroeste y el Filo Ardiente ha invocado demonios aquí. En triste contraste, la costa oeste es soleada y exuberante.""",

    357: """Feralas: Una selva tropical antigua y exuberante al sudoeste de Kalimdor, de árboles enormes, valles brumosos, ríos caudalosos y lagos claros, protegida por altas montañas. Formó parte del imperio elfo de la noche, y la vasta ciudad Altonato de Eldre'Thalas, hoy llamada La Masacre, yace en ruinas entre los árboles. Los elfos de la noche ocupan el Bastión Plumaluna en la isla de Sardor, y los tauren el Campamento Mojache al este. Los sanguinarios ogros Gordunni controlan muchas ruinas, los renegados Tótem Siniestro tienen un campamento, los nagas infestan las islas del oeste y un gran árbol en el noroeste es un portal al Sueño Esmeralda.""",

    400: """Las Mil Agujas: Un inmenso cañón seco al sur de Kalimdor, lleno de altas agujas de arenisca que se alzan como un bosque de agujas, talladas por el agua antes de que la Gran Fractura elevara la tierra. Al este se abre a las Salinas Brillantes, una llanura de sal donde ingenieros goblin y gnomos corren con sus máquinas, y los amaneceres desde las mesetas son espectaculares. Tribus tauren vivieron mucho tiempo precariamente en lo alto de las mesetas y ahora contraatacan desde el Poblado Viento Libre. Los centauros Galak patrullan el fondo del cañón, los renegados Tótem Siniestro ocupan el Pináculo Nube Negra y puentes de cuerda unen las agujas por encima de los peligros.""",

    15: """Marjal Revolcafango: Un vasto pantano caluroso y fétido en la costa este del centro de Kalimdor, hundido en la Gran Fractura, donde zumban los mosquitos, los árboles hunden sus frondas en charcas estancadas y bancos de lodo separan canales ahogados de algas. Raptores, arañas, crocoliscos y múrlocs acechan por doquier, y en el sur se dice que la dragona negra Onyxia habita en la Ciénaga de los Dragones. Jaina Valiente fundó Theramore en una isla frente a la costa, los ogros Petrandis acogen a la Horda en Matojo, y aquí encontró su fin el almirante Daelin Valiente. Escaramuzas encubiertas continúan pese a la tregua, y los goblins de Fangoapestoso dan la bienvenida a todos.""",

    2159: """Guarida de Onyxia: Una cueva volcánica en la Ciénaga de los Dragones, al sur del Marjal Revolcafango, la guarida de Onyxia, la gran dragona negra e hija de Alamuerte, madre del Vuelo Negro. La cueva se adentra profundamente en la tierra cálida, y la sala principal guarda su enorme nidada, custodiada por crías y dracónidos. El suelo no es más que una fina costra sobre roca fundida, el aire está cargado de humo, azufre y el hedor de sus víctimas, y huesos y tesoros yacen entre las rocas. Los viajeros cuentan historias sombrías sobre los que se lleva su progenie, y pocos de los que entran regresan.""",

    440: """Tanaris: Un inmenso desierto al sudeste de Kalimdor, un mar infinito de dunas bajo un cielo sin nubes, abrasador de día y barrido por peligrosas tormentas de arena, con montañas y cavernas profundas en el sur. Es el hogar ancestral del Vuelo Bronce, cuyo Aspecto Nozdormu reside en las Cavernas del Tiempo, y en el sur se encuentra la puerta sellada de la ciudad titánica de Uldum. Los goblins del Cártel Bonvapor mantienen la ciudad neutral de Gadgetzan y el puerto del cártel. Los trols Furiarena gobiernan desde Zul'Farrak, los ogros ocupan ruinas al sur, los bandidos se adueñan de las torres de agua y los piratas se esconden en la costa.""",

    1941: """Cavernas del Tiempo: Una vasta red de cuevas al este de Tanaris, hogar del Vuelo Bronce y de su Aspecto Nozdormu, guardianes del curso del tiempo. Portales en su interior llevan a momentos clave de la historia del mundo, como la apertura del Portal Oscuro, la huida de Thrall de Durnholde, la batalla del Monte Hyjal y la purga de Stratholme. La arena da paso a una vegetación exuberante, grandes relojes de arena giran y colosales estatuas de dragones de bronce se alzan sobre todo. Recientemente, el Vuelo Infinito ha empezado a inmiscuirse en la historia, y los dragones de bronce buscan ayuda. Se dice que quienes entran sin permiso salen cambiados.""",

    490: """Cráter de Un'Goro: Un inmenso cráter exuberante al sur de Kalimdor, entre Tanaris y Silithus, aislado por altas paredes. Una jungla humeante de plantas exóticas y criaturas gigantes lo llena: demosaurios, estegodontes y pterrordáctilos vagan libremente, los gorilas viven en las cuevas y los silítidos excavan colmenas en el sur. El volcán activo de la Cresta de Fuego se alza en su centro, fuentes termales y pozos de alquitrán burbujean, y extraños cristales y misteriosos pilones salpican la tierra. Muchos eruditos creen que fue un lugar de los titanes. Exploradores de todas las razas se reúnen en el Refugio de Marshal, en la pared norte, y la jungla nunca calla.""",

    1377: """Silithus: Un desierto duro de roca y arena en la esquina sudoeste de Kalimdor, interrumpido por las altas colmenas de los silítidos insectoides. Hace mil años, sus amos qiraji libraron la Guerra de las Arenas Movedizas, hasta que los elfos de la noche y los Vuelos dragón los encerraron tras el Muro del Escarabajo, en Ahn'Qiraj. Recientemente las puertas se abrieron de nuevo, y los ejércitos de la Alianza y de la Horda marcharon contra los qiraji. El Círculo Cenarion vigila desde el Fuerte Cenarion, el Vuelo Bronce ha regresado y el Martillo Crepuscular acampa por toda la región. El calor es implacable y el viento arrastra una arena hiriente.""",

    3478: """Puertas de Ahn'Qiraj: Las grandes puertas del Muro del Escarabajo en el límite sur de Silithus, que custodian Ahn'Qiraj, la antigua fortaleza de los qiraji y sus silítidos. Hace mil años, los elfos de la noche y los Vuelos dragón encerraron a los qiraji tras el muro; recientemente, las puertas se abrieron de nuevo con el Cetro de las Arenas Movedizas, y los ejércitos de la Alianza y de la Horda entraron. Más allá se extienden las Ruinas y el Templo de Ahn'Qiraj, donde se dice que moran los verdaderos amos de los qiraji. La arena ante las puertas está marcada por la batalla, y un silencio inquietante pesa sobre ellas.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Península del Fuego Infernal: Un páramo árido y rojo sangre al este de Terrallende, un resto de Draenor y la primera tierra al otro lado del Portal Oscuro. Los brujos orcos drenaron su vida hace mucho, el suelo rojo y agrietado escupe géiseres de fuego, y fragmentos de tierra flotan en sus bordes contra el cielo arremolinado del Vacío. Aquí la expedición de la Alianza combatió a la Horda de Draenor y selló el Portal. Hoy la Ciudadela del Fuego Infernal es la fortaleza de los orcos viles, la Legión Ardiente asalta los Escalones del Destino desde sus forjas, la Alianza ocupa el Bastión del Honor y la Horda, Thrallmar.""",

    3521: """Marisma de Zangar: Un pantano de belleza inquietante al oeste de Terrallende, cubierto por un bosque de hongos gigantes que se alzan sobre sus lagos como grandes árboles. Hongos brillantes, esporas resplandecientes y criaturas bioluminiscentes llenan su crepúsculo eterno de luz azul y verde, y escapó en gran parte a la corrupción que arrasó Draenor. Ahora su equilibrio se tambalea: los nagas de lady Vashj drenan sus aguas con grandes bombas en la Reserva Colmillo Torcido, los ogros talan los hongos y la marisma se muere. La Expedición Cenarion la defiende desde el Refugio Cenarion, y los pacíficos esporiélagos, un pueblo de hongos racionales, viven en Esporaggar.""",

    3519: """Bosque de Terokkar: Un bosque oscuro y antiguo al sur de Terrallende, de altos pinos de cristal, denso dosel verde y claros brumosos, hogar de los arakkoa de aspecto de ave, cuya capital oculta, Skettis, se halla en las montañas del sudeste. Al noroeste se alza Shattrath, refugio para exiliados de todas las razas. La mitad sur son los Páramos de Hueso, arrasados cuando el Concilio de la Sombra invocó una entidad terrible en la necrópolis draenei de Auchindoun y abrió una grieta que atrajo a los etéreos a Terrallende. La Alianza ocupa el Bastión de Allerian y la Horda el Bastión Rompepedras, mientras orcos viles y brujos del Concilio de la Sombra acechan en el bosque.""",

    3703: """Ciudad de Shattrath: La Ciudad de la Luz, la antigua capital draenei al noroeste del Bosque de Terokkar, caída ante los orcos corrompidos por los demonios y reconstruida por los Sha'tar, naaru nacidos de la luz, junto a los sacerdotes draenei Aldor. Los elfos de sangre enviados por Kael'thas para destruirla depusieron las armas y se convirtieron en los Arúspices, rivales acérrimos de los Aldor en la misma ciudad. El naaru A'dal gobierna desde la Terraza de la Luz, donde también reside el archimago Khadgar. El Bajo Arrabal rebosa de refugiados de todas las razas, la violencia entre la Alianza y la Horda está prohibida y portales unen la ciudad con las capitales de Azeroth.""",

    3917: """Auchindoun: La necrópolis destrozada de los draenei en el corazón de los Páramos de Hueso del Bosque de Terokkar, durante milenios su lugar más sagrado, donde enterraban a sus muertos honrados. Agentes del Concilio de la Sombra invocaron en su interior a un antiguo elemental del sonido, y el ritual hizo estallar el templo, arrasó el bosque y abrió una grieta que atrajo a los etéreos a Terrallende. Los muertos draenei vagan ahora por las ruinas como espíritus sin descanso. Sus salas son reclamadas por distintos poderes: etéreos en las Tumbas de Maná, demonios en las Criptas Auchenai, arakkoa en las Salas Sethekk y el Concilio de la Sombra en el Laberinto de las Sombras.""",

    3518: """Nagrand: La última tierra intacta de Terrallende, praderas ondulantes verdes y doradas, lagos resplandecientes e islas flotantes bajo un cielo teñido de rosa. Su nombre significa Tierra de Vientos; fue la patria del clan Lobo Gélido y el lugar de reunión de los orcos al pie de la montaña sagrada de Oshu'gun. Los elementales hablan con los mortales en el Trono de los Elementos. Los orcos mag'har, aún puros, viven en Garadar bajo la guía de la Abuela Geyah, y los tábidos kurenai en Telaar. Los ogros amenazan la tierra, la Legión tiene forjas al oeste y la ciudad de Halaa es disputada por la Alianza y la Horda.""",

    3522: """Montañas Filoespada: Crestas afiladas como cuchillas y valles cortados a hachazos al norte de Terrallende, desgastados por vientos feroces en púas semejantes a dagas bajo el resplandor verde del Vacío. Es la tierra de los ogros de los clanes Filoespada y Mazo Sangriento, que luchan entre sí por el favor de los gronn, gigantes dirigidos por Gruul el Asesino de Dragones desde su guarida en el norte; los huesos de dragones negros muertos cuelgan empalados en los picos. La Legión tiene forjas en las mesetas, y sectarios de los dragones negros acechan en el norte. Los elfos de la noche ocupan Sylvanaar, la Horda el Bastión Señor del Trueno, y los ogros iluminados de Ogri'la viven en una meseta del oeste.""",

    3523: """Tormenta Abisal: Grandes fragmentos de tierra e incontables esquirlas de roca que flotan en el Vacío Abisal al nordeste de Terrallende, antaño los campos de Farahlon. Una tormenta arcana incesante deforma la tierra: el suelo es de un violeta enfermizo, rayos mágicos cruzan una bruma violácea y franjas de energía se retuercen en el cielo mientras la región se desintegra lentamente. Elfos de sangre leales a Kael'thas extraen el Vacío con grandes forjas de maná construidas con la tecnología del Castillo de la Tempestad, que ocupan, y la Legión Ardiente tiene bases en las islas. Los etéreos del Consorcio ocupan la Flecha de la Tormenta y sus ecodomos, y los goblins dirigen el Área 52.""",

    3520: """Valle Sombraluna: Una tierra sombría y arrasada al sudeste de Terrallende, donde día y noche brota energía vil fundida que ilumina el cielo con llamas verdes. Roca negra y ceniza cubren el suelo, y el volcán llamado Mano de Gul'dan escupe lava verde en su centro. Al este se alza el Templo Oscuro, antaño el templo de Karabor de los draenei, hoy la ciudadela de Illidan Tempestira, autoproclamado señor de Terrallende, y de sus Illidari, que contienen a la Legión Ardiente desde el Bastión de la Legión. Los orcos viles Faucedraco esclavizan a los dracos de Ala Abisal. El Bastión Martillo Salvaje, la Aldea Sombraluna y los campamentos de los Aldor y los Arúspices hacen la guerra a Illidan.""",

    3540: """El Vacío Abisal: El caótico reino astral entre los mundos, una dimensión de magia salvaje que une los mundos del universo y es el hogar de los demonios de la Legión Ardiente. Cuando Draenor fue desgarrado, sus restos fueron arrastrados al Vacío, y en los bordes de Terrallende la tierra simplemente termina en un vacío infinito de nubes iridiscentes, cintas de energía de colores y rocas a la deriva. Mundos lejanos se adivinan en el cielo arremolinado, las leyes de la naturaleza parecen inciertas y la mente se esfuerza por comprender lo que ven los ojos. Quien se aventura demasiado lejos puede no regresar jamás.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Tundra Boreal: Una vasta llanura azotada por el viento en el borde sudoeste de Rasganorte, para muchos la primera tierra que ven en la guerra contra el Rey Exánime. Tierra pardo rojiza, líquenes y hielo se extienden bajo un viento capaz de arrancarle la barba a un enano; en el centro humean los géiseres, y el este nevado es el más duro. Mamuts y rinocerontes lanudos recorren las llanuras, y los pacíficos colmillarr pescan y cazan ballenas en la costa, con sus aldeas arrasadas por saqueadores kvaldir. Malygos y el Vuelo Azul dominan la isla de Gelidar, la Plaga ocupa En'kilah, y el Fuerte Denuedo de la Alianza y el Bastión Grito de Guerra de la Horda miran al norte.""",

    495: """Fiordo Aquilonal: Una región agreste al sudeste de Rasganorte, de praderas verdes, ríos helados, oscuros bosques de pinos y altos fiordos cuyos acantilados caen al mar frío. Al fondo de la Bahía Garfaescarcha se alza el Castillo de Utgarde sobre el lago Cauldros. Fue la sede ancestral de los vrykul, guerreros gigantes despertados de un largo sueño; muchos sirven ahora al Rey Exánime y asaltan a quien se acerca. La Alianza ocupa el viejo puerto de Valgarde y la Atalaya Oeste, los Renegados de la Mano de la Venganza ocupan Bahía de la Venganza y Nuevo Agamand, y la Liga de Expedicionarios excava ruinas de los titanes donde han aparecido enanos férreos.""",

    65: """Cementerio de Dragones: El corazón del sur de Rasganorte, un páramo ártico de glaciares de un blanco cegador sembrado de huesos relucientes de dragones, el lugar adonde los dragones acuden a morir. Aquí los guardianes de los titanes crearon a los primeros Aspectos, y los huesos de Galakrond aún sobresalen del hielo. En su centro se alza el Templo del Reposo del Dragón, donde se reúnen los Vuelos dragón, rodeado por los cinco santuarios de dragón. La Plaga asedia los santuarios y alza vermis de escarcha con los huesos, Naxxramas flota sobre las llanuras del este y la Embestida Escarlata ocupa una fortaleza en la costa. La Alianza y la Horda han levantado fortalezas ante la Puerta de Cólera, la entrada cerrada a Corona de Hielo.""",

    394: """Colinas Pardas: Una región boscosa al sudeste de Rasganorte, suaves colinas verdes cubiertas de pinos que suben hacia montañas escarpadas, donde el espeso bosque frena el viento y las colinas parecen casi templadas. Osos, lobos, ciervos y búhos nivales llenan los bosques. Es la patria de los fúrbolgs, cuya ciudad de Fauceparda se alza en el tocón de Vordrassil, un Árbol del Mundo que los druidas destruyeron al hallarlo corrompido, y una locura rastrera se extiende entre sus tribus. Tramperos mantienen puestos comerciales en el bosque, la Plaga ocupa el Fuerte Drak'Tharon en el norte, y la Alianza y la Horda se disputan los campamentos madereros.""",

    4201: """Lágrimas de Vordrassil: Uno de los grandes fragmentos caídos del Árbol del Mundo Vordrassil, en las Colinas Pardas. Hace mucho, Fandral Corzocelada plantó ramas de Nordrassil por todo Rasganorte, y la mayor de ellas, Andrassil, la Corona de la Nieve, dominó estas colinas durante décadas. Pero sus raíces alcanzaron la prisión de un mal antiguo, y la locura se extendió entre las criaturas de la región, así que el Círculo Cenarion destruyó el árbol y lo llamó Vordrassil, la Corona Rota. Sus pedazos aún yacen en el bosque, y la tierra alrededor de este fragmento está cubierta de un limo vivo, señal de la corrupción que lo condenó.""",

    3477: """Azjol-Nerub: Un inmenso reino subterráneo bajo la mitad de Rasganorte, el antiguo reino de los nerubianos arácnidos, un pueblo dedicado al saber, al arte y a la filosofía, de pasillos pulidos, salas talladas y grandes bibliotecas iluminadas por hongos luminosos. El Rey Exánime vio en ellos la mayor amenaza para su poder y arrasó el reino en la Guerra de la Araña; cada nerubiano caído se alzaba para luchar por la Plaga, y su propio rey Anub'arak le sirve ahora. Nerubianos no-muertos custodian nidadas en el Reino Superior, supervivientes vivos libran una guerra oculta y en el Reino Antiguo de Ahn'kahet se agitan los Sin Rostro.""",

    66: """Zul'Drak: La patria de los trols de hielo Drakkari al este de Rasganorte, un valle que es en sí mismo una inmensa ciudad templo de plazas, zigurats, murallas y acueductos construidos en terrazas, con árboles espinosos, estanques helados y nieve entre las ruinas. Los Drakkari se cuentan entre las razas más antiguas de Azeroth y gobiernan desde Gundrak, pero su imperio se derrumba. La Plaga ocupa el Fuerte Drak'Tharon y sus necrópolis alzan a los trols caídos contra su propio pueblo. Desesperados, los profetas Drakkari han matado a sus propios dioses, los loas, y beben su sangre para obtener poder, lo que ha enloquecido a muchos. La Cruzada Argenta y los Zandalari han venido a intervenir.""",

    3711: """Cuenca de Sholazar: Una cuenca de jungla tropical en medio de Rasganorte, rodeada de altas montañas, calurosa, húmeda y rebosante de vida tras el frío cortante del exterior. La guardiana Freya la convirtió en una cuna de vida, y pilones de los titanes coronados de cristales giratorios mantienen su calor y la protegen de criaturas impuras. Cuatro ríos se unen en el Corazón del Río, en el denso Manglar Silvestre. Rinocerontes, gorilas, crocoliscos e hidras pueblan la jungla, y los gorlocs del Oráculo combaten a los wolvar Corazón Frenético. La Plaga ha irrumpido en la cuenca por el este, y el Avatar de Freya lucha por contener la plaga que se extiende.""",

    2817: """Bosque Canto de Cristal: Una tierra en medio de Rasganorte donde cada árbol, cada brizna de hierba y gran parte del suelo se han convertido en cristal vivo y luminoso, que vibra con el viento de modo que el bosque toca una música suave e interminable. Antaño fue Canción de la Luna, donde los Altonato mantenían el puesto de Shandaral; cuando los dragones azules llegaron a vengarse por reliquias robadas, el hechizo imprudente de los hechiceros cristalizó todo el bosque, y sus espíritus aún vagan por él. Dalaran flota ahora sobre el oeste del bosque, el Pacto de Plata y los Atracasol ocupan torres en ruinas en lados opuestos, y el Vuelo Azul libra la Guerra del Nexo en el sur.""",

    4395: """Dalaran: La ciudad de los magos y hogar del Kirin Tor, cuyas agujas violetas se alzaban antaño junto al Lago Lordamere, hasta que la Plaga la destruyó en la Tercera Guerra. El Kirin Tor elevó la ciudad entera al cielo y la trasladó a Rasganorte, donde flota sobre el Bosque Canto de Cristal para enfrentarse al Rey Exánime y al Aspecto azul Malygos, cuya guerra contra los lanzadores de hechizos la convierte en objetivo principal. El Consejo de los Seis, dirigido por el archimago Rhonin, gobierna desde la Ciudadela Violeta. Dalaran acoge a la Alianza y a la Horda: el Pacto de Plata y los Atracasol mantienen sus propios enclaves y se vigilan con recelo.""",

    4197: """Conquista del Invierno: Un valle helado en el centro de Rasganorte, elevado sobre las tierras vecinas, el lecho de un lago reducido que ha dejado al descubierto ruinas de los titanes, bosques oscuros, pantanos helados y un caldero volcánico. En su corazón se alza la Fortaleza de Conquista del Invierno, un complejo titánico que custodia la entrada a la Cámara de Archavon, donde reposan reliquias de los titanes de un poder inimaginable bajo la vigilancia de antiguos gigantes que detestan a todo intruso. Desde el inicio de la guerra contra el Rey Exánime, la Alianza y la Horda luchan sin fin por la fortaleza y la cámara, golpeando sus muros con máquinas de asedio mientras el control cambia de manos una y otra vez.""",

    67: """Las Cumbres Tormentosas: Una imponente cordillera al nordeste de Rasganorte, dura y peligrosa, donde vientos feroces pueden arrancar a un enano de un acantilado, las avalanchas retumban por las laderas y el brillo del hielo ciega a los incautos. Las cumbres fueron el hogar de los guardianes de los titanes, y casi cada montaña oculta templos, terrazas y máquinas inmensas; el Templo de las Tormentas corona el pico más alto, y al norte se extiende Ulduar, el mayor complejo de los titanes de Azeroth. Su guardián Loken se ha vuelto hacia la oscuridad, y sus enanos y gigantes férreos expulsan a los terráneos de su hogar. Los gigantes de escarcha de los Hijos de Hodir ocupan los valles del este.""",

    210: """Corona de Hielo: El oscuro corazón de Rasganorte y sede del Rey Exánime, una tierra de montañas y glaciar donde el hielo se ha ennegrecido de corrupción. Desde el Trono Helado, el Rey Exánime esclavizó a los pueblos de Rasganorte y alzó la Plaga, y alrededor del trono se alza la Ciudadela de Corona de Hielo, una catedral de hojas de saronita visible desde casi cualquier lugar del continente. Murallas y pasarelas de saronita unen fortalezas, necrópolis y minas, y los no-muertos superan en número a todo lo demás. Ahora la guerra ha llegado a su puerta: la Cruzada Argenta y los Caballeros de la Espada de Ébano atacan desde fortalezas conquistadas, y las naves de guerra de la Alianza y de la Horda combaten en el cielo.""",

    4742: """Desembarco de Hrothgar: Una pequeña isla envuelta en niebla frente a la costa norte de Corona de Hielo, al otro lado del estrecho llamado Paso del Saqueador. Allí se alzaba una aldea colmillarr, hasta que llegaron los kvaldir, los malditos vrykul del mar, bajo su caudillo Hrothgar, mataron o expulsaron a sus habitantes y dieron a la isla su nombre. Ahora es una base para los asaltos kvaldir contra los barcos del estrecho, donde invocan grandes kraken de las profundidades, mientras las flotas del Pacto de Plata y de los Atracasol luchan por rechazarlos.""",

    # -------------------------------------------------------------------------
    # Seas
    # -------------------------------------------------------------------------
    308: """Mar Prohibido: Un mar vasto, frío y apenas cartografiado a lo largo de la costa este de los Reinos del Este, desde el Pantano de las Penas hasta el Bosque Canción Eterna. Sus aguas grises son bravas y a menudo envueltas en niebla, fuertes corrientes y tormentas repentinas hacen peligrosa la navegación, y gran parte de la costa está cerrada por acantilados y montañas. Pocos barcos se alejan de la orilla, y los marinos hablan de tierras desconocidas y criaturas terribles más allá del horizonte. Tiburones y serpientes marinas viven en sus profundidades, y múrlocs y nagas acechan en sus orillas.""",

    214: """Mare Magnum: El inmenso océano entre los continentes de Azeroth, nacido cuando el Pozo de la Eternidad fue destruido y el antiguo Kalimdor se partió en la Gran Fractura; todos los mares del mundo se unen a él. Sus aguas de un azul profundo se extienden más allá del horizonte, y los marinos hablan de islas perdidas, ciudades hundidas y el gran remolino de la Vorágine en su corazón, donde estuvo el Pozo. Las tormentas se levantan de repente, y se dice que serpientes marinas, tiburones gigantes y nagas acechan en sus profundidades. Barcos de la Alianza, la Horda, los goblins y los piratas lo cruzan sin cesar entre los continentes.""",

    332: """Mare Magnum: El mar abierto entre los continentes de Azeroth, nacido cuando el Pozo de la Eternidad implosionó en la Gran Fractura. Lejos de cualquier costa, solo se extiende un agua azul infinita en todas direcciones, rota por alguna isla lejana o un barco de paso. El oleaje sube y baja, las aves marinas vuelan en círculos muy alto y en las profundidades nadan criaturas que pocos han visto. Los marinos hablan con temor de la Vorágine, el colosal remolino en el centro del mar, y de los innumerables barcos perdidos en tormentas y abismos. Es un lugar de soledad y peligro, donde reinan el viento y las olas.""",

    457: """Mar de la Bruma: El gran océano frente a las costas oeste de Kalimdor, que se extiende desde Costa Oscura, Vallefresno, Desolace y Feralas hacia el oeste desconocido. A menudo está envuelto en bruma, de ahí su nombre; sus aguas son profundas, frías en el norte y más cálidas en el sur. Teldrassil se alza de él frente a la costa noroeste, y las islas Bruma Azur se encuentran en sus aguas. Nagas, gigantes marinos y serpientes marinas viven en sus profundidades, y las ruinas hundidas de antiguas ciudades elfas de la noche yacen bajo sus olas. Más allá de las costas conocidas apenas ha sido explorado.""",

    3479: """Mar de la Bruma: Las aguas alrededor de las islas Bruma Azur, frente al noroeste de Kalimdor, donde se estrelló la nave draenei llamada el Exodar. El mar es profundo y a menudo velado por la bruma, y los restos y cristales de la nave caída dan a algunas aguas costeras un brillo extraño, sobre todo alrededor de la Isla Bruma de Sangre, cuyas orillas se tiñen de rojo. Múrlocs y nagas viven a lo largo de las costas, ruinas elfas de la noche hundidas yacen bajo las olas y los barcos navegan entre el Exodar y las tierras de los elfos de la noche, mientras al este Teldrassil se alza del mar.""",

    3455: """Mar del Norte: Las aguas frías frente a las costas norte de Quel'Thalas, que se extienden desde el Bosque Canción Eterna hacia el norte, en dirección a Rasganorte. La Isla de Quel'Danas se alza de ellas frente a la costa norte, y los barcos élficos que las surcan unen desde hace mucho la patria de los elfos con el resto del mundo. Las aguas son frías y grises, y los vientos que las barren traen el frío del norte helado.""",

    4258: """Mar del Norte: Las aguas frías a lo largo de las costas sudeste de Rasganorte, frente a las Colinas Pardas y el Fiordo Aquilonal, que llegan al sur hasta las costas norte de Lordaeron. Islas como la Isla Luna de Sangre y las Ruinas de Tethys salpican el agua gris. Barcos de la Alianza y de los Renegados la cruzan rumbo a los puertos del fiordo, mientras drakkares vrykul y saqueadores kvaldir merodean entre la niebla.""",

    4630: """Mar del Norte: Las aguas gélidas alrededor de las costas este y norte de Rasganorte, grises y llenas de hielo a la deriva bajo vientos cortantes. Pocos barcos se aventuran lejos en ellas, pues icebergs y niebla ocultan las costas, y se dice que los malditos kvaldir y otros saqueadores del mar surgen de las brumas.""",

    3979: """Mar Gélido: El mar frío al sur de Rasganorte, parte de Mare Magnum, que se extiende desde las costas sur de la Tundra Boreal, el Cementerio de Dragones y el Fiordo Aquilonal hasta la Vorágine. Hielo flotante e icebergs derivan por sus aguas grises. Las flotas de la Alianza y de la Horda lo cruzan para llegar al continente, los colmillarr viajan en tortugas gigantes entre sus aldeas costeras y las columnas talladas del antiguo Sendero de los Titanes emergen de las olas. Saqueadores kvaldir y monstruos marinos rondan sus profundidades.""",
}

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'Un valle oculto en lo profundo de las Montañas de '
            'Alterac, hogar de los orcos Lobo Gélido desde que '
            'Gul\'dan los desterró allí antes de la Primera Guerra. '
            'Los enanos de la Expedición Pico Tormenta llegaron en '
            'busca de recursos y reliquias de los titanes y reclaman '
            'el valle para Forjaz, y los Lobo Gélido han jurado '
            'expulsarlos. La guerra arde ahora desde la fortaleza de '
            'Dun Baldar en el norte hasta el Bastión Lobo Gélido en '
            'el sur.'
        ),
        'tone': (
            'Épico y enorme, una verdadera guerra entre dos ejércitos '
            'en la nieve.'
        ),
        'objectives': (
            'Mata al general enemigo. Conquista torres y cementerios.'
        ),
        'landmarks': (
            'Lugares clave: Dun Baldar y los búnkeres Pico Tormenta '
            'en el norte, Piedrahogar y Avalancha en el centro, la '
            'Torre Sangrehielo y la Torre de la Punta, el cementerio '
            'y el Bastión Lobo Gélido en el sur. Nieve, bosques de '
            'pinos, pasos de montaña y cuevas de hielo. NO menciones '
            'lugares de otros campos de batalla.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'Un barranco boscoso al sur de Vallefresno, donde los '
            'orcos de Grom Grito Infernal talaron grandes franjas de '
            'bosque durante la Tercera Guerra. Los orcos de los '
            'Escoltas Grito de Guerra aún talan madera aquí para la '
            'Horda, y las Centinelas Ala de Plata de los elfos de la '
            'noche han jurado no descansar hasta expulsar al último '
            'orco de la garganta.'
        ),
        'tone': (
            'Intenso, rápido y personal, una lucha encarnizada por el '
            'bosque.'
        ),
        'objectives': 'Captura la bandera enemiga tres veces.',
        'landmarks': (
            'Lugares clave: el Bastión Ala de Plata (fortaleza de los '
            'elfos de la noche), el fuerte Grito de Guerra (fortaleza '
            'de los orcos), los túneles bajo cada base, el campo '
            'central abierto, las rampas y los cementerios. Árboles '
            'altos, tocones y pilas de madera. NO menciones lugares '
            'de otros campos de batalla como aserraderos, granjas o '
            'torres.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'Una cuenca fértil en el corazón de las Tierras Altas de '
            'Arathi, rica en mineral, madera y tierras de cultivo. La '
            'Liga de Arathor, lo que queda de Stromgarde, lucha por '
            'recuperar los recursos de la región, mientras los '
            'Rapiñadores Renegados buscan apoderarse de ellos para la '
            'Horda.'
        ),
        'tone': (
            'Estratégico y territorial, disputado en toda la cuenca a '
            'la vez.'
        ),
        'objectives': (
            'Controla los nodos para llegar primero a 1600 recursos.'
        ),
        'landmarks': (
            'Lugares clave: Establos (norte, pastos abiertos con '
            'cercados de caballos), Herrería (cruce central, humo y '
            'yunques), Aserradero (mirador en la colina, plataformas '
            'de madera y hojas de sierra), Mina de oro (entrada de '
            'cueva al sudeste, vagonetas y antorchas), Granja (sur, '
            'campos y almiares junto a una casa de labranza). NO '
            'menciones lugares de otros campos de batalla.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'Un fragmento de Draenor que flota en el Vacío Abisal en '
            'el borde de Tormenta Abisal, donde cuatro ruinas se '
            'alzan sobre una gran isla alrededor de una fuente de '
            'energía pura en su centro. La Alianza y la Horda luchan '
            'por controlar la isla y su poder.'
        ),
        'tone': (
            'Tenso y caótico, con el vacío del Vacío Abisal justo al '
            'otro lado de los bordes.'
        ),
        'objectives': (
            'Controla bases y captura la bandera central para llegar '
            'a 1600 puntos.'
        ),
        'landmarks': (
            'Lugares clave: Ruinas del Atracador Vil, Torre de los '
            'Elfos de Sangre, Ruinas Draenei, Torre de los Magos, los '
            'puentes y la bandera central. Piedra violeta, energía '
            'crepitante y el Vacío infinito alrededor. NO menciones '
            'lugares de otros campos de batalla.'
        ),
    },
    9: {  # SA (BATTLEGROUND_SA = 9)
        'name': 'Strand of the Ancients',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'Una isla frente a la costa sur del Cementerio de '
            'Dragones, donde una reliquia de los titanes reposa tras '
            'los muros desmoronados de una antigua ciudadela. La '
            'Alianza y la Horda la codician por el saber de los '
            'titanes que se dice que guarda: un bando asalta los '
            'muros desde el mar mientras el otro los defiende.'
        ),
        'tone': (
            'Un asedio agotador, oleada tras oleada contra muros '
            'antiguos.'
        ),
        'objectives': (
            'Abre brecha en las puertas y captura la reliquia, o '
            'defiéndela el mayor tiempo posible.'
        ),
        'landmarks': (
            'Lugares clave: la playa y los muelles donde desembarcan '
            'los atacantes, la Puerta del Esmeralda Verde y la Puerta '
            'del Zafiro Azul, la Puerta del Sol Rojo y la Puerta de '
            'la Amatista Púrpura, la Puerta de la Luna Amarilla, la '
            'Cámara de las Reliquias Antiguas, demoledores, cañones y '
            'cementerios. Arena reluciente, piedra titánica y olas '
            'que rompen. NO menciones lugares de otros campos de '
            'batalla.'
        ),
    },
    30: {  # IC (BATTLEGROUND_IC = 30)
        'name': 'Isle of Conquest',
        'alliance_faction': '7th Legion',
        'horde_faction': 'Warsong Offensive',
        'lore': (
            'Una isla de gran valor estratégico para la guerra en '
            'Rasganorte, con muelles, una cantera, una refinería, un '
            'taller de asedio y un hangar de naves de guerra. La '
            'Alianza, bajo el alto comandante Halford Aterravermis, y '
            'la Horda, bajo el señor supremo Agmar, ocupan cada una '
            'una fortaleza en la isla y luchan por controlarla.'
        ),
        'tone': (
            'Enorme y mecanizado, máquinas de asedio y naves de '
            'guerra en guerra abierta.'
        ),
        'objectives': (
            'Mata al general enemigo. Conquista los muelles, el '
            'taller y el hangar para abrir brecha en la fortaleza '
            'enemiga.'
        ),
        'landmarks': (
            'Lugares clave: la fortaleza de la Alianza al oeste, la '
            'fortaleza de la Horda al este, los Muelles, el Taller, '
            'el Hangar con sus naves de guerra, la Cantera y la '
            'Refinería. Máquinas de asedio, cañones y muros de '
            'hierro. NO menciones lugares de otros campos de batalla.'
        ),
    },
}

DUNGEON_FLAVOR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Castillo de Colmillo Oscuro: Un castillo embrujado sobre un risco por encima de Aldea Piroleña, al sur del Bosque de Argénteos, antaño la sede del barón Filargenta. Durante la Tercera Guerra, el archimago Arugal invocó a los huargen contra la Plaga, pero se volvieron contra todos; enloquecido por la culpa, los adoptó como sus hijos e hizo del castillo su guarida. Los huargen acechan en patios y torres, sirvientes no-muertos recorren las salas y se dice que el fantasma vengativo del barón sigue allí. Piedra fría, antorchas vacilantes y aullidos de lobo llenan la noche.""",

    34: """Las Mazmorras: Una prisión de alta seguridad oculta bajo el distrito de los canales de Ventormenta, donde se encierra a rateros, agitadores políticos, asesinos y algunos de los criminales más peligrosos del reino, muchos de ellos Defias. Una revuelta reciente ha expulsado a los guardias, y los reclusos vagan ahora libremente por celdas y pasillos bajo las órdenes del astuto criminal que encabezó el motín. El aire es húmedo y viciado, el agua gotea de la piedra y los gritos de los presos resuenan por los estrechos pasillos.""",

    36: """Las Minas de la Muerte: Una vieja mina de oro bajo la aldea fantasma de Arroyoluna, en los Páramos de Poniente, la fortaleza oculta de la Hermandad Defias, forajidos nacidos de los canteros no pagados de Ventormenta. Mineros Defias, ingenieros goblin y ogros trabajan en los túneles, y los pasadizos desembocan en una enorme cala oculta donde la Hermandad construye un gran buque de guerra, pieza central de sus planes contra el reino. Los túneles son oscuros y estrechos, huelen a polvo, aceite y pólvora, y por todas partes crujen las vigas y traquetea la maquinaria.""",

    43: """Cuevas de los Lamentos: Una red de cuevas bajo el corazón de Los Baldíos, llamada así por los largos gemidos lastimeros de las fisuras de vapor que escapan por ellas. El druida elfo de la noche Naralex esperaba usar sus manantiales y el poder del Sueño Esmeralda para devolver el verdor a Los Baldíos, pero su sueño se convirtió en pesadilla. Las aguas se pudrieron, las bestias del interior se transformaron en depredadores feroces y sus propios discípulos se convirtieron en los Druidas del Colmillo. Se dice que Naralex yace en algún lugar de las profundidades, atrapado en su pesadilla despierta.""",

    47: """Horado Rajacieno: La gran madriguera de espinas de los jabaespines en el borde sur de Los Baldíos, nacida de las lianas que brotaron donde se derramó la sangre del semidiós Agamaggan en la Guerra de los Ancestros. Los jabaespines la veneran como el hogar de su raza. La vieja bruja Charlga Filonavaja la gobierna, sus chamanes atacan a tribus rivales y aldeas de la Horda, y algunos susurran que trata con emisarios de la Plaga. Enormes lianas espinosas se cierran sobre las cabezas, y los túneles son fangosos, estrechos y llenos de jabalíes.""",

    48: """Cavernas de Brazanegra: Antaño un glorioso templo de la diosa de la luna Elune en la Ribera de Zoram, en Vallefresno, destrozado por la Gran Fractura y hundido bajo las olas del Mar de la Bruma. Sus cuevas inundadas y ruinas rotas descienden hasta un santuario de los Dioses Antiguos. Nagas y sátiros escudriñan sus secretos, el culto del Martillo Crepuscular trabaja a su lado y se dice que en las profundidades mora la antigua bestia Aku'mai, favorita de los Dioses Antiguos. Agua fría, piedra resbaladiza y una luz tenue e inquietante llenan las cavernas.""",

    70: """Uldaman: Una antigua cámara de los titanes enterrada en lo profundo del norte de las Tierras Inhóspitas, abierta recientemente por excavaciones enanas que liberaron a los troggs, las primeras creaciones fallidas de los titanes. Las leyendas dicen que la cámara guarda los secretos de la creación de los enanos en los legendarios Discos de Norgannon. Los enanos Hierro Negro excavan aquí para su amo Ragnaros, mientras guardianes de piedra viva aplastan a cualquier intruso. Vastas salas de piedra tallada, pasadizos derrumbados y silenciosa maquinaria titánica yacen bajo el peso de las montañas.""",

    90: """Gnomeregan: La maravilla tecnológica que fue la capital de los gnomos bajo las nieves de Dun Morogh, perdida cuando los troggs invadieron desde las profundidades y los gnomos, desesperados, liberaron los residuos radiactivos de la ciudad. Irradiados pero no vencidos, los troggs aún vagan por sus salas, y los gnomos supervivientes huyeron a Forjaz. El traidor mekigeniero Termochufe gobierna las ruinas como un tecnoseñor demente. Maquinaria traqueteante, tuberías que gotean, lodo tóxico y centinelas de alarma llenan los pasillos sinuosos.""",

    109: """El Templo de Atal'Hakkar: El templo que los sacerdotes Atal'ai exiliados alzaron en el Pantano de las Penas para preparar el regreso del dios de la sangre Hakkar el Desollador de Almas. El Aspecto dragón Ysera lo hundió bajo el pantano, y sus dragones verdes aún custodian las ruinas sumergidas, algunos ya corrompidos. Pero Atal'ai fanáticos han sobrevivido en su interior y siguen sirviendo a Hakkar. Salas inundadas, piedra desmoronada e ídolos trols yacen en agua turbia, y el aire pesa de podredumbre y vieja magia de sangre.""",

    129: """Zahúrda Rajacieno: Los túmulos funerarios ancestrales y capital tradicional de los jabaespines, un vasto laberinto de espinas en el borde sur de Los Baldíos, nacido de las mismas poderosas lianas que el Horado Rajacieno. Una sombra amenazante ha caído sobre el lugar: se dice que la Plaga se ha apoderado de la zahúrda, que un liche manda sobre los sumos sacerdotes Cabeza de Muerte y que los muertos de los túmulos vuelven a levantarse. Una niebla fría se aferra a las zarzas, y el hedor de la muerte se mezcla con el barro y las espinas.""",

    189: """Monasterio Escarlata: Antaño un orgulloso centro de estudio del clero de Lordaeron al nordeste de los Claros de Tirisfal, hoy una fortaleza de la fanática Cruzada Escarlata, que no confía en nadie que no sea humano y ve en cada forastero un portador de la peste. Su cementerio, biblioteca, armería y catedral están en manos de guerreros fervientes bajo el comandante escarlata Mograine, mientras la alta inquisidora Melenablanca, de quien se dice que devuelve a los caídos al combate, es la verdadera señora del monasterio. Estandartes rojos, incienso y los gritos de los fieles llenan sus salas.""",

    209: """Zul'Farrak: La ciudad amurallada de los trols Furiarena en los desiertos del noroeste de Tanaris, piedra abrasada por el sol y pirámides que surgen de las dunas. Sus guerreros, sacerdotes y médicos brujos la defienden con fiereza y alzan a los muertos para protegerla. Las leyendas hablan de una poderosa espada trol partida en dos que se hallaría en algún lugar de su interior, de mercenarios que se perdieron en la ciudad y nunca volvieron, y de una antigua criatura dormida en el estanque sagrado de su corazón. Calor, arena y escórpidos están por todas partes.""",

    229: """Cumbre de Roca Negra: La fortaleza tallada en las alturas de la Montaña Roca Negra por el maestro cantero Hierro Negro Franclorn Forjador como símbolo de su poder. La Horda orca la convirtió en su capital en la Segunda Guerra. Hoy la ocupan la Horda Oscura del jefe de guerra Rend Puño Negro, con orcos, ogros y trols, y el dragón negro Nefarian y sus dracónidos, que dominan la parte alta de la cumbre y libran la guerra contra Ragnaros en las profundidades. Lava, cadenas, puertas de hierro y dracos que giran en el humo hacen de ella una fortaleza inmensa y mortal.""",

    230: """Profundidades de Roca Negra: La que fue gran capital de los enanos Hierro Negro, un laberinto volcánico en lo más hondo de la Montaña Roca Negra, gobernado hoy por el emperador Dagran Thaurissan como sede del poder de Ragnaros, el Señor del Fuego. Las forjas arden, la lava fluye por las salas, se construyen gólems de piedra viva para el ejército del Señor del Fuego, y una arena, una prisión y una taberna se abren entre sus vastas cámaras. Soldados Hierro Negro, elementales de fuego y cautivos esclavizados pueblan la ciudad. El calor es abrumador y el martilleo nunca cesa.""",

    269: """La Ciénaga Negra: Un viaje a través de las Cavernas del Tiempo a los pantanos de la Ciénaga Negra, el día en que Medivh, el último Guardián de Tirisfal, abrió el Portal Oscuro y dejó entrar a la Horda orca en Azeroth. El Vuelo Bronce custodia ese momento, pues el Vuelo Infinito envía oleada tras oleada a través de grietas en el tiempo para matar a Medivh y cambiar la historia. Niebla, agua estancada y árboles retorcidos rodean el portal que crece, y el propio tiempo parece temblar.""",

    289: """Scholomance: Una escuela de nigromancia en las criptas bajo Caer Darrow, un viejo castillo en una isla del lago Darrowmere. La noble familia Barov cedió el castillo al Culto de los Malditos de Kel'Thuzad a cambio de la inmortalidad prometida, y el culto convirtió sus criptas en una academia que formó a quienes propagaron la peste. Los Barov recorren ahora sus salas como no-muertos, el liche Ras Levescarcha la custodia para la Plaga y el nigromante maestro oscuro Gandling la dirige como director. Velas, huesos y tomos prohibidos llenan sus aulas.""",

    329: """Stratholme: La segunda ciudad de Lordaeron, donde se fundó la Orden de la Mano de Plata y donde el príncipe Arthas masacró a la población infectada por la peste. Hoy es la capital de la Plaga en Lordaeron, y sigue ardiendo. La ciudad está dividida entre la Cruzada Escarlata, que ocupa el Bastión Escarlata bajo el gran cruzado Dathrohan, y la Plaga, cuyo caballero de la Muerte, el barón Osahendido, gobierna los zigurats de los barrios del este. La ceniza flota sobre calles destruidas, y las plazas están llenas de muertos.""",

    349: """Maraudon: Un lugar sagrado de los centauros en el Valle de las Lanzas, en Desolace, la tumba de Zaetar, hijo de Cenarius, y el hogar de la princesa elemental de tierra Theradras, madre de la raza de los centauros. Sus hijos malditos mataron a su padre, y Theradras guarda su cuerpo en sus cavernas de cristal. La bendición de la naturaleza convirtió su lugar de descanso en un paraíso subterráneo de flores y estanques, mientras cuevas manchadas de púrpura, elementales de tierra y los espíritus de los khans centauros llenan el laberinto. Los centauros Maraudine lo custodian con fiereza.""",

    389: """Sima Ígnea: Una red de cuevas volcánicas bajo Orgrimmar, llena de lava y fuego. Los troggs han subido desde las profundidades y rechazan todo intento de paz, y un culto leal al Filo Ardiente y al Concilio de la Sombra se ha refugiado en la sima, conspirando para destruir todo lo que la Horda ha construido en Durotar. Los túneles arden, la luz es roja y el siseo de la roca fundida nunca cesa, un peligro que acecha justo bajo la capital.""",

    429: """La Masacre: Las ruinas de Eldre'Thalas, una ciudad de los Altonato construida hace doce mil años al norte de Feralas para guardar los secretos arcanos más preciados de la reina Azshara. Arrasada por la Gran Fractura, gran parte de ella sigue en pie. Los ogros Gordunni dominan el barrio norte, sátiros y ancestros corrompidos rondan los jardines del este, y los últimos Altonato, los reservados Shen'dralar, ocupan las salas del oeste y su gran biblioteca, guardando los males antiguos encerrados en sus cámaras. Mármol roto, arcos élficos y patios invadidos por la maleza llenan la ciudad.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Guarida de Onyxia: Una cueva volcánica en la Ciénaga de los Dragones, al sur del Marjal Revolcafango, la guarida de Onyxia, madre del Vuelo Negro e hija de Alamuerte. Un estrecho túnel de roca chamuscada desciende, entre crías y dracónidos, hasta una sala inmensa sembrada de huesos y nidadas. El suelo de la cueva no es más que una fina costra sobre roca fundida, y el aire está cargado de humo y azufre. La propia Onyxia llena la sala de fuego y sombra, y pocos de los que entran en su guarida regresan.""",

    309: """Zul'Gurub: La antigua capital del imperio Gurubashi al nordeste de la Vega de Tuercespina, una enorme ciudad trol de templos y zigurats invadida por la jungla. Hace más de mil años, los Atal'ai invocaron a Hakkar el Desollador de Almas y destrozaron el imperio; ahora el dios de la sangre ha regresado al corazón de las ruinas. Los sumos sacerdotes enviados por las tribus para detenerlo, campeones del Murciélago, la Pantera, el Tigre, la Araña y la Serpiente, han caído bajo su dominio y alimentan su poder. Rituales de sangre, tambores y los gritos de las bestias de la jungla llenan el aire.""",

    409: """Núcleo de Magma: El corazón ardiente de la Montaña Roca Negra, en lo más profundo, donde Thaurissan invocó a Ragnaros, el Señor del Fuego, a este mundo. El Señor del Fuego mora aquí en un lago de fuego que sirve de grieta hacia el plano elemental, y sus sirvientes, los velaflamas y su mayordomo Ejecutus, mandan sobre los elementales y los enanos Hierro Negro esclavizados. Ríos de lava fluyen entre plataformas de obsidiana, canes del Núcleo y gigantes fundidos recorren las cuevas, y el calor es abrumador.""",

    469: """Guarida Alanegra: La guarida del dragón negro Nefarian en lo alto de la Cumbre de Roca Negra, donde conspira para aplastar a Ragnaros y adueñarse de toda la Montaña Roca Negra. Como su padre Alamuerte, cría un nuevo ejército experimentando con la sangre de todos los Vuelos dragón para crear guerreros imparables. Laboratorios, salas de supresión y criaderos de dracos llenan la guarida, custodiados por dracónidos negros y sus creaciones más terribles. Calor, humo y el hedor de la sangre de dragón flotan en las salas.""",

    509: """Ruinas de Ahn'Qiraj: Las ruinas exteriores de la ciudad de Ahn'Qiraj tras el Muro del Escarabajo, al sur de Silithus, donde los qiraji y sus silítidos fueron encerrados hace mil años al final de la Guerra de las Arenas Movedizas. Las puertas se han abierto de nuevo, y los ejércitos de la Alianza y de la Horda han empujado a los qiraji de vuelta a las ruinas. Colosales estructuras de piedra y columnas surgen de la arena entre colmenas silítidas, y los generales qiraji y sus enjambres defienden las ruinas con fiereza.""",

    531: """Templo de Ahn'Qiraj: El gran templo en el corazón de Ahn'Qiraj, al sur de Silithus, fortaleza de los emperadores qiraji y de sus enjambres silítidos. Oscuros susurros dicen que debajo un Dios Antiguo se agita en su guarida, recuperando fuerzas tras milenios, y que los dragones que se sacrificaron para encerrarlo yacen en su interior debilitados o esclavizados. Vastas salas insectoides, colmenas palpitantes y cámaras retorcidas descienden cada vez más, y con cada paso crece un terror extraño y opresivo.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Las Salas Arrasadas: El ala más profunda de la Ciudadela del Fuego Infernal, en la península del mismo nombre, campo de entrenamiento y cuartel de los orcos viles. Aquí el jefe de guerra Kargath Garrafilada manda sobre la Horda Vil, los brujos del Concilio de la Sombra obran su magia oscura, los gladiadores combaten en la arena y los arqueros hacen llover fuego sobre los estrechos pasillos. Las salas son brutales, angostas y llenas del estruendo de las armas, y todas están empapadas de sangre y energía vil.""",

    542: """El Horno de Sangre: Un ala de la Ciudadela del Fuego Infernal donde los orcos viles sangran al señor del foso Magtheridon encerrado y usan su sangre para engendrar una nueva Horda Vil, imbuida de poder demoníaco. Tinas de sangre corrompida, celdas de prisioneros y brujos encadenados bordean las salas del horno. Los hechiceros orcos viles canalizan la energía del demonio cautivo que yace debajo, y el aire está cargado de vapores viles, calor y gritos.""",

    543: """Murallas del Fuego Infernal: Las murallas y torres fortificadas de la Ciudadela del Fuego Infernal, la primera línea de defensa de los orcos viles. Orcos viles patrullan las almenas, sus vigías mandan sobre los muros y un campeón orco vil monta un dragón abisal sobre las torres. Las murallas dominan el páramo rojo, el Portal Oscuro y las forjas de la Legión. Viento, fuego vil y el rugido de los dracos llenan el aire.""",

    545: """La Cámara de Vapor: El corazón de la Reserva Colmillo Torcido, en la Marisma de Zangar, donde los nagas de lady Vashj hacen funcionar grandes máquinas y bombas de vapor que drenan las aguas de la marisma. Guerreros nagas, sirenas y elementales de agua custodian la cámara, y tábidos esclavizados trabajan en las salas. Tuberías que silban, turbinas que rugen y nubes de vapor llenan el aire, y las paredes chorrean condensación. El zumbido de las máquinas nunca cesa.""",

    546: """La Sotiénaga: Un ala de la Reserva Colmillo Torcido, en la Marisma de Zangar, hogar de la última vida natural de la marisma que los nagas aún no han exterminado. Hongos gigantes, señores del pantano, murciélagos de esporas y bestias hambrientas prosperan en sus cuevas, mientras los nagas defienden un templo donde guardan a su dios hidra Ghaz'an. Hongos brillantes, agua turbia y un aire espeso cargado de esporas la convierten en un lugar salvaje e indómito.""",

    547: """Recinto de los Esclavos: La primera ala de la Reserva Colmillo Torcido, en la Marisma de Zangar, donde los nagas de lady Vashj mantienen a tábidos y señores del pantano esclavizados trabajando en sus grandes bombas. Capataces nagas y sus sirvientes patrullan los corrales, mientras los esclavos trabajan encadenados. Pasarelas de madera, jaulas de hierro y agua que gotea llenan las salas, y los gritos de los cautivos resuenan sobre la reserva.""",

    552: """El Arcatraz: Un satélite del Castillo de la Tempestad, en Tormenta Abisal, donde los naaru encerraron a las criaturas más peligrosas que encontraron en sus viajes: demonios, agentes del Vuelo Negro e incluso sirvientes de los Dioses Antiguos. Los elfos de sangre de Kael'thas lo custodian ahora, pero son corruptibles, y los prisioneros se están liberando. Celdas de fuerza reluciente, pasillos de cristal y los aullidos de horrores fugados llenan la prisión.""",

    553: """El Invernáculo: Un satélite del Castillo de la Tempestad, en Tormenta Abisal, donde científicos elfos de sangre leales a Kael'thas usan tecnología naaru robada para experimentar con las plantas y criaturas de Terrallende en busca de nuevos poderes. Jardines de flora extraña crecen bajo cúpulas de cristal, pero los experimentos se han descontrolado, y plantas mutadas y antárboles enfurecidos llenan ahora las salas. El aire es húmedo y espeso de polen.""",

    554: """El Mechanar: Un satélite del Castillo de la Tempestad, en Tormenta Abisal, convertido por Kael'thas en una fábrica que aprovecha la tecnología naaru para producir enormes cantidades de energía, almacenada en células de maná apiladas en muros y montones. Elfos de sangre bajo el mando de Pathaleon el Calculador manejan las máquinas, ayudados por demonios de la Legión Ardiente. Motores zumbantes, conductos arcanos y constructos traqueteantes llenan las salas de cristal violeta.""",

    555: """Laberinto de las Sombras: El ala más profunda de Auchindoun, en el Bosque de Terokkar, donde el Concilio de la Sombra invocó a un antiguo elemental del sonido cuyo ritual hizo estallar la necrópolis. El Concilio aún conspira aquí, luchando por contener y dominar la entidad que liberó, servido por orcos viles y demonios. Largas salas, cámaras rituales y un eco constante y ensordecedor llenan el laberinto, y el propio aire tiembla.""",

    556: """Salas Sethekk: Un ala de Auchindoun, en el Bosque de Terokkar, ocupada por los Sethekk, arakkoa renegados que rompieron con Skettis bajo el demente rey garra Ikiss. Creen que la destrucción de Auchindoun anunció el regreso de su amo y lo buscan entre las ruinas. Ídolos de plumas, fuegos rituales y magia oscura llenan las antiguas salas draenei, y los chillidos de los arakkoa resuenan en ellas.""",

    557: """Tumbas de Maná: Un ala de Auchindoun, en el Bosque de Terokkar, donde etéreos renegados liderados por el príncipe del Nexo Shaffar saquean las criptas y extraen energía arcana de las ruinas. Unas guardas mantienen alejados a sus rivales del Consorcio. Energía reluciente, escombros flotantes y los espíritus sin descanso de los muertos draenei llenan las tumbas, y las salas zumban de poder robado.""",

    558: """Criptas Auchenai: Un ala de Auchindoun, en el Bosque de Terokkar, las criptas funerarias de los draenei, donde los sacerdotes auchenai cuidaban de sus muertos honrados. Desde que la necrópolis quedó destrozada, las criptas han caído en la oscuridad: demonios de la Legión Ardiente cosechan almas aquí, y los muertos draenei se alzan como espíritus sin descanso y no-muertos. Piedra fría, luz sagrada apagada y los susurros de los muertos llenan las salas.""",

    560: """Antiguas Laderas de Trabalomas: Un viaje a través de las Cavernas del Tiempo a Trabalomas años antes de la Tercera Guerra, cuando el joven orco Thrall era esclavo de Aedelas Blackmoore en el Castillo de Durnholde y los orcos languidecían en campos de internamiento. El Vuelo Bronce custodia el momento de su huida, pues el Vuelo Infinito pretende cambiarlo. Colinas verdes, granjas apacibles, la ciudad de Costasur y las murallas de piedra de Durnholde aparecen tal como eran antaño.""",

    568: """Zul'Aman: La ciudad templo de los trols del bosque Amani al este de las Tierras Fantasma, último vestigio del imperio que se extendía por Lordaeron antes de que humanos y altos elfos lo quebraran juntos. El señor de la guerra Zul'jin, que nunca perdonó a los elfos, ha reunido a sus trols y, con ayuda del Señor de los Maleficios, ha sellado el poder de los dioses animales amani, el oso, el águila, el lince y el dracohalcón, en sus campeones más fuertes. Zigurats escalonados, tótems vudú y tambores llenan el bosque oscuro y primitivo.""",

    585: """Bancal del Magister: Un elegante complejo elfo de sangre en la esquina nordeste de la Isla de Quel'Danas, con un observatorio orientado hacia la Fuente del Sol. Lo ocupan seguidores de Kael'thas Caminante del Sol, quien se dice que se ha retirado aquí, y las salas zumban de poder arcano robado y de la energía de los cristales de maná. Agujas doradas, jardines y cúpulas de observatorio llenan el bancal, hermoso y peligroso.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan: La torre de marfil de Medivh, el último Guardián de Tirisfal, en el Paso de la Muerte, alzada sobre un nexo de líneas ley donde la realidad es delgada. Tras la muerte de Medivh, una terrible maldición cayó sobre la torre y las tierras circundantes. Ahora ha despertado: una presencia maligna se ha adueñado de ella, sus salas rebosan de espíritus y demonios, nobles espectrales de Villa Oscura reviven un banquete sin fin y ecos del pasado se representan en sus bibliotecas, su ópera y su casa de fieras. Esplendor polvoriento y magia fría llenan cada estancia.""",

    534: """La Cima Hyjal: Un viaje a través de las Cavernas del Tiempo a las laderas del Monte Hyjal al final de la Tercera Guerra, cuando humanos, orcos y elfos de la noche se alzaron juntos contra la Legión Ardiente y la Plaga. El señor demoníaco Archimonde asciende por la montaña para drenar el poder del Árbol del Mundo Nordrassil. El Vuelo Bronce preserva la batalla tal como fue, mientras los defensores se repliegan de campamento en campamento. Bosques antiguos, el gran árbol arriba y los ejércitos en llamas de la Legión abajo.""",

    544: """Guarida de Magtheridon: Una cámara en lo profundo de la Ciudadela del Fuego Infernal donde el señor del foso Magtheridon, antaño amo de Terrallende, yace encadenado desde que Illidan lo derrotó. Su sangre se recoge para engendrar la Horda Vil, y canalizadores del Fuego Infernal mantienen sus cadenas. La caverna tiembla con su ira, el techo se agrieta bajo su poder y el fuego vil parpadea alrededor de su jaula. Es un lugar de furia demoníaca en estado puro.""",

    548: """Caverna Santuario Serpiente: La guarida de lady Vashj, la hechicera naga al servicio de Illidan, en lo más profundo de la Reserva Colmillo Torcido, en la Marisma de Zangar, donde se acumulan las aguas bombeadas de la marisma. Sus lugartenientes más poderosos, desde un elemental de agua corrompido hasta un acechador de las profundidades, custodian el santuario, y las aguas rebosan de nagas. Vastas cavernas inundadas, pilares de coral y estanques relucientes brillan con una inquietante luz azul.""",

    550: """El Castillo de la Tempestad - El Ojo: El palacio interior del Castillo de la Tempestad, la fortaleza naaru de Tormenta Abisal, tomada por los elfos de sangre de Kael'thas Caminante del Sol, el Rey Sol, que gobierna aquí con sus fénix y sus consejeros más poderosos. Salas de cristal, maquinaria arcana y plataformas flotantes brillan con energía naaru robada, y un naaru cautivo es drenado de su poder. El Ojo domina las tormentas arremolinadas del Vacío, magnífico y frío.""",

    564: """El Templo Oscuro: Antaño el templo de Karabor, el lugar más sagrado de los draenei y refugio del profeta Velen, conquistado por Gul'dan como cuartel general del Concilio de la Sombra y ocupado después por la Legión Ardiente. Hoy es la ciudadela de Illidan Tempestira, autoproclamado señor de Terrallende, custodiada por sus Illidari: nagas, elfos de sangre, tábidos, demonios y orcos viles. El fuego vil arde en sus santuarios, la sombra llena sus salas y desde sus profundidades llegan los gritos de almas atormentadas.""",

    565: """Guarida de Gruul: Una guarida cavernosa al norte de las Montañas Filoespada, hogar de Gruul el Asesino de Dragones, despiadado señor de los gronn, y de su hijo, el alto rey ogro Maulgar, que gobiernan a los ogros de las montañas. Los huesos de dragones muertos cuelgan de las paredes, y el suelo tiembla bajo los pasos de los gigantes. Toscos estandartes ogros, trofeos y roca desnuda llenan la enorme cueva, un lugar de fuerza bruta y violencia.""",

    580: """Meseta de La Fuente del Sol: El lugar más sagrado de los elfos en la Isla de Quel'Danas, donde la Fuente del Sol, el manantial de poder que sustentó Quel'Thalas, se alza en el corazón de patios y salas elegantes. Recientemente, la Legión Ardiente ha querido usarla como portal para el señor eredar Kil'jaeden, y los siervos de la Legión, demonios y elfos de sangre leales a ellos, ocupan la meseta. Agujas doradas, naaru cautivos y energía vil rodean la fuente profanada.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Fortaleza de Utgarde: La gran fortaleza vrykul sobre los acantilados del lago Cauldros, en el Fiordo Aquilonal, construida en el propio fiordo con cascadas que caen a ambos lados, hogar del clan Desuelladragones. Largo tiempo silenciosa, ha despertado, y sus guerreros asaltan todos los asentamientos cercanos, al servicio, según se dice, del Rey Exánime, que alza a los más dignos de ellos de la tumba. Protodracos, huargos y no-muertos sirven a los vrykul, y cuanto más se sube por la fortaleza, más poderosos son sus moradores.""",

    575: """Pináculo de Utgarde: Los niveles más altos de la Fortaleza de Utgarde, en el Fiordo Aquilonal, donde viven los vrykul más poderosos y el rey Ymiron tiene su trono, ansioso por demostrar que su pueblo merece el favor del Rey Exánime. Grandes salas de piedra y madera, cráneos tallados y los trofeos de enemigos caídos llenan el pináculo, y protodracos vuelan en círculos sobre las frías alturas del fiordo.""",

    576: """El Nexo: El antiguo hogar del Vuelo Azul bajo la isla de Gelidar, frente a la Tundra Boreal, una fortaleza arcana de hielo y cristales flotantes donde el Aspecto de la Magia, Malygos, libra su guerra contra todos los lanzadores de hechizos mortales. Los dragones azules y sus sirvientes custodian sus salas heladas, y los enemigos capturados permanecen en prisiones de hielo. La energía arcana chisporrotea en el aire, y el hielo brilla de magia.""",

    578: """El Oculus: La gran torre de anillos flotantes sobre el Nexo, en Gelidar, donde Malygos canaliza las líneas ley de Azeroth y desvía la magia del mundo a través del Nexo hacia el Vacío Abisal. El Kirin Tor y el Vuelo Rojo luchan por detenerlo. Los anillos flotan muy alto en el cielo, chisporroteando de poder arcano, y solo los dracos llevan de uno a otro. La magia pura desgarra el aire, y grietas lejanas rasgan la realidad.""",

    595: """La Matanza de Stratholme: Un viaje a través de las Cavernas del Tiempo al día en que la peste llegó a Stratholme en grano contaminado y el príncipe Arthas, negándose a dejar que sus habitantes se alzaran como no-muertos, ordenó purgar la ciudad. El señor del terror Mal'Ganis vigila la ciudad moribunda, y el Vuelo Infinito pretende alterar ese momento. Las calles están llenas de ciudadanos aterrados, casas en llamas y los primeros muertos que caminan, un día que marcó el comienzo de la caída de Arthas.""",

    599: """Cámaras de Piedra: Un ala de la ciudad titánica de Ulduar, en las Cumbres Tormentosas, hogar del Tribunal de los Tiempos, el inmenso archivo de piedra de la historia de los titanes, y de la Forja de Voluntades. Enanos férreos y gigantes de piedra, corrompidos por el guardián caído Loken, ocupan ahora sus salas y custodian sus secretos. Estatuas imponentes, relieves tallados y maquinaria titánica llenan las vastas salas de piedra, silenciosas salvo por el rumor de las máquinas.""",

    600: """Fortaleza de Drak'Tharon: Una vieja fortaleza de los trols de hielo, de agujas y muros tallados, en la frontera entre las Colinas Pardas y Zul'Drak, tomada por la Plaga, que alza a los Drakkari caídos para luchar contra su propio imperio. Su antiguo líder, el profeta Tharon'ja, ha sido transformado en una monstruosa forma no-muerta, y trols no-muertos salen en tropel de sus puertas hacia las colinas. Huesos, estandartes de la Plaga y tallas trols heladas llenan la fortaleza.""",

    601: """Azjol-Nerub: El Reino Superior de los nerubianos bajo el Cementerio de Dragones, un grandioso reino subterráneo de saber y arte arrasado por la Plaga en la Guerra de la Araña. Nerubianos no-muertos patrullan ahora sus salas pulidas, custodiando nidadas de las que nacerán nuevos guerreros de la Plaga, y su rey caído Anub'arak sirve al Rey Exánime. Telarañas, murales tallados y hongos luminosos llenan las vastas cavernas, mientras los nerubianos vivos libran una guerra oculta y perdida.""",

    602: """Cámaras de Relámpagos: El ala este de la ciudad titánica de Ulduar, en las Cumbres Tormentosas, donde el guardián caído Loken se sienta en su trono y fabrica en masa vrykul férreos y constructos para sus oscuros fines. Elementales de tormenta, gigantes férreos y guardianes forjados por el rayo le sirven, y grandes forjas y máquinas retumban por doquier. Los relámpagos chisporrotean por las vastas salas de piedra y metal.""",

    604: """Gundrak: La capital de los trols de hielo Drakkari en Zul'Drak, una enorme ciudad de muros gruesos, altas torres y edificios escalonados entrelazados como un nido. Desesperados ante la Plaga, sus sumos profetas han matado a sus propios dioses, los loas, y beben su sangre para obtener poder, impregnando los santuarios sagrados del poder de dioses muertos. Ídolos de rinoceronte, serpiente y mamut se alzan en los patios, y los tambores resuenan por las calles escalonadas.""",

    608: """El Bastión Violeta: La prisión del Kirin Tor en Dalaran, cuyas celdas protegidas por magia retienen a prisioneros poderosos y peligrosos. El Vuelo Azul de Malygos ha irrumpido por una gran grieta en el techo y se vierte por portales en su interior, poniendo a prueba las defensas de la prisión y liberando a sus reclusos. Las guardas arcanas parpadean, la piedra violeta brilla y los guardias del Kirin Tor luchan por mantener la línea.""",

    619: """Ahn'kahet: El Reino Antiguo, las profundidades más remotas de Azjol-Nerub bajo el Cementerio de Dragones, una enorme ciudad subterránea del antiguo imperio nerubiano. Nerubianos de la Plaga y los misteriosos Sin Rostro la ocupan, estos últimos al servicio, según se dice, de un poder maligno que acecha bajo Rasganorte, y el Martillo Crepuscular se agita entre ellos. Bosques de hongos, grandes cámaras cubiertas de telarañas y una oscuridad opresiva llenan las profundidades.""",

    632: """La Forja de Almas: La primera de las Cámaras Heladas de la Ciudadela de la Corona de Hielo, una enorme fábrica donde se construyen trituradoras de almas, las más recientes y viles creaciones del Rey Exánime. Almas atormentadas quedan atadas a las máquinas entre pilares de saronita y cadenas espectrales. El aire está cargado de desesperación y de los gemidos de los muertos.""",

    650: """Prueba del Campeón: El campo de torneo de la Cruzada Argenta bajo el Coliseo Argenta, en Corona de Hielo, donde campeones de la Alianza y de la Horda justan y se baten en duelo para demostrar su valía en la guerra contra el Rey Exánime. Monturas, lanzas, estandartes y el rugido de la multitud llenan la arena, festiva y orgullosa, aunque la Plaga nunca está lejos.""",

    658: """Foso de Saron: La gran mina de saronita bajo la Ciudadela de la Corona de Hielo, donde la Plaga obliga a prisioneros de la Alianza y de la Horda a extraer el mineral de sus fortalezas bajo el látigo del señor de la Plaga Tyrannus. Vetas de saronita palpitan en las paredes, los esclavos trabajan encadenados y los muertos son alzados para seguir trabajando. El frío, la oscuridad y los chasquidos de los látigos llenan el foso.""",

    668: """Cámaras de Reflexión: Los aposentos privados del Rey Exánime en la Ciudadela de la Corona de Hielo, el único lugar donde baja la guardia, una réplica oscura y retorcida de la sala del trono de Lordaeron. Agonía de Escarcha, la espada rúnica del Rey Exánime, aguarda aquí, y los espíritus atrapados en ella rondan las salas. Hielo, silencio y recuerdos del pasado llenan los aposentos.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas: Una necrópolis de la Plaga que flota sobre el Cementerio de Dragones, antaño un zigurat nerubiano arrasado por la Plaga y alzado al cielo por la magia oscura del Rey Exánime. Es la sede del archiliche Kel'Thuzad, que la ha traído de vuelta a Rasganorte para asediar Hibergarde. Sus cuatro barrios albergan horrores de todo tipo: señores de las criptas arácnidos, laboratorios de peste y abominaciones, legiones de caballeros de la Muerte y creaciones de carne cosida. Limo verde, carne putrefacta y el frío de la tumba llenan sus salas.""",

    603: """Ulduar: El mayor complejo de los titanes en Azeroth, perfectamente conservado en las nieves de las Cumbres Tormentosas, oculto tras la roca y el hielo, un laberinto de túneles, escaleras y balcones excavado en una enorme caverna. Fue el hogar de los guardianes de los titanes y de sus máquinas de creación, pero se susurra que un gran mal se esconde tras su caída, y sus guardianes corrompidos se vuelven contra todo intruso. Estatuas colosales, maquinaria titánica y observatorios llenos de estrellas llenan sus salas.""",

    615: """El Sagrario Obsidiana: La cámara del Vuelo Negro bajo el Templo del Reposo del Dragón, en el Cementerio de Dragones, parte de la Cámara de los Aspectos, donde Sartharion el Guardián Ónice custodia una nidada de huevos de dragón crepuscular. Tres dracos crepusculares vigilan sus propias islas entre ríos de lava y plataformas de obsidiana. La cámara resplandece de naranja y rojo, y el calor hace temblar el aire.""",

    616: """El Ojo de la Eternidad: El dominio personal del Aspecto azul Malygos, muy por encima del Nexo en Gelidar, desde el que libra su guerra para recuperar el dominio sobre las energías arcanas de Azeroth. Es una inmensa plataforma flotante en un vacío infinito de energía arcana arremolinada y estrellas, donde fluye la magia del mundo. Un poder puro llena el aire.""",

    624: """La Cámara de Archavon: Una cámara de los titanes bajo la Fortaleza de Conquista del Invierno, que guarda reliquias de un poder inimaginable bajo la vigilancia de antiguos guardianes de piedra que detestan a todo intruso. Sus salas solo se abren a quienes ocupan la fortaleza de arriba. Piedra tallada, maquinaria titánica y un silencio inquietante llenan la cámara.""",

    631: """Ciudadela de la Corona de Hielo: La fortaleza del Rey Exánime, que se alza del hielo negro de Corona de Hielo, una catedral de hojas y agujas de saronita alrededor del Trono Helado. Sus salas rebosan de los sirvientes más leales y viles de la Plaga: caballeros de la Muerte, sectarios, abominaciones y vermis de escarcha. La Aguja Inferior, los Talleres de la Peste, el Salón Carmesí y las Cámaras de Alaescarcha llevan al trono. El Veredicto Cinéreo dirige el asalto, y el frío cala hasta los huesos.""",

    649: """Prueba del Cruzado: El gran Coliseo Argenta en Corona de Hielo, construido por la Cruzada Argenta para poner a prueba a los campeones dignos del asalto final contra el Rey Exánime. Los estandartes de la Alianza y de la Horda ondean sobre gradas jubilosas, y temibles bestias y campeones son llevados a la arena bajo la mirada del alto señor Tirion Vadín. Pompa y espectáculo se despliegan a las mismas puertas del Rey Exánime, y la vieja rivalidad de las dos facciones arde en las gradas.""",

    724: """El Sagrario Rubí: El santuario del Vuelo Rojo bajo el Templo del Reposo del Dragón, en el Cementerio de Dragones, parte de la Cámara de los Aspectos, un refugio apacible de huevos de dragón rojo, luz cálida y verdor. Sus guardianes han enmudecido y los guardias del portal han sido asesinados; una fuerza oscura ha irrumpido en el sagrario, y dragones crepusculares amenazan ahora los huevos del Vuelo Rojo.""",

    # -------------------------------------------------------------------------
    # Arenas
    # -------------------------------------------------------------------------
    559: """Arena de Nagrand: El Anillo de las Pruebas, en las praderas de Nagrand, un antiguo lugar de pruebas de los orcos construido al estilo del viejo imperio ogro. Gladiadores de todas las razas se reúnen aquí para luchar por la gloria. Un círculo de pilares de piedra erosionados se alza a cielo abierto, el viento barre la hierba y los espectadores miran desde las colinas.""",

    562: """Arena Filoespada: El Círculo de Sangre, en las Montañas Filoespada, una arena construida por ogros donde los gladiadores luchan por la gloria ante una multitud rugiente. Un puente de madera cruza un foso en su centro, cuerdas y pilares atraviesan el anillo y a su alrededor se alzan picos dentados. Madera tosca, huesos y estandartes le dan un aire brutal y salvaje.""",

    572: """Ruinas de Lordaeron: Una arena entre las ruinas destrozadas de la capital de Lordaeron, en los Claros de Tirisfal, sobre Entrañas, donde el gran palacio aún se alza como triste recuerdo de la caída de la ciudad. Muros rotos, estatuas derribadas y una tumba en ruinas rodean el lugar de combate, y el recuerdo del trágico final del reino flota sobre las piedras.""",

    617: """Cloacas de Dalaran: Una arena oculta en las Cloacas, los desagües bajo la ciudad flotante de Dalaran, donde los gladiadores combaten en un foso rodeado de canales y tuberías. Piedra húmeda, el correr del agua y el murmullo de una multitud ruda llenan la arena, lejos del esplendor de la ciudad violeta de arriba.""",

    618: """El Anillo del Valor: La gran arena del Valle del Honor en Orgrimmar, donde entrenan y combaten los gladiadores del Anillo Carmesí. Columnas se alzan desde el suelo, los espectadores rugen en las gradas y el calor de Durotar cae sobre la arena. Es un lugar de honor, fuerza y espectáculo.""",
}
