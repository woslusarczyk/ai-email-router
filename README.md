# AI Email Router

Proof of Concept aplikacji mikroserwisowej. API aplikacji przyjmuje zapytania użytkowników, model językowy LLM (Ollama) interpretuje ich treść i automatycznie przekierowuje je jako wiadomości email do odpowiedniego działu poprzez wywołanie tool calling.
## Spis treści

- [Architektura i kluczowe decyzje](#architektura-i-kluczowe-decyzje)
- [Struktura repozytorium](#struktura-repozytorium)
- [Uruchomienie](#uruchomienie)
- [Zmienne środowiskowe](#zmienne-środowiskowe)
- [Endpointy](#endpointy)
- [Przykładowe zapytanie](#przykładowe-zapytanie)
- [Jak zweryfikować działanie](#jak-zweryfikować-działanie)
- [Znane ograniczenia](#znane-ograniczenia)

## Architektura i kluczowe decyzje

**Python 3.12 + FastAPI.** Możliwość stworzenia prostego entpoint'a API oraz wygenerowanie dokumentacji Swagger pod endpointem `/api/v1/docs`.

**pydantic-ai + Ollama (dedykowany `OllamaModel`/`OllamaProvider`, protokół kompatybilny z OpenAI).** Instalowany jako `pydantic-ai-slim[openai]`, zamiast pełnego `pydantic-ai`, aby uniknąć konfliktów i zbędnych modułów.

**Agent wysyła e-mail sam, przez wywołanie narzędzia (tool calling), a nie sam kod.** Agent na podstawie otrzymanego zgłoszenia użytkownika wywołuje narzędzie `send_email`, zarejestrowane przez `@agent.tool` (`api/app/agent.py`) i to LLM decyduje, kiedy i z jakimi argumentami go wywołać.

**Agent może wybrać dział tylko spośród zdefiniowanych, a nie dowolny przez siebie wygenerowany.** Parametr `department` w narzędziu `send_email` jest typu `Department` (enum z pięcioma wartościami).

**`Reply-To` i treść zgłoszenia wstrzykiwane przez kod, nie wybierane przez model.** Dane specyficzne dla requestu (`sender_email`, oryginalna treść `message`) trafiają do narzędzia przez `RunContext[Deps]`, a nie jako parametry, które LLM wypełnia:
- **Bezpieczeństwo** — model nie może ustawić dowolnego `Reply-To` ani wstrzyknąć czegoś do nagłówków.
- **Uniknięcie błędnych transformacji treści** — agent przekazuje oryginalną treść zgłoszenia, aby uniknąć nieprawidłowych przekształceń wynikających z polskich znaków oraz uniknięcie przeinaczania treści. Decyduje on tylko o temacie oraz dziale, do którego trafi zgłoszenie.

**Ponowne wywołanie narzędzia `send_email`** W celu uniknięcia gubienia zgłoszeń, agent wykrywa brak wywołania narzędzia i ponawia próbę (`MAX_ATTEMPTS` razy), a jeżeli ta ilość prób się nie powiedzie to ostatecznie zgłoszenie trafi do działu OTHER.

**Docker Compose** `ollama/entrypoint.sh` pobiera model przy starcie kontenera (tylko jeśli go jeszcze nie ma w wolumenie `ollama_data`), a healthcheck w `docker-compose.yml` sprawdza nie tylko, czy proces Ollamy odpowiada, ale czy **konkretny, skonfigurowany model** jest już dostępny. Serwis `API` ma zależnośc od ollamy, więc nigdy nie przyjmie requestu, zanim model nie będzie gotowy.

**MailHog jako serwer testowy poczty** — przechwytuje wysyłane e-maile bez realnej dostawy, z panelem webowym do wizualnej weryfikacji.

## Struktura repozytorium

```
ai-email-router/
├── docker-compose.yml
├── .env.example
├── README.md
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI, endpoint POST /api/v1/route, Swagger pod /api/v1/docs
│       ├── config.py        # ustawienia z env (OLLAMA_HOST, MODEL_NAME, SMTP_HOST, SMTP_PORT)
│       ├── schemas.py       # RouteRequest / RouteResponse (pydantic)
│       ├── departments.py   # enum Department + mapowanie działów - adres e-mail
│       ├── agent.py         # agent pydantic-ai, tool send_email, tool calling retry
│       └── mailer.py        # budowa i wysyłka e-maila przez SMTP (MailHog)
├── ollama/
│   ├── Dockerfile
│   └── entrypoint.sh        # serve + automatyczny pull modelu przy starcie
└── scripts/
    └── smoke_test.sh
```

## Jak uruchomić ?

Wymagany jest Docker Desktop (z backendem WSL2 na Windows).

```bash
git clone <adres-repo>
cd ai-email-router
docker compose up -d
```

Pierwsze uruchomienie pobiera obrazy i model LLM (`llama3.2` domyślnie) — może to potrwać kilka minut. Kolejne uruchomienia są szybsze, ponieważ model jest już pobrany.

Jak sprawdzić status?
```bash
docker compose ps
```
Wszystkie trzy serwisy(API, Ollama, Mailhog) powinny być `Up`, `ollama` dodatkowo `(healthy)`.

## Zmienne środowiskowe

Skopiuj `.env.example` do `.env`, jeśli chcesz zmienić model:
```
MODEL_NAME=llama3.2
```
Model musi wspierać tool/function calling w Ollamie (np. `llama3.2`, `qwen2.5`).

## Endpointy

| Metoda | Ścieżka | Opis |
|---|---|---|
| `GET` | `/health` | Health check API |
| `POST` | `/api/v1/route` | Przyjmuje zgłoszenie, agent klasyfikuje i wysyła e-mail |
| `GET` | `/api/v1/docs` | Interaktywna dokumentacja Swagger UI |

## Przykładowe zapytanie

**bash / zsh / Git Bash:**
```bash
curl -X POST http://localhost:8000/api/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jan.nowak@example.com",
    "message": "Nie dziala mi komputer, ekran jest czarny"
  }'
```

**PowerShell:**
```powershell
$body = @{
    email   = "jan.nowak@example.com"
    message = "Nie dziala mi komputer, ekran jest czarny"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/route" -Method Post -ContentType "application/json" -Body $body
```

> `curl` w PowerShell jest domyślnie aliasem do `Invoke-WebRequest`, a `curl.exe` (prawdziwy curl) gubi wewnętrzne cudzysłowy JSON-a podczas przekazywania argumentów przez Windows — `Invoke-RestMethod` to natywny odpowiednik, wolny od tego problemu.

Przykładowa odpowiedź:
```json
{
  "department": "it",
  "department_email": "it@example.com"
}
```

## Jak zweryfikować działanie?

1. Wyślij zapytanie jak wyżej (albo przez Swagger UI pod `/api/v1/docs`, przycisk "Try it out").
2. Otwórz panel MailHog: [http://localhost:8025](http://localhost:8025).
3. Sprawdź przechwyconą wiadomość:
   - `To` — adres zgodny z wybranym działem (`it@example.com`, `help-desk@example.com`, `human-resources@example.com`, `kadry@example.com` lub `other@example.com`),
   - nagłówek `Reply-To` — adres nadawcy z requestu (`jan.nowak@example.com`),
   - treść (`Body`) — oryginalna treść zgłoszenia, bez zmian.

## Znane ograniczenia

- Kategoryzacja zgłoszeń w zależności od modelu może być mniej lub bardziej skuteczna, zgłoszenia mogą częściej być kierowane do `other@example.com` przy niejednoznacznych zgłoszeniach.
- Brak automatycznych testów jednostkowych/integracyjnych w tej wersji PoC — weryfikacja odbywa się manualnie przez request do API i panel MailHog.
