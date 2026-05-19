# BDD — Sprint 4
## US-018/019 {#oauth-config-routes}
### Szenario: unkonfiguriert = inaktiv
**Given** keine KF_OAUTH_*-ENV **When** GET /api/oauth/providers
**Then** `{providers:[]}`; /api/oauth/google/login → 404
### Szenario: konfiguriert
**Given** Google-ID+Secret gesetzt **When** /api/oauth/google/login
**Then** 302 zu accounts.google.com, state-Cookie gesetzt
### Szenario: callback
**Given** gültiger code+state **When** callback **Then** app_user
angelegt, kf_sess gesetzt, 302 /
## US-020 {#valid-cookie-zero-regression}
### Szenario: KF_USERS unverändert
**Given** KF_USERS-User-Cookie **Then** valid_cookie True, KEIN DB-Hit
### Szenario: OAuth-User via DB
**Given** email nur in app_user **Then** valid_cookie True
### Szenario: DB down, kein Lockout
**Given** DB nicht erreichbar, KF_USERS-User-Cookie
**Then** valid_cookie True (Short-Circuit), kein Raise/5xx
### Szenario: unbekannt
**Given** email weder KF_USERS noch app_user **Then** False
## US-021 {#login-buttons}
### Szenario: keine Provider → Seite unverändert (Passwort-Login)
### Szenario: Provider aktiv → Button → /api/oauth/{p}/login
