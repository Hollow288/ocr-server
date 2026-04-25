import logging
import time
import uuid

from fastapi import FastAPI, Request

from app.config import settings
from app.logging_setup import configure_logging, request_id_ctx
from app.routes import router

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger("ocr.access")

app = FastAPI(title="OCR Service")


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    token = request_id_ctx.set(rid)
    start = time.monotonic()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        logger.info(
            "access",
            extra={
                "extras": {
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": duration_ms,
                    "client": request.client.host if request.client else None,
                    "content_length": request.headers.get("content-length"),
                }
            },
        )
        request_id_ctx.reset(token)


@app.get("/")
def home():
    return {"message": "OCR 服务正在运行中...请使用 POST /ocr 上传图片或 PDF"}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
