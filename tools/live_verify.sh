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

BASE="${LIVE_BASE:-https://kochfabrik-studio.flinkbase.com}"
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

# 2) Auth-gatete Routen — erwartet 401 (Route lebt; 404 = Route fehlt =
#    kaputte Revision). 200 wäre ebenfalls OK (falls je public), aber 401
#    ist der deterministische Erwartungswert ohne Cookie.
check_auth_gated() {
  local path="$1" method="${2:-GET}"
  local c
  if [ "$method" = "POST" ]; then
    c=$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X POST \
      -H 'Content-Type: application/json' -d '{"query":"smoke"}' \
      "$BASE$path" 2>/dev/null || true)
  else
    c=$("${CURL[@]}" -o /dev/null -w '%{http_code}' "$BASE$path" 2>/dev/null || true)
  fi
  case "$c" in
    401|200) ok "$method $path → $c (Route lebt)" ;;
    *)       bad "$method $path → $c (erwartet 401/200; 404 = Route fehlt)" ;;
  esac
}

check_auth_gated "/api/angebot/health"
check_auth_gated "/api/praesentation/health"
check_auth_gated "/api/slidesuche/search" "POST"

echo ""
if [ "$fails" -eq 0 ]; then
  echo "LIVE-VERIFY GRUEN — alle Health-Routen erreichbar."
  exit 0
else
  echo "LIVE-VERIFY ROT — $fails Check(s) fehlgeschlagen."
  exit 1
fi
