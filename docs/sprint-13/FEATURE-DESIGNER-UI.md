---
key: KOCHFABRIK-FEATURE-012
status: approved
title: "Präsentationsdesigner — UI (Vorschläge + Suche + Storyboard + Download)"
created: 2026-06-11
project: kochfabrik
---

# KOCHFABRIK-FEATURE-012: Designer-UI

> **Typ:** FEATURE (Brownfield-Delta). Sprint 13 / EPIC-006 D1+D2+D3+D6.
> Design-2-Frontend (Gold/Weiß, kanonische Sidebar) wie alle Seiten.

## 1. Vision

Eine Seite `web/designer.html`: links die Quelle (Angebots-Upload oder
gespeichertes Angebot wählen) + Freitext-Suche, Mitte die
Vorschlags-Gruppen (PNG-Karten je Gang + Pflicht-Slides), rechts das
Storyboard (gewählte Slides, Reihenfolge, Entfernen, Download). Der
User „designt" seine Präsentation per Klick.

## 4. Flows

```
Quelle wählen:  Upload-PDF  ODER  Dropdown gespeicherter Angebote
                (GET /api/angebote)  → POST /api/designer/suggest
Vorschläge:     Gruppen-Spalten, Karte = PNG-Preview + Score + Deck/Seite;
                Klick → ins Storyboard (visuelles Feedback „im Deck")
Suche:          Eingabe → POST /api/slidesuche/search → Karten wie oben
Storyboard:     Thumbnails in Reihenfolge; ↑/↓ + Entfernen; Zähler;
                sessionStorage (reload-fest, D2 Session-Level = Default)
Download:       Button → POST /api/slidesuche/download {slides:[{deck,page}]}
                → PPTX (Data-URL wie bestehende Downloads)
Fehler/Empty:   503-Korpus-Hinweis, Preview-Platzhalter bei 404,
                leeres Storyboard = Download disabled
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN der User ein Angebot hochlädt oder auswählt THE SYSTEM SHALL
   Vorschlags-Gruppen mit klickbaren PNG-Karten anzeigen; ein Klick
   SHALL die Slide ins Storyboard übernehmen.
2. WHEN der User die Freitext-Suche nutzt THE SYSTEM SHALL Treffer
   als gleichartige Karten anzeigen, die ebenfalls per Klick ins
   Storyboard wandern (Kombination Suche + Vorschläge, eine Seite).
3. WHILE Slides im Storyboard liegen THE SYSTEM SHALL Reihenfolge-
   Änderung und Entfernen erlauben und den Zustand über einen
   Page-Reload erhalten (sessionStorage).
4. WHEN der User Download klickt THE SYSTEM SHALL eine PPTX mit exakt
   den Storyboard-Slides in Storyboard-Reihenfolge liefern.
5. IF die Vorschau eines Kandidaten fehlt (404) THEN THE SYSTEM SHALL
   einen Platzhalter zeigen statt die Karte zu verwerfen.

## 9. Abgrenzung (Nicht-Teil)

- Kein Drag&Drop-Framework (↑/↓-Buttons reichen, kein neues JS-Dep)
- Kein Server-State fürs Storyboard (Session-Level = Default-Entscheid)
- Kein Editieren von Slide-Inhalten (D5)

## 9a. Boundaries (3-Tier)

- ✅ **Always:** `web/designer.html` + `web/assets/designer.js` neu;
  GENAU EIN additiver Nav-Link in bestehenden Seiten (1-Zeilen-Regel);
  FE-Smoke-Tests nach EPIC-002-Muster (Marker-basiert)
- ⚠️ **Ask-first (headless → BLOCKED):** neue JS-Dependencies/CDN-Libs;
  Änderungen an bestehenden Seiten jenseits des Nav-Links;
  style.css-Umbauten (nur additive Klassen)
- 🚫 **Never:** bestehende Slidesuche-/Generator-Seiten umbauen;
  master pushen; Inline-Secrets

## 10. Abgrenzung zum Ist

- Heute: Slidesuche (Suche→Top-5→Download-Liste) und Generator
  (Angebot→fertiges Deck) sind GETRENNTE Seiten ohne Storyboard →
  NEU: eine Designer-Seite kombiniert beide Quellen mit kuratierbarem
  Storyboard.

## 11. Implementierungs-Anker (Ist)

`web/` Design-2-Muster: Sidebar/Styles in `web/assets/style.css`,
Seiten-Gerüst z.B. `web/bibliothek.html` (Liste+Detail),
Slidesuche-FE als Vorbild für Karten/Preview-Handling (Seite mit
`/api/slidesuche/search`-Aufruf — `grep -l slidesuche web/*.html`),
`web/chat.html` (fetch-Muster mit Cookie/401-Redirect),
Angebots-Liste: `GET /api/angebote` (Response-Shape in
`backend/routers/angebot.py`). FE-Smoke-Vorbild:
`backend/tests/test_sprint4.py`-Stil (Marker-Greps) +
`test_charakterisierung.py` (statische Auslieferung).

## 12. Bekannte Pitfalls

1. **Nav-Link-Konflikt:** mehrere Stories ändern web/*.html-Navs NICHT
   parallel — der Nav-Link gehört GENAU EINER Story (US-063).
2. **sessionStorage-Schema versionieren** (`kfDesigner.v1`) — sonst
   bricht ein späteres Format Alt-Sessions ohne klaren Fehler.
3. **PNG-Preview-URLs sind auth-geschützt** (gleiches Cookie) — `<img>`
   funktioniert im selben Origin; bei 401 auf Login redirecten wie
   bestehende Seiten.
4. **Download als Data-URL bei großen Decks:** bestehendes Muster
   übernehmen (slidesuche-Download), keine neuen Blob-Experimente.

## Vision-Alignment

**Adressierte These:** R-DECK-1, R-DECK-2 (Session-Default), R-DECK-3 ·
EPIC-006 D1/D2/D3/D6
**Kern-Loop-Schritt:** „zusammenklicken statt generieren-und-hoffen"
**Nächste Iteration:** D5 Text-Swap; gespeicherte Decks pro User (D2-Server-Level)

## Referenzen
- implements → REQUIREMENTS R-DECK-1, R-DECK-2, R-DECK-3, R-NF-1
- depends_on → [[KOCHFABRIK-FEATURE-011]] (Suggest-API)
- relates_to → [[EPIC-006]] D1–D3, D6

## Referenziert von
— USER-STORIES Sprint 13 (US-063, US-064, US-065, US-066, US-067)
