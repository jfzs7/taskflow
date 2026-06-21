#!/bin/bash
# ============================================
# stop-all.sh — Pełne zatrzymanie środowiska i zwolnienie zasobów
# ============================================

echo "========================================"
# Zatrzymywanie środowiska aplikacji i monitoringu
echo "  TaskFlow — Zatrzymywanie środowiska"
echo "========================================"
echo ""

# 1. Zatrzymanie tunelu Ingress działającego w tle
echo "🛑 Zatrzymywanie tunelu Ingress..."
sudo pkill -f "minikube tunnel" 2>/dev/null || true
rm -f minikube_tunnel.log
echo "  ✅ Tunel zatrzymany."
echo ""

# 2. Zatrzymanie klastra Minikube
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    echo "☸️ Zatrzymywanie klastra Minikube..."
    minikube stop
    echo "  ✅ Minikube został wyłączony."
else
    echo "  ℹ️ Minikube jest już zatrzymany."
fi
echo ""

# 3. Zatrzymanie ewentualnych kontenerów Docker Compose
echo "🐳 Zatrzymywanie kontenerów Docker Compose..."
docker-compose down --remove-orphans 2>/dev/null || true
echo "  ✅ Kontenery Docker Compose zatrzymane."
echo ""

# 4. Czyszczenie plików tymczasowych
echo "🧹 Czyszczenie plików tymczasowych..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  ✅ Pliki tymczasowe usunięte."

echo ""
echo "========================================"
echo "  🛑 Wszystkie serwisy zostały zatrzymane!"
echo "========================================"
echo ""
