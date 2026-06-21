#!/bin/bash
# ============================================
# start-all.sh — Pełny start środowiska (Minikube + Ingress + Aplikacja)
# ============================================

set -e

echo "========================================"
# Uruchomienie pełnego stosu aplikacyjnego i monitoringu
echo "  TaskFlow — Uruchamianie środowiska"
echo "========================================"
echo ""

# 1. Wywołanie głównego skryptu wdrożenia Kubernetes
./scripts/deploy-minikube.sh

# 2. Uruchomienie tunelu Ingress w tle
echo ""
echo "🔑 Uruchamianie tunelu Ingress..."
echo "Skrypt wymaga uprawnień sudo do powiązania Ingress z portami 80/443."

# Odświeżenie sesji sudo (zapyta o hasło tylko raz)
sudo -v

# Zatrzymanie poprzednich tuneli jeśli wisiały w tle
sudo pkill -f "minikube tunnel" 2>/dev/null || true

# Uruchomienie tunelu w tle i zapisanie logów
sudo nohup minikube tunnel > minikube_tunnel.log 2>&1 &

echo "✅ Tunel Ingress został pomyślnie uruchomiony w tle."
echo "   Logi tunelu są zapisywane w pliku: minikube_tunnel.log"
echo ""
echo "========================================"
echo "  🚀 Wszystkie serwisy są gotowe!"
echo "========================================"
echo "  🔗 Aplikacja:   http://taskflow.local"
echo "  🔗 Prometheus:  http://taskflow.local/prometheus"
echo "  🔗 Grafana:     http://taskflow.local/grafana"
echo "========================================"
echo ""
