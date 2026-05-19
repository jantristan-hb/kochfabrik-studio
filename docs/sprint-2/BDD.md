# BDD — Sprint 2

## US-006: Chat-Turns persistieren {#us-006-chat-turns-persistieren}

### Szenario: Erster Chat legt Offer an + speichert Turn
**Given** eingeloggter User, Angebot ohne `_offer_id`
**When** `POST /api/angebot/chat {message}`
**Then** Offer wird angelegt (Nummern zugewiesen), `_offer_id` in
Response; je 1 chat_message `me` + `bot` persistiert

### Szenario: DB-Ausfall bricht Chat nicht
**Given** DB nicht erreichbar
**When** `/api/angebot/chat`
**Then** Antwort kommt (Engine), Response enthält `persist_warn`,
kein 5xx

## US-007: Angebot + Chat laden {#us-007-angebot-chat-laden}

### Szenario: Laden liefert State + Verlauf
**Given** Offer mit 2 persistierten Turns (User A)
**When** A `GET /api/angebot/{id}`
**Then** `{angebot: state, chat: [4 Einträge chronologisch
(role,content,ts)]}`

### Szenario: Fremdes Offer
**Given** Offer gehört A
**When** B `GET /api/angebot/{id}`
**Then** 404, kein Leak von state/chat

## US-008: chat.html Wiederöffnen {#us-008-chat-html-wiederoeffnen}

### Szenario: ?offer= rekonstruiert exakt
**Given** `?offer={id}` eines eigenen Angebots
**When** chat.html lädt
**Then** Editor zeigt gespeicherten State (renderForm), `#stream`
zeigt den vollständigen Verlauf in Reihenfolge, kein Bot-Re-Request

### Szenario: ohne Param = neues Angebot
**Given** chat.html ohne `?offer=`
**Then** unverändertes Verhalten (leeres/neues Angebot)

## US-009: Tenant-Härtung {#us-009-tenant-haertung}

### Szenario: B kann A's Chat nicht lesen/schreiben
**Given** Offer von A mit Chat
**When** B versucht get_offer_full / add_chat auf A's offer_id
**Then** None bzw. Abbruch — keine fremde chat_message les-/schreibbar

## US-010: Alembic-Setup {#us-010-alembic-setup}

### Szenario: Idempotent auf bestehender Live-DB
**Given** Live-DB mit S1-Schema (Tabellen existieren), `stamp head`
**When** `alembic upgrade head` (2x)
**Then** kein Fehler, kein DROP/RE-CREATE, genau 1 head

## US-011: pytest Test-PG {#us-011-pytest-test-pg}

### Szenario: DB-Tests laufen gegen Test-PG
**Given** `TEST_DATABASE_URL` gesetzt
**When** `pytest backend/tests`
**Then** S1+S2 DB-Tests (numbering/store/chat/tenant) grün; ohne
Var → sauber skipped
