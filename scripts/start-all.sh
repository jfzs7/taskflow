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

# 2. Informacja o tunelu Ingress
echo ""
echo "🔌 Konfigurowanie usługi Ingress jako LoadBalancer..."
kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec": {"type": "LoadBalancer"}}' 2>/dev/null || true

echo ""
echo "👉 Aby udostępnić usługi, otwórz nową kartę terminala i wpisz:"
echo "   minikube tunnel"
echo "   (wymagane będzie podanie hasła administratora)"
echo ""

echo "========================================"
echo "  🚀 Wszystkie serwisy są gotowe!"
echo "========================================"
echo "  🔗 Aplikacja:   http://taskflow.local"
echo "  🔗 Prometheus:  http://taskflow.local/prometheus"
echo "  🔗 Grafana:     http://taskflow.local/grafana"
echo "========================================"
echo ""
