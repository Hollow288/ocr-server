from fastapi import FastAPI

from app.routes import router

app = FastAPI(title="OCR Service")


@app.get("/")
def home():
    return {"message": "OCR 服务正在运行中...请使用 POST /ocr 上传图片或 PDF"}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
