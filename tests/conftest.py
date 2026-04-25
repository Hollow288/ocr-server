import sys
from unittest.mock import MagicMock

_fake_rapidocr = MagicMock()
_fake_engine_instance = MagicMock(return_value=([], 0.0))
_fake_rapidocr.RapidOCR = MagicMock(return_value=_fake_engine_instance)
sys.modules["rapidocr_onnxruntime"] = _fake_rapidocr

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def api_key():
    from app.config import settings

    return settings.API_KEY


@pytest.fixture
def fake_engine():
    return _fake_engine_instance
