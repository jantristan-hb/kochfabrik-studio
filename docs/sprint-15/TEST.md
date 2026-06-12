# TEST.md — Sprint 15 (TDD-Stubs aus EARS)

> Stubs initial ROT. Framework: **pytest, synchron** (kein Async-Plugin).
> venv: `tools/.venv`. **fitz (PyMuPDF) wird in US-081 installiert** —
> alle fidelity-Tests `skipif fitz fehlt`; Render-Tests zusätzlich
> docker-gated. **Datei-Ownership:** `test_sprint15.py` = CI-Kette
> (US-079/080) · `test_sprint15_fidelity.py` = Treue-Kette (US-081–084)
> · US-078 hat keinen pytest (Shell-Verify + Protokoll).

## us-079-ci-pipeline (FEATURE-009 EARS 2)

```python
def test_ci_workflow_exists():            # .github/workflows/ci.yml + Job "ci"
    assert False
def test_ci_workflow_steps():             # ruff E9,F63,F7,F82 + pytest + docker build + Trigger PR/master
    assert False
def test_ci_no_timeout_binary():          # kein `timeout `-Aufruf (macOS-Lehre gilt auch für Skripte)
    assert False
```

## us-080-branch-protection (FEATURE-009 EARS 1+4)

```python
def test_delivery_flow_doc():             # DELIVERY-FLOW.md: Admin-Bypass + manueller Deploy + LIVE_DEEP
    assert False
def test_protection_state():              # gh api: contexts enthält "ci", enforce_admins false (skipif kein gh)
    assert False
```

## us-081-fidelity-metrik (FEATURE-016 EARS 1)

```python
def test_self_compare_is_one():           # ref.pdf:1 vs. sich selbst → total >= 0.99
    assert False
def test_text_mutation_lowers_text():     # synthetisches PDF mit geändertem Text → text-Score sinkt
    assert False
def test_font_mutation_lowers_font():     # geänderte Font-Size → font-Score sinkt (Monotonie)
    assert False
def test_geometry_normalized():           # A4-Seite vs. 16:9 — Koordinaten normalisiert, kein Crash
    assert False
```

## us-082-fidelity-run (FEATURE-016 EARS 2)

```python
def test_run_outputs_scores():            # --deck Sample → JSON je Slide mit scores.total (docker-gated)
    assert False
def test_run_reproducible():              # zweiter Lauf ±0.005 (docker-gated)
    assert False
```

## us-083-baseline (FEATURE-016 EARS 4)

Kein pytest-Stub — Verify prüft Artefakte (fidelity_baseline.json
vollständig + metrik_version, Report mit Schwellen-Vorschlag).

## us-084-gate (FEATURE-016 EARS 3 + FEATURE-009 EARS 3)

```python
def test_gate_green_on_unchanged():       # Sample-Lauf vs. Baseline: total >= baseline-0.02 (docker-gated)
    assert False
def test_gate_catches_regression():       # Font-Size x0.5 in elements vor Render → Gate-Vergleich SCHLÄGT FEHL
    assert False                          # (Test assertet das Fehlschlagen — der Beweis, EARS 3)
```
