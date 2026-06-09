---
key: KOCHFABRIK-ADR-002
status: proposed
title: "Monorepo-Schnitt: studio + Engine in ein Repo, Vendoring abbauen"
created: 2026-06-09
project: kochfabrik
Sprint: 10
---

# ADR-002: Monorepo-Schnitt — studio + Engine zusammenführen, Vendoring abbauen

> **Typ:** ADR (Architecture Decision Record, MADR-artig). Hält **eine**
> Entscheidung fest — klein, datiert, unveränderlich (bei Revision: neues
> ADR mit `supersedes`). Entsteht in EPIC-003/Q5 als Voraussetzung für
> EPIC-004 (M1–M3). Pfad: `docs/adr/`. Status:
> `proposed → accepted → superseded/deprecated`.
>
> **Doc-only (R-REF-6):** Dieses ADR schlägt einen Schnitt VOR. Es wird
> NICHTS verschoben, gelöscht oder gemergt. Alt-Ordner sind hier nur
> inventarisiert; Umsetzung erst in EPIC-004 nach `accepted`.

**Sprint:** 10

## Kontext

`kochfabrik-studio` (FastAPI-Backend + Design-2-Web + vendored Engine)
und `pptxgenerator_v2` (Render-Engine, Single Source) sind heute zwei
getrennte GitHub-Repos unter `jantristan-hb/` (verifiziert:
`git -C kochfabrik-studio remote` → `…/kochfabrik-studio.git`,
`git -C pptxgenerator_v2 remote` → `…/pptxgenerator_v2.git`). Verbunden
sind sie über `vendor.sh` (~13 MB Engine-Kopie nach `engine/phase0/` +
pgbundle-Regen + Container-Pfad-Sim-Gate, `vendor.sh:24-93`). Jede
Engine-Änderung erzwingt Doppel-Pflege: entwickeln in
`pptxgenerator_v2/phase0/`, dann `./vendor.sh`, dann `git add engine`
im Studio (`README.md:55-62`).

Diese Kopplung verursacht belegte Probleme: F-E-03/F-S-09 (pg_shim-
Bypass — `pgbundle.npz`-Vertrag an zwei Stellen gepflegt,
`slidesuche.py:98-115` vs. `pg_shim.py:80-87`); die Engine-Pfad-
Auflösung muss vendored ODER sibling raten (`backend/app.py:349-352`
`_VEND if isdir else _SIB`); und der `vendor.sh`-Quellpfad zeigt auf
`~/work/03 AKARA Solutions GmbH/…` (`vendor.sh:12`, ebenso
`README.md:44`), während beide Repos real unter
`02 AKARA Solutions GmbH/kochfabrik/` liegen — eine schon driftende,
maschinen-lokale Annahme. Dazu liegt im Arbeitsverzeichnis ein Wildwuchs
an Alt-Ordnern (POCs, Backups, Material), deren Schicksal für den
Repo-Schnitt geklärt sein muss.

Zu entscheiden (R-REF-1 ❓ + R-NF-2): **(1)** Repo-Name + Layout des
Monorepos, **(2)** wie die Git-Historie beider Repos erhalten bleibt,
**(3)** das Schicksal jedes Alt-Ordners, **(4)** der Coolify-Migrations-
plan ohne Downtime (App-UUID `yu2fqx0twmtqcp6zyx2e59si`, Korpus-Volume
~4,8 GB bleibt gemountet).

## Entscheidung

**Option (a): Neues Monorepo durch historie-erhaltenden Merge beider
Repos in das bestehende `jantristan-hb/kochfabrik-studio` als Wurzel.**
Die Engine wird als interne Schicht `engine/` (Python-Package, kein
Vendoring) per `git subtree add --prefix=engine` aus
`pptxgenerator_v2` eingezogen — beide Historien bleiben im selben Repo
erhalten. Repo-Name bleibt `kochfabrik-studio` (Coolify-Webhook + Deploy
unverändert → kein Re-Wiring der Pipeline). `vendor.sh` und die
vendored Engine-Kopie entfallen; Backend/Dockerfile lösen die Engine
über repo-interne Pfade auf. Der Korpus-Cache (~4,8 GB) bleibt
**außerhalb** von Git (Coolify-Volume, wie heute) — er wird NICHT
mit-historisiert.

Begründung der Wurzel-Wahl: Studio trägt die Deploy-Identität
(Coolify zieht von `kochfabrik-studio` master), das Web-Frontend und
die Auth/DB-Schicht; die Engine ist die eingezogene Render-Bibliothek.
Studio absorbiert die Engine, nicht umgekehrt.

## Layout (Vorschlag, in EPIC-004/M1 final)

```
kochfabrik-studio/                 (Monorepo-Wurzel, GitHub-Remote bleibt)
├── backend/                       FastAPI (app/db/store/oauth/migrate/slidesuche)
├── web/                           Design-2-Frontend (statisch)
├── engine/                        Render-Engine (ex pptxgenerator_v2, subtree)
│   ├── scripts/                   Runtime (assemble/compose_offer/angebot_*/pg_shim)
│   ├── tooling/                   Einmal-/Build-Tooling (getrennt — EPIC-004/M5)
│   ├── spike-pptxgenjs/           reconstruct.js + node_modules
│   └── data/                      Templates + pgbundle.npz (KEIN Korpus-Cache)
├── docs/                          REQUIREMENTS/epics/adr/sprint-*
├── Dockerfile                     COPY backend web engine + alembic.ini
└── alembic.ini                    (Container-Fix, F-S-01 → EPIC-004/M6)
```

Die heutige Doppelebene `engine/phase0/scripts` wird auf `engine/scripts`
flachgezogen (das `phase0`-Präfix ist ein Engine-Repo-internes
Stage-Relikt ohne Studio-Bedeutung). Pfad-Konstanten
(`backend/app.py:349-352`, `backend/slidesuche.py:33-38`) lösen dann
deterministisch repo-intern auf — die `_VEND/_SIB`-Fallback-Heuristik
entfällt.

## Alternativen

| Option | Pro | Contra |
|--------|-----|--------|
| **(a) Monorepo, Historie-Merge via subtree, studio = Wurzel** (gewählt) | Eine Quelle der Wahrheit, Vendoring + Doppelpflege weg (F-E-03/F-S-09 strukturell entschärft); Coolify-Deploy bleibt am bestehenden Repo → minimale Migration; beide Historien erhalten | Einmaliger Merge-Aufwand; `engine/`-Historie liegt nun unter Studio-Repo (Engine-Repo wird read-only); `git subtree`-Mechanik muss sauber ausgeführt werden |
| (b) Studio absorbiert Engine **ohne** Historie-Merge (Engine read-only archiviert, Code per Plain-Copy übernommen) | Schnellste Umsetzung; sauberer Schnitt | Engine-Git-Historie geht im Studio-Kontext verloren (verstößt gegen R-REF-1-Ziel „Historie erhalten"); Blame/Bisect über Engine-Commits nur noch im Altrepo |
| (c) Status quo + besseres Vendoring (vendor.sh härten, Pfad-Drift fixen) | Kein Repo-Umbau; geringstes Risiko kurzfristig | Doppelpflege bleibt (jede Engine-Änderung = 2 Repos + Re-Vendor); pg_shim-Bypass-Drift bleibt latent; widerspricht EPIC-004-Akzeptanzkriterium 1 (kein vendor.sh/Engine-Kopie mehr) |

## Alt-Ordner-Inventar + Schicksal (pro Ordner)

> Pfade relativ zu `~/work/02 AKARA Solutions GmbH/kochfabrik/`.
> Größen/Git-Status verifiziert via `du -sh` + `.git`-Test (2026-06-09).
> **Aktion = Empfehlung für EPIC-004/M1; in diesem Sprint NICHT ausgeführt.**

| Ordner | Größe | Git | Schicksal | Begründung |
|--------|-------|-----|-----------|------------|
| `kochfabrik-studio/` | — | git | **Wurzel** | wird Monorepo-Root (s.o.) |
| `pptxgenerator_v2/` | 8,1 G | git | **als `engine/` einziehen, danach Remote read-only archivieren** | Single Source der Engine; Größe v.a. Korpus-Cache (bleibt out-of-git) |
| `praesentationsgenerator/` | 5,3 G | git | **archivieren (off-repo, nicht löschen)** | Vorgänger-POC des Generators; EPIC-002-Rollback-Linie, kein Prod-Bezug |
| `imagetagging/` | 997 M | git | **archivieren (off-repo)** | eigenständiges Tooling-Experiment, nicht Teil des Studio-/Engine-Pfades |
| `KOCHfabrik_Decks_2026-05-19/` | 65 M | no-git | **archivieren (Asset-Backup, off-repo)** | Roh-Decks/Material, kein Code; ggf. als Korpus-Quelle aufheben |
| `workshop_23032026_material/` | 101 M | no-git | **archivieren (off-repo)** | datiertes Workshop-Material, einmalig |
| `poc/` | 88 M | no-git | **archivieren (off-repo)** | Proof-of-Concept-Reste |
| `angebot/` | 13 M | no-git | **archivieren (off-repo)** | frühe Angebots-Experimente, vom Generator abgelöst |
| `angebot-002/` | 8,5 M | no-git | **archivieren (off-repo)** | dito, zweite Iteration |
| `_bak/` | 7,7 G | no-git | **prüfen, dann löschen/auslagern (Jan-Entscheid)** | undatiertes Sammel-Backup; größter Brocken, blockt aber nichts |
| `kochfabrik-studio.bak-2026-05-26-2337/` | 54 M | git | **löschen nach Merge-Verify** | datierter Studio-Snapshot vor dem Merge; durch Monorepo-Historie redundant |
| `pptx/` | 0 B | no-git | **löschen** | leer |
| `../DEPRECATED-kochfabrik-pptxgenerator` | 2,8 M | git | **belassen (bereits als DEPRECATED markiert)** | liegt eine Ebene höher, schon stillgelegt; nicht Teil des Schnitts |
| lose `.pptx` im Wurzel-Listing (bechtle/kochfabrik_slides_*) | — | — | **archivieren zu Asset-Backup** | Einzel-Artefakte, kein Code |

„Archivieren" = Plain-Copy in einen datierten Archiv-/Backup-Ort
(3-2-1, keine tar-Bundles), Original erst nach Verify entfernen.
Löschungen NUR mit Jans Freigabe — dieses ADR sammelt die Empfehlung,
löscht nichts.

## Coolify-Migrationsplan (ohne Downtime, M1→M3)

App-UUID `yu2fqx0twmtqcp6zyx2e59si`, Deploy zieht von GitHub
`jantristan-hb/kochfabrik-studio` master. Da das Monorepo dieses Repo
als Wurzel behält, bleibt der Deploy-Webhook unverändert — der Schnitt
ist deploy-seitig ein normaler Push, kein Pipeline-Re-Wiring.

1. **M1 (Vorbereitung, kein Deploy-Effekt):** Feature-Branch im
   Studio-Repo; `git subtree add --prefix=engine <engine-remote> master`
   → Engine-Historie liegt im Monorepo. Layout flachziehen
   (`phase0/scripts` → `engine/scripts`). Backend-Pfad-Konstanten auf
   repo-intern umstellen. `vendor.sh` + alte `engine/phase0`-Kopie
   entfernen. Bestandstests (EPIC-003/Q4-Baseline) müssen grün bleiben
   (R-REF-6). NICHT auf master.
2. **M2:** Dockerfile umstellen — `COPY engine ./engine` zieht jetzt
   die ge-merge-te Engine; zusätzlich `COPY alembic.ini .` (F-S-01-Fix,
   gehört EPIC-004/M6, hier nur Migrations-Voraussetzung). Lokaler
   Container-Build + Sim-Gate (Äquivalent zu `vendor.sh` Schritt 4/4)
   als Vor-Verify.
3. **M3 (Cutover):** Merge des Branches nach master → Coolify baut das
   Monorepo-Image. **Korpus-Volume bleibt gemountet** (Directory Mount
   auf `data/cache`, unverändert — kein Volume-Umbau, daher kein
   ~4,8-GB-Transfer). Health-Verify aller drei Module
   (`/api/health`, `/api/angebot/health`, `/api/praesentation/health`,
   `/api/slidesuche/search`) gegen die neue Revision; Coolify behält die
   alte Revision bis Health grün ist (Rolling, kein Downtime). Rollback
   = vorheriges Image re-deployen (Webhook/Repo unverändert).

**Vorbedingung:** Der `vendor.sh`-Pfad-Drift (03 vs. 02) wird durch den
Wegfall von `vendor.sh` gegenstandslos; bis dahin ist er ein bekanntes
Deploy-Risiko (Re-Vendor von der falschen Quelle).

## Konsequenzen

- **Positiv:** Eine Quelle der Wahrheit; `vendor.sh` + Doppelpflege
  entfallen (EPIC-004-Akzeptanzkriterium 1 erfüllt). Engine-Pfad-
  Heuristik (`_VEND/_SIB`) verschwindet, Pfad-Drift wird
  gegenstandslos. Historie beider Repos bleibt erhalten (R-REF-1).
- **Positiv:** Coolify-Deploy bleibt am bestehenden Repo → Migration
  ist ein Branch-Merge, kein Pipeline-Umbau; Korpus-Volume unangetastet.
- **Negativ/Einschränkung:** Einmaliger, sorgfältiger `git subtree`-
  Merge nötig; das Engine-Repo wird danach read-only (neue Engine-
  Arbeit nur noch im Monorepo). Das Monorepo-`.git` wächst um die
  Engine-Historie (der Korpus-Cache bleibt aber out-of-git → kein
  GB-Aufblähen des Repos).
- **Beachten:** Der pg_shim-Bypass (F-E-03/F-S-09) wird durch den
  Schnitt strukturell ENTSCHÄRFT (geteilter Code möglich), aber nicht
  automatisch gelöst — der Bundle↔Postgres-Schnitt bleibt
  Gegenstand von **ADR-003** (US-043). Alt-Ordner-Löschungen sind
  Jan-Entscheide und erfolgen erst in EPIC-004/M1 nach Verify.

## Referenzen
- relates_to → [[EPIC-004-monorepo-refactoring]] (M1–M3, M5)
- relates_to → REQUIREMENTS R-REF-1 ❓, R-REF-2, R-REF-6, R-NF-2
- depends_on → FINDINGS-STUDIO (F-S-09 pg_shim-Bypass), FINDINGS-ENGINE (F-E-03)
- relates_to → [[ADR-003]] — pgbundle vs. Postgres (US-043; löst den Bundle-Vertrag)
