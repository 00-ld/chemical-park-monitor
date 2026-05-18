"""Chemical park gas detection and source tracing API server.

Integrates gas diffusion simulation, PINN-based source inversion, and
D* Lite emergency evacuation path planning into a unified FastAPI service.
YOLO visual detection runs independently on port 8001.

Typical usage:
    uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
import uvicorn

from gasDiffusionAstar import (
    calculate_gas_and_path,
    get_gas_types_info,
    simulate_time_series,
)
from engine.task_router import route_task
from response_utils import success_response, error_response

app = FastAPI(title="Chemical Park Gas Detection and Tracing - Algorithm Service", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# ========== Global Exception Handler ==========


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> Dict[str, Any]:
    """Handle all uncaught exceptions with a uniform error response.

    FastAPI/Starlette standard HTTP exceptions (e.g. 404) are re-raised
    for normal handling.

    Args:
        request: The incoming request.
        exc: The unhandled exception.

    Returns:
        Error response dict with traceback.
    """
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        raise exc
    return error_response(str(exc))


# ========== 1. Gas Diffusion + Path Planning ==========


@app.post("/api/gas-path")
async def gas_path(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate gas diffusion and escape path.

    Accepts leak source, wind, and stability parameters, then computes
    concentration fields and optimal evacuation routes.

    Args:
        data: Request dict with sourceRate, windAngle, windSpeed,
            stability, gasType, startPoint, endPoint, leakPoint.

    Returns:
        Dict with diffusion, escapePath, safetyAnalysis, and gasInfo.
    """
    try:
        return success_response(calculate_gas_and_path(data))
    except Exception as e:
        return error_response(str(e))


@app.get("/api/gas-types")
async def gas_types() -> Dict[str, Any]:
    """Get information about all supported gas types.

    Returns:
        Dict with gas type data including molecular weight, safety
        thresholds, density ratio, and diffusion coefficient.
    """
    try:
        return success_response(get_gas_types_info())
    except Exception as e:
        return error_response(str(e))


@app.post("/api/time-series")
async def time_series_simulation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Run a time-series diffusion simulation.

    Computes concentration evolution over multiple time steps with
    corresponding evacuation route changes.

    Args:
        data: Request dict with numSteps, stepInterval, and same
            parameters as /api/gas-path.

    Returns:
        Dict with frames, dynamicRoutes, and gasInfo.
    """
    try:
        return success_response(simulate_time_series(data))
    except Exception as e:
        return error_response(str(e))


# ========== 2. Algorithm Engine (Pyodide Compatible Task Routing) ==========


@app.post("/api/engine/run")
async def run_engine_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """Unified algorithm engine entrypoint compatible with Pyodide worker tasks.

    Args:
        data: Request dict with task_type (e.g. 'run_diffusion_simulation',
            'run_pinn_coarse_search', 'run_pinn_inversion',
            'run_evacuation_planning') and payload.

    Returns:
        Dict with success status, data or error details.
    """
    task_type = data.get("task_type", "")
    payload = data.get("payload", {})
    try:
        result = route_task(task_type, payload)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))


# ========== 3. Convenience Shortcuts ==========


@app.post("/api/diffusion/simulate")
async def diffusion_simulate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for diffusion simulation.

    Delegates to the engine task router with 'run_diffusion_simulation'.

    Args:
        data: Diffusion simulation parameters.

    Returns:
        Simulation result dict.
    """
    return await run_engine_task({"task_type": "run_diffusion_simulation", "payload": data})


@app.post("/api/inversion/coarse-search")
async def pinn_coarse_search(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for PINN coarse source search.

    Delegates to the engine task router with 'run_pinn_coarse_search'.

    Args:
        data: Coarse search parameters.

    Returns:
        Coarse search result with candidate regions.
    """
    return await run_engine_task({"task_type": "run_pinn_coarse_search", "payload": data})


@app.post("/api/inversion/solve")
async def pinn_inversion(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for PINN source inversion.

    Delegates to the engine task router with 'run_pinn_inversion'.

    Args:
        data: Inversion parameters with sensor data and config.

    Returns:
        Inversion result with estimated source location.
    """
    return await run_engine_task({"task_type": "run_pinn_inversion", "payload": data})


@app.post("/api/planning/evacuation")
async def evacuation_planning(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for evacuation planning.

    Delegates to the engine task router with 'run_evacuation_planning'.

    Args:
        data: Evacuation planning parameters.

    Returns:
        Evacuation route result.
    """
    return await run_engine_task({"task_type": "run_evacuation_planning", "payload": data})


# ========== 4. Health Check ==========


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict with service status, version, and name.
    """
    return {"status": "ok", "version": "3.0.0", "service": "chemical-algorithm"}


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)
