# ALEMBIC-VERIFY.md — Container-Migrate-Abnahme (US-057)

> **Story:** US-057 / Issue #38 — EPIC-004 / M6-Abnahme (F-S-01-Abschluss).
> **Datum:** 2026-06-11
> **Branch:** `sprint-12-code`

## Was bewiesen wird (EARS, FEATURE-006 §8 Nr. 4)

> WHEN der Container mit erreichbarem Postgres startet THE SYSTEM SHALL den
> Migrations-Schritt mit **rc=0** abschließen und **`alembic_version`** SHALL
> gestampt/aktuell sein (kein graceful `rc=255` mehr).

`alembic.ini` ist seit Sprint 11 im Image (Dockerfile `COPY alembic.ini .`),
der Container-CMD ruft `python -m backend.migrate` vor `uvicorn`. Bisher fehlte
der Beweis, dass dieser Schritt mit **erreichbarem** Postgres sauber durchläuft.
Hier ist er — kein App-Code wurde verändert (wir beweisen, wir fixen nicht).

## Protokoll (reproduzierbar via `SIM_GATE_DB=1 ./tools/sim_gate.sh`)

### 1. Wegwerf-Postgres (Port 15432 — NIE 5432/5434)

```bash
docker run -d --rm --name kf-sim-alembic-pg -p 15432:5432 \
  -e POSTGRES_USER=kfstudio -e POSTGRES_PASSWORD=kfstudio \
  -e POSTGRES_DB=kfstudio postgres:16-alpine
# Ready-Poll (bash-Schleife, kein GNU timeout): ready nach ~1s
```

### 2. App-Image bauen

```bash
docker build -t kf-studio-sim .        # rc=0
```

### 3. Migrate-Schritt gegen erreichbaren Postgres

DATABASE-URL-Schema exakt wie `backend/db.py` es erwartet
(`postgresql+asyncpg://`); `host.docker.internal` auf macOS erreicht den
gemappten Host-Port.

```bash
docker run --rm \
  -e DATABASE_URL="postgresql+asyncpg://kfstudio:kfstudio@host.docker.internal:15432/kfstudio" \
  kf-studio-sim python -m backend.migrate; echo rc=$?
```

**Log + rc:**

```
migrate: Schema OK (create_all, idempotent)
migrate: Alembic gestampt auf 0003_drop_praesentation_v2 (kein Re-Create)
rc=0
```

- **rc=0** (kein graceful `rc=255`) ✅
- **Log-Marker:** `Alembic gestampt auf 0003_drop_praesentation_v2` ✅
  (leere DB → STAMP-Pfad in `backend/migrate.py`; `HEAD = "0003_drop_praesentation_v2"`)

### 4. `alembic_version` vom Host prüfen (psql)

```bash
docker exec kf-sim-alembic-pg psql -U kfstudio -d kfstudio -c 'TABLE alembic_version;'
```

```
        version_num
----------------------------
 0003_drop_praesentation_v2
(1 row)
```

Schema vollständig angelegt (`create_all`):

```
 public | alembic_version | table | kfstudio
 public | app_user        | table | kfstudio
 public | chat_message    | table | kfstudio
 public | customer        | table | kfstudio
 public | offer           | table | kfstudio
 public | seq_counter     | table | kfstudio
```

### 5. Teardown

`--rm` + `cleanup`-Trap im Gate räumen den Wegwerf-Container ab. Nach dem Lauf
existiert `kf-sim-alembic-pg` nicht mehr.

## Verankerung im Gate

`tools/sim_gate.sh` hat einen optionalen Block (Schritt 1b), der **nur bei
`SIM_GATE_DB=1`** läuft: eigener Wegwerf-PG hoch → Migrate-Beweis (rc=0 +
Log-Marker + `alembic_version`-Check via psql) → PG runter. Ohne die Env-Var
ist das Verhalten unverändert. Kein GNU-`timeout`-Binary (macOS-Pitfall,
Sprint-10-RETRO) — Ready-Poll als reine bash-Schleife mit `sleep`.

**Gate-Ergebnis (`SIM_GATE_DB=1 ./tools/sim_gate.sh`):** `GATE_RC=0`

```
✅ Wegwerf-Postgres ready (nach 1s)
✅ Alembic-Abnahme: migrate rc=0, alembic_version=0003_drop_praesentation_v2
…
SIM-GATE GRUEN — Container lebt (Build + Health + Engine + reconstruct).
```
