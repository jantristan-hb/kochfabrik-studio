---
key: KOCHFABRIK-ADR-001
status: accepted
title: "PPTX-Font-Embedding vs. Server-Treue (Open Sans)"
created: 2026-06-09
project: kochfabrik
---

# ADR-001: PPTX-Font-Embedding vs. Server-Treue (Open Sans)

> **Typ:** ADR (Architecture Decision Record, MADR-artig). Hält **eine** Entscheidung fest —
> klein, datiert, unveränderlich (bei Revision: neues ADR mit `supersedes`).
> Status: `proposed → accepted → superseded/deprecated`. Diese ADR ist **proposed** —
> die Annahme (R-FONT-6) ist Jans Entscheidung.

**Sprint:** 10

**Abnahme:** accepted 2026-06-09 — Entscheidung von Jan an Claude delegiert (Chat: „ich vertrau dir. mach weiter, solang es sicher und SOTA is“).

## Kontext

Der Generator rekonstruiert KOCHfabrik-Referenz-PDFs zu element-für-element editierbaren PPTX: `extract.py` zieht Text/Fonts pro Span aus dem PDF (pdfminer), `reconstruct.js`/pptxgenjs emittiert die Textfelder mit `fontFace: "Open Sans …"` (`spike-pptxgenjs/lib/text.js:6-12`), und server-seitig rendert LibreOffice (`soffice`) das PPTX zu PDF/PNG für Vorschau und Versand. Die offene Frage **R-FONT-6**: Muss die ausgelieferte PPTX-Datei auch auf einem Kunden-Rechner **ohne installiertes Open Sans** exakt aussehen — oder reicht es, wenn der server-seitige PDF/PNG-Export pixel-treu ist und die editierbare PPTX beim Öffnen auf einer Fremdmaschine ggf. substituiert?

Die Frage ist real, weil zwei Befunde aus der Engine-Analyse (US-037) zusammenlaufen: Das Render-Image installiert nur `fonts-dejavu-core fonts-liberation`, kein Open Sans (FINDINGS-ENGINE F-E-02, `Dockerfile:8`) — server-seitig wird also bereits heute substituiert; und der Font-Report (US-038, 200 Decks) belegt, wie dominant Open Sans im Korpus ist.

**Evidenz aus `font-report.json` (US-038, 200 Decks, 0 Fehler):**

| Schrift | Spans | Anteil |
|---------|-------|--------|
| Open Sans | 848.798 | 72,8 % |
| Helvetica | 312.691 | 26,8 % |
| Calibri / Wingdings / Arial / Candara / Courier | 4.336 | 0,37 % |

Open Sans erscheint in **199 von 200 Decks**. Span-Count nach Face: `OpenSans-Regular` 515.313, `OpenSans-Bold` 262.452, `OpenSans-ExtraBold` 36.940, `OpenSans-Italic` 32.172, `OpenSans-BoldItalic` 1.921 — also **5 reale Faces** (Regular/Bold/ExtraBold + Italic-Varianten), die die `WEIGHT`-Map heute teils synthetisch (`bold:true`) erzeugt. Open Sans steht unter der SIL Open Font License (OFL), die Einbettung ausdrücklich erlaubt.

## Entscheidung

Empfehlung: **Option (a) — Server-Treue.** Open Sans (alle benötigten Faces) wird ins Docker-Render-Image aufgenommen, sodass der server-seitige PDF/PNG-Export pixel-treu ist; die editierbare PPTX wird **ohne** eingebettete Fonts ausgeliefert und referenziert „Open Sans" als `fontFace`. Font-Embedding in die PPTX (Option b) wird als optionaler, eigenständig zu beschließender EPIC-005-Folgeschritt dokumentiert, nicht jetzt umgesetzt.

## Alternativen

| Option | Pro | Contra |
|--------|-----|--------|
| **(a) Server-Treue: Open Sans ins Image, PDF/PNG pixel-treu, PPTX ohne Embedding** | Behebt F-E-02 direkt (Render-Treue, der Hauptbug); minimaler Aufwand (Font-Paket im Dockerfile); deckt 100 % des Versand-/Vorschau-Pfads ab, der heute das kundenrelevante Artefakt ist; OFL unkritisch beim reinen Installieren | Editierbare PPTX sieht auf einem Kunden-Rechner ohne Open Sans substituiert aus (LibreOffice/PowerPoint fällt auf eine Ersatzschrift zurück) — Glyphenbreiten/Umbrüche weichen dort ab |
| (b) Font-Embedding in die PPTX (OOXML `fontTable` + `embeddedFont`-Parts) | PPTX ist überall self-contained, exakt auch beim Kunden-Edit ohne installiertes Open Sans; Open Sans OFL erlaubt Embedding ausdrücklich | python-pptx/pptxgenjs können das **nicht** nativ — eigener OOXML-Post-Processing-Baustein nötig (fontTable.xml, embeddedFontN.fntdata-Parts, Relationships, `embedTrueTypeFonts`); 5 Faces × Embedding; Dateigröße steigt; PowerPoint-Embedding ist plattform-zickig (macOS-PowerPoint ignoriert eingebettete Fonts teils) — hoher Aufwand für einen Randfall |
| (c) Kunden installieren Open Sans (organisatorisch) | Null Code-Aufwand; PPTX bleibt schlank | Nicht durchsetzbar/kontrollierbar; verlagert das Problem zum Kunden; löst F-E-02 server-seitig **nicht** (Image braucht die Schrift ohnehin) |

## Konsequenzen

- **Positiv:** Der dominante Treue-Bug (F-E-02) wird mit einer Zeile im `Dockerfile` (Open-Sans-Paket bzw. die 5 OFL-Faces nach `/usr/share/fonts/`) behoben — der server-gerenderte PDF/PNG-Output, den der Kunde primär sieht, wird pixel-treu. Das ist die mit Abstand günstigste Maßnahme mit dem größten Treue-Gewinn.
- **Positiv:** Helvetica (26,8 %) ist mit `fonts-liberation` (Liberation Sans, metrik-kompatibel zu Helvetica/Arial) bereits server-seitig abgedeckt; nur Open Sans fehlt real. Die 0,37 % Restfonts (Calibri/Wingdings/Candara/Courier) sind vernachlässigbar und können separat (Carlito für Calibri, Wingdings-Glyph-Mapping) betrachtet werden — kein Blocker für (a).
- **Negativ/Einschränkung:** Die ausgelieferte PPTX bleibt nicht self-contained. Öffnet ein Kunde sie zum Bearbeiten auf einem Rechner ohne Open Sans, substituiert sein Office die Schrift; das editierbare Artefakt weicht dort optisch ab. Sollte das als kundenrelevant eingestuft werden, ist Option (b) der dokumentierte Weg.
- **Scope-Folge EPIC-005:** Option (a) erfordert **kein** eigenes Folge-Epic — sie ist ein kleiner Schritt innerhalb EPIC-005 (Font/Render-Treue, T2: Open Sans im Image). Option (b) (OOXML-Font-Embedding) wäre ein eigenständiges, separat zu beschließendes Arbeitspaket innerhalb EPIC-005 und sprengt den aktuellen Scope — daher hier nur als Option festgehalten, nicht eingeplant.
- **Voraussetzung:** Die `WEIGHT`-Map (`lib/text.js:6-12`) muss die real auftretenden 5 Faces sauber bedienen (siehe F-E-07) — sonst greift selbst bei installiertem Open Sans ein stiller Regular-Fallback. Diese ADR setzt voraus, dass T2 beide Punkte (Image-Font + Map-Vollständigkeit) abdeckt.

## Referenzen
- relates_to → FINDINGS-ENGINE.md (US-037) F-E-02 (Open Sans fehlt im Docker-Image), F-E-07 (WEIGHT-Map-Fallback)
- relates_to → font-report.json (US-038, 200 Decks) — Evidenz Open-Sans-Dominanz (72,8 % der Spans, 199/200 Decks, 5 Faces)
- relates_to → EPIC-005 (Font/Render-Treue), T2 (Open Sans ins Render-Image)
- SIL Open Font License (OFL) — erlaubt Einbettung von Open Sans
