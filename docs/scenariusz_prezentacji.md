# TaskFlow — Scenariusz Prezentacji dla Promotora
# Autor: Jakub Francuz | Praca magisterska, 2026
# Temat: "Opracowanie i implementacja aplikacji konteneryzowanej z wykorzystaniem metodyki DevOps"
#
# WSKAZOWKA: Fragmenty w [nawiasach kwadratowych] to podpowiedzi co powiedziec/pokazac.
# Reszta to gotowe zdania do przeczytania lub parafrazy na swoj styl.

===================================================
CO TO JEST TaskFlow? (wstep — powiedz to na poczatku)
===================================================

"Projekt nazywa sie TaskFlow i jest to aplikacja webowa do zarzadzania zadaniami —
cos w stylu bardzo uproszczonego Jira czy Trello. Uzytkownik moze przez przegladarke
dodawac zadania, edytowac je, zmieniac statusy i usuwac. Tyle jezeli chodzi o sama funkcjonalnosc."

"Ale celem tej pracy nie bylo zbudowanie kolejnego todo-lista. Aplikacja jest celowo prosta,
bo chcialem skupic sie na tym, co w srodowisku DevOps jest naprawde trudne i interesujace:
konteneryzacja, orkiestracja, automatyczne testy, pipeline CI/CD i monitoring produkcyjny.
Innymi slowy — mniej 'co' aplikacja robi, bardziej 'jak' jest zbudowana i utrzymywana."

[Mozna dodac]: "Temat pracy mowi o 'metodyce DevOps' — i to wlasnie jest gwoli scisnlosci osia
calego projektu. Kazdy element, ktory zaraz omowie, wpisal sie bezposrednio w te metodologie."


===================================================
1. TECHNOLOGIE — Czego uzylem i dlaczego?
===================================================

JEZYK I FRAMEWORK (backend)
---------------------------

Python 3.12 + FastAPI:
  "Na backendzie uzylem Pythona z frameworkiem FastAPI. Wybor Pythona byl naturalny —
  to dominujacy jezyk w srodowiskach DevOps i cloud. FastAPI to stosunkowo nowy framework,
  ale bardzo popularny wlasnie dlatego, ze jest asynchroniczny. Co to znaczy w praktyce?
  Gdy aplikacja czeka na odpowiedz z bazy danych, nie stoi w miejscu i nie blokuje
  innych uzytkownikow — obsluguję inne zapytania w tym samym czasie.
  Dodatkowo FastAPI generuje dokumentacje API (Swagger UI) automatycznie —
  nie musialem pisac ani jednej linii dokumentacji recznie."

  [Mozna pokazac: http://taskflow.local/docs]

SQLAlchemy + asyncpg (komunikacja z baza):
  "Do komunikacji z baza danych uzylem SQLAlchemy — to najczesciej uzywany ORM w Pythonie.
  ORM to warstwa, dzieki ktorej pisze sie zapytania w Pythonie zamiast czystym SQL.
  Uzylem wersji asynchronicznej, zeby nie tracic tej zalety FastAPI, ktora wlasnie opisalem.
  Sterownik asyncpg to najszybszy dostepny sterownik PostgreSQL dla Pythona."

Pydantic v2 (walidacja danych):
  "Pydantic zajmuje sie walidacja danych — mozna myslic o nim jako o 'bramkarzu' przy wejsciu
  do API. Jesli ktos wysle pusty tytul zadania albo niepoprawny status — Pydantic
  odrzuca takie zapytanie z kodem HTTP 422 zanim jakkolwiek dotrze do bazy danych.
  Schematy walidacji sa pisane raz, a Pydantic na ich podstawie generuje rowniez
  dokumentacje w Swagger — dwie korzysci z jednej definicji."

Uvicorn (serwer):
  "Uvicorn to serwer, ktory faktycznie uruchamia aplikacje. Mozna go porownac do Apache
  lub nginx od strony PHP — to on nasluchuje na porcie i przekazuje przychodzace
  polaczenia do FastAPI. W Dockerfile ustawilem 2 procesy robocze."

BAZY DANYCH I CACHE
-------------------

PostgreSQL 16 (glowna baza danych):
  "PostgreSQL to sprawdzona, relacyjna baza danych — chyba nie trzeba jej przedstawiac.
  Tutaj przechowywane sa wszystkie zadania uzytkownikow. Na Kubernetes uruchomilem ja
  jako StatefulSet z Persistent Volume — co oznacza, ze nawet jesli kontener zostanie
  zrestartowany albo zastapiony nowym, dane w bazie nie znikna.
  Dla porownania: normalny kontener Docker po restarcie traci wszystko."

Redis 7 (cache — pamiec podreczna):
  "Redis to baza danych dzialajaca w pamieci RAM — jest wielokrotnie szybsza od PostgreSQL,
  ale dane sa ulotne (wyczyszcza sie przy restarcie, choc mozna skonfigurowac trwalosc).
  Uzylem go jako cache'u — czyli pamiec podreczna dla najczestszych zapytan.
  Zasada jest prosta: jesli ktos pyta o liste zadan i ta sama lista byla pobierana
  5 sekund temu — nie id do bazy, oddaj to co juz masz w Redis.
  Dzieki temu czasy odpowiedzi potrafia spasc z kilkudziesieciu milisekund do ponizej 5ms.
  Zaimplementowalem wzorzec Cache-Aside, o ktorym moge opowiedziec szczegolowo."

  [Jesli promotor zapyta o Cache-Aside — patrz sekcja Architektura nizej]

INFRASTRUKTURA
--------------

Docker (konteneryzacja):
  "Docker to serce calej infrastrutury. Kazdy serwis — API, baza danych, Redis, Nginx —
  dziala w osobnym, izolowanym kontenerze. Kontener mozna myslec jak male, samodzielne
  'pudelko' z aplikacja i wszystkimi jej zaleznosci. Nie ma sytuacji 'u mnie dziala,
  u Ciebie nie' — bo kontener dziala identycznie wszedzie."

  "Docker Compose pozwala uruchomic caly stos 4 serwisow jednym poleceniem: docker-compose up."

Kubernetes (orkiestracja):
  "Kubernetes to nastepny poziom po Docker Compose — zamiast jednej maszyny, zarzadza
  wdrozeniem na wielu maszynach jednoczesnie (w produkcji). Opisuje sie mu 'zelamy stan'
  w plikach YAML: chce 2 repliki API, Postgres jako StatefulSet, Redis z PVC —
  a Kubernetes dba o to, zeby ten stan byl ciagle utrzymany.
  Lokalnie uzylem Minikube — to wirtualny klaster K8s na jednej maszynie."

Nginx (reverse proxy):
  "Nginx stoi przed aplikacja jako 'bramkarz'. Uzytkownicy lacza sie z Nginx na porcie 80,
  a Nginx przekazuje ruch do aplikacji FastAPI na porcie 8000. Dzieki temu aplikacja
  nie jest wystawiona bezposrednio na internet. Nginx rowniez kompresuje odpowiedzi
  (gzip) i loguje kazde przychodzace zapytanie."

CI/CD I BEZPIECZENSTWO
----------------------

GitHub Actions:
  "Mam 4 niezalezne pipeline'y automatyzacji: CI (testy), CD (deploy), security (scan)
  i walidacja K8s. Szczegoly omowie w czesci powieconej CI/CD."

Testy:
  "pytest z rozszerzeniem asyncio — bo FastAPI jest asynchroniczny, wiec testy tez musza byc."

Bezpieczenstwo:
  "Bandit — analizuje kod Python pod katem typowych bledow bezpieczenstwa.
   Trivy — skanuje kontener Docker pod katem publicznych podatnosci CVE."

Monitoring:
  "Prometheus + Grafana — klasyczny duet do monitorowania aplikacji produkcyjnych.
   Prometheus zbiera metryki, Grafana je wyswietla na ladnych dashboardach."


===================================================
2. ARCHITEKTURA — jak to wszystko dziala razem
===================================================

[Mozna narysowac schemat lub pokazac diagram z katalogu diagrams/]

"Pokaze jak wyglada podroze zwyklego zapytania HTTP od uzytkownika az do bazy danych."

  Uzytkownik (przegladarka)
         |  HTTP :80
         v
  [ Nginx Reverse Proxy ]    <- "tu trafia kazde zapytanie"
         |  HTTP :8000
         v
  [ FastAPI Backend API ]    <- "tu jest logika biznesowa"
       /           \
      v             v
  [PostgreSQL]   [Redis]     <- "baza permanentna + pamiec podreczna"
         |
  [Prometheus] <--- co 15s pyta /metrics
         |
  [Grafana]    <--- wyswietla dashboardy

---

WZORZEC CACHE-ASIDE — jak to naprawde dziala?

"Przyklad: uzytkownik klika 'odswierz liste zadan'. Co sie dzieje?

  Krok 1: FastAPI pyta Redis — 'Hej, czy masz juz ta liste?'
  Krok 2a (Cache HIT): Redis mowi 'Mam!' -> odpowiedz w < 5ms. PostgreSQL w ogole nie widzi zapytania.
  Krok 2b (Cache MISS): Redis mowi 'Nie mam.' -> FastAPI idzie do PostgreSQL,
           pobiera dane, zapisuje je w Redis z czasem wygasniecia (TTL=5 minut),
           i zwraca uzytkownikowi.
  Krok 3: Ktos tworzy lub edytuje zadanie -> FastAPI usuwa stary cache z Redis,
           zeby nastepny GET musial pobrac swiezze dane z bazy."

"Po co to komplikowanie? W typowej aplikacji mamy CRUD, ktory ma znacznie wiecej odczytow
niz zapisow. Jesli 100 uzytkownikow co sekunde pyta o te sama liste — 99 z nich
dostanie odpowiedz z Redis, tylko jeden uderzy w baze. To ogromna oszczednosc zasobow."

---

SOFT-DELETE — dlaczego zadania nie sa kasowane z bazy?

"Kiedy uzytkownik kliknie 'Usun zadanie', w rzeczywistosci w bazie danych nic nie jest kasowane.
Ustawiam flage is_deleted=True i zmieniam status na 'archived'. Rekord zostaje.

Dlaczego? Bo dane w systemach produkcyjnych sa cenne. Przypadkowe usuniecie, audyt,
wymogi prawne (RODO), mozliwosc odtworzenia — to wszystko przemawia za przechowywaniem
historii zamiast fizycznego kasowania. Fizyczne DELETE jest destruktywne i nieodwracalne."


===================================================
3. STRUKTURA PROJEKTU — co jest gdzie i po co
===================================================

=== src/api/ — KOD ZRODLOWY BACKENDU ===

--- main.py — "serce aplikacji, punkt wejscia" ---

"To jest plik, od ktorego wszystko sie zaczyna — tu tworzona jest instancja aplikacji FastAPI.
Mam tu kilka rzeczy, ktore chcialbym podkreslic:"

  - Lifespan (cykl zycia aplikacji):
    "Zamiast wrzucac inicjalizacje wszedzie, mam dedykowana funkcje lifespan,
     ktora uruchamia sie przy starcie serwera i przy jego zamykaniu.
     Przy starcie: laczy sie z baza i tworzy tabele jezeli ich nie ma.
     Przy zamknieciu: ladnie zamyka polaczenia do PostgreSQL i Redis zamiast
     je brutalnie ucinac. To dobra praktyka — bez tego moga zostac 'zombie connections'."

  - Middleware CORS:
    "CORS to mechanizm przegladarki, ktory blokuje zapytania do innego serwera
     niz ta strona. Dodaem middleware zezwalajacy na takie zapytania — wymagane
     aby frontend mogl komunikowac sie z API."

  - Middleware Prometheus:
    "Dla kazdego zapytania HTTP automatycznie mierze czas odpowiedzi i licze zapytania.
     To klucz do monitoringu — bez tego Prometheus nie mialbym co mierzyc.
     Dwa metryki: REQUEST_COUNT (ile zapytan) i REQUEST_LATENCY (jak dlugo trwaly)."

--- config.py — "jeden config, zeby rzadzic nimi wszystkimi" ---

"Wszystkie parametry konfiguracyjne aplikacji — adresy bazy, hasla, srodowisko —
 sa w jednym miejscu: klasie Settings. Pydantic waliduje je automatycznie przy starcie.
 Czytam je ze zmiennych srodowiskowych lub z pliku .env.

 Dlaczego to wazne? Wyobrazmy sobie aplikacje, ktora ma adres bazy zahardkodowany
 w 15 plikach. Zmiana srodowiska (dev/prod) to 15 zmian. Tu zmieniam jedno miejsce —
 lub po prostu przekazuje inne zmienne srodowiskowe do kontenera.

 Istotny detal: @lru_cache na funkcji get_settings() oznacza, ze konfiguracja jest
 wczytywana tylko RAZ, a potem trzymana w pamieci. Nie mam I/O do pliku przy kazdym zapytaniu.

 extra='ignore' — to jest cos, co musialem dodac po czasie. Docker Compose przekazuje
 do kontenera rowniez zmienne jak NGINX_PORT, ktore Pydantic nie zna. Bez 'ignore'
 aplikacja wyrzucala blad. Prosta linia kodu, nieoczywisty problem."

--- database.py — "jak aplikacja rozmawia z PostgreSQL" ---

"Ten plik konfiguruje polaczenie z baza. Kilka rzeczy sa tu celowe:

 Pool polaczen (pool_size=5, max_overflow=10): Aplikacja nie otwiera nowego polaczenia
 do bazy przy kazdym zapytaniu HTTP — to byloby bardzo wolne. Zamiast tego utrzymuje
 pule 5 otwartych polaczen, z mozliwoscia chwilowego rozszerzenia do 15.
 Polaczenie jest 'wyciagane z puli', uzywane, i 'oddawane' — jak samochody w wypozyczalni.

 get_db() jako generator: Sesja bazy jest wstrzykiwana przez Dependency Injection.
 FastAPI sam zamknie sesje po zakonczeniu zapytania HTTP — nie moge zapomniec o zamknieciu.
 To pattern zapobiegajacy 'wyciekowi polaczen' (connection leak)."

--- models.py — "jak wyglada zadanie w bazie danych" ---

"models.py to opis tabeli 'tasks' w jezyku Pythona — SQLAlchemy przetlumaczy to na SQL.
 
 Uzywam klas Enum dla pol Status (todo/in_progress/done/archived) i Priority
 (low/medium/high/critical). Dzieki temu baza fizycznie odrzuci niepoprawna wartosc —
 nie mozna zapisac status='banan'. To walidacja na poziomie bazy, nie tylko API.

 Automatyczne znaczniki czasu: created_at i updated_at uzywaja lambda funkcji, zeby
 przy kazdym tworzeniu/aktualizacji rekordu Python sam uzupelnil date w UTC.
 Nie moge zapomniec o tej operacji w logice biznesowej — baza to zrobi sama.

 Indeksy na title i status: zapytania filtrujace po statusie (najczestszy filtr)
 beda znacznie szybsze dzieki indeksowi — baza nie musi skanowac calej tabeli."

--- schemas.py — "walidacja i kontrakt API" ---

"schemas.py to definicja 'kontraktu' API — co mozna wyslac i co sie dostanie z powrotem.
 Mam 3 schematy dla zadan:

 TaskCreate — co musi byc w ciele POST-a:
   title jest wymagany (field z ...) i musi miec min 1 znak.
   description jest opcjonalny, domyslnie pusty string.
   priority jest opcjonalny, domyslnie 'medium'.
   Jezeli cos sie nie zgadza — Pydantic odrzuca zapytanie z 422 ZANIM dotrze do bazy.

 TaskUpdate — co mozna wyslac w PATCH-u:
   Tu wszystkie pola sa Optional — mozna zmienic tylko tytul, tylko status, albo obydwa.
   Implementacja Partial Update: model_dump(exclude_unset=True) w serwisie zwraca
   tylko te pola, ktore faktycznie zostaly wyslane w zapytaniu.

 TaskResponse — co dostaje uzytkownik z powrotem:
   Zawiera wszystkie pola z bazy, lacznie z is_deleted i znacznikami czasu.
   from_attributes=True pozwala Pydantic mapowac obiekt ORM (z bazy) bezposrednio
   na ten schemat bez recznej konwersji.

 Osobne schematy wejscia i wyjscia to celowy design — nie chce, zeby uzytkownik
 widzial wewnetrzne pola (np. is_deleted), ale chce je zwracac w odpowiedzi dla kompletnosci."

=== src/api/routes/ ===

--- routes/tasks.py — "endpointy CRUD, gdzie API 'przyjmuje zamowienia'" ---

"To jest warstwa HTTP aplikacji — tu API slucha zapytan i zwraca odpowiedzi.
 Mam 5 endpointow:

 POST /api/v1/tasks/ — stworz nowe zadanie.
   Przyjmuje TaskCreate, zwraca TaskResponse z kodem 201 (nie 200!).
   201 = 'Created', semantycznie poprawny dla tworzenia zasobu.

 GET /api/v1/tasks/ — pobierz liste (z filtrowaniem i paginacja).
   Ma sporo parametrow query: page, per_page, status, priority, sort_by, sort_order.
   sort_by jest walidowany przez regex — mozna sortowac tylko po dozwolonych kolumnach,
   nie mozna wstrzyknac SQL przez ten parametr.

 GET /api/v1/tasks/{task_id} — pobierz jedno zadanie. Jezeli nie istnieje: HTTP 404.

 PATCH /api/v1/tasks/{task_id} — czesciowa aktualizacja.
   Kluczowe: PATCH zamiast PUT. PUT wymaga przeslania calego obiektu, PATCH tylko zmian.

 DELETE /api/v1/tasks/{task_id} — usuniecie (soft-delete). Zwraca JSON z wiadomoscia.

 Kazdy endpoint uzywa Depends(get_db) — FastAPI wstrzykuje sesje bazodanowa automatycznie.
 Logike biznesowa deleguje do TaskService — route nie powinien wiedziec o SQL i Redis."

--- routes/health.py — "oczy Kubernetes i Prometheus" ---

"Health endpointy to cos, czego aplikacja 'produkcyjna' musi miec.
 Sa to sygnaly dla infrastruktury, nie dla uzytkownika.

 GET /health — sprawdza czy baza odpowiada (SELECT 1) i czy Redis odpowiada (ping()).
   Jesli baza nie zyje — zwraca status='unhealthy'. Kubernetes na tej podstawie
   moze zrestartowac pod. To liveness/readiness probe.

 GET /prometheus — generuje metryki w formacie tekstowym Prometheus.
   Przed odpowiedzia aktualizuje Gauge'y: ile zadan w systemie, ile na kazdy status,
   status polaczenia z baza i Redis (1=OK, 0=brak).
   Prometheus odpytuje ten endpoint co 15 sekund — mechanizm 'pull', nie 'push'.
   Czyli to Prometheus przychodzi do aplikacji, nie odwrotnie."

=== src/api/services/ ===

--- services/cache_service.py — "opakowanie na Redis" ---

"Ten plik to warstwa abstrakcji nad Redis. Zamiast uzywac klienta Redis bezposrednio
 w logice biznesowej, mam zestaw prostych funkcji: cache_get, cache_set, cache_delete.
 
 Najwazniejsza decyzja projektowa: jezeli Redis jest niedostepny — zadna z tych funkcji
 nie wyrzuca wyjatku. Zwracaja po prostu None/False, a aplikacja dziala dalej bez cache.
 To sie nazywa graceful degradation — degradacja z wdziekiem. Uzytkownik dostanie wolniejsza
 odpowiedz, ale nie dostanie bledu 500.

 cache_invalidate_pattern — usuwa WSZYSTKIE klucze pasujace do wzorca 'taskflow:tasks:*'.
 Uzywam SCAN zamiast KEYS, bo KEYS na duzej bazie Redis blokuje caly serwer na czas
 operacji (Redis jest jednowatkowy). SCAN iteruje po czesciach — bezpieczniejszy."

--- services/task_service.py — "tu jest logika, nie w routerach" ---

"TaskService to warstwa logiki biznesowej — tu dzieje sie wszystko co interesujace.
 Router przyjmuje zapytanie HTTP i od razu oddaje je do serwisu. Dzieki temu logike
 mozna testowac bez uruchamiania serwera HTTP — to jest ten wzorzec Service Layer.

 Kilka ciekawych elementow:

 create_task(): Po zapisaniu zadania do bazy, robie cache_invalidate_pattern('taskflow:tasks:*').
   Po co? Bo mam w cache stara liste zadan — musi zniknac, zeby nastepny GET pobral swiezza.

 update_task() — Partial Update przez model_dump(exclude_unset=True):
   Jesli klient wyslal tylko {'status': 'done'} — to tylko status zostanie zaktualizowany.
   Pydantic wie ktore pola byly faktycznie przeslane, ktore byly domyslne — exclude_unset
   zwraca tylko te przeslane. To jest subtelna, ale wazna roznica w implementacji PATCH.

 delete_task() — Soft-delete: is_deleted=True i status=ARCHIVED.
   Po zapisie usuwam z cache zarówno ten konkretny rekord jak i wszystkie listy."

=== src/api/Dockerfile — "jak zbudowany jest kontener" ===

"Dockerfile uzywa techniki multi-stage build — dwuetapowego budowania.

 Etap 1 ('builder'): instaluje wszystkie zaleznosci pip. Moze tu byc pip, gcc i inne narzezia.

 Etap 2 ('production'): kopiuje tylko gotowe paczki z etapu 1 — BEZ pip, BEZ narzedziowych.
   Wynik: obraz produkcyjny jest znacznie mniejszy i ma mniejsza 'powierzchnie ataku'.
   Mniej zainstalowanego oprogramowania = mniej potencjalnych podatnosci.

 Uzytkownik 'appuser' (nie root): Kontener uruchamia sie jako niepriwilejowany uzytkownik.
   To standartowa praktyka bezpieczenstwa — nawet jezeli ktos przejmie kontener,
   nie ma uprawnien roota do systemu operacyjnego hosta.

 HEALTHCHECK: Docker sam co 30s sprawdza czy aplikacja zyje — wykrywa zablokowany proces
 ktory odpowiada na porcie, ale w rzeczywistosci jest 'zamrozony'."

=== src/nginx/ — "bramkarz przed API" ===

"Konfiguracja Nginx jako reverse proxy. Kluczowe rzeczy:

 upstream api { server api:8000 } — 'api' to nazwa serwisu Docker/K8s.
   DNS wewnetrzny rozwiazuje ja automatycznie — nie wpisuje IP na stale.

 Naglowki proxy (X-Real-IP, X-Forwarded-For): Nginx przekazuje prawdziwy IP klienta
   do aplikacji FastAPI. Bez tego API widzi tylko IP Nginx (np. 172.17.0.1),
   nie wiedzialby kto naprawde wysyla zapytania — wazne przy logowaniu i rate-limitingu.

 gzip on: odpowiedzi JSON sa kompresowane. Lista 100 zadan zamiast 50KB -> 8KB.
   Dla uzytkownikow z wolnym polaczeniem to odczuwalna roznica."

=== docker-compose.yml — "lokalna orkiestrantura" ===

"docker-compose.yml definiuje caly stos jako 4 serwisy.
 Kluczowe mechanizmy:

 depends_on z condition: service_healthy:
   Nginx startuje DOPIERO gdy healthcheck API przejdzie pomyslnie.
   API startuje DOPIERO gdy PostgreSQL i Redis odpowiedza na healthcheck.
   Bez tego mozna miec race condition — API startuje zanim baza jest gotowa i sie crashuje.

 Woluminy (postgres_data, redis_data):
   Dane bazy przetrwaja docker-compose down i docker-compose up. Bez woluminu dane znikaja.

 Siec taskflow-network:
   Wszystkie serwisy sa w jednej sieci bridge. Moga sie komunikowac po nazwie
   (np. api moze robic postgres:5432) — bez znajomosci adresow IP."


===================================================
4. KUBERNETES — wdrozenie produkcyjne
===================================================

"Kubernetes to kolejny poziom automatyzacji po Docker Compose. Na lokalnym Minikube
 mam dokladnie taki sam stack jak w Docker Compose, ale opisany manifestami K8s w YAML.
 
 Powiem krotko o kazdym manifescie — to pokaze, ze rozumiem co znaczy kazdy."

k8s/namespace.yaml — "segregacja zasobow":
  "Tworzy namespace 'taskflow'. Wszystkie moje zasoby sa odizolowane od innych aplikacji
   klastra. Analogia: namespace to jak osobny folder w systemie plikow — porządek."

k8s/configmap.yaml — "konfiguracja bez twardego kodowania":
  "Przechowuje nieskryte zmienne konfiguracyjne: adresy hostow, nazwe bazy.
   Zmiana konfiguracji nie wymaga rebuildu obrazu Docker — tylko zmieniam ConfigMap
   i restartuję pody. W firmie to oznacza ze devops nie potrzebuje dewelopera do zmiany hosta."

k8s/secrets.yaml — "hasla w bezpieczniejszy sposob":
  "Hasla zakodowane base64. To lepsze niz wpisanie hasla w Dockerfile, bo K8s moze
   limitowac dostep do Secret per-pod i per-service-account. W produkcji Secret
   byloby zastapione np. HashiCorp Vault lub AWS Secrets Manager."

k8s/api/ (Deployment + Service + HPA) — "skalowanie API":
  "Deployment API uruchamia 2 repliki — od razu mam High Availability.
   Gdyby jeden pod padl, ruch przejdzie do drugiego zanim operator to zauważy.

   HPA (HorizontalPodAutoscaler) to jest cos, z czego jestem dumny w tym projekcie.
   Skalowan automatyczne: gdy srednie CPU > 70%, K8s automatycznie dodaje repliki (max 5).
   Gdy ruch spada — wraca do 2. To jest elastycznosc, za ktora placi sie w chmurze
   tylko za faktycznie uzyte zasoby."

k8s/postgres/ i k8s/redis/ (StatefulSet + PVC) — "bazy z pamiecią":
  "StatefulSet zamiast Deployment — bo bazy danych NIE sa bezstanowe.
   Kluczowa roznica: StatefulSet gwarantuje ze pod zawsze bedzie sie nazywal postgres-0
   i zawsze bedzie podlaczony do tego samego PVC (dysku). Deployment moze zastapic pod
   dowolnym i na dowolnym wezle — dla bazy danych to katastrofa.

   PersistentVolumeClaim (5Gi dla postgres, 1Gi dla redis) to rezerwacja miejsca na dysku
   klastra. Dane przezyja nawet usuniecie i ponowne stworzenie podu."

k8s/ingress.yaml — "jeden adres dla wszystkiego":
  "Ingress Controller to 'recepcja' klastra. Ruch na hostname taskflow.local jest
   kierowany do serwisu nginx. Na macOS z Minikube wymagane jest minikube tunnel —
   tworzy tunel sieciowy miedzy maszyną a klastrem."

k8s/monitoring/ (Prometheus + Grafana) — "wzrok na system":
  "Prometheus i Grafana dzialaja jak monitoringowy panel kontrolny.
   Skonfigurowalem provisionowany datasource — Grafana automatycznie wie o Prometheusie
   przy pierwszym starcie, bez recznej konfiguracji przez UI."


===================================================
5. CI/CD — jak dziala automatyzacja?
===================================================

"Mam 4 pipeline'y w GitHub Actions. Pokaze jak myslac o kazdym z nich."

--- ci.yml — test zanim cos sie zmiesci na main ---

"Ten pipeline ustawia poprzeczkę jakosc kodu. Uruchamia sie przy kazdym push i PR.

 Jezeli ktos (nawet ja) wypchniesz kod ktory nie przechodzi testow — CI zakaza merge.
 To jest siatka bezpieczenstwa.

 Kroki:
 1. black --check: czy kod jest poprawnie sformatowany?
    Jesli nie — pipeline pada. Formatowanie nie jest kosmetyka, to standard w teamie.

 2. flake8: czy sa oczywiste bledy i naruszenia PEP8?

 3. pytest z --cov: testy + pokrycie kodu.
    Raport mowi: 'ta linia kodu nie ma zadnego testu' — widac gdzie jest ryzyko.

 4. docker build (push: false): czy Dockerfile jest poprawny i obraz sie buduje?
    Sprawdzam to bez wypychania do rejestru — tylko weryfikacja poprawnosci."

--- cd.yml — automatyczny deploy po merge ---

"Po pomyslnym CI i merge do main, CD automatycznie:
 1. Buduje obrazy API i Nginx
 2. Wypcycha je do GitHub Container Registry (GHCR)

 Obraz dostaje 2 tagi:
   :latest — zawsze wskazuje na najnowszy
   :abc123def (hash commita SHA) — unikalny, niezmienialny

 Dlaczego SHA? Jesli nowy deploy ma blad, moge robic rollback do dokladnie poprzedniej wersji:
 kubectl set image deployment/api api=ghcr.io/.../api:poprzedni-sha

 Autoryzacja do GHCR przez automatyczny GITHUB_TOKEN — zero sekretow do konfiguracji recznie."

--- security.yml — DevSecOps w praktyce ---

"'Security as Code' — bezpieczenstwo wbudowane w pipeline, nie jako etap na koncu.

 Trivy skanuje pliki repozytorium pod katem publicznych podatnosci CVE.
 Porownuje wersje bibliotek z baza NIST NVD. Raportuje tylko CRITICAL i HIGH.
 Dzieki ignore-unfixed: true — pomija podatnosci bez dostepnej poprawki,
 bo i tak nic nie mozna z nimi zrobic w tym momencie.

 Bandit analizuje KOD ZRODLOWY Python — szuka wzorcow takich jak:
 hardcoded passwords, niebezpieczne funkcje (eval, exec, pickle),
 wzorce SQL injection. Nie uruchamia kodu — to analiza statyczna.
 Uzylem -ll -ii: tylko problemy o wysokim severity I wysokiej pewnosci."

--- k8s-validate.yml — szybkie sprawdzenie przed deployem ---

"Kubeconform waliduje pliki YAML z k8s/ pod katem zgodnosci ze schema Kubernetes.
 Wykrywa bledy w nazwach pol, typach i wymaganych wartosciach zanim zmiana
 dotrze do klastra. Szybsze i tansze niz odpalenie kubectl apply na zywy klaster
 i patrzenie co sie posypie."


===================================================
6. TESTY — co i jak testuje?
===================================================

"Testy to sekcja, na ktora chcialbym zwrocic szczegolna uwage.
 Napisalem trzy pliki testowe i przez to widac, ze nie traktuje testow jako formalnosci."

--- tests/conftest.py — fundament izolacji testow ---

"conftest.py to plik konfiguracyjny pytest — raz napisany, uzywa sie w kazdym tescie.

 Najwazniejsza decyzja: ZAMIAST POSTGRESQL uzywam SQLite in-memory w testach.
 To nie jest lenistwo — to celowy wybor:
   - SQLite nie wymaga uruchomionego serwera
   - Kazdy test dziala na 100% izolowanej bazie
   - Testy moga biec rowolegle
   - Sa wielokrotnie szybsze

 Jak to dziala technicznie? app.dependency_overrides[get_db] = override_get_db.
 FastAPI ma system Dependency Injection — podmieniam zaleznosc get_db tak,
 zeby zamiast sesji PostgreSQL, endpoint dostawal sesje SQLite.
 Aplikacja o niczym nie wie — dziala tak samo, tylko z inna baza pod spodem.

 setup_database (autouse=True): przed KAZDYM testem tworze tabele od zera,
 po KAZDYM tescie usuwam je. Kazdy test dostaje czyste srodowisko — zero zaleznosci
 miedzy testami. Kolejnosc uruchamiania testow nie ma znaczenia.

 Redis w testach: calkowicie wylaczony. Cache service zwroci None przy braku polaczenia
 i aplikacja dziala bez cache. Testuje logike — nie integracje z Redis."

--- tests/test_tasks.py — 11 testow jednostkowych CRUD ---

"Pokrywam pelny cykl zycia zasobu przez HTTP. Chcialbym omowic kilka ciekawszych:

 test_create_task_empty_title:
   Wysylam POST z title=''. Sprawdzam ze dostaje HTTP 422.
   To test ze WALIDACJA dziala — nie ze zapis do bazy. Pydantic blokuje przed baza.

 test_delete_task:
   Tworze zadanie -> kasuje -> probuje pobrac.
   Drugi GET musi zwrocic 404. To testuje soft-delete end-to-end.

 test_pagination:
   Tworze 5 zadan, pytam o page=1&per_page=2.
   Sprawdzam: len(tasks)=2, total=5, pages=3.
   To testuje poprawnosc obliczen paginacji (math.ceil) i poprawnosc OFFSET/LIMIT."

--- tests/test_functional.py — 3 testy integracyjne End-to-End ---

"To sa testy scenariuszy biznesowych — nie pojedynczych endpointow, ale ciagow akcji.

 test_full_task_lifecycle:
   To moj 'zloty test'. Tworze zadanie -> sprawdzam w bazie -> zmieniam status na done
   i priorytet na high -> usuwam -> sprawdzam ze jest niedostepne.
   5 zapytan HTTP w jednym tescie. Jezeli ten test przechodzi, cala aplikacja dziala.

 test_filtering_and_pagination_combination:
   Testuje jednoczesne uzycie filtrow i paginacji na realnym zbiorze danych.
   To test ze logika w get_tasks() poprawnie laczy WHERE + OFFSET + LIMIT.

 test_validation_and_error_handling:
   Testuje BLEDY — co sie dzieje kiedy uzytkownik robi cos blednego.
   Brak tytulu (422), nieistniejace ID (404), niepoprawny status (422).
   API musi zwracac prawidlowe kody HTTP — to jest kontrakt z klientem."


===================================================
7. MONITORING I ALERTY
===================================================

"Mowiac o DevOps bez monitoringu byloby jak mowic o samochodzde bez deski rozdzielczej.

 Prometheus zbiera metryki przez mechanizm pull — sam przychodzi do aplikacji
 co 15 sekund i pyta '/prometheus' o aktualny stan. Zbiera:
   - taskflow_requests_total (ile zapytan, jaka metoda, jaki kod HTTP)
   - taskflow_request_latency_seconds (histogram czasu odpowiedzi)
   - taskflow_tasks_total (ile zadan w systemie)
   - taskflow_tasks_by_status (ile zadan na kazdy status)
   - taskflow_database_status / taskflow_redis_status (1/0)

 Grafana vizualizuje te dane na dashboardach. Moge konfigurować alerty:
 np. 'wyslij powiadomienie kiedy czas odpowiedzi API przekroczy 500ms'
 lub 'alarm kiedy status bazy = 0'.

 Bez monitoringu nie wiem ze aplikacja ma problem dopoki uzytkownik mi nie napisze.
 Z monitoringiem widze problem zanim uzytkownik go zauważy."


===================================================
8. SZYBKI SLOWNIK — jak tlumaczyc na laiku
===================================================

Kontener Docker:
  "Pudelko z aplikacja i wszystkimi jej zaleznosci. Dziala tak samo wszedzie."

Kubernetes:
  "Zarzadca kontenerow. Pilnuje zeby zawsze bylo tyle kontenerow ile potrzeba,
   restartuje je jak padna, rozklada ruch miedzy nimi."

CI/CD Pipeline:
  "Automatyczny tasmociag — kod wchodzi na jednym koncu, gotowy deploy wychodzi na drugim.
   W srodku sa testy, sprawdzenie jakosci, budowanie obrazu, deploy."

Cache (Redis):
  "Notatnik kelnera. Kelner (API) pamięta ostatnie zamowienie (lista zadan) zamiast
   za kazdym razem biec do kuchni (bazy danych). Szybciej — ale po czasie notatnik
   musi byc czyszczony zeby nie podawac starych dan."

StatefulSet vs Deployment:
  "Deployment: pody sa jak nienazwane pojemniki — jeden za drugi. Deployment moze
   je przestawiac i zastepowac bez ostrzezenia.
   StatefulSet: pody sa jak krawedzie z numerem — 'ten dysk nalezy do postgres-0'.
   Wazne dla baz, bo muszą pamietac gdzie sa ich dane."

Soft-delete:
  "Zamiast wyrywania strony z ksiazki — przekreslam ja. Strona nadal istnieje,
   mozna ja odtworzyc, ale nie jest wyswietlana uzytkownikowi."

HPA — skalowanie poziome:
  "Kiedy w sklepie robi sie kolejka — zatrudniasz wiecej kasjerow.
   Kiedy kolejka znika — zmniejszasz obsade. HPA robi to samo z podami API."


===================================================
9. KOMENDY — co pokazac podczas prezentacji
===================================================

# Status calego stosu na Kubernetes
kubectl get all -n taskflow

# Logi API (co sie dzieje w srodku)
kubectl logs -n taskflow deployment/api --tail=30

# Status HPA — czy skaluje?
kubectl get hpa -n taskflow

# Uruchomienie lokalne przez Docker Compose
make run
make test     # uruchom testy, wyniki do tests/test.txt

# Dokumentacja API (Swagger)
# http://taskflow.local/docs
# http://taskflow.local/health
# http://taskflow.local/prometheus


===================================================
10. PYTANIA PROMOTORA — gotowe odpowiedzi
===================================================

P: Dlaczego FastAPI a nie Flask lub Django?
O: "Flask jest synchroniczny — przy kazdym zapytaniu do bazy, serwer czeka.
   FastAPI jest asynchroniczny — czeka, ale w tym czasie obsluguję inne zapytania.
   Django jest 'batteries included' — ogromny framework z ORM, admin, auth.
   Dla mikroserwisu CRUD to overkill. FastAPI jest lekki, szybki i ma dokumentacje
   wbudowana w framework."

P: Dlaczego Redis jako cache?
O: "Redis ma wsparcie dla TTL na poziomie klucza, operator SCAN do wzorcowej inwalidacji
   i jest standardem w srodowisku Python. Kluczowe: jesli Redis padnie, moja aplikacja
   NADAL DZIALA — tylko wolniej. Napisalem graceful degradation w cache_service.py."

P: Co to jest soft-delete i dlaczego?
O: "Zamiast fizycznego DELETE, ustawiam is_deleted=True. Dane pozostaja w bazie.
   Zalety: historia, audyt, odtwarzalnosc, lepsza obsluga RODO (anonymizacja
   zamiast usuniecia). Fizyczny DELETE jest niszczacy i nieodwracalny."

P: Jak testy sa odizolowane od produkcji?
O: "dependency_overrides w FastAPI — podmieniam zaleznos get_db tak, ze zamiast
   sesji PostgreSQL, test dostaje sesje SQLite in-memory. Przed kazdym testem
   tworze tabele, po teście je usuwam. Zero zaleznosci miedzy testami."

P: Co robi HPA?
O: "Monitoruje CPU podow. Gdy srednie CPU > 70% — dodaje repliki (max 5).
   Gdy ruch spada — wraca do minimum 2. To elastycznosc kosztowa w chmurze —
   placisz za tyle zasobow ile faktycznie uzywasz."

P: Czym rozni sie StatefulSet od Deployment?
O: "Deployment: pody sa wymienne, K8s moze je przesuwac miedzy wezlami.
   StatefulSet: gwarantuje stala tozsamosc podu (postgres-0) i stale powiazanie
   z PVC. Dla baz danych to kluczowe — muszą wiedziec gdzie sa ich dane."

P: Co sprawdza Trivy i Bandit?
O: "Trivy skanuje pliki pod katem CVE — czy zainstalowane biblioteki maja znane podatnosci.
   Bandit analizuje statycznie kod Python — czy nie ma hardcoded haseł, niebezpiecznych
   funkcji (eval, pickle). Oba dzialaja automatycznie w CI przy kazdym pushu."

P: Dlaczego multi-stage build w Dockerfile?
O: "Etap 1 instaluje pip i narzedzia. Etap 2 kopiuje tylko gotowe paczki.
   Wynik: mniejszy obraz, mniej zainstalowanego oprogramowania, mniejsza powierzchnia ataku.
   Bezpieczniej i szybciej przy transferze obrazu."

P: Co to graceful degradation w kontekscie Redis?
O: "Jesli Redis nie odpowiada — zamiast wyrzucic blad 500, aplikacja przechodzi
   na tryb 'bez cache' i odpytuje PostgreSQL bezposrednio. Uzytkownik dostanie
   wolniejsza odpowiedz, ale aplikacja nie padnie."

P: Co to ASGI i czym rozni sie od WSGI?
O: "WSGI (Flask, Django) obsluguję jedno zapytanie naraz w jednym watku.
   ASGI (FastAPI, uvicorn) obsluguję wiele zapytan jednoczesnie asynchronicznie —
   bez tworzenia nowego watku dla kazdego. Znacznie wydajniejszy przy I/O-bound workload."
