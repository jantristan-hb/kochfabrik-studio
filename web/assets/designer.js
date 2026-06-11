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

// API-Stubs — Endpunkte (Designer-Router) kommen in der API-Kette;
// die Verdrahtung der UI-Handler folgt in US-064 ff.
async function fetchOffers() { return apiJson("/api/angebote"); }       // stub
async function fetchSuggestions(_payload) { return null; }              // stub
async function search(_q) { return null; }                              // stub

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

// --- Init-Hook ------------------------------------------------------------

function init() {
  // US-064 ff. verdrahten Quelle/Suche/Karten/Download hier.
  document.addEventListener("designer:add", onDesignerAdd);
  renderBoard();        // Restore: Board aus sessionStorage rekonstruieren
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
  boardKey };
