from pydantic import BaseModel, field_validator
from typing import List, Optional


class SingleDocumentSummary(BaseModel):
    """Single document response schema."""
    title: str
    summary: str
    bullets: List[str]
    highlights: List[str]
    keywords: List[str]
    document_id: Optional[str] = None

    @field_validator("bullets", "highlights", "keywords", mode="before")
    @classmethod
    def coerce_to_list(cls, v):
        """Auto-convert string → [string] if AI returns wrong type."""
        if isinstance(v, str):
            return [v] if v.strip() else []
        return v


class MultiDocumentSummary(BaseModel):
    """One row in the multi-document table response."""
    name: str
    summary: str
    keywords: List[str]
    highlights: List[str]

    @field_validator("keywords", "highlights", mode="before")
    @classmethod
    def coerce_to_list(cls, v):
        """Auto-convert string → [string] if AI returns wrong type."""
        if isinstance(v, str):
            return [v] if v.strip() else []
        return v


class IngestResponse(BaseModel):
    """Response after document is ingested into vector store."""
    status: str
    document_id: str
    filename: str
    chunks_stored: int
    message: str


class ChatRequest(BaseModel):
    """Chat request schema."""
    document_id: str
    question: str


class ChatResponse(BaseModel):
    """Chat response schema."""
    document_id: str
    question: str
    answer: str
    sources: List[str]   # Relevant chunks used to answer