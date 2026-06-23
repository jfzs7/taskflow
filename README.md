# TaskFlow — Mikroserwisowy System Zarządzania Zadaniami

[![CI Pipeline](https://github.com/TWOJ_USERNAME/taskflow/actions/workflows/ci.yml/badge.svg)](https://github.com/TWOJ_USERNAME/taskflow/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue.svg)](https://kubernetes.io/)

## 📋 Opis projektu

**TaskFlow** to mikroserwisowy system zarządzania zadaniami.

Aplikacja demonstruje podejście DevOps na etapie projektowania, wdrażania i zarządzania skonteneryzowaną aplikacją klastrową z wykorzystaniem orkiestratora Kubernetes.

## 🏗️ Architektura

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│    Nginx         │────▶│  FastAPI      │────▶│ PostgreSQL   │
│  (Reverse Proxy) │     │  (Backend)   │     │  (Baza danych)│
│    Port: 80      │     │  Port: 8000  │     │  Port: 5432  │
└─────────────────┘     └──────┬───────┘     └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │    Redis     │
                        │   (Cache)    │
                        │  Port: 6379  │
                        └──────────────┘
```

## 🛠️ Stos technologiczny

| Warstwa | Technologia |
|---------|-------------|
| Backend API | Python 3.12 + FastAPI |
| Baza danych | PostgreSQL 16 |
| Cache | Redis 7 |
| Reverse Proxy | Nginx |
| ORM | SQLAlchemy 2.0 (async) |
| Konteneryzacja | Docker + Docker Compose |
| Orkiestracja | Kubernetes (Minikube) |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |
| Testy | pytest + httpx |

## 🚀 Szybki start

### Wymagania
- Docker i Docker Compose
- (opcjonalnie) Python 3.12+ (do lokalnego developmentu)

### Uruchomienie z Docker Compose
```bash
# Sklonowano repozytorium
git clone https://github.com/TWOJ_USERNAME/taskflow.git
cd taskflow

# Skopiowano plik zmiennych środowiskowych
cp .env.example .env

# Uruchomiono aplikację
docker-compose up -d

# Sprawdzono status
docker-compose ps

# Otworzono w przeglądarce
# Aplikacja: http://localhost
# Swagger UI: http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

### Uruchomienie lokalne (bez Dockera)
```bash
# Utworzono środowisko wirtualne
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Zainstalowano zależności
pip install -r src/api/requirements.txt

# Uruchomiono serwer deweloperski
cd src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 Dokumentacja API

Po uruchomieniu aplikacji dokumentacja API jest dostępna pod adresami:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testy

```bash
# Uruchomiono testy
make test

# Lub bezpośrednio
cd src/api && python -m pytest ../../tests/ -v --cov=.
```

## 📁 Struktura projektu

```
taskflow/
├── src/api/              # Backend FastAPI
│   ├── main.py           # Punkt wejścia
│   ├── config.py         # Konfiguracja
│   ├── database.py       # Połączenie z bazą
│   ├── models.py         # Modele SQLAlchemy
│   ├── schemas.py        # Schematy Pydantic
│   ├── routes/           # Endpointy API
│   └── services/         # Logika biznesowa
├── tests/                # Testy jednostkowe
├── k8s/                  # Manifesty Kubernetes
├── docs/                 # Dokumentacja
├── docker-compose.yml    # Lokalne wdrożenie
└── Makefile              # Skróty poleceń
```

## 📄 Licencja

Projekt opracowany w celach edukacyjnych.
