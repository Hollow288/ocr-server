import base64

import pytest


def test_pdf_too_many_pages_rejected(client, api_key, monkeypatch):
    from app import readers

    def fake_pdf_to_pages(data):
        raise readers.PDFTooLargeError("PDF has 80 pages, exceeds limit of 50")

    monkeypatch.setattr("app.routes.pdf_bytes_to_np_pages", fake_pdf_to_pages)

    pdf = b"%PDF-1.4\n..."
    payload = base64.b64encode(pdf).decode()
    r = client.post(
        "/ocr/base64",
        json={"data": payload},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 413
    assert "pages" in r.json()["detail"].lower()


def test_invalid_pdf_rejected(client, api_key, monkeypatch):
    def boom(data):
        raise RuntimeError("malformed xref")

    monkeypatch.setattr("app.routes.pdf_bytes_to_np_pages", boom)

    pdf = b"%PDF-bad"
    payload = base64.b64encode(pdf).decode()
    r = client.post(
        "/ocr/base64",
        json={"data": payload},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 400
    assert "invalid pdf" in r.json()["detail"].lower()


def test_unsupported_image_format_rejected(client, api_key, monkeypatch):
    def boom(data):
        raise ValueError("not an image")

    monkeypatch.setattr("app.routes.image_bytes_to_np", boom)

    payload = base64.b64encode(b"garbage-not-an-image").decode()
    r = client.post(
        "/ocr/base64",
        json={"data": payload, "mime": "image/png"},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 400
    assert "unsupported" in r.json()["detail"].lower()
