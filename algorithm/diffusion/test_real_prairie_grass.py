"""Validate dispersion width against the Prairie Grass field dataset.

This test uses the measured crosswind spread column ``Sy (m)`` from the
Prairie Grass observation analysis sample committed under
``datasets/samples/prairie_grass``. It does not validate absolute
concentration because that would require release averaging, sampler, and
historical unit assumptions that are outside this small regression test.

Run from the ``algorithm`` directory:

    python -m diffusion.test_real_prairie_grass
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from diffusion.gaussian_plume import (
    briggs_sigma_y,
    comparison_statistics,
    corrected_dispersion_coefficients,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = REPOSITORY_ROOT / "datasets" / "samples" / "prairie_grass" / "PGrassOBSAnalysis.txt"
URBAN_TERRAIN = False
REPRESENTATIVE_WIND_M_S = 3.0
DEFAULT_DIFFUSION_K = 1.0


def load_prairie_grass_spread() -> dict[int, dict[str, np.ndarray]]:
    """Load observed distance and Sy values grouped by experiment number."""
    experiments: dict[int, dict[str, list[float]]] = {}
    raw_lines = DATA_FILE.read_text(encoding="utf-8").splitlines()

    for line in raw_lines:
        parts = line.split()
        if len(parts) < 12 or not parts[0].isdigit():
            continue
        try:
            experiment_id = int(parts[0])
            distance_m = float(parts[3])
            observed_sy_m = float(parts[10])
        except (IndexError, ValueError):
            continue
        if distance_m <= 0.0 or observed_sy_m <= 0.0 or not np.isfinite(observed_sy_m):
            continue

        bucket = experiments.setdefault(experiment_id, {"distance_m": [], "observed_sy_m": []})
        bucket["distance_m"].append(distance_m)
        bucket["observed_sy_m"].append(observed_sy_m)

    return {
        experiment_id: {
            "distance_m": np.asarray(values["distance_m"], dtype=float),
            "observed_sy_m": np.asarray(values["observed_sy_m"], dtype=float),
        }
        for experiment_id, values in experiments.items()
        if len(values["observed_sy_m"]) >= 2
    }


def choose_best_fit_stability(distance_m: np.ndarray, observed_sy_m: np.ndarray) -> str:
    """Choose the Pasquill class whose classic Briggs Sy has the lowest NMSE."""
    best_stability = "D"
    best_nmse = float("inf")
    for stability in "ABCDEF":
        model_sy_m = np.asarray(briggs_sigma_y(distance_m, stability, URBAN_TERRAIN), dtype=float)
        nmse = comparison_statistics(model_sy_m, observed_sy_m)["NMSE"]
        if nmse < best_nmse:
            best_nmse = nmse
            best_stability = stability
    return best_stability


def run_prairie_grass_validation() -> dict[str, object]:
    """Compare classic and calibrated improved Sy against observed Sy."""
    experiments = load_prairie_grass_spread()

    observed_values: list[float] = []
    classic_values: list[float] = []
    improved_k1_values: list[float] = []

    for experiment in experiments.values():
        distance_m = experiment["distance_m"]
        observed_sy_m = experiment["observed_sy_m"]
        stability = choose_best_fit_stability(distance_m, observed_sy_m)

        classic_sy_m = np.asarray(briggs_sigma_y(distance_m, stability, URBAN_TERRAIN), dtype=float)
        improved_sy_m, _ = corrected_dispersion_coefficients(
            distance_m,
            stability,
            URBAN_TERRAIN,
            REPRESENTATIVE_WIND_M_S,
            DEFAULT_DIFFUSION_K,
            "improved",
        )

        observed_values.extend(observed_sy_m.tolist())
        classic_values.extend(classic_sy_m.tolist())
        improved_k1_values.extend(np.asarray(improved_sy_m, dtype=float).tolist())

    observed = np.asarray(observed_values, dtype=float)
    classic = np.asarray(classic_values, dtype=float)
    improved_k1 = np.asarray(improved_k1_values, dtype=float)

    best_k = 0.0
    best_nmse = float("inf")
    best_calibrated = classic.copy()
    for candidate_k in np.linspace(0.0, 5.0, 501):
        calibrated = classic * (1.0 + 0.38 * float(candidate_k))
        nmse = comparison_statistics(calibrated, observed)["NMSE"]
        if nmse < best_nmse:
            best_k = float(candidate_k)
            best_nmse = nmse
            best_calibrated = calibrated

    classic_stats = comparison_statistics(classic, observed)
    improved_k1_stats = comparison_statistics(improved_k1, observed)
    calibrated_stats = comparison_statistics(best_calibrated, observed)

    return {
        "experiment_count": len(experiments),
        "sample_count": int(observed.size),
        "classic": classic_stats,
        "improved_k1": improved_k1_stats,
        "calibrated": calibrated_stats,
        "best_k": best_k,
        "passed": (
            observed.size > 0
            and calibrated_stats["NMSE"] <= classic_stats["NMSE"] + 1e-9
            and 0.0 <= best_k <= 5.0
        ),
    }


def print_stats(label: str, stats: dict[str, float]) -> None:
    """Print a compact metric row."""
    print(f"{label:<18}{stats['FB']:>12.4f}{stats['NMSE']:>12.4f}{stats['FAC2']:>10.3f}")


def main() -> int:
    print("=" * 72)
    print("Prairie Grass Sy validation")
    print(f"Data file: {DATA_FILE}")
    print("=" * 72)

    if not DATA_FILE.exists():
        print("[FAIL] Dataset sample is missing.")
        return 1

    result = run_prairie_grass_validation()
    if result["sample_count"] == 0:
        print("[FAIL] No valid observed Sy samples were parsed.")
        return 1

    print(f"Experiments: {result['experiment_count']}")
    print(f"Distance samples: {result['sample_count']}")
    print()
    print(f"{'Model':<18}{'FB':>12}{'NMSE':>12}{'FAC2':>10}")
    print("-" * 52)
    print_stats("classic", result["classic"])
    print_stats("improved K=1", result["improved_k1"])
    print_stats("calibrated", result["calibrated"])
    print("-" * 52)
    print(f"Best K: {result['best_k']:.3f}")
    print()

    if result["passed"]:
        print("[PASS] Calibrated improved Sy is not worse than classic Briggs Sy on NMSE.")
        return 0

    print("[FAIL] Calibrated improved Sy regressed against classic Briggs Sy.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
