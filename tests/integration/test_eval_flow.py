import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@patch("eval_worker.api.init_db")
@patch("eval_worker.api.worker_loop")
@patch("threading.Thread")
def test_health_endpoint(mock_thread, mock_loop, mock_init):
    from eval_worker.api import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("eval_worker.api.init_db")
@patch("eval_worker.api.worker_loop")
@patch("threading.Thread")
@patch("eval_worker.api.metrics_output", return_value=(b"# metrics\n", "text/plain"))
def test_metrics_endpoint(mock_metrics, mock_thread, mock_loop, mock_init):
    from eval_worker.api import app
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"metrics" in response.content


def test_dummy_app_health():
    from example_app.main import app
    client = TestClient(app)
    response = client.get("/run_agent?query=pytest")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"