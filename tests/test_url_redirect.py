import socket
from unittest.mock import MagicMock


def _public_addrinfo(host, port, *a, **kw):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))]


def test_too_many_redirects(client, api_key, monkeypatch):
    from app import readers

    monkeypatch.setattr(readers.socket, "getaddrinfo", _public_addrinfo)

    redirect_resp = MagicMock()
    redirect_resp.is_redirect = True
    redirect_resp.is_permanent_redirect = False
    redirect_resp.headers = {"Location": "/next"}
    redirect_resp.__enter__ = lambda self: self
    redirect_resp.__exit__ = lambda *a: None

    monkeypatch.setattr(readers.requests, "get", lambda *a, **kw: redirect_resp)

    r = client.post(
        "/ocr/url",
        json={"url": "https://8.8.8.8/x.png"},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 400
    assert "redirect" in r.json()["detail"].lower()


def test_url_max_bytes_enforced(client, api_key, monkeypatch):
    from app import config, readers

    monkeypatch.setattr(config.settings, "URL_MAX_BYTES", 50)
    monkeypatch.setattr(readers.settings, "URL_MAX_BYTES", 50)
    monkeypatch.setattr(readers.socket, "getaddrinfo", _public_addrinfo)

    resp = MagicMock()
    resp.is_redirect = False
    resp.is_permanent_redirect = False
    resp.headers = {"content-type": "image/png"}
    resp.raise_for_status = lambda: None
    resp.iter_content = lambda chunk_size: [b"x" * 200]
    resp.__enter__ = lambda self: self
    resp.__exit__ = lambda *a: None

    monkeypatch.setattr(readers.requests, "get", lambda *a, **kw: resp)

    r = client.post(
        "/ocr/url",
        json={"url": "https://8.8.8.8/x.png"},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 400
    assert "exceeds" in r.json()["detail"].lower()
