# BATCH-PROTOKOLL — US-078 Voll-Korpus-Batches (2026-06-12)

> Lead-Story, exakt nach `docs/sprint-14/KORPUS-RUNBOOK.md` +
> `IMGBUNDLE-RUNBOOK.md`. Alle Schritte durch den Sprint-15-Plan
> explizit autorisiert.

## 1. Notext-Render (Voll-Korpus)

- Quelle: lokaler Alt-Korpus `../pptxgenerator_v2/phase0/data/cache`
- Variante B (deckweise, ohne DB), im Container `kf-studio-sim`
- **201/201 Decks gerendert, 0 Fehler**, Dauer ~35 min
- Ergebnis: 2376 Notext-PNGs in 201 `preview_notext/`-Verzeichnissen

## 2. Volume-Sync (Prod)

- rsync (`--ignore-existing`, nur `*/preview_notext/**`) →
  `188.245.110.5:/data/coolify/applications/yu2fqx0twmtqcp6zyx2e59si/cache/`
- rc=0 · Zähl-Beweis: Volume vorher **0** notext-Dirs → nachher
  **201 Dirs / 2376 PNGs** (deckungsgleich mit lokal)
- Korpus-Bestand unangetastet (nur neue Dateien)

## 3. Bild-Embeddings (Voll-Korpus)

- `embed_images.py` im Container (Nested-Mounts), Vision
  gemini-2.5-flash → compose_offer.embed (gemini-embedding-001, 768D)
- **Ergebnis: imgbundle.npz mit 2087 Slides über alle 201 Decks (6,8 MB)**
- **Vorfall + Härtung:** Erster Lauf brach nach 1043 Vision-Calls mit
  Gemini-503 ab — `np.savez` lief nur am Ende, alle Calls verloren.
  embed_images.py auf diesem Branch gehärtet: **Checkpoint alle 25
  Slides (atomar via tmp+rename) + Retry mit Backoff (10/30/60 s) bei
  429/5xx, SKIP statt Crash nach 3 Versuchen.** Zweiter Lauf: 2079 neue
  Slides, 2 Retries erfolgreich gefangen, 0 Skips, rc=0.
- Kosten: ~3100 Vision-Calls gesamt (inkl. verlorener erster Lauf),
  gemini-2.5-flash — niedriger einstelliger €-Bereich.

## 4. Semantik-Stichprobe (volles Bundle)

Query „Flying Dinner mit eleganten Fingerfood-Häppchen",
`rank_mixed(alpha=0.3)` (bildlastig):

```
1. 16-01-2026-dfvxpdl S.4            FLYING FINGERFOOD
2. 09-10-2025-marazzi-abendevent S.4 FLYING DINNER
3. 17-10-2025-kf-stiftungstreffen S.6 FLYING DINNER
```

Alle Top-Treffer sind echte Flying-Dinner/Fingerfood-Slides — das
bildbewusste Ranking arbeitet über den vollen Korpus.

## 5. Aktivierung

Nach Merge dieses Branches + Deploy (Sprint-Review): suggest nutzt
rank_mixed mit vollem imgbundle (KF_RANK_ALPHA=0.7 Default), die
Wizard-Stage findet für jede Korpus-Slide ein Notext-PNG.
