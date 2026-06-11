# USER-STORIES — kochfabrik Sprint 13

> **Typ:** US. Feature-getrieben (Jan 2026-06-11: „Präsentationsdesigner —
> Angebot hochladen, Vorschläge für Slides, Kombination aus Suche und
> Präsentationserstellung") = [[EPIC-006]] D1–D3 + D6. Dazu US-068 aus
> dem Korpus-Mount-Incident (Gate-Lücke). EPIC-007/008 → Sprint 14.

## Story-Gate (PFLICHT)

- [x] ≤ 5 Task-Schritte · ≤ 3 Output-Einträge · Verify deterministisch
- [x] Verify bildet ein EARS-Kriterium ab · Null Platzhalter
- [x] Blocked-by explizit · Trace vorhanden

## Boundaries (sprintweit)

- ✅ **Always:** Feature-Branches; neuer Router/neue Seite nach
  bestehendem Muster; venv-Tests; Gemini-embed in Tests MOCKEN;
  Sim-Gate lokal
- ⚠️ **Ask-first (headless → BLOCKED):** Logik-Änderungen an
  assemble/compose_offer; neue Dependencies (Python ODER JS/CDN);
  Änderungen bestehender Seiten jenseits 1 Nav-Zeile; schreibende
  Server-/Coolify-Calls außer in US-068 explizit genannt
- 🚫 **Never:** master pushen; eigenes np.load/ANN (bundle.py-Regel);
  pgbundle/cache schreiben; echte Gemini-Calls in Suite/CI;
  bestehende Slidesuche-/Generator-Flows umbauen

---

## Phase 1 (Wave 1 — parallel)

### US-061: Designer-Router + Angebots-Parsing-Wrapper

**Context:** D6 braucht einen Endpoint, der ein Angebot (PDF/DB/JSON)
in geparste Gänge+Meta überführt — mit den BESTEHENDEN
Engine-Funktionen, ohne assemble-Logik zu ändern.

**Input (Vorbedingungen):**
- Anker: `backend/routers/praesentation.py` (from-pdf-Upload-Muster),
  `backend/engine_glue.py:340-347` (`_ang2md`; Nutzungs-Muster praesentation.py:95-105), `backend/routers/angebot.py:311` (Offer-by-id),
  `engine/scripts/compose_offer.py` (parse_offer_dishes),
  `engine/scripts/assemble.py` (parse_header)

**Task:**
1. TDD: `backend/tests/test_sprint13.py` anlegen — TestClient-Tests: designer/health-Shape; suggest ohne Auth → 401; suggest mit ungültigem Body → 400/422; suggest mit gemocktem Parsing/Embed → Response-Schema (§3) — rot
2. `backend/routers/designer.py`: `GET /api/designer/health` ({engine, korpus, embed}) + `POST /api/designer/suggest` — Input-Zweige: multipart PDF (%PDF-Magic, 25-MB-Limit wie from-pdf), `{offer_id}` (Offer laden wie /api/angebot/{offer_id} → _ang2md), `{offer}` (JSON direkt)
3. Parsing-Wrapper: Angebot → `{kunde, datum, gaenge[]}` via parse_header/parse_offer_dishes (Import via engine_glue-Muster); Ranking-Teil als Stub (`groups: []`) — kommt in US-062
4. include_router in app.py (eine additive Zeile); Suite 0 failed

**Output:**
- `backend/routers/designer.py`
- `backend/tests/test_sprint13.py`
- `backend/app.py` (+1 include-Zeile)

**Verify:** (EARS 2+3 aus FEATURE-011, Parsing-Teil)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint13.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q "designer" backend/app.py
```

**Trace:** R-DECK-4 (D6) · WP D6 · [[KOCHFABRIK-FEATURE-011]]
**Blocked-by:** —

---

### US-063: Designer-Seite Grundgerüst + Navigation

**Context:** Die Designer-UI braucht das Seiten-Skelett im
Design-2-Muster, bevor Interaktion verdrahtet wird.

**Input (Vorbedingungen):**
- Anker: `web/bibliothek.html` (Gerüst), `web/assets/style.css`
  (Design-2-Klassen), Nav-Struktur der bestehenden Seiten

**Task:**
1. `web/designer.html`: Sidebar (kanonisch) + 3-Bereichs-Layout (Quelle+Suche links, Vorschläge Mitte, Storyboard rechts) — statisches Gerüst mit Markern (`id="designer-source"`, `id="designer-groups"`, `id="designer-board"`)
2. `web/assets/designer.js`: Modul-Skelett (State `kfDesigner.v1`, API-Wrapper-Stubs, 401→Login-Redirect wie chat.html)
3. GENAU EINE Nav-Link-Zeile in den bestehenden Seiten ergänzen (alle Design-2-Seiten mit Sidebar — konsistent, je 1 additive Zeile)
4. FE-Smoke in NEUER Datei `backend/tests/test_sprint13_fe.py` (UI-Ketten-Testdatei — getrennt von test_sprint13.py der API-Kette!): designer.html wird ausgeliefert (200, Marker vorhanden), designer.js erreichbar

**Output:**
- `web/designer.html`, `web/assets/designer.js`
- `backend/tests/test_sprint13_fe.py` (+ `web/*.html` je 1 additive Nav-Zeile)

**Verify:** (EARS-Vorstufe zu FEATURE-012 Nr. 1; Auslieferung)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint13_fe.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q 'designer-board' web/designer.html && grep -q 'kfDesigner.v1' web/assets/designer.js && \
test "$(grep -l 'designer.html' web/*.html | wc -l | tr -d ' ')" -ge 5
```

**Trace:** R-DECK-1 · WP D1 · [[KOCHFABRIK-FEATURE-012]]
**Blocked-by:** —

---

### US-068: live_verify Deep-Check (Incident-Nacharbeit)

**Context:** Der Korpus-Mount-Incident (2026-06-11) blieb unsichtbar,
weil live_verify nur 401 sieht und Sim-Gate korpus:false als graceful
wertet. Ein authentifizierter Deep-Check schließt die Lücke.

**Input (Vorbedingungen):**
- `tools/live_verify.sh`; SSH `~/.ssh/hetzner_id root@188.245.110.5`;
  In-Container-Muster: `docker exec <app> python3 -c "make_cookie(<KF_USERS-User>) → /api/praesentation/health"`

**Task:**
1. `tools/live_verify.sh`: optionaler Block `LIVE_DEEP=1` — via SSH+docker exec im Prod-Container Cookie für den ersten KF_USERS-User minten und `praesentation/health` + `angebot/health` abfragen; FAIL wenn `korpus` nicht true oder `engine` nicht true
2. Standard-Lauf (ohne Env) bleibt byte-identisch; kein `timeout`-Binary
3. `LIVE_DEEP=1 ./tools/live_verify.sh` gegen Prod ausführen — grün (Korpus ist seit dem Fix gemountet)
4. CUTOVER-RUNBOOK: Post-Cutover-Schritt um `LIVE_DEEP=1` ergänzen + Incident als Referenz (1 Absatz, minimal-invasiv)

**Output:**
- `tools/live_verify.sh` (Deep-Block)
- `docs/sprint-11/CUTOVER-RUNBOOK.md` (E8.0-konforme Ergänzung)

**Verify:** (neues Kriterium: Gate-Lücke geschlossen)
```bash
grep -q 'LIVE_DEEP' tools/live_verify.sh && ! grep -qw 'timeout' tools/live_verify.sh && \
./tools/live_verify.sh && LIVE_DEEP=1 ./tools/live_verify.sh && \
grep -q 'LIVE_DEEP' docs/sprint-11/CUTOVER-RUNBOOK.md
```

**Trace:** R-NF-2 · Incident 2026-06-11 (Korpus-Mount) · [[KOCHFABRIK-FEATURE-005]]-Nachtrag
**Blocked-by:** —

---

## Phase 2 (nach Wave 1)

### US-062: Vorschlags-Ranking (Top-N je Gang + Pflicht-Gruppe)

**Context:** Das Herz von D6 — die Generator-Bausteine liefern
Kandidaten statt fertigem Deck.

**Input (Vorbedingungen):**
- US-061 DONE; Anker: `compose_offer.embed` (Gemini-Batch),
  `bundle.rank`, `pg_shim`/static_slide (pick_frame-Shape),
  Preview-Route `/api/slidesuche/preview/{deck}/{page}.png`

**Task:**
1. TDD erweitern: suggest mit gemocktem embed → groups: je Gang Top-5-Kandidaten (deck/page/score/preview/label) + pflicht-Gruppe; 503-Pfad ohne Korpus — rot
2. Ranking in designer.py: 1 embed-Batch über alle Gänge → je Gang `bundle.rank(qv, idx_menu, k=5)` (gleiche Index-Menge wie assemble: menu_composition-Slides); Score mitliefern
3. Pflicht-Gruppe: static_slide-Kandidaten (is_golden/pflicht) wie pick_frame — als eigene Gruppe `kind=pflicht`
4. preview-URLs aus deck/page bauen (bestehende Route); Suite 0 failed + Live-Smoke dokumentieren (1 echter suggest-Call lokal mit Key — Output-Auszug in Story-Meldung, NICHT in Tests)

**Output:**
- `backend/routers/designer.py` (Ranking komplett)
- `backend/tests/test_sprint13.py` (erweitert)

**Verify:** (EARS 1+4 aus FEATURE-011)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint13.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
! grep -E "np\.load" backend/routers/designer.py && \
grep -q "bundle" backend/routers/designer.py
```

**Trace:** R-DECK-4 (D6) · WP D6 · [[KOCHFABRIK-FEATURE-011]] · [[KOCHFABRIK-ADR-003]]
**Blocked-by:** US-061

---

### US-064: Quelle + Vorschlags-Karten verdrahten

**Context:** Upload/Angebots-Auswahl → suggest → klickbare Karten.

**Input (Vorbedingungen):**
- US-062 + US-063 DONE; `GET /api/angebote` (Liste), fetch-Muster chat.html

**Task:**
1. designer.js: Quelle-Panel — PDF-Upload (FormData) + Dropdown gespeicherter Angebote (GET /api/angebote) → suggest-Call, Lade-/Fehlerzustände (503-Korpus-Hinweis)
2. Vorschlags-Gruppen rendern: Spalte je Gruppe, Karte = PNG (`onerror`→Platzhalter), Label, Score; Klick → Storyboard-Add (Event an Board-Modul) + „im Deck"-Markierung
3. FE-Smoke in test_sprint13_fe.py erweitern: Marker für Upload-Input, Dropdown, Gruppen-Container; designer.js enthält suggest-/angebote-Endpoints

**Output:**
- `web/assets/designer.js`
- `web/designer.html` (Panel-Marker)
- `backend/tests/test_sprint13_fe.py` (FE-Smoke)

**Verify:** (EARS 1+5 aus FEATURE-012)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint13_fe.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q '/api/designer/suggest' web/assets/designer.js && \
grep -q '/api/angebote' web/assets/designer.js && \
grep -qi 'placeholder\|platzhalter' web/assets/designer.js
```

**Trace:** R-DECK-1, R-DECK-4 · WP D1+D6 · [[KOCHFABRIK-FEATURE-012]]
**Blocked-by:** US-062, US-065

---

### US-065: Storyboard (Reorder, Remove, Session-Persistenz)

**Context:** D1+D2 — das kuratierbare Arbeits-Deck.

**Input (Vorbedingungen):**
- US-063 DONE (Board-Container + State-Skelett)

**Task:**
1. designer.js Board-Modul: Add (aus Karten-Klick), Thumbnails in Reihenfolge, ↑/↓-Buttons, Entfernen, Zähler; Duplikat-Schutz (gleiche deck/page nur 1×)
2. Persistenz: Zustand als `kfDesigner.v1` in sessionStorage bei jeder Änderung; Restore beim Laden (inkl. Preview-URLs)
3. FE-Smoke in test_sprint13_fe.py: Marker für Board-Funktionen (sessionStorage-Key, Reorder-Handler) in designer.js

**Output:**
- `web/assets/designer.js`
- `backend/tests/test_sprint13_fe.py` (FE-Smoke)

**Verify:** (EARS 3 aus FEATURE-012)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint13_fe.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q "sessionStorage" web/assets/designer.js && \
grep -q "kfDesigner.v1" web/assets/designer.js
```

**Trace:** R-DECK-1, R-DECK-2 · WP D1+D2 · [[KOCHFABRIK-FEATURE-012]]
**Blocked-by:** US-063

---

### US-066: Freitext-Suche im Designer

**Context:** Die „Kombination aus Suche und Präsentationserstellung" —
Slidesuche-Treffer landen im selben Storyboard.

**Input (Vorbedingungen):**
- US-063 + US-065 DONE; `POST /api/slidesuche/search` (Top-5-Shape aus backend/slidesuche.py)

**Task:**
1. designer.js: Suche-Panel (Input + Button/Enter) → search-Call → Treffer-Karten im selben Karten-Format wie Vorschläge (gemeinsame Render-Funktion), Klick → Storyboard
2. Leere-Treffer-/Fehler-Zustand; Suche koexistiert mit Vorschlags-Gruppen (eigener Bereich, ersetzt sie nicht)
3. FE-Smoke in test_sprint13_fe.py: search-Endpoint in designer.js, Such-Panel-Marker in designer.html

**Output:**
- `web/assets/designer.js`
- `web/designer.html` (Such-Panel)
- `backend/tests/test_sprint13_fe.py` (FE-Smoke)

**Verify:** (EARS 2 aus FEATURE-012)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint13_fe.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q '/api/slidesuche/search' web/assets/designer.js
```

**Trace:** R-DECK-1 · WP D1+D6 · [[KOCHFABRIK-FEATURE-012]]
**Blocked-by:** US-064

---

## Phase 3 (Abschluss)

### US-067: Download + End-to-End-Beweis

**Context:** D3 — aus dem Storyboard wird die PPTX; plus der
End-to-End-Beweis über den ganzen Designer-Flow.

**Input (Vorbedingungen):**
- US-064 + US-065 + US-066 DONE; `POST /api/slidesuche/download`

**Task:**
1. designer.js: Download-Button → download-Call mit Storyboard-Liste → PPTX speichern (bestehendes Data-URL-Muster); disabled bei leerem Board
2. E2E-TestClient-Test in test_sprint13_fe.py: suggest (gemockt) → Kandidaten in Download-Liste → download → Response ist PPTX (Magic-Bytes PK + Größe >10 KB; nutzt die 2 committeten Cache-Decks!)
3. Lokaler Live-Smoke des Gesamtflows (mit Key + lokalem Cache): dokumentierter Durchlauf in der Story-Meldung
4. Suite komplett 0 failed + Sim-Gate grün (neue Route lebt im Container)

**Output:**
- `web/assets/designer.js`
- `backend/tests/test_sprint13_fe.py` (E2E)

**Verify:** (EARS 4 aus FEATURE-012 + EARS 1 aus FEATURE-011 e2e)
```bash
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q '/api/slidesuche/download' web/assets/designer.js && \
./tools/sim_gate.sh
```

**Trace:** R-DECK-3 · WP D3 · [[KOCHFABRIK-FEATURE-012]]
**Blocked-by:** US-066

---

## Dependency Graph

```
API-Kette:  US-061 ─▶ US-062 ─────────┐
UI-Kette:   US-063 ─▶ US-065 ─▶ US-064 ─▶ US-066 ─▶ US-067
US-068 (unabhängig, Wave 1)
```

> US-063→US-067 = sequentielle UI-Kette auf EINEM Branch (alle ändern
> web/assets/designer.js + test_sprint13.py-FE-Teil — bewusst kein
> Parallel-Gewürge, Sprint-11/12-Muster). API-Kette parallel dazu auf
> eigenem Branch; US-064 stackt die API-Kette ein (Lead-Merge).

## Summary

| Phase | Stories | Parallelisierbar | Kritischer Pfad |
|---|---|---|---|
| Wave 1 | US-061 (API-Kette), US-063 (UI-Kette), US-068 | ja (3 parallel) | beide Ketten |
| Ketten | API: US-062 · UI: US-065→064→066→067 | 2 Ketten parallel | UI-Kette |
| **Total** | **8 Stories** | 3 Stränge | |
