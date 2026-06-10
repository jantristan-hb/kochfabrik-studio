# Präsentations-Blueprint — Assembly-Vertrag (Angebot → Deck)

> **Zweck:** Was für eine Kundenanfrage zusammengebaut wird. Empirisch
> aus `docs/REPORT-structure.md` (199 Korpus-Decks, 2026-05-19).
> Dies ist der **Bauplan, dem der Assembler folgt** — Reihenfolge,
> Quelle und Aufnahme-Regel je Slide-Typ.

## Umfang (Scope-Faustregel)

- Ziel-Länge: **~11 Slides** (Median 11, Schnitt 11.9; 64% der Decks
  liegen 10–14).
- Mix: **~5 Food-Module + ~6 Rahmen-Slides** (Food-Anteil 43%).
- Formel: `Slides ≈ Rahmen-Skelett (fix) + N Food-Module` wobei
  N = Anzahl Speisen-Gänge im Angebot (typisch 3–6).

## Kanonisches Skelett (feste Reihenfolge)

| # | Slide-Typ | Quelle | Aufnahme-Regel | Inputs / Platzhalter |
|---|---|---|---|---|
| 1 | **Cover** (Event-Titel) | datengetrieben | immer | `{kunde} {event} {datum} {ort} {gäste}` |
| 2 | **Deine Catering- & Event-Crew im Norden** | Template-Bib (statisch) | immer (77%) | — (Brand) |
| 3 | **So empfangen wir euch** | Template-Bib | bedingt (35%) — wenn Empfang/Sektempfang im Angebot | ggf. Empfangs-Gericht |
| 4…k | **FOOD-MODULE** | `menu_composition` via pgvector-ANN + Text-Swap | je Angebot-Gang eins, in Angebot-Reihenfolge | Gang-Headline + Gerichte (Text-Swap) |
| k+1 | **Personal** | Template-Bib | meist (74%) | optional aus Angebot-Personal-Tabelle |
| k+2 | **Ausstattung** | Template-Bib | optional (~11%) — wenn Equipment/Ausstattung relevant | — |
| k+3 | **Wertschätzung ist der Schlüssel** | Template-Bib (reine Brand) | fast immer (80%) | — |
| k+4 | **Kontakt** | Template-Bib | immer (82%, **stets letzte**) | KOCHfabrik-Kontakt (fix) |

**Aufnahme-Logik:** „immer" = Skelett-Pflicht. „bedingt" = nur wenn das
Angebot den Anlass hergibt (Empfang-Gang → So empfangen wir euch;
Equipment-Posten → Ausstattung). „meist/fast immer" = default an, per
Flag abschaltbar.

## Empirische Template-Frequenz (exakt-identische Instanzen)

> Quelle: `dedup_exact.sig` über pristine 1053-Nicht-Food (199 Decks).
> **Exakt-identisch** (gesamter Text + Element-Layout byte-gleich) =
> härtestes Kanonizitäts-Signal — schärfer als Headline-Cluster-%.
> **Scharfe Kante: nur 4 Typen sind exakt-kanonisch, danach Abfall auf
> ≤4%.** Das definiert das Pflicht-Skelett.

| Rang | Exakt-Kopien | Decks-Anteil | Typ | Regel |
|---|---|---|---|---|
| 1 | 155 | 77% | **KONTAKT** | **Pflicht** (immer letzte) |
| 2 | 151 | 75% | **WERTSCHÄTZUNG IST DER SCHLÜSSEL** | **Pflicht** |
| 3 | 143 | 71% | **DEINE CATERING- & EVENT-CREW IM NORDEN** | **Pflicht** |
| 4 | 122 (+Phrasing-Varianten ≈140) | ~70% | **PERSONAL** | **Pflicht** (eine kanonische Phrasing wählen) |
| 5+ | ≤9 | ≤4% | Ausstattung / So-empfangen / Vision / Tellersprache / Lounge Factory / … | **bedingt/optional** (event-spezifisch, keine Kanon-Instanz) |

→ **Hartes Pflicht-Skelett = Cover (datengetrieben) + diese 4 Frame-
Templates.** Alles ab Rang 5 ist NICHT byte-kanonisch → nur aufnehmen
wenn der Angebot-Anlass es trägt; sonst weglassen. PERSONAL hat mehrere
Phrasing-Varianten über die Jahre — in der Template-Bib **eine** als
kanonisch markieren.

**Scope-Präzisierung:** `Slides ≈ Cover + 4 Pflicht-Frame + N Food
[+ Ausstattung/So-empfangen falls Anlass]` ≈ 5 + N (typisch 8–12).

## Food-Modul-Reihenfolge (kanonisch, früh → spät)

Innerhalb des Food-Blocks die gematchten Module nach typischer Position
ordnen (aus Korpus-Ø-Position):

`Finger Food / Flying Fingerfood → BIG BBQ / Street Food / Flying Food →
Live Cooking → Lunch → Sweet Dreams (Dessert) → Wine Time → Mitternachts
Snack → Softes & Hopfiges / Longdrinks / High Balls`

Heuristik: herzhaft/warm vor süß, Speisen vor Getränken, Mitternachtssnack
spät. Bei Gleichstand: Reihenfolge wie im Angebot.

## Assembly-Algorithmus

1. **Angebot parsen** → Felder (`kunde,event,datum,ort,gäste`) +
   Vereinbarung/Agenda + Speisen-Gänge (`compose_offer.parse_offer*`).
2. **Cover** datengetrieben aus Feldern füllen.
3. **Rahmen-Skelett** (Crew / [So empfangen] / Personal / [Ausstattung] /
   Wertschätzung / Kontakt) aus **Template-Bibliothek** (`info_slide`,
   eine goldene Instanz je Typ, Platzhalter füllen).
4. **Food-Module:** je Gang pgvector-ANN gegen `menu_composition`
   (kategorie-kohärent) → beste Komposition → **Text-Swap** auf die
   Angebot-Gerichte (Headline/Foto-Set/Layout bleiben).
5. **Reihenfolge** = Skelett oben; Food-Block in kanonischer Modul-
   Reihenfolge einsortieren.
6. **Element-JSONs konkatenieren** (alles aus dem warmen Cache, keine
   Laufzeit-Extraktion) → **1× `reconstruct.js`** → editierbares PPTX.

## Quellen-Mapping

| Slide-Typ | Datenquelle | Mechanik |
|---|---|---|
| Cover, Agenda | Angebot-Felder | datengetrieben (Platzhalter) |
| Crew, So-empfangen, Personal, Ausstattung, Wertschätzung, Kontakt | `info_slide` (Template-Bib) | kanonische Instanz + Platzhalter |
| Food-Module | `menu_composition` (+ `embedding`) | ANN-Match + Text-Swap |
| Alle Elemente/Assets | `phase0/data/cache/<slug>/` | reine Assembly (Hot-Path ~0.3 s) |

## Quelle der Wahrheit / Stand

- Empirie: `docs/REPORT-structure.md` (199 Decks).
- Food-Korpus: `menu_composition` (1010, pgvector) —
  [[reference_pptxgenerator_v2_postgres]].
- Template-Bib (Nicht-Food): wird aus dem kuratierten `/tmp/all_info.pptx`
  → `info_slide` befüllt (Step 2/3).
- Frequenzen/Positionen = Aufnahme- & Reihenfolge-Regeln; bei
  Korpus-Update Report neu erzeugen und Tabellen hier nachziehen.
