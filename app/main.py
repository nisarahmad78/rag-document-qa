"""RAG Document Q&A — FastAPI application.

Run locally:
    uvicorn app.main:app --reload

Endpoints:
    GET    /health            service health + LLM configuration status
    POST   /documents         upload a PDF or TXT document (multipart form)
    GET    /documents         list uploaded documents
    DELETE /documents/{id}    remove a document and its chunks
    POST   /ask               ask a question -> answer + source chunks
    GET    /                  web UI (static)
"""
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import ingestion, llm_client, retrieval, store
from .config import settings

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_FILE_MB = 20

app = FastAPI(
    title="RAG Document Q&A",
    description="Upload documents and ask questions answered from their content (Retrieval-Augmented Generation).",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=retrieval.DEFAULT_TOP_K, ge=1, le=10)


class Source(BaseModel):
    filename: str
    chunk_index: int
    score: float
    text: str


class AskResponse(BaseModel):
    answer: str
    llm_configured: bool
    sources: list[Source]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_configured": settings.llm_configured,
        "llm_model": settings.llm_model if settings.llm_configured else None,
        "embedding_model": settings.embedding_model,
        "documents": len(store.list_documents()),
    }


@app.post("/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    raw = await file.read()
    if len(raw) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_MB} MB).")
    try:
        record = ingestion.ingest_document(file.filename, raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return record


@app.get("/documents")
def list_documents():
    return {"documents": store.list_documents()}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    if not store.remove_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"deleted": doc_id}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    sources = retrieval.search(payload.question, top_k=payload.top_k)
    if not sources:
        return AskResponse(
            answer="No documents have been uploaded yet, or no relevant content was found. "
                   "Please upload a document first.",
            llm_configured=settings.llm_configured,
            sources=[],
        )
    try:
        answer = llm_client.generate_answer(payload.question, sources)
    except llm_client.LLMNotConfigured as exc:
        # Retrieval still succeeded — return the sources with a clear notice.
        answer = str(exc)
    return AskResponse(
        answer=answer,
        llm_configured=settings.llm_configured,
        sources=[
            Source(filename=s["filename"], chunk_index=s["chunk_index"], score=s["score"], text=s["text"])
            for s in sources
        ],
    )


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
