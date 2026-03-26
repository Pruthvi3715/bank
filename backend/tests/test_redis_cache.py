import os
import pytest
import pytest_asyncio

# Ensure no Redis URL so it falls back to in-memory
os.environ["REDIS_URL"] = "redis://localhost:19999"  # unreachable port

from app.cache.redis_cache import (
    init_redis,
    close_redis,
    cache_set,
    cache_get,
    cache_delete,
    cache_exists,
    _fallback_cache,
    _redis_client,
)


@pytest_asyncio.fixture(autouse=True)
async def setup():
    """Clear fallback cache before each test."""
    _fallback_cache.clear()
    # Don't init_redis (would fail to connect) — just test fallback directly
    # But set _redis_client to None to force fallback
    import app.cache.redis_cache as rc

    rc._redis_client = None
    yield
    _fallback_cache.clear()


@pytest.mark.asyncio
async def test_cache_set_and_get():
    """cache_set stores, cache_get retrieves."""
    await cache_set("key1", {"hello": "world"}, ttl=60)
    result = await cache_get("key1")
    assert result == {"hello": "world"}


@pytest.mark.asyncio
async def test_cache_get_missing_returns_none():
    """cache_get on non-existent key returns None."""
    result = await cache_get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete():
    """cache_delete removes the key."""
    await cache_set("key2", "value2")
    assert await cache_exists("key2") is True
    await cache_delete("key2")
    assert await cache_exists("key2") is False


@pytest.mark.asyncio
async def test_cache_exists():
    """cache_exists returns True/False correctly."""
    assert await cache_exists("key3") is False
    await cache_set("key3", 42)
    assert await cache_exists("key3") is True


@pytest.mark.asyncio
async def test_cache_complex_types():
    """Handles lists, nested dicts, numbers, strings."""
    await cache_set("list_key", [1, 2, 3])
    assert await cache_get("list_key") == [1, 2, 3]

    await cache_set("nested", {"a": {"b": [1, 2]}, "c": True})
    result = await cache_get("nested")
    assert result["a"]["b"] == [1, 2]
    assert result["c"] is True

    await cache_set("num", 3.14)
    assert await cache_get("num") == 3.14

    await cache_set("str", "hello")
    assert await cache_get("str") == "hello"


@pytest.mark.asyncio
async def test_cache_overwrite():
    """Setting same key overwrites previous value."""
    await cache_set("overwrite", "old")
    await cache_set("overwrite", "new")
    assert await cache_get("overwrite") == "new"


@pytest.mark.asyncio
async def test_cache_delete_nonexistent_no_error():
    """Deleting a non-existent key doesn't raise."""
    await cache_delete("does_not_exist")  # Should not raise


@pytest.mark.asyncio
async def test_init_redis_unavailable_graceful():
    """init_redis with unreachable Redis should set _redis_client to None."""
    import app.cache.redis_cache as rc

    await rc.init_redis()
    assert rc._redis_client is None  # Should gracefully fail


@pytest.mark.asyncio
async def test_close_redis_when_none():
    """close_redis when _redis_client is None should not raise."""
    import app.cache.redis_cache as rc

    rc._redis_client = None
    await rc.close_redis()  # Should not raise
