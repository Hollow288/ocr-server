import base64
import binascii
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.engine import run_ocr
from app.readers import (
    DownloadError,
    PDFTooLargeError,
    download_bytes,
    image_bytes_to_np,
    pdf_bytes_to_np_pages,
)
from app.schemas import Mode, OCRBase64Request, OCRItem, OCRResponse, OCRUrlRequest
from app.security import get_api_key

router = APIRouter()

PDF_MIME = "application/pdf"
PDF_MAGIC = b"%PDF-"


def _is_pdf(content_type: Optional[str], filename: Optional[str]) -> bool:
    if content_type and content_type.lower().split(";")[0].strip() == PDF_MIME:
        return True
    return bool(filename and filename.lower().endswith(".pdf"))


def _is_pdf_bytes(data: bytes) -> bool:
    return data[:5] == PDF_MAGIC


async def _read_upload_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    chunks = []
    total = 0
    chunk_size = 64 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Upload exceeds max size of {max_bytes} bytes",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _run(
    data: bytes,
    is_pdf: bool,
    mode: Mode,
    min_confidence: Optional[float],
) -> OCRResponse:
    items: list[OCRItem] = []
    total_elapse = 0.0
    pages = None

    def _accept(conf: float) -> bool:
        return min_confidence is None or conf >= min_confidence

    if is_pdf:
        try:
            page_images = pdf_bytes_to_np_pages(data)
        except PDFTooLargeError as e:
            raise HTTPException(status_code=413, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid PDF: {e}")
        pages = len(page_images)
        for idx, img_np in enumerate(page_images, start=1):
            result, elapse = run_ocr(img_np)
            total_elapse += elapse
            if result:
                for item in result:
                    confidence = float(item[2])
                    if not _accept(confidence):
                        continue
                    items.append(
                        OCRItem(text=item[1], confidence=confidence, bbox=item[0], page=idx)
                    )
    else:
        try:
            img_np = image_bytes_to_np(data)
        except Exception:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        result, elapse = run_ocr(img_np)
        total_elapse = elapse
        if result:
            for item in result:
                confidence = float(item[2])
                if not _accept(confidence):
                    continue
                items.append(OCRItem(text=item[1], confidence=confidence, bbox=item[0]))

    if mode == "detail":
        response_data = items
    elif mode == "text":
        response_data = "".join(it.text for it in items)
    else:
        response_data = [it.text for it in items]
    return OCRResponse(code=200, data=response_data, elapse=total_elapse, pages=pages)


@router.post("/ocr", response_model=OCRResponse, dependencies=[Depends(get_api_key)])
async def ocr_process(
    file: UploadFile = File(...),
    mode: Mode = Query("detail"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
):
    data = await _read_upload_with_limit(file, settings.UPLOAD_MAX_BYTES)
    is_pdf = _is_pdf(file.content_type, file.filename)
    return await run_in_threadpool(_run, data, is_pdf, mode, min_confidence)


@router.post("/ocr/url", response_model=OCRResponse, dependencies=[Depends(get_api_key)])
async def ocr_url(req: OCRUrlRequest):
    url = str(req.url)
    try:
        data, content_type = await run_in_threadpool(download_bytes, url)
    except DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await run_in_threadpool(
        _run, data, _is_pdf(content_type, url), req.mode, req.min_confidence
    )


@router.post("/ocr/base64", response_model=OCRResponse, dependencies=[Depends(get_api_key)])
async def ocr_base64(req: OCRBase64Request):
    payload = req.data
    if "," in payload[:64] and payload[:5].lower() == "data:":
        payload = payload.split(",", 1)[1]
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Invalid base64 payload")
    if not raw:
        raise HTTPException(status_code=400, detail="Empty payload")
    if len(raw) > settings.UPLOAD_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds max size of {settings.UPLOAD_MAX_BYTES} bytes",
        )
    if req.mime:
        is_pdf = req.mime.lower().split(";")[0].strip() == PDF_MIME
    else:
        is_pdf = _is_pdf_bytes(raw)
    return await run_in_threadpool(_run, raw, is_pdf, req.mode, req.min_confidence)
