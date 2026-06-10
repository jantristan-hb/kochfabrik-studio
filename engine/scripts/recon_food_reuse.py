"""Recon v3: Werden die SPEISENFOTOS selbst recycelt? (Furniture entfernt)

Korrigiert den Furniture-Confound von v1/v2:
- Furniture-Strip: Bild-Hash in >=80% der Decks  -> Template, raus.
- Größenfilter: nur große Hero-/Speisenfotos (PIL-Pixelmaße), kleine
  quadratische Logos/Badges raus.
- Reuse der verbleibenden Speisenfoto-Kandidaten EXAKT (sha256) UND
  PERCEPTUAL (8x8 aHash, Hamming<=5) -> re-encode-fest.

Nur Aggregat + Slide-für-Slide-Profil (3 Decks) nach stdout und
phase0/recon-food-reuse.md. Keine Pixel in den Chat-Kontext.
"""
import hashlib
import os
import subprocess
import sys
from collections import defaultdict
from PIL import Image

CORPUS = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACT = os.path.join(HERE, "cache", "extract50")
MIN_BYTES = 8 * 1024
FOOD_MIN_AREA = 500_000      # ~ >= 0.5 MP  (1920x1065 hero >> das)
FOOD_MIN_DIM = 600           # kürzeste Kante
FURNITURE_DECK_FRAC = 0.80   # in >=80% Decks => Template-Furniture


def list_sample(n=50):
    out = subprocess.run(["bash", "-lc",
        f'cd "{CORPUS}" && ls *.pdf | grep -v "^Angebot #"'],
        capture_output=True, text=True)
    full = [x for x in out.stdout.splitlines() if x]
    if len(full) <= n:
        return full
    step = len(full) / n
    return [full[int(i * step)] for i in range(n)]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def ahash(img):
    g = img.convert("L").resize((8, 8), Image.BILINEAR)
    px = list(g.getdata())
    avg = sum(px) / 64
    bits = 0
    for i, p in enumerate(px):
        if p >= avg:
            bits |= (1 << i)
    return bits


def ham(a, b):
    return bin(a ^ b).count("1")


def page_of(fn):
    import re
    m = re.search(r"-(\d+)-(\d+)\.[A-Za-z]+$", fn)
    return int(m.group(1)) if m else -1


SAMPLE = list_sample(50)
print(f"Sample: {len(SAMPLE)} Decks\n")

# 1) Extrahieren + klassifizieren
records = []  # (deck, page, sha, ahash, w, h, is_food)
for i, deck in enumerate(SAMPLE):
    src = os.path.join(CORPUS, deck)
    if not os.path.isfile(src):
        print(f"!! fehlt: {deck}", file=sys.stderr)
        continue
    d = os.path.join(EXTRACT, f"{i:02d}")
    os.makedirs(d, exist_ok=True)
    if not os.listdir(d):
        subprocess.run(["pdfimages", "-png", "-p", src, os.path.join(d, "p")],
                        check=False, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    for fn in os.listdir(d):
        fp = os.path.join(d, fn)
        if os.path.getsize(fp) < MIN_BYTES:
            continue
        try:
            im = Image.open(fp)
            w, h = im.size
        except Exception:
            continue
        is_food = (w * h >= FOOD_MIN_AREA and min(w, h) >= FOOD_MIN_DIM)
        try:
            ah = ahash(im)
        except Exception:
            ah = None
        records.append([deck, page_of(fn), sha(fp), ah, w, h, is_food])

# 2) Furniture per Deck-Frequenz erkennen (über ALLE Bilder)
hash_decks = defaultdict(set)
for r in records:
    hash_decks[r[2]].add(r[0])
ndecks = len(set(r[0] for r in records))
furniture = {h for h, ds in hash_decks.items()
             if len(ds) >= FURNITURE_DECK_FRAC * ndecks}

# 3) Speisenfoto-Kandidaten = is_food UND nicht Furniture-Hash
food = [r for r in records if r[6] and r[2] not in furniture]
food_sha_decks = defaultdict(set)
for r in food:
    food_sha_decks[r[2]].add(r[0])

# perceptual: greedy-cluster über alle Food-aHashes
ahs = [(r[3], r[0]) for r in food if r[3] is not None]
clusters = []  # (repr_hash, set(decks), count)
for ah, dk in ahs:
    placed = False
    for c in clusters:
        if ham(ah, c[0]) <= 5:
            c[1].add(dk)
            c[2][0] += 1
            placed = True
            break
    if not placed:
        clusters.append([ah, {dk}, [1]])

tot_food = len(food)
uniq_sha = len(food_sha_decks)
food_sha_multi = sum(1 for ds in food_sha_decks.values() if len(ds) >= 2)
food_inst_reused = sum(1 for r in food if len(food_sha_decks[r[2]]) >= 2)
pclusters = len(clusters)
pclusters_multi = sum(1 for c in clusters if len(c[1]) >= 2)
pinst_reused = sum(c[2][0] for c in clusters if len(c[1]) >= 2)

L = []
L.append(f"# Recon v3: Speisenfoto-Reuse, Furniture entfernt ({ndecks} Decks)\n")
L.append(f"- Bild-Instanzen gesamt: {len(records)}")
L.append(f"- Als Furniture erkannt (Hash in ≥{int(FURNITURE_DECK_FRAC*100)}% "
         f"Decks): **{len(furniture)} Hashes**")
L.append(f"- **Speisenfoto-Kandidaten** (groß, kein Furniture): "
         f"**{tot_food}**\n")
L.append("## Recyceln sich die SPEISENFOTOS?\n")
L.append(f"**Exakt (sha256):**")
L.append(f"- eindeutige Fotos: {uniq_sha} → Dedup "
         f"{100*(1-uniq_sha/max(tot_food,1)):.0f}%")
L.append(f"- Fotos in ≥2 Decks: **{food_sha_multi}** "
         f"({100*food_sha_multi/max(uniq_sha,1):.0f}% der eindeutigen)")
L.append(f"- Instanzen, die recycelt sind: "
         f"**{100*food_inst_reused/max(tot_food,1):.0f}%**\n")
L.append(f"**Perceptual (aHash, re-encode-fest):**")
L.append(f"- visuell eigenständige Fotos (Cluster): {pclusters}")
L.append(f"- Cluster in ≥2 Decks: **{pclusters_multi}** "
         f"({100*pclusters_multi/max(pclusters,1):.0f}%)")
L.append(f"- Instanzen in deck-übergreifenden Clustern: "
         f"**{100*pinst_reused/max(tot_food,1):.0f}%**\n")
L.append("## Slide-für-Slide-Profil (erste 3 Decks)\n")
for i, deck in enumerate(SAMPLE[:3]):
    pp = defaultdict(lambda: [0, 0])  # page -> [food, furniture]
    for r in records:
        if r[0] != deck:
            continue
        if r[2] in furniture:
            pp[r[1]][1] += 1
        elif r[6]:
            pp[r[1]][0] += 1
    L.append(f"**{deck}**")
    for pg in sorted(p for p in pp if p > 0):
        L.append(f"  S{pg}: Speisenfotos={pp[pg][0]} Furniture={pp[pg][1]}")
    L.append("")

rep = "\n".join(L)
print(rep)
with open(os.path.join(HERE, "recon-food-reuse.md"), "w") as f:
    f.write(rep + "\n")
