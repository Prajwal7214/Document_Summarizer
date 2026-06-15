from fastapi import APIRouter, UploadFile, File, Query
from typing import List, Literal
from services.file_parser import extract_text
from services.summarizer import summarize_document, summarize_single_for_multi
from services.rag_service import ingest_document
from models.schemas import SingleDocumentSummary, MultiDocumentSummary
import asyncio

router = APIRouter(prefix="/api/v1", tags=["Summarizer"])


def safe_list(val, default: list) -> list:
    """Return val as a list; if it's a string wrap it; if missing use default."""
    if val is None:
        return default
    if isinstance(val, list):
        return val if val else default
    if isinstance(val, str):
        return [val] if val.strip() else default
    return default


@router.post(
    "/summarize",
    response_model=SingleDocumentSummary,
    summary="Upload ONE document → structured summary",
)
async def summarize(
    file: UploadFile = File(...),
    summary_type: Literal["short", "detailed", "academic"] = Query(
        default="detailed",
        description="Type of summary: 'short' (3 bullets), 'detailed' (full), 'academic' (formal abstract)"
    )
):
    """
    Phase 1 + 3: Single file upload with summary type selection.

    - **short**: 1 sentence summary + 3 bullet points
    - **detailed**: Full paragraph + 5 bullet points (default)
    - **academic**: Formal abstract-style + structured bullets
    """
    text = await extract_text(file)
    result = await summarize_document(text, summary_type)
    
    # Ingest document into vector store to support chat feature
    document_id = None
    try:
        ingest_res = await ingest_document(file.filename, text)
        document_id = ingest_res.get("document_id")
    except Exception as e:
        print(f"Warning: Failed to auto-ingest document for chat: {e}")

    result["document_id"] = document_id

    from pydantic import ValidationError
    try:
        return SingleDocumentSummary(**result)
    except ValidationError as e:
        # Provide fallback values for missing/wrong-type fields
        fallback = {
            "title": result.get("title") or "Untitled Document",
            "summary": result.get("summary") or "Summary could not be generated.",
            "bullets": safe_list(result.get("bullets"), ["No key points found."]),
            "highlights": safe_list(result.get("highlights"), ["No highlights found."]),
            "keywords": safe_list(result.get("keywords"), ["N/A"]),
            "document_id": document_id
        }
        return SingleDocumentSummary(**fallback)


@router.post(
    "/summarize-multiple",
    response_model=List[MultiDocumentSummary],
    summary="Upload MULTIPLE documents → table of summaries",
)
async def summarize_multiple(
    files: List[UploadFile] = File(...),
    summary_type: Literal["short", "detailed", "academic"] = Query(
        default="detailed",
        description="Type of summary applied to all documents"
    )
):
    """
    Phase 2 + 3: Multiple file upload with summary type selection.
    Returns array — one row per document.
    """
    if len(files) < 2:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Please upload at least 2 files. For single file use /summarize endpoint."
        )

    if len(files) > 10:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed per request."
        )

    # Extract text from all files
    texts = []
    for file in files:
        text = await extract_text(file)
        texts.append((file.filename, text))

    # Summarize all documents concurrently
    tasks = [
        summarize_single_for_multi(filename, text, summary_type)
        for filename, text in texts
    ]
    results = await asyncio.gather(*tasks)

    from pydantic import ValidationError
    final_results = []
    for result in results:
        try:
            final_results.append(MultiDocumentSummary(**result))
        except ValidationError:
            fallback = {
                "name": result.get("name") or "Unknown Document",
                "summary": result.get("summary") or "Summary could not be generated.",
                "keywords": safe_list(result.get("keywords"), ["N/A"]),
                "highlights": safe_list(result.get("highlights"), ["No highlights found."])
            }
            final_results.append(MultiDocumentSummary(**fallback))

    return final_results