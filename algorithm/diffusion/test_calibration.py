"""Regression checks for diffusion K calibration helpers.

Run from ``algorithm/``:

    python -m diffusion.test_calibration
"""

from __future__ import annotations

import sys

import numpy as np

from diffusion.calibration import (
    SteadyPlumeCalibrationScenario,
    calibrate_diffusion_correction_k,
    calibrate_steady_plume_k,
    predict_steady_concentration,
)


def main() -> int:
    scenario = SteadyPlumeCalibrationScenario(
        emission_rate_g_s=80.0,
        wind_speed_10m=3.5,
        release_height_m=1.0,
        stability_class="D",
        urban=False,
        receptor_height_m=1.5,
        molar_mass_g_mol=17.03,
    )
    downwind = np.array([50.0, 100.0, 200.0, 400.0, 800.0])
    true_k = 1.25
    observed = predict_steady_concentration(
        scenario,
        downwind,
        diffusion_correction_k=true_k,
        concentration_unit="mg_m3",
    )
    k_grid = np.linspace(0.75, 1.75, 41)
    result = calibrate_steady_plume_k(
        scenario,
        downwind,
        observed,
        k_grid=k_grid,
        concentration_unit="mg_m3",
    )

    direct_result = calibrate_diffusion_correction_k(
        observed,
        lambda k: predict_steady_concentration(
            scenario,
            downwind,
            diffusion_correction_k=k,
            concentration_unit="mg_m3",
        ),
        k_grid=k_grid,
    )

    failures: list[str] = []
    if abs(result.best_k - true_k) > 1e-12:
        failures.append(f"expected best_k={true_k}, got {result.best_k}")
    if result.metrics["NMSE"] > 1e-20:
        failures.append(f"expected near-zero NMSE, got {result.metrics['NMSE']}")
    if result.metrics["FAC2"] != 1.0:
        failures.append(f"expected FAC2=1.0, got {result.metrics['FAC2']}")
    if direct_result.to_dict()["best_k"] != result.best_k:
        failures.append("direct calibration and steady-plume calibration disagree")

    print("Diffusion K calibration regression check")
    print(f"true_k={true_k}, best_k={result.best_k}, tested={result.tested_count}")
    print(f"metrics={result.metrics}")
    print("Result:", "FAILED" if failures else "PASSED")
    for failure in failures:
        print(f" - {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
