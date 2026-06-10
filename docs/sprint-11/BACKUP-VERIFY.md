# US-044 — Backup vor Cutover (verifiziert)

Sicherheitsnetz vor dem Monorepo-Cutover (EPIC-004), vorgezogen aus EPIC-009/B1.
Erstellt am 2026-06-10 (Backup-Datumsstempel: 2026-06-09).

## Container-Verifikation

Der vom Lead genannte Kandidat `wdjhk7cwcwxz8tpg8gdx5zkv` ist **nicht** kf-studio-pg, sondern
`flinkbase-db` (POSTGRES_DB=flinkbase, Image pgvector/pgvector:pg16). Der korrekte Container
trägt den Namen der erwarteten Service-UUID:

| Feld | Wert |
|------|------|
| Container-Name/UUID | `tqg2xzsx9zau68jlhmuwyffj` |
| Image | `postgres:16-alpine` |
| `coolify.resourceName` | `kf-studio-pg` |
| `coolify.serviceName` | `kf-studio-pg` |
| `POSTGRES_DB` | `kfstudio` |
| `POSTGRES_USER` | `kfstudio` |

Verifiziert via `docker inspect tqg2xzsx9zau68jlhmuwyffj` auf dem Host (188.245.110.5).

## Datenbank-Dump

- **Pfad (off-repo):** `../backups/kf-studio-pg-2026-06-09.sql.gz`
  (relativ zum Worktree; absolut: `/Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/backups/kf-studio-pg-2026-06-09.sql.gz`)
- **Erzeugt mit:**
  ```bash
  ssh -i ~/.ssh/hetzner_id root@188.245.110.5 \
    "docker exec tqg2xzsx9zau68jlhmuwyffj pg_dump -U kfstudio kfstudio" \
    | gzip > ".../backups/kf-studio-pg-2026-06-09.sql.gz"
  ```
- **Komprimierte Größe:** 28K (24665 Bytes)

### Integritäts-Check

```
gzip -t: OK
```

`CREATE TABLE`-Anweisungen im Dump: **6** (≥ 5 gefordert).

Tabellen-Marker (je 1 `CREATE TABLE` pro Tabelle):

| Tabelle | gefunden |
|---------|----------|
| `app_user` | 1 |
| `customer` | 1 |
| `offer` | 1 |
| `chat_message` | 1 |
| `seq_counter` | 1 |

## Korpus-Volume-Inventar

Read-only erhoben via SSH auf dem Host.

- **Volume-Pfad:** `/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache`
- **Deck-Count (Top-Level-Verzeichnisse):** 201
- **Gesamtgröße (`du -sh`):** 5.2G
- **Dateien gesamt (`find -type f`):** 29566

### Stichproben (Größe + md5)

| Datei | Bytes | md5 |
|-------|-------|-----|
| `03-09-2025-efwx-lunch/logos.json` | 1710 | `9cc684684eb7cecac78795986b7dbec3` |
| `03-09-2025-efwx-lunch/preview/p4.png` | 381650 | `a246caf567b0ec4d501b8f50245111b2` |
| `03-09-2025-efwx-lunch/preview/p3.png` | 300163 | `60db713c22b22210698f34e729427b30` |

## Restore-Hinweis

Dump dekomprimieren und in den (frischen) Postgres-Container einspielen:

```bash
gunzip -c ".../backups/kf-studio-pg-2026-06-09.sql.gz" \
  | ssh -i ~/.ssh/hetzner_id root@188.245.110.5 \
    "docker exec -i <kf-studio-pg-container> psql -U kfstudio -d kfstudio"
```

Das Korpus-Volume liegt direkt auf dem Host (`/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache`)
und wird über die obige Inventar-Tabelle (Deck-Count, Größe, Stichproben-Checksummen) verifiziert.
