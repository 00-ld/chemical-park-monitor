"""YOLO person detection service for Ackermann patrol car images."""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from ultralytics import YOLO


logger = logging.getLogger("chemical-algorithm-yolo")

app = FastAPI(title="Chemical Park Patrol Vision Service", version="1.0.0")

_API_KEY = os.getenv("ALGORITHM_API_KEY")
_REQUIRE_AUTH = os.getenv("ALGORITHM_REQUIRE_AUTH", "false").lower() in ("1", "true", "yes")
_YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolo11m.pt")
_YOLO_DEVICE = os.getenv("YOLO_DEVICE", "cpu")
_YOLO_IMAGE_SIZE = int(os.getenv("YOLO_IMAGE_SIZE", "1024"))
_YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.35"))

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_PERSON_CLASS_ID = 0
_model: YOLO | None = None


def _check_key(x_api_key: str | None) -> None:
    """Validate the shared algorithm service key."""
    if _API_KEY is None:
        if _REQUIRE_AUTH:
            raise HTTPException(status_code=503, detail="YOLO 服务未配置密钥，拒绝服务")
        logger.warning("ALGORITHM_API_KEY 未设置，YOLO 服务当前无鉴权，仅可用于本地开发")
        return
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="无效的算法服务密钥")


def _get_model() -> YOLO:
    """Load the YOLO model lazily so health/import checks do not need weights."""
    global _model
    if _model is None:
        model_path = Path(_YOLO_MODEL_PATH)
        if not model_path.exists():
            raise HTTPException(status_code=503, detail=f"YOLO 模型文件不存在: {_YOLO_MODEL_PATH}")
        _model = YOLO(str(model_path))
    return _model


@app.post("/api/analysis/person")
async def detect_and_render(
    file: UploadFile = File(...),
    x_api_key: str | None = Header(default=None),
):
    """Detect people in an uploaded patrol image and return an annotated JPEG."""
    _check_key(x_api_key)

    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 JPEG/PNG 图片")

    contents = await file.read()
    if len(contents) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="图片过大，上传上限为 10MB")

    image_buffer = np.frombuffer(contents, np.uint8)
    image_bgr = cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="无法解析图片")

    results = _get_model().predict(
        source=image_bgr,
        imgsz=_YOLO_IMAGE_SIZE,
        classes=[_PERSON_CLASS_ID],
        conf=_YOLO_CONFIDENCE,
        device=_YOLO_DEVICE,
    )

    annotated_image = results[0].plot(line_width=1, font_size=0.8)
    ok, encoded_image = cv2.imencode(".jpg", annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise HTTPException(status_code=500, detail="检测结果图片编码失败")

    image_base64 = base64.b64encode(encoded_image).decode("utf-8")
    return {
        "status": "success",
        "count": len(results[0].boxes),
        "image_base64": f"data:image/jpeg;base64,{image_base64}",
        "analysis_info": f"YOLO person detection, imgsz={_YOLO_IMAGE_SIZE}, conf={_YOLO_CONFIDENCE}",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
