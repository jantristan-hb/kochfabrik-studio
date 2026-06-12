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

function renderProgress() {
  const wrap = $("wizard-progress");
  if (!wrap) return;
  if (!state.groups.length) { wrap.innerHTML = ""; return; }
  // Chips: Quelle, je Gruppe einer, Abschluss — in Server-Reihenfolge.
  const labels = ["Angebot", ...state.groups.map((g) => g.label || "Slide"),
                  "Download"];
  wrap.innerHTML = labels.map((lab, i) => {
    const cls = i === state.stepIndex ? "is-active"
      : i < state.stepIndex ? "is-done" : "";
    return `<span class="wz-prog-step ${cls}">`
      + `<span class="wz-prog-ix">${i + 1}</span>${esc(lab)}</span>`;
  }).join("");
}

function renderStep() {
  const total = stepCount();
  // Panels umschalten.
  const onSource = isSourceStep();
  const onFinish = isFinishStep();
  $("wz-step0").hidden = !onSource;
  $("wz-slide").hidden = onSource || onFinish;
  $("wz-finish").hidden = !onFinish;

  // Titel/Subtitel.
  const title = $("wz-step-title"), sub = $("wz-step-sub");
  if (onSource) {
    title.textContent = "Angebot wählen";
    sub.textContent = "";
  } else if (onFinish) {
    title.textContent = "Fertig — herunterladen";
    sub.textContent = "";
  } else {
    const gi = currentGroupIdx();
    const g = state.groups[gi];
    // "Slide i von N: <label>" — i/N zählen nur die Gruppen-Schritte.
    title.textContent = `Slide ${gi + 1} von ${state.groups.length}`;
    sub.textContent = g ? (g.label || "") : "";
  }

  // Steuer-Buttons.
  const back = $("wz-back"), next = $("wz-next");
  back.disabled = state.stepIndex === 0;
  next.disabled = onSource || onFinish;            // Schritt 0 schaltet via suggest weiter
  next.textContent = (state.stepIndex === total - 2) ? "Abschluss →" : "Weiter →";

  // Slide-Schritt-Inhalt: Alternativen-Leiste + Stage (US-076 ergänzt Overlay).
  if (!onSource && !onFinish) {
    ensureDefaultSelection(currentGroupIdx());
    renderAlts();
    renderStage();
    renderCover();
  }
  renderProgress();
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

function renderAlts() {
  const wrap = $("wizard-alts");
  if (!wrap) return;
  const gi = currentGroupIdx();
  const g = state.groups[gi];
  const cands = (g && g.candidates) || [];
  if (!cands.length) {
    wrap.innerHTML = '<div class="wz-stage-empty">Keine Alternativen.</div>';
    return;
  }
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
  // Hintergrund = preview_notext; onerror → normales preview + Notext-Badge.
  // Maßstab relativ: Overlays in % von w_pt/h_pt, Stage hält das 16:9-Format.
  stage.innerHTML = "";
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

  // Text-Overlays absolut positioniert in % (Pitfall 1).
  (slide.texts || []).forEach((t) => {
    const ov = document.createElement("div");
    ov.className = "wz-tov";
    ov.dataset.idx = t.i;
    ov.style.left = (100 * t.x / meta.w_pt) + "%";
    ov.style.top = (100 * t.y / meta.h_pt) + "%";
    ov.style.width = (100 * t.w / meta.w_pt) + "%";
    ov.style.height = (100 * t.h / meta.h_pt) + "%";
    if (t.color) ov.style.color = t.color;
    if (t.weight) ov.style.fontWeight = t.weight;
    if (t.italic) ov.style.fontStyle = "italic";
    ov.dataset.size = String(t.size);        // pt; Fontgröße = size/h_pt*Höhe

    const ed = document.createElement("div");
    ed.className = "wz-ted";
    ed.contentEditable = "plaintext-only";
    ed.dataset.idx = t.i;
    ed.textContent = fieldValue(slide, t.i);
    // Pitfall 2: plain-text erzwingen — paste-Strip, Enter = \n.
    ed.addEventListener("paste", (e) => {
      e.preventDefault();
      const txt = (e.clipboardData || window.clipboardData).getData("text");
      document.execCommand("insertText", false, txt);
    });
    ed.addEventListener("input", () => {
      setTextOverride(cand.deck, cand.page, t.i, ed.innerText);
    });
    ov.appendChild(ed);

    // ✦ Formulieren je Feld (US-076, /api/designer/formulate) + Undo.
    const tools = document.createElement("div");
    tools.className = "wz-tov-tools";
    const fbtn = document.createElement("button");
    fbtn.type = "button";
    fbtn.className = "wz-tov-btn";
    fbtn.textContent = "✦";
    fbtn.title = "Im KOCHfabrik-Ton neu formulieren";
    fbtn.addEventListener("click",
      () => formulateField(cand, group, t.i, ed));
    tools.appendChild(fbtn);
    ov.appendChild(tools);
    frame.appendChild(ov);
  });

  // Bild-Overlays: Rahmen je images[]-Element + 🖼-Generieren.
  const imgs = slide.images || [];
  imgs.forEach((im) => {
    const box = document.createElement("div");
    box.className = "wz-iov";
    box.dataset.idx = im.i;
    box.style.left = (100 * im.x / meta.w_pt) + "%";
    box.style.top = (100 * im.y / meta.h_pt) + "%";
    box.style.width = (100 * im.w / meta.w_pt) + "%";
    box.style.height = (100 * im.h / meta.h_pt) + "%";
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

  stage.appendChild(frame);
  applyOverlayFontSizes(frame, meta);
  // Pitfall 1: ResizeObserver rechnet die pt-basierten Fontgrößen nach,
  // wenn sich die Stage-Breite ändert.
  _stageObserver = new ResizeObserver(() => applyOverlayFontSizes(frame, meta));
  _stageObserver.observe(frame);
}

// Fontgröße = size_pt / h_pt * aktuelle Stage-Höhe (relativer Maßstab).
function applyOverlayFontSizes(frame, meta) {
  const h = frame.clientHeight;
  if (!h) return;
  frame.querySelectorAll(".wz-ted").forEach((ed) => {
    const ov = ed.parentNode;
    const size = parseFloat(ov.dataset.size || "0");
    if (size) ed.style.fontSize = (size / meta.h_pt * h) + "px";
  });
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

function coverPrompt() {
  // Prompt aus Angebots-Kontext (Muster designer.js coverPrompt).
  const o = state.offer || {};
  const labels = (state.groups || [])
    .filter((g) => g.kind === "gang" || g.kind === "konzept")
    .map((g) => g.label);
  const parts = ["Catering-Event"];
  if (o.kunde) parts.push("für " + o.kunde);
  if (labels.length) parts.push("Menü/Konzept: " + labels.join(", "));
  return parts.join(" ");
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

// 🖼 je image-Element: Food-Bild generieren → in-memory Override, deckt das
// Element positionsgenau (das <img> liegt im positionierten .wz-iov-Rahmen).
async function generateImageOverlay(cand, group, idx, box) {
  const gbtn = box.querySelector(".wz-iov-btn");
  if (gbtn) gbtn.disabled = true;
  try {
    const img = await generateImage(foodPrompt(group), "food");
    if (img == null) return;                 // 401 -> Redirect lief schon
    setImageOverride(cand, idx, img);
    renderStage();
  } catch (e) {
    setStatus("Bild generieren fehlgeschlagen: " + (e.message || e), "error");
    if (gbtn) gbtn.disabled = false;
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

// --- Navigation -----------------------------------------------------------

function nextStep() {
  if (state.stepIndex >= stepCount() - 1) return;
  state.stepIndex += 1;
  saveState(state);
  renderStep();
}

function prevStep() {
  if (state.stepIndex <= 0) return;
  state.stepIndex -= 1;
  saveState(state);
  renderStep();
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

  const back = $("wz-back"), next = $("wz-next");
  if (back) back.addEventListener("click", prevStep);
  if (next) next.addEventListener("click", nextStep);
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
