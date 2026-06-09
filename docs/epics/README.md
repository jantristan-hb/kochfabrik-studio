# Epics & Implementierungs-Roadmap — kochfabrik

> **Typ:** ROADMAP. Zerlegung des Gesamtvorhabens (REQUIREMENTS.md
> 2026-06-09) in Arbeitspakete (WP), gruppiert in Epics, mit fester
> Implementierungs-Reihenfolge. Lückenlosigkeit: siehe
> [[TRACEABILITY]]. **Stand:** 2026-06-09.
>
> **WP** = vernünftiges kleines Paket (≈ 1 bis wenige Stories).
> `/sprint-plan` schneidet WPs in Stories.

## Epics

| Epic | Titel | WPs | Status | Liefert |
|---|---|---|---|---|
| [[EPIC-001]] | Persistenz, Multi-Tenant & CRM | — (vor WP-System) | DONE | PostgreSQL-Persistenz, Nummernkreise, Tenant-Isolation |
| [[EPIC-002]] | WYSIWYG-Präsentationsgenerator v2 | — (vor WP-System) | DONE (rollback Sprint 9) | Erkenntnisse; Code wieder ausgebaut |
| [[EPIC-003]] | Analyse-Fundament & Entscheidungen | Q1–Q5 | OPEN | Bug-Findings beider Repos, Font-Report (200 PDFs), 3 ADRs, Test-Baseline |
| [[EPIC-004]] | Monorepo & Refactoring | M1–M7 | OPEN | Ein Repo ohne Vendoring, entzerrte Struktur, sauberes Alembic, Docs auf Stand |
| [[EPIC-005]] | Font-Treue | T1–T4, T6 | OPEN | Exakte Open-Sans-Fonts + pt-Größen, Previews re-rendert |
| [[EPIC-006]] | Live-Deck-Builder | D1–D5 | OPEN | Deck per Suche + Klick bauen, PPTX-Download |
| [[EPIC-007]] | Render-Treue-Harness | V1–V5 | OPEN | Treue-Metrik + Korpus-Harness + Baseline-Gate + Diff-Report — „super nah am PDF" messbar |

## Arbeitspakete (Master-Liste)

**EPIC-003 Analyse-Fundament & Entscheidungen**
- **Q1** Bug-Analyse kochfabrik-studio (backend/web/Dockerfile/Deploy) — verifizierte, priorisierte Findings
- **Q2** Bug-Analyse pptxgenerator_v2-Engine (scripts/, spike-pptxgenjs/)
- **Q3** Font-/Größen-Report über 200 Referenz-PDFs (Report + JSON)
- **Q4** Test-Baseline-Inventur (111 Tests: was abgesichert, wo Lücken)
- **Q5** ADRs: PPTX-Embedding, Monorepo-Schnitt + Alt-Ordner, pgbundle vs. Postgres

**EPIC-004 Monorepo & Refactoring**
- **M1** Monorepo-Merge (Historie erhalten) + Alt-Verzeichnisse gemäß ADR
- **M2** Vendoring abbauen (vendor.sh + Engine-Kopie weg)
- **M3** Coolify-Deploy auf Monorepo migrieren + Live-Verify
- **M4** backend/app.py in Module entzerren (Verhalten identisch)
- **M5** Engine-Skripte ordnen (Runtime vs. Tooling), Dead Code raus
- **M6** Alembic-Drift fixen (alembic.ini im Container, Tracking sauber)
- **M7** Docs: README/CLAUDE.md/ARCH — Techstack an einem Ort

**EPIC-005 Font-Treue**
- **T1** Exakte pt-Größen-Extraktion, SIZE_K/LINE_K/Y_OFF_K-Heuristiken weg
- **T2** Run-genaue Weight/Style-Treue + vollständiges Face-Mapping
- **T3** Open Sans ins Docker-Image + Substitutions-Verify
- **T4** Wingdings-/Bullet-Glyphen-Mapping
- **T6** Preview-PNGs im Volume re-rendern
  *(T5 entfallen — aufgegangen in EPIC-007)*

**EPIC-007 Render-Treue-Harness**
- **V1** Treue-Metrik: Pixel/SSIM + Text + Geometrie + Font → Score je Slide/Deck
- **V2** Korpus-Harness: reproduzierbarer Lauf (Sample-Set + Voll-Lauf 200 Decks), Prod-identisches Rendering
- **V3** Baseline einfrieren + Regressions-Gate in der Test-Suite
- **V4** Treue-Report: Worst-Slides, Side-by-Side-Diffs, Trend
- **V5** Abnahme-Integration: EPIC-005 wird über den Harness abgenommen

**EPIC-006 Live-Deck-Builder**
- **D1** Builder-UI (Suche + Storyboard, Klick/Reorder/Remove)
- **D2** Arbeits-Deck-Persistenz (reload-fest)
- **D3** PPTX-Download via /api/slidesuche/download
- **D4** Ausbaustufe ❓: Generator-Deck als Startpunkt laden
- **D5** Ausbaustufe ❓: Text-Swap auf übernommenen Slides

## Implementierungs-Reihenfolge (Dependency-getrieben)

| Phase | WPs | Warum hier | Meilenstein |
|---|---|---|---|
| **0 — Analyse & Decisions** | Q1–Q5 | Doc-only, billig, entsperrt alles | Findings + Font-Report + 3 ADRs abgenommen |
| **1 — Foundation** | M1–M3, dann M4–M7 | Monorepo zuerst — sonst Doppelarbeit im Vendoring | Coolify-Deploy aus Monorepo grün, Tests grün |
| **2 — Messen** | V1–V3 | Erst messen, dann verbessern — Baseline vor Font-Arbeit | Treue-Baseline eingefroren, Gate in Suite |
| **3 — Font-Kern** | T1–T4 | Engine-Arbeit auf neuer Struktur, Score-Delta sichtbar | Rekonstruktion exakt (pdffonts + pt-Abgleich), Score ↑ |
| **4 — Gate + Feature** | V4–V5, T6, D1–D3 | Report + Abnahme; Builder-MVP als vertikale Scheibe | EPIC-005 über Harness abgenommen; Deck klick-bar + Download |
| **später** | D4–D5 | Scope-Entscheid (❓) ausstehend | — |

**Vertikale-Scheibe-Prinzip:** Phase 4 liefert den Deck-Builder
end-to-end (Suche → Storyboard → Download) auf bereits font-treuen
Previews; D4/D5 erweitern dieselbe Surface später.

**MVP-Kern:** Phasen 0–4. D4/D5 und ggf. PPTX-Embedding sind Ausbau.

## Referenzen
- parent_of → [[EPIC-003]], [[EPIC-004]], [[EPIC-005]], [[EPIC-006]],
  [[EPIC-007]] (Historie: [[EPIC-001]], [[EPIC-002]])
- relates_to → REQUIREMENTS.md (R-IDs, 2026-06-09)
- depends_on → [[TRACEABILITY]] — Abdeckungs-Nachweis WP ↔ Quelle
