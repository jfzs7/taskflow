# Instrukcja wdrożenia lokalnego — TaskFlow

## Wymagania systemowe

Przygotowano listę wymagań do uruchomienia aplikacji lokalnie:

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
1. Pobrano instalator z: https://docs.docker.com/desktop/install/mac-install/
2. Przeciągnięto Docker.app do folderu Applications
3. Uruchomiono Docker Desktop
4. Zweryfikowano instalację:
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
# Skopiowano szablon zmiennych środowiskowych
cp .env.example .env

# Opcjonalnie: edytowano plik .env (domyślne wartości są wystarczające)
```

### Krok 3: Budowanie i uruchomienie
```bash
# Zbudowano obrazy Docker i uruchomiono kontenery
docker-compose up -d --build

# Sprawdzono status kontenerów
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
# Sprawdzono health check
curl http://localhost/health

# Sprawdzono API (odpowiedź JSON)
curl http://localhost/api/v1/tasks/

# Otworzono dokumentację Swagger UI
open http://localhost:8000/docs
```

## Przydatne polecenia

| Polecenie | Opis |
|-----------|------|
| `docker-compose up -d` | Uruchomiono kontenery w tle |
| `docker-compose down` | Zatrzymano kontenery |
| `docker-compose logs -f` | Wyświetlono logi (na żywo) |
| `docker-compose logs api` | Logi tylko serwisu API |
| `docker-compose restart api` | Restartowano serwis API |
| `docker-compose build --no-cache` | Przebudowano obrazy od zera |
| `docker-compose ps` | Sprawdzono status kontenerów |

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
# Sprawdzono logi konkretnego kontenera
docker-compose logs api

# Sprawdzono, czy porty nie są zajęte
lsof -i :80
lsof -i :8000
lsof -i :5432
```

### Baza danych nie odpowiada
```bash
# Sprawdzono stan kontenera PostgreSQL
docker-compose exec postgres pg_isready -U taskflow_user

# Połączono się z bazą bezpośrednio
docker-compose exec postgres psql -U taskflow_user -d taskflow
```

### Reset danych
```bash
# Usunięto kontenery i woluminy (UWAGA: dane zostaną utracone)
docker-compose down -v
docker-compose up -d --build
```
