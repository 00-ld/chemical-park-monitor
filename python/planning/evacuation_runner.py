"""Evacuation planning runner module.

Orchestrates D* Lite hazard-aware evacuation route planning for single
start points or multi-building scenarios. Designed for Pyodide worker
execution.

Typical usage:
    result = run_evacuation_planning_task(payload)
"""

from __future__ import annotations

from typing import Dict

from .dstar_lite import plan_evacuation_route, plan_evacuation_routes_by_building


def run_evacuation_planning_task(payload: Dict) -> Dict:
    """Run an evacuation planning task.

    If buildingEntrances are provided, plans routes for all buildings.
    Otherwise, plans a single route from the startPoint.

    Args:
        payload: Request dict with roads, gas, frame, blockedMask,
            parking entrances, and optionally buildingEntrances or
            startPoint.

    Returns:
        Route result with path, distance, estimated time, and risk
        assessment. Includes candidateRoutes for single route or
        routesByBuilding for multi-building planning.
    """
    if isinstance(payload.get("buildingEntrances"), list):
        result = plan_evacuation_routes_by_building(payload)
        result["executor"] = {
            "mode": "worker-pyodide",
            "runtime": "pyodide-python",
            "implementation": "python.planning.evacuation_runner",
        }
        return result

    result = plan_evacuation_route(payload)
    result["executor"] = {
        "mode": "worker-pyodide",
        "runtime": "pyodide-python",
        "implementation": "python.planning.evacuation_runner",
    }
    return result
