"""Konstanten der IDA*-Demo: Raster-Geometrie (wortgleich zur A*-Demo), Regler, Beschriftungen (Messwerte und
Presets folgen nach der Messreihe).

Regler-Bereiche aus der Vorab-Messreihe (5 Seeds, Obergrenze 1 Mio. Expansionen): auf dem offenen Feld reißt die
Obergrenze schon bei Rastergröße 10 (4 von 5 Instanzen), bei Größe 12 dominieren abgebrochene Läufe - deshalb
endet der Größen-Regler bei 12 und die Sweeps bei 10; Größe 8 löst noch in Bruchteilen einer Sekunde und ist die
Voreinstellung."""

AREA = 100.0                     # Kantenlänge des Gebiets in km
JITTER = 0.35                    # Lageabweichung je Zelle, Anteil des Zellenabstands

SIDE_MIN, SIDE_MAX, DEFAULT_SIDE, SIDE_STEP = 5, 12, 8, 1      # Rastergröße (Zellen je Kante)
OBSTACLE_MIN, OBSTACLE_MAX, DEFAULT_OBSTACLE, OBSTACLE_STEP = 0, 40, 15, 5   # Prozent gesperrte Zellen
SEED_MAX = 999999
DEFAULT_SEED = 35
CAPS = (10000, 100000, 300000, 1000000)      # Expansions-Obergrenze (Sicherheitsnetz gegen den Blow-up)
DEFAULT_CAP = 1000000                        # MUSS Mitglied von CAPS sein (st.select_slider snappt sonst still)

SWEEP_SEEDS = tuple(range(100000, 100005))
SCALING_SIDES = (5, 6, 7, 8, 9, 10)
OBSTACLE_SWEEP = (0, 10, 20, 30, 40)

# --- Gemessene Werte (MEDIAN über 5 feste Sweep-Instanzen, Seeds 100000-100004; Rastergröße 8, Hindernisdichte 15 %,
# --- Obergrenze 1 Mio., sofern nicht anders angegeben; 2026-09-23, alle Werte über ev.run_config/ev.sweep
# --- nachgerechnet, s. tests/test_claims.py). Faktoren sind stark schief verteilt - deshalb Median, nicht Mittelwert.
# ZENTRALE FRAGE - was kostet der Speichergewinn? Speicher: IDA* hält nur den Pfad (Tiefe 15), A* im Mittel 47
#   Knoten - Verhältnis 3.0x. Zeit: IDA* expandiert im Median 705x so viele Knoten wie A* (231 Iterationen; Spanne
#   325 bis 1126 über die Instanzen). Die Vorab-Hypothese "Speichergewinn zu akzeptablen Zeitkosten" ist
#   WIDERLEGT: rund 3x weniger Speicher für rund 700x mehr Expansionen.
# WARUM (gemessen): IDA* expandiert (fast) DIESELBEN Knoten wie A* (Knotenmengen-Verhältnis 1.0) - nur je Knoten
#   im Mittel ~700-mal. Die letzte Iteration macht nur 0.7 % aller Expansionen aus: der Aufwand entsteht durch die
#   Wiederholungen über 231 Iterationen (A* expandiert nur 38 Knoten). Zwei aus der Literatur bekannte Ursachen -
#   reelle Kantengewichte (viele verschiedene Schwellen) und Transpositionen im Raster (viele Wege zum selben Knoten,
#   ohne Closed-Set nicht erkennbar) - werden hier NICHT einzeln isoliert; gemessen ist nur das Ergebnis.
# HINDERNISDICHTE-SWEEP (0/10/20/30/40 %): Faktor 917/1771/611/281/71, Iterationen 281/408/200/132/61, Speicher-
#   Verhältnis 3.7/3.4/3.0/2.5/2.0x - der Faktor sinkt bei dichten Hindernissen deutlich, steigt aber von 0 auf 10 %
#   zunächst - kein sauber monotoner Verlauf (5 Instanzen). Warum, wird hier nicht getrennt untersucht.
# GRÖSSEN-SWEEP (5/6/7/8/9/10, 15 % Hindernisse): Faktor 28/55/369/705/507/1771 (bei Größe 10 2 von 5 Läufen
#   abgebrochen, der Faktor dort nur eine UNTERGRENZE; nur gelöste Läufe: 477 - sinkt scheinbar, weil die schwersten
#   Instanzen herausfallen), Speicher-Verhältnis wächst nur langsam 2.3/2.5/2.6/3.0/3.3/3.7x. Der Speichervorteil
#   wächst ungefähr linear mit der Größe, der Zeitpreis um Größenordnungen.
# OFFENES FELD (0 % Hindernisse): Anteil abgebrochener Läufe je Größe 5..10: 0/0/0/0/20/80 % - dort reißt die
#   Obergrenze zuerst (Größe 10: 4 von 5 Läufen brechen bei 1 Mio. Expansionen ab).
# HANDGEBAUTE FALLE: A* 7 Expansionen (8 gespeicherte Knoten), IDA* 22 Expansionen in 6 Iterationen bei Tiefe 4 -
#   auch hier optimal (wie A*, anders als Greedy Best-First), Faktor 3.1.

PRESETS = {
    "Standardfall (Voreinstellung)": {"network": "grid", "side": 8, "obstacle_pct": 15, "seed": 35, "cap": 1000000},
    "Handgebaute Heuristik-Falle": {"network": "trap", "side": 8, "obstacle_pct": 15, "seed": 35, "cap": 1000000},
    "Offenes Feld (viele Transpositionen)": {"network": "grid", "side": 8, "obstacle_pct": 0, "seed": 35, "cap": 1000000},
    "Viele Hindernisse (40 %)": {"network": "grid", "side": 8, "obstacle_pct": 40, "seed": 35, "cap": 1000000},
    "Größe 10 (Obergrenze wird knapp)": {"network": "grid", "side": 10, "obstacle_pct": 15, "seed": 35, "cap": 1000000},
    "Kleine Obergrenze (Abbruch)": {"network": "grid", "side": 8, "obstacle_pct": 15, "seed": 35, "cap": 10000},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Rastergröße 8, 15 % Hindernisse: IDA\\* findet denselben optimalen Pfad wie A\\*, hält aber nur den Pfad im Speicher (Tiefe 15 gegen im Mittel 47 gespeicherte Knoten, 3.0x) - und braucht dafür im Median 705x so viele Expansionen.",
    "Handgebaute Heuristik-Falle": "Der 8-Knoten-Graph aus der Wurzel: IDA\\* löst ihn optimal (wie A\\*, anders als Greedy Best-First) - mit 22 statt 7 Expansionen in 6 Iterationen bei Tiefe 4.",
    "Offenes Feld (viele Transpositionen)": "Keine Hindernisse: viele gleichwertige Wege zum selben Knoten, die IDA\\* ohne Closed-Set nicht erkennt - es expandiert im Median 917x so viel wie A\\*.",
    "Viele Hindernisse (40 %)": "40 % Hindernisse: der Faktor sinkt im Median auf 71x (Iterationen 61 statt 231), der Speichervorteil auf 2.0x - dichte Hindernisse machen die Suche deutlich billiger.",
    "Größe 10 (Obergrenze wird knapp)": "Rastergröße 10: hier reißt bei 2 von 5 Instanzen bereits die Obergrenze von 1 Mio. Expansionen - diese Instanz (Seed 35) ist noch lösbar, mit 150 734 Expansionen gegen 56 bei A\\*.",
    "Kleine Obergrenze (Abbruch)": "Dieselbe Instanz wie der Standardfall, aber Obergrenze 10 000: IDA\\* bricht ab, ohne einen Pfad zu behaupten - der Faktor ist dann nur noch eine Untergrenze.",
}
# Beobachtete Spannweite des Expansions-Faktors (bei abgebrochenen Läufen Untergrenze) über die 5 festen Sweep-
# Instanzen (mit Sicherheitsabstand). Vollständig deterministisch - die Spannweite ist stark, weil Faktoren über
# Größenordnungen streuen. Die Falle ist ein fester Graph (22 / 7 = 3.14).
PRESET_EXPECTED_BANDS = {
    "Standardfall (Voreinstellung)": (200.0, 1600.0),
    "Handgebaute Heuristik-Falle": (3.0, 3.3),
    "Offenes Feld (viele Transpositionen)": (100.0, 15000.0),
    "Viele Hindernisse (40 %)": (20.0, 1500.0),
    "Größe 10 (Obergrenze wird knapp)": (50.0, 30000.0),
    "Kleine Obergrenze (Abbruch)": (150.0, 400.0),
}
