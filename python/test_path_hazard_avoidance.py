import math
import unittest
from typing import Dict, List, Set, Tuple

from gasDiffusionAstar import AStarPathPlanner, _edge_key

Point = Tuple[float, float]


class DummyLayout:
    def __init__(self, road_graph: Dict[Point, Dict[Point, float]]):
        self.road_graph = road_graph


def add_edge(graph: Dict[Point, Dict[Point, float]], a: Point, b: Point):
    graph.setdefault(a, {})
    graph.setdefault(b, {})
    w = math.hypot(a[0] - b[0], a[1] - b[1])
    graph[a][b] = w
    graph[b][a] = w


def build_test_graph() -> Dict[Point, Dict[Point, float]]:
    s = (0.0, 0.0)
    a = (1.0, 0.0)
    b = (2.0, 0.0)
    g = (3.0, 0.0)
    u1 = (1.0, 1.0)
    u2 = (2.0, 1.0)
    l1 = (1.0, -1.0)
    l2 = (2.0, -1.0)

    graph: Dict[Point, Dict[Point, float]] = {}
    # 中间最短路径
    add_edge(graph, s, a)
    add_edge(graph, a, b)
    add_edge(graph, b, g)
    # 上下两条备选路径
    add_edge(graph, s, u1)
    add_edge(graph, u1, u2)
    add_edge(graph, u2, g)
    add_edge(graph, s, l1)
    add_edge(graph, l1, l2)
    add_edge(graph, l2, g)
    return graph


def to_path_edges(path: List[Point]) -> Set[Tuple[Point, Point]]:
    edges = set()
    for i in range(1, len(path)):
        edges.add(_edge_key(path[i - 1], path[i]))
    return edges


def build_danger_mask_from_concentration(
    edge_conc: Dict[Tuple[Point, Point], float],
    threshold: float
) -> Dict[str, Set]:
    blocked_edges = {e for e, c in edge_conc.items() if c >= threshold}
    blocked_nodes: Set[Point] = set()
    return {"blocked_nodes": blocked_nodes, "blocked_edges": blocked_edges}


class PathHazardAvoidanceTests(unittest.TestCase):
    def setUp(self):
        self.graph = build_test_graph()
        self.layout = DummyLayout(self.graph)
        self.planner = AStarPathPlanner(self.layout)
        self.start = (0.0, 0.0)
        self.goal = (3.0, 0.0)
        self.idlh_threshold = 100.0

    def _run_with_blocked_edges(self, blocked: List[Tuple[Point, Point]]) -> Dict:
        conc_map: Dict[Tuple[Point, Point], float] = {}
        for a, nbrs in self.graph.items():
            for b in nbrs:
                conc_map[_edge_key(a, b)] = 0.0
        for e in blocked:
            conc_map[_edge_key(e[0], e[1])] = 120.0

        mask = build_danger_mask_from_concentration(conc_map, self.idlh_threshold)
        return self.planner.find_path(self.start, self.goal, danger_mask=mask)

    def test_shortest_path_blocked_then_detour(self):
        # 原始最短路径会走 (1,0)->(2,0)，该段高浓度后必须绕行
        result = self._run_with_blocked_edges([((1.0, 0.0), (2.0, 0.0))])
        self.assertEqual(result["status"], "success")
        used = to_path_edges(result["path"])
        self.assertNotIn(_edge_key((1.0, 0.0), (2.0, 0.0)), used)

    def test_three_shortest_segments_all_polluted(self):
        # 中轴最短路径三段均高浓度，必须改走次优安全路径
        blocked = [
            ((0.0, 0.0), (1.0, 0.0)),
            ((1.0, 0.0), (2.0, 0.0)),
            ((2.0, 0.0), (3.0, 0.0)),
        ]
        result = self._run_with_blocked_edges(blocked)
        self.assertEqual(result["status"], "success")
        used = to_path_edges(result["path"])
        for e in blocked:
            self.assertNotIn(_edge_key(e[0], e[1]), used)

    def test_dynamic_replan_switches_safe_route(self):
        # 第一次重规划：最短中轴+上路径污染 -> 必须走下路径
        upper_blocked = [
            ((1.0, 0.0), (2.0, 0.0)),
            ((1.0, 1.0), (2.0, 1.0)),
        ]
        r1 = self._run_with_blocked_edges(upper_blocked)
        self.assertEqual(r1["status"], "success")
        used1 = to_path_edges(r1["path"])
        self.assertIn(_edge_key((1.0, -1.0), (2.0, -1.0)), used1)

        # 第二次重规划：最短中轴+下路径污染 -> 切换上路径
        lower_blocked = [
            ((1.0, 0.0), (2.0, 0.0)),
            ((1.0, -1.0), (2.0, -1.0)),
        ]
        r2 = self._run_with_blocked_edges(lower_blocked)
        self.assertEqual(r2["status"], "success")
        used2 = to_path_edges(r2["path"])
        self.assertIn(_edge_key((1.0, 1.0), (2.0, 1.0)), used2)


if __name__ == "__main__":
    unittest.main()
