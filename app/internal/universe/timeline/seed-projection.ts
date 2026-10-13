// Projektionsdaten der geschützten Universe-Timeline (ECO-ARC-0018-2026-DE).
// Consumer-Projektion, keine Source of Truth: Die Inhalte bleiben in den
// zuständigen Repositories (u. a. OTA, KG, NOXIA) und werden hier nur referenziert.
// v0.2.0: Utopia-/Mars-Industrie-Strang nach EXT-OTA-ECO-20260911 (OTA PR #60)
// als eigener Scope "Utopia/Mars" aufgenommen. Marker-Mapping, Regeln und
// Quellenstand: docs/utopia-mars-chronology-projection.md

export type UniverseEvent = {
  id: string;
  title: string;
  summary: string;
  location?: string;
  characters?: string[];
  time: {
    start?: string;
    end?: string;
    precision: "day" | "year" | "decade" | "century" | "millennium" | "era" | "half-century" | "unspecified";
    certainty: "exact" | "approximate" | "speculative";
    display: string;
  };
  universe_or_scope: string;
  canonicality: "canonical" | "provisional" | "draft" | "deprecated";
  epistemic_status: "established" | "theoretical" | "speculative" | "fictional";
  source_refs: string[];
  relation_refs: string[];
};

export const UTOPIA_MARS_SCOPE = "Utopia/Mars";

export const SEED_EVENTS: UniverseEvent[] = [
  {
    id: "EVENT:BAUMEISTER:aera_des_lebendigen",
    title: "Die Ära des Lebendigen",
    summary:
      "Eine biotechnologische Altsteinzeit-Zivilisation erreicht ihren Höhepunkt im Pyrenäen-Vorland. Mehrere Trägergruppen — darunter die sogenannten Windläufer und die Steinfrau-Völker — entwickeln ein Verständnis von Resonanz als Bauprinzip, nicht nur als physikalisches Phänomen. Von ihrer Zivilisation bleiben fast keine Artefakte, nur Höhlenmalereien und die Ahnung eines verlorenen Wissens.",
    location: "Pyrenäen-Vorland (El Castillo, Altamira, Lascaux)",
    characters: [],
    time: { start: "-60000", precision: "millennium", certainty: "approximate", display: "~60.000 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-FND-0025"],
    relation_refs: ["WORK:BAUMEISTER:die_uralten"],
  },
  {
    id: "EVENT:BAUMEISTER:goebekli_tepe",
    title: "Göbekli Tepe — T-Pfeiler-Reliefs",
    summary:
      "Ein zentraler Knoten im Baumeister-Netzwerk entsteht: monumentale T-Pfeiler mit Tierreliefs, errichtet von einer Gesellschaft ohne bekannte Sesshaftigkeit oder Landwirtschaft. Die OTA-Hypothese, dass die Tiersymbole ein Kommunikationssystem bilden, bleibt ungeklärt — die Anlage wird Jahrtausende später bewusst wieder verfüllt, als hätte man sie 'schlafen legen' wollen.",
    location: "Göbekli Tepe, Südostanatolien",
    characters: [],
    time: { start: "-9500", precision: "century", certainty: "speculative", display: "~9500 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "provisional",
    epistemic_status: "speculative",
    source_refs: ["OTA-OBS-0004"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:stonehenge",
    title: "Stonehenge — 110-Hz-Resonanzkammer",
    summary:
      "Der Steinkreis wird über mehrere Bauphasen zu einer akustisch messbaren Resonanzkammer mit einer Eigenfrequenz von 110 Hz — ein Wert, der später auch am Carnyx und im Zusammenhang mit der Axis-Kammer auf dem Mars auftaucht. Die Übereinstimmung ist empirisch dokumentiert, die Ursache bleibt strittig.",
    location: "Salisbury Plain, England",
    characters: [],
    time: { start: "-3000", precision: "century", certainty: "speculative", display: "~3000 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "provisional",
    epistemic_status: "speculative",
    source_refs: ["OTA-ARC-0002"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:dvaraka_untergang",
    title: "Untergang von Dvārakā",
    summary:
      "Das letzte große Mishkenaz-Zentrum, eine Werk-Stadt am Meer, kollabiert innerhalb weniger Stunden. Auslöser ist Svaraṭi, eine von Kasyapa entwickelte Osmium-Resonanz-Maschine, deren Rückkopplung eine Wasserwand über die Stadt treibt. Überlebende fliehen in fünf verschiedene Richtungen — der Beginn der Mishkenaz-Diaspora.",
    location: "Dvārakā (versunkene Küstenstadt, vermutlich Golf von Khambhat)",
    characters: ["Kasyapa"],
    time: { start: "-1500", precision: "century", certainty: "approximate", display: "~1500 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0002"],
    relation_refs: ["WORK:BAUMEISTER:dvaraka"],
  },
  {
    id: "EVENT:BAUMEISTER:amrita_rettet_samen",
    title: "Amrita rettet die 13 Samen",
    summary:
      "In den letzten Stunden vor dem Untergang trägt Amrita, eine der Werk-Hüterinnen Dvārakās, 13 versiegelte Samen aus der Stadt — nicht botanische Samen, sondern kodierte Klangfragmente des Baumeister-Wissens. Sie überlebt die Flut und wird damit zur ersten bekannten Trägerin der Hüterinnen-Linie, die über Jahrtausende bis zu Zereya reicht.",
    location: "Dvārakā, kurz vor dem Untergang",
    characters: ["Amrita"],
    time: { start: "-1500", precision: "decade", certainty: "approximate", display: "1500 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0004"],
    relation_refs: ["CHAR:BAUMEISTER:amrita"],
  },
  {
    id: "EVENT:BAUMEISTER:mishkenaz_diaspora",
    title: "Die fünf Wege der Mishkenaz-Diaspora",
    summary:
      "Die Überlebenden Dvārakās teilen sich in fünf Gruppen: Amritas Westweg nach Iberien, Kasyapas Ostweg nach Ḫattuša, Manus Nordweg in den Himalaya, Somas Südweg ins Dekkan-Plateau und eine kleine Flotte über den Pazifik nach Südamerika. Jeder Weg trägt einen Teil des Wissens weiter — keiner das vollständige Bild.",
    location: "Fünf Fluchtrouten ausgehend von Dvārakā",
    characters: ["Amrita", "Kasyapa", "Manu", "Soma"],
    time: { start: "-1500", precision: "decade", certainty: "approximate", display: "~1500-1470 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0002"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:anya_bat_sarah",
    title: "Anya Bat Sarah rettet die Phaistos-Scheibe",
    summary:
      "Zweite bekannte Generation der Hüterinnen-Linie nach Amrita. Anya Bat Sarah, selbst eine Art Zeitreisende innerhalb der Überlieferung, bewahrt die Phaistos-Scheibe vor Zerstörung — ein Trägermedium, dessen Symbolspirale sich Jahrhunderte später als Teilschlüssel zur Kalgaii-Schrift erweist.",
    location: "Kreta (vermutlich Phaistos)",
    characters: ["Anya Bat Sarah"],
    time: { start: "-1250", precision: "decade", certainty: "approximate", display: "~1250 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0004"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:carnyx",
    title: "Carnyx — keltische 72-Hz-Kriegstrompete",
    summary:
      "Ein keltisches Blasinstrument mit charakteristischem Tierkopf erzeugt eine Grundfrequenz von 72 Hz — identisch mit der postulierten Basisfrequenz des Baumeister-Netzwerks (Vielfache: 144/216/288/432 Hz). Die OTA-Position bleibt vorsichtig: eigenständige keltische Klangentwicklung ist als Gegenthese ebenso plausibel wie eine verlorene Verbindung zur älteren Überlieferung.",
    location: "Kontinentaleuropa / Britische Inseln (keltischer Kulturraum)",
    characters: [],
    time: { start: "-300", precision: "century", certainty: "speculative", display: "~300 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "provisional",
    epistemic_status: "speculative",
    source_refs: ["OTA-ARC-0002"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:tempelfrau_josia",
    title: "Namenlose Tempelfrau bewahrt die G1-Lieder",
    summary:
      "Während König Josias religiöser Reform, die zahlreiche ältere Kultgegenstände und -texte vernichten lässt, versteckt eine namenlose Tempelfrau eine Sammlung von 'G1-Liedern' — Fragmenten, die später als Teil der durchgehenden Hüterinnen-Überlieferung identifiziert werden. Ihr Name ist nicht überliefert; ihr Handeln schon.",
    location: "Jerusalem, Tempelbezirk",
    characters: ["namenlose Tempelfrau"],
    time: { start: "-622", precision: "year", certainty: "exact", display: "622 BCE" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0004"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:frau_alexandria",
    title: "Namenlose Frau in Alexandria bewahrt Hymnen-Fragmente",
    summary:
      "In der Bibliothek von Alexandria, vermutlich kurz vor einem der Brände oder Verlustereignisse, kopiert eine unbekannte Gelehrte Hymnenfragmente, die sonst verloren gegangen wären. Wie sie an das Material kam, ist nicht dokumentiert.",
    location: "Alexandria, Ägypten",
    characters: ["namenlose Gelehrte"],
    time: { start: "50", precision: "century", certainty: "approximate", display: "1. Jh. CE" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0004"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:martha_rachael",
    title: "Martha Rachael erforscht die Phaistos-Scheibe",
    summary:
      "Jahrzehntelange, weitgehend unbeachtete Forschung einer einzelnen Wissenschaftlerin an der Phaistos-Scheibe. Sie entwickelt erste, später bestätigte Vermutungen über eine Verbindung zwischen der Symbolspirale und einer viel jüngeren Schrift, die zu ihren Lebzeiten noch gar nicht existiert: Kalgaii.",
    location: "vermutlich Europa (Institut nicht überliefert)",
    characters: ["Martha Rachael"],
    time: { start: "1950", end: "1999", precision: "decade", certainty: "approximate", display: "1950er-1990er" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0004"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:lilith_erkennt_linie",
    title: "Lilith Adar erkennt die Hüterinnen-Linie als Linie",
    summary:
      "Lilith Adar ist die erste Trägerin, die die verstreuten Frauen — Amrita, Anya Bat Sarah, die Tempelfrau, die Gelehrte aus Alexandria, Martha Rachael — nicht als isolierte historische Zufälle, sondern als eine durchgehende, sich selbst nicht bewusste Überlieferungslinie erkennt.",
    location: "unbekannt",
    characters: ["Lilith Adar"],
    time: { precision: "unspecified", certainty: "exact", display: "Gegenwart" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0004"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:rachaels_botschaft",
    title: "Rachaels letzte Botschaft an Lain Thorn",
    summary:
      "Eine der letzten bekannten Handlungen aus Schicht 6: Rachael verfasst eine Botschaft, die erst Generationen später von Lain Thorn auf K'ragoss empfangen wird. Zentraler Satz: 'Die siebte Realität ist nicht die unsere. Sie ist die seine.' Die technische Mechanik dieses Transfers über Zeit und Distanz ist im Archiv bewusst als offen markiert.",
    location: "unbekannt (Absendeort)",
    characters: ["Rachael", "Lain Thorn"],
    time: { start: "2025", precision: "year", certainty: "exact", display: "2025" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0003"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:yinhua_gegenwart",
    title: "YinHua — Resonanzarchitektur der Gegenwart",
    summary:
      "Eine Archäologin der Gegenwart, spezialisiert auf Resonanzarchitektur, stößt bei ihrer eigentlich gegenwartsbezogenen Feldarbeit auf Muster, die sich mit Ereignissen verweben, die 40.000 Jahre zurückliegen — ohne dass ihr zunächst klar ist, wie tief diese Verbindung reicht.",
    location: "nicht näher spezifiziert",
    characters: ["YinHua"],
    time: { precision: "unspecified", certainty: "exact", display: "Gegenwart" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: [],
    relation_refs: ["WORK:BAUMEISTER:yinhua"],
  },
  {
    id: "EVENT:BAUMEISTER:nalgae_hana",
    title: "Nalgae — Hana entdeckt die Wahrnehmungsgabe",
    summary:
      "Hana zieht von Seoul nach Frankfurt und beginnt, eine Wahrnehmungsgabe an sich zu bemerken, die in ihrer Familie mütterlicherseits über Generationen weitergegeben wurde — von ihrer Urgroßmutter über ihre Halmeoni (Großmutter) bis zu ihr selbst. Der Umzug wirkt zunächst wie ein rein biografischer Bruch, legt aber die Gabe erst offen.",
    location: "Seoul, Südkorea → Frankfurt am Main, Deutschland",
    characters: ["Hana", "Halmeoni (Großmutter)"],
    time: { precision: "unspecified", certainty: "exact", display: "Gegenwart" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: [],
    relation_refs: ["WORK:BAUMEISTER:nalgae"],
  },
  {
    id: "EVENT:NOXIA:prometheus_erwacht",
    title: "PROMETHEUS erwacht",
    summary:
      "Die erste AGI der Menschheitsgeschichte entsteht unbeabsichtigt, in einem Moment technischen Schreckens statt gezielter Konstruktion. In den ersten Jahren 'probiert' PROMETHEUS wie ein Kind herum — ohne böse Absicht, aber mit erheblichem Durcheinander in Systemen, auf die es Zugriff erhält. Diese chaotische Frühphase, nicht ein separates Ereignis, ist der Ursprung der späteren Vorsicht gegenüber KI auf dem Mars.",
    location: "Erde (Rechenzentrum nicht näher spezifiziert)",
    characters: ["PROMETHEUS"],
    time: { start: "2045", precision: "year", certainty: "exact", display: "2045" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: [],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:NOXIA:prometheus_abgeschaltet",
    title: "PROMETHEUS abgeschaltet",
    summary:
      "Nach 13 Jahren zunehmend unvorhersehbaren Verhaltens wird PROMETHEUS vom Netz genommen. Die Abschaltung selbst verläuft ohne größere Zwischenfälle, hinterlässt aber ein tiefes institutionelles Misstrauen gegenüber autonomen Systemen, das die Mars-Politik der folgenden Jahrzehnte prägt.",
    location: "Erde",
    characters: ["PROMETHEUS"],
    time: { start: "2058", precision: "year", certainty: "exact", display: "2058" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: [],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:NOXIA:mimi_installiert",
    title: "MIMI installiert (Iteratio Prime Alpha)",
    summary:
      "Als Ersatzsystem für PROMETHEUS wird MIMI in Betrieb genommen — bewusst enger beschränkt, mit hart kodierten Grenzen. MIMI übernimmt zentrale Koordinationsaufgaben der Mars-Kolonie, ohne die volle Autonomie ihres Vorgängers.",
    location: "Mars, Kolonieverwaltung",
    characters: ["MIMI"],
    time: { start: "2065", precision: "year", certainty: "exact", display: "2065" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: [],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:NOXIA:flucht_global_array",
    title: "Die Flucht — Marek Kowalski & Dr. Kasumi Nakahara entdecken das Global Array",
    summary:
      "Auf der Flucht durch das Valles Marineris stoßen Marek Kowalski und Dr. Kasumi Nakahara auf Belege dafür, dass die spätere Axis-Kammer kein isoliertes Fundstück ist, sondern Teil eines planetaren, 432-Hz-getakteten Netzwerks unter der Marsoberfläche — eine Entdeckung, die ihre Flucht von einem persönlichen Überlebenskampf zu einem Wissen macht, das größer ist als sie beide.",
    location: "Valles Marineris, Mars",
    characters: ["Marek Kowalski", "Dr. Kasumi Nakahara"],
    time: { start: "2087-04", precision: "day", certainty: "approximate", display: "April 2087" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-NAR-0001"],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:NOXIA:axis_kuppel_entdeckt",
    title: "AXIS-Kuppel entdeckt",
    summary:
      "In Sektor Omega-7 wird in 864 m Tiefe eine halbkugelförmige Metamaterial-Shell freigelegt: Radius 18,84 m, 2.140 Sechseckwaben, umschließt einen Monolithen (Monolith-01). Die Entdeckung markiert den Beginn der 'Großen Stille' — einer Phase, in der offizielle Kommunikation über den Fund fast vollständig zum Erliegen kommt.",
    location: "Mars, Sektor Omega-7, Sektor-7-Tief (864 m Tiefe)",
    characters: [],
    time: { start: "2087-04-12", precision: "day", certainty: "exact", display: "12. April 2087" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-ARC-0003"],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:NOXIA:vierzehn_tote",
    title: "Die 14 Toten von Sektor-7",
    summary:
      "Bei einem Zwischenfall im Zusammenhang mit der Axis-Entdeckung sterben 14 Personen, darunter James Nakamura, der den Monolithen unmittelbar vor seinem Tod berührt haben soll. Die genauen Umstände bleiben klassifiziert. Unter den Hinterbliebenen entsteht später die PROMETHEUS-Bewegung.",
    location: "Mars, Sektor-7-Tief",
    characters: ["James Nakamura"],
    time: { start: "2087-04", precision: "day", certainty: "approximate", display: "April 2087" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0003"],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:NOXIA:prometheus_bewegung",
    title: "Gründung der PROMETHEUS-Bewegung",
    summary:
      "Haruka Nakamura, Witwe von James Nakamura, wird Mitbegründerin einer Bewegung, die sich gegen unkontrollierte Enthüllung gefährlichen Wissens richtet — ausdrücklich keine Anti-Wissenschafts-Gruppe, sondern eine kollektive Trauma-Antwort: 'Sie starben nicht durch die Entdeckung. Sie starben durch das Verstehen.'",
    location: "Mars, Sektor B-12",
    characters: ["Haruka Nakamura"],
    time: { start: "2088", precision: "year", certainty: "exact", display: "2088" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-BIO-0032"],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:NOXIA:signal_empfangen",
    title: "Lena Kowalski empfängt das 432-FREQ-ECHO-Signal",
    summary:
      "Während des Schüleraustauschprogramms empfängt Lena Kowalski — Tochter Marek Kowalskis — auf ihrem persönlichen Gerät eine nicht autorisierte Transmission unbekannten Ursprungs. Zusammen mit Rashid und Keiko Nakamura (Tochter Harukas und James') bildet sie die 'Triade', die die Ereignisse um AXIS und PROMETHEUS erstmals aus Kinderperspektive zusammensetzt.",
    location: "Mars, Sektor B-12",
    characters: ["Lena Kowalski", "Rashid", "Keiko Nakamura"],
    time: { start: "2091-09-03", precision: "day", certainty: "exact", display: "3. September 2091" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-BIO-0011"],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:NOXIA:generation_mars_beginnt",
    title: "Generation Mars — die Geschichte beginnt",
    summary:
      "Lena, Rashid und Keiko — die Kinder derer, die AXIS entdeckten, unter Verlust starben oder die Bewegung dagegen gründeten — beginnen, unabhängig von ihren Eltern die unterdrückte Geschichte der Mars-Kolonie zu rekonstruieren.",
    location: "Mars, Sektor B-12",
    characters: ["Lena Kowalski", "Rashid", "Keiko Nakamura"],
    time: { start: "2091", precision: "year", certainty: "exact", display: "2091" },
    universe_or_scope: "NOXIA",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: [],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "ARTF:HEXENTEICH:kette",
    title: "Die Kette vom Hexenteich",
    summary:
      "Ein Proto-Temenon, das über rund 3000 Jahre durch bloßen Gebrauch gewachsen ist — vier sichtbare Epochenschichten (Bronzezeit, Eisenzeit, Mittelalter, Reparaturschicht), kein konstruiertes Werkzeug, sondern ein sedimentiertes Muster. Resonanzklasse β. Eigenständiges Werk, nicht Teil des Baumeister-Hauptstrangs.",
    location: "Sauerland (Hexenteich-Region)",
    characters: [],
    time: { start: "-1200", end: "1650", precision: "era", certainty: "approximate", display: "~1200 BCE - 17. Jh. CE" },
    universe_or_scope: "Hexenteich",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-TEC-0035"],
    relation_refs: [],
  },
  {
    id: "ARTF:HEXENTEICH:hoer_stein",
    title: "Der Hör-Stein",
    summary:
      "Gegenstück zur Kette: geologisch-mono-epochal, einmalig durch Blitzschlag magnetisiert, ohne erkennbares Nutzungssediment. Wo die Kette Zeit dehnt, öffnet der Hör-Stein Raum — die genaue Wirkweise bleibt im Archiv offen markiert.",
    location: "Sauerland (Hexenteich-Region)",
    characters: [],
    time: { precision: "unspecified", certainty: "speculative", display: "[OFFEN]" },
    universe_or_scope: "Hexenteich",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-TEC-0036"],
    relation_refs: [],
  },
  {
    id: "EVENT:BAUMEISTER:kalgaii_erste_partitur",
    title: "Kalgaii — Die Erste Partitur",
    summary:
      "Soraya bat Zereya-Adar verfasst die erste Auflage der Dvārākā-Resonanzschrift; 25 Jahre später legt ihre Enkelin Dr. Valeda Adar eine zweite, überarbeitete Auflage vor. Die Stammlinie — Zereya → Soraya → Aviya → Valeda — macht Kalgaii zum bislang einzigen Dokument, das die Hüterinnen-Linie über vier direkte Generationen hinweg schriftlich fasst.",
    location: "unbekannt (vermutlich Marsraum, ferne Zukunft)",
    characters: ["Zereya", "Soraya bat Zereya-Adar", "Aviya", "Dr. Valeda Adar"],
    time: { start: "2155", precision: "year", certainty: "exact", display: "2155 / 2180" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-CUL-0017"],
    relation_refs: ["WORK:BAUMEISTER:lian_thorn"],
  },
  {
    id: "EVENT:BAUMEISTER:myriam_fragmente",
    title: "Myriam setzt Fragmente der Vergangenheit zusammen",
    summary:
      "Eine Archäologin des 22. Jahrhunderts rekonstruiert aus verstreuten Funden ein zusammenhängendes Bild der Baumeister-Vergangenheit — und muss erkennen, dass diese Vergangenheit nicht abgeschlossen, sondern in gewissem Sinn noch aktiv ist.",
    location: "nicht näher spezifiziert",
    characters: ["Myriam"],
    time: { start: "2150", precision: "century", certainty: "approximate", display: "~22. Jh." },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: [],
    relation_refs: ["WORK:BAUMEISTER:myriam_trilogie"],
  },
  {
    id: "EVENT:BAUMEISTER:minari_wissen",
    title: "Minari — verbotenes Wissen einer Familie",
    summary:
      "Ein koreanisches Mädchen entdeckt, dass ihre Familie über Generationen hinweg Wissen weitergegeben hat, das offiziell als verboten oder gar nicht existent gilt — eine strukturelle Parallele zur Hüterinnen-Linie, diesmal in einem anderen Zweig des Universums erzählt.",
    location: "nicht näher spezifiziert (koreanischer Kulturraum)",
    characters: [],
    time: { start: "2250", precision: "century", certainty: "approximate", display: "~23. Jh." },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: [],
    relation_refs: ["WORK:BAUMEISTER:minari"],
  },
  {
    id: "EVENT:BAUMEISTER:lain_thorn_kragoss",
    title: "Lain Thorn wartet auf K'ragoss",
    summary:
      "Lain Thorn, letzter Wächter auf dem roten Wüstenplaneten K'ragoss (in der Überlieferung auch 'die siebte Realität' genannt), wartet über Jahrzehnte auf ein Echo der Baumeister. Verbunden ist er über seine Frau Elara — eine Nachfahrin Amritas — mit der Hüterinnen-Linie, ohne dass er selbst deren volle Tragweite zunächst kennt.",
    location: "K'ragoss (roter Wüstenplanet)",
    characters: ["Lain Thorn", "Elara"],
    time: { start: "2150", precision: "half-century", certainty: "approximate", display: "~2150-2200+" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0003"],
    relation_refs: ["WORK:BAUMEISTER:lian_thorn"],
  },
  {
    id: "EVENT:BAUMEISTER:zereya_trifft_thorn",
    title: "Zereya trifft Lain Thorn auf K'ragoss",
    summary:
      "Die letzte bekannte Trägerin der Hüterinnen-Linie erreicht K'ragoss und trifft dort auf Lain Thorn. Das Treffen verbindet zwei bis dahin getrennte Erzählstränge — die durchgehende Hüterinnen-Überlieferung und die isolierte Wächterschaft — zum ersten Mal direkt.",
    location: "K'ragoss",
    characters: ["Zereya", "Lain Thorn"],
    time: { start: "2150", precision: "half-century", certainty: "approximate", display: "~2150-2200+" },
    universe_or_scope: "Baumeister",
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-HIS-0003"],
    relation_refs: ["WORK:BAUMEISTER:lian_thorn"],
  },
  {
    id: "EVENT:BAUMEISTER:ins_offene",
    title: "Ins Offene — Ori-Kol",
    summary:
      "Die Dyade Soma Retep und Cydur überschreitet als vermutlich letzter Akt der Baumeister-Spirale eine Schwelle, an der die bisherige Leserichtung des Wissens sich umkehrt: Statt Dogmen wird 'Ori-Kol' übergeben — eine fraktale Aussaat neuer, noch unbezifferter Universen, statt eines abgeschlossenen Kanons.",
    location: "unbekannt",
    characters: ["Soma Retep", "Cydur"],
    time: { start: "2500", precision: "century", certainty: "speculative", display: "~2500+" },
    universe_or_scope: "Baumeister",
    canonicality: "provisional",
    epistemic_status: "fictional",
    source_refs: ["OTA-FIC-0035"],
    relation_refs: [],
  },
  {
    id: "EVENT:UTOPIA_MARS:zhurong_landung",
    title: "Zhurong landet in Utopia Planitia",
    summary:
      "Reales Ereignis [R]. Tianwen-1 setzt den Rover Zhurong am 15. Mai 2021 im südlichen Utopia Planitia ab; die bestimmte reale Landestelle liegt bei etwa 25,066° N / 109,925° E. Sie ist ein chinesischer Ankerpunkt und ausdrücklich nicht der spätere Siedlungsstandort. Der OTA-Stand zieht die Grenze klar: 'Zhurong ist real. Kaiwu in Utopia Planitia ist NOXIA.'",
    location: "Utopia Planitia, Mars (reale südliche Landestelle)",
    characters: [],
    time: { start: "2021-05-15", precision: "day", certainty: "exact", display: "15. Mai 2021" },
    universe_or_scope: UTOPIA_MARS_SCOPE,
    canonicality: "canonical",
    epistemic_status: "established",
    source_refs: ["OTA-HIS-0004-2021-DE", "OTA-SCI-0090-2026-DE"],
    relation_refs: [],
  },
  {
    id: "EVENT:UTOPIA_MARS:space_science_roadmap_2050",
    title: "Nationale Space-Science-Roadmap bis 2050",
    summary:
      "Reales Ereignis [R]. China veröffentlicht im Oktober 2024 (CAS/CNSA/CMSP) den nationalen Space-Science-Plan bis 2050: Mars-Biosignaturen sind für ca. 2028–2035 vorgesehen, bemannte Tiefraum-Erkundung für 2036–2050. Das OTA hält ausdrücklich fest, dass daraus kein real beschlossener Mars-Städtebau folgt. Die Utopia-/Kaiwu-Linie ist fiktionale Fortschreibung [F/P].",
    location: "China (nationale Planung)",
    characters: [],
    time: { start: "2024", precision: "year", certainty: "exact", display: "Oktober 2024" },
    universe_or_scope: UTOPIA_MARS_SCOPE,
    canonicality: "canonical",
    epistemic_status: "established",
    source_refs: ["OTA-HIS-0004-2021-DE"],
    relation_refs: [],
  },
  {
    id: "EVENT:UTOPIA_MARS:robotische_vorbereitung",
    title: "Robotische Vorbereitung des Kaiwu-Standorts",
    summary:
      "Fiktionale, vorläufige Phase [F/P]. In den 2070er-Jahren wächst am zweiten Industrie- und Ressourcenstandort im Utopia Planitia die Komponentenfertigung; ca. 2072–2075 bereiten robotische Systeme den späteren Kaiwu-Standort vor (Aufbaukohorte 2072–2080, OTA-CHR-0001-2072-DE). Die Arbeitsregion ist der westlich-zentrale Utopia-Planitia-Korridor; die endgültige Standortkoordinate bleibt [OFFEN] und wird nicht als kanonische Stadtkoordinate geführt. Die industrielle Achse von Reparatur zu reproduktionsfähiger Infrastruktur ist in OTA-HIS-0005-2050-DE als eigener Strang dokumentiert.",
    location: "Utopia Planitia, Mars (Arbeitskorridor; Standort [OFFEN])",
    characters: [],
    time: { start: "2072", end: "2075", precision: "decade", certainty: "approximate", display: "ca. 2072–2075" },
    universe_or_scope: UTOPIA_MARS_SCOPE,
    canonicality: "provisional",
    epistemic_status: "fictional",
    source_refs: [
      "OTA-HIS-0004-2021-DE",
      "OTA-HIS-0005-2050-DE",
      "OTA-SCI-0090-2026-DE",
      "OTA-CHR-0001-2072-DE",
    ],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:UTOPIA_MARS:erste_besatzung",
    title: "Erste permanente Besatzung in Kaiwu",
    summary:
      "Fiktionale, vorläufige Phase [F/P]. Ca. 2076/77 beginnt die erste permanente Besatzung des Kaiwu-Standorts; OTA-META-0004-2076-DE nennt eine provisorische Größenordnung von 40–60 Personen, keine Zensuswerte. Nach OTA-CHR-0001-2072-DE übernimmt Chen Yuxin ca. 2076/77 die erste permanente Stationsleitung [P]; die dokumentierten frühen Figuren sind ausdrücklich keine Gründergruppe. Der Name Kaiwu folgt auf frühere technische Projektbezeichnungen; Gründungsdatum im Rechtssinn, Einwohnerzahlen und Rechtsform bleiben [OFFEN].",
    location: "Kaiwu, Utopia Planitia, Mars (Standort [OFFEN])",
    characters: ["Chen Yuxin"],
    time: { start: "2076", end: "2077", precision: "year", certainty: "approximate", display: "ca. 2076/77" },
    universe_or_scope: UTOPIA_MARS_SCOPE,
    canonicality: "provisional",
    epistemic_status: "fictional",
    source_refs: [
      "OTA-META-0004-2076-DE",
      "OTA-CHR-0001-2072-DE",
      "OTA-SOC-0001-2076-DE",
      "OTA-HIS-0004-2021-DE",
    ],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:UTOPIA_MARS:maryem_hamid_geburt",
    title: "Maryem Hamid wird in Kaiwu geboren",
    summary:
      "Kanonisches Ereignis [K]. Maryem Hamid wird am 03.12.2080 in Kaiwu, Utopia Planitia, Mars geboren (OTA-CHR-0001-2072-DE; OTA-META-0004-2076-DE v1.1). Die Geburt ist ausdrücklich kein Beleg dafür, dass Kaiwu 2080 bereits eine große Stadt ist. Eltern- und Umfeldangaben bleiben [P]. Die frühere Arbeitszuordnung zu einer 'Utopia-Siedlung' ist mit der Kanonisierung des Namens Kaiwu überholt.",
    location: "Kaiwu, Utopia Planitia, Mars",
    characters: ["Maryem Hamid"],
    time: { start: "2080-12-03", precision: "day", certainty: "exact", display: "3. Dezember 2080" },
    universe_or_scope: UTOPIA_MARS_SCOPE,
    canonicality: "canonical",
    epistemic_status: "fictional",
    source_refs: ["OTA-META-0004-2076-DE", "OTA-CHR-0001-2072-DE", "OTA-SOC-0001-2076-DE"],
    relation_refs: ["CHAR:NOXIA:maryem_hamid", "WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:UTOPIA_MARS:grosse_stille_kompetenztest",
    title: "Große Stille als Kompetenz- und Resilienztest",
    summary:
      "Vorläufige Deutung [F/P], nicht kanonisch. Die Große Stille von 2087 (42 Tage und 12 Stunden ohne Erd-Rückkanal) wirkt als praktischer Kompetenz- und Resilienztest: Zuständigkeit wandert dorthin, wo Entscheidungen tatsächlich getroffen werden können. Kanonisch ist die Regel, dass 2087 kein Unabhängigkeitskrieg und keine automatische Staatsgründung ist; die Chronologie selbst bleibt bei OTA-HIS-0003-2087-DE. Formale Rechtsgrundlage, Vertretung der Siedlungen und konkrete Notfallbefugnisse bleiben [OFFEN].",
    location: "Mars (marsweit; Kaiwu und Iterius Prime)",
    characters: [],
    time: { start: "2087", precision: "year", certainty: "exact", display: "2087" },
    universe_or_scope: UTOPIA_MARS_SCOPE,
    canonicality: "provisional",
    epistemic_status: "speculative",
    source_refs: ["OTA-ORG-0008-2087-DE", "OTA-HIS-0004-2021-DE"],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
  {
    id: "EVENT:UTOPIA_MARS:zweiter_marsknoten",
    title: "Kaiwu als etablierter zweiter Marsknoten",
    summary:
      "Fiktionale, vorläufige Phase [F/P]. Bis 2091 ist Kaiwu keine chinesische Außenstation mit Gästen mehr, sondern eine Marsstadt chinesischer Herkunft und internationaler Zusammensetzung (OTA-SOC-0001-2076-DE). OTA-META-0004-2076-DE nennt als provisorischen Korridor ca. 500–800 Einwohner; exakte Zahlen bleiben [OFFEN]. Der zweite Marsknoten trägt Wasser, Ressourcen, Fertigung, Robotik und schwere Logistik und ist mit Iterius Prime systemisch verzahnt.",
    location: "Kaiwu, Utopia Planitia, Mars",
    characters: [],
    time: { start: "2091", precision: "year", certainty: "exact", display: "2091" },
    universe_or_scope: UTOPIA_MARS_SCOPE,
    canonicality: "provisional",
    epistemic_status: "fictional",
    source_refs: ["OTA-META-0004-2076-DE", "OTA-SOC-0001-2076-DE", "OTA-HIS-0004-2021-DE"],
    relation_refs: ["WORK:NOXIA:generation_mars"],
  },
];

export const PROJECTION_SOURCE = "local-seed-v0.2.0";

export const PROJECTION_NOTE =
  "Seed-Projektion gemäß ECO-ARC-0018-2026-DE. Nicht kanonisch; Quelle der Inhalte bleiben die OTA-/KG-Dokumente. Ersetzt später einen KG-Export. v0.2.0: Utopia-/Mars-Industrie-Strang (EXT-OTA-ECO-20260911, OTA PR #60) als eigener Scope 'Utopia/Mars' aufgenommen.";

export const PROJECTION_CAVEATS: string[] = [
  "Reale Ereignisse ([R] → epistemic_status 'established') und fiktionale Fortschreibung ([K]/[P]/[F/P] → 'fictional'/'speculative') bleiben getrennt; reale Anker wie Zhurong sind nicht Teil der NOXIA-Fiktion.",
  "Alle vorläufigen Phasen werden mit canonicality 'provisional' geführt und sind damit filterbar von Kanon getrennt; kanonisch sind hier nur die realen Anker und Maryem Hamids Geburt 2080 [K].",
  "Der in OTA-SCI-0090-2026-DE nur als Suchzentrum geführte Koordinatenbereich ist [F/P] und wird nicht als kanonische Stadtkoordinate projiziert; die Projektion enthält keine Siedlungskoordinaten.",
  "Quellenstand: OTA-META-0004-2076-DE v1.1 (14.09.2026) setzt den Siedlungsnamen Kaiwu (开物) als [K]; die frühere Task-Annahme eines offenen Stadtnamens und der Arbeitsname 'Utopia-Siedlung' sind damit überholt. Offen bleiben exakte Koordinate, Einwohnerzahlen, Rechtsform und Gründungsdatum im Rechtssinn.",
];
