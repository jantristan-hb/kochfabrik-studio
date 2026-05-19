# FEATURE-ARCH — Sprint 4: OAuth2 (Abschluss EPIC-001)

## Scope
Microsoft/Google OAuth2 Authorization-Code-Login auf der bestehenden
`_owner`/`kf_sess`-Abstraktion. Rein additiv, env-gated, zero-regression.

### Goals
- OAuth-Login → identische `kf_sess`-Session wie Passwort (Tenant-Modell
  unverändert: owner_email steuert alles)
- Unkonfiguriert = exakt heutiges Verhalten (KF_USERS-Passwort)
### Non-Goals
- Rollen/Gruppen-Mapping, SCIM, Logout-beim-IdP, Token-Refresh
- IdP-App-Registrierung (User-seitig, externe Abhängigkeit)

## Architektur
```
login.html ──/api/oauth/providers──► aktive Provider (env-gated)
  Button → GET /api/oauth/{p}/login → 302 IdP (state-Cookie, HMAC)
  IdP → GET /api/oauth/{p}/callback → code→token→userinfo(email)
        → app_user upsert (DB, graceful) → kf_sess=make_cookie(email)
        → 302 /
valid_cookie: sig+exp → (email in KF_USERS)  [unverändert, zuerst]
                       └ sonst _db_user_ok(email)  [psycopg2, TTL, safe]
```
Keine neuen Tabellen (nutzt `app_user` aus S1). Keine neue Dependency
(stdlib urllib/json/hmac; psycopg2 seit S2 vorhanden).

## Security / Zero-Regression
- KF_USERS-Pfad in valid_cookie bleibt erster Short-Circuit → kein
  DB-Hit, bitidentisches Verhalten für bestehende User.
- `_db_user_ok` exception-safe: jeder DB-Fehler → False, nie Raise,
  nie Lockout bestehender User, nie 5xx (middleware).
- state-Cookie HMAC-signiert + kurzlebig (CSRF). redirect_uri fix aus
  ENV. Provider nur aktiv mit id+secret.
- Unkonfiguriert: `/api/oauth/providers`=[], login-Routen 404, keine
  Buttons → Prod unverändert.

## Vision-Alignment
Schließt EPIC-001: die in S1-S3 gebaute Multi-Tenant-/Persistenz-/CRM-
Plattform bekommt zeitgemäßes SSO (MS/Google) ohne den bewährten
KF_USERS-Pfad zu gefährden. Letzter Epic-Sprint.
