"""Loss functions for PINN-based gas source inversion.

Provides observation loss, PDE residual loss, source regularization,
and combined loss computation for refining candidate source locations.

Typical usage:
    loss = compute_loss_snapshot(center, candidate, sensors, scenario)
"""

from __future__ import annotations

import math
from typing import Dict, Sequence


def compute_observation_loss(center: Dict, sensors: Sequence[Dict], distance_scale: float = 90.0) -> float:
    """Compute sensor observation loss for a candidate source center.

    Measures the weighted absolute error between predicted (distance-based)
    and observed sensor signals.

    Args:
        center: Candidate source center dict with 'x' and 'y'.
        sensors: List of active sensor dicts with signal and priority.
        distance_scale: Characteristic distance scale for signal decay.

    Returns:
        Normalized weighted observation error.
    """
    if not sensors:
        return 1.0
    max_signal = max(float(sensor.get("signal", 0.0)) for sensor in sensors) or 1.0
    weighted_error = 0.0
    for sensor in sensors:
        distance = math.hypot(center["x"] - sensor["mapPoint"]["x"], center["y"] - sensor["mapPoint"]["y"])
        predicted = 1.0 / (1.0 + distance / max(distance_scale, 1.0))
        observed = float(sensor.get("signal", 0.0)) / max_signal
        weighted_error += abs(predicted - observed) * (1 + float(sensor.get("priority", 0)) * 0.18)
    return weighted_error / max(len(sensors), 1)


def compute_pde_loss(center: Dict, scenario: Dict, sensors: Sequence[Dict]) -> float:
    """Compute PDE residual loss based on advection-diffusion physics.

    Penalizes cross-wind spread and upwind sensor signals based on
    wind direction and speed.

    Args:
        center: Candidate source center dict with 'x' and 'y'.
        scenario: Scenario dict with windSpeed and windDirection.
        sensors: List of active sensor dicts with positions.

    Returns:
        Normalized PDE residual loss.
    """
    wind_speed = float(scenario.get("windSpeed") or 0)
    wind_direction = math.radians(float(scenario.get("windDirection") or 0))
    cos_theta = math.cos(wind_direction)
    sin_theta = math.sin(wind_direction)
    residual = 0.0
    for sensor in sensors:
        dx = sensor["mapPoint"]["x"] - center["x"]
        dy = sensor["mapPoint"]["y"] - center["y"]
        along = dx * cos_theta + dy * sin_theta
        cross = -dx * sin_theta + dy * cos_theta
        residual += abs(cross) / 120.0 + max(0.0, -along) / 180.0 + wind_speed * 0.008
    return residual / max(len(sensors), 1)


def compute_source_regularization(center: Dict, candidate_center: Dict, candidate_radius: float) -> float:
    """Compute source regularization loss penalizing distance from candidate center.

    Args:
        center: Current estimated source center.
        candidate_center: Original candidate region center.
        candidate_radius: Radius of the candidate region.

    Returns:
        Normalized distance-based regularization loss.
    """
    distance = math.hypot(center["x"] - candidate_center["x"], center["y"] - candidate_center["y"])
    return distance / max(candidate_radius, 1.0)


def combine_losses(losses: Dict[str, float], weights: Dict[str, float]) -> float:
    """Combine multiple loss terms into a single weighted total.

    Args:
        losses: Dictionary of loss term names to values.
        weights: Dictionary of loss term names to weights.

    Returns:
        Weighted sum of all loss terms.
    """
    total = 0.0
    for name, value in losses.items():
        total += float(weights.get(name, 1.0)) * float(value)
    return total


def compute_loss_snapshot(center: Dict, candidate: Dict, sensors: Sequence[Dict], scenario: Dict) -> Dict[str, float]:
    """Compute a complete loss snapshot for a candidate source location.

    Combines observation, PDE, and source regularization losses with
    default weights.

    Args:
        center: Candidate source center to evaluate.
        candidate: Candidate region dict with center and radius.
        sensors: List of active sensor dicts.
        scenario: Scenario dict with wind data.

    Returns:
        Dictionary with obs, pde, src, and total loss values.
    """
    obs_loss = compute_observation_loss(center, sensors)
    pde_loss = compute_pde_loss(center, scenario, sensors)
    src_loss = compute_source_regularization(center, candidate["center"], float(candidate.get("radius") or 45))
    total_loss = combine_losses(
        {
            "obs": obs_loss,
            "pde": pde_loss,
            "src": src_loss,
        },
        {
            "obs": 1.0,
            "pde": 0.55,
            "src": 0.35,
        },
    )
    return {
        "obs": round(obs_loss, 4),
        "pde": round(pde_loss, 4),
        "src": round(src_loss, 4),
        "total": round(total_loss, 4),
    }
