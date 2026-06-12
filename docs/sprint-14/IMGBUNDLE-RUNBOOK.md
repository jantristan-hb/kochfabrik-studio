# IMGBUNDLE-RUNBOOK — Bild-Embeddings (US-073)

Erzeugung von `engine/data/imgbundle.npz`: je Korpus-Slide mit Foto ein
L2-normierter 768er-Bild-Embedding-Vektor, abgeleitet aus einer
Gemini-Vision-Beschreibung. `rank_mixed()` (in `engine/scripts/bundle.py`)
mischt diesen img-Score mit dem Text-Score (`score = alpha*text_sim +
(1-alpha)*img_sim`).

## Pipeline (`engine/tooling/embed_images.py`)

1. **Slide sammeln** — Cache-Decks (`engine/data/cache/<deck>/elements.json`)
   nach Slides mit `image`-Elementen scannen.
2. **Vision-Quelle wählen** — bevorzugt das vorab gerenderte
   Slide-Preview `cache/<deck>/preview/p<page>.png` (gleicher Render, den
   die Slide-Suche serviert). Fehlt es, Fallback auf das größte
   eingebettete Foto-Asset der Slide (`elements.json` `src`).
3. **Vision** — Gemini `generateContent` (inlineData-PNG + Text-Prompt,
   OHNE `responseModalities: [IMAGE]` → Text-Antwort) → kurze deutsche
   Beschreibung (Speisen / Szene / Stimmung). Modell:
   `KF_VISION_MODEL` (Default `gemini-2.5-flash`).
4. **Embedding** — `compose_offer.embed()`, das **gleiche** Gemini-Modell
   wie pgbundle (`gemini-embedding-001`, 768D, `SEMANTIC_SIMILARITY`).
   Anderes Modell ⇒ Cosinus-Mischung in `rank_mixed` bedeutungslos
   (FEATURE-013 §12 Pitfall 3).
5. **Schreiben** — `imgbundle.npz {deck, page, imgemb (float32,
   L2-normiert), desc}`, sortiert nach (deck, page).

Idempotent: vorhandene (deck,page)-Einträge werden geskippt, nur neue
Slides beschrieben + embedded. `--force` embeddet alle gesammelten Slides
neu.

## Befehle

```bash
source ~/work/.env                 # GEMINI_API_KEY

# Voll-Lauf über ALLE Cache-Decks
tools/.venv/bin/python engine/tooling/embed_images.py

# nur bestimmte Decks
tools/.venv/bin/python engine/tooling/embed_images.py --decks deckA,deckB

# erste N Slides (Smoke), alle neu
tools/.venv/bin/python engine/tooling/embed_images.py --limit 5 --force
```

> **Previews zuerst rendern (Prod-Pfad):** Für die beste Vision-Quelle vor
> dem Voll-Lauf die Slide-Previews erzeugen — `engine/tooling/render_previews.py`
> (braucht `node` + `soffice`/LibreOffice + Postgres mit dem Korpus).
> Ohne Previews greift der Foto-Asset-Fallback (für rein dekorative
> Slides — z.B. Logo-Splash-Frames — entsprechend wenig aussagekräftig).

## Kosten / Dauer (Voll-Korpus)

> ⚠️ **Voll-Korpus-LLM-Läufe sind kostenpflichtig — vor einem Lauf über
> den gesamten Korpus erst Rücksprache (Sprint-Boundary „Ask-first").**

- 1 Gemini-Vision-Call (`generateContent`) **pro** image-Slide +
  Embedding-Batches à 100 Beschreibungen (`batchEmbedContents`).
- Der pgbundle-Korpus umfasst ~1007 Slides; davon trägt nur eine Teilmenge
  Foto-Elemente. Grobe Hausnummer: ein Vision-Call je Foto-Slide, sequ
  mit ~120 s Timeout je Call → Voll-Lauf im Minuten- bis Zehn-Minuten-
  Bereich, dominiert von der Anzahl Foto-Slides und der Vision-Latenz.
- Embedding-Kosten sind gegenüber Vision vernachlässigbar
  (`gemini-embedding-001`, 768D, gebatcht).
- **idempotent** → ein wiederholter Lauf embeddet nur neue Slides nach,
  kostet also nichts für bereits enthaltene (deck,page).

## Sample-Lauf (committet, 2 Decks)

`source ~/work/.env` + Voll-Lauf über die 2 committeten Cache-Decks
(`10-182-raumkarussell-gmbh-12-09-2026`, `kf-ausstattung-location`) →
8 image-Slides, `imgbundle.npz` 27 KB (< 1 MB → committet).

Semantische Stichprobe — Query „Flying Dinner mit eleganten
Fingerfood-Häppchen in rustikaler Location" (via `compose_offer.embed`),
Bild-Embeddings nach Cosinus gerankt:

```
+0.843  kf-ausstattung-location:1   rustikaler Raum, Holzbalken, Backsteinwände …
+0.804  10-182-…:5                  goldene abstrakte Spritzer (Deko-Frame)
 …      10-182-…:*                  abstrakte KOCHfabrik-Logo-Splash-Frames
```

Die einzige Slide mit echtem Szenen-Foto (rustikale Location) rankt klar
vor den dekorativen Logo-Frames — semantisch plausibel.

`rank_mixed(qv, 5, alpha=0.3)` über pgbundle läuft fehlerfrei; da die 2
Sample-Decks nicht im pgbundle stehen, greift dort sauber der
Text-only-Fallback (Treffer: FLYING FINGERFOOD / FLYING DINNER).
