---
key: KOCHFABRIK-ADR-003
status: proposed
title: "pgbundle.npz vs. Postgres für Engine-Korpus-Queries"
created: 2026-06-09
project: kochfabrik
---

# ADR-003: pgbundle.npz vs. Postgres für Engine-Korpus-Queries

> **Typ:** ADR (Architecture Decision Record, MADR-artig). Eine Entscheidung, datiert,
> unveränderlich. Status: `proposed` (Sprint 10, Doc-only-Analyse — nichts festgeklopft).
> Bezug: R-REF-3, FINDINGS-ENGINE F-E-03/F-E-10, EPIC-004 (Monorepo-Schnitt, „Verhalten
> strikt erhalten").

**Sprint:** 10

## Kontext

Im System existieren heute **drei verschiedene „Postgres"-Bezüge**, die in der Diskussion
ständig verwechselt werden — sie sauber zu trennen ist die halbe Entscheidung:

1. **Build-Time-Korpus-DB** (lokal, `host=localhost port=5434 dbname=pptxgen`,
   `assemble.py:154` DSN, `vendor.sh:55`): ein *Entwickler-Postgres mit pgvector*, in dem
   der Slide-Korpus (`menu_composition`, `static_slide`) liegt. Existiert nur auf Jans
   Maschine, nie im Container.
2. **Runtime-Korpus-Snapshot** `phase0/data/pgbundle.npz` (3,26 MB, N×768 float32 `emb`
   + `deck/page/src_pdf/module_type/module_label`) + `static_slide.json`: ein von
   `vendor.sh` Schritt 3 aus (1) regeneriertes numpy-Artefakt. Das ist die einzige
   Korpus-Datenquelle, die der Container tatsächlich sieht.
3. **Runtime-App-DB** (Coolify-Service `kf-studio-pg`, `backend/db.py`,
   `backend/models.py`): echtes Postgres für **App-Daten** — `app_user`, `customer`,
   `offer` (Angebot-State als JSONB), `chat_message`, `seq_counter`. Hat **kein**
   pgvector, kennt den Korpus nicht, wird über `DATABASE_URL` graceful eingebunden.

Der Korpus-Snapshot (2) wird zur Laufzeit über **zwei parallele Datenpfade** gelesen
(F-E-03):

- **`pg_shim.py`** (`connect()` → numpy statt psycopg2): bedient exakt die 4 Query-Shapes
  von `assemble.py` (Angebotsgenerator). Der Studio-Container erzwingt ihn via
  `PPTX_PGSHIM=1` (`backend/app.py:804`), sodass kein Postgres-Connect-Timeout entsteht.
- **`slidesuche.py:_bundle()`**: lädt `pgbundle.npz` **direkt** per `np.load`, normalisiert
  selbst (`/(norm+1e-9)`) und dupliziert die Cosinus-ANN aus `pg_shim.py:60-65`. Begründung
  im Code (Z. 99–103): pg_shim deckt nur die `LIMIT 8`-Shapes ab, nicht `LIMIT %s` /
  `SELECT module_label` der Slidesuche.

Daraus zwei parallele Lade-/Normalisier-/ANN-Implementierungen auf **ein** Artefakt, dessen
Schema (Spaltennamen) bei jeder Änderung an zwei Stellen nachgezogen werden muss — plus die
Regenerierungs-Kette (1)→(2) via `vendor.sh`, die selbst eine implizite pgvector-Abhängigkeit
zur Build-Zeit ist. EPIC-004 will die Engine ins Monorepo ziehen, „Verhalten strikt erhalten".
Diese Entscheidung legt fest, **welcher Datenpfad nach dem Schnitt der legitime ist** und ob
die Korpus-Queries auf das vorhandene Runtime-Postgres (3) gehoben werden.

## Entscheidung

**Option (c) Hybrid mit explizit dokumentierter Grenze, in zwei Schritten:** pgbundle.npz
bleibt **die** Runtime-Korpus-Datenquelle (read-only, deploy-frei), aber die zwei Lesepfade
werden hinter **einer** Bundle-Zugriffs-Schicht konsolidiert — `slidesuche.py` und
`assemble.py` lesen künftig über dasselbe Modul (Lade-/Normalisier-/ANN-Code genau einmal),
`pg_shim` wird zu dieser einen Schicht erweitert statt parallel dupliziert. Das Runtime-
App-Postgres (`kf-studio-pg`) bleibt **ausschließlich** für App-Daten zuständig; Korpus-
Queries werden **nicht** dorthin migriert. Die Build-Time-Korpus-DB (Port 5434) + `vendor.sh`
bleiben der Regenerierungs-Pfad. Diese Konsolidierung ist die Mindest-Voraussetzung („SHALL
before refactor") für den EPIC-004-Schnitt; die vollständige Vereinheitlichung ist als
Arbeitspaket innerhalb EPIC-004/M5 zu führen, **kein** separates Epic.

## Alternativen

| Option | Pro | Contra |
|--------|-----|--------|
| **(c) Hybrid: pgbundle read-only für Korpus, Postgres nur App-Daten, EIN konsolidierter Bundle-Lesepfad** | Container bleibt DB-frei (graceful, kein Connect-Timeout, F-E-03-Begründung erhalten); App-DB-Trennung ist bereits Realität (db.py/models.py kennen Korpus nicht); Doppelpflege (zwei `np.load`/Normalisier-/ANN-Kopien) verschwindet → ein Schema-Vertrag; minimal-invasiv = „Verhalten strikt erhalten" einhaltbar | Snapshot-Konsistenz bleibt ein offenes Thema (Korpus-Update braucht `vendor.sh`-Lauf, kein Live-Read); Build-Time-pgvector-Abhängigkeit (Port 5434) bleibt; Grenze App-DB↔Korpus muss diszipliniert dokumentiert/eingehalten werden |
| (a) pgbundle behalten + Direktzugriff als EINZIGEN Pfad, pg_shim deprecaten | Entfernt die SQL-Shim-Indirektion ganz; `slidesuche`-Direktzugriff ist schon der schlankere Code | `assemble.py` müsste von „spricht psycopg2/pg_shim-SQL" auf „ruft numpy-API" umgebaut werden — das ist **Verhaltensänderung** an der Angebots-Kernlogik, verletzt EPIC-004 „strikt erhalten"; die originaltreue `<=>`-Ranking-Semantik (pg_shim-Kommentar Z. 4–6) müsste neu verifiziert werden |
| (b) Korpus-Queries aufs Coolify-Postgres heben (pgvector im Runtime-Container) | Eine DB, ein Live-Datenstand, kein Snapshot-Drift; Korpus-Updates sofort sichtbar | Runtime-Container braucht dann **zwingend** DB-Zugriff für den Präsentationspfad → graceful-Degradation (heute: ohne DB läuft Generator via pgbundle) geht verloren; pgvector-Extension + Datenmigration des Korpus nach `kf-studio-pg`; Connect-Timeout-Risiko, das `PPTX_PGSHIM=1` heute gerade vermeidet; größter Eingriff, höchstes Regressionsrisiko für EPIC-004 |

## Konsequenzen

- **Positiv:** Der Container bleibt für den Generator-/Slidesuche-Pfad DB-frei und graceful
  (ohne `DATABASE_URL` läuft beides weiter über `pgbundle.npz`); die heute doppelte Lade-/
  Normalisier-/ANN-Logik (F-E-03) wird auf **eine** Implementierung reduziert, womit das
  Schema des Bundles (`emb/deck/page/module_type/module_label`) genau einen Vertrag hat.
- **Positiv für EPIC-004:** Der Datenpfad ist vor dem Monorepo-Schnitt eindeutig — nur
  *ein* Korpus-Lesepfad muss „strikt erhalten" verifiziert werden, nicht zwei divergierende.
- **Negativ/Einschränkung:** Snapshot-Konsistenz bleibt manuell — ein geänderter Korpus wird
  erst nach `vendor.sh` (Regen aus Port-5434-DB + Re-Deploy) sichtbar; das deckt sich mit
  dem Cache-Invalidierungs-Loch F-E-11 und muss in der Bundle-Metadata (Quell-Hash/Timestamp)
  signalisiert werden. pgvector bleibt eine **Build-Time**-Abhängigkeit (Port 5434), nicht
  Runtime.
- **Zu beachten — Grenze hart dokumentieren:** App-DB (`kf-studio-pg`) niemals für Korpus-
  Queries, Korpus-Bundle niemals für App-State. Die `data/cache/`- und `pgbundle.npz`-
  Artefakte sind read-only Deploy-Inputs (Coolify Directory Mount überlagert `cache/` zur
  Laufzeit, `vendor.sh:97-99`) — der Server-Volume-Stand ist autoritativ.
- **Zu beachten — Hardcodes blockieren den Schnitt (F-E-10):** Build-DSN
  (`localhost:5434`, Passwort im Klartext) und `CORPUS_DIR` (absoluter Mac-Pfad) müssen vor
  dem Monorepo-Schnitt env-/arg-konfigurierbar werden, sonst ist die Regen-Kette nicht
  reproduzierbar außerhalb von Jans Maschine.
- **Kein Folge-Epic nötig:** Die Konsolidierung des Bundle-Lesepfads ist ein Arbeitspaket in
  **EPIC-004/M5** (Datenpfad/Monorepo). Sie ist klein und an den Schnitt gekoppelt; ein
  eigenes Epic wäre Overhead.

## Referenzen
- relates_to → FINDINGS-ENGINE F-E-03 (pg_shim-Bypass in `slidesuche.py`), F-E-10
  (hardcodierte DSN / `CORPUS_DIR`), F-E-11 (Cache ohne Invalidierung)
- relates_to → EPIC-004/M5 (Datenpfad/Monorepo-Schnitt)
- Belege: `backend/slidesuche.py:98-115`, `phase0/scripts/pg_shim.py:79-97`,
  `phase0/scripts/assemble.py:146-158`, `backend/app.py:804`, `backend/db.py`,
  `backend/models.py`, `vendor.sh:51-84`
