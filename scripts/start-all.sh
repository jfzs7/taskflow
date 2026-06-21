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

# Upewnienie się, że ingress controller ma typ LoadBalancer (wymagane dla poprawnego mapowania portów na macOS)
echo "🔧 Konfigurowanie usługi Ingress jako LoadBalancer..."
kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec": {"type": "LoadBalancer"}}' 2>/dev/null || true

# Uruchomienie tunelu w nowym oknie terminala macOS i wyciągnięcie go na pierwszy plan
osascript -e "tell app \"Terminal\" to do script \"$MINIKUBE_PATH tunnel\""
osascript -e 'tell app "Terminal" to activate'

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
