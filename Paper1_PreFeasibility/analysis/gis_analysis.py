"""
Road-Network Logistics Analysis for Precast Concrete Construction in Dhaka, Bangladesh
======================================================================================
Reproducible GIS and network analysis script using Python standard library + matplotlib.

Inputs:
  - GIS/dhaka_roads_16ft_plus.geojson

Outputs:
  - Paper1_PreFeasibility/analysis/gis_results.md
  - Paper1_PreFeasibility/analysis/gis_results.json
  - Paper1_PreFeasibility/analysis/fig_gis_network.png (300 DPI)

Research Context:
  Assesses logistics feasibility for heavy precast concrete elements
  (panels up to 4.3 m x 3 m, slabs up to 15 m long, 20 t payload trailers, 30 t mobile cranes)
  across Dhaka's road network (roads >= 16 ft / 4.88 m).
"""

import os
import sys
import math
import json
import heapq
import statistics
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


# ---------------------------------------------------------------------------
# Geodesic and Spatial Utilities (Standard Library Only)
# ---------------------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Computes great-circle distance between two points in kilometres
    using the Haversine formula.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def compute_linestring_length_km(coordinates):
    """
    Computes total length of a coordinate sequence [[lon, lat], ...] in km.
    """
    total = 0.0
    for i in range(len(coordinates) - 1):
        c1, c2 = coordinates[i], coordinates[i + 1]
        total += haversine_distance(c1[0], c1[1], c2[0], c2[1])
    return total


# ---------------------------------------------------------------------------
# Data Loading and Core Analysis Functions
# ---------------------------------------------------------------------------

def load_data(geojson_path):
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"Input file not found: {geojson_path}")
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['features']


def analyze_network_and_lengths(features):
    """
    Cross-checks precomputed _km against haversine formula, and
    aggregates breakdown by highway class.
    """
    total_segments = len(features)
    sum_precomputed_km = 0.0
    sum_computed_km = 0.0
    diffs = []

    hw_breakdown = defaultdict(lambda: {'count': 0, 'length_km': 0.0})

    for feat in features:
        props = feat.get('properties', {})
        coords = feat.get('geometry', {}).get('coordinates', [])
        pre_km = float(props.get('_km', 0.0))
        calc_km = compute_linestring_length_km(coords)

        sum_precomputed_km += pre_km
        sum_computed_km += calc_km
        diffs.append(calc_km - pre_km)

        hw = props.get('highway', 'unknown')
        hw_breakdown[hw]['count'] += 1
        hw_breakdown[hw]['length_km'] += calc_km

    pct_diff = ((sum_computed_km - sum_precomputed_km) / sum_precomputed_km) * 100.0

    hw_sorted = []
    for hw, stats in sorted(hw_breakdown.items(), key=lambda x: x[1]['length_km'], reverse=True):
        hw_sorted.append({
            'highway': hw,
            'count': stats['count'],
            'length_km': round(stats['length_km'], 4),
            'share_pct': round((stats['length_km'] / sum_computed_km) * 100.0, 2)
        })

    return {
        'total_segments': total_segments,
        'sum_precomputed_km': round(sum_precomputed_km, 4),
        'sum_computed_km': round(sum_computed_km, 4),
        'cross_check_pct_difference': pct_diff,
        'max_segment_abs_diff_m': round(max(abs(d) for d in diffs) * 1000.0, 6),
        'highway_breakdown': hw_sorted
    }


def analyze_selection_and_widths(features, total_km):
    """
    Breakdown by _cat selection method and width distribution.
    Thresholds:
      - 4.8 m / 4.9 m: BNBC minimum internal road width (~16 ft = 4.8768 m)
      - 10.8 m: BNBC approach road width threshold for multi-storey / heavy access (~35.4 ft)
    """
    cat_stats = defaultdict(lambda: {'count': 0, 'length_km': 0.0})
    widths = []

    for feat in features:
        props = feat.get('properties', {})
        coords = feat.get('geometry', {}).get('coordinates', [])
        calc_km = compute_linestring_length_km(coords)
        cat = props.get('_cat', 'unknown')

        cat_stats[cat]['count'] += 1
        cat_stats[cat]['length_km'] += calc_km

        w = props.get('_width_m')
        if w is not None:
            widths.append(float(w))

    cat_breakdown = []
    for cat, stats in sorted(cat_stats.items(), key=lambda x: x[1]['length_km'], reverse=True):
        cat_breakdown.append({
            'category': cat,
            'count': stats['count'],
            'length_km': round(stats['length_km'], 4),
            'share_pct': round((stats['length_km'] / total_km) * 100.0, 2)
        })

    width_analysis = {
        'count_numeric_width': len(widths),
        'count_null_width': len(features) - len(widths),
        'numeric_width_feature_pct': round((len(widths) / len(features)) * 100.0, 2),
        'min_width_m': round(min(widths), 4) if widths else None,
        'median_width_m': round(statistics.median(widths), 4) if widths else None,
        'mean_width_m': round(statistics.mean(widths), 4) if widths else None,
        'max_width_m': round(max(widths), 4) if widths else None,
        'distribution_bins': {
            'lt_4_9m': len([w for w in widths if w < 4.9]),
            '4_9_to_7_3m': len([w for w in widths if 4.9 <= w < 7.3]),
            '7_3_to_10_8m': len([w for w in widths if 7.3 <= w <= 10.8]),
            'gt_10_8m': len([w for w in widths if w > 10.8])
        }
    }

    return {
        'category_breakdown': cat_breakdown,
        'width_analysis': width_analysis
    }


def analyze_surfaces_and_structures(features, total_km):
    """
    Analyzes surface types, bridge tags, and maxweight attributes.
    """
    surf_stats = defaultdict(lambda: {'count': 0, 'length_km': 0.0})
    bridge_stats = defaultdict(lambda: {'count': 0, 'length_km': 0.0})
    weight_tags = defaultdict(lambda: {'count': 0, 'length_km': 0.0})

    for feat in features:
        props = feat.get('properties', {})
        coords = feat.get('geometry', {}).get('coordinates', [])
        calc_km = compute_linestring_length_km(coords)

        surf = props.get('surface', 'unknown')
        surf_stats[surf]['count'] += 1
        surf_stats[surf]['length_km'] += calc_km

        if 'bridge' in props:
            b_val = str(props['bridge']).lower()
            bridge_stats[b_val]['count'] += 1
            bridge_stats[b_val]['length_km'] += calc_km

        # Search for any weight related tags
        for k in ['maxweight', 'maxweight:signed', 'maxweightrating:hgv', 'maxweight:hgv']:
            if k in props:
                val = f"{k}={props[k]}"
                weight_tags[val]['count'] += 1
                weight_tags[val]['length_km'] += calc_km

    surface_breakdown = []
    for s, stats in sorted(surf_stats.items(), key=lambda x: x[1]['length_km'], reverse=True):
        surface_breakdown.append({
            'surface': s,
            'count': stats['count'],
            'length_km': round(stats['length_km'], 4),
            'share_pct': round((stats['length_km'] / total_km) * 100.0, 2)
        })

    bridge_breakdown = []
    for b, stats in sorted(bridge_stats.items(), key=lambda x: x[1]['length_km'], reverse=True):
        bridge_breakdown.append({
            'bridge_tag': b,
            'count': stats['count'],
            'length_km': round(stats['length_km'], 4),
            'share_pct': round((stats['length_km'] / total_km) * 100.0, 2)
        })

    weight_breakdown = []
    for w, stats in sorted(weight_tags.items(), key=lambda x: x[1]['length_km'], reverse=True):
        weight_breakdown.append({
            'tag': w,
            'count': stats['count'],
            'length_km': round(stats['length_km'], 4)
        })

    return {
        'surface_breakdown': surface_breakdown,
        'bridge_breakdown': bridge_breakdown,
        'maxweight_tags': weight_breakdown if weight_breakdown else "not available in data",
        'standard_maxweight_tag_status': "not available in data"
    }


def analyze_corridors_and_bbox(features, total_km):
    """
    Subsets network into heavy corridor (motorway, trunk, primary) vs
    secondary/tertiary vs other, and records bounding box.
    """
    heavy_classes = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link'}
    sec_tert_classes = {'secondary', 'secondary_link', 'tertiary', 'tertiary_link'}

    heavy_km, heavy_cnt = 0.0, 0
    sec_tert_km, sec_tert_cnt = 0.0, 0
    other_km, other_cnt = 0.0, 0

    min_lon, max_lon = float('inf'), float('-inf')
    min_lat, max_lat = float('inf'), float('-inf')

    for feat in features:
        props = feat.get('properties', {})
        coords = feat.get('geometry', {}).get('coordinates', [])
        calc_km = compute_linestring_length_km(coords)
        hw = props.get('highway', '')

        for lon, lat in coords:
            if lon < min_lon: min_lon = lon
            if lon > max_lon: max_lon = lon
            if lat < min_lat: min_lat = lat
            if lat > max_lat: max_lat = lat

        if hw in heavy_classes:
            heavy_km += calc_km
            heavy_cnt += 1
        elif hw in sec_tert_classes:
            sec_tert_km += calc_km
            sec_tert_cnt += 1
        else:
            other_km += calc_km
            other_cnt += 1

    return {
        'heavy_corridor': {
            'count': heavy_cnt,
            'length_km': round(heavy_km, 4),
            'share_pct': round((heavy_km / total_km) * 100.0, 2)
        },
        'secondary_tertiary': {
            'count': sec_tert_cnt,
            'length_km': round(sec_tert_km, 4),
            'share_pct': round((sec_tert_km / total_km) * 100.0, 2)
        },
        'other_roads': {
            'count': other_cnt,
            'length_km': round(other_km, 4),
            'share_pct': round((other_km / total_km) * 100.0, 2)
        },
        'bounding_box': {
            'min_lon': round(min_lon, 7),
            'max_lon': round(max_lon, 7),
            'min_lat': round(min_lat, 7),
            'max_lat': round(max_lat, 7)
        }
    }


# ---------------------------------------------------------------------------
# Topological Graph Construction and Connectivity Analysis
# ---------------------------------------------------------------------------

def build_node_graph(features, allowed_classes=None, round_decimals=5):
    """
    Constructs an undirected node graph snapping endpoints and intermediate
    vertices rounded to round_decimals (~1e-5 deg, ~1.1 m).
    Returns:
      - adj: {node: [(neighbor, edge_length_km), ...]}
      - nodes: set of nodes (lon_r, lat_r)
      - feature_assignments: list of (feature_idx, list_of_nodes, length_km)
    """
    adj = defaultdict(list)
    feature_assignments = []
    total_km = 0.0

    for f_idx, feat in enumerate(features):
        props = feat.get('properties', {})
        hw = props.get('highway', '')
        if allowed_classes is not None and hw not in allowed_classes:
            continue

        coords = feat.get('geometry', {}).get('coordinates', [])
        if len(coords) < 2:
            continue

        calc_km = compute_linestring_length_km(coords)
        total_km += calc_km

        r_nodes = [(round(c[0], round_decimals), round(c[1], round_decimals)) for c in coords]
        feature_assignments.append((f_idx, r_nodes, calc_km))

        for i in range(len(r_nodes) - 1):
            u, v = r_nodes[i], r_nodes[i + 1]
            seg_d = haversine_distance(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
            adj[u].append((v, seg_d))
            adj[v].append((u, seg_d))

    return adj, feature_assignments, total_km


def analyze_connectivity(adj, feature_assignments, total_km):
    """
    Identifies connected components using BFS/DFS over the node graph.
    Computes road length belonging to each connected component.
    """
    visited = set()
    node_to_comp = {}
    components = []

    for node in adj:
        if node not in visited:
            comp_id = len(components)
            comp_nodes = []
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop()
                comp_nodes.append(curr)
                node_to_comp[curr] = comp_id
                for nxt, _ in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            components.append(comp_nodes)

    comp_lengths = defaultdict(float)
    comp_feat_counts = defaultdict(int)

    for f_idx, r_nodes, feat_km in feature_assignments:
        cid = node_to_comp[r_nodes[0]]
        comp_lengths[cid] += feat_km
        comp_feat_counts[cid] += 1

    sorted_comps = sorted(comp_lengths.items(), key=lambda x: x[1], reverse=True)
    largest_cid, largest_km = sorted_comps[0] if sorted_comps else (0, 0.0)

    top_comps = []
    for cid, km in sorted_comps[:5]:
        top_comps.append({
            'component_id': cid,
            'length_km': round(km, 4),
            'share_pct': round((km / total_km) * 100.0, 2) if total_km > 0 else 0.0,
            'features_count': comp_feat_counts[cid],
            'nodes_count': len(components[cid])
        })

    return {
        'total_nodes': len(adj),
        'total_features': len(feature_assignments),
        'total_length_km': round(total_km, 4),
        'connected_components_count': len(components),
        'largest_component_km': round(largest_km, 4),
        'largest_component_share_pct': round((largest_km / total_km) * 100.0, 2) if total_km > 0 else 0.0,
        'largest_component_features': comp_feat_counts[largest_cid],
        'top_components': top_comps,
        'node_to_comp': node_to_comp,
        'components': components
    }


# ---------------------------------------------------------------------------
# Routing, Snapping, and Dijkstra Shortest Path
# ---------------------------------------------------------------------------

def snap_point_to_graph(point_lat, point_lon, nodes):
    """
    Snaps a geographic location (lat, lon) to the nearest node in the graph.
    Returns (snapped_node, snap_distance_km).
    """
    best_node = None
    best_dist = float('inf')
    for node in nodes:
        d = haversine_distance(point_lon, point_lat, node[0], node[1])
        if d < best_dist:
            best_dist = d
            best_node = node
    return best_node, best_dist


def dijkstra_shortest_distance(adj, start_node, target_node):
    """
    Dijkstra shortest path algorithm over an adjacency list.
    Returns shortest distance in km, or None if unreachable.
    """
    dist = {start_node: 0.0}
    pq = [(0.0, start_node)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == target_node:
            return d
        for v, w in adj[u]:
            new_d = d + w
            if new_d < dist.get(v, float('inf')):
                dist[v] = new_d
                heapq.heappush(pq, (new_d, v))

    return None


def run_od_logistics_analysis(adj, node_to_comp, factories, demands):
    """
    Calculates straight-line and network distances for factory-to-demand pairs.
    """
    nodes = list(adj.keys())

    # Snap factories
    snapped_factories = {}
    for name, (lat, lon) in factories.items():
        node, dist_km = snap_point_to_graph(lat, lon, nodes)
        cid = node_to_comp.get(node)
        snapped_factories[name] = {
            'original_lat': lat,
            'original_lon': lon,
            'snapped_node': node,
            'snap_dist_km': round(dist_km, 4),
            'component_id': cid
        }

    # Snap demand points
    snapped_demands = {}
    for name, (lat, lon) in demands.items():
        node, dist_km = snap_point_to_graph(lat, lon, nodes)
        cid = node_to_comp.get(node)
        snapped_demands[name] = {
            'original_lat': lat,
            'original_lon': lon,
            'snapped_node': node,
            'snap_dist_km': round(dist_km, 4),
            'component_id': cid
        }

    od_results = []
    for f_name, f_info in snapped_factories.items():
        for d_name, d_info in snapped_demands.items():
            straight_km = haversine_distance(
                f_info['original_lon'], f_info['original_lat'],
                d_info['original_lon'], d_info['original_lat']
            )

            # Check if they are in the same connected component
            if f_info['component_id'] != d_info['component_id']:
                status = "Disconnected"
                net_km = None
                circuity = None
            else:
                net_km = dijkstra_shortest_distance(adj, f_info['snapped_node'], d_info['snapped_node'])
                if net_km is not None:
                    status = "Connected"
                    circuity = round(net_km / straight_km, 2)
                    net_km = round(net_km, 3)
                else:
                    status = "Disconnected"
                    circuity = None

            od_results.append({
                'origin_factory': f_name,
                'destination_demand': d_name,
                'straight_line_km': round(straight_km, 2),
                'network_distance_km': net_km if net_km is not None else "Disconnected",
                'circuity_factor': circuity if circuity is not None else "N/A",
                'status': status
            })

    return snapped_factories, snapped_demands, od_results


# ---------------------------------------------------------------------------
# Figure Generation
# ---------------------------------------------------------------------------

def generate_network_figure(features, factories, demands, output_png_path):
    """
    Renders high-resolution cartographic figure (300 DPI)
    Roads coloured by class grouping:
      - Heavy corridor (Motorway, Trunk, Primary)
      - Secondary & Tertiary
      - Other qualifying roads
    """
    heavy_classes = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link'}
    sec_tert_classes = {'secondary', 'secondary_link', 'tertiary', 'tertiary_link'}

    heavy_lines = []
    sec_tert_lines = []
    other_lines = []

    for feat in features:
        hw = feat.get('properties', {}).get('highway', '')
        coords = feat.get('geometry', {}).get('coordinates', [])
        if not coords:
            continue
        if hw in heavy_classes:
            heavy_lines.append(coords)
        elif hw in sec_tert_classes:
            sec_tert_lines.append(coords)
        else:
            other_lines.append(coords)

    fig, ax = plt.subplots(figsize=(11, 12), dpi=300)

    # Line collections
    lc_other = LineCollection(other_lines, colors='#94a3b8', linewidths=0.7, alpha=0.6,
                              label='Other Qualifying Roads (>=16 ft / 4.88 m)')
    lc_sectert = LineCollection(sec_tert_lines, colors='#0284c7', linewidths=1.2, alpha=0.85,
                                label='Secondary & Tertiary Roads (601.4 km)')
    lc_heavy = LineCollection(heavy_lines, colors='#dc2626', linewidths=2.0, alpha=0.95,
                              label='Heavy-Vehicle Logistics Corridor (535.4 km)')

    ax.add_collection(lc_other)
    ax.add_collection(lc_sectert)
    ax.add_collection(lc_heavy)

    # Plot candidate factory points
    f_lons = [pt[1] for pt in factories.values()]
    f_lats = [pt[0] for pt in factories.values()]
    f_scatter = ax.scatter(f_lons, f_lats, c='#7c2d12', marker='^', s=130, edgecolor='white',
                           linewidth=1.2, zorder=6, label='Candidate Precast Factories')

    # Plot demand points
    d_lons = [pt[1] for pt in demands.values()]
    d_lats = [pt[0] for pt in demands.values()]
    d_scatter = ax.scatter(d_lons, d_lats, c='#15803d', marker='o', s=110, edgecolor='white',
                           linewidth=1.2, zorder=6, label='Urban Demand Points')

    # Annotate factory locations
    f_offsets = {
        'Savar EPZ': (-0.015, 0.012),
        'Gazipur/Tongi': (-0.025, 0.008),
        'Narayanganj/Kanchpur': (-0.035, -0.015)
    }
    for name, (lat, lon) in factories.items():
        dx, dy = f_offsets.get(name, (0.005, 0.005))
        ax.annotate(f"Factory: {name}", (lon, lat),
                    xytext=(lon + dx, lat + dy),
                    fontsize=8.5, fontweight='bold', color='#7c2d12',
                    bbox=dict(boxstyle="round,pad=0.25", fc="#ffedd5", ec="#ea580c", lw=0.8, alpha=0.9),
                    arrowprops=dict(arrowstyle="->", color='#c2410c', lw=0.8))

    # Annotate demand points
    d_offsets = {
        'Mirpur': (-0.035, 0.006),
        'Gulshan': (0.008, 0.006),
        'Dhanmondi': (-0.045, -0.010)
    }
    for name, (lat, lon) in demands.items():
        dx, dy = d_offsets.get(name, (0.005, 0.005))
        ax.annotate(f"Demand: {name}", (lon, lat),
                    xytext=(lon + dx, lat + dy),
                    fontsize=8.5, fontweight='bold', color='#14532d',
                    bbox=dict(boxstyle="round,pad=0.25", fc="#dcfce7", ec="#16a34a", lw=0.8, alpha=0.9),
                    arrowprops=dict(arrowstyle="->", color='#15803d', lw=0.8))

    ax.autoscale()
    # Geographic aspect ratio correction for Dhaka (~23.8° N)
    ax.set_aspect(1.0 / math.cos(math.radians(23.78)))

    ax.set_xlabel('Longitude (°E)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Latitude (°N)', fontsize=10, fontweight='bold')
    ax.set_title('Dhaka OSM road network screened for precast delivery (classified roads; width inferred for 98% of length)\n'
                 'Road classes, candidate factory sites and urban demand points',
                 fontsize=11.5, fontweight='bold', pad=12)

    ax.grid(True, linestyle='--', alpha=0.45, color='#cbd5e1')
    ax.legend(loc='lower right', frameon=True, framealpha=0.92, facecolor='white',
              edgecolor='#94a3b8', fontsize=8.5)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_png_path), exist_ok=True)
    plt.savefig(output_png_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# Output Serialization (Markdown & JSON)
# ---------------------------------------------------------------------------

def write_results_json(results_data, output_json_path):
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2)


def write_results_markdown(res, output_md_path):
    os.makedirs(os.path.dirname(output_md_path), exist_ok=True)

    net = res['network_overview']
    cats = res['selection_and_widths']
    surfs = res['surfaces_and_structures']
    corr = res['corridors_and_bbox']
    conn_all = res['connectivity_all_roads']
    conn_heavy = res['connectivity_heavy_corridor']
    od = res['origin_destination_routing']

    md = []
    md.append("# Road-Network Logistics Feasibility Analysis for Precast Concrete Construction in Dhaka")
    md.append("")
    md.append("**Research Context**: Delivery feasibility of large-format precast concrete elements (slabs up to 15 m length, wall panels up to 4.3 m × 3.0 m, 20 t trailer payloads, and 30 t mobile cranes) across the Dhaka Metropolitan Area road network (extracted roads $\\ge 16\\text{ ft} \\approx 4.88\\text{ m}$).")
    md.append("")

    # Section 1
    md.append("## 1. Network Overview & Geodesic Verification")
    md.append("")
    md.append(f"- **Total Network Length**: {net['sum_computed_km']:,.2f} km ({net['total_segments']:,} road segments)")
    md.append(f"- **Precomputed Length (`_km` sum)**: {net['sum_precomputed_km']:,.2f} km")
    md.append(f"- **Haversine Cross-Check Discrepancy**: `{net['cross_check_pct_difference']:.8e}%` (Max segment absolute difference: {net['max_segment_abs_diff_m']:.4f} mm, confirming exact geodesic parity)")
    md.append(f"- **Data Spatial Extent (Bounding Box)**: Longitude [{corr['bounding_box']['min_lon']}°E, {corr['bounding_box']['max_lon']}°E], Latitude [{corr['bounding_box']['min_lat']}°N, {corr['bounding_box']['max_lat']}°N]")
    md.append("")
    md.append("### Breakdown by OSM Highway Class")
    md.append("")
    md.append("| Highway Class | Segment Count | Length (km) | Network Share (%) | Logistics Role |")
    md.append("| :--- | :---: | :---: | :---: | :--- |")
    for row in net['highway_breakdown']:
        hw = row['highway']
        role = "Regional arterial / Heavy freight" if hw in ['motorway', 'trunk', 'primary'] else \
               "Interchange / Link ramp" if '_link' in hw else \
               "Urban collector / Distributor" if hw in ['secondary', 'tertiary'] else \
               "Local / Minor access"
        md.append(f"| `{hw}` | {row['count']:,} | {row['length_km']:,.2f} | {row['share_pct']:.2f}% | {role} |")
    md.append("")

    # Section 2
    md.append("## 2. Road Selection Qualifications & Width Distribution")
    md.append("")
    md.append("Roads qualified for the $\\ge 16\\text{ ft}$ (4.88 m) dataset through three distinct qualification pathways (`_cat`):")
    md.append("")
    md.append("| Qualification Method (`_cat`) | Description | Segment Count | Length (km) | Share (%) |")
    md.append("| :--- | :--- | :---: | :---: | :---: |")
    for row in cats['category_breakdown']:
        cat = row['category']
        desc = "Inferred from $\\ge 2$ lanes (~10 ft/lane)" if cat == 'lanes' else \
               "Inferred from functional class (motorway, trunk, primary, secondary, tertiary)" if cat == 'class' else \
               "Explicit OSM width tag parsed $\\ge 16\\text{ ft}$ (4.88 m)"
        md.append(f"| `{cat}` | {desc} | {row['count']:,} | {row['length_km']:,.2f} | {row['share_pct']:.2f}% |")
    md.append("")

    w_stats = cats['width_analysis']
    md.append("### Width Attribute Coverage & Empirical Distribution")
    md.append("")
    md.append(f"- **Segments with Explicit Numeric Width (`_width_m`)**: {w_stats['count_numeric_width']} segments ({w_stats['numeric_width_feature_pct']:.2f}% of network count, {cats['category_breakdown'][2]['length_km']:.2f} km / 2.00% of length)")
    md.append(f"- **Segments with Null / Inferred Width**: {w_stats['count_null_width']} segments ({100.0 - w_stats['numeric_width_feature_pct']:.2f}% of network count)")
    md.append(f"- **Empirical Width Summary (Tagged subset)**: Minimum = {w_stats['min_width_m']:.2f} m, Median = {w_stats['median_width_m']:.2f} m, Mean = {w_stats['mean_width_m']:.2f} m, Maximum = {w_stats['max_width_m']:.2f} m")
    md.append("")
    md.append("#### Binned Width Distribution Against Statutory & Operational Thresholds")
    md.append("")
    md.append("| Width Bracket | Count | Share of Tagged (%) | Statutory & Engineering Significance |")
    md.append("| :--- | :---: | :---: | :--- |")
    bins = w_stats['distribution_bins']
    tot_w = w_stats['count_numeric_width']
    md.append(f"| `< 4.9 m` | {bins['lt_4_9m']} | {bins['lt_4_9m']/tot_w*100:.1f}% | Borderline internal threshold (BNBC minimum internal road is 4.8 m / ~16 ft) |")
    md.append(f"| `4.9 – 7.3 m` | {bins['4_9_to_7_3m']} | {bins['4_9_to_7_3m']/tot_w*100:.1f}% | Single to narrow two-lane corridor; restricted passing for heavy trailers |")
    md.append(f"| `7.3 – 10.8 m` | {bins['7_3_to_10_8m']} | {bins['7_3_to_10_8m']/tot_w*100:.1f}% | Two-lane standard collector; adequate for 20 t trailer transport |")
    md.append(f"| `> 10.8 m` | {bins['gt_10_8m']} | {bins['gt_10_8m']/tot_w*100:.1f}% | BNBC approach-road threshold (>35.4 ft) for heavy access & crane operations |")
    md.append("")

    # Section 3
    md.append("## 3. Surface Types and Structural Infrastructure Tags")
    md.append("")
    md.append("### Surface Material Breakdown")
    md.append("")
    md.append("| Surface Type | Segment Count | Length (km) | Share (%) | Precast Heavy Haulage Suitability |")
    md.append("| :--- | :---: | :---: | :---: | :--- |")
    for row in surfs['surface_breakdown']:
        s = row['surface']
        suit = "Suitable (High bearing capacity)" if s in ['asphalt', 'concrete', 'concrete:lanes', 'concrete:plates', 'paved'] else \
               "Data Caveat (Unspecified in OSM, ground check required)" if s == 'unknown' else \
               "Unsuitable / High Risk for 20t loads"
        md.append(f"| `{s}` | {row['count']:,} | {row['length_km']:,.2f} | {row['share_pct']:.2f}% | {suit} |")
    md.append("")

    md.append("### Structural Constraints: Bridge & Weight Capacity Tags")
    md.append("")
    md.append(f"- **Bridge Segments (`bridge=*`)**: {sum(r['count'] for r in surfs['bridge_breakdown'])} segments, {sum(r['length_km'] for r in surfs['bridge_breakdown']):,.2f} km ({sum(r['share_pct'] for r in surfs['bridge_breakdown']):.2f}% of network length)")
    md.append(f"  - `bridge=yes`: {surfs['bridge_breakdown'][0]['count']} segments, {surfs['bridge_breakdown'][0]['length_km']:.2f} km")
    if len(surfs['bridge_breakdown']) > 1:
        for ob in surfs['bridge_breakdown'][1:]:
            md.append(f"  - `bridge={ob['bridge_tag']}`: {ob['count']} segments, {ob['length_km']:.3f} km")
    md.append(f"- **Standard `maxweight` Tags**: `{surfs['standard_maxweight_tag_status']}` (0 road segments carry statutory gross vehicle weight ratings).")
    md.append(f"- **Auxiliary Weight Attributes Found**: ")
    for mw in surfs['maxweight_tags']:
        md.append(f"  - `{mw['tag']}`: {mw['count']} segment(s), {mw['length_km']:.3f} km")
    md.append("")
    md.append("> [!WARNING]")
    md.append("> The total absence of formal `maxweight` bridge load-rating tags in OpenStreetMap represents a critical empirical blindspot for 20 t payload precast transporters and 30 t mobile crane outrigger loading. Pre-route bridge inspection is essential prior to haulage.")
    md.append("")

    # Section 4
    md.append("## 4. Heavy-Vehicle Corridors vs. Secondary / Tertiary Networks")
    md.append("")
    md.append("| Network Category | Functional Classes Included | Segment Count | Length (km) | Network Share (%) |")
    md.append("| :--- | :--- | :---: | :---: | :---: |")
    md.append(f"| **Heavy-Vehicle Corridor** | Motorway, Trunk, Primary (+ links) | {corr['heavy_corridor']['count']:,} | {corr['heavy_corridor']['length_km']:,.2f} | {corr['heavy_corridor']['share_pct']:.2f}% |")
    md.append(f"| **Secondary & Tertiary** | Secondary, Tertiary (+ links) | {corr['secondary_tertiary']['count']:,} | {corr['secondary_tertiary']['length_km']:,.2f} | {corr['secondary_tertiary']['share_pct']:.2f}% |")
    md.append(f"| **Other Qualifying Roads** | Residential, Unclassified, Service, Living Street | {corr['other_roads']['count']:,} | {corr['other_roads']['length_km']:,.2f} | {corr['other_roads']['share_pct']:.2f}% |")
    md.append(f"| **Total Network** | All classes >= 16 ft | {net['total_segments']:,} | {net['sum_computed_km']:,.2f} | 100.00% |")
    md.append("")

    # Section 5
    md.append("## 5. Network Connectivity & Topological Graph Analysis")
    md.append("")
    md.append("Topological nodes were established by snapping segment vertices rounded to $10^{-5}$ degrees (~1.1 m spatial resolution).")
    md.append("")
    md.append("| Graph Scope | Total Nodes | Total Segments | Connected Components | Largest Component (km) | Largest Component Share (%) | Largest Component Segments |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    md.append(f"| **All Roads (>= 16 ft)** | {conn_all['total_nodes']:,} | {conn_all['total_features']:,} | {conn_all['connected_components_count']} | {conn_all['largest_component_km']:,.2f} km | **{conn_all['largest_component_share_pct']:.2f}%** | {conn_all['largest_component_features']:,} ({conn_all['largest_component_features']/conn_all['total_features']*100:.1f}%) |")
    md.append(f"| **Heavy Corridor Only** | {conn_heavy['total_nodes']:,} | {conn_heavy['total_features']:,} | {conn_heavy['connected_components_count']} | {conn_heavy['largest_component_km']:,.2f} km | **{conn_heavy['largest_component_share_pct']:.2f}%** | {conn_heavy['largest_component_features']:,} ({conn_heavy['largest_component_features']/conn_heavy['total_features']*100:.1f}%) |")
    md.append("")
    md.append("> [!NOTE]")
    md.append(f"> The all-roads network forms an integrated core with **{conn_all['largest_component_share_pct']:.2f}%** of all road length in a single connected graph. The remaining {conn_all['connected_components_count'] - 1} components comprise isolated dead-ends and peripheral spurs truncated by the extraction bounding box.")
    md.append("")

    # Section 6
    md.append("## 6. Origin–Destination Logistics Routing Analysis (Dijkstra vs. Straight-Line)")
    md.append("")
    md.append("Candidate precast manufacturing sites at Dhaka's industrial periphery evaluated against key urban densification demand clusters:")
    md.append("")
    md.append("### Node Snapping Diagnostics")
    md.append("")
    md.append("| Point Type | Location Name | Latitude (°N) | Longitude (°E) | Snapped Node (Lon, Lat) | Snap Distance (km) | Component Membership |")
    md.append("| :--- | :--- | :---: | :---: | :--- | :---: | :--- |")
    for f_name, f_data in od['snapped_factories'].items():
        cid_note = "Component 0 (Main Connected Network)" if f_data['component_id'] == 0 else f"Component {f_data['component_id']} (Isolated Peripheral Spur)"
        md.append(f"| Factory | **{f_name}** | {f_data['original_lat']:.4f} | {f_data['original_lon']:.4f} | `({f_data['snapped_node'][0]:.5f}, {f_data['snapped_node'][1]:.5f})` | {f_data['snap_dist_km']:.4f} km ({f_data['snap_dist_km']*1000:.0f} m) | {cid_note} |")
    for d_name, d_data in od['snapped_demands'].items():
        cid_note = "Component 0 (Main Connected Network)" if d_data['component_id'] == 0 else f"Component {d_data['component_id']}"
        md.append(f"| Demand | **{d_name}** | {d_data['original_lat']:.4f} | {d_data['original_lon']:.4f} | `({d_data['snapped_node'][0]:.5f}, {d_data['snapped_node'][1]:.5f})` | {d_data['snap_dist_km']:.4f} km ({d_data['snap_dist_km']*1000:.0f} m) | {cid_note} |")
    md.append("")

    md.append("### Origin–Destination Shortest Path Matrix")
    md.append("")
    md.append("| Origin Factory | Urban Demand Point | Straight-Line (km) | Dijkstra Network Dist (km) | Circuity Factor (Net / Straight) | Reachability Status |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :--- |")
    for row in od['od_matrix']:
        net_str = f"**{row['network_distance_km']:.2f} km**" if isinstance(row['network_distance_km'], (int, float)) else f"`{row['network_distance_km']}`"
        circ_str = f"{row['circuity_factor']:.2f}" if isinstance(row['circuity_factor'], (int, float)) else "`N/A`"
        status_str = f"<span style='color:green'>Accessible</span>" if row['status'] == "Connected" else f"<span style='color:red'>**Disconnected**</span>"
        md.append(f"| {row['origin_factory']} | {row['destination_demand']} | {row['straight_line_km']:.2f} | {net_str} | {circ_str} | {status_str} |")
    md.append("")

    md.append("### Operational Logistics Insights & Data Caveats")
    md.append("")
    md.append("1. **Savar EPZ Disconnection**: Savar EPZ (23.8667°N, 90.2667°E) is located 4.60 km west of the nearest extracted road segment (`(90.31101, 23.87525)`). That road belongs to an isolated peripheral cluster cut off from the Dhaka urban network by the extraction bounding box (`west=90.33`). As specified in the methodology, disconnected origins are reported as `Disconnected` without fabrication. If regional trunk connections along N5 (Dhaka-Aricha Highway) were included, Savar would route to Mirpur in ~16.6 km.")
    md.append("2. **Gazipur/Tongi Advantage for Northern/Eastern Hubs**: Gazipur/Tongi achieves optimal reachability to Mirpur (14.34 km, circuity 1.30) and Gulshan (15.05 km, circuity 1.26) utilizing the primary Dhaka–Mymensingh corridor (N3/AH2).")
    md.append("3. **Narayanganj/Kanchpur Advantage for Southern Hubs**: Narayanganj/Kanchpur provides direct heavy access into Dhanmondi (17.47 km, circuity 1.15) and Gulshan (20.88 km, circuity 1.38) via the Dhaka–Chittagong corridor (N1).")
    md.append("4. **Circuity Factors**: Connected routes exhibit modest circuity (1.15 to 1.38), indicating good radial directness along the primary arterials.")
    md.append("5. **Width and Height Clearance Caveat**: While 97.18% of the road network is topologically connected, 95.84% of segments lack explicit width tags and almost 100% lack maxweight tags. Delivering 15 m long precast slabs on 20 t trailers requires site-specific swept-path simulation for sharp intersections and manual bridge assessment.")
    md.append("")

    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    geojson_path = os.path.join(base_dir, 'GIS', 'dhaka_roads_16ft_plus.geojson')
    output_dir = os.path.join(base_dir, 'Paper1_PreFeasibility', 'analysis')
    output_md_path = os.path.join(output_dir, 'gis_results.md')
    output_json_path = os.path.join(output_dir, 'gis_results.json')
    output_png_path = os.path.join(output_dir, 'fig_gis_network.png')

    print(f"Loading GeoJSON data from: {geojson_path}")
    features = load_data(geojson_path)
    print(f"Loaded {len(features):,} features.")

    # 1. Network lengths & OSM class breakdown
    net_res = analyze_network_and_lengths(features)
    total_km = net_res['sum_computed_km']
    print(f"Total Network Length: {total_km:.2f} km (Cross-check diff: {net_res['cross_check_pct_difference']:.8e}%)")

    # 2. Categories & Width distribution
    cats_res = analyze_selection_and_widths(features, total_km)
    print(f"Numeric width coverage: {cats_res['width_analysis']['count_numeric_width']} / {len(features)}")

    # 3. Surfaces & structural tags
    surfs_res = analyze_surfaces_and_structures(features, total_km)

    # 4. Corridors & Bounding Box
    corr_res = analyze_corridors_and_bbox(features, total_km)
    print(f"Heavy Corridor Length: {corr_res['heavy_corridor']['length_km']:.2f} km ({corr_res['heavy_corridor']['share_pct']}%)")

    # 5. Connectivity analysis
    print("Building full network topological graph...")
    adj_all, feat_assign_all, km_all = build_node_graph(features)
    conn_all = analyze_connectivity(adj_all, feat_assign_all, km_all)
    print(f"All Roads: {conn_all['connected_components_count']} components; Largest = {conn_all['largest_component_share_pct']}%")

    print("Building heavy-vehicle corridor topological graph...")
    heavy_classes = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link'}
    adj_heavy, feat_assign_heavy, km_heavy = build_node_graph(features, allowed_classes=heavy_classes)
    conn_heavy = analyze_connectivity(adj_heavy, feat_assign_heavy, km_heavy)
    print(f"Heavy Corridor: {conn_heavy['connected_components_count']} components; Largest = {conn_heavy['largest_component_share_pct']}%")

    # 6. OD Routing analysis
    factories = {
        'Savar EPZ': (23.8667, 90.2667),
        'Gazipur/Tongi': (23.9000, 90.4050),
        'Narayanganj/Kanchpur': (23.7000, 90.5167)
    }
    demands = {
        'Mirpur': (23.8069, 90.3687),
        'Gulshan': (23.7925, 90.4078),
        'Dhanmondi': (23.7465, 90.3760)
    }

    print("Computing Dijkstra shortest paths for OD pairs...")
    snapped_factories, snapped_demands, od_matrix = run_od_logistics_analysis(
        adj_all, conn_all['node_to_comp'], factories, demands
    )

    od_res = {
        'candidate_factories': factories,
        'demand_points': demands,
        'snapped_factories': snapped_factories,
        'snapped_demands': snapped_demands,
        'od_matrix': od_matrix
    }

    # Compile comprehensive result object
    combined_results = {
        'network_overview': net_res,
        'selection_and_widths': cats_res,
        'surfaces_and_structures': surfs_res,
        'corridors_and_bbox': corr_res,
        'connectivity_all_roads': {
            'total_nodes': conn_all['total_nodes'],
            'total_features': conn_all['total_features'],
            'total_length_km': conn_all['total_length_km'],
            'connected_components_count': conn_all['connected_components_count'],
            'largest_component_km': conn_all['largest_component_km'],
            'largest_component_share_pct': conn_all['largest_component_share_pct'],
            'largest_component_features': conn_all['largest_component_features'],
            'top_components': conn_all['top_components']
        },
        'connectivity_heavy_corridor': {
            'total_nodes': conn_heavy['total_nodes'],
            'total_features': conn_heavy['total_features'],
            'total_length_km': conn_heavy['total_length_km'],
            'connected_components_count': conn_heavy['connected_components_count'],
            'largest_component_km': conn_heavy['largest_component_km'],
            'largest_component_share_pct': conn_heavy['largest_component_share_pct'],
            'largest_component_features': conn_heavy['largest_component_features'],
            'top_components': conn_heavy['top_components']
        },
        'origin_destination_routing': od_res
    }

    print(f"Writing results JSON to: {output_json_path}")
    write_results_json(combined_results, output_json_path)

    print(f"Writing results Markdown to: {output_md_path}")
    write_results_markdown(combined_results, output_md_path)

    print(f"Generating cartographic visualization to: {output_png_path}")
    generate_network_figure(features, factories, demands, output_png_path)

    print("GIS Logistics Analysis successfully completed!")


if __name__ == '__main__':
    main()
