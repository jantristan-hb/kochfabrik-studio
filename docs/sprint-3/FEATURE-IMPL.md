# FEATURE-IMPL — Sprint 3

## Geänderte/neue Dateien
```
backend/store.py   # + stats(), list_customers(), get_customer();
                    #   list_offers(owner,q="",status="") erweitert
backend/app.py     # + GET /api/stats, /api/kunden, /api/kunde/{id};
                    #   /api/angebote q/status durchreichen
web/index.html     # Stub → echte KPIs + letzte (US-015)
web/bibliothek.html# Stub → suchbares Archiv (US-016)
web/kunden.html    # NEU — Kunden-CRM (US-017)
web/index.html + web/bibliothek.html  # Nav-Link "Kunden"
backend/tests/test_sprint3.py
docs/sprint-3/*
```
**Keine** Migration, **keine** neuen Tabellen. client.html unangetastet.

## Daten-Flows
- **stats:** `SELECT` Offer+Customer WHERE owner → count distinct
  customer, count offer, Σ über `state.bloecke[].zwischensumme`
  (defensiv: fehlende Keys → 0.0), letzte 5 by updated desc.
- **list_customers/get_customer:** join Customer/Offer WHERE owner;
  Detail = Kunde + list_offers-Shape seiner Angebote; fremd → None→404.
- **list_offers(q,status):** Python-Filter auf das bestehende
  Result (kleine Datenmenge, kein SQL-LIKE nötig) — q case-insensitiv
  über kunde/anlass/angebotsnummer, status exakt; leer = alles.
- **UI:** fetch → render; jede Zeile Link `chat.html?offer={id}`
  (S2 exaktes Wiederöffnen). 401→login. db:false/Fehler→Empty-State.

## Pitfalls
- Aggregat graceful: `_db.ping()` vor store-Aufruf (S1/S2-Muster),
  sonst 503 + Nullobjekt — UI zeigt Empty, nie 5xx.
- Volumen robust gegen `state` ohne `bloecke`/`zwischensumme`.
- `/api/angebote` Filter ADDITIV — ohne Query identisches S1-Verhalten
  (chat.html/andere Consumer dürfen nicht brechen).
- kunden.html: Layout/Sidebar 1:1 aus index.html kopieren
  (Konsistenz), nav-item "Kunden" aktiv; `assets/style.css` nutzen.
- client.html NICHT editieren (Regressionscheck `git diff`).
- Routen-Reihenfolge: `/api/kunde/{id}` vor evtl. generischeren
  Routen; FastAPI matcht in Deklarationsreihenfolge (wie S1
  `/api/angebot/{offer_id}` nach `/api/angebot/health`).

## Phasen
1 US-012 stats · 2 US-013 kunden · 3 US-014 filter · 4 US-015 index
· 5 US-016 bibliothek · 6 US-017 kunden.html. Sequentiell.
