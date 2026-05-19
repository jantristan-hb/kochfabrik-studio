# Feature-Sheet — Modul: Dashboard / Bibliothek / Kunden-CRM

**Typ:** Service + API + UI · **Stories:** US-012..017

## Inputs
- Cookie `kf_sess` → `_owner` (S1) · `offer`/`customer` (S1)
- `offer.state.bloecke[].zwischensumme` (Volumen-Aggregat)
- Query: `?q=`, `?status=`, `?offer=`, `?kunde=`

## Logik (Kern-Interfaces)
```python
# store.py (neu/erweitert)
async def stats(owner) -> {angebote:int,kunden:int,volumen:float,
                           letzte:list[≤5]}
async def list_customers(owner) -> [{customer_id,kundennummer,name,
                                     angebote:int,letztes:iso}]
async def get_customer(owner, customer_id) -> {kunde,angebote[]} | None
async def list_offers(owner, q="", status="") -> [...]   # + Filter
```
```
GET /api/stats · /api/kunden · /api/kunde/{id} ·
GET /api/angebote?q=&status=     (alle owner-scoped, graceful)
```

## Output / UI
```
index.html   : KPI-Kacheln (stats) + "Zuletzt"-Tabelle → ?offer=
bibliothek.html: Suchfeld+Status-Filter → /api/angebote → Tabelle → ?offer=
kunden.html  : Kundenliste → /api/kunde/{id} Detail → ?offer=
(client.html : UNVERÄNDERT — anderes Feature)
Nav: "Kunden"-Link in index+bibliothek+kunden
Jede Seite: Loading + Empty-State + 401→/login.html
```

## Akzeptanz (= BDD/TEST.md)
- stats/kunden/filter strikt owner-scoped (Tenant-Regression)
- Volumen = Σ zwischensummen; letzte ≤5
- Bibliothek-Suche debounced, abwärtskompat (leere Filter = alle)
- Wiederöffnen via `chat.html?offer={id}` (S2 exakt)
- DB-Ausfall → Empty/503, kein 5xx
- client.html per `git diff` unverändert

## Nicht in diesem Modul
OAuth (S4), Charts/Export/Pagination, client.html-Umbau.
