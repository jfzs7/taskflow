# Zarys pracy magisterskiej
# Temat: Opracowanie i implementacja aplikacji konteneryzowanej
#         z wykorzystaniem metodyki DevOps
# Autor: Jakub Francuz
# Rok: 2026

---

## Spis treści (proponowany)

1. Wstęp
2. Przegląd zastosowań metodyki DevOps w branży technologicznej
3. Porównanie sposobów wdrażania aplikacji w chmurze z wykorzystaniem procesów DevOps
4. Integracja narzędzi DevOps z chmurowymi usługami
5. Konteneryzacja i zarządzanie infrastrukturą w kontekście chmurowych platform
6. Analiza roli DevOps w zarządzaniu kosztami i zasobami chmurowymi
7. Specyfikacja projektowa i implementacja aplikacji TaskFlow
8. Dokumentacja techniczna i użytkowa
9. Podsumowanie i wnioski
10. Bibliografia
11. Załączniki

---

## Rozdział 1. Wstęp

### 1.1. Wprowadzenie do tematu
Omówiono ewolucję podejść do wytwarzania oprogramowania — od modelu kaskadowego
(Waterfall), przez metodyki zwinne (Agile/Scrum), aż po DevOps jako naturalne rozszerzenie
filozofii ciągłego doskonalenia. Wskazano na rosnące znaczenie automatyzacji procesów
wdrożeniowych i operacyjnych w nowoczesnym wytwarzaniu oprogramowania.

### 1.2. Cel pracy
Celem pracy jest opracowanie i implementacja autorskiej aplikacji konteneryzowanej,
a także omówienie i analiza podejścia DevOps na etapie projektowania, wdrażania
i zarządzania skonteneryzowaną aplikacją klastrową z wykorzystaniem orkiestratora Kubernetes.

### 1.3. Zakres pracy
Opisano zakres pracy obejmujący pięć głównych obszarów tematycznych (rozdziały 2-6)
oraz część praktyczną (rozdziały 7-8).

### 1.4. Struktura pracy
Przedstawiono organizację pracy — krótki opis zawartości każdego rozdziału.

---

## Rozdział 2. Przegląd zastosowań metodyki DevOps w branży technologicznej

### 2.1. Geneza i definicja DevOps
- Przedstawiono historię powstania DevOps (konferencja DevOpsDays, 2009, Patrick Debois).
- Zdefiniowano DevOps jako kulturę, zbiór praktyk i narzędzi łączących rozwój (Dev),
  operacje (Ops) i zapewnienie jakości (QA).
- Omówiono model CALMS (Culture, Automation, Lean, Measurement, Sharing).

### 2.2. Kluczowe praktyki DevOps
- **Continuous Integration (CI)** — ciągła integracja kodu.
  *Odniesienie do aplikacji: Skonfigurowano pipeline CI w GitHub Actions
  automatycznie uruchamiający testy i linting po każdym pushu do repozytorium.*
- **Continuous Delivery/Deployment (CD)** — ciągłe dostarczanie/wdrażanie.
  *Odniesienie do aplikacji: Zaimplementowano automatyczne wdrożenie
  na środowisko staging po merge do gałęzi develop.*
- **Infrastructure as Code (IaC)** — infrastruktura jako kod.
  *Odniesienie do aplikacji: Zdefiniowano infrastrukturę w manifestach
  Kubernetes (YAML) i Helm Charts.*
- **Monitoring i observability** — monitoring i obserwowalność.
  *Odniesienie do aplikacji: Zintegrowano Prometheus i Grafana
  do zbierania i wizualizacji metryk.*

### 2.3. Narzędzia ekosystemu DevOps
Przedstawiono przegląd popularnych narzędzi w podziale na kategorie:

| Kategoria | Narzędzia |
|-----------|-----------|
| Kontrola wersji | Git, GitHub, GitLab |
| CI/CD | GitHub Actions, Jenkins, GitLab CI, CircleCI |
| Konteneryzacja | Docker, Podman, containerd |
| Orkiestracja | Kubernetes, Docker Swarm, Nomad |
| IaC | Terraform, Ansible, Pulumi |
| Monitoring | Prometheus, Grafana, Datadog, New Relic |
| Zarządzanie sekretami | Vault, AWS Secrets Manager |

### 2.4. DevOps w praktyce — studia przypadków
- Przedstawiono przykłady wdrożenia DevOps w firmach technologicznych
  (np. Netflix, Spotify, Amazon).
- Omówiono mierzalne korzyści: skrócenie cyklu wdrożeń, redukcja awarii,
  szybsze odzyskiwanie po incydentach (MTTR).

### 2.5. Raport DORA — metryki efektywności DevOps
- Omówiono cztery kluczowe metryki DORA:
  1. Deployment Frequency (częstotliwość wdrożeń)
  2. Lead Time for Changes (czas od commitu do produkcji)
  3. Change Failure Rate (wskaźnik awarii po wdrożeniu)
  4. Mean Time to Recovery (średni czas odzyskiwania)

---

## Rozdział 3. Porównanie sposobów wdrażania aplikacji w chmurze z wykorzystaniem procesów DevOps (AWS, Azure, Google Cloud)

### 3.1. Modele chmurowe — IaaS, PaaS, SaaS, CaaS
- Zdefiniowano modele usług chmurowych.
- Wskazano, że aplikacja TaskFlow wykorzystuje model CaaS
  (Container as a Service) — Kubernetes zarządzany w chmurze.

### 3.2. Amazon Web Services (AWS)
- **EKS** (Elastic Kubernetes Service) — zarządzany Kubernetes.
- **ECR** (Elastic Container Registry) — rejestr obrazów Docker.
- **RDS** — zarządzana baza PostgreSQL.
- **ElastiCache** — zarządzany Redis.
- **CodePipeline** / GitHub Actions — CI/CD.
- *Odniesienie do aplikacji: Opisano proces wdrożenia TaskFlow na EKS
  z wykorzystaniem tych samych manifestów Kubernetes co lokalnie.*

### 3.3. Microsoft Azure
- **AKS** (Azure Kubernetes Service) — zarządzany Kubernetes.
- **ACR** (Azure Container Registry) — rejestr obrazów.
- **Azure Database for PostgreSQL** — zarządzana baza danych.
- **Azure Cache for Redis** — zarządzany cache.
- **Azure DevOps** / GitHub Actions — CI/CD.
- *Odniesienie do aplikacji: Opisano analogiczny proces wdrożenia na AKS.*

### 3.4. Google Cloud Platform (GCP)
- **GKE** (Google Kubernetes Engine) — zarządzany Kubernetes (najstarszy na rynku).
- **Artifact Registry** — rejestr obrazów.
- **Cloud SQL** — zarządzana baza PostgreSQL.
- **Memorystore** — zarządzany Redis.
- **Cloud Build** / GitHub Actions — CI/CD.
- *Odniesienie do aplikacji: Opisano wdrożenie na GKE.*

### 3.5. Porównanie platform chmurowych

| Kryterium | AWS (EKS) | Azure (AKS) | GCP (GKE) |
|-----------|-----------|-------------|-----------|
| Koszt klastra K8s | ~$72/mies. (control plane) | Darmowy (control plane) | ~$72/mies. (standard) |
| Darmowy tier | 12 mies. Free Tier | $200 kredyt | $300 kredyt |
| Łatwość konfiguracji | Średnia | Wysoka | Najwyższa |
| Integracja z K8s | Dobra | Bardzo dobra | Najlepsza (Google stworzył K8s) |
| Rynkowy udział | Największy (~32%) | Drugi (~22%) | Trzeci (~11%) |

### 3.6. Przenośność aplikacji między chmurami
- Omówiono znaczenie standardów (OCI, Kubernetes API) dla przenośności.
- *Odniesienie do aplikacji: Wykazano, że TaskFlow może zostać wdrożony
  na dowolnej z trzech platform bez modyfikacji kodu — zmianie ulega
  jedynie konfiguracja infrastruktury.*

---

## Rozdział 4. Integracja narzędzi DevOps z chmurowymi usługami

### 4.1. Automatyzacja wdrożeń w chmurze
- Omówiono koncepcję GitOps — infrastruktura i konfiguracja zarządzana w Git.
- Przedstawiono narzędzia: ArgoCD, Flux, GitHub Actions.
- *Odniesienie do aplikacji: Zaimplementowano pipeline CI/CD w GitHub Actions
  automatyzujący: linting → testy → build obrazu Docker → push do registry
  → wdrożenie na Kubernetes.*

### 4.2. Skalowanie aplikacji w chmurze
- **Horizontal Pod Autoscaler (HPA)** — automatyczne skalowanie poziome.
  *Odniesienie do aplikacji: Skonfigurowano HPA dla serwisu API TaskFlow
  (skalowanie 2-10 replik na podstawie CPU/RAM).*
- **Vertical Pod Autoscaler (VPA)** — skalowanie pionowe.
- **Cluster Autoscaler** — skalowanie klastra.

### 4.3. Zarządzanie sekretami i konfiguracją
- Omówiono ConfigMaps i Secrets w Kubernetes.
- Przedstawiono zewnętrzne menedżery sekretów (Vault, AWS Secrets Manager).
- *Odniesienie do aplikacji: Wykorzystano Kubernetes ConfigMap do konfiguracji
  i Secrets do przechowywania haseł bazy danych.*

### 4.4. Service Mesh i networking
- Omówiono koncepcje: Ingress Controller, Service Mesh (Istio, Linkerd).
- *Odniesienie do aplikacji: Skonfigurowano Nginx Ingress Controller
  do routingu ruchu do serwisów TaskFlow.*

### 4.5. Monitoring i alerting w chmurze
- Porównano natywne narzędzia (CloudWatch, Azure Monitor, Cloud Monitoring)
  z rozwiązaniami open-source (Prometheus + Grafana).
- *Odniesienie do aplikacji: Zintegrowano Prometheus do zbierania metryk
  z endpointu /metrics i Grafana do wizualizacji dashboardów.*

---

## Rozdział 5. Konteneryzacja i zarządzanie infrastrukturą w kontekście chmurowych platform

### 5.1. Podstawy konteneryzacji
- Omówiono koncepcję kontenerów vs. maszyny wirtualne.
- Przedstawiono technologię Docker: obrazy, kontenery, rejestry.
- *Odniesienie do aplikacji: Każdy komponent TaskFlow (API, PostgreSQL, Redis, Nginx)
  działa w osobnym kontenerze Docker.*

### 5.2. Dockerfile — budowanie obrazów
- Opisano najlepsze praktyki tworzenia Dockerfile.
- Multi-stage builds — optymalizacja rozmiaru obrazu.
- *Odniesienie do aplikacji: Zastosowano multi-stage build dla obrazu API
  (etap budowania → etap produkcyjny), co zmniejszyło rozmiar obrazu o ~60%.*

### 5.3. Docker Compose — orkiestracja lokalna
- Omówiono docker-compose.yml jako narzędzie orkiestracji na jednym hoście.
- *Odniesienie do aplikacji: Zdefiniowano docker-compose.yml uruchamiający
  4 serwisy (API, PostgreSQL, Redis, Nginx) z jednym poleceniem.*

### 5.4. Kubernetes — orkiestracja klastrowa
- Omówiono kluczowe koncepcje: Pod, Deployment, Service, Ingress,
  ConfigMap, Secret, PersistentVolume, StatefulSet.
- *Odniesienie do aplikacji: Dla każdego komponentu TaskFlow przygotowano
  odpowiednie manifesty Kubernetes.*

### 5.5. Helm — menedżer pakietów Kubernetes
- Omówiono Helm Charts jako szablon manifestów Kubernetes.
- *Odniesienie do aplikacji: Utworzono Helm Chart umożliwiający
  parametryzowane wdrożenie TaskFlow z jednym poleceniem.*

### 5.6. Porównanie lokalnego i chmurowego wdrożenia
- Przedstawiono różnice między Docker Compose (lokalne) a Kubernetes (chmura).
- Omówiono ścieżkę migracji: dev (Compose) → staging (Minikube) → prod (EKS/AKS/GKE).

---

## Rozdział 6. Analiza roli DevOps w zarządzaniu kosztami i zasobami chmurowymi

### 6.1. Model kosztowy chmury obliczeniowej
- Omówiono model pay-as-you-go i rezerwacje zasobów.
- Opisano składniki kosztów: compute, storage, network, managed services.

### 6.2. Optymalizacja kosztów z DevOps
- **Right-sizing** — dopasowanie zasobów (CPU, RAM) do potrzeb.
  *Odniesienie do aplikacji: Zdefiniowano requests/limits w manifestach K8s.*
- **Auto-scaling** — automatyczne skalowanie zmniejszające koszty w okresach niskiego ruchu.
  *Odniesienie do aplikacji: HPA skaluje API od 2 do 10 replik.*
- **Spot/Preemptible Instances** — tańsze instancje dla workloadów odpornych na przerwania.

### 6.3. Szacunkowe koszty wdrożenia TaskFlow

| Komponent | AWS | Azure | GCP |
|-----------|-----|-------|-----|
| Kubernetes (control plane) | $72/mies. | $0 | $72/mies. |
| Worker nodes (2x t3.medium) | ~$60/mies. | ~$60/mies. | ~$50/mies. |
| PostgreSQL (managed) | ~$25/mies. | ~$25/mies. | ~$20/mies. |
| Redis (managed) | ~$15/mies. | ~$15/mies. | ~$15/mies. |
| Load Balancer | ~$18/mies. | ~$18/mies. | ~$18/mies. |
| **Suma** | **~$190/mies.** | **~$118/mies.** | **~$175/mies.** |

*Uwaga: Powyższe koszty są szacunkowe dla minimalnej konfiguracji (2026).*

### 6.4. DevOps a TCO (Total Cost of Ownership)
- Omówiono wpływ automatyzacji na redukcję kosztów operacyjnych.
- Przedstawiono ROI (Return on Investment) wdrożenia DevOps.

### 6.5. FinOps — zarządzanie kosztami chmury
- Omówiono praktykę FinOps jako rozszerzenie DevOps o aspekt finansowy.
- Narzędzia: AWS Cost Explorer, Azure Cost Management, GCP Billing Reports.

---

## Rozdział 7. Specyfikacja projektowa i implementacja aplikacji TaskFlow

### 7.1. Wymagania funkcjonalne
Przedstawiono listę wymagań funkcjonalnych aplikacji:
1. Zarządzanie zadaniami (CRUD): tworzenie, odczyt, edycja, usuwanie.
2. Filtrowanie i sortowanie zadań po statusie, priorytecie.
3. Paginacja wyników.
4. Health check i metryki.
5. Automatyczna dokumentacja API (Swagger/OpenAPI).

### 7.2. Wymagania niefunkcjonalne
- Skalowalność (HPA, load balancing).
- Przenośność (Docker, Kubernetes).
- Bezpieczeństwo (CORS, Secrets, walidacja danych).
- Testowalność (pytest, pokrycie kodu).

### 7.3. Architektura systemu
- Diagram architektury (Docker Compose i Kubernetes).
- Opis warstw: prezentacji, aplikacji, danych.
- Wzorce projektowe: Repository Pattern, Dependency Injection, Cache-Aside.

### 7.4. Model danych
- Diagram ERD (Entity-Relationship Diagram).
- Opis tabeli `tasks` z typami kolumn.
- Typy wyliczeniowe: Priority (low/medium/high/critical),
  Status (todo/in_progress/done/archived).

### 7.5. Implementacja backendu (FastAPI)
- Opis struktury kodu: config, database, models, schemas, routes, services.
- Omówienie kluczowych wzorców:
  - Asynchroniczność (async/await) dla wydajności I/O.
  - Dependency Injection (wstrzykiwanie sesji bazy danych).
  - Pydantic — walidacja i serializacja danych.
  - Soft-delete — bezpieczne usuwanie rekordów.

### 7.6. Implementacja cache (Redis)
- Opis wzorca Cache-Aside (Lazy Loading).
- Strategia unieważniania cache po operacjach zapisu.
- Graceful degradation — aplikacja działa bez Redis.

### 7.7. Konteneryzacja (Docker)
- Analiza Dockerfile (multi-stage build).
- Konfiguracja docker-compose.yml.
- Sieć Docker (bridge network).

### 7.8. Orkiestracja (Kubernetes)
- Opis manifestów: Deployment, StatefulSet, Service, Ingress.
- ConfigMap i Secrets.
- PersistentVolumeClaim dla PostgreSQL i Redis.
- HPA — automatyczne skalowanie.

### 7.9. Pipeline CI/CD (GitHub Actions)
- Opis etapów pipeline: lint → test → build → deploy.
- Konfiguracja workflow dla branchy develop i main.

### 7.10. Testy
- Strategia testowania: testy jednostkowe, integracyjne.
- Pokrycie kodu (code coverage).
- Izolacja testów (SQLite in-memory, dependency override).

---

## Rozdział 8. Dokumentacja techniczna i użytkowa

### 8.1. Dokumentacja techniczna
- Środowisko implementacyjne (Python, FastAPI, Docker, K8s).
- Instrukcja instalacji i konfiguracji.
- Opis API (endpointy, parametry, odpowiedzi).

### 8.2. Dokumentacja użytkowa
- Instrukcja uruchomienia aplikacji (Docker Compose).
- Instrukcja korzystania z API (Swagger UI).
- Instrukcja wdrożenia na Kubernetes (Minikube).

### 8.3. Instrukcja wdrożenia chmurowego
- Kroki wdrożenia na AWS EKS.
- Kroki wdrożenia na Azure AKS.
- Kroki wdrożenia na GCP GKE.

---

## Rozdział 9. Podsumowanie i wnioski

### 9.1. Podsumowanie osiągniętych celów
- Opracowano i zaimplementowano aplikację TaskFlow.
- Zademonstrowano pełen cykl DevOps.
- Wykazano przenośność aplikacji między platformami chmurowymi.

### 9.2. Wnioski
- DevOps znacząco skraca czas wdrożenia i poprawia jakość oprogramowania.
- Konteneryzacja zapewnia przenośność i powtarzalność środowisk.
- Kubernetes umożliwia skalowanie i zarządzanie aplikacjami klastrowymi.
- Automatyzacja CI/CD eliminuje błędy ludzkie w procesie wdrażania.

### 9.3. Kierunki dalszego rozwoju
- Implementacja Service Mesh (Istio).
- Wdrożenie GitOps (ArgoCD).
- Rozszerzenie monitoringu (distributed tracing, Jaeger).
- Dodanie autentykacji i autoryzacji (OAuth2, JWT).

---

## Bibliografia (przykładowe pozycje)

1. Kim G., Humble J., Debois P., Willis J. — „The DevOps Handbook", IT Revolution Press, 2016.
2. Burns B. — „Kubernetes: Up and Running", O'Reilly Media, 2022.
3. Dokumentacja Kubernetes — https://kubernetes.io/docs/
4. Dokumentacja Docker — https://docs.docker.com/
5. Dokumentacja FastAPI — https://fastapi.tiangolo.com/
6. Raport DORA — „Accelerate: State of DevOps", Google Cloud, 2023.
7. AWS Well-Architected Framework — https://aws.amazon.com/architecture/well-architected/
8. Microsoft Azure Architecture Center — https://learn.microsoft.com/en-us/azure/architecture/
9. Google Cloud Architecture Framework — https://cloud.google.com/architecture/framework

---

## Załączniki

- Załącznik A: Kod źródłowy aplikacji TaskFlow (repozytorium GitHub)
- Załącznik B: Manifesty Kubernetes
- Załącznik C: Konfiguracja pipeline CI/CD
- Załącznik D: Screenshoty interfejsu Swagger UI
- Załącznik E: Wyniki testów i raport pokrycia kodu
