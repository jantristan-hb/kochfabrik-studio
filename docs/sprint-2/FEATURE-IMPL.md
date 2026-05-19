# FEATURE-IMPL — Sprint 2

## Geänderte/neue Dateien
```
backend/store.py      # + add_chat(), get_offer_full()
backend/app.py        # /api/angebot/chat → async + _owner + persist;
                       #   /api/angebot/{id} → {angebot, chat}
web/chat.html         # ?offer= Lade-/Replay-Flow + history.replaceState
backend/alembic/ + alembic.ini   # US-010 (Baseline = S1-Schema)
backend/migrate.py    # US-010: alembic upgrade head statt create_all
backend/tests/conftest.py        # US-011 async session/Test-PG Fixture
backend/tests/test_sprint2.py    # US-006..009 Tests
requirements.txt      # US-011: pytest, pytest-asyncio (dev)
Dockerfile            # US-010: CMD migrate(alembic)→serve
```

## Daten-Flows
**Chat (US-006):** owner=_owner; wenn `angebot._offer_id` fehlt →
`save_offer` (S1, legt Offer+Nummern an, setzt `_offer_id`); `upd =
_chat_patch(angebot,msg)`; `add_chat(owner,oid,"me",msg)` +
`add_chat(owner,oid,"bot",bot_text)`; Resp `{angebot:upd,
offer_id, persist_warn}`. DB-Fehler → try/except, `persist_warn`, kein 5xx.
**Laden (US-007/008):** `GET /api/angebot/{id}` → `get_offer_full`
(owner-Check) → `{angebot,chat}`; chat.html `?offer=` → A+renderForm +
Stream-Replay.
**Tenant (US-009):** jede chat_message-Query joined/filtert über
`Offer.owner_email == owner`; `add_chat` lädt Offer + prüft owner,
sonst `raise PermissionError`.

## US-010 Alembic (Caveat)
- `env.py` async-engine aus `DATABASE_URL` (`_normalize` aus db.py
  wiederverwenden), `target_metadata=Base.metadata`.
- Baseline-Revision spiegelt S1-Schema 1:1. **Live-DB hat die Tabellen
  schon (S1 create_all)** → Deploy-Migration darf nicht neu anlegen:
  Entrypoint robust = `alembic upgrade head` (no-op am head); einmalig
  bestehende DB `alembic stamp head` (manuell oder idempotenter
  Entrypoint: wenn alembic_version leer & Tabellen existieren → stamp).
- Graceful: Alembic-Fehler loggen, App startet trotzdem (S1-Muster).

## Pitfalls
- `/api/angebot/chat` war sync → `async def` + `request: Request`;
  `_chat_patch` bleibt sync (in Thread/await-safe lassen).
- Abwärtskompat: `/api/angebot/{id}` MUSS weiter `angebot` als Key
  liefern (chat.html S1) — nur `chat` additiv.
- chat.html: Stream-Replay NICHT erneut an Bot senden; `esc()` für
  content; `history.replaceState` statt reload.
- Alembic auf Live: NIE autogenerate-drop gegen Prod; Baseline==Ist.
- pytest-asyncio Mode (`asyncio_mode=auto` o. Marker) in conftest/ini.

## Phasen
1 US-010 Alembic · 2 US-011 Test-Infra · 3 US-006 Chat-Persist ·
4 US-007 Laden · 5 US-009 Härtung · 6 US-008 Frontend-Restore.
Sequentiell (geteilte Dateien).
