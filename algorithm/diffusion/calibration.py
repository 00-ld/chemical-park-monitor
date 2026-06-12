"""Calibration helpers for the Gaussian plume diffusion correction coefficient.

This module intentionally reuses :mod:`diffusion.gaussian_plume` instead of
duplicating the plume equations. It is designed for small, auditable validation
jobs where a measured or reference concentration series is available and the
best ``diffusionCorrectionK`` should be selected objectively by metrics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Iterable

import numpy as np

from diffusion.gaussian_plume import (
    STANDARD_PRESSURE_PA,
    comparison_statistics,
    mass_to_ppm,
    steady_plume_mass_conc,
    wind_at_height,
)


VALID_CALIBRATION_UNITS = ("g_m3", "mg_m3", "ppm")


@dataclass(frozen=True)
class SteadyPlumeCalibrationScenario:
    """Physical inputs shared by one steady-plume calibration case."""

    emission_rate_g_s: float
    wind_speed_10m: float
    release_height_m: float
    stability_class: str
    urban: bool = False
    receptor_height_m: float = 1.5
    wind_reference_height_m: float = 10.0
    molar_mass_g_mol: float | None = None
    temperature_k: float = 298.15
    pressure_pa: float = STANDARD_PRESSURE_PA
    reflection_alpha: float | None = None

    @property
    def effective_wind_m_s(self) -> float:
        """Wind speed transported to the release height."""

        return wind_at_height(
            self.wind_speed_10m,
            self.release_height_m,
            self.stability_class,
            self.wind_reference_height_m,
        )


@dataclass(frozen=True)
class DiffusionCalibrationResult:
    """Best-K result and objective metrics for one calibration run."""

    best_k: float
    metrics: dict[str, float]
    tested_count: int
    model_variant: str
    concentration_unit: str

    def to_dict(self) -> dict:
        """Return a JSON-serializable result for API or report usage."""

        payload = asdict(self)
        payload["metrics"] = dict(self.metrics)
        return payload


def default_k_grid(min_k: float = 0.05, max_k: float = 3.0, count: int = 60) -> np.ndarray:
    """Return a deterministic K grid suitable for objective comparison."""

    if count < 2:
        raise ValueError("count must be at least 2")
    if min_k <= 0:
        raise ValueError("min_k must be positive for the current improved-model semantics")
    if max_k < min_k:
        raise ValueError("max_k must be greater than or equal to min_k")
    return np.linspace(float(min_k), float(max_k), int(count))


def predict_steady_concentration(
    scenario: SteadyPlumeCalibrationScenario,
    downwind_m: np.ndarray | Iterable[float] | float,
    crosswind_m: np.ndarray | Iterable[float] | float = 0.0,
    diffusion_correction_k: float = 1.0,
    model_variant: str = "improved",
    concentration_unit: str = "mg_m3",
) -> np.ndarray:
    """Predict steady plume concentration for a calibration receptor set.

    The current project uses ``diffusionCorrectionK=1`` as the improved-model
    baseline. Therefore calibration should search positive K values and compare
    metrics instead of assuming K=0 is equivalent to the classic model.
    """

    unit = normalize_concentration_unit(concentration_unit)
    mass_g_m3 = steady_plume_mass_conc(
        scenario.emission_rate_g_s,
        scenario.effective_wind_m_s,
        downwind_m,
        crosswind_m,
        scenario.receptor_height_m,
        scenario.release_height_m,
        scenario.stability_class,
        scenario.urban,
        model_variant=model_variant,
        diffusion_correction_k=diffusion_correction_k,
        reflection_alpha=scenario.reflection_alpha,
    )
    mass_g_m3 = np.asarray(mass_g_m3, dtype=float)
    if unit == "g_m3":
        return mass_g_m3
    if unit == "mg_m3":
        return mass_g_m3 * 1000.0
    if scenario.molar_mass_g_mol is None:
        raise ValueError("molar_mass_g_mol is required when concentration_unit='ppm'")
    return np.asarray(
        mass_to_ppm(
            mass_g_m3,
            scenario.molar_mass_g_mol,
            scenario.temperature_k,
            scenario.pressure_pa,
        ),
        dtype=float,
    )


def calibrate_diffusion_correction_k(
    observed_concentration: np.ndarray | Iterable[float],
    predict_fn: Callable[[float], np.ndarray],
    k_grid: Iterable[float] | None = None,
    model_variant: str = "improved",
    concentration_unit: str = "mg_m3",
) -> DiffusionCalibrationResult:
    """Select the K value with the smallest NMSE against observations."""

    unit = normalize_concentration_unit(concentration_unit)
    observed = np.asarray(observed_concentration, dtype=float)
    if observed.size == 0:
        raise ValueError("observed_concentration must not be empty")
    if not np.all(np.isfinite(observed)):
        raise ValueError("observed_concentration contains NaN or infinite values")

    candidates = default_k_grid() if k_grid is None else np.asarray(list(k_grid), dtype=float)
    if candidates.size == 0:
        raise ValueError("k_grid must not be empty")

    best_k = float(candidates[0])
    best_metrics: dict[str, float] | None = None
    for candidate in candidates:
        k = float(candidate)
        predicted = np.asarray(predict_fn(k), dtype=float)
        if predicted.shape != observed.shape:
            raise ValueError("predict_fn(k) must return the same shape as observed_concentration")
        if not np.all(np.isfinite(predicted)):
            raise ValueError(f"predict_fn({k}) returned NaN or infinite values")
        metrics = comparison_statistics(predicted, observed)
        if best_metrics is None or metrics["NMSE"] < best_metrics["NMSE"]:
            best_k = k
            best_metrics = metrics

    assert best_metrics is not None
    return DiffusionCalibrationResult(
        best_k=best_k,
        metrics=best_metrics,
        tested_count=int(candidates.size),
        model_variant=model_variant,
        concentration_unit=unit,
    )


def calibrate_steady_plume_k(
    scenario: SteadyPlumeCalibrationScenario,
    downwind_m: np.ndarray | Iterable[float],
    observed_concentration: np.ndarray | Iterable[float],
    crosswind_m: np.ndarray | Iterable[float] | float = 0.0,
    k_grid: Iterable[float] | None = None,
    model_variant: str = "improved",
    concentration_unit: str = "mg_m3",
) -> DiffusionCalibrationResult:
    """Calibrate ``diffusionCorrectionK`` for one steady-plume scenario."""

    downwind = np.asarray(downwind_m, dtype=float)

    def predict(k: float) -> np.ndarray:
        return predict_steady_concentration(
            scenario,
            downwind,
            crosswind_m,
            diffusion_correction_k=k,
            model_variant=model_variant,
            concentration_unit=concentration_unit,
        )

    return calibrate_diffusion_correction_k(
        observed_concentration,
        predict,
        k_grid=k_grid,
        model_variant=model_variant,
        concentration_unit=concentration_unit,
    )


def normalize_concentration_unit(unit: str) -> str:
    """Normalize and validate concentration unit labels."""

    normalized = str(unit or "mg_m3").strip().lower().replace("/", "_")
    aliases = {
        "g/m3": "g_m3",
        "g_m^3": "g_m3",
        "mg/m3": "mg_m3",
        "mg_m^3": "mg_m3",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in VALID_CALIBRATION_UNITS:
        raise ValueError(f"unsupported concentration unit: {unit!r}")
    return normalized
