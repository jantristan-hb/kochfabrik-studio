# TEST.md — Sprint 13 (TDD-Stubs aus EARS)

> Stubs initial ROT. Framework: **pytest, synchron** (TestClient —
> KEIN Async-Plugin, wie die Bestands-Suite; keine anyio/pytest-asyncio-
> Marker mischen). venv: `tools/.venv`.
>
> **Fixture-Ownership (Wave-Plan-konform):**
> - `backend/tests/test_sprint13.py` — gehört der **API-Kette**
>   (US-061→062). Eigener TestClient + make_cookie LOKAL in der Datei
>   (kein conftest-Umbau).
> - `backend/tests/test_sprint13_fe.py` — gehört der **UI-Kette**
>   (US-063→067). Eigener TestClient LOKAL.
> - Geteilte Bestands-Fixtures werden NICHT angefasst.
> - Gemini-embed wird via `monkeypatch` auf Modul-Ebene gemockt —
>   NIE echte API-Calls in der Suite (Boundary).

## us-061-designer-router (FEATURE-011 EARS 2+3)

```python
def test_designer_health_shape():        # GET /api/designer/health → 200, keys engine/korpus/embed (bool)
    assert False
def test_suggest_requires_auth():        # POST suggest ohne Cookie → 401
    assert False
def test_suggest_invalid_body():         # weder PDF noch offer_id noch offer → 400/422
    assert False
def test_suggest_offer_id_parsing(monkeypatch):  # gemockt: offer_id → offer-Block {kunde,datum,gaenge} (EARS 2)
    assert False
def test_suggest_graceful_503(monkeypatch):      # Engine/Korpus weg → 503 mit Klartext (EARS 3)
    assert False
```

## us-062-vorschlags-ranking (FEATURE-011 EARS 1+4)

```python
def test_suggest_groups_topn(monkeypatch):   # gemockter embed → je Gang Gruppe mit 5 Kandidaten (deck/page/score/preview/label) (EARS 1)
    assert False
def test_suggest_pflicht_gruppe(monkeypatch):# Response enthält genau eine Gruppe kind=pflicht (EARS 1)
    assert False
def test_suggest_embed_fail_502(monkeypatch):# embed wirft → 502 gekürzte Meldung (EARS 3)
    assert False
def test_designer_uses_bundle_layer():       # statisch: designer.py ohne np.load, mit bundle-Import (EARS 4)
    assert False
```

## us-063-ui-geruest (FEATURE-012 EARS 1-Vorstufe) — test_sprint13_fe.py

```python
def test_designer_page_served():         # GET /designer.html → 200 + Marker designer-source/groups/board
    assert False
def test_designer_js_served():           # GET /assets/designer.js → 200 + kfDesigner.v1
    assert False
def test_nav_links_added():              # ≥5 bestehende Seiten verlinken designer.html
    assert False
```

## us-064-karten (FEATURE-012 EARS 1+5)

```python
def test_designer_js_wires_suggest():    # designer.js referenziert /api/designer/suggest + /api/angebote
    assert False
def test_preview_fallback_marker():      # Platzhalter-/onerror-Pfad in designer.js vorhanden (EARS 5)
    assert False
```

## us-065-storyboard (FEATURE-012 EARS 3)

```python
def test_board_persistence_markers():    # sessionStorage + kfDesigner.v1 + Reorder/Remove-Handler in designer.js
    assert False
```

## us-066-suche (FEATURE-012 EARS 2)

```python
def test_designer_js_wires_search():     # designer.js referenziert /api/slidesuche/search
    assert False
```

## us-067-download-e2e (FEATURE-012 EARS 4 + FEATURE-011 EARS 1)

```python
def test_designer_download_wired():      # designer.js referenziert /api/slidesuche/download + disabled-Logik
    assert False
def test_e2e_suggest_to_pptx(monkeypatch):  # gemockter suggest-Kandidat (committetes Cache-Deck) → download → PK-Magic, >10 KB
    assert False
```

## us-068-live-verify-deep (Incident-Kriterium)

Kein pytest-Stub — Shell-Gate: `LIVE_DEEP=1 ./tools/live_verify.sh`
(Verify der Story selbst; Standard-Lauf bleibt byte-identisch).
