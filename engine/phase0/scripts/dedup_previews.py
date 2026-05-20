"""dedup_previews.py — SHA256-Dedup der Slide-Vorschau-PNGs.

Erzeugt phase0/data/dedup_manifest.json:
  {
    "kept":  ["deck::page", ...],          # nur Repräsentanten
    "redirect": {                          # alle (deck, page) → Repräsentant
        "deck-A::5": "deck-B::5",          # Dublette → Master
        "deck-B::5": "deck-B::5",          # Master zeigt auf sich selbst
        ...
    },
    "stats": {"total": N, "kept": K, "duplicates": D}
  }

Lokal: alle 1023 PNGs bleiben unangetastet (Master-Set).
Server-Volume: vendor.sh --push-previews rsynct nur die `kept`-PNGs.
slidesuche.py Search nutzt `redirect` um ANN-Treffer auf den
Repräsentanten umzulenken + dedup'd dann nach (deck, page).

Idempotent. DB read-only (nur falls --validate gegen menu_composition
abgleicht — Default ist DB-frei, weil PNG-Dateien die Truth sind).

Usage:
  python3 dedup_previews.py             # Manifest schreiben
  python3 dedup_previews.py --stats     # nur Stats, kein Write
"""
import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _deckpipe import CACHE                                       # noqa

DATA = os.path.dirname(CACHE)
MANIFEST = os.path.join(DATA, "dedup_manifest.json")


def scan():
    """Walks cache/*/preview/p*.png, hashes them, returns
    {(deck, page): sha256}."""
    out = {}
    for deck in sorted(os.listdir(CACHE)):
        prev_dir = os.path.join(CACHE, deck, "preview")
        if not os.path.isdir(prev_dir):
            continue
        for fn in sorted(os.listdir(prev_dir)):
            m = re.match(r"^p(\d+)\.png$", fn)
            if not m:
                continue
            page = int(m.group(1))
            path = os.path.join(prev_dir, fn)
            try:
                with open(path, "rb") as f:
                    h = hashlib.sha256(f.read()).hexdigest()
                out[(deck, page)] = h
            except Exception as e:
                print(f"  ⚠ {path}: {e}", file=sys.stderr)
    return out


def build_manifest(hashes):
    """Eine PNG-Hash-Gruppe → ein Repräsentant (lexikographisch erstes
    deck::page für stabile/deterministische Wahl)."""
    by_hash = {}                            # h → first (deck, page)
    for key in sorted(hashes):              # sorted = lexikograpisch
        h = hashes[key]
        if h not in by_hash:
            by_hash[h] = key
    redirect = {}
    for key, h in hashes.items():
        repr_key = by_hash[h]
        redirect[f"{key[0]}::{key[1]}"] = f"{repr_key[0]}::{repr_key[1]}"
    kept = sorted({v for v in redirect.values()})
    return {
        "kept": kept,
        "redirect": redirect,
        "stats": {
            "total": len(hashes),
            "kept": len(kept),
            "duplicates": len(hashes) - len(kept),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true",
                    help="nur Stats ausgeben, kein Write")
    a = ap.parse_args()

    print(f"Scanne PNGs in {CACHE} …")
    hashes = scan()
    print(f"  {len(hashes)} PNGs gehasht")
    m = build_manifest(hashes)
    s = m["stats"]
    print(f"  unique: {s['kept']} | duplicates: {s['duplicates']} | "
          f"ratio: {s['duplicates'] / max(s['total'], 1):.1%}")

    # Top-5 Dublettengruppen für sanity-check
    from collections import Counter
    redirect_targets = Counter(m["redirect"].values())
    print("\nTop-5 Dublettengruppen (Repräsentant → #Dubletten):")
    for repr_key, n in redirect_targets.most_common(5):
        if n > 1:
            print(f"  {repr_key} ← {n}× (")
            dups = [k for k, v in m["redirect"].items()
                    if v == repr_key and k != repr_key]
            for d in dups[:3]:
                print(f"      {d}")
            if len(dups) > 3:
                print(f"      … +{len(dups) - 3} more")
            print("  )")

    if a.stats:
        return
    with open(MANIFEST, "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    print(f"\n→ {MANIFEST}")


if __name__ == "__main__":
    main()
