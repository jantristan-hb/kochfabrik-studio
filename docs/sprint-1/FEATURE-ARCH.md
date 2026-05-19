# FEATURE-ARCH — Sprint 1: DB-Fundament + Persistenz + Nummern

## Scope
DB-Persistenzschicht für den Angebotsgenerator. Eigener Postgres,
Schema, atomare Nummernsequenzen, owner-scoped Store, API + Integration
in die PDF-Generierung.

### Goals
- Angebote persistent + owner-scoped speicherbar/ladbar
- Fortlaufende Kunden- (`100001-A`) + Angebotsnummer, kollisionsfrei
- Null Regression: bestehende Endpoints unverändert, App graceful bei DB-Ausfall

### Non-Goals (spätere Sprints / Epic)
- Chat-History-Restore (S2 — Tabelle wird hier nur angelegt)
- Dashboard/Bibliothek-UI (S3)
- OAuth2 (S4, nur design-kompatibel: Auth über `owner_email`-Abstraktion)
- Such-/Filter-Logik, RBAC

## Architektur

```
Browser (chat.html JS `A`)
        │  POST /api/angebot/save | /pdf   GET /api/angebote | /angebot/{id}
        ▼
FastAPI app.py ── Cookie-Auth (valid_cookie → owner_email)
        │
        ▼
store.py (owner-scoped)  ──  numbering.py (atomar)
        │
        ▼
db.py (async engine, DB_OK graceful)  ──►  PostgreSQL  kf-studio-pg
        ▲                                   (eigener Coolify-Service)
   models.py / alembic (Schema, idempotent)
```

DB-Ausfall: `DB_OK=False` → save/list/load liefern 503-ähnlich graceful,
`/pdf` rendert weiter ohne Persistenz (Warnung). Muster = `ENGINE_OK`.

## Datenmodell (SQLAlchemy 2)

```python
app_user(email str PK, created ts)
customer(id int PK, kundennummer str UNIQUE, name str,
         owner_email str FK→app_user, created ts)
offer(id int PK, angebotsnummer str UNIQUE, customer_id int FK→customer,
      owner_email str FK→app_user, state JSONB, status str default 'draft',
      created ts, updated ts)
chat_message(id int PK, offer_id int FK→offer, role str, content text,
             ts ts)            # S2-Nutzung, S1 nur Schema
seq_counter(name str PK, value int)   # 'kunde','angebot' — atomarer Zähler
```

`offer.state` = vollständiges Angebot-JSON (JS `A` / engine
`angebot_model`), damit der Chatbot-Editor 1:1 rekonstruierbar ist.

## Nummernformat (Entscheidung, fixiert)
- **Kundennummer:** `f"{100000+n:06d}-A"` → erste = `100001-A`
  (A = AI). Zähler `seq_counter['kunde']`.
- **Angebotsnummer:** `f"KF-{YYYY}-{n:04d}"` (Jahr aus `created`,
  fortlaufender Zähler `seq_counter['angebot']`, nicht jahres-reset →
  global fortlaufend, Jahr nur Präfix). Beide atomar via
  `UPDATE seq_counter SET value=value+1 WHERE name=:n RETURNING value`.

## API

| Methode | Pfad | Auth | Zweck |
|---|---|---|---|
| POST | `/api/angebot/save` | Cookie | Angebot persistieren → {offer_id,angebotsnummer,kundennummer} |
| GET | `/api/angebote` | Cookie | eigene Angebote (Liste, Kurzfelder) |
| GET | `/api/angebot/{id}` | Cookie | eigenes Angebot laden (fremd → 404) |
| POST | `/api/angebot/pdf` | Cookie | wie bisher + save_offer + Nummern ins PDF |

Auth: vorhandenes `valid_cookie(COOKIE)` → email = owner. Kein neues
Auth-System (OAuth später, gleiche `owner_email`-Abstraktion).

## Security
- Jede Store-Query `WHERE owner_email=:owner` — keine Cross-Tenant-Leaks
  (Test-Pflicht US-004).
- `DATABASE_URL` nur als Coolify-ENV, nie im Repo (Secrets=~/work/.env).
- Idempotente Migrationen, additive Infra (neuer Container, nichts ersetzt).
- Pydantic-Validierung der Save-Payload.

## Vision-Alignment
**Epic:** EPIC-001 (Persistenz/Multi-Tenant/CRM). **Sprint-Rolle:**
Fundament — ohne DB+Nummern+owner-Scope ist S2 (Chat-History/Restore)
und S3 (Dashboard/Bibliothek) nicht baubar. **Nächste Iteration:** S2
Chat-History-Persistenz + exakte Editor-Rekonstruktion auf diesem
Fundament.
