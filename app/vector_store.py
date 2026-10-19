
import chromadb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DB_PATH = BASE_DIR / "data" / "chroma_db"
VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))

collection = client.get_or_create_collection(
    name="project_atlas_reports",
    metadata={"hnsw:space": "cosine"},
)


def store_chunks(
    report_id: str,
    title: str,
    chunks: list[str],
    allowed_clients: list[str],
):
    if not chunks:
        return

    collection.upsert(
        ids=[f"{report_id}-chunk-{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[
            {
                "report_id": report_id,
                "title": title,
                "chunk_id": i,
                "allowed_clients": ",".join(sorted(set(allowed_clients))),
            }
            for i in range(len(chunks))
        ],
    )


def search_chunks(
    question: str,
    client_id: str,
    top_k: int = 3,
    allowed_report_ids: list[str] | None = None,
) -> list[dict]:
    if not question.strip() or top_k < 1:
        return []

    # Never search without an explicit authorized report list.
    if not allowed_report_ids:
        return []

    # Use exact report IDs obtained from the permission-checked database.
    authorized_ids = sorted(set(allowed_report_ids))
    matches = []

    for report_id in authorized_ids:
        result = collection.query(
            query_texts=[question],
            n_results=1,
            where={"report_id": report_id},
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for document, metadata, distance in zip(
            documents, metadatas, distances
        ):
            # Defense in depth: verify stored metadata too.
            allowed = set(
                metadata.get("allowed_clients", "").split(",")
            )
            if client_id not in allowed:
                continue

            matches.append({
                "report_id": metadata["report_id"],
                "title": metadata["title"],
                "chunk_id": metadata["chunk_id"],
                "content": document,
                "score": round(1 - distance, 4),
            })

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:top_k]
