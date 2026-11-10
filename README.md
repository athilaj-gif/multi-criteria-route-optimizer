# Multi-Criteria Route Optimizer

A geospatial routing engine built on real OpenStreetMap road networks that optimizes for **Time**, **Distance**, or **Fuel Consumption**, benchmarks **A\*** against **Dijkstra's Algorithm**, and solves the **Traveling Salesperson Problem (TSP)** for multi-stop delivery routes.

---

## Key Features

- **Real-World Geospatial Graph Ingestion:** Downloads, processes, and caches drivable street networks via `OSMnx` (`data/graph.graphml`) and filters to the largest strongly connected component so every node pair has a valid path.
- **Piecewise Quantitative Fuel Model:** Estimates edge-level fuel expenditure (Liters) based on imputed and real-world road speed limits (`speed_kph`).
- **Decoupled Shortest-Path Engine:** Custom implementations of **Dijkstra** and **A\*** tracking exact node exploration counts and execution time.
- **Multi-Stop TSP Solver:** Uses Held-Karp Dynamic Programming (`python-tsp`) over pairwise A\* cost matrices to compute optimal multi-stop tour sequences.
- **Interactive Folium Visualizations:** Generates 3 standalone HTML maps (`criteria_comparison.html`, `algorithm_comparison.html`, `tsp_route.html`) and Matplotlib benchmark plots (`benchmark_chart.png`).

---

## Mathematical Formulation

### 1. Piecewise Fuel Consumption Model
Since OpenStreetMap does not natively store fuel telemetry, fuel consumption per kilometer is modeled as a piecewise function of road speed $v$ ($\text{km/h}$):

$$f(v) = \begin{cases} 0.12 \text{ L/km} & \text{if } v < 20 \text{ (Stop-and-go)} \\ 0.09 \text{ L/km} & \text{if } 20 \le v < 50 \text{ (Urban)} \\ 0.07 \text{ L/km} & \text{if } 50 \le v < 80 \text{ (Optimal cruising)} \\ 0.08 \text{ L/km} & \text{if } 80 \le v < 120 \text{ (Highway)} \\ 0.11 \text{ L/km} & \text{if } v \ge 120 \text{ (High aerodynamic drag)} \end{cases}$$

### 2. Admissible A\* Heuristics
To guarantee optimality under the Triangle Inequality ($h(u) \le c(u, v) + h(v)$), the heuristic $h(n)$ uses great-circle **Haversine distance** $d_{\text{hav}}(n, \text{goal})$ scaled by the minimum possible unit cost:
- **Distance:** $h_{\text{dist}}(n) = d_{\text{hav}}(n, \text{goal})$
- **Time:** $h_{\text{time}}(n) = \frac{d_{\text{hav}}(n, \text{goal})}{v_{\max}}$ where $v_{\max} = 130\text{ km/h}$
- **Fuel:** $h_{\text{fuel}}(n) = \frac{d_{\text{hav}}(n, \text{goal})}{1000} \times 0.07\text{ L/km}$

### 3. Held-Karp TSP Complexity
Given $N$ waypoints, pairwise optimal routes are computed via A\*, and Held-Karp dynamic programming solves the exact tour in $\mathcal{O}(N^2 \cdot 2^N)$ time and $\mathcal{O}(N \cdot 2^N)$ space.

---

## Project Structure

```text
route-optimizer/
├── data/
│   └── graph.graphml            # Cached OpenStreetMap road network
├── notebooks/
│   └── benchmark_analysis.ipynb # Interactive benchmark analysis
├── output/
│   ├── criteria_comparison.html # Map 1: Time vs Fuel vs Distance
│   ├── algorithm_comparison.html# Map 2: Dijkstra vs A* explored nodes
│   ├── tsp_route.html           # Map 3: Multi-stop Held-Karp TSP tour
│   └── benchmark_chart.png      # Matplotlib node reduction chart
├── src/
│   ├── __init__.py
│   ├── graph_loader.py          # OSMnx ingestion, caching & SCC filtering
│   ├── fuel_model.py            # Piecewise speed-to-fuel edge weights
│   ├── router.py                # Custom Dijkstra, A*, and TSP solver
│   ├── visualizer.py            # Folium HTML map generators
│   └── utils.py                 # Haversine & admissible A* heuristics
├── main.py                      # CLI entry point & benchmarking suite
├── requirements.txt
└── README.md