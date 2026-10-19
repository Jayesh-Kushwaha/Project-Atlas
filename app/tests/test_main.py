
import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app, is_insufficient_answer, validate_citations

client = TestClient(app)


@pytest.fixture(autouse=True)
def configure_test_keys(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "CLIENT_API_KEYS",
        {
            "C-01": "test-client-key-01",
            "C-02": "test-client-key-02",
        },
    )
    monkeypatch.setattr(
        main_module,
        "ADMIN_API_KEY",
        "test-admin-key",
    )


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200


def test_insufficient_answer_detection():
    assert is_insufficient_answer(
        "There is insufficient evidence in the reports."
    ) is True


def test_sufficient_answer_detection():
    assert is_insufficient_answer(
        "The market was valued at $4.21 billion [R-101]."
    ) is False


def test_invalid_citation_detection():
    chunks = [{"report_id": "R-101"}]

    result = validate_citations(
        "The estimate is $5 billion [R-999].",
        chunks,
    )

    assert result["valid"] is False
    assert "R-999" in result["invalid_report_ids"]


def test_valid_citation_detection():
    chunks = [{"report_id": "R-101"}]

    result = validate_citations(
        "The estimate is $4.21 billion [R-101].",
        chunks,
    )

    assert result["valid"] is True


def test_allowed_clients_configuration():
    assert main_module.ALLOWED_CLIENTS == {"C-01", "C-02"}


def test_client_authentication():
    assert (
        main_module.authenticate_client("test-client-key-01")
        == "C-01"
    )
    assert (
        main_module.authenticate_client("test-client-key-02")
        == "C-02"
    )


def test_invalid_client_key_rejected():
    with pytest.raises(main_module.HTTPException) as error:
        main_module.authenticate_client("wrong-key")

    assert error.value.status_code == 401


def test_missing_client_key_rejected():
    with pytest.raises(main_module.HTTPException) as error:
        main_module.authenticate_client("")

    assert error.value.status_code == 401


def test_identical_client_keys_rejected(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "CLIENT_API_KEYS",
        {
            "C-01": "same-key",
            "C-02": "same-key",
        },
    )

    with pytest.raises(main_module.HTTPException) as error:
        main_module.authenticate_client("same-key")

    assert error.value.status_code == 503


def test_admin_key_rejected_for_client_authentication():
    with pytest.raises(main_module.HTTPException) as error:
        main_module.authenticate_client("test-admin-key")

    assert error.value.status_code == 401


def test_client_key_rejected_for_admin_endpoint():
    with pytest.raises(main_module.HTTPException) as error:
        main_module.check_admin_api_key("test-client-key-01")

    assert error.value.status_code == 401


def test_admin_key_accepted():
    main_module.check_admin_api_key("test-admin-key")


def test_chat_rejects_invalid_api_key():
    response = client.post(
        "/chat",
        headers={"x-api-key": "wrong-key"},
        json={
            "client_id": "C-01",
            "message": "Tell me about the market",
        },
    )

    assert response.status_code == 401


def test_chat_rejects_missing_api_key():
    response = client.post(
        "/chat",
        json={
            "client_id": "C-01",
            "message": "Tell me about the market",
        },
    )

    assert response.status_code == 401


def test_chat_rejects_cross_client_access():
    response = client.post(
        "/chat",
        headers={"x-api-key": "test-client-key-01"},
        json={
            "client_id": "C-02",
            "message": "Tell me about the market",
        },
    )

    assert response.status_code == 403


def test_chat_valid_key_creates_escalation_when_no_chunks(
    monkeypatch,
):
    monkeypatch.setattr(
        main_module,
        "retrieve_chunks",
        lambda **kwargs: [],
    )

    response = client.post(
        "/chat",
        headers={"x-api-key": "test-client-key-01"},
        json={
            "client_id": "C-01",
            "message": "Tell me about the market",
        },
    )

    assert response.status_code == 200
    assert response.json()["escalation"]["created"] is True


def test_escalations_requires_client_id():
    response = client.get(
        "/escalations",
        headers={"x-api-key": "test-client-key-01"},
    )

    assert response.status_code == 422


def test_escalations_rejects_cross_client_access():
    response = client.get(
        "/escalations?client_id=C-02",
        headers={"x-api-key": "test-client-key-01"},
    )

    assert response.status_code == 403

def test_client_key_cannot_ingest_report():
    response = client.post(
        "/ingest",
        headers={"x-api-key": "test-client-key-01"},
        json={
            "report_id": "R-TEST-SEC",
            "title": "Security test report",
            "content": "This is a test report with enough text.",
            "access": "public",
            "allowed_clients": ["C-01"],
        },
    )

    assert response.status_code == 401


def test_client_cannot_create_another_clients_ticket():
    response = client.post(
        "/escalations",
        headers={"x-api-key": "test-client-key-01"},
        json={
            "client_id": "C-02",
            "question": "Test another client access",
            "reason": "Testing cross-client authorization",
        },
    )

    assert response.status_code == 403


def test_admin_key_cannot_access_client_chat():
    response = client.post(
        "/chat",
        headers={"x-api-key": "test-admin-key"},
        json={
            "client_id": "C-01",
            "message": "Tell me about the market",
        },
    )

    assert response.status_code == 401
