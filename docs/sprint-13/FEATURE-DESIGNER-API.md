---
key: KOCHFABRIK-FEATURE-011
status: implemented
title: "Präsentationsdesigner — Vorschlags-API (Angebot → Slide-Kandidaten)"
created: 2026-06-11
project: kochfabrik
---

# KOCHFABRIK-FEATURE-011: Designer-Vorschlags-API

> **Typ:** FEATURE (Brownfield-Delta). Sprint 13 / EPIC-006 D6 + D3.
> Kern-Idee (Jan): Die Generator-Pipeline wird zur VORSCHLAGSQUELLE —
> statt Top-1-Slide pro Gang fest zu verbauen, liefert sie Top-N
> Kandidaten, aus denen der User wählt.

## 1. Vision

Der User lädt ein Angebot hoch (PDF) oder wählt ein gespeichertes —
das System liefert pro Gang/Kategorie die passendsten Referenz-Slides
als Kandidaten (mit PNG-Preview) plus die Pflicht-Frame-Gruppe
(Cover/Crew/Personal/Wertschätzung/Kontakt). Zusammen mit der
Freitext-Suche entsteht daraus per Klick ein Deck.

## 3. Datenmodell (API-Verträge, generisch)

### Suggest-Response

| Feld | Typ | Beschreibung |
|---|---|---|
| `offer` | `object` | `{kunde: string, datum: string, gaenge: array[string]}` (geparst) |
| `groups` | `array[group]` | eine Gruppe je Gang + eine `pflicht`-Gruppe |
| `group.label` | `string` | Gang-Text bzw. `Pflicht-Slides` |
| `group.kind` | `enum` | `gang` / `pflicht` |
| `group.candidates` | `array[candidate]` | Top-N (Default 5) |
| `candidate` | `object` | `{deck: string, page: int, score: decimal, preview: string (URL), label: string}` |

## 4. Flows

```
POST /api/designer/suggest (multipart PDF ODER {offer_id} ODER {offer: json})
  → Parsing: bestehende Engine-Funktionen (parse_header/parse_offer_dishes
    — WIEDERVERWENDEN, nicht duplizieren)
  → 1 Gemini-Embed-Batch über alle Gänge (wie assemble.py)
  → je Gang bundle.rank Top-N (statt Top-1) gegen menu_composition-Slides
  → Pflicht-Gruppe aus static_slide (pg_shim-Query wie pick_frame)
  → Kandidaten mit preview-URL (bestehende Route
    /api/slidesuche/preview/{deck}/{page}.png — Previews liegen für
    alle Korpus-Decks vorab im Volume)
Download: bestehender POST /api/slidesuche/download (unverändert, D3).
```

## 7. API-Skizze

```
POST /api/designer/suggest    — Body: PDF-Upload | {offer_id} | {offer}
                                → Suggest-Response (s. §3); 401 ohne Auth;
                                503 graceful wenn Engine/Korpus fehlt
GET  /api/designer/health     — {engine, korpus, embed} (embed = Gemini-Key da)
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN ein Angebots-PDF hochgeladen wird THE SYSTEM SHALL eine
   Suggest-Response liefern mit ≥1 Gang-Gruppe à Top-N Kandidaten
   (Default 5, je mit deck/page/score/preview-URL) und einer
   Pflicht-Gruppe.
2. WHEN eine `offer_id` eines gespeicherten Angebots übergeben wird
   THE SYSTEM SHALL dieselbe Response-Struktur aus dem DB-Angebot
   erzeugen (Wiederverwendung der `_ang2md`-Kette aus engine_glue (Muster: praes_from_angebot)).
3. IF Engine oder Korpus fehlen THEN THE SYSTEM SHALL 503 mit
   Klartext-Fehler liefern (graceful, kein 500); IF der Gemini-Embed
   fehlschlägt THEN 502 mit gekürzter Fehlermeldung.
4. THE SYSTEM SHALL die Kandidaten-Rankings über `engine/scripts/
   bundle.py` beziehen (keine eigene np.load/ANN — ADR-003-Regel).

## 9. Abgrenzung (Nicht-Teil)

- Kein neues Slide-Rendering / keine Text-Swaps (D5, Ausbaustufe)
- Kein neuer Download-Pfad (D3 nutzt slidesuche/download verbatim)
- Keine Persistenz der Vorschläge server-seitig (Storyboard = Client)

## 9a. Boundaries (3-Tier)

- ✅ **Always:** neuer Router `backend/routers/designer.py` nach
  bestehendem Muster (engine_glue, kein app-Import); Tests
- ⚠️ **Ask-first (headless → BLOCKED):** Änderungen an assemble.py/
  compose_offer-LOGIK (nur importieren/aufrufen!); neue Runtime-Dependency
- 🚫 **Never:** eigenes np.load/ANN (bundle.py-Regel); master pushen;
  pgbundle/cache schreiben; Gemini-Calls in Unit-Tests (mocken!)

## 10. Abgrenzung zum Ist

- assemble.py: Angebot → fertiges Deck (Top-1 fest) → NEU: gleiche
  Pipeline-Bausteine liefern Top-N-KANDIDATEN als JSON
- Slidesuche: Freitext → Top-5 → bleibt; Designer ergänzt
  Angebots-getriebene Vorschläge

## 11. Implementierungs-Anker (Ist)

`engine/scripts/assemble.py` (parse_header; Ablauf-Vorlage Z.1–20-Doku),
`engine/scripts/compose_offer.py` (embed = Gemini-Batch,
parse_offer_dishes, slot_count, pick_frame, menu_overlay),
`engine/scripts/bundle.py` (load/normalize_query/rank — einzige
ANN-Schicht), `engine/scripts/pg_shim.py` (static_slide-Query-Shape),
`backend/routers/praesentation.py` (Upload-Muster from-pdf:
%PDF-Magic-Check, 25-MB-Limit, tempfile), `backend/engine_glue.py:340-347`
(`_ang2md` = angebot_to_offer_md-Re-Export; Nutzung: praesentation.py:105),
`backend/routers/angebot.py:237,311` (GET /api/angebote + /api/angebot/{offer_id}), `backend/slidesuche.py`
(Preview-Route + `_PREV`-Pfade), `backend/engine_glue.py`
(ENGINE_OK, sys.path), `backend/tests/test_charakterisierung.py`
(TestClient-Muster mit make_cookie).

## 12. Bekannte Pitfalls

1. **Gemini-Embed im Test/CI:** Suggest braucht GEMINI-Key — Endpoint-
   Tests mocken die embed-Funktion (monkeypatch auf Modul-Ebene),
   sonst rote CI + Kosten. Ein Live-Smoke bleibt manuell.
2. **Top-N ≠ Top-1-Refactor:** bundle.rank(k=N) statt [0] — NICHT die
   assemble-Logik umbauen (die bleibt Verhalten-identisch), sondern
   die Bausteine in designer.py NEU KOMBINIEREN.
3. **Preview-404s:** Decks ohne preview/-PNGs im Volume → Kandidat
   trotzdem liefern, FE zeigt Platzhalter (kein Server-Render on
   demand — zu teuer).
4. **PPTX_PGSHIM-Kontext:** pg_shim-Queries laufen nur mit gesetztem
   Env im Studio-Kontext — wie praesentation.py es macht (subprocess)
   bzw. direkt-Import mit PPTX_PGSHIM=1-Semantik prüfen.
5. **Upload-Validierung:** %PDF-Magic + Größenlimit wie from-pdf —
   identische Grenzen, kein neues Verhalten erfinden.

## Vision-Alignment

**Adressierte These:** R-DECK-1, R-DECK-3, R-DECK-4 (konkretisiert als
D6), R-NF-1 · EPIC-006/D6 (neues R-ID via /epic nachzutragen)
**Kern-Loop-Schritt:** Angebot → Deck wird interaktiv statt Blackbox
**Nächste Iteration:** D5 Text-Swap (Kundenname auf Slides), Cover-Generierung

## Referenzen
- implements → REQUIREMENTS R-DECK-1, R-DECK-3, R-DECK-4, R-NF-1, R-NF-3
- depends_on → [[KOCHFABRIK-ADR-003]] (bundle-Schicht) · EPIC-006 D6
- relates_to → [[KOCHFABRIK-FEATURE-012]] (UI)

## Referenziert von
— USER-STORIES Sprint 13 (US-061, US-062, US-067)
