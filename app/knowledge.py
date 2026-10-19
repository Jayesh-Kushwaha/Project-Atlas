
from dataclasses import dataclass

from app.database import (
    SessionLocal,
    ReportDB,
    ReportPermissionDB,
    init_db,
)


@dataclass
class Report:
    report_id: str
    title: str
    access: str
    content: str


@dataclass
class ReportChunk:
    report_id: str
    title: str
    chunk_id: int
    content: str


VALID_CLIENTS = {"C-01", "C-02"}


# Initial reports are inserted only when the database is empty.
INITIAL_REPORTS = [
    Report(
        report_id="R-101",
        title="Global Smart Water Meter Market 2025",
        access="paid",
        content=(
            "Global smart water meter market in 2024 was "
            "$4.21 billion, covering hardware, software and services. "
            "The reported CAGR for 2025-2030 is 11.2%. "
            "APAC accounted for 38% of the market."
        ),
    ),
    Report(
        report_id="R-102",
        title="Smart Water Metering Industry Outlook 2024",
        access="public",
        content=(
            "The public report excerpt estimates the 2024 global "
            "smart water metering hardware-only market at $3.87 billion. "
            "The reported CAGR for 2024-2029 is 9.8%. "
            "APAC accounted for 41% of the market. "
            "These figures cover hardware only, unlike reports that "
            "include software and services."
        ),
    ),
    Report(
        report_id="R-103",
        title="Residential Water Purifier Market 2025",
        access="paid",
        content=(
            "This report covers the residential water purifier market. "
            "Detailed market figures must be added from the source report "
            "before numerical answers can be provided."
        ),
    ),
]


def split_into_chunks(
    text: str,
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Overlap helps preserve context between adjacent chunks.
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size"
        )

    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - overlap

    return chunks


def seed_initial_reports():
    """Insert the initial reports and their permissions once."""

    with SessionLocal() as db:
        if db.query(ReportDB).first():
            return

        for report in INITIAL_REPORTS:
            db.add(
                ReportDB(
                    report_id=report.report_id,
                    title=report.title,
                    access=report.access,
                    content=report.content,
                )
            )

            if report.access == "public":
                permitted_clients = VALID_CLIENTS
            elif report.report_id == "R-101":
                permitted_clients = {"C-01"}
            elif report.report_id == "R-103":
                permitted_clients = {"C-01", "C-02"}
            else:
                permitted_clients = set()

            for client_id in permitted_clients:
                db.add(
                    ReportPermissionDB(
                        client_id=client_id,
                        report_id=report.report_id,
                    )
                )

        db.commit()


def get_allowed_reports(client_id: str) -> list[Report]:
    """Return only reports this client is authorized to access."""

    if client_id not in VALID_CLIENTS:
        return []

    with SessionLocal() as db:
        rows = (
            db.query(ReportDB)
            .join(
                ReportPermissionDB,
                ReportDB.report_id
                == ReportPermissionDB.report_id,
            )
            .filter(
                ReportPermissionDB.client_id == client_id
            )
            .all()
        )

        return [
            Report(
                report_id=row.report_id,
                title=row.title,
                access=row.access,
                content=row.content,
            )
            for row in rows
        ]


def add_report(
    report: Report,
    allowed_clients: list[str],
) -> None:
    """Save a report and assign access permissions."""

    if report.access not in {"public", "paid"}:
        raise ValueError("Invalid report access type")

    if not report.report_id.strip():
        raise ValueError("Report ID cannot be empty")

    if not report.title.strip():
        raise ValueError("Report title cannot be empty")

    if not report.content.strip():
        raise ValueError("Report content cannot be empty")

    if not set(allowed_clients).issubset(VALID_CLIENTS):
        raise ValueError("Invalid client ID")

    if report.access == "paid" and not allowed_clients:
        raise ValueError(
            "Paid reports require at least one authorized client"
        )

    with SessionLocal() as db:
        existing = db.get(ReportDB, report.report_id)

        if existing is not None:
            raise ValueError(
                f"Report ID already exists: {report.report_id}"
            )

        db.add(
            ReportDB(
                report_id=report.report_id,
                title=report.title,
                access=report.access,
                content=report.content,
            )
        )

        if report.access == "public":
            permitted_clients = VALID_CLIENTS
        else:
            permitted_clients = set(allowed_clients)

        for client_id in permitted_clients:
            db.add(
                ReportPermissionDB(
                    client_id=client_id,
                    report_id=report.report_id,
                )
            )

        db.commit()


# Initialize database tables and seed initial reports.
init_db()
seed_initial_reports()
