"""Unabhängiges Orakel für IDA*: rekursive Neuimplementierung nach Korfs Definition (Pfad-Prefixe mit f <= Schwelle,
nächste Schwelle = kleinstes abgeschnittenes f) vergleicht Schwellenfolge, Expansionen je Iteration, Expansionszähler
je Knoten, Pfadtiefe und Abbruchverhalten; Optimalität gegen networkx-Dijkstra; A*-Expansionsmenge zwischen
{dist + h < C*} und {dist + h <= C*}; eine von Hand gerechnete Schwellenfolge. Zufallsgraphen mit Gleichständen und
getrennten Komponenten (zulässiges h: Kantengewicht >= euklidischer Abstand)."""

import math
import random

import numpy as np
import pytest

import idastar_algorithm as A
import idastar_graph as G
import idastar_scenario as S

nx = pytest.importorskip("networkx")


def _oracle_ida(graph, start, goal, cap):
    h = [float(x) for x in np.hypot(*(graph.xy - graph.xy[goal]).T)]
    threshold, total, counts, per_iter, max_depth = h[start], 0, {}, [], 1
    while True:
        st = {"exp": 0, "next": math.inf, "found": None, "capped": False}

        def dfs(node, g, path):
            nonlocal total, max_depth
            f = g + h[node]
            if f > threshold:
                st["next"] = min(st["next"], f)
                return False
            if total >= cap:
                st["capped"] = True
                return True
            total += 1
            st["exp"] += 1
            counts[node] = counts.get(node, 0) + 1
            path = path + [node]
            max_depth = max(max_depth, len(path))
            if node == goal:
                st["found"] = (path, g)
                return True
            for v, w in zip(graph.neighbors[node], graph.weights[node]):
                if v not in path and dfs(v, g + w, path):
                    return True
            return False

        dfs(start, 0.0, [])
        per_iter.append((threshold, st["exp"]))
        if st["found"]:
            return st["found"][0], st["found"][1], per_iter, counts, max_depth, False
        if st["capped"]:
            return [], math.inf, per_iter, counts, max_depth, True
        if st["next"] == math.inf:
            return [], math.inf, per_iter, counts, max_depth, False
        threshold = st["next"]


def _nx(graph):
    g = nx.Graph()
    g.add_nodes_from(range(graph.n))
    for u in range(graph.n):
        for v, w in zip(graph.neighbors[u], graph.weights[u]):
            g.add_edge(u, v, weight=w)
    return g


def _check(graph, s, t, cap):
    r = A.ida_star(graph, s, t, cap)
    path, cost, per_iter, counts, depth, capped = _oracle_ida(graph, s, t, cap)
    assert r.capped == capped and r.path == path
    assert [e for _, e in r.per_iteration] == [e for _, e in per_iter]
    assert all(a == pytest.approx(b, abs=1e-9) for (a, _), (b, _) in zip(r.per_iteration, per_iter))
    assert r.expansion_counts == counts and r.expansions == sum(counts.values()) and r.stored == depth
    g = _nx(graph)
    if not capped:
        if nx.has_path(g, s, t):
            assert r.cost == pytest.approx(nx.dijkstra_path_length(g, s, t), abs=1e-9)
        else:
            assert r.path == [] and r.cost == math.inf
    if nx.has_path(g, s, t):
        d = nx.dijkstra_path_length(g, s, t)
        dist = nx.single_source_dijkstra_path_length(g, s)
        h = np.hypot(*(graph.xy - graph.xy[t]).T)
        a = A.a_star(graph, s, t)
        must = {u for u in dist if dist[u] + h[u] < d - 1e-9}
        may = {u for u in dist if dist[u] + h[u] <= d + 1e-9}
        assert must <= set(a.order) <= may
        discovered = set(a.order)
        for u in set(a.order) - {t}:
            discovered.update(graph.neighbors[u])
        assert a.stored == len(discovered)


def test_random_graphs_match_the_oracle():
    rnd = random.Random(7)
    for _ in range(150):
        n = rnd.randint(1, 8)
        xy = [(rnd.randint(0, 3), rnd.randint(0, 3)) for _ in range(n)]
        edges = []
        for _ in range(rnd.randint(0, 2 * n)):
            u, v = rnd.randrange(n), rnd.randrange(n)
            if u != v:
                e = math.dist(xy[u], xy[v])
                edges.append((u, v, max(1.0, float(math.ceil(e)) if rnd.random() < .5 else e + rnd.choice([0, 1, 2]))))
        _check(G.from_edges(n, xy, edges), rnd.randrange(n), rnd.randrange(n), rnd.choice([50, 5000]))


def test_small_grids_match_the_oracle_including_the_cap():
    rnd = random.Random(3)
    for _ in range(40):
        inst = S.grid_instance(rnd.randint(2, 6), rnd.choice([0, 15, 40]), rnd.randint(0, 10**6))
        _check(inst.graph, inst.start, inst.goal, rnd.choice([30, 200, 100000]))


def test_threshold_sequence_by_hand():
    """s(0,0) a(1,0) t(3,0) b(0,2); s-a 1, a-t 2.5, s-b 2, b-t 4; h(s) = 3.
    Schwelle 3: s, a expandiert (f(a) = 1 + 2 = 3), t über a hat f = 3.5 -> nächste Schwelle 3.5; b hat f = 2 + 3.61 > 3.5.
    Schwelle 3.5: s, a, t -> 3 Expansionen, Kosten 3.5."""
    graph = G.from_edges(4, [(0, 0), (1, 0), (3, 0), (0, 2)], [(0, 1, 1.0), (1, 2, 2.5), (0, 3, 2.0), (3, 2, 4.0)])
    r = A.ida_star(graph, 0, 2, 100)
    assert r.per_iteration == [(3.0, 2), (3.5, 3)] and r.path == [0, 1, 2] and r.cost == 3.5
