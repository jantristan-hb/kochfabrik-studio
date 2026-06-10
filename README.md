# KOCHfabrik Studio

Web-App (FastAPI + Design-2-Frontend) mit drei Modulen, live auf
**https://kochfabrik-studio.flinkbase.com** (Coolify, Standard-Hetzner).

| Modul | Seite | API | Was es tut |
|-------|-------|-----|------------|
| **Bildgenerator** | `web/bildgenerator.html` → `web/gen.html?cat=` | `/api/cats`, `/api/image` | Chat → KOCHfabrik-Style-Bild (7 Kategorien, Gemini) |
| **Angebotsgenerator** | `web/chat.html` | `/api/angebot/{health,chat,pdf}` | Chat **+ Hand-Edit-Formular** → Angebots-**PDF** jederzeit |
| **Präsentationsgenerator** | `web/praesentationsgenerator.html` | `/api/praesentation/{health,generate}` | Angebot rein → kanonisches KOCHfabrik-**Deck** (PPTX) |

> ℹ️ **`engine/` ist repo-intern** (Monorepo via git-subtree, ADR-002)
> mit eigener Git-Historie — direkt hier entwickeln. Siehe
> [Engine im Monorepo](#engine-im-monorepo).

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
├── engine/               ⚙️ Engine repo-intern (subtree, eigene Historie)
│   ├── scripts/*.py      assemble.py, compose_offer.py, angebot_*.py,
│   │                     kf_classify.py, pg_shim.py, _deckpipe.py …
│   ├── spike-pptxgenjs/  reconstruct.js + lib/ + node_modules/ (pptxgenjs)
│   ├── data/             cover/ausstattung/angebot_template.elements.json,
│   │                     pgbundle.npz (DB-Snapshot), static_slide.json,
│   │                     cache/<ref-slug>/  (1 Referenz-Slug; Voll-Cache
│   │                                         = Server-Volume, s. Deploy)
│   ├── tests/            Engine-Tests (ex phase0/tests)
│   └── upstream/         Engine-Repo-Reste (docs/, design/, fixtures …)
├── Dockerfile            python:3.12-slim + nodejs + LibreOffice + poppler-utils + COPY engine
├── requirements.txt      fastapi uvicorn pydantic anthropic python-pptx numpy
└── README.md             dieses Dokument
```

**Engine-Historie:** als Subtree aus `jantristan-hb/pptxgenerator_v2`
(branch `main`) eingezogen — `git log -- engine/` zeigt die volle
Engine-Historie. Upstream-Reste (docs/, design/) liegen unter
`engine/upstream/`.

---

## Engine im Monorepo

Die Engine liegt repo-intern unter `engine/` (git-subtree, ADR-002) mit
eigener Git-Historie. **Kein Vendoring, kein Schwester-Repo, kein
`vendor.sh` mehr** — Engine-Änderungen werden direkt in `engine/`
committet und mit dem Studio-Code gemeinsam versioniert.

**Bei JEDER Engine-Änderung (Präsentations-/Angebotsgenerator):**

```
1. Direkt in engine/scripts/ (bzw. engine/spike-pptxgenjs/) entwickeln
2. Tests grün halten: tools/.venv/bin/python -m pytest backend/tests -q
3. git add engine backend && git commit && git push   # Feature-Branch
4. Coolify force-deploy (s.u.) — Push triggert NICHT
```

> Die Engine kann optional via `git subtree push`/`pull` mit dem
> Upstream-Repo `jantristan-hb/pptxgenerator_v2` synchronisiert bleiben;
> für den Studio-Betrieb ist `engine/` aber autark.

### Zwei Snapshot-Fallen (sonst stille Drift)

1. **`engine/data/pgbundle.npz`** = eingefrorener Snapshot von
   `pptxgen-pg` (`menu_composition` + `static_slide` + Embeddings).
   Ändert sich die DB → `pgbundle.npz` neu aus der Live-DB regenerieren
   und committen. Im Container ersetzt `pg_shim.py` Postgres 1:1 (Picks
   byte-identisch verifiziert) — **kein DB-Zugriff zur Laufzeit**,
   `PPTX_PGSHIM=1`.
2. **Korpus-Cache (~4,8 GB, 200 Deck-Dirs)** liegt NICHT im Image,
   sondern als **Coolify-Volume** auf dem Server (s. Deployment). Neue
   Korpus-Decks → zusätzlich rsync, sonst rendert der
   Präsentationsgenerator alte/fehlende Decks.

### Static Slide ändern/hinzufügen → bereitstellen

Static Slides (Cover · CREW · PERSONAL · KONTAKT · WERTSCHÄTZUNG ·
**AUSSTATTUNG/Location**) sind **kein Template/Token** mehr, sondern
alle derselbe Mechanismus, alles an einem Ort:

- **`static_slide`-Row** in der Live-DB `pptxgen-pg`
  (`localhost:5434`, db `pptxgen`) — Spalten u.a. `category`,
  `deck`, `page`, `skel_pos`, `inclusion`, `tier`, `is_golden`.
  UNIQUE(`deck`,`page`). `inclusion='pflicht'` ⇒ `assemble.py`
  `pick_frame` zieht sie deterministisch (kunden-stabil) und rendert
  das zugehörige Cache-Deck **verbatim**.
- **Cache-Deck** `engine/data/cache/<slug>/`:
  `elements.json` (`{"1":[…],"_meta":{"w_pt":960,"h_pt":540,
  "deck":"<slug>"}}`), `assets/<bild>`, `logos.json` (`{}` reicht →
  `resolve(src)=src`). Bild-`src` = `"<slug>/assets/<datei>"`.
  Text: `reconstruct` rendert mit **`wrap:false`** (kein Reflow →
  Zeilen manuell brechen) und **eff. Größe = `size · 0.78`** (SIZE_K).
  Canvas 13,333 × 7,5 in. Foto als `.jpg` (klein halten, ~≤500 KB).

**Bereitstellen (end-to-end, genau dieser Ablauf):**

```
1. Cache-Deck bauen in engine/data/cache/<slug>/
   (cache/ ist gitignored → lebt nur lokal + DB + Server-Volume;
    der eine Referenz-Slug ist getrackt, der Voll-Korpus nicht)
2. static_slide-Row in pptxgen-pg setzen/ändern, z.B.:
   UPDATE static_slide SET deck='<slug>',page=1,inclusion='pflicht',
     tier='T',is_golden=true,skel_pos=0.78 WHERE category='…';
   (DB-Creds aus ~/work/.env — nie im Repo)
3. pgbundle.npz + static_slide.json aus der Live-DB regenerieren
   (engine/data/) und das autorisierte Static-Deck nach
   engine/data/cache/<slug>/ legen (KEIN Korpus — gehört INS Repo)
4. rsync das Static-Deck aufs Server-Volume:
   # PFLICHT: data/cache ist Coolify Directory Mount → das committete
   # Deck wird zur Laufzeit ÜBERLAGERT; authoritativ ist das Volume
   rsync -a -e "ssh -i ~/.ssh/hetzner_id" engine/data/cache/<slug>/ \
     root@188.245.110.5:/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache/<slug>/
5. git add engine && git commit && git push   # Feature-Branch, NICHT master
6. Coolify force-deploy (s.u.)
7. Verify am Server (auth-frei, autoritativ):
   ssh -i ~/.ssh/hetzner_id root@188.245.110.5
   CID=$(docker ps -q --filter name=<APP-UUID>)
   docker exec $CID python3 -c "import json;print([x for x in \
     json.load(open('/app/engine/data/static_slide.json')) \
     if x['category']=='<CAT>'])"
   docker exec $CID ls /app/engine/data/cache/<slug>/assets/
```

> **Secrets:** DB-Creds (`pptxgen-pg`), `COOLIFY_TOKEN`,
> `GEMINI_API_KEY`/`ANTHROPIC_API_KEY`, SSH-Key-Pfad — **alle in
> `~/work/.env`** (bzw. `~/.ssh/hetzner_id`). Nie ins Repo/README,
> nie hardcoden. Prod-Runtime liest sie als Coolify-ENV (s.u.).

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
| Destination (Container) | `/app/engine/data/cache` |

Daten auf den Host bringen / aktualisieren:
```
rsync -a -e "ssh -i ~/.ssh/hetzner_id" \
  "engine/data/cache/" \
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
# Studio lokal (Engine wird repo-intern aus engine/scripts geladen):
KF_SESSION_SECRET=dev KF_USERS="t@t|s|x" \
  uvicorn backend.app:app --port 8000
# Login-Cookie: python -c "from backend.app import make_cookie;print(make_cookie('t@t'))"

# Engine direkt (repo-intern, volle DB+Cache):
cd engine/scripts
python3 assemble.py <offer.md|pdf> -o out.pptx        # Präsentation
python3 angebot_render.py <angebot.json> -o out.pdf   # Angebot
PPTX_PGSHIM=1 python3 assemble.py …                   # DB-frei (wie Container)
```

## Tests lokal

> **Python ≥ 3.10 zwingend.** Backend- und Engine-Code nutzen PEP-604-Typen
> (`str | None`). System-Python 3.9 wirft beim Collect `TypeError` und bricht
> ab. Auf macOS daher gegen `/opt/homebrew/bin/python3.13` ein venv anlegen
> (System-Python ist 3.9).

```bash
# venv anlegen (httpx = Test-Dep für fastapi.testclient, NICHT in requirements.txt)
/opt/homebrew/bin/python3.13 -m venv tools/.venv
tools/.venv/bin/pip install pytest httpx -r requirements.txt

# Volle Suite (DB-Tests skippen ohne TEST_DATABASE_URL — kein Fehler):
tools/.venv/bin/python -m pytest backend/tests -q

# DB-Integration zusätzlich (gegen Test-Postgres):
TEST_DATABASE_URL=postgresql://… tools/.venv/bin/python -m pytest backend/tests -q
```

`backend/tests/test_charakterisierung.py` ist das DB-lose HTTP-Verhaltens-Netz
(TestClient): friert vor dem Monorepo-Schnitt das IST-Verhalten der Routen ein
(Health-Shape, Auth-Gate-Status, statische Seiten). Die `tools/.venv/` ist
nicht eingecheckt.

## System-Dependencies (Container — Dockerfile)

Engine-Pfade brauchen mehr als Python. Fehlt eins → Modul-Endpoint 502.

| apt-Paket | Wofür | Symptom wenn weg |
|-----------|-------|------------------|
| `nodejs` | `reconstruct.js` (pptxgenjs) | reconstruct rc≠0 |
| `libreoffice-impress` + `-core` | pptx→pdf (Angebots-PDF) | soffice pptx→pdf fehlgeschlagen |
| `poppler-utils` | `pdftotext`/`pdfinfo`/`pdftoppm` — PDF-**Input** des Präsentationsgen. | `FileNotFoundError` aus innerem subprocess |
| `fonts-dejavu-core` `fonts-liberation` | faithful Text-Render | falsche/fehlende Glyphen |

Python (`requirements.txt`): fastapi · uvicorn · pydantic · anthropic ·
python-pptx · **numpy** (compose_offer/pg_shim/assemble) ·
**python-multipart** (PDF-Upload `UploadFile`).

## Deploy verifizieren

Push triggert NICHT — immer force-deployen, dann prüfen. Build-Zeit:
nur `engine/`-Änderung = schnell (COPY-Layer); `requirements.txt` =
pip-Layer neu; **`Dockerfile`-apt-Zeile = ~5–8 min** (LibreOffice).
Coolify-Build **atomar**: Fehlbuild ⇒ alte Version bleibt live.

```bash
# Login → Cookie → Health aller Module
python3 - <<'PY'
import json,urllib.request as u
B="https://kochfabrik-studio.flinkbase.com"
r=u.urlopen(u.Request(B+"/api/login",json.dumps(
 {"email":"<user>","password":"<pw>"}).encode(),
 {"Content-Type":"application/json"}))
ck=r.headers["set-cookie"].split(";")[0]
for p in ("/api/health","/api/angebot/health","/api/praesentation/health"):
  print(p, u.urlopen(u.Request(B+p,headers={"Cookie":ck})).read())
PY
```
`praesentation/health` muss `engine:true, korpus:true` zeigen.
**405 auf `/api/...`** = Route fehlt im laufenden Container (POST fällt
auf StaticFiles-Mount) ⇒ neuer Build noch nicht geswappt → warten/force.

## Troubleshooting (real durchlebte Failure-Modes)

| Symptom | Ursache | Fix |
|---------|---------|-----|
| `ModuleNotFoundError: numpy` (502) | Dep fehlt im Image | `requirements.txt` ergänzen → rebuild |
| `FileNotFoundError ~/work/.env` in `_key` | Host-Pfad im Container | `_key()` env-first (schon gefixt); API-Key als Coolify-ENV |
| `os.listdir(CORPUS_DIR)` crash | Nextcloud fehlt im Container | CORPUS_DIR-Guard (gefixt) — Cache-Hits brauchen Quelle nicht |
| `cover_template.elements.json` not found | Template fehlt im Repo | gehört committet in `engine/data/` |
| `copyfile('')` / Cache-Miss | `cached_deck(src)` slugifizierte Nextcloud-Pfad | `load()` löst über **deck-Slug** auf (gefixt) |
| PDF-Upload 502 `subprocess FileNotFoundError` | `pdftotext` fehlt | `poppler-utils` ins Dockerfile |
| `korpus:false`, Präsentation 503 | 4,8-GB-Cache-Volume nicht gemountet | Coolify Directory Mount (s. Deployment) |
| `405` auf neuem Endpoint | alter Container (kein Auto-Deploy) | Coolify force-deploy, Build abwarten |
| Studio-Modul down nach Push | — kann nicht passieren | atomarer Build; alte Version bleibt live |

**Goldene Regel:** vor jedem Deploy den Container-Pfad-Sim laufen
lassen (`HOME=/nonexistent PPTX_PGSHIM=1` gegen vollen lokalen Cache)
— fängt genau diese Fehler VOR dem ~Minuten-Deploy-Zyklus. Das
eigenständige Sim-Gate (`tools/sim_gate.sh`, Nachfolger der
vendor.sh-Logik) kommt mit US-050.

## Host-Zugriff / Debug

```bash
ssh -i ~/.ssh/hetzner_id root@188.245.110.5      # Coolify-Host (CAX21)
docker ps | grep yu2fqx0                          # laufender Studio-Container
docker exec -it <id> bash                         # rein (Engine prüfen)
docker logs --tail=100 <id>                        # App-Logs
ls /data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache | wc -l  # Cache-Mount (≈200)
```
Coolify-Token: `~/work/.env` → `COOLIFY_TOKEN`. SSH-Key `~/.ssh/hetzner_id`.

## Benutzerverwaltung

User werden **von Hand** verwaltet, Format `KF_USERS` =
`email|salt|sha256(salt + ":" + pw)` (mehrere `;`-getrennt) als
Coolify-ENV. Passwörter/Secrets NIE in Repo/README — Single Source ist
`~/work/.env` (lokal) bzw. Coolify-ENV (Prod). Neuen User: Salt+Hash
lokal bilden, an `KF_USERS` anhängen, Coolify-ENV updaten, redeploy.
Session = HMAC-signiertes Cookie (`KF_SESSION_SECRET`).

## API-Referenz (alle Endpoints hinter Auth-Cookie)

```
POST /api/login {email,password}            → set-cookie
POST /api/logout
GET  /api/health                            (public) Modell/Key/cats
GET  /api/cats                               Bildgenerator-Kategorien
POST /api/image {prompt,table,category}     → Bild (base64)
GET  /api/angebot/health
POST /api/angebot/chat {message,angebot}    → Angebot-JSON (LLM-Patch)
POST /api/angebot/pdf  {angebot}            → Angebots-PDF (base64)
GET  /api/praesentation/health              engine+korpus
POST /api/praesentation/generate {offer}    → Deck-PPTX (Offer-md)
POST /api/praesentation/from-angebot {angebot} → Deck (Übernahme)
POST /api/praesentation/from-pdf  (multipart file) → Deck (PDF-Upload)
```

## Architektur-Prinzipien

- **Graceful Degradation:** fehlt Engine/Cache → 503 mit Klartext,
  App + andere Module laufen weiter. Nie harter Crash.
- **Single Source:** Engine-Logik lebt repo-intern in `engine/`
  (subtree mit eigener Historie) — eine Quelle, kein Vendoring.
- **Container-tauglich:** keine fixen Host-Pfade (env-first Keys,
  CORPUS_DIR/Nextcloud-Guards, Cache über deck-Slug statt src-Pfad).
- **Pixel-Treue:** `extract.py`/`reconstruct.js`/`lib/` unverändert
  (Spike-Kern), nur darüberliegende Orchestrierung.
