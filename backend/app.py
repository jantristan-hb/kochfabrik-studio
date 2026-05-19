"""KOCHfabrik Studio — Backend (Phase 1: nur Bildgenerator).

Bewusst KEIN Präsentationsgenerator (Jans Vorgabe — der kommt später).
Framework-agnostischer Kern: image_kochfabrik() ist pure Logik, FastAPI
nur dünne API-Schicht (Web-App ODER später Electron-spawnbar).

Endpunkte:
  GET  /                → Design-2-Frontend (web/index.html)
  GET  /<page>.html     → statische Frontend-Seiten
  GET  /assets/*        → CSS/Logo
  POST /api/image {prompt}  → KOCHfabrik-Style-Bild (Gemini), base64-PNG
  GET  /api/health      → ok
"""
import base64
import json
import os
import urllib.request

from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
MODEL = os.environ.get("KF_IMG_MODEL", "gemini-3-pro-image-preview")
IMG_SIZE = os.environ.get("KF_IMG_SIZE", "2K")        # pro: 1K/2K/4K
IMG_ASPECT = os.environ.get("KF_IMG_ASPECT", "16:9")  # Food = landscape

# Foto-realistischer KOCHfabrik-Stil — jedem Motiv vorangestellt.
# Ziel: echtes Foto, KEIN KI-Look (Jan: "perfekte, realistische
# essens shots"). Kamera/Licht/Authentizität explizit, Brand dezent.
STYLE = (
    "Ultra-realistic professional food photograph, shot on a full-frame "
    "DSLR with an 85mm prime lens at f/2.8, soft natural window light, "
    "shallow depth of field, true-to-life colours and textures, fine "
    "surface detail, authentic hand-plated catering food, subtle natural "
    "imperfections, light steam, editorial fine-dining quality. Context: "
    "KOCHfabrik premium event catering — clean, modern, appetising "
    "presentation. This is a REAL PHOTOGRAPH — not an illustration, not a "
    "3D render, not AI art; no oversaturation, no plastic or waxy look, "
    "no artificial perfection, no text, no logo, no watermark. Motiv: ")


def _gemini_key():
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    env = os.path.expanduser("~/work/.env")
    if os.path.isfile(env):
        for ln in open(env):
            if ln.startswith("GEMINI_API_KEY="):
                return ln.split("=", 1)[1].strip().strip('"')
    return None


def image_kochfabrik(prompt: str) -> bytes:
    """Pure Logik: Prompt → KOCHfabrik-Style-PNG (bytes). Framework-frei."""
    key = _gemini_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY fehlt")
    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"models/{MODEL}:generateContent?key={key}")
    body = {
        "contents": [{"parts": [{"text": STYLE + prompt.strip()}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": IMG_ASPECT,
                            "imageSize": IMG_SIZE},
        },
    }
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    res = json.loads(urllib.request.urlopen(req, timeout=120).read())
    parts = (res.get("candidates", [{}])[0].get("content", {})
             .get("parts", []))
    for p in parts:
        if "inlineData" in p:
            return base64.b64decode(p["inlineData"]["data"])
    raise RuntimeError("Kein Bild in Gemini-Antwort")


app = FastAPI(title="KOCHfabrik Studio")


class ImgReq(BaseModel):
    prompt: str


@app.get("/api/health")
def health():
    return {"ok": True, "model": MODEL, "size": IMG_SIZE,
            "aspect": IMG_ASPECT, "key": bool(_gemini_key())}


@app.post("/api/image")
def api_image(r: ImgReq):
    if not r.prompt.strip():
        return JSONResponse({"error": "prompt leer"}, status_code=400)
    try:
        png = image_kochfabrik(r.prompt)
    except Exception as e:
        return JSONResponse({"error": str(e)[:200]}, status_code=502)
    return {"image": "data:image/png;base64,"
            + base64.b64encode(png).decode(), "model": MODEL}


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


# statisches Frontend (Design 2) zuletzt mounten
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
