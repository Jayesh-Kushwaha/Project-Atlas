
import json
import pytest
import app.main as main_module
from fastapi.testclient import TestClient

client = TestClient(main_module.app)

C01_API_KEY = "test-client-key-01"
C02_API_KEY = "test-client-key-02"


@pytest.fixture(autouse=True)
def configure_test_keys(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "CLIENT_API_KEYS",
        {
            "C-01": C01_API_KEY,
            "C-02": C02_API_KEY,
        },
    )
    monkeypatch.setattr(
        main_module,
        "ADMIN_API_KEY",
        "test-admin-key",
    )


def test_blue_delta_cannot_access_r101():
    response = client.post(
        "/chat",
        headers={"x-api-key": C02_API_KEY},
        json={
            "client_id": "C-02",
            "message": (
                "Global smart water meter market "
                "size in 2024"
            ),
        },
    )

    assert response.status_code == 200

    result = json.dumps(response.json())
    assert "R-101" not in result
    assert "$4.21 billion" not in result


def test_northwind_can_access_r101():
    response = client.post(
        "/chat",
        headers={"x-api-key": C01_API_KEY},
        json={
            "client_id": "C-01",
            "message": (
                "Global smart water meter market "
                "size in 2024"
            ),
        },
    )

    assert response.status_code == 200

    result = json.dumps(response.json())
    assert "R-101" in result


def test_invalid_api_key_is_rejected():
    response = client.post(
        "/chat",
        headers={"x-api-key": "wrong-key"},
        json={
            "client_id": "C-01",
            "message": "Market size?",
        },
    )

    assert response.status_code == 401


def test_unknown_client_is_rejected():
    response = client.post(
        "/chat",
        headers={"x-api-key": C01_API_KEY},
        json={
            "client_id": "C-99",
            "message": "Market size?",
        },
    )

    assert response.status_code == 403
