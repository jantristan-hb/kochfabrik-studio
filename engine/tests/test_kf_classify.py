"""Deterministische Tests für kf_classify (keine DB/PDF/API):
Identify · Footer-Strip · Classify · Extract · Derive.
Run: python3 test_kf_classify.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from kf_classify import (is_kochfabrik, strip_footer, classify,   # noqa
                         extract_event, derive_from_text)

f = 0


def chk(name, cond):
    global f
    print(("  ok  " if cond else "  FAIL") + " " + name)
    f += 0 if cond else 1


SIG = "Die KOCHfabrik GmbH - Peiner Hag 9a - 25497 Prisdorf\n"
ANGEBOT = SIG + """
Veranstaltungsinformationen
Veranstaltungsanlass:    Abendveranstaltung
Veranstaltungsdatum:     10. Juni 2025
Personenanzahl:          45 Personen
Cateringkonzept:         Menü
Empfang der Gäste mit Aperitif
Servieren des 3 Gang Menüs
Planungsfabrik Hamburg   Restaurant Goldschätzchen   Bankverbindung
www.koch-fabrik.com      anfrage@koch-fabrik.com
"""
FLYING = SIG + ("Veranstaltungsanlass: Einweihungsfeier\n"
                "Cateringkonzept: Flying Dinner\n"
                "Trinkgenuss zum Empfang 1 Stunde\n")
ALT = SIG + "Sommerfest 2019 — schöne Grüße, keine Labels hier\n"

# 1) IDENTIFY
chk("KOCHfabrik erkannt", is_kochfabrik(ANGEBOT))
chk("Fremd-PDF NICHT erkannt",
    not is_kochfabrik("Müller Catering GmbH\nLeckeres Buffet"))

# 2) FOOTER-STRIP — invarianter Block weg, Inhalt bleibt
s = strip_footer(ANGEBOT)
chk("Footer entfernt", "anfrage@koch-fabrik" not in s
    and "Bankverbindung" not in s)
chk("Inhalt bleibt", "Veranstaltungsanlass" in s and "3 Gang" in s)

# 3) CLASSIFY
chk("classify menue (geparste Gänge)", classify(ANGEBOT, 3) == "menue")
chk("classify angebot (Labels, 0 Gänge)",
    classify(ANGEBOT, 0) == "angebot")
chk("classify kontext (altes Template)", classify(ALT, 0) == "kontext")

# 4) EXTRACT — feste Labels robust
ev = extract_event(ANGEBOT)
chk("Anlass extrahiert", ev["anlass"] == "Abendveranstaltung")
chk("Konzept extrahiert", ev["konzept"] == "Menü")
chk("Personen extrahiert", ev["personen"].startswith("45"))
chk("n_gang erkannt (3 Gang)", ev["n_gang"] == 3)
chk("Empfang-Signal", ev["empfang"] is True)

# 5) DERIVE — Konzept/Anlass → geordnete Gang-Headlines
d = [h for h, _ in derive_from_text(ANGEBOT)]
chk("Menü+3Gang -> Empfang+Vorspeise/Hauptgang/Dessert",
    d == ["EMPFANG", "VORSPEISE", "HAUPTGANG", "DESSERT"])
d2 = [h for h, _ in derive_from_text(FLYING)]
chk("Flying Dinner + Empfang abgeleitet",
    "EMPFANG" in d2 and "FLYING DINNER" in d2)
d3 = [h for h, _ in derive_from_text(ALT)]
chk("alter Typ -> Anlass als semantischer Fallback",
    d3 == ["SOMMERFEST 2019 — SCHÖNE GRÜSSE, KEINE LABELS HIER"[:40]]
    or (len(d3) == 1 and d3[0].startswith("SOMMERFEST")))
chk("Fremd-PDF -> keine Ableitung",
    derive_from_text("Fremd Catering\nBuffet") == [])

print(f"\n{'ALLE TESTS GRÜN' if f == 0 else str(f)+' FEHLER'}")
raise SystemExit(1 if f else 0)
