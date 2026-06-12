# USER-STORIES — kochfabrik Sprint 14

> **Typ:** US. Feature-getrieben (Jan 2026-06-12: Präsentations-Wizard —
> ein Schritt pro Slide, 3-4 Alternativen, Overlay-Editing auf
> textfreien Renders, bildbewusstes Ranking, Bild-Overrides,
> Formulieren). Vertragsbezug 2026-001 §3.2. CI/Treue → Sprint 15
> (Seed verschoben: docs/sprint-15/FEATURE-CI-DELIVERY.md).

## Story-Gate (PFLICHT)

- [x] ≤ 5 Task-Schritte · ≤ 3 Output-Einträge · Verify deterministisch
- [x] Verify bildet ein EARS-Kriterium ab · Null Platzhalter
- [x] Blocked-by explizit · Trace vorhanden

## Boundaries (sprintweit)

- ✅ **Always:** Feature-Branches; venv-Tests; LLM-Calls (Gemini/
  Anthropic) in Tests IMMER mocken; Sample = die 2 committeten
  Cache-Decks; Sim-Gate vor Ketten-Abschluss
- ⚠️ **Ask-first (headless → BLOCKED):** Volume-/Host-Writes;
  Voll-Korpus-LLM-Läufe; neue Dependencies (Py/JS); Änderungen an
  reconstruct.js/lib oder bestehenden Seiten jenseits 1 Nav-Zeile
- 🚫 **Never:** pgbundle.npz/cache verändern (R-NF-3); rank()/
  Bestands-Response-Felder ändern (Ranking-Gold-Test bleibt grün!);
  np.load außerhalb bundle.py; in Asset-Symlinks schreiben;
  master pushen; kein `timeout`-Binary

---

## Phase 1 (Wave 1 — 4 parallel)

### US-069: Textfreie Korpus-Renders (render_notext)

**Context:** Korpus-Previews zeigen fremde Kundentexte — der Wizard
braucht textbereinigte Vorlagen-Renders (F5). Element-Filter statt
Bilderkennung: deterministisch.

**Input (Vorbedingungen):**
- Anker: `engine/tooling/render_notext` existiert NICHT; Vorlage
  `engine/tooling/render_previews.py` (idempotente Pipeline
  elements→reconstruct.js→soffice→PIL 800×450); Filterkriterium
  `e["t"] == "text"`; Sample-Decks `kf-ausstattung-location`,
  `10-182-raumkarussell-gmbh-12-09-2026`

**Task:**
1. TDD: `backend/tests/test_sprint14_tooling.py` NEU — Modul existiert + nach Sample-Lauf liegt `cache/kf-ausstattung-location/preview_notext/p1.png` (>5 KB) und die gefilterte Element-Sequenz enthält kein t=="text" (Unit auf Filterfunktion) — rot
2. `engine/tooling/render_notext.py`: render_previews-Pipeline kopieren/anpassen — je Slide elements ohne Text-Elemente rendern → `cache/<deck>/preview_notext/p<page>.png`; idempotent, --deck/--page/--limit/--force wie Vorlage
3. Sample-Lauf über die 2 committeten Decks IM CONTAINER (Mac hat kein soffice! `docker build -t kf-studio-sim .` falls nötig, dann `docker run --rm -v "$PWD/engine/data:/app/engine/data" kf-studio-sim python3 engine/tooling/render_notext.py --deck … `); render_notext liest SOFFICE-Env (Default soffice); erzeugte PNGs committen (wenige 100 KB)
4. Runbook-Block in `docs/sprint-14/KORPUS-RUNBOOK.md` (NEU): Voll-Korpus-Befehl (lokaler Alt-Korpus-Pfad via Env), Dauer-Hinweis, Volume-Sync-Befehl als MANUELLER Schritt (Ask-first, nicht ausführen)

**Output:**
- `engine/tooling/render_notext.py`
- `backend/tests/test_sprint14_tooling.py`
- `docs/sprint-14/KORPUS-RUNBOOK.md` (+ Sample-PNGs unter engine/data/cache/*/preview_notext/)

**Verify:** (FEATURE-013 EARS 1)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint14_tooling.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
test -s engine/data/cache/kf-ausstattung-location/preview_notext/p1.png && \
docker run --rm -v "$PWD/engine/data:/app/engine/data" kf-studio-sim python3 engine/tooling/render_notext.py --deck kf-ausstattung-location --page 1 && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```

**Trace:** R-DECK-4 · Vertrag §3.2 · [[KOCHFABRIK-FEATURE-013]]
**Blocked-by:** —

---

### US-073: Bild-Embeddings + rank_mixed (imgbundle)

**Context:** Ranking ist rein textbasiert — Slides mit unpassenden
Fotos ranken zu gut (F6). Beschreibung via Gemini-Vision →
Text-Embedding im pgbundle-Raum → Score-Mix.

**Input (Vorbedingungen):**
- Anker: `engine/scripts/bundle.py` (load/rank — NICHT anfassen,
  Gold-Test!), `engine/scripts/compose_offer.py` (embed),
  `backend/engine_glue.py:288` (Gemini-Request-Muster für Vision),
  Previews `cache/<deck>/preview/p<page>.png` als Vision-Input

**Task:**
1. TDD: `backend/tests/test_sprint14_bundle.py` NEU (eigene Datei — test_sprint14_tooling.py gehört US-069!): bundle.rank_mixed(qv, k, alpha=1.0) == bundle.rank(qv, None, k) (Fake-imgbundle via tmp/monkeypatch); rank_mixed ohne imgbundle == rank (graceful); embed_images-Beschreibungsfunktion gemockt — rot
2. `engine/tooling/embed_images.py`: je Slide mit image-Elementen Preview-PNG → Gemini-Vision-Beschreibung (kurz, deutsch, Speisen/Szene) → compose_offer.embed → `engine/data/imgbundle.npz` (deck/page/imgemb L2-normiert/desc); idempotent, --limit/--force
3. `engine/scripts/bundle.py` ADDITIV: `load_img()` (gecacht, np.load NUR hier) + `rank_mixed(qv, k, alpha)` — Slides ohne img-Vektor text-only (Pitfall 4); rank()/load() unverändert
4. Sample-Lauf (2 committete Decks, echter Gemini-Call dokumentiert): imgbundle-Sample committen falls <1 MB, sonst gitignore; semantische Stichprobe in DONE-Meldung ("Flying Dinner"-Query); Runbook (Voll-Lauf + Kosten) als `docs/sprint-14/IMGBUNDLE-RUNBOOK.md` (eigene Datei — KORPUS-RUNBOOK.md gehört US-069)

**Output:**
- `engine/tooling/embed_images.py`
- `engine/scripts/bundle.py` (additiv: load_img + rank_mixed)
- `backend/tests/test_sprint14_bundle.py` (+ ggf. engine/data/imgbundle.npz Sample)

**Verify:** (FEATURE-013 EARS 2+3)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint14_bundle.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
tools/.venv/bin/python -m pytest backend/tests/test_sprint12.py::test_bundle_ranking_gold -q 2>&1 | tail -1 | grep -q "1 passed" && \
grep -q "def rank_mixed" engine/scripts/bundle.py && \
test "$(grep -rl "imgbundle" --include='*.py' backend engine/scripts | grep -v "/tests/" | tr -d ' ')" = "engine/scripts/bundle.py"
```

**Trace:** R-DECK-4, R-NF-3 · Vertrag §3.2 · [[KOCHFABRIK-FEATURE-013]] · [[KOCHFABRIK-ADR-003]]
**Blocked-by:** —

---

### US-070: Element-Geometrie-API + Notext-Preview-Route

**Context:** Das Overlay-Editing braucht Geometrie + Maßstab + die
textfreie Vorschau-URL (F3-Unterbau). API-Kette Start.

**Input (Vorbedingungen):**
- Anker: `backend/routers/designer.py` (designer_texts,
  _slide_text_elements), `backend/slidesuche.py` (Preview-Route als
  Muster), `elements.json` `_meta.w_pt/h_pt` (VARIIERT: 960×540 vs.
  595×839!), Fixture `backend/tests/fixtures/routes_baseline.txt`
  (additiv ergänzen erlaubt)

**Task:**
1. TDD: `backend/tests/test_sprint14.py` NEU (API-Ketten-Datei, TestClient+Auth lokal): texts-Response enthält meta{w_pt,h_pt} + je Text x/y/w/h/color/weight/italic + images[]-Liste + preview_notext-URL; notext-Route liefert 200 für committete Sample-Slide und 404 für nicht gerenderte — rot
2. designer_texts erweitern (ADDITIV — bestehende Felder unverändert, #66-Tests bleiben grün): meta aus _meta, Geometrie/Stil je Text-Element, images[] (t=="image" mit i/x/y/w/h), preview_notext-URL
3. `GET /api/slidesuche/preview-notext/{deck}/{page}.png` (Muster Preview-Route, Pfad cache/<deck>/preview_notext/); Routen-Fixture additiv nachziehen
4. Suite 0 failed

**Output:**
- `backend/routers/designer.py` (additiv)
- `backend/slidesuche.py` (notext-Route)
- `backend/tests/test_sprint14.py` (+ fixtures/routes_baseline.txt)

**Verify:** (FEATURE-014 EARS 1)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint14.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```

**Trace:** R-DECK-5 · WP API-Kette · [[KOCHFABRIK-FEATURE-014]]
**Blocked-by:** — (notext-PNGs der Samples kommen aus US-069; bis dahin testet die Route den 404-Pfad + einen via render_notext frisch erzeugten Sample-PNG — falls US-069 noch nicht gemergt: PNG im Test-Setup einmalig selbst rendern überspringen und 404-Test reicht, 200-Test mit pytest.mark.skipif(not exists))

---

### US-074: Wizard-Gerüst + Schritt 0 + Navigation

**Context:** Der Wizard braucht Seite, Schritt-Maschine und
Angebots-Einstieg (F1/F4-Unterbau). Wizard-Kette Start.

**Input (Vorbedingungen):**
- Anker: web/designer.html (Sidebar/Design-2-Muster), designer.js
  (API-Wrapper 401-Redirect, suggest/fetchOffers-Wiring als Vorlage —
  designer.js NICHT ändern!), FE-Smoke-Muster test_sprint13_fe.py

**Task:**
1. TDD: `backend/tests/test_sprint14_fe.py` NEU (Wizard-Ketten-Datei): wizard.html 200 + Marker (wizard-progress, wizard-step, wizard-alts, wizard-stage), wizard.js 200 + kfWizard.v1, ≥5 Seiten verlinken wizard.html — rot
2. `web/wizard.html`: Sidebar + Schritt-Container (Fortschritt „Slide i von N", Alternativen-Leiste, große Stage, Zurück/Weiter); `web/assets/wizard.js`: State-Maschine kfWizard.v1 (sessionStorage: Schritt, Auswahl je Gruppe, Overrides; image_overrides NUR in-memory — Pitfall 3), Schritt-0-Panel (Upload/Dropdown → suggest, Muster designer.js)
3. Schritt-Rendering-Skelett: Gruppen aus suggest = Schritte in Server-Reihenfolge, Navigation Weiter/Zurück + Restore; Alternativen/Stage als Stubs für US-075/076
4. GENAU EINE additive Nav-Zeile „Wizard" je Bestands-Seite; Suite 0 failed

**Output:**
- `web/wizard.html`, `web/assets/wizard.js`
- `backend/tests/test_sprint14_fe.py` (+ web/*.html je 1 Nav-Zeile)

**Verify:** (FEATURE-015 EARS 1-Vorstufe + 6)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint14_fe.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q "kfWizard.v1" web/assets/wizard.js && grep -q "wizard-stage" web/wizard.html && \
test "$(grep -l 'wizard.html' web/*.html | wc -l | tr -d ' ')" -ge 5
```

**Trace:** R-DECK-1, R-DECK-2 · WP Wizard-Kette · [[KOCHFABRIK-FEATURE-015]]
**Blocked-by:** —

---

## Phase 2 (Ketten)

### US-071: Bild-Overrides im Download

**Context:** Generierte Bilder (Cover + Gericht-Bilder) müssen in die
PPTX (F7). API-Kette 2/3.

**Input (Vorbedingungen):**
- US-070 DONE (gleicher Branch); Anker: slidesuche.py SlideRef/
  _apply_overrides/combined-Loop + **Symlink-Pitfall** (shared/<deck>/
  assets zeigt in den READ-ONLY-Cache — Overrides nach
  shared/_overrides/!), image-Element `{t:"image", src}`

**Task:**
1. TDD (test_sprint14.py): download mit image_overrides {idx: data-URL} → 200, Zip enthält das Override-Bild in ppt/media (Bytes-Vergleich Magic+Größe), Cache-Verzeichnis unverändert (mtime/Datei-Set); ungültige Data-URL → 400; >8 MB → 413 — rot
2. SlideRef + `image_overrides: Optional[Dict[str, str]]`; im combined-Loop: Data-URL decodieren → `shared/_overrides/s<i>_<idx>.png` → Element-src ersetzen (Limits: max 8 MB/Bild, PNG/JPEG-Magic)
3. Suite 0 failed (inkl. node-gated E2E wie test_download_applies_overrides-Muster)

**Output:**
- `backend/slidesuche.py`
- `backend/tests/test_sprint14.py` (erweitert)

**Verify:** (FEATURE-014 EARS 2)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint14.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q "_overrides" backend/slidesuche.py && \
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed"
```

**Trace:** R-DECK-3, R-NF-3 · Vertrag §3.2 · [[KOCHFABRIK-FEATURE-014]]
**Blocked-by:** US-070

---

### US-072: Formulieren-Endpoint + Ranking-Mix-Wiring

**Context:** Markengerechte Umformulierung (F8) + suggest nutzt das
bildbewusste Ranking (F6-Wiring). API-Kette 3/3.

**Input (Vorbedingungen):**
- US-071 DONE (Branch), US-073 DONE (rank_mixed in bundle.py);
  Anker: `engine/scripts/angebot_chat.py:22-35` (Anthropic-Client +
  MODEL), designer.py _gang_groups (rank-Aufruf)

**Task:**
1. TDD (test_sprint14.py): formulate mit gemocktem Anthropic → {text}, Ton-Konstante (DNA-Beispiele) im Prompt enthalten, LLM-Fehler → 502, ohne Auth 401; suggest nutzt rank_mixed wenn imgbundle da (monkeypatch), sonst byte-identisch (Vergleichstest gegen rank) — rot
2. `POST /api/designer/formulate` {text, kind?, gang_label?} → Anthropic (Muster angebot_chat, gleiche MODEL-Konstante), Systemprompt mit 3–5 kuratierten Korpus-Formulierungen (Konstante im Router), max ~2× Input-Länge; Routen-Fixture additiv
3. _gang_groups: `bundle.rank_mixed(qv, n, alpha=KF_RANK_ALPHA)` (Env, Default 0.7) statt rank — Fallback-Semantik kommt aus bundle (US-073)
4. Suite 0 failed + **Sim-Gate** (Container ohne imgbundle → graceful, FEATURE-014 EARS 4) + Live-Smoke formulate (1 echter Call, Auszug in Meldung)

**Output:**
- `backend/routers/designer.py`
- `backend/tests/test_sprint14.py` (+ fixtures/routes_baseline.txt)

**Verify:** (FEATURE-014 EARS 3+4)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint14.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q "rank_mixed" backend/routers/designer.py && \
! grep -E "np\.load" backend/routers/designer.py && \
./tools/sim_gate.sh
```

**Trace:** R-DECK-4, R-DECK-5 · Vertrag §3.2 · [[KOCHFABRIK-FEATURE-014]] · [[KOCHFABRIK-FEATURE-013]]
**Blocked-by:** US-071, US-073

---

### US-075: Wizard-Schritte — Alternativen + Auswahl

**Context:** Pro Schritt 3–4 Alternativen, Top vorausgewählt, Cover
mit Generieren-Option (F2). Wizard-Kette 2/4.

**Input (Vorbedingungen):**
- US-074 DONE (Branch); suggest-Gruppen (candidates[0] = Top);
  /api/image-Muster aus designer.js (#65)

**Task:**
1. TDD (test_sprint14_fe.py): Marker — Alternativen-Render (slice(0, 4) o.ä.), Vorauswahl candidates[0], Cover-Schritt-Generieren-Wiring (/api/image, category cover) — rot
2. wizard.js: Alternativen-Leiste je Schritt (max 4 sichtbar, „+N weitere"), Klick wechselt Auswahl im State; Top-Kandidat default; Auswahl-Markierung
3. Cover-Schritt: „✨ Cover-Bild generieren" (Prompt aus offer wie designer.js coverPrompt) → Ergebnis in-memory als pending image_override des größten image-Elements (Anwendung visuell in US-076)
4. Suite 0 failed

**Output:**
- `web/assets/wizard.js`
- `web/wizard.html` (Marker)
- `backend/tests/test_sprint14_fe.py` (erweitert)

**Verify:** (FEATURE-015 EARS 1+4-Teil)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint14_fe.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q '/api/image' web/assets/wizard.js && \
grep -q 'candidates\[0\]' web/assets/wizard.js
```

**Trace:** R-DECK-1, R-DECK-2 · [[KOCHFABRIK-FEATURE-015]]
**Blocked-by:** US-074

---

### US-076: Overlay-Editor (Texte + Bilder auf der Stage)

**Context:** Das Herz des Wizards — große Slide mit editierbaren
Overlays (F3+F7+F8 im FE). Wizard-Kette 3/4. **WARTEPUNKT: Lead merged
API-Kette (US-072) in den Wizard-Branch.**

**Input (Vorbedingungen):**
- US-075 DONE + API-Kette gemergt (texts-Geometrie, notext-Route,
  formulate); Pitfalls: Maßstab meta.w_pt (ResizeObserver!),
  contenteditable plain-text, image_overrides in-memory

**Task:**
1. TDD (test_sprint14_fe.py): Marker — Stage nutzt preview-notext-URL + Fallback, Overlay-Positionierung aus meta/w_pt, contenteditable + paste-Strip, Formulieren-Wiring (/api/designer/formulate) mit Undo, Bild-Element-Button (/api/image, category food) — rot
2. wizard.js Stage: notext-PNG (onerror → preview + Badge), Text-Overlays absolut positioniert (Prozent von w_pt/h_pt, Fontgröße skaliert, ResizeObserver), vorbefüllt Auto-Override>Ist; Edit → Override im State
3. „✦ Formulieren" je Feld (Ersetzen + Undo auf vorherigen Wert); Bild-Overlays: Rahmen je image-Element + „🖼 Bild generieren" (Prompt aus Gang/Gericht) → <img>-Overlay deckt Element, image_override in-memory (inkl. pending Cover aus US-075)
4. Suite 0 failed

**Output:**
- `web/assets/wizard.js`
- `web/wizard.html` (Stage-Marker/CSS)
- `backend/tests/test_sprint14_fe.py` (erweitert)

**Verify:** (FEATURE-015 EARS 2+3+4)
```bash
tools/.venv/bin/python -m pytest backend/tests/test_sprint14_fe.py -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q 'preview-notext' web/assets/wizard.js && \
grep -q '/api/designer/formulate' web/assets/wizard.js && \
grep -q 'ResizeObserver' web/assets/wizard.js
```

**Trace:** R-DECK-5 · Vertrag §3.2 · [[KOCHFABRIK-FEATURE-015]]
**Blocked-by:** US-075, US-072

---

## Phase 3 (Abschluss)

### US-077: Filmstreifen + Download + E2E

**Context:** Abschluss-Schritt und der End-to-End-Beweis des ganzen
Wizards (F4). Wizard-Kette 4/4.

**Input (Vorbedingungen):**
- US-076 DONE; download-API mit overrides + image_overrides (US-071)

**Task:**
1. TDD (test_sprint14_fe.py): Marker Filmstreifen + Download-Payload (overrides + image_overrides); E2E-TestClient: suggest (gemockt) → Auswahl + Text-Override + image_override (1×1-PNG-Data-URL) → download → PPTX PK-Magic + Override-Text im Slide-XML + Bild in ppt/media (node-gated skipif) — rot
2. wizard.js Abschluss-Schritt: Filmstreifen (gewählte Slides als Overlay-Thumbs in Reihenfolge), „PPTX herunterladen" → download mit allen Overrides (Data-URL-Muster); „Von vorn"-Reset
3. Suite komplett 0 failed + ./tools/sim_gate.sh grün; Lokaler Live-Smoke des Gesamtflows dokumentiert (Risk-Ident-PDF, in DONE-Meldung)

**Output:**
- `web/assets/wizard.js`
- `web/wizard.html`
- `backend/tests/test_sprint14_fe.py` (E2E)

**Verify:** (FEATURE-015 EARS 5)
```bash
tools/.venv/bin/python -m pytest backend/tests -q 2>&1 | tail -1 | grep -E "passed" | grep -vq "failed" && \
grep -q '/api/slidesuche/download' web/assets/wizard.js && \
./tools/sim_gate.sh
```

**Trace:** R-DECK-3 · [[KOCHFABRIK-FEATURE-015]]
**Blocked-by:** US-076

---

## Dependency Graph

```
Tooling:      US-069 (notext)        US-073 (imgbundle+rank_mixed)
API-Kette:    US-070 ─▶ US-071 ─▶ US-072 ◀── (auch US-073)
Wizard-Kette: US-074 ─▶ US-075 ─▶ US-076 ─▶ US-077
                              ▲
                    [Lead merged API-Kette vor US-076]
```

> 3 Stränge + 1 Solo: US-069 (Solo-Branch), US-073 (Solo-Branch,
> bundle.py exklusiv), API-Kette auf `sprint-14-api` (designer.py +
> slidesuche.py + test_sprint14.py exklusiv), Wizard-Kette auf
> `sprint-14-wizard` (wizard.* + test_sprint14_fe.py exklusiv).
> test_sprint14_tooling.py: US-069 legt an, US-073 erweitert —
> KREUZUNGS-REGEL: getrennte Branches, additive Abschnitte, /integrate
> merged in Reihenfolge (069 vor 073 = trivial additiv).

## Summary

| Strang | Stories | Parallelisierbar |
|---|---|---|
| Wave 1 | US-069, US-073, US-070, US-074 | ja (4 parallel) |
| API-Kette | US-070→071→072 | sequentiell |
| Wizard-Kette | US-074→075→076→077 | sequentiell, Wartepunkt vor 076 |
| **Total** | **9 Stories** | 4 Stränge |
