"""Shared pytest fixtures for Chart-Monitor backend tests."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Return a TestClient bound to the FastAPI app."""
    return TestClient(app, raise_server_exceptions=True)
