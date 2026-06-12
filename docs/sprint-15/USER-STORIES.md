# USER-STORIES — kochfabrik Sprint 15

> **Typ:** US. Epic-getrieben: [[EPIC-008]] C1–C3 + [[EPIC-007]] V1–V4
> (2× geschoben, jetzt fällig) + Carry-Over HIGH: Voll-Korpus-Batches
> (entsperrt den Wizard in Prod). Suite-Baseline 213 passed/5 skipped.

## Story-Gate (PFLICHT)

- [x] ≤ 5 Task-Schritte · ≤ 3 Output-Einträge · Verify deterministisch
- [x] Verify bildet ein EARS-Kriterium ab · Null Platzhalter
- [x] Blocked-by explizit · Trace vorhanden

## Boundaries (sprintweit)

- ✅ **Always:** Feature-Branches; venv-Tests; Container-Renders
  (kf-studio-sim); fitz als Analyse-Dep in tools/.venv (US-081,
  explizit freigegeben); **US-078: Voll-Korpus-Läufe + Volume-Sync +
  Deploy sind durch den Sprint-Plan EXPLIZIT autorisiert** (sonst
  Ask-first) — exakt nach Runbooks, nichts darüber hinaus
- ⚠️ **Ask-first (headless → BLOCKED):** weitere Dependencies; andere
  GitHub-Settings als die in US-080/084 genannten Protection-Calls;
  Host-Writes außerhalb der Runbook-Pfade
- 🚫 **Never:** Cache-BESTAND/pgbundle verändern (neue preview_notext-
  Dateien anlegen ist ok); Tests/Lint/Gate aufweichen für grün;
  rank()/Gold-Test anfassen; master pushen; kein timeout-Binary

---

## Phase 1 (Wave 1 — 3 Stränge parallel)

### US-078: Voll-Korpus-Batches + Volume-Sync + Deploy [LEAD-STORY]

**Context:** Wizard läuft in Prod im Fallback (Previews mit Texten,
text-only-Ranking) — die Sprint-14-Artefakte fehlen für 199 von 201
Decks. **Diese Story führt der LEAD aus** (Stunden-Langläufer +
Prod-Writes — kein Team-Agent).

**Input (Vorbedingungen):**
- `docs/sprint-14/KORPUS-RUNBOOK.md` + `IMGBUNDLE-RUNBOOK.md`
  (verbindliche Befehle); lokaler Voll-Korpus
  `../pptxgenerator_v2/phase0/data/cache` (201 Decks); Volume
  `/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache`;
  GEMINI-Key in ~/work/.env

**Task:**
1. render_notext-Voll-Lauf exakt nach KORPUS-RUNBOOK (Container, idempotent, als überwachter Hintergrund-Lauf mit aktivem Polling) über den lokalen Alt-Korpus
2. embed_images-Voll-Lauf exakt nach IMGBUNDLE-RUNBOOK (Gemini-Vision über alle Foto-Slides) → volles `engine/data/imgbundle.npz`; Stichproben-Query dokumentieren
3. Volume-Sync der `preview_notext/`-Verzeichnisse nach Runbook (rsync auf den Host, NUR neue Dateien — Bestand unangetastet); Zähl-Beweis vorher/nachher
4. imgbundle.npz auf Branch `sprint-15-us078-batches` committen (Größe dokumentieren) + Draft-PR; nach Merge durch /sprint-review: Deploy + `LIVE_DEEP=1 live_verify` + Wizard-Stichprobe (notext-PNG einer Nicht-Sample-Slide via Route = 200)

**Output:**
- `engine/data/imgbundle.npz` (Voll-Korpus)
- Volume: `cache/<deck>/preview_notext/` für alle render-fähigen Decks
- `docs/sprint-15/BATCH-PROTOKOLL.md` (Zahlen, Dauer, Kosten, Stichproben)

**Verify:** (FEATURE-013 EARS 4 — Betriebs-Vollzug)
```bash
test -s docs/sprint-15/BATCH-PROTOKOLL.md && \
grep -q "Decks gerendert" docs/sprint-15/BATCH-PROTOKOLL.md && \
tools/.venv/bin/python -c "import numpy; d=numpy.load('engine/data/imgbundle.npz'); assert len(d['deck']) > 200, len(d['deck']); print('imgbundle:', len(d['deck']), 'Slides')" && \
ssh -i ~/.ssh/hetzner_id root@188.245.110.5 "ls /data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache/*/preview_notext/ -d | wc -l" | awk '{exit ($1 < 100)}'
```

**Trace:** R-DECK-4, R-NF-3 · Carry-Over S14 (HIGH) · [[KOCHFABRIK-FEATURE-013]]
**Blocked-by:** —

---

### US-079: GitHub-Actions-Pipeline (C1)

**Context:** Kein CI — jedes Gate ist freiwillig (EPIC-008/C1, 2×
geschoben). Pipeline = Lint + Tests + Image-Build auf PR und master.

**Input (Vorbedingungen):**
- Anker: ruff-Baseline `tools/.venv/bin/ruff check --select
  E9,F63,F7,F82 backend engine/scripts` = sauber (verifiziert
  2026-06-11); Suite 213/5skip läuft DB-los (DB-gated Skips by
  design); Dockerfile baut auf Ubuntu; Tests brauchen Python ≥3.10 →
  CI nimmt 3.12 (Container-Parität); FEATURE-009 §12 Pitfalls 1–3

**Task:**
1. TDD: `backend/tests/test_sprint15.py` NEU (CI-Ketten-Datei): ci.yml existiert, enthält Jobs `ci` (ruff E9,F63,F7,F82 + pytest + docker build), Trigger pull_request+push-master, KEIN timeout-Binary-Aufruf — Marker-Tests rot
2. `.github/workflows/ci.yml`: Job `ci` auf ubuntu-latest, Python 3.12, pip install -r requirements.txt + pytest httpx ruff → ruff (nur E9,F63,F7,F82) → pytest backend/tests -q → docker build -t kf-studio-sim . (Pitfall 1: KEIN tools/.venv-Pfad im Runner)
3. Push → ersten echten Lauf auf dem Branch pollen (gh run watch/list, max ~8×30s) bis grün; bei rot: fixen (max 2 Iterationen, sonst FAILED melden)
4. Suite lokal 0 failed · `git add .github/workflows/ci.yml backend/tests/test_sprint15.py` · Commit `feat(ci): US-079 GitHub-Actions-Pipeline (Lint+Tests+Build)` + Leerzeile + `Closes #` (Issue-Nr.) + Leerzeile + Co-Authored-By · KEIN Rebase (Ketten-Branch) · push origin sprint-15-ci

**Output:**
- `.github/workflows/ci.yml`
- `backend/tests/test_sprint15.py`

**Verify:** (FEATURE-009 EARS 2)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint15.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
test "$(gh run list --branch sprint-15-ci --workflow ci.yml --limit 1 --json conclusion -q '.[0].conclusion')" = "success"
```

**Trace:** R-CI-1 · WP C1 · [[KOCHFABRIK-FEATURE-009]]
**Blocked-by:** —

---

### US-081: Treue-Metrik fidelity.py (V1)

**Context:** Treue braucht eine Zahl — fitz-basierter Vergleich
Original-PDF-Seite vs. Rekonstruktions-PDF-Seite (Text/Geometrie/
Font/Pixel → total).

**Input (Vorbedingungen):**
- Anker: `tools/font_report.py` (fitz-Span-Muster aus Sprint 10);
  ref.pdf NUR im Deck `10-182-raumkarussell-gmbh-12-09-2026` (kf-ausstattung-location ist ein synthetisches Template-Deck OHNE ref.pdf — Sample = nur raumkarussell, A4-Format → Pitfall 2 greift);
  **fitz installieren: `tools/.venv/bin/pip install "pymupdf>=1.24"`
  (Analyse-Dep, NICHT requirements.txt — explizit freigegeben)**

**Task:**
1. TDD: `backend/tests/test_sprint15_fidelity.py` NEU (Treue-Ketten-Datei; skipif fitz fehlt): Selbst-Vergleich ref.pdf-Seite → total ≥ 0.99; manipulierter Text → text-Score sinkt; manipulierte Font-Size → font-Score sinkt (Monotonie via synthetisch erzeugtem Vergleichs-PDF aus fitz selbst) — ROT
2. `engine/tooling/fidelity.py`: compare(ref_pdf, ref_page, neu_pdf, neu_page) nach FEATURE-016 §4 (Token-F1, BBox-IoU-Matching, Font-Match size±0.5/Familie, Pixmap-Graustufen 1−MAE @192px; total = 0.35/0.25/0.25/0.15); Koordinaten auf Seitenmaße normalisieren (Pitfall 2: A4 vs. 16:9); CLI `python3 fidelity.py a.pdf:1 b.pdf:1`
3. Metrik-Version als Konstante (FIDELITY_VERSION = "1.0" + fitz-Version im Output)
4. Suite 0 failed · `git add engine/tooling/fidelity.py backend/tests/test_sprint15_fidelity.py` · Commit `feat(tooling): US-081 Treue-Metrik fidelity.py (V1)` + Closes-Footer · KEIN Rebase · push origin sprint-15-treue

**Output:**
- `engine/tooling/fidelity.py`
- `backend/tests/test_sprint15_fidelity.py`

**Verify:** (FEATURE-016 EARS 1)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint15_fidelity.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
tools/.venv/bin/python engine/tooling/fidelity.py "engine/data/cache/10-182-raumkarussell-gmbh-12-09-2026/assets/ref.pdf:1" "engine/data/cache/10-182-raumkarussell-gmbh-12-09-2026/assets/ref.pdf:1" | grep -q '"total"' && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```

**Trace:** R-FID-1, R-FID-4 · WP V1 · [[KOCHFABRIK-FEATURE-016]]
**Blocked-by:** —

---

## Phase 2 (Ketten)

### US-080: Branch-Protection + Delivery-Flow-Doku (C3)

**Context:** master ist ungeschützt; nach grünem CI-Lauf wird
PR-Pflicht + required check verbindlich. CI-Kette 2/3.

**Input (Vorbedingungen):**
- US-079 DONE (Check `ci` existiert + ist grün gelaufen — Pitfall 2:
  Protection NIE vor erstem grünen Lauf); FEATURE-009 §12 Pitfall 4
  (Protection sperrt eigenen Workflow — Admin-Bypass dokumentieren)

**Task:**
1. TDD (test_sprint15.py): DELIVERY-FLOW.md existiert + nennt Admin-Bypass + manuellen Deploy; Protection-Zustand via gh api (required_status_checks enthält "ci", enforce_admins false) — rot (API-Test skipif kein gh)
2. `gh api repos/jantristan-hb/kochfabrik-studio/branches/master/protection -X PUT` — required_status_checks {strict:false, contexts:["ci"]}, enforce_admins:false, required_pull_request_reviews:null (PR-Pflicht via Status-Check, keine Review-Pflicht — 1-Mann-Betrieb), restrictions:null — **dieser eine schreibende Call ist explizit Task-gedeckt**
3. `docs/ops/DELIVERY-FLOW.md`: PR→CI→Merge→manueller Deploy+LIVE_DEEP; Admin-Bypass-Regel (Review-Doc-Commits via Bypass erlaubt, Code nie); CLAUDE.md-Verweis ergänzen (1 Zeile im Befehle-Block)
4. Suite 0 failed · `git add docs/ops/DELIVERY-FLOW.md backend/tests/test_sprint15.py CLAUDE.md` · Commit `feat(ops): US-080 Branch-Protection + Delivery-Flow (C3)` + Closes-Footer · push origin sprint-15-ci

**Output:**
- `docs/ops/DELIVERY-FLOW.md`
- `backend/tests/test_sprint15.py` (erweitert; + CLAUDE.md 1 Zeile)

**Verify:** (FEATURE-009 EARS 1+4)
```bash
gh api repos/jantristan-hb/kochfabrik-studio/branches/master/protection -q '.required_status_checks.contexts' | grep -q '"ci"' && \
grep -qi "admin" docs/ops/DELIVERY-FLOW.md && \
tools/.venv/bin/python -m pytest backend/tests/test_sprint15.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```

**Trace:** R-CI-2 · WP C3 · [[KOCHFABRIK-FEATURE-009]]
**Blocked-by:** US-079

---

### US-082: Korpus-Harness fidelity_run (V2)

**Context:** Die Metrik braucht den Lauf: Sample-Slides rekonstruieren
(Container) und gegen ihre Original-ref.pdf-Seiten messen. Treue-Kette 2/4.

**Input (Vorbedingungen):**
- US-081 DONE (Branch); Container-Render-Muster
  `engine/tooling/render_notext.py` (elements→reconstruct→soffice);
  ref.pdf-Seiten ↔ elements.json-Seiten sind 1:1 nummeriert

**Task:**
1. TDD (test_sprint15_fidelity.py): fidelity_run --deck 10-182-raumkarussell-gmbh-12-09-2026 → JSON mit je-Slide-Scores; zweiter Lauf reproduzierbar ±0.005 (docker-gated skipif) — ROT
2. `engine/tooling/fidelity_run.py`: je Sample-Slide elements→1-Slide-PPTX (reconstruct.js)→soffice-PDF→fidelity.compare gegen ref.pdf:page; Ausgabe JSON {deck, page, scores, metrik_version}; --decks/--limit; Render via SOFFICE-Env (Container-Aufruf wie render_notext dokumentiert im Modul-Docstring)
3. Sample-Lauf im Container über beide committeten Decks — Output zeigen (die Scores WERDEN Font-Defekte zeigen: F-E-02/SIZE_K — erwartet, dokumentieren, Pitfall 3)
4. Suite 0 failed · `git add engine/tooling/fidelity_run.py backend/tests/test_sprint15_fidelity.py` · Commit `feat(tooling): US-082 Korpus-Harness fidelity_run (V2)` + Closes-Footer · push origin sprint-15-treue

**Output:**
- `engine/tooling/fidelity_run.py`
- `backend/tests/test_sprint15_fidelity.py` (erweitert)

**Verify:** (FEATURE-016 EARS 2)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint15_fidelity.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
docker run --rm -v "$PWD/engine/data:/app/engine/data" -v "$PWD/engine/tooling:/app/engine/tooling" kf-studio-sim python3 engine/tooling/fidelity_run.py --deck 10-182-raumkarussell-gmbh-12-09-2026 | grep -q '"total"'
```

**Trace:** R-FID-2 · WP V2 · [[KOCHFABRIK-FEATURE-016]]
**Blocked-by:** US-081

---

### US-083: Baseline einfrieren + Report + Schwellen-Vorschlag (V3+V4)

**Context:** Der Ist-Stand wird die Referenz — inkl. der bekannten
Font-Defekte. EPIC-005 misst seinen Fortschritt später daran.
Treue-Kette 3/4.

**Input (Vorbedingungen):**
- US-082 DONE (Branch); fidelity_run-Sample-Output

**Task:**
1. Baseline-Lauf über das Sample-Deck 10-182-raumkarussell (alle Seiten — einziges committetes Deck mit ref.pdf) im Container → `docs/sprint-15/fidelity_baseline.json` committen (inkl. metrik_version)
2. `docs/sprint-15/FIDELITY-REPORT.md`: Score-Tabelle je Slide, Teil-Score-Analyse (wo verliert der Render — erwartbar font wegen F-E-02/SIZE_K), größte 3 Abweichungen mit 1-Satz-Diagnose, **Schwellen-Vorschlag** (z.B. Gate-Toleranz 0.02 + Mindest-total) als Entscheidungsvorlage für Jan (V5, offen markiert), Voll-Korpus-Runbook-Abschnitt
3. `git add docs/sprint-15/fidelity_baseline.json docs/sprint-15/FIDELITY-REPORT.md` · Commit `feat(tooling): US-083 Treue-Baseline + Report (V3/V4)` + Closes-Footer · push origin sprint-15-treue

**Output:**
- `docs/sprint-15/fidelity_baseline.json`
- `docs/sprint-15/FIDELITY-REPORT.md`

**Verify:** (FEATURE-016 EARS 4)
```bash
tools/.venv/bin/python -c "import json; d=json.load(open('docs/sprint-15/fidelity_baseline.json')); assert d and all('total' in s['scores'] for s in d['slides']); print(len(d['slides']), 'Slides')" && \
grep -qi "schwellen" docs/sprint-15/FIDELITY-REPORT.md && \
grep -q "metrik_version" docs/sprint-15/fidelity_baseline.json
```

**Trace:** R-FID-3, R-FID-5 (❓ Vorlage) · WP V3+V4 · [[KOCHFABRIK-FEATURE-016]]
**Blocked-by:** US-082

---

## Phase 3 (Konvergenz)

### US-084: Regressions-Gate + CI-Pflicht-Check (V3-Gate + C2)

**Context:** Das Gate macht die Baseline scharf: Verschlechterung
blockiert den Merge. Treue-Kette 4/4 — **WARTEPUNKT: Lead merged
sprint-15-ci in sprint-15-treue** (Gate erweitert ci.yml).

**Input (Vorbedingungen):**
- US-083 DONE + US-079/080 gemergt (ci.yml im Branch); FEATURE-009
  Pitfall 5 (fidelity-Job braucht das Image → needs/Build im Job)

**Task:**
1. TDD (test_sprint15_fidelity.py): Gate-Test — fidelity_run-Sample vs. fidelity_baseline.json, total je Slide ≥ baseline−0.02 (docker/node-gated skipif); Regressions-BEWEIS-Test: Render mit künstlich manipulierten elements (Font-Size ×0.5 vor reconstruct) → Gate-Vergleich schlägt fehl (assertet das FEHLSCHLAGEN — EARS 3) — rot, dann grün
2. ci.yml: Job `fidelity` (needs: docker build; führt Gate-pytest mit Markern aus; required-tauglicher Job-Name)
3. Branch-Protection um Check `fidelity` erweitern (gh api PUT, contexts ["ci","fidelity"] — Task-gedeckt); CI-Lauf auf dem Branch pollen bis grün (max 2 Fix-Iterationen)
4. Suite 0 failed + Sim-Gate grün · `git add .github/workflows/ci.yml backend/tests/test_sprint15_fidelity.py` · Commit `feat(ci): US-084 Treue-Regressions-Gate als Pflicht-Check (C2)` + Closes-Footer · push origin sprint-15-treue

**Output:**
- `.github/workflows/ci.yml` (Job fidelity)
- `backend/tests/test_sprint15_fidelity.py` (Gate + Beweis)

**Verify:** (FEATURE-016 EARS 3 + FEATURE-009 EARS 3)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint15_fidelity.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
gh api repos/jantristan-hb/kochfabrik-studio/branches/master/protection -q '.required_status_checks.contexts' | grep -q '"fidelity"' && \
test "$(gh run list --branch sprint-15-treue --workflow ci.yml --limit 1 --json conclusion -q '.[0].conclusion')" = "success"
```

**Trace:** R-FID-3, R-CI-3 · WP V3+C2 · [[KOCHFABRIK-FEATURE-016]] · [[KOCHFABRIK-FEATURE-009]]
**Blocked-by:** US-083, US-080

---

## Dependency Graph

```
LEAD:        US-078 (Batches, läuft nebenher — kein Code-Konflikt)
CI-Kette:    US-079 ─▶ US-080 ──────────────┐
Treue-Kette: US-081 ─▶ US-082 ─▶ US-083 ─▶ US-084
                                  [Lead merged CI-Kette vor US-084]
```

> Datei-Ownership: ci.yml + test_sprint15.py + docs/ops/DELIVERY-FLOW
> = CI-Kette · fidelity* + test_sprint15_fidelity.py + FIDELITY-Docs
> = Treue-Kette · imgbundle.npz + BATCH-PROTOKOLL = US-078 (Lead).
> CLAUDE.md: 1 additive Zeile nur in US-080.

## Summary

| Strang | Stories | Parallelisierbar |
|---|---|---|
| Wave 1 | US-078 (Lead), US-079, US-081 | ja (3 parallel) |
| CI-Kette | US-079→080 | sequentiell |
| Treue-Kette | US-081→082→083→084 | sequentiell, Wartepunkt vor 084 |
| **Total** | **7 Stories** | 3 Stränge |
