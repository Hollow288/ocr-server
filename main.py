import os
import time

# ⚠️ 必须在所有 import 之前
# os.environ["FLAGS_enable_onednn"] = "0"
# os.environ["FLAGS_enable_mkldnn"] = "0"
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from fastapi import FastAPI, UploadFile, File
from paddleocr import PaddleOCR
import uvicorn
import shutil

app = FastAPI()


ocr = PaddleOCR(
    lang="ch",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
        enable_mkldnn=False,
    device="cpu")



@app.post("/ocr")
def ocr_process(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"

    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ✅ 正确调用
        start_time = time.perf_counter()

        result = ocr.predict(temp_filename)

        end_time = time.perf_counter()
        cost = end_time - start_time
        print(f"🕒 OCR 耗时: {cost:.3f} 秒")

        relust_list = []

        for res in result:
            relust_list.append(res['rec_texts'])

        return {
            "code": 200,
            "cost": cost,
            "data": relust_list
        }

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

def extract_text(result):
    texts = []
    for page in result:
        for line in page:
            texts.append(line[1][0])  # line[1][0] 是识别到的文字
    return texts

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
