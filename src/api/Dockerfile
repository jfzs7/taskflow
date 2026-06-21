# ============================================
# Dockerfile — Obraz Docker serwisu API (FastAPI)
#
# Zastosowano wieloetapowy build (multi-stage) w celu
# optymalizacji rozmiaru końcowego obrazu.
# Etap 1 (builder): instalacja zależności
# Etap 2 (production): obraz produkcyjny bez narzędzi budowania
# ============================================

# --- Etap 1: Builder ---
# Zainstalowano zależności Python w osobnym etapie,
# aby wykorzystać cache warstw Docker.
FROM python:3.12-slim AS builder

WORKDIR /app

# Skopiowano plik zależności jako pierwszy (optymalizacja cache)
COPY requirements.txt .

# Zainstalowano zależności do katalogu /install
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Etap 2: Production ---
# Użyto minimalnego obrazu Python bez narzędzi kompilacji.
FROM python:3.12-slim AS production

# Dodano metadane obrazu (standard OCI)
LABEL maintainer="Jakub Francuz"
LABEL description="TaskFlow API — mikroserwisowy system zarządzania zadaniami"
LABEL version="1.0.0"

WORKDIR /app

# Skopiowano zainstalowane zależności z etapu builder
COPY --from=builder /install /usr/local

# Skopiowano kod źródłowy aplikacji
COPY . .

# Utworzono użytkownika nie-root (najlepsza praktyka bezpieczeństwa)
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Wyeksponowano port aplikacji
EXPOSE 8000

# Skonfigurowano health check na poziomie Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Uruchomiono serwer Uvicorn
# --workers 2: dwa procesy robocze (dostosować do CPU)
# --proxy-headers: obsługa nagłówków proxy (Nginx)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
