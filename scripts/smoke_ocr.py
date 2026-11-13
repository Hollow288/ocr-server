"""Run real CPU OCR, including in AMD64/ARM64 images without network access.

Usage: python -m scripts.smoke_ocr
"""

import io

from PIL import Image, ImageDraw, ImageFont

from app.routes import _run


def main():
    image = Image.new("RGB", (720, 140), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (24, 30), "RapidOCR 12345", font=ImageFont.load_default(size=64), fill="black"
    )
    payload = io.BytesIO()
    image.save(payload, format="PNG")

    result = _run(payload.getvalue(), is_pdf=False, mode="detail", min_confidence=None)
    text = "".join(item.text for item in result.data)
    if "rapidocr12345" not in "".join(text.lower().split()):
        raise AssertionError(f"Unexpected OCR result: {text!r}")
    if not all(len(item.bbox) == 4 and 0 <= item.confidence <= 1 for item in result.data):
        raise AssertionError(f"Invalid OCR details: {result.data!r}")
    print(f"Real OCR smoke test passed: {text!r}; OCR time: {result.elapse:.3f}s")


if __name__ == "__main__":
    main()
