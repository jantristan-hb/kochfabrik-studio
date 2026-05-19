---
id: EPIC-002
title: "WYSIWYG-Präsentationsgenerator v2 (parallel zum bestehenden)"
status: OPEN
created: 2026-05-20
project: kochfabrik-studio
sprints: [5, 6, 7, 8, 9]
---

# EPIC-002: WYSIWYG-Präsentationsgenerator v2

## Beschreibung

Zweiter Präsentationsgenerator parallel zum bestehenden, mit Live-WYSIWYG-
Editor: Slides editierbar **bevor** die PPTX erstellt wird. UX-Pattern wie
Angebotsgenerator (Drei-Spalten-Editor: Chat links, Live-Edit-Form mitte,
3–4 Slide-Vorschläge mit Realtime-PPTX-Preview rechts). Pro Slide werden
3–4 DB-Treffer aus den 7 Kategorien (Food, Deckblatt, Location, Ausstattung,
Goldschätzchen, KOCHfabrik, Freitext) angeboten. Slide-Auswahl persistiert
auf `offer_id` — angezeigte Präsentationen MÜSSEN zum verknüpften Angebot
passen (Kunde, Veranstaltung, Konzept, Block-Themen).

Strategie: Sicherheits-First. Alter Generator (`/api/praesentation/*` +
`web/praesentationsgenerator.html`) bleibt während der Bauphase voll
funktionsfähig. Neuer Generator wird parallel auf eigenem Pfad gebaut.
Erst wenn stabil: alten FE ausblenden (Backend bleibt aktiv → Rollback).
Refactor (alten Code rausschneiden) erst wenn alles entspannt läuft.

## Scope

### Was drin ist
- Backend-Routes `/api/praesentation_v2/*` (parallel)
- Frontend `web/praesentation_v2/` (eigener Editor, eigene Templates)
- Additive DB-Tabellen für Slide-Auswahl pro `offer_id`
- 3–4 DB-Vorschläge pro Slide aus den 7 Kategorien
- Realtime-PPTX-Preview-Rendering (gerne aggressiv gecacht)
- Live-Edit-Form mit gefühlter Echtzeit (< ~150ms optische Latenz)
- Kohärenz-Layer: Präsentation ↔ Angebot (offer_id-Scope)
- Switch im FE: neuer Generator als Default, alter ausgeblendet
- Refactor: alten FE-Code entfernen, Shared-Code modularisieren

### Was NICHT drin ist (Non-Goals — NICHT ANFASSEN)
- `/api/angebot/*` Endpoints — bleiben bit-identisch (Snapshot-Smoke vor+nach)
- `backend/store.py` Offer-Persistenz
- `backend/numbering.py` atomare Sequenzen
- Engine `angebot_*.py` (positions/fill/model/render)
- DB-Schema `kf-studio-pg`: NUR additive Migrationen, KEIN DROP/TRUNCATE/destruktives ALTER
- Bestehende Test-Suite (Engine 57 + Studio 47 = 104 Tests) — muss grün bleiben

## Sprint-Zuordnung

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 5 | Backend-Skelett `/api/praesentation_v2/*` + additive DB-Migration (Tabellen für Slide-Vorschläge + Slide-Auswahl-Persistenz) | L |
| Sprint 6 | Frontend Drei-Spalten-Editor (Chat / Live-Edit / Slide-Vorschau), 3–4 DB-Treffer je Slide | L |
| Sprint 7 | Realtime-PPTX-Preview-Cache + Kohärenz-Layer (Angebot ↔ Präsentation) | M |
| Sprint 8 | Frontend-Switch: v2 als Default, alter Generator FE ausgeblendet (Backend bleibt) | S |
| Sprint 9 | Refactor: alten FE-Code raus, Shared-Code modularisieren | M |

> Sprint-Zuordnung ist grob. Details bestimmt `/sprint-plan`.

## Akzeptanzkriterien

1. Neuer Generator unter eigenem Pfad erreichbar, alter parallel weiter erreichbar (bis Sprint 8)
2. Drei-Spalten-Editor (Chat / Live-Edit-Form / Slide-Vorschau) je Slide funktional
3. 3–4 DB-Vorschläge je Slide mit Realtime-PPTX-Preview (cache-gestützt)
4. Slide-Auswahl persistiert pro `offer_id` (additive DB-Tabelle)
5. Generierte Präsentation matched das verknüpfte Angebot (Kunde, Datum, Konzept, Block-Themen)
6. Smoke-Diff: `/api/angebot/*`-Responses bit-identisch zu pre-Epic-Snapshot
7. Bestehende Tests grün, neue Tests für v2-Module
8. Nach Sprint 8: v2 = Default-Route im FE, alter Generator im FE versteckt
9. Nach Sprint 9: alter FE-Code entfernt, Shared-Code in Modulen

## Fortschritt

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 5 | Backend-Skelett v2 + additive DB-Migration | ✅ DONE (master 7df66f1) |
| Sprint 6 | Frontend Drei-Spalten-Editor + DB-Vorschläge | ⏳ TODO |
| Sprint 7 | Realtime-Preview-Cache + Kohärenz-Layer | ⏳ TODO |
| Sprint 8 | Frontend-Switch (v2 = Default) | ⏳ TODO |
| Sprint 9 | Refactor (alten Code raus) | ⏳ TODO |
