# Sprint 4 — OAuth2 (Microsoft/Google) auf der _owner-Abstraktion

> EPIC-001 Sprint 4 (Abschluss). Baut auf S1-S3 (master e4ad9e4):
> Cookie-Auth `make_cookie`/`valid_cookie`/`_owner`, `app_user`-Tabelle
> (S1), KF_USERS-Passwort-Login. Stack: FastAPI + Postgres.
>
> **OBERSTE REGEL: ZERO REGRESSION.** Live-Prod-App. Unkonfiguriert
> (keine OAuth-ENV) → exakt heutiges Verhalten (KF_USERS-Passwort,
> keine Buttons). OAuth ist rein additiv + env-gated. valid_cookie
> KF_USERS-Pfad bleibt unverändert (Short-Circuit zuerst).
>
> **Externe Abhängigkeit (NICHT autonom):** Live-OAuth braucht vom
> User registrierte Azure-AD- + Google-Cloud-OAuth-Apps + Client-
> Secrets als Coolify-ENV. Code ist env-getrieben & deploy-ready;
> bis ENV gesetzt ist, ist OAuth schlicht inaktiv (kein Schaden).

## Phasen
Provider-Config (US-018) → Routes (US-019) → valid_cookie-Erweiterung
(US-020, kritisch) → login.html-Buttons (US-021).

---

### US-018: OAuth-Provider-Konfiguration (env-gated)

**Context:** Microsoft/Google nur aktiv wenn Client-ID+Secret als ENV
gesetzt. Sonst komplett inaktiv (Null-Regression).

**Input:** `backend/app.py` (os.environ-Muster).

**Task:**
1. `backend/oauth.py`: `providers()` → dict der AKTIVEN Provider aus
   ENV: google (`KF_OAUTH_GOOGLE_ID`/`_SECRET`), microsoft
   (`KF_OAUTH_MS_ID`/`_SECRET`/`_TENANT` default `common`). Nur mit
   id+secret aktiv. `redirect_uri(provider, request)` aus
   `KF_OAUTH_REDIRECT_BASE` o. Request-Host. Authorize/Token/Userinfo-
   URLs je Provider.
2. Nur stdlib (`urllib`, `json`, `hmac`) — keine neue Dependency.

**Output:** `backend/oauth.py`

**Verify:** `python3 -c "import ast;ast.parse(open('backend/oauth.py').read())"`;
ohne ENV → `providers()=={}`.
**Blocked-by:** —

---

### US-019: OAuth-Routes (login/callback) + Auto-Registrierung

**Context:** Authorization-Code-Flow; bei Erfolg dieselbe `kf_sess`-
Session wie Passwort-Login (volle Integration in Tenant-Modell).

**Input:** US-018; `make_cookie` (S1), `store._ensure_user` (S1).

**Task:**
1. `GET /api/oauth/providers` (PUBLIC) → `{providers:[keys]}`.
2. `GET /api/oauth/{p}/login` (PUBLIC) → 302 zur Authorize-URL;
   signierter, kurzlebiger `kf_oauth_state`-Cookie (HMAC `_secret()`).
3. `GET /api/oauth/{p}/callback` (PUBLIC) → State prüfen → Code→Token
   →Userinfo→`email`. `app_user`-Row sicherstellen (DB, graceful).
   `kf_sess`=`make_cookie(email)` setzen → redirect `/`. Fehler →
   `/login.html?err=oauth`.
4. PUBLIC um die 3 Pfade erweitern. Provider unbekannt/inaktiv → 404.

**Output:** `backend/app.py` (+ oauth-Routes), `backend/oauth.py`

**Verify:** Routes registriert; ohne ENV `/api/oauth/providers` → `[]`,
`/api/oauth/google/login` → 404.
**Blocked-by:** US-018

---

### US-020: valid_cookie um DB-User erweitern (ZERO-REGRESSION)

**Context:** OAuth-User stehen nicht in KF_USERS → valid_cookie muss
sie über `app_user` (DB) akzeptieren — OHNE den KF_USERS-Pfad oder
die Robustheit zu verändern.

**Input:** `valid_cookie` (app.py:195), `app_user` (S1), psycopg2
(dep seit S2).

**Task:**
1. `valid_cookie`: nach Signatur/Exp-Check — `email in _users()`
   bleibt **erster** Treffer (KF_USERS unverändert, kein DB-Hit).
   NUR wenn nicht in KF_USERS: `_db_user_ok(email)` (psycopg2-
   SELECT app_user, kurzer Timeout, TTL-Cache ~60s).
2. `_db_user_ok` **exception-safe**: DB-Fehler/down → `False`
   (kein Lockout für KF_USERS, kein Raise, kein 5xx).
3. Default (keine OAuth-ENV, keine OAuth-User) → Verhalten bit-
   identisch zu heute.

**Output:** `backend/app.py` (`valid_cookie`, `_db_user_ok`)

**Verify:** KF_USERS-User-Cookie weiter gültig; unbekannte Email →
False; DB-down → KF_USERS-User trotzdem rein (Graceful-Test).
**Blocked-by:** —

---

### US-021: login.html — Provider-Buttons (konditional)

**Context:** Buttons nur wenn Provider aktiv; sonst Seite unverändert.

**Input:** US-019 (`/api/oauth/providers`); `web/login.html`.

**Task:**
1. Nach Load `fetch('/api/oauth/providers')`; je aktivem Provider
   Button „Mit Microsoft/Google anmelden" → `/api/oauth/{p}/login`.
2. Keine Provider → DOM unverändert (Passwort-Login wie heute).
3. `?err=oauth` → Hinweis anzeigen.

**Output:** `web/login.html`

**Verify:** `node --check` JS; ohne Provider keine Buttons.
**Blocked-by:** US-019

---

## Waves
| Wave | Stories |
|------|---------|
| 1 | US-018, US-020 |
| 2 | US-019 (US-018) |
| 3 | US-021 (US-019) |
Sequentiell (US-018/019/020 → app.py). Reihenfolge 018→020→019→021.
