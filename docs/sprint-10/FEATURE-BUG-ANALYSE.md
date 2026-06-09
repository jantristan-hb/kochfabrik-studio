---
key: KOCHFABRIK-FEATURE-001
status: approved
title: "Bug-Analyse beider Repos + Test-Baseline-Inventur"
created: 2026-06-09
project: kochfabrik
---

# KOCHFABRIK-FEATURE-001: Bug-Analyse + Test-Baseline

> **Typ:** FEATURE (Brownfield-Delta, doc-only). Sprint 10 / EPIC-003,
> WPs Q1 + Q2 + Q4. Es wird KEIN Produktiv-Code geändert — Output sind
> verifizierte Analyse-Dokumente.

## 1. Vision

Nach diesem Feature existiert eine belastbare, priorisierte Inventur
aller Bugs/Risiken in kochfabrik-studio und pptxgenerator_v2 sowie
eine Test-Baseline-Karte. EPIC-004 (Refactoring) und EPIC-010
(Härtung) arbeiten Findings ab statt neu zu suchen; R-REF-6
(„Verhalten strikt erhalten") bekommt sein Mess-Fundament.

## 3. Datenmodell (Finding-Format)

> Findings sind Markdown-Abschnitte mit festem Schema — greppbar,
> kein Fließtext-Brei.

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `string` | `F-S-{NN}` (Studio) / `F-E-{NN}` (Engine) — Überschrift `## F-S-01: …` |
| `severity` | `enum` | `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` |
| `beleg` | `string` | Datei:Zeile ODER Repro-Schritte — Zeile beginnt mit `**Beleg:**` |
| `zuordnung` | `string` | Epic/WP (z.B. `EPIC-004/M6`) ODER `VERWORFEN: {Grund}` — Zeile `**Zuordnung:**` |

## 4. Flow

```
Repo lesen (read-only) → Verdacht → Beleg erbringen (Code-Zeile/Repro)
  → verifiziert? ja: Finding mit Severity + Zuordnung
               → nein: VERWORFEN mit Grund (bleibt im Doc)
```

Bekannte Verdachts-Kandidaten (aus Ideation 2026-06-09, MÜSSEN
geprüft werden): Open Sans fehlt im Docker-Image · `SIZE_K=0.78`-
Widerspruch in `lib/text.js` · alembic.ini-Drift (rc=255) ·
pg_shim-Bypass der Slidesuche · `web/_legacy/`-Reste.

## 7. API-Skizze

Entfällt (doc-only).

## 8. Akzeptanzkriterien (EARS)

1. WHEN die Studio-Analyse abgeschlossen ist THE SYSTEM SHALL
   `docs/sprint-10/FINDINGS-STUDIO.md` liefern, in dem jeder Finding
   ID, Severity, `**Beleg:**`-Zeile und `**Zuordnung:**`-Zeile trägt.
2. WHEN die Engine-Analyse abgeschlossen ist THE SYSTEM SHALL
   `docs/sprint-10/FINDINGS-ENGINE.md` im selben Schema liefern und
   die 5 Verdachts-Kandidaten je als Finding oder VERWORFEN führen.
3. WHEN die Baseline-Inventur abgeschlossen ist THE SYSTEM SHALL
   `docs/sprint-10/TEST-BASELINE.md` liefern mit der realen
   Test-Anzahl (pytest-Collect), der Abdeckungs-Karte pro Modul und
   einer expliziten Lücken-Liste (Engine-Skripte).
4. IF ein Verdacht nicht belegbar ist THEN THE SYSTEM SHALL ihn als
   `VERWORFEN: {Grund}` dokumentieren statt ihn wegzulassen.

## 9. Abgrenzung (Nicht-Teil)

- Keine Fixes — auch keine „trivialen" (Analyse-Sprint, R-REF-6)
- Kein Font-Daten-Report (→ [[KOCHFABRIK-FEATURE-002]])

## 9a. Boundaries (3-Tier)

- ✅ **Always:** beide Repos read-only lesen; Docs unter
  `docs/sprint-10/` anlegen; pytest read-only ausführen (collect/run)
- ⚠️ **Ask-first:** jede Änderung außerhalb `docs/` und `tools/`;
  neue Dependency in `requirements.txt`
- 🚫 **Never:** `data/cache/` schreiben/löschen (R-NF-3); Fixes
  „nebenbei" einbauen; auf master pushen

## 10. Abgrenzung zum Ist

- Heute: Bugs anekdotisch bekannt (PROGRESS, Kommentare) → Soll:
  ein greppbares, priorisiertes Findings-Inventar mit Beleg-Pflicht.
- Heute: „111 Tests grün" als Pauschalaussage → Soll: Karte, WAS die
  Tests absichern und wo die Engine blank ist.

## 11. Implementierungs-Anker (Ist)

`backend/app.py` (939 Z., 3 Module gemischt), `backend/slidesuche.py`
(pgbundle-Direktzugriff), `backend/migrate.py` + `Dockerfile` CMD
(alembic-Drift), `web/_legacy/`, `backend/tests/test_*.py` (7 Dateien);
Engine: `pptxgenerator_v2/phase0/scripts/` (40+ Skripte),
`phase0/spike-pptxgenjs/lib/text.js` (SIZE_K), `phase0/spike-pptxgenjs/
extract.py`, `vendor.sh`.

## 12. Bekannte Pitfalls

1. **Finding ohne Beleg** — „sieht falsch aus" zählt nicht; jede
   Zeile Code zitieren oder Repro angeben, sonst VERWORFEN.
2. **Scope-Creep zum Fixen** — Analyse-Sprint; der Reflex „ist ja nur
   eine Zeile" bricht R-REF-6.
3. **Doppelzählung mit REQUIREMENTS-Befunden** — bekannte Kandidaten
   referenzieren, nicht als „neu entdeckt" verkaufen.

## Referenzen
- implements → REQUIREMENTS R-QA-1, R-QA-3, R-QA-4
- relates_to → [[EPIC-003]] WP Q1, Q2, Q4

## Referenziert von
— USER-STORIES Sprint 10 (US-036, US-037, US-040)
