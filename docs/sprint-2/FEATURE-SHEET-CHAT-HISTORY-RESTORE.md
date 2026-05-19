# Feature-Sheet — Modul: Chat-History & Exakte Wiederherstellung

**Typ:** Service + API + UI
**Stories:** US-006, US-007, US-008, US-009 (+ Tech-Debt US-010/011)

## Inputs
- Cookie `kf_sess` → `_owner(request)` (S1)
- `/api/angebot/chat {message, angebot}`; `?offer={id}` (chat.html)
- S1: `offer`, `chat_message`, `store.save_offer/get_offer`

## Logik (Kern-Interfaces)
```python
# store.py (neu)
async def add_chat(owner:str, offer_id:int, role:str, content:str) -> None
   # owner-Check auf Offer; sonst raise/abort (Tenant)
async def get_offer_full(owner:str, offer_id:int) -> dict | None
   # {"angebot": offer.state, "chat":[{role,content,ts(iso)}...]} | None
```
```
/api/angebot/chat (async): owner→ensure offer(save_offer wenn kein
  _offer_id)→_chat_patch→add_chat(me)+add_chat(bot)→{angebot,offer_id,
  persist_warn}
/api/angebot/{id} (GET): get_offer_full → {angebot, chat} | 404
```

## Output
- Persistierte chat_message-Reihen je Offer (CASCADE mit Offer)
- Wiederöffnen reproduziert Editor-State + Chat-Stream exakt
- Migrations-Historie (Alembic) + CI-fähige DB-Tests

## UI (chat.html)
```
?offer=123 → GET /api/angebot/123
  A = angebot ; renderForm(); collect(); syncTotals()
  for m in chat: add(m.role, esc(m.content))      # #stream replay
  history.replaceState(?offer=123)                # reload-fest
kein ?offer → wie bisher (neues Angebot)
```

## Akzeptanz (= BDD/TEST.md)
- Erster Chat legt Offer an, Turns persistiert; DB-Ausfall graceful
- get_offer_full owner-scoped (fremd → None/404)
- Wiederöffnen: State + voller Verlauf, kein Bot-Re-Request
- B kann A's Chat nicht lesen/schreiben
- Alembic idempotent auf bestehender Live-DB (stamp, kein DROP)
- pytest DB-Tests grün gegen Test-PG / sauber skip ohne

## Nicht in diesem Modul
Dashboard/Bibliothek-Listen-Wiederöffnen (S3), OAuth (S4),
Chat-Bearbeiten/Löschen.
