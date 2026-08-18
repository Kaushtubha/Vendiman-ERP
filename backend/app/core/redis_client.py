"""
app/core/redis_client.py — Redis Connection Pool & Client

PATTERN: Singleton connection pool with typed async client wrapper.

WHY a dedicated Redis module vs inline initialization:
    - Single pool shared across all application code. Each call to redis.Redis()
      without a pool creates a NEW connection — a common production bug.
    - Centralizes configuration: timeout, max connections, decode_responses.
    - Allows clean testing via dependency injection / monkeypatching.

SECURITY:
    - Connections authenticated via requirepass (configured in Docker Compose).
    - In production: use Redis ACLs to restrict keys by prefix per service.
      Celery keys (celery-task-*) should only be readable by the worker.
    - All network traffic encrypted via TLS (Redis 6+ supports TLS natively).
      Set ssl=True and provide cert in production Redis URL.

SCALABILITY:
    - max_connections=50 per process × 4 workers = 200 total connections.
      Redis default limit is 10,000. We're well within bounds.
    - hiredis parser (C extension) provides 10x faster response parsing
      compared to the pure-Python parser. Critical at high throughput.
    - For read-heavy caching (e.g., dashboard KPIs), add Redis Cluster or
      read replicas. Client changes from Redis() to RedisCluster() only.

CACHE STRATEGY (applied in service layer):
    - Cache-aside pattern: services check cache first, query DB on miss,
      populate cache on return.
    - TTL-based expiry: all cached keys have explicit TTLs. No unbounded growth.
    - Cache invalidation: services call cache.delete(key) on writes.
      No background polling required.
"""

from __future__ import annotations

import logging
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Cache TTL constants (seconds)
# WHY constants: Magic numbers in service files are unreviewed and silently wrong.
# Centralizing TTLs makes cache behavior auditable and tunable.
CACHE_TTL_SHORT = 60           # 1 minute: real-time data (stock counts, cart)
CACHE_TTL_MEDIUM = 300         # 5 minutes: frequently changing data (orders)
CACHE_TTL_LONG = 3600          # 1 hour: slowly changing data (product catalog)
CACHE_TTL_DAY = 86400          # 24 hours: reference data (categories, warehouses)

# Key prefix constants — prevents key collisions between modules
CACHE_KEY_PRODUCT = "product"
CACHE_KEY_INVENTORY = "inventory"
CACHE_KEY_SUPPLIER = "supplier"
CACHE_KEY_PO = "purchase_order"
CACHE_KEY_DASHBOARD = "dashboard"
CACHE_KEY_RESERVATION = "reservation"
CACHE_KEY_USER = "user"


class RedisClient:
    """
    Typed wrapper around the async Redis client.

    WHY a wrapper class vs direct Redis usage:
        1. Adds business-level methods (cache_set with serialization, etc.)
        2. Allows swapping Redis for another cache backend (e.g., Memcached)
           by changing only this class.
        3. Adds structured logging for cache hits/misses — important for
           understanding cache effectiveness in production.
        4. Implements cache key namespacing to prevent module collisions.

    DESIGN: This class follows the Facade pattern — presents a simpler
    interface over the raw Redis client.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    @staticmethod
    def build_key(*parts: str) -> str:
        """
        Build a namespaced cache key.

        Example: build_key("product", "detail", "uuid-123") → "erp:product:detail:uuid-123"

        WHY namespace "erp:": Prevents collisions if Redis is shared with other
        applications. In production, each env (dev/staging/prod) should use
        its own Redis instance, not just a prefix.
        """
        return "erp:" + ":".join(parts)

    async def get(self, key: str) -> str | None:
        """Retrieve a cached value by key."""
        try:
            value = await self._client.get(key)
            if value is not None:
                logger.debug("Cache HIT: %s", key)
            else:
                logger.debug("Cache MISS: %s", key)
            return value
        except Exception as exc:
            # RESILIENCE: Cache failures must NEVER crash the application.
            # Log the error and return None (forces a DB read).
            logger.error("Redis GET error for key=%s: %s", key, exc)
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: int = CACHE_TTL_MEDIUM,
    ) -> bool:
        """Set a cache value with TTL."""
        try:
            await self._client.setex(name=key, time=ttl, value=value)
            return True
        except Exception as exc:
            logger.error("Redis SET error for key=%s: %s", key, exc)
            return False

    async def delete(self, *keys: str) -> int:
        """Invalidate one or more cache keys."""
        try:
            return await self._client.delete(*keys)
        except Exception as exc:
            logger.error("Redis DELETE error: %s", exc)
            return 0

    async def delete_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        WHY NOT KEYS command: KEYS blocks Redis server (single-threaded) during
        scan. For large keyspaces, this causes latency spikes. SCAN iterates
        in batches without blocking.

        Example: delete_pattern("erp:product:*") clears all product cache.
        """
        try:
            deleted = 0
            async for key in self._client.scan_iter(match=pattern, count=100):
                await self._client.delete(key)
                deleted += 1
            logger.info("Cleared %d cache keys matching pattern: %s", deleted, pattern)
            return deleted
        except Exception as exc:
            logger.error("Redis pattern delete error: %s", exc)
            return 0

    async def set_with_nx(self, key: str, value: str, ttl: int) -> bool:
        """
        Set a key only if it does NOT exist (atomic).

        Used for: distributed locks, idempotency tokens, reservation keys.

        WHY SET NX (not GET + SET): GET + SET has a race condition window.
        SET NX is atomic at the Redis server level.
        """
        try:
            result = await self._client.set(key, value, ex=ttl, nx=True)
            return result is True
        except Exception as exc:
            logger.error("Redis SETNX error for key=%s: %s", key, exc)
            return False

    async def increment(self, key: str, amount: int = 1) -> int | None:
        """Atomic increment — used for counters (rate limiting, PO sequence)."""
        try:
            return await self._client.incrby(key, amount)
        except Exception as exc:
            logger.error("Redis INCR error for key=%s: %s", key, exc)
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        """Refresh TTL on an existing key."""
        try:
            return await self._client.expire(key, ttl)
        except Exception as exc:
            logger.error("Redis EXPIRE error for key=%s: %s", key, exc)
            return False

    async def ping(self) -> bool:
        """Health check — used in /health endpoint."""
        try:
            return await self._client.ping()
        except Exception:
            return False

    @property
    def raw(self) -> Redis:
        """
        Escape hatch to raw Redis client for advanced operations
        (pub/sub, pipelines, Lua scripts).

        Use sparingly — prefer the typed methods above.
        """
        return self._client


def create_redis_pool() -> ConnectionPool:
    """
    Create a connection pool for the Redis client.

    WHY ConnectionPool: A single pool is created at startup and reused by all
    coroutines. Without a pool, each async Redis operation creates a new TCP
    connection — expensive and limited by OS file descriptor limits.
    """
    settings = get_settings()
    return aioredis.ConnectionPool.from_url(
        url=settings.redis.url,
        max_connections=settings.redis.max_connections,
        socket_timeout=settings.redis.socket_timeout,
        socket_connect_timeout=settings.redis.socket_connect_timeout,
        health_check_interval=settings.redis.health_check_interval,
        decode_responses=True,       # Auto-decode bytes → str. Assumes UTF-8.
        retry_on_timeout=True,       # Retry transient timeouts automatically
    )


# Module-level pool — shared across all requests
_redis_pool: ConnectionPool | None = None


def get_redis_pool() -> ConnectionPool:
    """Return the global Redis connection pool, creating it if needed."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = create_redis_pool()
    return _redis_pool


def get_redis_client() -> RedisClient:
    """
    Get a Redis client using the shared connection pool.

    Usage in FastAPI dependencies:
        redis = Annotated[RedisClient, Depends(get_redis_client)]
    """
    pool = get_redis_pool()
    raw_client: Redis = aioredis.Redis(connection_pool=pool)
    return RedisClient(client=raw_client)
