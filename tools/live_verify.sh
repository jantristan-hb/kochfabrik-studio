#!/usr/bin/env bash
# live_verify.sh — Live-Health-Check der Prod-Instanz, VOR und NACH dem
# Cutover lauffähig (US-051, FEATURE-005 EARS 4). Deterministisch ohne
# Credentials: /api/health (public) muss 200 + db:true liefern; die
# auth-gateten Modul-Routen müssen 401 liefern (= Route lebt in der
# laufenden Revision — ein 404 hieße: Route fehlt, Deploy kaputt).
# Exit 0 = alle grün, exit 1 = mindestens ein Check rot.
#
# macOS-tauglich: keine GNU-only-Tools, reines curl + bash.
set -euo pipefail

BASE="${BASE_URL:-https://kochfabrik-studio.flinkbase.com}"
CURL=(curl -sS -m 15)

fails=0
ok()   { echo "✅ $1"; }
bad()  { echo "❌ $1"; fails=$((fails + 1)); }

echo "==> Live-Verify gegen $BASE"

# 1) /api/health — public, MUSS 200 + db:true (DB erreichbar in Prod)
body=$("${CURL[@]}" "$BASE/api/health" 2>/dev/null || true)
code=$("${CURL[@]}" -o /dev/null -w '%{http_code}' "$BASE/api/health" 2>/dev/null || true)
if [ "$code" = "200" ] && printf '%s' "$body" | grep -q '"db":true'; then
  ok "/api/health 200, db:true"
elif [ "$code" = "200" ]; then
  bad "/api/health 200 aber db!=true ($body)"
else
  bad "/api/health code=$code (erwartet 200)"
fi

# 2) Auth-gatete Modul-Routen — erwartet 401 ohne Cookie (Route lebt; 200
#    auch ok falls je public). Ein 404/5xx = Route fehlt/kaputt = FAIL.
check_route() {
  local path="$1" method="${2:-GET}" allow="$3"
  local c
  if [ "$method" = "POST" ]; then
    c=$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X POST \
      -H 'Content-Type: application/json' -d '{"query":"smoke"}' \
      "$BASE$path" 2>/dev/null || true)
  else
    c=$("${CURL[@]}" -o /dev/null -w '%{http_code}' "$BASE$path" 2>/dev/null || true)
  fi
  # Treffer auf erlaubte Codes (Wort-genau, damit 200 nicht 2000 matcht)
  if printf ' %s ' "$allow" | grep -q " $c "; then
    ok "$method $path → $c (Route lebt)"
  else
    bad "$method $path → $c (erlaubt: $allow)"
  fi
}

check_route "/api/angebot/health"       GET  "200 401"
check_route "/api/praesentation/health" GET  "200 401"
# slidesuche/search: 401 (kein Cookie) / 422 (Validierung) / 200 zulässig,
# 5xx (oder 404) = FAIL.
check_route "/api/slidesuche/search"     POST "200 401 422"

# 3) Statische Login-Seite — MUSS 200 (Frontend ausgeliefert)
check_route "/login.html"                GET  "200"

echo ""
if [ "$fails" -eq 0 ]; then
  echo "LIVE-VERIFY GRUEN — alle Health-Routen erreichbar."
  exit 0
else
  echo "LIVE-VERIFY ROT — $fails Check(s) fehlgeschlagen."
  exit 1
fi
