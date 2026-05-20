#!/usr/bin/env bash
# vendor.sh — Engine aus der SINGLE SOURCE (pptxgenerator_v2) ins
# Studio-Bundle synchronisieren. NIE engine/ von Hand editieren.
#
# Ablauf bei jeder Präsentations-/Angebots-Generator-Änderung:
#   1. In pptxgenerator_v2/phase0/ entwickeln (Quelle)
#   2. ./vendor.sh            (re-vendor + pgbundle-Regen + Sim-Gate)
#   3. git add engine && git commit && git push
#   4. ./vendor.sh --deploy   (force-deploy via Coolify)  ODER manuell
set -euo pipefail

SRC="/home/jrudat/work/03 AKARA Solutions GmbH/kochfabrik/pptxgenerator_v2/phase0"
DST="$(cd "$(dirname "$0")" && pwd)/engine/phase0"
UUID=yu2fqx0twmtqcp6zyx2e59si
REFSLUG=10-182-raumkarussell-gmbh-12-09-2026
# Autorierte Static-Slide-Decks (kein Korpus, gehören INS Bundle).
# kf-ausstattung-location = Static Slide "Ausstattung und Location"
# (static_slide category='AUSSTATTUNG', pflicht). Achtung: data/cache/
# ist auf dem Server ein Coolify Directory Mount → das vendorte Deck
# wird zur Laufzeit überlagert. Authoritativ ist das Server-Volume
# (siehe Hinweis am Ende / rsync). Vendoren = Local-Sim + Fallback.
STATIC_DECKS=(kf-ausstattung-location)

echo "==> 1/4 Scripts vendoren"
mkdir -p "$DST/scripts" "$DST/spike-pptxgenjs" "$DST/data/cache"
# Prune: in der Quelle gelöschte .py dürfen nicht im Bundle zurückbleiben
# (cp aliniert nicht — sonst driftet toter Code wie ein Zombie mit).
rm -f "$DST"/scripts/*.py
cp "$SRC"/scripts/*.py "$DST/scripts/"
cp -r "$SRC"/spike-pptxgenjs/{lib,node_modules,reconstruct.js,package.json} \
      "$DST/spike-pptxgenjs/"

echo "==> 2/4 Templates + Referenz-/Static-Cache-Decks vendoren"
cp "$SRC"/data/cover_template.elements.json \
   "$SRC"/data/angebot_template.elements.json "$DST/data/"
rm -rf "$DST/data/cache/$REFSLUG"
cp -r "$SRC/data/cache/$REFSLUG" "$DST/data/cache/"
for d in "${STATIC_DECKS[@]}"; do
  [ -d "$SRC/data/cache/$d" ] || { echo "   ❌ Static-Deck fehlt: $d"; exit 1; }
  rm -rf "$DST/data/cache/$d"
  cp -r "$SRC/data/cache/$d" "$DST/data/cache/"
  echo "   static: $d"
done

echo "==> 3/4 pgbundle aus Live-DB regenerieren (Snapshot → SRC + DST)"
python3 - "$SRC" "$DST" <<'PY'
import sys, json, numpy as np, psycopg2
src, dst = sys.argv[1], sys.argv[2]
cx = psycopg2.connect(host="localhost", port=5434, user="postgres",
                      password="pptxgen", dbname="pptxgen")
cu = cx.cursor()
cu.execute("SELECT deck,page,src_pdf,module_type,module_label,"
           "embedding::text FROM menu_composition")
r = cu.fetchall()
emb = np.array([[float(x) for x in q[5].strip("[]").split(",")]
                for q in r], np.float32)
deck = np.array([q[0] for q in r], object)
page = np.array([q[1] for q in r])
spdf = np.array([q[2] for q in r], object)
mt = np.array([str(q[3]) for q in r], object)
ml = np.array([str(q[4]) for q in r], object)
cu.execute("SELECT deck,page,src_pdf,category,skel_pos,inclusion "
           "FROM static_slide")
ss = [dict(deck=a, page=int(b), src_pdf=c, category=d,
           skel_pos=float(e), inclusion=f)
      for a, b, c, d, e, f in cu.fetchall()]
cx.close()
# Quelle (pg_shim-Sim liest dirname(__file__)/../data) UND Bundle
# (Live-Container) konsistent halten — sonst testet die Sim stale.
for base in (src, dst):
    np.savez(base + "/data/pgbundle.npz", emb=emb, deck=deck, page=page,
             src_pdf=spdf, module_type=mt, module_label=ml)
    json.dump(ss, open(base + "/data/static_slide.json", "w"),
              ensure_ascii=False)
print("   menu_composition:", len(r), "| static_slide:", len(ss),
      "| AUSSTATTUNG:",
      [s for s in ss if s["category"] == "AUSSTATTUNG"])
PY

echo "==> 4/4 Container-Pfad-Sim (Gate, gegen vollen lokalen Cache)"
GK=$(grep -m1 '^GEMINI_API_KEY=' ~/work/.env | cut -d= -f2- | tr -d '"')
printf '## Angebot — Sim GmbH (Sommerfest)\n\n| Veranstaltungsdatum | 1. Juli 2026 |\n\n### BIG BBQ\n\nSpareribs\nKrautsalat\n' > /tmp/vendor_sim.md
( cd "$SRC/scripts" && timeout 200 env HOME=/nonexistent-container \
    GEMINI_API_KEY="$GK" PPTX_PGSHIM=1 \
    python3 assemble.py /tmp/vendor_sim.md -o /tmp/vendor_sim.pptx >/dev/null 2>&1 )
[ -s /tmp/vendor_sim.pptx ] && echo "   ✅ Sim grün ($(stat -c%s /tmp/vendor_sim.pptx) bytes)" \
  || { echo "   ❌ Sim FEHLGESCHLAGEN — NICHT deployen"; exit 1; }

VOL="/data/coolify/applications/$UUID/cache"
echo "==> Bundle synchron."
echo "    WICHTIG: data/cache/ ist auf dem Server ein Coolify Directory"
echo "    Mount → vendorte Cache-Decks werden zur Laufzeit ÜBERLAGERT."
echo "    Static-/Korpus-Decks müssen aufs Host-Volume:"
for d in "${STATIC_DECKS[@]}"; do
  echo "      rsync -az --delete \"$SRC/data/cache/$d/\" \\"
  echo "        root@188.245.110.5:$VOL/$d/"
done
if [ "${1:-}" = "--deploy" ] || [ "${2:-}" = "--push-static" ] \
   || [ "${1:-}" = "--push-static" ]; then
  echo "==> Static-Decks aufs Server-Volume rsyncen"
  for d in "${STATIC_DECKS[@]}"; do
    rsync -az --delete -e "ssh -i $HOME/.ssh/hetzner_id" \
      "$SRC/data/cache/$d/" "root@188.245.110.5:$VOL/$d/" \
      && echo "   ✅ $d → Volume" || { echo "   ❌ rsync $d"; exit 1; }
  done
fi

# Slide-Suche-Previews: alle cache/*/preview/*.png aufs Server-Volume
# (lokal mit phase0/scripts/render_previews.py vorgeneriert). Wir
# rsyncen das ganze cache-Tree, --include-Pattern beschränkt auf
# preview/-Verzeichnisse → kein Risiko fürs Asset-Dir (sonst würden
# wir 4,8 GB hochladen). Nur EIN Rsync pro Aufruf (idempotent).
if [ "${1:-}" = "--push-previews" ] \
   || [ "${2:-}" = "--push-previews" ] \
   || [ "${1:-}" = "--deploy" ]; then
  PREVIEW_CNT=$(find "$SRC/data/cache" -type f -name 'p*.png' \
    -path '*/preview/*' 2>/dev/null | wc -l)
  echo "==> Slide-Previews aufs Server-Volume ($PREVIEW_CNT PNGs)"
  if [ "$PREVIEW_CNT" -gt 0 ]; then
    rsync -az -e "ssh -i $HOME/.ssh/hetzner_id" \
      --include='*/' --include='preview/***' --exclude='*' \
      "$SRC/data/cache/" "root@188.245.110.5:$VOL/" \
      && echo "   ✅ Previews → Volume" \
      || { echo "   ❌ rsync Previews"; exit 1; }
  else
    echo "   ⚠ Keine preview/*.png lokal — render_previews.py erst laufen"
  fi
fi

if [ "${1:-}" = "--deploy" ]; then
  echo "==> Force-Deploy via Coolify"
  set -a; source ~/work/.env; set +a
  curl -s "https://coolify.flinkbase.com/api/v1/deploy?uuid=$UUID&force=true" \
       -H "Authorization: Bearer $COOLIFY_TOKEN" >/dev/null && echo "   queued"
fi
