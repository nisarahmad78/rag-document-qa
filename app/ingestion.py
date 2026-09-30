"""Document ingestion: text extraction, chunking, embedding, storage.

Supported inputs: PDF and plain text. Text is split into overlapping
chunks so that retrieval can return focused passages while keeping
enough surrounding context for the LLM.
"""
import io
import uuid

from . import store
from .embeddings import embed_texts

CHUNK_SIZE = 1000      # characters per chunk
CHUNK_OVERLAP = 200    # characters shared between consecutive chunks


def extract_text(filename: str, raw: bytes) -> str:
    """Extract plain text from an uploaded file."""
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    if name.endswith(".txt") or name.endswith(".md"):
        return raw.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {filename}. Please upload a PDF or TXT file.")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character chunks, preferring paragraph breaks."""
    text = "\n".join(line.strip() for line in text.splitlines())
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 <= chunk_size:
            current = f"{current}\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            # A single paragraph longer than chunk_size is hard-split with overlap.
            while len(para) > chunk_size:
                chunks.append(para[:chunk_size])
                para = para[chunk_size - overlap:]
            current = para
    if current:
        chunks.append(current)
    return [c for c in chunks if c.strip()]


def ingest_document(filename: str, raw: bytes) -> dict:
    """Full ingestion pipeline for one uploaded file. Returns the document record."""
    text = extract_text(filename, raw)
    if not text.strip():
        raise ValueError("No readable text found in the uploaded file.")

    chunks = chunk_text(text)
    doc_id = uuid.uuid4().hex[:12]
    embeddings = embed_texts(chunks)

    collection = store.get_collection()
    collection.add(
        ids=[f"{doc_id}-{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {"doc_id": doc_id, "filename": filename, "chunk_index": i}
            for i in range(len(chunks))
        ],
    )
    return store.register_document(doc_id, filename, len(chunks))
