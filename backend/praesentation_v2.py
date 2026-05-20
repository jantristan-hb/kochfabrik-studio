"""EPIC-002 Sprint 5 — Präsentationsgenerator v2 API-Router.

Strikt parallel zum alten /api/praesentation/*. Eigener Prefix, eigener
Router → Sprint-9-Refactor entfernt diese Datei + den include_router-
Call in app.py, fertig.

Routes:
- GET  /api/praesentation_v2/health        — Status + Kategorien
- GET  /api/praesentation_v2/suggestions   — 3-4 Slide-Vorschläge
- GET  /api/praesentation_v2/offer/{id}/slides   — aktuelle Auswahl
- PUT  /api/praesentation_v2/offer/{id}/slide    — Slide für Position setzen
- DELETE /api/praesentation_v2/offer/{id}/slides — Auswahl leeren
- POST /api/praesentation_v2/render-preview      — Preview-Stub (Sprint 7)
- POST /api/praesentation_v2/generate/{id}       — finales Deck-Stub

Multi-Tenant: Reads + Writes auf Offer scoped via Owner-Check (Cookie).
"""
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select

from backend import praesentation_v2_coherence as coherence
from backend import praesentation_v2_store as store
from backend.db import DB_OK, Session
from backend.models import Offer
from backend.praesentation_v2_models import KATEGORIEN


router = APIRouter(prefix="/api/praesentation_v2",
                   tags=["praesentation_v2"])


# ---------- Auth/Owner-Helpers (late import gegen Cycles) ----------

def _owner_email(request: Request) -> Optional[str]:
    """Owner aus Cookie — späte Import-Auflösung, weil app.py uns
    importiert."""
    from backend.app import _owner
    return _owner(request)


async def _owns_offer(session, owner: str, offer_id: int) -> bool:
    """Liefert True wenn `owner` Eigentümer der Offer ist. False sonst
    (inkl. 'nicht existent') — verhindert Cross-Tenant-Leaks."""
    stmt = select(Offer.owner_email).where(Offer.id == offer_id)
    r = (await session.execute(stmt)).scalar_one_or_none()
    return r is not None and r == owner


# ---------- Request-Bodies ----------

class SetSlideBody(BaseModel):
    position: int
    kategorie: str
    slide_id: Optional[int] = None
    overrides: Optional[dict] = None


class RenderPreviewBody(BaseModel):
    kategorie: str
    payload: dict
    overrides: Optional[dict] = None


class ChatBody(BaseModel):
    message: str
    overrides: Optional[dict] = None
    kategorie: Optional[str] = None
    offer_id: Optional[int] = None


# ---------- Routes ----------

@router.get("/health")
async def health():
    """Liveness + Kategorien-Manifest (FE braucht das für Tabs)."""
    return {"ok": True, "db": DB_OK,
            "kategorien": list(KATEGORIEN),
            "version": "v2.0-sprint5"}


@router.get("/suggestions")
async def get_suggestions(kategorie: str, limit: int = 4):
    """3-4 Slide-Vorschläge je Kategorie. Auth nicht zwingend — der
    Katalog ist nicht tenant-spezifisch (nur Auswahl pro Offer ist es).
    """
    if not DB_OK or Session is None:
        return JSONResponse({"error": "db unavailable"},
                            status_code=503)
    if kategorie not in KATEGORIEN:
        return JSONResponse({"error": f"unbekannte kategorie: "
                             f"{kategorie}",
                             "erlaubt": list(KATEGORIEN)},
                            status_code=400)
    limit = max(1, min(int(limit), 8))
    async with Session() as s:
        items = await store.suggestions(s, kategorie, limit)
        # Lazy-Seed: wenn Katalog für die Kategorie noch leer ist
        # → 3 Default-Karten erzeugen + sofort liefern. Damit erscheint
        # nach Erst-Deploy ohne Admin-Eingriff sofort Inhalt im UI.
        if not items:
            await store.seed_default_slides(s)
            await s.commit()
            items = await store.suggestions(s, kategorie, limit)
    return {"kategorie": kategorie, "items": items}


@router.get("/offer/{offer_id}/slides")
async def list_offer_slides(offer_id: int, request: Request):
    """Aktuelle Slide-Auswahl der Offer. Owner-scoped."""
    owner = _owner_email(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    if not DB_OK or Session is None:
        return JSONResponse({"error": "db unavailable"},
                            status_code=503)
    async with Session() as s:
        if not await _owns_offer(s, owner, offer_id):
            return JSONResponse({"error": "forbidden"},
                                status_code=403)
        items = await store.get_offer_slides(s, offer_id)
    return {"offer_id": offer_id, "items": items}


@router.put("/offer/{offer_id}/slide")
async def put_offer_slide(offer_id: int, body: SetSlideBody,
                          request: Request):
    """Slide für Position setzen (upsert). Persistiert die Auswahl."""
    owner = _owner_email(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    if not DB_OK or Session is None:
        return JSONResponse({"error": "db unavailable"},
                            status_code=503)
    if body.kategorie not in KATEGORIEN:
        return JSONResponse({"error": "kategorie"}, status_code=400)
    async with Session() as s:
        if not await _owns_offer(s, owner, offer_id):
            return JSONResponse({"error": "forbidden"},
                                status_code=403)
        try:
            rec_id = await store.set_offer_slide(
                s, offer_id, body.position, body.kategorie,
                body.slide_id, body.overrides)
            await s.commit()
        except Exception as e:
            await s.rollback()
            return JSONResponse({"error": f"db: {type(e).__name__}"},
                                status_code=500)
    return {"id": rec_id, "offer_id": offer_id,
            "position": body.position}


@router.delete("/offer/{offer_id}/slides")
async def delete_offer_slides(offer_id: int, request: Request):
    """Auswahl leeren (vor Neu-Generierung)."""
    owner = _owner_email(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    if not DB_OK or Session is None:
        return JSONResponse({"error": "db unavailable"},
                            status_code=503)
    async with Session() as s:
        if not await _owns_offer(s, owner, offer_id):
            return JSONResponse({"error": "forbidden"},
                                status_code=403)
        n = await store.clear_offer_slides(s, offer_id)
        await s.commit()
    return {"deleted": n, "offer_id": offer_id}


@router.post("/render-preview")
async def render_preview(body: RenderPreviewBody):
    """Stub für Realtime-Slide-Preview. Sprint 7 implementiert echtes
    PPTX→PNG-Caching. Hier: synthetisches Preview-Payload, damit das
    FE seine Vorschau-Logik schon entwickeln kann."""
    if body.kategorie not in KATEGORIEN:
        return JSONResponse({"error": "kategorie"}, status_code=400)
    merged = dict(body.payload or {})
    merged.update(body.overrides or {})
    # Stub: gibt 'preview-Manifest' zurück; FE rendert das.
    return {"kategorie": body.kategorie, "merged": merged,
            "preview_url": "", "synthetic": True,
            "hint": "Sprint 7 liefert echtes preview_url"}


@router.get("/offer/{offer_id}/context")
async def get_offer_context(offer_id: int, request: Request):
    """Kohärenz-Endpoint: gibt für jede Kategorie Default-Overrides
    aus dem verknüpften Angebot zurück. FE benutzt das beim Slide-
    Anlegen → Kunde/Veranstaltung/Konzept landen automatisch in den
    Slides (Akzeptanzkriterium 5)."""
    owner = _owner_email(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    if not DB_OK or Session is None:
        return JSONResponse({"error": "db unavailable"},
                            status_code=503)
    async with Session() as s:
        offer = await coherence.offer_context(s, owner, offer_id)
        if offer is None:
            return JSONResponse({"error": "not found / forbidden"},
                                status_code=404)
    defaults = {k: coherence.defaults_for(k, offer)
                for k in KATEGORIEN}
    # Kurzfassung der Offer-Felder für Header/Anzeige im FE
    short = {
        "kunde": offer.get("kunde", ""),
        "anlass": (offer.get("veranstaltung") or {}).get("anlass", ""),
        "v_datum": (offer.get("veranstaltung") or {}).get("datum", ""),
        "konzept": (offer.get("veranstaltung") or {}).get("konzept", ""),
        "ort": (offer.get("veranstaltung") or {}).get("ort", ""),
    }
    return {"offer_id": offer_id, "short": short,
            "defaults_per_kategorie": defaults}


@router.post("/chat")
async def chat_patch(body: ChatBody, request: Request):
    """LLM-Editor: User schreibt 'Mach Titel kürzer' o.ä. → Slide-
    Overrides werden gepatcht. Pattern wie /api/angebot/chat. Graceful
    bei fehlendem ANTHROPIC_API_KEY (returns synthetic).

    KEIN State-Touch in DB — FE bekommt zurück + persistiert separat
    via PUT /offer/{}/slide."""
    owner = _owner_email(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    if not body.message.strip():
        return JSONResponse({"error": "empty message"}, status_code=400)

    # Offer-Kontext optional einbinden (Akzeptanzkriterium 5)
    ctx_short = {}
    if body.offer_id is not None and DB_OK and Session is not None:
        async with Session() as s:
            offer = await coherence.offer_context(s, owner, body.offer_id)
            if offer:
                v = offer.get("veranstaltung") or {}
                ctx_short = {"kunde": offer.get("kunde", ""),
                             "anlass": v.get("anlass", ""),
                             "konzept": v.get("konzept", ""),
                             "ort": v.get("ort", ""),
                             "v_datum": v.get("datum", "")}

    # LLM-Aufruf — late import + graceful (kein crash wenn key fehlt)
    try:
        from backend.app import _akey, _AMODEL
        from anthropic import Anthropic
        import json as _json
        client = Anthropic(api_key=_akey())
        prompt = (
            "Du editierst Slide-Overrides für eine Präsentation. "
            f"KATEGORIE: {body.kategorie or 'unbekannt'}. "
            f"OFFER-KONTEXT: {_json.dumps(ctx_short, ensure_ascii=False)}. "
            f"AKTUELLE OVERRIDES: {_json.dumps(body.overrides or {}, ensure_ascii=False)}. "
            f"USER-WUNSCH: {body.message}. "
            "Gib ausschließlich ein striktes JSON-Object mit Feldern "
            "titel, untertitel, bullets (Liste). Keine Kommentare, "
            "keine Code-Fences."
        )
        msg = client.messages.create(
            model=_AMODEL, max_tokens=600,
            messages=[{"role": "user", "content": prompt}])
        txt = "".join(b.text for b in msg.content
                      if getattr(b, "type", "") == "text").strip()
        # Code-Fences strippen falls trotzdem da
        if txt.startswith("```"):
            txt = "\n".join(l for l in txt.splitlines()
                            if not l.startswith("```"))
        patched = _json.loads(txt)
    except Exception as e:
        # Graceful: kein LLM → echo + Hint zurück
        return {"patched": body.overrides or {},
                "reply": ("(LLM nicht verfügbar — bitte direkt im "
                          f"Formular editieren. Detail: {type(e).__name__})"),
                "synthetic": True}

    return {"patched": patched,
            "reply": "Aktualisiert. Schau dir die Slide-Vorschau an.",
            "synthetic": False}


@router.post("/generate/{offer_id}")
async def generate_deck(offer_id: int, request: Request):
    """Stub für finale Deck-Generierung. Sprint 6+ implementiert die
    Engine-Pipeline (Slide-Auswahl + Overrides → PPTX). Aktuell:
    Manifest-Echo + Slide-Auswahl der Offer zurück."""
    owner = _owner_email(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    if not DB_OK or Session is None:
        return JSONResponse({"error": "db unavailable"},
                            status_code=503)
    async with Session() as s:
        if not await _owns_offer(s, owner, offer_id):
            return JSONResponse({"error": "forbidden"},
                                status_code=403)
        slides = await store.get_offer_slides(s, offer_id)
    return {"offer_id": offer_id, "slides_selected": slides,
            "deck_url": "", "synthetic": True,
            "hint": "Sprint 6+: echte PPTX-Generierung"}
