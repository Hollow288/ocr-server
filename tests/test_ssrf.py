import socket

import pytest


def _addrinfo_for(ip: str):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",
        "10.0.0.5",
        "192.168.1.10",
        "169.254.0.1",
        "0.0.0.0",
    ],
)
def test_ssrf_private_ips_rejected(client, api_key, monkeypatch, ip):
    from app import readers

    monkeypatch.setattr(
        readers.socket,
        "getaddrinfo",
        lambda host, port, *a, **kw: _addrinfo_for(ip),
    )
    r = client.post(
        "/ocr/url",
        json={"url": "http://attacker-controlled.example.com/x.png"},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 400
    assert "restricted" in r.json()["detail"].lower()


def test_ssrf_unresolvable_hostname_rejected(client, api_key, monkeypatch):
    from app import readers

    def boom(*a, **kw):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(readers.socket, "getaddrinfo", boom)
    r = client.post(
        "/ocr/url",
        json={"url": "http://nope.invalid/x.png"},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 400
    assert "resolve" in r.json()["detail"].lower()


def test_non_http_scheme_rejected(client, api_key):
    r = client.post(
        "/ocr/url",
        json={"url": "ftp://example.com/x.png"},
        headers={"X-API-KEY": api_key},
    )
    assert r.status_code == 422
