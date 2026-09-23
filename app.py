"""IDA* - Speicher sparen, aber zu welchem Preis? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Heuristische-Baumsuche-Linie der "Konzepte"-Reihe, Fortsetzung von A* (astar-demo): A* ist
optimal, hält aber die gesamte Grenzmenge im Speicher. IDA* (Iterative Deepening A*) ersetzt sie durch
wiederholte, auf f = g + h begrenzte Tiefensuchen - Speicher wächst nur mit der Pfadlänge. Der Preis: Knoten werden
immer wieder expandiert. Wie hoch ist er auf einem Raster, das voller Transpositionen steckt? Muss gemessen
werden, nicht angenommen.

Lauffähig mit: streamlit run app.py
"""

from dataclasses import replace

import streamlit as st

import idastar_constants as C
from idastar_evaluation import SWEEP_LABELS, Settings, analyse, sweep
from idastar_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from idastar_visualization import (
    ASTAR_COLOR,
    IDA_COLOR,
    build_capped_share,
    build_instance,
    build_iterations_bar,
    build_multiplicity,
    build_paths,
    build_sweep,
)

st.set_page_config(page_title="IDA* – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(param, base):
    return sweep(param, base)


def _fmt_int(x):
    return f"{int(round(x)):,}".replace(",", ".")


st.title("🪜 IDA* – Speicher sparen, aber zu welchem Preis?")
st.markdown(
    """
**Drittes Stück der Heuristische-Baumsuche-Linie** - die Fortsetzung von A\\*. A\\* ist optimal, hält aber die
gesamte Grenzmenge im Speicher - auf großen Graphen das eigentliche Problem.

**IDA\\*** (Iterative Deepening A\\*) ersetzt sie durch **wiederholte Tiefensuchen**: eine Schwelle auf
**f = g + h**, alles darüber wird abgeschnitten, die kleinste abgeschnittene f-Kosten werden die nächste Schwelle.
Gespeichert wird nur der aktuelle **Pfad**. Der Preis: Knoten werden über die Iterationen (und über verschiedene
Wege zum selben Knoten) **immer wieder** expandiert. Wie hoch ist er hier, auf einem Raster voller Transpositionen?
"""
)
st.caption(
    "Setzt direkt auf [astar-demo](https://github.com/sebastian-hanisch/astar-demo) auf (derselbe Graph, dieselbe "
    "Instanz, dasselbe A\\* als Vergleich). Noch nicht gebaute Geschwister: Beam Search → {Diverse Beam Search, "
    "Monobeam}, Monte Carlo Tree Search (MCTS), Beam Search + A\\* → Beam Stack Search."
)

with st.expander("So funktioniert IDA*", expanded=True):
    st.markdown(
        """
1. **Schwelle** T = h(Start). Tiefensuche über den aktuellen Pfad; ein Knoten mit f = g + h **über T** wird
   abgeschnitten und merkt sich sein f als Kandidat für die nächste Schwelle.
2. Wird das Ziel nicht erreicht, wird T auf das **kleinste abgeschnittene f** gesetzt und **alles von vorn**
   durchsucht. Erster Zielfund = optimal (h zulässig, wie bei A\\*).
3. **Speicher** = nur der aktuelle Pfad. Es gibt bewusst **kein Closed-Set** (das wäre wieder Speicher) - ein Knoten
   wird nur gegen den eigenen Pfad auf Zyklen geprüft, nicht gegen bereits Gesehenes.
4. Folge: derselbe Knoten wird pro Iteration über jeden Weg dorthin erneut expandiert - und das über viele
   Iterationen. Wie viele, zeigt der Vergleich mit A\\* unten.
5. Die **Expansions-Obergrenze** ist ein Sicherheitsnetz: bei Erreichen bricht die Suche ab und behauptet **keinen**
   Pfad.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:3], preset_names[3:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    network = st.radio("Instanz", options=["grid", "trap"], format_func=lambda n: "Raster" if n == "grid" else "Handgebaute Heuristik-Falle",
                        key="network_select", horizontal=True, help="Die Falle ist ein fester, von Hand gebauter Graph - Rastergröße/Hindernisdichte/Seed/Obergrenze wirken dort nicht.")
    if network == "grid":
        side = st.slider("Rastergröße (Seitenlänge)", *bounds("side_slider"), key="side_slider",
                          help="Ab Größe 10 reißt auf offenem Gelände schon die Obergrenze von 1 Mio. Expansionen - deshalb endet der Regler bei 12.")
        obstacle_pct = st.slider("Hindernisdichte [%]", *bounds("obstacle_slider"), key="obstacle_slider", step=C.OBSTACLE_STEP,
                                  help="Bei dichten Hindernissen sinken Faktor (Median 71x bei 40 %, 917x bei 0 %) und Iterationen deutlich - nicht ganz monoton (Spitze bei 10 %).")
        cap = st.select_slider("Expansions-Obergrenze", options=list(C.CAPS), key="cap_select", format_func=_fmt_int,
                                help="Sicherheitsnetz gegen den Blow-up: bei Erreichen bricht IDA* ab und behauptet keinen Pfad.")
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        side, obstacle_pct, seed, cap = C.DEFAULT_SIDE, C.DEFAULT_OBSTACLE, C.DEFAULT_SEED, C.DEFAULT_CAP

sync_query_params({"network_select": network, "side_slider": int(side), "obstacle_slider": int(obstacle_pct), "seed_input": int(seed), "cap_select": int(cap)})

settings = Settings(network, int(side), int(obstacle_pct), int(seed), int(cap))
with st.spinner("Rechne..."):
    a = _analysis(settings)
ida = a.ida

# --- IDA* in Aktion ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 IDA* in Aktion")
STEP_LABELS = {1: "1 · Instanz", 2: "2 · Wiederholungen", 3: "3 · Ergebnis"}
step = st.select_slider("Schritt", options=list(STEP_LABELS), key="idastar_step", format_func=lambda s: STEP_LABELS[s])

if step == 1:
    st.markdown(f"**{a.inst.graph.n} Zellen** ({len(a.inst.blocked_xy)} Hindernisse), Start (grün) und Ziel (rot)")
    st.plotly_chart(build_instance(a.inst), width="stretch", key="s1_map")
elif step == 2:
    st.markdown(
        f"**IDA\\* expandierte {_fmt_int(ida.expansions)} Knoten** in {ida.iterations} Iterationen"
        + (" (**abgebrochen** - Obergrenze erreicht, die Zahl ist nur der bis dahin gesehene Anteil)" if ida.capped else "")
        + f" - **A\\* nur {a.astar.expansions}**. Farbe = wie oft ein Knoten expandiert wurde, Ring = von A\\* expandiert."
    )
    st.plotly_chart(build_multiplicity(a.inst, ida.expansion_counts, a.astar.order), width="stretch", key="s2_map")
    st.caption(
        f"IDA\\* berührt {len(ida.expansion_counts)} verschiedene Knoten, A\\* {a.astar.expansions} (Verhältnis {a.node_set_ratio:.2f}): "
        "dieselben Knoten, nur ungleich öfter. Im Mittel wurde jeder Knoten " + f"{a.multiplicity:.0f}-mal expandiert."
    )
    st.plotly_chart(build_iterations_bar(ida.per_iteration), width="stretch", key="s2_bars")
    if ida.capped:
        st.caption(f"Die bei der Obergrenze unfertige Iteration macht {100 * a.last_iteration_share:.1f} % der bis dahin gezählten Expansionen aus - der Aufwand entsteht durch die Wiederholungen.")
    else:
        st.caption(f"Die letzte Iteration macht nur {100 * a.last_iteration_share:.1f} % aller Expansionen aus - der Aufwand entsteht durch die Wiederholungen.")
else:
    if ida.capped:
        st.warning(f"IDA\\* wurde bei {_fmt_int(ida.expansions)} Expansionen abgebrochen (Obergrenze) und behauptet keinen Pfad. A\\* fand {a.astar.cost:.2f} km mit {a.astar.expansions} Expansionen.")
        st.plotly_chart(build_paths(a.inst, [], a.astar.path), width="stretch", key="s3_map")
    else:
        st.markdown(f"**IDA\\***: {ida.cost:.2f} km – **A\\***: {a.astar.cost:.2f} km – Lücke **{a.gap:.2f} %** (beide optimal)")
        st.plotly_chart(build_paths(a.inst, ida.path, a.astar.path), width="stretch", key="s3_map")

st.markdown("---")

# --- Ergebnis ----------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Was der Speichergewinn kostet")
st.caption(
    "**Speicher:** A\\* = gespeicherte Knoten, IDA\\* = maximale Pfadtiefe. **Expansions-Faktor:** Expansionen IDA\\* / A\\* "
    "(bei Abbruch nur eine Untergrenze)."
)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Speicher-Verhältnis", "-" if not a.solved else f"{a.memory_ratio:.1f}x", delta=f"{a.astar.stored} gegen Tiefe {ida.stored}" if a.solved else "IDA* abgebrochen", delta_color="off")
m2.metric("Expansions-Faktor", (f"≥ {_fmt_int(a.factor)}x" if ida.capped else f"{_fmt_int(a.factor)}x"), delta=f"{_fmt_int(ida.expansions)} gegen {a.astar.expansions}", delta_color="off")
m3.metric("Iterationen", f"{ida.iterations}", delta="bis Abbruch" if ida.capped else "bis zum Ziel", delta_color="off")
m4.metric("Status", "Abbruch" if ida.capped else "Gelöst", delta="Obergrenze erreicht" if ida.capped else f"Lücke {a.gap:.2f} %", delta_color="off")

st.markdown("---")

# --- Sweeps ------------------------------------------------------------------------------------------------------------------------------------

if network == "grid":
    st.subheader("📐 Wie hängt der Preis von Hindernisdichte und Rastergröße ab?")
    sweep_param = st.selectbox("Welcher Regler soll durchgefahren werden?", list(SWEEP_LABELS), format_func=lambda k: SWEEP_LABELS[k], key="sweep_select")
    metric = st.radio("Kennzahl", options=["factor", "memory_ratio", "iterations", "capped"],
                       format_func=lambda k: {"factor": "Expansions-Faktor (x)", "memory_ratio": "Speicher-Verhältnis (x)", "iterations": "Iterationen", "capped": "Abgebrochene Läufe (%)"}[k],
                       key="sweep_metric", horizontal=True)
    base_sweep = replace(settings, seed=0)
    if st.button("Sweep über 5 feste Instanzen berechnen (kann einige Sekunden dauern)", key="sweep_start"):
        st.session_state["sweep_done"] = st.session_state.get("sweep_done", set()) | {(sweep_param, base_sweep)}
    if (sweep_param, base_sweep) in st.session_state.get("sweep_done", set()):
        with st.spinner("Rechne den Sweep über 5 feste Instanzen..."):
            rows_sweep = _sweep(sweep_param, base_sweep)
        if metric == "capped":
            st.plotly_chart(build_capped_share(rows_sweep, SWEEP_LABELS[sweep_param]), width="stretch", key="sweep_capped")
        else:
            label = {"factor": "Expansions-Faktor IDA* / A* (x, logarithmisch)", "memory_ratio": "Speicher-Verhältnis A* / IDA* (x)", "iterations": "Iterationen"}[metric]
            st.plotly_chart(build_sweep(rows_sweep, SWEEP_LABELS[sweep_param], metric, label, color=IDA_COLOR if metric != "memory_ratio" else ASTAR_COLOR, log_y=metric == "factor"),
                            width="stretch", key="sweep_chart")
        st.caption(
            "Median über 5 feste Instanzen (Seeds 100000–100004), Band = Minimum bis Maximum. Bei abgebrochenen Läufen ist der Faktor nur eine "
            "Untergrenze; Speicher-Verhältnis und Iterationen nur über gelöste Läufe."
        )

    st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **IDA\\* spart Speicher zu akzeptablen Zeitkosten** | Gemessen NICHT: rund 3x weniger Speicher (Tiefe 15 gegen 47 gespeicherte Knoten) für im Median 705x so viele Expansionen. Der Speichervorteil wächst ungefähr linear mit der Größe (2.3x bis 3.7x), der Zeitpreis um Größenordnungen. | (kein Nachfolger nötig - eine echte, gemessene Eigenschaft dieses Vehikels) |
| **Wenige Wege zum selben Knoten** | Ein Raster hat extrem viele Transpositionen. Ohne Closed-Set (das wäre wieder Speicher) erkennt IDA\\* sie nicht: es berührt dieselben Knoten wie A\\*, jeden aber im Mittel hunderte Male. | Transpositionstabelle (hier bewusst nicht gebaut - sie würde den Speichervorteil aufgeben) |
| **Wenige Iterationen** | Jede Iteration hebt die Schwelle nur um den kleinsten abgeschnittenen f-Wert: im Median 231 Iterationen bei Größe 8, obwohl A\\* nur 38 Knoten expandiert - die letzte Iteration macht nur 0.7 % der Expansionen aus. Wie viel davon an den reellen Kantengewichten und wie viel an den Transpositionen liegt, wird hier NICHT einzeln getrennt. | Varianten für reell bewertete Kosten (hier nicht gebaut) |
| **Die Suche bleibt praktikabel** | Auf offenem Gelände reißt die Obergrenze von 1 Mio. Expansionen schon bei Größe 10 (4 von 5 Instanzen). Abgebrochene Läufe behaupten keinen Pfad. | **Monte Carlo Tree Search** / **Beam Search** (andere Wege, Speicher zu begrenzen) |
| **Synthetische Instanzen** | Ein Raster mit Jitter, Vierer-Nachbarschaft, keine Zeitfenster, keine gerichteten Kanten; Größen bis 12 im Regler. Andere Graphstrukturen (z. B. mit weniger Transpositionen) wurden nicht gemessen. | Echte Straßennetze (hier nicht gebaut) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Schwelle.** $T_0 = h(\text{Start})$; in Iteration $k$ werden alle Knoten mit $f(n) = g(n) + h(n) > T_k$ abgeschnitten,
$T_{k+1} = \min \{ f(n) : f(n) > T_k \}$. Der erste Zielfund ist optimal, da $h$ zulässig ist.

**Speicher.** A*: Zahl der entdeckten Knoten am Ende. IDA*: maximale Pfadtiefe $\le n$.

**Expansions-Faktor.** $E_{\text{IDA*}} / E_{\text{A*}}$. Bei abgebrochenen Läufen eine Untergrenze.

**Knotenmengen-Verhältnis.** verschiedene von IDA* expandierte Knoten / von A* expandierte Knoten.

**Sonderfälle, im Test nachgewiesen.** Auf einem Kettengraph (Baum ohne Transpositionen) genau eine Iteration;
bei Einheitsgewichten und $h \equiv 0$ die Schwellen $0, 1, 2, \dots$ des klassischen Iterative-Deepening-DFS.

**Literatur.** Korf, R. E. (1985). *Depth-first iterative-deepening: An optimal admissible tree search.*
Artificial Intelligence, 27(1), 97-109.

Implementiert in `idastar_algorithm.py` (Suchkerne aus der A*-Demo, `ida_star` neu),
`idastar_graph.py`/`idastar_scenario.py` (Graph, Raster- und Fallen-Instanzen, Kopie), `idastar_evaluation.py`
(Kennzahlen, Sweeps).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
