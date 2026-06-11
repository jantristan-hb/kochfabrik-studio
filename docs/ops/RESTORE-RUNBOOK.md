# RESTORE-RUNBOOK — kochfabrik-studio

> **EPIC-009 B2/B3 — „Ein Backup, das nie zurückgespielt wurde, ist keins."**
> Dieses Runbook deckt den **DB-Restore** (Schritt-für-Schritt, lokale Probe +
> Worst-Case Prod-Neuaufbau) und den **Korpus-Wiederaufbau** (originär vs.
> regenerierbar) ab. Es enthält ein verifiziertes **Proben-Protokoll**
> (2026-06-11) mit echten Befehlen und Outputs.
>
> Erfüllt FEATURE-007 §8 Nr. 2 + 3 (EARS) sowie FEATURE-BACKUP-RESTORE §12
> (Pitfalls).

---

## 0. Backup-Inventar (Stand 2026-06-11)

| Artefakt | Pfad | Zweck |
|---|---|---|
| Postgres-Dump (jüngster) | `backups/kfstudio-2026-06-11.sql.gz` (24,5 KB) | Voller `pg_dump`-Plain-SQL der Prod-DB `kf-studio-pg` |
| Postgres-Dump (Referenz) | `backups/kf-studio-pg-2026-06-09.sql.gz` (24,7 KB) | Älterer Dump zum Quervergleich |
| Korpus-Volume | Host: `/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache` | 201 Decks / 5,2 GB PDF-Assets + Preview-PNGs |

- **Backup-Zyklus:** Host-Cron erzeugt täglich den Dump unter
  `/data/backups/kf-studio-pg/`; ein dokumentierter rsync-Pull spiegelt ihn
  lokal nach `backups/` (siehe US-052).
- **Dump-Format:** `pg_dump` Plain-SQL (kein custom/directory-Format),
  Owner `kfstudio`, Server-Version 16.14. Restore daher per
  `psql`, **nicht** `pg_restore`.

---

## 1. DB-Restore — lokale Probe (Wegwerf-Postgres)

> **Pitfall §12:** Restore IMMER gegen einen **lokalen Wegwerf-Container**,
> NIE gegen Prod. Connection hartkodiert `localhost`, Port **15433**
> (NIE 5432/5434 — die sind anderweitig belegt). Container läuft mit
> `--rm`, ist also nach `docker rm` rückstandslos weg.

### 1.1 Wegwerf-Container starten

```bash
docker rm -f kf-restore-pg 2>/dev/null
docker run -d --rm --name kf-restore-pg \
  -p 15433:5432 \
  -e POSTGRES_USER=kfstudio \
  -e POSTGRES_PASSWORD=kfstudio \
  -e POSTGRES_DB=kfstudio \
  postgres:16-alpine
```

### 1.2 Auf Postgres-ready pollen

> **Pitfall §12:** macOS hat kein GNU `timeout` — daher eigene Poll-Schleife
> (max ~30 s) statt `timeout`. `psql` erst nach `pg_isready`, sonst
> „connection refused" während Container-Init.

```bash
for i in $(seq 1 15); do
  if docker exec kf-restore-pg pg_isready -U kfstudio -d kfstudio >/dev/null 2>&1; then
    echo "READY after ${i} iterations"; break
  fi
  sleep 2
done
```

### 1.3 Jüngsten Dump einspielen

```bash
gunzip -c "backups/kfstudio-2026-06-11.sql.gz" \
  | docker exec -i kf-restore-pg psql -v ON_ERROR_STOP=0 -U kfstudio -d kfstudio
```

Erwartung: nur `CREATE TABLE` / `ALTER TABLE` / `COPY n` / `setval` /
`CREATE INDEX` — **kein `ERROR:`** im Output.

### 1.4 Beweise sammeln (5 Kern-Tabellen + alembic)

```bash
# Tabellenliste
docker exec kf-restore-pg psql -U kfstudio -d kfstudio -c '\dt'

# Rowcounts der 5 Kern-Tabellen
docker exec kf-restore-pg psql -U kfstudio -d kfstudio -c \
"SELECT 'app_user' AS tbl, count(*) FROM app_user
 UNION ALL SELECT 'customer', count(*) FROM customer
 UNION ALL SELECT 'offer', count(*) FROM offer
 UNION ALL SELECT 'chat_message', count(*) FROM chat_message
 UNION ALL SELECT 'seq_counter', count(*) FROM seq_counter
 ORDER BY tbl;"

# Migrations-Stand + Sequenz-Stände
docker exec kf-restore-pg psql -U kfstudio -d kfstudio -c "TABLE alembic_version;"
docker exec kf-restore-pg psql -U kfstudio -d kfstudio -c "TABLE seq_counter;"
```

### 1.5 Aufräumen

```bash
docker rm -f kf-restore-pg
```

---

## 2. DB-Restore — Worst-Case Prod-Neuaufbau

> Greift, wenn die Prod-DB-Instanz `kf-studio-pg` verloren ist (Volume-Verlust,
> versehentliches Löschen). **Voraussetzung:** der Dump wurde vorher per Probe
> (Abschnitt 1) verifiziert — sonst spielt man ungeprüft ein.

1. **Coolify:** Service `kf-studio-pg` neu provisionieren (gleiche
   Postgres-16-Major-Version, gleicher DB-Name `kfstudio`, User `kfstudio`).
   *(Coolify-Calls / Host-Writes sind Ask-first — nur mit explizitem
   Go ausführen, headless = BLOCKED.)*
2. Dump auf den Host bringen (rsync vom lokalen Spiegel oder aus
   `/data/backups/kf-studio-pg/`).
3. Restore **in den frischen, leeren** DB-Container:
   ```bash
   gunzip -c kfstudio-<datum>.sql.gz \
     | docker exec -i <kf-studio-pg-container> psql -U kfstudio -d kfstudio
   ```
   > Connection läuft über den Container-Namen lokal auf dem Host —
   > **niemals** eine externe Host-IP/Prod-Endpoint als Restore-Ziel angeben
   > (Pitfall §12: kein Restore gegen laufendes Prod).
4. Verifikation analog Abschnitt 1.4 (Rowcounts + `alembic_version`).
5. App-Container neustarten, damit das Engine-Glue (`gen_fiktiv` →
   `ENGINE_OK`) gegen die wiederhergestellte DB hochfährt.

---

## 3. Korpus-Wiederaufbau (B2)

Der **Korpus** (PDF-Decks + Embeddings + Preview-PNGs) liegt **nicht** im
Postgres-Dump. Er zerfällt in zwei Klassen:

### 3.1 Originär — muss gesichert werden (NICHT regenerierbar)

- **Was:** Die PDF-Assets / Roh-Decks im Cache-Volume.
- **Wo (Prod):** Host-Volume
  `/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache`
  — **201 Decks / 5,2 GB** (Inventar + Stichproben-Checksummen:
  `docs/sprint-11/BACKUP-VERIFY.md`).
- **Sicherung:** Liegt auf dem Coolify-Host + dokumentierter **rsync-Pull**
  (3-2-1). Beispiel-Pull (read-only Quelle):
  ```bash
  rsync -a --info=stats2 \
    <host>:/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache/ \
    "backups/korpus-cache/"
  ```
- **Restore:** 1:1 zurück auf das Cache-Volume des neu provisionierten
  App-Containers (Plain-Copy, keine Transformation).
- **Warum originär:** Diese PDFs sind die kuratierte Quelle des
  Slide-Korpus. Gehen sie verloren, lassen sie sich **nicht** aus DB +
  Code rekonstruieren.

### 3.2 Regenerierbar — aus Code + Build-Korpus-DB neu erzeugbar

Diese Artefakte müssen **nicht** gesichert werden, solange Code und
Build-Korpus-DB vorhanden sind — sie werden deterministisch neu gebaut.
**Pfad-Hinweis:** nach dem Tooling-Split (US-056, siehe
`docs/sprint-12/TOOLING-SPLIT.md`) liegen die Build-Tools unter
`engine/tooling/`; die einzige Lade-Schicht `bundle.py` bleibt unter
`engine/scripts/` (ADR-003).

**(a) `pgbundle.npz`** (Embedding-Bundle: `emb` float32 N×768 +
`deck`/`page`/`src_pdf`-Metadaten) — aus der Build-Korpus-DB.
Konfiguration über `KF_PG_*`-Env (Defaults: `KF_PG_HOST=localhost`,
`KF_PG_PORT=5434`, `KF_PG_USER=postgres`, `KF_PG_PASSWORD=pptxgen`,
`KF_PG_DB=pptxgen`):

```bash
cd engine/tooling
# Build-Korpus-DB env (Beispiel — Werte projektabhängig)
export KF_PG_HOST=localhost KF_PG_PORT=5434 \
       KF_PG_USER=postgres KF_PG_PASSWORD=pptxgen KF_PG_DB=pptxgen

python3 db_embed.py        # füllt menu_composition.embedding + npz-Cache
```

> Geladen wird `pgbundle.npz` zur Laufzeit ausschließlich über
> `engine/scripts/bundle.py` (`np.load`, ADR-003 / FEATURE-006 EARS 2) —
> die einzige Ladestelle. Bei Versionssprung des Embedding-Modells
> (`gemini-embedding-001`, `SEMANTIC_SIMILARITY`, dim 768) muss neu
> gebaut werden, damit Offer-Query- und Korpus-Vektoren vergleichbar bleiben.

**(b) Preview-PNGs** (`cache/<deck>/preview/p<page>.png`, 800×450) —
aus den Cache-Decks regeneriert:

```bash
cd engine/tooling
python3 render_previews.py            # alle Slides (idempotent, skippt vorhandene)
python3 render_previews.py --force    # erzwingt Re-Render
```

> `render_previews.py` ist Vorab-Tooling (offline). Die Slide-Suche liest
> zur Laufzeit nur die fertigen PNGs — kein Live-Rendern im Hot-Path.

**(c) Fiktive Korpus-PDFs** (Sample-/Original-Stil-Decks, falls der
Build-Korpus neu aufgebaut wird):

```bash
cd engine/tooling
python3 build_korpus.py               # data/fiktiv/*.json → data/fiktiv_korpus/*.pdf
python3 build_cache.py                # Cache vorwärmen (Hot-Path ~0.3 s)
```

---

## 4. Proben-Protokoll 2026-06-11

> Verifizierte Restore-Probe gemäß FEATURE-007 §8 Nr. 2. Alle Outputs sind
> echte Container-Ausgaben, kein Mock.

**Umgebung:** Wegwerf-Container `kf-restore-pg`, Image `postgres:16-alpine`,
Port **15433** → 5432, Connection `localhost`. Dump:
`backups/kfstudio-2026-06-11.sql.gz` (24,5 KB).

**Dump-Header (verifiziert):** `Dumped from database version 16.14` /
`pg_dump version 16.14` / Plain-SQL / Owner `kfstudio`.

### 4.1 Ready-Poll

```
$ for i in $(seq 1 15); do docker exec kf-restore-pg pg_isready ... done
READY after 1 iteration
/var/run/postgresql:5432 - accepting connections
```

### 4.2 Restore-Lauf

Befehl:
```
gunzip -c "backups/kfstudio-2026-06-11.sql.gz" \
  | docker exec -i kf-restore-pg psql -v ON_ERROR_STOP=0 -U kfstudio -d kfstudio
```
Output (Auszug, **kein `ERROR:`**):
```
CREATE TABLE ... ALTER TABLE ...
COPY 1
COPY 3
COPY 44
COPY 13
COPY 22
COPY 2
 setval
--------
     52
 setval
--------
     18
 setval
--------
     28
CREATE INDEX (×7) ... ALTER TABLE ...
```
**Restore-Dauer:** < 1 s.

### 4.3 Tabellenliste (`\dt`)

```
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | alembic_version | table | kfstudio
 public | app_user        | table | kfstudio
 public | chat_message    | table | kfstudio
 public | customer        | table | kfstudio
 public | offer           | table | kfstudio
 public | seq_counter     | table | kfstudio
(6 rows)
```

### 4.4 Rowcounts der 5 Kern-Tabellen

| Tabelle | Rowcount | Plausibel? |
|---|---|---|
| `app_user` | 3 | ✅ kleine Nutzerbasis |
| `customer` | 13 | ✅ |
| `offer` | 22 | ✅ |
| `chat_message` | 44 | ✅ (mehrere Messages je Offer) |
| `seq_counter` | 2 | ✅ (`kunde`, `angebot`) |

```
     tbl      | count
--------------+-------
 app_user     |     3
 chat_message |    44
 customer     |    13
 offer        |    22
 seq_counter  |     2
(5 rows)
```

### 4.5 Migrations-Stand + Sequenz-Konsistenz

```
$ TABLE alembic_version;
        version_num
----------------------------
 0003_drop_praesentation_v2
(1 row)

$ TABLE seq_counter;
  name   | value
---------+-------
 kunde   |    18
 angebot |    28
(2 rows)
```

**Konsistenz-Check:** Die `setval`-Werte aus dem Restore (kunde-Sequenz 18,
angebot-Sequenz 28) decken sich mit den `seq_counter`-Werten — Sequenzen und
Counter-Tabelle sind synchron, keine Dateninkonsistenz.

### 4.6 Cleanup

```
$ docker rm -f kf-restore-pg
```

**Ergebnis:** Restore-Probe **bestanden** — alle 6 Tabellen wiederhergestellt,
alle 5 Kern-Tabellen mit plausiblen Rowcounts, Migrations-Stand und Sequenzen
konsistent. Der jüngste Dump ist nachweislich rückspielbar.
