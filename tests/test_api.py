from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from scripts.train_model import train_and_save


@pytest.fixture(scope="session", autouse=True)
def ensure_model_artifact():
    train_and_save(Path(settings.model_path))


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert {"total_requests", "prediction_requests", "last_prediction_timestamp", "avg_latency_ms"}.issubset(data.keys())


def test_predict_endpoint(client):
    payload = {
        "age": 32,
        "tenure_months": 24,
        "monthly_spend": 150.5,
        "num_support_tickets": 2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["upsell_probability"] <= 1
    assert isinstance(data["upsell_label"], bool)
    assert isinstance(data["request_id"], str) and data["request_id"]
