import argparse
import os
import random
import matplotlib.pyplot as plt
from src.graph_loader import get_graph
from src.utils import snap_to_node, haversine_distance
from src.router import run_dijkstra, run_astar, solve_multi_stop_tsp
from src.visualizer import (
    generate_criteria_comparison_map,
    generate_algorithm_comparison_map,
    generate_tsp_map,
    generate_custom_criteria_comparison_map,
)

OUTPUT_DIR = "output"

def run_custom_route(G, start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    """Snaps custom GPS coordinates to nodes, computes routes for all 3 criteria, prints table, and maps."""
    src_node = snap_to_node(G, start_lat, start_lon)
    dst_node = snap_to_node(G, end_lat, end_lon)

    print(f"\nSnapping Coordinates:")
    print(f"  Start ({start_lat}, {start_lon}) -> Node {src_node}")
    print(f"  End   ({end_lat}, {end_lon}) -> Node {dst_node}")

    criteria = ["time", "fuel", "distance"]
    routes = {}

    print("\n================ MULTI-CRITERIA COST COMPARISON ================")
    print(f"{'Criterion':<12} | {'Total Cost':<15} | {'Travel Time':<15} | {'Fuel (L)':<12} | {'Distance (m)':<12}")
    print("-" * 75)

    for crit in criteria:
        res = run_astar(G, src_node, dst_node, criterion=crit)
        routes[crit] = res
        
        # Calculate full metrics across the chosen path
        path = res["path"]
        total_time, total_fuel, total_dist = 0.0, 0.0, 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge_data = min(G[u][v].values(), key=lambda x: float(x.get(crit, 0)))
            total_time += float(edge_data.get("travel_time", 0))
            total_fuel += float(edge_data.get("fuel", 0))
            total_dist += float(edge_data.get("length", 0))

        cost_label = f"{res['cost']:.2f}"
        print(f"{crit.capitalize():<12} | {cost_label:<15} | {total_time/60:.1f} mins      | {total_fuel:.3f} L      | {total_dist:.1f} m")
    print("=" * 75)

    # Generate Map
    map_path = generate_custom_criteria_comparison_map(
        G, routes, (start_lat, start_lon), (end_lat, end_lon)
    )
    print(f"Interactive comparison map saved to: {map_path}")

def run_benchmark(G, num_trials: int = 50, seed: int = 42):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    random.seed(seed)
    nodes = list(G.nodes)

    dijkstra_nodes_list, astar_nodes_list, reductions = [], [], []

    print(f"\nRunning benchmark across {num_trials} random route pairs...")
    for _ in range(num_trials):
        u, v = random.sample(nodes, 2)
        d_res = run_dijkstra(G, u, v, criterion="time")
        a_res = run_astar(G, u, v, criterion="time")
        dijkstra_nodes_list.append(d_res["explored_count"])
        astar_nodes_list.append(a_res["explored_count"])
        if d_res["explored_count"] > 0:
            reductions.append((1.0 - a_res["explored_count"] / d_res["explored_count"]) * 100.0)

    avg_d = sum(dijkstra_nodes_list) / num_trials
    avg_a = sum(astar_nodes_list) / num_trials
    avg_red = sum(reductions) / len(reductions)

    print(f"\n=== Benchmark Results ===")
    print(f"Avg Nodes Explored (Dijk): {avg_d:.1f}")
    print(f"Avg Nodes Explored (A*)  : {avg_a:.1f}")
    print(f"Avg Node Reduction by A* : {avg_red:.1f}%")

    # Plot chart
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["Dijkstra", "A*"], [avg_d, avg_a], color=["#e74c3c", "#3498db"], width=0.5)
    ax.set_title(f"Avg Nodes Explored ({avg_red:.1f}% Reduction)")
    ax.set_ylabel("Nodes Explored")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, "benchmark_chart.png")
    plt.savefig(chart_path, dpi=150)
    plt.close()
    print(f"Saved Benchmark Chart -> {chart_path}")

def main():
    parser = argparse.ArgumentParser(description="Multi-Criteria Route Optimizer CLI")
    parser.add_argument("--mode", choices=["all", "custom", "maps", "benchmark"], default="all")
    parser.add_argument("--start", type=str, default="19.0600,72.8300", help="Start Lat,Lon (default: Bandra West area)")
    parser.add_argument("--end", type=str, default="19.0500,72.8400", help="End Lat,Lon (default: Bandra East/Kurla area)")
    parser.add_argument("--trials", type=int, default=50)
    args = parser.parse_args()

    G = get_graph()

    if args.mode in ("all", "custom"):
        try:
            s_lat, s_lon = map(float, args.start.split(","))
            e_lat, e_lon = map(float, args.end.split(","))
            run_custom_route(G, s_lat, s_lon, e_lat, e_lon)
        except Exception as e:
            print(f"Error parsing coordinates: {e}. Use format --start '19.06,72.83'")

    if args.mode in ("all", "maps"):
        nodes = list(G.nodes)
        start_node, end_node = nodes[0], nodes[len(nodes) // 2]
        routes = {crit: run_astar(G, start_node, end_node, criterion=crit) for crit in ["time", "fuel", "distance"]}
        generate_criteria_comparison_map(G, routes)
        d_res = run_dijkstra(G, start_node, end_node, criterion="time")
        generate_algorithm_comparison_map(G, d_res, routes["time"])
        step = len(nodes) // 6
        generate_tsp_map(G, solve_multi_stop_tsp(G, [nodes[i * step] for i in range(5)], criterion="time"))

    if args.mode in ("all", "benchmark"):
        run_benchmark(G, num_trials=args.trials)

if __name__ == "__main__":
    main()