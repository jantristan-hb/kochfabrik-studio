// Zwei klar definierte Normalisierungen auf der Paint-Order-Pipeline
// (kein Heuristik-Pile — beides folgt PDF-Semantik):
//
// 1) FRAME: ein goldener, dünner Streifen über (fast) die volle Slide-
//    Kante IST per Definition die äußerste Begrenzung -> zuletzt zeichnen
//    (oben) + minimal über die Kante ziehen (kein Slide-BG-Spalt).
// 2) BACKING: ein gefülltes Rect, das unmittelbar danach von einem Bild
//    ~deckungsgleich übermalt wird, ist eine Hinterlegung (im Original nie
//    sichtbar, z.B. blaues Foto-Frame-Rect) -> weglassen.

const PX = 1 / 96;
const BLEED = 2 * PX;

function isGold(hex) {
  if (!hex || hex.length !== 6) return false;
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return Math.abs(r - 170) < 45 && Math.abs(g - 131) < 45 && Math.abs(b - 57) < 45;
}

function isFrame(e, SW, SH) {
  if (e.t !== "rect" || !isGold(e.fill)) return false;
  const wide = e.w >= SW * 0.9 && e.h < 0.4;   // oben/unten
  const tall = e.h >= SH * 0.9 && e.w < 0.4;   // links/rechts
  return wide || tall;
}

// Frame-Geometrie nach außen über die Kante ziehen, Innenkante bleibt
function bleed(e, SW, SH) {
  if (e.w >= SW * 0.9) {                        // horizontaler Streifen
    const top = e.y < SH / 2;
    return { x: -BLEED, w: SW + 2 * BLEED,
             y: top ? -BLEED : e.y, h: top ? e.h + BLEED : SH + BLEED - e.y };
  }
  const left = e.x < SW / 2;                    // vertikaler Streifen
  return { y: -BLEED, h: SH + 2 * BLEED,
           x: left ? -BLEED : e.x, w: left ? e.w + BLEED : SW + BLEED - e.x };
}

// rect unmittelbar danach von Bild ~deckungsgleich übermalt?
function backedBy(rect, nextEl) {
  if (!nextEl || nextEl.t !== "image") return false;
  const ix = Math.max(0, Math.min(rect.x + rect.w, nextEl.x + nextEl.w) - Math.max(rect.x, nextEl.x));
  const iy = Math.max(0, Math.min(rect.y + rect.h, nextEl.y + nextEl.h) - Math.max(rect.y, nextEl.y));
  const area = rect.w * rect.h;
  return area > 0 && (ix * iy) / area >= 0.9;
}

module.exports = { isFrame, bleed, backedBy };
