/* KOCHfabrik Studio — Wizard (geführter Flow).
 *
 * FEATURE-015 §4 (FEATURE-WIZARD-UI): geführte Kette Schritt 0 (Angebot) ->
 * je suggest-Gruppe ein Schritt ("Slide i von N: <label>") -> Abschluss
 * (Filmstreifen + Download).
 *
 * US-074: Gerüst + Schritt 0 + State-Maschine + Navigation.
 *   - versionierter State (sessionStorage) unter kfWizard.v1
 *   - API-Wrapper mit 401 -> /login.html-Redirect (Muster designer.js)
 *   - Schritt 0: Angebot (Upload-Dropzone | Dropdown) -> suggest -> groups
 *   - Schritt-Maschine: Gruppen = Schritte in SERVER-Reihenfolge (Pitfall 4,
 *     FE sortiert NICHT um), Weiter/Zurück + reload-feste Persistenz (EARS 6)
 * US-075: Alternativen-Leiste (#wizard-alts) füllen.
 * US-076: große Stage (#wizard-stage) + Overlay-Editor füllen.
 * US-077: Abschluss (Filmstreifen + Download + E2E).
 *
 * Vanilla, kein Framework/CDN (Bestands-Muster).
 */

// State-Schema versioniert (Pitfall §12.2): Key-Bump bei Schema-Bruch.
const STATE_KEY = "kfWizard.v1";

// Pitfall 3: Bild-Overrides (Data-URLs, MB!) gehören NICHT in sessionStorage.
// Sie leben rein in-memory und gehen bei Reload bewusst verloren (die Stage
// zeigt dann einen Hinweis). Schlüssel = "deck::page" -> {seqIdx: dataUrl},
// damit die Override an der Slide (nicht am Schritt) hängt und beim Wechsel
// der gewählten Alternative korrekt neu greift.
const imageOverrides = {};   // {"deck::page": {seqIdx: dataUrl}} — flüchtig

const emptyState = () => ({
  version: 1,
  source: null,        // {type:'upload'|'offer', id, label}
  offer: null,         // geparstes Angebot vom suggest-Response (Kontext)
  groups: [],          // Server-Reihenfolge: [{label, kind, candidates:[...]}]
  stepIndex: 0,        // 0 = Quelle; 1..N = je Gruppe; N+1 = Abschluss
  selections: {},      // {groupIdx: candIdx} — gewählte Alternative je Gruppe
  textOverrides: {},   // {"deck::page": {seqIdx: text}} — editierte Texte
  // W1: editierte Bild-Prompts je image-Element. NUR Text (Pitfall 3 bleibt:
  // die generierten Data-URLs leben weiter rein in-memory in imageOverrides).
  imagePrompts: {},    // {"deck::page": {imgIdx: prompt}}
  // Schriftart je Text-Element (PPTX-Font-Name, "" = Standard/aus Gewicht).
  fontOverrides: {},   // {"deck::page": {seqIdx: fontName}}
});

function loadState() {
  try {
    const raw = sessionStorage.getItem(STATE_KEY);
    if (!raw) return emptyState();
    const s = JSON.parse(raw);
    if (!s || s.version !== 1) return emptyState();
    // Defensive: fehlende Felder aus Alt-/Teil-States auffüllen.
    return {
      ...emptyState(), ...s,
      groups: Array.isArray(s.groups) ? s.groups : [],
      selections: s.selections || {},
      textOverrides: s.textOverrides || {},
      imagePrompts: s.imagePrompts || {},
      fontOverrides: s.fontOverrides || {},
    };
  } catch (e) {
    return emptyState();
  }
}

function saveState(s) {
  // Nur der persistierbare Teil-State (Pitfall 3: KEINE Bilder).
  try {
    sessionStorage.setItem(STATE_KEY, JSON.stringify({
      version: 1,
      source: s.source,
      offer: s.offer,
      groups: s.groups,
      stepIndex: s.stepIndex,
      selections: s.selections,
      textOverrides: s.textOverrides,
      imagePrompts: s.imagePrompts,
      fontOverrides: s.fontOverrides,
    }));
  } catch (e) {}
}

let state = loadState();

// --- API-Wrapper (401 -> Login-Redirect wie designer.js) ------------------
// Same-Origin -> Session-Cookie kf_sess wird automatisch mitgesendet.

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (r.status === 401) { location.href = "/login.html"; return null; }
  return r;
}

async function apiJson(path, opts) {
  const r = await api(path, opts);
  if (!r) return null;
  try { return await r.json(); } catch (e) { return null; }
}

// Angebots-Liste fürs Dropdown (gleiche Route wie bibliothek.html/designer.js).
async function fetchOffers() {
  const d = await apiJson("/api/angebote");
  return (d && d.offers) || [];
}

// suggest: drei Input-Zweige (FormData-PDF | {offer_id} | {offer}).
// Liefert {offer, groups[]}; wirft bei !ok mit gekürzter Server-Meldung,
// gibt null zurück, wenn 401 schon zum Login umgeleitet hat.
async function fetchSuggestions(payload) {
  const opts = (payload instanceof FormData)
    ? { method: "POST", body: payload }
    : { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload) };
  const r = await api("/api/designer/suggest", opts);
  if (!r) return null;                       // 401 -> Redirect bereits erfolgt
  const data = await r.json().catch(() => null);
  if (!r.ok) {
    const err = new Error((data && data.error) || `Fehler ${r.status}`);
    err.status = r.status;
    throw err;
  }
  return data;
}

// Bild generieren (US-075 Cover / US-076 Food): /api/image. category steuert
// den Stil ("cover" 16:9 Negativraum | "food"); Muster designer.js
// generateCover. Liefert die Bild-Data-URL oder null bei 401-Redirect.
async function generateImage(prompt, category) {
  const r = await api("/api/image", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, table: false, category: category || "cover" }),
  });
  if (!r) return null;                       // 401 -> Redirect bereits erfolgt
  const data = await r.json().catch(() => null);
  if (!r.ok || !data || !data.image) {
    throw new Error((data && data.error) || `Fehler ${r.status}`);
  }
  return data.image;
}

// Texte/Geometrie der gewählten Slide (US-076): /api/designer/texts liefert
// meta{w_pt,h_pt} + texts[] (i/text/x/y/w/h/size/color/weight/italic) +
// images[] (i/x/y/w/h) + preview_notext + suggestions. Slide-Objekt oder null.
async function fetchTexts(deck, page, kind, gang, offer) {
  const d = await apiJson("/api/designer/texts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      slides: [{ deck, page, kind: kind || null, gang: gang || null }],
      offer: offer || null,
    }),
  });
  return (d && d.slides && d.slides[0]) || null;
}

// Formulieren (US-076): /api/designer/formulate {text,kind,gang_label} ->
// {text}. Liefert den neuen Text oder null bei 401-Redirect; wirft bei !ok.
async function formulateText(text, kind, gangLabel) {
  const r = await api("/api/designer/formulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, kind: kind || null,
                           gang_label: gangLabel || null }),
  });
  if (!r) return null;                       // 401 -> Redirect bereits erfolgt
  const data = await r.json().catch(() => null);
  if (!r.ok || !data || !data.text) {
    throw new Error((data && data.error) || `Fehler ${r.status}`);
  }
  return data.text;
}

// Download (US-077): Storyboard -> PPTX-Bundle (Data-URL). slides tragen
// overrides (Text) + image_overrides (Data-URLs). Liefert das pptx-Data-URL
// oder null bei 401-Redirect; wirft bei !ok.
async function downloadDeck(slides) {
  const r = await api("/api/slidesuche/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slides }),
  });
  if (!r) return null;                       // 401 -> Redirect bereits erfolgt
  const data = await r.json().catch(() => null);
  if (!r.ok) {
    const err = new Error((data && data.error) || `Fehler ${r.status}`);
    err.status = r.status;
    throw err;
  }
  return data && data.pptx;
}

function triggerDataUrlDownload(dataUrl, filename) {
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// --- DOM-Helfer -----------------------------------------------------------
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s)
  .replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

function setStatus(msg, kind) {
  const el = $("wz-status");
  if (!el) return;
  el.textContent = msg || "";
  el.className = "wz-status" + (kind ? " wz-status-" + kind : "");
}

// --- Schritt-Modell -------------------------------------------------------
// Schritt 0 = Quelle. Schritte 1..N = Gruppen in SERVER-Reihenfolge
// (Pitfall 4: das FE sortiert NICHT um). Schritt N+1 = Abschluss.

function stepCount() {
  // Gesamtzahl Schritte: Quelle + N Gruppen + Abschluss.
  return state.groups.length ? state.groups.length + 2 : 1;
}

function isSourceStep() { return state.stepIndex === 0; }
function isFinishStep() {
  return state.groups.length > 0 && state.stepIndex === state.groups.length + 1;
}
function currentGroupIdx() {
  // Bei Slide-Schritten: 0-basierter Gruppen-Index (Schritt 1 -> Gruppe 0).
  return isSourceStep() || isFinishStep() ? -1 : state.stepIndex - 1;
}

// --- Rendering ------------------------------------------------------------

function renderStep() {
  const onSource = isSourceStep();
  const onFinish = isFinishStep();
  const hasDeck = state.groups.length > 0;

  // Quelle (volle Breite) vs. Navigator+Editor-Shell.
  $("wz-step0").hidden = !onSource;
  $("wz-shell").hidden = onSource || !hasDeck;
  $("wz-slide").hidden = onSource || onFinish;
  $("wz-finish").hidden = !onFinish;

  // Editor-Titel: auf den Slide-Schritten redundant zum Navigator links →
  // ausgeblendet. Nur der Abschluss-Schritt behält seine Überschrift.
  const title = $("wz-step-title"), sub = $("wz-step-sub");
  const head = $("wz-main-head");
  if (onFinish) {
    if (head) head.hidden = false;
    title.textContent = "Fertig — herunterladen";
    sub.textContent = "";
  } else if (head) {
    head.hidden = true;
  }

  // Slide-Schritt-Inhalt: Alternativen-Leiste + Stage (Overlay-Editor).
  if (!onSource && !onFinish) {
    ensureDefaultSelection(currentGroupIdx());
    renderAlts();
    renderStage();
    renderCover();
  }
  if (onFinish) renderFilm();                // US-077: Filmstreifen + Download
  renderNav();
}

// Slide-Navigator (PPT-Stil): vertikale Liste aller Gruppen (Server-Reihenfolge,
// Pitfall 4) mit Thumbnail der gewählten Alternative + Download-Eintrag. Klick
// springt direkt zum Slide-Schritt; ersetzt den linearen Weiter/Zurück-Stepper.
function renderNav() {
  const nav = $("wz-nav");
  if (!nav) return;
  if (!state.groups.length) { nav.innerHTML = ""; return; }
  nav.innerHTML = "";
  // Einstieg zurück zur Angebotsauswahl (Schritt 0) — sonst kommt man aus dem
  // Deck nicht mehr zum Angebots-Dropdown zurück.
  const src = document.createElement("button");
  src.type = "button";
  src.className = "wz-nav-item wz-nav-src"
    + (state.stepIndex === 0 ? " is-active" : "");
  src.innerHTML = `<span class="wz-nav-ix">≡</span>`
    + `<span class="wz-nav-lab">Angebot wechseln</span>`;
  src.addEventListener("click", () => goToStep(0));
  nav.appendChild(src);
  state.groups.forEach((g, gi) => {
    const stepIdx = gi + 1;
    const cand = (g.candidates || [])[selectedCandIdx(gi)];
    // Override-Bild bevorzugen (zeigt den echten Stand), sonst Kandidat-Preview.
    let thumb = cand ? cand.preview : "";
    if (cand) {
      const iov = imageOverrides[_slideKey(cand.deck, cand.page)];
      if (iov && Object.keys(iov).length) thumb = iov[Object.keys(iov)[0]];
    }
    const item = document.createElement("button");
    item.type = "button";
    item.className = "wz-nav-item" + (state.stepIndex === stepIdx ? " is-active" : "");
    item.innerHTML =
      `<span class="wz-nav-ix">${gi + 1}</span>`
      + `<span class="wz-nav-thumb">`
      + (thumb ? `<img src="${esc(thumb)}" alt="" `
          + `onerror="this.removeAttribute('src')">` : "")
      + `</span>`
      + `<span class="wz-nav-lab">${esc(g.label || "Slide")}</span>`;
    item.addEventListener("click", () => goToStep(stepIdx));
    nav.appendChild(item);
  });
  // Download-Eintrag (Abschluss-Schritt).
  const dlStep = state.groups.length + 1;
  const dl = document.createElement("button");
  dl.type = "button";
  dl.className = "wz-nav-item wz-nav-dl"
    + (state.stepIndex === dlStep ? " is-active" : "");
  dl.innerHTML = `<span class="wz-nav-ix">↓</span>`
    + `<span class="wz-nav-lab">Fertig &amp; Download</span>`;
  dl.addEventListener("click", () => goToStep(dlStep));
  nav.appendChild(dl);
}

// Direkt-Sprung zu einem Schritt (Slide oder Download). Kollabiert die
// Bilder-Liste neu (frische Slide startet aufgeräumt).
function goToStep(idx) {
  if (idx < 0 || idx >= stepCount()) return;
  state.stepIndex = idx;
  _imgsExpanded = false;
  _fieldsExpanded = false;
  saveState(state);
  renderStep();
}

// --- US-075: Alternativen + Auswahl ---------------------------------------
// EARS Nr. 1: 3-4 Alternativen je Schritt, Top-Kandidat (candidates[0])
// vorausgewählt. Pitfall 4: KEINE Umsortierung — Reihenfolge bleibt Server.

// max sichtbare Alternativen, Rest hinter "+N weitere" (Designer-Slot-Muster).

function ensureDefaultSelection(gi) {
  // Vorauswahl = Top-Kandidat candidates[0], falls noch keine Wahl getroffen.
  const g = state.groups[gi];
  if (!g || !g.candidates || !g.candidates.length) return;
  if (state.selections[gi] == null) {
    state.selections[gi] = 0;    // Index von candidates[0]
    saveState(state);
  }
}

function selectedCandIdx(gi) {
  const v = state.selections[gi];
  return v == null ? 0 : v;
}

function selectAlt(gi, candIdx) {
  state.selections[gi] = candIdx;
  saveState(state);
  renderAlts();
  renderStage();
}

let _altsExpanded = false;       // "+N weitere" je Schritt (flüchtig)
let _imgsExpanded = false;       // "+N weitere Bilder" je Slide (flüchtig)
let _fieldsExpanded = false;     // "+N weitere Felder" je Slide (flüchtig)

function renderAlts() {
  const wrap = $("wizard-alts");
  if (!wrap) return;
  const gi = currentGroupIdx();
  const g = state.groups[gi];
  const cands = (g && g.candidates) || [];
  // Gibt es nichts zu wählen (0/1 Variante), ist die Leiste nur eine
  // redundante Vorschau zur großen Folie + zum Navigator → ausblenden.
  if (cands.length <= 1) {
    wrap.innerHTML = "";
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const sel = selectedCandIdx(gi);
  // Max 4 sichtbar; Rest hinter "+N weitere" (Designer-Slot-Muster).
  const visible = _altsExpanded ? cands : cands.slice(0, 4);
  const rest = cands.length - visible.length;
  wrap.innerHTML = visible.map((c, i) => {
    const on = i === sel ? " wz-alt-on" : "";
    const score = (c.score != null) ? `· ${c.score}` : "";
    return `<button type="button" class="wz-alt${on}" data-cand="${i}">`
      + `<img src="${esc(c.preview)}" alt="${esc(c.label)}" `
      + `onerror="this.classList.add('wz-alt-missing');this.removeAttribute('src')">`
      + `<div class="wz-alt-cap">${esc(c.label) || "Slide"} ${score}</div>`
      + `</button>`;
  }).join("");
  if (rest > 0) {
    const more = document.createElement("button");
    more.type = "button";
    more.className = "wz-more";
    more.textContent = `+${rest} weitere`;
    more.addEventListener("click", () => { _altsExpanded = true; renderAlts(); });
    wrap.appendChild(more);
  }
  wrap.querySelectorAll(".wz-alt").forEach((btn) => {
    btn.addEventListener("click", () => selectAlt(gi, Number(btn.dataset.cand)));
  });
}

// --- US-076: Overlay-Editor (FEATURE-015 §8 Nr. 2+3+4) --------------------
// Stage = Notext-Hintergrund der gewählten Slide + absolut positionierte
// Text-Overlays (editierbar) und Bild-Overlays. Maßstab IMMER relativ aus
// meta.w_pt/h_pt (Pitfall 1, nie hartkodieren), ResizeObserver rechnet die
// Fontgrößen beim Layout-Wechsel nach.

const _slideKey = (deck, page) => `${deck}::${page}`;

// Cache der texts-API je Slide (vermeidet Re-Fetch beim Re-Render).
const _textsCache = {};          // {"deck::page": slideObj} — flüchtig
let _stageObserver = null;       // aktiver ResizeObserver der Stage

// Vorbelegung eines Felds: Override > Auto-Suggestion > Ist-Text.
function fieldValue(slide, idx) {
  const key = _slideKey(slide.deck, slide.page);
  const ov = state.textOverrides[key];
  if (ov && ov[idx] != null) return ov[idx];
  const sug = slide.suggestions || {};
  if (sug[idx] != null) return sug[idx];
  const t = (slide.texts || []).find((e) => e.i === idx);
  return t ? t.text : "";
}

function setTextOverride(deck, page, idx, value) {
  const key = _slideKey(deck, page);
  if (!state.textOverrides[key]) state.textOverrides[key] = {};
  state.textOverrides[key][idx] = value;
  saveState(state);
}

// Kuratierte, web-sichere Schriftarten: rendern zuverlässig im Browser-
// Preview UND als fontFace im PPTX (beim Empfänger meist vorhanden). label =
// Anzeige, ppt = Name im PPTX (leer = Standard/aus Gewicht), css = Overlay-Font.
const FONTS = [
  { label: "Standard", ppt: "", css: "" },
  { label: "Arial", ppt: "Arial", css: "Arial, sans-serif" },
  { label: "Helvetica", ppt: "Helvetica", css: "Helvetica, Arial, sans-serif" },
  { label: "Verdana", ppt: "Verdana", css: "Verdana, sans-serif" },
  { label: "Trebuchet MS", ppt: "Trebuchet MS", css: '"Trebuchet MS", sans-serif' },
  { label: "Tahoma", ppt: "Tahoma", css: "Tahoma, sans-serif" },
  { label: "Georgia", ppt: "Georgia", css: "Georgia, serif" },
  { label: "Times New Roman", ppt: "Times New Roman", css: '"Times New Roman", serif' },
  { label: "Garamond", ppt: "Garamond", css: "Garamond, serif" },
  { label: "Courier New", ppt: "Courier New", css: '"Courier New", monospace' },
];

function fontOverrideValue(deck, page, idx) {
  const ov = state.fontOverrides[_slideKey(deck, page)];
  return (ov && ov[idx]) || "";
}

// PPTX-Font-Name → CSS-Family fürs Overlay (Fallback: Name selbst + serif-frei).
function fontCss(ppt) {
  if (!ppt) return "";
  const f = FONTS.find((x) => x.ppt === ppt);
  return f ? f.css : `"${ppt}"`;
}

function setFontOverride(deck, page, idx, ppt) {
  const key = _slideKey(deck, page);
  if (!state.fontOverrides[key]) state.fontOverrides[key] = {};
  if (ppt) state.fontOverrides[key][idx] = ppt;
  else delete state.fontOverrides[key][idx];     // "" = Standard → entfernen
  if (!Object.keys(state.fontOverrides[key]).length) {
    delete state.fontOverrides[key];
  }
  saveState(state);
}

// Stage: gewählte Alternative groß. US-074-Stub wird hier gefüllt; lädt die
// texts-API asynchron und rendert dann die Overlays.
function renderStage() {
  const stage = $("wizard-stage");
  if (!stage) return;
  if (_stageObserver) { _stageObserver.disconnect(); _stageObserver = null; }
  const gi = currentGroupIdx();
  const g = state.groups[gi];
  const cands = (g && g.candidates) || [];
  const c = cands[selectedCandIdx(gi)];
  if (!c) {
    stage.innerHTML = '<div class="wz-stage-empty">Wähle oben eine Alternative.</div>';
    return;
  }
  const key = _slideKey(c.deck, c.page);
  const cached = _textsCache[key];
  if (cached) { renderStageOverlay(stage, g, c, cached); return; }
  stage.innerHTML = '<div class="wz-stage-empty">Slide wird geladen …</div>';
  fetchTexts(c.deck, c.page, g.kind, g.gang || null, state.offer)
    .then((slide) => {
      if (!slide) return;                    // 401 -> Redirect lief schon
      _textsCache[key] = slide;
      // Nur rendern, wenn noch derselbe Schritt/dieselbe Auswahl aktiv ist.
      const g2 = state.groups[currentGroupIdx()];
      const c2 = g2 && g2.candidates[selectedCandIdx(currentGroupIdx())];
      if (c2 && c2.deck === c.deck && c2.page === c.page) {
        renderStageOverlay(stage, g, c, slide);
      }
    })
    .catch(() => {
      stage.innerHTML = '<div class="wz-stage-empty">'
        + 'Texte konnten nicht geladen werden.</div>';
    });
}

function renderStageOverlay(stage, group, cand, slide) {
  const meta = slide.meta || { w_pt: 960, h_pt: 540 };
  // Overlay-Geometrie (x/y/w/h) kommt in ZOLL, meta.w_pt/h_pt in PUNKT (×72).
  // Direkt 100*x/w_pt zu rechnen ergab 72× zu kleine Boxen (5×2 px →
  // unsichtbar). Erst in Zoll umrechnen, dann als % der Folie.
  const wIn = (meta.w_pt || 960) / 72;
  const hIn = (meta.h_pt || 540) / 72;
  // Farben kommen als bare Hex ("FFFFFF") — ohne # ist es ungültiges CSS und
  // der Text fiel auf die dunkle Default-Farbe zurück (dunkel-auf-dunkel).
  const cssColor = (c) => (c && /^[0-9a-fA-F]{6}$/.test(c)) ? "#" + c : (c || null);
  // Hintergrund = preview_notext; onerror → normales preview + Notext-Badge.
  // Maßstab relativ: Overlays in % der Folie, Stage hält das 16:9-Format.
  stage.innerHTML = "";
  // 2-Spalten-WYSIWYG (#W1-Layout): links die Folie als Live-Vorschau
  // (sticky, bleibt beim Editieren sichtbar), rechts der scrollbare Editor.
  // Vorher hingen Folie + Feldlisten als zentrierte Flex-Geschwister im
  // Stage und zerstreuten sich über die Breite.
  const wrap = document.createElement("div");
  wrap.className = "wz-edit";
  const previewCol = document.createElement("div");
  previewCol.className = "wz-preview";
  const editorCol = document.createElement("div");
  editorCol.className = "wz-editor";
  wrap.appendChild(previewCol);
  wrap.appendChild(editorCol);
  stage.appendChild(wrap);

  const frame = document.createElement("div");
  frame.className = "wz-frame";
  frame.style.aspectRatio = `${meta.w_pt} / ${meta.h_pt}`;
  const bg = document.createElement("img");
  bg.className = "wz-bg";
  bg.src = slide.preview_notext;
  bg.alt = cand.label || "";
  bg.addEventListener("error", () => {
    // Fallback aufs normale preview + Hinweis-Badge (Texte sind dann
    // eingebrannt, der Editor liegt trotzdem darüber).
    bg.src = cand.preview;
    if (!frame.querySelector(".wz-notext-badge")) {
      const badge = document.createElement("div");
      badge.className = "wz-notext-badge";
      badge.textContent = "Notext-Vorschau fehlt — Texte ggf. doppelt";
      frame.appendChild(badge);
    }
  });
  frame.appendChild(bg);

  // Text-Overlays absolut positioniert in % (Pitfall 1). Hybrid-Edit
  // (Option 2): die Overlays sind JETZT direkt editierbar (contenteditable)
  // UND das rechte Feld-Panel bleibt bidirektional synchron. _eds: idx →
  // Overlay-Element, _tas: idx → Textarea — beide schreiben denselben
  // textOverride und spiegeln ins jeweils ANDERE (nur wenn es nicht den
  // Fokus hat → kein Caret-Sprung). #95-Lektion bewahrt: das Panel bleibt
  // sichtbare, verlässliche Eingabe (Affordanz, Mobile, Font/Bild/Formulieren).
  const _eds = {};
  const _tas = {};
  const k0 = _slideKey(cand.deck, cand.page);
  // Anti-Clutter (Preis-/Tabellen-Slides mit dutzenden Text-Zellen): bei >8
  // Texten nur die PROMINENTEN (große Schrift, dann große Fläche) editierbar
  // machen + im Feld-Panel zeigen. Die übrigen bleiben REINE Anzeige (kein
  // Rahmen/Tint, nicht editierbar) → die Folie sieht aus wie die echte Folie,
  // nur die relevanten Texte sind hervorgehoben statt 80 wilder Edit-Boxen.
  const _allTexts = slide.texts || [];
  const _COLLAPSE_AT = 8, _KEEP = 6;
  const _collapsing = _allTexts.length > _COLLAPSE_AT && !_fieldsExpanded;
  const _hasContent = (t) => (fieldValue(slide, t.i) || "").trim() !== "";
  // Beim Kollabieren NUR Felder mit Inhalt als prominent (nach Größe) — leere
  // Platzhalter-Frames (im Korpus oft groß) wandern hinter "+N weitere Felder"
  // statt als leere Eingabeboxen das Panel zu füllen und als Edit-Overlays die
  // Folie zu sprenkeln. Nach Expand (_fieldsExpanded) sind alle erreichbar.
  const _prominent = _collapsing
    ? new Set([..._allTexts]
        .filter(_hasContent)
        .sort((a, b) => (b.size || 0) - (a.size || 0)
          || (b.w * b.h) - (a.w * a.h))
        .slice(0, _KEEP).map((t) => t.i))
    : new Set(_allTexts.map((t) => t.i));
  _allTexts.forEach((t) => {
    const editable = _prominent.has(t.i);
    const ov = document.createElement("div");
    ov.className = "wz-tov" + (editable ? "" : " wz-tov-ro");
    ov.dataset.idx = t.i;
    ov.style.left = (100 * t.x / wIn) + "%";
    ov.style.top = (100 * t.y / hIn) + "%";
    ov.style.width = (100 * t.w / wIn) + "%";
    ov.style.height = (100 * t.h / hIn) + "%";
    const _col = cssColor(t.color);
    if (_col) ov.style.color = _col;
    if (t.weight) ov.style.fontWeight = t.weight;
    if (t.italic) ov.style.fontStyle = "italic";
    ov.dataset.size = String(t.size);        // pt; Fontgröße = size/h_pt*Höhe

    const ed = document.createElement("div");
    // Leere editierbare Felder: Klasse wz-ted-empty → Rahmen/Tint erst bei
    // Hover/Focus (sonst verstreute leere Kästen über der Folie). Discoverability
    // bleibt über das rechte Feld-Panel (#95).
    const val = fieldValue(slide, t.i);
    ed.className = "wz-ted" + (editable ? "" : " wz-ted-plain")
      + (editable && !val.trim() ? " wz-ted-empty" : "");
    ed.dataset.idx = t.i;
    ed.textContent = val;
    // Schriftart-Override live aufs Overlay (falls gesetzt).
    const _font = fontOverrideValue(cand.deck, cand.page, t.i);
    if (_font) ed.style.fontFamily = fontCss(_font);
    // #95: Angebots-Suggestion sofort committen — sonst wird sie nur
    // angezeigt, landet aber nie im Download (PPTX behielt den Originaltext).
    const hasOv = state.textOverrides[k0] && state.textOverrides[k0][t.i] != null;
    if (!hasOv && val !== t.text) {
      setTextOverride(cand.deck, cand.page, t.i, val);
    }
    if (editable) {
      ed.contentEditable = "plaintext-only";
      ed.spellcheck = false;
      // In-Place-Edit: Tippen auf der Folie schreibt den Override + spiegelt
      // in die Textarea (nur wenn die nicht gerade selbst fokussiert ist).
      ed.addEventListener("input", () => {
        const v = ed.innerText;
        setTextOverride(cand.deck, cand.page, t.i, v);
        ed.classList.toggle("wz-ted-empty", !v.trim());
        fitTed(ed);                                    // Auto-Fit bei Überlauf
        const ta = _tas[t.i];
        if (ta && document.activeElement !== ta) ta.value = v;
      });
      _eds[t.i] = ed;
    }
    ov.appendChild(ed);
    frame.appendChild(ov);
  });

  // Bild-Overlays: Rahmen je images[]-Element + 🖼-Generieren.
  const imgs = slide.images || [];
  imgs.forEach((im) => {
    const box = document.createElement("div");
    box.className = "wz-iov";
    box.dataset.idx = im.i;
    box.style.left = (100 * im.x / wIn) + "%";
    box.style.top = (100 * im.y / hIn) + "%";
    box.style.width = (100 * im.w / wIn) + "%";
    box.style.height = (100 * im.h / hIn) + "%";
    const ovImg = currentImageOverride(cand, im.i);
    if (ovImg) {
      const el = document.createElement("img");
      el.className = "wz-iov-img";
      el.src = ovImg;
      box.appendChild(el);
    }
    const gbtn = document.createElement("button");
    gbtn.type = "button";
    gbtn.className = "wz-iov-btn";
    gbtn.textContent = "🖼";
    gbtn.title = "Bild generieren";
    gbtn.addEventListener("click",
      () => generateImageOverlay(cand, group, im.i, box));
    box.appendChild(gbtn);
    frame.appendChild(box);
  });

  previewCol.appendChild(frame);
  applyOverlayFontSizes(frame, meta);
  // Pitfall 1: ResizeObserver rechnet die pt-basierten Fontgrößen nach,
  // wenn sich die Stage-Breite ändert.
  _stageObserver = new ResizeObserver(() => applyOverlayFontSizes(frame, meta));
  _stageObserver.observe(frame);

  // #95: Sichtbare Feldliste unter der Vorschau — DAS ist der Editor.
  // Echte textareas mit Label, vorbefüllt aus dem Angebot; Tippen
  // schreibt den Override und spiegelt live ins Bild oben.
  const texts = slide.texts || [];
  if (texts.length) {
    const list = document.createElement("div");
    list.className = "wz-fields";
    const head = document.createElement("div");
    head.className = "wz-fields-h";
    head.textContent = "Texte dieser Slide";
    list.appendChild(head);
    // Feld-Panel nutzt dieselbe Prominenz-Auswahl wie die Overlays (oben):
    // nur die prominenten Felder zeigen, Rest hinter "+N weitere Felder".
    const shown = texts.filter((t) => _prominent.has(t.i));
    const hiddenCount = texts.length - shown.length;
    shown.forEach((t) => {
      // Kompakte Zeile: Textarea + dezenter ✦-Icon-Button (Formulieren) oben
      // rechts. Kein doppelter Rahmen, kein redundantes Label (der Feldinhalt
      // IST der Text) und keine vollbreite Button-Zeile mehr → aufgeräumt.
      const row = document.createElement("div");
      row.className = "wz-field";
      const ta = document.createElement("textarea");
      ta.className = "wz-field-in";
      ta.rows = Math.min(4, ((fieldValue(slide, t.i) || "").split("\n").length) || 1);
      ta.value = fieldValue(slide, t.i);
      _tas[t.i] = ta;                                       // Hybrid-Mirror
      ta.addEventListener("input", () => {
        setTextOverride(cand.deck, cand.page, t.i, ta.value);
        // Spiegeln aufs Overlay — nur wenn es nicht selbst editiert wird
        // (sonst Caret-Sprung). textContent statt innerHTML (plain text).
        if (_eds[t.i] && document.activeElement !== _eds[t.i]) {
          _eds[t.i].textContent = ta.value;
          _eds[t.i].classList.toggle("wz-ted-empty", !ta.value.trim());
          fitTed(_eds[t.i]);
        }
      });
      const fbtn = document.createElement("button");
      fbtn.type = "button";
      fbtn.className = "wz-field-fmt";
      fbtn.textContent = "✦";
      fbtn.title = "Im KOCHfabrik-Ton neu formulieren";
      fbtn.setAttribute("aria-label", "Im KOCHfabrik-Ton neu formulieren");
      fbtn.addEventListener("click", async () => {
        const prev = ta.value;
        fbtn.disabled = true;
        try {
          const gangLabel = (group && group.kind === "gang") ? group.label : null;
          const out = await formulateText(prev, group && group.kind, gangLabel);
          if (out == null) return;             // 401 -> Redirect lief schon
          ta.value = out;
          setTextOverride(cand.deck, cand.page, t.i, out);
          if (_eds[t.i]) {
            _eds[t.i].textContent = out;
            _eds[t.i].classList.toggle("wz-ted-empty", !out.trim());
            fitTed(_eds[t.i]);
          }
        } catch (e) {
          setStatus("Formulieren fehlgeschlagen: " + (e.message || e), "error");
        } finally {
          fbtn.disabled = false;
        }
      });
      // Schriftart-Wähler (erscheint dezent bei Hover/Fokus, wie ✦).
      const fsel = document.createElement("select");
      fsel.className = "wz-field-font";
      fsel.title = "Schriftart dieses Textes";
      fsel.setAttribute("aria-label", "Schriftart dieses Textes");
      const curFont = fontOverrideValue(cand.deck, cand.page, t.i);
      FONTS.forEach((f) => {
        const o = document.createElement("option");
        o.value = f.ppt;
        o.textContent = f.label;
        if (f.ppt === curFont) o.selected = true;
        fsel.appendChild(o);
      });
      fsel.addEventListener("change", () => {
        setFontOverride(cand.deck, cand.page, t.i, fsel.value);
        if (_eds[t.i]) _eds[t.i].style.fontFamily = fontCss(fsel.value);
      });
      const tools = document.createElement("div");
      tools.className = "wz-field-tools";
      tools.appendChild(fsel);
      tools.appendChild(fbtn);
      row.appendChild(ta);
      row.appendChild(tools);
      list.appendChild(row);
    });
    if (hiddenCount > 0) {
      const more = document.createElement("button");
      more.type = "button";
      more.className = "wz-more";
      more.textContent = `+${hiddenCount} weitere Felder`;
      more.addEventListener("click", () => { _fieldsExpanded = true; renderStage(); });
      list.appendChild(more);
    }
    editorCol.appendChild(list);
  }

  // W1: "Bilder dieser Slide" — editierbarer Prompt je image-Element, mit
  // Vorschau-Thumbnail + Generieren. Spiegelt das #95-Text-Feldlisten-Muster
  // (Editieren unten, Overlay oben nur Anzeige). Bei vielen Bildern (z.B.
  // Cover mit 11 Platzhaltern): nur Hero + bereits generierte zeigen, Rest
  // hinter "+N weitere Bilder" (gegen Clutter).
  const imgList = slide.images || [];
  if (imgList.length) {
    const largest = largestImageIdx(slide);
    const ilist = document.createElement("div");
    ilist.className = "wz-imgs";
    const ihead = document.createElement("div");
    ihead.className = "wz-fields-h";
    ihead.textContent = "Bilder dieser Slide";
    ilist.appendChild(ihead);

    // Eine Zeile bauen (ord = Original-Ordinal fürs stabile Label).
    const buildImgRow = (im, ord) => {
      const row = document.createElement("div");
      row.className = "wz-img-row";

      const lab = document.createElement("div");
      lab.className = "wz-field-lab";
      lab.textContent = "Bild " + (ord + 1)
        + (im.i === largest ? " · groß (Titel/Hero)" : "");

      const ta = document.createElement("textarea");
      ta.className = "wz-img-prompt";
      ta.rows = 3;
      ta.value = imagePromptValue(cand, group, im.i);
      ta.placeholder = "Bild-Prompt …";
      ta.addEventListener("input", () => setImagePrompt(cand, im.i, ta.value));

      const tools = document.createElement("div");
      tools.className = "wz-img-tools";

      const thumb = document.createElement("div");
      thumb.className = "wz-img-thumb";
      const ovImg = currentImageOverride(cand, im.i);
      if (ovImg) {
        const t = document.createElement("img");
        t.src = ovImg;
        thumb.appendChild(t);
      } else {
        thumb.classList.add("is-empty");
        thumb.textContent = "—";
      }

      const status = document.createElement("div");
      status.className = "wz-status wz-img-status";

      const gen = document.createElement("button");
      gen.type = "button";
      gen.className = "btn wz-img-gen";
      gen.textContent = ovImg ? "✨ Neu generieren" : "✨ Bild generieren";
      gen.addEventListener("click",
        () => generateImageForField(cand, group, im.i, gen, status));

      tools.appendChild(thumb);
      tools.appendChild(gen);
      if (ovImg) {
        const clr = document.createElement("button");
        clr.type = "button";
        clr.className = "wz-img-clear";
        clr.textContent = "✕ entfernen";
        clr.addEventListener("click", () => {
          clearImageOverride(cand, im.i);
          renderStage();
        });
        tools.appendChild(clr);
      }
      tools.appendChild(status);

      row.appendChild(lab);
      row.appendChild(ta);
      row.appendChild(tools);
      ilist.appendChild(row);
    };

    // Kollabieren ab >2 Bildern: Hero + bereits generierte immer sichtbar,
    // Rest hinter Toggle. Ordinal bleibt am Original hängen.
    const collapsible = imgList.length > 2 && !_imgsExpanded;
    const alwaysShow = (im) =>
      im.i === largest || currentImageOverride(cand, im.i) != null;
    let hiddenCount = 0;
    imgList.forEach((im, ord) => {
      if (collapsible && !alwaysShow(im)) { hiddenCount++; return; }
      buildImgRow(im, ord);
    });
    if (hiddenCount > 0) {
      const more = document.createElement("button");
      more.type = "button";
      more.className = "wz-more";
      more.textContent = `+${hiddenCount} weitere Bilder`;
      more.addEventListener("click", () => { _imgsExpanded = true; renderStage(); });
      ilist.appendChild(more);
    }
    editorCol.appendChild(ilist);
  }
}

// Fontgröße = size_pt / h_pt * aktuelle Stage-Höhe (relativer Maßstab).
// h_pt wird am Frame hinterlegt, damit fitTed() ohne meta-Closure rechnen kann.
function applyOverlayFontSizes(frame, meta) {
  const h = frame.clientHeight;
  if (!h) return;
  frame.dataset.hpt = meta.h_pt;
  frame.querySelectorAll(".wz-ted").forEach((ed) => fitTed(ed));
}

// Treuer Render statt Auto-Fit-Heuristik: Die Schriftgröße kommt aus dem
// gerenderten PDF (LibreOffice hat PowerPoints Autofit/fontScale bereits
// eingebacken) — sie ist also schon final und korrekt. Wir übertragen sie nur
// maßstäblich auf die Stage (PDF-Punkt × Stage-Höhe / Folien-Höhe). KEIN
// Recompute aus der Box-Höhe, KEIN Shrink-Loop — das würde gegen die bereits
// korrekten PDF-Größen arbeiten (Ursache für "mal zu klein, mal Überlauf").
function fitTed(ed) {
  const ov = ed.parentNode;
  const frame = ov && ov.closest(".wz-frame");
  if (!frame) return;
  const h = frame.clientHeight;
  const hpt = parseFloat(frame.dataset.hpt || "0");
  const size = parseFloat(ov.dataset.size || "0");
  if (!h || !hpt || !size) return;
  ed.style.fontSize = (size / hpt * h) + "px";
}

// --- US-076: Bild-Overrides je Element + Cover-Auflösung ------------------
// Cover (US-075) liefert ein pending image_override, das HIER aufs GRÖSSTE
// image-Element der gewählten Slide aufgelöst wird (largest by w*h).

function imgKey(cand) { return _slideKey(cand.deck, cand.page); }

function currentImageOverride(cand, idx) {
  const m = imageOverrides[imgKey(cand)];
  return m ? m[idx] : null;
}

function setImageOverride(cand, idx, dataUrl) {
  const key = imgKey(cand);
  if (!imageOverrides[key]) imageOverrides[key] = {};
  imageOverrides[key][idx] = dataUrl;        // in-memory (Pitfall 3)
}

function largestImageIdx(slide) {
  const imgs = slide.images || [];
  if (!imgs.length) return null;
  return imgs.reduce((best, im) =>
    (im.w * im.h) > (best.w * best.h) ? im : best, imgs[0]).i;
}

function clearImageOverride(cand, idx) {
  const key = imgKey(cand);
  const m = imageOverrides[key];
  if (!m) return;
  delete m[idx];
  if (!Object.keys(m).length) delete imageOverrides[key];
}

// --- W1: editierbarer Bild-Prompt je image-Element ------------------------
// Default = der schritt-passende Auto-Prompt (Cover -> coverPrompt, sonst
// foodPrompt). Beide sind hoisted function declarations, daher hier nutzbar.
function defaultImagePrompt(group) {
  return (group && group.kind === "cover") ? coverPrompt() : foodPrompt(group);
}

function imageCategory(group) {
  return (group && group.kind === "cover") ? "cover" : "food";
}

// Aktueller Prompt: editierter Wert (persistiert) > Auto-Prompt.
function imagePromptValue(cand, group, idx) {
  const m = state.imagePrompts[imgKey(cand)];
  if (m && m[idx] != null) return m[idx];
  return defaultImagePrompt(group);
}

function setImagePrompt(cand, idx, value) {
  const key = imgKey(cand);
  if (!state.imagePrompts[key]) state.imagePrompts[key] = {};
  state.imagePrompts[key][idx] = value;
  saveState(state);
}

function coverPrompt() {
  // #95: Cover = atmosphärischer TITEL-Hintergrund, NICHT die Speisen.
  // Früher hängten wir die Gang-Labels an → Gemini machte ein Essensbild
  // trotz background-Scaffold. Jetzt Anlass/Location/Stimmung als
  // Aufhänger, Speisen bleiben draußen.
  const o = state.offer || {};
  const parts = ["Stimmungsvoller, atmosphärischer Veranstaltungs-Hintergrund "
    + "für ein gehobenes Catering-Event"];
  if (o.anlass) parts.push("Anlass: " + o.anlass);
  else if (o.kunde) parts.push("Kunde: " + o.kunde);
  if (o.ort) parts.push("Location: " + o.ort);
  parts.push("elegante Eventstimmung, viel ruhiger Negativraum oben "
    + "für einen Titel, kein Speisen-Close-up");
  return parts.join(", ");
}

// Food-Prompt eines Gang-/Gericht-Schritts (US-076 Bild-Element).
function foodPrompt(group) {
  const parts = ["Gericht-Foto, appetitlich, KOCHfabrik-Catering"];
  if (group && group.label) parts.push(group.label);
  const dishes = (group && group.gang && group.gang.dishes) || [];
  const names = dishes.map((d) => d.name).filter(Boolean);
  if (names.length) parts.push(names.join(", "));
  return parts.join(" — ");
}

// Cover-Generieren-Panel nur im Cover-Schritt; das erzeugte Bild wird aufs
// größte image-Element der gewählten Slide aufgelöst.
function renderCover() {
  const host = $("wz-cover-host");
  if (!host) return;
  const gi = currentGroupIdx();
  const g = state.groups[gi];
  const isCover = g && g.kind === "cover";
  host.hidden = !isCover;
  if (!isCover) return;
  host.innerHTML =
    `<button type="button" class="btn" id="wz-gencover">`
    + `✨ Cover-Bild generieren</button>`
    + `<div id="wz-cover-status" class="wz-status"></div>`;
  const btn = $("wz-gencover");
  if (btn) btn.addEventListener("click", () => generateCoverFor());
}

async function generateCoverFor() {
  const gi = currentGroupIdx();
  const g = state.groups[gi];
  const cand = g && g.candidates[selectedCandIdx(gi)];
  if (!cand) return;
  const slide = _textsCache[_slideKey(cand.deck, cand.page)];
  const idx = slide ? largestImageIdx(slide) : null;
  const st = $("wz-cover-status");
  const btn = $("wz-gencover");
  if (btn) btn.disabled = true;
  if (st) {
    st.textContent = "Cover-Bild wird generiert … (bis zu 1 Minute)";
    st.className = "wz-status wz-status-load";
  }
  try {
    const img = await generateImage(coverPrompt(), "cover");
    if (img == null) return;                 // 401 -> Redirect lief schon
    if (idx != null) {
      // Auf das größte image-Element auflösen (Pitfall 3: in-memory).
      setImageOverride(cand, idx, img);
      renderStage();
    }
    if (st) { st.textContent = ""; st.className = "wz-status"; }
  } catch (e) {
    if (st) {
      st.textContent = "Cover-Bild fehlgeschlagen: " + (e.message || e);
      st.className = "wz-status wz-status-error";
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// 🖼 je image-Element (Overlay-Shortcut): generiert mit dem AKTUELLEN
// (ggf. editierten) Prompt aus dem Store → in-memory Override, deckt das
// Element positionsgenau (das <img> liegt im positionierten .wz-iov-Rahmen).
async function generateImageOverlay(cand, group, idx, box) {
  const gbtn = box.querySelector(".wz-iov-btn");
  if (gbtn) gbtn.disabled = true;
  try {
    const img = await generateImage(imagePromptValue(cand, group, idx),
                                    imageCategory(group));
    if (img == null) return;                 // 401 -> Redirect lief schon
    setImageOverride(cand, idx, img);
    renderStage();
  } catch (e) {
    setStatus("Bild generieren fehlgeschlagen: " + (e.message || e), "error");
    if (gbtn) gbtn.disabled = false;
  }
}

// W1: Generieren aus der Feldliste — nutzt den im Textfeld stehenden Prompt
// (bereits via setImagePrompt persistiert). Statuszeile lokal an der Zeile.
async function generateImageForField(cand, group, idx, btn, statusEl) {
  const prompt = imagePromptValue(cand, group, idx).trim();
  if (!prompt) {
    if (statusEl) {
      statusEl.textContent = "Prompt ist leer.";
      statusEl.className = "wz-status wz-status-error";
    }
    return;
  }
  if (btn) btn.disabled = true;
  if (statusEl) {
    statusEl.textContent = "Bild wird generiert … (bis zu 1 Minute)";
    statusEl.className = "wz-status wz-status-load";
  }
  try {
    const img = await generateImage(prompt, imageCategory(group));
    if (img == null) return;                 // 401 -> Redirect lief schon
    setImageOverride(cand, idx, img);
    renderStage();                           // baut Stage + Feldliste neu (Thumb)
  } catch (e) {
    if (statusEl) {
      statusEl.textContent = "Fehlgeschlagen: " + (e.message || e);
      statusEl.className = "wz-status wz-status-error";
    }
    if (btn) btn.disabled = false;
  }
}

// ✦ Feld neu formulieren (Undo speichert den vorherigen Wert).
async function formulateField(cand, group, idx, ed) {
  const prev = ed.innerText;                 // für Undo
  const gangLabel = (group && group.kind === "gang") ? group.label : null;
  setStatus("Wird formuliert …", "load");
  try {
    const out = await formulateText(prev, group && group.kind, gangLabel);
    if (out == null) return;                 // 401 -> Redirect lief schon
    ed.innerText = out;
    setTextOverride(cand.deck, cand.page, idx, out);
    // Undo: ein Klick stellt den vorherigen Wert wieder her.
    showFormulateUndo(cand, idx, ed, prev);
    setStatus("");
  } catch (e) {
    setStatus("Formulieren fehlgeschlagen: " + (e.message || e), "error");
  }
}

function showFormulateUndo(cand, idx, ed, prev) {
  const el = $("wz-status");
  if (!el) return;
  el.className = "wz-status";
  el.innerHTML = 'Neu formuliert. <button type="button" class="wz-undo" '
    + 'id="wz-undo">↶ Undo</button>';
  const ub = $("wz-undo");
  if (ub) ub.addEventListener("click", () => {
    ed.innerText = prev;
    setTextOverride(cand.deck, cand.page, idx, prev);
    setStatus("");
  });
}

// --- US-077: Abschluss — Filmstreifen + Download --------------------------
// Die gewählten Slides in SERVER-Reihenfolge (Pitfall 4) → Filmstreifen +
// PPTX-Download. Payload je Slide: {deck, page, overrides, image_overrides}.

// Die gewählten Slides in Gruppen-Reihenfolge (eine je Gruppe mit Kandidaten).
function chosenSlides() {
  const out = [];
  state.groups.forEach((g, gi) => {
    const cands = g.candidates || [];
    if (!cands.length) return;
    const c = cands[selectedCandIdx(gi)];
    if (c) out.push({ deck: c.deck, page: c.page, label: c.label, gi });
  });
  return out;
}

// Download-Payload: overrides (Text, leere = entfernen) + image_overrides.
function downloadPayload() {
  return chosenSlides().map((s) => {
    const key = _slideKey(s.deck, s.page);
    const tov = state.textOverrides[key];
    const iov = imageOverrides[key];
    const fov = state.fontOverrides[key];
    const slide = { deck: s.deck, page: s.page };
    if (tov && Object.keys(tov).length) slide.overrides = tov;
    if (iov && Object.keys(iov).length) slide.image_overrides = iov;
    if (fov && Object.keys(fov).length) slide.font_overrides = fov;
    return slide;
  });
}

function renderFilm() {
  const film = $("wz-film");
  const dl = $("wz-download");
  const slides = chosenSlides();
  if (film) {
    if (!slides.length) {
      film.innerHTML = '<div class="wz-stage-empty">Keine Slides gewählt.</div>';
    } else {
      // Statische Mini-Stage je Slide: Override-Bild deckt das Element, sonst
      // das preview-PNG der gewählten Karte (Overlay-Thumbs reichen hier).
      film.innerHTML = slides.map((s, i) => {
        const key = _slideKey(s.deck, s.page);
        const iov = imageOverrides[key];
        const big = iov && Object.keys(iov).length
          ? iov[Object.keys(iov)[0]] : null;
        const cand = state.groups[s.gi].candidates[selectedCandIdx(s.gi)];
        const src = big || (cand && cand.preview) || "";
        return `<div class="wz-film-item"><span class="wz-film-ix">${i + 1}</span>`
          + `<img src="${esc(src)}" alt="${esc(s.label)}" `
          + `onerror="this.classList.add('wz-alt-missing');this.removeAttribute('src')">`
          + `</div>`;
      }).join("");
    }
  }
  if (dl) dl.disabled = !slides.length;
}

async function runDownload() {
  const dl = $("wz-download");
  const slides = downloadPayload();
  if (!slides.length) return;
  const prev = dl ? dl.textContent : "";
  if (dl) { dl.disabled = true; dl.textContent = "Erzeuge PPTX …"; }
  setStatus("PPTX wird erzeugt …", "load");
  try {
    const pptx = await downloadDeck(slides);
    if (pptx) {
      triggerDataUrlDownload(pptx, "kochfabrik-wizard.pptx");
      setStatus("");
    }
  } catch (e) {
    setStatus(e.message || "Download fehlgeschlagen.", "error");
  } finally {
    if (dl) { dl.textContent = prev || "Download"; dl.disabled = !slides.length; }
  }
}

// "Von vorn": State + in-memory-Overrides leeren, zurück auf Schritt 0.
function resetWizard() {
  state = emptyState();
  for (const k of Object.keys(imageOverrides)) delete imageOverrides[k];
  for (const k of Object.keys(_textsCache)) delete _textsCache[k];
  _altsExpanded = false;
  saveState(state);
  const sel = $("wz-offer");
  if (sel) sel.value = "";
  setStatus("");
  renderStep();
}

// --- Schritt-0: Quelle wählen ---------------------------------------------

async function loadOffers() {
  const sel = $("wz-offer");
  if (!sel) return;
  const offers = await fetchOffers();
  for (const o of offers) {
    const opt = document.createElement("option");
    opt.value = o.offer_id;
    opt.textContent = `${o.angebotsnummer || "—"} · ${o.kunde || ""}`.trim();
    sel.appendChild(opt);
  }
}

// suggest -> state.groups (Server-Reihenfolge, FE sortiert NICHT) -> Schritt 1.
async function startFromPayload(payload, sourceMeta) {
  setStatus("Vorschläge werden geladen …", "load");
  try {
    const data = await fetchSuggestions(payload);
    if (!data) return;                       // 401 -> Redirect
    state.source = sourceMeta;
    state.offer = data.offer || null;
    state.groups = Array.isArray(data.groups) ? data.groups : [];
    state.selections = {};
    state.textOverrides = {};
    state.stepIndex = state.groups.length ? 1 : 0;
    saveState(state);
    setStatus(state.groups.length
      ? "" : "Keine Vorschlags-Gruppen für dieses Angebot.",
      state.groups.length ? "" : "error");
    renderStep();
  } catch (e) {
    setStatus(e.message || "Fehler beim Laden der Vorschläge.", "error");
  }
}

function onOfferPicked() {
  const sel = $("wz-offer");
  const id = sel && sel.value;
  if (!id) return;
  const label = sel.options[sel.selectedIndex].textContent;
  startFromPayload({ offer_id: id }, { type: "offer", id, label });
}

function onFilePicked(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  startFromPayload(fd, { type: "upload", id: file.name, label: file.name });
}

// --- Init -----------------------------------------------------------------

function bind() {
  const drop = $("wz-upload"), file = $("wz-file");
  if (drop && file) {
    drop.addEventListener("click", () => file.click());
    drop.addEventListener("dragover", (e) => {
      e.preventDefault(); drop.classList.add("wz-drop-over");
    });
    drop.addEventListener("dragleave", () => drop.classList.remove("wz-drop-over"));
    drop.addEventListener("drop", (e) => {
      e.preventDefault(); drop.classList.remove("wz-drop-over");
      onFilePicked(e.dataTransfer.files && e.dataTransfer.files[0]);
    });
    file.addEventListener("change", () => onFilePicked(file.files && file.files[0]));
  }
  const offer = $("wz-offer");
  if (offer) offer.addEventListener("change", onOfferPicked);

  const dl = $("wz-download");
  if (dl) dl.addEventListener("click", runDownload);
  const reset = $("wz-reset");
  if (reset) reset.addEventListener("click", resetWizard);

  const logout = $("logout");
  if (logout) logout.addEventListener("click", async (e) => {
    e.preventDefault();
    await fetch("/api/logout", { method: "POST" });
    location.href = "/login.html";
  });
}

function init() {
  bind();
  loadOffers();
  // Restore (EARS 6): reload-fest aus sessionStorage, Schritt-Position erhalten.
  // Bei zurückgesetztem/leerem State landen wir wieder auf Schritt 0.
  if (state.stepIndex >= stepCount()) state.stepIndex = 0;
  renderStep();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
