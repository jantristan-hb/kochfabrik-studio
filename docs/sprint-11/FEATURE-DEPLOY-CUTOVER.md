---
key: KOCHFABRIK-FEATURE-005
status: approved
title: "Deploy-Cutover: Backup, Dockerfile, Sim-Gate, Live-Verify"
created: 2026-06-09
project: kochfabrik
---

# KOCHFABRIK-FEATURE-005: Deploy-Cutover (M2 + M3 + Backup)

> **Typ:** FEATURE (Brownfield-Delta). Sprint 11 / EPIC-004, WPs M2 + M3
> + vorgezogenes B1-Element (EPIC-009, Cross-Epic-Pull — Sicherheits-
> Auflage: master-Push = Auto-Deploy auf Prod).

## 1. Vision

Der Monorepo-Stand deployt ohne Downtime: Vor dem Cutover existiert
ein verifiziertes Backup (Postgres-Dump off-host + Korpus-Volume-
Inventar), das neue Image wird lokal im Sim-Gate bewiesen (Build +
Container-Smoke), und der Cutover hat ein Runbook mit Live-Verify
und Rollback-Pfad.

## 3. Datenmodell

Entfällt.

## 4. Flows (aus ADR-002 Migrationsplan)

```
US-044 Backup (pg_dump off-host + Volume-Inventar)   [jederzeit, vor Merge]
US-049 Dockerfile: COPY engine (neues Layout) + COPY alembic.ini
US-050 Sim-Gate: docker build + Container-Smoke (Engine-Import,
       Health-Routen via uvicorn im Container, reconstruct-Probe)
US-051 Runbook + Live-Verify-Skript (vor UND nach Cutover lauffähig)
→ Cutover selbst = PR-Merge nach master im /sprint-review-/integrate-
  Schritt, NACH grünem Sim-Gate. Coolify baut, Volume bleibt gemountet.
```

**Infra-Fakten (verifiziert 2026-06-09):** Coolify-API
`https://coolify.flinkbase.com` (`COOLIFY_TOKEN` in `~/work/.env`),
App-UUID `yu2fqx0twmtqcp6zyx2e59si`, Server-Volume
`/data/coolify/applications/{UUID}/cache` (Directory Mount auf
`data/cache`, autoritativ), DB-Service `kf-studio-pg`
(UUID `tqg2xzsx9zau68jlhmuwyffj`). SSH-Zugang zum Host: NICHT in
`~/.ssh/config` — Discovery über `~/work/99 Jan/settings/INFRA.md` /
`SOVEREIGN-COOLIFY.md`; ohne Zugang → BLOCKED (kein Workaround basteln).

## 7. API-Skizze

Entfällt — bestehende Health-Endpoints werden nur verifiziert:
`GET /api/health` · `GET /api/angebot/health` ·
`GET /api/praesentation/health` · `POST /api/slidesuche/search`.

## 8. Akzeptanzkriterien (EARS)

1. WHEN das Backup gelaufen ist THE SYSTEM SHALL einen pg_dump von
   `kf-studio-pg` mit Integritäts-Check (pg_restore --list bzw.
   gzip -t + Tabellen-Marker) an einem Off-Host-Ort abgelegt haben
   und ein Korpus-Volume-Inventar (Deck-Count, Gesamtgröße,
   Stichproben-Checksummen) dokumentieren.
2. WHEN das Monorepo-Image lokal gebaut wird THE SYSTEM SHALL den
   Build ohne vendor.sh abschließen und der Container-Smoke SHALL
   Engine-Import (`ENGINE_OK`-Pfad), alle drei Modul-Health-Routen
   und eine reconstruct.js-Probe bestehen (Sim-Gate exit 0).
3. IF das Sim-Gate fehlschlägt THEN THE SYSTEM SHALL den Merge nach
   master blockieren (Gate ist Vorbedingung im Runbook + PR-Text).
4. WHEN der Cutover vollzogen ist THE SYSTEM SHALL per Live-Verify-
   Skript alle Health-Routen der neuen Revision grün zeigen; IF nicht
   THEN das Runbook SHALL den Rollback (Re-Deploy voriges Image via
   Coolify) als ausführbaren Schritt enthalten.

## 9. Abgrenzung (Nicht-Teil)

- Automatisierter Backup-ZYKLUS (B1 vollständig) → EPIC-009, Sprint 12
- Open Sans ins Image → EPIC-005/T3 (NICHT hier — ein Umbau pro Sprint)
- CI-Verankerung des Sim-Gates → EPIC-008/C1, Sprint 13

## 9a. Boundaries (3-Tier)

- ✅ **Always:** lokaler docker build; read-only-Zugriffe auf Coolify-API
  (GET); pg_dump LESEND; Dateien unter `tools/`, `docs/sprint-11/`,
  `Dockerfile` (Branch!)
- ⚠️ **Ask-first (headless: BLOCKED):** JEDER schreibende Coolify-API-
  Call (deploy/restart/env); SSH-Befehle die nicht read-only sind;
  Backup-Ablage außerhalb `~/work/02 AKARA Solutions GmbH/kochfabrik/backups/`
- 🚫 **Never:** Push/Merge auf master (Cutover macht /sprint-review nach
  Sim-Gate, nicht der Agent); Volume-Inhalte ändern/löschen; DB-Writes;
  Secrets (COOLIFY_TOKEN, Dumps) ins Repo committen

## 10. Abgrenzung zum Ist

- Dockerfile `COPY engine ./engine` zeigt auf vendored `engine/phase0/…`
  → neues flaches Layout; zusätzlich fehlt `COPY alembic.ini` (F-S-01,
  Migrations-Voraussetzung — voller M6-Fix in Sprint 12)
- vendor.sh-Sim-Gate (Schritt 4/4) entfällt mit vendor.sh → eigenes,
  wiederverwendbares `tools/sim_gate.sh`
- Kein Backup-Stand existiert → Erst-Backup + Inventar als Cutover-Gate

## 11. Implementierungs-Anker (Ist)

`Dockerfile` (python:3.12-slim + nodejs + libreoffice + poppler;
CMD migrate→uvicorn), `vendor.sh:94-160` (Sim-Gate-Logik + Volume-
Hinweise + Deploy-Call als Vorlage), `backend/migrate.py`,
`alembic.ini` (Root), `~/work/.env` (`COOLIFY_TOKEN`),
`~/work/99 Jan/settings/INFRA.md` (Host-Zugang, Discovery).

## 12. Bekannte Pitfalls

1. **master-Push = sofortiger Prod-Deploy** — ALLES auf Branches; der
   Merge ist der Cutover und passiert erst nach grünem Sim-Gate.
2. **`timeout` existiert nicht auf macOS** — Skripte ohne GNU-coreutils-
   Annahmen schreiben (Sprint-10-RETRO-Learning).
3. **Sim-Gate ohne Volume-Simulation** — im Container fehlt der
   Korpus-Voll-Cache; Smoke muss die graceful-503-Pfade als OK werten
   (wie heute: `_korpus_ok()`-Gate), nicht auf 200 bestehen wo Prod
   ein Volume hat.
4. **Dump mit Secrets im Repo** — Backups + Token bleiben außerhalb
   des Git-Trees (backups/-Ordner neben den Repos, nicht committen).
5. **docker auf dem Mac nicht gestartet** — Pre-Check `docker info`,
   sonst BLOCKED statt kryptischem Build-Fehler.

## Referenzen
- implements → REQUIREMENTS R-NF-2, R-REF-1 (Deploy-Teil), R-BAK-1 (vorgezogen, Teil), R-BAK-2 (Inventar-Teil), R-NF-3
- depends_on → [[KOCHFABRIK-ADR-002]] Migrationsplan M1→M3 · [[KOCHFABRIK-FEATURE-004]]
- relates_to → [[EPIC-004]] WP M2, M3 · [[EPIC-009]] B1 (Cross-Epic-Pull, annotiert)

## Referenziert von
— USER-STORIES Sprint 11 (US-044, US-049, US-050, US-051)
