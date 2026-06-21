#!/bin/bash
# ============================================
# setup-local.sh — Skrypt konfiguracji środowiska lokalnego
#
# Skrypt automatyzujący instalację wymaganych
# narzędzi na macOS (Docker Desktop, Minikube, kubectl).
# ============================================

set -e

echo "========================================"
echo "  TaskFlow — Konfiguracja środowiska"
echo "========================================"
echo ""

# --- Sprawdzenie systemu operacyjnego ---
OS=$(uname -s)
echo "📋 System operacyjny: $OS"

# --- Funkcja sprawdzania zainstalowanych narzędzi ---
check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "  ✅ $1 — zainstalowany ($(command -v $1))"
        return 0
    else
        echo "  ❌ $1 — NIE zainstalowany"
        return 1
    fi
}

echo ""
echo "🔍 Sprawdzanie wymaganych narzędzi..."
echo ""

# --- Docker ---
if ! check_tool "docker"; then
    echo ""
    echo "📥 Instalacja Docker Desktop..."
    if [ "$OS" = "Darwin" ]; then
        if command -v brew &> /dev/null; then
            brew install --cask docker
            echo "  ✅ Docker Desktop zainstalowany. Uruchom go z Applications."
        else
            echo "  ⚠️  Zainstaluj Docker Desktop ręcznie:"
            echo "     https://docs.docker.com/desktop/install/mac-install/"
        fi
    elif [ "$OS" = "Linux" ]; then
        echo "  ⚠️  Zainstaluj Docker Engine:"
        echo "     https://docker.com/engine/install/"
    fi
fi

# --- Docker Compose ---
check_tool "docker-compose" || check_tool "docker compose"

# --- Python ---
check_tool "python3"

# --- kubectl ---
if ! check_tool "kubectl"; then
    echo ""
    echo "📥 Instalacja kubectl..."
    if [ "$OS" = "Darwin" ] && command -v brew &> /dev/null; then
        brew install kubectl
    else
        echo "  ⚠️  Zainstaluj kubectl ręcznie:"
        echo "     https://kubernetes.io/docs/tasks/tools/"
    fi
fi

# --- Minikube ---
if ! check_tool "minikube"; then
    echo ""
    echo "📥 Instalacja Minikube..."
    if [ "$OS" = "Darwin" ] && command -v brew &> /dev/null; then
        brew install minikube
    else
        echo "  ⚠️  Zainstaluj Minikube ręcznie:"
        echo "     https://minikube.sigs.k8s.io/docs/start/"
    fi
fi

# --- Helm ---
if ! check_tool "helm"; then
    echo ""
    echo "📥 Instalacja Helm..."
    if [ "$OS" = "Darwin" ] && command -v brew &> /dev/null; then
        brew install helm
    else
        echo "  ⚠️  Zainstaluj Helm ręcznie:"
        echo "     https://helm.sh/docs/intro/install/"
    fi
fi

# --- Tworzenie pliku .env ---
echo ""
if [ ! -f ".env" ]; then
    echo "📄 Tworzenie pliku .env z szablonu .env.example..."
    cp .env.example .env
    echo "  ✅ Plik .env utworzony."
else
    echo "  ℹ️  Plik .env już istnieje — pominięto."
fi

echo ""
echo "========================================"
echo "  ✅ Konfiguracja zakończona!"
echo "========================================"
echo ""
echo "Następne kroki:"
echo "  1. Upewnij się, że Docker Desktop jest uruchomiony"
echo "  2. Uruchom aplikację: docker-compose up -d"
echo "  3. Otwórz w przeglądarce: http://localhost"
echo "  4. Dokumentacja API: http://localhost:8000/docs"
echo ""
