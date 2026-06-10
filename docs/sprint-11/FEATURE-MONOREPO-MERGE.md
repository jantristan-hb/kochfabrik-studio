---
key: KOCHFABRIK-FEATURE-004
status: implemented
title: "Monorepo-Merge: Engine via subtree, Pfade repo-intern, Vendoring weg"
created: 2026-06-09
project: kochfabrik
---

# KOCHFABRIK-FEATURE-004: Monorepo-Merge (M1 + Vorbedingungen)

> **Typ:** FEATURE (Brownfield-Delta). Sprint 11 / EPIC-004, WPs M1 + M2
> (Teil). Setzt [[ADR-002]] (accepted) um. **Verhalten strikt erhalten
> (R-REF-6)** — jede Änderung testgesichert gegen die Sprint-10-Baseline.

## 1. Vision

Nach diesem Feature ist `kochfabrik-studio` das Monorepo: Die Engine
liegt als `engine/` (volle Git-Historie via subtree) im Repo, die
`_VEND/_SIB`-Pfad-Heuristik und `vendor.sh` sind weg, und die
Verhaltens-Baseline ist durch Charakterisierungs-Tests abgesichert.

## 3. Datenmodell

Entfällt — Struktur-Refactoring, keine Datenmodell-Änderung.

## 4. Flows / Ziel-Layout (aus ADR-002)

```
kochfabrik-studio/
├── backend/            (unverändert)
├── web/                (unverändert)
├── engine/             ex pptxgenerator_v2 (subtree, Historie erhalten)
│   ├── scripts/        Runtime (ex phase0/scripts)
│   ├── spike-pptxgenjs/  reconstruct.js + lib/ + node_modules (gerettet)
│   ├── data/           Templates + pgbundle.npz (gerettet, KEIN Korpus)
│   ├── tests/          ex phase0/tests
│   └── upstream/       Engine-Repo-Reste (docs/, design/, fixtures …)
├── docs/  Dockerfile  alembic.ini  requirements.txt
```

**Merge-Mechanik (kritische Fakten, verifiziert 2026-06-09):**
- Engine-Repo Default-Branch ist **`main`** (nicht master), Remote
  `jantristan-hb/pptxgenerator_v2`, getrackte Größe 117 MB.
- `.gitignore` des Engine-Repos schließt `phase0/data/` + `node_modules/`
  aus → der Subtree liefert **weder pgbundle.npz/Templates noch
  node_modules**. Beide sind heute in der vendored Studio-Kopie
  GETRACKT (engine/phase0/data: u.a. pgbundle.npz, *_template.elements.json,
  static_slide.json, 1 Cache-Deck; node_modules: 351 Dateien) und müssen
  beim Umbau an die neuen Pfade gerettet werden (`git checkout <alt> --`).
- Engine-Repo ist dirty: uncommitteter Fedora→Mac-Migrations-Diff
  (Mode-Bits 644→755 + `/home/jrudat`→`/Users/janrudat` in Docs/Skripten).
  MUSS vor dem Subtree-Add committet werden (US-045) — subtree braucht
  einen sauberen, gepushten Stand.

## 7. API-Skizze

Entfällt — alle HTTP-Endpoints bleiben byte-identisch (R-REF-6).

## 8. Akzeptanzkriterien (EARS)

1. WHEN das Engine-Repo konsolidiert ist THE SYSTEM SHALL den
   Mac-Migrations-Diff committet haben und DSN/CORPUS_DIR über
   Umgebungsvariablen (`KF_BUILD_DSN`-Felder, `KF_CORPUS_DIR`)
   übersteuerbar machen — mit den heutigen Werten als Default
   (Verhalten ohne gesetzte Env identisch).
2. WHEN die Charakterisierungs-Tests laufen THE SYSTEM SHALL die
   HTTP-Oberfläche DB-los absichern (TestClient: Health-Routen,
   Auth-Gate 401, statische Seiten) und die Bestands-Suite SHALL
   lokal 100% grün sein (Alembic-Namespace-Test gefixt, 0 failed).
3. WHEN der Subtree-Merge abgeschlossen ist THE SYSTEM SHALL die
   Engine-Historie im Studio-Repo tragen (`git log -- engine/` zeigt
   Engine-Commits) und `engine/scripts/*.py` SHALL vollständig
   py_compile-sauber sein.
4. WHEN die Pfad-Umstellung abgeschlossen ist THE SYSTEM SHALL keine
   Referenz auf `phase0` oder `pptxgenerator_v2` mehr in `backend/`
   tragen und `vendor.sh` SHALL entfernt sein; die Test-Suite SHALL
   grün bleiben (Baseline-Abgleich).
5. IF die Engine-Verzeichnisse `engine/data` oder
   `engine/spike-pptxgenjs/node_modules` nach dem Umbau fehlen THEN
   THE SYSTEM SHALL das als FAILED werten (Rettungs-Pflicht — Deploy
   braucht beide, es gibt kein npm install im Dockerfile).

## 9. Abgrenzung (Nicht-Teil)

- Dockerfile/Deploy → [[KOCHFABRIK-FEATURE-005]]
- pg_shim/Bundle-Schicht-Konsolidierung (ADR-003) → EPIC-004/M5, Sprint 12
- Runtime/Tooling-Trennung in `engine/scripts` → M5, Sprint 12
- Alt-Ordner-Archivierung → Jan-Entscheid, NICHT dieser Sprint

## 9a. Boundaries (3-Tier)

- ✅ **Always:** Arbeit auf Feature-Branches; Engine-Repo: Migrations-
  Diff committen + F-E-10-Env-Konfig + push auf `main` (Engine-`main`
  ist NICHT deploy-gebunden — Coolify zieht nur Studio-master);
  Tests/py_compile lokal
- ⚠️ **Ask-first (headless: BLOCKED):** Force-Push; History-Rewrite;
  jede Änderung der Ranking-/Render-Semantik („nur eine Zeile schöner")
- 🚫 **Never:** Push auf Studio-`master` (= Auto-Deploy!); `data/cache/`
  oder `pgbundle.npz` regenerieren/löschen; Alt-Ordner verschieben;
  `--squash` beim subtree (Historie-Verlust)

## 10. Abgrenzung zum Ist

- 2 Repos + vendor.sh-Kopie → 1 Repo, Engine mit Historie als `engine/`
- `_VEND/_SIB`-Raten (`backend/app.py:349-352`) → deterministischer
  repo-interner Pfad
- Hardcodes `/Users/janrudat/Nextcloud/...` + `localhost:5434`
  (`compose_offer.py:30,37`) → Env-übersteuerbar mit identischen Defaults

## 11. Implementierungs-Anker (Ist)

Studio: `backend/app.py:344-360` (_VEND/_SIB, sys.path),
`backend/slidesuche.py:33-38` (_VEND/_SIB analog), `vendor.sh`,
`engine/phase0/` (vendored: 449 getrackte Dateien, 13 MB, inkl.
`data/pgbundle.npz` + `spike-pptxgenjs/node_modules`),
`backend/tests/` (97 collect, 1 known-fail `test_sprint2.py::
test_alembic_baseline_present_and_empty` — `backend/alembic/versions/`
ohne `__init__.py`, `__file__=None`).
Engine: `../pptxgenerator_v2` (branch `main`, dirty: Mac-Migrations-Diff),
`phase0/scripts/compose_offer.py:30` (CORPUS_DIR), `:37` (DSN),
`phase0/scripts/assemble.py:39,154,291-295` (Importe + graceful Fallback).

## 12. Bekannte Pitfalls

1. **Subtree auf dirty/unpushed Quelle** — erst Engine-Repo committen
   + pushen, dann `git subtree add --prefix=engine <pfad-oder-url> main`
   (ohne `--squash`).
2. **data/ + node_modules vergessen** — kommen NICHT über den Subtree
   (gitignored im Engine-Repo); aus dem alten vendored Stand retten
   (`git checkout <commit-vor-rm> -- engine/phase0/data …` + `git mv`).
3. **„Verhalten erhalten" durch Pfad-Sed brechen** — `phase0`-Strings
   existieren auch in Engine-Skripten relativ (`_ROOT`/`DATA`-Ableitung
   via `__file__`); nach dem Flachziehen stimmen relative Ableitungen
   automatisch — NICHT blind seden, sondern `__file__`-Ableitungen prüfen.
4. **Env-Default-Drift** — F-E-10-Fix muss bei UNGESETZTER Env exakt
   die heutigen Werte liefern (Charakterisierung: Diff der effektiven
   Konfiguration vor/nach).
5. **Großer Umbau in parallelen Worktrees** — US-047→US-050 arbeiten
   auf EINEM Branch sequentiell (geteilte Dateien); nur Wave 1 ist
   parallel.

## Referenzen
- implements → REQUIREMENTS R-REF-1, R-REF-4 (Teil), R-REF-6, R-QA-3
- depends_on → [[KOCHFABRIK-ADR-002]] (accepted) · Findings F-E-10, F-S-09
- relates_to → [[EPIC-004]] WP M1 · [[KOCHFABRIK-FEATURE-005]]

## Referenziert von
— USER-STORIES Sprint 11 (US-045, US-046, US-047, US-048)
