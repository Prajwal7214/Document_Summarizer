import hashlib
import json
import redis.asyncio as redis
from datetime import datetime
from config import settings

# Initialize Redis client lazily
_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        url = settings.REDIS_URL or "redis://localhost:6380/0"
        try:
            _redis_client = redis.from_url(url, decode_responses=True)
        except Exception as e:
            print(f"[ERROR] Could not connect to Redis at {url}: {e}")
            _redis_client = None
    return _redis_client

def get_file_hash(text: str, summary_type: str) -> str:
    """
    Generate unique hash for a document + summary type combo.
    Same file + same type = same hash = return cached result.
    """
    content = f"{text[:5000]}_{summary_type}"  # Use first 5000 chars for hash
    return hashlib.md5(content.encode()).hexdigest()

async def get_cached(text: str, summary_type: str) -> dict | None:
    """
    Check if summary already exists in Redis cache.
    Returns cached result or None.
    """
    if not settings.ENABLE_CACHE:
        return None
    
    r = get_redis()
    if not r: return None

    file_hash = get_file_hash(text, summary_type)
    try:
        cached = await r.get(f"summary:{file_hash}")
        if cached:
            print(f"[SUCCESS] Cache hit! Returning cached summary (saves API call)")
            return json.loads(cached)
    except Exception as e:
        print(f"[WARN] Redis get error: {e}")
    return None

async def set_cache(text: str, summary_type: str, result: dict) -> None:
    """Store summary result in Redis cache for 7 days."""
    if not settings.ENABLE_CACHE:
        return
        
    r = get_redis()
    if not r: return

    file_hash = get_file_hash(text, summary_type)
    try:
        # 86400 * 7 = 7 days expiration
        await r.set(f"summary:{file_hash}", json.dumps(result), ex=604800)
        print(f"[INFO] Cached summary in Redis for future use")
    except Exception as e:
        print(f"[WARN] Redis set error: {e}")

async def get_cache_stats() -> dict:
    """Return cache statistics from Redis."""
    r = get_redis()
    if not r: return {"total_cached": 0, "status": "redis not connected"}
    
    try:
        keys = await r.keys("summary:*")
        return {
            "total_cached": len(keys),
            "status": "connected"
        }
    except Exception as e:
        return {"total_cached": 0, "status": f"error: {e}"}

async def clear_cache() -> None:
    """Clear all cached summaries from Redis."""
    r = get_redis()
    if not r: return
    
    try:
        keys = await r.keys("summary:*")
        if keys:
            await r.delete(*keys)
        print("[INFO] Redis cache cleared")
    except Exception as e:
        print(f"[WARN] Redis clear error: {e}")