# Porównanie Wdrażania Aplikacji w Chmurach Publicznych (AWS vs Azure vs GCP)

Dokument zawiera porównanie usług, narzędzi DevOps oraz metod wdrażania skonteneryzowanych aplikacji w trzech wiodących chmurach publicznych: Amazon Web Services (AWS), Microsoft Azure oraz Google Cloud Platform (GCP).

---

## 1. Mapowanie usług dla aplikacji mikroserwisowej (np. TaskFlow)

Wdrożenie aplikacji wielokontenerowej (API + Baza danych + Cache + Proxy) wymaga skorzystania z określonych typów usług chmurowych. Poniższa tabela przedstawia odpowiedniki usług w poszczególnych chmurach:

| Warstwa infrastruktury | AWS | Azure | GCP |
|------------------------|-----|-------|-----|
| **Orkiestracja (Kubernetes)** | Amazon EKS (Elastic Kubernetes Service) | AKS (Azure Kubernetes Service) | GKE (Google Kubernetes Engine) |
| **Rejestr kontenerów** | Amazon ECR (Elastic Container Registry) | ACR (Azure Container Registry) | Artifact Registry |
| **Zarządzana relacyjna baza danych** | Amazon RDS for PostgreSQL | Azure Database for PostgreSQL | Cloud SQL for PostgreSQL |
| **Zarządzana pamięć cache** | Amazon ElastiCache for Redis | Azure Cache for Redis | Memorystore for Redis |
| **Kierowanie ruchem (Load Balancer)** | Application Load Balancer (ALB) | Azure Application Gateway / LB | Cloud Load Balancing |
| **Zarządzanie sekretami** | AWS Secrets Manager | Azure Key Vault | Secret Manager |

---

## 2. Analiza porównawcza platform Kubernetes (EKS vs AKS vs GKE)

### Amazon EKS (AWS):
*   **Charakterystyka**: Bardzo dojrzała i stabilna usługa, o wysokim poziomie bezpieczeństwa i integracji z IAM (Identity and Access Management).
*   **Zalety**: Szerokie możliwości konfiguracji sieciowej (VPC CNI) oraz wysoka stabilność środowisk produkcyjnych.
*   **Wady**: Trudniejsza w konfiguracji początkowej w porównaniu do konkurentów. Domyślnie płatna opłata za godzinę utrzymania samego klastra kontrolnego (Control Plane).

### Azure AKS (Microsoft):
*   **Charakterystyka**: Doskonała integracja z systemem tożsamości Microsoft Entra ID (dawniej Active Directory) oraz ekosystemem narzędzi Microsoftu.
*   **Zalety**: Brak dodatkowej opłaty za Control Plane w wersji standardowej (płaci się tylko za maszyny węzłów), bardzo prosty w integracji z Azure DevOps.
*   **Wady**: Zdarzają się przejściowe problemy z wydajnością konsoli zarządzania lub opóźnienia w aktualizacjach wersji Kubernetes.

### Google GKE (GCP):
*   **Charakterystyka**: Najbardziej zaawansowana i intuicyjna usługa Kubernetes na rynku. Google, jako twórca Kubernetes, dostarcza najbardziej zoptymalizowane środowisko.
*   **Zalety**: Niezrównane mechanizmy automatycznego skalowania klastra (Autopilot), szybkie czasy uruchamiania podów i bezproblemowe aktualizacje bez przestojów.
*   **Wady**: Mniejsza popularność w przedsiębiorstwach o ugruntowanej infrastrukturze Microsoft.

---

## 3. Integracja Narzędzi CI/CD z Usługami Chmurowymi

Potoki wdrażania (CD) mogą być realizowane na dwa sposoby: przy użyciu natywnych narzędzi chmurowych lub narzędzi zewnętrznych (np. GitHub Actions).

### Podejście A: Natywne narzędzia chmurowe (Vendor Lock-in)
*   **AWS**: AWS CodePipeline, CodeBuild i CodeDeploy. Pozwalają na bardzo bezpieczne wdrożenia wewnątrz VPC, ale ich konfiguracja w plikach YAML jest mało czytelna i skomplikowana.
*   **Azure**: Azure Pipelines (część Azure DevOps). Jedno z najbardziej rozbudowanych i profesjonalnych narzędzi na rynku, oferujące łatwe wdrożenia do AKS za pomocą dedykowanych zadań (tasks).
*   **GCP**: Google Cloud Build. Prosty, szybki i w pełni bezserwerowy system budowania zintegrowany z Artifact Registry i GKE.

### Podejście B: Narzędzia uniwersalne (np. GitHub Actions)
*   **Opis**: GitHub Actions łączy się z chmurami za pomocą tożsamości federacyjnej **OIDC (OpenID Connect)**. Pozwala to na autoryzację potoków CI/CD bez konieczności przechowywania statycznych kluczy dostępowych (np. AWS Access Key) w sekretach repozytorium.
*   **Zaleta**: Kod potoku wdrożenia (`.github/workflows/`) jest niezależny od dostawcy chmury — zmiana dostawcy chmury wymaga jedynie modyfikacji kroków logowania i adresu docelowego rejestru obrazów kontenerów.

---

## 4. Przenośność Aplikacji (Cloud Portability) w kontekście TaskFlow

Dzięki zastosowaniu standardowych narzędzi DevOps na poziomie kodu i orkiestracji (Docker, manifesty Kubernetes w czystym standardzie YAML), aplikacja TaskFlow charakteryzuje się pełną przenośnością:
*   Manifesty z katalogu `k8s/` mogą zostać zaaplikowane na EKS, AKS oraz GKE bez żadnych modyfikacji w kodzie API czy Nginxa.
*   Jedynym elementem wymagającym dostosowania podczas wdrożenia chmurowego jest konfiguracja dynamicznych klas pamięci (StorageClass) dla dysków trwałych (PVC) oraz integracja z zewnętrznym Ingress Controllerem/Load Balancerem dostawcy chmury.
