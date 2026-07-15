"""Integration-style tests for FastAPI routes (no Redis/Celery needed)."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from server.main import app
    with TestClient(app) as c:
        yield c


class TestHealthEndpoints:
    def test_status_ok(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["server"] == "online"
        assert "algo_count" in data

    def test_algos_returns_list(self, client):
        resp = client.get("/api/algos")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_algo_not_found(self, client):
        resp = client.get("/api/algo/99999")
        assert resp.status_code == 404

    def test_bars_returns_data(self, client):
        resp = client.get("/api/bars/ES?limit=50")
        assert resp.status_code == 200
        data = resp.json()
        assert "bars" in data
        assert len(data["bars"]) > 0

    def test_account_returns_balance(self, client):
        resp = client.get("/api/account")
        assert resp.status_code == 200
        data = resp.json()
        assert "balance" in data
        assert data["balance"] > 0

    def test_positions_returns_list(self, client):
        resp = client.get("/api/positions")
        assert resp.status_code == 200
        assert "positions" in resp.json()


class TestTradeEndpoint:
    def test_trade_503_without_celery(self, client):
        """Without a real Celery worker the endpoint returns 503."""
        resp = client.post(
            "/api/trade",
            json={"symbol": "ES", "action": "Buy", "quantity": 1},
        )
        # Either 200 (if Celery happened to be available) or 503
        assert resp.status_code in (200, 503)

    def test_trade_rejects_invalid_payload(self, client):
        resp = client.post("/api/trade", json={"symbol": "ES"})
        assert resp.status_code == 422
