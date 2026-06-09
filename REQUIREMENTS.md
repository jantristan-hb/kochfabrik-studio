# kochfabrik — Requirements (lebendes, informelles Dokument)

> **Typ:** REQ. Sammelsurium → Anhaltspunkt für `/epic`. Formalisierung
> (R-ID→WP-Mapping) lebt später in der TRACEABILITY, nicht hier.
>
> **Scope:** BEIDE Repos — `kochfabrik-studio` (App, Deploy) +
> `pptxgenerator_v2` (Engine, Single Source). Entschieden 2026-06-09.
>
> **Status:** v0.2 — initiale Ableitung aus Jans Brain-Dump 2026-06-09
> (Original: `REQUIREMENTS-raw-2026-06-09.md`) + Code-/PDF-Faktencheck.
> v0.2: §2b Render-Treue (R-FID-*) ergänzt — Jan, Epic-Dialog
> 2026-06-09: „die präsentationen, die wir generieren, sollen super
> nah an den pdfs sein. alleine dieses testing ist nen epic."
> Offene Punkte mit ❓.

---

## 1. Produkt-These

KOCHfabrik Studio ist die Web-App, mit der das KOCHfabrik-Team Angebote
und Präsentationen im exakten Look der eigenen 200 Referenz-Decks
erzeugt — ohne PowerPoint-Handarbeit. Die nächste Stufe: weg vom reinen
„Angebot rein → Deck raus"-Generator hin zu einem **interaktiven
Deck-Builder**, in dem sich der User seine Präsentation live aus
durchsuchbaren Referenz-Slides (PNG-Vorschauen) zusammenklickt.

Das Projekt ist „hart gevibecoded" (O-Ton Jan) — funktional live, aber
ohne saubere Specs, mit Tech-Debt und gewachsener Struktur. Dieses
Dokument ist der Einstieg, um es auf den /epic-Workflow-Standard zu
heben: saubere Specs, sauberer Techstack, saubere Dokumente, Monorepo.

---

## 2. Font-Treue · `R-FONT-*`

> **Befund (2026-06-09, pdffonts über alle 200 Referenz-PDFs in
> `pptxgenerator_v2/phase0/data/cache/*/assets/`):** Open Sans dominiert
> massiv — Regular 363×, Bold 360×, ExtraBold 268×, Italic 97×,
> BoldItalic 33×. Streufunde: Arial 92×, Calibri 45×, Helvetica 38×,
> Candara 32×, Wingdings 161× (Bullet-Glyphen), CourierNew 1×.
>
> **Render-Pfad (verifiziert):** Referenz-PDF → `extract.py` (pdfminer)
> → `elements.json` → `reconstruct.js`/`lib/text.js` (pptxgenjs) → PPTX
> → `soffice --headless` → PDF/PNG. Schriftgrößen kommen aus
> `ch.size` der ERSTEN Glyphe pro Zeile und werden mit globalem
> Fudge-Faktor `SIZE_K = 0.78` korrigiert („visuell abgeglichen") —
> nicht exakt. Weight ebenfalls nur aus der ersten Glyphe pro Zeile.

- **R-FONT-1** Generierte Präsentationen verwenden **exakt dieselbe
  Schriftart** wie die 200 Referenz-PDFs. Entschieden: **Open Sans ist
  kanonisch** (Regular/Bold/ExtraBold/Italic + ggf. Semibold/Light);
  Ausreißer-Fonts (Arial/Calibri/Helvetica/Candara) werden auf Open
  Sans normalisiert.
- **R-FONT-2** Schriftgrößen werden **exakt** aus der Quelle übernommen
  statt heuristisch kalibriert: Der Fudge-Faktor `SIZE_K = 0.78` in
  `lib/text.js` wird durch exakte pt-Größen-Extraktion ersetzt (z.B.
  Text-Rendering-Matrix via PyMuPDF-Spans statt pdfminer-Glyph-Bbox).
  Messbar: extrahierte Größe == pdffonts/Original-pt, kein Faktor mehr.
- **R-FONT-3** Open-Sans-Fontdateien sind in der Render-Umgebung
  installiert. **Bug-Befund:** Das Dockerfile installiert nur
  `fonts-dejavu-core` + `fonts-liberation` — kein Open Sans →
  LibreOffice substituiert beim PPTX→PDF/PNG-Render im Container.
- **R-FONT-4** Font-Weight/Style-Treue pro **Run**, nicht pro Zeile:
  Mischformatierung innerhalb einer Zeile (Bold-Anteil, Italic) darf
  nicht durch das Erste-Glyphe-pro-Zeile-Sampling verloren gehen.
- **R-FONT-5** Wingdings-Bullet-Glyphen (161 Vorkommen) bekommen ein
  definiertes Mapping (Original-Glyphe oder äquivalentes
  Unicode-Bullet) — kein Tofu/Substitution. ❓ Welche Glyphen genau
  vorkommen, klärt die Analyse (R-QA-2).
- **R-FONT-6** ❓ **PPTX-Portabilität:** Muss die PPTX auch auf
  Kunden-Rechnern ohne installiertes Open Sans exakt aussehen
  (→ Font-Embedding in die PPTX, eigener Baustein — python-pptx/
  pptxgenjs können das nicht nativ), oder reicht server-seitige
  Treue (PDF/PNG-Export)? Jan: „schau dir erstmal an wie wir die pptx
  rendern" — Befund steht oben, Entscheidung offen.
- **R-FONT-7** ❓ Bereits gerenderte Preview-PNGs im Coolify-Volume
  (Slidesuche-Cache) wurden ggf. mit Font-Substitution erzeugt —
  nach R-FONT-3 prüfen und ggf. `render_previews.py --force` Re-Render.

---

## 2b. Render-Treue (Fidelity) · `R-FID-*`

> Jan O-Ton (Epic-Dialog 2026-06-09): „die präsentationen, die wir
> generieren, sollen super nah an den pdfs sein. alleine dieses
> testing ist nen epic." Treue ist mehr als Fonts — sie umfasst
> Layout, Geometrie, Farben, Text — und sie muss **gemessen** werden,
> nicht per Augenmaß beurteilt (so entstand der SIZE_K-Fudge).

- **R-FID-1** Generierte/rekonstruierte Präsentationen sind messbar
  „super nah" am jeweiligen Referenz-PDF: definierte Treue-Metrik
  über visuelle Ähnlichkeit (Pixel/SSIM), Text (Inhalt + Reihenfolge),
  Geometrie (Element-Positionen) und Font (Face + pt) — Score pro
  Slide und Deck.
- **R-FID-2** Die Treue wird automatisiert über den Referenz-Korpus
  gemessen: reproduzierbarer Harness-Lauf (Sample-Set für schnelle
  Läufe, Voll-Lauf über alle 200 Decks), Rendering identisch zur
  Prod-Umgebung (gleiche Fonts/soffice).
- **R-FID-3** Regressions-Gate: Verschlechterung gegenüber der
  eingefrorenen Baseline lässt die Test-Suite fehlschlagen.
- **R-FID-4** Treue-Report als Artefakt: Worst-Slides-Ranking,
  Side-by-Side-Diff-Bilder, Score-Trend über Läufe.
- **R-FID-5** ❓ Was „super nah" als Zahl heißt (Ziel-Schwellen pro
  Metrik-Dimension): wird nach der ersten Baseline-Messung festgelegt
  und von Jan abgenommen.

---

## 3. Qualität / Bug-Analyse · `R-QA-*`

- **R-QA-1** Systematische Bug-Analyse über beide Repos (Backend,
  Frontend, Engine-Skripte, Dockerfile, Deploy-Pfad). Output:
  verifizierte Findings mit Repro/Beleg, priorisiert — als Input für
  Epic-WPs.
- **R-QA-2** Vollständige Font-/Größen-Analyse der 200 Referenz-PDFs
  als Datengrundlage für R-FONT-*: Verteilung Schriftarten, Größen
  (pt-Histogramm pro Element-Typ Titel/Body/Bullet), Farben, Weights.
  Ergebnis als dokumentiertes Artefakt (Report + maschinenlesbar).
- **R-QA-3** Bekannte Tech-Debt-Befunde fließen in die Analyse ein
  (nicht neu entdecken): alembic.ini fehlt im Container (Migrations-
  Drift, rc=255 seit Sprint 1), `web/_legacy/` Altlasten nach
  EPIC-002-Rollback, pg_shim-Bypass-Inkonsistenz (Slidesuche greift
  direkt auf pgbundle zu, Rest via pg_shim), widersprüchliche
  Kommentare (z.B. „Größe 1:1 verifiziert" direkt über `SIZE_K=0.78`).
- **R-QA-4** Verhalten ist durch Tests abgesichert, BEVOR refactored
  wird: 111 Tests grün ist die Baseline; Lücken (Engine-Skripte sind
  weitgehend testfrei) werden in der Analyse benannt.

---

## 4. Refactoring / Projekt-Hygiene · `R-REF-*`

> Jan O-Ton: „komplettes refactoring … ich hab das hart gevibecoded und
> es fehlt einiges aus der /epic checkliste. wir brauchen saubere specs,
> nen sauberen techstack, saubere dokumente, nen monorepo."

- **R-REF-1** **Monorepo:** kochfabrik-studio + pptxgenerator_v2 werden
  zu einem Repo zusammengeführt; das Vendoring-Modell (`vendor.sh`,
  ~13 MB Engine-Kopie, Container-Pfad-Sim-Gate) entfällt bzw. wird
  durch normale Repo-interne Pfade ersetzt. ❓ Schicksal der
  Alt-Verzeichnisse (`praesentationsgenerator/`, `poc/`,
  `DEPRECATED-kochfabrik-pptxgenerator/`, `_bak/`, `imagetagging/`,
  `kochfabrik-studio.bak-*`): archivieren oder mit reinziehen?
- **R-REF-2** **Saubere Specs nach /epic-Checkliste:** REQUIREMENTS
  (dieses Doc) → Epics/WPs → ROADMAP (`docs/epics/README.md`) →
  TRACEABILITY → FEATURE-Specs mit EARS-Akzeptanzkriterien. Bestehende
  Sprint-Docs (sprint-1…4, PROGRESS.md) bleiben als Historie.
- **R-REF-3** **Sauberer Techstack:** Stack-Inventur + Konsolidierung —
  Python-FastAPI-Backend, Node/pptxgenjs-Engine-Teil, LibreOffice,
  poppler, pdfminer/pdftohtml-Mix, pgbundle.npz-Shim vs. echtes
  Postgres. Zielbild in ARCH-Spec/CLAUDE.md verankern.
  (Tech-Richtung — Stack wird in CLAUDE.md/ARCH verankert; Specs
  bleiben stack-agnostisch)
- **R-REF-4** **Struktur/Lesbarkeit:** `backend/app.py` (939 Zeilen,
  Bildgenerator+Angebot+Präsentation gemischt) in Module entzerren;
  `phase0/scripts/` (40+ Flat-Skripte, Build-Tools und Runtime-Code
  gemischt) in Runtime vs. Build/Einmal-Tooling trennen; Dead Code aus
  EPIC-002-Rollback entfernen.
- **R-REF-5** **Saubere Dokumente:** README/CLAUDE.md/PROGRESS auf den
  Monorepo-Stand heben; Engine-Pipeline (PDF→elements→reconstruct)
  dokumentieren; Deploy-Doku (Coolify-Volume, Korpus-Cache ~4,8 GB).
- **R-REF-6** **Verhalten strikt erhalten:** Refactoring ändert kein
  beobachtbares Verhalten — Prod = Truth, jede Änderung testgesichert
  (vgl. R-QA-4). Ausnahme: explizit beauftragte Änderungen (R-FONT-*,
  R-DECK-*).

---

## 5. Live-Deck-Builder · `R-DECK-*`

> Neue Produktrichtung aus der Ideation-Runde. Fundament existiert:
> `/api/slidesuche/search` (Vektor-Suche → Top-5 mit PNG-Preview),
> `/api/slidesuche/preview/{deck}/{page}.png`,
> `/api/slidesuche/download` (PPTX-Bundle aus Liste `{deck,page}`).

- **R-DECK-1** Der User kann sich **live eine Präsentation
  zusammenklicken**: Slides per Suche finden (PNG-Vorschauen), per
  Klick in ein Arbeits-Deck übernehmen, Reihenfolge ändern, Slides
  entfernen — und das Ergebnis als PPTX herunterladen.
- **R-DECK-2** Das Arbeits-Deck ist während der Session sichtbar
  (Tray/Storyboard mit PNG-Thumbnails) und überlebt Page-Reloads. ❓
  Persistenz-Level: Session reicht, oder gespeicherte Decks pro User?
- **R-DECK-3** Download nutzt den bestehenden Bundle-Pfad
  (`/api/slidesuche/download`) — Slides kommen verbatim aus dem
  Referenz-Cache, damit Font-Treue (R-FONT-*) automatisch gilt.
- **R-DECK-4** ❓ Mischbetrieb mit dem Generator: Kann ein generiertes
  Deck (Angebot → assemble.py) als Startpunkt ins Klick-Deck geladen
  und ergänzt werden — oder sind Generator und Builder getrennte Wege?
- **R-DECK-5** ❓ Text-Anpassung im Builder (z.B. Kundenname auf
  übernommener Slide tauschen): im Scope der ersten Ausbaustufe oder
  bewusst raus?

---

## 6. Nicht-funktionale Anforderungen

- **R-NF-1** Graceful Degradation bleibt erhalten: App startet und
  meldet 503 mit Klartext, wenn Engine/Korpus-Volume fehlt (bestehendes
  Verhalten, nicht verschlechtern).
- **R-NF-2** Keine Regression im Deploy-Pfad: Coolify-Deploy
  (yu2fqx0twmtqcp6zyx2e59si) muss nach jedem Refactoring-Schritt
  funktionieren — Monorepo-Umstellung braucht einen Migrationsplan
  für das Deploy-Repo. ❓ GitHub-Repo-Schnitt nach Monorepo-Merge.
- **R-NF-3** Referenz-Korpus ist unantastbar: `data/cache/` (200 Decks,
  ~4,8 GB Voll-Cache auf Server-Volume) wird nie destruktiv angefasst.

---

## 7. Offene Entscheidungen (❓ zusammengefasst)

1. **PPTX-Font-Embedding** (R-FONT-6): Server-Treue vs. Portabilität
   auf Kunden-Rechnern — blockiert den Schnitt des Font-Epics.
2. **Preview-PNG-Re-Render** (R-FONT-7): Prüfen, ob Bestands-PNGs mit
   Substitutions-Fonts gerendert wurden.
3. **Monorepo-Schnitt** (R-REF-1, R-NF-2): Welche Alt-Verzeichnisse
   kommen mit, wie heißt das Repo, wie migriert das Coolify-Deploy.
4. **Deck-Builder-Scope** (R-DECK-2/4/5): Persistenz, Generator-
   Integration, Text-Edit — Ausbaustufen schneiden.
5. **Treue-Schwellen** (R-FID-5): Zielwerte pro Metrik-Dimension —
   nach Baseline-Messung, vor Abnahme der Font-Arbeit.

---

## 8. Backlog / Unsortiert

_(neue, noch nicht eingeordnete Anforderungen hier rein)_

---

> **Quellen dieses Dokuments:** Jans Brain-Dump + Rückfragerunde
> 2026-06-09 (`REQUIREMENTS-raw-2026-06-09.md`); Code-Faktencheck
> kochfabrik-studio@88747dc + pptxgenerator_v2/phase0 (extract.py,
> lib/text.js, assemble.py, render_previews.py, Dockerfile,
> backend/slidesuche.py); pdffonts-Sweep über 200 Referenz-PDFs.

## Referenzen
- implements ← Epics/WPs referenzieren R-IDs von hier; Abdeckung
  entsteht in der TRACEABILITY via `/epic`.
