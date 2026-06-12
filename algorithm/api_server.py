"""Chemical park gas detection and source tracing API server.

Integrates gas diffusion simulation, PINN-based source inversion, and
D* Lite emergency evacuation path planning into a unified FastAPI service.
YOLO visual detection runs independently on port 8001.

Typical usage:
    uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from engine.task_router import route_task
from gas_diffusion_astar import (
    calculate_gas_and_path,
    get_gas_types_info,
    simulate_time_series,
)
from response_utils import error_response, success_response


logger = logging.getLogger("chemical-algorithm")

app = FastAPI(title="Chemical Park Gas Detection and Tracing - Algorithm Service", version="3.0.0")

# CORS origins are configured by environment variable. The default only
# supports local development and does not use a wildcard.
_cors_origins = os.getenv(
    "ALGORITHM_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8081",
)
allowed_origins = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

_API_KEY = os.getenv("ALGORITHM_API_KEY")
_REQUIRE_AUTH = os.getenv("ALGORITHM_REQUIRE_AUTH", "false").lower() in ("1", "true", "yes")


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Validate the request X-API-Key header."""
    if _API_KEY is None:
        if _REQUIRE_AUTH:
            raise HTTPException(status_code=503, detail="算法服务未配置密钥，拒绝服务")
        logger.warning("ALGORITHM_API_KEY 未设置，算法服务当前无鉴权，仅可用于本地开发")
        return
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="无效的算法服务密钥")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Return HTTP errors with the same JSON envelope as business errors."""
    message = str(exc.detail) if exc.detail else "请求失败"
    return JSONResponse(status_code=exc.status_code, content=error_response(message, exc.status_code))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions with a uniform error response."""
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return await http_exception_handler(request, exc)
    logger.exception("Unhandled algorithm service error: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content=error_response("算法服务内部错误"))


@app.post("/api/gas-path", dependencies=[Depends(require_api_key)])
async def gas_path(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate gas diffusion and escape path."""
    try:
        return success_response(calculate_gas_and_path(data))
    except Exception:
        logger.exception("gas_path calculation failed")
        return error_response("气体扩散与路径计算失败")


@app.get("/api/gas-types", dependencies=[Depends(require_api_key)])
async def gas_types() -> Dict[str, Any]:
    """Get information about all supported gas types."""
    try:
        return success_response(get_gas_types_info())
    except Exception:
        logger.exception("gas_types query failed")
        return error_response("气体类型查询失败")


@app.post("/api/time-series", dependencies=[Depends(require_api_key)])
async def time_series_simulation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Run a time-series diffusion simulation."""
    try:
        return success_response(simulate_time_series(data))
    except Exception:
        logger.exception("time_series_simulation failed")
        return error_response("时序扩散模拟失败")


@app.post("/api/engine/run", dependencies=[Depends(require_api_key)])
async def run_engine_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """Unified algorithm engine entrypoint compatible with Pyodide worker tasks."""
    task_type = data.get("task_type", "")
    payload = data.get("payload", {})
    try:
        result = route_task(task_type, payload)
        return success_response(result)
    except Exception:
        logger.exception("run_engine_task failed, task_type=%s", task_type)
        return error_response("算法引擎执行失败")


@app.post("/api/diffusion/simulate", dependencies=[Depends(require_api_key)])
async def diffusion_simulate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for diffusion simulation."""
    return await run_engine_task({"task_type": "run_diffusion_simulation", "payload": data})


@app.post("/api/inversion/coarse-search", dependencies=[Depends(require_api_key)])
async def pinn_coarse_search(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for PINN coarse source search."""
    return await run_engine_task({"task_type": "run_pinn_coarse_search", "payload": data})


@app.post("/api/inversion/solve", dependencies=[Depends(require_api_key)])
async def pinn_inversion(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for PINN source inversion."""
    return await run_engine_task({"task_type": "run_pinn_inversion", "payload": data})


@app.post("/api/planning/evacuation", dependencies=[Depends(require_api_key)])
async def evacuation_planning(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for evacuation planning."""
    return await run_engine_task({"task_type": "run_evacuation_planning", "payload": data})


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return success_response({"status": "ok", "version": "3.0.0", "service": "chemical-algorithm"})


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)
