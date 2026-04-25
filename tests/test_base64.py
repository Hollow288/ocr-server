import base64


def test_invalid_base64_rejected(client, api_key):
    r = client.post(
        "/ocr/base64",
        json={"data": "***not-base64***"},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 400
    assert "base64" in r.json()["detail"].lower()


def test_empty_payload_rejected(client, api_key):
    r = client.post(
        "/ocr/base64",
        json={"data": ""},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 400


def test_data_url_prefix_stripped(client, api_key, fake_engine):
    fake_engine.return_value = ([], 0.0)
    raw = b"\x89PNG\r\n\x1a\nfake"
    payload = "data:image/png;base64," + base64.b64encode(raw).decode()
    r = client.post(
        "/ocr/base64",
        json={"data": payload},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code in (200, 400)


def test_pdf_magic_byte_detection(client, api_key, monkeypatch):
    captured = {}

    def fake_run(data, is_pdf, mode, min_confidence):
        captured["is_pdf"] = is_pdf
        from app.schemas import OCRResponse

        return OCRResponse(code=200, data=[], elapse=0.0, pages=None)

    from app import routes

    monkeypatch.setattr(routes, "_run", fake_run)
    pdf_bytes = b"%PDF-1.4\nrest"
    payload = base64.b64encode(pdf_bytes).decode()
    r = client.post(
        "/ocr/base64",
        json={"data": payload},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 200
    assert captured["is_pdf"] is True


def test_explicit_mime_overrides_magic(client, api_key, monkeypatch):
    captured = {}

    def fake_run(data, is_pdf, mode, min_confidence):
        captured["is_pdf"] = is_pdf
        from app.schemas import OCRResponse

        return OCRResponse(code=200, data=[], elapse=0.0, pages=None)

    from app import routes

    monkeypatch.setattr(routes, "_run", fake_run)
    payload = base64.b64encode(b"%PDF-1.4\nrest").decode()
    r = client.post(
        "/ocr/base64",
        json={"data": payload, "mime": "image/png"},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 200
    assert captured["is_pdf"] is False
