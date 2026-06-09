# TEST-BASELINE — kochfabrik-studio (US-040)

> Doc-only-Analyse-Sprint. Verbindliche Zahl ist der **pytest-Collect-Count**, nicht
> der Run-Pass-Count. Diese Inventur ist das **Refactoring-Gate für EPIC-004**
> (Monorepo-Schnitt, „Verhalten strikt erhalten"): nur testgesichertes Verhalten
> ist beim Verschieben/Umstrukturieren abgesichert.

**Test-Count (pytest collect):** 63

(`tools/.venv/bin/python -m pytest backend/tests --collect-only -q` → `63 tests collected`)

## Reproduktion / Umgebung

```bash
# Engine-Code (../pptxgenerator_v2/phase0) und Backend nutzen PEP-604-Typen
# (str | None). Das ERZWINGT Python >= 3.10 — System-Python 3.9.6 wirft beim
# Collect TypeError und bricht ab (siehe Befund E1).
/opt/homebrew/bin/python3.13 -m venv tools/.venv
tools/.venv/bin/pip install pytest -r requirements.txt
tools/.venv/bin/python -m pytest backend/tests --collect-only -q   # → 63
tools/.venv/bin/python -m pytest backend/tests -q                  # Run-Verhalten s.u.
```

| Größe | Wert |
|-------|------|
| Test-Dateien (`backend/tests/test_*.py`) | 7 |
| Collected Tests | **63** |
| Run ohne `TEST_DATABASE_URL` | 57 passed, 5 skipped, **1 failed** |
| Python-Mindestversion (faktisch) | 3.10+ (Collect-Crash unter 3.9) |

> **PROGRESS.md-Diskrepanz:** PROGRESS.md behauptet „111 Tests grün". Real
> collected die Suite **63 Tests**. Die Zahl 111 ist nicht reproduzierbar —
> entweder veraltet, gegen einen anderen Stand gezählt, oder Engine-Tests
> (Schwester-Repo, separate Suite) mitgerechnet. Vor EPIC-004 ist die
> verbindliche Backend-Baseline **63**.

## Abdeckungs-Karte (pro Test-Datei)

Was jede Datei konkret absichert — kein „gut getestet"-Pauschalurteil.

| Test-Datei | Tests | Modul / Target | Abgesichertes Verhalten |
|------------|------:|----------------|--------------------------|
| `test_app_helpers.py` | 21 | `backend/app.py` (pure Helpers) | `_today_de()` (dt. Monatsname, `TT. Monat JJJJ`); `_ensure_correct_dates()` (datum=heute erzwungen, lieferdatum-Default aus `veranstaltung.datum`, kein Override wenn gesetzt, Idempotenz, defensiv bei str/None/list/`veranstaltung=None`); `valid_cookie()` (HMAC-Signatur, Expiry, unbekannter User → False, Garbage); `_owner()` (Cookie→email, None ohne/bei invalid Cookie, lowercased) |
| `test_oauth.py` | 15 | `backend/oauth.py` | `providers()` ENV-Gating (keine ENV→`{}`, ID-ohne-Secret inaktiv, Leerstring inaktiv, Google+MS parallel, MS default/custom Tenant); `redirect_uri()` (explizite Base, Trailing-Slash-Normalisierung, Provider im Pfad, Fallback auf `request.url`); `auth_url()` (inaktiv→None, aktiv→URL mit state/client_id/redirect_uri/scope, unbekannter Provider→None) |
| `test_numbering.py` | 11 | `backend/numbering.py` | `_next()` async, gibt int zurück, setzt **2 Queries** ab (INSERT…ON CONFLICT + UPDATE…RETURNING = atomar, kein read-then-write-Race) via Mock-Session; `next_kundennummer()` (`100001-A`, 6-stellig padded, `-A`-Suffix immer); `next_angebotsnummer()` (`KF-{Jahr}-{n:04d}`, 4-stellig padded, >9999 wächst, Jahr aus Systemzeit) |
| `test_sprint1.py` | 7 | `backend/db.py`, `app.py`, `migrate.py`, `numbering.py`, `store.py` | **Graceful (kein DB):** `db` importiert ohne `DATABASE_URL` (DB_OK=False, `ping()`→False), `app` importiert ohne DB, Nummern-Format pur. **DB-gated (skip):** Migration idempotent, Numbering unique unter 15× parallel, Tenant-Isolation `save_offer`/`get_offer`/`list_offers` |
| `test_sprint2.py` | 4 | `backend/app.py`, `alembic/`, `store.py` | Chat-Endpoint `/api/angebot/chat` registriert ohne DB; Alembic-Baseline `0001_baseline.py` (no-op upgrade, down_revision=None) — **failt lokal, s. E2**. **DB-gated (skip):** Chat persist+full (`add_chat`/`get_offer_full`), Chat-Tenant-Isolation (`TenantError`) |
| `test_sprint3.py` | 2 | `backend/app.py`, `store.py` | Routen `/api/stats`, `/api/kunden`, `/api/kunde/{customer_id}` registriert; `store.stats/list_customers/get_customer` callable + `list_offers`-Signatur (`q`, `status`) |
| `test_sprint4.py` | 3 | `backend/oauth.py`, `app.py` | OAuth inaktiv ohne ENV; Routen `/api/oauth/providers`, `/api/oauth/{provider}/login`, `/api/oauth/{provider}/callback` registriert; `valid_cookie(make_cookie("nobody"))`→False ohne DB |

### Run-Verhalten (Befunde — keine Blocker, dokumentiert)

- **E1 — Collect-Crash unter Python 3.9:** `app.py:263` und `oauth.py:51` nutzen
  `str | None` (PEP 604). Unter dem System-Python 3.9.6 wirft der Collect
  `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` und
  bricht 3 Dateien ab (`test_app_helpers`, `test_oauth`, `test_sprint3`). Erst
  mit Python ≥ 3.10 (hier 3.13) collected die volle Suite (63). **Implikation:**
  Die faktische Mindest-Runtime ist 3.10+; das ist nirgends als Constraint
  fixiert (requirements.txt hat kein `python_requires`).
- **E2 — `test_alembic_baseline_present_and_empty` failt lokal (nicht DB-gated):**
  `backend/alembic/versions/` hat **kein `__init__.py`** → importiert als
  Namespace-Package, `__file__` ist `None` →
  `os.path.dirname(_v.__file__)` → `TypeError: expected str … not NoneType`.
  Schlägt unabhängig von DB/ENV fehl. Der Test selbst ist brüchig (verlässt
  sich auf `__file__` eines Package-Imports), die Datei `0001_baseline.py`
  existiert real.
- **5 DB-gated Tests skippen ohne `TEST_DATABASE_URL`:** `test_migration_idempotent`,
  `test_numbering_first_and_unique`, `test_tenant_isolation_and_numbers`
  (sprint1), `test_chat_persist_and_full`, `test_chat_tenant_isolation`
  (sprint2). Marker `needs_db` (conftest). Diese decken die **eigentliche
  Persistenz-/Tenant-Schicht** ab — lokal ungeprüft, laut Test-Docstrings nur
  „live gegen kf-studio-pg" verifiziert (nicht maschinell in dieser Suite).

## Lücken

### Backend (`backend/*.py`) — ungetestete oder nur indirekt getestete Bereiche

| Bereich | Status | Risiko für EPIC-004 |
|---------|--------|---------------------|
| `slidesuche.py` | **Keine** dedizierte Testdatei | Slidesuche-Verhalten beim Verschieben nicht abgesichert |
| OAuth-Callbacks (Token-Exchange, IdP-Calls) | Nur `auth_url`/`redirect_uri`/`providers` getestet — **kein** Callback-Roundtrip, kein Token-Tausch, keine User-Anlage | Auth-Flow-Regression unbemerkt |
| `store.py` Persistenz-Logik | Nur DB-gated (5 Tests **skippen lokal**) | Kernschicht lokal unverifiziert → vor Refactoring DB-Tests in CI erzwingen |
| `app.py` HTTP-Endpoints (Request→Response) | Nur **Routen-Registrierung** geprüft (Pfad existiert), kein echter Request gegen TestClient (Body/Status/Auth-Gate) | Endpoint-Verhalten nicht abgesichert |
| Bildgenerator-/Asset-Endpoints | Keine Tests gefunden | falls vorhanden: ungetestet |
| `migrate.py` Run-Pfad | DB-gated, lokal skip | Migration nur live geprüft |
| `db.py` Connect-Pfad mit DB | Nur Graceful-ohne-DB getestet | Verbindungs-Setup ungeprüft |

### Engine-Skripte (`../pptxgenerator_v2/phase0/`)

Das Schwester-Repo hat eine **eigene** Suite (`tests/`, 8 Dateien), die NICHT Teil
des Backend-Collect-Counts (63) ist und nur einen Bruchteil der **45 Runtime-Skripte
in `scripts/`** + die JS-Pipeline (`spike-pptxgenjs/`) abdeckt.

**Vorhandene Engine-Tests (Target):**
`test_angebot_fill_model.py` (Token-Replacement + `angebot_model`),
`test_angebot_positions_layout.py` (`angebot_positions.py` Layout),
`test_angebot_render.py` (`angebot_render.py` E2E + Pixel-Gate),
`test_angebot_template.py` (Template+Modell→Angebot),
`test_empty_courses.py` (`assemble.py` Edge: 0 Gänge kein Crash),
`test_frame_pick.py` (nur `compose_offer.pick_frame`),
`test_kf_classify.py` (`kf_classify.py` deterministisch),
`test_no_external_data.py` (Datenschutz-Regression: PDFs nur Kalkulationen).

**Ungetestete kritische Runtime-Skripte (Auswahl):**

| Skript | LOC | Rolle | Test? |
|--------|----:|-------|-------|
| `assemble.py` | 369 | Deck-Assembly (Hauptpipeline) | nur Empty-Courses-Edge |
| `_deckpipe.py` | 106 | Deck-Pipeline-Kern | **keine** |
| `compose_offer.py` | 589 | Angebots-Komposition | nur `pick_frame` |
| `angebot_render.py` | 78 | Render | E2E-Pixel-Gate vorhanden |
| `angebot_fill.py` | 121 | Token-Fill | abgedeckt |
| `spike-pptxgenjs/reconstruct.js` | 112 | PPTX-Rekonstruktion (JS) | **keine** (JS-Suite fehlt komplett) |
| `spike-pptxgenjs/lib/*.js` (design/photos/logos/text/frame/gutter/overrides) | — | Render-Bausteine | **keine** |
| `extract.py` / `db_load*.py` / `build_*.py` / `embed_*.py` / `curate.py` / `dedup_*.py` / `recon_*.py` / `pdf_diff.py` / `validate_assembled.py` u.v.m. | — | Ingestion/Korpus/Embedding/Validierung | **keine** (≈37 der 45 Skripte ungetestet) |

> JS-Pipeline (`spike-pptxgenjs/`, 8 `.js`-Dateien) hat **keinerlei** Tests —
> reconstruct.js erzeugt das finale PPTX. Beim Monorepo-Schnitt komplett ungesichert.

## Konsequenz für EPIC-004

EPIC-004 verlangt „Verhalten strikt erhalten". Aktuell ist nur abgesichert, was
die **63 Backend-Tests** (davon 57 lokal grün) prüfen — und das ist überwiegend
**Format-/Pure-Logik + Routen-Registrierung**, nicht das durchlaufende Verhalten.

**Vor dem Refactoring zusätzlich abzusichern (Mindest-Gate):**

1. **Python-Version pinnen:** `python_requires = ">=3.10"` (requirements/pyproject)
   + CI-Matrix, sonst reproduziert E1 jeden Onboarding-Setup-Crash.
2. **E2 fixen oder Test härten:** `__init__.py` in `backend/alembic/versions/`
   ergänzen ODER den Test auf `importlib.resources`/Pfad-Glob umstellen, damit
   die Suite lokal **grün** als Baseline gilt (aktuell 1 Dauer-Fail).
3. **DB-gated Tests in CI scharf schalten:** `TEST_DATABASE_URL` in der Pipeline
   setzen, damit die 5 skippenden Persistenz-/Tenant-Tests die **Kernschicht**
   tatsächlich vor dem Schnitt absichern (nicht nur „live verifiziert").
4. **Endpoint-Charakterisierungstests** (FastAPI `TestClient`): echte Requests
   gegen die Routen (Status/Body/Auth-Gate), nicht nur Pfad-Registrierung —
   das ist das Verhalten, das EPIC-004 „erhalten" muss.
5. **`slidesuche.py` + OAuth-Callback** mit mindestens Smoke-/Charakterisierungs-
   tests abdecken (heute null bzw. nur URL-Bau).
6. **Engine-Hauptpipeline charakterisieren:** Golden-Output-Test für
   `assemble.py` → `_deckpipe.py` → `compose_offer.py` → `reconstruct.js`
   (Byte-/Struktur-Vergleich des erzeugten PPTX) als Refactoring-Netz, bevor
   Skripte ins Monorepo verschoben werden. Die JS-Pipeline hat heute **keinen**
   Test.
