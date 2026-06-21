# Dokumentacja Techniczna — System TaskFlow

Dokument zawiera opis techniczny architektury, modelu danych, punktów końcowych API (REST) oraz konfiguracji infrastrukturalnej i potoków CI/CD systemu zarządzania zadaniami TaskFlow.

---

## 1. Architektura systemu

Aplikacja TaskFlow została zaprojektowana w architekturze mikroserwisowej z podziałem na warstwy prezentacji, logiki biznesowej oraz przechowywania danych. Wszystkie komponenty działają jako niezależne usługi kontenerowe.

```mermaid
graph TD
    Client["👤 Klient (Przeglądarka)"] -->|HTTP / Port 80| Proxy["🔀 Nginx Proxy"]
    
    subgraph "Warstwa Prezentacji i Logiki"
        Proxy -->|Przekierowanie| API["🐍 FastAPI Backend"]
    end

    subgraph "Warstwa Danych"
        API -->|Odczyt/Zapis SQL| DB["🐘 PostgreSQL"]
        API -->|Cache-Aside (GET/SET)| Cache["⚡ Redis Cache"]
    end
```

### Komponenty systemu:
1.  **Nginx (Reverse Proxy)**: Odpowiada za przyjmowanie ruchu HTTP na porcie 80, kompresję gzip, logowanie zapytań oraz przekazywanie żądań do serwera aplikacji.
2.  **FastAPI Backend**: Asynchroniczny serwer aplikacji napisany w Pythonie 3.12. Odpowiada za logikę biznesową, walidację danych (Pydantic), generowanie stron HTML (Jinja2) oraz wystawianie interfejsu REST API.
3.  **PostgreSQL 16**: Główna relacyjna baza danych przechowująca informacje o zadaniach.
4.  **Redis 7**: Pamięć podręczna (in-memory) przechowująca zserializowane listy zadań w celu odciążenia bazy danych i przyspieszenia czasu odpowiedzi aplikacji.

---

## 2. Architektura oprogramowania (Backend)

Kod backendu został podzielony zgodnie ze wzorcem Separation of Concerns (Rozdzielenie Odpowiedzialności) na warstwy:
*   **Warstwa routingu (`src/api/routes/`)**: Definiuje punkty końcowe HTTP, obsługuje parametry zapytań i formatuje odpowiedzi.
*   **Warstwa logiki biznesowej (`src/api/services/`)**: Implementuje reguły biznesowe, steruje dostępem do bazy danych oraz zarządza unieważnianiem i zapisem danych w pamięci podręcznej.
*   **Warstwa dostępu do danych (`src/api/database.py`, `src/api/models.py`)**: Odpowiada za sesje asynchroniczne ORM SQLAlchemy 2.0 i mapowanie obiektowo-relacyjne.

### Wzorzec Cache-Aside (Redis)
Zaimplementowany mechanizm cache działa według następujących zasad:
1.  Odczyt listy zadań kierowany jest w pierwszej kolejności do Redis.
2.  W przypadku trafienia (cache hit), dane są deserializowane i zwracane natychmiast.
3.  W przypadku braku (cache miss), dane są pobierane z PostgreSQL, zapisywane w cache z określonym czasem życia (TTL = 60s) i zwracane klientowi.
4.  Każda operacja modyfikująca stan (zapis, edycja, usunięcie zadania) powoduje natychmiastowe usunięcie odpowiednich kluczy z cache (cache invalidation), co gwarantuje spójność danych.

---

## 3. Model danych bazy (PostgreSQL)

Baza danych przechowuje zadania w tabeli `tasks`. Schemat bazy danych został zaprojektowany z uwzględnieniem asynchronicznego dialektu `asyncpg`.

### Tabela `tasks`
| Kolumna | Typ danych | Ograniczenia | Opis |
|---------|------------|--------------|------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unikalny identyfikator zadania. |
| `title` | VARCHAR(100) | NOT NULL | Tytuł zadania. |
| `description` | TEXT | NULLABLE | Szczegółowy opis zadania. |
| `status` | VARCHAR (Enum) | NOT NULL, Default: 'todo' | Status: `todo`, `in_progress`, `done`. |
| `priority` | VARCHAR (Enum) | NOT NULL, Default: 'medium' | Priorytet: `low`, `medium`, `high`, `critical`. |
| `created_at` | TIMESTAMP | NOT NULL, Default: UTC NOW | Data i czas utworzenia rekordu. |
| `updated_at` | TIMESTAMP | NOT NULL, Default: UTC NOW | Data i czas ostatniej modyfikacji. |
| `is_deleted` | BOOLEAN | NOT NULL, Default: FALSE | Flaga dla mechanizmu bezpiecznego usuwania (soft-delete). |

---

## 4. Specyfikacja API (REST)

Punkt wejścia dla API: `/api/v1/tasks`

| Metoda | Endpoint | Opis | Format wejścia (JSON) | Kod sukcesu | Kody błędów |
|--------|----------|------|-----------------------|-------------|-------------|
| **POST** | `/` | Tworzy nowe zadanie | `{title, description?, priority?, status?}` | `201 Created` | `422` (Błędna walidacja) |
| **GET** | `/` | Pobiera listę zadań (filtry, sortowanie, paginacja) | *Query params*: `page`, `per_page`, `status`, `priority`, `sort_by`, `sort_order` | `200 OK` | `422` (Błędne parametry) |
| **GET** | `/{id}` | Pobiera szczegóły pojedynczego zadania | *Brak* | `200 OK` | `404` (Brak zadania) |
| **PATCH** | `/{id}` | Częściowo aktualizuje dane zadania | `{title?, description?, priority?, status?}` | `200 OK` | `404` (Brak zadania), `422` |
| **DELETE**| `/{id}` | Usuwa zadanie (soft-delete) | *Brak* | `200 OK` | `404` (Brak zadania) |

---

## 5. Infrastruktura i Konteneryzacja

### Obrazy Docker:
*   **API**: Dwuetapowy proces budowania (multi-stage build) oparty na obrazie `python:3.12-slim`. Pierwsza faza instaluje zależności do katalogu `/install`, druga faza kopiuje prekompilowane pakiety do lekkiego obrazu bazowego, tworzy użytkownika systemowego bez uprawnień roota (`appuser`) i definiuje sondę kontrolną `HEALTHCHECK`.
*   **Nginx**: Lekki obraz oparty na `nginx:alpine` z podmienioną konfiguracją proxy.

### Orkiestracja Kubernetes:
*   **Namespace (`taskflow`)**: Logiczna separacja zasobów klastra.
*   **StatefulSets**: Wykorzystane do uruchomienia PostgreSQL (`postgres`) oraz Redis (`redis`) w celu zagwarantowania stałych nazw sieciowych (poprzez powiązane usługi *headless*) oraz stałego połączenia z przypisanymi wolumenami danych (`PersistentVolumeClaims`).
*   **Deployments**: Wykorzystane do skalowania bezstanowej warstwy API oraz serwera Nginx.
*   **Autoskalowanie (HPA)**: Skonfigurowane dla usługi API, automatycznie zwiększające liczbę replik podów w zakresie od 2 do 5 na podstawie średniego zużycia procesora (próg 70% CPU).
*   **Ingress**: Zarządza ruchem zewnętrznym w oparciu o domenę `taskflow.local`.

---

## 6. Potoki CI/CD (GitHub Actions)

Wdrożono automatyzację procesów w ramach Continuous Integration (CI) oraz Continuous Deployment (CD).

### Proces CI (`ci.yml`):
1.  Uruchomienie przy każdym zdarzeniu typu `push` oraz `pull_request` do gałęzi `main`.
2.  Konfiguracja środowiska Python 3.12 z buforowaniem pakietów (cache).
3.  Instalacja zależności projektu.
4.  Weryfikacja jakości kodu za pomocą narzędzi `black` (formatowanie) oraz `flake8` (linting).
5.  Uruchomienie testów jednostkowych za pomocą biblioteki `pytest` wraz z wygenerowaniem raportu pokrycia kodu.
6.  Weryfikacja poprawności kompilacji i budowania kontenerów Docker.

### Proces CD (`cd.yml`):
1.  Uruchomienie automatyczne po pomyślnym zakończeniu etapu CI na gałęzi `main`.
2.  Zalogowanie do rejestru pakietów GitHub Container Registry (GHCR).
3.  Zbudowanie produkcyjnych obrazów Docker dla API oraz Nginx.
4.  Oznaczenie obrazów tagami: `latest` oraz unikalnym identyfikatorem zatwierdzenia SHA (`${{ github.sha }}`).
5.  Wypchnięcie gotowych obrazów do rejestru GHCR, skąd mogą być natychmiast pobrane przez klaster Kubernetes.
