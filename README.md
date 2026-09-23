# IDA* – Speicher sparen, aber zu welchem Preis? – Streamlit-Demo

Drittes Stück der **Heuristische-Baumsuche-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning" - die Antwort auf die Schwäche, die [astar-demo](../astar-demo) selbst offen benennt: **A\*** ist optimal, hält aber die gesamte Grenzmenge im Speicher. **IDA\*** (Iterative Deepening A\*, Korf 1985) ersetzt sie durch **wiederholte, tiefenbegrenzte Tiefensuchen** mit einer Schwelle auf f = g + h; gespeichert wird nur der aktuelle Pfad. Der Preis: Knoten werden über die Iterationen (und ohne Closed-Set über verschiedene Wege dorthin) **immer wieder** expandiert.

**Einordnung in die Linie:** derselbe Graph, dieselbe Instanz, derselbe Suchkern wie in [astar-demo](../astar-demo) (dort schon korrektheitsgeprüft); A\* dient hier als Vergleichsgröße. Neu ist `ida_star` mit einer Expansions-Obergrenze als Sicherheitsnetz.

```
Greedy Best-First Search (Wurzel)                                                          [gebaut]
 ├─ A* → Iterative Deepening A* (IDA*)                              [A* gebaut, IDA* = DIESES STÜCK]
 ├─ Beam Search → {Diverse Beam Search, Monobeam}                                          [nicht gebaut]
 └─ Monte Carlo Tree Search (MCTS)                                                         [nicht gebaut]
Beam Search + A* → Beam Stack Search (Konvergenzpunkt)                                     [nicht gebaut]
```

Ergebnis in Kürze: IDA\* findet ausnahmslos denselben optimalen Pfad wie A\* - aber die Vorab-Hypothese "**der Speichergewinn kommt zu akzeptablen Zeitkosten**" ist **widerlegt**: im Standardfall rund **3x weniger Speicher** (Pfadtiefe 15 gegen im Mittel 47 gespeicherte Knoten) für rund **700x mehr Expansionen** (Median; 231 Iterationen). Der Zeitpreis wächst mit der Rastergröße um Größenordnungen, der Speichervorteil nur langsam - auf dem offenen Feld reißt schon bei Größe 10 die Obergrenze von 1 Mio. Expansionen (4 von 5 Instanzen).

| Frage | Ergebnis (Rastergröße 8, Hindernisdichte 15 %, Obergrenze 1 Mio., sofern nicht anders angegeben; **Median** über 5 feste Instanzen, Seeds 100000–100004; vollständig deterministisch) |
|---|---|
| **Ist IDA\* optimal?** | ✅ derselbe Pfadwert wie A\* und UCS in jedem nicht abgebrochenen Lauf, auch gegen Brute-Force und auf der handgebauten Falle |
| **Wie viel Speicher spart es?** | **3.0x** (IDA\* Tiefe 15, A\* im Mittel 47 gespeicherte Knoten); wächst langsam mit der Größe: 2.3/2.5/2.6/3.0/3.3/3.7x bei Größe 5–10 |
| **Was kostet das an Zeit?** | ⚠️ Expansions-Faktor **705x** ggü. A\* (Spanne 325–1126 über die Instanzen), **231 Iterationen** |
| **Woran liegt es (gemessen)?** | IDA\* expandiert (fast) **dieselben Knoten** wie A\* (Knotenmengen-Verhältnis 1.0), nur je Knoten im Mittel ~700-mal; die letzte Iteration macht nur **0.7 %** aller Expansionen aus |
| **Hindernisdichte-Sweep (0/10/20/30/40 %)** | Faktor **917/1771/611/281/71x**, Iterationen 281/408/200/132/61, Speicher-Verhältnis 3.7/3.4/3.0/2.5/2.0x - sinkt bei dichten Hindernissen deutlich, aber nicht sauber monoton (0 → 10 % steigt er) |
| **Größen-Sweep (5/6/7/8/9/10)** | Faktor **28/55/369/705/507/1771x** - bei Größe 10 sind 2 von 5 Läufen abgebrochen, der Faktor dort nur eine **Untergrenze** (nur gelöste Läufe: 477 - scheinbar sinkend, weil die schwersten Instanzen herausfallen) |
| **Offenes Feld (0 %): abgebrochene Läufe je Größe 5…10** | **0/0/0/0/20/80 %** - dort reißt die Obergrenze zuerst |
| **Handgebaute Heuristik-Falle** | ✅ optimal (wie A\*, anders als Greedy Best-First): IDA\* 22 Expansionen in 6 Iterationen bei Tiefe 4, A\* 7 Expansionen (8 gespeicherte Knoten) |

## Was die Demo zeigt

1. **IDA\* in Aktion** (Schritt-Slider): **Instanz** → **Wiederholungen** (Karte: Farbe = wie oft ein Knoten expandiert wurde, Ring = von A\* expandiert; Balken: Expansionen je Iteration, die Schwelle steigt von h(Start) bis zu den optimalen Kosten) → **Ergebnis** (beide Pfade überlagert; bei Abbruch ohne Pfadbehauptung).
2. **Was der Speichergewinn kostet:** Speicher-Verhältnis, Expansions-Faktor (bei Abbruch als "≥" gekennzeichnet), Iterationen, Status.
3. **📐 Sweeps** über Hindernisdichte und Rastergröße (Median, Min-Max-Band, logarithmische Achse), wählbare Kennzahl (Faktor / Speicher-Verhältnis / Iterationen / Anteil abgebrochener Läufe), 5 feste Instanzen ab Seed 100000.
4. **🚧 Grenzen:** Tabelle "Annahme – was passiert – wer setzt an".

Regler: Instanz (Raster / handgebaute Heuristik-Falle), Rastergröße (5–12), Hindernisdichte (0–40 %), **Expansions-Obergrenze** (10 000 bis 1 Mio.), Seed der Instanz (+ 🎲). Kein Zufall im Kern, kein Ketten-Seed - vollständig deterministisch.

## Messwerte der Presets (einzelne Instanz, Seed 35)

| Preset | Expansions-Faktor | Speicher-Verhältnis | Iterationen | Expansionen IDA\* / A\* |
|---|---|---|---|---|
| Standardfall (Voreinstellung) | 1110x | 3.5x | 316 | 49 956 / 45 |
| Handgebaute Heuristik-Falle | 3.1x | 2.0x | 6 | 22 / 7 |
| Offenes Feld (viele Transpositionen) | 835x | 3.8x | 271 | 36 756 / 44 |
| Viele Hindernisse (40 %) | 173x | 2.4x | 108 | 5 884 / 34 |
| Größe 10 (Obergrenze wird knapp) | 2692x | 3.8x | 549 | 150 734 / 56 |
| Kleine Obergrenze (Abbruch) | ≥ 222x | - | 141 | 10 000 (abgebrochen) / 45 |

Die einzelne Instanz (Seed 35) weicht von den Sweep-Medianen ab (z. B. Standardfall 1110x gegen 705x) - die Mediane oben sind die belastbaren Zahlen; jedes Preset prüft sich zusätzlich über die 5 festen Sweep-Instanzen gegen eine gemessene Spannweite (siehe `tests/test_presets.py`).

## Modell und Verfahren

- **Instanz und Graph** (`idastar_scenario.py`, `idastar_graph.py`): wortgleiche Kopien aus [astar-demo](../astar-demo) - gestörtes Raster mit Hindernissen, Kantengewicht = echter euklidischer Abstand (macht die Heuristik zulässig), plus die handgebaute 8-Knoten-Falle.
- **Suchkern** (`idastar_algorithm.py`): der `_search`-Kern samt `greedy_best_first`/`uniform_cost_search`/`a_star` aus der A\*-Demo, ergänzt um das Feld `stored` (A\*: Zahl der gespeicherten Knoten). NEU `ida_star`: Schwelle T = h(Start); iterative Tiefensuche über den aktuellen Pfad, Knoten mit f = g + h > T werden abgeschnitten und liefern die nächste Schwelle (das kleinste abgeschnittene f); **kein Closed-Set** - Zyklen werden nur gegen den eigenen Pfad geprüft; Speicher = maximale Pfadtiefe; Nachbarreihenfolge fest (deterministisch); bei Erreichen der Expansions-Obergrenze bricht die Suche ab, setzt `capped` und behauptet **keinen** Pfad.
- **Auswertung** (`idastar_evaluation.py`): Expansions-Faktor (IDA\* / A\*), Speicher-Verhältnis (A\*-gespeicherte Knoten / IDA\*-Tiefe), Iterationen, Knotenmengen-Verhältnis, Mehrfachheit, Anteil der letzten Iteration; Sweeps mit **Median und Min-Max-Spanne** (Faktoren sind stark schief verteilt); abgebrochene Läufe werden **getrennt ausgewiesen**, nie still in Mittelwerte gemischt.

## Was nicht funktioniert hat / Grenzen

- **Vorab-Hypothese "IDA\* spart den Speicher zu akzeptablen Zeitkosten" - WIDERLEGT.** Rund 3x weniger Speicher gegen rund 700x mehr Expansionen im Median; auf dem offenen Feld ab Größe 10 kippt es in Abbrüche.
- **Die Ursachen sind nicht isoliert.** Aus der Literatur sind zwei bekannt: reelle Kantengewichte (viele verschiedene Schwellen, also viele Iterationen) und Transpositionen im Raster (viele Wege zum selben Knoten, ohne Closed-Set nicht erkennbar). Hier gemessen ist nur das Ergebnis - dasselbe Knotenmengen-Verhältnis, ~700 Expansionen je Knoten, 231 Iterationen - nicht, wie viel davon auf welche Ursache entfällt. Ebenso wird nicht untersucht, warum der Faktor von 0 auf 10 % Hindernisse zunächst steigt.
- **Die Faktoren sind schief verteilt**: Median statt Mittelwert; bei abgebrochenen Läufen ist der Faktor nur eine Untergrenze, und Mediane über nur die gelösten Läufe täuschen (die schwersten Instanzen fallen heraus) - beides ist in den Sweeps ausgewiesen.
- **Nicht gebaut:** Transpositionstabelle (würde Speicher gegen Wiederholung tauschen und damit den Kern der Frage verändern), Varianten für reell bewertete Kosten (z. B. IDA\*_CR).
- **Andere Wege, den Speicher zu begrenzen** sind die noch nicht gebauten Geschwister: Beam Search und Monte Carlo Tree Search.
- **Synthetische Instanzen:** ein Raster mit Jitter, Vierer-Nachbarschaft, keine Zeitfenster, keine gerichteten Kanten; Größen bis 12 im Regler. Andere Graphstrukturen wurden nicht gemessen.

## Verifikation

- **IDA\* findet IMMER denselben Pfadwert wie A\*/UCS**: über 30 Zufallsinstanzen UND gegen vollständige Enumeration aller einfachen Pfade (Brute-Force) auf kleinen Instanzen kreuzgeprüft.
- **IDA\* löst die handgebaute Falle**, an der Greedy Best-First scheitert.
- **Gültiger Pfad**: zusammenhängend, Start bis Ziel, ohne Wiederholung, Kosten gegen unabhängige Neuberechnung geprüft; deterministisch.
- **Schwellen-Folge**: beginnt bei h(Start), steigt streng, endet bei den optimalen Kosten; Expansionen je Iteration summieren sich zur Gesamtzahl.
- **Zwei Sonderfälle direkt nachgewiesen**: ein Kettengraph (Baum ohne Transpositionen, perfekte Heuristik) braucht genau eine Iteration; mit Einheitsgewichten und h ≡ 0 reproduziert IDA\* das klassische Iterative-Deepening-DFS (Schwellen 0, 1, 2, 3).
- **Obergrenze**: bricht exakt bei der Grenze ab, behauptet keinen Pfad; ein nicht erreichbares Ziel wird ohne Abbruch gemeldet.
- **Alle Zahlen der App-Texte sind als Tests hinterlegt**, über dieselben Auswertungsfunktionen wie die App selbst (`ev.run_config`/`ev.sweep`), NIE über ein Ad-hoc-Skript; AppTest-Rauchtests (Voreinstellung, jedes Preset, jeder Schritt, beide Instanz-Typen, abgebrochene Läufe, Extremwerte, Würfel, Permalink-Grenzen, Instanzwechsel, ausgeblendete Regler bei der Falle, Sweeps auf Abruf, Footer). 207 Tests.

Literatur: Korf, R. E. (1985). *Depth-first iterative-deepening: An optimal admissible tree search.* Artificial Intelligence, 27(1), 97-109.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: Instanz-Umschalter, Schritte, Ergebnis, 📐 Sweeps, 🚧 Grenzen, Mathe |
| `idastar_algorithm.py` | Gemeinsamer Suchkern (Kopie aus der A\*-Demo, plus `stored`) + `ida_star` |
| `idastar_graph.py`, `idastar_scenario.py` | Graph, Raster- und Fallen-Instanz (Kopie) |
| `idastar_constants.py` | Konstanten, Presets, gemessene Werte |
| `idastar_evaluation.py` | Faktor, Speicher-Verhältnis, Iterationen, Sweeps mit Median/Spanne |
| `idastar_presets.py`, `idastar_visualization.py` | Permalink/Presets, Plotly-Figuren (Mehrfachheits-Karte, Iterationen-Balken, Pfade, Sweeps) |
| `tests/` | Zentrale Korrektheitskette, Szenario/Auswertung, Aussagen der App, Presets, AppTest |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
