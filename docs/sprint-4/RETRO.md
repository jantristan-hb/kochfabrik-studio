# Sprint 4 + 5 — Retrospektive (EPIC-001-Abschluss)

## Was lief gut
- AK2 in einem Batch-API-Lauf (CLAUDE.md-konform): 20/20 valide
  JSONs → 20/20 PDFs → 20/20 konform, ein durchgängiger Pipeline-Lauf.
- AK3 cross-repo sauber via **graceful Engine-Import** — Live-Studio
  (Bildgenerator) bleibt bei fehlender Engine unberührt (kein Crash).
- Engine-Bundle erkannt klein (~9 MB statt 5 GB Vollcache):
  `cached_deck` short-circuit + nur 1 Referenz-Slug.
- Coolify-Build atomar → Live-Deploy-Versuch ohne Prod-Risiko.

## Was lief schlecht / hätte besser sein können
- LLM-JSON erst durch max_tokens=1800 abgeschnitten (invalides JSON);
  Fix max_tokens=4000 + kompakt/begrenzt erzwingen. Hätte vorab als
  Risiko gesehen werden können.
- `_key()` öffnete `~/work/.env` unbedingt → Container-FileNotFound;
  Fix env-first. Containertauglichkeit gehört in die Story-Annahmen.
- Scope-Erweiterung (Frontend statt CLI) + Studio-Host kamen mitten
  in Sprint 4 — flexibel gelöst, aber Plan-Drift.

## Plan-vs-Reality
| Story | Status | Abweichung |
|-------|--------|------------|
| US-020/021/024 | ✅ | — (AK2 20/20) |
| US-022/023/025 | ❌→Post-Epic | GEN-1/3 + Polish bewusst nicht AK |
| US-026 (Sprint 5) | 🔄 | aus „CLI-Chat" → vollwertiges Studio-Modul (Chat+Hand-Edit+PDF) erweitert |

## Learnings
- Bei LLM-JSON-Bulk: Output-Größe begrenzen + max_tokens großzügig +
  Schema-Validierung mit Skip — vorab einplanen.
- Engine-Code container-tauglich schreiben (env-first Keys, keine
  fixen Host-Pfade) — spart Vendoring-Nacharbeit.
- Studio-Engine-Integrations-Pattern dokumentiert
  (`reference_studio_engine_integration_pattern`) — für
  Präsentationsgenerator wiederverwenden (DB-Caveat).

## Offene technische Schulden → Post-Epic-Backlog (PROGRESS.md)
GEN-1/3-Generalisierung · Cross-Template-Treue · `_kunde`-Heuristik ·
Sub-Header-Unterstreichung · Präsentationsgenerator-Studio-Integration
(DB-Caveat) · Live-Container-Verifikation (LibreOffice/node Build).
