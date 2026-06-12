import os
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from ultralytics import YOLO
import cv2
import numpy as np
import base64

logger = logging.getLogger("chemical-algorithm-yolo")

app = FastAPI()

model = YOLO('yolo11m.pt')

# 共享密钥：与 api_server 一致，仅供 Java 后端内网调用。
_API_KEY = os.getenv("ALGORITHM_API_KEY")
# 鉴权强制开关：生产部署设为 true，漏配密钥时显式拒绝服务而非裸奔放行。
_REQUIRE_AUTH = os.getenv("ALGORITHM_REQUIRE_AUTH", "false").lower() in ("1", "true", "yes")

# 上传图片限制：防止超大文件 / 非图片内容耗尽内存（F-2）。
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB


def _check_key(x_api_key: str | None) -> None:
    if _API_KEY is None:
        if _REQUIRE_AUTH:
            # 生产环境强制鉴权但未配置密钥：显式拒绝，避免无鉴权裸奔
            raise HTTPException(status_code=503, detail="算法服务未配置密钥，拒绝服务")
        # 本地开发放行，但告警提醒生产环境务必配置密钥
        logger.warning("ALGORITHM_API_KEY 未设置，YOLO 服务当前无鉴权（仅可用于本地开发）")
        return
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="无效的算法服务密钥")


@app.post("/api/analysis/person")
async def detect_and_render(
    file: UploadFile = File(...),
    x_api_key: str | None = Header(default=None),
):
    _check_key(x_api_key)

    # 仅允许常见图片类型，拦截非图片上传（F-2）
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 JPEG/PNG 图片")

    contents = await file.read()

    # 限制图片大小，防止超大文件耗尽内存（F-2）
    if len(contents) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="图片过大，上限10MB")

    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 解码失败（损坏或伪造的图片字节）直接拒绝（F-2）
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="无法解析图片")

    # 这样可以识别更远、更小的人体
    results = model.predict(
        source=img_bgr,
        imgsz=1024,   # 提高输入分辨率是解决准确率的第一手段
        classes=[0],
        conf=0.35,    # 稍微提高置信度，确保抓到的都是真的
        device='cpu'
    )

    # 美化渲染：画框更细，标签更清晰
    annotated_img = results[0].plot(line_width=1, font_size=0.8)

    _, buffer = cv2.imencode('.jpg', annotated_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    return {
        "status": "success",
        "count": len(results[0].boxes),
        "image_base64": f"data:image/jpeg;base64,{img_base64}",
        "analysis_info": "High-Res Mode (1024px)"
    }
if __name__ == "__main__":
    import uvicorn
    # 仅绑定回环地址，禁止外部直连；由 Java 后端经内网调用
    uvicorn.run(app, host="127.0.0.1", port=8001)




