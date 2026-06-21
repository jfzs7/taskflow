# TaskFlow — Dziennik Wdrożenia i Spis Plików
# Autor: Jakub Francuz | Praca magisterska, 2026

Dokument zawiera kompletny spis plików projektu oraz chronologiczny opis
kolejnych kroków wdrożenia — co wykonano, dlaczego i jaki był tego rezultat.

---

## Spis plików projektu

### Konfiguracja projektu
| Plik | Opis |
|------|------|
| `.gitignore` | Reguły ignorowania plików przez Git. Wykluczono cache Pythona, środowiska wirtualne, pliki IDE, `.env` z sekretami oraz artefakty testów. |
| `.env.example` | Szablon zmiennych środowiskowych. Zdefiniowano wartości domyślne dla połączeń z PostgreSQL, Redis i ustawień aplikacji — użytkownik kopiuje go jako `.env`. |
| `Makefile` | Skróty poleceń terminalowych. Umożliwia szybkie uruchamianie testów, budowanie obrazów Docker i wdrażanie na Kubernetes jednym poleceniem. |
| `README.md` | Główna dokumentacja projektu. Zawiera opis architektury, stos technologiczny, instrukcję szybkiego uruchomienia oraz strukturę katalogów. |
| `docker-compose.yml` | Definicja orkiestracji lokalnej. Zdefiniowano 4 serwisy (API, PostgreSQL, Redis, Nginx) z health checkami, limitami zasobów i nazwanymi woluminami. |

### Kod źródłowy — Backend API (`src/api/`)
| Plik | Opis |
|------|------|
| `src/api/main.py` | Punkt wejścia aplikacji FastAPI. Skonfigurowano middleware CORS, lifespan (inicjalizacja/zamykanie DB i Redis), routery oraz serwowanie szablonów HTML i plików statycznych. |
| `src/api/config.py` | Moduł konfiguracyjny (pydantic-settings). Wczytuje zmienne środowiskowe i udostępnia je jako obiekt Singleton — zapewnia jedno źródło konfiguracji w aplikacji. |
| `src/api/database.py` | Asynchroniczne połączenie z bazą danych (SQLAlchemy 2.0 + asyncpg). Zaimplementowano Dependency Injection sesji bazodanowej oraz funkcje init/close bazy. |
| `src/api/models.py` | Modele SQLAlchemy — definicja tabeli `tasks`. Zdefiniowano Enumy (Priority, Status), pola z walidacją, timestampy i soft-delete (pole `is_deleted`). |
| `src/api/schemas.py` | Schematy Pydantic v2 do walidacji żądań i serializacji odpowiedzi. Zdefiniowano schematy CRUD, health check, metryk oraz paginacji listy zadań. |
| `src/api/requirements.txt` | Zależności Python z przypiętymi wersjami. Zapewnia powtarzalność budowania — te same wersje pakietów na każdym środowisku. |
| `src/api/Dockerfile` | Multi-stage Dockerfile dla serwisu API. Etap 1 instaluje zależności, etap 2 tworzy lekki obraz produkcyjny z użytkownikiem nie-root i wbudowanym health checkiem. |

### Endpointy API (`src/api/routes/`)
| Plik | Opis |
|------|------|
| `src/api/routes/__init__.py` | Plik inicjalizacyjny pakietu routerów. Grupuje moduły endpointów tasks i health. |
| `src/api/routes/tasks.py` | Endpointy CRUD zadań (REST API v1). Zaimplementowano POST/GET/PATCH/DELETE z filtrowaniem, sortowaniem i paginacją — wersjonowanie API (`/api/v1/`). |
| `src/api/routes/health.py` | Endpointy monitoringu `/health` i `/metrics`. Sprawdzają stan bazy danych i Redis — kluczowe dla Kubernetes liveness/readiness probes. |

### Logika biznesowa (`src/api/services/`)
| Plik | Opis |
|------|------|
| `src/api/services/__init__.py` | Plik inicjalizacyjny pakietu serwisów. Grupuje moduły task_service i cache_service. |
| `src/api/services/task_service.py` | Serwis operacji na zadaniach (warstwa biznesowa). Oddziela logikę CRUD od endpointów, integruje cache Redis i zapewnia unieważnianie cache po modyfikacjach. |
| `src/api/services/cache_service.py` | Serwis cache Redis (wzorzec Cache-Aside). Obsługuje get/set/delete z TTL, graceful degradation (aplikacja działa bez Redis) i unieważnianie wg wzorca. |

### Frontend (`src/api/templates/` i `src/api/static/`)
| Plik | Opis |
|------|------|
| `src/api/templates/base.html` | Bazowy szablon HTML (Jinja2). Zdefiniowano strukturę strony: sidebar z nawigacją, header ze wyszukiwarką i statusem API, sloty na zawartość dynamiczną. |
| `src/api/templates/index.html` | Strona główna — tablica Kanban z zadaniami. Zawiera karty statystyk, filtry, 3 kolumny (Todo/W toku/Zrobione) i modal dodawania/edycji zadań. |
| `src/api/static/css/style.css` | Arkusz stylów — ciemny motyw z efektem glassmorphism. Responsywna siatka, mikro-animacje, karty zadań z kolorowym wskaźnikiem priorytetu, powiadomienia Toast. |
| `src/api/static/js/app.js` | Logika kliencka JavaScript (fetch API). Obsługuje CRUD zadań, drag-and-drop między kolumnami, filtrowanie/sortowanie, health check i powiadomienia Toast. |

### Reverse Proxy (`src/nginx/`)
| Plik | Opis |
|------|------|
| `src/nginx/Dockerfile` | Obraz Nginx oparty na Alpine. Podmienia domyślną konfigurację na własną i dodaje health check. |
| `src/nginx/nginx.conf` | Konfiguracja Nginx jako reverse proxy. Przekierowuje ruch z portu 80 do API (upstream), włącza kompresję gzip i logowanie. |

### Testy (`tests/`)
| Plik | Opis |
|------|------|
| `tests/__init__.py` | Plik inicjalizacyjny pakietu testów. |
| `tests/conftest.py` | Fixtures pytest — konfiguracja testowa. Tworzy bazę SQLite in-memory, nadpisuje zależność `get_db` i dostarcza klienta HTTP (httpx) do testów endpointów. |
| `tests/test_tasks.py` | 12 testów CRUD zadań. Pokrywają tworzenie, odczyt, aktualizację, usuwanie, walidację, filtrowanie po statusie i paginację. |
| `tests/test_health.py` | Testy endpointów monitoringu. Sprawdzają odpowiedź `/` (HTML z TaskFlow) i `/health` (status, baza danych, Redis). |

### Skrypty pomocnicze (`scripts/`)
| Plik | Opis |
|------|------|
| `scripts/setup-local.sh` | Skrypt konfiguracji środowiska na macOS. Sprawdza/instaluje Docker, kubectl, Minikube, Helm przez Homebrew i tworzy plik `.env`. |
| `scripts/cleanup.sh` | Skrypt czyszczenia środowiska. Zatrzymuje kontenery Docker, opcjonalnie usuwa woluminy/obrazy i czyści pliki tymczasowe Pythona. |

### Dokumentacja (`docs/`)
| Plik | Opis |
|------|------|
| `docs/zarys_pracy_magisterskiej.md` | Zarys pracy magisterskiej — 9 rozdziałów. Zawiera spis treści, opis każdego podrozdziału z odniesieniami do aplikacji TaskFlow (perspektywa 3. osoby). |
| `docs/deployment-local.md` | Instrukcja wdrożenia lokalnego (Docker Compose). Krok po kroku: instalacja Dockera, uruchomienie, weryfikacja, polecenia cURL i rozwiązywanie problemów. |
| `docs/dziennik_wdrozenia.md` | Ten plik — dziennik wdrożenia i spis plików. |

---

## Chronologia kroków wdrożenia

### Krok 1 — Analiza wymagań i plan implementacji
**Co:** Przeanalizowano temat pracy magisterskiej, zdefiniowano wymagania, zaproponowano aplikację „TaskFlow" i stos technologiczny.
**Dlaczego:** Przed rozpoczęciem kodowania niezbędne jest zrozumienie zakresu pracy i wybranie technologii, które najlepiej demonstrują podejście DevOps — konteneryzację, orkiestrację i CI/CD.
**Rezultat:** Plan implementacji z 6 fazami, diagramy architektury (Docker Compose, Kubernetes, CI/CD pipeline), struktura repozytorium.

---

### Krok 2 — Fundament projektu (struktura i konfiguracja)
**Co:** Utworzono strukturę katalogów, `.gitignore`, `.env.example`, `Makefile`, `README.md` i `requirements.txt`.
**Dlaczego:** Standardowa struktura projektu ułatwia orientację w kodzie, a pliki konfiguracyjne zapewniają powtarzalność środowiska — każdy deweloper pracuje z tymi samymi wersjami pakietów i zmiennymi.
**Rezultat:** Szkielet projektu gotowy do wypełnienia kodem.

---

### Krok 3 — Backend API (FastAPI + SQLAlchemy + Redis)
**Co:** Zaimplementowano kompletny backend:
- `config.py` — konfiguracja z env vars (pydantic-settings, wzorzec Singleton)
- `database.py` — asynchroniczne połączenie z PostgreSQL (SQLAlchemy 2.0 + asyncpg)
- `models.py` — model Task z Enumami Priority/Status i soft-delete
- `schemas.py` — schematy Pydantic v2 (walidacja, serializacja, dokumentacja OpenAPI)
- `routes/tasks.py` — 5 endpointów CRUD z wersjonowaniem API (`/api/v1/`)
- `routes/health.py` — health check i metryki (dla Kubernetes probes)
- `services/task_service.py` — warstwa biznesowa z integracją cache
- `services/cache_service.py` — Redis cache (wzorzec Cache-Aside, graceful degradation)

**Dlaczego:** FastAPI zapewnia automatyczną dokumentację Swagger, asynchroniczność dla wydajności I/O oraz wbudowaną walidację Pydantic. Separacja warstw (routes → services → database) to wzorzec Repository/Service Layer — ułatwia testowanie i rozszerzanie. Redis Cache-Aside przyspiesza odczyty i demonstruje warstwę cache w architekturze mikroserwisowej.
**Rezultat:** Kompletne REST API z operacjami CRUD, filtrowaniem, paginacją, sortowaniem i monitoringiem.

---

### Krok 4 — Testy jednostkowe (pytest + httpx)
**Co:** Napisano 14 testów:
- `test_tasks.py` — 12 testów CRUD (tworzenie, odczyt, aktualizacja, usuwanie, walidacja pustego tytułu, filtrowanie po statusie, paginacja)
- `test_health.py` — 2 testy monitoringu (endpoint główny, health check)
- `conftest.py` — fixtures z bazą SQLite in-memory i nadpisaniem zależności `get_db`

**Dlaczego:** Testy automatyczne są kluczowym elementem metodyki DevOps (Continuous Integration). SQLite in-memory zamiast PostgreSQL upraszcza testy — nie wymaga zewnętrznej bazy danych. Nadpisanie `get_db` (Dependency Override) izoluje testy od produkcyjnej infrastruktury.
**Rezultat:** Suite testowy pokrywający kluczowe ścieżki aplikacji, gotowy do uruchamiania w pipeline CI.

---

### Krok 5 — Konteneryzacja (Docker + Docker Compose)
**Co:** Przygotowano:
- `src/api/Dockerfile` — multi-stage build (builder → production), użytkownik nie-root, health check
- `src/nginx/Dockerfile` — obraz Nginx Alpine z własną konfiguracją
- `src/nginx/nginx.conf` — reverse proxy z upstream, gzip, logowanie
- `docker-compose.yml` — 4 serwisy (API, PostgreSQL, Redis, Nginx) z health checkami, limitami zasobów, siecią bridge i woluminami

**Dlaczego:** Konteneryzacja jest centralnym tematem pracy. Multi-stage build zmniejsza rozmiar obrazu (~60% mniej). Użytkownik nie-root zwiększa bezpieczeństwo. Docker Compose umożliwia uruchomienie całej infrastruktury jednym poleceniem `docker-compose up -d`. Limity zasobów symulują środowisko Kubernetes.
**Rezultat:** Aplikacja gotowa do uruchomienia lokalnego w kontenerach Docker.

---

### Krok 6 — Skrypty pomocnicze i dokumentacja wdrożenia
**Co:** Utworzono:
- `scripts/setup-local.sh` — automatyczna instalacja Docker, kubectl, Minikube, Helm na macOS
- `scripts/cleanup.sh` — czyszczenie kontenerów, woluminów i plików tymczasowych
- `docs/deployment-local.md` — instrukcja krok po kroku (Docker Desktop → compose up → weryfikacja cURL)

**Dlaczego:** Automatyzacja powtarzalnych czynności jest fundamentem DevOps. Skrypty eliminują błędy ludzkie przy konfiguracji środowiska. Dokumentacja wdrożeniowa umożliwia odtworzenie środowiska na dowolnym komputerze.
**Rezultat:** Pełna instrukcja od instalacji narzędzi po uruchomienie i testowanie aplikacji.

---

### Krok 7 — Zarys pracy magisterskiej
**Co:** Opracowano dokument `docs/zarys_pracy_magisterskiej.md` z 9 rozdziałami:
1. Wstęp  2. Przegląd DevOps  3. Porównanie chmur  4. Integracja narzędzi DevOps  5. Konteneryzacja i K8s  6. Koszty chmurowe  7. Implementacja TaskFlow  8. Dokumentacja  9. Wnioski

**Dlaczego:** Zarys pracy stanowi mapę drogową dla pisania tekstu pracy magisterskiej. Każdy podrozdział zawiera opis tematyki oraz odniesienie do konkretnego elementu aplikacji TaskFlow — co ułatwia powiązanie teorii z praktyką.
**Rezultat:** Kompletny szkielet pracy magisterskiej z opisem zawartości każdego rozdziału.

---

### Krok 8 — Inicjalizacja Git i push na GitHub
**Co:** Zainicjalizowano lokalne repozytorium Git, dodano wszystkie pliki, utworzono commit `feat: inicjalizacja projektu TaskFlow, Faza 1 i 2`, a następnie połączono z nowym repozytorium na GitHub i wypchnięto kod.
**Dlaczego:** Kontrola wersji (Git) jest fundamentem DevOps — umożliwia śledzenie zmian, współpracę i integrację z pipeline CI/CD (GitHub Actions). Zdalne repozytorium na GitHub stanowi centralny punkt prawdy (single source of truth).
**Rezultat:** Kod źródłowy dostępny na GitHub, gotowy do dalszej pracy i integracji z CI/CD.

---

### Krok 9 — Frontend (Jinja2 + CSS + JavaScript) [Faza 3]
**Co:** Zaimplementowano panel użytkownika:
- `templates/base.html` — szablon bazowy z sidebar, header, slotami
- `templates/index.html` — tablica Kanban (3 kolumny: Todo/W toku/Zrobione), statystyki, filtry, modal
- `static/css/style.css` — ciemny motyw, glassmorphism, responsywność, mikro-animacje
- `static/js/app.js` — fetch API (CRUD), drag-and-drop, filtrowanie/sortowanie, powiadomienia Toast
- Zaktualizowano `main.py` — dodano StaticFiles, Jinja2Templates, endpoint `/` renderuje HTML

**Dlaczego:** Frontend umożliwia prezentację aplikacji promotorowi bez znajomości cURL/Swagger. Tablica Kanban intuicyjnie wizualizuje przepływ zadań. Ciemny motyw i glassmorphism tworzą profesjonalny wygląd. Drag-and-drop między kolumnami automatycznie zmienia status zadania przez API.
**Rezultat:** Pełnofunkcjonalny panel webowy do zarządzania zadaniami, zintegrowany z backendem API.

---

## Następne kroki (planowane)

### Krok 10 — Kubernetes (Faza 4)
Przygotowanie manifestów YAML (Deployment, StatefulSet, Service, Ingress, ConfigMap, Secrets, PVC, HPA) oraz skryptu wdrożenia na Minikube.

### Krok 11 — CI/CD Pipeline (Faza 5)
Konfiguracja GitHub Actions: lint (flake8, black) → testy (pytest) → build Docker → push do registry → deploy na Kubernetes.

### Krok 12 — Monitoring + Dokumentacja końcowa (Faza 6)
Integracja Prometheus + Grafana, dokumentacja wdrożenia chmurowego (AWS/Azure/GCP), porównanie platform i analiza kosztów.
