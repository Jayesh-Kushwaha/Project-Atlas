
import pytest
import app.main as main_module


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
