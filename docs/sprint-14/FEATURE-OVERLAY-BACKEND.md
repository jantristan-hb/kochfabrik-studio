---
key: KOCHFABRIK-FEATURE-014
status: approved
title: "Overlay-Backend: Element-Geometrie, Bild-Overrides, Formulieren, Ranking-Mix"
created: 2026-06-12
project: kochfabrik
---

# KOCHFABRIK-FEATURE-014: Overlay-Backend

> **Typ:** FEATURE (Brownfield-Delta, Backend). Sprint 14. Liefert dem
> Wizard die Element-Daten fürs Overlay-Editing, den Bild-Tausch im
> Download und die KI-Umformulierung.

## 3. Datenmodell (API-Verträge)

### Slide-Elements-Response (Erweiterung von /api/designer/texts)

| Feld | Typ | Beschreibung |
|---|---|---|
| `meta` | `object` | `{w_pt, h_pt}` aus elements.json `_meta` (Overlay-Maßstab!) |
| `texts[]` | wie #66 | + `x, y, w, h, color, weight, italic` je Element |
| `images[]` | `array` | `{i, x, y, w, h}` der `t=="image"`-Elemente |
| `preview_notext` | `string` | URL der textfreien Vorschau (404 → FE-Fallback auf preview) |

### Download-Erweiterung (SlideRef)

| Feld | Typ | Beschreibung |
|---|---|---|
| `image_overrides` | `dict[str,str]` | seq-Index → Data-URL (PNG/JPEG) — ersetzt `src` des image-Elements |

## 4. Flows

```
GET /api/slidesuche/preview-notext/{deck}/{page}.png
  → cache/<deck>/preview_notext/p<page>.png; 404 wenn nicht gerendert
POST /api/designer/texts   (erweitert)
  → meta + texts(+Geometrie) + images + preview_notext-URL
POST /api/designer/formulate {text, kind?, gang_label?}
  → Anthropic (Muster angebot_chat): Umformulierung im KOCHfabrik-Ton;
    3-5 kuratierte Korpus-Textbeispiele (DNA) im Systemprompt;
    Antwort {text} — KEINE Längenexplosion (max ~2x Input)
POST /api/slidesuche/download  (erweitert)
  image_overrides: Data-URL decodieren → PNG in shared/_overrides/
  schreiben → element.src auf "_overrides/<name>.png" setzen.
  ⚠ NIEMALS in die Asset-Symlinks schreiben (zeigen in den read-only
  Cache!) — eigenes Verzeichnis im Bundle-Tempdir.
suggest-Ranking: bundle.rank_mixed statt rank (alpha aus Env
  KF_RANK_ALPHA, Default 0.7; ohne imgbundle → identisch zu heute)
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN /api/designer/texts für eine Cache-Slide antwortet THE SYSTEM
   SHALL Element-Geometrie (x/y/w/h in Folien-Einheiten) + meta
   (w_pt/h_pt) + die image-Elemente liefern — ausreichend, um Overlays
   pixelgenau zu positionieren.
2. WHEN der Download ein image_override (Data-URL) trägt THE SYSTEM
   SHALL das Bild im Bundle ablegen, die src des Elements ersetzen und
   die fertige PPTX SHALL das neue Bild enthalten (Zip-Beweis:
   ppt/media enthält das Override-Bild); der Cache SHALL unverändert
   bleiben.
3. WHEN /api/designer/formulate aufgerufen wird THE SYSTEM SHALL eine
   Umformulierung im KOCHfabrik-Ton liefern (Test: gemockter
   Anthropic-Client; Live-Smoke dokumentiert); IF der LLM-Call
   fehlschlägt THEN 502 mit gekürzter Meldung.
4. WHEN imgbundle.npz vorhanden ist THE SYSTEM SHALL suggest-Kandidaten
   über rank_mixed beziehen; IF nicht vorhanden THEN SHALL das
   Verhalten byte-identisch zu heute sein (Sim-Gate-Container hat kein
   imgbundle → graceful).

## 9. Abgrenzung (Nicht-Teil)

- Kein Live-Re-Render der Previews nach Edit (Variante D, bewusst)
- Keine Schrift-Vermessung/Auto-Fit im Overlay (FE rendert best-effort)
- Kein Bild-Upload durch den User (nur generierte Bilder; Upload später)

## 9a. Boundaries (3-Tier)

- ✅ **Always:** backend/routers/designer.py + backend/slidesuche.py
  additiv erweitern; Tests mit gemocktem Anthropic/Gemini
- ⚠️ **Ask-first (headless → BLOCKED):** neue Dependencies; Änderungen
  an reconstruct.js/lib (Bild-Tausch passiert in elements-Daten, NICHT
  im Renderer!)
- 🚫 **Never:** in Cache/Symlink-Ziele schreiben (R-NF-3!); rank()/
  bestehende Response-Felder ändern (nur additiv); echte LLM-Calls in
  der Suite; master pushen

## 10. Abgrenzung zum Ist

- texts-API (#66) liefert nur i/text/size → + Geometrie/meta/images/notext-URL
- Download kann Texte tauschen (#66) → + Bilder (inkl. generiertes Cover)
- suggest rankt text-only → optional Mix (Env-Schalter, Default an sobald Artefakt da)

## 11. Implementierungs-Anker (Ist)

`backend/routers/designer.py` (designer_texts, _slide_text_elements,
_suggest_overrides, _gang_groups→bundle.rank-Aufruf),
`backend/slidesuche.py:203-213` (SlideRef/DownloadReq + overrides),
`:248-290` (combined-Loop, Asset-Symlinks — Pitfall!), `_apply_overrides`,
Preview-Route (preview/{deck}/{page}.png — Muster für notext-Route),
`engine/scripts/angebot_chat.py:22-35` (Anthropic-Client + MODEL),
`engine/data/cache/*/elements.json` (`t:"image"` mit `src`
"<deck>/assets/<file>"; `_meta.w_pt/h_pt` — VARIIERT je Deck:
960×540 Präsis, 595×839 A4-Angebote!).

## 12. Bekannte Pitfalls

1. **Symlink-Falle:** `shared/<deck>/assets` ist Symlink in den
   READ-ONLY-Cache — Override-Bilder in `shared/_overrides/` (neues
   Verzeichnis), src relativ dazu. Schreiben in den Symlink = Schreiben
   in den Korpus = R-NF-3-Bruch.
2. **Maßstab pro Deck:** _meta.w_pt variiert (960 vs. 595) — Geometrie
   IMMER mit meta ausliefern, FE rechnet relativ; nichts hartkodieren.
3. **Data-URL-Größe:** generierte Bilder ~2-3 MB → Request-Limit
   prüfen/setzen (z.B. max 3 Bilder × 8 MB), 413 statt Crash.
4. **Sprint-12-Guards:** Routen-Inventar-Fixture um neue Routen
   ergänzen (additiv erlaubt); KEIN np.load außerhalb bundle.py —
   imgbundle-Laden gehört in bundle.load_img, nicht in den Router.
5. **Formulieren-Prompt-Drift:** DNA-Beispiele als Konstante im Router
   (3-5 echte Korpus-Formulierungen) — kein dynamisches Korpus-Lesen
   zur Laufzeit (Latenz/Brüchigkeit).

## Vision-Alignment

**Adressierte These:** R-DECK-5 (Text-Edit, jetzt voll), Vertrag
2026-001 §3.2 (Bildgenerierung + Zuschnitt in Folien, markengerechte
Textformulierung)
**Kern-Loop-Schritt:** Korpus-Slide → personalisierte Vorlage
**Nächste Iteration:** Dialog-Nachbearbeitung (Chat setzt dieselben Overrides)

## Referenzen
- implements → REQUIREMENTS R-DECK-5, R-DECK-4, R-NF-3 · Vertrag 2026-001 §3.2
- depends_on → [[KOCHFABRIK-FEATURE-013]] (notext + imgbundle)
- relates_to → [[KOCHFABRIK-FEATURE-015]] (Wizard-UI konsumiert alles)

## Referenziert von
— USER-STORIES Sprint 14 (US-070, US-071, US-072)
