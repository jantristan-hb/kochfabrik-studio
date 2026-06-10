"""Unscharfe Deck-Logos durch das offizielle scharfe KOCHFABRIK-Logo
ersetzen. Perceptual-Match (16x16 aHash auf weiss) gegen das Original;
Treffer in logos.json auf das offizielle File umbiegen. Deterministisch.
"""
import json
from PIL import Image

OFFICIAL_SRC = "assets/logo_src/kochfabrik.png"
OFFICIAL = "assets/logos/kochfabrik_official.png"
GOLD = (170, 131, 57)  # KF-Gold (#AA8339, aus pdfminer-Fill)

# Logo auf KF-Gold tinten: jedes nicht-transparente Pixel -> Gold,
# Alpha (Form/Anti-Aliasing) bleibt exakt erhalten. Dunkler "KOCHFABRIK"-
# Schriftzug wird damit gold und auf dunklen Slides lesbar.
def goldify(src, dst):
    im = Image.open(src).convert("RGBA")
    a = im.getchannel("A")
    solid = Image.new("RGBA", im.size, GOLD + (255,))
    solid.putalpha(a)
    solid.save(dst)


goldify(OFFICIAL_SRC, OFFICIAL)


def ahash(path, n=16):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    g = Image.alpha_composite(bg, im).convert("L").resize((n, n))
    px = list(g.getdata())
    avg = sum(px) / len(px)
    return [1 if p >= avg else 0 for p in px]


def ham(a, b):
    return sum(x != y for x, y in zip(a, b))


ref = ahash(OFFICIAL)
m = json.load(open("logos.json"))
hits = []
for src, out in list(m.items()):
    try:
        d = ham(ref, ahash(out))
    except Exception:
        continue
    if d <= 30:                       # KOCHFABRIK-Lockup erkannt
        m[src] = OFFICIAL
        hits.append((src, d))

json.dump(m, open("logos.json", "w"), indent=1)
print(f"ersetzt: {len(hits)} Deck-Logos -> offizielles Original")
for s, d in hits:
    print(f"  {s}  (dist {d})")
