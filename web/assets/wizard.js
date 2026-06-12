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
// Sie leben rein in-memory und gehen bei Reload bewusst verloren (US-076
// zeigt dann einen Hinweis). Persistiert werden nur Schritt/Auswahl/Texte.
const imageOverrides = {};   // {groupIdx: dataUrl} — flüchtig, NICHT persistiert

const emptyState = () => ({
  version: 1,
  source: null,        // {type:'upload'|'offer', id, label}
  offer: null,         // geparstes Angebot vom suggest-Response (Kontext)
  groups: [],          // Server-Reihenfolge: [{label, kind, candidates:[...]}]
  stepIndex: 0,        // 0 = Quelle; 1..N = je Gruppe; N+1 = Abschluss
  selections: {},      // {groupIdx: candIdx} — gewählte Alternative je Gruppe
  textOverrides: {},   // {groupIdx: {feld: text}} — editierte Texte (US-076)
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

// Cover-Bild (US-075): /api/image (category "cover", 16:9, Negativraum für
// Titel-Overlay; Muster designer.js generateCover). Liefert die Bild-Data-URL
// oder null bei 401-Redirect; wirft bei !ok.
async function generateImage(prompt) {
  const r = await api("/api/image", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, table: false, category: "cover" }),
  });
  if (!r) return null;                       // 401 -> Redirect bereits erfolgt
  const data = await r.json().catch(() => null);
  if (!r.ok || !data || !data.image) {
    throw new Error((data && data.error) || `Fehler ${r.status}`);
  }
  return data.image;
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

// Stage: gewählte Alternative groß. US-074-Stub wird hier gefüllt; das
// Overlay (editierbare Texte / aufgelöstes Cover-Bild) folgt in US-076.
function renderStage() {
  const stage = $("wizard-stage");
  if (!stage) return;
  const gi = currentGroupIdx();
  const g = state.groups[gi];
  const cands = (g && g.candidates) || [];
  const c = cands[selectedCandIdx(gi)];
  if (!c) {
    stage.innerHTML = '<div class="wz-stage-empty">Wähle oben eine Alternative.</div>';
    return;
  }
  stage.innerHTML = `<img src="${esc(c.preview)}" alt="${esc(c.label)}" `
    + `onerror="this.parentNode.innerHTML='<div class=\\'wz-stage-empty\\'>`
    + `Vorschau nicht verfügbar.</div>'">`;
}

// --- US-075: Cover-Schritt (Gruppe kind=="cover") -------------------------
// "✨ generieren" -> /api/image -> Ergebnis als pending image_override der
// Gruppe (in-memory, Pitfall 3). Die visuelle Auflösung auf der Stage folgt
// in US-076.

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

function renderCover() {
  // Cover-Generieren-Button nur im Cover-Schritt einblenden.
  const host = $("wz-cover-host");
  if (!host) return;
  const gi = currentGroupIdx();
  const g = state.groups[gi];
  const isCover = g && g.kind === "cover";
  host.hidden = !isCover;
  if (!isCover) return;
  const have = imageOverrides[gi];
  host.innerHTML =
    `<button type="button" class="btn" id="wz-gencover">`
    + `${have ? "Cover neu generieren" : "✨ Cover-Bild generieren"}</button>`
    + `<div id="wz-cover-status" class="wz-status"></div>`
    + (have ? `<img class="wz-cover-pending" src="${esc(have)}" `
      + `alt="Generiertes Cover (wird in US-076 auf die Stage gelegt)">` : "");
  const btn = $("wz-gencover");
  if (btn) btn.addEventListener("click", () => generateCoverFor(gi));
}

async function generateCoverFor(gi) {
  const st = $("wz-cover-status");
  const btn = $("wz-gencover");
  if (btn) btn.disabled = true;
  if (st) {
    st.textContent = "Cover-Bild wird generiert … (bis zu 1 Minute)";
    st.className = "wz-status wz-status-load";
  }
  try {
    const img = await generateImage(coverPrompt());
    if (img == null) return;                 // 401 -> Redirect lief schon
    // Pitfall 3: pending image_override IN-MEMORY (Data-URL, MB) — NICHT
    // in sessionStorage. US-076 löst das größte Bild-Element auf der Stage auf.
    imageOverrides[gi] = img;
    renderCover();
  } catch (e) {
    if (st) {
      st.textContent = "Cover-Bild fehlgeschlagen: " + (e.message || e);
      st.className = "wz-status wz-status-error";
    }
    if (btn) btn.disabled = false;
  }
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
