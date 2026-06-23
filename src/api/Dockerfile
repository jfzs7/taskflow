# ============================================
# Dockerfile — serwis API (FastAPI + Uvicorn)
#
# Multi-stage build: etap 1 instaluje zaleznosci,
# etap 2 kopiuje tylko gotowe paczki — mniejszy obraz, mniej podatnosci.
# ============================================

# --- Etap 1: Builder ---
# Instalujemy zależności do /install, nie do systemu.
# Dzieki temu etap 2 nie musi zawierac pip ani narzedziowych pakietow.
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Etap 2: Production ---
FROM python:3.12-slim AS production

LABEL maintainer="Jakub Francuz"
LABEL description="TaskFlow API — system zarzadzania zadaniami"
LABEL version="1.0.0"

WORKDIR /app

# Kopiujemy tylko zainstalowane paczki z buildera (bez pip, gcc itp.)
COPY --from=builder /install /usr/local

# Kopiujemy kod aplikacji
COPY . .

# Aplikacja dziala jako niepriwilejowany uzytkownik — dobra praktyka bezpieczenstwa.
# Nawet jezeli atakujacy przejmie kontener, nie ma uprawnien roota.
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 8000

# Docker sam sprawdza co 30s czy aplikacja odpowiada.
# Przydatne do wykrywania "zamrozonych" procesow ktore nie obsługuja ruchu.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# --workers 2: dwa procesy Uvicorn (dostosowac do liczby CPU).
# --proxy-headers: poprawne odczytywanie X-Forwarded-For od Nginx.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
