# TRACEABILITY — Sprint 13 (Präsentationsdesigner)

> **Typ:** TRACE. Epic-getrieben ([[EPIC-006]] D1–D3+D6) + Incident-
> Nacharbeit. Feature-Prompt Jan 2026-06-11. Stand: Planung 2026-06-11.

## 1. Feature-Prompt-Abdeckung (Checkliste F1–F3)

| # | Feature (wörtlich) | Story | Status |
|---|---|---|---|
| F1 | „man lädt ein angebot hoch" | US-061 (PDF/offer_id/JSON-Zweige) | ✅ |
| F2 | „bekommt vorschläge für slides" | US-062 (Top-N je Gang + Pflicht), US-064 (Karten-UI) | ✅ |
| F3 | „kombination aus suche und präsentationserstellung" | US-066 (Suche im Designer) + US-065/067 (Storyboard→PPTX) | ✅ |

## 2. R-ID-Abdeckung (Sprint-relevant)

| R-ID | Story/Verify | Anmerkung |
|---|---|---|
| R-DECK-1 | US-063/064/065/066 | Suche+Klick+Reorder+Remove |
| R-DECK-2 | US-065 | Session-Level (Scope-Entscheid: Default) |
| R-DECK-3 | US-067 | Download verbatim via slidesuche/download |
| R-DECK-4 | US-061/062 | als D6 konkretisiert (Vorschläge statt Deck-Laden) |
| R-DECK-5 | — | offen markiert (D5 Text-Edit, Ausbaustufe) |
| R-NF-1 | US-063–067 | bestehende Flows unverändert (EPIC-Kriterium 4) |
| R-NF-2 | US-068 | live_verify Deep-Check (Incident) |
| R-NF-3 | US-062 | read-only Korpus, bundle-Schicht |

## 3. EPIC-006-Akzeptanzkriterien → Stories

| # | Kriterium | Stories |
|---|---|---|
| 1 | Suche+Klick+Storyboard+Reorder+Remove | US-064, US-065, US-066 |
| 2 | Reload-fest | US-065 |
| 3 | Download exakt/verbatim | US-067 |
| 4 | Slidesuche regressionsfrei | US-067 (volle Suite + Sim-Gate) |

D6 (Scope-Erweiterung): US-061 + US-062. ⚠ Neues R-ID für D6 via
/epic nachtragen (REQUIREMENTS gehört Jan — hier nur annotiert).

## 4. Abdeckungs-Summe

| Inventar | Anzahl | zugeordnet | offen markiert |
|---|---|---|---|
| Feature-Prompt-Punkte | 3 | 3 | 0 |
| R-IDs (sprint-relevant) | 8 | 7 | 1 (R-DECK-5 → D5 später) |
| EPIC-006-Kriterien | 4 + D6 | 4 + D6 | 0 |
| Incident-Nacharbeit | 1 | 1 (US-068) | 0 |

**Verschoben (explizit):** EPIC-007 V1–V5 + EPIC-008 C1–C3 → Sprint 14
(Seed liegt: `docs/sprint-14/FEATURE-CI-DELIVERY.md`); EPIC-005 → S15,
EPIC-010 → S16 (Roadmap-Shift dokumentiert in EPIC-006).
