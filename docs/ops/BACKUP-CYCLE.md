# Backup-Zyklus — kf-studio-pg (Prod, flinkbase)

Täglicher automatischer Postgres-Dump der Produktionsdatenbank mit 14-Tage-Rotation.
Story: EPIC-009/US-052 (Issue #33). EARS: FEATURE-007 §8 Nr. 1.

## Überblick

| Aspekt | Wert |
|--------|------|
| Host | `188.245.110.5` (flinkbase, Hetzner) |
| DB-Container | `tqg2xzsx9zau68jlhmuwyffj` (`postgres:16-alpine`) |
| DB / User | `kfstudio` / `kfstudio` |
| Dump-Verzeichnis | `/data/backups/kf-studio-pg/` |
| Skript | `/data/backups/kf-studio-pg/backup.sh` |
| Cron | `/etc/cron.d/kf-studio-pg-backup` |
| Zeitplan | täglich `03:30` (Host-Zeit, UTC) |
| Rotation | 14 Tage (`find ... -mtime +14 -delete`) |
| Log | `/data/backups/kf-studio-pg/backup.log` |
| Dateinamen | `kfstudio-YYYY-MM-DD.sql.gz` |

Der Dump ist rein lesend (`pg_dump` via `docker exec`); es werden keine
Prod-DB-Writes ausgeführt.

## Zyklus / Mechanik

Cron (`/etc/cron.d/kf-studio-pg-backup`) ruft täglich um 03:30 `backup.sh` als
`root` auf. Das Skript:

1. `pg_dump -U kfstudio kfstudio` im DB-Container, Stdout durch `gzip` →
   `/data/backups/kf-studio-pg/kfstudio-$(date +%F).sql.gz`
2. Rotation: löscht nur Dateien des Musters `kfstudio-*.sql.gz` älter als
   14 Tage — niemals das Verzeichnis selbst.
3. Schreibt eine Statuszeile (Pfad + Größe) in `backup.log`.

`set -euo pipefail` sorgt dafür, dass ein fehlgeschlagener `pg_dump` den Lauf
abbricht, statt eine leere/kaputte Datei zu hinterlassen.

## Cron-Eintrag

```cron
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
30 3 * * * root /data/backups/kf-studio-pg/backup.sh >> /data/backups/kf-studio-pg/backup.log 2>&1
```

cron.d-Eigenheiten (sonst läuft der Job still nicht):
- User-Feld (`root`) ist Pflicht — cron.d-Zeilen haben es, crontab-Zeilen nicht.
- Explizite `PATH`-Zeile, da cron mit minimalem Environment startet.
- Datei MUSS mit Newline enden.

## Manuell triggern

```bash
ssh -i ~/.ssh/hetzner_id root@188.245.110.5 /data/backups/kf-studio-pg/backup.sh
```

Erzeugt sofort den heutigen Dump (überschreibt einen bereits vorhandenen
gleichen Tages-Dump).

## Off-Host-Pull

Dump auf den Arbeitsrechner ziehen (off-repo, nicht committen):

```bash
scp -i ~/.ssh/hetzner_id \
  "root@188.245.110.5:/data/backups/kf-studio-pg/kfstudio-*.sql.gz" \
  "/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/backups/"
```

## Verify

```bash
# heutige Datei existiert
ssh -i ~/.ssh/hetzner_id root@188.245.110.5 \
  "ls -la /data/backups/kf-studio-pg/kfstudio-$(date +%F).sql.gz"

# gzip-Integrität
ssh -i ~/.ssh/hetzner_id root@188.245.110.5 \
  "gzip -t /data/backups/kf-studio-pg/kfstudio-*.sql.gz && echo OK"

# Tabellen-Marker (>=5 erwartet)
ssh -i ~/.ssh/hetzner_id root@188.245.110.5 \
  "gunzip -c /data/backups/kf-studio-pg/kfstudio-$(date +%F).sql.gz | grep -c 'CREATE TABLE'"

# Cron installiert
ssh -i ~/.ssh/hetzner_id root@188.245.110.5 \
  "cat /etc/cron.d/kf-studio-pg-backup"

# Log der letzten Läufe
ssh -i ~/.ssh/hetzner_id root@188.245.110.5 \
  "tail /data/backups/kf-studio-pg/backup.log"
```

## Restore

Restore-Probe + Runbook sind eigene Story (US-058, B2/B3). Schnellpfad:

```bash
gunzip -c kfstudio-YYYY-MM-DD.sql.gz | \
  docker exec -i tqg2xzsx9zau68jlhmuwyffj psql -U kfstudio kfstudio
```
