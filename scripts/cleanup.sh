#!/bin/bash
# ============================================
# cleanup.sh — Skrypt czyszczenia środowiska
#
# Skrypt usuwający kontenery, woluminy
# i dane tymczasowe projektu TaskFlow.
# ============================================

set -e

echo "========================================"
echo "  TaskFlow — Czyszczenie środowiska"
echo "========================================"
echo ""

# --- Zatrzymanie kontenerów Docker Compose ---
echo "🐳 Zatrzymywanie kontenerów Docker Compose..."
docker-compose down --remove-orphans 2>/dev/null || true
echo "  ✅ Kontenery zatrzymane."

# --- Usunięcie zasobów Kubernetes ---
if command -v kubectl &> /dev/null; then
    read -p "Czy usunąć zasoby z klastra Kubernetes (namespace taskflow)? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "☸️ Usuwanie przestrzeni nazw taskflow z Kubernetes..."
        kubectl delete namespace taskflow --ignore-not-found=true
        echo "  ✅ Zasoby Kubernetes usunięte."
    else
        echo "  ℹ️ Zasoby Kubernetes zachowane."
    fi
fi

# --- Usunięcie woluminów (opcjonalnie) ---
read -p "Czy usunąć woluminy danych Docker (PostgreSQL, Redis)? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker volume rm taskflow-postgres-data taskflow-redis-data 2>/dev/null || true
    echo "  ✅ Woluminy usunięte."
else
    echo "  ℹ️  Woluminy zachowane."
fi

# --- Usunięcie obrazów Docker (opcjonalnie) ---
read -p "Czy usunąć zbudowane obrazy Docker? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi $(docker images "praca_magisterska*" -q) 2>/dev/null || true
    echo "  ✅ Obrazy usunięte."
else
    echo "  ℹ️  Obrazy zachowane."
fi

# --- Usunięcie plików tymczasowych Python ---
echo "🧹 Czyszczenie plików tymczasowych..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name ".coverage" -delete 2>/dev/null || true
find . -type f -name "test_taskflow.db" -delete 2>/dev/null || true
echo "  ✅ Pliki tymczasowe usunięte."

echo ""
echo "========================================"
echo "  ✅ Czyszczenie zakończone!"
echo "========================================"
