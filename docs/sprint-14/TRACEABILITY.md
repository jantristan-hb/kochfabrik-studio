# TRACEABILITY — Sprint 14 (Präsentations-Wizard)

> **Typ:** TRACE. Feature-getrieben (Jan 2026-06-12) mit Vertragsbezug
> (signiertes Angebot 2026-001 §3.2). Stand: Planung 2026-06-12.

## 1. Feature-Prompt-Abdeckung (F1–F8)

| # | Feature | Story | Status |
|---|---|---|---|
| F1 | Wizard-Flow: Schritt 0 Angebot, ein Schritt pro Slide | US-074 | ✅ |
| F2 | 3–4 Alternativen, Top vorausgewählt, Cover-Generieren | US-075 | ✅ |
| F3 | Overlay-Editing über textfreiem Render, vorbefüllt | US-070 (API) + US-076 (FE) | ✅ |
| F4 | Navigation/Fortschritt/Session + Filmstreifen/Download | US-074 + US-077 | ✅ |
| F5 | Tooling-Batch textfreie Renders | US-069 | ✅ |
| F6 | Bildbewusstes Ranking (Score-Mix) | US-073 + US-072 (Wiring) | ✅ |
| F7 | Bild-Overrides + „Bild generieren je Gericht" + Cover→PPTX | US-071 (Download) + US-075/076 (FE) | ✅ |
| F8 | Formulieren-Button (KOCHfabrik-Ton) | US-072 (API) + US-076 (FE) | ✅ |

## 2. R-ID-Abdeckung (sprint-relevant)

| R-ID | Story | Anmerkung |
|---|---|---|
| R-DECK-1 | US-074/075 | geführte Auswahl |
| R-DECK-2 | US-074 | kfWizard.v1 session-persistent |
| R-DECK-3 | US-071/077 | Download inkl. Bild-Overrides |
| R-DECK-4 | US-069/073/072 | Vorschlagsqualität (bildbewusst) |
| R-DECK-5 | US-070/076 | Text-Edit als Overlay (Vollausbau von #66) |
| R-NF-1 | alle FE | Designer/Bestand unangetastet |
| R-NF-3 | US-069/071/073 | Cache read-only (Symlink-Pitfall, Gold-Test) |

## 3. Vertrags-Abdeckung (2026-001 §3.2 — offene Punkte aus Gap-Analyse 2026-06-12)

| Vertragspunkt | Story | Status nach Sprint |
|---|---|---|
| Formatierung/Zuschnitt von Bildern in Folien | US-071/076 | ✅ geschlossen |
| Markengerechte KI-Textformulierung | US-072/076 | ✅ geschlossen |
| KI-Bildsuche nach Kontext UND Inhalt | US-073 | ✅ geschlossen |
| Nachbearbeitung im Dialog (Chatbot) | — | offen markiert (Folge-Iteration: Chat-Layer über denselben Override-Kanal) |
| DNA-Doku als Artefakt | — | offen markiert (separater Doc-Task, kein Code) |
| Font-Treue (Open Sans im Image) | — | offen markiert → EPIC-005, Sprint 15/16 |

## 4. Abdeckungs-Summe

| Inventar | Anzahl | zugeordnet | offen markiert |
|---|---|---|---|
| Feature-Prompt-Punkte | 8 | 8 | 0 |
| R-IDs (sprint-relevant) | 7 | 7 | 0 |
| Vertragspunkte §3.2 (offen) | 6 | 3 | 3 (Dialog, DNA-Doku, Fonts) |

**Verschoben (explizit):** EPIC-008 C1–C3 + EPIC-007 V1–V5 → Sprint 15
(Seed: docs/sprint-15/FEATURE-CI-DELIVERY.md), EPIC-005 → S16,
EPIC-010 → S17. Voll-Korpus-Batches (notext + imgbundle) = manuelle
Runbook-Schritte NACH dem Sprint (Volume-Sync Ask-first).

## Erfüllungs-Stand (Review 2026-06-12)

9/9 DONE (PRs #77–#81, 4 Stränge, 0 Konflikte). Alle EARS-Kriterien
grün (FEATURE-013 Nr. 1–4, 014 Nr. 1–4, 015 Nr. 1–6); F1–F8
vollständig. Beweise: E2E real (Override-Text im Slide-XML + Bild in
ppt/media), Live-Smoke Gesamtflow mit Risk-Ident-PDF (9 Schritte),
Formulieren-Ton-Probe, Bild-Ranking-Stichprobe, Sim-Gate grün,
Gold-Test unangetastet. Vertragspunkte „Bild in Folie" +
„markengerechte Texte" + „Bildsuche nach Inhalt" geschlossen.
**OFFEN (Betriebs-Schritt):** Voll-Korpus-Batches (render_notext +
embed_images) + Volume-Sync — Runbooks liegen, braucht Jan-Go.
