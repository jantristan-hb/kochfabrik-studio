// Logo-Lib: mappt ein Original-Bild auf seine transparente Fassung
// (Gemini-Freistellung, logos.json). Kein Match-Gerödel — simpler Lookup.
const fs = require("fs");

let MAP = {};
try { MAP = JSON.parse(fs.readFileSync("logos.json", "utf8")); }
catch (_) { /* noch keine Logos freigestellt */ }

// liefert transparente Fassung, sonst Original
function resolve(src) {
  return MAP[src] || src;
}

module.exports = { resolve };
