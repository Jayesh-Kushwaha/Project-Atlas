
from types import SimpleNamespace

import app.retrieval as retrieval


def test_invalid_client_returns_empty_list(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Database should not be queried for invalid client")

    monkeypatch.setattr(retrieval, "get_allowed_reports", fail_if_called)

    result = retrieval.retrieve_chunks(
        client_id="C-99",
        question="What is the smart water meter market?",
    )

    assert result == []


def test_empty_question_returns_empty_list(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Database should not be queried for empty question")

    monkeypatch.setattr(retrieval, "get_allowed_reports", fail_if_called)

    result = retrieval.retrieve_chunks(
        client_id="C-01",
        question="   ",
    )

    assert result == []


def test_invalid_top_k_returns_empty_list(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Database should not be queried for invalid top_k")

    monkeypatch.setattr(retrieval, "get_allowed_reports", fail_if_called)

    result = retrieval.retrieve_chunks(
        client_id="C-01",
        question="Market size?",
        top_k=0,
    )

    assert result == []


def test_no_allowed_reports_skips_vector_search(monkeypatch):
    monkeypatch.setattr(
        retrieval,
        "get_allowed_reports",
        lambda client_id: [],
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Vector search must not run without allowed reports")

    monkeypatch.setattr(retrieval, "search_chunks", fail_if_called)

    result = retrieval.retrieve_chunks(
        client_id="C-02",
        question="What is the market size?",
    )

    assert result == []


def test_only_allowed_report_ids_are_passed_to_search(monkeypatch):
    reports = [
        SimpleNamespace(report_id="R-102"),
        SimpleNamespace(report_id="R-103"),
    ]
    monkeypatch.setattr(
        retrieval,
        "get_allowed_reports",
        lambda client_id: reports,
    )

    expected_chunks = [
        {
            "report_id": "R-102",
            "text": "Public market report evidence",
        }
    ]

    def fake_search_chunks(
        question,
        client_id,
        top_k,
        allowed_report_ids,
    ):
        assert question == "What is the market size?"
        assert client_id == "C-02"
        assert top_k == 3
        assert allowed_report_ids == ["R-102", "R-103"]
        return expected_chunks

    monkeypatch.setattr(
        retrieval,
        "search_chunks",
        fake_search_chunks,
    )

    result = retrieval.retrieve_chunks(
        client_id="C-02",
        question="What is the market size?",
    )

    assert result == expected_chunks


def test_custom_top_k_is_passed_to_search(monkeypatch):
    monkeypatch.setattr(
        retrieval,
        "get_allowed_reports",
        lambda client_id: [
            SimpleNamespace(report_id="R-102")
        ],
    )

    captured = {}

    def fake_search_chunks(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        retrieval,
        "search_chunks",
        fake_search_chunks,
    )

    retrieval.retrieve_chunks(
        client_id="C-02",
        question="Smart water meter trends",
        top_k=5,
    )

    assert captured["top_k"] == 5
    assert captured["client_id"] == "C-02"
    assert captured["allowed_report_ids"] == ["R-102"]

from app.knowledge import get_allowed_reports
from app.retrieval import retrieve_chunks


def test_c02_database_permissions_exclude_r101():
    reports = get_allowed_reports("C-02")
    report_ids = {report.report_id for report in reports}

    assert "R-101" not in report_ids
    assert "R-102" in report_ids


def test_c01_database_permissions_include_r101():
    reports = get_allowed_reports("C-01")
    report_ids = {report.report_id for report in reports}

    assert "R-101" in report_ids


def test_c02_retrieval_never_returns_r101():
    chunks = retrieve_chunks(
        client_id="C-02",
        question="Global smart water meter market size in 2024",
        top_k=10,
    )

    assert all(
        chunk["report_id"] != "R-101"
        for chunk in chunks
    )
