
from app.knowledge import get_allowed_reports, split_into_chunks
from app.database import SessionLocal, ReportDB, ReportPermissionDB
from app.vector_store import store_chunks

VALID_CLIENTS = {"C-01", "C-02"}


def sync_all_reports():
    with SessionLocal() as db:
        reports = db.query(ReportDB).all()

        for report in reports:
            permission_rows = (
                db.query(ReportPermissionDB.client_id)
                .filter(
                    ReportPermissionDB.report_id == report.report_id
                )
                .all()
            )

            allowed_clients = sorted({
                row[0]
                for row in permission_rows
                if row[0] in VALID_CLIENTS
            })

            # Public reports should be accessible to both known clients.
            if report.access == "public":
                allowed_clients = sorted(VALID_CLIENTS)

            if not allowed_clients:
                print(f"Skipping {report.report_id}: no authorized clients")
                continue

            chunks = split_into_chunks(report.content)

            store_chunks(
                report_id=report.report_id,
                title=report.title,
                chunks=chunks,
                allowed_clients=allowed_clients,
            )

            print(
                f"Indexed {report.report_id}: "
                f"{len(chunks)} chunks"
            )


if __name__ == "__main__":
    sync_all_reports()
    print("Vector synchronization complete.")
