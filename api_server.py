from fastapi import FastAPI, UploadFile, File
from rapidocr_onnxruntime import RapidOCR
import uvicorn
import io
from PIL import Image
import numpy as np

app = FastAPI()

# 初始化 OCR 引擎 (只在启动时加载一次，不用每次请求都加载，速度更快)
engine = RapidOCR()

@app.get("/")
def home():
    return {"message": "OCR 服务正在运行中...请使用 POST /ocr 上传图片"}

@app.post("/ocr")
async def ocr_process(file: UploadFile = File(...)):
    # 1. 读取上传的图片文件
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    
    # 2. 转换为 numpy 数组 (RapidOCR 需要的格式)
    img_np = np.array(image)

    # 3. 执行识别
    result, elapse = engine(img_np)

    # 4. 格式化返回结果
    formatted_result = []
    if result:
        for item in result:
            # item[1] 是文本, item[2] 是置信度
            formatted_result.append({
                "text": item[1],
                "confidence": float(item[2])
            })
    
    return {
        "code": 200,
        "data": formatted_result,
        "elapse": elapse
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
