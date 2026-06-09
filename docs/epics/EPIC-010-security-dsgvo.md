---
id: EPIC-010
title: "Security & DSGVO-Light: Härtung + Kosten-Schutz + Compliance-Basics"
status: OPEN
created: 2026-06-09
project: kochfabrik-studio
sprints: []
---

# EPIC-010: Security & DSGVO-Light

> **Typ:** EPIC. Klammer über Sprints — kein Detail-Spec. `/sprint-plan`
> schneidet die WPs in Stories. Status: `OPEN → IN_PROGRESS → DONE`.

## Beschreibung

Die App hält PII (Kunden, Angebote, Chat-Verläufe) hinter einer
HMAC-Cookie-Auth mit Env-Usern und ruft kostenpflichtige LLM-APIs
(Gemini, Anthropic) ohne Rate-Limits auf — ein offener
Kosten-Runaway- und Missbrauchs-Vektor. Für ein Kunden-Tool fehlen
zudem die DSGVO-Basics (Verantwortlichkeits-Klärung, AVV,
Datenschutz-Seiten).

Bewusst „light": Die konkreten Härtungs-Findings liefert die
Bug-Analyse (EPIC-003/Q1) — dieses Epic bündelt deren Fixes plus die
Compliance-Pflichten. Kein Security-Theater, keine RBAC-Suite.

## Scope

### Was drin ist

- **H1** Rate-Limits/Usage-Caps auf den LLM-Endpoints (Bildgenerator,
  Angebots-Chat, Präsentations-Chat) — pro User + global
- **H2** Secrets-Audit: alle Keys nur via Env/Coolify-Secrets, keine
  Secrets in Repo/Logs; Rotation dokumentiert
- **H3** Auth-Härtung gemäß Q1-Findings (Cookie-Attribute,
  Session-Laufzeit, Login-Bruteforce-Schutz)
- **H4** DSGVO-Basics: PII-Inventar, Datenschutz/Impressum-Seiten,
  AVV-Klärung. ❓ Verantwortlichkeit AKARA vs. KOCHfabrik klären
  (bestimmt, wessen Impressum/AVV gilt)

### Was NICHT drin ist

- RBAC/Rollenmodell — Tenant-Isolation aus EPIC-001 reicht
- Pen-Test/externes Audit — bei Bedarf später
- Vollständiges DSGVO-Programm (Löschkonzept-Automation etc.) —
  erst wenn das Tool über den internen Kreis hinaus wächst

## Sprint-Zuordnung (grob)

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 16 | H1–H4 (Input: Q1-Findings) | M |

> **Fortschritt:** wird von /sprint-review aktualisiert.

## Akzeptanzkriterien

1. LLM-Endpoints lehnen Anfragen jenseits der Limits nachweisbar ab
   (Test); ein Kosten-Runaway durch einen einzelnen User ist gekappt.
2. Secrets-Audit dokumentiert: kein Secret im Repo/Image/Log;
   Rotation beschrieben.
3. Q1-Security-Findings sind gefixt oder begründet akzeptiert
   (Risk-Log).
4. Datenschutz/Impressum erreichbar, PII-Inventar liegt vor,
   Verantwortlichkeits-/AVV-Frage ist entschieden und dokumentiert.

## Referenzen

- **REQUIREMENTS:** R-SEC-1, R-SEC-2, R-SEC-3, R-SEC-4 (❓ AVV)
- **Audit:** [[TRACEABILITY]] → WP H1–H4

## Abhängigkeiten

Blockiert von: EPIC-003/Q1 (Findings als Input). Blockiert: nichts —
kann parallel zu EPIC-005/006 laufen, sobald Q1 vorliegt.
