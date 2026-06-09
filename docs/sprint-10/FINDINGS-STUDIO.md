# FINDINGS-STUDIO — Bug-Analyse kochfabrik-studio (US-036 / EPIC-003 Q1)

> **Typ:** Analyse-Artefakt (Doc-only-Sprint, R-REF-6 — kein Code-Fix).
> **Scope:** `backend/`, `web/` (inkl. `_legacy/`), `Dockerfile`, `vendor.sh`,
> Deploy-Pfad. **Methode:** statische Code-Lektüre, jede Aussage mit
> `Datei:Zeile` belegt oder als Repro angegeben; nicht belegbare Verdachte
> als `VERWORFEN: {Grund}` geführt (FEATURE-BUG-ANALYSE §8 Nr. 4).
> **Stand:** 2026-06-09.
>
> **Schema je Finding:** `## F-S-NN: Titel` · Severity · `**Beleg:**` ·
> `**Zuordnung:**` (Epic/WP oder `VERWORFEN: {Grund}`).
>
> **Severity-Skala:** CRITICAL (Datenverlust/RCE/Auth-Bypass live) ·
> HIGH (Sicherheit/Korrektheit, real auslösbar) · MEDIUM (degradierte
> Funktion / latente Falle) · LOW (Hygiene/Hardening).
>
> **Doppelzählungs-Hinweis (FEATURE-BUG-ANALYSE §12.3):** F-S-01, F-S-02,
> F-S-04, F-S-07 sind bereits in REQUIREMENTS/Ideation als Verdachts-
> Kandidaten benannt — hier mit Code-Beleg verifiziert, nicht als
> Neuentdeckung verkauft.

---

## F-S-01: `alembic.ini` fehlt im Container → `alembic upgrade head` schlägt fehl, Versions-Drift

**Severity:** HIGH

**Beleg:** `Dockerfile:12-16` kopiert nur `requirements.txt`, `backend/`, `web/`, `engine/` — `alembic.ini` (Repo-Root) wird NICHT ins Image kopiert. `backend/migrate.py:68-69` ruft aber `subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], …)` mit cwd=`/app`. Dort existiert keine `alembic.ini` → `alembic` bricht ab; der Fehler wird in `migrate.py:76-78` graceful geschluckt (`Alembic übersprungen`). Folge: Auf einer DB, die noch auf `0001_baseline` steht (S1-Live), wird `0002`/`0003` NIE angewendet — Versions-Tracking driftet still. Der Stamp-Pfad (`migrate.py:59-66`) greift nur bei leerer/fehlender `alembic_version`-Tabelle und stampt dann direkt auf `HEAD="0003"` (`migrate.py:18`), überspringt also die echten Revisionen.

**Zuordnung:** EPIC-004/M6 (Alembic-Drift fixen, alembic.ini im Container)

---

## F-S-02: Open Sans fehlt im Docker-Image → LibreOffice-Font-Substitution beim PPTX→PDF-Render

**Severity:** HIGH

**Beleg:** `Dockerfile:6-9` installiert nur `fonts-dejavu-core` + `fonts-liberation`. Der Render-Pfad nutzt LibreOffice headless (`Dockerfile:8` libreoffice-impress) für PPTX→PDF; die Korpus-/Angebots-Decks sind aber in Open Sans gesetzt (EPIC-005 Font-Treue). Fehlt die Familie im Image, substituiert LibreOffice still durch Liberation/DejaVu → abweichende Glyph-Metriken/Zeilenumbrüche, „nicht super nah am PDF". Kein Open-Sans-Paket im `apt-get install`-Block.

**Zuordnung:** EPIC-005/T3 (Open Sans ins Docker-Image + Substitutions-Verify)

---

## F-S-03: Kein Rate-Limit/Usage-Cap auf den LLM-Endpoints → Kosten-/DoS-Exposure

**Severity:** HIGH

**Beleg:** `backend/app.py:549 /api/image` (Gemini-Image, Call in `image_kochfabrik`), `backend/app.py:578 /api/angebot/chat` (Anthropic, `_chat_patch` `app.py:435`) und `backend/slidesuche.py:133 /search` (Gemini-Embedding, `_embed` `slidesuche.py:148`) lösen pro Request kostenpflichtige Upstream-LLM-Calls aus. `grep -rn "rate.limit|ratelimit|throttle" backend/` liefert keinen Treffer — es gibt weder pro-User- noch globale Drosselung. Ein authentifizierter (oder bei kompromittiertem Cookie: beliebiger) Client kann unbegrenzt teure Calls auslösen.

**Zuordnung:** EPIC-010/H1 (Rate-Limits/Usage-Caps auf LLM-Endpoints pro User + global)

---

## F-S-04: `KF_SESSION_SECRET` defaultet auf Leerstring → bei fehlender Env signierbare/fälschbare Cookies

**Severity:** HIGH

**Beleg:** `backend/app.py:188-189` `_secret()` gibt `os.environ.get("KF_SESSION_SECRET", "")` zurück — bei nicht gesetzter Var wird mit **leerem** HMAC-Key signiert (`make_cookie` `app.py:204-205`) UND verifiziert (`valid_cookie` `app.py:251-252`). Es gibt keinen Fail-Fast/Startup-Guard (kein `raise`/`assert` für das Secret; `grep` zeigt `raise` nur in `image_kochfabrik`/Render, nicht beim Boot). Folge bei Fehlkonfiguration: jeder, der das (öffentlich bekannte, weil Repo public) Cookie-Format kennt, kann mit leerem Schlüssel ein gültiges Session-Cookie für eine beliebige `KF_USERS`-Mail bauen → Auth-Bypass. Verschärfend: die Signatur ist auf 128 bit gekürzt (`[:32]` Hex, `app.py:205`/`:252`).

**Zuordnung:** EPIC-010/H3 (Auth-Härtung gemäß Q1-Findings — Startup-Guard, der bei leerem Secret hart abbricht)

---

## F-S-05: `_db_user_ok` öffnet pro Request eine neue psycopg2-Verbindung (kein Pool, neben dem async-Engine-Pool)

**Severity:** MEDIUM

**Beleg:** `backend/app.py:233` `cx = psycopg2.connect(u, connect_timeout=2)` in `_db_user_ok` — eine frische synchrone Verbindung pro Cookie-Validierung eines OAuth-Users (durch `valid_cookie` `app.py:258` in der Auth-Middleware `app.py:489-497` auf JEDEM geschützten Request). Es existiert bereits ein async-Pool (`backend/db.py:29-31`), der hier umgangen wird. Der 60s-TTL-Cache (`app.py:243`) dämpft das, fängt aber Cache-Miss-Spitzen (viele verschiedene OAuth-User / Cold Cache) nicht ab → Connection-Churn gegen Postgres. Sync-`connect` blockiert zudem den Event-Loop (Aufruf aus async-Middleware-Kette).

**Zuordnung:** EPIC-010/H3 (Auth-Härtung — über den async-Pool/`db.py` lösen statt Sync-Connect je Request)

---

## F-S-06: OAuth-Email ungefiltert in den `|`-delimitierten Cookie-Raw → Integritäts-Edgecase bei `|` im Identifier

**Severity:** MEDIUM

**Beleg:** `backend/oauth.py:94-96` `exchange()` nimmt `email = info.get("email") or info.get("upn") or info.get("preferred_username")` — `upn`/`preferred_username` sind providerseitig weniger streng als RFC-Email. Dieser Wert geht in `app.py:927` direkt in `make_cookie(email)`, das `raw = f"{email.lower()}|{exp}"` baut (`app.py:203`). `valid_cookie`/`_owner` parsen via `raw.rsplit("|", 2)` (`app.py:250`/`:271`). Enthält der Identifier ein `|`, verschiebt sich das Split → `email` wird abgeschnitten, `exp` mis-geparst (`int(exp)` `app.py:254` wirft, landet im `except` → Cookie ungültig). Kein Hard-Security-Bypass (HMAC schützt), aber: ein legitimer OAuth-User mit `|` im Claim kann sich nicht einloggen, und die Tenant-Scope-Email (`_owner`) wäre im Grenzfall verfälscht. Keine Sanitisierung/Reject von `|` vorhanden.

**Zuordnung:** EPIC-010/H3 (Auth-Härtung — Identifier-Validierung/Reject bei `|` oder strukturiertes Cookie-Encoding)

---

## F-S-07: `web/_legacy/praesentationsgenerator.html` ist toter EPIC-002-Rollback-Rest, wird aber von StaticFiles mit ausgeliefert

**Severity:** LOW

**Beleg:** `web/_legacy/praesentationsgenerator.html` (einziger Inhalt von `_legacy/`) stammt aus dem in Sprint 9 zurückgerollten WYSIWYG-Generator (EPIC-002, „DONE (rollback Sprint 9)" docs/epics/README.md:16). `backend/app.py:939` mountet `StaticFiles(directory=WEB, html=True)` auf `/` — damit ist die Legacy-Seite unter `/_legacy/praesentationsgenerator.html` weiterhin abrufbar (durch die Auth-Middleware geschützt, aber funktional verwaist; keine Nav verlinkt sie). Toter, mit-ausgelieferter Code.

**Zuordnung:** EPIC-004/M5 (Dead Code raus) bzw. M1 (Alt-Verzeichnisse gemäß ADR)

---

## F-S-08: `web/chat.html` ruft `/api/praesentation/from-angebot` auf — in Prod hart 503 (Korpus-Cache nicht gemountet)

**Severity:** MEDIUM

**Beleg:** `web/chat.html:221` `fetch('/api/praesentation/from-angebot', {method:'POST', …})`. Der Endpoint `app.py:838` läuft durch `_praes_guard()` (`app.py:783-792`), das `_korpus_ok()` (`app.py:762-772`) verlangt: >5 Deck-Dirs im Korpus-Cache (~4,8 GB). Laut `vendor.sh:16-21,97-99` ist `data/cache/` auf dem Server ein Coolify Directory Mount und der Voll-Korpus ist NICHT vendorbar/gemountet (REQUIREMENTS: „nicht vendorbar"). Folge: Der „Aus Angebot → Deck"-Button im UI liefert in Prod deterministisch `503 Korpus-Cache … nicht gemountet` — ein im Frontend angebotener, serverseitig nicht erfüllbarer Pfad (degradierte Funktion, kein Crash).

**Zuordnung:** EPIC-006/D4 (Generator-Deck als Startpunkt — Scope-Entscheid ?) bzw. EPIC-009/B2 (Korpus-Volume-Pfad); UI-Gating gegen `/api/praesentation/health` als Härtung in EPIC-004/M4

---

## F-S-09: pg_shim-Bypass in `slidesuche.py` — direkter `pgbundle.npz`-Zugriff, zweiter Pfad zur selben Daten-Wahrheit

**Severity:** LOW

**Beleg:** `backend/slidesuche.py:98-115` `_bundle()` lädt `data/pgbundle.npz` direkt via numpy und normalisiert die Embeddings selbst (`slidesuche.py:107-114`), während der Rest der Engine (`assemble.py`) über das pg_shim/`PPTX_PGSHIM`-Konstrukt geht (`app.py:804`). Der Kommentar `slidesuche.py:99-103` begründet das bewusst (pg_shim kann die ANN-Query-Form nicht), aber es entsteht eine zweite, parallele Lade-/Konsistenz-Achse: `pgbundle.npz` wird von `vendor.sh:51-84` aus der Live-DB regeneriert; driftet das Bundle gegen den Korpus-Cache (`_CACHE` `slidesuche.py:38`), liefert die Suche Treffer, deren PNG dann fehlt (durch den Existenz-Filter `slidesuche.py:180` still verworfen → leise weniger als `limit` Resultate). Architektur-Schuld, kein Laufzeit-Crash.

**Zuordnung:** EPIC-004/M5 (Engine-Skripte ordnen, Runtime vs. Tooling) bzw. EPIC-003-Folge ADR-003 (pgbundle vs. Postgres, US-043)

---

## F-S-10: `_gemini_key()` liest Dev-Fallback `~/work/.env` — im Container wirkungslos, in lokalen Dev-Setups latentes Secret-Leak-Muster

**Severity:** LOW

**Beleg:** `backend/app.py:280-286` — fehlt `GEMINI_API_KEY` in der Env, liest `_gemini_key()` zeilenweise `~/work/.env` (`app.py:281` `os.path.expanduser`). Im Container existiert dieser Pfad nicht (Fallback no-op, harmlos), aber das Muster koppelt den Prozess an eine maschinen-lokale Secret-Datei außerhalb des Deploy-Kontrakts (Env-only). In lokalen/CI-Läufen wird damit unbeabsichtigt ein persönliches `.env` gezogen. Hygiene/Hardening, kein Live-Bug.

**Zuordnung:** EPIC-010/H2 (Secrets-Audit — Env/Coolify only, Dev-Fallback entfernen)

---

## Geprüft & VERWORFEN (kein belegbarer Bug)

## F-S-11: Vermutung — `make_cookie` `|`-Delimiter generell unsicher (Email-Injection)

**Severity:** LOW

**Beleg:** `app.py:203` `raw = f"{email.lower()}|{exp}"`, geparst via `rsplit("|", 2)` (`app.py:250`). Für regulär per `KF_USERS` konfigurierte Mail-Adressen (RFC-Email enthält kein `|`) ist der Parse korrekt: `rsplit(…, 2)` schneidet von rechts genau `exp` und `sig` ab. Der einzige real auslösbare Edgecase (`|` in einem OAuth-Identifier) ist bereits separat als F-S-06 belegt. Eine darüber hinausgehende Injection-Schwäche ist im Code NICHT belegbar — der HMAC über `f"{email}|{exp}"` deckt den ganzen Raw ab.

**Zuordnung:** VERWORFEN: Kein eigenständiger Bug — der einzige reale Trigger ist F-S-06; für RFC-Mails ist der Parse korrekt und HMAC-gesichert.

---

## F-S-12: Vermutung — StaticFiles-Mount auf `/` shadowed die API-Routen

**Severity:** LOW

**Beleg:** `app.py:939` `app.mount("/", StaticFiles(...))` steht nach `include_router` (`app.py:482`) und allen `@app.get/post`-Dekoratoren. In Starlette werden explizite Routen/Router VOR einem Catch-all-Mount ausgewertet (Reihenfolge der Registrierung); `/api/*` und `/` (`app.py:934`) sind vor dem Mount registriert. Ein Repro, bei dem eine API-Route durch den StaticFiles-Mount verdeckt wird, ist im Code nicht konstruierbar.

**Zuordnung:** VERWORFEN: Routen sind vor dem Mount registriert (`app.py:482`/`:934` vor `:939`) → korrekte Starlette-Auflösungsreihenfolge, keine Verdeckung belegbar.

---

## Zusammenfassung

| ID | Severity | Kurz | Zuordnung |
|---|---|---|---|
| F-S-01 | HIGH | alembic.ini fehlt im Container | EPIC-004/M6 |
| F-S-02 | HIGH | Open Sans fehlt im Image | EPIC-005/T3 |
| F-S-03 | HIGH | Kein Rate-Limit auf LLM-Endpoints | EPIC-010/H1 |
| F-S-04 | HIGH | KF_SESSION_SECRET defaultet leer | EPIC-010/H3 |
| F-S-05 | MEDIUM | psycopg2-Connect je Request (kein Pool) | EPIC-010/H3 |
| F-S-06 | MEDIUM | OAuth-Email `|` ungefiltert in Cookie-Raw | EPIC-010/H3 |
| F-S-07 | LOW | web/_legacy/ toter Rollback-Rest, ausgeliefert | EPIC-004/M5 |
| F-S-08 | MEDIUM | chat.html -> praesentation-Endpoint 503 in Prod | EPIC-006/D4 · EPIC-004/M4 |
| F-S-09 | LOW | pg_shim-Bypass, zweite Daten-Achse | EPIC-004/M5 · ADR-003 |
| F-S-10 | LOW | _gemini_key Dev-Fallback ~/work/.env | EPIC-010/H2 |
| F-S-11 | LOW | (VERWORFEN) | — |
| F-S-12 | LOW | (VERWORFEN) | — |

**10 verifizierte Findings** (3 HIGH, 3 MEDIUM, 4 LOW) + 2 verworfen.
Security-Cluster (F-S-03/04/05/06) speist EPIC-010; Deploy-/Build-Cluster
(F-S-01/02) speist EPIC-004/M6 + EPIC-005/T3.
