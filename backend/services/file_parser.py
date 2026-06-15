import io
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from docx import Document
from config import settings


def get_file_extension(filename: str) -> str:
    """Extract and validate the file extension."""
    if "." not in filename:
        raise HTTPException(status_code=400, detail="File has no extension.")
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    return ext


async def extract_text(file: UploadFile) -> str:
    """
    Main dispatcher: reads file bytes and routes to the correct extractor.
    Returns raw extracted text string.
    """
    ext = get_file_extension(file.filename)
    contents = await file.read()

    # Enforce max file size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )

    if ext == "pdf":
        return _extract_pdf(contents)
    elif ext == "docx":
        return _extract_docx(contents)
    elif ext == "txt":
        return _extract_txt(contents)


def _extract_pdf(contents: bytes) -> str:
    """Extract text from all pages of a PDF."""
    reader = PdfReader(io.BytesIO(contents))
    pages_text = []

    for page in reader.pages:
        text = page.extract_text()
        if text:  # Some pages (images-only) return None
            pages_text.append(text.strip())

    if not pages_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from PDF. It may be scanned/image-only."
        )

    return "\n\n".join(pages_text)


def _extract_docx(contents: bytes) -> str:
    """Extract text from all paragraphs of a DOCX file."""
    doc = Document(io.BytesIO(contents))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    if not paragraphs:
        raise HTTPException(
            status_code=422,
            detail="DOCX file appears to be empty."
        )

    return "\n\n".join(paragraphs)


def _extract_txt(contents: bytes) -> str:
    """Decode TXT file with BOM detection and fallback chain."""
    text = None
    
    # 1. Check for UTF-16 BOM (LE or BE)
    if contents.startswith(b"\xff\xfe") or contents.startswith(b"\xfe\xff"):
        try:
            text = contents.decode("utf-16").strip()
        except Exception:
            pass
            
    # 2. Check for UTF-8 BOM
    if text is None and contents.startswith(b"\xef\xbb\xbf"):
        try:
            text = contents.decode("utf-8-sig").strip()
        except Exception:
            pass

    # 3. Fallback to UTF-8 then Latin-1
    if text is None:
        try:
            text = contents.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                text = contents.decode("latin-1").strip()
            except Exception:
                pass

    if not text:
        raise HTTPException(status_code=422, detail="Text file is empty or could not be decoded.")

    return text


def chunk_text(text: str, chunk_size: int = None) -> list[str]:
    """
    Split large text into chunks to stay within Claude's context window.
    For Phase 1 we send only the first chunk (most docs fit).
    Phase 3+ will handle multi-chunk summarization with map-reduce.
    """
    size = chunk_size or settings.CHUNK_SIZE_CHARS
    chunks = []

    for i in range(0, len(text), size):
        chunks.append(text[i:i + size])

    return chunks