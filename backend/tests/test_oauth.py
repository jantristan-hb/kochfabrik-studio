"""Tests für oauth.py — env-gated Provider-Config + URL-Bau.

OAuth ist deploy-ready ENV-gated: ohne KF_OAUTH_*-ENVs darf das Modul
inaktiv sein (null Regression-Risiko). Diese Tests decken die env-
basierte Aktivierung + URL-Bau OHNE echte IdP-Calls ab.
"""
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))

from backend import oauth


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Vor jedem Test: alle OAuth-ENVs löschen für deterministisches
    Verhalten."""
    for k in ("KF_OAUTH_GOOGLE_ID", "KF_OAUTH_GOOGLE_SECRET",
              "KF_OAUTH_MS_ID", "KF_OAUTH_MS_SECRET",
              "KF_OAUTH_MS_TENANT", "KF_OAUTH_REDIRECT_BASE"):
        monkeypatch.delenv(k, raising=False)


class TestProviders:
    def test_keine_envs_keine_provider(self):
        assert oauth.providers() == {}

    def test_nur_google_id_ohne_secret_inaktiv(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_GOOGLE_ID", "g-id")
        # Secret fehlt → Provider darf nicht aktiv sein
        assert "google" not in oauth.providers()

    def test_nur_google_secret_ohne_id_inaktiv(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_GOOGLE_SECRET", "s")
        assert "google" not in oauth.providers()

    def test_google_id_und_secret_aktiv(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_GOOGLE_ID", "g-id")
        monkeypatch.setenv("KF_OAUTH_GOOGLE_SECRET", "g-secret")
        p = oauth.providers()
        assert "google" in p
        assert p["google"]["id"] == "g-id"
        assert p["google"]["secret"] == "g-secret"
        assert "auth" in p["google"]
        assert p["google"]["label"] == "Google"

    def test_microsoft_aktiv_mit_default_tenant(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_MS_ID", "ms-id")
        monkeypatch.setenv("KF_OAUTH_MS_SECRET", "ms-secret")
        p = oauth.providers()
        assert "microsoft" in p
        # Default-Tenant 'common'
        assert "common" in p["microsoft"]["auth"]

    def test_microsoft_mit_custom_tenant(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_MS_ID", "ms-id")
        monkeypatch.setenv("KF_OAUTH_MS_SECRET", "ms-secret")
        monkeypatch.setenv("KF_OAUTH_MS_TENANT", "akara.tech")
        p = oauth.providers()
        assert "akara.tech" in p["microsoft"]["auth"]

    def test_beide_provider_aktiv_parallel(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_GOOGLE_ID", "g")
        monkeypatch.setenv("KF_OAUTH_GOOGLE_SECRET", "gs")
        monkeypatch.setenv("KF_OAUTH_MS_ID", "m")
        monkeypatch.setenv("KF_OAUTH_MS_SECRET", "ms")
        p = oauth.providers()
        assert set(p.keys()) == {"google", "microsoft"}

    def test_leerstring_envs_inaktiv(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_GOOGLE_ID", "  ")
        monkeypatch.setenv("KF_OAUTH_GOOGLE_SECRET", "  ")
        assert "google" not in oauth.providers()


class TestRedirectUri:
    def test_aus_explicit_base(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_REDIRECT_BASE", "https://app.akara.tech")
        req = MagicMock()
        assert (oauth.redirect_uri("google", req)
                == "https://app.akara.tech/api/oauth/google/callback")

    def test_trailing_slash_wird_normalisiert(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_REDIRECT_BASE",
                           "https://app.akara.tech/")
        req = MagicMock()
        url = oauth.redirect_uri("google", req)
        assert "//api" not in url
        assert url == "https://app.akara.tech/api/oauth/google/callback"

    def test_provider_im_pfad(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_REDIRECT_BASE", "https://x.test")
        req = MagicMock()
        assert "microsoft" in oauth.redirect_uri("microsoft", req)
        assert "google" not in oauth.redirect_uri("microsoft", req)

    def test_fallback_auf_request_url(self, monkeypatch):
        """Ohne ENV: nutze request.url.scheme + netloc."""
        req = MagicMock()
        req.url.scheme = "https"
        req.url.netloc = "live.example.com"
        url = oauth.redirect_uri("google", req)
        assert url.startswith("https://live.example.com/")
        assert url.endswith("/api/oauth/google/callback")


class TestAuthUrl:
    def test_inactive_provider_returns_none(self):
        """Provider ohne ENV → kein auth_url."""
        # _Default_state: alle ENV gelöscht durch fixture
        assert oauth.auth_url("google", "state-123",
                              "https://x.test/cb") is None

    def test_active_provider_returns_url_with_params(self, monkeypatch):
        monkeypatch.setenv("KF_OAUTH_GOOGLE_ID", "g-id")
        monkeypatch.setenv("KF_OAUTH_GOOGLE_SECRET", "g-secret")
        url = oauth.auth_url("google", "state-abc",
                             "https://x.test/cb")
        assert url is not None
        assert url.startswith(oauth._G_AUTH)
        # state + client_id + redirect_uri + scope als Query-Params
        assert "state=state-abc" in url
        assert "client_id=g-id" in url
        assert "redirect_uri=" in url
        assert "scope=" in url

    def test_unknown_provider_none(self):
        assert oauth.auth_url("yahoo", "s", "u") is None
