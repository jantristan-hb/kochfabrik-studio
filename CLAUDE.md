# CLAUDE.md — kochfabrik-studio

> Projekt-Kontext für Claude-Agents. Stand: Sprint 12 DONE (2026-06-11). Dieses
> File ist die erste Anlaufstelle für jeden neuen Agent.

## Session-Start

Vor jeder Arbeit in dieser Reihenfolge lesen:

1. **CLAUDE.md** (dieses File) — Stack, Befehle, Architektur-Regeln
2. **PROGRESS.md** — Status, Sprint-Tabelle, aktueller Zustand
3. **REQUIREMENTS.md** — Produkt-These + Anforderungen (informelle SoT)
4. **docs/epics/README.md** — Roadmap + Work-Packages (EPIC-001…010)
5. **docs/sprint-12/** — aktueller Sprint: `USER-STORIES.md`, `EXECUTE.md`,
   `TRACEABILITY.md`, die FEATURE-Specs (EARS/Pitfalls/Boundaries)

## Tech Stack

| Schicht | Technologie |
|---------|-------------|
| Web-Framework | FastAPI auf Uvicorn (`backend/app.py`, ASGI) |
| Persistenz | PostgreSQL 16 + SQLAlchemy 2 (async) + Alembic-Migrationen |
| DB-Zugriff | `backend/db.py` (async engine), graceful via `DB_OK`/`DB_ERR` |
| Engine-Runtime | Python-Runtime in `engine/scripts/` (13 Module): Angebots-/Deck-Pipeline |
| Deck-Render | `pptxgenjs` (Node) in `engine/spike-pptxgenjs/`, via `reconstruct.js` |
| Dokument-Tooling | LibreOffice + poppler im Container (PPTX→PDF, PDF-Diff) |
| Korpus | `engine/data/pgbundle.npz` — read-only Snapshot (emb float32 N×768 + Metadaten), ADR-003 |
| Auth | HMAC-Session-Cookie (`kf_sess`), `KF_SESSION_SECRET` + `KF_USERS` |
| Deploy | Coolify auf flinkbase (`https://kochfabrik-studio.flinkbase.com`) |

Engine ist repo-intern (Monorepo via git-subtree, ADR-002, eigene Historie) —
direkt hier entwickeln, kein separates Engine-Repo mehr.

## Befehle

### Setup + Tests

```bash
# venv (liegt unter tools/.venv) + Tests
python -m venv tools/.venv
tools/.venv/bin/pip install -r requirements.txt
tools/.venv/bin/python -m pytest backend/tests -q
```

### Gates (vor Cutover/Merge)

```bash
# 1) Sim-Gate — Container-Smoke OHNE DB/Volume (Build + Health + Engine +
#    reconstruct.js). exit 0 = grün, exit 1 = Cutover BLOCKIEREN.
./tools/sim_gate.sh

#    Optional mit Alembic-Container-Abnahme (Wegwerf-Postgres :15432):
SIM_GATE_DB=1 ./tools/sim_gate.sh

# 2) Live-Verify — Health-Routen der Prod-Instanz (vor + nach Cutover).
#    /api/health → 200/db:true, Modul-Routen → 401 (Route lebt).
./tools/live_verify.sh
```

### Container bauen

```bash
docker build -t kf-studio .
```

### Deploy — KEIN Auto-Deploy

Es gibt **KEINEN Deploy-Webhook**. Ein Merge nach master deployt NICHTS von
allein. Deploy = **manueller Coolify-API-Trigger**:

```bash
source ~/work/.env
curl "https://coolify.flinkbase.com/api/v1/deploy?uuid=yu2fqx0twmtqcp6zyx2e59si&force=true" \
  -H "Authorization: Bearer $COOLIFY_TOKEN"
```

Ablauf + Rollback: `docs/sprint-11/CUTOVER-RUNBOOK.md`.

### Backup / Restore

Cron-Backup (Host) + Restore-Probe + Runbook: `docs/ops/BACKUP-CYCLE.md` + `docs/ops/RESTORE-RUNBOOK.md`.
Täglicher Host-Cron (`pg_dump | gzip` → `/data/backups/kf-studio-pg/`, Rotation 14 Tage).

## Architektur-Regeln

- **Router-Layout:** Endpoints liegen in `backend/routers/` (4 Router: `auth`,
  `bildgenerator`, `angebot`, `praesentation`). `backend/app.py` bleibt schlank
  (~90 Z.) und montiert nur. Geteilter Kern (Auth-/Cookie-Helfer, Bild-Kern,
  Kategorie-/Prompt-Konstanten, Engine-Import) lebt in `backend/engine_glue.py`
  — Router importieren von dort, **nie** auf `app.py` (kein Import-Zyklus).
- **EINE Bundle-Schicht:** Das pgbundle wird ausschließlich über
  `engine/scripts/bundle.py` (`load()`/`rank()`) gelesen — `np.load` auf
  `pgbundle.npz` existiert genau EINMAL (dort). **Nie** ein eigenes `np.load`
  oder eine eigene L2-Normalisierung an anderer Stelle (ADR-003, Drift-Risiko).
- **Runtime vs. Tooling:** `engine/scripts/` (13 Module) = Laufzeit, lädt im
  Container. `engine/tooling/` (33 Module) = Build-/Analyse-Werkzeuge, läuft
  NICHT zur Laufzeit. Import-Graph-Regel: `scripts/` darf **nie** aus `tooling/`
  importieren (sonst zieht die Runtime Build-Abhängigkeiten). Details:
  `docs/sprint-12/TOOLING-SPLIT.md`.
- **Graceful Degradation:** Engine- und DB-Fehlen brechen den Boot nicht.
  `ENGINE_OK`/`ENGINE_ERR` (`engine_glue.py`) und `DB_OK`/`DB_ERR` (`db.py`)
  melden den Zustand; Health-Routen liefern `engine`/`db`-Flags, Endpoints
  degradieren statt zu crashen (Sim-Gate fährt genau diesen Worst-Case).
- **Read-only Daten:** `engine/data/cache` und `engine/data/pgbundle.npz`
  sind read-only Korpus-Artefakte — zur Laufzeit nicht beschreiben.
- **master = Prod-Disziplin:** NIE auf master pushen. Feature-Branch → Draft-PR
  → Review → Merge. Verify (Tests + Gates) vor DONE.

## Sprint-Abschluss

```
/sprint-review kochfabrik
```

Markiert NIE einen Sprint als DONE, solange nicht alle Änderungen committed +
gepusht sind.

## Sprints

| # | Epic / Fokus | Status |
|---|--------------|--------|
| 1 | EPIC-001 Persistenz/Multi-Tenant — Fundament | DONE |
| 2 | EPIC-001 Sheet-/Chat-History/Restore | DONE |
| 3 | EPIC-001 CRM-Anbindung | DONE |
| 4 | EPIC-001 Multi-Tenant-Abschluss | DONE |
| 5 | EPIC-002 WYSIWYG-Präsentationsgenerator v2 — Start | DONE |
| 6 | EPIC-002 v2 Editor-Kern | DONE |
| 7 | EPIC-002 v2 Kohärenz + Chat (Offer-Context-Merge, Anthropic) | DONE |
| 8 | EPIC-002 v2 Frontend-Switch (Nav auf /praesentation_v2/) | DONE |
| 9 | EPIC-002 v2 Refactor (Legacy-Archiv, Backend unverändert für Rollback) | DONE |
| 10 | EPIC-003 Analyse-Fundament (25 Findings, ADR-001…003) | DONE |
| 11 | EPIC-004 Monorepo-Schnitt M1–M3 (subtree, Cutover live, Gates) | DONE |
| 12 | EPIC-004-Abschluss M4–M7 + EPIC-009 (Router-Split, Bundle-Schicht, Tooling-Split, Alembic, Backup) | DONE (2026-06-11) |
