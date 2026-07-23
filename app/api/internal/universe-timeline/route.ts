import { NextRequest, NextResponse } from "next/server";

// Server-only. Diese Datei wird nie ins Client-Bundle aufgenommen.
// Zugriffsschutz: einfacher geteilter Code über Header, serverseitig geprüft.
// INTERNAL_ACCESS_TOKEN in den Vercel Environment Variables setzen.
//
// Datenmodell folgt dem Vertrag aus EXT-ECO-KG-20260722-001 / ECO-ARC-0018-2026-DE:
// id, title, summary, time.{start,end,precision,certainty,display},
// universe_or_scope, canonicality, epistemic_status, source_refs, relation_refs
// Erweitert (v0.1.1) um location und characters — beides optionale Anreicherung,
// verändert den Kernvertrag nicht, macht die Ansicht aber lesbarer.
//
// v0.1: lokale typisierte Seed-Projektion — ausdrücklich NICHT kanonisch.
// Spätere Version ersetzt dies durch einen Export aus kueper-knowledge-graph
// (kg_entities WHERE type IN ('Event','Artifact') AND visibility IN ('private','restricted')).

type UniverseEvent = {
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

const SEED_EVENTS: UniverseEvent[] = [
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
];

export async function GET(req: NextRequest) {
  const token = req.headers.get("x-internal-token");
  const expected = process.env.INTERNAL_ACCESS_TOKEN;

  if (!expected || token !== expected) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  return NextResponse.json({
    generated_at: new Date().toISOString(),
    source: "local-seed-v0.1.1",
    canonical: false,
    note: "Seed-Projektion gemäß ECO-ARC-0018-2026-DE. Nicht kanonisch. Ersetzt späteren KG-Export. v0.1.1: erweitert um location/characters und ausführlichere summary-Texte.",
    events: SEED_EVENTS,
  });
}
