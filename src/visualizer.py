import os
import folium
import networkx as nx

OUTPUT_DIR = "output"

def _get_path_coords(G: nx.MultiDiGraph, path: list[int]) -> list[tuple[float, float]]:
    """Extracts (lat, lon) coordinates for a sequence of node IDs."""
    return [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]

def _create_base_map(G: nx.MultiDiGraph, center_node: int, zoom_start: int = 15) -> folium.Map:
    """
    Creates a clean Folium base map using Esri World Street Map.
    Using Esri tiles prevents 403 access blocked errors when opening HTML files locally from disk.
    """
    lat, lon = G.nodes[center_node]["y"], G.nodes[center_node]["x"]
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom_start,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri"
    )

def generate_criteria_comparison_map(
    G: nx.MultiDiGraph,
    routes_by_criterion: dict[str, dict],
    filename: str = "criteria_comparison.html"
) -> str:
    """
    Map 1: Runs 1 algorithm (A*) across 3 criteria:
    - Blue line: Time
    - Green line: Fuel
    - Orange line: Distance
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    first_path = next(iter(routes_by_criterion.values()))["path"]
    m = _create_base_map(G, first_path[0])

    styles = {
        "time":     {"color": "blue",   "weight": 6, "opacity": 0.75, "label": "Time (Fastest)"},
        "fuel":     {"color": "green",  "weight": 5, "opacity": 0.80, "label": "Fuel (Most Eco)"},
        "distance": {"color": "orange", "weight": 4, "opacity": 0.85, "label": "Distance (Shortest)"}
    }

    for criterion, res in routes_by_criterion.items():
        coords = _get_path_coords(G, res["path"])
        style = styles.get(criterion, {"color": "purple", "weight": 4, "opacity": 0.8, "label": criterion})
        
        folium.PolyLine(
            locations=coords,
            color=style["color"],
            weight=style["weight"],
            opacity=style["opacity"],
            tooltip=f"{style['label']} | Cost: {res['cost']:.2f}"
        ).add_to(m)

    # Start & End Markers
    start_coords = _get_path_coords(G, [first_path[0]])[0]
    end_coords = _get_path_coords(G, [first_path[-1]])[0]
    folium.Marker(start_coords, popup="Start", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(end_coords, popup="End", icon=folium.Icon(color="red", icon="stop")).add_to(m)

    filepath = os.path.join(OUTPUT_DIR, filename)
    m.save(filepath)
    print(f"Saved Criteria Comparison Map -> {filepath}")
    return filepath

def generate_algorithm_comparison_map(
    G: nx.MultiDiGraph,
    dijkstra_res: dict,
    astar_res: dict,
    filename: str = "algorithm_comparison.html"
) -> str:
    """
    Map 2: Compares Dijkstra vs A* on 1 criterion (Time):
    - Red dots: Dijkstra explored nodes
    - Blue dots: A* explored nodes
    - Thick Black line: Final optimal route
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = astar_res["path"]
    m = _create_base_map(G, path[0])

    # 1. Plot Dijkstra's explored nodes as Red dots
    for node in dijkstra_res["explored_nodes"]:
        lat, lon = G.nodes[node]["y"], G.nodes[node]["x"]
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.35,
            weight=1,
            tooltip="Dijkstra Explored"
        ).add_to(m)

    # 2. Plot A*'s explored nodes as Blue dots
    for node in astar_res["explored_nodes"]:
        lat, lon = G.nodes[node]["y"], G.nodes[node]["x"]
        folium.CircleMarker(
            location=[lat, lon],
            radius=3.5,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.6,
            weight=1,
            tooltip="A* Explored"
        ).add_to(m)

    # 3. Plot the final route as a thick Black line
    route_coords = _get_path_coords(G, path)
    folium.PolyLine(
        locations=route_coords,
        color="black",
        weight=6,
        opacity=0.9,
        tooltip=f"Optimal Route | Dijkstra: {dijkstra_res['explored_count']} nodes, A*: {astar_res['explored_count']} nodes"
    ).add_to(m)

    # Start & End Markers
    folium.Marker(route_coords[0], popup="Start", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(route_coords[-1], popup="End", icon=folium.Icon(color="red", icon="stop")).add_to(m)

    filepath = os.path.join(OUTPUT_DIR, filename)
    m.save(filepath)
    print(f"Saved Algorithm Comparison Map -> {filepath}")
    return filepath

def generate_tsp_map(
    G: nx.MultiDiGraph,
    tsp_res: dict,
    filename: str = "tsp_route.html"
) -> str:
    """
    Map 3: Multi-stop TSP Map:
    - Draws numbered markers (1, 2, 3...) in optimal visiting order
    - Connects segments with distinct colors
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ordered_stops = tsp_res["ordered_stops"]
    segments = tsp_res["segments"]
    m = _create_base_map(G, ordered_stops[0])

    segment_colors = ["blue", "green", "purple", "orange", "darkred", "cadetblue", "darkgreen", "darkblue"]

    # Draw colored route lines for each leg of the tour
    for idx, seg_path in enumerate(segments):
        coords = _get_path_coords(G, seg_path)
        color = segment_colors[idx % len(segment_colors)]
        folium.PolyLine(
            locations=coords,
            color=color,
            weight=5,
            opacity=0.85,
            tooltip=f"Leg {idx + 1} -> {(idx + 1) % len(ordered_stops) + 1}"
        ).add_to(m)

    # Draw numbered markers for each stop in the optimal order
    for order_idx, node in enumerate(ordered_stops, start=1):
        lat, lon = G.nodes[node]["y"], G.nodes[node]["x"]
        icon_html = f"""
        <div style="
            background-color: #2b2b2b;
            color: white;
            border-radius: 50%;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            border: 2px solid white;
            box-shadow: 0 0 4px rgba(0,0,0,0.5);">
            {order_idx}
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=f"Stop #{order_idx} (Node {node})",
            icon=folium.DivIcon(html=icon_html)
        ).add_to(m)

    filepath = os.path.join(OUTPUT_DIR, filename)
    m.save(filepath)
    print(f"Saved TSP Route Map -> {filepath}")
    return filepath

def generate_custom_criteria_comparison_map(
    G: nx.MultiDiGraph,
    routes_by_criterion: dict[str, dict],
    start_coords: tuple[float, float],
    end_coords: tuple[float, float],
    filename: str = "custom_criteria_comparison.html"
) -> str:
    """
    Map 4: Generates an interactive map comparing Time, Fuel, and Distance routes
    between custom user-specified start and end coordinates.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    m = folium.Map(
        location=start_coords,
        zoom_start=14,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri"
    )

    styles = {
        "time":     {"color": "blue",   "weight": 6, "opacity": 0.85, "label": "Time (Fastest)"},
        "fuel":     {"color": "green",  "weight": 5, "opacity": 0.85, "label": "Fuel (Most Eco)"},
        "distance": {"color": "orange", "weight": 4, "opacity": 0.85, "label": "Distance (Shortest)"}
    }

    for criterion, res in routes_by_criterion.items():
        coords = _get_path_coords(G, res["path"])
        style = styles.get(criterion, {"color": "purple", "weight": 4, "opacity": 0.8, "label": criterion})
        
        cost_str = f"{res['cost']:.2f}s" if criterion == "time" else (f"{res['cost']:.3f}L" if criterion == "fuel" else f"{res['cost']:.1f}m")
        
        folium.PolyLine(
            locations=coords,
            color=style["color"],
            weight=style["weight"],
            opacity=style["opacity"],
            tooltip=f"{style['label']} | Cost: {cost_str}"
        ).add_to(m)

    folium.Marker(start_coords, popup="Custom Start", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(end_coords, popup="Custom End", icon=folium.Icon(color="red", icon="stop")).add_to(m)

    filepath = os.path.join(OUTPUT_DIR, filename)
    m.save(filepath)
    print(f"Saved Custom Criteria Comparison Map -> {filepath}")
    return filepath