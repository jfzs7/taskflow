# Analiza Roli DevOps w Zarządzaniu Kosztami i Zasobami Chmurowymi (FinOps)

Dokument opisuje koszty uruchomienia architektury mikroserwisowej w chmurze publicznej, porównuje ceny podstawowych usług u głównych dostawców oraz przedstawia praktyki optymalizacyjne FinOps realizowane za pomocą narzędzi DevOps.

---

## 1. Szacunkowe koszty miesięczne infrastruktury chmurowej (AWS vs Azure vs GCP)

Poniższe zestawienie przedstawia szacunkowy koszt utrzymania środowiska produkcyjnego dla aplikacji o skali TaskFlow (klaster Kubernetes o rozmiarze 2 małych węzłów, baza danych SQL, pamięć cache Redis, transfer sieciowy oraz przechowywanie sekretów) przy założeniu cen z roku 2026 w regionie europejskim (Frankfurt / Irlandia).

*Ceny są szacunkami orientacyjnymi dla konfiguracji o niskim zapotrzebowaniu.*

| Usługa chmurowa | AWS | Azure | GCP |
|-----------------|-----|-------|-----|
| **Zarządzany klaster K8s** | ~73 USD (EKS Control Plane) + ~40 USD (2x t3.medium) | ~0 USD (AKS Free Tier) + ~42 USD (2x Standard_B2s) | ~0 USD (GKE Autopilot/Zone) + ~45 USD (2x e2-medium) |
| **Baza danych PostgreSQL** | ~30 USD (db.t4g.small - single AZ) | ~28 USD (Standard_D2ds_v5) | ~32 USD (db-f1-micro / db-custom-1-3840) |
| **Redis Cache** | ~17 USD (cache.t4g.micro) | ~16 USD (Basic C0) | ~18 USD (Basic 1GB) |
| **Transfer sieciowy (100GB)**| ~9 USD (data egress) | ~8 USD | ~8 USD |
| **Zarządzanie sekretami** | ~0.40 USD | ~0.03 USD | ~0.06 USD |
| **SUMA MIESIĘCZNIE** | **~169.40 USD** | **~94.03 USD** | **~103.06 USD** |

---

## 2. Rola procesów DevOps w redukcji kosztów chmurowych (Praktyki FinOps)

Podejście FinOps (połączenie finansów, biznesu i inżynierii) opiera się na ciągłym monitorowaniu i optymalizacji zasobów w chmurze za pomocą automatyzacji DevOps.

### Praktyka 1: Automatyczne skalowanie (Autoscaling)
Użycie HPA (Horizontal Pod Autoscaler) oraz CA (Cluster Autoscaler) pozwala na dopasowanie liczby maszyn w chmurze do aktualnego ruchu.
*   **Optymalizacja**: W godzinach nocnych pody API są skalowane w dół do minimum (np. 1-2 replik), co pozwala na wyłączenie nadmiarowych maszyn wirtualnych (węzłów klastra) i generuje oszczędności na poziomie 30-40%.

### Praktyka 2: Wykorzystanie Instancji Niskobudżetowych (Spot / Preemptible VMs)
*   **Opis**: Dostawcy chmury sprzedają nadwyżki mocy obliczeniowej z rabatami sięgającymi 70-90%. Wadą jest możliwość odebrania instancji przez dostawcę w dowolnym momencie z krótkim wyprzedzeniem (np. 30 sekund).
*   **Zastosowanie w DevOps**: Bezstanowa warstwa aplikacji API w klastrze Kubernetes jest idealnym kandydatem do działania na instancjach typu Spot. Dzięki replikacji (np. 2-3 pody) i mechanizmom restartów K8s, nagłe usunięcie jednej maszyny nie wpływa na dostępność aplikacji dla użytkownika końcowego.

### Praktyka 3: Bezserwerowe kontenery (Serverless Containers)
Dla aplikacji o nieregularnym ruchu, tańszą alternatywą od utrzymywania dedykowanego klastra Kubernetes są serwisy typu Serverless:
*   **Serwisy**: AWS Fargate, Azure Container Apps, Google Cloud Run.
*   **Optymalizacja**: Umożliwiają skalowanie aplikacji "do zera" (scale-to-zero) — gdy aplikacja nie odbiera ruchu, opłata za procesor i RAM wynosi 0 USD.

---

## 3. Odniesienie do struktury TaskFlow

Wdrożone w projekcie rozwiązania wspierają powyższe praktyki FinOps:
1.  **Limity zasobów (Resource Limits)**: W plikach `api/deployment.yaml` i `nginx/deployment.yaml` precyzyjnie określono minimalne gwarantowane zasoby (`requests`) oraz maksymalne (`limits`). Zapobiega to nadmiarowej alokacji maszyn chmurowych i ułatwia optymalne upakowanie podów (bin packing) na węzłach.
2.  **Horizontal Pod Autoscaler (`api/hpa.yaml`)**: Umożliwia dynamiczne skalowanie warstwy API w chmurze, redukując liczbę aktywnych podów przy braku obciążenia.
3.  **Headless Services i StatefulSets**: Umożliwiają łatwe planowanie układu baz danych i pamięci podręcznej, minimalizując narzut sieciowy i koszty związane z transferem danych pomiędzy strefami dostępności (cross-AZ traffic).
