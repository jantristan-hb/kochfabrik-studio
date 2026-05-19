"""Sprint 4 — OAuth zero-regression."""
import importlib, os


def test_providers_inactive_without_env(monkeypatch):
    for k in ("KF_OAUTH_GOOGLE_ID","KF_OAUTH_GOOGLE_SECRET",
              "KF_OAUTH_MS_ID","KF_OAUTH_MS_SECRET"):
        monkeypatch.delenv(k, raising=False)
    from backend import oauth; importlib.reload(oauth)
    assert oauth.providers() == {}


def test_oauth_routes_registered():
    import backend.app as a
    p={getattr(r,'path','') for r in a.app.routes}
    assert "/api/oauth/providers" in p
    assert "/api/oauth/{provider}/login" in p
    assert "/api/oauth/{provider}/callback" in p


def test_valid_cookie_unknown_email_false(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("KF_SESSION_SECRET", "test")
    import backend.app as a; importlib.reload(a)
    # Cookie für nicht-existierenden User → False (kein DB, kein Crash)
    assert a.valid_cookie(a.make_cookie("nobody@x.de")) is False
