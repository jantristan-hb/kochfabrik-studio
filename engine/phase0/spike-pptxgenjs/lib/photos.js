// Foto-Schicht: platzierte Bilder aus pdftohtml-xml + extrahierten Dateien.
// BESTÄTIGT funktionierend ("Bilder perfekt extrahiert und komponiert",
// Jan 2026-05-18). Snippet verbatim — NICHT umschreiben.
const fs = require("fs");
const { resolve } = require("./logos");
const U = 72; // pt -> inch

// parse-only: liefert Foto-Boxen in Zoll (für Design-Overlap-Test + Platzierung)
// logos.resolve() ersetzt das Original durch die transparente Fassung, falls da.
function parsePhotos(chunk) {
  return [...chunk.matchAll(
    /<image top="(-?\d+)" left="(-?\d+)" width="(\d+)" height="(\d+)" src="([^"]+)"/g)]
    .map(m => ({ t: +m[1], l: +m[2], w: +m[3], h: +m[4], src: m[5] }))
    .filter(im => fs.existsSync(im.src))
    .filter(im => Math.min(im.w, im.h) >= 120)
    .map(im => ({
      src: resolve(im.src),
      x: im.l / U, y: im.t / U, w: im.w / U, h: im.h / U,
    }));
}

function addPhotos(slide, boxes) {
  // groß zuerst (z-Order)
  [...boxes].sort((a, b) => b.w * b.h - a.w * a.h).forEach(b =>
    slide.addImage({ path: b.src, x: b.x, y: b.y, w: b.w, h: b.h }));
  return boxes.length;
}

module.exports = { parsePhotos, addPhotos };
