---
key: KOCHFABRIK-FEATURE-016
status: implemented
title: "Render-Treue-Harness: Metrik, Korpus-Lauf, Baseline, Regressions-Gate"
created: 2026-06-12
project: kochfabrik
---

# KOCHFABRIK-FEATURE-016: Render-Treue-Harness

> **Typ:** FEATURE (Brownfield-Delta, Tooling + Tests). Sprint 15 /
> EPIC-007 V1–V4. Jans Kern-Anforderung „super nah an den pdfs —
> alleine dieses testing ist nen epic" bekommt ihr Mess-Fundament:
> Treue wird eine ZAHL, Regressionen werden vom Gate gefangen.

## 1. Vision

Ein Befehl misst, wie nah eine rekonstruierte Slide am Original-PDF
ist (Score 0–1 aus Text-, Geometrie-, Font- und Pixel-Anteil). Eine
eingefrorene Baseline über das Sample macht jede Verschlechterung
sichtbar; das Gate blockiert sie im CI (FEATURE-009/C2).

## 3. Datenmodell

| Artefakt | Ort | Inhalt |
|---|---|---|
| Slide-Score | (Rückgabe) | `{text: decimal, geometry: decimal, font: decimal, pixel: decimal, total: decimal}` — total = gewichtetes Mittel |
| Lauf-Report | `docs/sprint-15/fidelity_baseline.json` | je Sample-Slide deck/page + Scores + Metrik-Version |
| Report-MD | `docs/sprint-15/FIDELITY-REPORT.md` | menschenlesbar: Tabelle, größte Abweichungen, Schwellen-Vorschlag |

## 4. Flows

```
fidelity.py (engine/tooling, reine Vergleichs-Metrik, fitz-basiert):
  compare(ref_pdf, ref_page, neu_pdf, neu_page) →
    text:    normalisierter Token-F1 (fitz get_text beider Seiten)
    geometry: Span-BBox-Matching (IoU-gewichtet, beste Zuordnung)
    font:    Anteil Spans mit gleicher (size±0.5pt, face-Familie)
    pixel:   Graustufen-Ähnlichkeit der fitz-Pixmaps (192px, 1−MAE)
    total:   0.35*text + 0.25*geometry + 0.25*font + 0.15*pixel
fidelity_run.py (Harness):
  je Sample-Slide: elements.json → 1-Slide-PPTX (reconstruct.js) →
  soffice→PDF (IM CONTAINER, wie render_notext) → compare gegen die
  Original-ref.pdf-Seite des Decks → JSON-Report; --decks/--limit
Gate (backend/tests/test_sprint15_fidelity.py):
  Sample-Lauf-Ergebnis vs. fidelity_baseline.json — total je Slide
  >= baseline_total − Toleranz (Default 0.02); node/docker-gated.
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN fidelity.compare eine Seite mit sich selbst vergleicht THE
   SYSTEM SHALL total ≥ 0.99 liefern; WHEN Texte/Fonts manipuliert
   sind THE SYSTEM SHALL messbar niedrigere Teil-Scores liefern
   (Monotonie-Beweis, kein absoluter Anspruch).
2. WHEN fidelity_run über das Sample läuft THE SYSTEM SHALL einen
   reproduzierbaren JSON-Report liefern (zweiter Lauf: identische
   Scores ±0.005 — Render-Determinismus-Toleranz).
3. WHEN die Baseline eingefroren ist THE SYSTEM SHALL eine künstlich
   eingebaute Regression (z.B. Font-Size-Manipulation vor dem Render)
   im Gate-Test nachweislich FANGEN (rot), und der unveränderte Stand
   SHALL grün sein.
4. THE SYSTEM SHALL einen menschenlesbaren Report mit den größten
   Abweichungen + einem Schwellen-Vorschlag liefern (R-FID-5 ❓ —
   Abnahme der Schwellen durch Jan = V5, bleibt offen markiert).

## 9. Abgrenzung (Nicht-Teil)

- Kein Voll-Korpus-Treue-Lauf im Sprint (Sample = committete Decks;
  Voll-Lauf = Runbook-Abschnitt im Report)
- Keine Treue-VERBESSERUNG (das ist EPIC-005 — hier wird nur gemessen)
- V5 (Schwellen-Abnahme durch Jan) = Entscheidung, keine Story

## 9a. Boundaries (3-Tier)

- ✅ **Always:** neue Dateien engine/tooling/fidelity.py +
  fidelity_run.py; Test test_sprint15_fidelity.py; **PyMuPDF (fitz)
  als Analyse-Dep in tools/.venv installieren — explizit freigegeben,
  NICHT in requirements.txt/Runtime** (Muster font_report Sprint 10);
  Render-Schritte im Container kf-studio-sim
- ⚠️ **Ask-first (headless → BLOCKED):** weitere neue Dependencies;
  Änderungen an reconstruct.js/Engine-Runtime
- 🚫 **Never:** Cache/pgbundle verändern; Metrik in die Runtime
  importieren (tooling-only); Gate-Toleranzen aufweichen, um grün zu
  werden; master pushen; kein timeout-Binary

## 10. Abgrenzung zum Ist

- Treue heute = Augenmaß + Sprint-10-Font-Report (statisch) →
  wiederholbare Zahl je Slide + Gate
- Ranking-Gold-Test sichert SUCHE, nicht RENDER-Treue — neues Gate
  deckt den Render-Pfad

## 11. Implementierungs-Anker (Ist)

`tools/font_report.py` (fitz-Nutzungsmuster: Spans mit size/font/bbox
— Sprint-10-Code als Referenz; fitz NICHT im aktuellen venv,
Installation Teil von US-081), `engine/tooling/render_notext.py`
(Container-Render-Muster: elements→reconstruct→soffice, 1:1 für
fidelity_run), Original-PDFs: `engine/data/cache/<deck>/assets/ref.pdf`
(beide committeten Decks haben eins), `docker run --rm -v
"$PWD/engine/data:/app/engine/data" -v "$PWD/engine/tooling:/app/
engine/tooling" kf-studio-sim …` (US-069-Muster), Suite-Baseline
213 passed/5 skipped.

## 12. Bekannte Pitfalls

1. **Render-Nichtdeterminismus:** soffice rendert nicht bit-identisch
   — Pixel-Anteil niedrig gewichten (0.15) + Reproduzierbarkeits-
   Toleranz ±0.005; NIE auf Bit-Gleichheit testen.
2. **A4 vs. 16:9:** ref.pdf von raumkarussell ist A4-hochkant
   (Angebots-Deck) — compare normalisiert Koordinaten auf Seitenmaße,
   nichts hartkodieren (Lehre _meta-Varianz Sprint 14).
3. **Bekannte Treue-Lücken messen, nicht verstecken:** Open Sans fehlt
   im Render (F-E-02) + SIZE_K=0.78 — die Baseline wird diese Defekte
   ZEIGEN (font-Score < 1). Das ist gewollt: EPIC-005 misst seinen
   Fortschritt später an genau dieser Zahl.
4. **fitz-Version pinnen** im Install-Befehl (Report trägt
   Metrik-Version) — Metrik-Drift durch Lib-Update erkennen.
5. **Docker-/node-Gates in Tests:** Gate-Test skipt sauber ohne
   docker/node (lokal), läuft aber im CI-fidelity-Job (FEATURE-009)
   verpflichtend.

## Vision-Alignment

**Adressierte These:** R-FID-1, R-FID-2, R-FID-3, R-FID-4, R-FID-5 (❓
Schwellen), R-QA-4 · Jan: „super nah an den pdfs … alleine dieses
testing ist nen epic"
**Kern-Loop-Schritt:** Treue wird messbar → EPIC-005 bekommt sein Lineal
**Nächste Iteration:** EPIC-005 T1–T3 (Open Sans, SIZE_K-Fix) gegen die Baseline

## Referenzen
- implements → REQUIREMENTS R-FID-1, R-FID-2, R-FID-3, R-FID-4, R-QA-4
- depends_on → [[KOCHFABRIK-FEATURE-013]] (Container-Render-Muster)
- relates_to → [[KOCHFABRIK-FEATURE-009]] (C2-Verdrahtung) · [[EPIC-007]] V1–V4

## Referenziert von
— USER-STORIES Sprint 15 (US-081, US-082, US-083, US-084)
