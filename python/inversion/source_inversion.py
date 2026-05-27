"""Two-stage PINN source inversion implementation.

Performs candidate ranking, iterative refinement with shrinking radius,
and convergence tracking to estimate the gas leak source location from
sensor observations and scenario data.

Typical usage:
    result = run_two_stage_inversion(dataset)
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence

from .pinn_losses import compute_loss_snapshot, fit_emission_rate, gaussian_plume_predict
from .pinn_model import blend_points, estimate_weighted_center

SIMPLEX_MAX_ITER = 200
SIMPLEX_ALPHA = 1.0
SIMPLEX_GAMMA = 2.0
SIMPLEX_RHO = 0.5
SIMPLEX_SIGMA = 0.5
SIMPLEX_XTOL = 3.0
SIMPLEX_FTOL = 1e-4


def nelder_mead_2d(
    objective,
    x0: float,
    y0: float,
    initial_step: float = 25.0,
    max_iter: int = SIMPLEX_MAX_ITER,
    xtol: float = SIMPLEX_XTOL,
    ftol: float = SIMPLEX_FTOL,
) -> Dict:
    """Run Nelder-Mead simplex optimization in 2D.

    Args:
        objective: Function that takes (x, y) and returns a scalar loss.
        x0: Initial X coordinate.
        y0: Initial Y coordinate.
        initial_step: Initial simplex edge length.
        max_iter: Maximum iterations.
        xtol: Convergence threshold for coordinate change.
        ftol: Convergence threshold for function value change.

    Returns:
        Dict with 'best', 'history', 'iterations', 'converged'.
    """
    simplex = [
        [x0, y0],
        [x0 + initial_step, y0],
        [x0, y0 + initial_step],
    ]
    values = [objective(p[0], p[1]) for p in simplex]
    history = [{"x": p[0], "y": p[1], "loss": v} for p, v in zip(simplex, values)]

    for iteration in range(max_iter):
        order = sorted(range(3), key=lambda i: values[i])
        best_idx, worst_idx = order[0], order[2]
        mid_idx = order[1]

        if values[worst_idx] - values[best_idx] < ftol:
            return {
                "best": {"x": simplex[best_idx][0], "y": simplex[best_idx][1]},
                "history": history,
                "iterations": iteration + 1,
                "converged": True,
            }

        centroid = [
            (simplex[best_idx][0] + simplex[mid_idx][0]) / 2.0,
            (simplex[best_idx][1] + simplex[mid_idx][1]) / 2.0,
        ]

        reflected = [
            centroid[0] + SIMPLEX_ALPHA * (centroid[0] - simplex[worst_idx][0]),
            centroid[1] + SIMPLEX_ALPHA * (centroid[1] - simplex[worst_idx][1]),
        ]
        f_reflected = objective(reflected[0], reflected[1])

        if values[best_idx] <= f_reflected < values[mid_idx]:
            simplex[worst_idx] = reflected
            values[worst_idx] = f_reflected
        elif f_reflected < values[best_idx]:
            expanded = [
                centroid[0] + SIMPLEX_GAMMA * (reflected[0] - centroid[0]),
                centroid[1] + SIMPLEX_GAMMA * (reflected[1] - centroid[1]),
            ]
            f_expanded = objective(expanded[0], expanded[1])
            if f_expanded < f_reflected:
                simplex[worst_idx] = expanded
                values[worst_idx] = f_expanded
            else:
                simplex[worst_idx] = reflected
                values[worst_idx] = f_reflected
        else:
            contracted = [
                centroid[0] + SIMPLEX_RHO * (simplex[worst_idx][0] - centroid[0]),
                centroid[1] + SIMPLEX_RHO * (simplex[worst_idx][1] - centroid[1]),
            ]
            f_contracted = objective(contracted[0], contracted[1])
            if f_contracted < values[worst_idx]:
                simplex[worst_idx] = contracted
                values[worst_idx] = f_contracted
            else:
                for i in range(3):
                    if i != best_idx:
                        simplex[i][0] = simplex[best_idx][0] + SIMPLEX_SIGMA * (simplex[i][0] - simplex[best_idx][0])
                        simplex[i][1] = simplex[best_idx][1] + SIMPLEX_SIGMA * (simplex[i][1] - simplex[best_idx][1])
                        values[i] = objective(simplex[i][0], simplex[i][1])

        best_val = min(values)
        history.append({"x": simplex[order[0]][0], "y": simplex[order[0]][1], "loss": best_val})

    best_idx = min(range(3), key=lambda i: values[i])
    return {
        "best": {"x": simplex[best_idx][0], "y": simplex[best_idx][1]},
        "history": history,
        "iterations": max_iter,
        "converged": False,
    }


def run_two_stage_inversion(dataset: Dict) -> Dict:
    """Run a two-stage PINN inversion to estimate gas source location.

    Stage 1: Prepare and rank candidate regions by loss and support.
    Stage 2: Refine the best candidate through iterative radius shrinking.

    Args:
        dataset: Normalized inversion dataset with activeSensors,
            candidateRegions, scenario, and trainingConfig.

    Returns:
        Inversion result with estimated source, loss history, and
        error metrics.
    """
    active_sensors = dataset.get("activeSensors") or []
    candidate_regions = prepare_candidate_regions(dataset.get("candidateRegions") or [], active_sensors)
    if not candidate_regions:
        return create_empty_result(dataset)

    weighted_center = estimate_weighted_center(active_sensors, candidate_regions[0]["center"])
    ranked_candidates = rank_candidates(candidate_regions, active_sensors, dataset.get("scenario") or {}, weighted_center)

    top_k = min(len(ranked_candidates), int((dataset.get("trainingConfig") or {}).get("topK", 4) or 4))
    refined_results = []
    for candidate in ranked_candidates[:top_k]:
        refinement = refine_candidate(
            candidate=candidate,
            sensors=active_sensors,
            scenario=dataset.get("scenario") or {},
            weighted_center=weighted_center,
            training_config=dataset.get("trainingConfig") or {},
            gas=dataset.get("gas") or {},
            true_source_map_point=dataset.get("trueSourceMapPoint"),
        )
        refined_results.append((candidate, refinement))

    best_pair = min(refined_results, key=lambda pair: pair[1]["errorMetrics"]["finalLoss"])
    best_candidate, refinement = best_pair

    return {
        "datasetVersion": "pyodide-pinn-inversion-v1",
        "stage": "python_pinn_two_stage",
        "timeline": {
            "currentFrameIndex": dataset.get("currentFrameIndex", 0),
            "currentTimeSec": dataset.get("frameTimeSec", 0),
        },
        "coarseCandidates": ranked_candidates,
        "estimatedSource": refinement["estimatedSource"],
        "confidenceRadius": refinement["confidenceRadius"],
        "lossHistory": refinement["lossHistory"],
        "shrinkFrames": refinement["shrinkFrames"],
        "iterations": refinement["iterations"],
        "errorMetrics": refinement["errorMetrics"],
        "summary": refinement["summary"],
    }


def prepare_candidate_regions(candidate_regions: Sequence[Dict], sensors: Sequence[Dict]) -> List[Dict]:
    """Prepare and normalize candidate regions, or create a fallback.

    Args:
        candidate_regions: Raw candidate region list from coarse search.
        sensors: Active sensor list for fallback center estimation.

    Returns:
        Normalized list of candidate region dicts.
    """
    if candidate_regions:
        prepared = []
        for index, candidate in enumerate(candidate_regions):
            prepared.append(
                {
                    "candidateId": candidate.get("candidateId") or f"cand_{index + 1}",
                    "rank": int(candidate.get("rank") or index + 1),
                    "center": normalize_point(candidate.get("center") or {"x": 500, "y": 325}),
                    "geoCenter": candidate.get("geoCenter"),
                    "score": float(candidate.get("score") or 0),
                    "error": float(candidate.get("error") or 0),
                    "supportCount": int(candidate.get("supportCount") or 0),
                    "radius": float(candidate.get("radius") or 45),
                    "bounds": candidate.get("bounds"),
                    "label": candidate.get("label") or f"候选区域 {index + 1}",
                }
            )
        return prepared

    fallback_center = estimate_weighted_center(sensors, {"x": 500, "y": 325})
    return [
        {
            "candidateId": "cand_1",
            "rank": 1,
            "center": fallback_center,
            "geoCenter": None,
            "score": 0.0,
            "error": 0.0,
            "supportCount": len(sensors),
            "radius": 55.0,
            "bounds": None,
            "label": "候选区域 1",
        }
    ]


def rank_candidates(candidate_regions: Sequence[Dict], sensors: Sequence[Dict], scenario: Dict, weighted_center: Dict) -> List[Dict]:
    """Rank candidate regions by loss, support, and proximity scores.

    Args:
        candidate_regions: List of candidate region dicts.
        sensors: Active sensor list for loss computation.
        scenario: Scenario dict with wind data.
        weighted_center: Sensor-weighted center for proximity bonus.

    Returns:
        Ranked list of candidates with added rankScore and lossSnapshot.
    """
    ranked = []
    for candidate in candidate_regions:
        center = candidate["center"]
        loss_snapshot = compute_loss_snapshot(center, candidate, sensors, scenario)
        support_bonus = min(0.35, float(candidate.get("supportCount", 0)) / max(len(sensors), 1) * 0.35) if sensors else 0.0
        proximity_bonus = max(0.0, 1.0 - distance(center, weighted_center) / max(float(candidate.get("radius") or 45) * 3.2, 1.0)) * 0.25
        score = max(0.0, 1.8 - loss_snapshot["total"] + support_bonus + proximity_bonus + float(candidate.get("score", 0)) * 0.15)
        ranked.append(
            {
                **candidate,
                "rankScore": round(score, 4),
                "lossSnapshot": loss_snapshot,
            }
        )
    ranked.sort(key=lambda item: item["rankScore"], reverse=True)
    for index, candidate in enumerate(ranked):
        candidate["rank"] = index + 1
    return ranked


def refine_candidate(
    candidate: Dict,
    sensors: Sequence[Dict],
    scenario: Dict,
    weighted_center: Dict,
    training_config: Dict,
    gas: Dict,
    true_source_map_point: Dict | None,
) -> Dict:
    """Refine a candidate source location using Nelder-Mead optimization.

    Uses gradient-free simplex optimization to minimize the Gaussian
    plume observation loss, starting from the candidate center and
    bounded within the candidate region.

    Args:
        candidate: Selected candidate region to refine.
        sensors: Active sensor list.
        scenario: Scenario dict with wind data.
        weighted_center: Sensor-weighted center for initialization.
        training_config: Config dict with animationSteps and
            convergenceRatio.
        gas: Gas properties dict.
        true_source_map_point: Optional true source location for
            error computation.

    Returns:
        Refinement result with iterations, estimated source, loss
        history, and error metrics.
    """
    wind_speed = float(scenario.get("windSpeed") or 1.0)
    wind_direction = float(scenario.get("windDirection") or 0)
    candidate_center = candidate["center"]
    candidate_radius = float(candidate.get("radius") or 45)
    bounds_min_x = candidate_center["x"] - candidate_radius * 4
    bounds_max_x = candidate_center["x"] + candidate_radius * 4
    bounds_min_y = candidate_center["y"] - candidate_radius * 4
    bounds_max_y = candidate_center["y"] + candidate_radius * 4

    def objective(x, y):
        x_clamped = max(bounds_min_x, min(bounds_max_x, x))
        y_clamped = max(bounds_min_y, min(bounds_max_y, y))
        center = {"x": x_clamped, "y": y_clamped}
        snapshot = compute_loss_snapshot(center, candidate, sensors, scenario)
        return snapshot["total"]

    initial_x = blend_points(candidate_center, weighted_center, 0.5)["x"]
    initial_y = blend_points(candidate_center, weighted_center, 0.5)["y"]
    initial_step = max(candidate_radius * 1.5, 25.0)

    nm_result = nelder_mead_2d(
        objective, initial_x, initial_y,
        initial_step=initial_step,
        max_iter=max(int(training_config.get("animationSteps") or 18), 20) * 8,
    )

    best_center = nm_result["best"]
    best_center["x"] = round(best_center["x"], 2)
    best_center["y"] = round(best_center["y"], 2)

    iterations = []
    shrink_frames = []
    loss_history = []
    total_points = len(nm_result["history"])
    max_animation_steps = max(int(training_config.get("animationSteps") or 18), 8)
    step_indices = []
    if total_points <= max_animation_steps:
        step_indices = list(range(total_points))
    else:
        for i in range(max_animation_steps):
            step_indices.append(int(i * (total_points - 1) / (max_animation_steps - 1)))

    for anim_idx, hist_idx in enumerate(step_indices):
        point = nm_result["history"][hist_idx]
        center = {"x": round(point["x"], 2), "y": round(point["y"], 2)}
        progress = anim_idx / max(max_animation_steps - 1, 1)
        eased = 1 - math.pow(1 - progress, 2)
        radius = round(candidate_radius * (1.2 - eased * 0.85), 2)
        polygon = build_refinement_polygon(center, radius, anim_idx, int(candidate.get("rank") or 1))
        loss_snapshot = compute_loss_snapshot(center, candidate, sensors, scenario)
        confidence = round(1 - eased * 0.78, 4)

        iterations.append({
            "iteration": anim_idx + 1,
            "progress": round(progress, 4),
            "center": center,
            "radius": radius,
            "polygon": polygon,
            "loss": loss_snapshot["total"],
            "confidence": confidence,
            "lossBreakdown": loss_snapshot,
        })
        shrink_frames.append(polygon)
        loss_history.append(loss_snapshot["total"])

    if not iterations:
        final_center = {"x": round(best_center["x"], 2), "y": round(best_center["y"], 2)}
        final_loss = objective(final_center["x"], final_center["y"])
        final_snapshot = compute_loss_snapshot(final_center, candidate, sensors, scenario)
        iterations.append({
            "iteration": 1, "progress": 1.0, "center": final_center,
            "radius": round(candidate_radius * 0.35, 2),
            "polygon": build_refinement_polygon(final_center, candidate_radius * 0.35, 0, 1),
            "loss": final_loss, "confidence": 0.22, "lossBreakdown": final_snapshot,
        })
        loss_history.append(final_loss)

    estimated = iterations[-1]
    source_match_error = None
    if true_source_map_point:
        source_match_error = round(distance(estimated["center"], normalize_point(true_source_map_point)), 2)

    estimated_source = {
        "mapPoint": estimated["center"],
        "radius": estimated["radius"],
        "iconSize": max(12.0, estimated["radius"] * 0.9),
    }
    error_metrics = {
        "finalLoss": estimated["loss"],
        "sourceMatchError": source_match_error,
        "matched": source_match_error is not None and source_match_error <= 15,
        "activeSensorCount": len(sensors),
        "candidateCount": 1,
        "warningThreshold": float(gas.get("warningThreshold") or 0),
        "dangerThreshold": float(gas.get("dangerThreshold") or 0),
        "optimizerConverged": nm_result["converged"],
        "optimizerIterations": nm_result["iterations"],
    }
    summary = {
        "bestCandidateId": candidate.get("candidateId"),
        "finalLoss": estimated["loss"],
        "sourceMatchError": source_match_error,
        "estimatedCoord": f"{estimated['center']['x']:.0f}, {estimated['center']['y']:.0f}",
        "totalIterations": nm_result["iterations"],
    }
    return {
        "iterations": iterations,
        "shrinkFrames": shrink_frames,
        "lossHistory": loss_history,
        "estimatedSource": estimated_source,
        "confidenceRadius": estimated["radius"],
        "errorMetrics": error_metrics,
        "summary": summary,
    }


def create_empty_result(dataset: Dict) -> Dict:
    """Create an empty inversion result when no candidates are available.

    Args:
        dataset: The original dataset dict for timeline info.

    Returns:
        Empty result dict with zeroed fields.
    """
    return {
        "datasetVersion": "pyodide-pinn-inversion-v1",
        "stage": "python_pinn_two_stage",
        "timeline": {
            "currentFrameIndex": dataset.get("currentFrameIndex", 0),
            "currentTimeSec": dataset.get("frameTimeSec", 0),
        },
        "coarseCandidates": [],
        "estimatedSource": None,
        "confidenceRadius": 0,
        "lossHistory": [],
        "shrinkFrames": [],
        "iterations": [],
        "errorMetrics": {
            "finalLoss": 0,
            "sourceMatchError": None,
            "matched": False,
            "activeSensorCount": 0,
            "candidateCount": 0,
        },
        "summary": {
            "bestCandidateId": "",
            "finalLoss": 0,
            "sourceMatchError": None,
            "estimatedCoord": "--",
            "totalIterations": 0,
        },
    }


def build_refinement_polygon(center: Dict, radius: float, iteration: int, candidate_rank: int) -> List[Dict]:
    """Build a polygon visualization for a refinement iteration.

    Creates a wobbled heptagon centered at the given point with
    radius-based size and iteration-dependent distortion.

    Args:
        center: Center point dict with 'x' and 'y'.
        radius: Base radius of the polygon.
        iteration: Current iteration index for wobble variation.
        candidate_rank: Candidate rank for base rotation offset.

    Returns:
        List of polygon vertex dicts with 'x' and 'y'.
    """
    points = []
    vertex_count = 7
    base_rotation = (candidate_rank * 0.37 + iteration * 0.08) % (math.pi * 2)
    for index in range(vertex_count):
        angle = base_rotation + (math.pi * 2 * index) / vertex_count
        wobble = 0.88 + 0.16 * math.sin(iteration * 0.6 + index * 1.4 + candidate_rank)
        points.append(
            {
                "x": round(center["x"] + math.cos(angle) * radius * wobble, 2),
                "y": round(center["y"] + math.sin(angle) * radius * wobble, 2),
            }
        )
    return points


def normalize_point(point: Dict) -> Dict:
    """Normalize a point dict to standard (x, y) float format.

    Args:
        point: Raw point dict with 'x' and 'y'.

    Returns:
        Normalized point dict rounded to 2 decimals.
    """
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
