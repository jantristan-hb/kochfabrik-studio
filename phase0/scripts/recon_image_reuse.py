"""Recon: Werden Bilder/Slides über Decks hinweg recycelt?

Misst byte-identische Bild-Wiederverwendung über eine Stichprobe von
KOCHfabrik-PDFs. Beantwortet die MVP-Frage: fertige Kompositionen
aneinanderketten (kein Bild-AI) vs. jedes Deck individuell.

Output: nur Aggregat nach stdout + phase0/recon-image-reuse.md.
Extrakt landet in phase0/cache/extract/ (gitignored).
"""
import hashlib
import os
import subprocess
import sys
from collections import defaultdict

CORPUS = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # phase0/
EXTRACT = os.path.join(HERE, "cache", "extract")
MIN_BYTES = 8 * 1024  # winzige Masken/Spacer rausfiltern

SAMPLE = [
    "12.09.2025_KF Bechtle.pdf",
    "Eure Hochzeit mit der KOCHfabrik V3.pdf",
    "13.09.2025._Foodidee_.pdf",
    "07.06._Speisenidee_KOCHfabrik.pdf",
    "28.06._KF_Eventkonzept_Mares_.pdf",
    "50. Geburtstag Dr. Hesse.pdf",
    "IKEA Sommerfest.pdf",
    "Foodkonzept.pdf",
    "26.09. Foodkonzept KIBEK.pdf",
    "Neumann Kaffee Gruppe.pdf",
    "Hochzeit Tichy.pdf",
    "Step One Jubiläumsfeier.pdf",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def page_of(fname):
    # pdfimages -p  → name-<page>-<num>.ext
    parts = fname.rsplit(".", 1)[0].split("-")
    for p in reversed(parts):
        if p.isdigit():
            return int(p)
    return -1


hash_decks = defaultdict(set)          # bildhash -> {decks}
deck_imgs = defaultdict(list)          # deck -> [hash]
page_set = defaultdict(set)            # (deck,page) -> {hash}
total = 0

for i, deck in enumerate(SAMPLE):
    src = os.path.join(CORPUS, deck)
    if not os.path.isfile(src):
        print(f"!! fehlt: {deck}", file=sys.stderr)
        continue
    outdir = os.path.join(EXTRACT, f"{i:02d}")
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(["pdfimages", "-png", "-p", src, os.path.join(outdir, "p")],
                   check=False, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    for fn in os.listdir(outdir):
        fp = os.path.join(outdir, fn)
        if os.path.getsize(fp) < MIN_BYTES:
            continue
        hh = sha(fp)
        total += 1
        hash_decks[hh].add(deck)
        deck_imgs[deck].append(hh)
        page_set[(deck, page_of(fn))].add(hh)

uniq = len(hash_decks)
multi = sum(1 for d in hash_decks.values() if len(d) >= 2)
img_instances_reused = sum(len(deck_imgs[d]) for d in deck_imgs) and sum(
    1 for d in SAMPLE for h in deck_imgs.get(d, []) if len(hash_decks[h]) >= 2)

# "recycelte Slides": gleiche Bildmenge einer Seite taucht in >=2 Decks auf
sig_decks = defaultdict(set)
for (deck, pg), hs in page_set.items():
    if hs:
        sig = "|".join(sorted(hs))
        sig_decks[sig].add(deck)
recycled_pages = sum(1 for d in sig_decks.values() if len(d) >= 2)
total_pages = len(page_set)

top = sorted(hash_decks.items(), key=lambda kv: -len(kv[1]))[:12]

lines = []
lines.append(f"# Recon: Bild-/Slide-Wiederverwendung ({len(SAMPLE)} Decks)\n")
lines.append(f"- Bild-Instanzen (≥{MIN_BYTES//1024} KB): **{total}**")
lines.append(f"- Eindeutige Bilder (sha256): **{uniq}**  "
             f"→ Dedup-Quote {100*(1-uniq/max(total,1)):.0f}%")
lines.append(f"- Bilder in **≥2 Decks**: **{multi}** "
             f"({100*multi/max(uniq,1):.0f}% der eindeutigen)")
lines.append(f"- Bild-Instanzen, die wiederverwendet sind: "
             f"**{100*img_instances_reused/max(total,1):.0f}%** aller Instanzen")
lines.append(f"- Seiten gesamt: {total_pages} · "
             f"**Seiten mit Bildset, das in ≥2 Decks identisch wiederkehrt: "
             f"{recycled_pages}** ({100*recycled_pages/max(total_pages,1):.0f}%)")
lines.append("\n## Top wiederverwendete Bilder (in wie vielen Decks)\n")
for h, decks in top:
    lines.append(f"- `{h[:10]}` in **{len(decks)}/{len(SAMPLE)}** Decks")

report = "\n".join(lines)
print(report)
with open(os.path.join(HERE, "recon-image-reuse.md"), "w") as f:
    f.write(report + "\n")
