# Dokumentacja Użytkowa — Podręcznik Użytkownika TaskFlow

Podręcznik opisuje wymagania systemowe, sposoby uruchomienia aplikacji w różnych środowiskach oraz instrukcję obsługi interfejsu graficznego i interfejsu API systemu TaskFlow.

---

## 1. Wymagania systemowe

Do uruchomienia i obsługi aplikacji TaskFlow wymagane jest posiadanie zainstalowanych poniższych pakietów oprogramowania:

| Narzędzie | Wymagana wersja | Opis i cel |
|-----------|-----------------|------------|
| **Docker Desktop** | `>= 4.0` | Środowisko uruchomieniowe kontenerów (macOS, Windows, Linux). |
| **Docker Compose** | `>= 2.0` | Narzędzie do uruchamiania konfiguracji wielokontenerowych. |
| **Minikube** | `>= 1.30` | Lokalny jednowęzłowy klaster Kubernetes. |
| **kubectl** | `>= 1.25` | Narzędzie wiersza poleceń do zarządzania klastrem Kubernetes. |
| **Przeglądarka internetowa** | Nowoczesna (Chrome, Firefox, Safari) | Obsługa interfejsu graficznego. |

---

## 2. Instrukcja uruchomienia aplikacji

Aplikację można uruchomić na dwa sposoby: lokalnie za pomocą **Docker Compose** (rozwiązanie lżejsze, przeznaczone do rozwoju aplikacji) lub w klastrze **Kubernetes (Minikube)** (rekomendowane do testów skalowalności i orkiestracji).

### Metoda A: Uruchomienie przez Docker Compose (szybkie uruchomienie)
1.  Otwórz terminal w katalogu głównym projektu.
2.  Przygotuj plik zmiennych środowiskowych:
    ```bash
    cp .env.example .env
    ```
3.  Zbuduj i uruchom kontenery w tle:
    ```bash
    make docker-up  # lub: docker-compose up -d --build
    ```
4.  Aplikacja jest dostępna w przeglądarce pod adresem: [http://localhost](http://localhost).
5.  Dokumentacja API (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs).
6.  Zatrzymanie aplikacji:
    ```bash
    make docker-down  # lub: docker-compose down
    ```

### Metoda B: Uruchomienie w klastrze Kubernetes (Minikube)
1.  Upewnij się, że aplikacja Docker Desktop jest włączona.
2.  Uruchom skrypt automatycznego wdrożenia:
    ```bash
    ./scripts/deploy-minikube.sh
    ```
3.  Po zakończeniu budowania skrypt wyświetli wewnętrzny adres IP Minikube i port, pod którym aplikacja jest dostępna (np. `http://192.168.49.2:30080`).
4.  **Dla macOS**: Z powodu ograniczeń sieciowych systemu macOS, aby otworzyć aplikację w przeglądarce, wykonaj w osobnym terminalu polecenie:
    ```bash
    minikube service nginx-svc -n taskflow
    ```
    Tunel otworzy aplikację automatycznie w domyślnej przeglądarce (np. pod adresem `http://127.0.0.1:55801`).

---

## 3. Instrukcja obsługi interfejsu graficznego (GUI)

Interfejs graficzny aplikacji opiera się na interaktywnej tablicy Kanban z ciemnym motywem oraz wskaźnikami wydajności w czasie rzeczywistym.

```
+-----------------------------------------------------------+
| [TaskFlow]    Szukaj zadań...                 [API Online] |
+-----------------------------------------------------------+
| Statystyki: Do zrobienia (0) | W toku (0) | Zakończone (0) |
+-----------------------------------------------------------+
|  [DO ZROBIENIA]    |    [W TOKU]     |   [ZAKOŃCZONE]     |
|                    |                 |                    |
|  + Nowe zadanie    |                 |                    |
|  [Karta zadania]   |                 |                    |
+-----------------------------------------------------------+
```

### Podstawowe operacje:
1.  **Tworzenie nowego zadania**: Kliknij przycisk **„Nowe zadanie”** w prawym górnym rogu lub na dole kolumny „Do zrobienia”. Wypełnij formularz (Tytuł jest wymagany, Opis i Priorytet są opcjonalne) i kliknij **„Zapisz zadanie”**.
2.  **Przenoszenie zadań (Drag-and-Drop)**: Przeciągnij kartę zadania lewym przyciskiem myszy i upuść ją w odpowiedniej kolumnie (*Do zrobienia*, *W toku*, *Zakończone*). Zmiana statusu zostanie automatycznie zapisana w bazie danych i zaktualizowana w cache.
3.  **Edycja zadania**: Kliknij ikonę ołówka na karcie zadania, aby otworzyć formularz edycji, zmodyfikować dane i zatwierdzić zmiany.
4.  **Usuwanie zadania**: Kliknij ikonę kosza na karcie zadania. Zadanie zostanie zarchiwizowane (usunięcie programowe - soft-delete) i zniknie z tablicy.
5.  **Filtrowanie i wyszukiwanie**:
    *   Wpisz frazę w pole wyszukiwania na górnym pasku, aby filtrować zadania po tytule i opisie w czasie rzeczywistym.
    *   Wybierz priorytet z listy rozwijanej w panelu filtrów, aby ograniczyć wyświetlane zadania.
    *   Zmień kryterium sortowania (np. według daty utworzenia lub priorytetu).

---

## 4. Obsługa interfejsu API

Dla zaawansowanych użytkowników system udostępnia pełne API REST.

### Testowanie przez dokumentację interaktywną (Swagger):
1.  Wejdź na adres: `http://localhost:8000/docs` (dla Docker Compose) lub adres tunelu `/docs` (dla Minikube).
2.  Rozwiń sekcję wybranego punktu końcowego (np. `POST /api/v1/tasks/`).
3.  Kliknij przycisk **„Try it out”**, uzupełnij przykładowe dane w formacie JSON i kliknij **„Execute”**, aby wysłać żądanie i zobaczyć odpowiedź serwera.

### Przykłady zapytań cURL (Terminal):
*   **Tworzenie zadania**:
    ```bash
    curl -X POST http://localhost/api/v1/tasks/ \
      -H "Content-Type: application/json" \
      -d '{"title": "Wdrożyć Kubernetes", "description": "Przetestować pody na Minikube", "priority": "high"}'
    ```
*   **Pobieranie listy zadań**:
    ```bash
    curl http://localhost/api/v1/tasks/
    ```

---

## 5. Diagnostyka i rozwiązywanie problemów (Troubleshooting)

### Problem 1: Błąd uruchamiania kontenerów (zajęty port)
*   *Objaw*: Docker Compose zgłasza błąd: `bind: address already in use`.
*   *Rozwiązanie*: Sprawdź, czy inne programy nie blokują wymaganych portów (80, 8000, 5432, 6379) za pomocą komendy w terminalu:
    ```bash
    lsof -i :80
    ```
    Zakończ procesy blokujące porty i spróbuj ponownie.

### Problem 2: Brak połączenia z bazą danych lub Redis w Kubernetes
*   *Objaw*: Aplikacja zgłasza błąd połączenia, endpoint `/health` zwraca status `"unhealthy"`.
*   *Rozwiązanie*: Sprawdź stan wdrożeń i logi kontenerów w klastrze:
    ```bash
    kubectl get pods -n taskflow
    kubectl logs deployment/api -n taskflow
    kubectl logs statefulset/postgres -n taskflow
    ```

### Problem 3: Chęć całkowitego zresetowania danych aplikacji
*   *Ostrzeżenie*: Ta operacja usunie wszystkie zapisane zadania.
*   *Rozwiązanie dla Docker Compose*:
    ```bash
    make clean        # Czyszczenie plików tymczasowych
    ./scripts/cleanup.sh  # Potwierdź usunięcie woluminów bazodanowych
    ```
*   *Rozwiązanie dla Kubernetes*:
    ```bash
    kubectl delete namespace taskflow
    # Wolumeny PVC zostaną automatycznie usunięte wraz z przestrzenią nazw
    ```
