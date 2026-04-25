import pytest


@pytest.fixture
def small_limit(monkeypatch):
    from app import config, routes

    monkeypatch.setattr(config.settings, "UPLOAD_MAX_BYTES", 100)
    monkeypatch.setattr(routes.settings, "UPLOAD_MAX_BYTES", 100)
    return 100


def test_upload_over_limit_rejected(client, api_key, small_limit):
    big = b"x" * (small_limit * 4)
    r = client.post(
        "/ocr",
        files={"file": ("a.png", big, "image/png")},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 413
    assert "exceeds" in r.json()["detail"].lower()


def test_base64_over_limit_rejected(client, api_key, small_limit):
    import base64

    payload = base64.b64encode(b"x" * (small_limit * 4)).decode()
    r = client.post(
        "/ocr/base64",
        json={"data": payload},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 413
