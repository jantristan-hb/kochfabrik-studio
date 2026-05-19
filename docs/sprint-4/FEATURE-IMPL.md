# FEATURE-IMPL — Sprint 4
## Dateien
backend/oauth.py (neu) · backend/app.py (3 Routes + valid_cookie/
_db_user_ok + PUBLIC) · web/login.html (Buttons konditional).
Keine neue Dependency (stdlib + psycopg2 aus S2). Keine Migration.
## valid_cookie (KRITISCH, zero-regression)
```
sig+exp ok? →
  if email in _users(): return True            # UNVERÄNDERT, kein DB
  return _db_user_ok(email)                     # nur OAuth-User
_db_user_ok: TTL-Cache(60s) → psycopg2 connect(timeout=2) SELECT 1
  FROM app_user WHERE email=%s → bool; JEDER Fehler → False (safe).
```
KF_USERS-User treffen NIE die DB → bitidentisch zu heute. DB-down
sperrt KF_USERS-User NICHT aus (Short-Circuit davor).
## OAuth-Flow
login → state=HMAC(email-less rand|exp, _secret) als Cookie +
302 authorize?client_id&redirect_uri&scope=openid email&state.
callback → state-Cookie==query state & exp → POST token → GET
userinfo → email → await store._ensure_user via kurze async-Bridge
(asyncio.run in sync route ODER async route) → set kf_sess → 302 /.
Routes async (FastAPI) → app_user-Upsert via store/db (graceful:
DB-Fehler → /login.html?err=oauth, kein 5xx).
## Pitfalls
- valid_cookie ist sync + middleware-heiß → DB-Check nur für Nicht-
  KF_USERS + TTL-Cache + 2s-Timeout, niemals Raise.
- redirect_uri muss exakt der IdP-App-Registrierung entsprechen
  (KF_OAUTH_REDIRECT_BASE Pflicht für Live).
- PUBLIC um /api/oauth/* erweitern (sonst auth_gate blockt callback).
- Provider unbekannt/inaktiv → 404 (kein 500).
## Phasen
018 Config → 020 valid_cookie → 019 Routes → 021 login.html.
