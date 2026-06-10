// Manual-Override-Schicht: hand-korrigierte Element-Positionen persistieren,
// ohne die generische Extraktion anzufassen. Pro DECK gekeyt.
// Struktur: { "<deck>": { "<page>": [ {match, set} ] } }
// Backward-compat: flaches { "<page>": [...] } (kein Deck) wird weiter erkannt.
const fs = require("fs");

let OV = {};
try { OV = JSON.parse(fs.readFileSync("overrides.json", "utf8")); }
catch (_) { /* keine Overrides */ }

let DECK = null;
function setDeck(key) { DECK = key || null; }

function entriesFor(pno) {
  const p = String(pno);
  if (DECK && OV[DECK]) return OV[DECK][p] || [];
  // Legacy: flaches Format ohne Deck-Key
  if (Array.isArray(OV[p])) return OV[p];
  return [];
}

// gibt {x,y,w,h} zurück: korrigiert falls Override greift, sonst Original
function apply(pno, e) {
  for (const o of entriesFor(pno)) {
    const m = o.match;
    if (m.t !== e.t || (m.fill && m.fill !== e.fill)) continue;
    const dx = Math.abs((m.nearX ?? e.x) - e.x);
    const dy = Math.abs((m.nearY ?? e.y) - e.y);
    if (dx < 0.25 && dy < 0.25) {
      return { x: o.set.x, y: o.set.y, w: o.set.w, h: o.set.h };
    }
  }
  return { x: e.x, y: e.y, w: e.w, h: e.h };
}

module.exports = { apply, setDeck };
