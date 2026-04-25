from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.engine import run_ocr
from app.readers import (
    DownloadError,
    PDFTooLargeError,
    download_bytes,
    image_bytes_to_np,
    pdf_bytes_to_np_pages,
)
from app.schemas import Mode, OCRItem, OCRResponse, OCRUrlRequest
from app.security import get_api_key

router = APIRouter()

PDF_MIME = "application/pdf"


def _is_pdf(content_type: Optional[str], filename: Optional[str]) -> bool:
    if content_type and content_type.lower().split(";")[0].strip() == PDF_MIME:
        return True
    return bool(filename and filename.lower().endswith(".pdf"))


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

    response_data = items if mode == "detail" else [it.text for it in items]
    return OCRResponse(code=200, data=response_data, elapse=total_elapse, pages=pages)


@router.post("/ocr", response_model=OCRResponse, dependencies=[Depends(get_api_key)])
async def ocr_process(
    file: UploadFile = File(...),
    mode: Mode = Query("detail"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
):
    data = await file.read()
    return _run(data, _is_pdf(file.content_type, file.filename), mode, min_confidence)


@router.post("/ocr/url", response_model=OCRResponse, dependencies=[Depends(get_api_key)])
async def ocr_url(req: OCRUrlRequest):
    url = str(req.url)
    try:
        data, content_type = download_bytes(url)
    except DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _run(data, _is_pdf(content_type, url), req.mode, req.min_confidence)
