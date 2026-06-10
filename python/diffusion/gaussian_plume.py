"""Engineering-grade Gaussian plume / puff dispersion physics.

Implements the canonical atmospheric dispersion model used for hazardous gas
release assessment in chemical plants, with physically grounded components:

    - Briggs (1973) dispersion coefficients sigma_y / sigma_z as functions of
      downwind distance (metres) and Pasquill stability class A-F, for both
      open-country (rural) and built-up (urban) environments.
    - Steady-state Gaussian plume with full ground reflection and elevated
      source height.
    - Gaussian puff superposition for finite-duration transient releases, which
      converges to the analytic continuous plume in the small-time-step limit
      and naturally reproduces both build-up and post-release dissipation.
    - Power-law wind profile to translate a 10 m reference wind speed to the
      release height.
    - Mass concentration (kg/m3) to volume mixing ratio (ppm) conversion via the
      ideal gas law, so warning / danger thresholds expressed in ppm carry real
      physical meaning.

References:
    - G. A. Briggs, "Diffusion estimation for small emissions" (1973).
    - D. B. Turner, "Workbook of Atmospheric Dispersion Estimates" (1970).
    - Atmospheric dispersion modeling, Wikipedia.

All distances inside this module are in metres, time in seconds, mass in grams,
and the emission rate in grams per second unless stated otherwise.

Typical usage:
    field = transient_ppm_field(along_m, cross_m, params)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


# Universal gas constant (J / mol / K) and standard atmospheric pressure (Pa).
R_GAS = 8.314462618
STANDARD_PRESSURE_PA = 101325.0

# Lower bound on the effective transport wind speed (m/s). Avoids singular
# concentrations under calm conditions; consistent with regulatory practice of
# capping Gaussian models at low wind speeds.
MIN_WIND_SPEED = 0.3

# Lower bound on downwind travel distance (m) used when evaluating dispersion
# coefficients, so sigma never collapses to zero at the source.
MIN_TRAVEL_DISTANCE = 1.0

# Power-law wind-profile exponents by stability class (open country values,
# Irwin 1979). Used to extrapolate the 10 m wind to the release height.
WIND_PROFILE_EXPONENT = {
    "A": 0.07,
    "B": 0.07,
    "C": 0.10,
    "D": 0.15,
    "E": 0.35,
    "F": 0.55,
}

VALID_STABILITY_CLASSES = ("A", "B", "C", "D", "E", "F")


def normalize_stability(stability_class: str) -> str:
    """Normalise an arbitrary stability label to a valid Pasquill class.

    Args:
        stability_class: Raw stability label (case-insensitive).

    Returns:
        One of 'A'..'F'; defaults to 'D' (neutral) when unrecognised.
    """
    label = str(stability_class or "D").strip().upper()
    return label if label in VALID_STABILITY_CLASSES else "D"


def briggs_sigma_y(distance_m: np.ndarray | float, stability_class: str, urban: bool) -> np.ndarray | float:
    """Compute the crosswind dispersion coefficient sigma_y (Briggs, 1973).

    Args:
        distance_m: Downwind distance(s) from the source, in metres.
        stability_class: Pasquill stability class 'A'..'F'.
        urban: True for built-up (urban) terrain, False for open country.

    Returns:
        sigma_y in metres, matching the shape/type of ``distance_m``.
    """
    x = np.maximum(distance_m, MIN_TRAVEL_DISTANCE)
    stab = normalize_stability(stability_class)
    if urban:
        # Briggs urban coefficients (A-B / C / D / E-F groupings).
        a = {"A": 0.32, "B": 0.32, "C": 0.22, "D": 0.16, "E": 0.11, "F": 0.11}[stab]
        return a * x / np.sqrt(1.0 + 0.0004 * x)
    # Briggs open-country coefficients.
    a = {"A": 0.22, "B": 0.16, "C": 0.11, "D": 0.08, "E": 0.06, "F": 0.04}[stab]
    return a * x / np.sqrt(1.0 + 0.0001 * x)


def briggs_sigma_z(distance_m: np.ndarray | float, stability_class: str, urban: bool) -> np.ndarray | float:
    """Compute the vertical dispersion coefficient sigma_z (Briggs, 1973).

    Args:
        distance_m: Downwind distance(s) from the source, in metres.
        stability_class: Pasquill stability class 'A'..'F'.
        urban: True for built-up (urban) terrain, False for open country.

    Returns:
        sigma_z in metres, matching the shape/type of ``distance_m``.
    """
    x = np.maximum(distance_m, MIN_TRAVEL_DISTANCE)
    stab = normalize_stability(stability_class)
    if urban:
        if stab in ("A", "B"):
            return 0.24 * x * np.sqrt(1.0 + 0.001 * x)
        if stab == "C":
            return 0.20 * x
        if stab == "D":
            return 0.14 * x / np.sqrt(1.0 + 0.0003 * x)
        return 0.08 * x / np.sqrt(1.0 + 0.0015 * x)
    # Open country.
    if stab == "A":
        return 0.20 * x
    if stab == "B":
        return 0.12 * x
    if stab == "C":
        return 0.08 * x / np.sqrt(1.0 + 0.0002 * x)
    if stab == "D":
        return 0.06 * x / np.sqrt(1.0 + 0.0015 * x)
    if stab == "E":
        return 0.03 * x / np.sqrt(1.0 + 0.0003 * x)
    return 0.016 * x / np.sqrt(1.0 + 0.0003 * x)


def wind_at_height(wind_speed_10m: float, release_height_m: float, stability_class: str) -> float:
    """Translate a 10 m reference wind speed to the release height.

    Uses a power-law profile with stability-dependent exponent and applies a
    lower bound so the transport speed never falls below ``MIN_WIND_SPEED``.

    Args:
        wind_speed_10m: Wind speed measured at the 10 m reference height (m/s).
        release_height_m: Effective release height above ground (m).
        stability_class: Pasquill stability class 'A'..'F'.

    Returns:
        Effective transport wind speed at the release height (m/s).
    """
    stab = normalize_stability(stability_class)
    exponent = WIND_PROFILE_EXPONENT[stab]
    reference = max(float(wind_speed_10m), 0.0)
    height = max(float(release_height_m), 1.0)
    speed = reference * (height / 10.0) ** exponent
    return max(speed, MIN_WIND_SPEED)


def mass_to_ppm(
    mass_conc_g_m3: np.ndarray | float,
    molar_mass_g_mol: float,
    temperature_k: float,
    pressure_pa: float = STANDARD_PRESSURE_PA,
) -> np.ndarray | float:
    """Convert a mass concentration (g/m3) to a volume mixing ratio (ppm).

    Uses the ideal gas law: ppm_v = C * R * T / (M * P) * 1e6, where C is the
    mass concentration, M the molar mass, T the absolute temperature and P the
    ambient pressure.

    Args:
        mass_conc_g_m3: Mass concentration in grams per cubic metre.
        molar_mass_g_mol: Molar mass of the gas in grams per mole.
        temperature_k: Ambient absolute temperature in kelvin.
        pressure_pa: Ambient pressure in pascal (defaults to 1 atm).

    Returns:
        Volume mixing ratio in parts per million (ppm), same shape as input.
    """
    molar = max(float(molar_mass_g_mol), 1e-6)
    temperature = max(float(temperature_k), 1.0)
    pressure = max(float(pressure_pa), 1.0)
    return mass_conc_g_m3 * R_GAS * temperature / (molar * pressure) * 1.0e6


def steady_plume_mass_conc(
    emission_rate_g_s: float,
    wind_speed: float,
    downwind_m: np.ndarray | float,
    crosswind_m: np.ndarray | float,
    height_m: np.ndarray | float,
    release_height_m: float,
    stability_class: str,
    urban: bool,
) -> np.ndarray | float:
    """Steady-state Gaussian plume mass concentration with ground reflection.

    Implements the canonical equation:

        C = Q / (2*pi*u*sigma_y*sigma_z)
            * exp(-y^2 / (2*sigma_y^2))
            * [ exp(-(z-H)^2 / (2*sigma_z^2)) + exp(-(z+H)^2 / (2*sigma_z^2)) ]

    Concentrations upwind of the source (downwind_m <= 0) are zero.

    Args:
        emission_rate_g_s: Continuous emission rate Q in grams per second.
        wind_speed: Effective transport wind speed u at release height (m/s).
        downwind_m: Downwind coordinate x relative to the source (m).
        crosswind_m: Crosswind coordinate y relative to the plume axis (m).
        height_m: Receptor height z above ground (m).
        release_height_m: Effective source height H (m).
        stability_class: Pasquill stability class 'A'..'F'.
        urban: True for urban terrain, False for open country.

    Returns:
        Mass concentration in grams per cubic metre, same shape as inputs.
    """
    x = np.asarray(downwind_m, dtype=float)
    y = np.asarray(crosswind_m, dtype=float)
    z = np.asarray(height_m, dtype=float)
    u = max(float(wind_speed), MIN_WIND_SPEED)
    h = float(release_height_m)

    sigma_y = np.asarray(briggs_sigma_y(x, stability_class, urban), dtype=float)
    sigma_z = np.asarray(briggs_sigma_z(x, stability_class, urban), dtype=float)
    sigma_y = np.maximum(sigma_y, 1e-3)
    sigma_z = np.maximum(sigma_z, 1e-3)

    norm = emission_rate_g_s / (2.0 * math.pi * u * sigma_y * sigma_z)
    crosswind_term = np.exp(-(y * y) / (2.0 * sigma_y * sigma_y))
    vertical_term = np.exp(-((z - h) ** 2) / (2.0 * sigma_z * sigma_z)) + np.exp(
        -((z + h) ** 2) / (2.0 * sigma_z * sigma_z)
    )
    conc = norm * crosswind_term * vertical_term
    # Upwind of the source there is no plume.
    return np.where(x > 0.0, conc, 0.0)


@dataclass
class PlumeParams:
    """Physical parameters for a dispersion computation.

    Attributes:
        emission_rate_g_s: Emission rate Q in grams per second.
        wind_speed_10m: Reference wind speed at 10 m (m/s).
        release_height_m: Effective source height H (m).
        release_duration_s: Total release duration (s).
        stability_class: Pasquill stability class 'A'..'F'.
        urban: True for urban terrain, False for open country.
        molar_mass_g_mol: Molar mass of the released gas (g/mol).
        temperature_k: Ambient absolute temperature (K).
        pressure_pa: Ambient pressure (Pa).
    """

    emission_rate_g_s: float
    wind_speed_10m: float
    release_height_m: float
    release_duration_s: float
    stability_class: str
    urban: bool
    molar_mass_g_mol: float
    temperature_k: float
    pressure_pa: float = STANDARD_PRESSURE_PA

    @property
    def effective_wind(self) -> float:
        """Effective transport wind speed at the release height (m/s)."""
        return wind_at_height(self.wind_speed_10m, self.release_height_m, self.stability_class)


def build_emission_times(release_duration_s: float, emit_step_s: float) -> np.ndarray:
    """Build the discrete puff emission times for a finite release.

    Args:
        release_duration_s: Total release duration in seconds.
        emit_step_s: Spacing between successive puffs in seconds.

    Returns:
        1-D array of emission start times in seconds.
    """
    duration = max(float(release_duration_s), 0.0)
    step = max(float(emit_step_s), 1e-3)
    if duration <= 0.0:
        return np.array([0.0])
    count = max(1, int(math.ceil(duration / step)))
    return np.linspace(0.0, duration, count, endpoint=False)


def choose_emit_step(release_duration_s: float, frame_step_s: float, max_puffs: int = 80) -> float:
    """Choose a puff emission step that balances accuracy and cost.

    The step is fine enough for puffs to overlap (good convergence to the
    continuous plume) yet bounded so the puff count stays manageable.

    Args:
        release_duration_s: Total release duration in seconds.
        frame_step_s: Animation frame step in seconds.
        max_puffs: Upper bound on the number of emitted puffs.

    Returns:
        Puff emission step in seconds.
    """
    duration = max(float(release_duration_s), 1.0)
    base = min(max(0.5, float(frame_step_s)), duration / 20.0 if duration > 20.0 else duration)
    floor = duration / float(max_puffs)
    return max(base, floor, 0.5)


def transient_mass_conc_field(
    downwind_m: np.ndarray,
    crosswind_m: np.ndarray,
    time_sec: float,
    params: PlumeParams,
    emission_times: np.ndarray,
    emit_step_s: float,
    receptor_height_m: float = 0.0,
) -> np.ndarray:
    """Gaussian puff superposition mass-concentration field at a given time.

    Each puff carries mass ``Q * emit_step`` and is advected downwind at the
    effective wind speed; its spread is set by the Briggs coefficients evaluated
    at the puff travel distance. Summing overlapping puffs reproduces the
    continuous plume during release and its dissipation afterwards.

    Args:
        downwind_m: 2-D array of downwind coordinates relative to source (m).
        crosswind_m: 2-D array of crosswind coordinates relative to axis (m).
        time_sec: Observation time since release start (s).
        params: Physical plume parameters.
        emission_times: Puff emission start times (s).
        emit_step_s: Puff emission spacing (s); sets per-puff mass.
        receptor_height_m: Receptor height above ground (m).

    Returns:
        2-D mass-concentration field in grams per cubic metre.
    """
    u = params.effective_wind
    h = float(params.release_height_m)
    z = float(receptor_height_m)
    puff_mass = float(params.emission_rate_g_s) * float(emit_step_s)
    two_pi_15 = (2.0 * math.pi) ** 1.5

    total = np.zeros_like(downwind_m, dtype=float)
    active = emission_times[emission_times < time_sec]
    for emit_time in active:
        travel_time = time_sec - emit_time
        distance = max(u * travel_time, MIN_TRAVEL_DISTANCE)
        sigma_h = float(briggs_sigma_y(distance, params.stability_class, params.urban))
        sigma_v = float(briggs_sigma_z(distance, params.stability_class, params.urban))
        sigma_h = max(sigma_h, 1e-3)
        sigma_v = max(sigma_v, 1e-3)
        # Along-wind puff spread is taken equal to the horizontal spread.
        along = np.exp(-((downwind_m - distance) ** 2) / (2.0 * sigma_h * sigma_h))
        cross = np.exp(-(crosswind_m * crosswind_m) / (2.0 * sigma_h * sigma_h))
        vertical = np.exp(-((z - h) ** 2) / (2.0 * sigma_v * sigma_v)) + np.exp(
            -((z + h) ** 2) / (2.0 * sigma_v * sigma_v)
        )
        norm = puff_mass / (two_pi_15 * sigma_h * sigma_h * sigma_v)
        total += norm * along * cross * vertical
    return total


def transient_ppm_field(
    downwind_m: np.ndarray,
    crosswind_m: np.ndarray,
    time_sec: float,
    params: PlumeParams,
    emission_times: np.ndarray,
    emit_step_s: float,
    receptor_height_m: float = 0.0,
) -> np.ndarray:
    """Puff-superposition concentration field converted to ppm.

    Args:
        downwind_m: 2-D array of downwind coordinates relative to source (m).
        crosswind_m: 2-D array of crosswind coordinates relative to axis (m).
        time_sec: Observation time since release start (s).
        params: Physical plume parameters.
        emission_times: Puff emission start times (s).
        emit_step_s: Puff emission spacing (s).
        receptor_height_m: Receptor height above ground (m).

    Returns:
        2-D concentration field in ppm (volume mixing ratio).
    """
    mass_field = transient_mass_conc_field(
        downwind_m,
        crosswind_m,
        time_sec,
        params,
        emission_times,
        emit_step_s,
        receptor_height_m,
    )
    return mass_to_ppm(mass_field, params.molar_mass_g_mol, params.temperature_k, params.pressure_pa)


def integrated_crosswind_mass_flux(
    emission_rate_g_s: float,
    wind_speed: float,
    downwind_m: float,
    release_height_m: float,
    stability_class: str,
    urban: bool,
    y_samples: int = 801,
    z_samples: int = 801,
) -> float:
    """Numerically integrate the plume mass flux across a downwind plane.

    For a non-reactive, conserved tracer the flux ``\\int\\int C * u dy dz`` over a
    plane perpendicular to the wind must equal the emission rate Q. This helper
    is used by the validation suite to verify mass conservation.

    Args:
        emission_rate_g_s: Emission rate Q in grams per second.
        wind_speed: Effective transport wind speed (m/s).
        downwind_m: Downwind distance of the integration plane (m).
        release_height_m: Effective source height H (m).
        stability_class: Pasquill stability class 'A'..'F'.
        urban: True for urban terrain, False for open country.
        y_samples: Number of crosswind sample points.
        z_samples: Number of vertical sample points.

    Returns:
        Integrated mass flux in grams per second.
    """
    sigma_y = float(briggs_sigma_y(downwind_m, stability_class, urban))
    sigma_z = float(briggs_sigma_z(downwind_m, stability_class, urban))
    y = np.linspace(-6.0 * sigma_y, 6.0 * sigma_y, y_samples)
    z = np.linspace(0.0, 6.0 * sigma_z + release_height_m, z_samples)
    yy, zz = np.meshgrid(y, z, indexing="ij")
    xx = np.full_like(yy, downwind_m)
    conc = steady_plume_mass_conc(
        emission_rate_g_s,
        wind_speed,
        xx,
        yy,
        zz,
        release_height_m,
        stability_class,
        urban,
    )
    flux = np.trapezoid(np.trapezoid(conc, z, axis=1), y, axis=0)
    return float(flux * max(float(wind_speed), MIN_WIND_SPEED))


def comparison_statistics(predicted: np.ndarray, observed: np.ndarray) -> Dict[str, float]:
    """Compute standard model-evaluation statistics (FB, NMSE, FAC2).

    These are the metrics recommended for atmospheric dispersion model
    validation (Chang & Hanna, 2004).

    Args:
        predicted: Model-predicted concentrations.
        observed: Reference/observed concentrations.

    Returns:
        Dict with 'FB' (fractional bias), 'NMSE' (normalised mean square
        error) and 'FAC2' (fraction of predictions within a factor of two).
    """
    pred = np.asarray(predicted, dtype=float)
    obs = np.asarray(observed, dtype=float)
    eps = 1e-30
    mean_pred = float(np.mean(pred))
    mean_obs = float(np.mean(obs))
    fb = 2.0 * (mean_obs - mean_pred) / (mean_obs + mean_pred + eps)
    nmse = float(np.mean((obs - pred) ** 2) / (mean_obs * mean_pred + eps))
    ratio = pred / np.maximum(obs, eps)
    fac2 = float(np.mean((ratio >= 0.5) & (ratio <= 2.0)))
    return {"FB": fb, "NMSE": nmse, "FAC2": fac2}


def resolve_environment(terrain_roughness: float) -> bool:
    """Map a terrain-roughness value to a rural/urban dispersion regime.

    Chemical-park layouts with dense equipment behave closer to urban
    (built-up) dispersion. A roughness at or above 0.4 selects the urban
    Briggs coefficient set.

    Args:
        terrain_roughness: Surface roughness indicator (dimensionless).

    Returns:
        True for the urban regime, False for open country.
    """
    return float(terrain_roughness) >= 0.4
