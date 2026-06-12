# TEST.md — Sprint 14 (TDD-Stubs aus EARS)

> Stubs initial ROT. Framework: **pytest, synchron** (TestClient, KEIN
> Async-Plugin — wie Bestands-Suite). venv: `tools/.venv`.
>
> **Fixture-/Datei-Ownership (Wave-Plan-konform, strikt):**
> - `test_sprint14_tooling.py` — US-069 (render_notext)
> - `test_sprint14_bundle.py` — US-073 (imgbundle/rank_mixed)
> - `test_sprint14.py` — API-Kette US-070→072 (TestClient+Auth LOKAL)
> - `test_sprint14_fe.py` — Wizard-Kette US-074→077 (TestClient LOKAL)
> - conftest/Bestands-Fixtures eingefroren; LLM-Calls IMMER monkeypatch.

## us-069-render-notext (FEATURE-013 EARS 1)

```python
def test_notext_filter_drops_text_elements():   # Filterfunktion: seq ohne t=="text", Rest identisch
    assert False
def test_notext_sample_png_exists():            # Sample-Lauf-Artefakt: preview_notext/p1.png > 5 KB
    assert False
def test_notext_idempotent():                   # 2. Lauf ohne --force überspringt (mtime unverändert)
    assert False
```

## us-073-imgbundle (FEATURE-013 EARS 2+3)

```python
def test_rank_mixed_alpha1_equals_rank():       # alpha=1.0 → byte-identische Reihenfolge zu rank()
    assert False
def test_rank_mixed_without_imgbundle():        # Artefakt fehlt → Fallback rank(), kein Crash (EARS 3)
    assert False
def test_rank_mixed_blends_scores(monkeypatch): # Fake-imgbundle: Slide mit hohem img-Match steigt
    assert False
def test_embed_images_descriptions(monkeypatch):# Vision gemockt → npz mit L2-normierten Vektoren
    assert False
```

## us-070-geometrie-api (FEATURE-014 EARS 1)

```python
def test_texts_response_has_meta_and_geometry():  # meta{w_pt,h_pt} + x/y/w/h/color/weight/italic je Text
    assert False
def test_texts_response_lists_images():          # images[] mit i/x/y/w/h (t=="image")
    assert False
def test_notext_preview_route():                 # 200 für gerendertes Sample (skipif fehlt), 404 sonst
    assert False
def test_texts_backwards_compatible():           # #66-Felder (i/text/size, suggestions) unverändert
    assert False
```

## us-071-bild-overrides (FEATURE-014 EARS 2)

```python
def test_download_image_override_in_pptx():     # Data-URL → ppt/media enthält Override-Bild (node-gated)
    assert False
def test_download_image_override_cache_untouched():  # Cache-Dateiset/mtimes unverändert (R-NF-3)
    assert False
def test_download_image_override_validation():  # ungültige Data-URL → 400; > 8 MB → 413
    assert False
```

## us-072-formulate-und-mix (FEATURE-014 EARS 3+4)

```python
def test_formulate_returns_rewrite(monkeypatch):    # gemockter Anthropic → {text}, DNA-Konstante im Prompt
    assert False
def test_formulate_llm_error_502(monkeypatch):      # Client wirft → 502 gekürzt
    assert False
def test_formulate_requires_auth():                 # 401 ohne Cookie
    assert False
def test_suggest_uses_rank_mixed(monkeypatch):      # imgbundle da → rank_mixed; sonst identisch zu rank
    assert False
```

## us-074-wizard-geruest (FEATURE-015 EARS 6) — test_sprint14_fe.py

```python
def test_wizard_page_served():       # wizard.html 200 + Marker progress/step/alts/stage
    assert False
def test_wizard_js_state():          # kfWizard.v1 + sessionStorage + Schritt-Maschine-Marker
    assert False
def test_wizard_nav_links():         # ≥5 Seiten verlinken wizard.html
    assert False
```

## us-075-alternativen (FEATURE-015 EARS 1)

```python
def test_wizard_alternatives_markers():   # max-4-Render + candidates[0]-Vorauswahl
    assert False
def test_wizard_cover_generate_wiring():  # /api/image + category cover im Cover-Schritt
    assert False
```

## us-076-overlay-editor (FEATURE-015 EARS 2+3+4)

```python
def test_wizard_stage_notext_fallback():  # preview-notext-URL + onerror-Fallback aufs normale PNG
    assert False
def test_wizard_overlay_scaling():        # Positionierung aus meta.w_pt + ResizeObserver
    assert False
def test_wizard_formulate_wiring():       # /api/designer/formulate + Undo-Marker
    assert False
def test_wizard_image_generate_wiring():  # Bild-Element-Button → /api/image (food), in-memory Override
    assert False
```

## us-077-abschluss-e2e (FEATURE-015 EARS 5)

```python
def test_wizard_download_payload_markers():       # Filmstreifen + download mit overrides+image_overrides
    assert False
def test_wizard_e2e_full_flow(monkeypatch):       # suggest(gemockt)→Override+1x1-PNG-Bildoverride→download
    assert False                                   # → PK-Magic + Text im Slide-XML + Bild in ppt/media (node-gated)
```
