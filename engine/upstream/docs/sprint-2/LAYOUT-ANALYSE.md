# US-007 — Angebots-Korpus-Inventar & Layout-Analyse

> Erzeugt mit `phase0/scripts/scan_angebote.py` über den vollen Korpus
> `~/Nextcloud/Kochfabrik Dokumente/` (Stand 2026-05-19).

## Inventar

| | Wert |
|---|---|
| Korpus gesamt | **207 PDFs** (8 Muster + 199 Präsentationen) |
| `angebot` (kaufm. Angebot) | **34** |
| `menue` (Speisenidee/Menü) | 172 |
| `kontext` (Alt-Template ohne Labels) | 0 |
| nicht-KOCHfabrik | 1 |

`kf_classify` (Signatur 33/33 + Label-Block) trennt sauber: 34 echte
Angebots-PDFs als Grundlage für die Template-Extraktion.

## Layout-Generationen (3)

Geclustert nach Struktur-Signatur (Label-Set × Sektionen × Footer-Variante):

### GEN 2 — vollständig *(Referenz-Generation)* — 6 PDFs · score 12
- **Labels:** Veranstaltungsanlass, -datum, **-beginn**, Personenanzahl,
  -ort, Cateringkonzept (alle 6)
- **Footer:** Goldschätzchen + Planungsfabrik + Speisenmacherei (voller Bankblock)
- Preiszeilen vorhanden · Angebots-Nr. · Kundennr.
- Enthält die Muster RAUMKARUSSELL, HOWDENRE

### GEN 1 — modern-kompakt — 23 PDFs · score 6
- 5 Labels (**kein** Veranstaltungsbeginn), reduzierter Footer
- Die häufigste aktuelle Variante (z. B. Kinopolis, Hamburger Ding, Stage)

### GEN 3 — spärlich/alt — 5 PDFs · score 3
- nur Veranstaltungsort + Cateringkonzept, kein voller Block

> Bestätigt die Estimate-Warnung „Templates über Jahre variierend".
> Sprint 2 zielt auf **GEN 2** (vollständigste Felder → Template deckt
> auch GEN 1/3 ab, da diese eine Teilmenge der Felder nutzen).

## Referenz-Muster (für US-009 Template-Extraktion)

**`# 10_182_RAUMKARUSSELL GmbH_12_09_2026.pdf`** (GEN 2)
- höchster Vollständigkeits-Score (12): alle 6 Labels, voller Bankblock,
  Preisspalten, Angebots-/Kundennr.
- Sommerfest, 500 Personen, Live-Cooking/BBQ + Foodtruck + Buffet →
  enthält Positionsblöcke (Speisen/Getränke/Personal/Logistik) mit
  echten Preiszeilen → ideal um den Positions-Repeater abzuleiten.
- Hinweis: Datei ×2 md5-identisch gedoppelt; kanonisch ohne `(2)` nutzen.

## Block-Struktur (qualitativ; exakte Bboxes → US-009)

Reihenfolge im PDF (oben→unten), wird in US-009 via `extract.py`
(elements.json) geometrisch vermessen:

1. **Letterhead** — invariant: „Die KOCHfabrik GmbH - Peiner Hag 9a …"
2. **Empfänger** — Kunde + Adresse (variabel → Token)
3. **Metadaten** — Angebots-Nr./Datum/Kundennr./Lieferdatum/Ansprechpartner (Token)
4. **Veranstaltungsinformationen** — 6 Label-Felder (Token)
5. **Positionsblöcke** — Speisen/Menü · Getränke · Personal · Logistik,
   je wiederholbare Zeilen (Bezeichnung | Menge | Einzelpreis | Gesamt)
   → Repeater-Spec in US-011
6. **Footer/Bankblock** — invariant (Goldschätzchen/Planungsfabrik/
   Speisenmacherei + IBAN/BIC) → verbatim

> Sektions-Erkennung per Text-Regex griff nicht (in `pdftotext -layout`
> stehen Positions-Header auf Zeilen mit rechtsbündigen Preisspalten).
> Das ist **kein Blocker**: die Positions-Geometrie wird in US-009/US-011
> aus `extract.py`-Elementen (x/y/w/h) gewonnen — das vorgesehene,
> verlässliche Werkzeug.

## Verify

```bash
cd phase0/scripts && python3 scan_angebote.py
# → "angebot-Typen: 34 | Layout-Generationen: 3"
# → ">>> REFERENZ-MUSTER: # 10_182_RAUMKARUSSELL GmbH_12_09_2026 …"
```
