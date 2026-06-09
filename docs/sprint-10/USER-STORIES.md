# USER-STORIES — kochfabrik Sprint 10

> **Typ:** US. Geschnitten aus [[EPIC-003]] (WPs Q1–Q5). Doc-only-Sprint:
> Analyse, Report, ADRs — KEIN Produktiv-Code. Format: Context · Input ·
> Task · Output · Verify · Blocked-by.

## Story-Gate (PFLICHT)

- [x] ≤ 5 Task-Schritte · ≤ 3 Output-Dateien · Verify deterministisch
- [x] Verify bildet ein EARS-Kriterium der FEATURE-Spec ab
- [x] Null Platzhalter · Blocked-by explizit · Trace vorhanden

## Boundaries (sprintweit — /sprint-execute injiziert das in jeden Teammate)

- ✅ **Always:** beide Repos read-only lesen (`kochfabrik-studio`,
  `../pptxgenerator_v2`); Dateien NUR unter `docs/sprint-10/`,
  `docs/adr/`, `tools/` anlegen; pytest read-only ausführen;
  Analyse-venv `tools/.venv` mit `pymupdf` anlegen
- ⚠️ **Ask-first:** jede Änderung außerhalb `docs/` + `tools/`; neue
  Dependency in `requirements.txt`; Schreibzugriffe im Engine-Repo
- 🚫 **Never:** `data/cache/` schreiben/löschen (R-NF-3); Bugs
  „nebenbei" fixen (R-REF-6 — Analyse-Sprint!); auf master pushen;
  Secrets committen; ADR-`status: accepted` selbst setzen

---

## Phase 1: Analyse (parallel)

### US-036: Bug-Analyse kochfabrik-studio dokumentieren

**Context:** Es gibt keine systematische Bug-Inventur; EPIC-004/010
sollen Findings abarbeiten statt suchen (Q1).

**Input (Vorbedingungen):**
- Repo kochfabrik-studio @ master (read-only)
- Finding-Schema aus [[KOCHFABRIK-FEATURE-001]] §3

**Task:**
1. `backend/` vollständig lesen (app.py, slidesuche.py, store.py, oauth.py, migrate.py, db.py, numbering.py) — Verdachte notieren
2. `web/` (inkl. `_legacy/`), `Dockerfile`, `vendor.sh`, Deploy-Pfad prüfen
3. Jeden Verdacht verifizieren: Beleg (Datei:Zeile/Repro) oder `VERWORFEN: {Grund}`
4. Findings priorisieren (CRITICAL/HIGH/MEDIUM/LOW) + Epic/WP zuordnen
5. `FINDINGS-STUDIO.md` im Schema schreiben

**Output (erzeugte/geänderte Dateien):**
- `docs/sprint-10/FINDINGS-STUDIO.md` — priorisierte, belegte Findings

**Verify:** (EARS 1 aus FEATURE-001)
```bash
cd "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio" && \
test -s docs/sprint-10/FINDINGS-STUDIO.md && \
test "$(grep -cE '^## F-S-[0-9]{2}: ' docs/sprint-10/FINDINGS-STUDIO.md)" -ge 5 && \
test "$(grep -cE '^## F-S-[0-9]{2}: ' docs/sprint-10/FINDINGS-STUDIO.md)" -eq "$(grep -c '^\*\*Beleg:\*\*' docs/sprint-10/FINDINGS-STUDIO.md)" && \
test "$(grep -cE '^## F-S-[0-9]{2}: ' docs/sprint-10/FINDINGS-STUDIO.md)" -eq "$(grep -c '^\*\*Zuordnung:\*\*' docs/sprint-10/FINDINGS-STUDIO.md)"
```

**Trace:** R-QA-1, R-QA-3 · WP Q1 · [[KOCHFABRIK-FEATURE-001]]
**Blocked-by:** —

---

### US-037: Bug-Analyse pptxgenerator_v2-Engine dokumentieren

**Context:** Die Engine (Render-Pipeline) ist der Kern der Font-/
Treue-Arbeit; ihre Risiken müssen vor EPIC-005/007 inventarisiert
sein (Q2).

**Input (Vorbedingungen):**
- Repo `../pptxgenerator_v2/phase0/` (read-only)
- 5 Verdachts-Kandidaten aus [[KOCHFABRIK-FEATURE-001]] §4

**Task:**
1. `phase0/scripts/` sichten (Runtime-Pfad zuerst: assemble.py, _deckpipe.py, compose_offer.py, pg_shim.py, render_previews.py)
2. `phase0/spike-pptxgenjs/` sichten (extract.py, reconstruct.js, lib/, convert.py)
3. Die 5 Verdachts-Kandidaten je als Finding belegen oder VERWORFEN führen
4. Weitere Findings verifizieren + priorisieren + zuordnen
5. `FINDINGS-ENGINE.md` im Schema schreiben

**Output:**
- `docs/sprint-10/FINDINGS-ENGINE.md` — priorisierte, belegte Engine-Findings

**Verify:** (EARS 2 aus FEATURE-001)
```bash
cd "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio" && \
test -s docs/sprint-10/FINDINGS-ENGINE.md && \
test "$(grep -cE '^## F-E-[0-9]{2}: ' docs/sprint-10/FINDINGS-ENGINE.md)" -ge 5 && \
test "$(grep -cE '^## F-E-[0-9]{2}: ' docs/sprint-10/FINDINGS-ENGINE.md)" -eq "$(grep -c '^\*\*Beleg:\*\*' docs/sprint-10/FINDINGS-ENGINE.md)" && \
grep -q "SIZE_K" docs/sprint-10/FINDINGS-ENGINE.md
```

**Trace:** R-QA-1, R-QA-3 · WP Q2 · [[KOCHFABRIK-FEATURE-001]]
**Blocked-by:** —

---

### US-038: Font-Extraktor bauen + font-report.json über 200 PDFs

**Context:** R-FONT-1/2 brauchen exakte Zahlen statt Stichproben;
der Extraktor ist zugleich die technische Vorlage für EPIC-005/T1
(exakte pt-Extraktion) (Q3).

**Input (Vorbedingungen):**
- Korpus `../pptxgenerator_v2/phase0/data/cache/{slug}/assets/*.pdf` (200 PDFs, read-only)
- JSON-Schema aus [[KOCHFABRIK-FEATURE-002]] §3

**Task:**
1. `tools/.venv` anlegen, `pymupdf` installieren (NICHT requirements.txt)
2. `tools/font_report.py` schreiben: Span-Extraktion mit exakter pt-Größe (`span["size"]`), Subset-Präfixe strippen, Farben/Bold/Italic erfassen
3. Korpus-Lauf: pro PDF aggregieren, korpusweit aggregieren (fonts, sizes_pt, wingdings_glyphs), Fehler-PDFs unter `errors`
4. `docs/sprint-10/font-report.json` schreiben + `--verify`-Selbstcheck (pdf_count==200) implementieren

**Output:**
- `tools/font_report.py` — reproduzierbarer Extraktor (CLI, --verify)
- `docs/sprint-10/font-report.json` — Span-Daten + Aggregate, 200 PDFs

**Verify:** (EARS 1 aus FEATURE-002)
```bash
cd "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio" && \
tools/.venv/bin/python tools/font_report.py --verify && \
python3 -c "import json; d=json.load(open('docs/sprint-10/font-report.json')); assert d['pdf_count']==200 and len(d['pdfs'])==200 and 'fonts' in d['aggregate'] and 'wingdings_glyphs' in d['aggregate']"
```

**Trace:** R-QA-2 · WP Q3 · [[KOCHFABRIK-FEATURE-002]]
**Blocked-by:** —

---

### US-040: Test-Baseline-Inventur schreiben

**Context:** „111 Tests grün" ist eine Pauschalaussage; EPIC-004
braucht eine Karte, was abgesichert ist und wo die Engine blank ist —
als Refactoring-Gate (Q4).

**Input (Vorbedingungen):**
- `backend/tests/test_*.py` (7 Dateien) + `pytest.ini`
- Engine-Repo (Test-Lage prüfen: erwartbar testfrei)

**Task:**
1. Falls `tools/.venv` fehlt: `python3 -m venv tools/.venv` + `pytest` (und Backend-Test-Deps soweit nötig) installieren — System-Python auf dem Mac hat kein pytest; dann `tools/.venv/bin/python -m pytest backend/tests --collect-only -q` ausführen, reale Test-Anzahl erfassen
2. Pro Test-Datei kartieren: welche Module/Endpoints/Verhalten sie absichert
3. Lücken-Liste: ungetestete Backend-Bereiche + Engine-Skripte (Runtime-Pfad) explizit benennen
4. `TEST-BASELINE.md` schreiben mit `**Test-Count (pytest collect):** {N}`, Abdeckungs-Karte, `## Lücken`

**Output:**
- `docs/sprint-10/TEST-BASELINE.md` — Baseline-Karte + Lücken

**Verify:** (EARS 3 aus FEATURE-001)
```bash
cd "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio" && \
test -s docs/sprint-10/TEST-BASELINE.md && \
grep -qE '\*\*Test-Count \(pytest collect\):\*\* [0-9]+' docs/sprint-10/TEST-BASELINE.md && \
grep -q '^## Lücken' docs/sprint-10/TEST-BASELINE.md
```

**Trace:** R-QA-4 · WP Q4 · [[KOCHFABRIK-FEATURE-001]]
**Blocked-by:** —

---

## Phase 2: Synthese + Entscheidungen

### US-039: FONT-REPORT.md aus font-report.json generieren

**Context:** Das JSON ist für Maschinen (T1/V1) — Jan und die ADRs
brauchen den lesbaren Befund (Q3).

**Input (Vorbedingungen):**
- `docs/sprint-10/font-report.json` (US-038)

**Task:**
1. Aggregate auswerten: Font-Verteilung, pt-Histogramm, Farben, Wingdings-Glyphen-Inventar
2. Worst-Cases benennen (Nicht-Open-Sans-PDFs, exotische Größen)
3. `FONT-REPORT.md` schreiben: Abdeckung `200/200`, Tabellen, Konsequenz-Hinweise für T1–T4

**Output:**
- `docs/sprint-10/FONT-REPORT.md` — lesbarer Report

**Verify:** (EARS 3 aus FEATURE-002)
```bash
cd "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio" && \
grep -q '200/200' docs/sprint-10/FONT-REPORT.md && \
grep -qi 'wingdings' docs/sprint-10/FONT-REPORT.md && \
grep -qiE 'histogramm|verteilung' docs/sprint-10/FONT-REPORT.md
```

**Trace:** R-QA-2 · WP Q3 · [[KOCHFABRIK-FEATURE-002]]
**Blocked-by:** US-038

---

### US-041: ADR-001 PPTX-Font-Embedding schreiben

**Context:** R-FONT-6 ❓ blockiert den Schnitt von EPIC-005; die
Entscheidung braucht die Font-Daten als Grundlage (Q5).

**Input (Vorbedingungen):**
- `docs/sprint-10/font-report.json` (US-038)
- TEMPLATE-ADR aus `~/work/99 Jan/templates/`

**Task:**
1. Ist-Render-Pfad zusammenfassen (PPTX wird aus PDF-Extraktion rekonstruiert; soffice rendert server-seitig)
2. Optionen ausarbeiten: (a) Server-Treue reicht, (b) Font-Embedding in PPTX, (c) Kunden installieren Open Sans — je Pro/Contra mit Aufwandseinschätzung
3. Empfehlung begründen (mit Font-Report-Zahlen) und Konsequenzen für EPIC-005 ableiten
4. `docs/adr/ADR-001-pptx-font-embedding.md` schreiben (`status: proposed`)

**Output:**
- `docs/adr/ADR-001-pptx-font-embedding.md`

**Verify:** (EARS 1+2 aus FEATURE-003)
```bash
cd "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio" && \
grep -q 'status: proposed' docs/adr/ADR-001-pptx-font-embedding.md && \
grep -q '^## Kontext' docs/adr/ADR-001-pptx-font-embedding.md && \
grep -q '^## Alternativen' docs/adr/ADR-001-pptx-font-embedding.md && \
grep -q '^## Konsequenzen' docs/adr/ADR-001-pptx-font-embedding.md && \
! grep -q '{…}' docs/adr/ADR-001-pptx-font-embedding.md
```

**Trace:** R-FONT-6 · WP Q5 · [[KOCHFABRIK-FEATURE-003]]
**Blocked-by:** US-038

---

### US-042: ADR-002 Monorepo-Schnitt schreiben

**Context:** R-REF-1 ❓ + R-NF-2 blockieren EPIC-004/M1; Repo-Layout,
Alt-Ordner-Schicksal und Coolify-Migration müssen entschieden sein (Q5).

**Input (Vorbedingungen):**
- `docs/sprint-10/FINDINGS-STUDIO.md` + `FINDINGS-ENGINE.md` (US-036/037)
- Ist: `vendor.sh`, README §Engine-Sync, Alt-Ordner-Inventar unter `../`

**Task:**
1. Ist-Topologie dokumentieren (2 Repos + Vendoring + Coolify-Deploy von GitHub master)
2. Optionen: (a) Monorepo neu mit Historie-Merge, (b) studio absorbiert Engine, (c) Status quo + besseres Vendoring — je Pro/Contra
3. Alt-Ordner-Schicksal pro Verzeichnis vorschlagen (archivieren/mitnehmen/löschen) + Coolify-Migrationsplan skizzieren
4. `docs/adr/ADR-002-monorepo-schnitt.md` schreiben (`status: proposed`)

**Output:**
- `docs/adr/ADR-002-monorepo-schnitt.md`

**Verify:** (EARS 1+2 aus FEATURE-003)
```bash
cd "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio" && \
grep -q 'status: proposed' docs/adr/ADR-002-monorepo-schnitt.md && \
grep -q '^## Alternativen' docs/adr/ADR-002-monorepo-schnitt.md && \
grep -qi 'coolify' docs/adr/ADR-002-monorepo-schnitt.md && \
! grep -q '{…}' docs/adr/ADR-002-monorepo-schnitt.md
```

**Trace:** R-REF-1, R-NF-2 · WP Q5 · [[KOCHFABRIK-FEATURE-003]]
**Blocked-by:** US-036, US-037

---

### US-043: ADR-003 pgbundle vs. Postgres schreiben

**Context:** Die Engine nutzt einen npz-Shim, die Slidesuche umgeht
ihn bereits direkt — der Daten-Zugriffspfad braucht eine bewusste
Entscheidung statt zweier Wahrheiten (Q5, R-REF-3).

**Input (Vorbedingungen):**
- `docs/sprint-10/FINDINGS-ENGINE.md` (US-037)
- Ist: `phase0/scripts/pg_shim.py`, `backend/slidesuche.py` (Bypass), `data/pgbundle.npz`

**Task:**
1. Ist-Zugriffspfade dokumentieren (pg_shim vs. Direkt-Zugriff vs. echtes Postgres in EPIC-001-Tabellen)
2. Optionen: (a) pgbundle behalten + Bypass legitimieren, (b) Engine-Queries auf das bestehende Postgres heben, (c) Hybrid mit klarer Grenze — je Pro/Contra
3. Empfehlung + Konsequenzen (inkl. ob ein Folge-Epic nötig ist)
4. `docs/adr/ADR-003-pgbundle-vs-postgres.md` schreiben (`status: proposed`)

**Output:**
- `docs/adr/ADR-003-pgbundle-vs-postgres.md`

**Verify:** (EARS 1+2 aus FEATURE-003)
```bash
cd "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio" && \
grep -q 'status: proposed' docs/adr/ADR-003-pgbundle-vs-postgres.md && \
grep -q '^## Alternativen' docs/adr/ADR-003-pgbundle-vs-postgres.md && \
grep -q '^## Konsequenzen' docs/adr/ADR-003-pgbundle-vs-postgres.md && \
! grep -q '{…}' docs/adr/ADR-003-pgbundle-vs-postgres.md
```

**Trace:** R-REF-3 · WP Q5 · [[KOCHFABRIK-FEATURE-003]]
**Blocked-by:** US-037

---

## Dependency Graph

```
US-036 ─┬─▶ US-042
US-037 ─┤├─▶ US-043
US-038 ─┼─▶ US-039
        └─▶ US-041
US-040 (unabhängig)
```

## Summary

| Phase | Stories | Parallelisierbar | Kritischer Pfad |
|---|---|---|---|
| 1: Analyse | US-036, US-037, US-038, US-040 | ja (4 parallel) | US-037/US-038 |
| 2: Synthese + ADRs | US-039, US-041, US-042, US-043 | ja (4 parallel) | US-042 |
| **Total** | **8 Stories** | **max 4 parallel** | |
