# Feature-Sheet — Modul: OAuth2 (MS/Google)
**Typ:** Auth/Service+API+UI · **Stories:** US-018..021
## Inputs
ENV: KF_OAUTH_GOOGLE_ID/_SECRET, KF_OAUTH_MS_ID/_SECRET/_TENANT,
KF_OAUTH_REDIRECT_BASE. Cookie kf_sess (S1), app_user (S1).
## Logik
oauth.providers()→{aktiv}; auth_url/exchange (stdlib urllib).
app.py: /api/oauth/providers|{p}/login|{p}/callback; valid_cookie +=
_db_user_ok(email) (psycopg2, TTL, safe) NUR wenn nicht in KF_USERS.
## Output
OAuth-Login → kf_sess wie Passwort → volle Tenant-Integration.
Unkonfiguriert → 0 Provider, 0 Buttons, identisches Verhalten.
## Akzeptanz
Siehe BDD/TEST. Binding-Gate: Graceful-Fallback live (Passwort +
KF_USERS unverändert). Live-OAuth-Roundtrip: User-IdP-Creds nötig.
## Nicht im Modul
IdP-App-Registrierung, Refresh, Rollen.
