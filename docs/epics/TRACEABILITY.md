# Traceability- & Konsistenz-Audit — kochfabrik

> **Typ:** TRACE. Nachweis, dass die Zerlegung in WPs lückenlos ist
> (kein R-ID, kein Akzeptanzkriterium, keine Session-Absprache
> verloren) und konsistent. Lebendes Dokument. **Stand:** 2026-06-09.

## Methode

Quellen-Inventare: **30 R-IDs** (REQUIREMENTS.md v0.2, 2026-06-09),
**22 Epic-Akzeptanzkriterien** (EPIC-003…007), **Session-Absprachen**
(Ideation-/Epic-Dialog 2026-06-09). Regel: jedes Item ≥ 1 WP
zugeordnet; „später/offen" explizit markiert.

## 1. Requirement-Abdeckung (30/30)

| R-ID | WP | R-ID | WP |
|---|---|---|---|
| R-FONT-1 | T1 + T2 + T3 | R-REF-1 | M1 + M2 (Schnitt: Q5-ADR) |
| R-FONT-2 | T1 | R-REF-2 | Prozess: dieses Spec-Set + M7 |
| R-FONT-3 | T3 | R-REF-3 | Q5 + M7 |
| R-FONT-4 | T2 | R-REF-4 | M4 + M5 |
| R-FONT-5 | T4 (Inventar: Q3) | R-REF-5 | M7 |
| R-FONT-6 | Q5-ADR → ggf. Folge-Epic (offen markiert) | R-REF-6 | Querschnitt M1–M7 (Gate: Q4) |
| R-FONT-7 | T6 (Prüfung: Q2) | R-DECK-1 | D1 |
| R-QA-1 | Q1 + Q2 | R-DECK-2 | D2 (❓ Persistenz-Level beim Sprint-Schnitt) |
| R-QA-2 | Q3 | R-DECK-3 | D3 |
| R-QA-3 | Q1 + Q2 (Fixes: M5/M6) | R-DECK-4 | D4 (Ausbaustufe, offen markiert) |
| R-QA-4 | Q4 | R-DECK-5 | D5 (Ausbaustufe, offen markiert) |
| R-NF-1 | Querschnitt M3/M4, D1–D3 | R-NF-2 | M3 (Plan: Q5-ADR) |
| R-NF-3 | Querschnitt (Q3/T6/D3/V2 read-only) | R-FID-1 | V1 |
| R-FID-2 | V2 | R-FID-3 | V3 |
| R-FID-4 | V4 | R-FID-5 | V3 + V5 (❓ Schwellen nach Baseline) |

✅ **30/30 zugeordnet.** „Später/offen" markiert: R-FONT-6
(ADR-abhängig), R-DECK-4, R-DECK-5 (Ausbaustufen), R-FID-5
(Schwellen nach Baseline-Messung).

## 2. Architektur-Abdeckung (§)

Keine ARCH-Spec vorhanden — entsteht in M7 (Techstack an einem Ort).
Bis dahin: Ist-Architektur dokumentiert in README.md (Studio) +
REQUIREMENTS §2-Befund (Render-Pfad). **Offen markiert, Owner: M7.**

## 3. Epic-Akzeptanzkriterien-Abdeckung (22/22)

| Epic | Kriterien | WPs |
|---|---|---|
| [[EPIC-003]] (4) | Findings verifiziert · Report 200/200 + JSON · 3 ADRs abgenommen · Baseline-Doc | Q1–Q5 |
| [[EPIC-004]] (5) | Ein Repo ohne vendor.sh · Deploy grün · Tests grün/Verhalten gleich · Alembic sauber · Docs/Techstack 1 Ort | M1–M7 |
| [[EPIC-005]] (5) | Nur Open-Sans-Faces (pdffonts) · pt exakt ohne Faktor · Run-Roundtrip · Score-Delta über Harness · Previews re-rendert | T1–T4, T6 (+V5) |
| [[EPIC-006]] (4) | Suche+Klick+Reorder+Remove · reload-fest · Download exakt/verbatim · Suche regressionsfrei | D1–D3 |
| [[EPIC-007]] (5) | 1-Befehl-Messung mit Score · Korpus-Lauf reproduzierbar + Sample in Suite · Gate fängt eingebaute Regression · Report mit Diffs/Trend · Schwellen von Jan abgenommen | V1–V5 |

✅ **22/22 zugeordnet.**

## 4. Session-Absprachen-Abdeckung

| # | Absprache (2026-06-09) | Verankert in | WP |
|---|---|---|---|
| 1 | Scope = beide Repos (studio + pptxgenerator_v2) | REQUIREMENTS-Kopf | Q1+Q2, M1 |
| 2 | Open Sans kanonisch, Ausreißer normalisieren | R-FONT-1 | T1–T3 |
| 3 | PPTX-Embedding erst nach Render-Pfad-Analyse entscheiden | R-FONT-6 ❓ | Q5 |
| 4 | Verhalten strikt erhalten, Prod = Truth | R-REF-6 | Querschnitt M1–M7 |
| 5 | Monorepo vor Font-Arbeit (keine Doppelarbeit im Vendoring) | ROADMAP Phasen 1→2 | — (Reihenfolge) |
| 6 | D4/D5 als ❓-Ausbaustufe, nicht im MVP | EPIC-006 Scope | D4, D5 |
| 7 | 4 Epics statt einem (User-OK „ja passt") | ROADMAP | — (Struktur) |
| 8 | „super nah an den pdfs … alleine dieses testing ist nen epic" → eigenes Treue-Test-Epic, erst messen dann verbessern | R-FID-1…5, [[EPIC-007]], ROADMAP Phase 2 | V1–V5 |

## 5. Konsistenz-Findings

**Aufgelöst:**
- PROGRESS.md führte EPIC-001 als IN_PROGRESS, Epic-Doc sagt DONE →
  PROGRESS-Tabelle korrigiert (2026-06-09).

**Managed Inconsistency (bewusst):**
- EPIC-001/002 haben keine WP-Codes (vor Einführung des WP-Systems) —
  bleiben unverändert, Historie. Kein Code blockiert.
- `lib/text.js` Kopf-Kommentar („Größe 1:1 verifiziert") widerspricht
  `SIZE_K = 0.78` — wird nicht doc-gefixt, sondern durch T1 obsolet.

**Offene Entscheidungen (vor betroffenem WP zu klären):**
- **PPTX-Font-Embedding** — Q5-ADR, vor Schnitt von EPIC-005-Sprint 13.
- **Monorepo-Schnitt + Alt-Ordner** — Q5-ADR, vor M1.
- **pgbundle vs. Postgres** — Q5-ADR; Umbau wäre Folge-Epic, nicht M-Scope.
- **D2-Persistenz-Level + D4/D5-Scope** — beim Sprint-Schnitt EPIC-006.
- **Treue-Schwellen (R-FID-5)** — nach V3-Baseline, vor EPIC-005-Abnahme.

## 6. Abdeckungs-Summe

| Inventar | Anzahl | zugeordnet | offen markiert |
|---|---|---|---|
| R-IDs | 30 | 30 | 4 (R-FONT-6, R-DECK-4/5, R-FID-5) |
| §-Abschnitte (ARCH) | 0 | — | ARCH entsteht in M7 |
| Epic-Akzeptanzkriterien | 22 | 22 | 0 |
| Session-Absprachen | 8 | 8 | 0 |
| Epics | 7 (2 DONE) | 7 | — |

**Nichts verloren. Offene Entscheidungen sind als Q5-ADRs bzw.
Sprint-Schnitt-Punkte explizit verankert.**
