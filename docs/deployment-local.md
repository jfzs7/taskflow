# Instrukcja wdrożenia lokalnego — TaskFlow

## Wymagania systemowe

Lista wymagań do uruchomienia aplikacji lokalnie:

| Narzędzie | Wersja | Cel |
|-----------|--------|-----|
| Docker Desktop | >= 4.0 | Konteneryzacja serwisów |
| Docker Compose | >= 2.0 | Orkiestracja lokalna |
| Python | >= 3.12 (opcjonalnie) | Rozwój bez Dockera |
| Git | >= 2.0 | Kontrola wersji |

## Instalacja Docker Desktop na macOS

### Opcja 1: Homebrew (zalecana)
```bash
brew install --cask docker
```

### Opcja 2: Manualna
1. Pobranie instalatora z: https://docs.docker.com/desktop/install/mac-install/
2. Przeciągnięcie Docker.app do folderu Applications
3. Uruchomienie Docker Desktop
4. Weryfikacja instalacji:
```bash
docker --version
docker-compose --version
```

## Uruchomienie aplikacji

### Krok 1: Klonowanie repozytorium
```bash
git clone https://github.com/TWOJ_USERNAME/taskflow.git
cd taskflow
```

### Krok 2: Konfiguracja zmiennych środowiskowych
```bash
# Kopiowanie szablonu zmiennych środowiskowych
cp .env.example .env

# Opcjonalnie: edycja pliku .env (domyślne wartości są wystarczające)
```

### Krok 3: Budowanie i uruchomienie
```bash
# Budowanie obrazów Docker i uruchomienie kontenerów
docker-compose up -d --build

# Sprawdzenie statusu kontenerów
docker-compose ps
```

Oczekiwany wynik:
```
NAME                STATUS              PORTS
taskflow-api        running (healthy)   0.0.0.0:8000->8000/tcp
taskflow-postgres   running (healthy)   0.0.0.0:5432->5432/tcp
taskflow-redis      running (healthy)   0.0.0.0:6379->6379/tcp
taskflow-nginx      running (healthy)   0.0.0.0:80->80/tcp
```

### Krok 4: Weryfikacja
```bash
# Sprawdzenie health check
curl http://localhost/health

# Sprawdzenie API (odpowiedź JSON)
curl http://localhost/api/v1/tasks/

# Otwarcie dokumentacji Swagger UI
open http://localhost:8000/docs
```

## Przydatne polecenia

| Polecenie | Opis |
|-----------|------|
| `docker-compose up -d` | Uruchomienie kontenerów w tle |
| `docker-compose down` | Zatrzymanie kontenerów |
| `docker-compose logs -f` | Wyświetlenie logów (na żywo) |
| `docker-compose logs api` | Logi tylko serwisu API |
| `docker-compose restart api` | Restart serwisu API |
| `docker-compose build --no-cache` | Przebudowanie obrazów od zera |
| `docker-compose ps` | Sprawdzenie statusu kontenerów |

## Testowanie API przez cURL

### Utworzenie zadania
```bash
curl -X POST http://localhost/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Pierwsze zadanie", "description": "Testowe", "priority": "high"}'
```

### Pobranie listy zadań
```bash
curl http://localhost/api/v1/tasks/
```

### Aktualizacja zadania
```bash
curl -X PATCH http://localhost/api/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### Usunięcie zadania
```bash
curl -X DELETE http://localhost/api/v1/tasks/1
```

## Rozwiązywanie problemów

### Kontener nie uruchamia się
```bash
# Sprawdzenie logów konkretnego kontenera
docker-compose logs api

# Sprawdzenie, czy porty nie są zajęte
lsof -i :80
lsof -i :8000
lsof -i :5432
```

### Baza danych nie odpowiada
```bash
# Sprawdzenie stanu kontenera PostgreSQL
docker-compose exec postgres pg_isready -U taskflow_user

# Połączenie się z bazą bezpośrednio
docker-compose exec postgres psql -U taskflow_user -d taskflow
```

### Reset danych
```bash
# Usunięcie kontenerów i woluminów (UWAGA: dane zostaną utracone)
docker-compose down -v
docker-compose up -d --build
```
