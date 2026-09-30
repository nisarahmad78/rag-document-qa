"""Persistent storage: ChromaDB collection + a small JSON document registry.

ChromaDB stores the chunk vectors and text. A JSON registry keeps one
record per uploaded document (filename, chunk count, upload time) so the
document list stays cheap to serve.
"""
import json
import threading
from datetime import datetime, timezone

import chromadb

from .config import settings

_lock = threading.Lock()
_client = None
_collection = None

COLLECTION_NAME = "documents"


def get_collection():
    global _client, _collection
    if _collection is None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _registry_path():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir / "documents.json"


def _load_registry() -> dict:
    path = _registry_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_registry(registry: dict) -> None:
    _registry_path().write_text(json.dumps(registry, indent=2), encoding="utf-8")


def register_document(doc_id: str, filename: str, chunk_count: int) -> dict:
    record = {
        "id": doc_id,
        "filename": filename,
        "chunks": chunk_count,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    with _lock:
        registry = _load_registry()
        registry[doc_id] = record
        _save_registry(registry)
    return record


def list_documents() -> list[dict]:
    with _lock:
        registry = _load_registry()
    return sorted(registry.values(), key=lambda d: d["uploaded_at"])


def remove_document(doc_id: str) -> bool:
    with _lock:
        registry = _load_registry()
        if doc_id not in registry:
            return False
        del registry[doc_id]
        _save_registry(registry)
    get_collection().delete(where={"doc_id": doc_id})
    return True
