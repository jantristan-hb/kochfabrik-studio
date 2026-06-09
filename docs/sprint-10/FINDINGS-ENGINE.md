# FINDINGS-ENGINE — Bug-Analyse `pptxgenerator_v2`-Engine (US-037)

> **Sprint 10 / EPIC-003 — Doc-only-Analyse.** Kein Produktiv-Code geändert,
> weder im Studio noch im Engine-Repo. Quelle: `../pptxgenerator_v2/phase0/`
> (read-only, Commit-Stand 20.05.2026 / 26.05.2026). Belege sind exakte
> `Datei:Zeile`-Zitate relativ zu `phase0/`; Studio-seitige Belege sind als
> solche markiert (Pfad ohne `phase0/`-Präfix, im Studio-Worktree).
>
> **Schema:** `## F-E-NN: Titel` · Severity · `**Beleg:**` · `**Zuordnung:**`
> (`EPIC-xxx/Tn` oder `VERWORFEN: {Grund}`).
>
> **Zuordnungs-Targets** (aus Feature-Kontext): EPIC-005 T1–T6 (Font/Render-
> Treue), EPIC-007 V1–V5 (Verifikation/Gates), EPIC-004 M5 (Datenpfad/
> Monorepo). Studio-only-Befunde verweisen auf `FINDINGS-STUDIO.md` (US-036).

---

## Zusammenfassung

| Finding | Severity | Kandidat | Zuordnung |
|---------|----------|----------|-----------|
| F-E-01 SIZE_K-Fudge + widersprüchlicher Kommentar | HIGH | #1 | EPIC-005/T1 |
| F-E-02 Open Sans fehlt im Docker-Image | CRITICAL | #2 | EPIC-005/T2 |
| F-E-03 pg_shim-Bypass in slidesuche.py | MEDIUM | #3 | EPIC-004/M5 |
| F-E-04 alembic-Drift (Studio) | — | #4 | VERWORFEN |
| F-E-05 web/_legacy (Studio) | — | #5 | VERWORFEN |
| F-E-06 Weight nur aus erster Glyphe pro Zeile | HIGH | — | EPIC-005/T1 |
| F-E-07 WEIGHT-Map unvollständig / stiller Regular-Fallback | HIGH | — | EPIC-005/T2 |
| F-E-08 Silent-Skip verschluckt Render-Fehler ohne Gate | HIGH | — | EPIC-007/V1 |
| F-E-09 Subprocess-Timeouts inkonsistent (240/300/600/120/keiner) | MEDIUM | — | EPIC-007/V2 |
| F-E-10 CORPUS_DIR als hardcodierter Mac-Pfad + Klartext-DSN | MEDIUM | — | EPIC-004/M5 |
| F-E-11 Cache ohne Invalidierung (Quell-PDF-Änderung unsichtbar) | MEDIUM | — | EPIC-007/V3 |
| F-E-12 LINE_K / Y_OFF_K — weitere unbelegte Render-Heuristiken | MEDIUM | — | EPIC-005/T1 |
| F-E-13 Platzhalter-Rect bei fehlendem Asset, kein Fehler-Signal | MEDIUM | — | EPIC-007/V4 |

13 Findings, davon 5 Verdachts-Kandidaten (2 belegt-engine, 1 belegt-bypass,
2 VERWORFEN mit Studio-Verweis), 8 eigene Findings.

---

## F-E-01: `SIZE_K = 0.78` — heuristischer Schriftgrößen-Fudge widerspricht dem Modul-Kopfkommentar

**Beleg:** `spike-pptxgenjs/lib/text.js:16` (`const SIZE_K = 0.78;`, Kommentar Z. 14–15 „pdfminer char.size überschätzt … Kalibrierbarer Korrekturfaktor (visuell gegen Original abgeglichen)") vs. `spike-pptxgenjs/lib/text.js:4` (Kopf: „Größe 1:1 (pdfminer-size == pt, verifiziert)"). Angewandt in Z. 30 (`fontSize: Math.round(l.size * SIZE_K * 10) / 10`) und Z. 52.

**Severity:** HIGH

Die Schriftgröße ist nicht 1:1, sondern wird um den Faktor 0,78 verkleinert — ein „visuell abgeglichener" Einzelwert ohne Messreihe. Der Faktor kompensiert eine Eigenschaft von pdfminer (`char.size` aus der Subset-Font-Bbox überschätzt die pt-Größe), gilt aber pauschal für alle Decks/Fonts. Der Kopfkommentar (Z. 4) behauptet das Gegenteil („verifiziert") — d.h. die einzige Dokumentation der Größenlogik ist intern widersprüchlich und führt jeden, der die Datei liest, in die Irre. Für faithful-Anspruch („reproduzieren, nicht verschönern") ist ein globaler Magic-Faktor ein systematischer Fehler, der pro Font/Größe unterschiedlich daneben liegen kann.

**Zuordnung:** EPIC-005/T1

---

## F-E-02: Open Sans fehlt im Studio-Docker-Image — `WEIGHT`-Faces werden beim soffice-Render substituiert

**Beleg:** `WEIGHT`-Map fordert die Faces „Open Sans", „Open Sans Extrabold", „Open Sans Semibold", „Open Sans Light" (`spike-pptxgenjs/lib/text.js:6-12`, gesetzt als `fontFace` in Z. 33). Studio-Image installiert nur `fonts-dejavu-core fonts-liberation` (`Dockerfile:8`, Studio-Worktree) — kein Open-Sans-Paket. soffice (`Dockerfile:7`) substituiert fehlende Faces beim PPTX→PDF/PNG-Render still.

**Severity:** CRITICAL

Die Engine emittiert PPTX mit `fontFace: "Open Sans …"`, aber das Render-Image hat diese Schrift nicht. LibreOffice fällt beim Render still auf eine Ersatzschrift (Liberation/DejaVu) zurück → Glyphenbreiten, Kerning und damit Zeilenumbrüche/Box-Auslastung weichen vom Original ab. Das untergräbt den faithful-Render direkt und interagiert mit F-E-01 (der SIZE_K-Faktor wurde lokal „visuell abgeglichen", wo Open Sans installiert ist — im Container greift er auf eine andere Schrift). Engine-Sicht zur konkreten Bedarfsdeckung: die `WEIGHT`-Map braucht real die Faces **Open Sans Regular** (für `Regular` und `Bold`, letzteres via `bold:true` synthetisch), **Open Sans Semibold**, **Open Sans Light**, **Open Sans Extrabold** — vier Faces, von denen der Renderer aktuell null hat.

**Zuordnung:** EPIC-005/T2

---

## F-E-03: `slidesuche.py` lädt `pgbundle.npz` direkt und umgeht `pg_shim` — zwei parallele Datenpfade auf dasselbe Bundle

**Beleg:** `backend/slidesuche.py:98-115` (Studio-Worktree) — `_bundle()` lädt `data/pgbundle.npz` per `np.load` und normalisiert `emb` selbst; Kommentar Z. 99–103 begründet den Bypass explizit. Identische Lade-/Normalisier-Logik existiert bereits in `phase0/scripts/pg_shim.py:80-87` (`_Conn.__init__`: `np.load(_NPZ)`, `_normemb = e / (norm + 1e-9)`). ANN in `slidesuche.py:157-166` dupliziert die Cosinus-Logik aus `pg_shim.py:60-65`.

**Severity:** MEDIUM

Zwei Code-Pfade lesen dasselbe `pgbundle.npz` mit derselben Normalisierung (`/(norm + 1e-9)`) und derselben Cosinus-ANN-Mechanik — einmal über `pg_shim` (für `assemble.py`, das Studio per `PPTX_PGSHIM=1` aktiviert, `backend/app.py:804`), einmal direkt in `slidesuche.py`. Begründung im Code ist nachvollziehbar (pg_shim deckt nur die vier `assemble.py`-Query-Shapes ab, kein `LIMIT %s`/`module_label`), aber die Folge ist Doppelpflege: Bundle-Schema-Änderungen (Spaltennamen `emb/deck/page/module_label`) müssen an zwei Stellen nachgezogen werden, und die Normalisierungs-Konstante `1e-9` ist dupliziert statt geteilt. Kein Bug heute, aber Drift-Risiko und Mehraufwand beim Postgres↔Bundle-Schnitt (ADR-003). Engine-Bezug: der Bundle-Vertrag (`pgbundle.npz`-Keys) ist die geteilte Oberfläche zwischen Engine-`pg_shim` und Studio-Suche.

**Zuordnung:** EPIC-004/M5

---

## F-E-04: alembic-Drift

**Beleg:** Kein alembic im Engine-Repo (`find ../pptxgenerator_v2 -iname 'alembic*'` → leer). `alembic.ini` existiert nur Studio-seitig (`./alembic.ini`, Studio-Worktree). Engine arbeitet DB-frei über `pgbundle.npz` (`phase0/scripts/pg_shim.py:9-11`) bzw. lokales Postgres `port=5434` ohne Migrations-Tooling (`phase0/scripts/compose_offer.py:37-38`).

**Severity:** —

**Zuordnung:** VERWORFEN: Rein Studio-seitig, kein Engine-Bezug. Siehe `FINDINGS-STUDIO.md` (US-036).

---

## F-E-05: `web/_legacy/`

**Beleg:** Kein `_legacy`-Pfad im Engine-Repo (`find ../pptxgenerator_v2 -path '*_legacy*'` → leer; Engine hat kein `web/`-Verzeichnis). `web/_legacy` existiert nur Studio-seitig (`web/_legacy`, Studio-Worktree).

**Severity:** —

**Zuordnung:** VERWORFEN: Rein Studio-seitig, kein Engine-Bezug. Siehe `FINDINGS-STUDIO.md` (US-036).

---

## F-E-06: Schrift-Weight wird nur aus der ersten Glyphe der Zeile abgeleitet

**Beleg:** `spike-pptxgenjs/extract.py:125-134` — `ch = first_char(ln)`; `fn = (ch.fontname or "")`; `wt = fn.split("-")[-1]`; gespeichert als ein `weight`/`italic`/`size` pro Zeile. `first_char` (Z. 66–74) liefert die erste `LTChar` der Zeile. `lib/text.js:25` baut daraus genau einen Run pro Zeile.

**Severity:** HIGH

Eine PDF-Textzeile kann gemischte Runs enthalten (z.B. „**Rinderfilet** mit Pfefferjus" — Name bold, Beschreibung regular, oder ein gold gesetztes Wort in weißem Text). Die Extraktion nimmt Weight, Größe und Farbe ausschließlich aus dem ersten Zeichen und appliziert sie auf die ganze Zeile. Mixed-Style-Zeilen werden dadurch falsch vereinheitlicht — entweder alles bold oder alles regular. Das ist ein Treue-Verlust am Kern des faithful-Anspruchs und betrifft genau die Gericht-Captions, auf denen `text_swap`/`slot_count` (`compose_offer.py:341-356, 376-381`) ihre Bold-weiß-Heuristik aufbauen → Fehlklassifikation pflanzt sich fort.

**Zuordnung:** EPIC-005/T1

---

## F-E-07: `WEIGHT`-Map deckt nur 5 Suffixe — alles andere fällt still auf Regular

**Beleg:** `spike-pptxgenjs/lib/text.js:6-12` (Keys: `ExtraBold, Bold, Semibold, Light, Regular`) + Z. 26 (`const w = WEIGHT[l.weight] || WEIGHT.Regular;`). Quelle des `weight`-Strings: `extract.py:128` (`wt = fn.split("-")[-1]`) — beliebiges Font-Suffix, z.B. `Medium`, `SemiBold` (Binnen-B), `Black`, `Condensed`.

**Severity:** HIGH

Der Weight wird aus dem PDF-Fontnamen-Suffix gewonnen und ungeprüft als Map-Key benutzt. Jeder Wert außerhalb der fünf bekannten Schlüssel (`Medium`, `Black`, `SemiBold` mit Binnen-B ≠ `Semibold`, Subset-Präfixe wie `ABCDEF+OpenSans-Medium` → Suffix `Medium`) fällt still auf `Regular` zurück. Es gibt kein Logging und kein Gate, das einen unbekannten Weight meldet — der Treue-Verlust ist unsichtbar. Hängt direkt an F-E-02 (selbst bei korrekter Weight-Erkennung fehlt die Schrift im Container) und F-E-06.

**Zuordnung:** EPIC-005/T2

---

## F-E-08: Silent-Skip-Pfade in `reconstruct.js` verschlucken Element-/Slide-Fehler ohne hartes Gate

**Beleg:** `spike-pptxgenjs/reconstruct.js:71-74, 85-88, 99-102, 104-107` — vier `catch`-Blöcke inkrementieren nur `SKIP++` und `console.warn`; Z. 110–112 schreibt das PPTX in jedem Fall (`writeFile`) und endet mit Exit 0. Aufrufer prüfen nur `returncode != 0` (`assemble.py:358`, `compose_offer.py:237-239`/`check=True`, `render_previews.py:78`).

**Severity:** HIGH

Stirbt ein einzelnes Element, ein Text oder ein ganzer Slide beim Emittieren, zählt `reconstruct.js` es als `SKIP` und macht weiter — das Skript endet erfolgreich (Exit 0), die PPTX wird geschrieben. Aufrufer sehen nur den Returncode und werten das als Erfolg. Ein Deck mit fehlenden Slides/Elementen (z.B. durch einen Element-Bug) wird damit klaglos ausgeliefert; die `SKIP`-Zahl steht nur in der Konsole und wird nirgends als Schwellwert geprüft. Für ein faithful-Produkt braucht es ein Gate (z.B. `SKIP > 0 → Exit ≠ 0` oder Report-Eintrag). `convert.py`/`run_batch` erfasst Fehler nur, wenn `reconstruct` selbst nonzero zurückgibt (`convert.py:33-39, 95-102`) — Silent-Skips entgehen dem Batch-Report komplett.

**Zuordnung:** EPIC-007/V1

---

## F-E-09: Subprocess-Timeouts in der Render-Kette inkonsistent und teils nicht gesetzt

**Beleg:** `phase0/scripts/_deckpipe.py:42-43` (`timeout=240` für alle Pipeline-Schritte); `assemble.py:357` (`reconstruct.js timeout=300`); `compose_offer.py:239` (`timeout=600`) und Z. 565 (`timeout=600`); `render_previews.py:77` (`reconstruct timeout=120`), Z. 89 (`soffice timeout=120`); `spike-pptxgenjs/convert.py:34` (`subprocess.run(...)` **ohne** `timeout`) — `pdfinfo/pdftohtml/extract/reconstruct` können dort unbegrenzt hängen. `assemble.py:68, 100` (`pdftotext` ohne timeout).

**Severity:** MEDIUM

Dieselben Pipeline-Schritte (pdftohtml, extract.py, reconstruct.js, soffice) laufen je nach Aufrufer mit 120 s, 240 s, 300 s, 600 s oder ganz ohne Timeout. `convert.py` — der dokumentierte Haupt-Einstieg (CLAUDE.md) — setzt in `run()` (Z. 33–39) keinerlei Timeout, ein hängendes `soffice`/`pdftohtml` blockiert dort unbegrenzt. Im Studio-Webkontext (FastAPI ruft die Engine als Subprocess) ist ein nie zurückkehrender Render ein Hänger ohne Obergrenze. Die Werte wirken ad-hoc gewählt, nicht aus einer Messung der p99-Laufzeit abgeleitet.

**Zuordnung:** EPIC-007/V2

---

## F-E-10: `CORPUS_DIR` ist ein hardcodierter Mac-Pfad + Klartext-DSN

**Beleg:** `phase0/scripts/compose_offer.py:30` (`CORPUS_DIR = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"`). Verwendet in `compose_offer.py:166-167` (`load_corpus`), `compose_offer.py:534-535` (`cmd_swap`), `assemble.py:293-295` (`smap`). Lokales Postgres ebenfalls hardcodiert: `compose_offer.py:37-38` und `build_cache.py:20-21` (`host="localhost", port=5434, password="pptxgen"`).

**Severity:** MEDIUM

Der Korpus-Pfad ist ein absoluter Pfad in Jans persönlichem Nextcloud-Mount. Im Container existiert er nicht; `assemble.py:293-295` fängt das mit `os.path.isdir(CORPUS_DIR)`-Fallback ab (nutzt dann nur Cache-Hits), aber `compose_offer.py:cmd_match/cmd_build/cmd_swap` und `load_corpus` setzen ihn ungeprüft voraus (`os.listdir(CORPUS_DIR)` würde im Container werfen). Außerdem stehen DSN-Credentials im Klartext im Code. Für den Monorepo-/Deploy-Schnitt muss der Korpus-Pfad konfigurierbar (Env/Arg) und die Postgres-DSN aus der Umgebung kommen.

**Zuordnung:** EPIC-004/M5

---

## F-E-11: Deck-Cache hat keine Invalidierung — geänderte Quell-PDFs werden nie neu extrahiert

**Beleg:** `phase0/scripts/_deckpipe.py:82-106` (`cached_deck`) — Cache-Hit nur an Existenz von `cache/<slug>/elements.json` + `assets/` gekoppelt (Z. 92), kein mtime/Hash-Vergleich gegen das Quell-PDF. `build_cache.py:4-6` dokumentiert „bereits gecachte Decks = instant Cache-Hit, kein Re-Extrakt" als Feature.

**Severity:** MEDIUM

Der Cache ist rein existenzbasiert: liegt `cache/<slug>/elements.json` vor, wird es kopiert, egal ob das Quell-PDF inzwischen geändert/ersetzt wurde. Ändert KOCHfabrik ein Korpus-Deck (gleicher Dateiname), liefert die Engine stillschweigend die alte Extraktion. Da `phase0/data/cache/` zudem per Boundary nicht angefasst werden darf und auf dem Server gemountet ist, gibt es keinen automatischen Weg, veraltete Einträge zu erkennen. Braucht ein Invalidierungs-Signal (PDF-Hash in der Cache-Metadata) oder einen expliziten Rebuild-Pfad.

**Zuordnung:** EPIC-007/V3

---

## F-E-12: Weitere unbelegte Render-Heuristiken `LINE_K`, `Y_OFF_K` und Padding-Konstanten

**Beleg:** `spike-pptxgenjs/lib/text.js:17` (`const LINE_K = 0.9; // Zeilenabstand etwas enger (Original ist kompakt)`), Z. 20 (`const Y_OFF_K = 0.18;` mit Begründung Z. 18–19), angewandt Z. 53/65. Padding-Magic in Z. 56 (`w: e.w + 0.3, h: e.h + 0.12 // Padding gegen Clipping`). Frame-Bleed `BLEED = 2 * PX` (`lib/frame.js:11-12`), Gold-Toleranz `< 45` pro Kanal (`lib/frame.js:19`).

**Severity:** MEDIUM

Neben `SIZE_K` (F-E-01) tragen `LINE_K=0.9`, `Y_OFF_K=0.18` und die Box-Paddings `+0.3"/+0.12"` dieselbe Signatur: einzeln visuell justierte Konstanten ohne Messreihe, kommentiert mit qualitativen Begründungen („etwas enger", „gegen Clipping"). Sie verschieben Zeilenabstand, Block-Y und Boxgröße gegenüber dem Original und sind damit Teil derselben Treue-Unsicherheit wie F-E-01. Die Gold-Erkennung (`isGold`, Toleranz ±45 pro RGB-Kanal) ist großzügig genug, um Nicht-Gold-Töne als Frame/Sektion zu klassifizieren. Sammel-Finding: alle Render-Konstanten gehören gemeinsam gegen eine Pixel-Diff-Messreihe kalibriert/dokumentiert, statt einzeln nachjustiert.

**Zuordnung:** EPIC-005/T1

---

## F-E-13: Fehlendes Bild-Asset wird zu grauem Platzhalter-Rect — kein Fehler-Signal nach außen

**Beleg:** `spike-pptxgenjs/reconstruct.js:60-69` — bei `!fs.existsSync(src)` wird statt des Bildes ein `EEEEEE`-Rect mit `CCCCCC`-Rand gezeichnet, `P++` gezählt und nur `console.warn` ausgegeben; Z. 112 berichtet `P` Platzhalter nur in der Konsole. Aufrufer prüfen `P` nicht.

**Severity:** MEDIUM

Fehlt ein referenziertes Bild (z.B. weil `cached_deck`/`_deckpipe` die Asset-Pfade fehlerhaft namespaced hat, oder ein Logo nicht freigestellt wurde), produziert die Engine ein sichtbares graues Platzhalter-Rechteck im fertigen Deck und endet trotzdem mit Exit 0. Der Kunde bekäme ein Deck mit grauen Kästen an Foto-Positionen, ohne dass die Pipeline das als Fehler meldet. Wie F-E-08 fehlt ein Gate (`P > 0` sollte mindestens den Report markieren, ggf. fehlschlagen). Engine-relevant, weil der Platzhalter-Pfad in der Kernlogik `reconstruct.js` sitzt.

**Zuordnung:** EPIC-007/V4

---

## Methodik & Abgrenzung

- **Gegenprobe Doppelzählung (Pitfall §12.3):** F-E-01 (SIZE_K) und F-E-12 (LINE_K/Y_OFF_K) sind bewusst getrennt — F-E-01 ist der namentliche Verdachts-Kandidat #1 inkl. des Kommentar-Widerspruchs, F-E-12 sammelt die übrigen Render-Konstanten. F-E-06 (Weight-Quelle in extract.py) ist der zweite Teil von Kandidat #1 (im Feature-Kontext genannt: „Weight nur aus erster Glyphe pro Zeile, extract.py Z. ~127") und hier als eigenständiges Finding mit präzisem Beleg (`extract.py:125-134`) geführt.
- **VERWORFEN-Belege (Pitfall §12.1):** F-E-04/F-E-05 sind mit negativem `find`-Beleg (kein Treffer im Engine-Repo) plus positivem Studio-Beleg geführt, nicht nur behauptet.
- **Kein Fix (Pitfall §12.2):** Reiner Analyse-Sprint — keine Zeile Produktiv-Code geändert. Boundaries eingehalten: nur `docs/sprint-10/` + `backend/tests/test_sprint10_us037.py` + `tools/.venv` geschrieben, beide Repos read-only gelesen, `phase0/data/cache/` nicht angefasst.
