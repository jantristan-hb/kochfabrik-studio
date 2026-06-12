---
key: KOCHFABRIK-FEATURE-013
status: implemented
title: "Korpus-Assets: textfreie Renders + Bild-Embeddings (bildbewusstes Ranking)"
created: 2026-06-12
project: kochfabrik
---

# KOCHFABRIK-FEATURE-013: Korpus-Assets für den Wizard

> **Typ:** FEATURE (Brownfield-Delta, Tooling + Engine). Sprint 14.
> Zwei Offline-Batches, die der Wizard konsumiert: (1) textbereinigte
> Slide-Renders, (2) Bild-Beschreibungs-Embeddings für Score-Mix.

## 1. Vision

Jede Korpus-Slide existiert zusätzlich als **textfreies PNG** (Vorlage
ohne fremde Kundennamen/Gerichte) und trägt ein **Bild-Embedding**
(Gemini-Vision-Beschreibung der Fotos → Text-Embedding im selben
768er-Raum wie pgbundle). Kandidaten-Ranking = Mix aus Text- und
Bild-Match — vorgeschlagene Slides passen auch BILDLICH zum Angebot.

## 3. Datenmodell

| Artefakt | Ort | Inhalt |
|---|---|---|
| Notext-Render | `cache/<deck>/preview_notext/p<page>.png` | 800×450-PNG, Render ohne `t=="text"`-Elemente |
| Bild-Embeddings | `engine/data/imgbundle.npz` | `deck[]`, `page[]`, `imgemb float32 N×768` (L2-normiert), `desc[]` (Beschreibungstexte, debugbar) |

## 4. Flows

```
render_notext.py (analog render_previews.py, idempotent):
  elements.json[page] → Text-Elemente filtern → 1-Slide-PPTX via
  reconstruct.js → soffice png → PIL 800×450 → preview_notext/
embed_images.py (idempotent, --limit):
  je Slide mit image-Elementen: Slide-PNG (preview/) → Gemini-Vision
  „beschreibe die Speisen/Szene knapp deutsch" → compose_offer.embed
  (GLEICHES Modell wie pgbundle!) → imgbundle.npz
bundle.py: load_img() (gecacht) + rank_mixed(qv, k, alpha) —
  score = alpha*text_sim + (1-alpha)*img_sim (img fehlt → text only).
  np.load auf imgbundle NUR hier (ADR-003-Disziplin analog pgbundle).
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN render_notext.py für eine Slide läuft THE SYSTEM SHALL ein
   PNG ohne jegliche Korpus-Texte unter `preview_notext/` ablegen
   (Beweis: pdftotext/OCR-frei nicht nötig — Element-Filter ist
   deterministisch; Verify = Datei existiert + Quell-Elements ohne
   text-Typ gerendert), idempotent bei Wiederholung.
2. WHEN embed_images.py für eine Sample-Menge läuft THE SYSTEM SHALL
   imgbundle.npz mit L2-normierten 768er-Vektoren je Slide erzeugen
   und eine semantische Stichprobe SHALL plausibel ranken (Query
   „Flying Dinner" → Flying-Dinner-Slide vor Dessert-Slide).
3. WHEN bundle.rank_mixed mit alpha=1.0 läuft THE SYSTEM SHALL exakt
   die bisherige rank-Reihenfolge liefern (Rückwärtskompatibilität);
   IF imgbundle fehlt THEN SHALL rank_mixed auf reines Text-Ranking
   zurückfallen (graceful, kein Crash im Container ohne Artefakt).
4. THE SYSTEM SHALL beide Batches als dokumentierte Runbook-Befehle
   liefern (Voll-Korpus-Lauf = manueller Schritt, dauert Stunden).

## 9. Abgrenzung (Nicht-Teil)

- Kein Voll-Korpus-Lauf im Sprint-Verify (Sample = die 2 committeten
  Cache-Decks; Voll-Lauf + Volume-Sync = Runbook-Schritt danach)
- Kein OCR/keine Bilderkennung zum Text-Entfernen (Element-Filter!)
- imgbundle wird NICHT in pgbundle.npz eingebaut (read-only, R-NF-3)

## 9a. Boundaries (3-Tier)

- ✅ **Always:** neue Dateien `engine/tooling/render_notext.py`,
  `engine/tooling/embed_images.py`; `engine/scripts/bundle.py` additiv
  erweitern (load_img/rank_mixed — bestehende Funktionen UNANGETASTET);
  Sample-Läufe lokal (2 committete Decks); imgbundle.npz für das Sample
  committen NUR falls < 1 MB, sonst gitignore + Runbook
- ⚠️ **Ask-first (headless → BLOCKED):** Volume-/Host-Writes (Sync der
  notext-PNGs aufs Prod-Volume = Runbook-Schritt, NICHT im Sprint);
  Voll-Korpus-Gemini-Lauf (~Kosten); neue Python-Dependencies
- 🚫 **Never:** pgbundle.npz/cache-Bestand verändern (R-NF-3); echte
  Gemini-Calls in der Test-Suite; rank()-Bestandsverhalten ändern
  (Ranking-Gold-Test test_bundle_ranking_gold MUSS grün bleiben)

## 10. Abgrenzung zum Ist

- Previews zeigen fremde Texte → zusätzlich textfreie Variante
- Ranking rein textbasiert (pgbundle) → optionaler Text+Bild-Mix

## 11. Implementierungs-Anker (Ist)

`engine/tooling/render_previews.py` (idempotente Render-Pipeline:
elements→reconstruct.js→soffice→PIL 800×450 — 1:1-Vorlage),
`engine/scripts/bundle.py` (load/normalize_query/rank; Gold-Test
`backend/tests/test_sprint12.py::test_bundle_ranking_gold`),
`engine/scripts/compose_offer.py` (embed = Gemini-Batch, gleiches
Modell wie pgbundle), `backend/engine_glue.py:288` (image_kochfabrik —
Gemini-Request-Muster für Vision-Call), `engine/data/cache/*/
elements.json` (`t=="text"`-Filterkriterium; `_meta.w_pt/h_pt`),
Sample-Decks: `kf-ausstattung-location`, `10-182-raumkarussell-…`.

## 12. Bekannte Pitfalls

1. **Render-Dauer:** Voll-Korpus = Stunden (soffice je Slide) — Sprint
   verifiziert am Sample; Voll-Lauf ist Runbook-Schritt mit --limit/
   Resume (idempotent wie render_previews).
2. **Gold-Test-Falle:** test_bundle_ranking_gold friert rank() ein —
   rank_mixed als NEUE Funktion, rank() nicht anfassen.
3. **Embedding-Raum-Mix:** img-Beschreibungen MÜSSEN durch
   compose_offer.embed (gleiches Modell) — ein anderes Embedding-Modell
   macht die Cosine-Mischung bedeutungslos.
4. **Decks ohne Fotos** (reine Text-Slides): kein img-Vektor → in
   rank_mixed neutral behandeln (text-only für diese Slides), nicht 0.
5. **Kein `timeout`-Binary** (macOS); Batches mit eigenem --limit.
6. **Kein soffice auf dem Mac** (verifiziert 2026-06-12) — Render-Läufe
   laufen IM Docker-Image (`kf-studio-sim` hat LibreOffice+node):
   `docker run -v engine/data:/app/engine/data …`; render_notext liest
   SOFFICE-Env. Volume-Mount macht die PNGs auf dem Host sichtbar.

## Vision-Alignment

**Adressierte These:** R-DECK-1/4 (Vorschlagsqualität), R-FONT-5
(Vorlagen-Charakter), Vertrag 2026-001 §3.2 „KI-gestützte Bildsuche
nach Kontext und Inhalt"
**Kern-Loop-Schritt:** Vorschläge passen bildlich → weniger Nacharbeit
**Nächste Iteration:** Tag-Filter im Wizard („nur BBQ-Slides")

## Referenzen
- implements → REQUIREMENTS R-DECK-4, R-NF-3 · Vertrag 2026-001 §3.2
- depends_on → [[KOCHFABRIK-ADR-003]] (Bundle-Disziplin)
- relates_to → [[KOCHFABRIK-FEATURE-014]] · [[KOCHFABRIK-FEATURE-015]]

## Referenziert von
— USER-STORIES Sprint 14 (US-069, US-073)
