---
key: KOCHFABRIK-FEATURE-007
status: implemented
title: "Backup-Zyklus + Restore-Probe (EPIC-009 B1–B3)"
created: 2026-06-10
project: kochfabrik
---

# KOCHFABRIK-FEATURE-007: Backup & Restore

> **Typ:** FEATURE (Brownfield-Delta). Sprint 12 / EPIC-009 B1–B3.
> Baut auf dem Einmal-Backup aus Sprint 11 (US-044) auf — jetzt
> Automatisierung + geprobter Restore. „Ein Backup, das nie
> zurückgespielt wurde, ist keins."

## 1. Vision

Postgres wird automatisch täglich gesichert (Rotation, dokumentierter
Off-Host-Pull), der Korpus-Wiederaufbau ist dokumentiert, und der
Restore ist einmal real durchgespielt — mit Runbook.

## 3. Datenmodell / Artefakte

| Artefakt | Ort | Inhalt |
|---|---|---|
| Cron-Backup | Host `/etc/cron.d/kf-studio-pg-backup` + `/data/backups/kf-studio-pg/` | täglich `pg_dump | gzip`, Dateiname `kfstudio-YYYY-MM-DD.sql.gz`, Rotation 14 Tage |
| Off-Host-Pull | dokumentierter Befehl (scp → `…/kochfabrik/backups/`) | wöchentlich manuell / per Mac-Aufruf |
| `docs/ops/BACKUP-CYCLE.md` | Repo | Zyklus, Rotation, Pull, Verantwortung |
| `docs/ops/RESTORE-RUNBOOK.md` | Repo | DB-Restore Schritt für Schritt + Korpus-Wiederaufbau (B2) + Proben-Protokoll (B3) |

## 4. Flows

```
B1: cron (Host) → docker exec kf-studio-pg pg_dump | gzip
    → /data/backups/… → Rotation (find -mtime +14 -delete)
B3: jüngsten Dump holen → lokaler Wegwerf-Postgres (docker, Port 15433)
    → gunzip | psql → Tabellen + Rowcounts gegen Prod-Erwartung
    → Protokoll ins Runbook
B2: Korpus: originär = data/cache-PDF-Assets + previews (Volume,
    Backup = Sprint-11-Inventar + Host-Kopie), regenerierbar =
    pgbundle/Previews via tooling (build_cache/render_previews) —
    Doku, was woher wiederkommt
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN der Zyklus eingerichtet ist THE SYSTEM SHALL auf dem Host
   einen täglichen Dump mit 14-Tage-Rotation erzeugen; ein manuell
   getriggerter Lauf SHALL sofort eine valide (gzip -t, Tabellen-
   Marker) Dump-Datei produzieren.
2. WHEN die Restore-Probe läuft THE SYSTEM SHALL den jüngsten Dump in
   einem lokalen Wegwerf-Postgres wiederherstellen und die 5
   Kern-Tabellen (app_user, customer, offer, chat_message,
   seq_counter) SHALL mit plausiblen Rowcounts existieren.
3. THE SYSTEM SHALL den Korpus-Wiederaufbau dokumentieren
   (originär vs. regenerierbar, konkrete Befehle/Quellen) —
   RESTORE-RUNBOOK.md enthält beide Pfade + das Proben-Protokoll.

## 9. Abgrenzung (Nicht-Teil)

- Kein S3/Offsite-Automat (Off-Host-Pull bleibt manuell dokumentiert —
  Ausbau bei Bedarf)
- Keine HA/Replikation (EPIC-009 §Nicht-Teil)

## 9a. Boundaries (3-Tier)

- ✅ **Always:** Host-SSH read-only; lokaler Wegwerf-Postgres
  (Port 15433); Dateien unter `docs/ops/`; **explizit erlaubte
  Host-Writes (Task-Text):** `/etc/cron.d/kf-studio-pg-backup`
  anlegen, `/data/backups/kf-studio-pg/` anlegen, manueller
  Testlauf des Backup-Skripts
- ⚠️ **Ask-first (headless → BLOCKED):** JEDER andere Host-Write
  (Pakete, Container, Volumes, andere Crons); Coolify-Writes
- 🚫 **Never:** Prod-DB-Writes (pg_dump ist lesend!); Restore GEGEN
  Prod; Dumps/Secrets ins Repo committen; Korpus-Volume ändern

## 10. Abgrenzung zum Ist

- Einmal-Dump manuell (US-044) → täglicher Zyklus + Rotation + Doku
- Restore nie geprobt → real durchgespielt mit Protokoll
- Korpus-Wiederaufbau implizit (vendor.sh-Wissen, tot) → explizit
  dokumentiert auf Monorepo-Stand

## 11. Implementierungs-Anker (Ist)

Host: `ssh -i ~/.ssh/hetzner_id root@188.245.110.5`, Container
`tqg2xzsx9zau68jlhmuwyffj` (= kf-studio-pg, postgres:16-alpine,
DB/User `kfstudio`), Volume `/data/coolify/applications/
yu2fqx0twmtqcp6zyx2e59si/cache` (201 Decks/5,2 GB, Inventar in
`docs/sprint-11/BACKUP-VERIFY.md`). Referenz-Dump:
`../backups/kf-studio-pg-2026-06-09.sql.gz`. Regenerier-Tooling nach
US-055 unter `engine/tooling/` (build_cache.py, render_previews.py —
Pfade nach Tooling-Split prüfen!).

## 12. Bekannte Pitfalls

1. **cron.d-Datei braucht User-Feld + Newline am Ende** — sonst läuft
   nichts, still. Nach Anlage `run-parts --test` bzw. manuellen Lauf
   beweisen, nicht auf morgen warten.
2. **docker exec im Cron ohne TTY/PATH** — absolute Pfade
   (`/usr/bin/docker`), kein `-it`.
3. **Rotation löscht zu viel:** `find … -name 'kfstudio-*.sql.gz'
   -mtime +14` — Pattern eng halten, NIE das ganze Verzeichnis.
4. **Restore-Probe gegen falschen Port = Prod-Risiko:** Wegwerf-
   Container auf 15433, Verbindungsstring im Runbook hartkodiert
   lokal, niemals Host-IP.

## Referenzen
- implements → REQUIREMENTS R-BAK-1, R-BAK-2, R-BAK-3, R-NF-3
- relates_to → [[EPIC-009]] B1–B3 · docs/sprint-11/BACKUP-VERIFY.md

## Referenziert von
— USER-STORIES Sprint 12 (US-057, US-058)
