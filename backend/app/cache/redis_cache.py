"""
Redis-backed caching layer with graceful in-memory fallback.

Uses redis.asyncio for non-blocking operations. If Redis is unavailable
(e.g. during local dev without Docker), all operations fall back to a
module-level in-memory dict so the rest of the application keeps working.
"""

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback in-memory store (used when Redis is down or unavailable)
# ---------------------------------------------------------------------------
_fallback_cache: dict[str, Any] = {}

# ---------------------------------------------------------------------------
# Redis client (lazily initialised)
# ---------------------------------------------------------------------------
_redis_client: Any = None  # redis.asyncio.Redis | None


def _get_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379")


async def init_redis() -> None:
    """Create the async Redis connection pool and verify connectivity."""
    global _redis_client
    try:
        import redis.asyncio as aioredis

        url = _get_redis_url()
        _redis_client = aioredis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await _redis_client.ping()
        logger.info("Redis connected at %s", url)
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — using in-memory fallback", exc)
        _redis_client = None


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None


# ---------------------------------------------------------------------------
# Cache operations
# ---------------------------------------------------------------------------


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    """Serialize *value* as JSON and store under *key* with *ttl* seconds."""
    payload = json.dumps(value, default=str)
    if _redis_client is not None:
        try:
            await _redis_client.set(key, payload, ex=ttl)
            return
        except Exception as exc:
            logger.warning("Redis SET failed for %s: %s", key, exc)
    _fallback_cache[key] = value


async def cache_get(key: str) -> Optional[Any]:
    """Retrieve and deserialize the value stored under *key*."""
    if _redis_client is not None:
        try:
            raw = await _redis_client.get(key)
            if raw is not None:
                return json.loads(raw)
            return None
        except Exception as exc:
            logger.warning("Redis GET failed for %s: %s", key, exc)
    return _fallback_cache.get(key)


async def cache_delete(key: str) -> None:
    """Remove *key* from the cache."""
    if _redis_client is not None:
        try:
            await _redis_client.delete(key)
            return
        except Exception as exc:
            logger.warning("Redis DELETE failed for %s: %s", key, exc)
    _fallback_cache.pop(key, None)


async def cache_exists(key: str) -> bool:
    """Return True if *key* exists in the cache."""
    if _redis_client is not None:
        try:
            return bool(await _redis_client.exists(key))
        except Exception as exc:
            logger.warning("Redis EXISTS failed for %s: %s", key, exc)
    return key in _fallback_cache
