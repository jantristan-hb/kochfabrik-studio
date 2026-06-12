---
key: KOCHFABRIK-FEATURE-015
status: approved
title: "Präsentations-Wizard: Schritt pro Slide, Alternativen, Overlay-Editing"
created: 2026-06-12
project: kochfabrik
---

# KOCHFABRIK-FEATURE-015: Wizard-UI

> **Typ:** FEATURE (Brownfield-Delta, Frontend). Sprint 14. Der geführte
> Default-Einstieg — Jan: „Texte und Slides zusammenpacken, jede zu
> erstellende Slide ein eigener Schritt mit 3-4 Alternativen."
> Designer bleibt unverändert als Experten-Tool bestehen.

## 1. Vision

Eine Wizard-Seite führt vom Angebot zum fertigen Deck: ein Schritt pro
Slide, oben 3–4 Alternativen (Top-Kandidat vorausgewählt), darunter die
gewählte Slide GROSS mit direkt editierbaren Text-Overlays über dem
textfreien Render. Wer nur „Weiter" drückt, hat in einer Minute das
Generator-Deck; jeder Schritt erlaubt Eingriff ohne Zwang.

## 4. Flows

```
Schritt 0  Angebot: Upload-PDF / gespeichertes Angebot (suggest-API)
Schritt i  (1..N, eine Slide je suggest-Gruppe in Server-Reihenfolge):
           ┌─────────────────────────────────────────────────┐
           │ Slide 3 von 9 — Vorspeise        [← Zurück][Weiter →]
           │ [Alt A*] [Alt B] [Alt C] [+1 weitere]   (*=gewählt)
           │ ┌─────────────────────────────────────────────┐
           │ │   GROSSE Vorschau: preview_notext-PNG        │
           │ │   + positionierte Text-Overlays              │
           │ │   (contenteditable, vorbefüllt mit Auto-     │
           │ │    Overrides; ✦ Formulieren je Feld)         │
           │ │   + Bild-Overlays: [🖼 Bild generieren]       │
           │ └─────────────────────────────────────────────┘
           Cover-Schritt zusätzlich: [✨ Cover-Bild generieren]
           → Ergebnis ersetzt das größte Bild-Element (image_override)
Schritt N+1 Filmstreifen aller gewählten Slides (Overlay-Thumbs) →
           [PPTX herunterladen] (slides + overrides + image_overrides)
State: sessionStorage kfWizard.v1 (Schritt, Auswahl, Overrides) —
       reload-fest; „Von vorn"-Reset.
Fallbacks: preview_notext 404 → normales preview-PNG + Hinweis-Badge;
       Formulieren/Bild-Generieren-Fehler → Feld unverändert + Meldung.
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN ein Angebot gewählt/hochgeladen ist THE SYSTEM SHALL je
   suggest-Gruppe einen Wizard-Schritt in Server-Reihenfolge anzeigen
   (Fortschritt „Slide i von N"), mit 3–4 Alternativen und dem
   Top-Kandidaten vorausgewählt.
2. WHEN ein Schritt angezeigt wird THE SYSTEM SHALL die gewählte Slide
   groß rendern: textfreies PNG + Text-Overlays an Element-Geometrie
   (meta-skaliert), vorbefüllt mit Auto-Overrides; Editieren SHALL die
   Overrides im Wizard-State aktualisieren.
3. WHEN der User „✦ Formulieren" klickt THE SYSTEM SHALL den Feldtext
   durch die formulate-API ersetzen (mit Undo auf den vorherigen Wert).
4. WHEN der User im Cover-Schritt „✨ generieren" bzw. an einem
   Bild-Element „🖼 Bild generieren" klickt THE SYSTEM SHALL das
   erzeugte Bild als positioniertes Overlay zeigen und als
   image_override in den State übernehmen.
5. WHEN der Abschluss-Schritt bestätigt wird THE SYSTEM SHALL eine
   PPTX mit den gewählten Slides in Schritt-Reihenfolge inkl. aller
   Text- und Bild-Overrides liefern.
6. WHILE der Wizard läuft THE SYSTEM SHALL den Zustand reload-fest
   halten (sessionStorage) und Zurück-Navigation ohne Datenverlust
   erlauben.

## 9. Abgrenzung (Nicht-Teil)

- Kein Drag/Resize von Elementen (Position bleibt Korpus-Layout)
- Keine Schriftart-Pixelparität im Overlay (best-effort CSS; die
  WAHRHEIT rendert reconstruct beim Download)
- Designer-Seite unangetastet (eigene Seite wizard.html)
- Kein Server-State (Session-Level wie Designer)

## 9a. Boundaries (3-Tier)

- ✅ **Always:** `web/wizard.html` + `web/assets/wizard.js` NEU; GENAU
  EINE additive Nav-Zeile je Bestands-Seite („Wizard", vor „Designer");
  FE-Smoke-Tests in eigener Datei `backend/tests/test_sprint14_fe.py`
- ⚠️ **Ask-first (headless → BLOCKED):** neue JS-Deps/CDN; Änderungen
  an designer.js/bestehenden Seiten jenseits der Nav-Zeile
- 🚫 **Never:** echte Gemini-/Anthropic-Calls in Tests; master pushen;
  bestehende Flows umbauen

## 10. Abgrenzung zum Ist

- Designer = 3-Spalten-Experten-Tool (alles gleichzeitig) → Wizard =
  linearer Flow, eine Entscheidung pro Screen, Default vorausgewählt
- Texte-Editor (#66) = Liste neben Thumbnail → Overlay AUF der Slide

## 11. Implementierungs-Anker (Ist)

`web/designer.html`/`web/assets/designer.js` (Muster: API-Wrapper mit
401-Redirect, card(), sessionStorage-State `kfDesigner.v1`,
suggest/texts/download/image-Wiring — NICHT ändern, nur als Vorlage),
`backend/routers/designer.py` (suggest-Gruppen in Deck-Reihenfolge,
texts-API), `/api/image` (Cover/Food-Generierung),
FE-Smoke-Muster `backend/tests/test_sprint13_fe.py`,
`web/assets/style.css` + Design-2-Sidebar (bibliothek.html).

## 12. Bekannte Pitfalls

1. **Overlay-Maßstab:** Geometrie ist in Folien-Einheiten relativ zu
   meta.w_pt/h_pt — Skalierung = Container-Breite/w_pt; bei
   Resize/Zoom neu rechnen (ResizeObserver), sonst wandern Overlays.
2. **contenteditable-Eigenheiten:** plain-text erzwingen
   (paste-Handler strippt Formatierung), Enter = Zeilenumbruch im
   Override ("\n"), kein HTML in den State.
3. **sessionStorage-Größe:** image_overrides (Data-URLs, MB!) NICHT in
   sessionStorage — in-memory halten + Hinweis „generierte Bilder gehen
   bei Reload verloren" (gleiches Muster wie Cover-Generator #65).
4. **Ein Schritt = eine suggest-Gruppe:** Reihenfolge kommt vom Server
   (#64) — FE erfindet KEINE eigene Sortierung.
5. **Nav-Zeile:** gehört GENAU der Gerüst-Story (US-074), Folge-Stories
   fassen Bestands-Seiten nicht an.

## Vision-Alignment

**Adressierte These:** R-DECK-1/2/3/5, R-NF-1 · Vertrag 2026-001 §3.2
(markengerechte Formatierung + Textformulierung, Chatbot-Vorstufe)
**Kern-Loop-Schritt:** „Angebot → Deck" wird für Nicht-Experten gangbar
**Nächste Iteration:** Dialog-Nachbearbeitung über denselben Override-Kanal

## Referenzen
- implements → REQUIREMENTS R-DECK-1, R-DECK-2, R-DECK-3, R-DECK-5, R-NF-1
- depends_on → [[KOCHFABRIK-FEATURE-013]] · [[KOCHFABRIK-FEATURE-014]]
- relates_to → [[EPIC-006]] (Designer bleibt; Wizard = geführte Schicht darüber)

## Referenziert von
— USER-STORIES Sprint 14 (US-074, US-075, US-076, US-077)
