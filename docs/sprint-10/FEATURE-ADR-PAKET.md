---
key: KOCHFABRIK-FEATURE-003
status: implemented
title: "ADR-Paket: Embedding, Monorepo-Schnitt, pgbundle vs. Postgres"
created: 2026-06-09
project: kochfabrik
---

# KOCHFABRIK-FEATURE-003: ADR-Paket (Entscheidungen)

> **Typ:** FEATURE (doc-only). Sprint 10 / EPIC-003, WP Q5. Drei
> Entscheidungsvorlagen als ADRs (Format: TEMPLATE-ADR aus
> `~/work/99 Jan/templates/`). Finale Abnahme durch Jan — die ADRs
> entstehen mit `status: proposed` und klarer Empfehlung
> (ADR-Lifecycle: proposed → accepted).

## 1. Vision

Die drei Grundsatzfragen, die EPIC-004/005 blockieren, liegen als
entscheidbare Vorlagen vor: je Optionen, Trade-offs, Empfehlung,
Konsequenzen. Jan entscheidet auf Substanz statt im Chat-Verlauf.

## 3. Datenmodell (ADR-Inhalt)

| ADR | Frage | Entscheidet über |
|---|---|---|
| `docs/adr/ADR-001-pptx-font-embedding.md` | Server-Render-Treue vs. PPTX-Embedding für Kunden-Rechner | Scope von EPIC-005 (Folge-Epic ja/nein) — R-FONT-6 |
| `docs/adr/ADR-002-monorepo-schnitt.md` | Repo-Name, Verzeichnis-Layout, Historie-Erhalt, Schicksal der Alt-Ordner (`praesentationsgenerator/`, `poc/`, `_bak/`, `DEPRECATED-*`, `*.bak-*`, `imagetagging/`), Coolify-Migrationsplan | EPIC-004/M1–M3 — R-REF-1, R-NF-2 |
| `docs/adr/ADR-003-pgbundle-vs-postgres.md` | pgbundle.npz-Shim beibehalten vs. echtes Postgres für Engine-Queries | Folge-Epic ja/nein — R-REF-3 |

## 4. Flow

```
Findings (Q1/Q2) + Font-Daten (Q3) lesen → Optionen + Trade-offs
→ Empfehlung mit Begründung → ADR (status: review) → Jan entscheidet
→ status: approved (außerhalb dieses Sprints)
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN ein ADR erstellt ist THE SYSTEM SHALL Kontext, mindestens
   2 Optionen mit Trade-offs, eine begründete Empfehlung und
   Konsequenzen enthalten — ohne `{…}`-Platzhalter.
2. THE SYSTEM SHALL jeden ADR mit Frontmatter `status: proposed`
   anlegen (Abnahme = Jans Entscheidung, nicht Teil des Sprints).
3. IF eine Entscheidung Input aus Q1–Q3 braucht THEN THE SYSTEM
   SHALL die konkreten Findings/Zahlen referenzieren statt abstrakt
   zu argumentieren.

## 9. Abgrenzung (Nicht-Teil)

- Keine Umsetzung der Entscheidungen (→ EPIC-004/005/Folge-Epics)
- Keine vierte Entscheidung „nebenbei" — neue ❓ gehen in
  REQUIREMENTS §7

## 9a. Boundaries (3-Tier)

- ✅ **Always:** `docs/adr/` anlegen; TEMPLATE-ADR lesen; Findings/
  Report aus Sprint 10 zitieren
- ⚠️ **Ask-first:** ADR-Empfehlung, die ein Epic-Scope sprengt
  (z.B. „Postgres-Umbau sofort") — als Option dokumentieren, nicht
  als Empfehlung setzen ohne Rückfrage
- 🚫 **Never:** `status: approved` selbst setzen

## 11. Implementierungs-Anker (Ist)

Input: `docs/sprint-10/FINDINGS-{STUDIO,ENGINE}.md`,
`docs/sprint-10/font-report.json` + `FONT-REPORT.md`,
`vendor.sh` (Vendoring-Ist), `backend/slidesuche.py` +
`phase0/scripts/pg_shim.py` (pgbundle-Ist), README.md §Engine-Sync.

## 12. Bekannte Pitfalls

1. **Empfehlung ohne Zahlen** — ADR-001 ohne Font-Report-Daten ist
   Bauchgefühl; erst Q3 lesen.
2. **Monorepo-ADR vergisst das Deploy** — Coolify zieht von GitHub
   master; der Migrationsplan gehört IN die Entscheidung (R-NF-2).

## Referenzen
- implements → REQUIREMENTS R-REF-1 (❓), R-REF-3, R-FONT-6 (❓), R-NF-2
- relates_to → [[EPIC-003]] WP Q5; entsperrt [[EPIC-004]], [[EPIC-005]]

## Referenziert von
— USER-STORIES Sprint 10 (US-041, US-042, US-043)
