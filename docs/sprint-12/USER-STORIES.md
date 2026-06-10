# USER-STORIES — kochfabrik Sprint 12

> **Typ:** US. Geschnitten aus [[EPIC-004]] (M4–M7) + [[EPIC-009]]
> (B1–B3). 9 Stories (über Soll-8, begründet: Epic-Abschluss EPIC-004 +
> komplettes EPIC-009 + Carry-Over — alle klein geschnitten).
> Verhalten strikt erhalten; Gate = Sprint-11-Suite (112 Tests, 0 failed).

## Story-Gate (PFLICHT)

- [x] ≤ 5 Task-Schritte · ≤ 3 Output-Einträge · Verify deterministisch
- [x] Verify bildet ein EARS-Kriterium ab · Null Platzhalter
- [x] Blocked-by explizit · Trace vorhanden

## Boundaries (sprintweit)

- ✅ **Always:** Feature-Branches; git mv; lokale Wegwerf-Postgres
  (Ports 15432/15433, NIE 5432/5434); Host-SSH read-only; die in
  US-057/US-060 EXPLIZIT genannten Host-/GitHub-Writes; venv-Tests;
  Sim-Gate lokal
- ⚠️ **Ask-first (headless → BLOCKED):** jede beobachtbare
  Verhaltensänderung; andere Host-/Coolify-/GitHub-Writes als die
  explizit genannten; neue Runtime-Dependency
- 🚫 **Never:** master pushen (Deploy nur via Review + manuellem
  Trigger); Prod-DB-Writes; Restore gegen Prod; `engine/data/` +
  Korpus-Volume ändern; Dumps/Secrets committen; lokale Alt-Ordner
  (inkl. `../pptxgenerator_v2`) verschieben/löschen

---

## Phase 1: Backup-Zyklus (Wave 1 — parallel zur Kette startbar)

### US-052: Täglichen Backup-Zyklus auf dem Host einrichten

**Context:** Sprint 11 lieferte einen Einmal-Dump; EPIC-009/B1
verlangt den automatischen Zyklus mit Rotation (R-BAK-1).

**Input (Vorbedingungen):**
- Host-Zugang `ssh -i ~/.ssh/hetzner_id root@188.245.110.5`
- DB-Container `tqg2xzsx9zau68jlhmuwyffj` (kf-studio-pg, DB/User kfstudio)

**Task:**
1. Auf dem Host (explizit erlaubte Writes): `/data/backups/kf-studio-pg/` anlegen + Backup-Skript `/data/backups/kf-studio-pg/backup.sh` (`/usr/bin/docker exec tqg… pg_dump -U kfstudio kfstudio | gzip > …/kfstudio-$(date +%F).sql.gz` + Rotation `find … -name 'kfstudio-*.sql.gz' -mtime +14 -delete`)
2. `/etc/cron.d/kf-studio-pg-backup` anlegen (täglich 03:30, root, PATH gesetzt, Newline am Ende!)
3. Manuellen Testlauf ausführen → heutige Dump-Datei entsteht, `gzip -t` OK, ≥5 `CREATE TABLE`
4. Off-Host-Pull dokumentieren (scp-Befehl nach `…/kochfabrik/backups/`) + einmal ausführen
5. `docs/ops/BACKUP-CYCLE.md` schreiben (Zyklus, Rotation, Pull, Verify-Befehle)

**Output:**
- `docs/ops/BACKUP-CYCLE.md`
- (Host: backup.sh + cron.d-Eintrag + erster Zyklus-Dump; lokal: gepullter Dump off-repo)

**Verify:** (EARS 1 aus FEATURE-007)
```bash
test -s docs/ops/BACKUP-CYCLE.md && \
ssh -i ~/.ssh/hetzner_id root@188.245.110.5 "test -f /etc/cron.d/kf-studio-pg-backup && ls /data/backups/kf-studio-pg/kfstudio-*.sql.gz | head -1 && gzip -t /data/backups/kf-studio-pg/kfstudio-*.sql.gz" && \
ls "../backups/"kfstudio-*.sql.gz >/dev/null
```

**Trace:** R-BAK-1 · WP B1 · [[KOCHFABRIK-FEATURE-007]]
**Blocked-by:** —

---

## Phase 2: Code-Ordnungs-Kette (SEQUENTIELL — ein Branch `sprint-12-code`)

### US-053: Router auth + bildgenerator aus app.py extrahieren

**Context:** app.py (936 Z.) mischt 4 Domänen; M4 beginnt mit den
zwei kleinsten, klar abgegrenzten (Login/OAuth, Bildgenerator).

**Input (Vorbedingungen):**
- Branch `sprint-12-code` von master; Anker FEATURE-006 §11

**Task:**
1. Vorher: `app.routes`-Inventar dumpen (Pfad+Methode, sortiert) → `/tmp/routes_before.txt`; Suite grün beweisen
2. `backend/routers/__init__.py` + `backend/routers/auth.py` (login/logout/oauth/* inkl. Helper) + `backend/routers/bildgenerator.py` (cats/image inkl. Prompt-Konstanten) — Code 1:1 verschieben, APIRouter ohne Prefix-Änderung
3. Gemeinsam Genutztes (Auth-Helper/_owner, Engine-Glue) bei Bedarf nach `backend/engine_glue.py` — keine Router→app-Importe (Pitfall 2)
4. app.py: include_router; Routen-Inventar nachher == vorher (diff leer); Suite + `pytest backend/tests -q` 0 failed
5. Commit `refactor(backend): US-053 Router auth + bildgenerator` + `Closes #<issue>` + Footer

**Output:**
- `backend/routers/` (__init__.py, auth.py, bildgenerator.py)
- `backend/app.py` (geschrumpft)
- ggf. `backend/engine_glue.py`

**Verify:** (EARS 1 aus FEATURE-006, Teil 1)
```bash
tools/.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from backend.app import app
rs = sorted(f'{sorted(r.methods or [\"GET\"])} {r.path}' for r in app.routes)
open('/tmp/routes_after.txt','w').write('\n'.join(rs))" && \
diff /tmp/routes_before.txt /tmp/routes_after.txt && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```

**Trace:** R-REF-4 · WP M4 · [[KOCHFABRIK-FEATURE-006]]
**Blocked-by:** —

---

### US-054: Router angebot + praesentation extrahieren (app.py <200 Z.)

**Context:** M4-Abschluss — die zwei großen Domänen folgen; app.py
wird reine Komposition.

**Input (Vorbedingungen):**
- US-053 DONE (gleicher Branch); Routen-Inventar-Verfahren etabliert

**Task:**
1. `backend/routers/angebot.py` (angebot/*, angebote, stats, kunden, kunde/{id} inkl. _ang2md/_owner-Nutzung)
2. `backend/routers/praesentation.py` (praesentation/* inkl. _praes_guard/_assemble_src/_assemble_md, PPTX_PGSHIM-Env bleibt identisch)
3. app.py: nur Setup/Middleware/health/statics/include_router — unter 200 Zeilen
4. Routen-Inventar-Diff leer; volle Suite 0 failed; Commit + Push wie gehabt

**Output:**
- `backend/routers/angebot.py`, `backend/routers/praesentation.py`
- `backend/app.py` (<200 Z.)

**Verify:** (EARS 1 aus FEATURE-006, komplett)
```bash
test "$(wc -l < backend/app.py)" -lt 200 && \
diff /tmp/routes_before.txt /tmp/routes_after.txt && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```
(routes_after vor dem diff frisch erzeugen wie in US-053.)

**Trace:** R-REF-4 · WP M4 · [[KOCHFABRIK-FEATURE-006]]
**Blocked-by:** US-053

---

### US-055: Eine Bundle-Schicht (ADR-003) — pg_shim + Slidesuche konsolidieren

**Context:** pgbundle.npz wird 2× geladen/normalisiert/gerankt
(F-E-03); ADR-003 verlangt genau EINE Schicht.

**Input (Vorbedingungen):**
- US-054 DONE; Anker: `engine/scripts/pg_shim.py`, `backend/slidesuche.py:96-115`

**Task:**
1. Vorher-Gold: fixe Query gegen Slidesuche-ANN + pg_shim-Ranking dumpen (Deck/Page-Reihenfolgen) → `/tmp/ranking_before.json`
2. `engine/scripts/bundle.py`: load(pgbundle)+Normalisierung+Cosinus-ANN (Top-K parametrisch) + Spalten-Vertrag — einzige `np.load`-Stelle für pgbundle
3. `pg_shim.py` auf bundle.py umstellen (Query-Shapes unverändert); `backend/slidesuche.py`: `_bundle()`/eigene ANN ersetzen durch bundle-Aufrufe
4. Nachher-Gold == Vorher-Gold (bit-identische Reihenfolgen); Suite 0 failed; grep beweist: `np.load` auf pgbundle nur in bundle.py

**Output:**
- `engine/scripts/bundle.py`
- `engine/scripts/pg_shim.py`, `backend/slidesuche.py` (konsolidiert)

**Verify:** (EARS 2 aus FEATURE-006)
```bash
test "$(grep -rl "np.load" --include='*.py' backend engine/scripts | xargs grep -l pgbundle | wc -l | tr -d ' ')" = "1" && \
diff /tmp/ranking_before.json /tmp/ranking_after.json && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```

**Trace:** R-REF-3, R-QA-3 (F-E-03) · WP M5 · [[KOCHFABRIK-FEATURE-006]] · [[KOCHFABRIK-ADR-003]]
**Blocked-by:** US-054

---

### US-056: Engine-Tooling-Split (Runtime vs. Build-Tools)

**Context:** 45 Skripte gemischt; M5 trennt Runtime (vom Backend/
assemble erreicht) von Einmal-/Build-Tooling.

**Input (Vorbedingungen):**
- US-055 DONE; FEATURE-006 §12 Pitfall 3 (Import-Analyse!)

**Task:**
1. Transitiven Erreichbarkeits-Graph bestimmen: Start = backend/*.py + backend/routers/*.py + engine/scripts/assemble.py + render-relevante subprocess-Strings (grep nach Skriptnamen in .py UND tools/*.sh!) — Liste Runtime vs. Tooling dokumentieren
2. `git mv` der Tooling-Skripte nach `engine/tooling/` (inkl. __init__-frei, Skripte bleiben standalone)
3. Interne sys.path-/Import-Annahmen der verschobenen Tools prüfen (sie importieren teils aus scripts/ — `sys.path`-Zeile ergänzen, KEINE Logikänderung)
4. py_compile über scripts/ + tooling/; Suite 0 failed; `./tools/sim_gate.sh` grün (Runtime vollständig!)
5. Klassifikations-Tabelle in `docs/sprint-12/TOOLING-SPLIT.md`

**Output:**
- `engine/tooling/` (verschobene Skripte)
- `docs/sprint-12/TOOLING-SPLIT.md`

**Verify:** (EARS 3 aus FEATURE-006)
```bash
test -d engine/tooling && test -s docs/sprint-12/TOOLING-SPLIT.md && \
for f in engine/scripts/*.py engine/tooling/*.py; do tools/.venv/bin/python -m py_compile "$f" || exit 1; done && \
./tools/sim_gate.sh
```

**Trace:** R-REF-4 · WP M5 · [[KOCHFABRIK-FEATURE-006]]
**Blocked-by:** US-055

---

### US-057: Alembic-Container-Abnahme (M6) — rc=0 mit echter DB

**Context:** alembic.ini ist seit Sprint 11 im Image; der Beweis
„Migrations-Schritt rc=0 + Stamp" mit erreichbarem Postgres fehlt
(F-S-01-Abschluss).

**Input (Vorbedingungen):**
- US-056 DONE (Image-Stand final); Docker lokal

**Task:**
1. Lokalen Wegwerf-Postgres starten (Port 15432, postgres:16-alpine, DB kfstudio)
2. App-Image bauen + Container mit `DATABASE_URL` auf den Wegwerf-PG starten
3. Beweise sammeln: migrate-Step-Log enthält Stamp/„Schema OK", rc=0 (kein graceful-255-Pfad); `alembic_version` enthält head (psql-Check)
4. Check als Block in `tools/sim_gate.sh` ergänzen (optional aktivierbar via `SIM_GATE_DB=1`) + `docs/sprint-12/ALEMBIC-VERIFY.md` (Protokoll); Wegwerf-Container weg

**Output:**
- `tools/sim_gate.sh` (DB-Block)
- `docs/sprint-12/ALEMBIC-VERIFY.md`

**Verify:** (EARS 4 aus FEATURE-006)
```bash
grep -q 'SIM_GATE_DB' tools/sim_gate.sh && \
SIM_GATE_DB=1 ./tools/sim_gate.sh && \
grep -q 'alembic_version' docs/sprint-12/ALEMBIC-VERIFY.md
```

**Trace:** R-QA-3 (F-S-01) · WP M6 · [[KOCHFABRIK-FEATURE-006]]
**Blocked-by:** US-056

---

## Phase 3: Abschluss (Wave 3 — parallel, nach Kette bzw. US-052)

### US-058: Restore-Probe + Restore-Runbook (B2/B3)

**Context:** Backups existieren, Restore ist ungeprobt — B3 verlangt
den realen Durchstich; B2 die Korpus-Wiederaufbau-Doku.

**Input (Vorbedingungen):**
- US-052 DONE (Zyklus-Dump liegt lokal); US-056 DONE (Tooling-Pfade final)

**Task:**
1. Jüngsten gepullten Zyklus-Dump in lokalen Wegwerf-Postgres (Port 15433) restoren (`gunzip -c | psql`)
2. Beweise: 5 Kern-Tabellen existieren, Rowcounts > 0 wo erwartet (offer/customer/app_user), `alembic_version` vorhanden — Protokoll mit Befehlen+Outputs
3. Korpus-B2 dokumentieren: originär (cache-PDF-Assets, Host-Volume + Sprint-11-Inventar) vs. regenerierbar (pgbundle via Build-Korpus-DB, Previews via `engine/tooling/render_previews.py`) — konkrete Befehle
4. `docs/ops/RESTORE-RUNBOOK.md` (DB-Restore + Korpus-Wiederaufbau + Proben-Protokoll 2026-06-10); Wegwerf-Container weg

**Output:**
- `docs/ops/RESTORE-RUNBOOK.md`

**Verify:** (EARS 2+3 aus FEATURE-007)
```bash
test -s docs/ops/RESTORE-RUNBOOK.md && \
grep -q 'seq_counter' docs/ops/RESTORE-RUNBOOK.md && \
grep -qi 'regenerierbar' docs/ops/RESTORE-RUNBOOK.md && \
grep -qE 'Proben-Protokoll' docs/ops/RESTORE-RUNBOOK.md
```

**Trace:** R-BAK-2, R-BAK-3 · WP B2, B3 · [[KOCHFABRIK-FEATURE-007]]
**Blocked-by:** US-052, US-056

---

### US-059: Projekt-CLAUDE.md anlegen (M7)

**Context:** Es gibt kein Projekt-CLAUDE.md; jeder Agent rekonstruiert
Stack/Befehle/Regeln aus README+PROGRESS. M7 dokumentiert den
End-Stand des Sprints (deshalb NACH der Kette).

**Input (Vorbedingungen):**
- US-057 DONE (Code-/Gate-Endstand); FEATURE-008 §4-Gliederung

**Task:**
1. `CLAUDE.md` nach FEATURE-008 §4: Session-Start, Stack-Tabelle, Befehle (venv-Test, sim_gate [+SIM_GATE_DB], live_verify, docker build, **manueller Deploy-Trigger** + Runbook-Verweis), Architektur-Regeln (Router-Layout, EINE Bundle-Schicht, graceful-Muster, data/cache read-only, master=Deploy-Disziplin), Sprint-Tabelle 1–12
2. Pfad-Stichproben gegen Codebase (jeden genannten Pfad/Befehl einmal ausführen bzw. ls)
3. README-Drift-Check: Verweis auf CLAUDE.md ergänzen

**Output:**
- `CLAUDE.md`
- `README.md` (Verweis)

**Verify:** (EARS 1 aus FEATURE-008)
```bash
test -s CLAUDE.md && ! grep -q '{…}' CLAUDE.md && \
grep -q 'sim_gate.sh' CLAUDE.md && grep -q 'live_verify.sh' CLAUDE.md && \
grep -qi 'kein.*auto.*deploy\|manuell.*deploy\|deploy.*manuell' CLAUDE.md && \
grep -q 'backend/routers' CLAUDE.md
```

**Trace:** R-REF-5 · WP M7 · [[KOCHFABRIK-FEATURE-008]]
**Blocked-by:** US-057

---

### US-060: Engine-Repo read-only archivieren

**Context:** ADR-002-Konsequenz — nach dem Monorepo-Cutover darf
niemand mehr versehentlich ins alte Engine-Repo committen.

**Input (Vorbedingungen):**
- US-056 DONE (keine Engine-Repo-Rückgriffe mehr nötig)
- `../pptxgenerator_v2` @ main, clean

**Task:**
1. Engine-Repo-README: Archiv-Hinweis an den Anfang („⚠️ ARCHIVIERT 2026-06-10 — Code lebt im Monorepo jantristan-hb/kochfabrik-studio unter engine/, Historie via subtree erhalten") — committen + push origin main
2. `gh repo archive jantristan-hb/pptxgenerator_v2 -y`
3. Verifizieren: isArchived true; lokalen Ordner NICHT anfassen (Jan-Entscheid offen)

**Output:**
- (Engine-Repo: README-Commit + Archived-Status)

**Verify:** (EARS 2 aus FEATURE-008)
```bash
gh repo view jantristan-hb/pptxgenerator_v2 --json isArchived -q '.isArchived' | grep -q true && \
gh api repos/jantristan-hb/pptxgenerator_v2/readme -q '.content' | base64 -d | head -5 | grep -qi archiviert
```

**Trace:** R-REF-1 (Abschluss) · WP M1-Konsequenz/ADR-002 · [[KOCHFABRIK-FEATURE-008]]
**Blocked-by:** US-056

---

## Dependency Graph

```
US-052 ──────────────────────────────┐
US-053 ─▶ US-054 ─▶ US-055 ─▶ US-056 ─▶ US-057 ─▶ US-059
                              ├─▶ US-058 (auch ◀── US-052)
                              └─▶ US-060
```

## Summary

| Phase | Stories | Parallelisierbar | Kritischer Pfad |
|---|---|---|---|
| 1: Backup-Zyklus | US-052 | parallel zur Kette | nein |
| 2: Code-Kette (1 Branch) | US-053…US-057 | nein (sequentiell) | ja |
| 3: Abschluss | US-058, US-059, US-060 | ja (3 parallel) | US-059 |
| **Total** | **9 Stories** | Wave 1: 2 · End-Wave: 3 | |
