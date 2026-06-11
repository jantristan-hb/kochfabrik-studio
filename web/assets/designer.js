/* KOCHfabrik Studio — Designer (US-063 Grundgerüst).
 *
 * Modul-Skelett: versionierter State (sessionStorage), API-Wrapper mit
 * 401 -> /login.html-Redirect (Muster aus chat.html), Init-Hook. Die
 * Klick-Verdrahtung (Quelle/Karten/Storyboard/Download) folgt in
 * US-064 ff. — hier nur Gerüst + State, kein Verhalten.
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
  board: [],         // geordnete Liste gewählter Items
});

function loadState() {
  try {
    const raw = sessionStorage.getItem(STATE_KEY);
    if (!raw) return emptyState();
    const s = JSON.parse(raw);
    return (s && s.version === 1) ? s : emptyState();
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

// --- Init-Hook ------------------------------------------------------------

function init() {
  // US-064 ff. verdrahten Quelle/Suche/Karten/Storyboard/Download hier.
  // US-063 stellt nur das Gerüst + State bereit.
  saveState(state);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

export { STATE_KEY, loadState, saveState, emptyState, api, apiJson,
  fetchOffers, fetchSuggestions, search };
