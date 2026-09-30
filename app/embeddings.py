"""Local embedding model wrapper (sentence-transformers).

The model is loaded lazily on first use and kept in memory for the life of
the process. Default model: all-MiniLM-L6-v2 (384-dim, fast, runs on CPU,
no API key required). It is downloaded once (~90 MB) and cached by
sentence-transformers.
"""
from functools import lru_cache

from .config import settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, returning plain Python lists for ChromaDB."""
    vectors = _model().encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
