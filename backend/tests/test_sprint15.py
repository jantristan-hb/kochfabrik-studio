"""Sprint-15 CI-Kette — Marker-Tests fuer die GitHub-Actions-Pipeline.

Diese Tests pruefen statisch die Existenz und den Inhalt von
``.github/workflows/ci.yml`` (US-079). Sie sind absichtlich
infrastruktur-orientiert: die Pipeline ist Code-as-Config und muss
gegen Regression abgesichert sein (FEATURE-009 §8 Nr. 2).
"""

from __future__ import annotations

from pathlib import Path

import yaml

# Repo-Root: backend/tests/ -> backend/ -> <root>
_ROOT = Path(__file__).resolve().parents[2]
_CI_YML = _ROOT / ".github" / "workflows" / "ci.yml"


def _ci_text() -> str:
    assert _CI_YML.exists(), f"ci.yml fehlt: {_CI_YML}"
    return _CI_YML.read_text(encoding="utf-8")


def _ci_doc() -> dict:
    return yaml.safe_load(_ci_text())


def test_ci_yml_exists() -> None:
    assert _CI_YML.is_file(), "Pipeline-Datei .github/workflows/ci.yml fehlt"


def test_ci_yml_is_valid_yaml() -> None:
    doc = _ci_doc()
    assert isinstance(doc, dict), "ci.yml ist kein YAML-Mapping"


def test_job_ci_exists() -> None:
    doc = _ci_doc()
    jobs = doc.get("jobs", {})
    assert "ci" in jobs, "Job 'ci' fehlt in der Pipeline"


def test_triggers_pull_request_and_push_master() -> None:
    doc = _ci_doc()
    # YAML parst 'on:' zu Boolean True -> beide Schluessel pruefen.
    on = doc.get("on", doc.get(True))
    assert on is not None, "'on'-Trigger fehlt"
    assert "pull_request" in on, "Trigger 'pull_request' fehlt"
    push = on.get("push", {})
    branches = push.get("branches", []) if isinstance(push, dict) else []
    assert "master" in branches, "Trigger 'push' auf master fehlt"


def test_ruff_select_codes_present() -> None:
    text = _ci_text()
    assert "ruff check" in text, "ruff-check-Schritt fehlt"
    assert "--select E9,F63,F7,F82" in text, "ruff-Select E9,F63,F7,F82 fehlt"
    assert "backend engine/scripts" in text, "ruff-Pfade backend engine/scripts fehlen"


def test_pytest_step_present() -> None:
    text = _ci_text()
    assert "pytest backend/tests" in text, "pytest-Schritt fehlt"


def test_docker_build_step_present() -> None:
    text = _ci_text()
    assert "docker build" in text, "docker-build-Schritt fehlt"


def test_python_312_setup() -> None:
    text = _ci_text()
    assert "3.12" in text, "Python 3.12 (Container-Paritaet) fehlt"


def test_no_timeout_binary_invocation() -> None:
    """Kein ` timeout `-Binary-Aufruf in der Pipeline (Sprint-Regel)."""
    text = _ci_text()
    assert " timeout " not in text, "verbotener ' timeout '-Binary-Aufruf in ci.yml"
