"""Coarse grid search for gas source candidate regions.

Performs a grid-based search over sensor signals to identify candidate
areas where the gas leak source is most likely located. Uses the
Gaussian plume model for wind-aware signal prediction with support
count and error scoring.

Typical usage:
    result = run_coarse_search(payload)
"""

from __future__ import annotations

import math
from typing import Dict, List

from .pinn_dataset import normalize_coarse_search_payload, pick_arrival_frame
from .pinn_losses import fit_emission_rate, gaussian_plume_predict
from diffusion.gaussian_plume import normalize_stability, resolve_environment

MAP_METERS_PER_UNIT = 0.5
ORIGIN_LONGITUDE = 118.78
ORIGIN_LATITUDE = 32.04
BASE_ALTITUDE = 18.0
GRID_MIN_X = 40
GRID_MIN_Y = 40
GRID_MAX_X = 961
GRID_MAX_Y = 611


def run_coarse_search(payload: Dict) -> Dict:
    """Run a coarse grid search for candidate gas source regions.

    Iterates over a grid of candidate points, evaluates Gaussian plume
    prediction error against active sensor observations, and returns
    the top-ranked non-overlapping candidate regions.

    Args:
        payload: Request payload with sensor data and search config.

    Returns:
        Dictionary with candidateRegions list and search metadata.
    """
    dataset = normalize_coarse_search_payload(payload)
    config = dataset["config"]
    scenario = dataset.get("scenario") or {}
    wind_speed = float(scenario.get("windSpeed") or 1.0)
    wind_direction = float(scenario.get("windDirection") or 0)
    # Dispersion regime, shared with the EKI refine stage for self-consistency.
    stability_class = normalize_stability(scenario.get("stabilityClass") or "D")
    urban = resolve_environment(float(scenario.get("terrainRoughness") or 0.45))

    sensors = build_active_sensors(
        sensors=dataset.get("sensors") or [],
        current_frame_index=int(dataset.get("currentFrameIndex") or 0),
        min_observation_threshold=float(config.get("minObservationThreshold") or 0),
    )
    if not sensors:
        return {
            "candidateRegions": [],
            "meta": {
                "gasId": dataset.get("gas", {}).get("gasId") or dataset.get("gas", {}).get("id") or "",
                "activeSensorCount": 0,
                "currentFrameIndex": int(dataset.get("currentFrameIndex") or 0),
                "frameTimeSec": dataset.get("frameTimeSec") or 0,
                "gridStep": config.get("gridStep", 20),
                "topK": config["topK"],
                "candidateRadius": config["candidateRadius"],
                "minObservationThreshold": config["minObservationThreshold"],
            },
        }

    candidates = []
    # 钳制网格步长到 [5, 100]，并兜底缺失/<=0（gridStep=0 会触发 range ValueError，DoS）
    grid_step = min(max(int(config.get("gridStep", 20) or 20), 5), 100)
    support_radius = float(config.get("supportRadius") or 140)
    max_observed = max(s["observedSignal"] for s in sensors) or 1.0

    for x in range(GRID_MIN_X, GRID_MAX_X, grid_step):
        for y in range(GRID_MIN_Y, GRID_MAX_Y, grid_step):
            weighted_error = 0.0
            influence_score = 0.0
            support_count = 0

            raw_predictions = []
            for sensor in sensors:
                pred = gaussian_plume_predict(
                    x, y,
                    sensor["x"], sensor["y"],
                    wind_speed, wind_direction,
                    stability_class=stability_class, urban=urban,
                )
                raw_predictions.append(pred)
            max_predicted = max(raw_predictions) or 1.0

            for i, sensor in enumerate(sensors):
                norm_predicted = raw_predictions[i] / max_predicted
                norm_observed = sensor["observedSignal"] / max_observed
                error = abs(norm_predicted - norm_observed)
                weighted_error += error * (1 + sensor["priority"] * 0.18)
                influence_score += min(norm_predicted, norm_observed)
                distance = max(math.hypot(sensor["x"] - x, sensor["y"] - y), 1.0)
                if distance <= support_radius:
                    support_count += 1

            normalized_error = weighted_error / len(sensors)
            support_ratio = support_count / len(sensors)
            shape_score = influence_score / len(sensors) + support_ratio * 0.4 - normalized_error * 0.7

            abs_scale = max_observed / max_predicted
            abs_predicted = [p * abs_scale for p in raw_predictions]
            abs_error_sum = sum(abs(abs_predicted[i] - sensors[i]["observedSignal"]) for i in range(len(sensors)))
            abs_error = abs_error_sum / len(sensors) / max_observed
            abs_score = max(0.0, 1.0 - abs_error)

            arrival_score = 0.0
            timed_count = 0
            earliest_arrival = min(
                (s.get("arrivalTimeSec") for s in sensors if s.get("arrivalTimeSec") is not None),
                default=None,
            )
            if earliest_arrival is not None:
                for sensor in sensors:
                    arrival_sec = sensor.get("arrivalTimeSec")
                    if arrival_sec is None:
                        continue
                    timed_count += 1
                    dist_m = math.hypot(sensor["x"] - x, sensor["y"] - y) * MAP_METERS_PER_UNIT
                    expected_time = dist_m / max(wind_speed, 0.5)
                    observed_time = arrival_sec - earliest_arrival
                    if observed_time > 0:
                        time_ratio = expected_time / observed_time
                        arrival_score += max(0.0, 1.0 - abs(time_ratio - 1.0))
                if timed_count > 0:
                    arrival_score = arrival_score / timed_count
                else:
                    arrival_score = shape_score
            else:
                arrival_score = shape_score

            score = round(shape_score * 0.25 + abs_score * 0.25 + arrival_score * 0.50, 4)
            candidates.append(
                {
                    "mapPoint": {"x": x, "y": y},
                    "score": score,
                    "error": round(normalized_error, 4),
                    "supportCount": support_count,
                }
            )

    candidates.sort(key=lambda item: item["score"], reverse=True)

    candidate_regions: List[Dict] = []
    for candidate in candidates:
        if len(candidate_regions) >= int(config["topK"]):
            break
        too_close = any(
            math.hypot(region["center"]["x"] - candidate["mapPoint"]["x"], region["center"]["y"] - candidate["mapPoint"]["y"])
            < float(config["mergeDistance"])
            for region in candidate_regions
        )
        if too_close:
            continue

        center = candidate["mapPoint"]
        radius = float(config["candidateRadius"])
        candidate_regions.append(
            {
                "candidateId": f"cand_{len(candidate_regions) + 1}",
                "rank": len(candidate_regions) + 1,
                "center": center,
                "geoCenter": to_geo_point(center["x"], center["y"]),
                "score": candidate["score"],
                "error": candidate["error"],
                "supportCount": candidate["supportCount"],
                "radius": radius,
                "bounds": {
                    "minX": center["x"] - radius,
                    "maxX": center["x"] + radius,
                    "minY": center["y"] - radius,
                    "maxY": center["y"] + radius,
                },
                "label": f"候选区域 {len(candidate_regions) + 1}",
            }
        )

    return {
        "candidateRegions": candidate_regions,
        "meta": {
            "gasId": dataset.get("gas", {}).get("gasId") or dataset.get("gas", {}).get("id") or "",
            "activeSensorCount": len(sensors),
            "currentFrameIndex": int(dataset.get("currentFrameIndex") or 0),
            "frameTimeSec": dataset.get("frameTimeSec") or 0,
            "gridStep": config.get("gridStep", 20),
            "topK": config["topK"],
            "candidateRadius": config["candidateRadius"],
            "minObservationThreshold": config["minObservationThreshold"],
        },
    }


def build_active_sensors(sensors: List[Dict], current_frame_index: int, min_observation_threshold: float) -> List[Dict]:
    """Build a list of active sensors with observed signals above threshold.

    Combines sampled peak and current concentration into a weighted
    observed signal, filtering by minimum threshold.

    Args:
        sensors: Raw sensor list with sampled series and peak data.
        current_frame_index: Current frame for concentration lookup.
        min_observation_threshold: Minimum signal threshold for activation.

    Returns:
        List of active sensor dicts with id, position, and observed signal.
    """
    active_sensors = []
    for sensor in sensors:
        sampled_series = sensor.get("sampledSeries") or []
        current_concentration = pick_sampled_concentration(sampled_series, current_frame_index)
        arrival_frame = pick_arrival_frame(sampled_series)
        arrival_time_sec = None
        if arrival_frame is not None and arrival_frame < len(sampled_series):
            arrival_time_sec = float(sampled_series[arrival_frame].get("timeSec") or 0)
        active_sensors.append(
            {
                "id": sensor.get("id", ""),
                "priority": int(sensor.get("priority") or 0),
                "x": float(sensor.get("x") if sensor.get("x") is not None else sensor.get("mapPoint", {}).get("x", 0)),
                "y": float(sensor.get("y") if sensor.get("y") is not None else sensor.get("mapPoint", {}).get("y", 0)),
                "currentConcentration": round(current_concentration, 2),
                "observedSignal": round(current_concentration, 2),
                "arrivalFrame": arrival_frame,
                "arrivalTimeSec": arrival_time_sec,
            }
        )

    return [sensor for sensor in active_sensors if sensor["observedSignal"] >= min_observation_threshold]


def pick_sampled_concentration(sampled_series: List[Dict], current_frame_index: int) -> float:
    """Get the concentration at a given frame index from a sampled series.

    Args:
        sampled_series: List of frame concentration samples.
        current_frame_index: Target frame index.

    Returns:
        Concentration value, or last available if index out of range.
    """
    if not sampled_series:
        return 0.0
    if 0 <= current_frame_index < len(sampled_series):
        return float(sampled_series[current_frame_index].get("concentration") or 0)
    return float(sampled_series[-1].get("concentration") or 0)


def to_geo_point(x: float, y: float) -> Dict:
    """Convert map pixel coordinates to geographic coordinates.

    Uses the configured origin longitude/latitude and map scale to
    compute approximate GPS coordinates with elevation.

    Args:
        x: Map pixel X-coordinate.
        y: Map pixel Y-coordinate.

    Returns:
        Dictionary with longitude, latitude, and altitude.
    """
    meters_x = x * MAP_METERS_PER_UNIT
    meters_y = y * MAP_METERS_PER_UNIT
    latitude = ORIGIN_LATITUDE - meters_y / 111320
    longitude = ORIGIN_LONGITUDE + meters_x / (111320 * math.cos(ORIGIN_LATITUDE * math.pi / 180))
    normalized_y = min(max(y, 0), 650)
    altitude = (
        BASE_ALTITUDE
        + (650 - normalized_y) * 0.02
        + math.sin(x / 90) * 1.8
        + math.cos(y / 70) * 1.2
    )
    return {
        "longitude": round(longitude, 6),
        "latitude": round(latitude, 6),
        "altitude": round(altitude, 2),
    }
