"""Dataset normalization utilities for PINN inversion.

Provides payload normalization, active sensor building, candidate region
construction, and geometry helper functions for the two-stage PINN
inversion workflow.

Typical usage:
    dataset = normalize_inversion_payload(payload)
    config = normalize_coarse_search_payload(payload)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence


DEFAULT_TRAINING_CONFIG = {
    "epochs": 120,
    "learningRate": 0.01,
    "animationSteps": 18,
    "minSignalThreshold": 1.5,
    "convergenceRatio": 0.22,
}

DEFAULT_COARSE_SEARCH_CONFIG = {
    "topK": 4,
    "gridStep": 60,
    "candidateRadius": 45,
    "supportRadius": 140,
    "distanceScale": 90,
    "mergeDistance": 80,
    "minObservationThreshold": 1.5,
}


def normalize_inversion_payload(payload: Dict) -> Dict:
    """Normalize a PINN inversion payload into a standardized dataset.

    Extracts gas info, scenario, training config, active sensors, and
    candidate regions from various payload structures.

    Args:
        payload: Raw inversion request payload with refinementInput,
            pinnExportPayload, or direct flat structure.

    Returns:
        Normalized dataset dict with all fields for inversion.
    """
    refinement_input = payload.get("refinementInput") or {}
    export_payload = payload.get("pinnExportPayload") or payload.get("exportPayload") or payload
    coarse_search = payload.get("coarseSearchResult") or export_payload.get("coarseSearch") or {}

    gas = refinement_input.get("gas") or export_payload.get("gas") or {}
    scenario = refinement_input.get("scenario") or export_payload.get("scenario") or {}
    training_config = {
        **DEFAULT_TRAINING_CONFIG,
        **(refinement_input.get("trainingConfig") or payload.get("trainingConfig") or {}),
    }

    current_frame_index = (
        refinement_input.get("frameContext", {}).get("currentFrameIndex")
        or export_payload.get("timeline", {}).get("currentFrameIndex")
        or export_payload.get("currentFrameIndex")
        or 0
    )
    frame_time_sec = (
        export_payload.get("timeline", {}).get("currentTimeSec")
        or export_payload.get("currentFrameSnapshot", {}).get("timeSec")
        or 0
    )

    active_sensors = build_active_sensors(
        sensors=refinement_input.get("activeSensors"),
        fallback_sensors=export_payload.get("sensors") or payload.get("sensors") or [],
        current_frame_index=int(current_frame_index),
        min_signal_threshold=float(training_config.get("minSignalThreshold", 0)),
    )

    candidate_regions = (
        coarse_search.get("candidateRegions")
        or payload.get("candidateRegions")
        or build_candidate_regions_from_refinement(refinement_input.get("coarseCandidate"))
    )

    true_source_map_point = (
        payload.get("sourceMapPoint")
        or export_payload.get("scenario", {}).get("sourceMapPoint")
        or scenario.get("sourceMapPoint")
    )

    return {
        "gas": gas,
        "scenario": scenario,
        "trainingConfig": training_config,
        "currentFrameIndex": int(current_frame_index),
        "frameTimeSec": frame_time_sec,
        "activeSensors": active_sensors,
        "candidateRegions": candidate_regions,
        "trueSourceMapPoint": true_source_map_point,
    }


def normalize_coarse_search_payload(payload: Dict) -> Dict:
    """Normalize a coarse search payload into a standardized dataset.

    Extracts gas, config, frame info, and sensor data from various
    payload structures.

    Args:
        payload: Raw coarse search request payload.

    Returns:
        Normalized dataset dict with gas, config, frame index, and sensors.
    """
    export_payload = payload.get("pinnExportPayload") or payload.get("exportPayload") or payload
    gas = export_payload.get("gas") or payload.get("gas") or {}
    config = {
        **DEFAULT_COARSE_SEARCH_CONFIG,
        **(payload.get("config") or export_payload.get("inversionConfig") or {}),
    }
    current_frame_index = int(
        payload.get("currentFrameIndex")
        or export_payload.get("timeline", {}).get("currentFrameIndex")
        or export_payload.get("currentFrameIndex")
        or 0
    )
    frame_time_sec = (
        payload.get("frameTimeSec")
        or export_payload.get("timeline", {}).get("currentTimeSec")
        or export_payload.get("currentFrameSnapshot", {}).get("timeSec")
        or 0
    )

    return {
        "gas": gas,
        "config": config,
        "currentFrameIndex": current_frame_index,
        "frameTimeSec": frame_time_sec,
        "sensors": export_payload.get("sensors") or payload.get("sensors") or [],
    }


def build_active_sensors(
    sensors: Optional[Sequence[Dict]],
    fallback_sensors: Sequence[Dict],
    current_frame_index: int,
    min_signal_threshold: float,
) -> List[Dict]:
    """Build a filtered, sorted list of active sensors.

    If explicit sensors are provided, normalizes them. Otherwise,
    derives signals from fallback sensor sampled data.

    Args:
        sensors: Optional pre-built sensor list.
        fallback_sensors: Raw sensor data for signal derivation.
        current_frame_index: Current frame for concentration lookup.
        min_signal_threshold: Minimum signal to include sensor.

    Returns:
        Sorted list of active sensor dicts (highest signal first).
    """
    if sensors:
        normalized = [normalize_active_sensor(sensor) for sensor in sensors]
    else:
        normalized = []
        for sensor in fallback_sensors:
            current = pick_sampled_concentration(sensor.get("sampledSeries") or [], current_frame_index)
            peak = float(sensor.get("sampledPeak") or current or 0)
            signal = peak * 0.55 + current * 0.45
            normalized.append(
                {
                    "id": sensor.get("id", ""),
                    "priority": int(sensor.get("priority") or 0),
                    "mapPoint": normalize_point(sensor.get("mapPoint") or {"x": sensor.get("x", 0), "y": sensor.get("y", 0)}),
                    "geoPoint": sensor.get("geoPoint"),
                    "currentConcentration": round(current, 2),
                    "sampledPeak": round(peak, 2),
                    "signal": round(signal, 2),
                }
            )

    return sorted(
        [sensor for sensor in normalized if float(sensor.get("signal", 0)) >= min_signal_threshold],
        key=lambda item: item.get("signal", 0),
        reverse=True,
    )


def normalize_active_sensor(sensor: Dict) -> Dict:
    """Normalize a single active sensor to standard format.

    Args:
        sensor: Raw sensor dict with id, priority, position, and signals.

    Returns:
        Normalized sensor dict with standardized fields.
    """
    return {
        "id": sensor.get("id", ""),
        "priority": int(sensor.get("priority") or 0),
        "mapPoint": normalize_point(sensor.get("mapPoint") or {"x": 0, "y": 0}),
        "geoPoint": sensor.get("geoPoint"),
        "currentConcentration": round(float(sensor.get("currentConcentration") or 0), 2),
        "sampledPeak": round(float(sensor.get("sampledPeak") or 0), 2),
        "signal": round(float(sensor.get("signal") or 0), 2),
    }


def build_candidate_regions_from_refinement(coarse_candidate: Optional[Dict]) -> List[Dict]:
    """Build candidate regions list from a single coarse candidate.

    Args:
        coarse_candidate: Coarse search candidate result, or None.

    Returns:
        List with one candidate region dict, or empty list if no candidate.
    """
    if not coarse_candidate:
        return []
    return [
        {
            "candidateId": coarse_candidate.get("candidateId", "cand_1"),
            "rank": coarse_candidate.get("rank", 1),
            "center": normalize_point(coarse_candidate.get("center") or {"x": 500, "y": 325}),
            "geoCenter": coarse_candidate.get("geoCenter"),
            "score": float(coarse_candidate.get("score") or 0),
            "error": float(coarse_candidate.get("error") or 0),
            "supportCount": int(coarse_candidate.get("supportCount") or 0),
            "radius": float(coarse_candidate.get("radius") or 45),
            "bounds": coarse_candidate.get("bounds"),
            "label": coarse_candidate.get("label") or f"候选区域 {coarse_candidate.get('rank', 1)}",
        }
    ]


def pick_sampled_concentration(sampled_series: Sequence[Dict], current_frame_index: int) -> float:
    """Get concentration at a frame index from a sampled series.

    Args:
        sampled_series: List of frame concentration samples.
        current_frame_index: Target frame index.

    Returns:
        Concentration value, or last available if out of range.
    """
    if not sampled_series:
        return 0.0
    if 0 <= current_frame_index < len(sampled_series):
        return float(sampled_series[current_frame_index].get("concentration") or 0)
    return float(sampled_series[-1].get("concentration") or 0)


def normalize_point(point: Optional[Dict]) -> Dict:
    """Normalize a point dict to standard (x, y) float format.

    Args:
        point: Raw point dict, or None.

    Returns:
        Normalized point dict with 'x' and 'y' rounded to 2 decimals.
    """
    point = point or {"x": 0, "y": 0}
    return {
        "x": round(float(point.get("x", 0)), 2),
        "y": round(float(point.get("y", 0)), 2),
    }


def distance(left: Dict, right: Dict) -> float:
    """Compute Euclidean distance between two points.

    Args:
        left: First point dict with 'x' and 'y'.
        right: Second point dict with 'x' and 'y'.

    Returns:
        Euclidean distance between the two points.
    """
    return math.hypot(float(left["x"]) - float(right["x"]), float(left["y"]) - float(right["y"]))
