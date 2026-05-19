# Sprint 3 — Dashboard + Bibliothek + Kunden-CRM (letzter Funktions-Sprint)

> EPIC-001 Sprint 3. Baut auf S1+S2 (master 50f5c33): `store.py`
> (save_offer/get_offer/list_offers/get_offer_full/add_chat,
> owner-scoped), `chat.html?offer={id}` (Wiederöffnen), `_owner`,
> graceful DB, Alembic. Stack: FastAPI + PostgreSQL + SQLAlchemy 2
> async. Tests: pytest. GitHub → kein glab. Graceful-DB-Pflicht.
>
> Carry-Over: keine (S1-DEFERRED Alembic/pytest in S2 abgearbeitet).
> Web-Pages index/bibliothek/client sind aktuell **statische Stubs**
> mit Platzhalter-Daten → werden an echte Daten verdrahtet.
> S4 (OAuth) bewusst NICHT in S3.

## Phasen
Backend-Aggregation (US-012/013/014) → UI differenziert
(US-015 Dashboard, US-016 Bibliothek, US-017 Kunden-CRM).

---

### US-012: Stats/Aggregat-Endpoint (owner-scoped)

**Context:** Dashboard braucht echte Kennzahlen statt Platzhalter
("128 Decks").

**Input:** `backend/store.py` (list_offers-Muster), `_owner`,
`offer.state` (JSONB, Blöcke mit `zwischensumme`).

**Task:**
1. `store.py`: `async def stats(owner_email) -> dict` —
   `{angebote:int, kunden:int, volumen:float (Σ aller
   block.zwischensumme über alle Offers), letzte:[{offer_id,
   angebotsnummer,kunde,anlass,status,updated} ...max 5]}`.
   Strikt `WHERE owner_email`.
2. `GET /api/stats` (app.py, async, `_owner`, graceful: DB down →
   503 JSON mit Nullwerten).

**Output:** `backend/store.py` (`stats`), `backend/app.py` (`/api/stats`)

**BDD:** → `BDD.md#us-012-stats-endpoint`
**Test-Stubs:** → `TEST.md#us-012-stats-endpoint`

**Verify:**
```bash
python3 -c "import ast;[ast.parse(open(f).read()) for f in ['backend/store.py','backend/app.py']];print('OK')"
pytest backend/tests/test_sprint3.py -q -k stats
```
**Blocked-by:** —

---

### US-013: Kunden-Endpoints + Store (1 Kunde : n Angebote)

**Context:** CRM-Ansicht: Kundenliste + Detail mit dessen Angeboten.

**Input:** `backend/models.py` (Customer/Offer, S1), `_owner`.

**Task:**
1. `store.py`: `async def list_customers(owner) ->
   [{customer_id,kundennummer,name,angebote:int,letztes:iso}]`;
   `async def get_customer(owner, customer_id) ->
   {kunde:{...}, angebote:[list_offers-Shape]} | None` (owner-Check
   → None bei fremd).
2. `GET /api/kunden`, `GET /api/kunde/{id}` (async, `_owner`,
   graceful, 404 fremd).

**Output:** `backend/store.py`, `backend/app.py`

**BDD:** → `BDD.md#us-013-kunden-endpoints`
**Test-Stubs:** → `TEST.md#us-013-kunden-endpoints`

**Verify:**
```bash
pytest backend/tests/test_sprint3.py -q -k kunde
```
**Blocked-by:** —

---

### US-014: Angebote-Liste mit Such-/Status-Filter (owner-scoped)

**Context:** Bibliothek = durchsuchbares Archiv.

**Input:** `store.list_offers` (S1), `/api/angebote` (S1).

**Task:**
1. `list_offers(owner, q="", status="")` erweitern: `q`
   case-insensitive über kunde/anlass/angebotsnummer; `status`
   exakt; leere Filter = alles (abwärtskompat).
2. `GET /api/angebote?q=&status=` reicht Query durch (owner-scoped).

**Output:** `backend/store.py`, `backend/app.py`

**BDD:** → `BDD.md#us-014-angebote-filter`
**Test-Stubs:** → `TEST.md#us-014-angebote-filter`

**Verify:**
```bash
pytest backend/tests/test_sprint3.py -q -k filter
```
**Blocked-by:** —

---

### US-015: index.html — Dashboard mit echten KPIs

**Context:** Statischer Dashboard-Stub → echte Daten.

**Input:** US-012 (`/api/stats`); `web/index.html` (Stub, kanonische
Sidebar-Nav, "Zuletzt bearbeitet"-Tabelle).

**Task:**
1. `fetch('/api/stats')` → KPI-Kacheln (Angebote/Kunden/Volumen)
   füllen; Platzhalter-Zahlen entfernen.
2. "Zuletzt bearbeitet" = `stats.letzte` → Tabelle (Angebotsnr,
   Kunde, Anlass, Status, Datum), Zeile/Button → `chat.html?offer={id}`.
3. Loading- + Empty-State ("Noch keine Angebote — Angebotsgenerator").
   401 → `/login.html`. Graceful bei `db:false`.
4. Nav: Link "Kunden" (`kunden.html`) ergänzen.

**Output:** `web/index.html`

**BDD:** → `BDD.md#us-015-dashboard`
**Test-Stubs:** → `TEST.md#us-015-dashboard`

**Verify:**
```bash
python3 - <<'PY'
import re;h=open('web/index.html').read()
open('/tmp/i.js','w').write('\n'.join(re.findall(r'<script>(.*?)</script>',h,re.S)) or 'void 0')
PY
node --check /tmp/i.js && grep -q "/api/stats" web/index.html && echo OK
```
**Blocked-by:** US-012

---

### US-016: bibliothek.html — suchbares Angebots-Archiv

**Context:** Vollständiges, durchsuchbares/filterbares Archiv
(differenziert vom Dashboard-Überblick).

**Input:** US-014 (`/api/angebote?q=&status=`); `web/bibliothek.html`
(Stub).

**Task:**
1. Suchfeld (`q`) + Status-Filter (Dropdown) → debounced
   `fetch('/api/angebote?q=&status=')` → Tabelle (Angebotsnr, Kunde,
   Anlass, Status, Datum) sortiert nach `updated`.
2. Zeile → `chat.html?offer={id}` (Wiederöffnen, exakt — S2).
3. Loading/Empty-States; 401 → login. Platzhalter-Daten raus.
4. Nav: "Kunden" ergänzen.

**Output:** `web/bibliothek.html`

**BDD:** → `BDD.md#us-016-bibliothek`
**Test-Stubs:** → `TEST.md#us-016-bibliothek`

**Verify:**
```bash
python3 - <<'PY'
import re;h=open('web/bibliothek.html').read()
open('/tmp/b.js','w').write('\n'.join(re.findall(r'<script>(.*?)</script>',h,re.S)) or 'void 0')
PY
node --check /tmp/b.js && grep -q "/api/angebote" web/bibliothek.html && echo OK
```
**Blocked-by:** US-014

---

### US-017: kunden.html — Kunden-CRM (Liste + Detail)

**Context:** Kundendatenbank-Ansicht (1 Kunde : n Angebote). Neue
Seite (client.html „Client Research" bleibt unangetastet — anderes
Feature, nicht im Epic-Scope).

**Input:** US-013 (`/api/kunden`, `/api/kunde/{id}`); `web/`-Layout/
-Assets (style.css, Sidebar-Muster aus index.html).

**Task:**
1. Neue `web/kunden.html` (kanonisches Layout/Sidebar wie index.html,
   nav-item aktiv "Kunden").
2. Kundenliste (`/api/kunden`): Kundennr, Name, #Angebote, letztes
   Datum. Klick → Detail.
3. Detail (`?kunde={id}` → `/api/kunde/{id}`): Kundenkopf + Tabelle
   seiner Angebote, Zeile → `chat.html?offer={id}`.
4. Nav-Link "Kunden" in index.html + bibliothek.html (+ neue Seite)
   einfügen. Loading/Empty/401.

**Output:** `web/kunden.html` (+ Nav-Links in index/bibliothek)

**BDD:** → `BDD.md#us-017-kunden-crm`
**Test-Stubs:** → `TEST.md#us-017-kunden-crm`

**Verify:**
```bash
python3 - <<'PY'
import re;h=open('web/kunden.html').read()
open('/tmp/k.js','w').write('\n'.join(re.findall(r'<script>(.*?)</script>',h,re.S)) or 'void 0')
PY
node --check /tmp/k.js && grep -q "/api/kunden" web/kunden.html && echo OK
```
**Blocked-by:** US-013

---

## Dependency-Graph / Waves

| Wave | Stories | Hinweis |
|------|---------|---------|
| 1 | US-012, US-013, US-014 | Backend (alle store.py+app.py → sequentiell, Konflikt-Risiko) |
| 2 | US-015, US-016, US-017 | UI je [eigene Backend-Story] |

2 Waves. Headless: Pfad A **sequentiell** (US-012/013/014 teilen
store.py/app.py). Reihenfolge: 012 → 013 → 014 → 015 → 016 → 017.
