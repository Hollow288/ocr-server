import io
import ipaddress
import socket
from typing import List, Tuple
from urllib.parse import urlparse

import fitz
import numpy as np
import requests
from PIL import Image

from app.config import settings


class PDFTooLargeError(ValueError):
    pass


class DownloadError(Exception):
    pass


def image_bytes_to_np(data: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(data))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return np.array(image)


def pdf_bytes_to_np_pages(data: bytes) -> List[np.ndarray]:
    pages = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        page_count = len(doc)
        if page_count > settings.PDF_MAX_PAGES:
            raise PDFTooLargeError(
                f"PDF has {page_count} pages, exceeds limit of {settings.PDF_MAX_PAGES}"
            )
        for page in doc:
            pix = page.get_pixmap(dpi=settings.PDF_DPI, colorspace=fitz.csRGB)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            pages.append(arr.copy())
    return pages


def _validate_public_url(url: str) -> None:
    if settings.ALLOW_PRIVATE_URLS:
        return
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise DownloadError("Only http and https URLs are allowed")
    hostname = parsed.hostname
    if not hostname:
        raise DownloadError("URL must contain a hostname")
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise DownloadError(f"Failed to resolve hostname: {hostname}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise DownloadError(f"URL resolves to restricted IP: {ip}")


def download_bytes(url: str) -> Tuple[bytes, str]:
    current_url = url
    for _ in range(settings.URL_MAX_REDIRECTS + 1):
        _validate_public_url(current_url)
        try:
            resp = requests.get(
                current_url,
                timeout=settings.URL_DOWNLOAD_TIMEOUT,
                stream=True,
                allow_redirects=False,
            )
        except requests.RequestException as e:
            raise DownloadError(f"Failed to download: {e}")

        with resp:
            if resp.is_redirect or resp.is_permanent_redirect:
                location = resp.headers.get("Location")
                if not location:
                    raise DownloadError("Redirect response missing Location header")
                current_url = requests.compat.urljoin(current_url, location)
                continue

            try:
                resp.raise_for_status()
            except requests.RequestException as e:
                raise DownloadError(f"Failed to download: {e}")

            content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            chunks = []
            total = 0
            for chunk in resp.iter_content(chunk_size=8192):
                total += len(chunk)
                if total > settings.URL_MAX_BYTES:
                    raise DownloadError(
                        f"File exceeds max size of {settings.URL_MAX_BYTES} bytes"
                    )
                chunks.append(chunk)
            return b"".join(chunks), content_type

    raise DownloadError("Too many redirects")
