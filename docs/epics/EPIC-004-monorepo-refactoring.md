---
id: EPIC-004
title: "Monorepo & Refactoring (Verhalten strikt erhalten)"
status: IN_PROGRESS
created: 2026-06-09
project: kochfabrik-studio
sprints: [11, 12]
---

# EPIC-004: Monorepo & Refactoring

> **Typ:** EPIC. Klammer über Sprints — kein Detail-Spec. `/sprint-plan`
> schneidet die WPs in Stories. Status: `OPEN → IN_PROGRESS → DONE`.

## Beschreibung

kochfabrik-studio und pptxgenerator_v2 sind heute zwei Repos, verbunden
über `vendor.sh` (~13 MB Engine-Kopie + Container-Pfad-Sim-Gate) —
jede Engine-Änderung erfordert Doppel-Pflege. Dazu gewachsene Struktur:
`backend/app.py` mit 939 Zeilen über drei Module, 40+ Flat-Skripte in
`phase0/scripts/` (Runtime und Einmal-Tooling gemischt), Dead Code aus
dem EPIC-002-Rollback, Alembic-Versions-Drift seit Sprint 1.

Dieses Epic führt beide Repos in ein Monorepo zusammen, baut das
Vendoring ab, entzerrt die Code-Struktur und hebt die Doku auf den
Stand — bei **strikt erhaltenem Verhalten** (Prod = Truth, jede
Änderung testgesichert gegen die Baseline aus EPIC-003/Q4).

## Scope

### Was drin ist

- **M1** Monorepo-Merge studio + pptxgenerator_v2 (Git-Historie
  erhalten); Alt-Verzeichnisse gemäß ADR aus Q5 archivieren
- **M2** Vendoring abbauen: `vendor.sh` + Engine-Kopie weg, direkte
  Repo-Pfade in Backend/Dockerfile
- **M3** Coolify-Deploy (yu2fqx0twmtqcp6zyx2e59si) auf Monorepo
  migrieren + Live-Verify (Health, Korpus-Volume, alle drei Module)
- **M4** `backend/app.py` in Module entzerren (bildgenerator /
  angebot / praesentation / auth) — Endpoints und Verhalten identisch
- **M5** Engine-Skripte ordnen: Runtime vs. Build-Tooling trennen,
  Dead Code raus (EPIC-002-Reste, `web/_legacy/`)
- **M6** Alembic-Drift fixen: alembic.ini in den Container,
  Versionstracking sauber, Migrations-Lauf nicht mehr rc=255
- **M7** Docs auf Stand: README, CLAUDE.md, ARCH-Spec mit Techstack
  an genau einem Ort; Engine-Pipeline (PDF→elements→reconstruct)
  dokumentiert

### Was NICHT drin ist

- Font-Pipeline-Änderungen (auch wenn man „schon mal drin ist")
  → EPIC-005
- Neue Features, OAuth-Ausbau, Bildgenerator-Änderungen
- pgbundle→Postgres-Umbau, falls ADR ihn fordert → eigenes Folge-Epic

## Sprint-Zuordnung (grob)

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 11 | M1–M3 (Monorepo + Deploy) | L |
| Sprint 12 | M4–M7 (Code-Struktur + Docs) | M |

> **Fortschritt:** Sprint 11 = M1–M3 ✅ DONE (2026-06-10, PRs #29–#31,
> 8/8 Stories inkl. B1-Vorzug): Monorepo via subtree (Historie erhalten),
> vendor.sh weg, Pfade repo-intern, Dockerfile+alembic.ini, Sim-Gate,
> Cutover nach Runbook. Akzeptanzkriterien 1+2 erfüllt, 3 laufend,
> 4 teilweise (alembic.ini im Image; Versionstracking-Verify → M6),
> 5 offen (M7). Rest: M4–M7 in Sprint 12.

## Akzeptanzkriterien

1. Ein Repo; `vendor.sh` und Engine-Kopie existieren nicht mehr;
   Engine-Pfade sind repo-intern aufgelöst.
2. Coolify-Deploy aus dem Monorepo ist live und grün (Health-Checks
   aller drei Module, Korpus-Volume gemountet).
3. Alle Bestandstests grün; keine beobachtbare Verhaltensänderung
   (Baseline-Abgleich gegen EPIC-003/Q4-Inventur).
4. `python -m backend.migrate` läuft mit sauberem Alembic-Tracking
   (kein graceful rc=255 mehr).
5. README/CLAUDE.md beschreiben den Monorepo-Stand; Techstack steht
   an genau einer Stelle.

## Referenzen

- **REQUIREMENTS:** R-REF-1, R-REF-2, R-REF-3, R-REF-4, R-REF-5,
  R-REF-6, R-QA-3, R-NF-1, R-NF-2
- **ADR:** Monorepo-Schnitt + Alt-Ordner (aus EPIC-003/Q5)
- **Audit:** [[TRACEABILITY]] → WP M1–M7

## Abhängigkeiten

Blockiert von: EPIC-003 (Q4 Test-Baseline, Q5 Monorepo-ADR).
Blockiert: EPIC-005, EPIC-006 (bauen auf Monorepo-Struktur).
