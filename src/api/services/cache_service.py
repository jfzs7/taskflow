"""
Moduł serwisu cache (Redis) aplikacji TaskFlow.

Zaimplementowano warstwę cache z wykorzystaniem Redis
w celu przyspieszenia odczytów i zmniejszenia obciążenia
bazy danych PostgreSQL. Zastosowano wzorzec Cache-Aside
(Lazy Loading) — dane są pobierane z cache, a w przypadku
braku trafienia (cache miss) są wczytywane z bazy danych
i zapisywane w cache.
"""

import json
import logging
from typing import Optional

import redis.asyncio as redis

from config import get_settings

# Logowanie dla serwisu cache
logger = logging.getLogger(__name__)

# Konfiguracja
settings = get_settings()

# --- Instancja klienta Redis ---
# decode_responses=True ułatwia operacje na stringach
redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> Optional[redis.Redis]:
    """
    Zwraca instancję klienta Redis (wzorzec Singleton).

    Leniwa inicjalizacja — połączenie następuje przy pierwszym żądaniu.
    Gdy Redis leży, zwraca None i apka działa bez cache.
    """
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            # Sprawdzenie połączenia
            await redis_client.ping()
            logger.info("Nawiązano połączenie z Redis: %s", settings.redis_url)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(
                "Brak połączenia z Redis (%s). "
                "Praca bez warstwy cache.",
                str(e)
            )
            redis_client = None
    return redis_client


async def close_redis():
    """
    Zamknięcie połączenia z Redis przy wyłączaniu aplikacji.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Zamknięto połączenie z Redis.")


async def cache_get(key: str) -> Optional[dict]:
    """
    Pobranie wartości z cache.

    Zwraca słownik lub None (cache miss / brak połączenia).
    """
    client = await get_redis_client()
    if client is None:
        return None

    try:
        value = await client.get(key)
        if value:
            logger.debug("Cache HIT: %s", key)
            return json.loads(value)
        logger.debug("Cache MISS: %s", key)
        return None
    except (redis.ConnectionError, redis.TimeoutError, json.JSONDecodeError) as e:
        logger.warning("Błąd odczytu cache dla klucza '%s': %s", key, str(e))
        return None


async def cache_set(key: str, value: dict, ttl: int = 300) -> bool:
    """
    Zapisanie wartości w cache na określony czas TTL.
    """
    client = await get_redis_client()
    if client is None:
        return False

    try:
        await client.setex(key, ttl, json.dumps(value, default=str))
        logger.debug("Cache SET: %s (TTL: %ds)", key, ttl)
        return True
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.warning("Błąd zapisu cache dla klucza '%s': %s", key, str(e))
        return False


async def cache_delete(key: str) -> bool:
    """
    Usunięcie wartości z cache.
    """
    client = await get_redis_client()
    if client is None:
        return False

    try:
        await client.delete(key)
        logger.debug("Cache DELETE: %s", key)
        return True
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.warning("Błąd usuwania cache dla klucza '%s': %s", key, str(e))
        return False


async def cache_invalidate_pattern(pattern: str) -> bool:
    """
    Unieważnienie wszystkich kluczy pasujących do wzorca (np. tasks:*).

    SCAN chroni Redis przed zablokowaniem przy dużej liczbie kluczy.
    """
    client = await get_redis_client()
    if client is None:
        return False

    try:
        cursor = 0
        deleted_count = 0
        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
                deleted_count += len(keys)
            if cursor == 0:
                break
        logger.debug("Cache INVALIDATE pattern '%s': usunięto %d kluczy", pattern, deleted_count)
        return True
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.warning("Błąd unieważniania cache dla wzorca '%s': %s", pattern, str(e))
        return False


async def check_redis_health() -> bool:
    """
    Sprawdzenie stanu połączenia z Redis (wykorzystywane przez health check).
    """
    client = await get_redis_client()
    if client is None:
        return False

    try:
        return await client.ping()
    except (redis.ConnectionError, redis.TimeoutError):
        return False
