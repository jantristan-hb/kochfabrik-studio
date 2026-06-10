# CUTOVER-RUNBOOK.md — Monorepo-Cutover (Sprint 11, US-051)

> Bindung: FEATURE-005 EARS 4 · ADR-002 Coolify-Migrationsplan M3 ·
> Sicherheits-Auflage: **master-Push = Auto-Deploy auf Prod**.
> Verantwortlich: der `/sprint-review`-/`/integrate`-Schritt (NICHT ein
> Agent — der Merge nach master ist der Cutover und passiert manuell
> nach grünen Gates).

## Was der Cutover ist

Der Merge des Branches `sprint-11-monorepo` nach `master` **ist** der
Cutover: Coolify baut daraufhin das Monorepo-Image und swappt die
laufende Revision. Es gibt kein separates Deploy-Kommando-Ritual — der
Merge löst den Build aus (bzw. force-deploy via Coolify, da Push laut
README nicht auto-triggert; im Zweifel force, s.u.).

## Vorbedingungen (Gates — ALLE müssen grün sein)

| Gate | Story | Nachweis |
|------|-------|----------|
| **Backup liegt** | US-044 | `../backups/kf-studio-pg-2026-06-09.sql.gz` (off-host neben dem Repo) + `BACKUP-VERIFY.md` (Branch `sprint-11-us044-backup`); Restore-Hinweis dort |
| **Sim-Gate grün** | US-050 | `./tools/sim_gate.sh` → exit 0 (Build + Container-Smoke; siehe [SIM-GATE.md](SIM-GATE.md)) |
| **Suite grün** | US-046/048 | `tools/.venv/bin/python -m pytest backend/tests -q` → 0 failed |
| **Pre-Cutover Live-Verify** | US-051 | `./tools/live_verify.sh` gegen aktuelle Prod → exit 0 (Referenz, s.u.) |

> **IF eines dieser Gates rot ist → NICHT mergen.** Das `sim_gate`-
> Ergebnis ist die harte Vorbedingung (FEATURE-005 EARS 3): ein roter
> Sim-Gate blockiert den Cutover.

## Reihenfolge (Schritt für Schritt)

```
1. Backup verifizieren (US-044)            ✓ vorhanden
2. ./tools/sim_gate.sh                      ✓ exit 0 (lokal, Container-Smoke)
3. ./tools/live_verify.sh                   ✓ exit 0 (PRE-Cutover-Referenz)
4. PR sprint-11-monorepo → master mergen    = CUTOVER (Coolify baut)
   (ggf. Coolify force-deploy, da Push nicht auto-triggert)
5. Build abwarten (~5–8 min wenn apt-Layer; sonst schneller)
6. ./tools/live_verify.sh                   POST-Cutover gegen neue Revision
   → grün: fertig. → rot: ROLLBACK (s.u.)
```

**Korpus-Volume:** bleibt gemountet (Coolify Directory Mount auf
`data/cache`, unverändert) — **kein** ~4,8-GB-Transfer, kein Volume-Umbau
(ADR-002 M3).

## Rolling-Verhalten (kein Downtime)

Coolify-Builds sind **atomar** und **rolling**: Die alte Revision bleibt
live, bis die neue Health-grün ist. Schlägt der Build fehl, bleibt
schlicht die alte Version live (Prod nie gefährdet — README
„Troubleshooting": *Studio-Modul down nach Push → kann nicht passieren*).
Erst ein erfolgreicher, gesunder Build swappt.

## Live-Verify

`tools/live_verify.sh` prüft deterministisch ohne Credentials:

- `GET /api/health` → **200 + `db:true`** (DB erreichbar)
- `GET /api/angebot/health` → **401** (Route lebt hinter Auth-Gate; 200 falls public auch ok)
- `GET /api/praesentation/health` → **401** (Route lebt)
- `POST /api/slidesuche/search` → **401/422/200** (Route lebt; 5xx = FAIL)
- `GET /login.html` → **200** (statisches Frontend ausgeliefert)

Ein **404/5xx** auf einer der Routen = Route fehlt/kaputt in der laufenden
Revision = kaputter Deploy → Rollback. (Override Base-URL via
`BASE_URL`, Default `https://kochfabrik-studio.flinkbase.com`.)

### Pre-Cutover-Referenz (Lauf vom 2026-06-10, gegen laufende Prod)

```
==> Live-Verify gegen https://kochfabrik-studio.flinkbase.com
✅ /api/health 200, db:true
✅ GET /api/angebot/health → 401 (Route lebt)
✅ GET /api/praesentation/health → 401 (Route lebt)
✅ POST /api/slidesuche/search → 401 (Route lebt)
✅ GET /login.html → 200 (Route lebt)
LIVE-VERIFY GRUEN — alle Health-Routen erreichbar.   (exit 0)
```

Diese Signatur ist die Soll-Referenz: Nach dem Cutover muss
`live_verify.sh` dieselbe grüne Ausgabe liefern.

## Rollback (bei rotem POST-Cutover-Verify)

Coolify behält die alte Revision; ein Rollback = die **vorherige,
gesunde Revision re-deployen** (Webhook/Repo unverändert, ADR-002 M3):

**UI-Pfad (bevorzugt):**
1. `coolify.flinkbase.com` → Projekt „My first project" → App
   `kochfabrik-studio` → **Deployments**
2. Letztes gesundes Deployment wählen → **Redeploy / Rollback**

**API-Pfad (force-redeploy der App):**
```bash
set -a; source ~/work/.env; set +a   # COOLIFY_TOKEN
curl "https://coolify.flinkbase.com/api/v1/deploy?uuid=yu2fqx0twmtqcp6zyx2e59si&force=true" \
     -H "Authorization: Bearer $COOLIFY_TOKEN"
```
> Hinweis: Der API-Force baut den aktuellen master-Stand neu. Für ein
> echtes Zurück auf den Vor-Cutover-Code ist der zuverlässige Weg, den
> Merge-Commit auf master per `git revert` rückgängig zu machen und
> erneut zu deployen — danach `./tools/live_verify.sh` zur Bestätigung.

**DB-Restore (nur Worst-Case, falls Migration Daten beschädigt):** Der
Image-Rollback allein reicht für ein Code-Problem. Ist die DB betroffen,
liegt der Dump unter `../backups/kf-studio-pg-2026-06-09.sql.gz` (Restore-
Schritte in `BACKUP-VERIFY.md`, US-044). DB-Restore ist ein bewusster,
separater Eingriff — nicht Teil des Standard-Rollbacks.

App-UUID `yu2fqx0twmtqcp6zyx2e59si` · Server `188.245.110.5` ·
SSH `ssh -i ~/.ssh/hetzner_id root@188.245.110.5`. Secrets
(`COOLIFY_TOKEN`, DB-Creds) ausschließlich aus `~/work/.env` — nie ins
Repo.

## Nach grünem Cutover

- `./tools/live_verify.sh` grün gegen die neue Revision (Soll-Signatur oben)
- Korpus-Volume weiter gemountet (`/api/praesentation/health` `korpus:true`
  in Prod — anders als im Sim, wo bewusst kein Volume hängt)
- Sprint-Abschluss via `/sprint-review` (Docs, RETRO, /integrate)
