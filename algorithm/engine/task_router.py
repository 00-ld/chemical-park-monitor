"""Pyodide task router module.

Routes task type strings to the appropriate algorithm implementation
module (diffusion, inversion, or planning).

Typical usage:
    result = route_task("run_diffusion_simulation", payload)
"""

from __future__ import annotations

from typing import Dict

from diffusion.diffusion_runner import run_diffusion_simulation_task
from inversion.inversion_runner import (
    run_particle_filter_inversion_task,
    run_pinn_coarse_search_task,
    run_pinn_inversion_task,
)
from planning.evacuation_runner import run_evacuation_planning_task


def route_task(task_type: str, payload: Dict) -> Dict:
    """Route a task to the appropriate algorithm implementation.

    Args:
        task_type: Task type identifier. Supported values:
            - 'run_diffusion_simulation'
            - 'run_evacuation_planning'
            - 'run_pinn_coarse_search'
            - 'run_pinn_inversion'
            - 'run_particle_filter_inversion'
        payload: Task-specific payload dictionary.

    Returns:
        Task result dictionary from the routed algorithm module.

    Raises:
        ValueError: If task_type is not recognized or the task fails.
    """
    try:
        if task_type == "run_diffusion_simulation":
            return run_diffusion_simulation_task(payload)
        if task_type == "run_evacuation_planning":
            return run_evacuation_planning_task(payload)
        if task_type == "run_pinn_coarse_search":
            return run_pinn_coarse_search_task(payload)
        if task_type == "run_pinn_inversion":
            return run_pinn_inversion_task(payload)
        if task_type == "run_particle_filter_inversion":
            return run_particle_filter_inversion_task(payload)
        raise ValueError(f"Unsupported task type: '{task_type}'")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Task '{task_type}' failed: {e}") from e
