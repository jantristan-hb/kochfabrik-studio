---
id: EPIC-009
title: "Backup & Resilienz: Postgres + Korpus-Volume wiederherstellbar"
status: OPEN
created: 2026-06-09
project: kochfabrik-studio
sprints: []
---

# EPIC-009: Backup & Resilienz

> **Typ:** EPIC. Klammer über Sprints — kein Detail-Spec. `/sprint-plan`
> schneidet die WPs in Stories. Status: `OPEN → IN_PROGRESS → DONE`.

## Beschreibung

Zwei produktkritische Datenbestände haben keine dokumentierte
Backup/Restore-Story: die Postgres-Datenbank (Kunden, Angebote,
Chat-Verläufe, Nummernkreise — seit EPIC-001 die Quelle der
Geschäftsdaten) und das Korpus-Volume (~4,8 GB Referenz-Cache, auf
dem Präsentationsgenerator und Slidesuche stehen). Ein Volume- oder
Container-Verlust auf dem Coolify-Host wäre aktuell ein
Totalausfall ohne definierten Wiederanlauf.

Dieses Epic definiert Sicherungszyklen, legt sie automatisiert an
und **probt den Restore real** — ein Backup, das nie zurückgespielt
wurde, ist keins.

## Scope

### Was drin ist

- **B1** Postgres-Backup: automatischer pg_dump-Zyklus mit
  Aufbewahrungsregel, Ablage außerhalb des Hosts; Restore dokumentiert
- **B2** Korpus-Volume-Backup: Sicherung/Snapshot der ~4,8 GB
  (inkl. Preview-PNGs) + dokumentierter Wiederaufbau-Pfad
  (was ist regenerierbar, was nicht)
- **B3** Restore-Probe: einmal real durchgespielt (DB in
  Wegwerf-Instanz zurückgespielt, Volume-Wiederaufbau verifiziert);
  Runbook im Repo

### Was NICHT drin ist

- Hochverfügbarkeit/Replikation — überdimensioniert für ein
  internes Kunden-Tool
- LLM-Provider-Ausfall-Handling — bestehendes graceful-Verhalten
  (R-NF-1) reicht, kein neuer Scope

## Sprint-Zuordnung (grob)

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 12 (Teil) | B1–B3 (nach Deploy-Migration M3) | S–M |

> **Fortschritt:** wird von /sprint-review aktualisiert.

## Akzeptanzkriterien

1. Postgres wird automatisch im definierten Zyklus gesichert; das
   jüngste Backup liegt nachweislich außerhalb des Hosts.
2. Korpus-Volume ist gesichert bzw. sein Wiederaufbau ist
   dokumentiert und verifiziert (inkl. regenerierbarer Anteile).
3. Restore-Probe ist durchgeführt und im Runbook protokolliert
   (Befehle, Dauer, Ergebnis).

## Referenzen

- **REQUIREMENTS:** R-BAK-1, R-BAK-2, R-BAK-3, R-NF-3
- **Audit:** [[TRACEABILITY]] → WP B1–B3

## Abhängigkeiten

Blockiert von: EPIC-004/M3 (finale Deploy-Topologie — Backups gegen
den Monorepo-Stand einrichten). Blockiert: nichts hart; faktisch
Voraussetzung für jeden riskanten Eingriff danach.
