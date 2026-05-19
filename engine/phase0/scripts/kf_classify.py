"""KOCHfabrik-PDF: robust identifizieren, klassifizieren, Event-Kontext
extrahieren und — wenn kein Menü gelistet ist — Gang-Headlines aus dem
Kontext ableiten. Robustheit = Dokument sicher klassifizieren statt
Inhalt fragil parsen. Die abgeleiteten Headlines laufen anschließend
durch den bestehenden Kategorie-Lock (Headline → module_label → ANN);
der 1010-Korpus liefert die echten passenden KOCHfabrik-Speisen.

Invariante: ALLE KOCHfabrik-PDFs tragen Letterhead/Domain-Signatur
(empirisch 33/33 über Muster + Stichprobe der 199).
"""
import re
import subprocess

# 1) IDENTIFY ---------------------------------------------------------
KF_SIG = re.compile(
    r"(?i)die\s+kochfabrik\s+gmbh|koch-fabrik\.com|peiner\s+hag\s*9\s*a")

# invarianter Footer-/Bank-/Standort-Block → deterministisch wegschneiden
_FOOTER = re.compile(
    r"(?i)planungsfabrik hamburg|restaurant goldschätzchen|bankverbin"
    r"|\bBIC\b|\bIBAN\b|VR Bank|www\.koch-fabrik\.com|anfrage@koch-fabrik"
    r"|peiner hag 9\s*a|die kochfabrik gmbh - peiner|speisenmacherei"
    r"|zahlenwerk|schleswig - holstein|am kaiserkai 69|peiner hof 7"
    r"|^\s*seite\s*\d+\s*/\s*\d+\s*$|gläubiger-id|steuernr|ust-id")


def pdf_text(path):
    """pdftotext -layout (identisch zu parse_offer_dishes)."""
    return subprocess.run(["pdftotext", "-layout", path, "-"],
                          capture_output=True, text=True).stdout or ""


def is_kochfabrik(text):
    return bool(KF_SIG.search(text or ""))


def strip_footer(text):
    return "\n".join(l for l in (text or "").splitlines()
                     if not _FOOTER.search(l))


# 2) CLASSIFY ---------------------------------------------------------
_VINFO = re.compile(r"(?i)Veranstaltungsinformationen|Cateringkonzept:")
_COURSE = re.compile(r"^[A-ZÄÖÜ][A-ZÄÖÜ0-9 &/'\-\.]{3,40}$")


def classify(text, n_parsed_courses):
    """'angebot' = kaufm. Angebot (strukturierte Labels, ggf. ohne
    Gerichte) · 'menue' = enumeriertes Speisen-/Menü-PDF · 'kontext' =
    altes Template ohne beides → semantischer Fallback."""
    if n_parsed_courses > 0:
        return "menue"
    if _VINFO.search(text or ""):
        return "angebot"
    return "kontext"


# 3) EXTRACT (feste Labels — robust über Template-Generationen) --------
def _label(text, name):
    m = re.search(rf"(?im)^\s*{name}\s*:?\s*(.+?)\s*$", text or "")
    return m.group(1).strip() if m else ""


def extract_event(text):
    t = strip_footer(text)
    gang = re.search(r"(?i)(\d+)\s*[- ]?gang", t)
    return {
        "anlass": _label(t, "Veranstaltungsanlass"),
        "konzept": _label(t, "Cateringkonzept"),
        "datum": _label(t, "Veranstaltungsdatum"),
        "personen": _label(t, "Personenanzahl"),
        "ort": _label(t, "Veranstaltungsort"),
        "projekt": _label(t, "Projekt"),
        "empfang": bool(re.search(
            r"(?i)\bempfang\b|trinkgenuss zum empfang|sektempfang", t)),
        "dessert": bool(re.search(
            r"(?i)\bdessert\b|süßspeise|sweet dreams", t)),
        "n_gang": int(gang.group(1)) if gang else 0,
    }


# 4) DERIVE (Konzept/Anlass → Gang-Headlines, geordnet) ---------------
# Wortlaut unkritisch — Kategorie-Lock mappt per Embedding aufs nächste
# module_label; muss nur semantisch nah an KOCHfabrik-Modulen sein.
_MAP = [
    (r"flying dinner", ["FLYING DINNER"]),
    (r"live ?cooking", ["LIVE COOKING"]),
    (r"bbq|barbecue|grill", ["BIG BBQ"]),
    (r"street ?food|food ?truck", ["STREETFOOD"]),
    (r"finger ?food", ["FINGER FOOD"]),
    (r"brunch", ["BRUNCH"]),
    (r"frühstück|fruehstueck", ["FRÜHSTÜCK"]),
    (r"lunch|mittag", ["LUNCH"]),
    (r"buffet", ["BUFFET"]),
    (r"gala|dinner", ["FLYING DINNER"]),
]
_MENU_GANG = {2: ["VORSPEISE", "HAUPTGANG"],
              3: ["VORSPEISE", "HAUPTGANG", "DESSERT"],
              4: ["VORSPEISE", "ZWISCHENGANG", "HAUPTGANG", "DESSERT"]}


def derive_courses(path):
    """[(headline, [])] aus dem Event-Kontext. Leere dish-Liste →
    Assembler nimmt den Korpus-Slide verbatim (echte KF-Gerichte)."""
    return derive_from_text(pdf_text(path))


def derive_from_text(text):
    if not is_kochfabrik(text):
        return []
    ev = extract_event(text)
    blob = " ".join((ev["konzept"], ev["anlass"], ev["projekt"])).lower()
    heads = []
    if ev["empfang"]:
        heads.append("EMPFANG")
    if re.search(r"men[üue]", blob):
        heads += _MENU_GANG.get(ev["n_gang"] or 3, _MENU_GANG[3])
    for pat, hs in _MAP:
        if re.search(pat, blob):
            heads += hs
    if ev["dessert"] and not any("DESSERT" in h or h == "SWEET DREAMS"
                                 for h in heads):
        heads.append("SWEET DREAMS")
    if not heads:                       # alter Typ ohne Labels:
        body = [l.strip() for l in strip_footer(text).splitlines()
                if l.strip() and not KF_SIG.search(l)]
        fb = ev["anlass"] or ev["projekt"] or " ".join(body[:6])
        heads = [fb.upper()[:60]] if fb.strip() else []
    seen, out = set(), []
    for h in heads:                     # dedupe, Reihenfolge halten
        if h and h not in seen:
            seen.add(h)
            out.append((h, []))
    return out[:5]
