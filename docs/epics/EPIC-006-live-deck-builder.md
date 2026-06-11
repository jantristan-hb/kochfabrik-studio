---
id: EPIC-006
title: "Live-Deck-Builder: Präsentationen aus PNG-Slides zusammenklicken"
status: IN_PROGRESS
created: 2026-06-09
project: kochfabrik-studio
sprints: [13]
---

# EPIC-006: Live-Deck-Builder

> **Typ:** EPIC. Klammer über Sprints — kein Detail-Spec. `/sprint-plan`
> schneidet die WPs in Stories. Status: `OPEN → IN_PROGRESS → DONE`.

## Beschreibung

Neue Produktrichtung aus der Ideation 2026-06-09: weg vom reinen
„Angebot rein → Deck raus"-Generator hin zu einem interaktiven
Builder — der User sucht Referenz-Slides (Vektor-Suche mit
PNG-Vorschauen), klickt sie in ein Arbeits-Deck, ordnet sie und lädt
das Ergebnis als PPTX herunter.

Das Fundament existiert bereits vollständig im Backend:
`/api/slidesuche/search` (Top-5 mit Preview), `/api/slidesuche/
preview/{deck}/{page}.png` und `/api/slidesuche/download`
(PPTX-Bundle aus einer `{deck,page}`-Liste). Es fehlt die Builder-UI
und die Persistenz des Arbeits-Decks. Slides kommen verbatim aus dem
Referenz-Cache — Font-Treue (EPIC-005) gilt damit automatisch.

## Scope

### Was drin ist

- **D1** Builder-UI: Suchfeld + Ergebnis-Karten (PNG) + Storyboard-
  Tray; Klick = Slide übernehmen, Drag/Buttons = Reorder, Entfernen
- **D2** Arbeits-Deck-Persistenz: übersteht Page-Reload (mindestens
  Session-Ebene; Server-Persistenz pro User gemäß Scope-Entscheid
  beim Sprint-Schnitt)
- **D3** PPTX-Download über den bestehenden Bundle-Endpoint
  `/api/slidesuche/download` aus dem Storyboard heraus
- **D4** *(Ausbaustufe ❓)* Generiertes Deck (assemble.py-Ergebnis)
  als Startpunkt ins Arbeits-Deck laden und ergänzen
- **D5** *(Ausbaustufe ❓)* Text-Anpassung auf übernommenen Slides
  (z.B. Kundenname tauschen)
- **D6** *(Scope-Erweiterung 2026-06-11, Jan: „Präsentationsdesigner —
  man lädt ein Angebot hoch und bekommt Vorschläge für Slides, eine
  Kombination aus Suche und Präsentationserstellung")*: Angebots-Upload
  (PDF/gespeichertes Angebot) → pro Gang/Kategorie Top-N Slide-Vorschläge
  aus der Generator-Pipeline (Parsing + Embedding + bundle-Ranking) +
  Pflicht-Frame-Gruppe — als Vorschlagsquelle im Builder neben der
  Freitext-Suche. Konkretisiert/ersetzt D4 für die erste Ausbaustufe.
  ❗ R-ID-Nachtrag (R-DECK-6) gehört /epic — hier annotiert, nicht
  in REQUIREMENTS geschrieben (Regel: sprint-plan ändert REQUIREMENTS nie).

### Was NICHT drin ist

- Neue Slide-Generierung im Builder (macht der Generator-Pfad)
- Korpus-Pflege/Upload neuer Referenz-Decks — separater Prozess
- Multi-User-Kollaboration am selben Deck

## Sprint-Zuordnung (grob)

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 13 | D1–D3 + D6 (Präsentationsdesigner komplett) | L |
| später | D5 (Text-Edit) nach Scope-Entscheid | M |

> Vorgezogen von S15 → S13 (Jan-Priorisierung 2026-06-11);
> EPIC-007/008 verschieben sich auf S14.

> **Fortschritt:** wird von /sprint-review aktualisiert.

## Akzeptanzkriterien

1. User kann per Suche Slides finden, per Klick in ein Storyboard
   übernehmen, Reihenfolge ändern und Slides entfernen.
2. Das Arbeits-Deck übersteht einen Page-Reload.
3. Download liefert eine PPTX mit exakt den gewählten Slides in der
   gewählten Reihenfolge (verbatim aus dem Referenz-Cache).
4. Bestehende Slidesuche-Funktion bleibt unverändert nutzbar
   (kein Regressions-Bruch der Such-Seite).

## Referenzen

- **REQUIREMENTS:** R-DECK-1, R-DECK-2 (❓ Persistenz-Level),
  R-DECK-3, R-DECK-4 (❓ Ausbaustufe), R-DECK-5 (❓ Ausbaustufe),
  R-NF-1, R-NF-3
- **Audit:** [[TRACEABILITY]] → WP D1–D5

## Abhängigkeiten

Blockiert von: EPIC-004 (Monorepo-Struktur für FE/BE-Arbeit),
EPIC-005/T6 nur weich (bessere Previews, kein harter Blocker).
Blockiert: nichts.
