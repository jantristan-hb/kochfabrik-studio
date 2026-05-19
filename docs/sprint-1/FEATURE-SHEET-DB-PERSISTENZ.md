# Feature-Sheet — Modul: DB-Persistenz (Sprint 1)

**Typ:** Infrastructure + Service
**Stories:** US-001…US-005

## Inputs
- `DATABASE_URL` (Coolify-ENV) → eigener Postgres `kf-studio-pg`
- Cookie `kf_sess` → `owner_email` (vorhandenes `valid_cookie`)
- Angebot-JSON (JS `A` / engine `angebot_model.Angebot`)

## Logik (Kern-Interfaces)
```python
# db.py
engine; async_sessionmaker; DB_OK: bool; DB_ERR: str
async def ping() -> bool
# numbering.py
async def next_kundennummer(s) -> str   # '100001-A', '100002-A', ...
async def next_angebotsnummer(s) -> str # 'KF-2026-0001', ...
# store.py  (alle owner-scoped)
async def save_offer(owner_email:str, angebot:dict) -> dict
   # -> {offer_id, angebotsnummer, kundennummer}
async def get_offer(owner_email:str, offer_id:int) -> dict | None
async def list_offers(owner_email:str) -> list[dict]
```

## Output
- Persistierte `offer.state` (vollständiges Angebot-JSON, S2-restore-fähig)
- Zugewiesene Kunden-/Angebotsnummer (im PDF sichtbar)
- `/api/angebote`, `/api/angebot/{id}`, `/api/angebot/save`

## Akzeptanz (= BDD/TEST.md)
- App graceful bei DB-Ausfall (DB_OK-Muster, Health-Flag)
- Migration idempotent
- `100001-A` erste Kundennummer, nebenläufig kollisionsfrei
- Tenant-Isolation (User sieht nur eigene)
- PDF persistiert + zeigt Nummern

## Nicht in diesem Modul
Chat-History-Restore (S2), UI/Bibliothek (S3), OAuth (S4).
