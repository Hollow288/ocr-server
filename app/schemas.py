from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class OCRItem(BaseModel):
    text: str
    confidence: float
    bbox: List[List[float]]
    page: Optional[int] = None


class OCRResponse(BaseModel):
    code: int
    data: List[OCRItem]
    elapse: float
    pages: Optional[int] = None


class OCRUrlRequest(BaseModel):
    url: HttpUrl
