"""Phase 1 Gaussian plume diffusion simulation.

Implements a grid-based Gaussian plume dispersion model with obstacle,
channel, and atmospheric stability effects. Designed for chemical plant
gas leak scenario simulation.

Key features:
    - Grid-based concentration computation with configurable resolution.
    - Obstacle wake/shadow effects for buildings and equipment.
    - Road channel guidance for wind flow.
    - Multi-gas support with density and diffusion bias.
    - Sensor reading simulation.

Typical usage:
    result = create_phase1_diffusion_simulation(payload)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np

from diffusion.gaussian_plume import (
    PlumeParams,
    briggs_sigma_y,
    briggs_sigma_z,
    build_emission_times,
    choose_emit_step,
    resolve_environment,
    transient_ppm_field,
)


MAP_WIDTH = 1000
MAP_HEIGHT = 650
GRID_SIZE = 20
MAP_METERS_PER_UNIT = 0.5


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

PHASE1_GASES = [
    {
        "id": "co",
        "name": "一氧化碳",
        "color": "#f59e0b",
        "densityRatio": 0.97,
        "molarMass": 28.01,
        "diffusionBias": 1.05,
        "warningThreshold": 24,
        "dangerThreshold": 60,
        "blockingThreshold": 75,
    },
    {
        "id": "h2s",
        "name": "硫化氢",
        "color": "#ef4444",
        "densityRatio": 1.19,
        "molarMass": 34.08,
        "diffusionBias": 0.9,
        "warningThreshold": 8,
        "dangerThreshold": 20,
        "blockingThreshold": 24,
    },
    {
        "id": "ch4",
        "name": "甲烷",
        "color": "#38bdf8",
        "densityRatio": 0.55,
        "molarMass": 16.04,
        "diffusionBias": 1.5,
        "warningThreshold": 10,
        "dangerThreshold": 20,
        "blockingThreshold": 30,
    },
    {
        "id": "o2",
        "name": "氧气",
        "color": "#22c55e",
        "densityRatio": 1.11,
        "molarMass": 32.00,
        "diffusionBias": 0.95,
        "warningThreshold": 19,
        "dangerThreshold": 23,
        "blockingThreshold": 25,
    },
]


def get_gas_by_id(gas_id: Optional[str]) -> Dict:
    """Look up gas properties by gas identifier.

    Args:
        gas_id: Gas identifier string (e.g. 'h2s', 'nh3', 'co', 'toluene').

    Returns:
        Gas properties dictionary. Defaults to the first gas if not found.
    """
    for gas in PHASE1_GASES:
        if gas["id"] == gas_id:
            return dict(gas)
    return dict(PHASE1_GASES[0])


def create_phase1_diffusion_simulation(payload: Dict) -> Dict:
    """Run a phase 1 Gaussian plume diffusion simulation.

    Computes concentration fields across a grid for each time step,
    accounting for wind advection, atmospheric stability, obstacle effects,
    channel guidance, and sensor readings.

    Args:
        payload: Simulation parameters including facilities, roads, gas type,
            source location, wind, stability, release conditions, and
            terrain configuration.

    Returns:
        Simulation result with gas info, source point, frame data, stats,
        sensor series, and scenario metadata.
    """
    facilities = payload.get("facilities") or []
    roads = payload.get("roads") or []
    gas_id = payload.get("gasId")
    source_facility_id = payload.get("sourceFacilityId")
    source_map_point = payload.get("sourceMapPoint")
    source_rate = float(payload.get("sourceRate") or 0)
    release_duration = float(payload.get("releaseDuration") or 0)
    initial_temperature = parse_float(payload.get("initialTemperature"), 25.0)
    initial_pressure = parse_float(payload.get("initialPressure"), 0.8)
    release_height = parse_float(payload.get("releaseHeight"), 2.0)
    wind_speed = float(payload.get("windSpeed") or 0)
    wind_direction = float(payload.get("windDirection") or 0)
    ambient_temperature = parse_float(payload.get("ambientTemperature"), 25.0)
    humidity = parse_float(payload.get("humidity"), 55.0)
    stability_class = str(payload.get("stabilityClass") or "D").upper()
    terrain_roughness = clamp(parse_float(payload.get("terrainRoughness"), 0.45), 0.05, 1.5)
    obstacle_influence_enabled = payload.get("obstacleInfluenceEnabled", True) is not False
    # 钳制帧数到 [0, 600]，防止超大值耗尽资源（DoS）
    frame_count = int(clamp(int(payload.get("frameCount") or 0), 0, 600))
    frame_step_sec = float(payload.get("frameStepSec") or 1)
    sensors = payload.get("sensors") or []

    gas = get_gas_by_id(gas_id)
    source_facility = find_source_facility(facilities, source_facility_id)
    if not source_facility and not source_map_point:
        return {
            "gas": gas,
            "sourceFacility": None,
            "frames": [],
            "stats": {"peakConcentration": 0, "peakAffectedArea": 0},
        }

    source = normalize_source_point(source_map_point) or get_facility_center(source_facility)
    angle = wind_direction * math.pi / 180.0
    cos_theta = math.cos(angle)
    sin_theta = math.sin(angle)
    urban = resolve_environment(terrain_roughness)
    hard_blockers = build_hard_blockers(facilities)
    wake_obstacles = build_wake_obstacles(facilities)
    channel_segments = build_channel_segments(roads)
    frames: List[Dict] = []
    sensor_series = initialize_sensor_series(sensors)
    peak_concentration = 0.0
    peak_affected_area = 0.0
    peak_danger_area = 0.0

    # Physical plume parameters. ``sourceRate`` is interpreted as the gas
    # emission rate Q in grams per second; ambient temperature/pressure set the
    # mixing environment used for the kg/m3 -> ppm conversion.
    ambient_temperature_k = ambient_temperature + 273.15
    ambient_pressure_pa = initial_pressure * 1.0e5 if initial_pressure > 5.0 else max(initial_pressure, 0.5) * 1.013e5
    params = PlumeParams(
        emission_rate_g_s=max(source_rate, 0.0),
        wind_speed_10m=max(wind_speed, 0.0),
        release_height_m=max(release_height, 0.0),
        release_duration_s=max(release_duration, 0.0),
        stability_class=stability_class,
        urban=urban,
        molar_mass_g_mol=float(gas.get("molarMass", 28.97)),
        temperature_k=ambient_temperature_k,
        pressure_pa=ambient_pressure_pa,
    )
    emit_step_s = choose_emit_step(release_duration, frame_step_sec)
    emission_times = build_emission_times(release_duration, emit_step_s)

    # Pre-compute the grid geometry once: cell centres in pixels, and the
    # corresponding along/cross-wind coordinates in metres relative to the
    # source. ``along`` is positive in the direction the wind blows toward.
    xs = np.arange(GRID_SIZE / 2, MAP_WIDTH, GRID_SIZE, dtype=float)
    ys = np.arange(GRID_SIZE / 2, MAP_HEIGHT, GRID_SIZE, dtype=float)
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    dx = grid_x - float(source["x"])
    dy = grid_y - float(source["y"])
    along_m = (dx * cos_theta + dy * sin_theta) * MAP_METERS_PER_UNIT
    cross_m = (-dx * sin_theta + dy * cos_theta) * MAP_METERS_PER_UNIT

    # Humidity slightly enhances near-ground depletion for soluble gases; kept as
    # a small, explicit multiplicative attenuation rather than a hidden factor.
    humidity_retention = clamp(1.0 - humidity * 0.0008, 0.85, 1.0)

    cell_area_m2 = GRID_SIZE * GRID_SIZE * MAP_METERS_PER_UNIT * MAP_METERS_PER_UNIT
    warning_threshold = float(gas["warningThreshold"])
    danger_threshold = float(gas["dangerThreshold"])
    # Faint-but-visible floor for the diffuse halo (ppm).
    visible_floor = max(warning_threshold * 0.02, 0.05)

    for frame_index in range(max(frame_count, 0)):
        time_sec = frame_index * frame_step_sec

        ppm_field = transient_ppm_field(
            along_m,
            cross_m,
            time_sec,
            params,
            emission_times,
            emit_step_s,
            receptor_height_m=0.0,
        )
        ppm_field = ppm_field * humidity_retention

        cells: List[Dict] = []
        max_concentration = 0.0
        affected_area = 0.0
        warning_area = 0.0
        danger_area = 0.0

        rows, columns = ppm_field.shape
        for row in range(rows):
            for column in range(columns):
                base_ppm = float(ppm_field[row, column])
                if base_ppm < visible_floor:
                    continue
                cell_x = float(grid_x[row, column])
                cell_y = float(grid_y[row, column])
                if obstacle_influence_enabled and is_inside_hard_blocker(cell_x, cell_y, hard_blockers):
                    continue

                obstacle_effect = (
                    evaluate_obstacle_effects(
                        x=cell_x,
                        y=cell_y,
                        cos_theta=cos_theta,
                        sin_theta=sin_theta,
                        wake_obstacles=wake_obstacles,
                    )
                    if obstacle_influence_enabled
                    else {"obstacleFactor": 1.0, "shadowFactor": 1.0, "wakeOffset": 0.0}
                )
                channel_effect = evaluate_channel_effects(
                    x=cell_x,
                    y=cell_y,
                    wind_angle=angle,
                    channel_segments=channel_segments,
                )
                # Empirical near-field wake / channel attenuation applied on top
                # of the physically computed Gaussian-puff concentration. These
                # factors capture obstacle sheltering and street-channelling that
                # a flat-terrain Gaussian model cannot represent on its own.
                concentration = max(
                    0.0,
                    base_ppm
                    * obstacle_effect["obstacleFactor"]
                    * obstacle_effect["shadowFactor"]
                    * channel_effect["channelFactor"],
                )
                if concentration < visible_floor:
                    continue

                level = "low"
                alpha = min(0.24, 0.05 + concentration / (danger_threshold * 8))
                if concentration >= danger_threshold:
                    level = "danger"
                    alpha = min(0.56, 0.22 + concentration / (danger_threshold * 10))
                    danger_area += cell_area_m2
                elif concentration >= warning_threshold:
                    level = "warning"
                    alpha = min(0.42, 0.15 + concentration / (danger_threshold * 11))
                    warning_area += cell_area_m2

                affected_area += cell_area_m2
                max_concentration = max(max_concentration, concentration)
                cells.append(
                    {
                        "x": cell_x,
                        "y": cell_y,
                        "size": GRID_SIZE,
                        "concentration": round(concentration, 4),
                        "level": level,
                        "alpha": alpha,
                        "shadowFactor": round(obstacle_effect["shadowFactor"], 4),
                        "channelFactor": round(channel_effect["channelFactor"], 4),
                    }
                )

        # Plume visual envelope derived from the physical dispersion: the leading
        # edge sits at the wind-advection distance, the half-widths from Briggs
        # sigma at that distance (converted metres -> pixels, ~2 sigma envelope).
        advection_distance_m = params.effective_wind * time_sec
        advection_distance_px = advection_distance_m / MAP_METERS_PER_UNIT
        sigma_y_lead = float(briggs_sigma_y(max(advection_distance_m, 1.0), stability_class, urban))
        sigma_z_lead = float(briggs_sigma_z(max(advection_distance_m, 1.0), stability_class, urban))
        major_axis_px = max(advection_distance_px * 0.5, sigma_y_lead / MAP_METERS_PER_UNIT * 2.0)
        minor_axis_px = max(sigma_y_lead / MAP_METERS_PER_UNIT * 2.0, GRID_SIZE)

        frame_sensor_readings = build_frame_sensor_readings(sensors, cells, frame_index, time_sec)
        append_sensor_series(sensor_series, frame_sensor_readings)
        peak_concentration = max(peak_concentration, max_concentration)
        peak_affected_area = max(peak_affected_area, affected_area)
        peak_danger_area = max(peak_danger_area, danger_area)
        frames.append(
            {
                "frameIndex": frame_index,
                "timeSec": time_sec,
                "maxConcentration": max_concentration,
                "affectedArea": affected_area,
                "warningArea": warning_area,
                "dangerArea": danger_area,
                "cells": cells,
                "plume": {
                    "sourceX": source["x"],
                    "sourceY": source["y"],
                    "angle": angle,
                    "majorAxis": major_axis_px,
                    "minorAxis": minor_axis_px,
                    "driftDistance": advection_distance_px,
                },
                "sensorReadings": frame_sensor_readings,
            }
        )

    return {
        "gas": gas,
        "sourceFacility": source_facility,
        "sourcePoint": {
            "x": round(float(source["x"]), 2),
            "y": round(float(source["y"]), 2),
        },
        "frames": frames,
        "stats": {
            "peakConcentration": peak_concentration,
            "peakAffectedArea": peak_affected_area,
            "peakDangerArea": peak_danger_area,
        },
        "sensorSeries": sensor_series,
        "scenarioMeta": {
            "gasId": gas_id,
            "sourceRate": source_rate,
            "releaseDuration": release_duration,
            "initialTemperature": initial_temperature,
            "initialPressure": initial_pressure,
            "releaseHeight": release_height,
            "windSpeed": wind_speed,
            "windDirection": wind_direction,
            "ambientTemperature": ambient_temperature,
            "humidity": humidity,
            "stabilityClass": stability_class,
            "terrainRoughness": terrain_roughness,
            "obstacleInfluenceEnabled": obstacle_influence_enabled,
            "frameCount": frame_count,
            "frameStepSec": frame_step_sec,
        },
    }


def find_source_facility(facilities: Sequence[Dict], source_facility_id: Optional[str]) -> Optional[Dict]:
    """Find the source facility by ID or fall back to the first tank/tower.

    Args:
        facilities: List of facility objects with 'id' and 'type' fields.
        source_facility_id: Target facility ID, or None for fallback.

    Returns:
        Matching facility dictionary, or None if facilities list is empty.
    """
    if source_facility_id:
        for facility in facilities:
            if facility.get("id") == source_facility_id:
                return dict(facility)
    scoped = [facility for facility in facilities if facility.get("type") in ("tank", "tower") or facility.get("key")]
    if scoped:
        return dict(scoped[0])
    return dict(facilities[0]) if facilities else None


def normalize_source_point(source_map_point: Optional[Dict]) -> Optional[Dict]:
    """Normalize a source map point into a clean (x, y) dictionary.

    Args:
        source_map_point: Raw map point dict, or None.

    Returns:
        Normalized point dict with 'x' and 'y' floats, or None.
    """
    if not source_map_point:
        return None
    return {
        "x": float(source_map_point.get("x", 0)),
        "y": float(source_map_point.get("y", 0)),
    }


def get_facility_center(facility: Optional[Dict]) -> Dict:
    """Get the center point of a facility.

    Args:
        facility: Facility dict with type, position, and dimensions.

    Returns:
        Dictionary with 'x' and 'y' coordinates of the center.
    """
    facility = facility or {}
    if facility.get("type") in ("tank", "tower"):
        return {
            "x": float(facility.get("x", 0)),
            "y": float(facility.get("y", 0)),
        }
    return {
        "x": float(facility.get("x", 0)) + float(facility.get("w", 0)) / 2.0,
        "y": float(facility.get("y", 0)) + float(facility.get("h", 0)) / 2.0,
    }


def build_hard_blockers(facilities: Sequence[Dict]) -> List[Dict]:
    """Build hard blocking geometry from facilities (impassable areas).

    Non-tank/tower facilities are expanded by 4 units and treated as
    hard blockers that gas cannot penetrate.

    Args:
        facilities: List of facility objects with position and dimensions.

    Returns:
        List of blocker dicts with 'id', 'x1', 'x2', 'y1', 'y2' bounds.
    """
    blockers: List[Dict] = []
    for facility in facilities:
        if facility.get("type") in ("tank", "tower"):
            continue
        blockers.append(
            {
                "id": facility.get("id", ""),
                "x1": float(facility.get("x", 0)) - 4.0,
                "x2": float(facility.get("x", 0)) + float(facility.get("w", 0)) + 4.0,
                "y1": float(facility.get("y", 0)) - 4.0,
                "y2": float(facility.get("y", 0)) + float(facility.get("h", 0)) + 4.0,
            }
        )
    return blockers


def build_wake_obstacles(facilities: Sequence[Dict]) -> List[Dict]:
    """Build wake-generating obstacle geometry from facilities.

    Tank (circle) and tower/other (rect) obstacles with wake parameters
    for flow disturbance modeling.

    Args:
        facilities: List of facility objects with type and dimensions.

    Returns:
        List of obstacle dicts with shape, center, wake shift, shadow
        strength, and drag parameters.
    """
    obstacles: List[Dict] = []
    for index, facility in enumerate(facilities):
        center = get_facility_center(facility)
        if facility.get("type") == "tank":
            radius = float(facility.get("r", 0)) + 6.0
            obstacles.append(
                {
                    "id": facility.get("id", ""),
                    "shape": "circle",
                    "center": center,
                    "radius": radius,
                    "wakeShift": 5.6,
                    "shadowStrength": 0.72,
                    "dragStrength": 0.22,
                    "turnBias": 1 if index % 2 == 0 else -1,
                }
            )
            continue

        if facility.get("type") == "tower":
            half_width = float(facility.get("r", 0)) + 6.0
            half_height = float(facility.get("h", 0)) / 2.0 + 6.0
            obstacles.append(
                {
                    "id": facility.get("id", ""),
                    "shape": "rect",
                    "center": center,
                    "halfWidth": half_width,
                    "halfHeight": half_height,
                    "wakeShift": 7.5,
                    "shadowStrength": 0.78,
                    "dragStrength": 0.28,
                    "turnBias": 1 if index % 2 == 0 else -1,
                }
            )
            continue

        half_width = float(facility.get("w", 0)) / 2.0 + 8.0
        half_height = float(facility.get("h", 0)) / 2.0 + 8.0
        obstacles.append(
            {
                "id": facility.get("id", ""),
                "shape": "rect",
                "center": center,
                "halfWidth": half_width,
                "halfHeight": half_height,
                "wakeShift": 8.8,
                "shadowStrength": 0.88,
                "dragStrength": 0.36,
                "turnBias": 1 if index % 2 == 0 else -1,
            }
        )
    return obstacles


def build_channel_segments(roads: Sequence[Dict]) -> List[Dict]:
    """Build road channel segments for wind flow guidance.

    Converts road rectangles into oriented segments with width and
    angle for channel effect computation.

    Args:
        roads: List of road objects with position and dimensions.

    Returns:
        List of channel segment dicts with angle, center, length, width.
    """
    segments: List[Dict] = []
    for road in roads:
        width = max(float(road.get("w", 0)), float(road.get("h", 0)))
        horizontal = float(road.get("w", 0)) >= float(road.get("h", 0))
        if horizontal:
            segments.append(
                {
                    "angle": 0.0,
                    "centerX": float(road.get("x", 0)) + float(road.get("w", 0)) / 2.0,
                    "centerY": float(road.get("y", 0)) + float(road.get("h", 0)) / 2.0,
                    "halfLength": float(road.get("w", 0)) / 2.0,
                    "halfWidth": max(float(road.get("h", 0)) / 2.0, 5.0),
                    "width": width,
                }
            )
        else:
            segments.append(
                {
                    "angle": math.pi / 2.0,
                    "centerX": float(road.get("x", 0)) + float(road.get("w", 0)) / 2.0,
                    "centerY": float(road.get("y", 0)) + float(road.get("h", 0)) / 2.0,
                    "halfLength": float(road.get("h", 0)) / 2.0,
                    "halfWidth": max(float(road.get("w", 0)) / 2.0, 5.0),
                    "width": width,
                }
            )
    return segments


def is_inside_hard_blocker(x: float, y: float, hard_blockers: Sequence[Dict]) -> bool:
    """Check if a point is inside any hard blocker area.

    Args:
        x: X-coordinate to check.
        y: Y-coordinate to check.
        hard_blockers: List of blocker bounds dictionaries.

    Returns:
        True if the point falls within any blocker bounds.
    """
    for blocker in hard_blockers:
        if blocker["x1"] <= x <= blocker["x2"] and blocker["y1"] <= y <= blocker["y2"]:
            return True
    return False


def evaluate_obstacle_effects(x: float, y: float, cos_theta: float, sin_theta: float, wake_obstacles: Sequence[Dict]) -> Dict:
    """Evaluate obstacle drag, shadow, and wake effects at a point.

    Computes how obstacles modify wind flow and gas concentration at the
    given location based on obstacle geometry and wind direction.

    Args:
        x: X-coordinate of evaluation point.
        y: Y-coordinate of evaluation point.
        cos_theta: Cosine of wind direction angle.
        sin_theta: Sine of wind direction angle.
        wake_obstacles: List of obstacle geometry dictionaries.

    Returns:
        Dictionary with obstacleFactor, shadowFactor, and wakeOffset.
    """
    obstacle_factor = 1.0
    shadow_factor = 1.0
    wake_offset = 0.0
    for obstacle in wake_obstacles:
        center = obstacle["center"]
        dx = x - center["x"]
        dy = y - center["y"]
        along = dx * cos_theta + dy * sin_theta
        cross = -dx * sin_theta + dy * cos_theta
        half_along, half_cross = get_obstacle_projection_extent(obstacle, cos_theta, sin_theta)
        if along < -30 or abs(cross) > half_cross + 72:
            continue

        drag_band = half_cross + 24.0
        if -18.0 <= along <= half_along + 80.0 and abs(cross) <= drag_band:
            drag_core = 1.0 - min(1.0, abs(cross) / max(drag_band, 1.0))
            drag_decay = 1.0 - min(1.0, max(0.0, along + 18.0) / max(half_along + 98.0, 1.0))
            drag_strength = drag_core * max(0.15, drag_decay) * float(obstacle["dragStrength"])
            obstacle_factor *= max(0.42, 1.0 - drag_strength)

        shadow_band = half_cross + 18.0
        if along > half_along and along < half_along + 220.0 and abs(cross) <= shadow_band:
            shadow_depth = 1.0 - min(1.0, (along - half_along) / 220.0)
            shadow_core = 1.0 - min(1.0, abs(cross) / max(shadow_band, 1.0))
            shadow_strength = shadow_depth * shadow_core * float(obstacle["shadowStrength"])
            shadow_factor *= max(0.08, 1.0 - shadow_strength)

            wake_recovery = 1.0 - min(1.0, (along - half_along) / 160.0)
            wake_core = 1.0 - min(1.0, abs(cross) / max(shadow_band, 1.0))
            if wake_core > 0:
                direction = 1.0 if cross > 0 else -1.0
                if abs(cross) < 2.0:
                    direction = float(obstacle["turnBias"])
                wake_offset += direction * wake_core * wake_recovery * float(obstacle["wakeShift"])

    return {
        "obstacleFactor": max(0.16, obstacle_factor),
        "shadowFactor": max(0.05, shadow_factor),
        "wakeOffset": wake_offset,
    }


def evaluate_channel_effects(x: float, y: float, wind_angle: float, channel_segments: Sequence[Dict]) -> Dict:
    """Evaluate road channel guiding effects on wind and dispersion.

    Computes how road channels channel and accelerate wind flow, affecting
    along-wind and cross-wind dispersion scales.

    Args:
        x: X-coordinate of evaluation point.
        y: Y-coordinate of evaluation point.
        wind_angle: Wind direction in radians.
        channel_segments: List of channel segment geometry dictionaries.

    Returns:
        Dictionary with channelFactor, alongScale, and crossScale.
    """
    best_channel_factor = 1.0
    best_along_scale = 1.0
    best_cross_scale = 1.0
    for segment in channel_segments:
        distance = distance_to_channel(x, y, segment)
        influence_band = segment["halfWidth"] + 18.0
        if distance > influence_band:
            continue
        alignment = abs(math.cos(wind_angle - float(segment["angle"])))
        if alignment < 0.55:
            continue
        center_bias = 1.0 - min(1.0, distance / max(influence_band, 1.0))
        strength = alignment * center_bias
        best_channel_factor = max(best_channel_factor, 1.0 + strength * 0.34)
        best_along_scale = max(best_along_scale, 1.0 + strength * 0.42)
        best_cross_scale = min(best_cross_scale, max(0.66, 1.0 - strength * 0.24))

    return {
        "channelFactor": best_channel_factor,
        "alongScale": best_along_scale,
        "crossScale": best_cross_scale,
    }


def get_obstacle_projection_extent(obstacle: Dict, cos_theta: float, sin_theta: float) -> tuple[float, float]:
    """Get obstacle half extents projected along wind direction.

    Args:
        obstacle: Obstacle geometry dict with shape, radius/halfWidth/halfHeight.
        cos_theta: Cosine of wind direction angle.
        sin_theta: Sine of wind direction angle.

    Returns:
        Tuple of (half_along, half_cross) projected extents.
    """
    if obstacle["shape"] == "circle":
        radius = float(obstacle["radius"])
        return radius, radius
    half_width = float(obstacle["halfWidth"])
    half_height = float(obstacle["halfHeight"])
    half_along = abs(cos_theta) * half_width + abs(sin_theta) * half_height
    half_cross = abs(sin_theta) * half_width + abs(cos_theta) * half_height
    return half_along, half_cross


def distance_to_channel(x: float, y: float, segment: Dict) -> float:
    """Compute minimum distance from a point to a channel segment.

    Args:
        x: X-coordinate of the point.
        y: Y-coordinate of the point.
        segment: Channel segment dict with center, length, and angle.

    Returns:
        Minimum Euclidean distance to the segment.
    """
    local_x = x - float(segment["centerX"])
    local_y = y - float(segment["centerY"])
    if abs(float(segment["angle"])) < 1e-6:
        overflow = max(0.0, abs(local_x) - float(segment["halfLength"]))
        return math.hypot(overflow, local_y)
    overflow = max(0.0, abs(local_y) - float(segment["halfLength"]))
    return math.hypot(local_x, overflow)


def initialize_sensor_series(sensors: Sequence[Dict]) -> List[Dict]:
    """Initialize empty sensor series tracking structures.

    Args:
        sensors: List of sensor objects with 'id' fields.

    Returns:
        List of sensor series dicts with sensorId and empty series list.
    """
    return [{"sensorId": sensor.get("id", ""), "series": []} for sensor in sensors]


def build_frame_sensor_readings(sensors: Sequence[Dict], cells: Sequence[Dict], frame_index: int, time_sec: float) -> List[Dict]:
    """Build sensor readings for a single frame.

    Queries cell concentrations at each sensor's location.

    Args:
        sensors: List of sensor objects with position data.
        cells: List of cell concentration data for this frame.
        frame_index: Current frame index.
        time_sec: Current time in seconds.

    Returns:
        List of sensor reading dicts with concentration values.
    """
    readings = []
    for sensor in sensors:
        readings.append(
            {
                "sensorId": sensor.get("id", ""),
                "frameIndex": frame_index,
                "timeSec": time_sec,
                "concentration": get_cell_concentration_at_point(
                    cells,
                    float(sensor.get("x") if sensor.get("x") is not None else sensor.get("mapPoint", {}).get("x", 0)),
                    float(sensor.get("y") if sensor.get("y") is not None else sensor.get("mapPoint", {}).get("y", 0)),
                ),
            }
        )
    return readings


def append_sensor_series(sensor_series: List[Dict], frame_sensor_readings: Sequence[Dict]) -> None:
    """Append frame readings to sensor series buckets.

    Args:
        sensor_series: Mutable list of sensor series dicts to update.
        frame_sensor_readings: Readings from the current frame.
    """
    bucket_map = {item["sensorId"]: item for item in sensor_series}
    for reading in frame_sensor_readings:
        bucket = bucket_map.get(reading["sensorId"])
        if bucket is None:
            continue
        bucket["series"].append(
            {
                "frameIndex": int(reading["frameIndex"]),
                "timeSec": float(reading["timeSec"]),
                "concentration": round(float(reading["concentration"]), 4),
            }
        )


def get_cell_concentration_at_point(cells: Sequence[Dict], x: float, y: float) -> float:
    """Get the interpolated concentration at a point from cell data.

    Finds the nearest cell and applies distance-based fade.

    Args:
        cells: List of cell dicts with 'x', 'y', 'size', and 'concentration'.
        x: Target X-coordinate.
        y: Target Y-coordinate.

    Returns:
        Interpolated concentration value, or 0.0 if no cells exist.
    """
    if not cells:
        return 0.0
    nearest = None
    min_distance = math.inf
    for cell in cells:
        distance = math.hypot(float(cell.get("x", 0)) - x, float(cell.get("y", 0)) - y)
        if distance < min_distance:
            min_distance = distance
            nearest = cell
    if nearest is None:
        return 0.0
    fade = max(0.0, 1.0 - min_distance / max(float(nearest.get("size", 0)) * 1.8, 1.0))
    return float(nearest.get("concentration", 0)) * fade


def parse_float(value: object, default: float) -> float:
    """Parse a float value from an object, returning default on failure.

    Args:
        value: Input value to convert to float.
        default: Fallback value if conversion fails.

    Returns:
        Parsed float or default value.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
