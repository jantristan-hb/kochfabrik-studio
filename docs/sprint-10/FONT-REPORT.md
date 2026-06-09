# FONT-REPORT — Schriftarten-Inventar des Referenz-Korpus

**Quelle:** `docs/sprint-10/font-report.json` (US-038, Extraktor `tools/font_report.py`)
**Korpus:** `../pptxgenerator_v2/phase0/data/cache/{slug}/assets/*.pdf` (READ-ONLY, R-NF-3)
**Abdeckung:** **200/200** PDFs ausgewertet, `errors = 0` (kein PDF stumm übersprungen).
**Methodik:** pt-Größen stammen exakt aus der Text-Rendering-Matrix (PyMuPDF `span["size"]`) — **kein** Glyph-Bbox-Maß, **kein** `SIZE_K`-Fudge. Genau diese Korrektur soll EPIC-005/T1 in die Engine übernehmen.

Insgesamt erfasst: **1.165.825 Zeichen** über 200 Decks.

---

## 1. Font-Verteilung (Familie → Zeichen-Count)

| Familie | Zeichen | Anteil | präsent in |
|---|---:|---:|---:|
| **OpenSans** | 848.798 | **72,8 %** | 199/200 PDFs |
| Helvetica | 312.691 | 26,8 % | 33/200 PDFs |
| Calibri | 3.739 | 0,3 % | 43/200 PDFs |
| Wingdings | 322 | 0,03 % | 161/200 PDFs |
| ArialMT | 196 | 0,02 % | 12/200 PDFs |
| Candara | 64 | 0,01 % | 32/200 PDFs |
| CourierNewPSMT | 15 | 0,00 % | 1/200 PDFs |

**Lesart:** Open Sans ist kanonisch und dominiert die Masse — aber Helvetica trägt fast ein Drittel aller Zeichen, konzentriert auf wenige (32) Decks, in denen es Open Sans verdrängt (siehe §4). Calibri/Candara/Arial sind Fußnoten-Rauschen (meist Tabellen-Reste, Footer, eingebettete Fremd-Logos), tauchen aber breit gestreut auf. Wingdings ist mit 161/200 PDFs der zweithäufigste *präsente* Font, obwohl winzig im Volumen — es liefert Aufzählungs- und Pfeil-Glyphen (§5).

### Distinct Faces (voller Name, mit Stil)

| Face | Zeichen |
|---|---:|
| OpenSans-Regular | 515.313 |
| Helvetica | 312.446 |
| OpenSans-Bold | 262.452 |
| OpenSans-ExtraBold | 36.940 |
| OpenSans-Italic | 32.172 |
| Calibri | 3.501 |
| OpenSans-BoldItalic | 1.921 |
| Wingdings-Regular | 322 |
| Helvetica-Bold | 245 |
| Calibri-Italic | 214 |
| ArialMT | 196 |
| Candara | 64 |
| Calibri-Bold | 24 |
| CourierNewPSMT | 15 |

Open Sans wird in **vier** Schnitten benutzt: Regular, Bold, ExtraBold, Italic (+ BoldItalic). Stil-Anteil über alles: ~301.582 Zeichen **bold**, ~34.307 **italic**, Rest regulär.

---

## 2. pt-Größen-Histogramm

Gruppiert nach nominaler Größe (Subpixel-Varianten zusammengefasst). Die **dominanten Größen sind fett**.

| pt (nominal) | Zeichen | Anteil | Rolle (typisch) |
|---:|---:|---:|---|
| **14** (14,00 / 14,04 / 14,06 …) | **622.513** | **53,4 %** | **Fließtext / Tabellen-Body** |
| **8** (8,00 / 8,40 / 8,42) | **345.359** | **29,6 %** | **Kleingedrucktes / Helvetica-Body** |
| 9 (9,00 / 9,96 / 9,98) | 60.389 | 5,2 % | Sekundär-Text, Captions |
| 10 (10,00 / 10,56) | 34.600 | 3,0 % | Zwischengrößen |
| 36 (36,00 / 36,02 / 36,05) | 29.380 | 2,5 % | Headlines |
| 11 (11,00 / 11,04 / 11,06) | 19.925 | 1,7 % | Sub-Body |
| 12,96 / 12,98 | 20.485 | 1,8 % | skaliertes 13er |
| 13 (13,00 / 13,92 / 13,94) | 7.552 | 0,6 % | — |
| 54 (54,00 / 54,02 / 54,08) | 5.925 | 0,5 % | Cover-Titel |
| 5,00 | 3.535 | 0,3 % | Helvetica-Mikro-Text |
| 12 (12,00 / 12,02) | 8.890 | 0,8 % | — |
| 25,00 | 1.247 | 0,1 % | — |
| restliche (15–50 pt) | < 1 % je | | Headlines/Akzente |

**Kern-Befund:** Zwei Größen tragen **83 %** aller Zeichen — **14 pt** (Body) und **8 pt** (Kleingedrucktes/Helvetica). Alles darüber ist Headline-/Akzent-Rauschen.

### Subpixel-Ausreißer (exotische, nicht-ganzzahlige Größen)

Diese Werte existieren NUR, weil der Extraktor die exakte Rendering-Größe liefert — der alte bbox/`SIZE_K`-Ansatz hätte sie auf glatte Integer verschmiert.

| pt | Zeichen | Δ zum nächsten Integer | Vermutete Ursache |
|---:|---:|---:|---|
| 14,04 | 549.328 | +0,04 → 14 | **dominanter Body**, minimale Skalierung des 14er-Templates |
| 14,06 | 70.085 | +0,06 → 14 | s.o., zweite Template-Variante |
| 14,27 | 1.066 | +0,27 → 14 | gestauchtes/skaliertes Layout |
| 12,77 | 688 | −0,23 → 13 | skaliertes 13er |
| 14,25 | 546 | +0,25 → 14 | skaliertes 14er |
| 12,75 | 380 | −0,25 → 13 | skaliertes 13er |
| 11,27 / 11,25 | 506 | ±0,27/0,25 → 11 | skaliertes 11er |
| 8,40 / 8,42 | 28 | +0,40/0,42 → 8 | gestreckter Mikro-Text |
| 10,56 | 12 | −0,44 → 11 | skaliertes 11er |

Die `14,04`-Häufung (47 % aller Zeichen!) zeigt: Die Quell-Decks nutzen kein nominal-glattes 14 pt, sondern eine leicht skalierte Variante. **Das ist exakt der Effekt, den die Engine mit `SIZE_K = 0.78` zu kompensieren versuchte** — und der Grund, warum eine pauschale Konstante falsch ist: die Abweichung ist pro Größe verschieden (0,04 bei 14er, 0,40 bei 8er).

---

## 3. Farben (aussagekräftig)

| Hex | Zeichen | Bedeutung |
|---|---:|---|
| `#ffffff` | 581.469 | weiß — Text auf dunklen/farbigen Flächen |
| `#000000` | 426.125 | schwarz — Standard-Body |
| `#aa8339` | 102.300 | **Gold/Bronze — Marken-Akzent (Kochfabrik)** |
| `#666666` | 37.483 | grau — Sekundär-Text |
| `#efe5ae` | 10.722 | helles Gold — Hintergrund-Text |
| `#977825` | 3.535 | dunkleres Gold — Akzent-Variante |
| `#f2f3f7` | 2.384 | fast-weiß — Panel-Text |
| `#9c9c9c` | 1.675 | hellgrau |

**Lesart:** Drei tragende Farben (weiß, schwarz, Gold `#aa8339`) plus ein grau-abgestufter Long-Tail. Das Gold ist der wiederkehrende Marken-Akzent und sollte als Token erhalten bleiben.

---

## 4. Worst-Cases — Decks gegen die Open-Sans-Norm

### 4.1 Helvetica-dominierte Decks (32 PDFs)

In **32 von 200** Decks ist **Helvetica** die dominante Familie (mehr Zeichen als Open Sans). Es ist immer dasselbe Muster: ein Helvetica-Body von ~9.644 Zeichen bei 8 pt (oft Tabellen/Angebots-Positionen) plus ein kleinerer Open-Sans-Anteil und Calibri-Reste. Beispiele:

| Slug | Helvetica | OpenSans | Calibri |
|---|---:|---:|---:|
| `angebot-11-175-interamerican-coffee-gmbh-coffee-plaza-11-05-2026` | 9.644 | 7.853 | 170 |
| `angebot-200-personen-9-916-h-lssen-lyon-gmbh-13-09-2025` | 9.751 | 7.580 | 135 |
| `angebot-9-956-stage-entertainment-gmbh-11-09-2025` | 9.752 | 7.283 | 179 |
| `angebot-10-671-crystal-cabin-award-association-…-14-04-2026` | 9.751 | 6.384 | 124 |
| `angebot-11-046-bernhard-rothfos-gmbh-coffee-plaza-14-04-2026` | 9.644 | 6.346 | 124 |
| `angebot-10-545-hamburger-commercial-bank-ag-24-02-2026` | 9.751 | 5.000 | 113 |
| … (27 weitere, überwiegend `angebot-*` + `cineart-marketing-*`, `orlen-*`, `kinopolis-*`) | ~9.644 | 1.900–5.500 | 54–179 |

Die vollständige Liste der 32 Slugs steht im JSON; das Muster ist homogen genug, dass eine einzige Normalisierungsregel (Helvetica → Open Sans, 8 pt beibehalten) sie alle abdeckt.

### 4.2 PDF ohne extrahierbaren Text (1 PDF)

- `4-5-26-kfx-gaga` — **0 Text-Spans**. Vermutlich ein rein gerastertes/Bild-PDF (oder Text als Outlines). Lesbar (kein `errors`-Eintrag), aber für die Font-Analyse leer. **Muss in T1 als Sonderfall behandelt werden** (keine Font-Migration möglich; ggf. Re-Export oder OCR-Pfad).

### 4.3 Exotische Subpixel-Größen

Siehe §2 — die `14,04`/`14,06`-Häufung ist der Normalfall, nicht der Ausreißer; echte Ausreißer (`8,40`, `10,56`, `14,27`) sind volumenmäßig irrelevant (< 30 Zeichen je), bestätigen aber, dass pauschale Größen-Konstanten unzulässig sind.

---

## 5. Wingdings-Glyphen-Inventar

Wingdings ist ein Symbol-Font (Codepoints liegen in der Private-Use-Area `0xF0xx`). Erfasst über 161 PDFs:

| Codepoint | Zeichen | Bedeutung (Wingdings/Unicode) | Funktion im Deck |
|---|---:|---|---|
| `f0e0` | 188 | Wingdings-Glyph für rechten Pfeil (➜) | Aufzählungs-/Fluss-Pfeil |
| `2192` | 133 | Unicode RIGHTWARDS ARROW `→` | derselbe Pfeil, aber als echtes Unicode-Zeichen gesetzt |
| `f04a` | 1 | Wingdings „J" = Smiley ☺ | Einzel-Emoji |

**Befund:** Derselbe semantische Pfeil wird auf zwei Wegen gesetzt — als Wingdings-PUA-Glyph (`f0e0`) UND als echtes Unicode `→` (`2192`). Beim Font-Embedding/Bullet-Mapping muss beides auf dieselbe Ziel-Repräsentation gemappt werden, sonst gehen die `f0e0`-Pfeile verloren (Open Sans hat das PUA-Glyph nicht).

---

## 6. Konsequenzen für EPIC-005 (T1–T4)

### T1 — pt-Größen-Korrektur in der Engine (Kern)
- **Ersetze `SIZE_K = 0.78`** durch die exakte Span-Größe aus der Rendering-Matrix (PyMuPDF `span["size"]`), wie in `tools/font_report.py` vorgemacht. Die pauschale Konstante ist nachweislich falsch: die Bbox/Nominal-Abweichung ist größenabhängig (Δ 0,04 bei 14 pt vs. Δ 0,40 bei 8 pt).
- **Sonderfall `4-5-26-kfx-gaga`** (0 Text-Spans): Pipeline darf nicht crashen, wenn ein PDF keine Glyph-Größen liefert — leeren Span-Set sauber durchreichen.

### T2 — Normalisierungs-Map (Ausreißer → Open Sans)
Open Sans ist kanonisch. Alle Fremd-Familien auf Open-Sans-Faces abbilden:

| Quell-Familie | Ziel | Begründung |
|---|---|---|
| Helvetica / Helvetica-Bold | OpenSans-Regular / OpenSans-Bold | 32 Decks, homogenes 8-pt-Body-Muster |
| ArialMT | OpenSans-Regular | metrisch nah, reines Fremd-Rauschen |
| Calibri / Calibri-Bold / Calibri-Italic | OpenSans-{Regular,Bold,Italic} | Tabellen-/Footer-Reste |
| Candara | OpenSans-Regular | vereinzelt |
| CourierNewPSMT | *behalten* (mono) ODER OpenSans | nur 15 Zeichen, 1 PDF — entscheiden, ob Monospace semantisch nötig ist |
| Wingdings | Symbol-Mapping, **nicht** Open Sans | siehe T4 |

Subpixel-Größen (`14,04`, `14,06`, …) **nicht** auf glatte Integer runden — der Wert IST die Zielgröße.

### T3 — benötigte Open-Sans-Faces (Embedding)
Es müssen **mindestens diese fünf Faces** eingebettet werden, sonst fehlt Glyph-Abdeckung:
- **OpenSans-Regular** (Body, 515k Zeichen)
- **OpenSans-Bold** (262k)
- **OpenSans-ExtraBold** (37k — Headlines; **eigener Schnitt, nicht synthetisch fett**)
- **OpenSans-Italic** (32k)
- **OpenSans-BoldItalic** (2k)

Bold/Italic-Erkennung muss font-namen-führend bleiben (so im Extraktor): ExtraBold ist ein eigener Face, keine Bold-Synthese.

### T4 — Bullet-/Symbol-Mapping-Empfehlung
- **Wingdings `f0e0` (PUA-Pfeil) → Unicode `→` (U+2192)** vereinheitlichen. Beide existieren im Korpus für denselben Pfeil; Open Sans deckt `→` ab, die PUA-Glyphe nicht. Ohne Mapping gehen 188 Pfeile verloren.
- **Wingdings `f04a` (Smiley)** → bewusst entscheiden: Unicode `☺` (U+263A) oder weglassen (nur 1 Vorkommen).
- Bullet-Listen, die Wingdings-Glyphen als Aufzählungszeichen nutzen, auf native PPTX-Bullets oder ein definiertes Open-Sans-/Unicode-Symbol mappen.

---

*Generiert aus `font-report.json` (200/200 PDFs, Stand Sprint 10). Rohdaten + vollständige Slug-Listen im JSON.*
