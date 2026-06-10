# USER-STORIES — kochfabrik Sprint 11

> **Typ:** US. Geschnitten aus [[EPIC-004]] (M1–M3) + Cross-Epic-Pull
> [[EPIC-009]]/B1 (Backup, Sicherheits-Auflage). Setzt [[ADR-002]] um.
> **Prod-Sprint:** master-Push = Auto-Deploy — alles läuft auf Branches,
> der Cutover ist der finale Merge NACH grünem Sim-Gate.

## Story-Gate (PFLICHT)

- [x] ≤ 5 Task-Schritte · ≤ 3 Output-Dateien · Verify deterministisch
- [x] Verify bildet ein EARS-Kriterium der FEATURE-Spec ab
- [x] Null Platzhalter · Blocked-by explizit · Trace vorhanden

## Boundaries (sprintweit)

- ✅ **Always:** Feature-Branches; Engine-Repo `main` committen/pushen
  (nicht deploy-gebunden); lokale Builds/Tests; read-only Coolify-GETs;
  pg_dump lesend; Backups nach `../backups/` (außerhalb des Repos)
- ⚠️ **Ask-first (headless: BLOCKED melden):** schreibende Coolify-Calls
  (deploy/restart/env); nicht-read-only SSH; Force-Push; jede
  Semantik-Änderung an Ranking/Render („Verhalten strikt erhalten")
- 🚫 **Never:** Push/Merge auf Studio-master (Cutover = /sprint-review);
  `data/cache/` + `pgbundle.npz` ändern/regenerieren; Alt-Ordner
  verschieben/löschen; Secrets/Dumps committen; subtree mit `--squash`

---

## Phase 1: Vorbedingungen (Wave 1, parallel — eigene Branches)

### US-044: Backup vor Cutover erstellen + verifizieren

**Context:** Vor dem Deploy-Umbau existiert kein Backup; ein
fehlgeschlagener Cutover ohne Restore-Pfad wäre Totalausfall
(Sicherheits-Auflage, vorgezogen aus EPIC-009/B1).

**Input (Vorbedingungen):**
- `~/work/99 Jan/settings/INFRA.md` + `SOVEREIGN-COOLIFY.md` (Host-Zugang)
- `COOLIFY_TOKEN` in `~/work/.env`; DB-Service `kf-studio-pg`

**Task:**
1. Host-/DB-Zugang ermitteln (Settings-Docs, Coolify-API GET) — kein Zugang → BLOCKED melden
2. `pg_dump` von `kf-studio-pg` ziehen → `../backups/kf-studio-pg-2026-06-09.sql.gz` (außerhalb des Repos)
3. Integrität prüfen: `gzip -t` + Dump enthält `CREATE TABLE`-Marker für app_user/customer/offer/chat_message/seq_counter
4. Korpus-Volume-Inventar via SSH/API (read-only): Deck-Count unter `/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache`, Gesamtgröße, 3 Stichproben-Dateigrößen
5. `docs/sprint-11/BACKUP-VERIFY.md` schreiben (Pfade, Checks, Restore-Hinweis)

**Output:**
- `docs/sprint-11/BACKUP-VERIFY.md` (Dump selbst bleibt off-repo)

**Verify:** (EARS 1 aus FEATURE-005)
```bash
test -s docs/sprint-11/BACKUP-VERIFY.md && \
grep -qE 'kf-studio-pg-2026-06-09\.sql\.gz' docs/sprint-11/BACKUP-VERIFY.md && \
grep -q 'gzip -t: OK' docs/sprint-11/BACKUP-VERIFY.md && \
grep -qi 'deck-count' docs/sprint-11/BACKUP-VERIFY.md && \
F=$(grep -oE '\.\./backups/kf-studio-pg-2026-06-09\.sql\.gz' docs/sprint-11/BACKUP-VERIFY.md | head -1) && test -s "$F"
```

**Trace:** R-BAK-1 (Teil), R-BAK-2 (Teil), R-NF-2 · WP B1 (vorgezogen) · [[KOCHFABRIK-FEATURE-005]]
**Blocked-by:** —

---

### US-045: Engine-Repo konsolidieren (Mac-Diff + F-E-10 Env-Konfig)

**Context:** Das Engine-Repo ist dirty (uncommitteter Fedora→Mac-
Migrations-Diff) und trägt Hardcodes (DSN localhost:5434 mit Klartext-PW,
CORPUS_DIR als absoluter Mac-Pfad) — beides blockiert den Subtree-Merge.

**Input (Vorbedingungen):**
- `../pptxgenerator_v2` @ main (dirty: Mode-Bits + /home/jrudat→/Users/janrudat)
- Anker: `phase0/scripts/compose_offer.py:30,37`, `assemble.py:154`

**Task:**
1. Dirty-State sichten: Inhalts-Diffs = nur Mac-Pfad-Migration? Falls Unerwartetes → BLOCKED mit Diff-Zusammenfassung
2. Migrations-Diff committen (`chore(mac): Fedora→Mac-Pfadmigration`)
3. F-E-10: `compose_offer.py` — `CORPUS_DIR = os.environ.get("KF_CORPUS_DIR", "<heutiger Pfad>")`; DSN-Felder analog (`KF_PG_HOST/PORT/USER/PASSWORD/DB`, Defaults = heutige Werte; Passwort-Default bleibt funktional, Doku-Hinweis auf Rotation in EPIC-010/H2)
4. Engine-Tests laufen lassen (`phase0/tests`, 8er-Suite) — grün; committen
5. `git push origin main`

**Output:**
- `../pptxgenerator_v2/phase0/scripts/compose_offer.py` — Env-Konfig
- (Commits im Engine-Repo, gepusht auf main)

**Verify:** (EARS 1 aus FEATURE-004)
```bash
cd ../pptxgenerator_v2 && git diff --quiet && git diff --cached --quiet && \
git status -sb | head -1 | grep -vq behind && \
grep -q 'KF_CORPUS_DIR' phase0/scripts/compose_offer.py && \
grep -q 'KF_PG_' phase0/scripts/compose_offer.py && \
python3 - <<'PY'
import os, sys, importlib.util
spec = importlib.util.spec_from_file_location("co", "phase0/scripts/compose_offer.py")
src = open("phase0/scripts/compose_offer.py").read()
assert "os.environ.get" in src
assert "/Users/janrudat/Nextcloud" in src, "Default muss heutigen Wert behalten"
PY
```

**Trace:** R-QA-3, R-REF-6 · WP M1 (Vorbedingung, F-E-10) · [[KOCHFABRIK-FEATURE-004]]
**Blocked-by:** —

---

### US-046: Charakterisierungs-Tests + Suite lokal 100% grün

**Context:** Vor dem Struktur-Umbau braucht die HTTP-Oberfläche ein
Verhaltens-Netz (heute keine TestClient-Tests), und der bekannte
Alembic-Namespace-Failure muss weg, damit „Suite grün" als Gate taugt
(Carry-Over aus Sprint 10).

**Input (Vorbedingungen):**
- `docs/sprint-10/TEST-BASELINE.md` (E1/E2-Befunde)
- `backend/tests/test_sprint2.py::test_alembic_baseline_present_and_empty` (failing)

**Task:**
1. Alembic-Test fixen: `backend/alembic/versions/__init__.py` anlegen ODER Test auf pfad-robuste Ermittlung umstellen (kein `__file__`-None mehr) — Verhalten der App unverändert
2. `backend/tests/test_charakterisierung.py`: FastAPI-TestClient DB-los — Health-Routen-Status/Shape (`/api/health`, `/api/angebot/health`, `/api/praesentation/health`), Auth-Gate (geschützte Route ohne Cookie → 401/redirect), statisches Asset
3. README-Hinweis: Python ≥3.10 nötig (PEP-604), venv-Anleitung `tools/.venv`
4. Volle Suite im venv: 0 failed

**Output:**
- `backend/tests/test_charakterisierung.py`
- `backend/alembic/versions/__init__.py` (oder Test-Fix in test_sprint2.py)
- `README.md` — Test-/Python-Hinweis

**Verify:** (EARS 2 aus FEATURE-004)
```bash
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
test -s backend/tests/test_charakterisierung.py && \
grep -q "TestClient" backend/tests/test_charakterisierung.py
```

**Trace:** R-QA-4, R-REF-6 · WP M1 (Gate) + Carry-Over S10 · [[KOCHFABRIK-FEATURE-004]]
**Blocked-by:** —

---

## Phase 2: Monorepo-Umbau (SEQUENTIELL — ein Branch `sprint-11-monorepo`)

> US-047→US-050 bauen aufeinander auf denselben Dateien auf —
> bewusste Abweichung vom Parallel-Default (FEATURE-004 §12 Pitfall 5).

### US-047: Engine via subtree einziehen + Layout flachziehen

**Context:** M1-Kern aus ADR-002 — Engine-Historie ins Studio-Repo,
vendored Kopie ersetzen, Layout gemäß Ziel-Struktur.

**Input (Vorbedingungen):**
- US-045 DONE (Engine main sauber + gepusht)
- Branch `sprint-11-monorepo` von master

**Task:**
1. `git rm -r engine && git commit` (vendored Kopie raus; data/node_modules werden in Schritt 4 gerettet)
2. `git subtree add --prefix=engine "../pptxgenerator_v2" main` (OHNE --squash)
3. Flachziehen: `git mv engine/phase0/scripts engine/scripts`, `…/spike-pptxgenjs engine/spike-pptxgenjs`, `…/tests engine/tests`, `…/fixtures engine/fixtures`; Engine-Repo-Reste (docs/, design/, next-step.md, phase0-Restdateien) nach `engine/upstream/`
4. Retten aus dem Commit vor Schritt 1: `git checkout <sha> -- engine/phase0/data` + node_modules → an neue Pfade `engine/data`, `engine/spike-pptxgenjs/node_modules` verschieben, committen
5. `for f in engine/scripts/*.py; do python3 -m py_compile "$f"; done` — alles kompiliert

**Output:**
- `engine/` (neues Layout, Historie erhalten)
- (mehrere Commits auf `sprint-11-monorepo`)

**Verify:** (EARS 3 + 5 aus FEATURE-004)
```bash
git log --oneline -- engine | grep -qiE "subtree|phase0|angebot|korpus" && \
test -d engine/scripts && test -d engine/spike-pptxgenjs/node_modules && \
test -s engine/data/pgbundle.npz && \
ls engine/scripts/*.py | head -1 >/dev/null && \
for f in engine/scripts/*.py; do python3 -m py_compile "$f" || exit 1; done && \
test ! -d engine/phase0
```

**Trace:** R-REF-1 · WP M1 · [[KOCHFABRIK-FEATURE-004]]
**Blocked-by:** US-045

---

### US-048: Backend-Pfade repo-intern + vendor.sh entfernen

**Context:** Die `_VEND/_SIB`-Heuristik rät zwischen vendored und
Schwester-Repo; nach dem Merge gibt es genau einen Pfad.

**Input (Vorbedingungen):**
- US-047 DONE (gleicher Branch), US-046 DONE (Tests als Gate)
- Anker: `backend/app.py:344-360`, `backend/slidesuche.py:33-38`

**Task:**
1. `backend/app.py`: `_ENG = os.path.join(ROOT, "engine", "scripts")` (Heuristik weg), `SPIKE`-Ableitung anpassen
2. `backend/slidesuche.py`: analoge Pfade (`engine/scripts`, `engine/data/cache`, `engine/spike-pptxgenjs`)
3. `vendor.sh` löschen; README §Engine-Sync durch Monorepo-Absatz ersetzen (Engine-Entwicklung direkt in `engine/`)
4. Suite + Charakterisierung grün (venv); `grep`-Gegenprobe: kein `phase0`/`pptxgenerator_v2` mehr in backend/

**Output:**
- `backend/app.py`, `backend/slidesuche.py` — repo-interne Pfade
- `README.md` (vendor.sh-Abschnitt ersetzt; Datei `vendor.sh` gelöscht)

**Verify:** (EARS 4 aus FEATURE-004)
```bash
! grep -rE "phase0|pptxgenerator_v2" backend/*.py && \
test ! -f vendor.sh && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```

**Trace:** R-REF-1, R-REF-4 (Teil), R-REF-6 · WP M1/M2 · [[KOCHFABRIK-FEATURE-004]]
**Blocked-by:** US-046, US-047

---

## Phase 3: Deploy-Vorbereitung (gleicher Branch, sequentiell)

### US-049: Dockerfile auf Monorepo-Layout + alembic.ini

**Context:** M2 aus ADR-002 — das Image muss das neue Layout ziehen;
`alembic.ini` fehlt im Container seit Sprint 1 (rc=255-Drift).

**Input (Vorbedingungen):**
- US-048 DONE (gleicher Branch); `Dockerfile`, `alembic.ini` (Root)

**Task:**
1. `Dockerfile`: `COPY engine ./engine` (zieht neues Layout — prüfen dass `engine/data` + node_modules im Build-Context landen), `COPY alembic.ini .`
2. `.dockerignore` prüfen/anlegen: `tools/.venv`, `docs/`, `../backups` ausschließen — Image schlank halten
3. Lokaler Build: `docker build -t kf-studio-sim .` läuft durch

**Output:**
- `Dockerfile`
- `.dockerignore`

**Verify:** (EARS 2 aus FEATURE-005, Build-Teil)
```bash
grep -q 'COPY alembic.ini' Dockerfile && \
grep -q 'COPY engine ./engine' Dockerfile && \
docker info >/dev/null 2>&1 && docker build -q -t kf-studio-sim . >/dev/null
```

**Trace:** R-NF-2, R-QA-3 (F-S-01-Voraussetzung) · WP M2 · [[KOCHFABRIK-FEATURE-005]]
**Blocked-by:** US-048

---

### US-050: Sim-Gate-Skript + Container-Smoke

**Context:** Das vendor.sh-Sim-Gate entfällt — ein eigenständiges,
wiederverwendbares Gate muss VOR jedem Cutover beweisen, dass der
Container lebt (Sicherheits-Auflage 3; wird in EPIC-008 CI-Pflicht).

**Input (Vorbedingungen):**
- US-049 DONE (Image baut); `vendor.sh`-Sim-Gate-Logik als Vorlage (git history)

**Task:**
1. `tools/sim_gate.sh`: docker build → Container starten (ohne DATABASE_URL, ohne Volume) → warten auf uvicorn → curl `/api/health` (200) + `/api/angebot/health` + `/api/praesentation/health` (200 ODER definierte graceful-503-Antwort) → Engine-Import-Marker im Log (`ENGINE_OK` true/Fehlertext leer) → node reconstruct.js-Probe im Container (`node engine/spike-pptxgenjs/reconstruct.js --help` o.ä. Smoke) → Container weg, exit 0/1
2. Keine GNU-only-Tools (kein `timeout` — macOS!); Polling-Loop max ~40s
3. Gate lokal ausführen — grün
4. `docs/sprint-11/SIM-GATE.md`: was das Gate prüft, wie es vor Cutover läuft

**Output:**
- `tools/sim_gate.sh`
- `docs/sprint-11/SIM-GATE.md`

**Verify:** (EARS 2 + 3 aus FEATURE-005)
```bash
test -x tools/sim_gate.sh && ! grep -qw 'timeout' tools/sim_gate.sh && \
./tools/sim_gate.sh && echo "SIM-GATE GRUEN"
```

**Trace:** R-NF-1, R-NF-2 · WP M2 (Gate) · [[KOCHFABRIK-FEATURE-005]]
**Blocked-by:** US-049

---

## Phase 4: Cutover-Vorbereitung

### US-051: Cutover-Runbook + Live-Verify-Skript

**Context:** M3 aus ADR-002 — der Merge nach master ist der Cutover;
er braucht ein Runbook (Schritte, Gates, Rollback) und ein Skript, das
die Live-Instanz vor UND nach dem Cutover deterministisch prüft.

**Input (Vorbedingungen):**
- US-050 DONE (Sim-Gate grün), US-044 DONE (Backup liegt)
- Live: https://kochfabrik-studio.flinkbase.com (Health-Routen)

**Task:**
1. `tools/live_verify.sh`: curl gegen Live-Health-Routen (`/api/health` 200 + `db:true`, angebot/praesentation-health, slidesuche-search Status-Check mit Auth-tolerantem Erwartungswert 200/401), kompakte OK/FAIL-Ausgabe, exit 0/1
2. Skript JETZT gegen die laufende Prod ausführen (Pre-Cutover-Referenz) — Ergebnis ins Runbook
3. `docs/sprint-11/CUTOVER-RUNBOOK.md`: Reihenfolge (Backup ✓ → Sim-Gate ✓ → PR-Merge = Deploy → `live_verify.sh` → bei FAIL: Rollback via Coolify altes Image re-deployen, Befehl/UI-Pfad dokumentiert), Verantwortlich: /sprint-review-Schritt
4. Hinweis im Runbook: Coolify behält alte Revision bis Health grün (Rolling)

**Output:**
- `tools/live_verify.sh`
- `docs/sprint-11/CUTOVER-RUNBOOK.md`

**Verify:** (EARS 4 aus FEATURE-005, Pre-Cutover-Teil)
```bash
test -x tools/live_verify.sh && ./tools/live_verify.sh && \
grep -qi 'rollback' docs/sprint-11/CUTOVER-RUNBOOK.md && \
grep -q 'sim_gate' docs/sprint-11/CUTOVER-RUNBOOK.md
```

**Trace:** R-NF-2 · WP M3 · [[KOCHFABRIK-FEATURE-005]]
**Blocked-by:** US-044, US-050

---

## Dependency Graph

```
US-044 ─────────────────────────────┐
US-045 ──▶ US-047 ──▶ US-048 ──▶ US-049 ──▶ US-050 ──▶ US-051
US-046 ──────────────┘ (Gate)
```

## Summary

| Phase | Stories | Parallelisierbar | Kritischer Pfad |
|---|---|---|---|
| 1: Vorbedingungen | US-044, US-045, US-046 | ja (3 parallel) | US-045 |
| 2: Monorepo (1 Branch) | US-047, US-048 | nein (sequentiell) | ja |
| 3: Deploy-Vorbereitung | US-049, US-050 | nein (sequentiell) | ja |
| 4: Cutover-Vorbereitung | US-051 | — | ja |
| **Total** | **8 Stories** | **Wave 1: 3 parallel** | |
