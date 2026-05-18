// Manual-Override-Schicht: hand-korrigierte Element-Positionen persistieren,
// ohne die generische Extraktion anzufassen. Match per Seite + Typ + Fill +
// ungefährer Original-Position; liefert die korrigierte Geometrie.
const fs = require("fs");

let OV = {};
try { OV = JSON.parse(fs.readFileSync("overrides.json", "utf8")); }
catch (_) { /* keine Overrides */ }

// gibt {x,y,w,h} zurück: korrigiert falls Override greift, sonst Original
function apply(pno, e) {
  for (const o of OV[String(pno)] || []) {
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

module.exports = { apply };
