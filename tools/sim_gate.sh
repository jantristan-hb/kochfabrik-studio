#!/usr/bin/env bash
# sim_gate.sh — Container-Smoke-Gate VOR jedem Cutover (US-050, FEATURE-005
# EARS 2/3). Beweist lokal, dass das Monorepo-Image lebt: Build, Boot ohne
# DB/Volume (graceful-Pfade wie Prod ohne gemountetes Korpus-Volume), alle
# drei Modul-Health-Routen, Engine-Import-Marker und eine reconstruct.js-
# Probe (pptxgenjs end-to-end). Exit 0 = grün (Merge nach master erlaubt),
# exit 1 = rot (Cutover BLOCKIEREN).
#
# Bewusst KEINE GNU-only-Tools (kein GNU-Abbruch-Wrapper, kein `stat -c`):
# Polling per bash-Schleife mit sleep — läuft nativ auf macOS (Sprint-10-RETRO).
set -u

IMG="kf-studio-sim"
PORT="${SIM_GATE_PORT:-18055}"
CID=""
# Im Container minten wir eine Session selbst (Auth-Gate: nur /api/health ist
# public, die Modul-Health-Routen brauchen ein gültiges Cookie). Werte sind
# Wegwerf-Secrets nur für den Smoke — nie Prod.
SECRET="simgate-$$"
USER_EMAIL="sim@gate"
KF_USERS_VAL="${USER_EMAIL}|s|x"   # Login wird nicht gebraucht, make_cookie reicht

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || { echo "FAIL: ROOT nicht erreichbar"; exit 1; }

cleanup() { [ -n "$CID" ] && docker rm -f "$CID" >/dev/null 2>&1; }
trap cleanup EXIT INT TERM

fail() { echo "❌ $1"; exit 1; }
ok()   { echo "✅ $1"; }

# 0) Pre-Check: Docker läuft? (sonst BLOCKED statt kryptischem Build-Fehler)
docker info >/dev/null 2>&1 || fail "Docker-Daemon nicht erreichbar (BLOCKED)"

# 1) Build
echo "==> 1/5 Image bauen ($IMG)"
docker build -q -t "$IMG" . >/dev/null || fail "docker build fehlgeschlagen"
ok "Build grün"

# 2) Container starten — OHNE DATABASE_URL, OHNE Volume (= Prod-Worst-Case:
#    DB-los + Korpus-Volume fehlt → graceful-Pfade müssen tragen).
echo "==> 2/5 Container starten (ohne DB, ohne Volume)"
CID=$(docker run -d \
  -e "KF_SESSION_SECRET=$SECRET" \
  -e "KF_USERS=$KF_USERS_VAL" \
  -p "${PORT}:8000" "$IMG") \
  || fail "docker run fehlgeschlagen"

# 3) Auf uvicorn warten (Polling, max ~40s — reine bash-Schleife)
echo "==> 3/5 Auf uvicorn warten (max 40s)"
BASE="http://localhost:${PORT}"
code=""
i=0
while [ "$i" -lt 40 ]; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/api/health" 2>/dev/null)
  [ "$code" = "200" ] && break
  i=$((i + 1))
  sleep 1
done
[ "$code" = "200" ] || { docker logs "$CID" 2>&1 | tail -20; \
  fail "/api/health nicht 200 nach ${i}s (code=$code)"; }
ok "/api/health 200 (nach ${i}s)"

# 4) Modul-Health-Routen (mit Session-Cookie; graceful-Felder prüfen)
echo "==> 4/5 Modul-Health-Routen + Engine-Import-Marker"
# Cookie IM Container minten (gleicher KF_SESSION_SECRET) — kein Login nötig.
COOKIE=$(docker exec "$CID" python -c \
  "from backend.app import make_cookie; print(make_cookie('${USER_EMAIL}'))" \
  2>/dev/null)
[ -n "$COOKIE" ] || fail "make_cookie lieferte kein Cookie"

ah=$(curl -s -H "Cookie: kf_sess=${COOKIE}" "${BASE}/api/angebot/health")
echo "$ah" | grep -q '"engine":true' \
  || fail "/api/angebot/health: engine!=true ($ah)"
ok "/api/angebot/health engine:true"

ph=$(curl -s -H "Cookie: kf_sess=${COOKIE}" "${BASE}/api/praesentation/health")
echo "$ph" | grep -q '"engine":true' \
  || fail "/api/praesentation/health: engine!=true ($ph)"
# korpus:false ist OK + ERWARTET (kein Volume im Sim — graceful, wie Prod
# ohne Mount). Wir bestehen NICHT auf korpus:true.
echo "$ph" | grep -q '"korpus":false' \
  && ok "/api/praesentation/health engine:true, korpus:false (erwartet, graceful)" \
  || ok "/api/praesentation/health engine:true ($ph)"

# Engine-Import-Marker: ENGINE_ERR muss leer sein (Import sauber).
err=$(docker exec "$CID" python -c \
  "from backend.app import ENGINE_OK, ENGINE_ERR; \
print('OK' if ENGINE_OK and not ENGINE_ERR else 'ERR:'+ENGINE_ERR)" 2>/dev/null)
[ "$err" = "OK" ] || fail "Engine-Import-Marker nicht sauber ($err)"
ok "Engine-Import-Marker: ENGINE_OK=True, ENGINE_ERR leer"

# 5) reconstruct.js-Probe — pptxgenjs end-to-end gegen die mitgelieferte
#    elements.json; erzeugt eine .pptx im Container-/tmp (kein Host-Artefakt).
echo "==> 5/5 reconstruct.js-Probe (pptxgenjs end-to-end)"
recon=$(docker exec "$CID" sh -c '
  cd /app/engine/spike-pptxgenjs &&
  node reconstruct.js elements.json /tmp/sim_gate.pptx >/tmp/recon.log 2>&1 &&
  test -s /tmp/sim_gate.pptx &&
  echo "RECON_OK $(wc -c < /tmp/sim_gate.pptx)"
' 2>/dev/null)
case "$recon" in
  RECON_OK\ *) ok "reconstruct.js grün (pptx ${recon#RECON_OK } bytes)" ;;
  *) docker exec "$CID" tail -5 /tmp/recon.log 2>/dev/null
     fail "reconstruct.js-Probe fehlgeschlagen" ;;
esac

echo ""
echo "SIM-GATE GRUEN — Container lebt (Build + Health + Engine + reconstruct)."
exit 0
