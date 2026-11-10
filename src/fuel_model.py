import networkx as nx

def estimate_fuel_per_km(speed_kph: float) -> float:
    """
    Piecewise function estimating fuel consumption (L/km)
    based on road speed limit (km/h).
    """
    if speed_kph < 20:
        return 0.12   # Stop-and-go
    if speed_kph < 50:
        return 0.09   # Urban
    if speed_kph < 80:
        return 0.07   # Optimal
    if speed_kph < 120:
        return 0.08   # Highway
    return 0.11       # Very high speed

def add_fuel_weights(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Iterates through all edges in the graph and computes total fuel (L)
    for each road segment: fuel = (length_m / 1000) * estimate_fuel_per_km(speed_kph).
    """
    for u, v, k, data in G.edges(keys=True, data=True):
        length_m = float(data.get("length", 0.0))
        speed_kph = float(data.get("speed_kph", 40.0))
        
        length_km = length_m / 1000.0
        fuel_per_km = estimate_fuel_per_km(speed_kph)
        
        data["fuel"] = round(length_km * fuel_per_km, 6)
        data["length"] = length_m
        data["travel_time"] = float(data.get("travel_time", 0.0))
        data["speed_kph"] = speed_kph

    return G

if __name__ == "__main__":
    from src.graph_loader import get_graph
    
    G = get_graph()
    
    # Inspect the first edge to verify all 3 criteria exist
    u, v, k, sample_data = next(iter(G.edges(keys=True, data=True)))
    print(f"\nSample Edge ({u} -> {v}):")
    print(f"  Distance (m):    {sample_data['length']:.2f}")
    print(f"  Speed (km/h):    {sample_data['speed_kph']:.2f}")
    print(f"  Travel Time (s): {sample_data['travel_time']:.2f}")
    print(f"  Fuel (Liters):   {sample_data['fuel']:.5f}")