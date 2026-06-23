# Makefile — Skróty poleceń projektu TaskFlow
# Zestaw komend ułatwiających
# uruchamianie, testowanie i wdrażanie aplikacji.
# ============================================

.PHONY: help dev test lint format docker-up docker-down docker-build clean

# --- Pomoc ---
help: ## Wyświetla listę dostępnych poleceń
	@echo "TaskFlow — Dostępne polecenia:"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Rozwój lokalny ---
dev: ## Uruchamia serwer deweloperski (bez Dockera)
	cd src/api && ../../.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

# --- Testy ---
test: ## Uruchamia testy jednostkowe z pokryciem kodu
	cd src/api && ../../.venv/bin/python3 -m pytest ../../tests/ -v --cov=. --cov-report=term-missing 2>&1 | tee ../../tests/test.txt

test-quick: ## Uruchamia testy bez raportu pokrycia
	cd src/api && ../../.venv/bin/python3 -m pytest ../../tests/ -v 2>&1 | tee ../../tests/test.txt

# --- Jakość kodu ---
lint: ## Sprawdza jakość kodu (flake8)
	.venv/bin/flake8 src/ tests/ --max-line-length=120 --exclude=__pycache__,venv,.venv

format: ## Formatuje kod (black)
	.venv/bin/black src/ tests/ --line-length=120

format-check: ## Sprawdza formatowanie kodu bez zmian
	.venv/bin/black src/ tests/ --line-length=120 --check

# --- Docker ---
docker-build: ## Buduje obrazy Docker
	docker-compose build

docker-up: ## Uruchamia aplikację w kontenerach Docker
	docker-compose up -d

docker-down: ## Zatrzymuje kontenery Docker
	docker-compose down

docker-logs: ## Wyświetla logi kontenerów
	docker-compose logs -f

docker-restart: ## Restartuje kontenery Docker
	docker-compose down && docker-compose up -d

# --- Kubernetes (Minikube) ---
k8s-deploy: ## Wdraża aplikację na Minikube
	./scripts/deploy-minikube.sh

k8s-delete: ## Usuwa aplikację z Minikube
	kubectl delete namespace taskflow --ignore-not-found

k8s-status: ## Sprawdza status podów w Kubernetes
	kubectl get all -n taskflow

# --- Czyszczenie ---
clean: ## Czyści pliki tymczasowe
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete 2>/dev/null || true
