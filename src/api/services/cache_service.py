"""
Warstwa cache Redis — implementacja wzorca Cache-Aside.

Kluczowa zaleta: jezeli Redis jest niedostepny, zadna z funkcji nie rzuca wyjatku.
Aplikacja po cichu odpytuje baze bezposrednio (graceful degradation).

Wzorzec Cache-Aside:
  1. Sprawdz cache -> jezeli HIT, zwroc dane.
  2. Jezeli MISS -> pobierz z bazy, zapisz do cache z TTL, zwroc dane.
  3. Po kazdym zapisie/usunieciu -> uniewaznij powiazan klucze w cache.
"""

import json
import logging
from typing import Any, Optional

# pyrefly: ignore [missing-import]
import redis.asyncio as aioredis

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton klienta Redis — inicjowany przy pierwszym uzyciu (lazy init).
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> Optional[aioredis.Redis]:
    """
    Zwraca klienta Redis lub None jezeli polaczenie nie dziala.
    Uzywa lazy initialization — nie laczymy sie przy starcie aplikacji,
    tylko gdy faktycznie potrzebujemy cache.
    """
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await _redis_client.ping()
            logger.info("[OK] Polaczono z Redis: %s", settings.redis_url)
        except Exception as e:
            logger.warning("[WARN] Redis niedostepny: %s. Cache wylaczony.", e)
            _redis_client = None

    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    """Pobiera wartosc z cache. Zwraca None przy MISS lub braku Redis."""
    client = await get_redis_client()
    if not client:
        return None

    try:
        value = await client.get(key)
        if value:
            logger.debug("[CACHE HIT] %s", key)
            return json.loads(value)
        logger.debug("[CACHE MISS] %s", key)
        return None
    except Exception as e:
        logger.warning("[WARN] Blad cache_get(%s): %s", key, e)
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Zapisuje wartosc do cache z TTL (domyslnie 5 minut). Zwraca False przy bledzie."""
    client = await get_redis_client()
    if not client:
        return False

    try:
        serialized = json.dumps(value, default=str)
        await client.setex(key, ttl, serialized)
        logger.debug("[CACHE SET] %s (TTL=%ds)", key, ttl)
        return True
    except Exception as e:
        logger.warning("[WARN] Blad cache_set(%s): %s", key, e)
        return False


async def cache_delete(key: str) -> bool:
    """Usuwa konkretny klucz z cache."""
    client = await get_redis_client()
    if not client:
        return False

    try:
        await client.delete(key)
        logger.debug("[CACHE DEL] %s", key)
        return True
    except Exception as e:
        logger.warning("[WARN] Blad cache_delete(%s): %s", key, e)
        return False


async def cache_invalidate_pattern(pattern: str) -> int:
    """
    Usuwa wszystkie klucze pasujace do wzorca (np. 'taskflow:tasks:*').
    Uzywa SCAN zamiast KEYS — bezpieczne dla duzych baz Redis (nie blokuje serwera).
    """
    client = await get_redis_client()
    if not client:
        return 0

    deleted = 0
    try:
        async for key in client.scan_iter(match=pattern, count=100):
            await client.delete(key)
            deleted += 1
        if deleted:
            logger.debug("[CACHE INVALIDATE] Wzorzec '%s' -> usunieto %d kluczy", pattern, deleted)
    except Exception as e:
        logger.warning("[WARN] Blad cache_invalidate_pattern(%s): %s", pattern, e)

    return deleted


async def check_redis_health() -> bool:
    """Sprawdza czy Redis odpowiada na ping. Uzywane przez /health endpoint."""
    client = await get_redis_client()
    if not client:
        return False
    try:
        return await client.ping()
    except Exception:
        return False


async def close_redis():
    """Zamyka polaczenie z Redis przy shutdown aplikacji."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("[OK] Polaczenie Redis zamkniete.")
