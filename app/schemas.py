from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl

Mode = Literal["detail", "list"]


class OCRItem(BaseModel):
    text: str
    confidence: float
    bbox: List[List[float]]
    page: Optional[int] = None


class OCRResponse(BaseModel):
    code: int
    data: Union[List[OCRItem], List[str]]
    elapse: float
    pages: Optional[int] = None


class OCRUrlRequest(BaseModel):
    url: HttpUrl
    mode: Mode = "detail"
    min_confidence: Optional[float] = Field(default=None, ge=0, le=1)
