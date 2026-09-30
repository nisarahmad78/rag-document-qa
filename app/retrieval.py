"""Retrieval: semantic search over the stored document chunks."""
from . import store
from .embeddings import embed_query

DEFAULT_TOP_K = 4


def search(question: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """Return the most relevant chunks for a question, best match first."""
    collection = store.get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[embed_query(question)],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for text, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append(
            {
                "text": text,
                "filename": meta.get("filename", "unknown"),
                "doc_id": meta.get("doc_id", ""),
                "chunk_index": meta.get("chunk_index", 0),
                # Cosine distance -> similarity score in [0, 1], higher is better.
                "score": round(1 - distance, 4),
            }
        )
    return hits
