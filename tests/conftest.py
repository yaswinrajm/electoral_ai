"""
tests/conftest.py — Shared Test Fixtures
==========================================
Sets up the test environment BEFORE any other imports happen.

Critical: Python imports happen at collection time, before pytest plugins
(including pytest-env) can inject environment variables. Therefore, we
must set GOOGLE_APPLICATION_CREDENTIALS here at module level — the very
first thing in conftest.py — before any `from main import app` is executed.
"""

import os
import sys

# ─── Set credentials BEFORE any app module is imported ────────────────────────
# This ensures init_clients() in routes.py can authenticate with Google APIs.
# The key file path must be relative to the project root (f:\electoral_ai).
_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gcp-key.json")
if os.path.exists(_KEY_FILE):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _KEY_FILE

# Ensure MOCK_MODE is OFF — we want real initialization with our credentials
# (init_clients will authenticate via gcp-key.json, and endpoint handlers
# will check settings.mock_mode which reads from .env — not this env var)
# We leave MOCK_MODE to whatever is in the .env file (default: false)

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    """
    Session-scoped fixture returning the FastAPI app instance.
    Importing here (after credentials are set) ensures init_clients()
    succeeds on the first and only import.
    """
    from main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app):
    """
    Module-scoped TestClient. Shared across all tests in a module to avoid
    repeated app startup overhead.
    """
    with TestClient(app) as c:
        yield c
