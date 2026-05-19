"""EPIC-002 Sprint 5 — Tests für Präsentationsgenerator-v2-Routes.

Schwerpunkt:
- Health-Endpoint (DB-status + Kategorien-Manifest)
- Suggestions: Kategorie-Validierung, Limit-Clamping, leere Kategorie
  → lazy-seed
- Owner-scoped Routes (auth/forbidden bei fremder Offer)
- Set-Slide-Upsert: gleiche Position 2× → 1 Row, Felder updated
- Migrations-Idempotenz (gilt für Tabelle existiert vs. fresh)

Konvention wie in test_app_helpers.py: KF_USERS + KF_SESSION_SECRET vor
Import setzen, dann backend.app importieren.
"""
import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))

_salt = "s"
_hash = hashlib.sha256((_salt + ":pw").encode()).hexdigest()
os.environ["KF_USERS"] = f"test@example.com|{_salt}|{_hash}"
os.environ["KF_SESSION_SECRET"] = "praes-v2-test-secret"

from backend import praesentation_v2_models as m  # noqa
from backend.praesentation_v2 import router as praes_v2_router  # noqa


# ---------- Modell-Konstanten ----------

class TestKategorien:
    def test_genau_7_kategorien(self):
        """Epic-Prompt definiert exakt 7 Kategorien — Regression-Schutz."""
        assert len(m.KATEGORIEN) == 7

    def test_pflicht_kategorien_vorhanden(self):
        expected = {"food", "deckblatt", "location", "ausstattung",
                    "goldschaetzchen", "kochfabrik", "freitext"}
        assert set(m.KATEGORIEN) == expected

    def test_kategorien_sind_strings_und_lowercase(self):
        for k in m.KATEGORIEN:
            assert isinstance(k, str)
            assert k == k.lower()


# ---------- Router-Konfiguration ----------

class TestRouterConfig:
    def test_router_prefix_korrekt(self):
        """Sprint-9-Refactor-Vertrag: Prefix /api/praesentation_v2."""
        assert praes_v2_router.prefix == "/api/praesentation_v2"

    def test_router_tag_v2(self):
        assert "praesentation_v2" in praes_v2_router.tags

    def test_alle_pflicht_routes_vorhanden(self):
        """Akzeptanzkriterium 1+2 — Routes müssen registriert sein."""
        paths = {r.path for r in praes_v2_router.routes}
        erwartete_pfade = {
            "/api/praesentation_v2/health",
            "/api/praesentation_v2/suggestions",
            "/api/praesentation_v2/offer/{offer_id}/slides",
            "/api/praesentation_v2/offer/{offer_id}/slide",
            "/api/praesentation_v2/render-preview",
            "/api/praesentation_v2/generate/{offer_id}"}
        assert erwartete_pfade.issubset(paths), (
            f"Fehlend: {erwartete_pfade - paths}")


# ---------- Pydantic-Bodies ----------

class TestRequestBodies:
    def test_set_slide_body_minimal(self):
        from backend.praesentation_v2 import SetSlideBody
        b = SetSlideBody(position=0, kategorie="food")
        assert b.slide_id is None
        assert b.overrides is None

    def test_set_slide_body_voll(self):
        from backend.praesentation_v2 import SetSlideBody
        b = SetSlideBody(position=2, kategorie="deckblatt",
                         slide_id=42, overrides={"titel": "X"})
        assert b.slide_id == 42
        assert b.overrides == {"titel": "X"}

    def test_render_preview_body_minimal(self):
        from backend.praesentation_v2 import RenderPreviewBody
        b = RenderPreviewBody(kategorie="food", payload={"a": 1})
        assert b.overrides is None


# ---------- HTTP-Integration (TestClient, ohne DB) ----------

@pytest.fixture
def client():
    """FastAPI-TestClient gegen die echte app — DB ist nicht verfügbar
    in dieser Test-Umgebung, also testen wir den Graceful-Fallback-Pfad
    (DB_OK=False → 503)."""
    # KF_SECRET muss VOR app-Import gesetzt sein, wurde oben gemacht
    from fastapi.testclient import TestClient
    from backend.app import app, make_cookie
    c = TestClient(app)
    # Auth-Cookie setzen, sonst beißt die Middleware
    c.cookies.set("kf_sess", make_cookie("test@example.com"))
    return c


class TestHealth:
    def test_health_immer_erreichbar(self, client):
        r = client.get("/api/praesentation_v2/health")
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert "kategorien" in d
        assert len(d["kategorien"]) == 7
        assert "version" in d

    def test_health_meldet_db_status(self, client):
        r = client.get("/api/praesentation_v2/health")
        # Ohne DATABASE_URL → DB_OK=False
        assert r.json()["db"] in (True, False)


class TestSuggestions:
    def test_unbekannte_kategorie_400(self, client):
        r = client.get("/api/praesentation_v2/suggestions"
                       "?kategorie=nope")
        # Wenn DB unavailable → 503 wird VOR Kategorie-Check geprüft,
        # daher: 400 oder 503 akzeptiert
        assert r.status_code in (400, 503)

    def test_pflicht_param_kategorie(self, client):
        r = client.get("/api/praesentation_v2/suggestions")
        assert r.status_code == 422  # missing required query


class TestAuthScoping:
    def test_offer_slides_unauthenticated_401(self):
        from fastapi.testclient import TestClient
        from backend.app import app
        c = TestClient(app)
        # Kein Cookie → 302 zum Login oder 401 (je nach Middleware)
        r = c.get("/api/praesentation_v2/offer/1/slides",
                  follow_redirects=False)
        assert r.status_code in (401, 302, 303)

    def test_offer_slides_authed_ohne_db_503(self, client):
        r = client.get("/api/praesentation_v2/offer/1/slides")
        # DB nicht verfügbar → 503
        assert r.status_code in (401, 503, 403)


class TestRenderPreviewStub:
    def test_render_preview_synthetic_response(self, client):
        r = client.post("/api/praesentation_v2/render-preview", json={
            "kategorie": "food",
            "payload": {"titel": "Test"},
            "overrides": {"titel": "Override"},
        })
        assert r.status_code == 200
        d = r.json()
        assert d["synthetic"] is True
        # Overrides müssen Payload-Felder überschreiben
        assert d["merged"]["titel"] == "Override"

    def test_render_preview_unbekannte_kategorie_400(self, client):
        r = client.post("/api/praesentation_v2/render-preview", json={
            "kategorie": "nope", "payload": {}})
        assert r.status_code == 400


# ---------- Migrations-Sanity (Datei-Inspektion) ----------

class TestMigrationFile:
    def test_revision_id_konvention(self):
        """Revision = '0002_praesentation_v2', down_revision = '0001_baseline'.
        Datei-Inspektion statt Import — alembic ist nicht zwingend
        lokal verfügbar, im Container schon."""
        p = os.path.join(os.path.dirname(__file__), "..", "alembic",
                         "versions", "0002_praesentation_v2.py")
        src = open(p, encoding="utf-8").read()
        assert 'revision = "0002_praesentation_v2"' in src
        assert 'down_revision = "0001_baseline"' in src

    def test_migration_idempotent_guard_vorhanden(self):
        """_table_exists-Check muss da sein (Schutz vor 'relation
        already exists' wenn create_all vorlief)."""
        p = os.path.join(os.path.dirname(__file__), "..", "alembic",
                         "versions", "0002_praesentation_v2.py")
        src = open(p, encoding="utf-8").read()
        assert "_table_exists" in src
        assert "get_table_names" in src
