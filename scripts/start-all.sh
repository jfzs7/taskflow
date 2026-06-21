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

# 2. Uruchomienie tunelu Ingress w osobnym oknie
echo ""
echo "🔌 Uruchamianie tunelu Ingress w nowym oknie Terminala..."
echo "Wprowadź hasło administratora w nowo otwartym oknie terminala, aby powiązać porty 80/443."

# Pobranie bezwzględnej ścieżki do minikube
MINIKUBE_PATH=$(which minikube || echo "minikube")

# Uruchomienie tunelu w nowym oknie terminala macOS
osascript -e "tell app \"Terminal\" to do script \"$MINIKUBE_PATH tunnel\""

echo "✅ Proces uruchamiania tunelu został zainicjowany w nowym oknie."
echo ""
echo "========================================"
echo "  🚀 Wszystkie serwisy są gotowe!"
echo "========================================"
echo "  🔗 Aplikacja:   http://taskflow.local"
echo "  🔗 Prometheus:  http://taskflow.local/prometheus"
echo "  🔗 Grafana:     http://taskflow.local/grafana"
echo "========================================"
echo ""
