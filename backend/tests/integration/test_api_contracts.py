"""Integration tests: API contract for DashboardDataResponse (TDD)."""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest


class TestDashboardListContract:
    def test_get_dashboards_returns_list(self, client: TestClient) -> None:
        resp = client.get("/api/v1/dashboards")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_dashboard_list_item_schema(self, client: TestClient) -> None:
        resp = client.get("/api/v1/dashboards")
        body = resp.json()
        if body:
            d = body[0]
            assert "id" in d
            assert "name" in d
            assert "scrape_interval_seconds" in d
            assert isinstance(d["scrape_interval_seconds"], int)


class TestDashboardDataContract:
    def test_unknown_dashboard_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/dashboards/nonexistent/data")
        assert resp.status_code == 404

    def test_data_response_schema(self, client: TestClient) -> None:
        # This test requires at least one dashboard to be registered.
        # When no store is seeded, we simply skip to avoid false negatives.
        dashboards = client.get("/api/v1/dashboards").json()
        if not dashboards:
            pytest.skip("No dashboards registered – skipping data contract test")

        dashboard_id = dashboards[0]["id"]
        resp = client.get(f"/api/v1/dashboards/{dashboard_id}/data")
        assert resp.status_code == 200
        body = resp.json()
        assert "dashboard_id" in body
        assert "columns" in body
        assert "rows" in body
        assert "scrape_interval_seconds" in body
        assert isinstance(body["columns"], list)
        assert isinstance(body["rows"], list)
