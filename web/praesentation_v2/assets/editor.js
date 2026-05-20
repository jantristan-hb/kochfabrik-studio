// EPIC-002 Sprint 6 — Drei-Spalten-Editor State + Live-Edit-Glue.
//
// State-Modell:
//   S.offer_id            — gewähltes Angebot (null wenn keins)
//   S.slides[]            — pro Position: {kategorie, slide_id, overrides}
//   S.active              — Index des aktuell editierten Slides
//   S.suggestions{kat:[]} — Cache pro Kategorie
//
// API-Calls:
//   GET /api/angebote                       → Dropdown
//   GET /api/praesentation_v2/suggestions   → 3-4 Karten je Kategorie
//   GET /api/praesentation_v2/offer/{}/slides
//   PUT /api/praesentation_v2/offer/{}/slide
//   POST /api/praesentation_v2/render-preview (für Stub-Preview)
//
// Live-Edit: jedes Input-Event aktualisiert S.slides[active].overrides
// SOFORT (clientseitig — User sieht das = "Live"). Persistenz an die
// API ist debounced (~600ms) — verhindert Request-Sturm.

const KAT = ["food","deckblatt","location","ausstattung",
             "goldschaetzchen","kochfabrik","freitext"];

const S = {
  offer_id: null,
  slides: [],                 // {kategorie, slide_id, overrides}
  active: 0,
  suggestions: {},            // {kategorie: [items]}
  saveTimer: null,
};

const $ = id => document.getElementById(id);

// ---------------- API-Wrapper (alle graceful) ----------------

async function api(path, opts) {
  const r = await fetch(path, {credentials: "same-origin", ...opts});
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function loadOffers() {
  try {
    const d = await api("/api/angebote?status=&q=");
    const sel = $("offer-select");
    sel.innerHTML = '<option value="">— wählen —</option>';
    (d.items || d || []).forEach(o => {
      const opt = document.createElement("option");
      opt.value = o.id;
      opt.textContent = `${o.angebotsnummer || "#" + o.id} — ${o.kunde_name || o.kunde || "?"}`;
      sel.appendChild(opt);
    });
  } catch (e) {
    setStatus("Angebote-Liste fehlgeschlagen: " + e.message);
  }
}

async function loadSlidesForOffer(offerId) {
  // Sprint 7: parallel Kohärenz-Defaults holen (Kunde/Anlass/Konzept
  // werden in die Slide-Overrides gemergt → Slide matched das Angebot).
  let defaults = {};
  let short = {};
  try {
    const ctx = await api(`/api/praesentation_v2/offer/${offerId}/context`);
    defaults = ctx.defaults_per_kategorie || {};
    short = ctx.short || {};
    setStatus(`Angebot: ${short.kunde || ""} — ${short.anlass || ""}`);
  } catch (e) { /* graceful */ }

  try {
    const d = await api(`/api/praesentation_v2/offer/${offerId}/slides`);
    S.slides = (d.items || []).map(it => ({
      kategorie: it.kategorie,
      slide_id: it.slide_id,
      overrides: {...(defaults[it.kategorie] || {}), ...(it.overrides || {})},
    }));
    if (S.slides.length === 0) {
      // Sinnvolle Defaults: 1 Deckblatt, 1 Food, 1 Freitext —
      // jeweils mit Offer-Defaults vorgefüllt
      S.slides = [
        {kategorie: "deckblatt", slide_id: null,
         overrides: defaults.deckblatt || {}},
        {kategorie: "food", slide_id: null,
         overrides: defaults.food || {}},
        {kategorie: "freitext", slide_id: null,
         overrides: defaults.freitext || {}},
      ];
    }
    S.offer_defaults = defaults;
    S.active = 0;
    renderSlideList();
    renderForm();
    loadSuggestions(S.slides[0].kategorie);
  } catch (e) {
    setStatus("Slides laden: " + e.message);
  }
}

async function loadSuggestions(kat) {
  if (S.suggestions[kat]) {
    renderSuggestions(kat);
    return;
  }
  try {
    const d = await api(`/api/praesentation_v2/suggestions?kategorie=${kat}&limit=4`);
    S.suggestions[kat] = d.items || [];
    renderSuggestions(kat);
  } catch (e) {
    setStatus("Vorschläge laden: " + e.message);
    renderSuggestions(kat); // zeigt empty-state
  }
}

async function persistActiveSlide() {
  if (S.offer_id == null || S.active < 0) return;
  const sl = S.slides[S.active];
  try {
    await api(`/api/praesentation_v2/offer/${S.offer_id}/slide`, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        position: S.active,
        kategorie: sl.kategorie,
        slide_id: sl.slide_id,
        overrides: sl.overrides,
      }),
    });
    setStatus("Gespeichert ✓");
  } catch (e) {
    setStatus("Persistieren fehlgeschlagen: " + e.message);
  }
}

// Debouncer für Live-Edit → API
function schedulePersist() {
  if (S.saveTimer) clearTimeout(S.saveTimer);
  S.saveTimer = setTimeout(persistActiveSlide, 600);
}

// ---------------- Render ----------------

function renderSlideList() {
  const el = $("slide-list");
  el.innerHTML = "";
  S.slides.forEach((sl, i) => {
    const t = document.createElement("div");
    t.className = "slide-tab" + (i === S.active ? " active" : "");
    t.innerHTML = `<span class="pos">${i + 1}</span> ${sl.kategorie}`;
    t.onclick = () => switchSlide(i);
    el.appendChild(t);
  });
  const add = document.createElement("div");
  add.className = "slide-tab";
  add.id = "slide-add";
  add.textContent = "+ Slide";
  add.onclick = addSlide;
  el.appendChild(add);
  $("ft-count").textContent = S.slides.length;
}

function renderForm() {
  if (S.active < 0 || !S.slides[S.active]) return;
  const sl = S.slides[S.active];

  // Kategorie-Picker (Radios)
  const kp = $("kat-pick");
  kp.innerHTML = "";
  KAT.forEach(k => {
    const lab = document.createElement("label");
    lab.innerHTML = `<input type="radio" name="kat" value="${k}" ${sl.kategorie === k ? "checked" : ""}><span>${k}</span>`;
    lab.querySelector("input").onchange = () => {
      sl.kategorie = k;
      sl.slide_id = null;   // Auswahl resetten beim Kategorie-Wechsel
      renderForm();
      renderSlideList();
      loadSuggestions(k);
      schedulePersist();
    };
    kp.appendChild(lab);
  });

  // Form-Felder
  $("f-titel").value = sl.overrides.titel || "";
  $("f-untertitel").value = sl.overrides.untertitel || "";
  $("f-bullets").value = (sl.overrides.bullets || []).join("\n");

  loadSuggestions(sl.kategorie);
}

function renderSuggestions(kat) {
  const el = $("sugg");
  const items = S.suggestions[kat] || [];
  if (S.active < 0 || S.slides[S.active]?.kategorie !== kat) return;
  if (!items.length) {
    el.innerHTML = '<div class="sugg-empty">Noch keine Vorschläge ' +
                   'für „' + kat + '" — wird beim ersten Abruf erzeugt.</div>';
    return;
  }
  const sl = S.slides[S.active];
  el.innerHTML = "";
  items.forEach(it => {
    const c = document.createElement("div");
    c.className = "card" + (sl.slide_id === it.id ? " selected" : "");
    c.innerHTML = `
      <div class="k">${it.kategorie}</div>
      <div class="t">${esc(it.titel)}</div>
      <div class="preview">📄 Realtime-Preview (Sprint 7)</div>`;
    c.onclick = () => {
      sl.slide_id = it.id;
      renderSuggestions(kat);
      schedulePersist();
    };
    el.appendChild(c);
  });
}

function switchSlide(i) {
  if (i < 0 || i >= S.slides.length) return;
  S.active = i;
  renderSlideList();
  renderForm();
}

function addSlide() {
  S.slides.push({kategorie: "freitext", slide_id: null, overrides: {}});
  S.active = S.slides.length - 1;
  renderSlideList();
  renderForm();
  schedulePersist();
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;"}[c]));
}

function setStatus(s) { $("ft-status").textContent = s; }

// ---------------- Live-Edit-Wiring ----------------

function wireLiveEdit() {
  ["f-titel", "f-untertitel"].forEach(id => {
    $(id).addEventListener("input", e => {
      const sl = S.slides[S.active];
      sl.overrides[e.target.dataset.k] = e.target.value;
      schedulePersist();
    });
  });
  $("f-bullets").addEventListener("input", e => {
    const sl = S.slides[S.active];
    sl.overrides.bullets = e.target.value.split("\n")
      .map(l => l.replace(/^[•\-\*]\s*/, "").trim()).filter(Boolean);
    schedulePersist();
  });
}

function wireChat() {
  $("chat-send").onclick = sendChat;
  $("chat-text").addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); sendChat(); }
  });
}

async function sendChat() {
  const t = $("chat-text").value.trim();
  if (!t) return;
  appendMsg("me", t);
  $("chat-text").value = "";
  appendMsg("bot", "…");
  const ph = $("chat-msgs").lastChild;
  try {
    const sl = S.slides[S.active] || {};
    const d = await api("/api/praesentation_v2/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        message: t,
        overrides: sl.overrides || {},
        kategorie: sl.kategorie,
        offer_id: S.offer_id,
      }),
    });
    ph.textContent = d.reply || "Aktualisiert.";
    if (d.patched && typeof d.patched === "object") {
      // LLM-patched Overrides übernehmen + Form refreshen
      sl.overrides = {...sl.overrides, ...d.patched};
      renderForm();
      schedulePersist();
    }
  } catch (e) {
    ph.textContent = "Fehler: " + e.message;
  }
}

function appendMsg(role, text) {
  const m = document.createElement("div");
  m.className = "msg " + role;
  m.textContent = text;
  $("chat-msgs").appendChild(m);
  $("chat-msgs").scrollTop = $("chat-msgs").scrollHeight;
}

// ---------------- Bootstrap ----------------

window.addEventListener("DOMContentLoaded", async () => {
  await loadOffers();
  $("offer-select").addEventListener("change", e => {
    const id = parseInt(e.target.value, 10);
    if (!id) { S.offer_id = null; S.slides = []; renderSlideList();
               renderForm(); return; }
    S.offer_id = id;
    loadSlidesForOffer(id);
  });
  $("btn-save").onclick = persistActiveSlide;
  $("btn-generate").onclick = async () => {
    if (!S.offer_id) { setStatus("Erst Angebot wählen."); return; }
    try {
      const d = await api(`/api/praesentation_v2/generate/${S.offer_id}`, {
        method: "POST"});
      setStatus(`Generierung gestartet (${d.synthetic ? "Stub" : "live"}). ` +
                "Sprint 7+ liefert echte PPTX.");
    } catch (e) {
      setStatus("Generieren: " + e.message);
    }
  };
  wireLiveEdit();
  wireChat();
  // Initial Form (auch ohne Offer): Kategorie-Picker + Default-Slide
  S.slides = [{kategorie: "deckblatt", slide_id: null, overrides: {}}];
  renderSlideList();
  renderForm();
});
