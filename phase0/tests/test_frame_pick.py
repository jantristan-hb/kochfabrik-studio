"""Tests für compose_offer.pick_frame — kunden-stabile, variierende
Frame-Auswahl aus dem freigegebenen Set. Run: python3 test_frame_pick.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from compose_offer import pick_frame                            # noqa

CREW = ["crew::a", "crew::b", "crew::c", "crew::d"]   # 1 golden + 3 alt
PERS = ["pers::1", "pers::2", "pers::3"]
KUNDEN = ["Risk.Ident GmbH", "Nordwerk Robotics GmbH", "Hanse Audit AG",
          "Familie Brünjes", "Werft & Hafen Logistik", "Lübeck Marzipan",
          "Pixelwerk Studios", "Elbinsel Versicherung", "Deichkind Bau eG",
          "Watt & Wind Energie", "Kontor Kreativ GmbH", "ACME Test"]
f = 0


def chk(name, cond):
    global f
    print(("  ok  " if cond else "  FAIL") + " " + name)
    f += 0 if cond else 1


# 1) leere Optionen → None (kein Crash)
chk("leere options -> None", pick_frame("CREW", [], "X") is None)

# 2) eine Option → immer die, egal welcher Kunde
chk("single option stabil",
    all(pick_frame("CREW", ["only"], k) == "only" for k in KUNDEN))

# 3) deterministisch: gleicher (kunde,cat) -> identisch über Aufrufe
chk("deterministisch je (kunde,cat)",
    all(pick_frame("CREW", CREW, k) == pick_frame("CREW", CREW, k)
        for k in KUNDEN))

# 4) Auswahl immer AUS dem freigegebenen Set
chk("pick in set",
    all(pick_frame("CREW", CREW, k) in CREW for k in KUNDEN))

# 5) Varianz: über die Kunden NICHT immer dieselbe Crew-Slide
picks = {pick_frame("CREW", CREW, k) for k in KUNDEN}
chk(f"varianz ueber kunden ({len(picks)} distinkt von {len(CREW)})",
    len(picks) >= 2)

# 6) Kategorien unabhängig: Crew- und Personal-Wahl nicht zwangs-
#    korreliert (mind. ein Kunde wählt unterschiedliche Indizes)
indep = any(CREW.index(pick_frame("CREW", CREW, k)) !=
            PERS.index(pick_frame("PERS", PERS, k))
            for k in KUNDEN)
chk("kategorien unabhaengig", indep)

# 7) Kunde-Stabilität case/space-insensitiv
chk("kunde normalisiert (case/space)",
    pick_frame("CREW", CREW, " risk.ident gmbh ")
    == pick_frame("CREW", CREW, "Risk.Ident GmbH"))

print(f"\n{'ALLE TESTS GRÜN' if f == 0 else str(f)+' FEHLER'}")
sys.exit(1 if f else 0)
