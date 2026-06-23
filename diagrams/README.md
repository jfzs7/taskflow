# Diagramy Architektoniczne — TaskFlow

Ten katalog zawiera diagramy architektoniczne systemu TaskFlow w formacie **PlantUML** (`.puml`).

## Jak wyrenderować diagramy?

### Opcja 1: Wtyczka VS Code (Zalecane)
1. Zainstaluj wtyczkę **PlantUML** (autor: `jebbs`) w VS Code.
2. Zainstaluj Javę (wymagana przez wtyczkę): `brew install --cask temurin`
3. Otwórz dowolny plik `.puml` i naciśnij `Alt+D` (lub `Option+D` na Mac).

### Opcja 2: Online (bez instalacji)
Skopiuj zawartość wybranego pliku `.puml` i wklej na stronie:
**https://www.plantuml.com/plantuml/uml/**

### Opcja 3: Wiersz poleceń (CLI)
```bash
# Instalacja (wymagana Java)
brew install plantuml

# Generowanie PNG z wszystkich diagramow
plantuml diagrams/*.puml
```

---

## Opis Diagramow

### 1. `c4_container_diagram.puml` — Diagram Kontenerow (Model C4, Level 2)
Wysokopoziomowy widok architektury systemu w standardzie C4. Przedstawia wszystkie komponenty systemu (Nginx, FastAPI, PostgreSQL, Redis, Prometheus, Grafana) jako osobne "kontenery" oraz relacje i protokoly komunikacji miedzy nimi.

### 2. `deployment_diagram.puml` — Diagram Wdrozenia (UML Deployment)
Widok infrastrukturalny i operacyjny systemu. Prezentuje fizyczny (logiczny) podzial komponentow na wezly Kubernetes: pody, serwisy (Services), PersistentVolumeClaims, HPA oraz integracje z pipeline CI/CD (GitHub Actions + GHCR).

### 3. `sequence_create_task.puml` — Diagram Sekwencji: Tworzenie zadania
Ilustruje przepływ danych dla operacji `POST /api/v1/tasks/`. Pokazuje krok po kroku: walidacje danych wejsciowych przez Pydantic, zapis do PostgreSQL, mechanizm inwalidacji cache w Redis oraz budowanie odpowiedzi HTTP 201.

### 4. `sequence_get_tasks_cache.puml` — Diagram Sekwencji: Pobieranie zadan (Cache-Aside)
Szczegolowo ilustruje wzorzec **Cache-Aside (Lazy Loading)** dla operacji `GET /api/v1/tasks/`. Pokazuje dwie galezi: Cache HIT (szybka odpowiedz z Redis) oraz Cache MISS (odpytanie PostgreSQL i zapisanie wyniku do cache na 60s).
