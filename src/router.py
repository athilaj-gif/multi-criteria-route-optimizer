import heapq
import time
import numpy as np
import networkx as nx
from python_tsp.exact import solve_tsp_dynamic_programming
from src.utils import get_heuristic

CRITERIA_MAP = {
    "distance": "length",
    "time": "travel_time",
    "fuel": "fuel"
}

def get_min_edge_weight(G: nx.MultiDiGraph, u: int, v: int, weight_attr: str) -> float:
    """Returns the minimum weight among parallel edges between u and v."""
    edge_dict = G[u][v]
    return min(float(attr.get(weight_attr, float("inf"))) for attr in edge_dict.values())

def run_dijkstra(G: nx.MultiDiGraph, source: int, target: int, criterion: str = "time") -> dict:
    """
    Runs Dijkstra's algorithm and records explored nodes.
    """
    weight_attr = CRITERIA_MAP.get(criterion, criterion)
    start_time = time.perf_counter()

    pq = [(0.0, source)]
    dist = {source: 0.0}
    parent = {source: None}
    explored_nodes = []
    visited = set()

    while pq:
        d_u, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)
        explored_nodes.append(u)

        if u == target:
            break

        for v in G.successors(u):
            if v in visited:
                continue
            w = get_min_edge_weight(G, u, v, weight_attr)
            new_cost = d_u + w
            if new_cost < dist.get(v, float("inf")):
                dist[v] = new_cost
                parent[v] = u
                heapq.heappush(pq, (new_cost, v))

    runtime_ms = (time.perf_counter() - start_time) * 1000.0

    if target not in parent:
        raise ValueError(f"No path found between {source} and {target}.")

    # Reconstruct path
    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()

    return {
        "algorithm": "dijkstra",
        "criterion": criterion,
        "path": path,
        "cost": dist[target],
        "explored_nodes": explored_nodes,
        "explored_count": len(explored_nodes),
        "runtime_ms": runtime_ms
    }

def run_astar(G: nx.MultiDiGraph, source: int, target: int, criterion: str = "time") -> dict:
    """
    Runs A* search algorithm and records explored nodes.
    """
    weight_attr = CRITERIA_MAP.get(criterion, criterion)
    start_time = time.perf_counter()

    h_start = get_heuristic(G, source, target, weight_attr)
    pq = [(h_start, 0.0, source)]
    g_score = {source: 0.0}
    parent = {source: None}
    explored_nodes = []
    visited = set()

    while pq:
        f_u, g_u, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)
        explored_nodes.append(u)

        if u == target:
            break

        for v in G.successors(u):
            if v in visited:
                continue
            w = get_min_edge_weight(G, u, v, weight_attr)
            tentative_g = g_u + w
            if tentative_g < g_score.get(v, float("inf")):
                g_score[v] = tentative_g
                parent[v] = u
                f_v = tentative_g + get_heuristic(G, v, target, weight_attr)
                heapq.heappush(pq, (f_v, tentative_g, v))

    runtime_ms = (time.perf_counter() - start_time) * 1000.0

    if target not in parent:
        raise ValueError(f"No path found between {source} and {target}.")

    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()

    return {
        "algorithm": "astar",
        "criterion": criterion,
        "path": path,
        "cost": g_score[target],
        "explored_nodes": explored_nodes,
        "explored_count": len(explored_nodes),
        "runtime_ms": runtime_ms
    }

def solve_multi_stop_tsp(G: nx.MultiDiGraph, stop_nodes: list[int], criterion: str = "time") -> dict:
    """
    Solves the Traveling Salesperson Problem (TSP) across multiple stops
    using Held-Karp Dynamic Programming.
    """
    n = len(stop_nodes)
    dist_matrix = np.zeros((n, n))
    segment_paths = {}

    for i in range(n):
        for j in range(n):
            if i == j:
                dist_matrix[i][j] = 0.0
            else:
                res = run_astar(G, stop_nodes[i], stop_nodes[j], criterion=criterion)
                dist_matrix[i][j] = res["cost"]
                segment_paths[(i, j)] = res["path"]

    permutation, total_cost = solve_tsp_dynamic_programming(dist_matrix)

    ordered_stops = [stop_nodes[idx] for idx in permutation]
    ordered_segments = []
    for k in range(len(permutation)):
        u_idx = permutation[k]
        v_idx = permutation[(k + 1) % len(permutation)]
        ordered_segments.append(segment_paths[(u_idx, v_idx)])

    return {
        "permutation": permutation,
        "ordered_stops": ordered_stops,
        "segments": ordered_segments,
        "total_cost": total_cost,
        "criterion": criterion
    }

if __name__ == "__main__":
    from src.graph_loader import get_graph

    G = get_graph()
    nodes = list(G.nodes)
    src_node, dst_node = nodes[0], nodes[-1]

    d_res = run_dijkstra(G, src_node, dst_node, criterion="time")
    a_res = run_astar(G, src_node, dst_node, criterion="time")

    reduction = (1 - a_res["explored_count"] / d_res["explored_count"]) * 100

    print(f"\nRouting Benchmark ({src_node} -> {dst_node}):")
    print(f"  Dijkstra: Cost = {d_res['cost']:.2f}s | Explored = {d_res['explored_count']} nodes | Time = {d_res['runtime_ms']:.2f}ms")
    print(f"  A*      : Cost = {a_res['cost']:.2f}s | Explored = {a_res['explored_count']} nodes | Time = {a_res['runtime_ms']:.2f}ms")
    print(f"  Node Reduction by A*: {reduction:.1f}%")