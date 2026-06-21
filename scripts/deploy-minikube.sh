#!/bin/bash
# ============================================
# deploy-minikube.sh — Wdrożenie aplikacji na klastrze Minikube
#
# Skrypt automatyzujący uruchamianie środowiska lokalnego
# Kubernetes, budowanie obrazu kontenera API oraz aplikację
# wszystkich manifestów w dedykowanej przestrzeni nazw.
# ============================================

# Przerwanie działania w przypadku jakiegokolwiek błędu
set -e

echo "========================================"
# To rozpoczyna wdrożenie na Minikube
echo "  TaskFlow — Wdrożenie na Minikube"
# ========================================
echo ""

# --- Weryfikacja uruchomienia Minikube ---
if ! minikube status &> /dev/null; then
    echo "⚠️  Minikube nie jest uruchomiony. Uruchamianie klastra..."
    minikube start --driver=docker
else
    echo "✅ Minikube działa poprawnie."
fi

# --- Włączenie wymaganych dodatków (Addons) ---
echo ""
echo "🔌 Konfiguracja dodatków Minikube..."
minikube addons enable ingress
minikube addons enable metrics-server

# --- Konfiguracja Docker-env ---
echo ""
echo "🐳 Przełączanie środowiska Docker na Minikube..."
# To pozwala budować obrazy bezpośrednio wewnątrz rejestru Minikube
eval $(minikube docker-env)

# --- Budowanie obrazu aplikacji ---
echo ""
echo "🏗️  Budowanie obrazu taskflow-api wewnątrz Minikube..."
docker build -t taskflow-api:latest -f src/api/Dockerfile src/api

# --- Aplikacja manifestów Kubernetes ---
echo ""
echo "🚀 Aplikacja manifestów Kubernetes..."

# Przestrzeń nazw, konfiguracja i sekrety
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Baza danych PostgreSQL
kubectl apply -f k8s/postgres/pvc.yaml
kubectl apply -f k8s/postgres/service.yaml
kubectl apply -f k8s/postgres/statefulset.yaml

# Pamięć podręczna Redis
kubectl apply -f k8s/redis/pvc.yaml
kubectl apply -f k8s/redis/service.yaml
kubectl apply -f k8s/redis/statefulset.yaml

# Serwis API
kubectl apply -f k8s/api/service.yaml
kubectl apply -f k8s/api/deployment.yaml
kubectl apply -f k8s/api/hpa.yaml

# Serwer proxy Nginx
kubectl apply -f k8s/nginx/configmap.yaml
kubectl apply -f k8s/nginx/service.yaml
kubectl apply -f k8s/nginx/deployment.yaml

# Routing Ingress
kubectl apply -f k8s/ingress.yaml

# --- Monitorowanie wdrożenia ---
echo ""
echo "⏳ Oczekiwanie na gotowość wdrożeń..."
kubectl rollout status deployment/api -n taskflow --timeout=120s
kubectl rollout status deployment/nginx -n taskflow --timeout=120s

echo ""
echo "========================================"
echo "  ✅ Wdrożenie zakończone pomyślnie!"
echo "========================================"
echo ""
echo "Aplikacja jest dostępna pod adresem:"
# Pobranie adresu IP Minikube i portu dla Nginx NodePort
MINIKUBE_IP=$(minikube ip)
NODE_PORT=$(kubectl get svc nginx-svc -n taskflow -o jsonpath='{.spec.ports[0].nodePort}')
echo "  🔗 Interfejs WWW: http://$MINIKUBE_IP:$NODE_PORT"
echo "  🔗 Dokumentacja API: http://$MINIKUBE_IP:$NODE_PORT/docs"
echo ""
echo "Możesz także użyć tunelu dla Ingress (wymaga podania hasła sudo):"
echo "  1. Dodaj wpis do /etc/hosts: '$MINIKUBE_IP taskflow.local'"
echo "  2. Uruchom tunel: 'minikube tunnel'"
echo "  3. Otwórz: http://taskflow.local"
echo ""
