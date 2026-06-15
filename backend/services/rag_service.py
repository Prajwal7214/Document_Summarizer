import uuid
import time
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from fastapi import HTTPException
from config import settings
from services.file_parser import chunk_text
from services.ai_client import call_ai_with_fallback

# Embedding model (local, no API)
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model loaded")

vector_store: dict = {}

RAG_PROMPT = """You are a precise document assistant. Answer the user's question exactly as requested.

CRITICAL RULES:
- If user asks for EXACT text, quotes, or original content → copy it VERBATIM from context, word for word
- If user asks to summarize → give a summarized version
- If user asks a question → answer it directly
- NEVER paraphrase when user wants exact/original text
- NEVER summarize when user asks for exact content

How to detect what user wants:
- "exact", "original", "verbatim", "word for word", "copy", "paste" → return EXACT text from document
- "summarize", "brief", "short", "overview", "gist" → return summarized version
- "what is", "explain", "tell me" → return clear explanation
- "extract", "give me the abstract/introduction/conclusion" → return EXACT section from document

Context from document:
---
{context}
---

User Question: {question}

Important: If the user wants exact text and it exists in the context above, copy it exactly as it appears. Do not change a single word.

Answer:"""


def create_embeddings(texts: list[str]) -> np.ndarray:
    embeddings = embedding_model.encode(
        texts, show_progress_bar=False, convert_to_numpy=True
    )
    return embeddings.astype("float32")


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index


def chunk_text_with_overlap(text: str, chunk_size: int = 800, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks so sections aren't cut in half."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def search_similar_chunks(query: str, document_id: str, top_k: int = 5) -> list[str]:
    if document_id not in vector_store:
        raise HTTPException(
            status_code=404,
            detail=f"Document ID '{document_id}' not found. Please ingest first."
        )
    store = vector_store[document_id]
    query_embedding = create_embeddings([query])
    distances, indices = store["index"].search(
        query_embedding, min(top_k, len(store["chunks"]))
    )

    # Get valid chunk indices and SORT them by document order
    # so the context reads naturally instead of being jumbled
    valid_indices = sorted([i for i in indices[0] if i < len(store["chunks"])])
    return [store["chunks"][i] for i in valid_indices]


async def ingest_document(filename: str, text: str) -> dict:
    """Ingest document — no API call, runs locally."""
    # Use overlapping chunks so sections don't get split
    chunks = chunk_text_with_overlap(text, chunk_size=800, overlap=200)
    if not chunks:
        raise HTTPException(status_code=422, detail="Could not extract chunks.")

    embeddings = create_embeddings(chunks)
    index = build_faiss_index(embeddings)
    document_id = str(uuid.uuid4())[:8]

    vector_store[document_id] = {
        "index": index,
        "chunks": chunks,
        "filename": filename,
        "full_text": text,  # Store full text for section-level queries
    }

    return {
        "document_id": document_id,
        "chunks_stored": len(chunks),
        "filename": filename,
    }


# Map of section names to regex patterns that find them in academic papers
SECTION_PATTERNS = {
    "abstract": r'(?i)(?:^|\n)\s*abstract\s*[\n:.]\s*([\s\S]*?)(?=\n\s*(?:1[\.\s]|I[\.\s]|introduction|keywords|index terms|(?:\n\s*\n)))',
    "introduction": r'(?i)(?:^|\n)\s*(?:1[\.\s]*)?introduction\s*[\n:.]\s*([\s\S]*?)(?=\n\s*(?:2[\.\s]|II[\.\s]|related work|background|literature|methodology|method))',
    "conclusion": r'(?i)(?:^|\n)\s*(?:\d+[\.\s]*)?conclusions?\s*[\n:.]\s*([\s\S]*?)(?=\n\s*(?:\d+[\.\s]*)?(?:references|acknowledgment|appendix|$))',
    "methodology": r'(?i)(?:^|\n)\s*(?:\d+[\.\s]*)?(?:methodology|methods?|approach)\s*[\n:.]\s*([\s\S]*?)(?=\n\s*(?:\d+[\.\s]*)?(?:results|experiments?|evaluation|discussion))',
    "results": r'(?i)(?:^|\n)\s*(?:\d+[\.\s]*)?(?:results?|experiments?|evaluation)\s*[\n:.]\s*([\s\S]*?)(?=\n\s*(?:\d+[\.\s]*)?(?:discussion|conclusion|limitations|future))',
    "discussion": r'(?i)(?:^|\n)\s*(?:\d+[\.\s]*)?discussion\s*[\n:.]\s*([\s\S]*?)(?=\n\s*(?:\d+[\.\s]*)?(?:conclusion|references|acknowledgment|future))',
    "references": r'(?i)(?:^|\n)\s*(?:\d+[\.\s]*)?references\s*[\n:.]\s*([\s\S]*?)$',
    "background": r'(?i)(?:^|\n)\s*(?:\d+[\.\s]*)?(?:background|related work|literature review)\s*[\n:.]\s*([\s\S]*?)(?=\n\s*(?:\d+[\.\s]*)?(?:method|approach|proposed|system|framework))',
}


def _detect_requested_section(question: str) -> str | None:
    """Return the section name if the user is asking for a specific section, else None."""
    q_lower = question.lower()
    for section_name in SECTION_PATTERNS:
        if section_name in q_lower:
            return section_name
    return None


def _extract_section_from_text(full_text: str, section_name: str) -> str | None:
    """Extract a section directly from the full document text using regex."""
    import re
    pattern = SECTION_PATTERNS.get(section_name)
    if not pattern:
        return None

    match = re.search(pattern, full_text)
    if match:
        extracted = match.group(1).strip()
        if len(extracted) > 30:  # Must be meaningful content
            return extracted

    # Fallback: simple split-based extraction
    # Find the section header and grab everything until the next likely header
    lines = full_text.split('\n')
    capturing = False
    captured = []
    for line in lines:
        line_lower = line.strip().lower()
        # Check if this line IS the section header
        if not capturing and section_name in line_lower and len(line.strip()) < 80:
            capturing = True
            continue
        # If capturing, check if we hit the NEXT section header
        if capturing:
            # Stop if we hit a line that looks like a new section header
            if (line.strip() and len(line.strip()) < 80 and
                any(s in line_lower for s in [
                    "abstract", "introduction", "conclusion", "methodology",
                    "method", "results", "discussion", "references",
                    "acknowledgment", "appendix", "background", "related work"
                ]) and line_lower != section_name):
                break
            captured.append(line)

    result = '\n'.join(captured).strip()
    return result if len(result) > 30 else None


def _is_exact_text_request(question: str) -> bool:
    """Detect if user wants exact/verbatim text."""
    exact_keywords = [
        "exact", "verbatim", "word for word", "original",
        "copy", "same", "as it is", "actual",
        "give me the", "extract the", "show me the",
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in exact_keywords)


async def chat_with_document(document_id: str, question: str) -> dict:
    """Answer question using RAG with fallback AI."""

    if document_id not in vector_store:
        raise HTTPException(
            status_code=404,
            detail=f"Document ID '{document_id}' not found. Please ingest first."
        )

    store = vector_store[document_id]
    full_text = store.get("full_text", "")

    # ── STEP 1: Try DIRECT extraction (no AI, returns exact text) ──
    requested_section = _detect_requested_section(question)
    if requested_section and (_is_exact_text_request(question) or requested_section == "abstract"):
        extracted = _extract_section_from_text(full_text, requested_section)
        if extracted:
            return {
                "document_id": document_id,
                "question": question,
                "answer": extracted,
                "sources": [f"[Extracted directly from document — {requested_section} section]"],
            }

    # ── STEP 2: For section requests that need AI help, send full text ──
    if requested_section:
        if len(full_text) <= 12000:
            context = full_text
        else:
            relevant_chunks = search_similar_chunks(question, document_id, top_k=10)
            context = "\n\n".join(relevant_chunks)
    else:
        # ── STEP 3: Normal Q&A — use RAG chunks ──
        relevant_chunks = search_similar_chunks(question, document_id, top_k=5)
        if not relevant_chunks:
            raise HTTPException(status_code=404, detail="No relevant content found.")
        context = "\n\n".join(relevant_chunks)

    prompt = RAG_PROMPT.format(context=context, question=question)
    answer = call_ai_with_fallback(prompt)

    # If the response is wrapped in JSON (due to system prompt constraints), extract the clean answer
    cleaned_answer = answer.strip()
    if cleaned_answer.startswith("{") and cleaned_answer.endswith("}"):
        import json
        try:
            parsed = json.loads(cleaned_answer)
            if isinstance(parsed, dict):
                for key in ["answer", "response", "output"]:
                    if key in parsed:
                        cleaned_answer = str(parsed[key])
                        break
        except Exception:
            pass

    sources = search_similar_chunks(question, document_id, top_k=3)

    return {
        "document_id": document_id,
        "question": question,
        "answer": cleaned_answer,
        "sources": sources
    }


def list_documents() -> list[dict]:
    return [
        {"document_id": doc_id, "filename": data["filename"], "chunks": len(data["chunks"])}
        for doc_id, data in vector_store.items()
    ]


def delete_document(document_id: str) -> bool:
    if document_id not in vector_store:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    del vector_store[document_id]
    return True