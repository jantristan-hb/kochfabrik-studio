---
key: KOCHFABRIK-FEATURE-006
status: approved
title: "Code-Ordnung: app.py-Modularisierung, Bundle-Schicht, Tooling-Split, Alembic-Verify"
created: 2026-06-10
project: kochfabrik
---

# KOCHFABRIK-FEATURE-006: Code-Ordnung (M4 + M5 + M6)

> **Typ:** FEATURE (Brownfield-Delta). Sprint 12 / EPIC-004, WPs M4–M6.
> Setzt [[KOCHFABRIK-ADR-003]] (accepted, Hybrid/eine Bundle-Schicht) um.
> **Verhalten strikt erhalten (R-REF-6)** — Gate ist die
> Charakterisierungs-Suite aus Sprint 11 (112 Tests inkl. HTTP-Netz).

## 1. Vision

Nach diesem Feature ist das Backend in Domänen-Router zerlegt (kein
936-Zeilen-Monolith), der pgbundle-Zugriff existiert genau EINMAL
(F-E-03 strukturell gelöst), Runtime- und Build-Tooling der Engine
sind getrennt, und der Alembic-Lauf im Container ist bewiesen sauber
(F-S-01 abgeschlossen).

## 3. Datenmodell

Entfällt — Struktur-Refactoring, keine Schema-Änderung.

## 4. Flows / Ziel-Struktur

```
backend/
├── app.py            Setup: FastAPI(), Middleware (Auth-Gate),
│                     include_router(×5), statics, /api/health, /
├── routers/
│   ├── __init__.py
│   ├── auth.py       /api/login, /api/logout, /api/oauth/*
│   ├── bildgenerator.py  /api/cats, /api/image (+Gemini-Prompts)
│   ├── angebot.py    /api/angebot/*, /api/angebote, /api/stats,
│   │                 /api/kunden, /api/kunde/{id}
│   └── praesentation.py  /api/praesentation/* (+_assemble_*-Helper)
├── slidesuche.py     (bestehender Router — nutzt künftig bundle-Schicht)

engine/scripts/       NUR Runtime: assemble, compose_offer, _deckpipe,
│                     angebot_*, kf_classify, pg_shim, bundle (NEU),
│                     + transitive Runtime-Deps (Import-Analyse!)
engine/tooling/       Build-/Einmal-Tools: build_*, recon_*, dedup_*,
                      db_*, curate, gen_fiktiv, embed_cluster, gates …
engine/scripts/bundle.py   EINE Lade-/Normalisier-/ANN-Schicht für
                      pgbundle.npz — pg_shim UND slidesuche nutzen sie.
```

## 7. API-Skizze

Entfällt — alle HTTP-Routen bleiben pfad- und verhaltensidentisch.

## 8. Akzeptanzkriterien (EARS)

1. WHEN die Modularisierung abgeschlossen ist THE SYSTEM SHALL alle
   bisherigen Routen unverändert bedienen (Charakterisierungs- +
   Bestands-Suite 0 failed) und `backend/app.py` SHALL unter 200
   Zeilen liegen (nur Komposition).
2. WHEN die Bundle-Schicht steht THE SYSTEM SHALL pgbundle.npz nur
   noch über `engine/scripts/bundle.py` laden — `np.load` auf
   pgbundle SHALL in genau einer Datei vorkommen; Slidesuche- und
   Angebots-Ranking SHALL identische Ergebnisse liefern
   (Vorher/Nachher-Vergleich auf fixer Query).
3. WHEN der Tooling-Split abgeschlossen ist THE SYSTEM SHALL unter
   `engine/scripts/` nur Module tragen, die vom Runtime-Pfad
   (backend/* + assemble.py) transitiv importiert/aufgerufen werden;
   alles andere SHALL unter `engine/tooling/` liegen und weiterhin
   py_compile-sauber sein.
4. WHEN der Container mit erreichbarem Postgres startet THE SYSTEM
   SHALL den Migrations-Schritt mit rc=0 abschließen und
   `alembic_version` SHALL gestampt/aktuell sein (kein graceful
   rc=255 mehr — F-S-01-Abnahme).

## 9. Abgrenzung (Nicht-Teil)

- Keine neuen Endpoints, keine Logik-/Ranking-Änderungen
- Font-/Treue-Arbeit → EPIC-005/007
- pgvector/Postgres-Korpus-Migration — durch ADR-003 verworfen

## 9a. Boundaries (3-Tier)

- ✅ **Always:** Feature-Branch-Arbeit; git mv; Router-Extraktion mit
  identischen Pfaden; Tests/Sim-Gate lokal; Wegwerf-Postgres-Container
  lokal (docker run, eigener Port ≥15432)
- ⚠️ **Ask-first (headless → BLOCKED):** jede beobachtbare
  Verhaltensänderung („Route nebenbei verbessern"); Änderungen an
  KF_SESSION_SECRET-/Auth-Mechanik; neue Runtime-Dependency
- 🚫 **Never:** master-Push; `engine/data/`-Artefakte ändern;
  Prod-DB anfassen (nur lokaler Wegwerf-Container!)

## 10. Abgrenzung zum Ist

- `backend/app.py` 936 Z., 4 Domänen + Setup gemischt → Komposition
  <200 Z. + 4 Domänen-Router
- pgbundle 2× geladen (`pg_shim.py` + `slidesuche.py:_bundle`) →
  1× in `bundle.py` (ADR-003)
- `engine/scripts/` = 45 Dateien Runtime+Tooling gemischt → getrennt
- `python -m backend.migrate` im Container: bisher nur ohne DB
  (graceful) bewiesen → mit DB rc=0 + Stamp bewiesen

## 11. Implementierungs-Anker (Ist)

`backend/app.py` (Routen-Map: Z.508 health · 522/532 login/logout ·
539/546 cats/image · 569–737 angebot/kunden/stats · 819–871
praesentation inkl. `_praes_guard`/`_assemble_src`/`_assemble_md` ·
873–929 oauth · 931 statics; Middleware Z.486; Engine-Import-Block
Z.~340–380 inkl. `PPTX_PGSHIM=1` bei subprocess), `backend/slidesuche.py`
(`_bundle()` Z.96–115, `_ensure_engine`), `engine/scripts/pg_shim.py`
(Load/Normalisier/ANN Z.~50–97), `engine/scripts/assemble.py`
(Importe Z.36–39), `backend/migrate.py` (`_alembic_sync` Z.41ff),
`tools/sim_gate.sh`, `backend/tests/` (112 collect, 0 failed Baseline).

## 12. Bekannte Pitfalls

1. **Router-Extraktion ändert Reihenfolge:** Middleware/Auth-Gate und
   Static-Mount MÜSSEN in derselben Registrier-Reihenfolge bleiben —
   FastAPI-Routen-Matching und das Auth-Gate hängen daran. Vorher
   `app.routes`-Liste dumpen, nachher byte-gleich vergleichen.
2. **Modul-globale Konstanten:** Der Engine-Import-Block (ENGINE_OK,
   _ENG, sys.path.insert) und Gemini-Prompt-Konstanten leben auf
   Modulebene von app.py — beim Verschieben Import-Zyklen vermeiden
   (gemeinsames `backend/engine_glue.py` statt Router→app-Importe).
3. **Import-Analyse statt Namensraten beim Tooling-Split:** `slide_text`,
   `validate_assembled`, `render_previews` sehen nach Tooling aus —
   erst den transitiven Import-/subprocess-Graph von backend/* +
   assemble.py prüfen (auch String-Referenzen in subprocess-Aufrufen!).
4. **bundle.py-Ranking-Drift:** pg_shim sortiert mit Original-`<=>`-
   Semantik — die konsolidierte ANN muss bit-identische Reihenfolgen
   liefern (Vorher/Nachher-Goldvergleich, nicht „sieht gleich aus").
5. **Wegwerf-Postgres-Port-Kollision:** lokaler kf-Test-Postgres auf
   eigenem Port (≥15432), nie 5432/5434 (Build-Korpus-DB!).

## Referenzen
- implements → REQUIREMENTS R-REF-4, R-REF-3 (Teil), R-QA-3 (F-E-03, F-S-01)
- depends_on → [[KOCHFABRIK-ADR-003]] (accepted) · Sprint-11-Baseline
- relates_to → [[EPIC-004]] WP M4, M5, M6

## Referenziert von
— USER-STORIES Sprint 12 (US-052…US-056)
