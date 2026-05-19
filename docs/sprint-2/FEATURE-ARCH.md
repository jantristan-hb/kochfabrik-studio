# FEATURE-ARCH — Sprint 2: Chat-History + Restore + Tenant-Härtung

## Scope
Chat-Verlauf je Angebot persistieren, Angebot+Verlauf owner-scoped
laden, Chatbot-Editor exakt rekonstruieren. Plus S1-Carry-Over: echtes
Alembic, pytest-gegen-Test-PG.

### Goals
- Jeder Chat-Turn (me/bot) persistiert, offer-scoped
- Wiederöffnen `?offer={id}` → Editor-State + Chat-Stream 1:1 wie verlassen
- Keine Cross-Tenant-Lücke (Chat strikt owner-geprüft)
- Migrations-Historie (Alembic) ohne Live-Datenverlust; CI-fähige DB-Tests

### Non-Goals (S3/S4)
- Dashboard/Bibliothek-UI + Wiederöffnen aus Listen (S3 — hier nur
  `?offer=`-Parameter-Pfad)
- OAuth2 (S4) · Such/Filter · Chat-Edit/Delete

## Architektur (Delta zu S1)

```
chat.html  ──?offer={id}──►  GET /api/angebot/{id}
   │  A=state · renderForm() · #stream ← chat[]      → {angebot, chat}
   ▼
POST /api/angebot/chat (async, _owner)
   │  kein _offer_id → save_offer (S1) → offer_id
   │  _chat_patch (Engine)  → upd
   ▼
store.add_chat(owner, offer_id, "me"|"bot", content)   ── owner-Check
   ▼
chat_message (FK offer, ondelete CASCADE)   [S1-Schema, S2-Nutzung]
```

Migration: `migrate.py` → `alembic upgrade head` (Baseline = S1-Schema,
Live-DB via `stamp head`; idempotent/no-op am head; graceful).

## Datenmodell
**Keine neuen Tabellen** — `chat_message` (S1) wird genutzt:
`id, offer_id FK→offer ON DELETE CASCADE, role('me'|'bot'), content,
ts`. `offer.state` (JSONB) trägt weiterhin den vollen Angebot-Editor-
State inkl. `_offer_id`.

## API (Delta)
| Methode | Pfad | Änderung |
|---|---|---|
| POST | `/api/angebot/chat` | async + _owner; auto-save Offer; persistiert me+bot; Resp `{angebot, offer_id, persist_warn}` |
| GET | `/api/angebot/{id}` | Resp jetzt `{angebot, chat:[{role,content,ts}]}` (owner-scoped, 404 fremd) |

## Security
- `add_chat`/`get_offer_full`: Offer-Ownership-Check vor jedem
  chat_message-Read/Write — kein Cross-Tenant (Regressionstest US-009).
- Auth weiter über `_owner` (Cookie); OAuth-ready Abstraktion unverändert.
- Graceful: DB-Ausfall bricht Chat/PDF NICHT (nur ohne Persistenz).
- Alembic: `stamp head` auf bestehender Live-DB → kein DROP/RE-CREATE.

## Vision-Alignment
**Epic:** EPIC-001. **Sprint-Rolle:** macht Persistenz *nutzbar* —
Angebote+Gespräch sind reproduzierbar (Kern-Versprechen des Epics).
**Nächste Iteration:** S3 Dashboard/Bibliothek konsumiert `list_offers`
+ `?offer=` für Wiederöffnen aus der UI.
