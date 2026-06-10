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
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Header, Depends
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

logger = logging.getLogger("chemical-algorithm")

app = FastAPI(title="Chemical Park Gas Detection and Tracing - Algorithm Service", version="3.0.0")

# CORS：从环境变量读取允许来源，默认仅本地开发端口；不再使用通配 "*"。
# 多个来源用逗号分隔，例如 ALGORITHM_CORS_ORIGINS="https://example.com,https://admin.example.com"
_cors_origins = os.getenv(
    "ALGORITHM_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8081",
)
allowed_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# ========== 共享密钥鉴权 ==========
# 算法服务仅供 Java 后端 / 经 nginx 注入密钥的前端调用，不应公网裸奔。
# 通过环境变量 ALGORITHM_API_KEY 配置；未配置时为兼容本地开发放行，但会告警。
_API_KEY = os.getenv("ALGORITHM_API_KEY")
# 鉴权强制开关：生产部署设为 true，漏配密钥时显式拒绝服务而非静默裸奔放行。
_REQUIRE_AUTH = os.getenv("ALGORITHM_REQUIRE_AUTH", "false").lower() in ("1", "true", "yes")


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """校验请求头 X-API-Key。

    Args:
        x_api_key: 调用方在 X-API-Key 头中携带的密钥。

    Raises:
        HTTPException: 密钥缺失或不匹配时返回 401；强制鉴权但未配置密钥时返回 503。
    """
    if _API_KEY is None:
        if _REQUIRE_AUTH:
            # 生产环境强制鉴权但未配置密钥：显式拒绝服务，避免无鉴权裸奔
            raise HTTPException(status_code=503, detail="算法服务未配置密钥，拒绝服务")
        # 未配置密钥：本地开发模式放行，但记录告警提醒生产环境务必配置
        logger.warning("ALGORITHM_API_KEY 未设置，算法服务当前无鉴权（仅可用于本地开发）")
        return
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="无效的算法服务密钥")


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
        Error response dict with a generic message (no internal details).
    """
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        raise exc
    # 仅在服务端日志记录完整堆栈，对外只返回通用提示，避免泄露内部信息
    logger.exception("未处理的算法服务异常: %s %s", request.method, request.url.path)
    return error_response("算法服务内部错误")


# ========== 1. Gas Diffusion + Path Planning ==========


@app.post("/api/gas-path", dependencies=[Depends(require_api_key)])
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
    except Exception:
        logger.exception("gas_path 计算失败")
        return error_response("气体扩散与路径计算失败")


@app.get("/api/gas-types", dependencies=[Depends(require_api_key)])
async def gas_types() -> Dict[str, Any]:
    """Get information about all supported gas types.

    Returns:
        Dict with gas type data including molecular weight, safety
        thresholds, density ratio, and diffusion coefficient.
    """
    try:
        return success_response(get_gas_types_info())
    except Exception:
        logger.exception("gas_types 查询失败")
        return error_response("气体类型查询失败")


@app.post("/api/time-series", dependencies=[Depends(require_api_key)])
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
    except Exception:
        logger.exception("time_series_simulation 失败")
        return error_response("时序扩散模拟失败")


# ========== 2. Algorithm Engine (Pyodide Compatible Task Routing) ==========


@app.post("/api/engine/run", dependencies=[Depends(require_api_key)])
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
    except Exception:
        logger.exception("run_engine_task 失败, task_type=%s", task_type)
        return error_response("算法引擎执行失败")


# ========== 3. Convenience Shortcuts ==========


@app.post("/api/diffusion/simulate", dependencies=[Depends(require_api_key)])
async def diffusion_simulate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for diffusion simulation.

    Delegates to the engine task router with 'run_diffusion_simulation'.

    Args:
        data: Diffusion simulation parameters.

    Returns:
        Simulation result dict.
    """
    return await run_engine_task({"task_type": "run_diffusion_simulation", "payload": data})


@app.post("/api/inversion/coarse-search", dependencies=[Depends(require_api_key)])
async def pinn_coarse_search(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for PINN coarse source search.

    Delegates to the engine task router with 'run_pinn_coarse_search'.

    Args:
        data: Coarse search parameters.

    Returns:
        Coarse search result with candidate regions.
    """
    return await run_engine_task({"task_type": "run_pinn_coarse_search", "payload": data})


@app.post("/api/inversion/solve", dependencies=[Depends(require_api_key)])
async def pinn_inversion(data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick-access endpoint for PINN source inversion.

    Delegates to the engine task router with 'run_pinn_inversion'.

    Args:
        data: Inversion parameters with sensor data and config.

    Returns:
        Inversion result with estimated source location.
    """
    return await run_engine_task({"task_type": "run_pinn_inversion", "payload": data})


@app.post("/api/planning/evacuation", dependencies=[Depends(require_api_key)])
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
