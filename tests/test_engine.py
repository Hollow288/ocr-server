import io
from types import SimpleNamespace

import numpy as np
import pytest
import fitz
from PIL import Image

from app.engine import run_ocr


def test_empty_ocr_output(fake_engine):
    fake_engine.return_value = SimpleNamespace(
        boxes=None, txts=None, scores=None, elapse=0.125
    )

    assert run_ocr(np.zeros((32, 32, 3), dtype=np.uint8)) == ([], 0.125)


@pytest.mark.parametrize("mode", ["detail", "list", "text"])
def test_new_ocr_output_preserves_api(client, api_key, fake_engine, mode):
    box = [[1.0, 2.0], [100.0, 2.0], [100.0, 30.0], [1.0, 30.0]]
    fake_engine.return_value = SimpleNamespace(
        boxes=np.array([box, box], dtype=np.float32),
        txts=("识别结果", "低置信度"),
        scores=(np.float32(0.95), np.float32(0.6)),
        elapse=0.125,
    )
    image = io.BytesIO()
    Image.new("RGB", (120, 40), "white").save(image, format="PNG")

    response = client.post(
        f"/ocr?mode={mode}&min_confidence=0.8",
        files={"file": ("sample.png", image.getvalue(), "image/png")},
        headers={"X-API-KEY": api_key},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["elapse"] == 0.125
    assert body["pages"] is None
    if mode == "detail":
        assert len(body["data"]) == 1
        item = body["data"][0]
        assert item["text"] == "识别结果"
        assert item["bbox"] == box
        assert item["confidence"] == pytest.approx(0.95)
        assert item["page"] is None
    elif mode == "list":
        assert body["data"] == ["识别结果"]
    else:
        assert body["data"] == "识别结果"


def test_pdf_output_keeps_page_numbers_and_total_time(client, api_key, fake_engine):
    box = [[1.0, 2.0], [100.0, 2.0], [100.0, 30.0], [1.0, 30.0]]
    fake_engine.return_value = SimpleNamespace(
        boxes=np.array([box], dtype=np.float32),
        txts=("每页文字",),
        scores=(0.95,),
        elapse=0.125,
    )
    with fitz.open() as doc:
        doc.new_page()
        doc.new_page()
        payload = doc.tobytes()

    response = client.post(
        "/ocr",
        files={"file": ("sample.pdf", payload, "application/pdf")},
        headers={"X-API-KEY": api_key},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pages"] == 2
    assert body["elapse"] == 0.25
    assert [item["page"] for item in body["data"]] == [1, 2]
    assert fake_engine.call_count == 2
