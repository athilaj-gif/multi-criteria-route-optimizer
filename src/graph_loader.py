import os
import networkx as nx
import osmnx as ox
from src.fuel_model import add_fuel_weights

DATA_DIR = "data"
DEFAULT_PLACE = "Bandra West, Mumbai, India"

def get_graph(place_name: str = DEFAULT_PLACE, filename: str = "graph.graphml"):
    """
    Loads road network data, filters to the largest strongly connected component
    so every node is mutually reachable, and adds fuel weights.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)

    if os.path.exists(filepath):
        print(f"Loading cached graph from {filepath}...")
        G = ox.load_graphml(filepath)
    else:
        print(f"Downloading road network for '{place_name}'...")
        G = ox.graph_from_place(place_name, network_type="drive")
        
        # Calculate speeds and travel times
        G = ox.routing.add_edge_speeds(G)
        G = ox.routing.add_edge_travel_times(G)
        
        print(f"Saving graph cache to {filepath}...")
        ox.save_graphml(G, filepath)

    # Keep only the largest strongly connected component so every pair of nodes has a valid path
    largest_scc = max(nx.strongly_connected_components(G), key=len)
    G = G.subgraph(largest_scc).copy()

    # Compute fuel weights and ensure numeric types on edges
    G = add_fuel_weights(G)
    print(f"Graph ready: {len(G.nodes)} nodes, {len(G.edges)} edges (Strongly Connected).")
    return G

if __name__ == "__main__":
    get_graph()