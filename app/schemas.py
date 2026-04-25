from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl

Mode = Literal["detail", "list", "text"]


class OCRItem(BaseModel):
    text: str
    confidence: float
    bbox: List[List[float]]
    page: Optional[int] = None


class OCRResponse(BaseModel):
    code: int
    data: Union[List[OCRItem], List[str], str]
    elapse: float
    pages: Optional[int] = None


class OCRUrlRequest(BaseModel):
    url: HttpUrl
    mode: Mode = "detail"
    min_confidence: Optional[float] = Field(default=None, ge=0, le=1)


class OCRBase64Request(BaseModel):
    data: str = Field(..., description="base64 编码的图片或 PDF 字节")
    mime: Optional[str] = Field(
        default=None,
        description="可选的 MIME 提示，例如 image/png 或 application/pdf；缺省时按字节魔术头自动判断",
    )
    mode: Mode = "detail"
    min_confidence: Optional[float] = Field(default=None, ge=0, le=1)
