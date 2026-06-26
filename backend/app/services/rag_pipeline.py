"""
Simple RAG pipeline: PDF → extract → chunk → embed → index → query → answer.

Each step is a separate function so you can run or test them independently.
Uses OpenAI for embeddings + LLM; vectors are stored in an in-memory index.
"""

from __future__ import annotations

import logging
import pickle
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from openai import OpenAI
from pypdf import PdfReader

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_TOP_K = 4
INDEXABLE_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm"}


@dataclass
class TextChunk:
    """A slice of document text with metadata for retrieval."""

    text: str
    chunk_id: int
    source: str


@dataclass
class VectorIndex:
    """In-memory index: chunks + embedding matrix for cosine search."""

    chunks: list[TextChunk] = field(default_factory=list)
    embeddings: np.ndarray | None = None


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """
    Step 1 — Extract text from a PDF file.

    Reads every page and joins the text with newlines.
    """
    path = Path(pdf_path)
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _get_client() -> OpenAI:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for the RAG pipeline")
    return OpenAI(api_key=settings.openai_api_key)


def is_rag_supported(filename: str) -> bool:
    """Return True if the file type can be ingested by the RAG pipeline."""
    return Path(filename).suffix.lower() in INDEXABLE_EXTENSIONS


def extract_text_from_file(file_path: str | Path) -> str:
    """Extract text from PDF or plain-text files."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def index_path_for(file_id: uuid.UUID) -> Path:
    """Disk path where a file's vector index is stored."""
    return Path(settings.rag_index_dir) / f"{file_id}.pkl"


def save_index(index: VectorIndex, path: Path) -> None:
    """Persist a vector index to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump({"chunks": index.chunks, "embeddings": index.embeddings}, f)


def load_index(path: Path) -> VectorIndex | None:
    """Load a vector index from disk; return None if missing."""
    if not path.exists():
        return None
    with open(path, "rb") as f:
        data = pickle.load(f)
    return VectorIndex(chunks=data["chunks"], embeddings=data["embeddings"])


def merge_indices(indices: list[VectorIndex]) -> VectorIndex:
    """Combine multiple indexes into one searchable index."""
    all_chunks: list[TextChunk] = []
    embedding_rows: list[np.ndarray] = []
    for index in indices:
        if index.embeddings is not None and index.chunks:
            all_chunks.extend(index.chunks)
            embedding_rows.append(index.embeddings)
    if not all_chunks:
        return VectorIndex()
    return VectorIndex(chunks=all_chunks, embeddings=np.vstack(embedding_rows))


def chunk_text(
    text: str,
    *,
    source: str = "",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """
    Step 2 — Split extracted text into overlapping chunks.

    Uses a sliding window so context isn't lost at chunk boundaries.
    """
    if not text.strip():
        return []

    chunks: list[TextChunk] = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(TextChunk(text=chunk, chunk_id=chunk_id, source=source))
            chunk_id += 1
        if end >= len(text):
            break
        start = end - chunk_overlap

    return chunks


def embed_texts(texts: list[str], *, client: OpenAI | None = None) -> np.ndarray:
    """
    Step 3 — Embedding: convert text into vectors.

    Returns a (n, dim) float32 matrix of embeddings.
    """
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    client = client or _get_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    vectors = [item.embedding for item in response.data]
    return np.array(vectors, dtype=np.float32)


def build_index(chunks: list[TextChunk], *, client: OpenAI | None = None) -> VectorIndex:
    """
    Step 4 — Indexing: embed chunks and store them for fast search.
    """
    if not chunks:
        return VectorIndex()

    client = client or _get_client()
    texts = [chunk.text for chunk in chunks]
    embeddings = embed_texts(texts, client=client)
    return VectorIndex(chunks=chunks, embeddings=embeddings)


def embed_question(question: str, *, client: OpenAI | None = None) -> np.ndarray:
    """
    Step 5 — Embed the user's question (same model as document chunks).
    """
    client = client or _get_client()
    matrix = embed_texts([question], client=client)
    return matrix[0]


def search_index(
    index: VectorIndex,
    query_vector: np.ndarray,
    *,
    top_k: int = DEFAULT_TOP_K,
) -> list[tuple[TextChunk, float]]:
    """
    Step 6 — Search the index with cosine similarity; return top matches.
    """
    if index.embeddings is None or len(index.chunks) == 0:
        return []

    # Cosine similarity: dot product of normalized vectors.
    query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-10)
    doc_norms = index.embeddings / (
        np.linalg.norm(index.embeddings, axis=1, keepdims=True) + 1e-10
    )
    scores = doc_norms @ query_norm

    k = min(top_k, len(index.chunks))
    top_indices = np.argsort(scores)[::-1][:k]

    return [(index.chunks[i], float(scores[i])) for i in top_indices]


def retrieve_top_k(
    index: VectorIndex,
    question: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    client: OpenAI | None = None,
) -> list[TextChunk]:
    """
    Step 7 — Embed question and return the top K chunks.
    """
    query_vector = embed_question(question, client=client)
    results = search_index(index, query_vector, top_k=top_k)
    return [chunk for chunk, _ in results]


def generate_answer(
    question: str,
    chunks: list[TextChunk],
    *,
    client: OpenAI | None = None,
) -> str:
    """
    Step 8 — LLM: answer the question using retrieved chunks as context.
    """
    client = client or _get_client()

    if not chunks:
        context = "No relevant context was found in the document."
    else:
        context = "\n\n---\n\n".join(
            f"[Chunk {chunk.chunk_id}]\n{chunk.text}" for chunk in chunks
        )

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer the question using only the provided context. "
                    "If the context doesn't contain the answer, say so."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    return response.choices[0].message.content or ""


def ingest_file(
    file_path: str | Path,
    *,
    source: str = "",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    client: OpenAI | None = None,
) -> VectorIndex:
    """
    Ingestion pipeline: file → extract → chunk → embed → index.
    """
    path = Path(file_path)
    text = extract_text_from_file(path)
    chunks = chunk_text(
        text,
        source=source or path.name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    logger.info("Ingested %s: %d chunks", path.name, len(chunks))
    return build_index(chunks, client=client)


def ingest_and_save(file_path: Path, file_id: uuid.UUID) -> VectorIndex | None:
    """Ingest a file and persist its index; return None on failure."""
    try:
        index = ingest_file(file_path, source=file_path.name)
        save_index(index, index_path_for(file_id))
        return index
    except Exception:
        logger.exception("Failed to index file %s", file_id)
        return None


def load_or_ingest_index(file_path: Path, file_id: uuid.UUID) -> VectorIndex | None:
    """Load a saved index, or build one on demand if missing."""
    saved = load_index(index_path_for(file_id))
    if saved is not None:
        return saved
    if not file_path.exists() or not settings.openai_api_key:
        return None
    return ingest_and_save(file_path, file_id)


def ingest_pdf(
    pdf_path: str | Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    client: OpenAI | None = None,
) -> VectorIndex:
    """
    Ingestion pipeline: PDF → extract → chunk → embed → index.
    """
    path = Path(pdf_path)
    text = extract_text_from_pdf(path)
    chunks = chunk_text(text, source=path.name, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    logger.info("Ingested %s: %d chunks", path.name, len(chunks))
    return build_index(chunks, client=client)


def rag_query(
    index: VectorIndex,
    question: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    client: OpenAI | None = None,
) -> str:
    """
    Full query pipeline: embed question → search → top K → LLM answer.
    """
    chunks = retrieve_top_k(index, question, top_k=top_k, client=client)
    return generate_answer(question, chunks, client=client)
