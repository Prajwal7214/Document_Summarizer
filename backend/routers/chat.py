from fastapi import APIRouter, UploadFile, File
from services.file_parser import extract_text
from services.rag_service import (
    ingest_document,
    chat_with_document,
    list_documents,
    delete_document
)
from models.schemas import IngestResponse, ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1/chat", tags=["Chat with Document (RAG)"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Upload document → Store in vector DB for chatting",
)
async def ingest(file: UploadFile = File(...)):
    """
    Phase 5 Step 1: Upload and process document for RAG.

    - Extracts text from PDF/DOCX/TXT
    - Splits into chunks
    - Creates embeddings (locally, no API)
    - Stores in FAISS vector index
    - Returns document_id — use this to chat!
    """
    text = await extract_text(file)
    result = await ingest_document(file.filename, text)

    return IngestResponse(
        status="success",
        document_id=result["document_id"],
        filename=result["filename"],
        chunks_stored=result["chunks_stored"],
        message=f"Document ingested successfully! Use document_id '{result['document_id']}' to chat."
    )


@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Ask a question about an ingested document",
)
async def ask(request: ChatRequest):
    """
    Phase 5 Step 2: Ask a question about your document.

    - Send document_id from /ingest step
    - Ask any question about the document
    - Gets answer based ONLY on document content

    Example:
    {
        "document_id": "abc12345",
        "question": "What are the main findings of this paper?"
    }
    """
    result = await chat_with_document(request.document_id, request.question)
    return ChatResponse(**result)


@router.get(
    "/documents",
    summary="List all ingested documents in current session",
)
async def get_documents():
    """
    Returns all documents currently stored in vector DB.
    Note: Clears when server restarts (in-memory storage).
    """
    docs = list_documents()
    return {
        "total": len(docs),
        "documents": docs
    }


@router.delete(
    "/documents/{document_id}",
    summary="Remove a document from vector store",
)
async def remove_document(document_id: str):
    """Delete a document from the vector store by its ID."""
    delete_document(document_id)
    return {
        "status": "success",
        "message": f"Document '{document_id}' removed successfully."
    }