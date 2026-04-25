def test_missing_api_key_rejected(client):
    r = client.post("/ocr", files={"file": ("a.png", b"x", "image/png")})
    assert r.status_code == 403


def test_wrong_api_key_rejected(client):
    r = client.post(
        "/ocr",
        files={"file": ("a.png", b"x", "image/png")},
        headers={"X-API-KEY": "definitely-not-it"},
    )
    assert r.status_code == 403


def test_url_endpoint_requires_key(client):
    r = client.post("/ocr/url", json={"url": "https://example.com/a.png"})
    assert r.status_code == 403


def test_base64_endpoint_requires_key(client):
    r = client.post("/ocr/base64", json={"data": "AAAA"})
    assert r.status_code == 403


def test_health_endpoint_no_auth(client):
    r = client.get("/")
    assert r.status_code == 200


def test_request_id_header_echoed(client):
    r = client.get("/", headers={"X-Request-ID": "test-rid-1234"})
    assert r.headers.get("X-Request-ID") == "test-rid-1234"


def test_request_id_generated_when_missing(client):
    r = client.get("/")
    assert r.headers.get("X-Request-ID")
