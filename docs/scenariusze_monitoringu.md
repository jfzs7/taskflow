# Praktyczne Scenariusze Obserwowalności (Prometheus + Grafana)

Dokument przedstawia **5 zaawansowanych scenariuszy demonstracyjnych** przygotowanych na potrzeby prezentacji przed promotorem i komisją. Scenariusze te pokazują, jak w praktyce działa monitorowanie (obserwowalność) oraz automatyczne alertowanie w systemie **TaskFlow** uruchomionym w klastrze Kubernetes (Minikube).

---

## Wymagania wstępne (Setup)

Przed uruchomieniem scenariuszy upewnij się, że środowisko działa poprawnie:
1. Uruchom aplikację i tunel:
   * **Terminal 1**: `./scripts/start-all.sh`
   * **Terminal 2**: `minikube tunnel` (wymaga hasła administratora)
2. Zmapuj domenę: Upewnij się, że wpis `127.0.0.1 taskflow.local` znajduje się w pliku `/etc/hosts`.
3. Adresy dostępowe w przeglądarce:
   * **Aplikacja**: [http://taskflow.local](http://taskflow.local)
   * **Prometheus**: [http://taskflow.local/prometheus](http://taskflow.local/prometheus)
   * **Grafana**: [http://taskflow.local/grafana](http://taskflow.local/grafana)

---

## Scenariusz 1: Monitorowanie dynamiki i struktury zadań (Metryki Biznesowe)

**Cel**: Zademonstrowanie, jak działania użytkowników w GUI (Kanban) są natychmiast mapowane na metryki Prometheus i prezentowane na biznesowych panelach Grafany.

### 1. Zapytania PromQL do użycia w panelach Grafany:
*   **Całkowita liczba zadań (Wykres typu *Stat* / *Gauge*):**
    ```promql
    taskflow_tasks_total
    ```
*   **Podział zadań na statusy (Wykres typu *Bar Gauge* / *Pie Chart*):**
    ```promql
    taskflow_tasks_by_status
    ```
*   **Podział zadań na priorytety:**
    ```promql
    taskflow_tasks_by_priority
    ```

### 2. Akcja wywołująca (Trigger):
1. Wejdź na [http://taskflow.local](http://taskflow.local) i dodaj np. 4 nowe zadania (przypisz im różne priorytety: *Wysoki*, *Średni*).
2. Przeciągnij część zadań do kolumny **W toku** oraz **Zakończone**.

### 3. Oczekiwany efekt wizualny:
*   W panelu Grafana wykresy kołowe (Pie Charts) i słupkowe automatycznie zmienią swoje proporcje po kolejnym cyklu pobrania metryk (domyślnie co 5s). Pokazuje to zdolność systemu do śledzenia procesów biznesowych bez obciążania głównej bazy danych PostgreSQL zapytaniami typu `COUNT(*)`.

---

## Scenariusz 2: Test obciążeniowy i automatyczne skalowanie (Skalowanie HPA)

**Cel**: Demonstracja reakcji klastra na nagły skok ruchu sieciowego, automatyczne skalowanie podów (HPA) oraz monitorowanie zużycia zasobów CPU.

### 1. Zapytania PromQL do użycia na wykresach Grafany:
*   **Ruch sieciowy (żądania na sekundę):**
    ```promql
    sum(rate(taskflow_requests_total[1m]))
    ```
*   **Liczba aktywnych replik (podów) backendu API:**
    ```promql
    kube_deployment_status_replicas_available{deployment="api", namespace="taskflow"}
    ```

### 2. Reguła Alertu Prometheus (Alerting Rule):
```yaml
alert: APIHighCPUAlert
expr: sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{namespace="taskflow", pod=~"api-.*"}) > 80
for: 1m
labels:
  severity: warning
annotations:
  summary: "Wysokie zużycie CPU na podach API"
```

### 3. Akcja wywołująca (Trigger):
Uruchom w terminalu pętlę generującą wysokie obciążenie (odpytywanie API w nieskończoność):
```bash
while true; do curl -s -o /dev/null -w "%{http_code}\n" http://taskflow.local/api/v1/tasks/; done
```

### 4. Oczekiwany efekt:
*   W Grafanie na wykresie *Ruch sieciowy* pojawi się gwałtowny skok (np. do kilkudziesięciu RPS).
*   Po około minucie, w odpowiedzi na obciążenie CPU, Kubernetes zwiększy liczbę podów API (zobaczysz zmianę na wykresie *Liczba replik* z `2` do np. `4`).
*   W Prometheus w zakładce **Alerts** status alertu `APIHighCPUAlert` przejdzie w stan **PENDING**, a po minucie w **FIRING**.

---

## Scenariusz 3: Symulacja awarii bazy danych PostgreSQL (Krytyczny Alert SRE)

**Cel**: Zademonstrowanie reakcji monitoringu na całkowity brak dostępności kluczowego komponentu systemu (bazy danych SQL) oraz przejście systemu w stan krytycznej awarii.

### 1. Zapytania PromQL do użycia w Grafanie:
*   **Status połączenia z bazą danych (wartość `1` = OK, `0` = Awaria):**
    ```promql
    # Zwraca 0, jeśli baza danych PostgreSQL w `/health` raportuje błąd
    taskflow_database_status
    ```
    *(Wartość metryki jest eksportowana bezpośrednio z FastAPI na podstawie statusu DB).*

### 2. Reguła Alertu Prometheus:
```yaml
alert: PostgresDatabaseDown
expr: taskflow_database_status == 0
for: 10s
labels:
  severity: critical
annotations:
  summary: "KRYTYCZNA AWARIA: Brak połączenia z bazą danych PostgreSQL!"
```

### 3. Akcja wywołująca (Trigger):
Skaluj wdrożenie bazy danych PostgreSQL do `0` replik, symulując jej awarię lub wyłączenie serwera:
```bash
kubectl scale statefulset postgres -n taskflow --replicas=0
```

### 4. Oczekiwany efekt:
*   Aplikacja [http://taskflow.local](http://taskflow.local) wyświetli wskaźnik `API Offline` na czerwono w nagłówku.
*   Wykres statusu bazy danych w Grafanie natychmiast spadnie do wartości `0`.
*   W panelu Prometheus w ciągu 10 sekund wyzwoli się krytyczny alert **PostgresDatabaseDown** w stanie **FIRING**.
*   *Przywrócenie działania*: Przywróć bazę komendą `kubectl scale statefulset postgres -n taskflow --replicas=1`. Wykresy wrócą do normy, a alert wygaśnie.

---

## Scenariusz 4: Wyłączenie cache Redis (Graceful Degradation & Latency Degradation)

**Cel**: Pokazanie mechanizmu *graceful degradation* (aplikacja działa bez Redis, ale wolniej) oraz monitorowanie wpływu braku pamięci podręcznej na czas odpowiedzi API.

### 1. Zapytania PromQL do użycia w Grafanie:
*   **Średnia latencja (czas odpowiedzi) API (w sekundach):**
    ```promql
    sum(rate(taskflow_request_latency_seconds_sum[2m])) / sum(rate(taskflow_request_latency_seconds_count[2m]))
    ```
*   **Status dostępności Redis Cache (wykres typu *State Timeline*):**
    ```promql
    taskflow_redis_status
    ```

### 2. Reguła Alertu Prometheus:
```yaml
alert: RedisCacheUnavailable
expr: taskflow_redis_status == 0
for: 30s
labels:
  severity: warning
annotations:
  summary: "Brak pamięci podręcznej Redis — degradacja wydajności aplikacji"
```

### 3. Akcja wywołująca (Trigger):
1. Wyłącz usługę Redis:
   ```bash
   kubectl scale statefulset redis -n taskflow --replicas=0
   ```
2. Odśwież kilkukrotnie stronę aplikacji [http://taskflow.local](http://taskflow.local), aby wygenerować ruch bezpośrednio do bazy danych.

### 4. Oczekiwany efekt:
*   Aplikacja działa poprawnie (użytkownik nadal widzi i może edytować zadania, bo system pobiera je bezpośrednio z PostgreSQL).
*   Wykres latencji w Grafanie zarejestruje wyraźny wzrost czasu odpowiedzi (ponieważ pomijany jest ultra-szybki odczyt z pamięci RAM).
*   Alert `RedisCacheUnavailable` przejdzie w stan **FIRING** po 30 sekundach.
*   *Przywrócenie*: Włącz ponownie Redis za pomocą: `kubectl scale statefulset redis -n taskflow --replicas=1`.

---

## Scenariusz 5: Monitorowanie błędów HTTP i anomalii w ruchu (Error Rate %)

**Cel**: Prezentacja wykrywania anomalii aplikacji (błędy walidacji formularzy, ataki skanujące serwer) na podstawie procentowego udziału błędnych odpowiedzi.

### 1. Zapytania PromQL do użycia w Grafanie:
*   **Wskaźnik błędów API (Error Rate %):**
    ```promql
    sum(rate(taskflow_requests_total{http_status=~"[45].."}[2m])) / sum(rate(taskflow_requests_total[2m])) * 100
    ```
    *(Wzór wyznacza jaki procent ruchu z ostatnich 2 minut stanowią błędy klienta 4xx i serwera 5xx).*

### 2. Reguła Alertu Prometheus:
```yaml
alert: APIHighErrorRate
expr: (sum(rate(taskflow_requests_total{http_status=~"[45].."}[2m])) / sum(rate(taskflow_requests_total[2m])) * 100) > 15
for: 1m
labels:
  severity: warning
annotations:
  summary: "Wskaźnik błędów HTTP przekroczył 15% całkowitego ruchu!"
```

### 3. Akcja wywołująca (Trigger):
Wyślij w pętli błędne żądania POST (np. brakujący tytuł zadania wywoła walidację FastAPI i zwróci kod `422 Unprocessable Entity`):
```bash
for i in {1..100}; do
  curl -X POST http://taskflow.local/api/v1/tasks/ \
    -H "Content-Type: application/json" \
    -d '{}' -s -o /dev/null
done
```

### 4. Oczekiwany efekt:
*   Na wykresie *Error Rate %* w Grafanie pojawi się pionowa linia wskazująca nagły wzrost do poziomu np. 80-90% błędów w całkowitym ruchu.
*   W panelu Prometheus wyzwolony zostanie alert `APIHighErrorRate`.
