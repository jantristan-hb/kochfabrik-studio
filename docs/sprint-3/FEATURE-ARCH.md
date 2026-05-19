# FEATURE-ARCH — Sprint 3: Dashboard + Bibliothek + Kunden-CRM

## Scope
Die persistierten Daten (S1/S2) sichtbar/nutzbar machen: Dashboard-
KPIs, suchbares Bibliotheks-Archiv, Kunden-CRM. Letzter Funktions-
Sprint von EPIC-001 (S4 OAuth „später").

### Goals
- index.html: echte KPIs + letzte Angebote (statt Stub)
- bibliothek.html: vollständiges, durchsuchbares/filterbares Archiv
- kunden.html: Kundenliste + Detail (1 Kunde : n Angebote)
- Alles owner-scoped, Wiederöffnen → `chat.html?offer={id}` (S2)

### Non-Goals
- OAuth2 (S4) · client.html „Client Research" (anderes Feature, bleibt)
- Charts/Reporting · Bulk-Ops · Export · Pagination (Datenmenge klein)

## Architektur (Delta)

```
index.html ───/api/stats──►  store.stats(owner)
bibliothek ──/api/angebote?q=&status=──► store.list_offers(owner,q,status)
kunden.html ─/api/kunden , /api/kunde/{id}─► store.list_customers /
                                              get_customer(owner,..)
   alle Listen-Zeilen → chat.html?offer={id}  (S2 exaktes Wiederöffnen)
```
Reine Lese-Aggregation auf S1/S2-Tabellen (offer/customer/state-JSONB).
**Keine neuen Tabellen, keine Migration.** Alles `_owner`-gescoped,
graceful (db down → 503 + leere Defaults, UI Empty-State).

## Datenmodell
Unverändert (S1). Aggregation liest `offer`/`customer`; Volumen =
Σ `offer.state.bloecke[].zwischensumme`.

## API (neu)
| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/api/stats` | {angebote,kunden,volumen,letzte[≤5]} owner |
| GET | `/api/kunden` | Kundenliste owner |
| GET | `/api/kunde/{id}` | Kunde + dessen Angebote (404 fremd) |
| GET | `/api/angebote?q=&status=` | bestehend + Filter (abwärtskompat) |

## Security
- Jede Query `WHERE owner_email` (Tenant-Isolation, Regressionstests).
- `_owner`-Cookie (S1, OAuth-ready). Kein neuer Auth-Pfad.
- Graceful: DB-Ausfall bricht keine Seite (Empty/Hinweis statt 5xx).

## Vision-Alignment
**Epic:** EPIC-001 — schließt den Kern-Loop sichtbar: erzeugen →
speichern (S1) → wieder aufnehmen (S2) → **wiederfinden/verwalten
(S3)**. Damit ist der CRM-/Persistenz-Nutzen für den User komplett.
**Nächste Iteration:** S4 OAuth2 (Login/Registrierung) auf der schon
vorhandenen `_owner`-Abstraktion.
