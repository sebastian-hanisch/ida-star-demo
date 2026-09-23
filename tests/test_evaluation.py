import math

import idastar_constants as C
import idastar_evaluation as EV


def test_analyse_grid_and_trap_solve_and_agree_with_a_star():
    for network in ("grid", "trap"):
        a = EV.analyse(EV.Settings(network=network, side=6, obstacle_pct=20, seed=1))
        assert a.solved and abs(a.gap) < 1e-9
        assert a.ida.path[0] == a.inst.start and a.ida.path[-1] == a.inst.goal


def test_capped_run_is_flagged_and_its_factor_is_only_a_lower_bound():
    a = EV.analyse(EV.Settings(side=8, obstacle_pct=15, seed=35, cap=10000))
    assert not a.solved and a.ida.expansions == 10000
    assert math.isnan(a.memory_ratio) and math.isnan(a.gap)
    full = EV.analyse(EV.Settings(side=8, obstacle_pct=15, seed=35))
    assert a.factor < full.factor                                            # Untergrenze < wahrer Faktor


def test_factor_and_memory_ratio_are_above_one_for_solved_runs():
    for seed in range(10):
        a = EV.analyse(EV.Settings(side=6, obstacle_pct=15, seed=seed))
        assert a.factor > 1.0 and a.memory_ratio > 1.0


def test_ida_star_touches_the_same_nodes_as_a_star_on_solved_runs():
    for seed in range(10):
        a = EV.analyse(EV.Settings(side=7, obstacle_pct=15, seed=seed))
        assert 0.9 <= a.node_set_ratio <= 1.1


def test_multiplicity_and_last_iteration_share_are_consistent():
    a = EV.analyse(EV.Settings(side=7, obstacle_pct=15, seed=3))
    assert a.multiplicity == a.ida.expansions / len(a.ida.expansion_counts)
    assert 0.0 < a.last_iteration_share <= 1.0


def test_run_config_reports_capped_share_and_medians_with_ranges():
    out = EV.run_config(EV.Settings(side=8, obstacle_pct=15, cap=10000))
    assert out["n_runs"] == 5 and out["capped_share"] == 100.0 and out["n_solved"] == 0
    assert math.isnan(out["memory_ratio"])
    solved = EV.run_config(EV.Settings(side=6), seeds=(1, 2, 3))
    assert solved["capped_share"] == 0.0 and solved["factor_lo"] <= solved["factor"] <= solved["factor_hi"]


def test_sweep_returns_one_row_per_value():
    assert [r["value"] for r in EV.sweep("obstacle_pct", EV.Settings(side=6))] == list(C.OBSTACLE_SWEEP)
    assert [r["value"] for r in EV.sweep("side", EV.Settings(obstacle_pct=40), values=(5, 6))] == [5, 6]


def test_analyse_is_deterministic():
    a1 = EV.analyse(EV.Settings(side=7, obstacle_pct=25, seed=7))
    a2 = EV.analyse(EV.Settings(side=7, obstacle_pct=25, seed=7))
    assert a1.factor == a2.factor and a1.ida.per_iteration == a2.ida.per_iteration
