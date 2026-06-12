"""Gas diffusion simulation and A* path planning for chemical plants.

Integrates Gaussian plume dispersion modeling with A* path planning on
a factory road network. Provides hazard-aware escape routing with
multi-gas support (CH4, NH3, CO, O2).

Key components:
    - FactoryLayout: 2D factory road network and building map.
    - EnhancedGaussianPlumeModel: Atmospheric dispersion with stability
      classes, wind advection, and density corrections.
    - AStarPathPlanner: A* search on road graph with danger masks.
    - IntegratedEscapeSystem: Unified escape planning combining diffusion
      and path finding.

Typical usage:
    result = calculate_gas_and_path(data)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import heapq
import math
from typing import Dict, List, Optional, Set, Tuple

Point = Tuple[float, float]


class GasType(Enum):
    CH4 = "methane"
    NH3 = "ammonia"
    CO = "carbon_monoxide"
    O2 = "oxygen"


@dataclass
class GasProperties:
    molecular_weight: float = 28.97
    diffusion_coefficient: float = 0.18
    density_ratio: float = 1.0
    safety_threshold_ppm: float = 100.0
    idlh_threshold_ppm: float = 500.0
    decay_rate: float = 0.0008
    color: str = "#FF6B6B"
    name: str = "通用气体"


GAS_PROPERTIES_MAP: Dict[GasType, GasProperties] = {
    GasType.CH4: GasProperties(
        molecular_weight=16.04,
        diffusion_coefficient=0.24,
        density_ratio=0.55,
        safety_threshold_ppm=50.0,
        idlh_threshold_ppm=50000.0,
        decay_rate=0.0003,
        color="#E74C3C",
        name="甲烷(CH4)"
    ),
    GasType.NH3: GasProperties(
        molecular_weight=17.03,
        diffusion_coefficient=0.23,
        density_ratio=0.59,
        safety_threshold_ppm=25.0,
        idlh_threshold_ppm=300.0,
        decay_rate=0.0010,
        color="#9B59B6",
        name="氨气(NH3)"
    ),
    GasType.CO: GasProperties(
        molecular_weight=28.01,
        diffusion_coefficient=0.22,
        density_ratio=0.97,
        safety_threshold_ppm=35.0,
        idlh_threshold_ppm=1200.0,
        decay_rate=0.0007,
        color="#3498DB",
        name="一氧化碳(CO)"
    ),
    GasType.O2: GasProperties(
        molecular_weight=32.00,
        diffusion_coefficient=0.20,
        density_ratio=1.10,
        safety_threshold_ppm=120000.0,
        idlh_threshold_ppm=250000.0,
        decay_rate=0.0004,
        color="#2ECC71",
        name="氧气(O2)"
    ),
}


@dataclass
class DiffusionConfig:
    source_rate: float = 8.0
    stability: int = 4
    wind_angle: float = 90.0
    wind_speed: float = 3.0
    temperature: float = 293.15
    pressure: float = 101325.0
    terrain_roughness: float = 0.6
    release_height: float = 1.5
    max_radius: float = 220.0
    sample_resolution: int = 32


@dataclass
class DiffusionResult:
    high_concentration: List[List[Point]] = field(default_factory=list)
    medium_concentration: List[List[Point]] = field(default_factory=list)
    low_concentration: List[List[Point]] = field(default_factory=list)
    concentration_field: Dict[str, float] = field(default_factory=dict)
    max_concentration: float = 0.0
    affected_area: float = 0.0
    time_steps: int = 0


@dataclass
class Building:
    id: str
    name: str
    center: Point
    size: Tuple[float, float]
    exit_point: Point


@dataclass
class DiffusionSource:
    source_id: str
    building_id: str
    leak_point: Point
    gas_type: GasType


def _dist(a: Point, b: Point) -> float:
    """Compute Euclidean distance between two points.

    Args:
        a: First point as (x, y) tuple.
        b: Second point as (x, y) tuple.

    Returns:
        Euclidean distance between a and b.
    """
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _pt_key(p: Point) -> str:
    """Generate a string key for a point for deduplication.

    Args:
        p: Point as (x, y) tuple.

    Returns:
        String key with coordinates rounded to 2 decimals.
    """
    return f"{round(p[0], 2)}_{round(p[1], 2)}"


def _edge_key(a: Point, b: Point) -> Tuple[Point, Point]:
    """Generate a canonical unordered edge key from two points.

    Args:
        a: First point as (x, y) tuple.
        b: Second point as (x, y) tuple.

    Returns:
        Tuple of points sorted for consistent edge identification.
    """
    return (a, b) if a <= b else (b, a)


def _to_point(raw: object, default: Point) -> Point:
    """Convert a raw input to a point tuple.

    Accepts dicts with 'x'/'y' keys, lists/tuples with 2+ elements,
    or returns the default.

    Args:
        raw: Input data (dict, list, tuple, or other).
        default: Fallback point tuple.

    Returns:
        Point as (x, y) tuple.
    """
    if isinstance(raw, dict):
        return (float(raw.get("x", default[0])), float(raw.get("y", default[1])))
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        return (float(raw[0]), float(raw[1]))
    return default


class FactoryLayout:
    """
    工厂二维布局：
    - 主出口固定在左侧、上侧、右侧
    - 建筑具有独立出口
    - 复杂道路网络保证全局连通
    """

    def __init__(self):
        self.width = 1200.0
        self.height = 600.0
        self.main_exits: Dict[str, Point] = {
            "left": (100.0, 300.0),
            "top": (600.0, 100.0),
            "right": (1100.0, 300.0),
        }
        self.buildings: Dict[str, Building] = {
            "workshop1": Building("workshop1", "车间1", (350.0, 240.0), (100.0, 80.0), (400.0, 240.0)),
            "workshop2": Building("workshop2", "车间2", (750.0, 240.0), (100.0, 80.0), (700.0, 240.0)),
            "warehouse": Building("warehouse", "仓库", (350.0, 440.0), (100.0, 80.0), (400.0, 440.0)),
            "equipment_room": Building("equipment_room", "设备房", (750.0, 440.0), (100.0, 80.0), (700.0, 440.0)),
            "office": Building("office", "办公楼", (600.0, 190.0), (100.0, 80.0), (600.0, 230.0)),
            "admin": Building("admin", "行政楼", (210.0, 300.0), (120.0, 100.0), (270.0, 300.0)),
        }
        self.building_exit_candidates: Dict[str, List[Point]] = {
            "workshop1": [(400.0, 240.0), (350.0, 200.0)],
            "workshop2": [(700.0, 240.0), (750.0, 200.0), (800.0, 240.0)],
            "warehouse": [(400.0, 440.0), (350.0, 400.0)],
            "equipment_room": [(700.0, 440.0), (750.0, 400.0), (800.0, 440.0)],
            "office": [(600.0, 230.0), (600.0, 150.0)],
            "admin": [(270.0, 300.0)],
        }
        self.car_building_map: Dict[int, str] = {
            1: "workshop1",
            2: "equipment_room",
            3: "workshop2",
            4: "warehouse",
        }
        self.road_graph: Dict[Point, Dict[Point, float]] = {}
        self._build_road_network()

    def _add_edge(self, a: Point, b: Point):
        self.road_graph.setdefault(a, {})
        self.road_graph.setdefault(b, {})
        w = _dist(a, b)
        self.road_graph[a][b] = w
        self.road_graph[b][a] = w

    def _add_polyline(self, points: List[Point]):
        for i in range(1, len(points)):
            self._add_edge(points[i - 1], points[i])

    def _build_road_network(self):
        # 主横向干道
        self._add_polyline([
            (100, 300), (180, 300), (270, 300), (350, 300), (450, 300),
            (550, 300), (600, 300), (650, 300), (750, 300), (850, 300), (950, 300), (1030, 300), (1100, 300)
        ])
        # 上侧联络道
        self._add_polyline([(250, 180), (350, 180), (450, 180), (550, 180), (600, 180), (650, 180), (750, 180), (850, 180)])
        # 中上联络道
        self._add_polyline([(250, 240), (350, 240), (450, 240), (550, 240), (600, 240), (650, 240), (750, 240), (850, 240)])
        # 中下联络道
        self._add_polyline([(250, 360), (350, 360), (450, 360), (550, 360), (600, 360), (650, 360), (750, 360), (850, 360)])
        # 下侧联络道
        self._add_polyline([(250, 440), (350, 440), (450, 440), (550, 440), (650, 440), (750, 440), (850, 440)])

        # 多条纵向连接，形成互通网格
        for x in (250, 350, 450, 550, 650, 750, 850):
            self._add_polyline([(x, 180), (x, 240), (x, 300), (x, 360), (x, 440)])

        # 行政楼接入道路
        self._add_polyline([(270, 300), (270, 240), (250, 240)])
        self._add_polyline([(270, 300), (250, 300), (180, 300)])

        # 上主出口接入
        self._add_polyline([(600, 100), (600, 140), (600, 180), (600, 240), (600, 300)])

        # 关键建筑出口接入道路
        self._add_polyline([(400, 240), (450, 240)])
        self._add_polyline([(350, 200), (350, 180)])
        self._add_polyline([(700, 240), (650, 240)])
        self._add_polyline([(750, 200), (750, 180)])
        self._add_polyline([(800, 240), (850, 240)])
        self._add_polyline([(400, 440), (450, 440)])
        self._add_polyline([(350, 400), (350, 360)])
        self._add_polyline([(700, 440), (650, 440)])
        self._add_polyline([(750, 400), (750, 360)])
        self._add_polyline([(800, 440), (850, 440)])
        self._add_polyline([(600, 230), (600, 240)])
        self._add_polyline([(600, 150), (600, 180)])

    def is_connected(self) -> bool:
        if not self.road_graph:
            return False
        start = next(iter(self.road_graph.keys()))
        q = [start]
        visited: Set[Point] = {start}
        while q:
            cur = q.pop()
            for nxt in self.road_graph.get(cur, {}):
                if nxt not in visited:
                    visited.add(nxt)
                    q.append(nxt)
        return len(visited) == len(self.road_graph)

    def nearest_road_node(self, point: Point) -> Point:
        return min(self.road_graph.keys(), key=lambda p: _dist(p, point))

    def nearest_building_id(self, point: Point) -> str:
        return min(self.buildings.keys(), key=lambda bid: _dist(point, self.buildings[bid].center))

    def building_by_car_id(self, car_id: int) -> Optional[str]:
        return self.car_building_map.get(car_id)

    def get_building_exits(self, building_id: str) -> List[Point]:
        return list(self.building_exit_candidates.get(building_id, [self.buildings[building_id].exit_point]))

    def export_map_data(self) -> Dict:
        roads = []
        seen = set()
        for a, nbrs in self.road_graph.items():
            for b in nbrs:
                edge_key = tuple(sorted((_pt_key(a), _pt_key(b))))
                if edge_key in seen:
                    continue
                seen.add(edge_key)
                roads.append({"start": [a[0], a[1]], "end": [b[0], b[1]]})

        return {
            "size": {"width": self.width, "height": self.height},
            "mainExits": {k: [v[0], v[1]] for k, v in self.main_exits.items()},
            "buildings": {
                b.id: {
                    "name": b.name,
                    "center": [b.center[0], b.center[1]],
                    "size": [b.size[0], b.size[1]],
                    "exit": [b.exit_point[0], b.exit_point[1]],
                    "exits": [[p[0], p[1]] for p in self.get_building_exits(b.id)]
                } for b in self.buildings.values()
            },
            "roads": roads,
        }


class EnhancedGaussianPlumeModel:
    """
    简化增强型扩散模型：
    - 含风向平流、稳定度扩散、密度影响和时间衰减
    - 限制扩散范围，避免可视化过大
    """

    def __init__(self):
        # A(1)最不稳定 -> 扩散更快更宽；F(6)最稳定 -> 羽流更窄更长
        self.crosswind_factor = {1: 1.45, 2: 1.30, 3: 1.15, 4: 1.00, 5: 0.82, 6: 0.68}
        self.downwind_factor = {1: 1.00, 2: 1.02, 3: 1.05, 4: 1.12, 5: 1.24, 6: 1.36}
        self.stability_decay = {1: 0.85, 2: 0.90, 3: 0.95, 4: 1.00, 5: 1.06, 6: 1.12}
        # 稳定度对最终边界模型尺寸与形状的直接调制
        self.stability_radius_factor = {1: 1.35, 2: 1.22, 3: 1.12, 4: 1.00, 5: 0.88, 6: 0.78}
        self.stability_shape_factor = {1: 1.00, 2: 1.08, 3: 1.16, 4: 1.24, 5: 1.34, 6: 1.46}

    def calculate_concentration(
        self,
        leak_point: Point,
        target_point: Point,
        config: DiffusionConfig,
        gas_type: GasType = GasType.CH4,
        time_elapsed: float = 60.0
    ) -> float:
        gas_props = GAS_PROPERTIES_MAP.get(gas_type, GAS_PROPERTIES_MAP[GasType.CH4])
        t = max(1.0, time_elapsed)
        ws = max(0.1, config.wind_speed)

        angle = math.radians(config.wind_angle)
        dx = target_point[0] - leak_point[0]
        dy = target_point[1] - leak_point[1]
        downwind = dx * math.cos(angle) + dy * math.sin(angle)
        crosswind = -dx * math.sin(angle) + dy * math.cos(angle)
        distance = math.hypot(dx, dy)

        # 时间相关扩散尺度：泄漏强度影响规模，稳定度影响形状
        d_eff = gas_props.diffusion_coefficient * (1.0 + ws * 0.08) / max(0.5, config.terrain_roughness)
        base_sigma = max(6.0, math.sqrt(2.0 * d_eff * t) * 6.0)
        cross_k = self.crosswind_factor.get(config.stability, 1.0)
        down_k = self.downwind_factor.get(config.stability, 1.12)
        sigma_cross = max(6.0, base_sigma * cross_k)
        sigma_down = max(8.0, base_sigma * down_k)

        # 风致平流: 污染团沿风向位移
        advection = ws * t * 0.35
        drifted_downwind = downwind - advection

        # 密度修正: 重气体更贴地聚集，轻气体更易抬升扩散
        density_term = 1.0 + (gas_props.density_ratio - 1.0) * 0.25
        density_term = max(0.65, min(1.5, density_term))

        source_strength = (max(0.5, config.source_rate) ** 1.18) * 900.0
        norm = source_strength / (2.0 * math.pi * sigma_cross * sigma_down)
        plume = math.exp(-((drifted_downwind ** 2) / (2.0 * sigma_down ** 2) + (crosswind ** 2) / (2.0 * sigma_cross ** 2)))

        # 上风向保留少量逆扩散，避免“硬截断”
        if downwind < 0:
            plume *= 0.35

        stability_decay = self.stability_decay.get(config.stability, 1.0)
        time_decay = math.exp(-gas_props.decay_rate * t * stability_decay)
        distance_decay = math.exp(-distance / 420.0)
        ppm = norm * plume * time_decay * distance_decay * density_term * (28.97 / gas_props.molecular_weight) * 1000.0
        return max(0.0, ppm)

    def _trace_isopleth(
        self,
        leak_point: Point,
        config: DiffusionConfig,
        gas_type: GasType,
        time_elapsed: float,
        threshold_ppm: float
    ) -> List[Point]:
        if threshold_ppm <= 0:
            return []

        points: List[Point] = []
        resolution = max(20, config.sample_resolution)
        radius_factor = self.stability_radius_factor.get(config.stability, 1.0)
        shape_factor = self.stability_shape_factor.get(config.stability, 1.2)
        max_radius = max(80.0, config.max_radius * radius_factor)
        wind_angle = math.radians(config.wind_angle)
        for i in range(resolution):
            ang = math.radians(i * (360.0 / resolution))
            rel = ang - wind_angle
            # 稳定度越高，越强化“顺风向拉伸、侧风向压缩”；稳定度低时更接近团状扩散
            anisotropy = 1.0 + (shape_factor - 1.0) * math.cos(rel) ** 2
            directional_cap = max_radius * anisotropy
            best_r = 0.0
            r = 6.0
            while r <= directional_cap:
                p = (leak_point[0] + r * math.cos(ang), leak_point[1] + r * math.sin(ang))
                c = self.calculate_concentration(leak_point, p, config, gas_type, time_elapsed)
                if c >= threshold_ppm:
                    best_r = r
                r += 5.0

            points.append((
                round(leak_point[0] + best_r * math.cos(ang), 1),
                round(leak_point[1] + best_r * math.sin(ang), 1)
            ))
        return points

    def get_enhanced_diffusion_polygons(
        self,
        leak_point: Point,
        config: DiffusionConfig,
        gas_type: GasType = GasType.CH4,
        time_elapsed: float = 60.0
    ) -> DiffusionResult:
        gas_props = GAS_PROPERTIES_MAP.get(gas_type, GAS_PROPERTIES_MAP[GasType.CH4])
        result = DiffusionResult()

        high_th = gas_props.idlh_threshold_ppm * 0.7
        med_th = gas_props.safety_threshold_ppm * 1.6
        low_th = gas_props.safety_threshold_ppm * 0.5

        high_poly = self._trace_isopleth(leak_point, config, gas_type, time_elapsed, high_th)
        med_poly = self._trace_isopleth(leak_point, config, gas_type, time_elapsed, med_th)
        low_poly = self._trace_isopleth(leak_point, config, gas_type, time_elapsed, low_th)

        if any(any(v != leak_point[idx % 2] for idx, v in enumerate(pt)) for pt in high_poly):
            result.high_concentration.append(high_poly)
        if any(any(v != leak_point[idx % 2] for idx, v in enumerate(pt)) for pt in med_poly):
            result.medium_concentration.append(med_poly)
        if any(any(v != leak_point[idx % 2] for idx, v in enumerate(pt)) for pt in low_poly):
            result.low_concentration.append(low_poly)

        samples = [
            leak_point,
            (leak_point[0] + 20, leak_point[1]),
            (leak_point[0], leak_point[1] + 20),
            (leak_point[0] + 30, leak_point[1] + 20),
        ]
        result.max_concentration = max(
            self.calculate_concentration(leak_point, p, config, gas_type, time_elapsed) for p in samples
        )
        result.affected_area = math.pi * (config.max_radius ** 2)
        return result

    def calculate_time_evolution(
        self,
        leak_point: Point,
        config: DiffusionConfig,
        gas_type: GasType = GasType.CH4,
        num_steps: int = 30,
        step_interval: float = 5.0
    ) -> List[DiffusionResult]:
        series = []
        for i in range(1, num_steps + 1):
            t = i * step_interval
            frame = self.get_enhanced_diffusion_polygons(leak_point, config, gas_type, t)
            frame.time_steps = i
            series.append(frame)
        return series


class AStarPathPlanner:
    """A* path planner for the factory road network.

    Finds optimal paths on a graph while avoiding blocked nodes and
    edges from gas danger masks.

    Args:
        layout: FactoryLayout instance with the road graph.
    """

    def __init__(self, layout: FactoryLayout):
        self.layout = layout

    def _heuristic(self, a: Point, b: Point) -> float:
        """Heuristic function for A* (Euclidean distance).

        Args:
            a: Current point.
            b: Goal point.

        Returns:
            Estimated distance between a and b.
        """
        return _dist(a, b)

    def _reconstruct(self, came: Dict[Point, Point], cur: Point) -> List[Point]:
        """Reconstruct the path from the came-from map.

        Args:
            came: Dictionary mapping each node to its predecessor.
            cur: Goal node to trace back from.

        Returns:
            Ordered list of points from start to goal.
        """
        path = [cur]
        while cur in came:
            cur = came[cur]
            path.append(cur)
        return list(reversed(path))

    def _sample_segment(self, a: Point, b: Point, n: int = 5) -> List[Point]:
        """Sample intermediate points along a segment.

        Args:
            a: Start point of the segment.
            b: End point of the segment.
            n: Number of samples (default 5).

        Returns:
            List of interpolated points between a and b.
        """
        points = []
        for i in range(1, n):
            t = i / n
            points.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        return points

    def _summarize_route_risk(self, risk_samples: List[Dict[str, Any]]) -> Dict[str, float]:
        """Summarize risk metrics across sampled path points.

        Args:
            risk_samples: List of risk dicts for each path point.

        Returns:
            Dict with max_ratio_idlh, max_ratio_safe, and avg_risk_score.
        """
        if not risk_samples:
            return {
                "max_ratio_idlh": 0.0,
                "max_ratio_safe": 0.0,
                "avg_risk_score": 0.0,
            }
        return {
            "max_ratio_idlh": max((s.get("max_ratio_idlh", 0.0) for s in risk_samples), default=0.0),
            "max_ratio_safe": max((s.get("max_ratio_safe", 0.0) for s in risk_samples), default=0.0),
            "avg_risk_score": sum((s.get("risk_score", 0.0) for s in risk_samples), 0.0) / len(risk_samples),
        }

    def find_path(
        self,
        start: Point,
        goal: Point,
        danger_mask: Optional[Dict[str, Set]] = None,
        obstacles: Optional[List[Point]] = None,
        risk_fn=None
    ) -> Dict[str, Any]:
        """Find the shortest path from start to goal avoiding hazards.

        Uses A* search on the factory road graph with blocked nodes,
        blocked edges, and obstacle avoidance.

        Args:
            start: Start point on the road graph.
            goal: Goal point on the road graph.
            danger_mask: Optional dict with blocked_nodes and
                blocked_edges sets.
            obstacles: Optional list of obstacle points to avoid.
            risk_fn: Optional callable returning risk dict for a point.

        Returns:
            Dict with path, distance, iterations, status
            ('success'/'unreachable'/'blocked'), riskSamples, and
            routeRisk summary.
        """
        if start not in self.layout.road_graph or goal not in self.layout.road_graph:
            return {
                "path": [],
                "distance": float("inf"),
                "iterations": 0,
                "status": "unreachable",
                "riskSamples": [],
            }

        obstacle_list = obstacles or []
        blocked_nodes: Set[Point] = (danger_mask or {}).get("blocked_nodes", set())
        blocked_edges: Set[Tuple[Point, Point]] = (danger_mask or {}).get("blocked_edges", set())
        open_heap: List[Tuple[float, Point]] = []
        heapq.heappush(open_heap, (0.0, start))
        came: Dict[Point, Point] = {}
        g_score: Dict[Point, float] = {start: 0.0}
        visited: Set[Point] = set()
        iterations = 0

        while open_heap:
            iterations += 1
            _, cur = heapq.heappop(open_heap)
            if cur in visited:
                continue
            visited.add(cur)

            if cur == goal:
                path = self._reconstruct(came, cur)
                dist = sum(_dist(path[i - 1], path[i]) for i in range(1, len(path)))
                risks = [risk_fn(p) for p in path] if risk_fn else []
                route_risk = self._summarize_route_risk(risks)
                return {
                    "path": path,
                    "distance": dist,
                    "iterations": iterations,
                    "status": "success",
                    "riskSamples": risks,
                    "routeRisk": route_risk,
                }

            if cur in blocked_nodes:
                continue

            if any(_dist(cur, obs) < 16.0 for obs in obstacle_list):
                continue

            for nb, edge_len in self.layout.road_graph.get(cur, {}).items():
                if nb in visited:
                    continue

                if nb in blocked_nodes:
                    continue
                if any(_dist(nb, obs) < 16.0 for obs in obstacle_list):
                    continue

                if _edge_key(cur, nb) in blocked_edges:
                    continue

                # 纯最简A*：代价仅使用边几何长度，不引入任何道路附加权重
                tentative_g = g_score[cur] + edge_len
                if tentative_g < g_score.get(nb, float("inf")):
                    came[nb] = cur
                    g_score[nb] = tentative_g
                    f = tentative_g + self._heuristic(nb, goal)
                    heapq.heappush(open_heap, (f, nb))

        return {
            "path": [],
            "distance": float("inf"),
            "iterations": iterations,
            "status": "blocked",
            "riskSamples": [],
        }

    def find_nearest_safe_main_exit(
        self,
        start: Point,
        main_exits: Dict[str, Point],
        danger_mask: Optional[Dict[str, Set]] = None,
        obstacles: Optional[List[Point]] = None,
        risk_fn=None
    ) -> Dict[str, Any]:
        """Find the nearest safe main exit from a start point.

        Evaluates all main exits, preferring fully safe routes (all
        points below safety threshold) over the shortest route.

        Args:
            start: Start point on the road graph.
            main_exits: Dict mapping exit IDs to exit points.
            danger_mask: Optional danger mask for hazard avoidance.
            obstacles: Optional obstacle points.
            risk_fn: Optional risk evaluation callable.

        Returns:
            Best route dict with path, distance, exitId, exitPoint,
            and route risk assessment.
        """
        candidates = []
        candidates = []
        for exit_id, exit_point in main_exits.items():
            plan = self.find_path(start, exit_point, danger_mask=danger_mask, obstacles=obstacles, risk_fn=risk_fn)
            plan["exitId"] = exit_id
            plan["exitPoint"] = exit_point
            candidates.append(plan)

        successful = [p for p in candidates if p["status"] == "success"]
        fully_safe = [p for p in successful if p.get("routeRisk", {}).get("max_ratio_safe", float("inf")) < 1.0]
        if fully_safe:
            fully_safe.sort(key=lambda p: (
                p["distance"],
                p.get("routeRisk", {}).get("avg_risk_score", float("inf"))
            ))
            return fully_safe[0]
        if successful:
            successful.sort(key=lambda p: (
                p.get("routeRisk", {}).get("max_ratio_safe", float("inf")),
                p["distance"],
                p.get("routeRisk", {}).get("avg_risk_score", float("inf"))
            ))
            return successful[0]

        return candidates[0] if candidates else {
            "path": [],
            "distance": float("inf"),
            "iterations": 0,
            "status": "blocked",
            "exitId": "none",
            "exitPoint": start,
            "riskSamples": [],
        }


class IntegratedEscapeSystem:
    """Unified system integrating diffusion modeling and escape planning.

    Combines factory layout, Gaussian plume gas model, and A* path
    planner to compute hazard-aware evacuation routes for all buildings.

    Typical usage:
        system = IntegratedEscapeSystem()
        sources = system.build_sources(active_car_id=1)
        snapshot = system.compute_diffusion_snapshot(config, t, sources)
        escape = system.plan_escape_for_building("workshop1", ...)
    """

    def __init__(self):
        self.layout = FactoryLayout()
        self.gas_model = EnhancedGaussianPlumeModel()
        self.path_planner = AStarPathPlanner(self.layout)

    def build_sources(
        self,
        active_car_id: Optional[int] = None,
        active_building_id: Optional[str] = None
    ) -> List[DiffusionSource]:
        """Build diffusion sources from car-to-building-to-gas mapping.

        Maps car IDs to building and gas type:
            1 -> workshop1 (CH4), 2 -> equipment_room (NH3),
            3 -> workshop2 (CO), 4 -> warehouse (O2).

        Args:
            active_car_id: Optional car ID for single-source scenario.
            active_building_id: Optional building ID filter.

        Returns:
            List of DiffusionSource objects with source_id, building_id,
            leak_point, and gas_type.
        """
        car_source_map: Dict[int, Tuple[str, GasType]] = {
            1: ("workshop1", GasType.CH4),
            2: ("equipment_room", GasType.NH3),
            3: ("workshop2", GasType.CO),
            4: ("warehouse", GasType.O2),
        }

        if active_car_id is not None:
            source = car_source_map.get(active_car_id)
            if source:
                mapping = [source]
            else:
                mapping = list(car_source_map.values())
        else:
            mapping = list(car_source_map.values())
            if active_building_id:
                for bid, gtype in car_source_map.values():
                    if bid == active_building_id:
                        mapping = [(bid, gtype)]
                        break

        sources = []
        for idx, (bid, gtype) in enumerate(mapping, start=1):
            b = self.layout.buildings[bid]
            sources.append(DiffusionSource(
                source_id=f"S{idx}",
                building_id=bid,
                leak_point=b.center,
                gas_type=gtype
            ))
        return sources

    def _point_risk(
        self,
        point: Point,
        sources: List[DiffusionSource],
        config: DiffusionConfig,
        time_elapsed: float
    ) -> Dict[str, Any]:
        """Evaluate gas risk at a single point from all sources.

        Computes concentrations from all active sources and determines
        whether the point is blocked (above IDLH threshold).

        Args:
            point: (x, y) tuple of the evaluation point.
            sources: List of active diffusion sources.
            config: Diffusion configuration parameters.
            time_elapsed: Elapsed time in seconds.

        Returns:
            Dict with blocked flag, risk_score, max_ratio_idlh,
            max_ratio_safe, and concentrations per gas.
        """
        max_ratio_idlh = 0.0
        max_ratio_safe = 0.0
        concentrations: Dict[str, float] = {}
        for s in sources:
            props = GAS_PROPERTIES_MAP[s.gas_type]
            c = self.gas_model.calculate_concentration(s.leak_point, point, config, s.gas_type, time_elapsed)
            concentrations[s.gas_type.name] = c
            max_ratio_idlh = max(max_ratio_idlh, c / max(props.idlh_threshold_ppm, 1e-6))
            max_ratio_safe = max(max_ratio_safe, c / max(props.safety_threshold_ppm, 1e-6))
        return {
            "blocked": max_ratio_idlh >= 1.0,
            "risk_score": max_ratio_safe * 100.0,
            "max_ratio_idlh": max_ratio_idlh,
            "max_ratio_safe": max_ratio_safe,
            "concentrations": concentrations,
        }

    def build_danger_road_mask(
        self,
        sources: List[DiffusionSource],
        config: DiffusionConfig,
        time_elapsed: float,
        segment_samples: int = 5
    ) -> Dict[str, Set]:
        """Build a danger mask for the road graph based on gas concentration.

        Evaluates each road node and edge segment against gas risk to
        identify blocked areas.

        Args:
            sources: List of active diffusion sources.
            config: Diffusion configuration parameters.
            time_elapsed: Elapsed time in seconds.
            segment_samples: Number of samples per edge for evaluation.

        Returns:
            Dict with blocked_nodes set, blocked_edges set, and
            checked_edges set.
        """
        blocked_nodes: Set[Point] = set()
        blocked_edges: Set[Tuple[Point, Point]] = set()
        checked_edges: Set[Tuple[Point, Point]] = set()

        for a, nbrs in self.layout.road_graph.items():
            if self._point_risk(a, sources, config, time_elapsed)["blocked"]:
                blocked_nodes.add(a)

            for b in nbrs.keys():
                edge = _edge_key(a, b)
                if edge in checked_edges:
                    continue
                checked_edges.add(edge)

                edge_blocked = False
                if a in blocked_nodes or b in blocked_nodes:
                    edge_blocked = True
                else:
                    for i in range(1, max(2, segment_samples) + 1):
                        t = i / (max(2, segment_samples) + 1)
                        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                        if self._point_risk(p, sources, config, time_elapsed)["blocked"]:
                            edge_blocked = True
                            break

                if edge_blocked:
                    blocked_edges.add(edge)

        return {
            "blocked_nodes": blocked_nodes,
            "blocked_edges": blocked_edges,
            "checked_edges": checked_edges,
        }

    def compute_diffusion_snapshot(
        self,
        config: DiffusionConfig,
        time_elapsed: float,
        sources: List[DiffusionSource]
    ) -> Dict[str, Any]:
        """Compute a diffusion snapshot for all active sources.

        Generates concentration polygons (high/medium/low) for each
        source and merges them.

        Args:
            config: Diffusion configuration parameters.
            time_elapsed: Elapsed time in seconds.
            sources: List of active diffusion sources.

        Returns:
            Dict with merged high/medium/low polygons, maxConcentration,
            affectedArea, and per-source detail.
        """
        per_source = {}
        per_source = {}
        merged_high: List[List[Point]] = []
        merged_medium: List[List[Point]] = []
        merged_low: List[List[Point]] = []
        max_conc = 0.0
        affected_area = 0.0

        for src in sources:
            result = self.gas_model.get_enhanced_diffusion_polygons(
                src.leak_point, config, src.gas_type, time_elapsed
            )
            per_source[src.source_id] = {
                "buildingId": src.building_id,
                "gasType": src.gas_type.name,
                "leakPoint": [src.leak_point[0], src.leak_point[1]],
                "high": result.high_concentration,
                "medium": result.medium_concentration,
                "low": result.low_concentration,
                "maxConcentration": round(result.max_concentration, 2),
                "affectedArea": round(result.affected_area, 2),
            }
            merged_high.extend(result.high_concentration)
            merged_medium.extend(result.medium_concentration)
            merged_low.extend(result.low_concentration)
            max_conc = max(max_conc, result.max_concentration)
            affected_area += result.affected_area

        return {
            "high": merged_high,
            "medium": merged_medium,
            "low": merged_low,
            "maxConcentration": max_conc,
            "affectedArea": affected_area,
            "perSource": per_source,
        }

    def plan_escape_for_building(
        self,
        building_id: str,
        config: DiffusionConfig,
        time_elapsed: float,
        sources: List[DiffusionSource],
        obstacles: Optional[List[Point]] = None
    ) -> Dict[str, Any]:
        """Plan an escape route for a specific building.

        Evaluates all building exits and main exits, selects the safest
        route based on gas risk and distance.

        Args:
            building_id: Building identifier string.
            config: Diffusion configuration parameters.
            time_elapsed: Elapsed time in seconds.
            sources: List of active diffusion sources.
            obstacles: Optional list of obstacle points to avoid.

        Returns:
            Dict with building info, start exit, target main exit,
            path, distance, safety assessment, and danger mask stats.
        """
        building = self.layout.buildings[building_id]

        def risk_fn(p: Point) -> Dict:
            return self._point_risk(p, sources, config, time_elapsed)

        danger_mask = self.build_danger_road_mask(sources, config, time_elapsed)
        exit_candidates = self.layout.get_building_exits(building_id)
        candidate_plans = []
        for start in exit_candidates:
            exit_risk = risk_fn(start)
            best_plan = self.path_planner.find_nearest_safe_main_exit(
                start,
                self.layout.main_exits,
                danger_mask=danger_mask,
                obstacles=obstacles,
                risk_fn=risk_fn
            )
            best_plan["startExit"] = start
            best_plan["startExitRisk"] = exit_risk
            candidate_plans.append(best_plan)

        fully_safe_candidates = [
            plan for plan in candidate_plans
            if plan["status"] == "success" and plan.get("routeRisk", {}).get("max_ratio_safe", float("inf")) < 1.0
        ]
        if fully_safe_candidates:
            candidate_plans = fully_safe_candidates
            candidate_plans.sort(key=lambda plan: (
                plan["distance"],
                plan.get("routeRisk", {}).get("avg_risk_score", float("inf")),
                plan["startExitRisk"]["max_ratio_safe"]
            ))
        else:
            candidate_plans.sort(key=lambda plan: (
                plan["status"] != "success",
                plan.get("routeRisk", {}).get("max_ratio_safe", float("inf")),
                plan["distance"],
                plan.get("routeRisk", {}).get("avg_risk_score", float("inf")),
                plan["startExitRisk"]["blocked"],
                plan["startExitRisk"]["max_ratio_safe"]
            ))
        best_plan = candidate_plans[0] if candidate_plans else {
            "path": [],
            "distance": float("inf"),
            "iterations": 0,
            "status": "blocked",
            "exitId": "none",
            "exitPoint": building.exit_point,
            "startExit": building.exit_point,
            "riskSamples": [],
        }
        start = best_plan.get("startExit", building.exit_point)

        if best_plan["path"]:
            samples = best_plan.get("riskSamples", [])
            max_ratio_idlh = max((s["max_ratio_idlh"] for s in samples), default=0.0)
            max_ratio_safe = max((s["max_ratio_safe"] for s in samples), default=0.0)
            avg_risk = sum((s["risk_score"] for s in samples), 0.0) / max(1, len(samples))
            is_safe = max_ratio_idlh < 1.0
        else:
            max_ratio_idlh = 1.0
            max_ratio_safe = 1.0
            avg_risk = 999.0
            is_safe = False

        return {
            "buildingId": building_id,
            "buildingName": building.name,
            "startExit": [start[0], start[1]],
            "candidateExits": [[p[0], p[1]] for p in exit_candidates],
            "startExitRisk": {
                "blocked": best_plan["startExitRisk"]["blocked"],
                "maxSafeRatio": round(best_plan["startExitRisk"]["max_ratio_safe"], 4),
                "riskScore": round(best_plan["startExitRisk"]["risk_score"], 2),
            },
            "targetMainExit": best_plan["exitId"],
            "targetMainExitPoint": [best_plan["exitPoint"][0], best_plan["exitPoint"][1]],
            "path": [[p[0], p[1]] for p in best_plan["path"]],
            "distance": round(best_plan["distance"], 2) if math.isfinite(best_plan["distance"]) else 0.0,
            "nodeCount": len(best_plan["path"]),
            "iterations": best_plan["iterations"],
            "status": best_plan["status"],
            "safety": {
                "maxIdlhRatio": round(max_ratio_idlh, 4),
                "maxSafeRatio": round(max_ratio_safe, 4),
                "riskScore": round(avg_risk, 2),
                "isSafe": is_safe,
            },
            "routeRisk": {
                "maxSafeRatio": round(best_plan.get("routeRisk", {}).get("max_ratio_safe", 0.0), 4),
                "avgRiskScore": round(best_plan.get("routeRisk", {}).get("avg_risk_score", 0.0), 2),
            },
            "dangerMaskStats": {
                "blockedNodes": len(danger_mask.get("blocked_nodes", [])),
                "blockedEdges": len(danger_mask.get("blocked_edges", [])),
                "checkedEdges": len(danger_mask.get("checked_edges", [])),
            },
        }

    def validate_map_and_routes(
        self,
        route_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate the road network connectivity and route safety.

        Checks road network connectivity, building exit connections,
        route availability, and internal road node degrees.

        Args:
            route_map: Dict mapping building IDs to route plans.

        Returns:
            Dict with validation flags: roadNetworkConnected,
            allBuildingExitsConnected, allBuildingRoutesFound,
            allRoutesSafe, allInternalRoadNodesMultiConnected,
            and lowDegreeRoadNodes list.
        """
        excluded_nodes = set(self.layout.main_exits.values())
        for bid in self.layout.buildings:
            excluded_nodes.update(self.layout.get_building_exits(bid))

        low_degree_nodes = [
            [node[0], node[1]]
            for node, neighbors in self.layout.road_graph.items()
            if node not in excluded_nodes and len(neighbors) < 2
        ]
        all_exits_connected = all(
            all(exit_point in self.layout.road_graph for exit_point in self.layout.get_building_exits(bid))
            for bid in self.layout.buildings
        )
        all_routes_safe = all(plan["safety"]["isSafe"] for plan in route_map.values())
        all_routes_found = all(plan["status"] == "success" for plan in route_map.values())
        return {
            "roadNetworkConnected": self.layout.is_connected(),
            "allBuildingExitsConnected": all_exits_connected,
            "allBuildingRoutesFound": all_routes_found,
            "allRoutesSafe": all_routes_safe,
            "allInternalRoadNodesMultiConnected": len(low_degree_nodes) == 0,
            "lowDegreeRoadNodes": low_degree_nodes,
        }


def _parse_config(data: Dict[str, Any]) -> Tuple[DiffusionConfig, GasType, float]:
    """Parse and validate diffusion configuration from request data.

    Computes dynamic max_radius and sample_resolution scaling based
    on source rate, wind speed, and stability class.

    Args:
        data: Request dict with sourceRate, stability, windAngle,
            windSpeed, timeElapsed, and gasType.

    Returns:
        Tuple of (DiffusionConfig, GasType, time_elapsed).
    """
    source_rate = float(data.get("sourceRate", 8.0))
    stability = int(data.get("stability", 4))
    wind_angle = float(data.get("windAngle", 90.0))
    wind_speed = float(data.get("windSpeed", 3.0))
    time_elapsed = float(data.get("timeElapsed", 60.0))
    gas_type_str = str(data.get("gasType", "CH4")).upper()
    try:
        selected_gas = GasType[gas_type_str]
    except KeyError:
        selected_gas = GasType.CH4

    # 稳定度越低(A/B)整体影响范围越大；越高(E/F)范围收敛但顺风向更明显
    stability_radius_scale = {1: 1.22, 2: 1.14, 3: 1.07, 4: 1.00, 5: 0.92, 6: 0.85}
    radius_base = 90.0 + source_rate * 7.0 + wind_speed * 4.0
    dynamic_radius = min(
        420.0,
        max(120.0, radius_base * stability_radius_scale.get(max(1, min(6, stability)), 1.0))
    )
    dynamic_resolution = int(min(48, max(28, 24 + source_rate * 0.35)))

    cfg = DiffusionConfig(
        source_rate=source_rate,
        stability=max(1, min(6, stability)),
        wind_angle=wind_angle % 360.0,
        wind_speed=max(0.1, wind_speed),
        max_radius=dynamic_radius,
        sample_resolution=dynamic_resolution
    )
    return cfg, selected_gas, time_elapsed


def calculate_gas_and_path(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate gas diffusion and escape path for a given scenario.

    Main entry point for the integrated escape system. Parses input,
    computes diffusion, plans escape routes for all buildings, and
    returns combined results.

    Args:
        data: Request dict with sourceRate, stability, windAngle,
            windSpeed, leakPoint, startPoint, endPoint, gasType,
            leakCarId, obstacles, and timeElapsed.

    Returns:
        Dict with diffusion, escapePath, pathInfo, safetyAnalysis,
        gasInfo, factoryMap, multiGasDiffusion, buildingEscapePlans,
        validation, and success status.
    """
    try:
        system = IntegratedEscapeSystem()
        config, selected_gas, time_elapsed = _parse_config(data)

        raw_start = data.get("startPoint", (210, 300))
        raw_end = data.get("endPoint", (100, 300))
        raw_leak = data.get("leakPoint", (350, 240))
        start_point = _to_point(raw_start, (210.0, 300.0))
        end_point = _to_point(raw_end, (100.0, 300.0))
        leak_point = _to_point(raw_leak, (350.0, 240.0))
        obstacles = [_to_point(p, (0.0, 0.0)) for p in data.get("obstacles", [])]

        leak_car_id = data.get("leakCarId")
        active_car_id = int(leak_car_id) if isinstance(leak_car_id, (int, float, str)) and str(leak_car_id).isdigit() else None
        active_building = system.layout.building_by_car_id(active_car_id) if active_car_id is not None else system.layout.nearest_building_id(leak_point)
        sources = system.build_sources(active_car_id=active_car_id, active_building_id=active_building)
        snapshot = system.compute_diffusion_snapshot(config, time_elapsed, sources)

        route_map: Dict[str, Dict] = {}
        for building_id in system.layout.buildings:
            route_map[building_id] = system.plan_escape_for_building(
                building_id, config, time_elapsed, sources, obstacles=obstacles
            )

        # 兼容前端：默认采用“起点最近建筑”的逃生路径
        start_building = system.layout.nearest_building_id(start_point)
        primary_route = route_map.get(start_building)
        if not primary_route or primary_route["status"] != "success":
            # 如果默认路线不可达，退化为 endPoint 对应主出口的最近路线
            end_exit_id = min(system.layout.main_exits, key=lambda k: _dist(system.layout.main_exits[k], end_point))
            target_exit = system.layout.main_exits[end_exit_id]

            def risk_fn(p: Point) -> Dict:
                return system._point_risk(p, sources, config, time_elapsed)

            danger_mask = system.build_danger_road_mask(sources, config, time_elapsed)
            fallback = system.path_planner.find_path(
                system.layout.buildings[start_building].exit_point,
                target_exit,
                danger_mask=danger_mask,
                obstacles=obstacles,
                risk_fn=risk_fn
            )
            primary_route = {
                "path": [[p[0], p[1]] for p in fallback["path"]],
                "distance": round(fallback["distance"], 2) if math.isfinite(fallback["distance"]) else 0.0,
                "nodeCount": len(fallback["path"]),
                "iterations": fallback["iterations"],
                "status": fallback["status"] if fallback["path"] else "fallback",
                "safety": {"riskScore": 999.0, "isSafe": bool(fallback["path"])},
                "targetMainExit": end_exit_id
            }

        primary_gas_type = sources[0].gas_type if sources else selected_gas
        selected_props = GAS_PROPERTIES_MAP[primary_gas_type]
        safety_obj = primary_route.get("safety", {})
        map_validation = system.validate_map_and_routes(route_map)

        return {
            "diffusion": {
                "high": snapshot["high"],
                "medium": snapshot["medium"],
                "low": snapshot["low"],
                "affectedArea": round(snapshot["affectedArea"], 2),
                "maxConcentration": round(snapshot["maxConcentration"], 2),
            },
            "escapePath": primary_route.get("path", []),
            "pathInfo": {
                "distance": round(primary_route.get("distance", 0.0), 2),
                "nodeCount": int(primary_route.get("nodeCount", 0)),
                "iterations": int(primary_route.get("iterations", 0)),
                "status": primary_route.get("status", "fallback"),
                "targetMainExit": primary_route.get("targetMainExit", "unknown"),
                "startBuilding": start_building,
            },
            "safetyAnalysis": {
                "avgConcentration": round(snapshot["maxConcentration"] * 0.35, 2),
                "maxConcentration": round(snapshot["maxConcentration"], 2),
                "safeRatio": 1.0 if safety_obj.get("isSafe", False) else 0.0,
                "riskScore": round(float(safety_obj.get("riskScore", 999.0)), 2),
                "isSafe": bool(safety_obj.get("isSafe", False)),
                "pathSafetyValidated": bool(safety_obj.get("isSafe", False)),
            },
            "gasInfo": {
                "type": primary_gas_type.value,
                "name": selected_props.name,
                "color": selected_props.color,
                "safetyThreshold": selected_props.safety_threshold_ppm,
                "idlhThreshold": selected_props.idlh_threshold_ppm,
            },
            "factoryMap": system.layout.export_map_data(),
            "multiGasDiffusion": snapshot["perSource"],
            "activeLeakSource": {
                "carId": active_car_id,
                "buildingId": active_building,
                "sourceCount": len(sources),
            },
            "buildingEscapePlans": route_map,
            "validation": map_validation,
            "success": True,
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc(), "success": False}


def get_gas_types_info() -> Dict[str, Any]:
    """Get information about all supported gas types.

    Returns:
        Dict mapping gas type names to their properties including
        value, name, color, molecular weight, safety/IDLH thresholds,
        density ratio, and diffusion coefficient.
    """
    result = {}
    for gas_type, props in GAS_PROPERTIES_MAP.items():
        result[gas_type.name] = {
            "value": gas_type.value,
            "name": props.name,
            "color": props.color,
            "molecularWeight": props.molecular_weight,
            "safetyThreshold": props.safety_threshold_ppm,
            "idlhThreshold": props.idlh_threshold_ppm,
            "densityRatio": props.density_ratio,
            "diffusionCoefficient": props.diffusion_coefficient,
        }
    return result


def simulate_time_series(data: Dict[str, Any]) -> Dict[str, Any]:
    """Run a time-series diffusion and escape path simulation.

    Computes diffusion snapshots and escape routes across multiple
    time steps with dynamic hazard updating.

    Args:
        data: Request dict with numSteps, stepInterval, and same
            parameters as calculate_gas_and_path.

    Returns:
        Dict with frames, dynamicRoutes, totalFrames, duration,
        startBuilding, gasInfo, activeLeakSource, and success status.
    """
    try:
        system = IntegratedEscapeSystem()
        config, selected_gas, _ = _parse_config(data)
        # 钳制步数到 [1, 500]，防止超大值耗尽资源（DoS）
        num_steps = min(max(int(data.get("numSteps", 30)), 1), 500)
        step_interval = float(data.get("stepInterval", 5.0))
        raw_start = data.get("startPoint", (210, 300))
        raw_leak = data.get("leakPoint", (350, 240))
        start_point = _to_point(raw_start, (210.0, 300.0))
        leak_point = _to_point(raw_leak, (350.0, 240.0))
        start_building = system.layout.nearest_building_id(start_point)
        obstacles = [_to_point(p, (0.0, 0.0)) for p in data.get("obstacles", [])]

        leak_car_id = data.get("leakCarId")
        active_car_id = int(leak_car_id) if isinstance(leak_car_id, (int, float, str)) and str(leak_car_id).isdigit() else None
        active_building = system.layout.building_by_car_id(active_car_id) if active_car_id is not None else system.layout.nearest_building_id(leak_point)
        sources = system.build_sources(active_car_id=active_car_id, active_building_id=active_building)
        frames = []
        dynamic_routes = []

        for idx in range(num_steps):
            t = (idx + 1) * step_interval
            snapshot = system.compute_diffusion_snapshot(config, t, sources)
            route = system.plan_escape_for_building(
                start_building, config, t, sources, obstacles=obstacles
            )
            dynamic_routes.append({
                "frameIndex": idx,
                "timeElapsed": t,
                "buildingId": start_building,
                "path": route["path"],
                "distance": route["distance"],
                "status": route["status"],
                "isSafe": route["safety"]["isSafe"],
                "riskScore": route["safety"]["riskScore"],
                "targetMainExit": route["targetMainExit"],
            })

            frames.append({
                "frameIndex": idx,
                "timeElapsed": t,
                "high": snapshot["high"],
                "medium": snapshot["medium"],
                "low": snapshot["low"],
                "maxConcentration": round(snapshot["maxConcentration"], 2),
                "affectedArea": round(snapshot["affectedArea"], 2),
            })

        primary_gas_type = sources[0].gas_type if sources else selected_gas
        selected_props = GAS_PROPERTIES_MAP[primary_gas_type]
        return {
            "frames": frames,
            "dynamicRoutes": dynamic_routes,
            "totalFrames": len(frames),
            "duration": num_steps * step_interval,
            "startBuilding": start_building,
            "gasInfo": {
                "type": primary_gas_type.value,
                "name": selected_props.name,
                "color": selected_props.color,
            },
            "activeLeakSource": {
                "carId": active_car_id,
                "buildingId": active_building,
                "sourceCount": len(sources),
            },
            "success": True
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc(), "success": False}
