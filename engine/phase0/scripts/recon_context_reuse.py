"""Recon v2: Bild-Reuse KONDITIONIERT AUF SLIDE-ROLLE.

Baut auf dem Extrakt von recon_image_reuse.py auf (phase0/cache/extract/).
Labelt jede Seite per Textlayer-Heuristik zu einer Rolle und misst je
Rolle, wie stark Bilder über Decks hinweg wiederkehren.

Antwortet auf: "wie oft tauchen gleiche Bilder im bestimmten Kontext
wiederkehrend auf" — also welche Slide-Rollen reines Text-Swap-Template
sind vs. welche bespoke Fotos tragen.

Nur Aggregat nach stdout + phase0/recon-context-reuse.md. Kein Seitentext
in den Chat-Kontext.
"""
import hashlib
import os
import re
import subprocess
import sys
from collections import defaultdict

CORPUS = "/home/jrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACT = os.path.join(HERE, "cache", "extract")
MIN_BYTES = 8 * 1024

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

# Reihenfolge = Priorität (erste passende Regel gewinnt)
RULES = [
    ("getraenke", r"\b(getränk|weine?\b|bar\b|cocktail|drinks|aperitif)"),
    ("menue", r"\b(menü|menue|speise|vorspeise|hauptgang|hauptgäng|"
              r"dessert|gang\b|gänge|flying|buffet|fingerfood|"
              r"amuse|snack|kulinarik|food)"),
    ("team", r"\b(unser team|küchencrew|das team|köche|kochteam)"),
    ("ueber_uns", r"\b(über uns|wer wir sind|kochfabrik\b.*(seit|gmbh)|"
                  r"unsere philosophie|leidenschaft)"),
    ("location", r"\b(location|räumlichkeit|venue|veranstaltungsort)"),
    ("referenzen", r"\b(referenz|das sagen|kundenstimmen|feedback|"
                   r"vertrauen uns)"),
    ("kontakt", r"\b(kontakt|ansprechpartner|wir freuen uns|"
                r"@|telefon|\bt:\s|mobil)"),
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def page_of(fname):
    # pdfimages -p  →  <root>-<seite>-<bildnr>.<ext>  : erste Gruppe = Seite
    m = re.search(r"-(\d+)-(\d+)\.[A-Za-z]+$", fname)
    return int(m.group(1)) if m else -1


def label(text, is_first):
    t = text.lower()
    for name, pat in RULES:
        if re.search(pat, t):
            return name
    if is_first or len(t.strip()) < 40:
        return "cover"
    return "sonst"


# Seitentext je Deck holen (nur intern, nie ausgegeben)
deck_pages_text = {}
for deck in SAMPLE:
    src = os.path.join(CORPUS, deck)
    if not os.path.isfile(src):
        print(f"!! fehlt: {deck}", file=sys.stderr)
        continue
    out = subprocess.run(["pdftotext", "-layout", src, "-"],
                          capture_output=True, text=True)
    deck_pages_text[deck] = out.stdout.split("\f")

# Bild-Hashes global (für Reuse-Test) + je (deck,page)
hash_decks = defaultdict(set)
page_hashes = defaultdict(set)
for i, deck in enumerate(SAMPLE):
    d = os.path.join(EXTRACT, f"{i:02d}")
    if not os.path.isdir(d):
        continue
    for fn in os.listdir(d):
        fp = os.path.join(d, fn)
        if os.path.getsize(fp) < MIN_BYTES:
            continue
        hh = sha(fp)
        pg = page_of(fn)
        hash_decks[hh].add(deck)
        page_hashes[(deck, pg)].add(hh)

# Aggregation je Rolle
role_pages = defaultdict(int)
role_decks = defaultdict(set)
role_imgs = defaultdict(int)
role_reused_imgs = defaultdict(int)
role_sig = defaultdict(lambda: defaultdict(set))  # role -> sig -> {decks}

for (deck, pg), hs in page_hashes.items():
    pages = deck_pages_text.get(deck, [])
    txt = pages[pg - 1] if 0 < pg <= len(pages) else ""
    role = label(txt, pg == 1)
    role_pages[role] += 1
    role_decks[role].add(deck)
    role_imgs[role] += len(hs)
    role_reused_imgs[role] += sum(1 for h in hs if len(hash_decks[h]) >= 2)
    if hs:
        role_sig[role]["|".join(sorted(hs))].add(deck)

order = ["cover", "ueber_uns", "team", "menue", "getraenke",
         "location", "referenzen", "kontakt", "sonst"]
lines = ["# Recon v2: Bild-Reuse je Slide-Rolle (12 Decks)\n",
         "| Rolle | Seiten | Decks | Bilder | % Bilder recycelt | "
         "Rolle mit ident. Bildset in ≥2 Decks |",
         "|---|--:|--:|--:|--:|--:|"]
for r in order:
    if role_pages[r] == 0:
        continue
    recycled_sig = sum(1 for ds in role_sig[r].values() if len(ds) >= 2)
    pct = 100 * role_reused_imgs[r] / max(role_imgs[r], 1)
    lines.append(f"| {r} | {role_pages[r]} | {len(role_decks[r])} | "
                 f"{role_imgs[r]} | {pct:.0f}% | {recycled_sig} |")

lines.append("\n**Lesart:** hoher Recycling-Prozentsatz + hohe Ident-Bildset-Zahl "
             "= reine Text-Swap-Template-Rolle (MVP: Slide aus Bibliothek "
             "ketten). Niedrig = bespoke Fotos, braucht kuratierten Pool.")
report = "\n".join(lines)
print(report)
with open(os.path.join(HERE, "recon-context-reuse.md"), "w") as f:
    f.write(report + "\n")
