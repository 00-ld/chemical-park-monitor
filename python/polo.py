from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
import cv2
import numpy as np
import base64

app = FastAPI()

model = YOLO('yolo11m.pt')

@app.post("/api/analysis/person")
async def detect_and_render(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

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
    uvicorn.run(app, host="0.0.0.0", port=8001)




