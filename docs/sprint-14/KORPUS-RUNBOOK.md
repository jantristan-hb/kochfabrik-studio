# KORPUS-RUNBOOK — Textfreie Renders (US-069)

> Voll-Korpus-Lauf von `render_notext.py` über den kompletten lokalen
> Alt-Korpus. **Kein Sprint-Verify-Schritt** — dauert Stunden (soffice je
> Slide) und schreibt aufs Prod-Volume. Beide Schritte sind manuell und
> Ask-first (FEATURE-013 §11 Boundaries).

## Was im Sprint passiert ist (zur Abgrenzung)

Im Sprint wurden NUR die zwei committeten Cache-Decks gerendert (Sample):

- `kf-ausstattung-location` — 1 Seite
- `10-182-raumkarussell-gmbh-12-09-2026` — 8 Seiten

PNGs liegen unter `engine/data/cache/<deck>/preview_notext/p<page>.png`
(800×450, RGB) und sind committed. Reine Text-Seiten (z. B. raumkarussell
p1: nur `t=="text"`) rendern erwartungsgemäß leer — das ist der korrekte,
deterministische Filter-Output, kein Fehler.

## Pipeline-Kurzfassung

`render_notext.py` ist 1:1 die `render_previews.py`-Pipeline mit einem
deterministischen Filter davor: `strip_text(seq)` entfernt alle Elemente mit
`t == "text"`, der Rest (rect/image/Logos) bleibt unverändert und in Reihen-
folge. Ziel ist `preview_notext/` statt `preview/`. Idempotent: existierende
PNGs werden ohne `--force` geskippt.

SOFFICE-Binary kommt aus der Env `SOFFICE` (Default `soffice`).
**Mac hat kein soffice** (FEATURE-013 §12 Nr. 6) — alle Render-Läufe laufen
IM Container `kf-studio-sim` (LibreOffice + node vorhanden).

## Voraussetzungen

- Docker-Image `kf-studio-sim` lokal vorhanden (`docker images | grep kf-studio-sim`).
- Lokaler Voll-Korpus liegt als Cache-Verzeichnis vor (gleiches Layout wie
  `engine/data/cache/`: pro Deck `elements.json` + `logos.json` + `assets/`).
  Pfad hier als Env-Variable `KORPUS_CACHE` geführt — anpassen:

  ```bash
  export KORPUS_CACHE="/pfad/zum/voll-korpus/cache"   # ANPASSEN
  ```

## Schritt 1 — Voll-Lauf im Container (MANUELL, Ask-first)

`CACHE` ist im Skript fix relativ zu `engine/data/cache`. Den Voll-Korpus
deshalb über genau diesen Pfad in den Container mounten (überschattet im
Container nur den Mount, nicht das Repo). `render_notext.py` zusätzlich
mounten (frisches Image kennt das Skript noch nicht).

```bash
# Aus dem Repo-Root. Voll-Lauf ohne --deck = DB-Batch (menu_composition +
# static_slide) → braucht laufende Postgres im Container-Netz. Ohne DB:
# pro Deck einzeln mit --deck (Seiten werden aus elements.json abgeleitet).

# --- Variante A: DB-Batch (alle Slides aus der DB) ---
docker run --rm \
  -v "$KORPUS_CACHE:/app/engine/data/cache" \
  -v "$PWD/engine/tooling:/app/engine/tooling" \
  -e KF_PG_HOST="<host>" -e KF_PG_PORT="<port>" \
  -e KF_PG_DB="<db>" -e KF_PG_USER="<user>" -e KF_PG_PASS="<pass>" \
  kf-studio-sim python3 engine/tooling/render_notext.py

# --- Variante B: deckweise ohne DB (idempotent, resume-fähig) ---
# Deck-Slugs aus dem Korpus-Cache-Verzeichnis nehmen, je Deck:
docker run --rm \
  -v "$KORPUS_CACHE:/app/engine/data/cache" \
  -v "$PWD/engine/tooling:/app/engine/tooling" \
  kf-studio-sim python3 engine/tooling/render_notext.py --deck <deck-slug>
```

**Dauer-Warnung:** soffice startet je Slide einen Headless-Render — der
Voll-Korpus läuft **Stunden**. Kein `timeout`-Binary auf dem Mac
(FEATURE-013 §12 Nr. 5); stattdessen `--limit N` für Batches/Resume nutzen.
Der Lauf ist idempotent: bereits gerenderte PNGs werden geskippt, ein
Abbruch + Neustart setzt fort. `--force` nur, wenn bewusst neu gerendert
werden soll.

```bash
# Resume-Beispiel: erste 200 Slides, dann nächste Tranche
docker run --rm -v "$KORPUS_CACHE:/app/engine/data/cache" \
  -v "$PWD/engine/tooling:/app/engine/tooling" \
  kf-studio-sim python3 engine/tooling/render_notext.py --limit 200 ...
```

Nach dem Lauf liegen die PNGs durch den Volume-Mount direkt unter
`$KORPUS_CACHE/<deck>/preview_notext/` auf dem Host.

## Schritt 2 — Volume-Sync aufs Prod-Volume (MANUELL, Ask-first — NICHT ausführen)

> ⚠️ **Host-/Volume-Write — explizit Ask-first (FEATURE-013 §11).**
> Dieser Schritt synct die fertigen `preview_notext/`-PNGs auf das
> Prod-Cache-Volume und wird NUR nach ausdrücklicher Freigabe ausgeführt.
> Hier nur dokumentiert, im Sprint NICHT gelaufen.

```bash
# Beispiel: rsync der notext-PNGs auf das Prod-Volume (Pfade ANPASSEN).
# Nur die NEUEN Artefakte syncen — Bestand in cache/ ist read-only (R-NF-3),
# also gezielt nur preview_notext/-Verzeichnisse übertragen.
rsync -av --include="*/" --include="preview_notext/***" --exclude="*" \
  "$KORPUS_CACHE/" "<prod-host>:<prod-cache-pfad>/"
```

Verifizieren: stichprobenartig `preview_notext/p1.png` je Deck > 5 KB
(reine Text-Seiten ausgenommen — die sind erwartungsgemäß klein/leer).
