#!/usr/bin/env bash
# sim_gate.sh — Container-Smoke-Gate VOR jedem Cutover (US-050, FEATURE-005
# EARS 2/3). Beweist lokal, dass das Monorepo-Image lebt: Build, Boot ohne
# DB/Volume (graceful-Pfade wie Prod ohne gemountetes Korpus-Volume), alle
# drei Modul-Health-Routen, Engine-Import-Beweis und eine reconstruct.js-
# Probe. Exit 0 = grün (Merge nach master erlaubt), exit 1 = rot
# (Cutover BLOCKIEREN — IF-Gate aus EARS 3).
#
# Bewusst KEINE GNU-only-Tools (kein GNU-Abbruch-Wrapper, kein `stat -c`):
# Polling per bash-Schleife mit sleep — läuft nativ auf macOS (Sprint-10-RETRO).
set -euo pipefail

IMG="kf-studio-sim"
PORT="${SIM_GATE_PORT:-18000}"
CID=""
# Optionaler DB-Block (US-057, FEATURE-006 EARS 4): nur mit SIM_GATE_DB=1.
# Eigener Wegwerf-Postgres auf 15432 (NIE 5432/5434 — 5434 ist die lokale
# Build-Korpus-DB). PGCID wird im cleanup mit abgeräumt.
PGCID=""
PG_CONTAINER="kf-sim-alembic-pg"
PG_PORT="${SIM_GATE_DB_PORT:-15432}"
# Auth-Gate: nur /api/health ist public, die Modul-Health-Routen brauchen ein
# gültiges Cookie. Wir minten es im Container selbst via make_cookie (gleicher
# KF_SESSION_SECRET) — das KF_USERS-Login-Format (email|salt|sha256hex) müssen
# wir dafür nicht bedienen. Werte sind Wegwerf-Secrets nur für den Smoke.
SECRET="simgate-$$"
USER_EMAIL="sim@gate"
KF_USERS_VAL="${USER_EMAIL}|s|x"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cleanup() {
  [ -n "$CID" ] && docker rm -f "$CID" >/dev/null 2>&1 || true
  [ -n "$PGCID" ] && docker rm -f "$PG_CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

fail() { echo "❌ $1"; exit 1; }
ok()   { echo "✅ $1"; }

# 0) Pre-Check: Docker läuft? (sonst BLOCKED statt kryptischem Build-Fehler)
docker info >/dev/null 2>&1 || fail "Docker-Daemon nicht erreichbar (BLOCKED)"

# 1) Build
echo "==> 1/5 Image bauen ($IMG)"
docker build -q -t "$IMG" . >/dev/null || fail "docker build fehlgeschlagen"
ok "Build grün"

# 1b) Optionaler Alembic-Container-Abnahme-Block (US-057, FEATURE-006 EARS 4):
#     WHEN der Container mit erreichbarem Postgres startet THE SYSTEM SHALL den
#     Migrations-Schritt mit rc=0 abschließen und alembic_version SHALL
#     gestampt/aktuell sein. Nur mit SIM_GATE_DB=1; ohne Env unverändertes
#     Verhalten. Eigener Wegwerf-PG auf 15432, Migrate-Beweis, dann runter.
if [ "${SIM_GATE_DB:-0}" = "1" ]; then
  echo "==> 1b/5 Alembic-Container-Abnahme (SIM_GATE_DB, Wegwerf-PG :$PG_PORT)"
  # Eventuell verwaisten Vorlauf-Container abräumen (idempotent).
  docker rm -f "$PG_CONTAINER" >/dev/null 2>&1 || true
  PGCID=$(docker run -d --rm --name "$PG_CONTAINER" \
    -p "${PG_PORT}:5432" \
    -e POSTGRES_USER=kfstudio -e POSTGRES_PASSWORD=kfstudio \
    -e POSTGRES_DB=kfstudio postgres:16-alpine) \
    || fail "Wegwerf-Postgres-Start fehlgeschlagen"

  # Ready-Poll (reine bash-Schleife, kein GNU-Abbruch-Wrapper — macOS,
  # Sprint-10-RETRO).
  echo "    auf Postgres warten (max 30×1s)"
  j=0
  while [ "$j" -lt 30 ]; do
    docker exec "$PG_CONTAINER" pg_isready -U kfstudio -d kfstudio \
      >/dev/null 2>&1 && break
    j=$((j + 1))
    sleep 1
  done
  docker exec "$PG_CONTAINER" pg_isready -U kfstudio -d kfstudio \
    >/dev/null 2>&1 || fail "Wegwerf-Postgres nicht ready nach ${j}s"
  ok "Wegwerf-Postgres ready (nach ${j}s)"

  # Migrate-Schritt im App-Image gegen den erreichbaren PG. Schema exakt wie
  # backend/db.py erwartet (postgresql+asyncpg://). host.docker.internal auf
  # macOS reicht — Container erreicht den gemappten Host-Port.
  MIG_LOG=$(docker run --rm \
    -e DATABASE_URL="postgresql+asyncpg://kfstudio:kfstudio@host.docker.internal:${PG_PORT}/kfstudio" \
    "$IMG" python -m backend.migrate 2>&1)
  mrc=$?
  echo "$MIG_LOG" | sed 's/^/    /'
  [ "$mrc" = "0" ] || fail "Migrate-Schritt rc=$mrc (kein rc=0)"
  # Beweis-Marker im Log: entweder gestampt ODER upgrade head rc=0.
  echo "$MIG_LOG" | grep -Eq "Alembic gestampt auf|alembic upgrade head rc=0" \
    || fail "kein Alembic-Log-Marker (gestampt/upgrade head)"

  # alembic_version muss existieren und auf head stehen (vom Host via psql).
  AV=$(docker exec "$PG_CONTAINER" \
    psql -U kfstudio -d kfstudio -tA -c \
    "SELECT version_num FROM alembic_version" 2>/dev/null || true)
  [ -n "$AV" ] || fail "alembic_version leer/fehlt (nicht gestampt)"
  ok "Alembic-Abnahme: migrate rc=0, alembic_version=${AV}"

  docker rm -f "$PG_CONTAINER" >/dev/null 2>&1 || true
  PGCID=""
fi

# 2) Container starten — OHNE DATABASE_URL, OHNE Volume (= Prod-Worst-Case:
#    DB-los + Korpus-Volume fehlt → graceful-Pfade müssen tragen).
echo "==> 2/5 Container starten (ohne DB, ohne Volume)"
CID=$(docker run -d --rm \
  -e "KF_SESSION_SECRET=$SECRET" \
  -e "KF_USERS=$KF_USERS_VAL" \
  -p "${PORT}:8000" "$IMG") \
  || fail "docker run fehlgeschlagen"

# 3) Auf uvicorn warten (Polling max 20×2s = ~40s — reine bash-Schleife)
echo "==> 3/5 Auf uvicorn warten (max 20×2s)"
BASE="http://localhost:${PORT}"
code=""
i=0
while [ "$i" -lt 20 ]; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/api/health" 2>/dev/null || true)
  [ "$code" = "200" ] && break
  i=$((i + 1))
  sleep 2
done
[ "$code" = "200" ] || { docker logs "$CID" 2>&1 | tail -20; \
  fail "/api/health nicht 200 nach $((i * 2))s (code=$code)"; }
# JSON-Plausibilität: db:false ist OK (kein DATABASE_URL) — Route lebt.
health=$(curl -s "${BASE}/api/health" || true)
echo "$health" | grep -q '"ok":true' || fail "/api/health JSON unerwartet ($health)"
ok "/api/health 200, ok:true (nach $((i * 2))s; db:false erwartet)"

# 4) Modul-Health-Routen (mit im-Container-gemintetem Session-Cookie)
echo "==> 4/5 Modul-Health-Routen + Engine-Import-Beweis"
COOKIE=$(docker exec "$CID" python -c \
  "from backend.app import make_cookie; print(make_cookie('${USER_EMAIL}'))" \
  2>/dev/null || true)
[ -n "$COOKIE" ] || fail "make_cookie lieferte kein Cookie"

# Ohne Cookie: 401 (Route lebt hinter Auth-Gate) — definierter Erwartungswert.
nocode=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/api/angebot/health" 2>/dev/null || true)
[ "$nocode" = "401" ] && ok "/api/angebot/health ohne Cookie → 401 (Auth-Gate lebt)" \
  || echo "   (Hinweis: ohne Cookie code=$nocode, erwartet 401)"

ah=$(curl -s -H "Cookie: kf_sess=${COOKIE}" "${BASE}/api/angebot/health" || true)
echo "$ah" | grep -q '"engine":true' \
  || fail "/api/angebot/health: engine!=true ($ah)"
ok "/api/angebot/health engine:true"

ph=$(curl -s -H "Cookie: kf_sess=${COOKIE}" "${BASE}/api/praesentation/health" || true)
echo "$ph" | grep -q '"engine":true' \
  || fail "/api/praesentation/health: engine!=true ($ph)"
# korpus:false ist OK + ERWARTET (kein Volume im Sim — graceful, wie Prod
# ohne Mount). Wir bestehen NICHT auf korpus:true.
if echo "$ph" | grep -q '"korpus":false'; then
  ok "/api/praesentation/health engine:true, korpus:false (erwartet, graceful)"
else
  ok "/api/praesentation/health engine:true ($ph)"
fi

# Engine-Import-Beweis (zwei unabhängige Wege):
#  (a) App-Marker: ENGINE_OK True + ENGINE_ERR leer
err=$(docker exec "$CID" python -c \
  "from backend.app import ENGINE_OK, ENGINE_ERR; \
print('OK' if ENGINE_OK and not ENGINE_ERR else 'ERR:'+ENGINE_ERR)" 2>/dev/null || true)
[ "$err" = "OK" ] || fail "Engine-Import-Marker nicht sauber ($err)"
#  (b) Direkter Import aus engine/scripts (exit 0)
docker exec "$CID" python3 -c \
  "import sys; sys.path.insert(0,'/app/engine/scripts'); import angebot_model" \
  >/dev/null 2>&1 || fail "import angebot_model aus engine/scripts fehlgeschlagen"
# Keine Tracebacks im Log
docker logs "$CID" 2>&1 | grep -q "Traceback" \
  && fail "Traceback im Container-Log" || true
ok "Engine-Import-Beweis: ENGINE_OK=True, angebot_model importierbar, kein Traceback"

# 5) reconstruct.js / pptxgenjs-Probe
echo "==> 5/5 reconstruct.js + pptxgenjs-Probe"
#  (a) pptxgenjs auflösbar (require aus node_modules)
docker exec "$CID" node -e \
  "require('/app/engine/spike-pptxgenjs/node_modules/pptxgenjs'); console.log('pptxgenjs ok')" \
  >/dev/null 2>&1 || fail "require(pptxgenjs) im Container fehlgeschlagen"
#  (b) reconstruct.js end-to-end gegen mitgelieferte elements.json → nicht-leere
#      .pptx (beweist pptxgenjs/jszip/lib + reconstruct-Pfad zusammen)
recon=$(docker exec "$CID" sh -c '
  cd /app/engine/spike-pptxgenjs &&
  node reconstruct.js elements.json /tmp/sim_gate.pptx >/tmp/recon.log 2>&1 &&
  test -s /tmp/sim_gate.pptx &&
  echo "RECON_OK $(wc -c < /tmp/sim_gate.pptx)"
' 2>/dev/null || true)
case "$recon" in
  RECON_OK\ *) ok "reconstruct.js grün (pptxgenjs ok, pptx ${recon#RECON_OK } bytes)" ;;
  *) docker exec "$CID" tail -5 /tmp/recon.log 2>/dev/null || true
     fail "reconstruct.js-Probe fehlgeschlagen" ;;
esac

echo ""
echo "SIM-GATE GRUEN — Container lebt (Build + Health + Engine + reconstruct)."
exit 0
