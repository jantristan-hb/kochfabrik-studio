# CLAUDE.md — pptxgenerator_v2

## Session-Start (PFLICHT)
> 1. Diese Datei
> 2. `PROGRESS.md` — Status, Carry-Over
> 3. `docs/sprint-{aktuell}/{USER-STORIES,FEATURE-ARCH,RETRO}.md`
> 4. Learnings: `~/work/Projects/claude-pptx/pptxGenJS/PDF-zu-PPTX Rekonstruktion — Learnings.md`

## Was das ist
KOCHfabrik **PDF → faithful, element-für-element editierbares PPTX**.
Clean-Room. Kern-Prinzip: **reproduzieren, nicht verschönern (1:1)**.

## Stack / Tools
- Extraktion: `pdfminer.six` (Paint-Order), `pdftohtml` (Bild-Assets),
  `pdfimages`+PIL (Logo-smask-Transparenz)
- Emission: Node + `pptxgenjs`
- Render/Verify: LibreOffice (`soffice`), `pdftoppm`, `python-pptx`

## Einstieg / Befehle
```
cd phase0/spike-pptxgenjs
python3 convert.py <input.pdf> [out.pptx]      # einzeln
python3 convert.py --batch <dir> --out <dir>   # Batch
python3 readback_overrides.py <edit.pptx> <deck>   # Hand-Korrektur persistieren
python3 ../scripts/phase_b_gate.py --n 25      # Korpus-Mess-Gate
```
Kein Test-Framework — Verify = Story-Einzeiler (USER-STORIES.md).

## Architektur-Regeln (hart)
- Spike-Kernlogik (pdfminer-Paint-Order, z-Order-Regeln in `lib/`,
  Logo-Transparenz) NICHT verändern — nur parametrisieren/orchestrieren/
  absichern.
- z-Order: Grafik in Paint-Order → Text oben → Frame zuletzt (Bleed) →
  Backing-Rects skippen → Titel-Band zentriert. (`lib/frame.js`, `lib/text.js`)
- Faithful > schöner: keine Gutter-/Beautify-Heuristik (`lib/gutter.js`
  bewusst inaktiv).
- Hand-Korrekturen nur via `overrides.json` (deck-gekeyt) / `readback_overrides.py`.

## Git
- Repo: github.com/jantristan-hb/pptxgenerator_v2 (privat). Branch `main`.
- Feature-Branch pro Story, linear stacken bei geteilten Dateien.
- Kein Merge auf `main` ohne explizites User-Approval.

## Sprint-Tabelle
| Sprint | Thema | Status | Datum |
|--------|-------|--------|-------|
| 1 | Engine Phase A (parametrisieren/orchestrieren/absichern + Mess-Gate) | DONE | 2026-05-18 |

## Sprint-Abschluss
`/sprint-review pptxgenerator_v2 {N}` — Docs, RETRO, Integration.
Skills sind GitLab/Astro-zentriert → für dieses GitHub/Python-JS-Projekt
lean adaptieren (kein glab/BDD/7-File).
