# KOCHfabrik Studio

Web-App (Phase 1: **nur Bildgenerator** — Chat rein → Bild im
KOCHfabrik-Style raus. Präsentationsgenerator bewusst NOCH NICHT
eingebaut). Frontend = Design 2. Backend = FastAPI, framework-
agnostischer Kern (`image_kochfabrik`), später Electron-spawnbar.

## Lokal
```
GEMINI_API_KEY=... uvicorn backend.app:app --reload --port 8000
# http://localhost:8000  → Design-2 Studio
# http://localhost:8000/bildgenerator.html  → Bildgenerator (funktional)
```
Key wird auch aus ~/work/.env gelesen (lokal).

## Deploy (Standard-Hetzner / Coolify, NICHT Bülent)
Dockerfile vorhanden. Coolify-App auf coolify.flinkbase.com,
ENV `GEMINI_API_KEY` setzen. Remote-DB (pgvector) separat — der
Präsentations-Teil kommt erst nach dem Bildgenerator.

## API
- `GET /api/health` → {ok, model, key}
- `POST /api/image` {prompt} → {image: data:image/png;base64,…, model}
