"""Bildgenerator-Router (US-053) — Kategorien + Bild-Generierung.

1:1 aus app.py extrahiert (cats/image). Bild-Kern, Kategorien und die
Gemini-Prompt-Konstanten liegen in backend.engine_glue (kein Import auf
app.py — Pitfall 2). Verhalten unverändert."""
import base64
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..engine_glue import CATS, MODEL, image_kochfabrik

router = APIRouter()


class ImgReq(BaseModel):
    prompt: str
    table: bool = True
    category: str = "food"


@router.get("/api/cats")
def api_cats():
    return {"cats": [{"key": k, "label": v["label"], "hint": v["hint"],
                      "icon": v["icon"], "table": v["table"],
                      "chips": v["chips"]} for k, v in CATS.items()]}


@router.post("/api/image")
def api_image(r: ImgReq):
    if not r.prompt.strip():
        return JSONResponse({"error": "prompt leer"}, status_code=400)
    cat = r.category if r.category in CATS else "food"
    try:
        png, bg = image_kochfabrik(r.prompt, r.table, cat)
    except Exception as e:
        return JSONResponse({"error": str(e)[:200]}, status_code=502)
    return {"image": "data:image/png;base64,"
            + base64.b64encode(png).decode(), "model": MODEL,
            "bg": os.path.basename(bg) if bg else None}
