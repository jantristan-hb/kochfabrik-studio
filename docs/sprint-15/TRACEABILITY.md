# TRACEABILITY — Sprint 15 (CI/Delivery + Treue-Harness + Batches)

> **Typ:** TRACE. Epic-getrieben: [[EPIC-008]] C1–C3 + [[EPIC-007]]
> V1–V4 + Carry-Over S14. Stand: Planung 2026-06-12.

## 1. WP-Abdeckung

| WP | Story | Status |
|---|---|---|
| C1 (Pipeline) | US-079 | geplant |
| C2 (Treue-Gate als Pflicht-Check) | US-084 | geplant |
| C3 (Branch-Protection + Delivery-Doku) | US-080 | geplant |
| V1 (Metrik) | US-081 | geplant |
| V2 (Korpus-Lauf reproduzierbar) | US-082 | geplant |
| V3 (Baseline + Gate) | US-083 + US-084 | geplant |
| V4 (Report mit Diffs) | US-083 | geplant |
| V5 (Schwellen-Abnahme durch Jan) | — | **offen markiert** (Entscheidung; Vorlage liefert US-083) |

## 2. R-ID-Abdeckung (sprint-relevant)

| R-ID | Story |
|---|---|
| R-CI-1 | US-079 |
| R-CI-2 | US-080 |
| R-CI-3 | US-084 |
| R-FID-1 | US-081 |
| R-FID-2 | US-082 |
| R-FID-3 | US-083 + US-084 |
| R-FID-4 | US-081 |
| R-FID-5 | US-083 (❓ Vorlage, Abnahme offen) |
| R-QA-4 | US-083 (Baseline-Karte) |
| R-DECK-4 / R-NF-3 | US-078 (Batches-Vollzug) |

## 3. Carry-Over-Abdeckung (aus PROGRESS S14)

| Item | Story | Status |
|---|---|---|
| Voll-Korpus-Batches + Volume-Sync | US-078 (Lead) | ✅ eingeplant |
| EPIC-008 + EPIC-007 (CI + Treue) | US-079–084 | ✅ eingeplant |
| Vertrag-Rest: Dialog-Nachbearbeitung · DNA-Doku · Font-Treue (EPIC-005) | — | **offen markiert** → S16 (Font-Treue misst dann gegen die neue Baseline) |
| Alt-Ordner-Archivierung (Jan-Entscheid) | — | offen (seit S12) |

## 4. Epic-Akzeptanzkriterien

| Epic | Kriterium | Story |
|---|---|---|
| EPIC-008 | Roter Check blockiert Merge | US-080 |
| EPIC-008 | Treue-Gate fängt Regression im PR | US-084 |
| EPIC-008 | Delivery-Flow dokumentiert | US-080 |
| EPIC-007 | 1-Befehl-Messung mit Score | US-081/082 |
| EPIC-007 | Korpus-Lauf reproduzierbar + Sample in Suite | US-082/084 |
| EPIC-007 | Gate fängt eingebaute Regression | US-084 |
| EPIC-007 | Report mit Diffs/Trend | US-083 |
| EPIC-007 | Schwellen von Jan abgenommen | — offen markiert (V5) |

## 5. Abdeckungs-Summe

| Inventar | Anzahl | zugeordnet | offen markiert |
|---|---|---|---|
| WPs (C1–C3, V1–V5) | 8 | 7 | 1 (V5 = Jan-Entscheid) |
| R-IDs | 10 | 10 | R-FID-5-Abnahme |
| Carry-Over-Items | 4 | 2 | 2 (Vertrag-Rest → S16, Alt-Ordner) |
| Epic-Kriterien | 8 | 7 | 1 (V5) |

## Erfüllungs-Stand (Review 2026-06-15)

7/7 DONE (PRs #91–#94, Wizard-Bugfix #96). EPIC-008 (C1–C3) + EPIC-007
(V1–V4) erfüllt; V5 (Schwellen-Abnahme) offen = Jan. CI live + Branch-
Protection (ci+fidelity) auf master, Treue-Baseline eingefroren,
Voll-Korpus-Batches deployt. Beifang-Fixes: fastapi-Pin (CI-Drift),
Wizard-Editor (#95). master deployt + LIVE_DEEP grün.
