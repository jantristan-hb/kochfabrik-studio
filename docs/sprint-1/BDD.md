# BDD — Sprint 1

## US-001: Postgres + graceful DB-Layer {#us-001-postgres-graceful-db-layer}

### Szenario: App bootet trotz unerreichbarer DB
**Given** `DATABASE_URL` zeigt auf eine nicht erreichbare DB
**When** die App startet und `/api/health` abgefragt wird
**Then** die App läuft, `db:false` + `db_error` im Health, bestehende
Endpoints (chat/pdf) funktionieren unverändert

### Szenario: DB erreichbar
**Given** Postgres `kf-studio-pg` läuft, `DATABASE_URL` korrekt
**When** `/api/health`
**Then** `db:true`

## US-002: DB-Schema + Migrationen {#us-002-db-schema-migrationen}

### Szenario: Migration idempotent
**Given** frische DB
**When** `alembic upgrade head` zweimal
**Then** kein Fehler; alle Tabellen (app_user, customer, offer,
chat_message, seq_counter) existieren

## US-003: Atomare Nummern {#us-003-atomare-nummernsequenzen}

### Szenario: Erste Kundennummer
**Given** leerer seq_counter
**When** `next_kundennummer` erstmals
**Then** Ergebnis = `100001-A`

### Szenario: Keine Kollision bei Nebenläufigkeit
**Given** seq_counter
**When** N parallele `next_angebotsnummer`-Calls
**Then** N paarweise verschiedene, lückenlos fortlaufende Nummern

## US-004: Owner-scoped Store {#us-004-owner-scoped-store}

### Szenario: Tenant-Isolation
**Given** User A speichert ein Angebot
**When** User B ruft `get_offer`/`list_offers`
**Then** B sieht A's Angebot NICHT (get→None, list→ohne A's Eintrag)

### Szenario: Speichern weist Nummern zu
**Given** neues Angebot von User A
**When** `save_offer`
**Then** Customer + Offer angelegt, kundennummer `100001-A`,
angebotsnummer gesetzt, state == übergebenes Angebot-JSON

## US-005: API + Integration {#us-005-api-endpoints-integration}

### Szenario: Speichern & Wiederfinden
**Given** eingeloggter User (Cookie)
**When** `POST /api/angebot/save` dann `GET /api/angebote`
**Then** Liste enthält das Angebot mit Nummern

### Szenario: PDF persistiert + zeigt Nummern
**Given** eingeloggter User, Angebot ohne Nummern
**When** `POST /api/angebot/pdf`
**Then** Angebot ist persistiert, PDF enthält zugewiesene Kunden-/
Angebotsnummer; bei DB-Ausfall PDF trotzdem (ohne Persistenz)

### Szenario: Fremdes Angebot nicht ladbar
**Given** User B eingeloggt, offer_id gehört A
**When** `GET /api/angebot/{id}`
**Then** 404
