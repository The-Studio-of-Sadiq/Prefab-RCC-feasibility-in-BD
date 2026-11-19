# Road-Network Logistics Feasibility Analysis for Precast Concrete Construction in Dhaka

**Research Context**: Delivery feasibility of large-format precast concrete elements (slabs up to 15 m length, wall panels up to 4.3 m × 3.0 m, 20 t trailer payloads, and 30 t mobile cranes) across the Dhaka Metropolitan Area road network (extracted roads $\ge 16\text{ ft} \approx 4.88\text{ m}$).

## 1. Network Overview & Geodesic Verification

- **Total Network Length**: 1,235.67 km (3,441 road segments)
- **Precomputed Length (`_km` sum)**: 1,235.67 km
- **Haversine Cross-Check Discrepancy**: `-3.92747863e-10%` (Max segment absolute difference: 0.0000 mm, confirming exact geodesic parity)
- **Data Spatial Extent (Bounding Box)**: Longitude [90.2712105°E, 90.5157053°E], Latitude [23.6325328°N, 23.937444°N]

### Breakdown by OSM Highway Class

| Highway Class | Segment Count | Length (km) | Network Share (%) | Logistics Role |
| :--- | :---: | :---: | :---: | :--- |
| `tertiary` | 1,082 | 373.39 | 30.22% | Urban collector / Distributor |
| `primary` | 491 | 240.99 | 19.50% | Regional arterial / Heavy freight |
| `secondary` | 572 | 219.80 | 17.79% | Urban collector / Distributor |
| `trunk` | 250 | 178.89 | 14.48% | Regional arterial / Heavy freight |
| `residential` | 342 | 77.28 | 6.25% | Local / Minor access |
| `motorway` | 85 | 76.89 | 6.22% | Regional arterial / Heavy freight |
| `motorway_link` | 61 | 15.29 | 1.24% | Interchange / Link ramp |
| `unclassified` | 29 | 14.62 | 1.18% | Local / Minor access |
| `trunk_link` | 104 | 14.42 | 1.17% | Interchange / Link ramp |
| `primary_link` | 168 | 8.89 | 0.72% | Interchange / Link ramp |
| `secondary_link` | 141 | 7.19 | 0.58% | Interchange / Link ramp |
| `service` | 22 | 5.12 | 0.41% | Local / Minor access |
| `living_street` | 12 | 1.87 | 0.15% | Local / Minor access |
| `tertiary_link` | 82 | 1.02 | 0.08% | Interchange / Link ramp |

## 2. Road Selection Qualifications & Width Distribution

Roads qualified for the $\ge 16\text{ ft}$ (4.88 m) dataset through three distinct qualification pathways (`_cat`):

| Qualification Method (`_cat`) | Description | Segment Count | Length (km) | Share (%) |
| :--- | :--- | :---: | :---: | :---: |
| `lanes` | Inferred from $\ge 2$ lanes (~10 ft/lane) | 1,329 | 620.10 | 50.18% |
| `class` | Inferred from functional class (motorway, trunk, primary, secondary, tertiary) | 1,969 | 590.85 | 47.82% |
| `tagged` | Explicit OSM width tag parsed $\ge 16\text{ ft}$ (4.88 m) | 143 | 24.72 | 2.00% |

### Width Attribute Coverage & Empirical Distribution

- **Segments with Explicit Numeric Width (`_width_m`)**: 143 segments (4.16% of network count, 24.72 km / 2.00% of length)
- **Segments with Null / Inferred Width**: 3298 segments (95.84% of network count)
- **Empirical Width Summary (Tagged subset)**: Minimum = 4.88 m, Median = 5.50 m, Mean = 7.57 m, Maximum = 25.00 m

#### Binned Width Distribution Against Statutory & Operational Thresholds

| Width Bracket | Count | Share of Tagged (%) | Statutory & Engineering Significance |
| :--- | :---: | :---: | :--- |
| `< 4.9 m` | 3 | 2.1% | Borderline internal threshold (BNBC minimum internal road is 4.8 m / ~16 ft) |
| `4.9 – 7.3 m` | 95 | 66.4% | Single to narrow two-lane corridor; restricted passing for heavy trailers |
| `7.3 – 10.8 m` | 24 | 16.8% | Two-lane standard collector; adequate for 20 t trailer transport |
| `> 10.8 m` | 21 | 14.7% | BNBC approach-road threshold (>35.4 ft) for heavy access & crane operations |

## 3. Surface Types and Structural Infrastructure Tags

### Surface Material Breakdown

| Surface Type | Segment Count | Length (km) | Share (%) | Precast Heavy Haulage Suitability |
| :--- | :---: | :---: | :---: | :--- |
| `asphalt` | 1,420 | 624.95 | 50.58% | Suitable (High bearing capacity) |
| `unknown` | 1,701 | 498.98 | 40.38% | Data Caveat (Unspecified in OSM, ground check required) |
| `paved` | 227 | 59.21 | 4.79% | Suitable (High bearing capacity) |
| `concrete` | 75 | 48.33 | 3.91% | Suitable (High bearing capacity) |
| `concrete:lanes` | 8 | 2.81 | 0.23% | Suitable (High bearing capacity) |
| `concrete:plates` | 4 | 0.83 | 0.07% | Suitable (High bearing capacity) |
| `unpaved` | 4 | 0.34 | 0.03% | Unsuitable / High Risk for 20t loads |
| `gravel` | 1 | 0.13 | 0.01% | Unsuitable / High Risk for 20t loads |
| `metal` | 1 | 0.08 | 0.01% | Unsuitable / High Risk for 20t loads |

### Structural Constraints: Bridge & Weight Capacity Tags

- **Bridge Segments (`bridge=*`)**: 356 segments, 111.01 km (8.98% of network length)
  - `bridge=yes`: 354 segments, 110.98 km
  - `bridge=viaduct`: 1 segments, 0.016 km
  - `bridge=covered`: 1 segments, 0.012 km
- **Standard `maxweight` Tags**: `not available in data` (0 road segments carry statutory gross vehicle weight ratings).
- **Auxiliary Weight Attributes Found**: 
  - `maxweight:signed=no`: 3 segment(s), 0.085 km
  - `maxweightrating:hgv=4.8`: 1 segment(s), 0.072 km

> [!WARNING]
> The total absence of formal `maxweight` bridge load-rating tags in OpenStreetMap represents a critical empirical blindspot for 20 t payload precast transporters and 30 t mobile crane outrigger loading. Pre-route bridge inspection is essential prior to haulage.

## 4. Heavy-Vehicle Corridors vs. Secondary / Tertiary Networks

| Network Category | Functional Classes Included | Segment Count | Length (km) | Network Share (%) |
| :--- | :--- | :---: | :---: | :---: |
| **Heavy-Vehicle Corridor** | Motorway, Trunk, Primary (+ links) | 1,159 | 535.37 | 43.33% |
| **Secondary & Tertiary** | Secondary, Tertiary (+ links) | 1,877 | 601.40 | 48.67% |
| **Other Qualifying Roads** | Residential, Unclassified, Service, Living Street | 405 | 98.90 | 8.00% |
| **Total Network** | All classes >= 16 ft | 3,441 | 1,235.67 | 100.00% |

## 5. Network Connectivity & Topological Graph Analysis

Topological nodes were established by snapping segment vertices rounded to $10^{-5}$ degrees (~1.1 m spatial resolution).

| Graph Scope | Total Nodes | Total Segments | Connected Components | Largest Component (km) | Largest Component Share (%) | Largest Component Segments |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **All Roads (>= 16 ft)** | 32,481 | 3,441 | 92 | 1,200.85 km | **97.18%** | 3,317 (96.4%) |
| **Heavy Corridor Only** | 13,408 | 1,159 | 4 | 531.96 km | **99.36%** | 1,156 (99.7%) |

> [!NOTE]
> The all-roads network forms an integrated core with **97.18%** of all road length in a single connected graph. The remaining 91 components comprise isolated dead-ends and peripheral spurs truncated by the extraction bounding box.

## 6. Origin–Destination Logistics Routing Analysis (Dijkstra vs. Straight-Line)

Candidate precast manufacturing sites at Dhaka's industrial periphery evaluated against key urban densification demand clusters:

### Node Snapping Diagnostics

| Point Type | Location Name | Latitude (°N) | Longitude (°E) | Snapped Node (Lon, Lat) | Snap Distance (km) | Component Membership |
| :--- | :--- | :---: | :---: | :--- | :---: | :--- |
| Factory | **Savar EPZ** | 23.8667 | 90.2667 | `(90.31101, 23.87525)` | 4.6048 km (4605 m) | Component 8 (Isolated Peripheral Spur) |
| Factory | **Gazipur/Tongi** | 23.9000 | 90.4050 | `(90.40373, 23.90046)` | 0.1389 km (139 m) | Component 0 (Main Connected Network) |
| Factory | **Narayanganj/Kanchpur** | 23.7000 | 90.5167 | `(90.51571, 23.70179)` | 0.2231 km (223 m) | Component 0 (Main Connected Network) |
| Demand | **Mirpur** | 23.8069 | 90.3687 | `(90.36867, 23.80696)` | 0.0073 km (7 m) | Component 0 (Main Connected Network) |
| Demand | **Gulshan** | 23.7925 | 90.4078 | `(90.40828, 23.79244)` | 0.0493 km (49 m) | Component 0 (Main Connected Network) |
| Demand | **Dhanmondi** | 23.7465 | 90.3760 | `(90.37255, 23.74463)` | 0.4081 km (408 m) | Component 0 (Main Connected Network) |

### Origin–Destination Shortest Path Matrix

| Origin Factory | Urban Demand Point | Straight-Line (km) | Dijkstra Network Dist (km) | Circuity Factor (Net / Straight) | Reachability Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| Savar EPZ | Mirpur | 12.32 | `Disconnected` | `N/A` | <span style='color:red'>**Disconnected**</span> |
| Savar EPZ | Gulshan | 16.55 | `Disconnected` | `N/A` | <span style='color:red'>**Disconnected**</span> |
| Savar EPZ | Dhanmondi | 17.39 | `Disconnected` | `N/A` | <span style='color:red'>**Disconnected**</span> |
| Gazipur/Tongi | Mirpur | 10.99 | **14.34 km** | 1.30 | <span style='color:green'>Accessible</span> |
| Gazipur/Tongi | Gulshan | 11.96 | **15.05 km** | 1.26 | <span style='color:green'>Accessible</span> |
| Gazipur/Tongi | Dhanmondi | 17.32 | **22.41 km** | 1.29 | <span style='color:green'>Accessible</span> |
| Narayanganj/Kanchpur | Mirpur | 19.19 | **23.19 km** | 1.21 | <span style='color:green'>Accessible</span> |
| Narayanganj/Kanchpur | Gulshan | 15.12 | **20.88 km** | 1.38 | <span style='color:green'>Accessible</span> |
| Narayanganj/Kanchpur | Dhanmondi | 15.23 | **17.47 km** | 1.15 | <span style='color:green'>Accessible</span> |

### Operational Logistics Insights & Data Caveats

1. **Savar EPZ Disconnection**: Savar EPZ (23.8667°N, 90.2667°E) is located 4.60 km west of the nearest extracted road segment (`(90.31101, 23.87525)`). That road belongs to an isolated peripheral cluster cut off from the Dhaka urban network by the extraction bounding box (`west=90.33`). As specified in the methodology, disconnected origins are reported as `Disconnected` without fabrication. If regional trunk connections along N5 (Dhaka-Aricha Highway) were included, Savar would route to Mirpur in ~16.6 km.
2. **Gazipur/Tongi Advantage for Northern/Eastern Hubs**: Gazipur/Tongi achieves optimal reachability to Mirpur (14.34 km, circuity 1.30) and Gulshan (15.05 km, circuity 1.26) utilizing the primary Dhaka–Mymensingh corridor (N3/AH2).
3. **Narayanganj/Kanchpur Advantage for Southern Hubs**: Narayanganj/Kanchpur provides direct heavy access into Dhanmondi (17.47 km, circuity 1.15) and Gulshan (20.88 km, circuity 1.38) via the Dhaka–Chittagong corridor (N1).
4. **Circuity Factors**: Connected routes exhibit modest circuity (1.15 to 1.38), indicating good radial directness along the primary arterials.
5. **Width and Height Clearance Caveat**: While 97.18% of the road network is topologically connected, 95.84% of segments lack explicit width tags and almost 100% lack maxweight tags. Delivering 15 m long precast slabs on 20 t trailers requires site-specific swept-path simulation for sharp intersections and manual bridge assessment.
