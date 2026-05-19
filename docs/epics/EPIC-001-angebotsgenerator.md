---
id: EPIC-001
title: "KOCHfabrik Angebotsgenerator — Chat → pixelgenaues Angebots-PDF"
status: IN_PROGRESS
created: 2026-05-19
project: pptxgenerator_v2
sprints: [2, 3]
---

# EPIC-001: KOCHfabrik Angebotsgenerator

## Beschreibung

Inverse Richtung zum Präsentationsgenerator: nicht PDF → Präsentation,
sondern **Chat → KOCHfabrik-Angebots-PDF**. Nutzer beschreibt im Dialog
ein Event (Anlass, Datum, Personenzahl, Ort, Cateringkonzept, Budget);
das System erzeugt ein vollständiges Angebots-PDF, das im Aufbau **1:1**
den echten alten KOCHfabrik-Angeboten entspricht.

Die Engine hat KOCHfabrik-PDFs bereits faithful zerlegt (`kf_classify`:
invariante Letterhead/Footer-Signatur 33/33, `Veranstaltungs-
informationen`-Label-Block, Positionsstruktur Speisen/Getränke/Personal/
Logistik, Bankblock). Dasselbe Know-how rückwärts: **ein echtes Muster-
Angebot pixelgenau extrahieren → parametrisierbares Template → aus chat-
erfassten Daten füllen → rendern.** Baut auf dem eingefrorenen
Präsentationsgenerator auf (Tag `freeze/praesentationsgenerator-
2026-05-19`), ohne ihn zu verändern.

## Scope

### Was drin ist
- Pixelgenaue Template-Extraktion aus echten Muster-Angeboten
  (Faithful-Extraktion der bestehenden Engine wiederverwenden)
- Striktes Angebots-Datenmodell (Felder, Positionen, Pauschalen, Preise)
- Renderer Datenmodell → PDF mit Pixel-Diff-Gate gegen echte Muster
- Fiktiv-Korpus-Generator: 20–30 realistische Original-Stil-PDFs
- Angebotsgenerator-Chat-Flow: Dialog → Datenmodell → PDF-Download

### Was NICHT drin ist
- Echte KOCHfabrik-Preisliste / Kalkulationslogik — erst plausible
  fiktive Preise (echte Preise = Folge-Scope, braucht KOCHfabrik-Input)
- CRM/ERP-Anbindung, rechtsverbindliche Angebote
- Integration in die KOCHfabrik-Studio-Webapp (eigene Phase)
- Änderungen am Präsentationsgenerator (Freeze bleibt unangetastet)

## Sprint-Zuordnung

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 2 | Template-Extraktion aus Muster-Angeboten + Angebots-Datenmodell | L |
| Sprint 3 | Renderer Datenmodell→PDF + Pixel-Diff-Gate gegen echte Muster | L |
| Sprint 4 | Fiktiv-Korpus-Generator → 20–30 Original-Stil-PDFs | M |
| Sprint 5 | Angebotsgenerator-Chat-Flow (Dialog → Datenmodell → PDF) | M |

> Sprint-Zuordnung ist eine grobe Planung. Details bestimmt `/sprint-plan`.

## Akzeptanzkriterien

1. Renderer erzeugt aus dem Datenmodell ein PDF, das im Aufbau 1:1
   einem echten KOCHfabrik-Angebot entspricht: Pixel-Diff < Toleranz
   gegen ≥3 echte Muster; `kf_classify` → `angebot`; alle Label-Felder
   + Positionsblöcke (Speisen/Getränke/Personal/Logistik) + Bankblock.
2. 20–30 fiktive Original-Stil-PDFs erzeugt, jedes von `kf_classify`
   als KOCHfabrik + `angebot` klassifiziert, strukturell
   ununterscheidbar vom Original.
3. Chat-Flow: freie Event-Beschreibung → vollständiges Angebots-PDF
   zum Download, ohne manuelle Nacharbeit.
4. Tag `freeze/praesentationsgenerator-2026-05-19` bleibt unverändert
   grün (Präsentationsgenerator unangetastet).

## Fortschritt

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 2 | Template-Extraktion + Datenmodell | ✅ DONE (6/6, 2026-05-19) |
| Sprint 3 | Renderer + Pixel-Diff-Gate | 🔨 IN_PROGRESS (geplant 2026-05-19) |
| Sprint 4 | Fiktiv-Korpus-Generator (20–30 PDFs) | ⏳ TODO |
| Sprint 5 | Angebotsgenerator-Chat-Flow | ⏳ TODO |
