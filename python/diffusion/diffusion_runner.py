"""Diffusion simulation runner module.

Orchestrates the phase1 diffusion simulation and applies CFD calibration
to produce final calibrated results. Designed for Pyodide worker execution.

Typical usage:
    result = run_diffusion_simulation_task(payload)
"""

from __future__ import annotations

from typing import Dict

from .cfd_calibrator import apply_cfd_calibration
from .phase1_diffusion import create_phase1_diffusion_simulation


def run_diffusion_simulation_task(payload: Dict) -> Dict:
    """Run a full diffusion simulation with CFD calibration.

    Creates the base phase1 simulation, applies CFD calibration factors,
    and appends executor metadata for Pyodide worker tracking.

    Args:
        payload: Request payload containing facilities, gas, wind parameters,
            stability class, and diffusion configuration.

    Returns:
        Calibrated simulation result with frames, stats, and executor info.
    """
    base_result = create_phase1_diffusion_simulation(payload)
    calibrated_result = apply_cfd_calibration(base_result, payload)
    calibrated_result["executor"] = {
        "mode": "worker-pyodide",
        "runtime": "pyodide-python",
        "implementation": "python.diffusion.phase1_diffusion+python.diffusion.cfd_calibrator",
    }
    return calibrated_result
