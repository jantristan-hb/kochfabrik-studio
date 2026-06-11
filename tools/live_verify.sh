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

# 4) OPTIONAL: Deep-Check (LIVE_DEEP=1) — hinter dem Auth-Gate prüfen, dass
#    Engine UND Korpus wirklich geladen sind. Hintergrund (Incident
#    2026-06-11): Ein falsch gemountetes Coolify-Volume lieferte den
#    Präsentationsgenerator ohne Korpus aus — UNSICHTBAR für die 401-Checks
#    oben (Auth verdeckt das korpus-Flag) und für das Sim-Gate (korpus:false
#    gilt dort als graceful-ok). Der Deep-Check schließt diese Lücke: er mintet
#    via SSH+docker exec ein Session-Cookie und ruft die Health-Routen
#    AUTHENTIFIZIERT auf, sodass die echten engine/korpus-Flags sichtbar werden.
#    Read-only: nur Cookie minten + GET health, keine schreibenden Calls.
#    Ohne LIVE_DEEP byte-identisch zum bisherigen Verhalten.
if [ "${LIVE_DEEP:-}" = "1" ]; then
  echo ""
  echo "==> Deep-Check (LIVE_DEEP=1) — Engine/Korpus hinter dem Auth-Gate"
  SSH_HOST="${KF_SSH_HOST:-root@188.245.110.5}"
  SSH_KEY="${KF_SSH_KEY:-$HOME/.ssh/hetzner_id}"

  # In-Container: Cookie für den ersten KF_USERS-User minten, beide Health-
  # Routen authentifiziert abrufen und kompakt als "<route> engine=<b> korpus=<b>"
  # ausgeben (korpus nur bei praesentation). Bei Fehler: "ROUTE ERR <msg>".
  remote_py='
import sys, os, json, urllib.request
sys.path.insert(0, "/app")
from backend.engine_glue import make_cookie
user = os.environ.get("KF_USERS", "").split("|")[0].split(",")[0].split(":")[0]
cookie = "kf_sess=" + make_cookie(user)
for route in ("praesentation", "angebot"):
    try:
        req = urllib.request.Request("http://localhost:8000/api/%s/health" % route)
        req.add_header("Cookie", cookie)
        data = json.loads(urllib.request.urlopen(req, None, 10).read().decode())
        eng = bool(data.get("engine"))
        if route == "praesentation":
            kor = bool(data.get("korpus"))
            print("%s engine=%s korpus=%s" % (route, eng, kor))
        else:
            print("%s engine=%s" % (route, eng))
    except Exception as e:
        print("%s ERR %s" % (route, e))
'
  cid=$(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=15 "$SSH_HOST" \
    'docker ps -qf name=yu2fqx0' 2>/dev/null || true)
  if [ -z "$cid" ]; then
    bad "Deep-Check: App-Container (name=yu2fqx0) nicht gefunden via SSH"
  else
    deep_out=$(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=15 "$SSH_HOST" \
      "docker exec -i $cid python3 -" <<PYEOF 2>/dev/null || true
$remote_py
PYEOF
    )
    if [ -z "$deep_out" ]; then
      bad "Deep-Check: keine Ausgabe vom Container (docker exec fehlgeschlagen)"
    else
      # praesentation: engine=True UND korpus=True erwartet
      praes=$(printf '%s\n' "$deep_out" | grep '^praesentation ' || true)
      if printf '%s' "$praes" | grep -q 'engine=True' && \
         printf '%s' "$praes" | grep -q 'korpus=True'; then
        ok "Deep praesentation/health → engine:true, korpus:true"
      else
        bad "Deep praesentation/health → $praes (erwartet engine=True korpus=True)"
      fi
      # angebot: engine=True erwartet
      ang=$(printf '%s\n' "$deep_out" | grep '^angebot ' || true)
      if printf '%s' "$ang" | grep -q 'engine=True'; then
        ok "Deep angebot/health → engine:true"
      else
        bad "Deep angebot/health → $ang (erwartet engine=True)"
      fi
    fi
  fi
fi

echo ""
if [ "$fails" -eq 0 ]; then
  echo "LIVE-VERIFY GRUEN — alle Health-Routen erreichbar."
  exit 0
else
  echo "LIVE-VERIFY ROT — $fails Check(s) fehlgeschlagen."
  exit 1
fi
