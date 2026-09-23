"""Jede Zahl in den Hilfetexten, Presets, Tabellen und Grenzen der App ist hier über die fünf festen Sweep-
Instanzen belegt, mit denselben Auswertungsfunktionen wie die App selbst (`ev.run_config`/`ev.sweep`) - NIE über
ein Ad-hoc-Skript. Positive UND negative Aussagen: IDA* ist ausnahmslos optimal und spart Speicher (positiv) - aber
die Vorab-Hypothese "Speichergewinn zu akzeptablen Zeitkosten" ist FALSCH: rund 3x weniger Speicher für rund 700x
mehr Expansionen (negativ, der zentrale ehrliche Befund). Werte sind MEDIANE (Faktoren sind stark schief)."""

from functools import lru_cache

import pytest

import idastar_constants as C
import idastar_evaluation as ev


@lru_cache(maxsize=None)
def _cfg(items):
    return ev.run_config(ev.Settings(), **dict(items))


def cfg(**kw):
    return _cfg(tuple(sorted(kw.items())))


def near(value, expected, tol):
    assert abs(value - expected) <= tol, f"{value:.3f} statt {expected}"


# --- Standardfall ------------------------------------------------------------------------------------------------------------------------------


def test_default_numbers():
    row = cfg()
    assert row["n_solved"] == 5
    near(row["factor"], 705, 60)
    near(row["memory_ratio"], 3.0, 0.3)
    near(row["iterations"], 231, 20)
    near(row["astar_stored"], 47, 3)
    near(row["ida_depth"], 15, 0.6)
    near(row["astar_expansions"], 38, 3)


def test_the_hypothesis_of_an_acceptable_price_is_refuted():
    row = cfg()
    assert row["memory_ratio"] < 5 and row["factor"] > 100                 # wenige x Speicher gegen hunderte x Zeit


def test_ida_star_touches_the_same_nodes_as_a_star_and_the_last_iteration_is_tiny():
    row = cfg()
    assert row["node_set_ratio"] == pytest.approx(1.0, abs=0.02)
    assert row["last_share"] < 0.02
    near(row["multiplicity"], row["factor"], row["factor"] * 0.05)         # im Mittel so oft expandiert, wie der Faktor sagt


def test_every_solved_default_instance_is_optimal():
    for seed in C.SWEEP_SEEDS:
        assert abs(ev.analyse(ev.Settings(seed=seed)).gap) < 1e-9


# --- Hindernisdichte-Sweep -----------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("obstacle_pct,expected,tol", [(0, 917, 80), (10, 1771, 150), (40, 71, 10)])
def test_obstacle_sweep_factor_numbers(obstacle_pct, expected, tol):
    near(cfg(obstacle_pct=obstacle_pct)["factor"], expected, tol)


def test_dense_obstacles_make_the_search_much_cheaper_but_not_monotonically():
    f = {o: cfg(obstacle_pct=o)["factor"] for o in (0, 10, 40)}
    assert f[0] > 5 * f[40]
    assert f[10] > 1.3 * f[0]                                              # Spitze bei 10 % - kein sauber monotoner Verlauf


def test_iterations_and_memory_ratio_fall_with_obstacle_density():
    assert cfg(obstacle_pct=0)["iterations"] > 3 * cfg(obstacle_pct=40)["iterations"]
    near(cfg(obstacle_pct=40)["iterations"], 61, 8)
    near(cfg(obstacle_pct=0)["memory_ratio"], 3.73, 0.3)
    near(cfg(obstacle_pct=40)["memory_ratio"], 2.0, 0.3)


# --- Größen-Sweep -----------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("side,expected,tol", [(5, 28, 5), (6, 55, 8), (7, 369, 40)])
def test_size_sweep_factor_numbers(side, expected, tol):
    near(cfg(side=side)["factor"], expected, tol)


def test_the_memory_advantage_grows_only_slowly_while_the_time_price_grows_by_orders_of_magnitude():
    small, large = cfg(side=5), cfg(side=10)
    near(small["memory_ratio"], 2.33, 0.3)
    near(large["memory_ratio"], 3.68, 0.4)
    assert large["memory_ratio"] < small["memory_ratio"] * 2.0
    assert large["factor"] > 20 * small["factor"]


def test_at_size_ten_the_cap_starts_to_bind_and_solved_only_medians_would_mislead():
    row = cfg(side=10)
    assert row["capped_share"] == 40.0
    near(row["factor"], 1771, 200)                                         # Untergrenze
    assert row["factor_solved"] < row["factor"]                            # nur gelöste Läufe: die schwersten fehlen


@pytest.mark.parametrize("side,capped", [(8, 0.0), (9, 20.0), (10, 80.0)])
def test_open_field_capped_share(side, capped):
    assert cfg(obstacle_pct=0, side=side)["capped_share"] == capped


# --- Handgebaute Falle ---------------------------------------------------------------------------------------------------------------------------


def test_trap_instance_numbers():
    a = ev.analyse(ev.Settings(network="trap"))
    assert a.solved and abs(a.gap) < 1e-9
    assert (a.astar.expansions, a.astar.stored) == (7, 8)
    assert (a.ida.expansions, a.ida.iterations, a.ida.stored) == (22, 6, 4)
    near(a.factor, 3.14, 0.05)


def test_preset_count_matches_the_readme():
    assert len(C.PRESETS) == 6
