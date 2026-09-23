"""Die zentrale Korrektheits-Kette für IDA*: gleicher Pfadwert wie A*/UCS (gegen Brute-Force auf kleinen Instanzen
kreuzgeprüft), löst die handgebaute Falle, gültiger Pfad, Schwellen-Folge, Obergrenze, zwei Sonderfälle (Kettengraph:
genau eine Iteration; Einheitsgewichte + h = 0: klassisches Iterative-Deepening-DFS) und die geerbten Eigenschaften
der kopierten Suchkerne."""

import numpy as np
import pytest

import idastar_algorithm as A
import idastar_graph as G
import idastar_scenario as S

EPS = 1e-9
BIG = 5_000_000


def _brute_force_shortest_cost(graph, start, goal):
    best = None
    stack = [(start, [start], 0.0)]
    while stack:
        node, path, cost = stack.pop()
        if node == goal:
            if best is None or cost < best:
                best = cost
            continue
        for v, w in zip(graph.neighbors[node], graph.weights[node]):
            if v not in path:
                stack.append((v, path + [v], cost + w))
    return best


@pytest.mark.parametrize("seed", range(15))
def test_ida_star_finds_the_true_shortest_path_cost(seed):
    inst = S.grid_instance(side=5, obstacle_pct=15, seed=seed)
    result = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    assert not result.capped
    assert result.cost == pytest.approx(_brute_force_shortest_cost(inst.graph, inst.start, inst.goal), abs=1e-6)


def test_ida_star_matches_brute_force_on_the_trap_instance():
    inst = S.trap_instance()
    result = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    assert result.cost == pytest.approx(_brute_force_shortest_cost(inst.graph, inst.start, inst.goal), abs=1e-6)


@pytest.mark.parametrize("seed", range(30))
def test_ida_star_cost_equals_a_star_and_uniform_cost_search(seed):
    inst = S.grid_instance(side=6, obstacle_pct=(seed % 5) * 10, seed=seed)
    ida = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    assert not ida.capped
    assert ida.cost == pytest.approx(A.a_star(inst.graph, inst.start, inst.goal).cost, abs=1e-9)
    assert ida.cost == pytest.approx(A.uniform_cost_search(inst.graph, inst.start, inst.goal).cost, abs=1e-9)


def test_ida_star_solves_the_trap_where_greedy_best_first_fails():
    inst = S.trap_instance()
    gbfs = A.greedy_best_first(inst.graph, inst.start, inst.goal)
    ida = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    ucs = A.uniform_cost_search(inst.graph, inst.start, inst.goal)
    assert gbfs.cost > ucs.cost + 0.5
    assert ida.cost == pytest.approx(ucs.cost, abs=1e-9) and ida.path == ucs.path


@pytest.mark.parametrize("seed", range(20))
def test_ida_star_returns_a_valid_simple_connected_path_with_recomputed_cost(seed):
    inst = S.grid_instance(side=6, obstacle_pct=25, seed=seed)
    result = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    assert result.path[0] == inst.start and result.path[-1] == inst.goal
    assert len(set(result.path)) == len(result.path)
    for u, v in zip(result.path[:-1], result.path[1:]):
        assert v in inst.graph.neighbors[u]
    assert G.path_cost(inst.graph, result.path) == pytest.approx(result.cost, abs=1e-6)


def test_ida_star_is_deterministic():
    inst = S.grid_instance(side=6, obstacle_pct=20, seed=3)
    r1 = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    r2 = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    assert r1.path == r2.path and r1.expansions == r2.expansions and r1.per_iteration == r2.per_iteration


@pytest.mark.parametrize("seed", range(10))
def test_thresholds_start_at_h_of_start_rise_strictly_and_end_at_the_optimal_cost(seed):
    inst = S.grid_instance(side=6, obstacle_pct=15, seed=seed)
    result = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    thresholds = [t for t, _ in result.per_iteration]
    h = A.heuristic(inst.graph.xy, inst.goal)
    assert thresholds[0] == pytest.approx(h[inst.start], abs=1e-12)
    assert all(b > a for a, b in zip(thresholds[:-1], thresholds[1:]))
    assert thresholds[-1] == pytest.approx(result.cost, abs=1e-9)
    assert sum(e for _, e in result.per_iteration) == result.expansions == sum(result.expansion_counts.values())
    assert result.iterations == len(thresholds)


# --- Obergrenze ------------------------------------------------------------------------------------------------------------------------------


def test_cap_stops_the_search_exactly_at_the_limit_and_claims_no_path():
    inst = S.grid_instance(side=8, obstacle_pct=15, seed=35)
    result = A.ida_star(inst.graph, inst.start, inst.goal, 10)
    assert result.capped and result.path == [] and result.cost == float("inf")
    assert result.expansions == 10


def test_a_generous_cap_does_not_trigger():
    inst = S.grid_instance(side=6, obstacle_pct=15, seed=1)
    assert not A.ida_star(inst.graph, inst.start, inst.goal, BIG).capped


# --- Sonderfälle -----------------------------------------------------------------------------------------------------------------------------


def test_a_chain_graph_needs_exactly_one_iteration_and_expands_every_node_once():
    """Ein Baum ohne Transpositionen mit perfekter Heuristik: keine Wiederholung, keine zweite Iteration."""
    n = 6
    graph = G.from_edges(n, [(i, 0) for i in range(n)], [(i, i + 1, 1.0) for i in range(n - 1)])
    result = A.ida_star(graph, 0, n - 1, BIG)
    assert result.iterations == 1 and result.expansions == n
    assert result.path == list(range(n)) and set(result.expansion_counts.values()) == {1}


def test_unit_weights_and_zero_heuristic_reproduce_iterative_deepening_dfs():
    """Alle Koordinaten gleich -> h == 0; Einheitsgewichte -> Schwellen 0, 1, 2, ... = Tiefenlimits des klassischen
    Iterative-Deepening-DFS, die letzte Schwelle ist die kürzeste Kantenzahl."""
    edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (0, 4, 1.0), (4, 3, 1.0), (1, 4, 1.0), (3, 5, 1.0)]
    graph = G.from_edges(6, [(0, 0)] * 6, edges)
    result = A.ida_star(graph, 0, 5, BIG)
    assert [t for t, _ in result.per_iteration] == [0.0, 1.0, 2.0, 3.0]
    assert result.cost == 3.0


def test_disconnected_goal_is_reported_without_a_path_and_without_a_cap():
    graph = G.from_edges(4, [(0, 0), (1, 0), (2, 0), (3, 0)], [(0, 1, 1.0), (2, 3, 1.0)])
    result = A.ida_star(graph, 0, 3, BIG)
    assert result.path == [] and result.cost == float("inf") and not result.capped


# --- Speicher-Kennzahl und geerbte Eigenschaften -------------------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(10))
def test_stored_counts_are_consistent(seed):
    inst = S.grid_instance(side=6, obstacle_pct=15, seed=seed)
    ida = A.ida_star(inst.graph, inst.start, inst.goal, BIG)
    astar = A.a_star(inst.graph, inst.start, inst.goal)
    assert len(ida.path) <= ida.stored <= inst.graph.n
    assert astar.expansions <= astar.stored <= inst.graph.n


def test_inherited_heuristic_is_admissible_and_greedy_never_beats_the_optimum():
    for seed in range(10):
        inst = S.grid_instance(side=7, obstacle_pct=20, seed=seed)
        h = A.heuristic(inst.graph.xy, inst.goal)
        for node in range(inst.graph.n):
            assert h[node] <= A.uniform_cost_search(inst.graph, node, inst.goal).cost + EPS
        assert A.greedy_best_first(inst.graph, inst.start, inst.goal).cost >= A.uniform_cost_search(inst.graph, inst.start, inst.goal).cost - EPS
