"""Improved particle filtering for gas leak source-term estimation.

The estimator follows the paper's source state ``[X, Y, Q]`` idea while using
the repository's shared Gaussian-plume forward model as the physical operator:

* uniform prior over bounded source location and source strength;
* Bayesian likelihood with independent sensor and model error terms;
* effective sample size (ESS) based resampling;
* Gaussian-kernel jitter plus Metropolis-Hastings rejuvenation to reduce
  particle impoverishment after resampling.

The implementation is intentionally CPU-only and deterministic by default so it
can be used both by the FastAPI backend and by reproducible terminal validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence

import numpy as np

from .forward_model import MIN_EMISSION_RATE, ForwardModel


MAP_METERS_PER_UNIT = 0.5


@dataclass(frozen=True)
class ParticleFilterConfig:
    """Configuration for the improved particle filter."""

    num_particles: int = 8000
    iterations: int = 28
    resample_threshold: float = 0.55
    mcmc_steps: int = 2
    sensor_noise_relative: float = 0.10
    model_noise_relative: float = 0.05
    min_noise_ppm: float = 1e-4
    detection_threshold_ppm: float = 0.0
    kernel_scale: float = 0.35
    seed: int = 20250613
    x_bounds: tuple[float, float] = (40.0, 961.0)
    y_bounds: tuple[float, float] = (40.0, 611.0)
    q_bounds: tuple[float, float] = (MIN_EMISSION_RATE, 1.0e5)


@dataclass
class ParticleFilterResult:
    """Raw numerical result of the particle filter."""

    particles: np.ndarray
    weights: np.ndarray
    estimate: np.ndarray
    covariance: np.ndarray
    credible_intervals: Dict[str, tuple[float, float]]
    history: list[Dict[str, float]]
    effective_sample_size: float
    resample_count: int
    acceptance_rate: float
    final_rmse: float


def run_particle_filter(
    forward_model: ForwardModel,
    observed_ppm: np.ndarray,
    config: ParticleFilterConfig,
) -> ParticleFilterResult:
    """Estimate ``[x, y, Q]`` from sensor concentrations with improved PF."""

    rng = np.random.default_rng(config.seed)
    observed = np.asarray(observed_ppm, dtype=float)
    if observed.ndim != 1 or observed.size == 0:
        raise ValueError("observed_ppm must be a non-empty 1-D array")

    particles = _draw_uniform_particles(rng, config)
    weights = np.full(config.num_particles, 1.0 / config.num_particles, dtype=float)
    log_likelihood = _log_likelihood(forward_model, particles, observed, config)

    beta = 0.0
    history: list[Dict[str, float]] = []
    resample_count = 0
    accepted_total = 0
    proposed_total = 0

    for iteration in range(config.iterations):
        beta_next = (iteration + 1) / config.iterations
        weights = _normalize_log_weights(np.log(weights + 1e-300) + (beta_next - beta) * log_likelihood)
        beta = beta_next

        ess = effective_sample_size(weights)
        if ess < config.resample_threshold * config.num_particles:
            particles = _systematic_resample(rng, particles, weights)
            weights = np.full(config.num_particles, 1.0 / config.num_particles, dtype=float)
            log_likelihood = _log_likelihood(forward_model, particles, observed, config)
            resample_count += 1

            particles, log_likelihood, accepted, proposed = _mcmc_rejuvenate(
                rng,
                forward_model,
                particles,
                log_likelihood,
                observed,
                beta,
                config,
            )
            accepted_total += accepted
            proposed_total += proposed

        estimate, covariance = weighted_mean_covariance(particles, weights)
        prediction = forward_model.predict(estimate[0], estimate[1], estimate[2])
        rmse = float(np.sqrt(np.mean((prediction - observed) ** 2)))
        history.append(
            {
                "iteration": float(iteration + 1),
                "beta": float(beta),
                "x": float(estimate[0]),
                "y": float(estimate[1]),
                "emissionRate": float(estimate[2]),
                "ess": float(effective_sample_size(weights)),
                "rmse": rmse,
            }
        )

    estimate, covariance = weighted_mean_covariance(particles, weights)
    prediction = forward_model.predict(estimate[0], estimate[1], estimate[2])
    final_rmse = float(np.sqrt(np.mean((prediction - observed) ** 2)))

    return ParticleFilterResult(
        particles=particles,
        weights=weights,
        estimate=estimate,
        covariance=covariance,
        credible_intervals=_credible_intervals(particles, weights),
        history=history,
        effective_sample_size=effective_sample_size(weights),
        resample_count=resample_count,
        acceptance_rate=(accepted_total / proposed_total if proposed_total else 0.0),
        final_rmse=final_rmse,
    )


def run_particle_filter_inversion_task(payload: Dict) -> Dict:
    """Backend task wrapper compatible with ``engine.task_router``."""

    sensors = _extract_sensors(payload)
    if not sensors:
        raise ValueError("particle filter inversion requires at least one sensor observation")

    scenario = payload.get("scenario") or {}
    gas = payload.get("gas") or {}
    config = _config_from_payload(payload, sensors)
    observed = np.asarray([float(sensor["signal"]) for sensor in sensors], dtype=float)
    forward_model = ForwardModel.from_scenario(sensors, scenario, gas)

    result = run_particle_filter(forward_model, observed, config)
    estimate = result.estimate
    analytic_rate = forward_model.fit_emission_rate(estimate[0], estimate[1], observed)
    estimated_point = {"x": round(float(estimate[0]), 2), "y": round(float(estimate[1]), 2)}

    true_source = payload.get("trueSourceMapPoint") or scenario.get("sourceMapPoint")
    source_error_m = None
    if true_source:
        source_error_m = (
            np.hypot(float(estimate[0]) - float(true_source["x"]), float(estimate[1]) - float(true_source["y"]))
            * MAP_METERS_PER_UNIT
        )

    q_true = _optional_float(payload.get("trueEmissionRate") or scenario.get("emissionRate"))
    q_error_pct = None
    if q_true and q_true > 0:
        q_error_pct = abs(float(estimate[2]) - q_true) / q_true * 100.0

    credible_radius_95_m = covariance_to_radius(result.covariance[:2, :2], 2.45) * MAP_METERS_PER_UNIT

    return {
        "datasetVersion": "improved-particle-filter-v1",
        "stage": "python_improved_particle_filter",
        "estimatedSource": {
            "mapPoint": estimated_point,
            "emissionRate": round(float(estimate[2]), 4),
            "analyticEmissionRate": round(float(analytic_rate), 4),
            "credibleRadius95m": round(float(credible_radius_95_m), 3),
        },
        "posterior": {
            "credibleIntervals": {
                key: [round(float(value[0]), 4), round(float(value[1]), 4)]
                for key, value in result.credible_intervals.items()
            },
            "covariance": np.round(result.covariance, 6).tolist(),
            "splitRhat": {
                key: round(float(value), 4)
                for key, value in split_rhat(result.particles, result.weights).items()
            },
        },
        "diagnostics": {
            "particles": config.num_particles,
            "iterations": config.iterations,
            "resampleCount": result.resample_count,
            "effectiveSampleSize": round(float(result.effective_sample_size), 2),
            "acceptanceRate": round(float(result.acceptance_rate), 4),
            "finalRmsePpm": round(float(result.final_rmse), 6),
        },
        "errorMetrics": {
            "sourceLocationErrorM": round(float(source_error_m), 3) if source_error_m is not None else None,
            "emissionRateErrorPct": round(float(q_error_pct), 3) if q_error_pct is not None else None,
            "matched": bool(source_error_m is not None and source_error_m <= 15.0),
        },
        "history": [
            {
                "iteration": int(item["iteration"]),
                "beta": round(item["beta"], 4),
                "x": round(item["x"], 3),
                "y": round(item["y"], 3),
                "emissionRate": round(item["emissionRate"], 4),
                "ess": round(item["ess"], 2),
                "rmse": round(item["rmse"], 6),
            }
            for item in result.history
        ],
        "executor": {
            "mode": "backend-python",
            "runtime": "numpy",
            "implementation": "python.inversion.particle_filter",
        },
    }


def effective_sample_size(weights: np.ndarray) -> float:
    """Return the standard particle-filter effective sample size."""

    return float(1.0 / np.sum(np.square(weights)))


def weighted_mean_covariance(particles: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute weighted mean and covariance for ``[x, y, Q]`` particles."""

    weights = np.asarray(weights, dtype=float)
    weights = weights / np.sum(weights)
    mean = np.average(particles, axis=0, weights=weights)
    centered = particles - mean[None, :]
    covariance = (centered * weights[:, None]).T @ centered
    return mean, covariance


def covariance_to_radius(spatial_cov: np.ndarray, n_sigma: float = 1.0) -> float:
    """Convert a 2-D covariance matrix to a major-axis radius in pixels."""

    cov = np.asarray(spatial_cov, dtype=float)
    if cov.shape != (2, 2):
        return 0.0
    eigvals = np.linalg.eigvalsh(cov)
    max_eig = float(np.max(eigvals)) if eigvals.size else 0.0
    return n_sigma * float(np.sqrt(max(max_eig, 0.0)))


def split_rhat(particles: np.ndarray, weights: np.ndarray, chain_count: int = 4) -> Dict[str, float]:
    """Approximate split-Rhat from final posterior particles.

    This is a lightweight diagnostic for backend responses. Full validation can
    still run independent filters with different seeds.
    """

    order = np.argsort(np.asarray(weights, dtype=float))
    ordered = particles[order]
    chunks = np.array_split(ordered, chain_count)
    labels = ("x", "y", "emissionRate")
    values: Dict[str, float] = {}
    for dim, label in enumerate(labels):
        chains = [chunk[:, dim] for chunk in chunks if len(chunk) > 1]
        values[label] = _rhat_from_chains(chains)
    return values


def _rhat_from_chains(chains: Sequence[np.ndarray]) -> float:
    if len(chains) < 2:
        return float("nan")
    n = min(len(chain) for chain in chains)
    if n < 2:
        return float("nan")
    trimmed = np.asarray([chain[:n] for chain in chains], dtype=float)
    chain_means = np.mean(trimmed, axis=1)
    chain_vars = np.var(trimmed, axis=1, ddof=1)
    within = float(np.mean(chain_vars))
    if within <= 1e-30:
        return 1.0
    between = float(n * np.var(chain_means, ddof=1))
    var_hat = ((n - 1) / n) * within + between / n
    return float(np.sqrt(max(var_hat / within, 0.0)))


def _draw_uniform_particles(rng: np.random.Generator, config: ParticleFilterConfig) -> np.ndarray:
    particles = np.empty((config.num_particles, 3), dtype=float)
    particles[:, 0] = rng.uniform(config.x_bounds[0], config.x_bounds[1], config.num_particles)
    particles[:, 1] = rng.uniform(config.y_bounds[0], config.y_bounds[1], config.num_particles)
    log_q = rng.uniform(np.log(config.q_bounds[0]), np.log(config.q_bounds[1]), config.num_particles)
    particles[:, 2] = np.exp(log_q)
    return particles


def _log_likelihood(
    forward_model: ForwardModel,
    particles: np.ndarray,
    observed: np.ndarray,
    config: ParticleFilterConfig,
) -> np.ndarray:
    log_values = np.empty(particles.shape[0], dtype=float)
    threshold = float(config.detection_threshold_ppm)
    for index, particle in enumerate(particles):
        predicted = forward_model.predict(particle[0], particle[1], particle[2])
        scale = np.maximum.reduce([np.abs(observed), np.abs(predicted), np.full_like(observed, threshold)])
        sigma = np.sqrt(
            (config.sensor_noise_relative * np.maximum(np.abs(observed), threshold)) ** 2
            + (config.model_noise_relative * scale) ** 2
            + config.min_noise_ppm**2
        )
        residual = predicted - observed
        logp = -0.5 * np.sum((residual / sigma) ** 2 + np.log(2.0 * np.pi * sigma**2))
        if threshold > 0.0:
            below = observed <= threshold
            if np.any(below):
                over = np.maximum(predicted[below] - threshold, 0.0)
                logp += float(np.sum(-0.5 * (over / sigma[below]) ** 2))
        log_values[index] = logp
    return log_values


def _normalize_log_weights(log_weights: np.ndarray) -> np.ndarray:
    shifted = log_weights - np.max(log_weights)
    weights = np.exp(shifted)
    total = float(np.sum(weights))
    if total <= 0.0 or not np.isfinite(total):
        return np.full(log_weights.size, 1.0 / log_weights.size, dtype=float)
    return weights / total


def _systematic_resample(
    rng: np.random.Generator,
    particles: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    n = particles.shape[0]
    positions = (rng.random() + np.arange(n)) / n
    cumulative = np.cumsum(weights)
    indices = np.searchsorted(cumulative, positions, side="right")
    indices = np.clip(indices, 0, n - 1)
    return particles[indices].copy()


def _mcmc_rejuvenate(
    rng: np.random.Generator,
    forward_model: ForwardModel,
    particles: np.ndarray,
    log_likelihood: np.ndarray,
    observed: np.ndarray,
    beta: float,
    config: ParticleFilterConfig,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    accepted = 0
    proposed_count = 0
    kernel_std = _kernel_std(particles, config)

    current = particles.copy()
    current_log_like = log_likelihood.copy()
    for _ in range(config.mcmc_steps):
        proposed = current.copy()
        proposed[:, :2] += rng.normal(0.0, kernel_std[:2], size=(current.shape[0], 2))
        proposed[:, 2] *= np.exp(rng.normal(0.0, kernel_std[2], size=current.shape[0]))
        proposed = _clip_particles(proposed, config)

        proposed_log_like = _log_likelihood(forward_model, proposed, observed, config)
        log_accept = beta * (proposed_log_like - current_log_like)
        accept = np.log(rng.random(current.shape[0]) + 1e-300) < log_accept

        current[accept] = proposed[accept]
        current_log_like[accept] = proposed_log_like[accept]
        accepted += int(np.sum(accept))
        proposed_count += int(current.shape[0])

    return current, current_log_like, accepted, proposed_count


def _kernel_std(particles: np.ndarray, config: ParticleFilterConfig) -> np.ndarray:
    spread = np.std(particles, axis=0)
    x_floor = (config.x_bounds[1] - config.x_bounds[0]) * 0.01
    y_floor = (config.y_bounds[1] - config.y_bounds[0]) * 0.01
    q_log_floor = 0.03
    q_log_spread = float(np.std(np.log(np.maximum(particles[:, 2], MIN_EMISSION_RATE))))
    return np.array(
        [
            max(float(spread[0]) * config.kernel_scale, x_floor),
            max(float(spread[1]) * config.kernel_scale, y_floor),
            max(q_log_spread * config.kernel_scale, q_log_floor),
        ],
        dtype=float,
    )


def _clip_particles(particles: np.ndarray, config: ParticleFilterConfig) -> np.ndarray:
    clipped = particles.copy()
    clipped[:, 0] = np.clip(clipped[:, 0], config.x_bounds[0], config.x_bounds[1])
    clipped[:, 1] = np.clip(clipped[:, 1], config.y_bounds[0], config.y_bounds[1])
    clipped[:, 2] = np.clip(clipped[:, 2], config.q_bounds[0], config.q_bounds[1])
    return clipped


def _credible_intervals(particles: np.ndarray, weights: np.ndarray) -> Dict[str, tuple[float, float]]:
    return {
        "x": _weighted_quantile(particles[:, 0], weights, (0.025, 0.975)),
        "y": _weighted_quantile(particles[:, 1], weights, (0.025, 0.975)),
        "emissionRate": _weighted_quantile(particles[:, 2], weights, (0.025, 0.975)),
    }


def _weighted_quantile(
    values: np.ndarray,
    weights: np.ndarray,
    quantiles: Iterable[float],
) -> tuple[float, float]:
    sorter = np.argsort(values)
    sorted_values = values[sorter]
    sorted_weights = weights[sorter]
    cumulative = np.cumsum(sorted_weights)
    cumulative = cumulative / cumulative[-1]
    qs = np.asarray(list(quantiles), dtype=float)
    return tuple(float(v) for v in np.interp(qs, cumulative, sorted_values))


def _extract_sensors(payload: Dict) -> list[Dict]:
    raw_sensors = (
        payload.get("activeSensors")
        or payload.get("observations")
        or payload.get("sensors")
        or payload.get("pinnExportPayload", {}).get("sensors")
        or []
    )
    sensors: list[Dict] = []
    min_signal = float((payload.get("config") or {}).get("minSignalThreshold", 0.0))
    for sensor in raw_sensors:
        point = sensor.get("mapPoint") or {}
        x = sensor.get("x", point.get("x"))
        y = sensor.get("y", point.get("y"))
        signal = (
            sensor.get("signal")
            if sensor.get("signal") is not None
            else sensor.get("currentConcentration", sensor.get("conc_observed", sensor.get("concentration")))
        )
        if x is None or y is None or signal is None:
            continue
        value = float(signal)
        if value < min_signal:
            continue
        sensors.append(
            {
                "id": sensor.get("id") or sensor.get("sensor_id") or f"S{len(sensors) + 1}",
                "priority": int(sensor.get("priority") or 0),
                "mapPoint": {"x": float(x), "y": float(y)},
                "signal": value,
                "currentConcentration": value,
            }
        )
    return sensors


def _config_from_payload(payload: Dict, sensors: Sequence[Dict]) -> ParticleFilterConfig:
    raw = payload.get("particleFilterConfig") or payload.get("config") or {}
    bounds = raw.get("bounds") or payload.get("bounds") or {}
    xs = [float(sensor["mapPoint"]["x"]) for sensor in sensors]
    ys = [float(sensor["mapPoint"]["y"]) for sensor in sensors]
    x_bounds = _bounds_from_raw(bounds.get("x") or bounds.get("xBounds"), (min(xs) - 260.0, max(xs) + 80.0))
    y_bounds = _bounds_from_raw(bounds.get("y") or bounds.get("yBounds"), (min(ys) - 220.0, max(ys) + 220.0))
    q_bounds = _bounds_from_raw(bounds.get("q") or bounds.get("qBounds"), (MIN_EMISSION_RATE, 1.0e5))

    return ParticleFilterConfig(
        num_particles=min(max(int(raw.get("numParticles", 8000)), 500), 50000),
        iterations=min(max(int(raw.get("iterations", 28)), 4), 120),
        resample_threshold=min(max(float(raw.get("resampleThreshold", 0.55)), 0.05), 0.95),
        mcmc_steps=min(max(int(raw.get("mcmcSteps", 2)), 0), 12),
        sensor_noise_relative=max(float(raw.get("sensorNoiseRelative", 0.10)), 1e-6),
        model_noise_relative=max(float(raw.get("modelNoiseRelative", 0.05)), 0.0),
        min_noise_ppm=max(float(raw.get("minNoisePpm", 1e-4)), 1e-12),
        detection_threshold_ppm=max(float(raw.get("detectionThresholdPpm", 0.0)), 0.0),
        kernel_scale=min(max(float(raw.get("kernelScale", 0.35)), 0.02), 2.0),
        seed=int(raw.get("seed", 20250613)),
        x_bounds=x_bounds,
        y_bounds=y_bounds,
        q_bounds=q_bounds,
    )


def _bounds_from_raw(raw_bounds: object, default: tuple[float, float]) -> tuple[float, float]:
    if isinstance(raw_bounds, dict):
        lo = raw_bounds.get("min", raw_bounds.get("lo", default[0]))
        hi = raw_bounds.get("max", raw_bounds.get("hi", default[1]))
    elif isinstance(raw_bounds, (list, tuple)) and len(raw_bounds) >= 2:
        lo, hi = raw_bounds[0], raw_bounds[1]
    else:
        lo, hi = default
    lo = float(lo)
    hi = float(hi)
    if hi <= lo:
        raise ValueError(f"invalid bounds: {raw_bounds}")
    return lo, hi


def _optional_float(value: object) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None
