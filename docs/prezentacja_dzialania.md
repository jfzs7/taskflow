# Scenariusz Demonstracji Projektu TaskFlow

Dokument zawiera kompletny plan przebiegu demonstracji systemu TaskFlow. Opisuje wybrane technologie, strukturę plików, kluczowe fragmenty kodu oraz kroki wdrożenia i weryfikacji aplikacji w terminalu.

---

## 1. Wykorzystane technologie i ich rola w systemie

System TaskFlow składa się z następujących komponentów technologicznych:

*   **FastAPI (Python 3.12)**: Framework do budowy serwera backendowego. Umożliwia szybką i w pełni asynchroniczną obsługę zapytań HTTP. Dostarcza automatycznie generowaną dokumentację Swagger UI.
*   **PostgreSQL 16**: Relacyjna baza danych. Służy do bezpiecznego, trwałego i ustrukturyzowanego przechowywania danych o zadaniach.
*   **Redis 7**: Szybka pamięć podręczna w pamięci RAM. Przyspiesza działanie systemu poprzez unikanie powtarzalnych zapytań do bazy danych PostgreSQL.
*   **Nginx**: Serwer WWW działający jako pośrednik (reverse proxy). Zabezpiecza serwer aplikacji, obsługuje kompresję przesyłanych danych oraz rozdziela ruch sieciowy.
*   **Docker / Docker Compose**: Środowisko kontenerowe. Umożliwia spakowanie aplikacji wraz ze wszystkimi zależnościami w jeden spójny pakiet, gwarantując identyczne działanie systemu na każdym komputerze.
*   **Kubernetes (Minikube)**: System orkiestracji kontenerów. Odpowiada za automatyczne uruchamianie, monitorowanie stanu zdrowia, skalowanie replik oraz kierowanie ruchem w środowisku klastrowym.
*   **GitHub Actions**: Automatyczny system CI/CD. Odpowiada za testowanie kodu przy każdej zmianie oraz automatyczne budowanie i publikowanie obrazów kontenerów w rejestrze GHCR.

---

## 2. Struktura katalogów i kluczowe pliki projektu

Główne katalogi i pliki w repozytorium:
*   [docker-compose.yml](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/docker-compose.yml) — plik konfiguracji lokalnego środowiska Docker.
*   [Makefile](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/Makefile) — skróty poleceń ułatwiające uruchamianie testów i kontenerów.
*   `k8s/` — folder z manifestami konfiguracyjnymi Kubernetes:
    *   [k8s/namespace.yaml](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/k8s/namespace.yaml) — dedykowana przestrzeń nazw `taskflow`.
    *   [k8s/configmap.yaml](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/k8s/configmap.yaml) / [k8s/secrets.yaml](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/k8s/secrets.yaml) — konfiguracja zmiennych i hasła w Base64.
    *   `k8s/postgres/` — pliki wdrożeniowe bazy danych SQL (StatefulSet, Service, PVC).
    *   `k8s/redis/` — pliki wdrożeniowe pamięci podręcznej Redis (StatefulSet, Service, PVC).
    *   `k8s/api/` — pliki wdrożeniowe backendu FastAPI (Deployment z 2 replikami, Service, HPA).
    *   `k8s/nginx/` — pliki wdrożeniowe serwera proxy (Deployment, Service NodePort, ConfigMap).
    *   [k8s/ingress.yaml](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/k8s/ingress.yaml) — routing dla domeny `taskflow.local`.
*   `src/api/` — kod źródłowy backendu i interfejsu WWW:
    *   [src/api/main.py](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/src/api/main.py) — główny plik serwera FastAPI, middleware metryk Prometheus.
    *   [src/api/routes/tasks.py](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/src/api/routes/tasks.py) — endpointy REST API dla operacji CRUD.
    *   [src/api/routes/health.py](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/src/api/routes/health.py) — endpointy sprawdzające stan klastra `/health` oraz eksportujące dane `/prometheus`.
    *   [src/api/services/cache_service.py](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/src/api/services/cache_service.py) — logika integracji cache Redis (wzorzec Cache-Aside).
    *   `src/api/templates/` — szablony HTML (Jinja2) oraz kod interfejsu (CSS/JS).
*   `tests/` — folder z automatycznymi testami jednostkowymi i integracyjnymi.
*   `scripts/` — skrypty powłoki Bash automatyzujące instalację (`setup-local.sh`) i wdrożenie (`deploy-minikube.sh`).

---

## 3. Dokumentacja projektu

Dokumentację systemu sporządzono w formacie Markdown (pliki `.md`), co umożliwia bezpośredni podgląd w repozytorium GitHub. Zlokalizowana jest w folderze `docs/`:
1.  [dokumentacja_techniczna.md](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/docs/dokumentacja_techniczna.md) — specyfikacja techniczna (architektura, baza danych, opis API).
2.  [dokumentacja_uzytkowa.md](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/docs/dokumentacja_uzytkowa.md) — podręcznik instalacji i obsługi aplikacji.
3.  [dziennik_wdrozenia.md](file:///Users/jakubfrancuz/Library/CloudStorage/GoogleDrive-jakub.francuz7@gmail.com/Mój dysk/praca_magisterska/docs/dziennik_wdrozenia.md) — chronologiczny zapis prac wraz ze spisem wszystkich utworzonych plików.

---

## 4. Scenariusz demonstracji (Krok po kroku)

### Krok 1: Prezentacja kodu i testów automatycznych w konsoli
Pokazanie, jak wygląda weryfikacja poprawności działania oprogramowania bez konieczności uruchamiania całej infrastruktury.
*   **Działanie**: Uruchom polecenie testowe w terminalu:
    ```bash
    python3 -m pytest tests/ -v
    ```
*   **Omawiane zagadnienie**: Wyjaśnienie, że testy jednostkowe są w pełni automatyczne, pokrywają kluczowe funkcje API (tworzenie zadań, soft-delete, healthcheck) i korzystają z bazy danych w pamięci RAM (`sqlite in-memory`), co przyspiesza ich wykonanie.

### Krok 2: Uruchomienie lokalnego środowiska Docker Compose
Pokazanie procesu uruchomienia aplikacji w kontenerach na maszynie deweloperskiej.
*   **Działanie**: Wpisz w terminalu:
    ```bash
    make docker-up
    ```
    Następnie sprawdź stan kontenerów:
    ```bash
    docker-compose ps
    ```
*   **Omawiane zagadnienie**: Zwrócenie uwagi, że jednym poleceniem uruchomiono 4 kontenery (API, PostgreSQL, Redis, Nginx), które są w pełni odizolowane, a ich komunikacja odbywa się przez wewnętrzną, zamkniętą sieć wirtualną Dockera.

### Krok 3: Demonstracja działania interfejsu WWW
Pokazanie funkcjonalności samej aplikacji.
*   **Działanie**: Otwórz w przeglądarce adres `http://localhost`. Dodaj nowe zadanie za pomocą formularza, przeciągnij je (drag-and-drop) do kolumny "W toku", a następnie usuń jedno z zadań klikając w ikonę kosza.
*   **Omawiane zagadnienie**: Wyjaśnienie, że każda akcja użytkownika wywołuje asynchroniczne żądanie API. Przeniesienie zadania aktualizuje rekord w bazie danych SQL oraz natychmiastowo unieważnia klucze w cache Redis (wzorzec Cache-Aside), zapewniając brak rozbieżności w danych.

### Krok 4: Wdrożenie aplikacji w klastrze Kubernetes
Pokazanie działania systemu w środowisku klastrowym (Minikube).
*   **Działanie**: Zatrzymaj kontenery lokalne (`make docker-down`), a następnie uruchom skrypt wdrożenia klastra:
    ```bash
    ./scripts/deploy-minikube.sh
    ```
    W nowym oknie terminala otwórz tunel dostępowy do serwisu:
    ```bash
    minikube service nginx-svc -n taskflow
    ```
*   **Omawiane zagadnienie**: Wyjaśnienie, że skrypt automatycznie buduje obraz lokalnie w rejestrze Minikube, konfiguruje przestrzeń nazw, limity zasobów, trwałe woluminy dla baz danych (StatefulSets) oraz 2 repliki aplikacji API w celu zapewnienia bezprzerwowego działania w przypadku awarii jednego z kontenerów.

### Krok 5: Prezentacja metryk i monitoringu (Prometheus + Grafana)
Pokazanie mechanizmów obserwowania systemu w czasie rzeczywistym.
*   **Działanie**:
    1.  Pokaż surowy endpoint `/prometheus` wygenerowany przez aplikację.
    2.  Otwórz panel serwera Prometheus, wpisując w nowym terminalu:
        ```bash
        minikube service prometheus-svc -n taskflow
        ```
        (Można tam wpisać zapytanie `taskflow_requests_total` lub `taskflow_tasks_total` w zakładce Graph i zobaczyć wykres).
    3.  Otwórz graficzny panel Grafana:
        ```bash
        minikube service grafana-svc -n taskflow
        ```
        (Logowanie: `admin` / `admin`. Wyszukaj dodane automatycznie źródło danych Prometheus).
*   **Omawiane zagadnienie**: Wyjaśnienie, że aplikacja na bieżąco rejestruje ruch sieciowy i stan zadań, a serwer Prometheus zbiera te dane w klastrze. Grafana pozwala na tworzenie zaawansowanych pulpitów managerskich (Dashboards) do wizualizacji tych parametrów w czasie rzeczywistym.


### Krok 6: Pokazanie automatyzacji CI/CD na GitHubie
Wskazanie na automatyczne zapewnianie jakości.
*   **Działanie**: Otwórz stronę projektu na platformie GitHub i przejdź do zakładki **Actions**. Pokaz historię ostatnich potoków wdrożeniowych.
*   **Omawiane zagadnienie**: Zademonstrowanie, że każdy zatwierdzony zapis kodu (commit) uruchamia proces CI (testy, jakość kodu) oraz CD (automatyczne budowanie produkcyjnych obrazów Docker i wypychanie ich do rejestru GHCR).
