"""第一阶段高斯烟羽扩散仿真。

实现基于网格的高斯烟羽扩散模型，并考虑障碍物、通道和大气稳定度影响。
用于化工厂气体泄漏场景仿真。

主要特性：
    - 基于网格的浓度计算，分辨率可配置。
    - 建筑和设备的尾流/遮挡影响。
    - 道路通道对风流的引导作用。
    - 支持带密度和扩散偏置的多种气体。
    - 传感器读数仿真。

典型用法：
    result = create_phase1_diffusion_simulation(payload)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np

from diffusion.gaussian_plume import (
    PlumeParams,
    build_emission_times,
    choose_emit_step,
    corrected_dispersion_coefficients,
    particle_rebound_alpha,
    resolve_environment,
    transient_ppm_field,
)


MAP_WIDTH = 1000
MAP_HEIGHT = 650
GRID_SIZE = 20
MAP_METERS_PER_UNIT = 0.5


def clamp(value: float, minimum: float, maximum: float) -> float:
    """将数值限制在最小值和最大值之间。

    参数：
        value: 需要限制的输入值。
        minimum: 区间下限。
        maximum: 区间上限。

    返回：
        限制在 [minimum, maximum] 内的值。
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
        "id": "nh3",
        "name": "氨气",
        "color": "#a855f7",
        "densityRatio": 0.59,
        "molarMass": 17.03,
        "diffusionBias": 1.25,
        "warningThreshold": 25,
        "dangerThreshold": 50,
        "blockingThreshold": 75,
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
    """根据气体标识查找气体属性。

    参数：
        gas_id: 气体标识字符串，例如 'nh3'、'co'、'ch4'、'o2'。

    返回：
        气体属性字典；找不到时默认返回第一个气体。
    """
    for gas in PHASE1_GASES:
        if gas["id"] == gas_id:
            return dict(gas)
    return dict(PHASE1_GASES[0])


def create_phase1_diffusion_simulation(payload: Dict) -> Dict:
    """运行第一阶段高斯烟羽扩散仿真。

    为每个时间步计算网格浓度场，并考虑风平流、大气稳定度、障碍物影响、
    通道引导和传感器读数。

    参数：
        payload: 仿真参数，包括设施、道路、气体类型、源位置、风、稳定度、
            释放条件和地形配置。

    返回：
        仿真结果，包含气体信息、源点、帧数据、统计量、传感器序列和场景元数据。
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
    model_variant = str(payload.get("modelVariant") or payload.get("plumeModelVariant") or "classic").lower()
    diffusion_correction_k = parse_float(payload.get("diffusionCorrectionK"), 1.0)
    wind_reference_height = parse_float(payload.get("windReferenceHeight"), 10.0)
    reflection_alpha_raw = payload.get("reflectionAlpha")
    if reflection_alpha_raw is None:
        reflection_alpha = particle_rebound_alpha(
            parse_float(payload.get("settlingVelocity"), 0.0),
            parse_float(payload.get("turbulentVelocityStd"), 1.0),
            parse_float(payload.get("reboundEta"), 0.0),
        ) if model_variant in ("improved", "modified", "corrected") else None
    else:
        reflection_alpha = clamp(parse_float(reflection_alpha_raw, 1.0), 0.0, 1.0)
    terrain_roughness = clamp(parse_float(payload.get("terrainRoughness"), 0.45), 0.05, 1.5)
    obstacle_influence_enabled = payload.get("obstacleInfluenceEnabled", True) is not False
    # 钳制帧数到 [0, 600]，防止超大值耗尽资源（DoS）。
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

    # 物理烟羽参数。``sourceRate`` 解释为气体排放速率 Q（克/秒）；
    # 环境温度/压力用于设置 kg/m3 -> ppm 换算所需的混合环境。
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
        model_variant=model_variant,
        wind_reference_height_m=wind_reference_height,
        diffusion_correction_k=diffusion_correction_k,
        reflection_alpha=reflection_alpha,
    )
    emit_step_s = choose_emit_step(release_duration, frame_step_sec)
    emission_times = build_emission_times(release_duration, emit_step_s)

    # 预先计算一次网格几何：像素单位的单元中心，以及相对源点的沿风/横风
    # 坐标（米）。``along`` 在风吹向的方向上为正。
    xs = np.arange(GRID_SIZE / 2, MAP_WIDTH, GRID_SIZE, dtype=float)
    ys = np.arange(GRID_SIZE / 2, MAP_HEIGHT, GRID_SIZE, dtype=float)
    grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
    dx = grid_x - float(source["x"])
    dy = grid_y - float(source["y"])
    along_m = (dx * cos_theta + dy * sin_theta) * MAP_METERS_PER_UNIT
    cross_m = (-dx * sin_theta + dy * cos_theta) * MAP_METERS_PER_UNIT

    # 湿度会轻微增强可溶气体的近地损耗；这里保留为小幅、显式的乘性衰减，
    # 避免变成隐藏因子。
    humidity_retention = clamp(1.0 - humidity * 0.0008, 0.85, 1.0)

    cell_area_m2 = GRID_SIZE * GRID_SIZE * MAP_METERS_PER_UNIT * MAP_METERS_PER_UNIT
    warning_threshold = float(gas["warningThreshold"])
    danger_threshold = float(gas["dangerThreshold"])
    # 扩散晕的淡可见下限（ppm）。
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
                # 在物理高斯烟团浓度之上叠加经验近场尾流/通道衰减。这些因子
                # 表示障碍遮蔽和道路通道效应，是平坦地形高斯模型自身无法表达的。
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

        # 烟羽可视包络来自物理扩散：前缘位于风平流距离处，半宽取该距离处的
        # Briggs sigma（米 -> 像素，约 2 sigma 包络）。
        advection_distance_m = params.effective_wind * time_sec
        advection_distance_px = advection_distance_m / MAP_METERS_PER_UNIT
        sigma_y_raw, sigma_z_raw = corrected_dispersion_coefficients(
            max(advection_distance_m, 1.0),
            stability_class,
            urban,
            params.effective_wind,
            diffusion_correction_k,
            model_variant,
        )
        sigma_y_lead = float(sigma_y_raw)
        sigma_z_lead = float(sigma_z_raw)
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
            "modelVariant": model_variant,
            "windReferenceHeight": wind_reference_height,
            "diffusionCorrectionK": diffusion_correction_k,
            "reflectionAlpha": reflection_alpha,
            "obstacleInfluenceEnabled": obstacle_influence_enabled,
            "frameCount": frame_count,
            "frameStepSec": frame_step_sec,
        },
    }


def find_source_facility(facilities: Sequence[Dict], source_facility_id: Optional[str]) -> Optional[Dict]:
    """按 ID 查找源设施，找不到时退回到第一个储罐/塔器。

    参数：
        facilities: 带 'id' 和 'type' 字段的设施对象列表。
        source_facility_id: 目标设施 ID；为 None 时使用兜底逻辑。

    返回：
        匹配的设施字典；若设施列表为空则返回 None。
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
    """将源地图点规范化为干净的 (x, y) 字典。

    参数：
        source_map_point: 原始地图点字典，或 None。

    返回：
        包含浮点 'x' 和 'y' 的规范化点字典，或 None。
    """
    if not source_map_point:
        return None
    return {
        "x": float(source_map_point.get("x", 0)),
        "y": float(source_map_point.get("y", 0)),
    }


def get_facility_center(facility: Optional[Dict]) -> Dict:
    """获取设施中心点。

    参数：
        facility: 包含类型、位置和尺寸的设施字典。

    返回：
        包含中心点 'x' 和 'y' 坐标的字典。
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
    """根据设施生成硬阻挡几何（不可穿透区域）。

    非储罐/塔器设施会向外扩展 4 个单位，并作为气体不可穿透的硬阻挡物。

    参数：
        facilities: 带位置和尺寸的设施对象列表。

    返回：
        阻挡物字典列表，包含 'id'、'x1'、'x2'、'y1'、'y2' 边界。
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
    """根据设施生成会产生尾流的障碍物几何。

    为储罐（圆形）以及塔器/其他设施（矩形）生成带尾流参数的障碍物，
    用于模拟流场扰动。

    参数：
        facilities: 带类型和尺寸的设施对象列表。

    返回：
        障碍物字典列表，包含形状、中心、尾流偏移、遮挡强度和阻力参数。
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
    """生成用于风流引导的道路通道段。

    将道路矩形转换为带宽度和角度的有向线段，用于计算通道效应。

    参数：
        roads: 带位置和尺寸的道路对象列表。

    返回：
        通道段字典列表，包含角度、中心、长度和宽度。
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
    """检查点是否位于任意硬阻挡区域内。

    参数：
        x: 待检查的 X 坐标。
        y: 待检查的 Y 坐标。
        hard_blockers: 阻挡物边界字典列表。

    返回：
        若点落在任一阻挡物边界内，则返回 True。
    """
    for blocker in hard_blockers:
        if blocker["x1"] <= x <= blocker["x2"] and blocker["y1"] <= y <= blocker["y2"]:
            return True
    return False


def evaluate_obstacle_effects(x: float, y: float, cos_theta: float, sin_theta: float, wake_obstacles: Sequence[Dict]) -> Dict:
    """评估某点处的障碍阻力、遮挡和尾流效应。

    根据障碍物几何和风向，计算障碍物如何改变该位置的风流和气体浓度。

    参数：
        x: 评估点 X 坐标。
        y: 评估点 Y 坐标。
        cos_theta: 风向角余弦。
        sin_theta: 风向角正弦。
        wake_obstacles: 障碍物几何字典列表。

    返回：
        包含 obstacleFactor、shadowFactor 和 wakeOffset 的字典。
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
    """评估道路通道对风和扩散的引导效应。

    计算道路通道如何约束并加速风流，从而影响沿风向和横风向扩散尺度。

    参数：
        x: 评估点 X 坐标。
        y: 评估点 Y 坐标。
        wind_angle: 风向，单位弧度。
        channel_segments: 通道段几何字典列表。

    返回：
        包含 channelFactor、alongScale 和 crossScale 的字典。
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
    """获取障碍物沿风向投影后的半尺寸。

    参数：
        obstacle: 障碍物几何字典，包含形状、半径/半宽/半高。
        cos_theta: 风向角余弦。
        sin_theta: 风向角正弦。

    返回：
        投影尺寸元组 (half_along, half_cross)。
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
    """计算点到通道段的最小距离。

    参数：
        x: 点的 X 坐标。
        y: 点的 Y 坐标。
        segment: 包含中心、长度和角度的通道段字典。

    返回：
        到通道段的最小欧氏距离。
    """
    local_x = x - float(segment["centerX"])
    local_y = y - float(segment["centerY"])
    if abs(float(segment["angle"])) < 1e-6:
        overflow = max(0.0, abs(local_x) - float(segment["halfLength"]))
        return math.hypot(overflow, local_y)
    overflow = max(0.0, abs(local_y) - float(segment["halfLength"]))
    return math.hypot(local_x, overflow)


def initialize_sensor_series(sensors: Sequence[Dict]) -> List[Dict]:
    """初始化空的传感器序列跟踪结构。

    参数：
        sensors: 带 'id' 字段的传感器对象列表。

    返回：
        传感器序列字典列表，包含 sensorId 和空 series 列表。
    """
    return [{"sensorId": sensor.get("id", ""), "series": []} for sensor in sensors]


def build_frame_sensor_readings(sensors: Sequence[Dict], cells: Sequence[Dict], frame_index: int, time_sec: float) -> List[Dict]:
    """构建单帧传感器读数。

    查询每个传感器位置对应的单元浓度。

    参数：
        sensors: 带位置数据的传感器对象列表。
        cells: 当前帧的单元浓度数据列表。
        frame_index: 当前帧索引。
        time_sec: 当前时间，单位秒。

    返回：
        带浓度值的传感器读数字典列表。
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
    """将帧读数追加到传感器序列桶中。

    参数：
        sensor_series: 要更新的可变传感器序列字典列表。
        frame_sensor_readings: 当前帧读数。
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
    """根据单元数据获取某点处的插值浓度。

    查找最近单元，并按距离应用衰减。

    参数：
        cells: 单元字典列表，包含 'x'、'y'、'size' 和 'concentration'。
        x: 目标 X 坐标。
        y: 目标 Y 坐标。

    返回：
        插值浓度值；若没有单元则返回 0.0。
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
    """从对象解析浮点数，失败时返回默认值。

    参数：
        value: 要转换为浮点数的输入值。
        default: 转换失败时使用的兜底值。

    返回：
        解析得到的浮点数，或默认值。
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
