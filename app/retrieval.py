
from app.knowledge import get_allowed_reports
from app.vector_store import search_chunks


def retrieve_chunks(
    client_id: str,
    question: str,
    top_k: int = 3,
) -> list[dict]:
    if client_id not in {"C-01", "C-02"}:
        return []

    if not question.strip() or top_k < 1:
        return []

    # Authoritative permission check happens in SQLite first.
    reports = get_allowed_reports(client_id)
    allowed_report_ids = [report.report_id for report in reports]

    if not allowed_report_ids:
        return []

    return search_chunks(
        question=question,
        client_id=client_id,
        top_k=top_k,
        allowed_report_ids=allowed_report_ids,
    )
