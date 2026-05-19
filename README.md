# KOCHfabrik Studio

Web-App (FastAPI + Design-2-Frontend) mit drei Modulen, live auf
**https://kochfabrik-studio.flinkbase.com** (Coolify, Standard-Hetzner).

| Modul | Seite | API | Was es tut |
|-------|-------|-----|------------|
| **Bildgenerator** | `web/bildgenerator.html` → `web/gen.html?cat=` | `/api/cats`, `/api/image` | Chat → KOCHfabrik-Style-Bild (7 Kategorien, Gemini) |
| **Angebotsgenerator** | `web/chat.html` | `/api/angebot/{health,chat,pdf}` | Chat **+ Hand-Edit-Formular** → Angebots-**PDF** jederzeit |
| **Präsentationsgenerator** | `web/praesentationsgenerator.html` | `/api/praesentation/{health,generate}` | Angebot rein → kanonisches KOCHfabrik-**Deck** (PPTX) |

> ⚠️ **`engine/` NIEMALS von Hand editieren** — generiert aus der
> Single Source `pptxgenerator_v2`. Siehe [Engine-Sync](#engine-sync).

---

## Projektstruktur

```
kochfabrik-studio/
├── backend/app.py        FastAPI: Auth-Gate (HMAC-Cookie), Module,
│                         graceful Engine-Import (ENGINE_OK), Endpoints
├── web/                  Design-2 Frontend (kanonische Sidebar je Seite)
│   ├── index.html        Dashboard
│   ├── chat.html         Angebotsgenerator (Chat + Editor + PDF)
│   ├── praesentationsgenerator.html  Präsentationsgenerator
│   ├── bildgenerator.html / gen.html Bildgenerator-Hub + Generator
│   ├── login.html  client.html  bibliothek.html  upload.html  vorschau.html
│   └── assets/style.css  Design-2 (Gold/Weiß), kochfabrik-logo.png, bg/
├── engine/phase0/        ⚙️ VENDORED Engine-Bundle (generiert!)
│   ├── scripts/*.py      assemble.py, compose_offer.py, angebot_*.py,
│   │                     kf_classify.py, pg_shim.py, _deckpipe.py …
│   ├── spike-pptxgenjs/  reconstruct.js + lib/ + node_modules/ (pptxgenjs)
│   └── data/             cover/ausstattung/angebot_template.elements.json,
│                         pgbundle.npz (DB-Snapshot), static_slide.json,
│                         cache/<ref-slug>/  (1 Referenz-Slug; Voll-Cache
│                                             = Server-Volume, s. Deploy)
├── Dockerfile            python:3.12-slim + nodejs + LibreOffice + COPY engine
├── requirements.txt      fastapi uvicorn pydantic anthropic python-pptx numpy
├── vendor.sh             ⭐ Ein-Befehl Engine-Sync (s.u.)
└── README.md             dieses Dokument
```

**Single Source der Engine:** `~/work/03 AKARA Solutions GmbH/kochfabrik/pptxgenerator_v2/phase0/`
(eigenes GitHub-Repo `jantristan-hb/pptxgenerator_v2`, EPIC-001 dort).

---

## Engine-Sync

Die Engine lebt in `pptxgenerator_v2`. Studio enthält eine **vendored
Kopie** (~13 MB) unter `engine/`, weil der Coolify-Container kein
Schwester-Repo / kein Postgres / kein Nextcloud hat.

**Bei JEDER Engine-Änderung (Präsentations-/Angebotsgenerator):**

```
1. In pptxgenerator_v2/phase0/ entwickeln  (= Single Source)
2. cd kochfabrik-studio && ./vendor.sh      # re-vendor + pgbundle-Regen
                                            # + Container-Pfad-Sim-GATE
3. git add engine && git commit && git push
4. ./vendor.sh --deploy                     # ODER Coolify force-deploy
```

`vendor.sh` kopiert Scripts + spike + Templates + Referenz-Cache-Slug,
**regeneriert `pgbundle.npz` aus der Live-DB** und fährt ein
Container-Pfad-Sim (`HOME=/nonexistent`, `PPTX_PGSHIM=1`) gegen den
vollen lokalen Cache — schlägt der fehl, **NICHT deployen**.

### Zwei Snapshot-Fallen (sonst stille Drift)

1. **`engine/phase0/data/pgbundle.npz`** = eingefrorener Snapshot von
   `pptxgen-pg` (`menu_composition` + `static_slide` + Embeddings).
   Ändert sich die DB → `vendor.sh` neu laufen lassen (regeneriert es).
   Im Container ersetzt `pg_shim.py` Postgres 1:1 (Picks byte-identisch
   verifiziert) — **kein DB-Zugriff zur Laufzeit**, `PPTX_PGSHIM=1`.
2. **Korpus-Cache (~4,8 GB, 200 Deck-Dirs)** liegt NICHT im Image,
   sondern als **Coolify-Volume** auf dem Server (s. Deployment). Neue
   Korpus-Decks → zusätzlich rsync, sonst rendert der
   Präsentationsgenerator alte/fehlende Decks.

---

## Deployment (Coolify)

| | |
|---|---|
| Panel | `coolify.flinkbase.com` (Standard-Hetzner CAX21, **NICHT Bülent**) |
| App | **„kochfabrik-studio"** — *Application* im Projekt **„My first project"** (es gibt KEIN Projekt „kochfabrik-studio") |
| App-UUID | `yu2fqx0twmtqcp6zyx2e59si` · Server `188.245.110.5` |
| Repo | `github.com/jantristan-hb/kochfabrik-studio` branch `master`, Dockerfile-Build |
| **Kein Auto-Deploy** | Push auf master triggert NICHT. Deploy nur via Coolify-UI „Redeploy" oder API force: |

```
curl "https://coolify.flinkbase.com/api/v1/deploy?uuid=yu2fqx0twmtqcp6zyx2e59si&force=true" \
     -H "Authorization: Bearer $COOLIFY_TOKEN"
```
Builds sind **atomar**: schlägt der Build fehl, bleibt die alte Version
live (Prod nie gefährdet). Coolify hat auf dieser Version **keine
Storage-API** (alle Endpoints 404) → Volume nur per UI.

### Persistent Storage (Korpus-Cache, einmalig)

Coolify → „My first project" → App `kochfabrik-studio` → **Storages →
Add Directory Mount**:

| Feld | Wert |
|---|---|
| Source (Host) | `/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache` |
| Destination (Container) | `/app/engine/phase0/data/cache` |

Daten auf den Host bringen / aktualisieren:
```
rsync -a -e "ssh -i ~/.ssh/hetzner_id" \
  "<pptxgenerator_v2>/phase0/data/cache/" \
  root@188.245.110.5:/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache/
```
Mount persistiert über Deploys. Fehlt er → `/api/praesentation/health`
`korpus:false`, Endpoint liefert graceful 503 (Bild-/Angebotsgenerator
laufen weiter).

### Environment (Coolify-ENV, secrets)

`GEMINI_API_KEY` (Bildgenerator), `ANTHROPIC_API_KEY` (Angebots-/
Präsentations-Chat), `KF_USERS` (`email|salt|sha256(salt:pw)`),
`KF_SESSION_SECRET`. Coolify legt bei POST Doppel-Einträge an —
harmlos. `_key()` in der Engine ist env-first (Container) mit
`~/work/.env`-Fallback (lokale Dev).

---

## Lokal entwickeln / laufen

```
# Studio lokal (vendored Engine wird vendored-first geladen):
KF_SESSION_SECRET=dev KF_USERS="t@t|s|x" \
  uvicorn backend.app:app --port 8000
# Login-Cookie: python -c "from backend.app import make_cookie;print(make_cookie('t@t'))"

# Engine direkt (Single Source, volle DB+Cache):
cd <pptxgenerator_v2>/phase0/scripts
python3 assemble.py <offer.md|pdf> -o out.pptx        # Präsentation
python3 angebot_render.py <angebot.json> -o out.pdf   # Angebot
PPTX_PGSHIM=1 python3 assemble.py …                   # DB-frei (wie Container)
```

## Architektur-Prinzipien

- **Graceful Degradation:** fehlt Engine/Cache → 503 mit Klartext,
  App + andere Module laufen weiter. Nie harter Crash.
- **Single Source:** Engine-Logik nur in `pptxgenerator_v2`. `engine/`
  ist Build-Artefakt (`vendor.sh`).
- **Container-tauglich:** keine fixen Host-Pfade (env-first Keys,
  CORPUS_DIR/Nextcloud-Guards, Cache über deck-Slug statt src-Pfad).
- **Pixel-Treue:** `extract.py`/`reconstruct.js`/`lib/` unverändert
  (Spike-Kern), nur darüberliegende Orchestrierung.
