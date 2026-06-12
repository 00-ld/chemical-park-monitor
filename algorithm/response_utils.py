"""Unified API response helpers for the Python algorithm service."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict


def success_response(data: Any = None, code: int = 200, message: str = "成功") -> Dict[str, Any]:
    """Build a successful response compatible with the project JSON envelope."""
    return _build_response(code=code, message=message, data=data, ok=True)


def error_response(message: str, code: int = 500) -> Dict[str, Any]:
    """Build an error response compatible with the project JSON envelope."""
    return _build_response(code=code, message=message, data=None, ok=False)


def _build_response(code: int, message: str, data: Any, ok: bool) -> Dict[str, Any]:
    """Create the shared response body while preserving old algorithm fields."""
    return {
        "code": code,
        "message": message,
        "data": data,
        "ok": ok,
        "timestamp": int(time.time() * 1000),
        "requestId": str(uuid.uuid4()),
        "success": ok,
        "error": None if ok else message,
    }
