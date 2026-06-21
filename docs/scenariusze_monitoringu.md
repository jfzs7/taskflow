# Scenariusze Monitoringu i Obserwowalności (Prometheus + Grafana)

Dokument przedstawia praktyczne scenariusze demonstracji działania systemu monitoringu w aplikacji **TaskFlow** uruchomionej w klastrze Kubernetes. Scenariusze te doskonale nadają się do prezentacji przed promotorem i komisją, pokazując praktyczne zastosowanie koncepcji **DevOps** i **SRE** (Site Reliability Engineering) w projekcie.

---

## Wymagania wstępne (Setup)

Przed rozpoczęciem scenariuszy upewnij się, że:
1. Klaster Minikube jest wdrożony i działa:
   ```bash
   ./scripts/deploy-minikube.sh
   ```
2. Domena `taskflow.local` jest zmapowana w pliku `/etc/hosts`:
   ```text
   <IP_MINIKUBE> taskflow.local
   ```
3. Tunel dostępowy Ingress działa w osobnym terminalu:
   ```bash
   minikube tunnel
   ```
4. Masz dostęp do paneli w przeglądarce:
   * **Aplikacja WWW**: [http://taskflow.local](http://taskflow.local)
   * **Prometheus**: [http://taskflow.local/prometheus](http://taskflow.local/prometheus)
   * **Grafana**: [http://taskflow.local/grafana](http://taskflow.local/grafana)

---

## Scenariusz 1: Monitorowanie stanu aplikacji (Metryki Biznesowe / Stanowe)

**Cel**: Zademonstrowanie, jak zmiany w bazie danych i działania użytkowników w GUI są w czasie rzeczywistym odzwierciedlane w systemie monitorowania bez odpytywania samej bazy danych SQL.

### Krok 1: Weryfikacja stanu początkowego
1. Otwórz panel Prometheus i przejdź do zakładki **Graph**.
2. Wpisz i uruchom zapytanie:
   ```promql
   taskflow_tasks_total
   ```
   Zwrócona wartość będzie równa aktualnej liczbie zadań w systemie (np. `0` jeśli system jest pusty).
3. Sprawdź liczbę zadań według statusu:
   ```promql
   taskflow_tasks_by_status
   ```
   Zobaczysz podział na etykiety `status="todo"`, `status="in_progress"`, `status="done"`.

### Krok 2: Generowanie zmian w aplikacji
1. Otwórz tablicę Kanban [http://taskflow.local](http://taskflow.local).
2. Dodaj 3 nowe zadania:
   * *Zadanie A* (Priorytet: Niski)
   * *Zadanie B* (Priorytet: Średni)
   * *Zadanie C* (Priorytet: Wysoki)
3. Przeciągnij *Zadanie B* do kolumny **W toku**, a *Zadanie C* do kolumny **Zakończone**.

### Krok 3: Obserwacja w monitoringu
1. Wróć do panelu Prometheus i uruchom ponownie:
   ```promql
   taskflow_tasks_total
   ```
   Wartość wzrośnie do `3`.
2. Uruchom zapytanie o statusy:
   ```promql
   taskflow_tasks_by_status
   ```
   Powinieneś zobaczyć wartości:
   * `{status="todo"} => 1`
   * `{status="in_progress"} => 1`
   * `{status="done"} => 1`
3. W panelu Grafana ([http://taskflow.local/grafana](http://taskflow.local/grafana)) stwórz prosty wykres typu **Gauge** lub **Stat** dla tych metryk. Pokazuje to, jak menedżerowie projektu mogą w czasie rzeczywistym obserwować postęp prac zespołu (np. wskaźnik przepustowości Kanban).

---

## Scenariusz 2: Test obciążeniowy i skalowanie horyzontalne (HPA)

**Cel**: Zademonstrowanie reakcji infrastruktury na nagły skok ruchu sieciowego (tzw. "Slashdot effect") oraz automatycznego skalowania replik (Auto-scaling) przez Kubernetes.

### Krok 1: Przygotowanie monitorowania podów
Otwórz terminal i uruchom ciągły podgląd statusu Horizontal Pod Autoscaler (HPA) oraz podów API:
```bash
kubectl get hpa,pods -n taskflow -w
```
Zwróć uwagę na aktualne zużycie CPU (powinno być bliskie `0%` lub `1%`) oraz liczbę replik backendu API (domyślnie `2`).

### Krok 2: Uruchomienie generatora obciążenia
W osobnym oknie terminala uruchomimy prosty skrypt w pętli generujący setki zapytań do API backendu.
Możesz użyć wbudowanego w macOS narzędzia curl w pętli:
```bash
# Pętla wysyłająca zapytania GET do listy zadań tak szybko, jak to możliwe
while true; do curl -s -o /dev/null -w "%{http_code}\n" http://taskflow.local/api/v1/tasks/; done
```
*(Alternatywnie, jeśli masz zainstalowane narzędzie `ab` (ApacheBench), możesz uruchomić: `ab -n 10000 -c 50 http://taskflow.local/api/v1/tasks/`)*.

### Krok 3: Obserwacja reakcji systemu
1. **W Prometheus/Grafana**: Uruchom zapytanie obrazujące ruch (żądania na sekundę):
   ```promql
   rate(taskflow_requests_total[1m])
   ```
   Zobaczysz gwałtowny skok wykresu przedstawiający liczbę obsłużonych zapytań na sekundę.
2. **W terminalu (HPA)**: Po około 1-2 minutach stałego obciążenia wskaźnik CPU w poleceniu `kubectl get hpa` przekroczy zdefiniowany próg `50%` (np. wzrośnie do `120%`).
3. **Skalowanie**: Kubernetes automatycznie podejmie decyzję o wyskalowaniu wdrożenia. Zobaczysz uruchamianie nowych podów API (liczba wzrośnie z `2` do np. `4` lub maksymalnie `5` w zależności od obciążenia).
4. **Zatrzymanie testu**: Wyłącz pętlę w terminalu (`Ctrl + C`). Po kilku minutach bezczynności HPA zauważy spadek obciążenia i bezpiecznie zmniejszy liczbę replik z powrotem do wartości `2` (skalowanie w dół / cool-down).

---

## Scenariusz 3: Monitorowanie błędów i wykrywanie anomalii (Metryki Techniczne)

**Cel**: Zademonstrowanie, jak SRE/DevOps może natychmiast wykryć problemy z integracją lub błędy aplikacji (np. złe zapytania klientów, ataki) za pomocą analizy kodów statusu HTTP.

### Krok 1: Weryfikacja poprawnych zapytań
W standardowym trybie pracy aplikacja zwraca głównie kody `200` (OK) lub `201` (Created).
Wpisując w Prometheus:
```promql
sum(rate(taskflow_requests_total{http_status="200"}[5m]))
```
Widzimy stabilny ruch oznaczający poprawne działanie systemu.

### Krok 2: Generowanie błędów walidacji (HTTP 422 Unprocessable Entity)
Spróbujmy celowo wysłać niepoprawne żądanie do API (np. utworzenie zadania bez wymaganego pola `title`):
```bash
# Wyślij błędny payload (pusty słownik)
for i in {1..50}; do
  curl -X POST http://taskflow.local/api/v1/tasks/ \
    -H "Content-Type: application/json" \
    -d '{}' -s -o /dev/null
done
```

### Krok 3: Obserwacja wykrywania błędów
1. **W Prometheus**: Wpisz zapytanie filtrujące błędy klienta:
   ```promql
   taskflow_requests_total{http_status="422"}
   ```
   Licznik dla kodu statusu `422` natychmiast wzrośnie o `50`.
2. **Obliczanie współczynnika błędów (Error Rate %)**: W systemach produkcyjnych najważniejszą metryką jest procentowy udział błędów w całym ruchu. Możemy go obliczyć za pomocą następującego wyrażenia PromQL:
   ```promql
   sum(rate(taskflow_requests_total{http_status=~"[45].."}[2m])) / sum(rate(taskflow_requests_total[2m])) * 100
   ```
   To zapytanie pokazuje, jaki procent wszystkich zapytań z ostatnich 2 minut stanowiły błędy typu 4xx i 5xx. W trakcie naszego testu wykres ten gwałtownie skoczy w górę.
3. **Zastosowanie**: Na tej podstawie w Grafanie konfiguruje się **Alerty** (np. wysyłanie powiadomienia na Slack/Discord, jeśli współczynnik błędów przekroczy 5% w ciągu minuty).
