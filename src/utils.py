import math
import networkx as nx
import osmnx as ox

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance in meters between two GPS coordinates
    using the Haversine formula.
    """
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def get_heuristic(G: nx.MultiDiGraph, node_u: int, node_v: int, weight: str) -> float:
    """
    Admissible A* heuristic that never overestimates true cost.
    """
    u_data = G.nodes[node_u]
    v_data = G.nodes[node_v]
    dist_m = haversine_distance(u_data["y"], u_data["x"], v_data["y"], v_data["x"])

    if weight == "length":
        return dist_m
    elif weight == "travel_time":
        max_speed_mps = 130.0 / 3.6  # Assume 130 km/h max speed so we never overestimate time
        return dist_m / max_speed_mps
    elif weight == "fuel":
        min_fuel_per_km = 0.07       # Minimum possible fuel rate from fuel_model.py
        return (dist_m / 1000.0) * min_fuel_per_km
    return 0.0

def snap_to_node(G: nx.MultiDiGraph, lat: float, lon: float) -> int:
    """Finds the nearest graph node to a given (lat, lon) coordinate."""
    return ox.distance.nearest_nodes(G, X=lon, Y=lat)