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
    # Eastern Kingdoms - Alliance Starting Zones
    # -------------------------------------------------------------------------
    1: """Dun Morogh: Tierras altas nevadas de los enanos que rodean Forjaz. Los troggs
han invadido desde las profundidades, y trols de hielo hostiles acechan en las
montañas. El Valle Cresta Fría es donde jóvenes enanos y gnomos comienzan su
viaje. El aire es fresco, la cerveza es fuerte, y las montañas resuenan con
disparos y martillazos.""",

    12: """Bosque de Elwynn: Tierras de labranza humanas y pacíficas a las afueras de
Ciudad de Ventormenta, pero los problemas se gestan bajo la superficie. Los
kobolds infestan las minas gritando "tú no tocar vela", la Hermandad Defias
amenaza los caminos, y los gnolls asaltan desde las fronteras. La posada de
Loma de Oro siempre está animada. Una zona engañosamente tranquila donde
acecha el peligro.""",

    38: """Loch Modan: Una región montañosa dominada por un enorme lago. Los troggs y
kobolds plagan la zona, mientras los enanos Hierro Negro causan problemas cerca
de la presa. La gran presa es una maravilla de la ingeniería. Thelsamar es un
pueblo tranquilo de cazadores y excavadores. El paisaje se siente agreste y
fronterizo.""",

    40: """Páramos de Poniente: Antaño fértiles tierras de labranza, ahora polvorientas
y abandonadas. La Hermandad Defias controla gran parte de la región desde su
base oculta. Granjeros sin hogar vagan por los caminos, vigías mecánicos de
la cosecha patrullan campos vacíos, y gnolls merodean por los límites. Colina
Centinela sigue siendo el último bastión del orden.""",

    44: """Montañas Crestagrana: Un territorio humano asediado. Los orcos de Roca Negra
descienden de las montañas, los gnolls campan a sus anchas, y el pueblo de
Lagoto resiste desesperadamente. El puente está siempre bajo amenaza. Una
zona que se siente como un frente de guerra, con ciudadanos atrapados en
el fuego cruzado.""",

    10: """Bosque del Ocaso: Un bosque perpetuamente oscuro y maldito, envuelto en
noche eterna. Los no-muertos deambulan entre los árboles, los worgen aúllan
en la oscuridad, y arañas gigantes acechan por doquier. La Guardia Nocturna
de Los Sombríos apenas contiene los horrores. Una zona inquietante donde algo
terrible ocurrió y la tierra nunca se recuperó.""",

    11: """Los Humedales: Marismas empapadas que conectan las tierras enanas con
Lordaeron. Crocolisks y raptores hostiles por todas partes, los enanos Hierro
Negro conspiran en las colinas, y dragontes amenazan desde el noreste. El
Puerto de Menethil es una ciudad portuaria empapada de lluvia. Todo aquí está
húmedo y algo desdichado.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Horde Starting Zones
    # -------------------------------------------------------------------------
    85: """Claros de Trisfal: Bosque encantado que rodea Entrañas. La propia tierra se
siente enferma - árboles enfermizos, niebla verde, y no-muertos inquietos.
Los fanáticos de la Cruzada Escarlata cazan cualquier cosa no-muerta,
mientras zombis sin mente y murciélagos deambulan libremente. Brill es un
pueblo sombrío de los Renegados. La atmósfera es gótica y melancólica.""",

    130: """Bosque de Argénteos: Bosques oscuros y brumosos al sur de Trisfal. Los
worgen han invadido gran parte del bosque, y persiste la presencia del
Flagelo. La Fortaleza de Colmillo Sombrío se alza amenazante. Los Renegados
luchan por cada palmo de territorio. Una zona atrapada entre múltiples
amenazas, que se siente aislada y peligrosa.""",

    267: """Laderas de Trabalomas: Tierras de labranza disputadas donde la Horda y
la Alianza chocan abiertamente. Bahía del Sur y Molino Tarren están en
constante conflicto. Los yetis rondan las montañas, y los bandidos del
Sindicato causan problemas. Una zona definida por la guerra de facciones y
viejos rencores.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Mid-Level Zones
    # -------------------------------------------------------------------------
    47: """Tierras del Interior: Remotas tierras altas boscosas, hogar de los enanos
Martillo Salvaje y los trols del bosque, atrapados en un conflicto eterno.
Lobos y bestias búho rondan la espesura. Cima del Águila se asienta sobre
un acantilado imponente. La zona se siente indómita y alejada de la
civilización.""",

    45: """Tierras Altas de Arathi: Praderas onduladas salpicadas de ruinas
antiguas. El Sindicato controla las ruinas de Stromgarde, ogros habitan
las cuevas, y raptores cazan en las llanuras. Punto de Refugio y Marfil
se vigilan mutuamente con recelo. Una zona fronteriza azotada por el
viento con ecos de reinos caídos.""",

    33: """Vega de Tuercespina: Selva densa y peligrosa rebosante de vida. Trols,
piratas, raptores, tigres y gorilas por todas partes. Bahía del Botín es
un puerto goblin sin ley donde todo vale. La expedición de caza de
Nesingwary atrae a aventureros. La zona es hermosa pero mortal - algo
quiere devorarte en cada esquina.""",

    3: """Tierras Inhóspitas: Desierto árido y hostil de roca roja y polvo. Troggs
hostiles, coyotes y crías de dragón negro hacen peligroso el viaje.
Sitios arqueológicos dispersos insinúan secretos antiguos. Kargath es un
tosco puesto avanzado de la Horda. Una zona que se siente desolada e
implacable.""",

    8: """Pantano de las Penas: Turbio y deprimente pantano. Los perdidos deambulan
sin rumbo, jaguares acechan en las aguas, y el Templo de Atal'Hakkar
atrae a oscuros adoradores. Todo está mojado, embarrado y algo
desesperanzado. Un rincón olvidado del mundo.""",

    4: """Las Tierras Devastadas: Tierra baldía marcada por cicatrices, corrompida
por las energías del Portal Oscuro. Demonios, fauna mutada y criaturas
corrompidas por el vil deambulan libremente. El propio suelo se siente
mal. La Fortaleza Guardia Norte vigila el Portal con nerviosismo. Una
zona que se siente como el borde del mundo, donde todo salió mal.""",

    51: """La Garganta de Fuego: Tierra baldía volcánica controlada por los enanos
Hierro Negro. Ríos de lava, elementales de fuego y fosas de escoria
dominan el paisaje. Puesto Torio es un pequeño enclave de resistencia.
Brutalmente caluroso y devastado por la industria.""",

    46: """Las Estepas Ardientes: Orcos de Roca Negra y dragones negros gobiernan
esta tierra calcinada. La Cima de Roca Negra se alza sobre el paisaje.
Elementales de fuego y dragontes patrullan. Una zona de guerra de alto
nivel donde la Horda Oscura reúne sus fuerzas.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands
    # -------------------------------------------------------------------------
    28: """Tierras de la Peste del Oeste: Tierras de labranza enfermas plagadas de
no-muertos. Andorhal es una ciudad en ruinas disputada por múltiples
facciones. La presencia del Flagelo es intensa, y los Calderos esparcen
la peste por la tierra. La Cruzada Escarlata lucha con fanatismo. Una
zona de muerte, enfermedad y luchas desesperadas.""",

    139: """Tierras de la Peste del Este: El corazón del Flagelo. No-muertos por
todas partes - carroñeros, abominaciones, nigromantes. Stratholme arde
eternamente, Naxxramas flota en lo alto. La Capilla de la Esperanza de
la Luz es el último bastión de la humanidad. La zona más corrompida y
peligrosa del continente. Aquí la esperanza escasea.""",

    41: """Paso de la Muerte: Cañón desolado que conduce a Karazhan. Ogros de
Paso de la Muerte acechan en las cuevas, espíritus inquietos deambulan,
y la corrupción demoníaca se filtra desde la torre. La propia tierra se
siente drenada de vida. Espeluznante, vacía y ominosa - algo terrible
ocurrió aquí.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Alliance Starting Zones
    # -------------------------------------------------------------------------
    141: """Teldrassil: Un inmenso árbol del mundo, hogar de los elfos de la
noche. A pesar de algunos problemas con furbolgs Zarpa Retorcida y
elementales de madera hostiles, el bosque sigue siendo de una belleza
sobrecogedora - árboles antiguos que brillan suavemente al atardecer,
claros sagrados que resplandecen con magia persistente, y quietos
claros que invitan a la reflexión. Darnassus se asienta serenamente
sobre el dosel. El aire lleva susurros de magia antigua. Los elfos de
la noche siguen con su vida diaria: entrenan, elaboran, cuidan jardines.
Un lugar donde la belleza de la naturaleza persiste incluso mientras
los aventureros lidian con amenazas.""",

    148: """Costa Oscura: Una costa larga y brumosa donde la niebla llega desde el
mar, creando una atmósfera etérea. Ruinas antiguas de los elfos de la
noche guardan misterios y sabiduría olvidada. Auberdine bulle de
viajeros que toman barcos hacia Teldrassil, Ciudad de Ventormenta o
Isla Bruma Azur. Los pescadores trabajan en los muelles, los
aventureros comparten historias en la posada. Sí, los murlocs y los
naga causan problemas en las playas, y algo de la vida salvaje se ha
vuelto agresiva - pero la inquietante belleza del litoral perdura.
Costas iluminadas por la luna, arquitectura antigua, el sonido de las
olas. Una zona de contrastes: puertos apacibles y tierras salvajes
peligrosas, magia antigua y nuevas amenazas.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Horde Starting Zones
    # -------------------------------------------------------------------------
    14: """Durotar: Desierto rocoso y hostil, hogar de los orcos. Escórpidos,
raptores y jabalíes rondan los cañones rojos. Los quilboar asaltan desde
el sur, y cultistas de la Hoja Ardiente se ocultan en cuevas. Las
puertas de Orgrimmar dan la bienvenida a los guerreros. Una zona que
encarna la fuerza de la Horda frente a la adversidad.""",

    215: """Mulgore: Llanuras onduladas y pacíficas de los tauren. Los kodo pastan
plácidamente, pero las arpías descienden en picado desde las montañas
y los goblins de la Compañía Venture explotan la tierra. Cima del
Trueno se alza sobre sus mesetas. La zona de la Horda más serena -
cielos amplios y vientos suaves, aunque el peligro acecha en los
bordes.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Mid-Level Zones
    # -------------------------------------------------------------------------
    17: """Los Baldíos: Vasta y árida sabana que se extiende sin fin. Centauros,
quilboar, raptores, leones y zhevras por todas partes. La Encrucijada
es un importante centro donde se reúnen los aventureros. Conocida por
sus largos tiempos de viaje y su memorable chat general. Una
experiencia definitoria del ascenso de nivel de la Horda.""",

    331: """Vallefresno: Antiguo bosque de elfos de la noche bajo asedio. La
Horda avanza desde el este, demonios acechan en las sombras, y los
furbolgs han enloquecido. Astranaar y el puesto avanzado de
Bosquespina representan el conflicto entre facciones. Un bosque
hermoso empañado por la guerra y la corrupción.""",

    405: """Desolace: Tierra baldía árida y gris. Las tribus centauro guerrean
sin cesar entre sí y contra todos los demás. Cementerios de kodo
salpican el paisaje. La zona se siente vacía y desesperanzada -
incluso el cielo parece drenado de color. Uno de los lugares más
deprimentes de Azeroth.""",

    400: """Las Mil Agujas: Cañón dramático de agujas de piedra imponentes. Antes
del Cataclismo, un lecho desértico y seco con la pista de carreras de
los Bajíos Relucientes. Centauros y arpías controlan varios pilares.
El Gran Ascensor conecta con Los Baldíos. Visualmente impresionante
pero duro para viajar.""",

    15: """Marjal Revolcafango: Pantano cálido y húmedo. Dragones negros conspiran
en el sur, crocolisks y arañas hostiles acechan en el fango, y
Theramore se alza como fortaleza de la Alianza. Las ruinas de una
posada incendiada insinúan complots más oscuros. Opresivamente
bochornoso y peligroso.""",

    357: """Feralas: Selva y bosque exuberantes y desbordantes. Yetis en las
montañas, naga en la costa, ogros y gnolls por doquier. Los Colosales
Gemelos son árboles inmensos, y las ruinas de Dire Maul se alzan
imponentes. Una zona salvaje e indómita que engulle a los viajeros.""",

    440: """Tanaris: Desierto abrasador que rodea el puerto goblin de Gadgetzan.
Piratas, bandidos, basiliscos e insectos silítidos por todas partes.
Los trols de Zul'Farrak son hostiles. Las Cavernas del Tiempo se
esconden cerca. Ardiente durante el día, el desierto es implacable
pero rentable.""",

    16: """Azshara: Costa arruinada de los elfos de la noche, de una belleza
inquietante pero vacía. Los naga controlan gran parte de la orilla, y
la Bandada de Dragones Azules mantiene una presencia. Criaturas
marinas gigantes rondan, y restos de la Legión persisten en Cresta
Perdida. La zona se siente abandonada y triste - un monumento a lo
que se perdió.""",

    361: """Frondavil: Bosque corrompido que rezuma con la mancha demoníaca.
Limos, sátiros y fauna corrompida plagan cada rincón. Los propios
árboles parecen enfermos. Los furbolgs Fauces de Madera son
cautelosos pero neutrales; los furbolgs Bosque Muerto son hostiles.
Una zona que te hace sentir sucio con solo atravesarla.""",

    490: """Cráter de Un'Goro: Cráter selvático prehistórico rebosante de
dinosaurios. Los devilsaurios son depredadores dominantes, los
raptores cazan en manadas, y elementales custodian pilones. Es como
retroceder en el tiempo - exuberante, peligroso y lleno de maravillas.
Formaciones de cristal albergan un poder misterioso.""",

    493: """Claro de la Luna: Santuario sagrado de los druidas. Mayormente
pacífico y seguro, con pocas criaturas hostiles. El Círculo Cenarion
se reúne aquí, y la zona se siente atemporal y serena - un respiro
del caos del mundo. Los druidas se reúnen en Refugio Nocturno.""",

    618: """Cuna del Invierno: Tierras altas heladas de invierno eterno. Gatos
Zarpa de Escarcha, yetis y gigantes de hielo rondan la nieve.
Vistalejos es un pueblo goblin de tratos cuestionables. Los furbolgs
Otoño de Invierno son hostiles en toda la zona. Hermosa pero
mortalmente fría, la zona solo recompensa a quien está bien preparado.""",

    1377: """Silithus: Tierra baldía desértica plagada de insectos silítidos. La
amenaza qiraji se cierne desde Ahn'Qiraj. Los druidas del Círculo
Cenarion luchan desesperadamente contra la colmena. Tormentas de
arena, insectos gigantes, y una sensación abrumadora de que algo
antiguo y maligno se agita bajo las arenas.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Península del Fuego Infernal: Tierra baldía roja y destrozada,
primera zona tras el Portal Oscuro. Orcos del vil, demonios y fuerzas
de la Legión Ardiente por todas partes. Fortaleza Honor y Thrallmar
son las bases de las facciones. El cielo está desgarrado, el suelo
está agrietado, y la guerra ruge constantemente. Una introducción
brutal a Outland.""",

    3521: """Marisma de Zangar: Surrealista pantano de setas que brilla con
bioluminiscencia. Hongos gigantes se alzan en lo alto, esporomurciélagos
flotan perezosamente, y los naga drenan las aguas. El Refugio Cenarion
trabaja para salvar el ecosistema. Extrañamente hermoso y alienígena -
nada aquí se parece a Azeroth.""",

    3519: """Bosque de Terokkar: Dividido entre el bosque exuberante y las
tierras baldías sembradas de huesos alrededor de Auchindoun. Arakkoa
acechan entre los árboles, y el Consejo de las Sombras conduce rituales
oscuros. Ciudad de Shattrath es la capital neutral. Una zona de
contrastes entre la vida y la muerte.""",

    3522: """Montañas Filoespada: Paisaje escarpado y hostil de picos imponentes.
Los ogros gobiernan aquí, y los gigantes gronn son los depredadores
dominantes. La Legión Ardiente mantiene puestos avanzados, y dragones
sobrevuelan en círculos. Terreno peligroso donde la propia tierra
parece querer matarte.""",

    3520: """Valle Sombraluna: Tierra baldía oscura, corrompida por el vil. El
Templo Negro se alza amenazante, y las fuerzas de Illidan controlan
la región. Demonios, orcos del vil y caballeros de la muerte patrullan.
El cielo arde en verde. La zona más peligrosa y opresiva de Outland -
aquí la esperanza se siente distante.""",

    3523: """Tormenta Abisal: Islas destrozadas flotando en el Vacío Retorcido.
Forjas de maná cosechan la energía de la tierra, elfos de sangre y
etéreos compiten por recursos, y criaturas de maná deambulan
salvajemente. Las eco-cúpulas preservan la vida artificialmente. Una
zona que se desgarra a sí misma en las costuras.""",

    3524: """Isla Bruma Azur: Tranquila isla draenei bañada por una suave luz
azulada y el zumbido de la tecnología de cristal. El lugar del
accidente de El Exodar aún brilla con energía residual, y los
supervivientes draenei atienden sus heridas y reconstruyen. Fauna
apacible, estanques resplandecientes y ruinas cristalinas comparten
espacio con los esperanzadores inicios de un pueblo desplazado que
encuentra su lugar en un nuevo mundo.""",

    3525: """Isla Bruma de Sangre: Isla hermana de Bruma Azur, teñida de carmesí
por cristales corrompidos de los restos de El Exodar. La energía del
vil ha convertido a la fauna local en depredadores peligrosos y
mutado la vegetación. Elfos de sangre y demonios trabajan para
corromper aún más la tierra. Un lugar de belleza vuelto siniestro,
donde los draenei deben afrontar el daño causado por el accidente de
su propia nave.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Tundra Boreal: Tundra costera helada, uno de los dos puntos de
entrada a Rasganorte. Los nerubianos se ocultan bajo tierra, el
Flagelo pone a prueba las defensas, y los tuskarr pescan en las
orillas. Baluarte Grito de Guerra y Fortaleza Vigilancia son los
bastiones de las facciones. El frío muerde con fuerza - el invierno
apenas comienza.""",

    495: """Fiordo Aquilonal: Costa dramática de inspiración vikinga con
acantilados imponentes. Guerreros vrykul asaltan desde sus aldeas, y
el Flagelo corrompe a los muertos. Valgarde y Aterrizaje Venganza son
los puntos de desembarco. Los fiordos son sobrecogedores pero los
vrykul son implacables.""",

    394: """Colinas Pardas: Frontera boscosa que se siente casi pacífica.
Furbolgs corrompidos por el Flagelo, enanos de hierro excavan en
busca de secretos, y la maldición worgen se propaga. Operaciones de
tala cicatrizan las laderas. Una zona que sería hermosa de no ser
por la corrupción que se extiende.""",

    3711: """Cuenca de Sholazar: Exuberante cráter selvático intacto por el
Flagelo, mantenido por la tecnología de los titanes. Dinosaurios,
gorilas y bestias exóticas prosperan. Los Corazón Salvaje y los
Oráculos libran una guerra mezquina. Un paraíso inesperado en el
gélido Rasganorte - pero algo amenaza los pilones.""",

    66: """Zul'Drak: Reino trol congelado en colapso. Los Drakkari sacrifican
a sus propios dioses para luchar contra el Flagelo. No-muertos y
trols desesperados chocan por doquier. La zona se siente como
presenciar la muerte de una civilización - sombría, fría y sin
esperanza.""",

    67: """Cumbres Tormentosas: Montañas heladas e imponentes, hogar de secretos
de los titanes. Gigantes de tormenta, enanos de hierro y proto-dracos
dominan. La entrada a Ulduar se alza en lo alto. Los Hijos de Hodir
recelan de los forasteros. Escala épica, condiciones brutales,
misterios ancestrales.""",

    210: """Corona de Hielo: El dominio del Rey Exánime. Interminables
ejércitos no-muertos, fortalezas necrópolis, y la propia Ciudadela
de Corona de Hielo. La Cruzada Argenta hace su última resistencia.
El propio aire se siente muerto. Este es el final del camino -
victoria u olvido.""",

    # -------------------------------------------------------------------------
    # Capital Cities
    # -------------------------------------------------------------------------
    1519: """Ciudad de Ventormenta: La gran capital humana, reconstruida tras la Primera Guerra. La
gran catedral domina el horizonte, los canales serpentean entre distritos de piedra, y
el bullicioso Distrito Comercial nunca duerme. Los guardias patrullan por doquier. El
puerto conecta con tierras lejanas. El rey Varian Wrynn gobierna desde Ventormenta. Una
ciudad de adoquines, estandartes y orgullo cívico — el corazón de la Alianza.""",

    1537: """Forjaz: La gran ciudad enana tallada en el corazón de una montaña. Una enorme forja de
metal fundido domina el centro, rodeada por el distrito de la Gran Forja donde los
maestros herreros martillean día y noche. El aire es cálido y huele a hierro y cerveza.
Túneles se ramifican hacia el Distrito Militar, el Distrito Místico y el Tranvía de las
Profundidades hacia Ciudad de Ventormenta. Sólida, ancestral y construida para durar
para siempre.""",

    1657: """Darnassus: La serena capital de los elfos de la noche en la cima del árbol del mundo
Teldrassil. Árboles ancestrales se arquean en lo alto, una suave luz púrpura se filtra
por el dosel, y aguas quietas reflejan las estrellas incluso al mediodía. El Templo de
la Luna honra a Elune. Los druidas meditan en el Enclave Cenarion. La ciudad se siente
atemporal y pacífica, alejada de las guerras de abajo — aunque esa paz es más frágil de
lo que parece.""",

    3557: """El Exodar: La nave dimensional estrellada de los draenei, ahora reutilizada como su
capital. Pilones de cristal zumban con energía de otro mundo, luz púrpura y azul baña
corredores geométricos, y un santuario radiante brilla en su corazón. La arquitectura es
alienígena y hermosa — mitad catedral, mitad nave estelar. Los draenei siguen con sus
vidas con tranquila dignidad, reconstruyendo tras otro largo viaje.""",

    1637: """Orgrimmar: La brutal capital orca tallada en cañones de desierto rojo. Púas de hierro,
estandartes de guerra y puertas colosales definen el horizonte. El Valle del Poder
resuena con los gruñidos de guerreros en entrenamiento y el estruendo de la casa de
subastas. El legado de Thrall flota en el aire. La ciudad es cruda, ruidosa y
descaradamente agresiva — una ciudad fortaleza construida para un pueblo que espera la
guerra.""",

    1638: """Cima del Trueno: La capital tauren construida sobre mesetas imponentes conectadas por
puentes de cuerda muy por encima de las llanuras de Mulgore. El viento barre las
plataformas al aire libre. Tótems y pieles decoran cada estructura. La Cornisa de los
Ancianos alberga a los druidas, la Cornisa del Espíritu a los sacerdotes. Cairne Pezuña
de Sangre lidera con sabiduría ancestral. La capital de la Horda más pacífica — cielo,
viento, hierba, y la fuerza serena de un pueblo ancestral.""",

    1497: """Entrañas: La capital de los Renegados bajo las ruinas de Lordaeron. Una ciudad de
alcantarillas oscura y circular donde los no-muertos llevan su existencia entre canales
de limo verde y antorchas parpadeantes. El Distrito Real alberga a Sylvanas Windrunner.
Los boticarios elaboran pociones dudosas. El aire es húmedo, frío y ligeramente tóxico.
Sombría, funcional e inquietante — pero un hogar para quienes no tienen otro lugar
adonde ir.""",

    3487: """Ciudad de Lunargenta: La capital de los elfos de sangre, medio reconstruida tras la
invasión del Flagelo. La mitad occidental, en funcionamiento, brilla con agujas carmesí
y doradas, guardianes arcanos patrullan calles impecables, y fuentes fluyen con energía
mágica. Las ruinas orientales siguen siendo una cicatriz. La cultura sin'dorei valora la
belleza, la magia y la sofisticación. Una ciudad elegante que enmascara heridas
profundas y una desesperada adicción al poder arcano.""",

    3703: """Ciudad de Shattrath: La ciudad draenei neutral en el Bosque de Terokkar, ahora
compartida por las facciones Aldor y Videntes. La Terraza de la Luz brilla con
resplandor naaru en su centro. Refugiados de toda Outland abarrotan la Ciudad Baja.
Tanto la Alianza como la Horda caminan estas calles en una incómoda tregua. Un centro
cosmopolita donde se mezclan todas las razas — mitad santuario, mitad polvorín político.""",
}

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'El conflicto en las montañas heladas — enanos de la Expedición Cima '
            'Tempestuosa contra orcos del Clan Lobo Gélido en las Montañas de Alterac.'
        ),
        'tone': (
            'Épico, a gran escala, marcial. 40 contra 40 se siente como una '
            'batalla de verdad.'
        ),
        'objectives': (
            'Matad al general enemigo. Capturad torres y cementerios.'
        ),
        'landmarks': (
            'Ubicaciones clave: Base de Cima Tempestuosa, Dun Baldar, Búnker Ala de '
            'Hielo, Cementerio Corazón de Piedra, Cementerio Nevado, Torre Sangre '
            'Helada, Punto de la Torre, Cementerio Lobo Gélido, Fortaleza Lobo '
            'Gélido. NO menciones ubicaciones de otros campos de batalla.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'La guerra por la madera en Vallefresno — las Centinelas Ala de Plata '
            'defienden el bosque, los Exploradores Grito de Guerra buscan sus recursos.'
        ),
        'tone': (
            'Intenso, rápido, personal. Equipo pequeño, cada jugador importa.'
        ),
        'objectives': 'Capturad la bandera enemiga 3 veces.',
        'landmarks': (
            'Ubicaciones clave: Refugio Ala de Plata (base de la Alianza), Fuerte '
            'Grito de Guerra (base de la Horda), el túnel, el campo medio, la '
            'rampa. NO menciones ubicaciones de otros campos de batalla como '
            'molinos, granjas o torres.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'La lucha por los recursos de las Tierras Altas de Arathi entre '
            'Stromgarde y los Renegados.'
        ),
        'tone': (
            'Estratégico, territorial, disperso. Reacciones centradas en el '
            'control de los puntos.'
        ),
        'objectives': 'Controlad puntos para alcanzar 1600 recursos primero.',
        'landmarks': (
            'Ubicaciones clave: Establos (norte, pastos abiertos con corrales de '
            'caballos), Herrería (cruce central, humo y yunques), Aserradero '
            '(mirador en la cima de una colina, plataformas de madera y sierras), '
            'Mina de Oro (entrada de cueva al sureste, vagonetas y antorchas), '
            'Granja (sur, campos y pajares junto a una casa de labranza). NO '
            'menciones ubicaciones de otros campos de batalla.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': 'Un campo de batalla en Tormenta Abisal sobre un fragmento de Draenor.',
        'tone': (
            'Tensión híbrida. Mantener bases mientras se lucha por una bandera '
            'central.'
        ),
        'objectives': (
            'Controlad bases y capturad la bandera central para alcanzar 1600 '
            'puntos.'
        ),
        'landmarks': (
            'Ubicaciones clave: Ruinas del Devastador Vil, Torre de los Elfos de '
            'Sangre, Ruinas Draenei, Torre de los Magos, la bandera central. NO '
            'menciones ubicaciones de otros campos de batalla.'
        ),
    },
}

DUNGEON_FLAVOR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Colmillo Sombrío: Una fortaleza encantada en el Bosque de Argénteos, invadida por worgen
y los sirvientes no-muertos del nigromante Arugal. Nobles fantasmales deambulan por los
pasillos oscuros, sabuesos espectrales aúllan en los patios, y experimentos arcanos
fallidos acechan en cada sombra. La fortaleza se siente como una historia de terror
gótico - piedra fría, luz de antorchas parpadeante, y la constante sensación de que algo
está observando.""",

    34: """El Calabozo: Una prisión bajo Ciudad de Ventormenta donde los presos se han rebelado y
tomado el control. Amotinados Defias, convictos enloquecidos y jefes de banda merodean
por las estrechas celdas de piedra. El calabozo es claustrofóbico y brutal - corredores
angostos, barrotes de hierro, y el eco de la violencia contra muros húmedos. Rápido,
sucio y peligroso.""",

    36: """Las Minas de la Muerte: Un extenso complejo minero bajo Páramos de Poniente, sede
secreta de la Hermandad Defias. El camino serpentea por túneles diseñados por goblins,
aserraderos y operaciones de fundición antes de emerger en una caverna subterránea
inmensa donde un barco pirata a tamaño real descansa en una cala oculta. Se siente como
descubrir un imperio criminal escondido justo bajo las narices de Ciudad de Ventormenta.""",

    43: """Las Cavernas del Lamento: Un laberinto de cavernas retorcidas en Los Baldíos, cubierto
de vegetación exuberante alimentada por magia druídica corrompida. Criaturas mutantes -
raptores, serpientes y limos mutados - se deslizan por túneles teñidos de esmeralda. Los
Druidas del Colmillo se han perdido en la Pesadilla Esmeralda. El aire es espeso, húmedo
y huele a podredumbre de jungla.""",

    47: """Cuchilla Espinosa: Un laberinto espinoso crecido a partir de zarzas colosales en Los
Baldíos, hogar de los quilboar y su matriarca Charlga Zarpa Cuchilla. Guerreros
quilboar, chamanes y sus jabalíes compañeros llenan los sinuosos corredores de espinas.
El calabozo se siente primitivo y feroz - naturaleza retorcida en una fortaleza de
hueso, espina y lodo.""",

    48: """Las Profundidades de Vientonegro: Un templo antiguo parcialmente sumergido en la costa
de Costa Oscura, sagrado para poderes oscuros. Naga, sátiros y cultistas del crepúsculo
adoran a viejos dioses en salones inundados adornados con arquitectura de elfos de la
noche en ruinas. El agua brilla de un azul-verde inquietante, y la atmósfera es opresiva
y ancestral - algo poderoso duerme en las pozas más profundas.""",

    70: """Uldaman: Un yacimiento de excavación titánico enterrado en Tierras Inhóspitas, mitad
excavación, mitad calabozo. Troggs de piedra, autómatas terrígenos y peligros
arqueológicos llenan cámaras de metal titánico pulido y roca en bruto. Cuanto más
profundo se va, más alienígena se vuelve la arquitectura - salones geométricos y lisos
que zumban con poder latente. Se siente como allanar una biblioteca construida por
dioses.""",

    90: """Gnomeregan: Las ruinas irradiadas de la capital gnoma, perdida ante una invasión trogg y
una fuga de radiación catastrófica. Gnomos leprosos enloquecidos, robots averiados y
limos tóxicos pueblan el complejo mecánico de múltiples niveles. Sirenas de alarma
resuenan, charcos de radiación verde brillan, y maquinaria rota chispea por doquier. Es
a partes iguales trágico y absurdo.""",

    109: """El Templo Sumergido: El Templo de Atal'Hakkar, un templo trol arrastrado bajo los
pantanos por la Bandada de Dragones Verdes. Los trols Atal'ai adoran al dios de sangre
Hakkar en salones inundados y cubiertos de enredaderas. Dragontes custodian los niveles
más profundos, y el diseño laberíntico es desorientador. La atmósfera está cargada de
humedad de jungla, magia trol ancestral, y una sensación de ritual prohibido.""",

    129: """Cuchilla Espinosa: Necrópolis: Un cementerio quilboar en Los Baldíos, infestado de
no-muertos. El agente del Flagelo Amnennar el Portador del Frío ha resucitado a los
quilboar muertos, convirtiendo sus criptas sagradas en una necrópolis de hueso y espina.
Quilboar esqueléticos y murciélagos de la peste llenan los corredores sombríos. Un lugar
donde chocan dos tipos de muerte - primitiva y nigromántica.""",

    189: """Monasterio Escarlata: Un monasterio fortificado en Claros de Trisfal, bastión de la
fanática Cruzada Escarlata. Cuatro alas albergan una biblioteca de textos prohibidos, un
arsenal repleto de fanáticos, una catedral de fe retorcida, y un cementerio encantado.
Los Cruzados están bien armados, disciplinados y completamente dementes - convencidos de
que todos son secretamente no-muertos. Arquitectura hermosa que oculta un fanatismo
asesino.""",

    209: """Zul'Farrak: Una ciudad trol medio enterrada en las arenas de Tanaris, hogar de los
hostiles trols Furia de Arena. Templos de piedra abrasados por el sol, altares
sacrificiales y patios arenosos componen este calabozo al aire libre. La famosa batalla
de la escalera te enfrenta a oleadas de guerreros trols. El calor del desierto es
implacable, los trols son salvajes, y la magia ancestral crepita entre las ruinas.""",

    229: """La Cima de Roca Negra: Una fortaleza orca colosal tallada en las alturas de la Montaña
Roca Negra. La cima inferior rebosa de orcos de Roca Negra, ogros y trols, mientras la
cima superior es el asiento del Señor de la Guerra Rend Manonegra y sus aliados
dragontes. La lava brilla abajo, los tambores de guerra resuenan constantemente, y el
aire apesta a humo y sangre. Un bastión militar extenso en el corazón de la Horda
Oscura.""",

    230: """Las Profundidades de Roca Negra: Una vasta ciudad de enanos Hierro Negro en las
profundidades de la Montaña Roca Negra, construida alrededor de un lago de lava fundida.
La taberna El Trago Amargo, la sala del trono del Emperador, y el umbral del Núcleo de
Magma están todos aquí. Elementales, gólems y fanáticos enanos Hierro Negro llenan una
metrópolis subterránea de tamaño imposible. Se siente como si toda una civilización
existiera bajo tierra, oscura, industriosa y hostil.""",

    269: """El Pantano Negro: Una instancia de las Cavernas del Tiempo ambientada en el pantano
primigenio que se convertiría en Las Tierras Devastadas. Agentes de la Bandada de
Dragones Infinitos intentan evitar que Medivh abra el Portal Oscuro, y oleadas de
dragontes atacan a través de grietas temporales. El pantano es oscuro, brumoso y
primigenio, con la energía del Portal crepitando a lo lejos. El tiempo mismo se siente
inestable aquí.""",

    289: """Escuela de la Muerte: Una academia nigromántica en las criptas bajo Caer Darrow,
dirigida por el Culto de los Condenados. Estudiantes y profesores de magia oscura
practican su oficio tanto en los muertos como en los vivos. Esqueletos, fantasmas y
gólems de carne llenan aulas y laboratorios. El calabozo tiene una atmósfera académica
perversa - salones de conferencia y bibliotecas dedicados enteramente a la magia de la
muerte.""",

    329: """Stratholme: Las ruinas ardientes de una ciudad antaño grandiosa, en llamas eternas desde
que Arthas la purgó. El Flagelo no-muerto controla la mitad oriental mientras la Cruzada
Escarlata sostiene fanáticamente las puertas occidentales. Los edificios se derrumban en
fuego perpetuo, abominaciones deambulan por las calles, y la ceniza nunca se asienta. Un
monumento a la tragedia y la locura - cada rincón guarda la memoria de la masacre.""",

    349: """Maraudon: Un sistema de cavernas sagradas en Desolace, deformado por la Princesa
Theradras y sus descendientes centauro tras la muerte del guardián Zaetar. Tres senderos
codificados por color serpentean por cuevas cristalinas, cascadas venenosas y jardines
subterráneos exuberantes antes de llegar al santuario interior. Las cámaras más
profundas son de una belleza inquietante - cristales brillantes, aguas cristalinas, y
magia terrestre ancestral luchando contra la corrupción. Naturaleza, duelo y furia
elemental entrelazados.""",

    389: """La Sima Fuego Rabioso: Un sistema de cavernas volcánicas bajo la propia Orgrimmar, donde
cultistas de la Hoja Ardiente y troggs se han asentado. La lava fluye por túneles
angostos, elementales de fuego patrullan, y el calor es sofocante. Corto y brutal - el
tipo de lugar que te recuerda que la Horda construyó su capital sobre un volcán.""",

    429: """Dire Maul: Una ciudad Altiborne en ruinas en Feralas, dividida en tres alas. Los ogros
han reclamado el norte, sátiros y ancestrales corrompidos infestan el este, y espíritus
fantasmales Altiborne rondan la biblioteca del ala oeste. Una arquitectura élfica en
ruinas de asombrosa belleza sucumbe lentamente al crecimiento de la jungla. El calabozo
se siente vasto, ancestral y melancólico - el cadáver de una gran civilización siendo
despojado por ocupantes.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """La Guarida de Onyxia: Una única caverna vasta en Marjal Revolcafango, hogar de la madre
de cría Onyxia. El acceso serpentea por un túnel angosto de roca calcinada antes de
abrirse a una cámara enorme sembrada de huesos y nidadas de huevos. Los crías pululan,
la lava burbujea en los bordes, y la propia Onyxia llena la caverna de fuego y sombra.
Un túnel claustrofóbico que da paso a una arena abrumadora de fuego de dragón.""",

    309: """Zul'Gurub: Un complejo de templo trol colosal en las junglas de Vega de Tuercespina,
donde la tribu Gurubashi ha liberado al dios de sangre Hakkar. Patios cubiertos de
vegetación, altares sacrificiales y plazas repletas de bestias rodean un templo central
que rezuma magia de sangre. Sacerdotes serpiente, jinetes de murciélagos y cultistas
tigre sirven a sus oscuros amos. La propia jungla parece palpitar con energía vudú
primitiva.""",

    409: """El Núcleo de Magma: El corazón ardiente de la Montaña Roca Negra, un reino de fuego puro
gobernado por Ragnaros el Señor del Fuego. Ríos de lava fluyen entre plataformas de
obsidiana, elementales de fuego y gigantes fundidos patrullan por doquier, y el calor es
apocalíptico. Sabuesos del núcleo de múltiples cabezas, torreones de lava imponentes, y
despertadores de llama ancestrales custodian a su amo. La prueba definitiva de fuego -
hermosa y aterradora a partes iguales.""",

    469: """La Guarida del Ala Negra: El bastión de Nefarian en la cima de la Cima de Roca Negra, un
laboratorio oscuro donde el dragón negro experimenta con otras bandadas de dragones.
Soldados dracónidos, dragontes cromáticos y experimentos fallidos llenan salones de
hierro oscuro y hueso de dragón. Cada cámara presenta un desafío táctico único. La
incursión se siente clínica y siniestra - la guarida de un científico loco a escala de
dragón.""",

    509: """Ruinas de Ahn'Qiraj: Un campo de batalla al aire libre en Silithus donde las fuerzas
qiraji se congregan para la guerra. Guerreros insectoides, destructores de obsidiana y
colosales criaturas parecidas a escarabajos pululan por patios barridos por la arena y
ruinas de templos derrumbados. La arquitectura es alienígena y quitinosa, mitad tumba
egipcia, mitad colmena de insectos. El viento del desierto lleva el chasquido de un
millón de patas.""",

    531: """Templo de Ahn'Qiraj: El santuario interior sellado del imperio qiraji, una pesadilla de
arquitectura alienígena y corrupción de dios antiguo. Los emperadores gemelos, la
realeza silítida colosal, y el propio dios antiguo C'Thun acechan en su interior. Las
paredes palpitan con crecimiento orgánico, ojos observan desde cada superficie, y la
realidad se dobla cerca de la prisión del dios antiguo. El lugar más alienígena y
perturbador del Azeroth clásico.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Salas Destrozadas: El bastión de los orcos del vil dentro de la Ciudadela del Fuego
Infernal, un pasillo empapado de sangre de los sirvientes más fanáticos de la Legión
Ardiente. Gladiadores, legionarios y berserkers orcos del vil abarrotan cada corredor,
con prisioneros encadenados a los muros. La arquitectura es de hierro brutal y piedra
roja, manchada por evidencia de violencia constante. Un asalto implacable contra una
fortaleza que contraataca en cada paso.""",

    542: """El Alto Horno de Sangre: Una fábrica demoníaca dentro de la Ciudadela del Fuego Infernal
donde se fabrican orcos del vil mediante rituales oscuros. Cubas de sangre hirviendo,
prisioneros enjaulados a la espera de la transformación, y maquinaria vil llenan las
cámaras humeantes. Orcos del vil nacientes y sus supervisores custodian las líneas de
producción. El calabozo apesta a sangre y azufre - un espectáculo de horror industrial.""",

    543: """Las Murallas del Fuego Infernal: Las fortificaciones exteriores de la Ciudadela del
Fuego Infernal, primera línea de defensa del ejército orco del vil. Torres de
vigilancia, almenas y pasarelas angostas ofrecen vistas panorámicas de la destrozada
Península del Fuego Infernal abajo. Soldados orcos del vil, jinetes de worgs, y un
dragón cautivo custodian los muros. El viento aúlla entre las murallas destrozadas, y el
cielo rojo de Outland se extiende sin fin en lo alto.""",

    545: """La Cámara de Vapor: Una estación naga de bombeo de agua en el Embalse Colmillo
Serpiente, donde las fuerzas de Lady Vashj drenan la Marisma de Zangar. Tuberías,
válvulas y canales de agua colosales dominan el diseño industrial. Naga, señores del
pantano y elementales de agua custodian la maquinaria. El vapor silba de cada junta y el
rugido del agua torrencial es ensordecedor. Un calabozo que se siente como sabotear una
fábrica hostil.""",

    546: """El Bajo Pantano: Un pantano en descomposición bajo el Embalse Colmillo Serpiente,
plagado de criaturas fúngicas mutadas y espíritus de la naturaleza hostiles. Gigantes de
esporas, señores del pantano y fauna venenosa llenan las cavernas cubiertas de
vegetación. Hongos bioluminiscentes proyectan un brillo inquietante sobre pozas
estancadas. El aire está cargado de esporas y del olor a descomposición - naturaleza
desbocada vuelta hostil.""",

    547: """Los Corrales de Esclavos: Los campos de trabajo del Embalse Colmillo Serpiente donde los
draenei Rotos son mantenidos cautivos por capataces naga. Túneles anegados, corrales
toscos y supervisores naga con sus látigos definen la atmósfera. Crecimientos fúngicos y
criaturas del pantano han infiltrado el complejo. Un calabozo impregnado de miseria y
opresión, medio inundado y en descomposición.""",

    552: """El Arcatraz: Un satélite carcelario dimensional de la Fortaleza de la Tempestad, que
retiene a las entidades más peligrosas del cosmos. Brujos eredar, criaturas del vacío y
saboteadores elfos de sangre deambulan por celdas diseñadas para contener horrores más
allá de la imaginación. La arquitectura es tecnología cristalina draenei deformada por
sus internos. Cada puerta de celda que pasas te hace preguntarte qué escapó - y qué
sigue encerrado dentro.""",

    553: """La Botánica: Una biocúpula colosal satélite de la Fortaleza de la Tempestad, donde
antaño se cultivaba flora exótica de todo el cosmos. Los elfos de sangre se han
apoderado de la instalación, y las plantas han crecido salvajes y hostiles. Azotadores,
treants y especímenes botánicos alienígenas llenan invernaderos de cristal
resplandeciente. Hermosa pero mortal - cada flor podría matarte, y los elfos de sangre
son peores.""",

    554: """El Mecanar: Un ala de fabricación de la Fortaleza de la Tempestad, ahora controlada por
ingenieros elfos de sangre y sus creaciones mecánicas. Autómatas arcanos, devastadores
del vil y supervisores nigromantes custodian corredores de cristal reluciente y
maquinaria zumbante. La tecnología es elegante y alienígena - ingeniería draenei
reutilizada para fines siniestros. Todo zumba con energía arcana apenas contenida.""",

    555: """El Laberinto de las Sombras: El ala más profunda de Auchindoun, donde el Consejo de las
Sombras conduce sus rituales más oscuros. Caminantes del vacío, invocadores del vil y
cultistas de la Cábala adoran en cámaras cargadas de magia sombría. Murmullo, un
elemental de sonido primordial, está encadenado en la cámara más profunda. La oscuridad
aquí se siente viva y hambrienta - las sombras se mueven por sí solas, y los susurros
vienen de todas partes y de ninguna.""",

    556: """Salas de Sethekk: Salas de templo arakkoa dentro de Auchindoun, ocupadas por fanáticos
devotos del Dios Cuervo Anzu. Sacerdotes arakkoa enloquecidos, sus espíritus invocados y
guardianes espectrales llenan corredores cubiertos de plumas. La arquitectura mezcla
estilos draenei y arakkoa de formas inquietantes. Los habitantes se han vuelto
completamente dementes, y las salas resuenan con chillidos desquiciados y profecías
oscuras.""",

    557: """Tumbas de Maná: El ala infestada de etéreos de Auchindoun, donde el consorcio del
Príncipe-Nexo Shaffar saquea las bóvedas funerarias draenei. Bandidos etéreos, autómatas
arcanos y espíritus draenei inquietos chocan en cámaras funerarias cristalinas. Las
tumbas brillan con energía sagrada residual mientras los etéreos la drenan
sistemáticamente. Un lugar sagrado siendo saqueado sistemáticamente por ladrones
interdimensionales.""",

    558: """Criptas Auchenai: El cementerio draenei bajo Auchindoun, donde los sacerdotes auchenai
han enloquecido comunicándose con los muertos. Espíritus inquietos, clérigos poseídos y
draenei no-muertos llenan las criptas revestidas de huesos. Lo que antes fue un lugar de
recuerdo respetuoso se ha convertido en una casa de osarios. La tragedia es palpable -
eran cuidadores que se perdieron a sí mismos en el duelo.""",

    560: """Antiguas Laderas de Trabalomas: Una instancia de las Cavernas del Tiempo ambientada en
el pasado, cuando Thrall aún era esclavo en la Fortaleza Durnholde. El Trabalomas de
años atrás es verde, pacífico y lleno de humanos ajenos que siguen con sus vidas. La
Bandada de Dragones Infinitos intenta alterar la historia impidiendo la fuga de Thrall.
Se siente surrealista - caminar por un lugar que conoces antes de que todo saliera mal.""",

    568: """Zul'Aman: Un bastión de trols del bosque en las Tierras Fantasma, donde el Señor de la
Guerra Zul'jin ha imbuido a sus campeones con la esencia de dioses animales. Espíritus
de lince, oso, águila y halcón dragón infunden a los guardianes del templo trol. La
arquitectura selva-templo Amani es vívida y primitiva, decorada con máscaras, tótems y
pintura de guerra. Un desafío contrarreloj donde la velocidad importa y los tambores
trols nunca dejan de sonar.""",

    585: """Terraza de los Magísteres: El último bastión de Kael'thas Solestridente en la Isla de
Quel'Danas, un palacio de elfos de sangre de asombrosa elegancia que oculta corrupción
demoníaca. Cristales del vil alimentan autómatas arcanos, magísteres elfos de sangre
canalizan magia prohibida, y un naaru capturado está siendo drenado de su Luz. La
belleza de la arquitectura de Ciudad de Lunargenta retorcida por la desesperación y la
adicción - salones dorados que ocultan un pacto monstruoso.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan: La torre encantada del último Guardián, Medivh, en Paso de la Muerte. Una cena
espectral, un escenario de ópera con intérpretes fantasmales, una partida de ajedrez
cobrando vida, y un observatorio celestial llenan la torre imposiblemente alta. La torre
existe parcialmente fuera de la realidad normal - las habitaciones cambian, el tiempo se
dobla, y ecos de la locura de Medivh se repiten eternamente. Inquietantemente hermosa,
profundamente espeluznante, y absolutamente única.""",

    534: """Cumbre del Hyjal: Una incursión de las Cavernas del Tiempo ambientada durante la Batalla
del Monte Hyjal, la resistencia culminante contra Archimonde y la Legión Ardiente.
Oleadas de no-muertos y demonios asaltan tres bases sucesivamente - humana, de la Horda
y de elfos de la noche. El árbol del mundo Nordrassil se alza en lo alto mientras el
bosque arde. Un escenario de defensa épico donde el destino de Azeroth pende de un hilo
y héroes legendarios luchan a tu lado.""",

    544: """La Guarida de Magtheridon: Una única cámara brutal bajo la Ciudadela del Fuego Infernal
donde el señor del abismo Magtheridon está encadenado. Canalizadores mantienen su
prisión mientras la energía del fuego infernal palpita por la sala. El espacio es
opresivamente caluroso, apesta a sangre demoníaca y azufre. Un encuentro directo pero
castigador - un demonio colosal, una sala mortal, sin margen de error.""",

    548: """La Caverna del Santuario de la Serpiente: El bastión submarino de Lady Vashj en el
Embalse Colmillo Serpiente, un palacio inundado de belleza corrompida. Naga, caminantes
de marea y hidras colosales custodian cámaras donde cascadas caen en pozas luminosas.
Puentes cruzan lagos subterráneos, y las cámaras más profundas palpitan con las aguas
corrompidas de la Marisma de Zangar. Elegante arquitectura naga se encuentra con el
poder crudo de un océano subterráneo.""",

    550: """Fortaleza de la Tempestad - El Ojo: La fortaleza naaru capturada de Kael'thas
Solestridente, una ciudadela cristalina flotando sobre Tormenta Abisal. Consejeros elfos
de sangre, autómatas arcanos y criaturas del vacío custodian cámaras de cristal draenei
resplandeciente. La tecnología es asombrosamente alienígena y hermosa, reutilizada por
elfos desesperados que alimentan su adicción a la magia. La vista de Tormenta Abisal
destrozada desde las plataformas es tan impresionante como aterradora.""",

    564: """El Templo Negro: La fortaleza de Illidan Tempestira en Valle Sombraluna, un templo
draenei colosal corrompido por la ocupación demoníaca. Orcos del vil, demonios, naga y
elfos de sangre sirven al Traidor a través de patios extensos, sistemas de
alcantarillado y grandes salones. La belleza original del templo está marcada por la
corrupción del vil - símbolos sagrados agrietados, altares profanados, y fuego verde
donde antes hubo Luz. La culminación de la historia de Outland, terminando en el trono
de Illidan.""",

    565: """La Guarida de Gruul: Un tosco complejo de cavernas en las Montañas Filoespada, hogar del
padre gronn Gruul el Matadragones. Sirvientes ogros y los hijos monstruosos de Gruul
custodian el acceso a su cámara, sembrada de huesos de dragón y trofeos. Las cuevas se
sienten primitivas y brutales - sin arquitectura, sin decoración, solo roca cruda
moldeada por los puños de gigantes.""",

    580: """Meseta del Pozo de Sol: La incursión final de la Cruzada Ardiente, ambientada en el
corazón del Pozo de Sol restaurado en la Isla de Quel'Danas. La Legión Ardiente intenta
invocar a Kil'jaeden a través del propio Pozo de Sol. Una arquitectura élfica impecable
de belleza sobrecogedora enmarca una batalla desesperada contra los demonios más
poderosos del ejército de la Legión. La luz sagrada del Pozo de Sol choca con la
oscuridad demoníaca en cada cámara.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Fuerte Utgarde: Una fortaleza vrykul en las costas del Fiordo Aquilonal, la primera
muestra de los peligros de Rasganorte. Salones de inspiración vikinga de piedra oscura y
hierro, iluminados por hogares rugientes y decorados con cráneos de dragón. Guerreros
vrykul, cuidadores de proto-dracos y sus sirvientes no-muertos llenan los grandes
salones. El calabozo se siente como asaltar un salón nórdico - frío, brutal, e
impregnado de cultura guerrera.""",

    575: """Pináculo de Utgarde: Las alturas superiores del Fuerte Utgarde, donde el rey vrykul
Ymiron gobierna desde su trono helado. Salones de trofeos, pajareras de águilas, y
cámaras rituales se alzan sobre el fiordo. La arquitectura se vuelve más grandiosa y
amenazante a medida que se asciende, culminando en la sala del trono escarchada de
Ymiron. El viento aúlla entre las almenas abiertas, y la vista del paisaje helado abajo
produce vértigo.""",

    576: """El Nexo: Las cuevas cristalinas bajo Fríallende, bastión de la guerra de la Bandada de
Dragones Azules contra la magia mortal. Cavernas heladas de belleza imposible contienen
anomalías arcanas, cazadores de magos enloquecidos, y grietas en la realidad. Dragones
cristalizados cuelgan congelados en pleno vuelo. El calabozo resplandece con energía
arcana inestable - azules, púrpuras y blancos que se refractan a través del hielo y el
cristal en todas direcciones.""",

    578: """El Oculus: Los anillos superiores del Nexo, una serie de plataformas flotantes
conectadas por puentes mágicos muy por encima del nexo de líneas ley. Los jugadores
montan dracos para navegar entre segmentos de anillo mientras luchan contra las fuerzas
de Malygos. El vacío se extiende abajo, la energía arcana crepita entre plataformas, y
el vértigo es real. Un calabozo que se siente como volar a través de una tormenta mágica
al borde de la realidad.""",

    595: """La Masacre de Stratholme: Una instancia de las Cavernas del Tiempo ambientada durante la
fatídica purga de Arthas en la ciudad infectada por la plaga. Las calles de Stratholme
están intactas pero condenadas - los ciudadanos se transforman en no-muertos ante tus
ojos, y Arthas ordena sombríamente su muerte antes de la transformación. El calabozo es
únicamente perturbador porque estás ayudando a cometer la atrocidad que inicia la caída
de Arthas. El momento más oscuro de la historia, revivido.""",

    599: """Salas de Piedra: Una instalación titánica en las Cumbres Tormentosas, parte del vasto
complejo de Ulduar. Corredores de piedra de perfección geométrica albergan autómatas
titánicos averiados, enanos de hierro, y antiguos sistemas de defensa. El Tribunal de
las Eras guarda registros de la propia creación. El calabozo se siente académico y
ancestral - un museo donde las exhibiciones contraatacan y la historia guardada aquí
podría destrozar civilizaciones.""",

    600: """Fuerte Drak'Tharon: Una fortaleza trol infestada por el Flagelo en la frontera entre
Colinas Pardas y Zul'Drak. El Flagelo ha resucitado a los trols muertos y corrompido a
sus bestias dinosaurio, creando una fusión antinatural de cultura trol y poder
nigromántico. Raptores esqueléticos, trols zombis, y el liche Novos el Convocador llenan
los salones en decadencia. Arquitectura trol desmoronándose bajo el peso de la
no-muerte.""",

    601: """Azjol-Nerub: El reino nerubiano en ruinas bajo Rasganorte, un descenso vertical
asfixiado de telarañas a través del imperio arácnido. La arquitectura nerubiana de seda
y quitina se extiende por vastos abismos subterráneos. Nerubianos no-muertos sirven al
Flagelo mientras los vivos luchan desesperadamente. El calabozo te hace caer cada vez
más profundo a través de suelos que se derrumban - claustrofóbico, alienígena, y plagado
de cosas que no deberían existir.""",

    602: """Salas del Relámpago: Un complejo de forja titánico en Ulduar, crepitando con energía
eléctrica. Enanos de hierro, gigantes de tormenta y autómatas rúnicos custodian
corredores de metal reluciente y relámpagos en arco. Loken, el guardián titán
corrompido, espera en la cámara más profunda. Cada superficie zumba con poder, chispas
bailan por los muros, y el trueno de la forja es constante y ensordecedor.""",

    604: """Gundrak: Un templo trol Drakkari en Zul'Drak, donde los trols sacrifican a sus propios
dioses animales para alimentar su guerra contra el Flagelo. Los altares rebosan de
sangre divina mientras espíritus de serpiente, mamut y rinoceronte son consumidos. El
templo es masivo y primitivo - piedra tallada, pozas rituales, y la energía desesperada
de una civilización agonizante quemando a sus propios dioses por sobrevivir.""",

    608: """Fortaleza Violeta: Una prisión mágica bajo Dalaran, donde el Kirin Tor contiene a las
criaturas más peligrosas de Rasganorte. Agentes de la Bandada de Dragones Azur asaltan
la prisión desde portales, liberando internos en oleadas. La arquitectura es un elegante
púrpura y plata de Dalaran, pero los internos son de pesadilla. Un escenario de defensa
de torre en un calabozo de magos - las salvaguardas arcanas se tensan contra el caos.""",

    619: """Ahn'kahet: El Antiguo Reino: Las profundidades más recónditas de Azjol-Nerub, donde los
Sinrostro sirven al dios antiguo Yogg-Saron. La arquitectura cambia de nerubiana a algo
mucho más antiguo y alienígena - las paredes orgánicas palpitan, la realidad se deforma,
y efectos de locura asaltan la mente. Olvidados, lanzadores de hechizos, y el heraldo
Volazj acechan en cámaras que desafían la geometría. El calabozo más perturbador de
Rasganorte.""",

    632: """Forja de Almas: El primero de tres calabozos de la Ciudadela de Corona de Hielo, un
motor colosal que muele almas donde el Rey Exánime procesa a los muertos. Ríos de almas
torturadas fluyen por maquinaria de hierro, herreros espectrales martillean yunques de
sufrimiento, y el Devorador de Almas custodia la forja. Los gritos nunca cesan. Una
pesadilla industrial alimentada por tormento eterno.""",

    650: """Prueba del Campeón: Una gran arena de torneo bajo el Coliseo Argenta en Corona de Hielo,
donde campeones de la Alianza y la Horda demuestran su valía. Justas montadas, duelos de
campeones, y una emboscada final del Caballero Negro se desarrollan en el terreno del
torneo. La atmósfera es festiva y competitiva hasta que los no-muertos irrumpen en la
fiesta. Pompa y espectáculo con un giro oscuro.""",

    658: """Fosa de Saron: Una brutal mina de esclavos en Corona de Hielo donde las fuerzas del
Flagelo trabajan a los prisioneros hasta la muerte extrayendo mena de saronita. La fosa
está abierta al cielo helado, con cadenas colosales, plataformas mineras, y depósitos de
saronita por doquier. El Maestro de Forja Garfrost lanza rocas mientras Tyrannus
patrulla en su draco de cría escarchada en lo alto. Desesperanza y crueldad destiladas
en piedra helada y metal oscuro.""",

    668: """Salas del Reflejo: Los Pasillos Helados encantados de la Ciudadela de Corona de Hielo,
donde los ecos de las víctimas de Añoranza persisten alrededor de la cámara de la hoja.
El propio Rey Exánime te persigue a través de corredores que se derrumban mientras
oleadas de fantasmas atacan. Los pasillos son de hielo prístino y saronita oscura, y el
terror es real - no puedes luchar contra él, solo huir. El calabozo más intenso
narrativamente del juego, una huida desesperada de una perdición inevitable.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas: La necrópolis flotante del archiliche Kel'Thuzad, cerniéndose sobre
Cementerio de Dragones. Cuatro alas de horrores temáticos - el Cuartel Arácnido de
arañas gigantes, el Cuartel de la Plaga de enfermedad y abominaciones, el Cuartel
Militar de comandantes caballeros de la muerte, y el Cuartel de Autómatas de gólems de
carne. Arquitectura gótica de piedra oscura y limo verde, con la fría precisión de la
organización militar no-muerta. La obra maestra de muerte del Flagelo.""",

    603: """Ulduar: Una ciudad-prisión titánica en las Cumbres Tormentosas, la incursión más
grandiosa de Rasganorte. Salones colosales de metal reluciente y piedra albergan a los
guardianes titánicos corrompidos y sus sirvientes, con el dios antiguo Yogg-Saron
aprisionado en la bóveda más profunda. La escala es asombrosa - batallas de vehículos en
las puertas, un observatorio abierto al cosmos, jardines de belleza sobrenatural, y un
descenso a la propia locura. Ancestral, magnífica y aterradora.""",

    615: """Santuario de Obsidiana: Una cámara volcánica bajo el Templo del Reposo del Wyrm donde
Sartharion custodia huevos de dragón del crepúsculo. Ríos de lava dividen las
plataformas de obsidiana, y tres lugartenientes dracos del crepúsculo patrullan sus
propias islas. La cámara brilla en naranja y rojo, el calor distorsiona el aire, y la
traición de la bandada de dragones negros queda al descubierto. Una arena directa de
fuego y escamas.""",

    616: """El Ojo de la Eternidad: El santuario personal de Malygos en la cúspide del Nexo sobre
Fríallende, una plataforma suspendida en energía ley cruda. No hay suelo, no hay muros -
solo un disco de fuerza mágica sobre un vacío de arcano azul y violeta arremolinado. El
Tejedor de Hechizos ataca con todo el poder de la Bandada de Dragones Azules. La
incursión se siente de otro mundo - luchar contra un aspecto de dragón en el corazón de
la tormenta arcana de Azeroth.""",

    624: """Bóveda de Archavon: Una bóveda titánica bajo la Fortaleza de Fríallende, accesible solo
para la facción que controla la zona. Gigantes de piedra y autómatas elementales
custodian las cámaras en una serie directa de encuentros con jefes. La arquitectura es
diseño titánico utilitario - funcional, colosal y sin adornos. Una recompensa por la
victoria en JcJ, rápida y brutal.""",

    631: """Ciudadela de Corona de Hielo: El trono del Rey Exánime, la culminación de la Ira del Rey
Exánime. Una fortaleza imponente de saronita y hielo que se alza desde el corazón de
Corona de Hielo. Cada ala intensifica el horror - desde los ejércitos no-muertos de la
Cima Inferior, pasando por las Obras de la Plaga, el Salón Carmesí y las Salas del Ala
Escarchada, hasta el propio Trono Helado. La arquitectura es opresiva, hermosa en su
crueldad, y diseñada para quebrar la esperanza. Este es el final.""",

    649: """Prueba del Cruzado: El Coliseo Argenta en Corona de Hielo, una arena de torneo que
desciende a la tierra cuando el suelo se derrumba en una caverna nerubiana subterránea.
El nivel superior es estandartes brillantes y multitudes vitoreando; el nivel inferior
es horror quitinoso y el dominio de Anub'arak. El contraste entre la competición festiva
arriba y el terror ancestral abajo define toda la experiencia.""",

    724: """Santuario Rubí: Una cámara bajo el Templo del Reposo del Wyrm donde la bandada de
dragones del crepúsculo ha invadido el santuario de los dragones rojos. Halion, el
destructor del crepúsculo, se desplaza entre el reino físico y el reino de las sombras.
La cámara alterna entre cálida luz rubí y fría sombra púrpura. La última incursión antes
del Cataclismo - una breve y ominosa advertencia de la destrucción por venir.""",
}
