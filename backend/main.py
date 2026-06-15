from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.summarize import router as summarize_router
from routers.download import router as download_router
from routers.chat import router as chat_router
from services.cache_service import get_cache_stats, clear_cache
from fastapi.responses import JSONResponse
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import traceback

# Max total upload size: 10 files × 10 MB each = 100 MB
MAX_UPLOAD_BYTES = 100 * 1024 * 1024

app = FastAPI(
    title="Document Summarizer API",
    description="AI-powered summarization with Gemini + Groq fallback.",
    version="5.1.0"
)


class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    """Reject requests larger than MAX_UPLOAD_BYTES with a proper 413."""
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_UPLOAD_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request too large. Maximum total upload size is {MAX_UPLOAD_BYTES // (1024*1024)} MB."},
                headers={"Access-Control-Allow-Origin": "*"}
            )
        return await call_next(request)

# CORS must be added BEFORE the size-limit middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LimitUploadSizeMiddleware)

app.include_router(summarize_router)
app.include_router(download_router)
app.include_router(chat_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled Exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "*"} # Or explicit origins
    )


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "version": "5.1.0"}


@app.get("/cache/stats", tags=["System"])
def cache_stats():
    """See how many summaries are cached."""
    return get_cache_stats()


@app.delete("/cache/clear", tags=["System"])
def cache_clear():
    """Clear all cached summaries."""
    clear_cache()
    return {"status": "cache cleared"}