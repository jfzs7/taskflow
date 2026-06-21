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

# Skonfigurowano logger dla serwisu cache
logger = logging.getLogger(__name__)

# Pobrano konfigurację Redis
settings = get_settings()

# --- Utworzono klienta Redis ---
# decode_responses=True zapewnia automatyczną konwersję bajtów na stringi.
# Połączenie jest nawiązywane leniwie (przy pierwszym użyciu).
redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> Optional[redis.Redis]:
    """
    Zwrócono instancję klienta Redis (Singleton).

    Zastosowano wzorzec leniwej inicjalizacji — połączenie
    z Redis jest nawiązywane dopiero przy pierwszym wywołaniu.
    W przypadku błędu połączenia zwracany jest None,
    a aplikacja kontynuuje działanie bez cache.
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
            # Sprawdzono połączenie z Redis
            await redis_client.ping()
            logger.info("Nawiązano połączenie z Redis: %s", settings.redis_url)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(
                "Nie udało się połączyć z Redis: %s. "
                "Aplikacja działa bez warstwy cache.",
                str(e)
            )
            redis_client = None
    return redis_client


async def close_redis():
    """
    Zamknięto połączenie z Redis.

    Wywołanie tej funkcji następuje podczas zamykania aplikacji
    w celu prawidłowego zwolnienia zasobów.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Zamknięto połączenie z Redis.")


async def cache_get(key: str) -> Optional[dict]:
    """
    Pobrano wartość z cache Redis.

    Argumenty:
        key: Klucz cache (np. 'task:1', 'tasks:page:1')

    Zwrócono:
        Słownik z danymi lub None (cache miss lub brak połączenia).
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
    Zapisano wartość w cache Redis z czasem wygaśnięcia (TTL).

    Argumenty:
        key: Klucz cache
        value: Słownik z danymi do zapisania
        ttl: Czas życia w sekundach (domyślnie 300s = 5 minut)

    Zwrócono:
        True jeśli zapis się powiódł, False w przeciwnym razie.
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
    Usunięto wartość z cache Redis.

    Argumenty:
        key: Klucz cache do usunięcia

    Zwrócono:
        True jeśli usunięcie się powiodło, False w przeciwnym razie.
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
    Unieważniono wszystkie klucze pasujące do wzorca.

    Zastosowano operację SCAN zamiast KEYS w celu uniknięcia
    blokowania serwera Redis przy dużej liczbie kluczy.

    Argumenty:
        pattern: Wzorzec kluczy (np. 'tasks:*')

    Zwrócono:
        True jeśli operacja się powiodła, False w przeciwnym razie.
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
    Sprawdzono stan zdrowia połączenia z Redis.

    Wykorzystywane przez endpoint /health do raportowania
    statusu serwisu cache.

    Zwrócono:
        True jeśli Redis odpowiada na PING, False w przeciwnym razie.
    """
    client = await get_redis_client()
    if client is None:
        return False

    try:
        return await client.ping()
    except (redis.ConnectionError, redis.TimeoutError):
        return False
