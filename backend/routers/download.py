from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List
from models.schemas import SingleDocumentSummary
from services.pdf_generator import generate_summary_pdf, generate_table_pdf
from services.csv_generator import generate_summary_csv

router = APIRouter(prefix="/api/v1", tags=["Download"])

class TableRowData(BaseModel):
    id: str
    documentName: str
    summary: str
    keywords: List[str]
    highlights: List[str]

class MultiDownloadRequest(BaseModel):
    data: List[TableRowData]

@router.post(
    "/download/pdf",
    summary="Download single summary as PDF",
    response_class=Response,
)
async def download_pdf(summary: SingleDocumentSummary):
    """Single document → formatted PDF summary."""
    pdf_bytes = generate_summary_pdf(summary.model_dump() if hasattr(summary, "model_dump") else summary.dict())
    filename = summary.title.replace(" ", "_") + "_summary.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post(
    "/download/csv",
    summary="Download summaries as CSV",
    response_class=Response,
)
async def download_csv(request: MultiDownloadRequest):
    """Multiple documents → CSV table download."""
    if not request.data:
        raise HTTPException(
            status_code=400,
            detail="No data provided for CSV download."
        )

    summaries = []
    for row in request.data:
        summaries.append({
            "name": row.documentName,
            "summary": row.summary,
            "keywords": row.keywords,
            "highlights": row.highlights
        })

    csv_bytes = generate_summary_csv(summaries)

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="document_summaries.csv"'}
    )


@router.post(
    "/download/table-pdf",
    summary="Download summaries as PDF table",
    response_class=Response,
)
async def download_table_pdf(request: MultiDownloadRequest):
    """
    Multiple documents → beautifully formatted PDF table.
    Each row = one document with name, summary, keywords, highlights.
    """
    if not request.data:
        raise HTTPException(
            status_code=400,
            detail="No data provided for table PDF download."
        )

    summaries = []
    for row in request.data:
        summaries.append({
            "name": row.documentName,
            "summary": row.summary,
            "keywords": row.keywords,
            "highlights": row.highlights
        })

    pdf_bytes = generate_table_pdf(summaries)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="document_summaries_table.pdf"'
        }
    )