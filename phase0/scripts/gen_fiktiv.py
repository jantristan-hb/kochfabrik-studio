"""US-020 — Fiktiv-Event-Generator (Anthropic Batch API).

N realistische fiktive KOCHfabrik-Events → je ein `Angebot`-JSON
(Schema = angebot_model). Bulk via Batch API (CLAUDE.md-Pflicht:
messages.batches, 50% günstiger, parallel). Key aus ~/work/.env.

Run: python3 gen_fiktiv.py --n 20 --out ../data/fiktiv
"""
import argparse
import glob
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from angebot_model import load                                   # noqa

MODEL = "claude-sonnet-4-6"
ANLAESSE = ["Sommerfest", "Weihnachtsfeier", "Firmenjubiläum",
            "Produktlaunch", "Hochzeit", "Gala-Dinner", "Tagung",
            "Einweihungsfeier", "Mitarbeiterevent", "Kundenevent",
            "Richtfest", "Vereinsfeier", "Messeauftritt", "Empfang"]
KONZEPTE = ["Street Food", "Flying Dinner", "BBQ", "Live Cooking",
            "Buffet", "3-Gang-Menü", "Fingerfood", "Brunch"]
FIRMEN = ["Nordlicht Robotics GmbH", "Hanse Audit AG", "Elbwerk GmbH",
          "Watt & Wind Energie", "Pixelhaus Studios", "Kontor Kreativ",
          "Speicherstadt Bau AG", "Lübeck Marzipan GmbH", "Deich & Co",
          "Förde Digital AG", "Brammer Logistik KG", "Alster Pharma",
          "Travemünde Reederei", "Sylt Resort KG", "Kiel Marine GmbH"]
SCHEMA = '''{"kunde":str,"adresse":str,"angebots_nr":str,"datum":str,
"kundennr":str,"lieferdatum":str,"ansprechpartner":str,
"veranstaltung":{"anlass":str,"datum":str,"beginn":str,
"personen":int,"ort":str,"konzept":str},
"bloecke":[{"typ":"speisen|getraenke|personal|logistik","titel":str,
"positionen":[{"bezeichnung":str,"menge":num,"einzelpreis":num,
"gesamt":num,"is_header":bool}],"zwischensumme":num}]}'''


def _key():
    k = os.environ.get("ANTHROPIC_API_KEY")          # Container/Coolify
    if k:
        return k
    env = os.path.expanduser("~/work/.env")          # lokale Dev
    if os.path.isfile(env):
        for ln in open(env):
            if ln.startswith("ANTHROPIC_API_KEY="):
                return ln.split("=", 1)[1].strip().strip('"')
    return None


def _prompt(i):
    a = ANLAESSE[i % len(ANLAESSE)]
    k = KONZEPTE[(i * 3) % len(KONZEPTE)]
    fi = FIRMEN[i % len(FIRMEN)]
    return (f"Erzeuge EIN fiktives, realistisches KOCHfabrik-Catering-"
            f"Angebot als striktes, KOMPAKTES JSON in EINER Zeile (nur "
            f"JSON, keine Markdown-Fences, keine Kommentare, KEINE "
            f"trailing commas). Anlass≈'{a}', Cateringkonzept≈'{k}', "
            f"Kunde='{fi}' (oder ähnlich), realistische Personenzahl. "
            f"MAX 2 Positionsblöcke, je MAX 5 Positionen (davon 1 "
            f"Sub-Header is_header=true preislos). Preise plausibel "
            f"EUR, gesamt=menge*einzelpreis, Zwischensumme je Block. "
            f"Footer NICHT setzen. Schema:\n{SCHEMA}")


def _extract(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    return m.group(0) if m else txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", default="../data/fiktiv")
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    from anthropic import Anthropic
    c = Anthropic(api_key=_key())

    reqs = [{"custom_id": f"ev{i:03d}",
             "params": {"model": MODEL, "max_tokens": 4000,
                        "messages": [{"role": "user",
                                      "content": _prompt(i)}]}}
            for i in range(a.n)]
    batch = c.messages.batches.create(requests=reqs)
    print(f"Batch {batch.id} ({a.n} Requests) — warte…", flush=True)
    t0 = time.time()
    while time.time() - t0 < a.timeout:
        b = c.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended":
            break
        time.sleep(15)
    else:
        print("FEHLER: Batch-Timeout")
        sys.exit(1)

    ok = 0
    for r in c.messages.batches.results(batch.id):
        if r.result.type != "succeeded":
            continue
        txt = "".join(blk.text for blk in r.result.message.content
                      if blk.type == "text")
        p = os.path.join(a.out, r.custom_id + ".json")
        try:
            data = json.loads(_extract(txt))
            open(p, "w").write(json.dumps(data, ensure_ascii=False,
                                          indent=2))
            load(p)                                  # Schema-Validierung
            ok += 1
        except Exception as e:
            if os.path.exists(p):
                os.remove(p)
            print(f"  {r.custom_id} invalide: {str(e)[:80]}")
    print(f"OK: {ok}/{a.n} valide Angebot-JSONs → {a.out}")
    sys.exit(0 if ok >= max(1, int(a.n * 0.6)) else 1)


if __name__ == "__main__":
    main()
