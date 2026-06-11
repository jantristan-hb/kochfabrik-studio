# Tooling-Split — Klassifikation (US-056, 2026-06-11)

> Methode: AST-Import-Graph + subprocess-/String-Referenzen über alle
> 46 `engine/scripts/`-Module; transitive Closure ab den Runtime-Wurzeln
> (alles, was `backend/*` importiert, + subprocess-Entry `assemble.py`).
> **Klassifikation per Import-Graph, NICHT per Namen** — zwei
> Anti-Namensraten-Befunde unten. Freigabe: team-lead (Option A,
> EARS §8 Nr. 3 maßgeblich; TEST.md-Sample war fehlerhaft).

## Runtime — bleibt `engine/scripts/` (13)

| Modul | Begründung (Referenzpfad) |
|---|---|
| assemble.py | subprocess-Entry aus backend/routers/praesentation.py |
| compose_offer.py | import aus backend (engine_glue) + assemble.py |
| bundle.py | EINZIGE pgbundle-Ladestelle (ADR-003); backend/slidesuche.py + pg_shim |
| pg_shim.py | assemble.py-Datenpfad (PPTX_PGSHIM=1) |
| _deckpipe.py | import aus assemble.py + compose_offer.py |
| angebot_chat.py | import aus backend (engine_glue) — Chat→Angebot |
| angebot_model.py | import aus backend + angebot_chat |
| angebot_fill.py | import aus angebot_render-Pfad |
| angebot_positions.py | import aus angebot_render |
| angebot_render.py | import aus backend (PDF-Erzeugung) |
| **gen_fiktiv.py** | ⚠ Anti-Namensraten: trägt MODEL/SCHEMA/_key/_extract — import aus engine_glue:349 + angebot_chat:18; ohne sie ENGINE_OK=False → alle /api/angebot/* 503 |
| **build_angebot_template.py** | ⚠ Anti-Namensraten: subprocess-Aufruf aus angebot_render.py + verify_angebot.py |
| kf_classify.py | import aus compose_offer (Kategorie-Lock) |

## Tooling — verschoben nach `engine/tooling/` (33)

analyze_structure · angebot_gate · angebot_parse · build_cache ·
build_category_samples · build_cover_template · build_golden ·
build_info_deck · build_info_top20 · build_korpus · build_menu_deck ·
compose_demo · curate · db_embed · db_load · db_load_static ·
dedup_exact · dedup_previews · docs_samples · embed_cluster ·
ingest_compositions · korpus_gate · pdf_diff · phase_b_gate ·
recon_context_reuse · recon_food_reuse · recon_image_reuse ·
render_previews · resort_pptx · scan_angebote · slide_text ·
validate_assembled · verify_angebot

Kein Runtime-Modul importiert eines dieser 33 (geprüft: Imports +
subprocess-Strings in backend/**, engine/scripts/**, tools/*.sh,
Dockerfile). Tools mit Imports aus dem Runtime-Kern tragen eine
`sys.path`-Zeile auf `../scripts` (21 Module, reine Pfad-Zeile,
keine Logikänderung). `render_previews.py` ist Vorab-Tooling
(Preview-Generierung offline) — Slidesuche liest nur die PNGs.

## Hinweise

- Crash-Recovery: Der Split wurde nach einem cmux-Absturz vom
  team-lead aus dem gestageten Stand des Ketten-Agenten
  fertiggestellt (Klassifikation/Moves/sys.path-Fixes stammen vom
  Agenten, verifiziert vor Commit).
- Folgearbeit (EPIC-009/B2-Doku): Regenerier-Befehle referenzieren
  jetzt `engine/tooling/` (build_cache, render_previews).
