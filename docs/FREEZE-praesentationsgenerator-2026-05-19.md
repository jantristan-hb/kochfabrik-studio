# FREEZE — Präsentationsgenerator v1 (2026-05-19)

> **Eingefroren bei:** Tag `freeze/praesentationsgenerator-2026-05-19`
> = `main` @ `6d218bc` (GitHub jantristan-hb/pptxgenerator_v2).
> Bekannter guter Stand **vor** dem Angebotsgenerator-Riesenfeature.
> Rollback-Anker davor: `d5179ac` (DB fertig + Assembler verifiziert).

## Was der Präsentationsgenerator ist

**Input:** ein KOCHfabrik-Angebots-/Speisen-PDF (oder md-Fixture).
**Output:** ein kanonisches, element-für-element editierbares PPTX-Deck
im KOCHfabrik-Skelett (Cover → Food-Gänge → Pflicht-Frames →
Ausstattung → Kontakt), ~0,8 s, über den DB-Workflow.

**Abgrenzung:** Das hier ist der **Präsentationsgenerator**
(Angebot-PDF → Präsentation). Der geplante **Angebotsgenerator**
(Chat → pixelgenaues KOCHfabrik-Angebots-PDF) ist ein separates
Riesenfeature und NICHT Teil dieses Freezes.

## Pipeline (end-to-end)

```
PDF ─► kf_classify: IDENTIFY (Signatur 33/33) + Footer-Strip
      └► CLASSIFY  angebot | menue | kontext
         • menue   → parse_offer_dishes (Per-Gericht-Parser)
         • angebot → Felder per festem Label + derive_courses
                     (Cateringkonzept/Anlass/Empfang → Gang-Headlines)
         • kontext → ganzer Event-Text als semantische Headline
      └► Kategorie-Lock: Headline → nächstes module_label (Embedding)
         → ANN NUR im Modul → Kapazitäts-Tiebreak
      └► Assemble: Cover-Template (Kundenname) + Pflicht-Frames
         (kunden-stabil random) + Food-Slides + Ausstattung-Template
      └► reconstruct.js → editierbares PPTX
```

Abgeleitete Gänge (`ds=[]`) → Korpus-Slide **verbatim** (echte
KOCHfabrik-Gerichte, kein text_swap). Geparste Gänge → text_swap
(Angebots-Gerichte in die Caption-Slots).

## Datenbestand

- **DB** `pptxgen-pg`, `localhost:5434`, `postgres/pptxgen`, db `pptxgen`
  - `menu_composition`: **1010** Food + `embedding vector(768)`
    (hnsw cosine), `module_type`/`module_label`
  - `static_slide`: **16** Frames (golden + Alternativen, COVER/CREW/
    PERSONAL/AUSSTATTUNG/WERTSCHÄTZUNG/KONTAKT)
- **Korpus** `~/Nextcloud/Kochfabrik Dokumente/`
  - `AKARA_Präsentationen/` **199** echte Referenzdecks (Trainingskorpus)
  - `AKARA_Muster_Angebote/` 8 PDFs = **4 unique, ×2 md5-gedoppelt**
  - `images/` Bildquelle · doppelter Ordner `AKARA_Pr%C3%A4sentationen`
    (Nextcloud-Sync-Artefakt, bereinigen)
- Element-/Asset-Cache: `phase0/data/cache/` (Hot-Path, kein Runtime-
  Extrakt — Electron-tauglich)

## PDF-Typen (empirisch belegt, 33er-Stichprobe)

| Typ | Erkennung | Anteil | Verhalten |
|-----|-----------|--------|-----------|
| `menue` | enumerierte CAPS-Gänge + Gerichte | 23/33 | Per-Gericht-Parser + text_swap |
| `angebot` | `Veranstaltungsinformationen`/`Cateringkonzept:`-Labels, oft OHNE Gerichte | 10/33 | Gänge aus Kontext abgeleitet, Korpus liefert Speisen |
| `kontext` | altes Template, weder noch | 0/33 (Sample) | Event-Text als semantische Headline (nur Unit-getestet) |

**KOCHfabrik-Signatur 33/33** — Letterhead/Domain invariant über
Jahre/Kunden/Typen → deterministische Identifikation.

## Verifiziert

- **20 synthetische** Vary-Decks (Gänge 2–6) → Slide-Zahl skaliert
  linear (N+6), Kategorie-Lock 20/20 PASS
- **4 echte Muster-Angebote**: INBOUND 10 / RAUMKARUSSELL 8 /
  HOWDENRE 8 (abgeleitet, Korpus-Speisen) · Risk_Ident 9 (geparst)
- Food-Slides der abgeleiteten Decks = saubere generische KOCHfabrik-
  Content-Slides (Headline + Gerichte), **kein Fremdkunden-Leak**
- Tests grün auf main: `test_kf_classify`, `test_empty_courses`,
  `test_frame_pick`

## Bewusst offene Qualitätsthemen (kein Scope dieses Freezes)

1. **Risk_Ident-OVERFLOW** — text_swap quetscht bei vielen Gerichten
   mehrere in einen Slot (Qualität, nicht Korrektheit).
2. **`kontext`-Typ** nur per Unit-Test — am echten 199er-Korpus
   ungetestet (kam in Stichprobe nicht vor).
3. Abgeleitete Decks = **kuratierter Vorschlag** aus Bestandsmaterial,
   kein vom Kunden bestelltes Menü. Bespoke nur bei `menue`-Typ.
4. Kalibrier-Konstanten + z-Order-Regeln nur an Teilkorpus validiert
   (Phase-B-Gate offen, siehe USER-STORIES Sprint 1).

## Befehle

```
# DB muss laufen (pptxgen-pg :5434)
cd phase0/scripts
python3 assemble.py "<angebot.pdf|md>" [--offer SEL] -o out.pptx
python3 validate_assembled.py "<angebot>" out.pptx [--offer SEL]
cd phase0 && python3 tests/test_kf_classify.py   # + die anderen 2
```

## Nächstes (separat, via /epic)

**Angebotsgenerator** — Chat → 20–30 fiktive PDFs pixelgenau im
KOCHfabrik-Aufbau → später Generierung aus Angebotsgenerator-Chat.
Komplexes Riesenfeature, wird via `/epic` zergliedert. Dieser Freeze
ist der stabile Ausgangspunkt davor.
