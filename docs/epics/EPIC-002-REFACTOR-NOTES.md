# EPIC-002 Sprint 9 — Refactor Notes

Stand: 2026-05-20 (headless durchgezogen).

## Was wurde verschoben / entfernt

| Vorher | Nachher | Grund |
|--------|---------|-------|
| `web/praesentationsgenerator.html` | `web/_legacy/praesentationsgenerator.html` | Aus aktivem WEB-Mount-Pfad raus, FE-Seite ist nicht mehr unter `/praesentationsgenerator.html` erreichbar. Datei bleibt als historischer Anker + Rollback-Quelle. |

## Was bleibt unverändert (bewusst)

### Backend-Routes
`/api/praesentation/*` (alt) bleiben in `backend/app.py` registriert:
- `GET  /api/praesentation/health`
- `POST /api/praesentation/generate`
- `POST /api/praesentation/from-angebot`
- `POST /api/praesentation/from-pdf`

**Begründung:** Rollback-Fähigkeit. Falls v2 in Produktion ein Problem
zeigt, kann der alte FE-View aus `_legacy/` einfach zurückgeholt werden
und nutzt die Backend-Routes unverändert weiter.

### chat.html → /api/praesentation/from-angebot
Der „→ Präsentation"-Button in `chat.html` (Angebotsgenerator) ruft
immer noch den alten Backend-Endpoint. Das ist funktional und stört
v2 nicht. Wenn v2 stabil läuft und PPTX-Generierung produktiv ist,
kann dieser Button auf `/api/praesentation_v2/generate/{offer_id}`
umgestellt werden — nicht in dieser Nacht-Session.

## Shared-Code-Analyse

Erwartet hatte das Epic „Shared-Code in Module ziehen". Inspektion:

| Bereich | Alt | v2 | Shared? |
|---------|-----|-----|--------|
| Backend-Endpoint-Logik | `_assemble_md`, `_ang2md` (app.py) | eigener Router + Store | **Nein.** Verschiedene Use Cases. |
| Engine-Anbindung | `engine.assemble` (PDF→Deck) | (Sprint 7+ noch nicht angeschlossen) | **Nein.** v2 wird eigenständige Render-Pipeline. |
| FE-Code | single-page-vanilla in `praesentationsgenerator.html` | strukturiert mit Modul-File `editor.js` | **Nein.** Keine wiederverwendbaren Komponenten. |
| Auth/Cookie | `_owner` (app.py) | gleicher `_owner` (via late-import) | **Bereits shared.** Keine Aktion nötig. |

**Ergebnis:** Kein nennenswerter Shared-Code identifiziert. Beide
Generatoren bleiben eigenständig. Das ist Architektur-konform mit dem
Epic-Ziel „Schneidbarkeit" — minimaler Kopplungsgrad.

## Sprint-9-Verfeinerungs-Backlog (nicht in dieser Session)

- chat.html-Button auf `/api/praesentation_v2/generate/{offer_id}`
  umstellen wenn v2-Render produktiv (Sprint 7-Stub heute noch nicht
  ausreichend)
- Echtes PPTX-Render in v2 (Sprint 7-Stub → LibreOffice-Pipeline)
- `/api/praesentation/*` Backend-Routes nach Auslauffrist deprecaten
  + entfernen (frühestens nach 2-4 Wochen produktivem v2-Lauf)
- `web/_legacy/` aus Repo entfernen wenn 100% Sicherheit besteht
- alembic.ini ins Repo (Tech-Debt aus Sprint 5: alembic upgrade head
  läuft seit Sprint 1 graceful auf rc=255)
