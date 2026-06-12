"""D* Lite path planning for hazard-aware evacuation routing.

Implements the D* Lite algorithm on a road graph with dynamic hazard
mask updates. Plans safe evacuation routes from building entrances
to park exits while avoiding gas-affected road segments.

Key features:
    - Road network graph construction from rectangular segments.
    - Dynamic danger mask with blocked nodes and edges.
    - D* Lite incremental search for efficient replanning.
    - Multi-exit candidate ranking by distance and risk.

Typical usage:
    result = plan_evacuation_route(payload)
    results = plan_evacuation_routes_by_building(payload)
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


EVACUATION_WALKING_SPEED_MPS = 1.35
EVACUATION_PLANNER_NAME = "road-dstar-lite-hazard-mask-py-v1"
MAP_METERS_PER_UNIT = 0.5


def plan_evacuation_route(payload: Dict) -> Dict:
    """Plan a single evacuation route from a start point to park exits.

    Builds the road graph, computes danger mask from gas concentration,
    and ranks candidate routes to all park entrances.

    Args:
        payload: Request dict with startPoint, parkEntrances, roads,
            frame, gas, blockedMask, and startLabel.

    Returns:
        Route result with path, distance, estimated time, risk level,
        and candidate routes.
    """
    start_point = payload.get("startPoint")
    park_entrances = payload.get("parkEntrances") or []
    if not start_point:
        return create_failed_route("未提供逃生起点")
    if not park_entrances:
        return create_failed_route("未配置园区出口")

    graph = build_road_graph(payload.get("roads") or [])
    if not graph["nodeIds"]:
        return create_failed_route("道路网络为空")

    gas = payload.get("gas") or {}
    danger_mask = build_danger_mask(
        graph=graph,
        frame=payload.get("frame"),
        gas=gas,
        blocked_mask=payload.get("blockedMask"),
    )

    start_node_id = find_nearest_node_id(graph, start_point)
    if not start_node_id:
        return create_failed_route("未找到可用道路节点")
    if start_node_id in danger_mask["blockedNodeIds"]:
        return create_failed_route("建筑入口已位于危险浓度区，当前无法规划安全逃生路线", danger_mask)

    candidate_routes: List[Dict] = []
    for index, exit_ in enumerate(park_entrances):
        exit_point = {"x": exit_.get("x", 0), "y": exit_.get("y", 0)}
        exit_node_id = find_nearest_node_id(graph, exit_point)
        if not exit_node_id or exit_node_id in danger_mask["blockedNodeIds"]:
            continue

        planner = create_dstar_planner(graph, exit_node_id)
        node_path = run_dstar_lite_search(
            planner=planner,
            graph=graph,
            start_node_id=start_node_id,
            goal_node_id=exit_node_id,
            danger_mask=danger_mask,
        )
        if not node_path:
            continue

        route = build_route_result(
            graph=graph,
            start_point=start_point,
            start_label=payload.get("startLabel", "--"),
            start_node_id=start_node_id,
            exit_=exit_,
            exit_node_id=exit_node_id,
            node_path=node_path,
            danger_mask=danger_mask,
            gas=gas,
            frame=payload.get("frame"),
        )
        route["candidateId"] = route["exitId"] or f"route-{index + 1}"
        candidate_routes.append(route)

    if candidate_routes:
        ranked_routes = sorted(candidate_routes, key=lambda route: route["distanceMeters"])
        for index, route in enumerate(ranked_routes):
            route["rank"] = index + 1
            route["candidateId"] = route.get("candidateId") or route.get("exitId") or f"route-{index + 1}"
        best_route = ranked_routes[0]
        result = dict(best_route)
        result["candidateRoutes"] = ranked_routes
        result["recommendedCandidateId"] = best_route["candidateId"]
        return result

    return create_failed_route("所有园区出口均被危险浓度路段阻断", danger_mask)


def plan_evacuation_routes_by_building(payload: Dict) -> Dict:
    """Plan evacuation routes for all building entrances.

    Iterates over buildingEntrances, computes individual routes,
    and returns per-building results with summary statistics.

    Args:
        payload: Request dict with buildingEntrances, facilities, roads,
            parkEntrances, frame, gas, and blockedMask.

    Returns:
        Aggregated result with routesByBuilding, success/blocked counts,
        and recommended exits.
    """
    facilities = payload.get("facilities") or []
    facility_by_id = {facility.get("id"): facility for facility in facilities}
    routes_by_building: List[Dict] = []

    for index, entrance in enumerate(payload.get("buildingEntrances") or []):
        facility = facility_by_id.get(entrance.get("parentId"))
        route = plan_evacuation_route(
            {
                "roads": payload.get("roads"),
                "parkEntrances": payload.get("parkEntrances"),
                "startPoint": {"x": entrance.get("x", 0), "y": entrance.get("y", 0)},
                "startLabel": entrance.get("label") or f"{facility.get('name', '建筑')} 出入口" if facility else "建筑出入口",
                "frame": payload.get("frame"),
                "gas": payload.get("gas"),
                "blockedMask": payload.get("blockedMask"),
            }
        )
        route["buildingId"] = entrance.get("parentId") or f"building-{index + 1}"
        route["buildingName"] = facility.get("name") if facility else entrance.get("label", f"建筑 {index + 1}")
        route["entranceId"] = entrance.get("id") or f"entrance-{index + 1}"
        route["entranceLabel"] = entrance.get("label") or f"{route['buildingName']} 出入口"
        route["status"] = "success" if route.get("success") else "blocked"
        route["message"] = "" if route.get("success") else route.get("message", "当前无安全逃生路径")
        routes_by_building.append(route)

    success_routes = [route for route in routes_by_building if route.get("success")]
    blocked_routes = [route for route in routes_by_building if not route.get("success")]
    return {
        "success": bool(routes_by_building),
        "hasAnySuccess": bool(success_routes),
        "planner": EVACUATION_PLANNER_NAME,
        "message": "" if success_routes else "当前帧所有建筑均无安全逃生路径",
        "totalBuildings": len(routes_by_building),
        "successCount": len(success_routes),
        "blockedCount": len(blocked_routes),
        "routesByBuilding": routes_by_building,
        "blockedBuildingIds": [route["buildingId"] for route in blocked_routes],
        "recommendedExits": summarize_recommended_exits(success_routes),
    }


def build_road_graph(roads: Sequence[Dict]) -> Dict:
    """Build a road graph from rectangular road segments.

    Converts road rectangles to line segments, finds intersections,
    and constructs a graph with nodes, edges, and adjacency lists.

    Args:
        roads: List of road rectangles with position and dimensions.

    Returns:
        Graph dict with nodes, nodeIds, edges, adjacency, and signature.
    """
    road_segments = [segment for segment in (normalize_road_rect_to_segment(road) for road in roads) if segment]
    segment_points_map = {
        segment["id"]: [
            {"x": segment["x1"], "y": segment["y1"]},
            {"x": segment["x2"], "y": segment["y2"]},
        ]
        for segment in road_segments
    }

    for index, segment in enumerate(road_segments):
        for other in road_segments[index + 1 :]:
            intersection = find_segment_intersection(segment, other)
            if not intersection:
                continue
            segment_points_map[segment["id"]].append(intersection)
            segment_points_map[other["id"]].append(intersection)

    nodes: Dict[str, Dict] = {}
    edges: Dict[str, Dict] = {}
    adjacency: Dict[str, List[Dict]] = {}
    for segment in road_segments:
        ordered_points = sorted(
            unique_points(segment_points_map[segment["id"]]),
            key=lambda point: point["x"] if segment["orientation"] == "horizontal" else point["y"],
        )
        for point_index, point in enumerate(ordered_points):
            node_id = point_to_node_id(point)
            nodes.setdefault(node_id, {"id": node_id, "x": point["x"], "y": point["y"]})
            adjacency.setdefault(node_id, [])
            if point_index + 1 >= len(ordered_points):
                continue
            next_point = ordered_points[point_index + 1]
            distance = get_distance(point, next_point)
            if distance < 1:
                continue
            next_node_id = point_to_node_id(next_point)
            edge_id = create_edge_id(node_id, next_node_id)
            if edge_id in edges:
                continue
            edge = {
                "id": edge_id,
                "from": node_id,
                "to": next_node_id,
                "fromPoint": point,
                "toPoint": next_point,
                "distance": distance,
                "roadId": segment["id"],
            }
            edges[edge_id] = edge
            adjacency[node_id].append({"nodeId": next_node_id, "edgeId": edge_id, "distance": distance})
            adjacency.setdefault(next_node_id, [])
            adjacency[next_node_id].append({"nodeId": node_id, "edgeId": edge_id, "distance": distance})

    signature = build_road_signature(roads)
    return {"nodes": nodes, "nodeIds": list(nodes.keys()), "edges": edges, "adjacency": adjacency, "signature": signature}


def build_danger_mask(graph: Dict, frame: Optional[Dict], gas: Dict, blocked_mask: Optional[Dict]) -> Dict:
    """Build a danger mask identifying blocked nodes and edges.

    Checks each graph node and edge against gas concentration thresholds
    and the optional blocked mask grid.

    Args:
        graph: Road graph dict with nodes and edges.
        frame: Optional diffusion frame with cell concentration data.
        gas: Gas properties dict with blockingThreshold.
        blocked_mask: Optional grid-based blocked mask.

    Returns:
        Danger mask dict with blockedNodeIds, blockedEdgeIds, and counts.
    """
    threshold = gas.get("blockingThreshold")
    if threshold is None:
        threshold = gas.get("dangerThreshold", math.inf)

    blocked_node_ids: Set[str] = set()
    blocked_edge_ids: Set[str] = set()
    if not frame or not math.isfinite(threshold):
        return {
            "threshold": None,
            "blockedNodeIds": blocked_node_ids,
            "blockedEdgeIds": blocked_edge_ids,
            "blockedNodeCount": 0,
            "blockedEdgeCount": 0,
        }

    for node in graph["nodes"].values():
        if is_blocked_point(node, blocked_mask) or get_frame_concentration_at_point(frame, node["x"], node["y"]) >= threshold:
            blocked_node_ids.add(node["id"])

    for edge in graph["edges"].values():
        blocked = any(
            is_blocked_point(point, blocked_mask) or get_frame_concentration_at_point(frame, point["x"], point["y"]) >= threshold
            for point in sample_edge_points(edge["fromPoint"], edge["toPoint"], 6)
        )
        if blocked:
            blocked_edge_ids.add(edge["id"])

    return {
        "threshold": threshold,
        "blockedNodeIds": blocked_node_ids,
        "blockedEdgeIds": blocked_edge_ids,
        "blockedNodeCount": len(blocked_node_ids),
        "blockedEdgeCount": len(blocked_edge_ids),
    }


def create_dstar_planner(graph: Dict, goal_node_id: str) -> Dict:
    """Create a D* Lite planner instance with goal configuration.

    Initializes g and rhs scores, sets the goal node, and pushes it
    onto the open list.

    Args:
        graph: Road graph dict with nodes and adjacency.
        goal_node_id: Target goal node identifier.

    Returns:
        Planner dict with scores, open list, and blocked sets.
    """
    g_score = {node_id: math.inf for node_id in graph["nodeIds"]}
    rhs_score = {node_id: math.inf for node_id in graph["nodeIds"]}
    rhs_score[goal_node_id] = 0.0
    planner = {
        "goalNodeId": goal_node_id,
        "currentStartNodeId": goal_node_id,
        "lastStartNodeId": goal_node_id,
        "km": 0.0,
        "gScore": g_score,
        "rhsScore": rhs_score,
        "openList": [],
        "blockedNodeIds": set(),
        "blockedEdgeIds": set(),
    }
    push_open_node(planner, goal_node_id, calculate_node_key(planner, graph, goal_node_id))
    return planner


def run_dstar_lite_search(
    planner: Dict,
    graph: Dict,
    start_node_id: str,
    goal_node_id: str,
    danger_mask: Dict,
) -> List[str]:
    """Run the D* Lite search algorithm.

    Updates planner for start/goal changes, applies danger mask updates,
    computes the shortest path, and reconstructs the result path.

    Args:
        planner: D* Lite planner dict with scores and open list.
        graph: Road graph dict with nodes, edges, and adjacency.
        start_node_id: Start node identifier.
        goal_node_id: Goal node identifier.
        danger_mask: Danger mask dict with blocked nodes and edges.

    Returns:
        List of node IDs forming the optimal path, or empty list.
    """
    if planner["goalNodeId"] != goal_node_id:
        planner = create_dstar_planner(graph, goal_node_id)
    update_planner_for_start_change(planner, graph, start_node_id)
    apply_danger_mask_updates(planner, graph, danger_mask)
    compute_shortest_path(planner, graph)
    return reconstruct_dstar_path(planner, graph, start_node_id, goal_node_id, danger_mask)


def build_route_result(
    graph: Dict,
    start_point: Dict,
    start_label: str,
    start_node_id: str,
    exit_: Dict,
    exit_node_id: str,
    node_path: Sequence[str],
    danger_mask: Dict,
    gas: Dict,
    frame: Optional[Dict],
) -> Dict:
    """Build a complete route result from a D* Lite path.

    Converts node path to world coordinates, computes distance and
    time, evaluates peak concentration and risk level.

    Args:
        graph: Road graph dict.
        start_point: Start point dict.
        start_label: Human-readable start label.
        start_node_id: Start node identifier.
        exit_: Exit point dict with id and label.
        exit_node_id: Exit node identifier.
        node_path: List of node IDs forming the path.
        danger_mask: Danger mask dict for metadata.
        gas: Gas properties dict.
        frame: Optional diffusion frame for concentration lookup.

    Returns:
        Route result dict with path, distance, time, risk, and metadata.
    """
    path_points = [{"x": round(float(start_point["x"]), 2), "y": round(float(start_point["y"]), 2)}]
    for node_id in node_path:
        node = graph["nodes"].get(node_id)
        if node:
            push_point(path_points, {"x": node["x"], "y": node["y"]})

    exit_point = {"x": float(exit_.get("x", 0)), "y": float(exit_.get("y", 0))}
    push_point(path_points, exit_point)
    world_distance = get_polyline_distance(path_points)
    distance_meters = round(world_distance * MAP_METERS_PER_UNIT, 2)
    estimated_time_sec = round(distance_meters / EVACUATION_WALKING_SPEED_MPS, 1)
    peak_concentration = 0.0
    if frame:
        peak_concentration = max(get_frame_concentration_at_point(frame, point["x"], point["y"]) for point in path_points)

    return {
        "success": True,
        "replanned": danger_mask["blockedNodeCount"] > 0 or danger_mask["blockedEdgeCount"] > 0,
        "planner": EVACUATION_PLANNER_NAME,
        "exitId": exit_.get("id", ""),
        "startLabel": start_label,
        "exitLabel": exit_.get("label", "--"),
        "startNodeId": start_node_id,
        "exitNodeId": exit_node_id,
        "path": path_points,
        "distanceMeters": distance_meters,
        "estimatedTimeSec": estimated_time_sec,
        "peakConcentration": round(peak_concentration, 2),
        "riskLevelText": build_risk_level_text(peak_concentration, gas),
        "dangerMask": {
            "threshold": danger_mask["threshold"],
            "blockedNodeCount": danger_mask["blockedNodeCount"],
            "blockedEdgeCount": danger_mask["blockedEdgeCount"],
        },
    }


def create_failed_route(message: str, danger_mask: Optional[Dict] = None) -> Dict:
    """Create a failed route result with error message.

    Args:
        message: Human-readable failure reason.
        danger_mask: Optional danger mask for metadata.

    Returns:
        Route result dict with success=False and error details.
    """
    return {
        "success": False,
        "message": message,
        "planner": EVACUATION_PLANNER_NAME,
        "startLabel": "--",
        "exitLabel": "--",
        "path": [],
        "distanceMeters": 0,
        "estimatedTimeSec": 0,
        "peakConcentration": 0,
        "riskLevelText": "未生成",
        "candidateRoutes": [],
        "recommendedCandidateId": "",
        "dangerMask": {
            "threshold": danger_mask["threshold"] if danger_mask else None,
            "blockedNodeCount": danger_mask["blockedNodeCount"] if danger_mask else 0,
            "blockedEdgeCount": danger_mask["blockedEdgeCount"] if danger_mask else 0,
        },
    }


def summarize_recommended_exits(routes: Sequence[Dict]) -> List[Dict]:
    """Summarize recommended exits by counting building assignments.

    Args:
        routes: List of successful route results with exit info.

    Returns:
        Sorted list of exit summaries by building count (descending).
    """
    counter: Dict[str, Dict] = {}
    for route in routes:
        key = route.get("exitId") or route.get("exitLabel") or "unknown"
        item = counter.setdefault(
            key,
            {
                "exitId": route.get("exitId", ""),
                "exitLabel": route.get("exitLabel", "--"),
                "buildingCount": 0,
            },
        )
        item["buildingCount"] += 1
    return sorted(counter.values(), key=lambda item: item["buildingCount"], reverse=True)


def normalize_road_rect_to_segment(road: Dict) -> Optional[Dict]:
    """Convert a rectangular road definition to a line segment.

    Args:
        road: Road dict with x, y, w, h.

    Returns:
        Segment dict with id, orientation, and endpoints, or None.
    """
    if not road:
        return None
    horizontal = float(road.get("w", 0)) >= float(road.get("h", 0))
    if horizontal:
        return {
            "id": road_id(road),
            "orientation": "horizontal",
            "x1": float(road.get("x", 0)),
            "y1": float(road.get("y", 0)) + float(road.get("h", 0)) / 2,
            "x2": float(road.get("x", 0)) + float(road.get("w", 0)),
            "y2": float(road.get("y", 0)) + float(road.get("h", 0)) / 2,
        }
    return {
        "id": road_id(road),
        "orientation": "vertical",
        "x1": float(road.get("x", 0)) + float(road.get("w", 0)) / 2,
        "y1": float(road.get("y", 0)),
        "x2": float(road.get("x", 0)) + float(road.get("w", 0)) / 2,
        "y2": float(road.get("y", 0)) + float(road.get("h", 0)),
    }


def find_segment_intersection(left: Dict, right: Dict) -> Optional[Dict]:
    """Find the intersection point of two perpendicular road segments.

    Args:
        left: First road segment dict.
        right: Second road segment dict.

    Returns:
        Intersection point dict, or None if no intersection.
    """
    if left["orientation"] == right["orientation"]:
        return None
    horizontal = left if left["orientation"] == "horizontal" else right
    vertical = left if left["orientation"] == "vertical" else right
    within_horizontal = min(horizontal["x1"], horizontal["x2"]) <= vertical["x1"] <= max(horizontal["x1"], horizontal["x2"])
    within_vertical = min(vertical["y1"], vertical["y2"]) <= horizontal["y1"] <= max(vertical["y1"], vertical["y2"])
    if not (within_horizontal and within_vertical):
        return None
    return {"x": round(vertical["x1"], 2), "y": round(horizontal["y1"], 2)}


def unique_points(points: Iterable[Dict]) -> List[Dict]:
    """Deduplicate a list of points by node ID.

    Args:
        points: Iterable of point dicts with 'x' and 'y'.

    Returns:
        List of unique point dicts.
    """
    point_map: Dict[str, Dict] = {}
    for point in points:
        point_map[point_to_node_id(point)] = {"x": round(float(point["x"]), 2), "y": round(float(point["y"]), 2)}
    return list(point_map.values())


def find_nearest_node_id(graph: Dict, point: Dict) -> str:
    """Find the nearest road graph node to a point.

    Args:
        graph: Road graph dict with nodes.
        point: Target point dict.

    Returns:
        Nearest node ID string.
    """
    nearest_node_id = ""
    min_distance = math.inf
    for node in graph["nodes"].values():
        distance = get_distance(point, node)
        if distance < min_distance:
            min_distance = distance
            nearest_node_id = node["id"]
    return nearest_node_id


def sample_edge_points(from_point: Dict, to_point: Dict, segments: int) -> List[Dict]:
    """Sample points along an edge at regular intervals.

    Args:
        from_point: Starting point dict.
        to_point: Ending point dict.
        segments: Number of segments to divide the edge into.

    Returns:
        List of sampled point dicts.
    """
    points: List[Dict] = []
    for index in range(segments + 1):
        ratio = index / max(segments, 1)
        points.append(
            {
                "x": round(from_point["x"] + (to_point["x"] - from_point["x"]) * ratio, 2),
                "y": round(from_point["y"] + (to_point["y"] - from_point["y"]) * ratio, 2),
            }
        )
    return points


def is_blocked_point(point: Dict, blocked_mask: Optional[Dict]) -> bool:
    """Check if a point falls within a blocked mask grid cell.

    Args:
        point: Point dict with 'x' and 'y'.
        blocked_mask: Mask dict with grid dimensions and value matrix.

    Returns:
        True if the grid cell at this point has value 1.
    """
    if not blocked_mask or not blocked_mask.get("values"):
        return False
    grid_size = blocked_mask.get("gridSize", 20)
    column_index = int(round((float(point["x"]) - grid_size / 2) / grid_size))
    row_index = int(round((float(point["y"]) - grid_size / 2) / grid_size))
    if row_index < 0 or row_index >= blocked_mask.get("rows", 0):
        return False
    if column_index < 0 or column_index >= blocked_mask.get("columns", 0):
        return False
    return blocked_mask["values"][row_index][column_index] == 1


def update_planner_for_start_change(planner: Dict, graph: Dict, next_start_node_id: str) -> None:
    """Update planner state when the start node changes.

    Adjusts the heuristic modifier km by the distance between old and
    new start nodes.

    Args:
        planner: D* Lite planner dict.
        graph: Road graph dict.
        next_start_node_id: New start node identifier.
    """
    if planner["currentStartNodeId"] == next_start_node_id:
        return
    current_node = graph["nodes"].get(planner["currentStartNodeId"])
    next_node = graph["nodes"].get(next_start_node_id)
    if current_node and next_node:
        planner["km"] += get_distance(current_node, next_node)
    planner["lastStartNodeId"] = planner["currentStartNodeId"]
    planner["currentStartNodeId"] = next_start_node_id


def apply_danger_mask_updates(planner: Dict, graph: Dict, danger_mask: Dict) -> None:
    """Apply danger mask updates to the planner and update affected vertices.

    Args:
        planner: D* Lite planner dict to update.
        graph: Road graph dict.
        danger_mask: Danger mask with blockedNodeIds and blockedEdgeIds.
    """
    planner["blockedNodeIds"] = set(danger_mask["blockedNodeIds"])
    planner["blockedEdgeIds"] = set(danger_mask["blockedEdgeIds"])
    affected_node_ids: Set[str] = set(planner["blockedNodeIds"])
    for edge_id in planner["blockedEdgeIds"]:
        edge = graph["edges"].get(edge_id)
        if not edge:
            continue
        affected_node_ids.add(edge["from"])
        affected_node_ids.add(edge["to"])
    for node_id in affected_node_ids:
        update_vertex(planner, graph, node_id)
        for predecessor_id in get_predecessor_node_ids(graph, node_id):
            update_vertex(planner, graph, predecessor_id)


def compute_shortest_path(planner: Dict, graph: Dict) -> None:
    """Compute the shortest path using D* Lite algorithm.

    Iteratively processes the open list until the start node is consistent
    or the open list is exhausted. Guard limits iterations to 50000.

    Args:
        planner: D* Lite planner dict.
        graph: Road graph dict.
    """
    guard = 0
    while planner["openList"] and (
        compare_keys(peek_open_key(planner), calculate_node_key(planner, graph, planner["currentStartNodeId"])) < 0
        or not are_costs_equal(get_rhs(planner, planner["currentStartNodeId"]), get_g(planner, planner["currentStartNodeId"]))
    ):
        guard += 1
        if guard > 50000:
            break
        current = pop_open_node(planner)
        if not current:
            break
        current_key = calculate_node_key(planner, graph, current["nodeId"])
        if compare_keys(current["key"], current_key) < 0:
            push_open_node(planner, current["nodeId"], current_key)
            continue
        g_value = get_g(planner, current["nodeId"])
        rhs_value = get_rhs(planner, current["nodeId"])
        predecessors = get_predecessor_node_ids(graph, current["nodeId"])
        if g_value > rhs_value:
            planner["gScore"][current["nodeId"]] = rhs_value
            for predecessor_id in predecessors:
                update_vertex(planner, graph, predecessor_id)
        else:
            planner["gScore"][current["nodeId"]] = math.inf
            update_vertex(planner, graph, current["nodeId"])
            for predecessor_id in predecessors:
                update_vertex(planner, graph, predecessor_id)


def reconstruct_dstar_path(planner: Dict, graph: Dict, start_node_id: str, goal_node_id: str, danger_mask: Dict) -> List[str]:
    """Reconstruct the optimal path from D* Lite scores.

    Greedily follows the neighbor with minimum distance + g-score,
    avoiding blocked nodes and edges.

    Args:
        planner: D* Lite planner dict with g-scores.
        graph: Road graph dict with adjacency.
        start_node_id: Start node identifier.
        goal_node_id: Goal node identifier.
        danger_mask: Danger mask for hazard avoidance.

    Returns:
        List of node IDs forming the path, or empty list if blocked.
    """
    if not math.isfinite(get_g(planner, start_node_id)) and not math.isfinite(get_rhs(planner, start_node_id)):
        return []
    path = [start_node_id]
    visited = {start_node_id}
    cursor = start_node_id
    guard = 0
    while cursor != goal_node_id and guard < len(graph["nodeIds"]) + 5:
        guard += 1
        neighbors = [
            neighbor
            for neighbor in graph["adjacency"].get(cursor, [])
            if neighbor["nodeId"] not in danger_mask["blockedNodeIds"] and neighbor["edgeId"] not in danger_mask["blockedEdgeIds"]
        ]
        best_neighbor = None
        best_score = math.inf
        for neighbor in neighbors:
            score = neighbor["distance"] + get_g(planner, neighbor["nodeId"])
            if score < best_score:
                best_score = score
                best_neighbor = neighbor
        if not best_neighbor or not math.isfinite(best_score) or best_neighbor["nodeId"] in visited:
            return []
        path.append(best_neighbor["nodeId"])
        visited.add(best_neighbor["nodeId"])
        cursor = best_neighbor["nodeId"]
    return path if cursor == goal_node_id else []


def update_vertex(planner: Dict, graph: Dict, node_id: str) -> None:
    """Update a vertex's rhs value and manage open list membership.

    Recomputes rhs from neighbor costs and adds/removes from open list
    based on consistency.

    Args:
        planner: D* Lite planner dict.
        graph: Road graph dict.
        node_id: Node identifier to update.
    """
    if node_id != planner["goalNodeId"]:
        best_rhs = math.inf
        for neighbor in graph["adjacency"].get(node_id, []):
            cost = get_traversal_cost(planner, neighbor["edgeId"], node_id, neighbor["nodeId"], neighbor["distance"])
            best_rhs = min(best_rhs, cost + get_g(planner, neighbor["nodeId"]))
        planner["rhsScore"][node_id] = best_rhs
    remove_open_node(planner, node_id)
    if not are_costs_equal(get_g(planner, node_id), get_rhs(planner, node_id)):
        push_open_node(planner, node_id, calculate_node_key(planner, graph, node_id))


def calculate_node_key(planner: Dict, graph: Dict, node_id: str) -> Tuple[float, float]:
    """Calculate the D* Lite priority key for a node.

    Key = (min(g, rhs) + heuristic + km, min(g, rhs)).

    Args:
        planner: D* Lite planner dict.
        graph: Road graph dict.
        node_id: Node identifier.

    Returns:
        Tuple of (primary_key, secondary_key).
    """
    node = graph["nodes"].get(node_id)
    start_node = graph["nodes"].get(planner["currentStartNodeId"])
    best = min(get_g(planner, node_id), get_rhs(planner, node_id))
    heuristic = get_distance(node, start_node) if node and start_node else 0.0
    return (best + heuristic + planner["km"], best)


def get_traversal_cost(planner: Dict, edge_id: str, from_node_id: str, to_node_id: str, base_distance: float) -> float:
    """Get the traversal cost for an edge, considering blocked status.

    Args:
        planner: D* Lite planner dict.
        edge_id: Edge identifier.
        from_node_id: Source node identifier.
        to_node_id: Target node identifier.
        base_distance: Base edge length.

    Returns:
        Edge distance if passable, infinity if blocked.
    """
    if from_node_id in planner["blockedNodeIds"]:
        return math.inf
    if to_node_id in planner["blockedNodeIds"]:
        return math.inf
    if edge_id in planner["blockedEdgeIds"]:
        return math.inf
    return base_distance


def get_predecessor_node_ids(graph: Dict, node_id: str) -> List[str]:
    """Get all predecessor node IDs for a given node.

    Args:
        graph: Road graph dict with adjacency.
        node_id: Target node identifier.

    Returns:
        List of predecessor node IDs.
    """
    return [item["nodeId"] for item in graph["adjacency"].get(node_id, [])]


def push_open_node(planner: Dict, node_id: str, key: Tuple[float, float]) -> None:
    """Push a node onto the D* Lite open list.

    Args:
        planner: D* Lite planner dict.
        node_id: Node identifier to push.
        key: Priority key tuple.
    """
    planner["openList"].append({"nodeId": node_id, "key": key})


def remove_open_node(planner: Dict, node_id: str) -> None:
    """Remove a node from the D* Lite open list.

    Args:
        planner: D* Lite planner dict.
        node_id: Node identifier to remove.
    """
    planner["openList"] = [item for item in planner["openList"] if item["nodeId"] != node_id]


def pop_open_node(planner: Dict) -> Optional[Dict]:
    """Pop the highest-priority node from the open list.

    Args:
        planner: D* Lite planner dict.

    Returns:
        Node dict with 'nodeId' and 'key', or None if empty.
    """
    if not planner["openList"]:
        return None
    planner["openList"].sort(key=lambda item: item["key"])
    return planner["openList"].pop(0)


def peek_open_key(planner: Dict) -> Tuple[float, float]:
    """Peek at the highest-priority key without removing.

    Args:
        planner: D* Lite planner dict.

    Returns:
        Priority key tuple, or (inf, inf) if open list is empty.
    """
    if not planner["openList"]:
        return (math.inf, math.inf)
    planner["openList"].sort(key=lambda item: item["key"])
    return tuple(planner["openList"][0]["key"])


def compare_keys(left: Tuple[float, float], right: Tuple[float, float]) -> float:
    """Compare two D* Lite priority keys.

    Args:
        left: First key tuple.
        right: Second key tuple.

    Returns:
        Negative if left < right, positive if left > right.
    """
    if left[0] != right[0]:
        return left[0] - right[0]
    return left[1] - right[1]


def get_g(planner: Dict, node_id: str) -> float:
    """Get the g-score (estimated cost-to-goal) for a node.

    Args:
        planner: D* Lite planner dict.
        node_id: Node identifier.

    Returns:
        G-score value, or infinity if not set.
    """
    return planner["gScore"].get(node_id, math.inf)


def get_rhs(planner: Dict, node_id: str) -> float:
    """Get the rhs-score (one-step lookahead cost) for a node.

    Args:
        planner: D* Lite planner dict.
        node_id: Node identifier.

    Returns:
        RHS value, or infinity if not set.
    """
    return planner["rhsScore"].get(node_id, math.inf)


def are_costs_equal(left: float, right: float) -> bool:
    """Check if two cost values are equal within tolerance.

    Both infinity counts as equal.

    Args:
        left: First cost value.
        right: Second cost value.

    Returns:
        True if costs are effectively equal.
    """
    if not math.isfinite(left) and not math.isfinite(right):
        return True
    return abs(left - right) < 1e-6


def get_frame_concentration_at_point(frame: Optional[Dict], x: float, y: float) -> float:
    """Get gas concentration at a point from frame cell data.

    Finds the nearest cell and returns its concentration.

    Args:
        frame: Diffusion frame dict with cells list.
        x: X-coordinate to query.
        y: Y-coordinate to query.

    Returns:
        Concentration value at the nearest cell, or 0.0.
    """
    cells = frame.get("cells") if frame else None
    if not cells:
        return 0.0
    nearest = None
    min_distance = math.inf
    for cell in cells:
        distance = math.hypot(float(cell.get("x", 0)) - x, float(cell.get("y", 0)) - y)
        if distance < min_distance:
            min_distance = distance
            nearest = cell
    return float(nearest.get("concentration", 0.0)) if nearest else 0.0


def build_risk_level_text(peak_concentration: float, gas: Dict) -> str:
    """Build a human-readable risk level text from concentration and gas data.

    Args:
        peak_concentration: Peak concentration along the path.
        gas: Gas properties dict with danger/warning thresholds.

    Returns:
        Chinese risk level string.
    """
    if not gas:
        return "未知"
    if peak_concentration >= float(gas.get("dangerThreshold", math.inf)):
        return "危险穿越"
    if peak_concentration >= float(gas.get("warningThreshold", math.inf)):
        return "预警临近"
    return "安全可达"


def build_road_signature(roads: Sequence[Dict]) -> str:
    """Build a deterministic signature string from road data.

    Args:
        roads: List of road dicts.

    Returns:
        Concatenated signature string.
    """
    return "|".join(
        f"{road_id(road)}:{road.get('x', 0)},{road.get('y', 0)},{road.get('w', 0)},{road.get('h', 0)}"
        for road in roads
    )


def get_polyline_distance(points: Sequence[Dict]) -> float:
    """Compute the total distance along a polyline.

    Args:
        points: List of point dicts forming the polyline.

    Returns:
        Total Euclidean distance along the polyline.
    """
    return sum(get_distance(points[index - 1], points[index]) for index in range(1, len(points)))


def get_distance(left: Optional[Dict], right: Optional[Dict]) -> float:
    """Compute Euclidean distance between two points.

    Args:
        left: First point dict, or None.
        right: Second point dict, or None.

    Returns:
        Euclidean distance, or 0.0 if either point is None.
    """
    if not left or not right:
        return 0.0
    return math.hypot(float(left["x"]) - float(right["x"]), float(left["y"]) - float(right["y"]))


def push_point(points: List[Dict], point: Dict) -> None:
    """Add a point to a list, avoiding near-duplicates within 0.5 units.

    Args:
        points: Mutable list of point dicts to append to.
        point: Point dict to add.
    """
    if points and get_distance(points[-1], point) < 0.5:
        return
    points.append({"x": round(float(point["x"]), 2), "y": round(float(point["y"]), 2)})


def point_to_node_id(point: Dict) -> str:
    """Convert a point dict to a unique node ID string.

    Args:
        point: Point dict with 'x' and 'y'.

    Returns:
        Formatted node ID like 'x.xx,y.yy'.
    """
    return f"{float(point['x']):.2f},{float(point['y']):.2f}"


def create_edge_id(from_node_id: str, to_node_id: str) -> str:
    """Create a canonical edge ID from two node IDs.

    Args:
        from_node_id: Source node identifier.
        to_node_id: Target node identifier.

    Returns:
        Sorted, joined edge ID string.
    """
    return "::".join(sorted([from_node_id, to_node_id]))


def road_id(road: Dict) -> str:
    """Get or generate a road identifier.

    Args:
        road: Road dict with optional 'id', or position/dimensions.

    Returns:
        Road ID string.
    """
    return str(road.get("id") or f"{road.get('x', 0)}-{road.get('y', 0)}-{road.get('w', 0)}-{road.get('h', 0)}")
