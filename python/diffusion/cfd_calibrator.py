"""CFD calibration module for diffusion simulation results.

Provides correction factors based on facility obstacles, wind conditions,
and atmospheric stability to calibrate Gaussian plume diffusion outputs
toward computational fluid dynamics (CFD) accuracy.

Typical usage:
    calibrated = apply_cfd_calibration(simulation_result, payload)
"""

from __future__ import annotations

import math
from typing import Dict, Sequence


STABILITY_TURBULENCE = {
    "A": 0.22,
    "B": 0.18,
    "C": 0.14,
    "D": 0.1,
    "E": 0.07,
    "F": 0.04,
}


def apply_cfd_calibration(simulation_result: Dict, payload: Dict) -> Dict:
    """Apply CFD calibration factors to a diffusion simulation result.

    Corrects cell concentrations, plume geometry, and affected areas based
    on facility obstacle density, wind conditions, and atmospheric stability.

    Args:
        simulation_result: Raw diffusion simulation output with frame data.
        payload: Original request payload containing facilities, gas, wind
            parameters, and stability class.

    Returns:
        Calibrated simulation result with corrected concentrations, plume
        geometry, and calibration metadata.
    """
    if not simulation_result.get("frames"):
        calibration = {
            "enabled": False,
            "reason": "empty_frames",
        }
        result = dict(simulation_result)
        result["calibration"] = calibration
        return result

    source_point = simulation_result.get("sourcePoint") or payload.get("sourceMapPoint") or {"x": 0, "y": 0}
    factors = build_cfd_calibration_factors(
        facilities=payload.get("facilities") or [],
        gas_id=payload.get("gasId"),
        source_point=source_point,
        wind_speed=float(payload.get("windSpeed") or 0),
        wind_direction=float(payload.get("windDirection") or 0),
        stability_class=str(payload.get("stabilityClass") or "D").upper(),
    )

    gas = simulation_result.get("gas") or {}
    peak_concentration = 0.0
    peak_affected_area = 0.0
    frames = []
    release_duration = float(payload.get("releaseDuration") or 1)

    for frame in simulation_result.get("frames") or []:
        progress = min(1.0, float(frame.get("timeSec", 0)) / max(release_duration * 1.4, 1.0))
        wake_rotation = float(factors["wakeAngleBiasRad"]) * (0.35 + progress * 0.65)
        corrected_angle = float(frame.get("plume", {}).get("angle", 0)) + wake_rotation

        max_concentration = 0.0
        affected_area = 0.0
        warning_area = 0.0
        danger_area = 0.0
        cells = []
        for cell in frame.get("cells") or []:
            corrected_concentration = correct_cell_concentration(
                cell=cell,
                frame=frame,
                gas=gas,
                source_point=source_point,
                plume_angle=corrected_angle,
                factors=factors,
                time_sec=float(frame.get("timeSec", 0)),
            )
            classified = classify_cell(corrected_concentration, gas)
            if corrected_concentration > 0.12:
                affected_area += classified["areaTag"]["any"]
            warning_area += classified["areaTag"]["warning"]
            danger_area += classified["areaTag"]["danger"]
            max_concentration = max(max_concentration, corrected_concentration)

            next_cell = dict(cell)
            next_cell["concentration"] = corrected_concentration
            next_cell["level"] = classified["level"]
            next_cell["alpha"] = classified["alpha"]
            cells.append(next_cell)

        peak_concentration = max(peak_concentration, max_concentration)
        peak_affected_area = max(peak_affected_area, affected_area)

        next_frame = dict(frame)
        next_frame["maxConcentration"] = max_concentration
        next_frame["affectedArea"] = affected_area
        next_frame["warningArea"] = warning_area
        next_frame["dangerArea"] = danger_area
        next_frame["cells"] = cells
        if frame.get("plume"):
            next_plume = dict(frame["plume"])
            next_plume["angle"] = corrected_angle
            next_plume["majorAxis"] = round(float(frame["plume"].get("majorAxis", 0)) * float(factors["kCfdY"]), 2)
            next_plume["minorAxis"] = round(float(frame["plume"].get("minorAxis", 0)) * float(factors["kCfdZ"]), 2)
            next_plume["driftDistance"] = round(float(frame["plume"].get("driftDistance", 0)) * float(factors["kLocalWind"]), 2)
            next_frame["plume"] = next_plume
        next_frame["calibration"] = {
            "correctedAngle": corrected_angle,
            "concentrationScale": factors["kCfdConc"],
        }
        frames.append(next_frame)

    result = dict(simulation_result)
    result["frames"] = frames
    result["stats"] = {
        **(simulation_result.get("stats") or {}),
        "peakConcentration": peak_concentration,
        "peakAffectedArea": peak_affected_area,
    }
    result["calibration"] = {
        "enabled": True,
        "model": "parameterized-cfd-calibrator",
        "factors": factors,
    }
    return result


def build_cfd_calibration_factors(
    facilities: Sequence[Dict],
    gas_id: str | None,
    source_point: Dict,
    wind_speed: float,
    wind_direction: float,
    stability_class: str,
) -> Dict:
    """Build CFD calibration factors from facility layout and meteorology.

    Evaluates nearby obstacles, computes density and turbulence factors,
    and derives calibration coefficients for concentration, plume geometry,
    and wake effects.

    Args:
        facilities: List of facility objects with type and position data.
        gas_id: Identifier string for the gas type (e.g. 'nh3', 'h2s').
        source_point: Source leak point with 'x' and 'y' coordinates.
        wind_speed: Wind speed in m/s.
        wind_direction: Wind direction in degrees.
        stability_class: Atmospheric stability class (A-F).

    Returns:
        Dictionary of calibration factors including kCfdY, kCfdZ, kCfdConc,
        kWake, kLocalWind, and wakeAngleBiasRad.
    """
    nearby = []
    for facility in facilities:
        center = get_facility_center(facility)
        if math.hypot(center["x"] - float(source_point.get("x", 0)), center["y"] - float(source_point.get("y", 0))) <= 220:
            nearby.append(facility)

    obstacle_score = 0.0
    for facility in nearby:
        if facility.get("type") == "tower":
            obstacle_score += 1.2
        elif facility.get("type") == "tank":
            obstacle_score += 0.85
        else:
            obstacle_score += 0.4

    density_factor = clamp(obstacle_score / 18.0, 0.0, 1.0)
    turbulence = STABILITY_TURBULENCE.get(stability_class, STABILITY_TURBULENCE["D"])
    wind_factor = clamp(wind_speed / 8.0, 0.0, 1.0)
    direction_bias = math.sin((wind_direction * math.pi) / 180.0) * 0.08
    gas_bias = 0.06 if gas_id == "h2s" else 0.04 if gas_id == "co" else 0.03

    return {
        "obstacleDensity": round(density_factor, 4),
        "kCfdY": round(1 + density_factor * 0.24 + turbulence * 0.55, 4),
        "kCfdZ": round(1 + density_factor * 0.18 + turbulence * 0.4, 4),
        "kCfdConc": round(1 + density_factor * 0.12 + gas_bias - wind_factor * 0.05, 4),
        "kWake": round(1 + density_factor * 0.28 + turbulence * 0.35, 4),
        "kLocalWind": round(1 - density_factor * 0.08 + wind_factor * 0.06, 4),
        "wakeAngleBiasRad": round((density_factor * 0.16 + direction_bias) * (0.7 if wind_speed > 5 else 1), 4),
    }


def correct_cell_concentration(
    cell: Dict,
    frame: Dict,
    gas: Dict,
    source_point: Dict,
    plume_angle: float,
    factors: Dict,
    time_sec: float,
) -> float:
    """Correct a single cell's concentration using CFD calibration factors.

    Applies plume geometry corrections, wake gain, boundary decay, and
    time-based decay to the raw cell concentration.

    Args:
        cell: Cell data with 'x', 'y', and 'concentration' fields.
        frame: Frame data containing plume geometry.
        gas: Gas properties dictionary.
        source_point: Source leak point with 'x' and 'y' coordinates.
        plume_angle: Corrected plume angle in radians.
        factors: CFD calibration factors dictionary.
        time_sec: Elapsed time in seconds.

    Returns:
        Corrected concentration value rounded to 4 decimal places.
    """
    dx = float(cell.get("x", 0)) - float(source_point.get("x", 0))
    dy = float(cell.get("y", 0)) - float(source_point.get("y", 0))
    cos_theta = math.cos(plume_angle)
    sin_theta = math.sin(plume_angle)
    along = dx * cos_theta + dy * sin_theta
    cross = -dx * sin_theta + dy * cos_theta

    minor_axis = max(float(frame.get("plume", {}).get("minorAxis", 1)) * 0.42, 1.0)
    major_axis = max(float(frame.get("plume", {}).get("majorAxis", 1)) * float(factors["kCfdY"]) * 1.8, 1.0)
    wake_band = math.exp(-abs(cross) / minor_axis)
    downwind_gain = 1 + float(factors["kWake"]) * 0.12 * wake_band if along > 0 else 0.92
    boundary_decay = max(0.84, 1 - abs(cross) / major_axis * 0.18)
    time_decay = 1 - min(0.12, time_sec / 9000.0)
    corrected = (
        float(cell.get("concentration", 0))
        * float(factors["kCfdConc"])
        * downwind_gain
        * boundary_decay
        * time_decay
    )
    return round(max(0.0, corrected), 4)


def classify_cell(concentration: float, gas: Dict) -> Dict:
    """Classify a cell's danger level based on concentration thresholds.

    Args:
        concentration: Gas concentration value.
        gas: Gas properties dictionary with dangerThreshold and
            warningThreshold.

    Returns:
        Dictionary with 'level' ('low'/'warning'/'danger'), 'alpha' for
        visualization opacity, and 'areaTag' with area measurements.
    """
    danger_threshold = max(float(gas.get("dangerThreshold", 1) or 1), 1.0)
    warning_threshold = float(gas.get("warningThreshold", 0) or 0)
    cell_area = 20 * 20 * 0.5 * 0.5
    level = "low"
    alpha = min(0.24, 0.05 + concentration / (danger_threshold * 8))
    warning = 0.0
    danger = 0.0

    if concentration >= danger_threshold:
        level = "danger"
        alpha = min(0.56, 0.22 + concentration / (danger_threshold * 10))
        danger = cell_area
    elif concentration >= warning_threshold:
        level = "warning"
        alpha = min(0.42, 0.15 + concentration / (danger_threshold * 11))
        warning = cell_area

    return {
        "level": level,
        "alpha": alpha,
        "areaTag": {
            "any": cell_area if concentration > 0.12 else 0.0,
            "warning": warning,
            "danger": danger,
        },
    }


def get_facility_center(facility: Dict) -> Dict:
    """Get the center point of a facility.

    For tank/tower types, returns the direct coordinates. For other types,
    computes the center from position and dimensions.

    Args:
        facility: Facility dictionary with 'x', 'y', 'w', 'h', and 'type'.

    Returns:
        Dictionary with 'x' and 'y' coordinates of the center.
    """
    if facility.get("type") in ("tank", "tower"):
        return {"x": float(facility.get("x", 0)), "y": float(facility.get("y", 0))}
    return {
        "x": float(facility.get("x", 0)) + float(facility.get("w", 0)) / 2.0,
        "y": float(facility.get("y", 0)) + float(facility.get("h", 0)) / 2.0,
    }


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a value between a minimum and maximum range.

    Args:
        value: The input value to clamp.
        minimum: Lower bound of the range.
        maximum: Upper bound of the range.

    Returns:
        The clamped value within [minimum, maximum].
    """
    return min(max(value, minimum), maximum)
