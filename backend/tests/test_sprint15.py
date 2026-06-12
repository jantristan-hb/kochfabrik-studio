"""Sprint-15 CI-Kette — Marker-Tests fuer die GitHub-Actions-Pipeline.

Diese Tests pruefen statisch die Existenz und den Inhalt von
``.github/workflows/ci.yml`` (US-079). Sie sind absichtlich
infrastruktur-orientiert: die Pipeline ist Code-as-Config und muss
gegen Regression abgesichert sein (FEATURE-009 §8 Nr. 2).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

# Repo-Root: backend/tests/ -> backend/ -> <root>
_ROOT = Path(__file__).resolve().parents[2]
_CI_YML = _ROOT / ".github" / "workflows" / "ci.yml"
_DELIVERY_FLOW = _ROOT / "docs" / "ops" / "DELIVERY-FLOW.md"
_REPO = "jantristan-hb/kochfabrik-studio"


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


# --- US-080: Branch-Protection + Delivery-Flow-Doku -------------------------


def _delivery_text() -> str:
    assert _DELIVERY_FLOW.exists(), f"DELIVERY-FLOW.md fehlt: {_DELIVERY_FLOW}"
    return _DELIVERY_FLOW.read_text(encoding="utf-8")


def test_delivery_flow_doc_exists() -> None:
    assert _DELIVERY_FLOW.is_file(), "docs/ops/DELIVERY-FLOW.md fehlt"


def test_delivery_flow_names_admin_bypass() -> None:
    text = _delivery_text().lower()
    assert "admin" in text, "Admin-Bypass-Regel fehlt in DELIVERY-FLOW.md"
    assert "bypass" in text, "Begriff 'bypass' fehlt in DELIVERY-FLOW.md"


def test_delivery_flow_names_manual_deploy() -> None:
    text = _delivery_text().lower()
    assert "manuell" in text or "manual" in text, "manueller Deploy nicht dokumentiert"
    assert "coolify" in text, "Coolify-Deploy nicht dokumentiert"


def test_delivery_flow_names_live_deep() -> None:
    text = _delivery_text()
    assert "LIVE_DEEP" in text, "LIVE_DEEP nicht im Delivery-Flow dokumentiert"


def test_claude_md_links_delivery_flow() -> None:
    claude_md = (_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "DELIVERY-FLOW.md" in claude_md, "CLAUDE.md verweist nicht auf DELIVERY-FLOW.md"


def _gh_protection() -> dict | None:
    """Liest den Protection-Zustand von master via gh; None wenn gh fehlt."""
    if shutil.which("gh") is None:
        return None
    proc = subprocess.run(
        ["gh", "api", f"repos/{_REPO}/branches/master/protection"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return json.loads(proc.stdout)


@pytest.mark.skipif(shutil.which("gh") is None, reason="gh CLI nicht verfuegbar")
def test_branch_protection_requires_ci_check() -> None:
    prot = _gh_protection()
    assert prot is not None, "Branch-Protection auf master nicht aktiv/lesbar"
    contexts = prot.get("required_status_checks", {}).get("contexts", [])
    assert "ci" in contexts, f"Required-Check 'ci' fehlt in Protection: {contexts}"


@pytest.mark.skipif(shutil.which("gh") is None, reason="gh CLI nicht verfuegbar")
def test_branch_protection_enforce_admins_false() -> None:
    prot = _gh_protection()
    assert prot is not None, "Branch-Protection auf master nicht aktiv/lesbar"
    enforce = prot.get("enforce_admins", {})
    # gh liefert enforce_admins als Objekt {enabled: bool}.
    enabled = enforce.get("enabled") if isinstance(enforce, dict) else enforce
    assert enabled is False, "enforce_admins muss false sein (Admin-Bypass erlaubt)"
