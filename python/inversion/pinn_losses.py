"""Loss functions for PINN-based gas source inversion.

Provides observation loss, PDE residual loss, source regularization,
and combined loss computation for refining candidate source locations.

Uses the Gaussian plume model for physically-based signal prediction:
    C(x,y) = Q / (pi * u * sigma_y * sigma_z) * exp(-y^2 / (2*sigma_y^2))

Typical usage:
    loss = compute_loss_snapshot(center, candidate, sensors, scenario)
"""

from __future__ import annotations

import math
from typing import Dict, Sequence

MAP_METERS_PER_UNIT = 0.5
DEFAULT_EMISSION_RATE = 1.0
# Widened dispersion coefficients for park-scale inversion (100-500m)
# Standard PG-D: sigma_y=0.08*x/sqrt(u), sigma_z=0.06*x/sqrt(u)
# At park scale these are too narrow; use 2.5x wider for robust matching
SIGMA_Y_COEFF = 0.22
SIGMA_Z_COEFF = 0.15
MIN_WIND_SPEED = 0.5


def gaussian_plume_predict(
    source_x: float,
    source_y: float,
    sensor_x: float,
    sensor_y: float,
    wind_speed: float,
    wind_direction_deg: float,
    emission_rate: float = DEFAULT_EMISSION_RATE,
) -> float:
    """Predict concentration at a sensor location using the Gaussian plume model.

    Uses ground-level point source formulation with Pasquill-Gifford
    dispersion coefficients for stability class D.

    Args:
        source_x: Source X coordinate in map pixels.
        source_y: Source Y coordinate in map pixels.
        sensor_x: Sensor X coordinate in map pixels.
        sensor_y: Sensor Y coordinate in map pixels.
        wind_speed: Wind speed in m/s.
        wind_direction_deg: Wind direction in degrees (FROM direction).
        emission_rate: Source emission rate Q (default 1.0 for normalized).

    Returns:
        Predicted concentration value (0.0 if upwind or invalid).
    """
    wind_rad = math.radians(wind_direction_deg)
    dx = sensor_x - source_x
    dy = sensor_y - source_y
    along = dx * math.cos(wind_rad) + dy * math.sin(wind_rad)
    cross = -dx * math.sin(wind_rad) + dy * math.cos(wind_rad)

    if along <= 0:
        return 0.0

    u = max(wind_speed, MIN_WIND_SPEED)
    along_m = along * MAP_METERS_PER_UNIT
    cross_m = cross * MAP_METERS_PER_UNIT

    sigma_y = max(SIGMA_Y_COEFF * along_m / math.sqrt(u), 1.0)
    sigma_z = max(SIGMA_Z_COEFF * along_m / math.sqrt(u), 1.0)

    return emission_rate / (math.pi * u * sigma_y * sigma_z) * math.exp(-(cross_m ** 2) / (2 * sigma_y ** 2))


def fit_emission_rate(
    center: Dict,
    sensors: Sequence[Dict],
    scenario: Dict,
) -> float:
    """Find optimal emission rate Q that best fits observed sensor signals.

    Uses least-squares analytic solution:
        Q = sum(Ci * gi) / sum(gi^2)

    Args:
        center: Candidate source center dict with 'x' and 'y'.
        sensors: List of active sensor dicts with signal values.
        scenario: Scenario dict with windSpeed and windDirection.

    Returns:
        Optimal emission rate Q (clamped to reasonable range).
    """
    wind_speed = float(scenario.get("windSpeed") or 1.0)
    wind_direction = float(scenario.get("windDirection") or 0)
    sum_gi_ci = 0.0
    sum_gi_sq = 0.0
    for sensor in sensors:
        gi = gaussian_plume_predict(
            center["x"], center["y"],
            sensor["mapPoint"]["x"], sensor["mapPoint"]["y"],
            wind_speed, wind_direction,
        )
        ci = float(sensor.get("signal", 0.0))
        sum_gi_ci += gi * ci
        sum_gi_sq += gi * gi
    if sum_gi_sq < 1e-12:
        return 1.0
    return max(1e-6, sum_gi_ci / sum_gi_sq)


def compute_observation_loss(center: Dict, sensors: Sequence[Dict], scenario: Dict) -> float:
    """Compute sensor observation loss using Gaussian plume model.

    Fits optimal Q, then measures normalized weighted error between
    Gaussian-predicted and observed sensor signals.

    Args:
        center: Candidate source center dict with 'x' and 'y'.
        sensors: List of active sensor dicts with signal and priority.
        scenario: Scenario dict with windSpeed and windDirection.

    Returns:
        Normalized weighted observation error.
    """
    if not sensors:
        return 1.0
    wind_speed = float(scenario.get("windSpeed") or 1.0)
    wind_direction = float(scenario.get("windDirection") or 0)
    q = fit_emission_rate(center, sensors, scenario)

    max_signal = max(float(sensor.get("signal", 0.0)) for sensor in sensors) or 1.0
    raw_predictions = []
    for sensor in sensors:
        pred = gaussian_plume_predict(
            center["x"], center["y"],
            sensor["mapPoint"]["x"], sensor["mapPoint"]["y"],
            wind_speed, wind_direction, q,
        )
        raw_predictions.append(pred)
    max_predicted = max(raw_predictions) or 1.0

    total_weight = 0.0
    weighted_error = 0.0
    for i, sensor in enumerate(sensors):
        norm_predicted = raw_predictions[i] / max_predicted
        norm_observed = float(sensor.get("signal", 0.0)) / max_signal
        signal_weight = max(0.3, norm_observed ** 0.5)
        priority_weight = 1 + float(sensor.get("priority", 0)) * 0.18
        w = signal_weight * priority_weight
        weighted_error += abs(norm_predicted - norm_observed) * w
        total_weight += w
    return weighted_error / max(total_weight, 1.0)


def compute_pde_loss(center: Dict, scenario: Dict, sensors: Sequence[Dict]) -> float:
    """Compute PDE residual loss using Gaussian plume physics.

    Penalizes upwind sensors having significant signal, which violates
    the advection-diffusion equation. The Gaussian model naturally gives
    zero concentration upwind, so any observed upwind signal is a PDE
    violation proportional to its magnitude.

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
        distance = math.hypot(dx, dy)
        # Upwind penalty: sensors behind the source should have zero signal
        if along < 0:
            signal = float(sensor.get("signal", 0.0))
            residual += abs(along) / 120.0 * (1.0 + signal * 0.5)
        else:
            # Downwind: penalize large cross-wind spread relative to distance
            if distance > 0:
                cross_ratio = abs(cross) / distance
                if cross_ratio > 0.6:
                    residual += (cross_ratio - 0.6) * 0.8
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
    obs_loss = compute_observation_loss(center, sensors, scenario)
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
