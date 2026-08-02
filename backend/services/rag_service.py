import uuid
import numpy as np
import re
import asyncio
from typing import Optional
from sentence_transformers import SentenceTransformer
from fastapi import HTTPException
from config import settings
from services.ai_client import call_ai_with_fallback
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

_embedding_model: Optional[SentenceTransformer] = None
_qdrant_client: Optional[QdrantClient] = None

def get_qdrant() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        api_key = settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        if settings.QDRANT_URL:
            print("Connecting to Qdrant server...")
            _qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=api_key
            )
        else:
            print("Connecting to local Qdrant (disk)...")
            _qdrant_client = QdrantClient(path="local_qdrant")
    return _qdrant_client

def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        print("Loading embedding model on first use...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model loaded and cached.")
    return _embedding_model

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

def create_embeddings(texts: list[str]) -> list[list[float]]:
    embeddings = get_embedding_model().encode(
        texts, show_progress_bar=False, convert_to_numpy=True
    )
    return embeddings.tolist()

def chunk_text_with_overlap(text: str, chunk_size: int = 800, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks

def get_full_text(document_id: str) -> str:
    client = get_qdrant()
    collection_name = f"doc_{document_id}"
    try:
        if hasattr(client, "collection_exists") and not client.collection_exists(collection_name):
            return ""
        points = client.retrieve(
            collection_name=collection_name,
            ids=[0],
            with_payload=True
        )
        if points and points[0].payload:
            return points[0].payload.get("full_text", "")
    except Exception as e:
        print(f"Error retrieving full text for {collection_name}: {e}")
    return ""

def search_similar_chunks(query: str, document_id: str, top_k: int = 5) -> list[str]:
    client = get_qdrant()
    query_embedding = create_embeddings([query])[0]
    collection_name = f"doc_{document_id}"
    
    try:
        if hasattr(client, "collection_exists") and not client.collection_exists(collection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Document ID '{document_id}' not found. Please upload or ingest the document first."
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Warning checking collection existence: {e}")

    try:
        if hasattr(client, "query_points"):
            res = client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=top_k
            )
            hits = res.points
        else:
            hits = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Qdrant search error for {collection_name}: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Document ID '{document_id}' search failed: {str(e)}"
        )
    
    sorted_hits = sorted(hits, key=lambda x: x.payload.get("chunk_index", 0) if x.payload else 0)
    return [hit.payload["text"] for hit in sorted_hits if hit.payload and "text" in hit.payload]

async def ingest_document(filename: str, text: str) -> dict:
    chunks = chunk_text_with_overlap(text, chunk_size=800, overlap=200)
    if not chunks:
        raise HTTPException(status_code=422, detail="Could not extract chunks.")

    embeddings = create_embeddings(chunks)
    document_id = str(uuid.uuid4())[:8]
    collection_name = f"doc_{document_id}"

    client = get_qdrant()
    
    try:
        if hasattr(client, "collection_exists") and client.collection_exists(collection_name):
            client.delete_collection(collection_name)
    except Exception:
        pass

    if hasattr(client, "create_collection"):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE),
        )
    else:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE),
        )

    points = [
        PointStruct(
            id=i,
            vector=emb,
            payload={"text": chunk, "chunk_index": i, "filename": filename, "full_text": text if i == 0 else ""}
        )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]
    
    client.upsert(
        collection_name=collection_name,
        wait=True,
        points=points
    )

    return {
        "document_id": document_id,
        "chunks_stored": len(chunks),
        "filename": filename,
    }

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
    q_lower = question.lower()
    for section_name in SECTION_PATTERNS:
        if section_name in q_lower:
            return section_name
    return None

def _extract_section_from_text(full_text: str, section_name: str) -> str | None:
    if not full_text: return None
    pattern = SECTION_PATTERNS.get(section_name)
    if not pattern: return None

    match = re.search(pattern, full_text)
    if match:
        extracted = match.group(1).strip()
        if len(extracted) > 30: return extracted

    lines = full_text.split('\n')
    capturing = False
    captured = []
    for line in lines:
        line_lower = line.strip().lower()
        if not capturing and section_name in line_lower and len(line.strip()) < 80:
            capturing = True
            continue
        if capturing:
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
    exact_keywords = [
        "exact", "verbatim", "word for word", "original",
        "copy", "same", "as it is", "actual",
        "give me the", "extract the", "show me the",
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in exact_keywords)

async def chat_with_document(document_id: str, question: str) -> dict:
    full_text = get_full_text(document_id)
    if not full_text:
        # Check if collection exists
        try:
            get_qdrant().get_collection(f"doc_{document_id}")
        except:
            raise HTTPException(
                status_code=404,
                detail=f"Document ID '{document_id}' not found. Please ingest first."
            )

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

    if requested_section:
        if len(full_text) <= 12000 and full_text:
            context = full_text
        else:
            relevant_chunks = search_similar_chunks(question, document_id, top_k=10)
            context = "\n\n".join(relevant_chunks)
    else:
        relevant_chunks = search_similar_chunks(question, document_id, top_k=5)
        if not relevant_chunks:
            raise HTTPException(status_code=404, detail="No relevant content found.")
        context = "\n\n".join(relevant_chunks)

    prompt = RAG_PROMPT.format(context=context, question=question)
    answer = await call_ai_with_fallback(prompt)

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
    # Qdrant doesn't easily list collections named doc_* with chunk counts in a single query unless we iterate.
    # To avoid a huge query, we can just list collections.
    client = get_qdrant()
    collections = client.get_collections().collections
    result = []
    for col in collections:
        if col.name.startswith("doc_"):
            doc_id = col.name[4:]
            try:
                info = client.get_collection(col.name)
                result.append({"document_id": doc_id, "filename": f"Document {doc_id}", "chunks": info.vectors_count})
            except:
                pass
    return result

def delete_document(document_id: str) -> bool:
    client = get_qdrant()
    try:
        client.delete_collection(collection_name=f"doc_{document_id}")
        return True
    except Exception:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")