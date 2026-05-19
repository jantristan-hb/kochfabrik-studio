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

echo "==> 1/4 Scripts vendoren"
mkdir -p "$DST/scripts" "$DST/spike-pptxgenjs" "$DST/data/cache"
cp "$SRC"/scripts/*.py "$DST/scripts/"
cp -r "$SRC"/spike-pptxgenjs/{lib,node_modules,reconstruct.js,package.json} \
      "$DST/spike-pptxgenjs/"

echo "==> 2/4 Templates + Referenz-Cache-Slug vendoren"
cp "$SRC"/data/cover_template.elements.json \
   "$SRC"/data/ausstattung_template.elements.json \
   "$SRC"/data/angebot_template.elements.json "$DST/data/"
rm -rf "$DST/data/cache/$REFSLUG"
cp -r "$SRC/data/cache/$REFSLUG" "$DST/data/cache/"

echo "==> 3/4 pgbundle aus Live-DB regenerieren (Snapshot!)"
python3 - "$SRC" "$DST" <<'PY'
import sys, json, numpy as np, psycopg2
src, dst = sys.argv[1], sys.argv[2]
cx = psycopg2.connect(host="localhost", port=5434, user="postgres",
                      password="pptxgen", dbname="pptxgen")
cu = cx.cursor()
cu.execute("SELECT deck,page,src_pdf,module_type,module_label,"
           "embedding::text FROM menu_composition")
r = cu.fetchall()
np.savez(dst + "/data/pgbundle.npz",
         emb=np.array([[float(x) for x in q[5].strip("[]").split(",")]
                        for q in r], np.float32),
         deck=np.array([q[0] for q in r], object),
         page=np.array([q[1] for q in r]),
         src_pdf=np.array([q[2] for q in r], object),
         module_type=np.array([str(q[3]) for q in r], object),
         module_label=np.array([str(q[4]) for q in r], object))
cu.execute("SELECT deck,page,src_pdf,category,skel_pos,inclusion "
           "FROM static_slide")
json.dump([dict(deck=a, page=int(b), src_pdf=c, category=d,
                skel_pos=float(e), inclusion=f)
           for a, b, c, d, e, f in cu.fetchall()],
          open(dst + "/data/static_slide.json", "w"), ensure_ascii=False)
cx.close()
print("   menu_composition:", len(r))
PY

echo "==> 4/4 Container-Pfad-Sim (Gate, gegen vollen lokalen Cache)"
GK=$(grep -m1 '^GEMINI_API_KEY=' ~/work/.env | cut -d= -f2- | tr -d '"')
printf '## Angebot — Sim GmbH (Sommerfest)\n\n| Veranstaltungsdatum | 1. Juli 2026 |\n\n### BIG BBQ\n\nSpareribs\nKrautsalat\n' > /tmp/vendor_sim.md
( cd "$SRC/scripts" && timeout 200 env HOME=/nonexistent-container \
    GEMINI_API_KEY="$GK" PPTX_PGSHIM=1 \
    python3 assemble.py /tmp/vendor_sim.md -o /tmp/vendor_sim.pptx >/dev/null 2>&1 )
[ -s /tmp/vendor_sim.pptx ] && echo "   ✅ Sim grün ($(stat -c%s /tmp/vendor_sim.pptx) bytes)" \
  || { echo "   ❌ Sim FEHLGESCHLAGEN — NICHT deployen"; exit 1; }

echo "==> Bundle synchron. Korpus-Cache-Hinweis: bei NEUEN Korpus-Decks"
echo "    zusätzlich rsync nach root@188.245.110.5:/data/coolify/"
echo "    applications/$UUID/cache/ (Volume-Snapshot)."

if [ "${1:-}" = "--deploy" ]; then
  echo "==> Force-Deploy via Coolify"
  set -a; source ~/work/.env; set +a
  curl -s "https://coolify.flinkbase.com/api/v1/deploy?uuid=$UUID&force=true" \
       -H "Authorization: Bearer $COOLIFY_TOKEN" >/dev/null && echo "   queued"
fi
