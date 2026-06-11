/* KOCHfabrik Studio — Designer.
 *
 * Modul-Skelett: versionierter State (sessionStorage), API-Wrapper mit
 * 401 -> /login.html-Redirect (Muster aus chat.html), Init-Hook.
 *
 * US-063: Gerüst + State.
 * US-065: Storyboard-Modul — Add/Reorder/Remove/Zähler, Duplikat-Schutz,
 *         Session-Persistenz (reload-fest) + Restore (FEATURE-012 EARS 3).
 *         Karten-Klicks (US-064) feuern ein `designer:add`-Event; das Board
 *         hört darauf, ohne die Karten-Logik zu koppeln.
 * Klick-Verdrahtung der Quelle/Karten/Suche/Download folgt in US-064 ff.
 *
 * Vanilla, kein Framework/CDN (Bestands-Muster).
 */

// State-Schema versioniert (Pitfall §12.2): Key-Bump bei Schema-Bruch.
const STATE_KEY = "kfDesigner.v1";

const emptyState = () => ({
  version: 1,
  source: null,      // {type:'upload'|'offer', id, label}
  query: "",
  groups: [],        // [{title, items:[{png_url, slide_id, label}]}]
  board: [],         // geordnete Liste gewählter Items: {deck, page, png_url, label}
});

function loadState() {
  try {
    const raw = sessionStorage.getItem(STATE_KEY);
    if (!raw) return emptyState();
    const s = JSON.parse(raw);
    if (!s || s.version !== 1) return emptyState();
    // Defensive: fehlende Felder aus Alt-/Teil-States auffüllen.
    return { ...emptyState(), ...s, board: Array.isArray(s.board) ? s.board : [] };
  } catch (e) {
    return emptyState();
  }
}

function saveState(s) {
  try { sessionStorage.setItem(STATE_KEY, JSON.stringify(s)); } catch (e) {}
}

let state = loadState();

// --- API-Wrapper (401 -> Login-Redirect wie chat.html) --------------------
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

// --- Designer-API (US-064) ------------------------------------------------
// Angebots-Liste fürs Dropdown (gleiche Route wie bibliothek.html).
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

// Download (US-067): Storyboard -> PPTX-Bundle (Data-URL-Muster).
// Liefert das pptx-Data-URL oder null bei 401-Redirect; wirft bei !ok.
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

// Freitext-Suche (US-066): Slidesuche-ANN über den Korpus.
// Liefert das Treffer-Array (results) oder null bei 401-Redirect.
async function search(q) {
  const r = await api("/api/slidesuche/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: q, limit: 5 }),
  });
  if (!r) return null;                       // 401 -> Redirect bereits erfolgt
  const data = await r.json().catch(() => null);
  if (!r.ok) {
    const err = new Error((data && data.error) || `Fehler ${r.status}`);
    err.status = r.status;
    throw err;
  }
  return (data && data.results) || [];
}

// --- Storyboard-Modul (US-065) --------------------------------------------
// Identität einer Board-Karte = deck/page (Dedup-Schlüssel; deckt sich mit
// dem Download-Payload {slides:[{deck,page}]} und der Preview-Route
// /api/slidesuche/preview/{deck}/{page}.png).

function boardKey(it) { return `${it.deck}::${it.page}`; }

function boardIndexOf(item) {
  const k = boardKey(item);
  return state.board.findIndex((b) => boardKey(b) === k);
}

// Add (aus Karten-Klick). Duplikat-Schutz: gleiche deck/page nur 1×.
// Liefert true bei Aufnahme, false wenn bereits im Deck.
function addToBoard(item) {
  if (!item || item.deck == null || item.page == null) return false;
  if (boardIndexOf(item) !== -1) return false;
  state.board.push({
    deck: item.deck,
    page: item.page,
    png_url: item.png_url || item.preview || "",
    label: item.label || `${item.deck} / ${item.page}`,
  });
  persistAndRender();
  return true;
}

function removeFromBoard(index) {
  if (index < 0 || index >= state.board.length) return;
  state.board.splice(index, 1);
  persistAndRender();
}

// Reorder via ↑/↓ (kein Drag&Drop-Dep, FEATURE-012 §9).
function moveBoardItem(index, delta) {
  const target = index + delta;
  if (index < 0 || index >= state.board.length) return;
  if (target < 0 || target >= state.board.length) return;
  const [it] = state.board.splice(index, 1);
  state.board.splice(target, 0, it);
  persistAndRender();
}

function isOnBoard(item) { return boardIndexOf(item) !== -1; }

function persistAndRender() {
  saveState(state);              // Persistenz bei JEDER Änderung (EARS 3)
  renderBoard();
}

// --- DOM-Rendering des Storyboards ----------------------------------------

function el(tag, cls, txt) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (txt != null) n.textContent = txt;
  return n;
}

function renderBoard() {
  const host = document.getElementById("dz-board");
  const empty = document.getElementById("dz-board-empty");
  const dl = document.getElementById("dz-download");
  if (!host) return;

  host.innerHTML = "";
  const n = state.board.length;

  if (empty) empty.style.display = n === 0 ? "" : "none";
  if (dl) dl.disabled = n === 0;

  state.board.forEach((it, i) => {
    const row = el("div", "dz-board-item");
    row.dataset.deck = it.deck;
    row.dataset.page = it.page;

    row.appendChild(el("span", "dz-ix", String(i + 1)));

    if (it.png_url) {
      const img = document.createElement("img");
      img.className = "dz-board-thumb";
      img.src = it.png_url;
      img.alt = it.label || "";
      // Preview fehlt (404) -> Platzhalter statt Karte verwerfen (Pitfall §12.3 / EARS 5).
      img.onerror = () => { img.classList.add("dz-thumb-missing"); img.removeAttribute("src"); };
      row.appendChild(img);
    }

    row.appendChild(el("span", "dz-board-label", it.label || `${it.deck} / ${it.page}`));

    const ctrl = el("span", "dz-board-ctrl");
    const up = el("button", "btn btn-ghost dz-up", "↑");
    up.type = "button";
    up.title = "Nach oben";
    up.disabled = i === 0;
    up.addEventListener("click", () => moveBoardItem(i, -1));

    const down = el("button", "btn btn-ghost dz-down", "↓");
    down.type = "button";
    down.title = "Nach unten";
    down.disabled = i === n - 1;
    down.addEventListener("click", () => moveBoardItem(i, +1));

    const rm = el("button", "btn btn-ghost dz-remove", "✕");
    rm.type = "button";
    rm.title = "Entfernen";
    rm.addEventListener("click", () => removeFromBoard(i));

    ctrl.appendChild(up);
    ctrl.appendChild(down);
    ctrl.appendChild(rm);
    row.appendChild(ctrl);

    host.appendChild(row);
  });

  // Zähler im Spalten-Header (additiv, falls vorhanden).
  const counter = document.getElementById("dz-board-count");
  if (counter) counter.textContent = n ? `(${n})` : "";
}

// Karten-Klicks (US-064/066) feuern dieses Event; das Board entkoppelt sich
// so von der Karten-Render-Logik:  el.dispatchEvent(new CustomEvent(
//   "designer:add", {bubbles:true, detail:{deck,page,png_url,label}}))
function onDesignerAdd(ev) {
  if (ev && ev.detail) addToBoard(ev.detail);
}

// --- Vorschlags-Karten (US-064) -------------------------------------------
// Eine Kandidaten-Karte: PNG (onerror -> Platzhalter statt verwerfen,
// EARS 5), Label, Score. Klick dockt via designer:add ans Board (US-065).
// `card()` ist die gemeinsame Render-Funktion, die US-066 (Suche) mitnutzt.

function card(cand) {
  const c = el("button", "dz-card");
  c.type = "button";
  c.dataset.deck = cand.deck;
  c.dataset.page = cand.page;

  const img = document.createElement("img");
  img.loading = "lazy";
  img.src = cand.preview || cand.preview_url || "";
  img.alt = cand.label || cand.headline || "";
  // EARS 5: fehlt das Preview-PNG (404), Platzhalter setzen statt Karte killen.
  img.onerror = () => {
    img.classList.add("dz-thumb-missing");
    img.removeAttribute("src");
    c.classList.add("dz-card-placeholder");
  };
  c.appendChild(img);

  const cap = el("div", "dz-cap");
  cap.appendChild(el("span", "dz-cap-label",
    cand.label || cand.headline || `${cand.deck} / ${cand.page}`));
  if (typeof cand.score === "number") {
    cap.appendChild(el("span", "dz-cap-score", cand.score.toFixed(2)));
  }
  c.appendChild(cap);

  const detail = {
    deck: cand.deck, page: cand.page,
    png_url: cand.preview || cand.preview_url || "",
    label: cand.label || cand.headline || "",
  };
  const sync = () => c.classList.toggle("dz-card-on", isOnBoard(detail));
  c.addEventListener("click", () => {
    c.dispatchEvent(new CustomEvent("designer:add",
      { bubbles: true, detail }));
    sync();                                  // „im Deck"-Markierung
  });
  sync();
  return c;
}

// Vorschlags-Gruppen rendern: Spalte je Gruppe (Gang/Pflicht), Karten-Grid.
function renderGroups(groups) {
  const host = document.getElementById("dz-groups");
  const empty = document.getElementById("dz-groups-empty");
  if (!host) return;
  host.innerHTML = "";
  const list = groups || [];
  if (empty) empty.style.display = list.length ? "none" : "";
  list.forEach((g) => {
    const sec = el("div", "dz-group");
    sec.appendChild(el("div", "dz-group-h",
      g.label + (g.kind === "pflicht" ? " (Pflicht)" : g.kind === "konzept" ? " (aus Konzept)" : "")));
    const grid = el("div", "dz-cards");
    (g.candidates || []).forEach((cand) => grid.appendChild(card(cand)));
    sec.appendChild(grid);
    host.appendChild(sec);
  });
}

// --- Freitext-Suche (US-066) ----------------------------------------------
// Treffer im selben Karten-Format (card()), eigener Bereich #dz-results, der
// die Vorschlags-Gruppen NICHT ersetzt (EARS 2). Klick dockt wie Vorschläge
// ans Board (designer:add).

function renderResults(results, msg) {
  const host = document.getElementById("dz-results");
  if (!host) return;
  host.innerHTML = "";
  const list = results || [];
  if (!list.length) {
    host.appendChild(el("div", "dz-empty", msg || "Keine Treffer."));
    return;
  }
  const head = el("div", "dz-group-h", "Suchtreffer");
  host.appendChild(head);
  const grid = el("div", "dz-cards");
  list.forEach((hit) => grid.appendChild(card(hit)));
  host.appendChild(grid);
}

async function runSearch(q) {
  const query = (q || "").trim();
  if (!query) { renderResults([], "Suchbegriff eingeben."); return; }
  renderResults([], "Suche läuft …");
  try {
    const results = await search(query);
    if (results === null) return;            // 401 -> Redirect lief schon
    state.query = query;
    saveState(state);
    renderResults(results);
  } catch (e) {
    renderResults([], e.message || "Suche fehlgeschlagen.");
  }
}

function wireSearch() {
  const inp = document.getElementById("dz-search");
  if (!inp) return;
  let t = null;
  inp.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") { clearTimeout(t); runSearch(inp.value); }
  });
  inp.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => { if (inp.value.trim()) runSearch(inp.value); }, 350);
  });
}

// --- Quelle-Panel (US-064): Upload + Angebots-Dropdown -> suggest ---------

function setStatus(msg, kind) {
  const elS = document.getElementById("dz-source-status");
  if (!elS) return;
  elS.textContent = msg || "";
  elS.className = "dz-status" + (kind ? " dz-status-" + kind : "");
}

async function runSuggest(payload) {
  setStatus("Vorschläge werden geladen …", "load");
  try {
    const data = await fetchSuggestions(payload);
    if (data === null) return;               // 401 -> Redirect lief schon
    state.groups = data.groups || [];
    saveState(state);
    renderGroups(state.groups);
    // Pauschal-Angebot ohne Menü-Gänge (#62): erklären statt schweigen.
    const hasGang = state.groups.some((g) => g.kind === "gang");
    const hasKonzept = state.groups.some((g) => g.kind === "konzept");
    if (!hasGang && hasKonzept) {
      setStatus("Keine Menü-Gänge im Angebot erkannt (Pauschal-Angebot) — "
        + "Vorschläge basieren auf dem Catering-Konzept; ergänze per Suche.", "load");
    } else if (!hasGang) {
      setStatus("Keine Menü-Gänge im Angebot erkannt — nutze die Freitext-Suche.", "load");
    } else {
      setStatus("", "");
    }
  } catch (e) {
    renderGroups([]);
    // 503 = Korpus in diesem Deploy nicht verfügbar (Infra-Hinweis).
    const hint = e.status === 503
      ? "Korpus derzeit nicht verfügbar — bitte später erneut versuchen."
      : (e.message || "Vorschläge konnten nicht geladen werden.");
    setStatus(hint, "error");
  }
}

async function loadOfferOptions() {
  const sel = document.getElementById("dz-offer");
  if (!sel) return;
  const offers = await fetchOffers();
  offers.forEach((o) => {
    const opt = document.createElement("option");
    opt.value = o.offer_id;
    opt.textContent = `${o.kunde || "?"} — ${o.anlass || o.angebotsnummer || o.offer_id}`;
    sel.appendChild(opt);
  });
}

function wireSource() {
  const sel = document.getElementById("dz-offer");
  if (sel) {
    sel.addEventListener("change", () => {
      const id = sel.value;
      if (id) runSuggest({ offer_id: Number(id) });
    });
  }

  // Upload: Drop-Zone klickbar + Datei-Input (PDF -> FormData -> suggest).
  const drop = document.getElementById("dz-upload");
  const file = document.getElementById("dz-file");
  if (drop && file) {
    drop.addEventListener("click", () => file.click());
    file.addEventListener("change", () => {
      const f = file.files && file.files[0];
      if (!f) return;
      const fd = new FormData();
      fd.append("file", f);
      runSuggest(fd);
    });
    drop.addEventListener("dragover", (ev) => {
      ev.preventDefault(); drop.classList.add("dz-drop-over");
    });
    drop.addEventListener("dragleave", () => drop.classList.remove("dz-drop-over"));
    drop.addEventListener("drop", (ev) => {
      ev.preventDefault(); drop.classList.remove("dz-drop-over");
      const f = ev.dataTransfer && ev.dataTransfer.files[0];
      if (!f) return;
      const fd = new FormData();
      fd.append("file", f);
      runSuggest(fd);
    });
  }
}

// --- Download-Button (US-067) ---------------------------------------------
// Storyboard -> PPTX. disabled bei leerem Board (renderBoard setzt das);
// Klick lädt das Bundle als Data-URL (bestehendes Anker-Muster).

function triggerDataUrlDownload(dataUrl, filename) {
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function wireDownload() {
  const btn = document.getElementById("dz-download");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    if (!state.board.length) return;         // disabled-Logik (Doppel-Absicherung)
    const slides = state.board.map((b) => ({ deck: b.deck, page: b.page }));
    const prev = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Erzeuge PPTX …";
    try {
      const pptx = await downloadDeck(slides);
      if (pptx) triggerDataUrlDownload(pptx, "kochfabrik-designer.pptx");
    } catch (e) {
      setStatus(e.message || "Download fehlgeschlagen.", "error");
    } finally {
      btn.textContent = prev;
      btn.disabled = state.board.length === 0;
    }
  });
}

// --- Init-Hook ------------------------------------------------------------

function init() {
  document.addEventListener("designer:add", onDesignerAdd);
  wireSource();
  wireSearch();
  wireDownload();
  loadOfferOptions();
  renderGroups(state.groups);   // Restore: zuletzt geladene Vorschläge
  renderBoard();                // Restore: Board aus sessionStorage
  saveState(state);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

export { STATE_KEY, loadState, saveState, emptyState, api, apiJson,
  fetchOffers, fetchSuggestions, search,
  addToBoard, removeFromBoard, moveBoardItem, isOnBoard, renderBoard,
  boardKey, card, renderGroups, runSuggest, renderResults, runSearch,
  downloadDeck };
