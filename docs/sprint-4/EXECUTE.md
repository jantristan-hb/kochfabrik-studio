# Sprint 4 — kochfabrik-studio (EPIC-001 Abschluss)
**Pfad:** /home/jrudat/work/03 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 4 · Branch `sprint-4-oauth` · GitHub · master-Deploy (Coolify atomar)
**Basis:** S1-S3 DONE @ master e4ad9e4. **Test:** pytest -q + node --check.
## Waves (sequenziell — US-018/019/020 → app.py/oauth.py)
| Wave | Story | Blocked-by |
|------|-------|------------|
| 1 | US-018 Provider-Config | — |
| 1 | US-020 valid_cookie DB-Erweiterung (zero-regression) | — |
| 2 | US-019 OAuth-Routes + Auto-Reg | US-018 |
| 3 | US-021 login.html-Buttons | US-019 |
Reihenfolge: 018 → 020 → 019 → 021.
## Auftrag
Sequentiell, headless. ZERO-REGRESSION oberste Regel: unkonfiguriert =
heutiges Verhalten; valid_cookie KF_USERS-Short-Circuit zuerst;
_db_user_ok exception-safe. Live-OAuth-Roundtrip nicht autonom
verifizierbar (braucht IdP-Apps) → Binding-Gate = Graceful-Fallback
(Passwort-Login + KF_USERS-Cookie weiter ok, /api/oauth/providers=[]).
