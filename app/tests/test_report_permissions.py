
from app.knowledge import get_allowed_reports


def test_c01_can_access_r101():
    reports = get_allowed_reports("C-01")
    report_ids = {report.report_id for report in reports}

    assert "R-101" in report_ids


def test_c02_cannot_access_r101():
    reports = get_allowed_reports("C-02")
    report_ids = {report.report_id for report in reports}

    assert "R-101" not in report_ids


def test_both_clients_can_access_public_report():
    c01_reports = get_allowed_reports("C-01")
    c02_reports = get_allowed_reports("C-02")

    c01_ids = {report.report_id for report in c01_reports}
    c02_ids = {report.report_id for report in c02_reports}

    assert "R-102" in c01_ids
    assert "R-102" in c02_ids


def test_unknown_client_gets_no_reports():
    reports = get_allowed_reports("C-99")

    assert reports == []
