"""Suchkerne - `_search`, `greedy_best_first`, `uniform_cost_search`, `a_star` wortgleich aus `astar-demo` (dort
korrektheitsgeprüft), ergänzt um das Feld `stored` (Speicher-Kennzahl: wie viele Knoten der Algorithmus am Ende
gleichzeitig gespeichert hält) und NEU `ida_star`.

IDA* - (Korf 1985): statt einer Grenzmenge im Speicher wiederholte, auf f = g + h begrenzte Tiefensuchen. Die
Schwelle startet bei h(Start); Knoten mit f > Schwelle werden abgeschnitten, das kleinste abgeschnittene f wird die
nächste Schwelle. Zykluskontrolle NUR gegen den aktuellen Pfad - ein Closed-Set wäre wieder Speicher. Erster
Zielfund ist optimal (h zulässig). Speicher = maximale Pfadtiefe. Preis: Knoten werden über Iterationen UND über
verschiedene Wege zum selben Knoten mehrfach expandiert (im Raster extrem viele Transpositionen).

`max_expansions` ist ein Sicherheitsnetz gegen genau diesen Blow-up: bei Erreichen bricht die Suche ab
(`capped=True`, kein Pfad behauptet). Deterministisch: feste Nachbarreihenfolge (Adjazenzreihenfolge).
"""

import heapq
from dataclasses import dataclass, field

import numpy as np


def heuristic(xy, goal):
    """Euklidischer Abstand jedes Knotens zum Ziel - vektorisiert. Bei echten Kantengewichten (siehe
    `idastar_scenario.py`) automatisch zulässig (Dreiecksungleichung)."""
    return np.hypot(*(xy - xy[goal]).T)


@dataclass
class SearchResult:
    path: list                  # Knotenfolge Start..Ziel, oder [] falls kein Pfad existiert
    cost: float                 # Summe der Kantengewichte entlang des Pfades
    expansions: int             # Zahl der expandierten Knoten (Effizienz-Kennzahl dieses Stücks)
    order: list = field(default_factory=list)     # Reihenfolge der expandierten Knoten (für die Schritt-Visualisierung)
    stored: int = 0             # Speicher-Kennzahl: gespeicherte Knoten am Ende (A*/UCS/GBFS: entdeckte Knoten; IDA*: max. Pfadtiefe)


def _search(graph, start, goal, priority_fn, relax=True):
    """`priority_fn(node, g_cost) -> float` bestimmt die Warteschlangen-Priorität. `g_cost` ist der bislang
    aufgelaufene Pfadwert zu `node` (für Uniform-Cost-Search gebraucht, von Greedy Best-First ignoriert).

    `relax`: ob ein noch nicht expandierter, aber schon entdeckter Knoten einen GÜNSTIGEREN Elternknoten
    bekommt, sobald ein billigerer Weg zu ihm gefunden wird (klassische Dijkstra-Relaxation - für
    Uniform-Cost-Search nötig, damit es tatsächlich optimal bleibt). Bei `relax=False` behält ein Knoten für
    immer den ERSTEN gefundenen Elternknoten (echtes "kein Backtracking" - der Kern der GBFS-Schwäche: eine
    Relaxation hier würde den gemessenen Qualitätsverlust künstlich kleinrechnen, da GBFS dann doch beiläufig
    von g(n) profitieren würde, obwohl es g(n) laut Definition komplett ignoriert)."""
    counter = 0
    frontier = [(priority_fn(start, 0.0), counter, start, 0.0)]
    came_from = {start: None}
    g_cost = {start: 0.0}
    visited = set()
    order = []

    while frontier:
        _priority, _c, node, g = heapq.heappop(frontier)
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        if node == goal:
            path = []
            cur = node
            while cur is not None:
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return SearchResult(path, g, len(order), order, len(g_cost))
        for v, w in zip(graph.neighbors[node], graph.weights[node]):
            if v in visited:
                continue
            g_v = g + w
            is_new = v not in g_cost
            if is_new or (relax and g_v < g_cost[v]):
                g_cost[v] = g_v
                came_from[v] = node
                counter += 1
                heapq.heappush(frontier, (priority_fn(v, g_v), counter, v, g_v))

    return SearchResult([], float("inf"), len(order), order, len(g_cost))


def greedy_best_first(graph, start, goal):
    h = heuristic(graph.xy, goal)
    return _search(graph, start, goal, lambda node, g: h[node], relax=False)


def uniform_cost_search(graph, start, goal):
    return _search(graph, start, goal, lambda node, g: g, relax=True)


def a_star(graph, start, goal):
    h = heuristic(graph.xy, goal)
    return _search(graph, start, goal, lambda node, g: g + h[node], relax=True)


@dataclass
class IDAResult(SearchResult):
    iterations: int = 0
    per_iteration: list = field(default_factory=list)      # [(Schwelle, Expansionen in dieser Iteration), ...]
    expansion_counts: dict = field(default_factory=dict)   # Knoten -> wie oft expandiert (Mehrfachheit)
    capped: bool = False


def ida_star(graph, start, goal, max_expansions=1_000_000):
    h = heuristic(graph.xy, goal)
    neighbors, weights = graph.neighbors, graph.weights
    threshold = float(h[start])
    total = 0
    counts = {}
    per_iteration = []
    max_depth = 1

    while True:
        next_threshold = float("inf")
        expansions_here = 0
        path_nodes, path_g, path_idx = [], [], []
        on_path = set()
        found = capped = False

        def push(node, g):
            nonlocal next_threshold, total, expansions_here, found, capped, max_depth
            f = g + h[node]
            if f > threshold:
                if f < next_threshold:
                    next_threshold = f
                return
            if total >= max_expansions:
                capped = True
                return
            total += 1
            expansions_here += 1
            counts[node] = counts.get(node, 0) + 1
            path_nodes.append(node)
            path_g.append(g)
            path_idx.append(0)
            on_path.add(node)
            max_depth = max(max_depth, len(path_nodes))
            if node == goal:
                found = True

        push(start, 0.0)
        while path_nodes and not found and not capped:
            node = path_nodes[-1]
            i = path_idx[-1]
            if i == len(neighbors[node]):
                on_path.discard(path_nodes.pop())
                path_g.pop()
                path_idx.pop()
                continue
            path_idx[-1] = i + 1
            v = neighbors[node][i]
            if v in on_path:
                continue
            push(v, path_g[-1] + weights[node][i])

        per_iteration.append((threshold, expansions_here))
        if found:
            return IDAResult(list(path_nodes), path_g[-1], total, [], max_depth, len(per_iteration), per_iteration, counts, False)
        if capped:
            return IDAResult([], float("inf"), total, [], max_depth, len(per_iteration), per_iteration, counts, True)
        if next_threshold == float("inf"):
            return IDAResult([], float("inf"), total, [], max_depth, len(per_iteration), per_iteration, counts, False)
        threshold = next_threshold
