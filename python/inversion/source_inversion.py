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

from .pinn_losses import compute_loss_snapshot
from .pinn_model import blend_points, estimate_weighted_center


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
    best_candidate = ranked_candidates[0]
    refinement = refine_candidate(
        candidate=best_candidate,
        sensors=active_sensors,
        scenario=dataset.get("scenario") or {},
        weighted_center=weighted_center,
        training_config=dataset.get("trainingConfig") or {},
        gas=dataset.get("gas") or {},
        true_source_map_point=dataset.get("trueSourceMapPoint"),
    )

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
    """Iteratively refine a candidate source location.

    Progressively shrinks the search radius from the candidate region
    toward the weighted sensor center, computing loss at each iteration.

    Args:
        candidate: Selected candidate region to refine.
        sensors: Active sensor list.
        scenario: Scenario dict with wind data.
        weighted_center: Sensor-weighted center target.
        training_config: Config dict with animationSteps and
            convergenceRatio.
        gas: Gas properties dict.
        true_source_map_point: Optional true source location for
            error computation.

    Returns:
        Refinement result with iterations, estimated source, loss
        history, and error metrics.
    """
    total_iterations = max(int(training_config.get("animationSteps") or 18), 8)
    convergence_ratio = float(training_config.get("convergenceRatio") or 0.22)
    start_radius = float(candidate.get("radius") or 45) * 1.25
    end_radius = max(8.0, float(candidate.get("radius") or 45) * convergence_ratio)
    target_center = blend_points(candidate["center"], weighted_center, 0.72)

    iterations = []
    shrink_frames = []
    loss_history = []
    for index in range(total_iterations):
        progress = 1.0 if total_iterations == 1 else index / (total_iterations - 1)
        eased = 1 - math.pow(1 - progress, 2)
        center = blend_points(candidate["center"], target_center, eased)
        radius = round(start_radius + (end_radius - start_radius) * eased, 2)
        polygon = build_refinement_polygon(center, radius, index, int(candidate.get("rank") or 1))
        loss_snapshot = compute_loss_snapshot(center, candidate, sensors, scenario)
        confidence = round(1 - eased * 0.78, 4)

        iteration = {
            "iteration": index + 1,
            "progress": round(progress, 4),
            "center": center,
            "radius": radius,
            "polygon": polygon,
            "loss": loss_snapshot["total"],
            "confidence": confidence,
            "lossBreakdown": loss_snapshot,
        }
        iterations.append(iteration)
        shrink_frames.append(polygon)
        loss_history.append(loss_snapshot["total"])

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
    }
    summary = {
        "bestCandidateId": candidate.get("candidateId"),
        "finalLoss": estimated["loss"],
        "sourceMatchError": source_match_error,
        "estimatedCoord": f"{estimated['center']['x']:.0f}, {estimated['center']['y']:.0f}",
        "totalIterations": total_iterations,
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
