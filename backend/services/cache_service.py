import hashlib
import json
from datetime import datetime

# Simple in-memory cache
# Format: { file_hash: { "result": {...}, "cached_at": "..." } }
_cache: dict = {}


def get_file_hash(text: str, summary_type: str) -> str:
    """
    Generate unique hash for a document + summary type combo.
    Same file + same type = same hash = return cached result.
    """
    content = f"{text[:5000]}_{summary_type}"  # Use first 5000 chars for hash
    return hashlib.md5(content.encode()).hexdigest()


def get_cached(text: str, summary_type: str) -> dict | None:
    """
    Check if summary already exists in cache.
    Returns cached result or None.
    """
    file_hash = get_file_hash(text, summary_type)
    if file_hash in _cache:
        print(f"[SUCCESS] Cache hit! Returning cached summary (saves API call)")
        return _cache[file_hash]["result"]
    return None


def set_cache(text: str, summary_type: str, result: dict) -> None:
    """Store summary result in cache."""
    file_hash = get_file_hash(text, summary_type)
    _cache[file_hash] = {
        "result": result,
        "cached_at": datetime.now().isoformat()
    }
    print(f"[INFO] Cached summary for future use")


def get_cache_stats() -> dict:
    """Return cache statistics."""
    return {
        "total_cached": len(_cache),
        "cached_keys": list(_cache.keys())
    }


def clear_cache() -> None:
    """Clear all cached summaries."""
    _cache.clear()
    print("[INFO] Cache cleared")