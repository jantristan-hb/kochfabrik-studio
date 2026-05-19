# Epic-Prompt — WYSIWYG-Präsentationsgenerator v2

Brain-Dump enriched + sortiert, ready für morgen früh `/epic … kochfabrik-studio`.

---

## Vorhaben

Zweiter Präsentationsgenerator parallel zum bestehenden, mit WYSIWYG-Live-Editor: Slides editierbar **bevor** die PPTX erstellt wird (UX-Pattern wie Angebotsgenerator: Chat + Form + Preview).

## UI/UX — Drei-Spalten-Editor je Slide

- **Links**: Chatbot — unterstützt beim Editieren (Pattern wie `/api/angebot/chat`)
- **Mitte**: Texteingabefelder mit Live-Edit-Feedback. Der User muss nur das **Gefühl** haben dass er live editiert — Render läuft im Hintergrund, gerne aggressiv gecacht. Optische Latenz < ~150ms ist Ziel, echte Pixel-Updates dürfen lazy nachkommen.
- **Rechts**: 3–4 Slide-Vorschläge pro Slot mit Realtime-PPTX-Preview, klickbar zur Auswahl

## Datenquelle

- 3–4 Vorschläge pro Slide aus `kf-studio-pg` (bestehende Cache-Decks / Slide-Komponenten der 7 Kategorien: Food, Deckblatt, Location, Ausstattung, Goldschätzchen, KOCHfabrik, Freitext)
- Kohärenz-Pflicht: angezeigte Präsentationen MÜSSEN zum aktuell gewählten Angebot passen (gleicher `offer_id`-Scope, gleiche Kunde/Veranstaltung/Konzept/Blöcke)

## Vorgehensweise — 3 Phasen

| Phase | Wann | Was |
|-------|------|-----|
| **1. Kopie** | morgen (Mo, 21.05.) | Neuer Generator parallel zum alten — eigene Route, eigene Templates, eigene FE-Komponenten. Alter Generator bleibt vollständig erreichbar. |
| **2. Switch** | Di+ | Alter Generator im Frontend ausgeblendet (Backend-Route bleibt erreichbar → Rollback-fähig). |
| **3. Refactor** | nächste Woche, entspannt | Alten Code aus FE rausschneiden, Shared-Code in Module ziehen. |

## Harte Non-Goals — NICHT anfassen

- `/api/angebot/*` Endpoints — bleiben bit-identisch (Snapshot-Smoketest vor + nach Epic)
- `backend/store.py` Offer-Persistenz
- `backend/numbering.py` atomare Sequenzen
- Engine `angebot_*.py` (positions/fill/model/render)
- **DB-Schema `kf-studio-pg`** — NUR additive Migrationen (CREATE/ADD COLUMN NULL); KEIN DROP / TRUNCATE / DESTRUCTIVE ALTER
- Bestehende Tests müssen ALLE grün bleiben (Engine 57 + Studio 47 = 104)

## Architektur-Constraint (Schneidbarkeit)

Code so strukturieren dass der ALTE Präsentationsgenerator später ohne Risiko aus dem Frontend rausgeschnitten werden kann:

- Eigener Frontend-Ordner: `web/praesentation_v2/` (oder analog)
- Eigene API-Route: `/api/praesentation_v2/*`
- Keine Cross-Mutation zwischen alt und neu — beide lesen optional dieselbe DB, schreiben in eigene Tabellen falls Datenmodell abweicht
- Slide-Auswahl persistiert auf `offer_id` in NEUER Tabelle (additive Migration)

## Akzeptanzkriterien

1. Neuer Generator unter eigenem Pfad erreichbar, alter parallel weiter erreichbar
2. 3-Spalten-Editor (Chat / Live-Edit / Slide-Vorschau) je Slide funktional
3. 3–4 DB-Vorschläge je Slide mit Realtime-PPTX-Preview (gerne gecacht)
4. Slide-Auswahl persistiert pro Angebot
5. Generierte Präsentation matched das verknüpfte Angebot (Kunde, Datum, Konzept, Block-Themen)
6. Smoke-Diff: `/api/angebot/*`-Responses bit-identisch zu pre-Epic-Snapshot
7. Alle bestehenden Tests grün, neue Tests für v2-Module

## Recycling-Quellen (Inspiration, kein Mutationsverbund)

- `/api/angebot/chat` → Pattern für Editor-Chatbot
- `web/chat.html` → 3-Spalten-Layout
- Engine `angebot_*.py` → Modell-/Render-Pipeline-Pattern
- Bestehende Cache-Deck-Logik → Realtime-Slide-Renders

## Sicherheit

- **Headless-Implementierung** (Epic-Skill mit "A) Headless starten")
- **Kein interaktives Nachfragen** während des Sprint-Loops
- **DB-Schutz**: vor jeder Migration `pg_dump kf-studio-pg` als Backup; nur additive Migrationen committen
- **Branch-Disziplin**: jede Story auf eigenem Feature-Branch, Draft MR, kein Merge ohne Approval

## Skill-Aufruf morgen

```
/epic "WYSIWYG-Präsentationsgenerator v2: parallel zum bestehenden, Drei-Spalten-Editor (Chat links, Live-Edit-Form mitte, 3-4 Slide-Vorschläge mit Realtime-PPTX-Preview rechts), 3-4 DB-Treffer je Slide aus den 7 Kategorien, Slide-Auswahl persistiert auf offer_id. Kohärenz zum verknüpften Angebot Pflicht. Phasenplan: (1) heute Kopie parallel bauen, (2) alten FE-Generator ausblenden, (3) nächste Woche refactoren. Non-Goals: /api/angebot/*, store.py, numbering.py, Engine angebot_*.py, destruktive DB-Migrationen. Headless durchziehen." kochfabrik-studio
```
