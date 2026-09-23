"""Auswertung: was kostet IDA*s Speichergewinn? Vergleich mit A* (hält die gesamte Grenzmenge im Speicher) auf
demselben Graphen. Kennzahlen:

- **Speicher-Verhältnis** = von A* gespeicherte Knoten / maximale Pfadtiefe von IDA* (nur für gelöste Läufe).
- **Expansions-Faktor** = Expansionen IDA* / Expansionen A*. Bei abgebrochenen Läufen (Obergrenze erreicht) nur eine
  UNTERGRENZE - deshalb werden abgebrochene Läufe getrennt als Anteil ausgewiesen und der Faktor mit und ohne sie
  berichtet (der Faktor NUR über gelöste Läufe würde bei großen Instanzen fälschlich sinken: die schwersten
  Instanzen fielen heraus).
- **Mehrfachheit** = Expansionen / verschiedene expandierte Knoten (im Mittel wie oft ein Knoten expandiert wurde).

Faktoren sind stark schief verteilt - deshalb Median mit Spannweite (Minimum bis Maximum über die Instanzen) statt
Mittelwert mit Streuung. Vollständig deterministisch, kein Ketten-Seed."""

from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

import idastar_algorithm as A
import idastar_constants as C
import idastar_scenario as S


@dataclass(frozen=True)
class Settings:
    network: str = "grid"           # "grid" oder "trap"
    side: int = C.DEFAULT_SIDE
    obstacle_pct: int = C.DEFAULT_OBSTACLE
    seed: int = C.DEFAULT_SEED
    cap: int = C.DEFAULT_CAP


@lru_cache(maxsize=256)
def instance(side, obstacle_pct, seed):
    return S.grid_instance(side, obstacle_pct, seed)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    astar: A.SearchResult
    ucs: A.SearchResult
    ida: A.IDAResult

    @property
    def solved(self):
        return not self.ida.capped

    @property
    def factor(self):
        """Expansionen IDA* / A*. Bei `solved == False` eine UNTERGRENZE (die Suche wurde abgebrochen)."""
        return self.ida.expansions / self.astar.expansions

    @property
    def memory_ratio(self):
        """A*-gespeicherte Knoten / IDA*-Pfadtiefe; NaN, falls IDA* abgebrochen wurde (Tiefe dann unvollständig)."""
        return self.astar.stored / self.ida.stored if self.solved else float("nan")

    @property
    def multiplicity(self):
        """Im Mittel wie oft ein (überhaupt expandierter) Knoten expandiert wurde."""
        return self.ida.expansions / len(self.ida.expansion_counts)

    @property
    def node_set_ratio(self):
        """Verschiedene von IDA* expandierte Knoten / von A* expandierte Knoten. Nahe 1 heißt: IDA* schaut sich
        (fast) dieselben Knoten an wie A* - nur ungleich öfter."""
        return len(self.ida.expansion_counts) / self.astar.expansions

    @property
    def last_iteration_share(self):
        """Anteil der letzten Iteration an allen Expansionen - klein heißt: der Aufwand entsteht durch die vielen
        Wiederholungen über Iterationen, nicht durch die letzte Suche allein."""
        return self.ida.per_iteration[-1][1] / self.ida.expansions

    @property
    def gap(self):
        return 100.0 * (self.ida.cost - self.ucs.cost) / self.ucs.cost if self.solved else float("nan")


def analyse(settings):
    inst = S.trap_instance() if settings.network == "trap" else instance(settings.side, settings.obstacle_pct, settings.seed)
    astar = A.a_star(inst.graph, inst.start, inst.goal)
    ucs = A.uniform_cost_search(inst.graph, inst.start, inst.goal)
    ida = A.ida_star(inst.graph, inst.start, inst.goal, settings.cap)
    return Analysis(settings, inst, astar, ucs, ida)


# --- Sweeps --------------------------------------------------------------------------------------------------------------------------------------


def _median_range(values):
    values = [v for v in values if not np.isnan(v)]
    if not values:
        return float("nan"), float("nan"), float("nan")
    return float(np.median(values)), float(np.min(values)), float(np.max(values))


def run_config(base, seeds=C.SWEEP_SEEDS, **changes):
    s0 = replace(base, **changes)
    rows = [analyse(replace(s0, seed=seed)) for seed in seeds]
    out = {"n_runs": len(rows), "n_solved": sum(r.solved for r in rows), "capped_share": 100.0 * sum(not r.solved for r in rows) / len(rows)}
    for key, values in (
        ("factor", [r.factor for r in rows]),                                        # Untergrenze bei abgebrochenen Läufen
        ("factor_solved", [r.factor if r.solved else float("nan") for r in rows]),   # nur gelöste Läufe
        ("memory_ratio", [r.memory_ratio for r in rows]),
        ("iterations", [r.ida.iterations if r.solved else float("nan") for r in rows]),
        ("multiplicity", [r.multiplicity for r in rows]),
        ("node_set_ratio", [r.node_set_ratio for r in rows]),
        ("last_share", [r.last_iteration_share for r in rows]),
    ):
        out[key], out[f"{key}_lo"], out[f"{key}_hi"] = _median_range(values)
    out["astar_stored"] = float(np.mean([r.astar.stored for r in rows]))
    out["ida_depth"] = float(np.mean([r.ida.stored for r in rows if r.solved])) if out["n_solved"] else float("nan")
    out["astar_expansions"] = float(np.median([r.astar.expansions for r in rows]))
    return out


SWEEP_VALUES = {"obstacle_pct": C.OBSTACLE_SWEEP, "side": C.SCALING_SIDES}
SWEEP_LABELS = {"obstacle_pct": "Hindernisdichte (%)", "side": "Rastergröße (Seitenlänge)"}


def sweep(param, base=Settings(), values=None):
    values = SWEEP_VALUES[param] if values is None else values
    return [{"value": v, **run_config(base, **{param: v})} for v in values]
