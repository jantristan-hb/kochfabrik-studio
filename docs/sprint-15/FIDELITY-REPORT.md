# Treue-Report — Baseline Sprint 15 (FEATURE-TREUE-HARNESS, KOCHFABRIK-FEATURE-016)

> **Status:** V3 (Baseline eingefroren) + V4 (Report). **V5 (Schwellen-Abnahme
> durch Jan) = OFFEN** — der Schwellen-Vorschlag unten ist eine Entscheidungs-
> vorlage, kein beschlossenes Gate. Trace: R-FID-5 ❓
>
> **Metrik:** `engine/tooling/fidelity.py` `FIDELITY_VERSION = "1.0"`,
> fitz `1.27.2.3`. **Harness:** `engine/tooling/fidelity_run.py`.
> **Baseline-Daten:** [`fidelity_baseline.json`](./fidelity_baseline.json).

Der Report misst, wie treu die Reconstruct-Pipeline (`reconstruct.js` → soffice)
ein Deck gegen seine Original-`ref.pdf` reproduziert. Gemessen wurde das einzige
committete Deck mit `ref.pdf`: **`10-182-raumkarussell-gmbh-12-09-2026`**
(synthetisches A4-Hochkant-Deck, 595×839, 8 Seiten).

## 1. Score-Tabelle je Slide

| Slide | text | geometry | font | pixel | **total** |
|------:|-----:|---------:|-----:|------:|----------:|
| 1 | 1.000 | 0.519 | 0.000 | 0.991 | **0.628** |
| 2 | 1.000 | 0.463 | 0.000 | 0.992 | **0.614** |
| 3 | 1.000 | 0.488 | 0.000 | 0.990 | **0.620** |
| 4 | 1.000 | 0.530 | 0.000 | 0.997 | **0.632** |
| 5 | 1.000 | 0.509 | 0.000 | 0.997 | **0.627** |
| 6 | 1.000 | 0.344 | 0.000 | 0.940 | **0.577** |
| 7 | 1.000 | 0.352 | 0.000 | 0.949 | **0.580** |
| 8 | 1.000 | 0.485 | 0.000 | 0.990 | **0.620** |
| **Ø** | **1.000** | **0.461** | **0.000** | **0.981** | **0.612** |

Gewichtung (FEATURE-016 §4): `total = 0.35·text + 0.25·geometry + 0.25·font + 0.15·pixel`.

## 2. Teil-Score-Analyse — wo verliert der Render?

- **text = 1.000 (alle Slides):** Der Korpus-Text wird zeichengetreu
  rekonstruiert. Der Token-F1 ist überall maximal — die Pipeline verliert
  keinen Inhalt, nur dessen *Darstellung*.

- **font = 0.000 (alle Slides) — der dominante Defekt:** Das ist der bekannte
  **F-E-02** (FEATURE-TREUE-HARNESS §-Pitfall 3): **Open Sans fehlt im
  soffice-Render-Container**, LibreOffice substituiert eine Default-Familie.
  Da `fidelity.font` einen Span nur zählt, wenn Größe (±0.5pt) **und**
  Font-Familie matchen, fällt der Anteil auf 0. Zusätzlich zahlt der
  bekannte **SIZE_K = 0.78**-Defekt (systematischer Größen-Offset der Engine)
  auf die ±0.5pt-Toleranz ein. **Beides ist GEWOLLT** und wird hier bewusst
  *quantifiziert statt wegoptimiert* — die Baseline ist der Nullpunkt, gegen den
  EPIC-005 (Open-Sans-Embedding + SIZE_K-Fix) seinen Fortschritt misst.

- **geometry = 0.344–0.530:** Span-BBox-IoU bei mittlerem Niveau. Ursache ist
  der **Glyph-Breiten-Drift durch das Font-Substitut**: die Ersatzschrift hat
  andere Advance-Widths als Open Sans, dadurch wandern Zeilenumbrüche und
  Span-Endpositionen — die BBoxes überlappen das Original nur teilweise.
  geometry ist damit ein *Sekundäreffekt von F-E-02*, kein eigenständiger
  Layout-Fehler. Erwartung: steigt mit, sobald die korrekte Schrift im Render
  steht.

- **pixel = 0.940–0.997:** Graustufen-Ähnlichkeit durchweg hoch. Der visuelle
  Gesamteindruck stimmt — Flächen, Bilder und grobe Textblöcke sitzen richtig.
  Die niedrigsten Pixel-Werte (Slides 6/7) korrelieren mit der dortigen
  geometry-Schwäche (mehr Text → mehr Substitut-Drift → mehr Pixel-Differenz).

## 3. Größte 3 Abweichungen

| Rang | Slide | total | 1-Satz-Diagnose |
|-----:|------:|------:|-----------------|
| 1 | **6** | 0.577 | Niedrigster total: geometry 0.344 + pixel 0.940 — textreichste Folie, daher maximaler Glyph-Breiten-Drift durch das Open-Sans-Substitut. |
| 2 | **7** | 0.580 | Zweitniedrigster: geometry 0.352 + pixel 0.949 — gleiches Muster wie Slide 6 (dichter Text, Substitut-Drift). |
| 3 | **2** | 0.614 | Niedrigster der „ruhigen" Slides: geometry 0.463 zieht den Schnitt, font 0.0 wie überall — moderater Text, aber Substitut-Drift bleibt sichtbar. |

Gemeinsamer Nenner aller drei: **font 0.0 + geometry-Drift sind dieselbe Wurzel
(F-E-02)**. Kein Slide hat ein unabhängiges Layout- oder Text-Problem.

## 4. Schwellen-Vorschlag (Entscheidungsvorlage für Jan — V5, OFFEN)

Das Gate (US-084) soll **Regression** erkennen, nicht den heutigen Defekt-Zustand
bestrafen. Vorschlag:

1. **Regressions-Toleranz: 0.02 absolut je Slide gegen den Baseline-`total`.**
   D.h. ein künftiger Lauf failt, wenn `baseline_total[page] − neu_total[page] > 0.02`.
   Begründung: Die Repro-Toleranz der Pipeline liegt bei ±0.005 (US-082
   nachgewiesen); 0.02 lässt Render-Rauschen + kleine Layout-Anpassungen durch,
   schlägt aber bei echter Verschlechterung an. Verbesserungen (höherer total)
   passieren das Gate immer.

2. **KEIN absoluter Mindest-`total` jetzt.** Ein Floor (z.B. „total ≥ 0.80")
   wäre heute *rot auf der ganzen Linie* (Ø 0.612), weil F-E-02 noch nicht
   gefixt ist — er würde den Branch dauerhaft blockieren. Ein Mindest-`total`
   wird **erst NACH EPIC-005 sinnvoll**, wenn font auf ~1.0 springt; dann als
   separater V5-Beschluss nachziehen.

3. **Gate-Mechanik:** Vergleich pro Slide gegen `fidelity_baseline.json`,
   nur das Sample-Deck, im Container. Detail-Design in US-084.

> **Offen für Jan:** (a) Toleranz 0.02 ok oder enger/weiter? (b) Mindest-`total`
> erst nach EPIC-005 — bestätigt? (c) Gate hart (Merge-Block) oder zunächst
> Warnung?

## 5. Erwartung nach EPIC-005 — Baseline als Fortschrittsmesser

EPIC-005 (T1–T3: Open-Sans-Embedding im Render-Container + SIZE_K-Fix) adressiert
direkt die Wurzel von F-E-02. Erwartete Score-Bewegung gegen diese Baseline:

| Teil-Score | heute (Ø) | erwartet nach EPIC-005 | warum |
|-----------|----------:|-----------------------:|-------|
| font | 0.000 | **~1.0** | Open Sans verfügbar → Familie + Größe matchen wieder |
| geometry | 0.461 | **~0.85+** | korrekte Advance-Widths → Span-Positionen decken sich |
| pixel | 0.981 | ~0.99 | bereits hoch, leichter Zugewinn |
| text | 1.000 | 1.000 | unverändert (war nie das Problem) |
| **total** | **0.612** | **~0.85+** | font (+0.25·1.0) + geometry-Lift heben den Gesamt-Score |

Springt `total` nach EPIC-005 auf ~0.85+, ist der Fix maschinell belegt — die
Baseline macht den heute nur beschriebenen Defekt **messbar abgeschlossen**.

## 6. Voll-Korpus-Runbook

Die Baseline oben deckt das einzige committete Deck mit `ref.pdf` ab. Für einen
Voll-Korpus-Lauf (alle Decks unter `engine/data/cache/<slug>/` mit `assets/ref.pdf`):

```bash
# Pro Deck (einziges committetes mit ref.pdf):
docker run --rm \
  -v "$PWD/engine/data:/app/engine/data" \
  -v "$PWD/engine/tooling:/app/engine/tooling" \
  kf-studio-sim \
  python3 engine/tooling/fidelity_run.py --deck <slug> \
  > docs/sprint-15/fidelity_<slug>.json

# Mehrere Decks in einem Lauf (kommagetrennt):
docker run --rm \
  -v "$PWD/engine/data:/app/engine/data" \
  -v "$PWD/engine/tooling:/app/engine/tooling" \
  kf-studio-sim \
  python3 engine/tooling/fidelity_run.py --decks <slug1>,<slug2>,<slug3>
```

**Dauer-Schätzung (aus dem Sample gemessen):** ~0,5 s pro Slide für Render
(reconstruct.js + soffice) + Messung; das 8-Slide-Sample lief in ~4 s
`run_deck`-Wall (zzgl. einmalig ~2 s `pip install pymupdf` pro `--rm`-Container).
Hochgerechnet: ein Voll-Korpus von ~200 Decks à ~8 Slides ≈ 1600 Slides ≈
**13–20 Min reine Render-/Messzeit**, je nach soffice-Cold-Start-Verhalten und
Deck-Größe konservativ bis ~30 Min. Empfehlung für den Voll-Lauf: ein einziger
Container über `--decks` (spart die wiederholten `pip install` + soffice-Warmups).

**Voraussetzungen:** `kf-studio-sim`-Image gebaut (`docker build -t kf-studio-sim .`),
Decks mit `assets/ref.pdf` im Cache. Decks ohne `ref.pdf` werden mit einem
`errors`-Eintrag übersprungen, der Lauf bricht nicht ab.
