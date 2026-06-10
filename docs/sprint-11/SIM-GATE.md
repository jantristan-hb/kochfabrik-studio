# SIM-GATE.md — Container-Smoke vor dem Cutover (US-050)

> Bindung: FEATURE-005 EARS 2/3 · `tools/sim_gate.sh` · Sicherheits-Auflage 3
> (master-Push = Auto-Deploy). Das Gate ist die **Vorbedingung** für den
> Merge nach master — es ersetzt das weggefallene `vendor.sh`-Sim (Schritt 4/4).

## Zweck

Beweist **lokal**, dass das Monorepo-Image lebt, BEVOR der Merge nach
master (= Cutover = Auto-Deploy auf Prod) passiert. Schlägt das Gate fehl,
wird der Cutover blockiert (EARS 3). In EPIC-008/C1 wird es CI-Pflicht.

## Ausführen

```bash
./tools/sim_gate.sh        # exit 0 = grün (Merge erlaubt), exit 1 = rot
```

Voraussetzung: Docker-Daemon läuft (`docker info`). Läuft sonst kein
Workaround, sondern sauberer Abbruch (BLOCKED). Port via
`SIM_GATE_PORT` übersteuerbar (Default 18055). Das Skript baut das Image
selbst, startet einen Wegwerf-Container, prüft, und räumt ihn per `trap`
in jedem Fall wieder ab — kein Host-Artefakt bleibt liegen.

## Was geprüft wird (5 Schritte)

| # | Schritt | Bestanden wenn |
|---|---------|----------------|
| 1 | `docker build -q -t kf-studio-sim .` | Build ohne `vendor.sh` durch (EARS 2) |
| 2 | Container starten **ohne `DATABASE_URL`, ohne Volume** | = Prod-Worst-Case (DB-los + Korpus-Volume fehlt); graceful-Pfade müssen tragen |
| 3 | Polling auf `GET /api/health` (max ~40s) | HTTP 200 (uvicorn oben, `db:false` ist OK) |
| 4 | Modul-Health + Engine-Import-Marker | `/api/angebot/health` + `/api/praesentation/health` melden `engine:true`; `ENGINE_OK=True` und `ENGINE_ERR` leer |
| 5 | `node reconstruct.js` gegen mitgelieferte `elements.json` | rc=0 + nicht-leere `.pptx` (pptxgenjs/jszip/lib end-to-end) |

### Auth-Detail (Schritt 4)

Nur `/api/health` ist public; die Modul-Health-Routen liegen hinter dem
Auth-Gate (401 ohne Cookie). Das Gate **mintet im Container** ein
Session-Cookie via `backend.app.make_cookie(...)` mit demselben
Wegwerf-`KF_SESSION_SECRET` und curlt damit — so wird die Route
tatsächlich ausgeführt (nicht nur der 401-Pfad geprüft).

### Graceful, nicht streng (Schritt 4, korpus)

`/api/praesentation/health` meldet im Sim `korpus:false` — das ist
**erwartet und OK**: der 4,8-GB-Korpus-Cache ist in Prod ein Coolify-
Volume, das im Sim bewusst fehlt. Das Gate besteht NICHT auf
`korpus:true` (sonst würde es einen Zustand fordern, den nur Prod hat).
Es besteht auf `engine:true` (Engine-Import + node/soffice/Assets da).

## macOS-Kompatibilität

Keine GNU-only-Tools: kein GNU-Abbruch-Wrapper (`timeout`), kein
`stat -c`. Das Warten ist eine reine bash-Schleife mit `sleep`
(Sprint-10-RETRO-Learning). Der Test `test_sim_gate_vorhanden`
(`backend/tests/test_sprint11.py`) sichert das maschinell ab
(`os.X_OK` + kein `"timeout "` im Skript).

## Einordnung im Cutover (US-051)

```
… → ./tools/sim_gate.sh  (MUSS grün, sonst STOP)
    → PR-Merge nach master  (= Cutover, Coolify baut, Volume bleibt)
    → ./tools/live_verify.sh  (Post-Cutover-Verify, US-051)
```
Rot im Gate ⇒ nicht mergen; Ursache fixen (Build/Health/Engine/
reconstruct), Gate erneut grün fahren.
