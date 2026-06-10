// Design-Schicht: gefüllte Vektor-Rechtecke (pdfminer -> rects.json)
// als echte pptxgenjs-Shapes. BESTÄTIGT funktionierend (brauner Hintergrund
// + Gold-Rand passen, Jan 2026-05-18).
//
// Inkrementelle Tweaks hier kapseln — Snippet NICHT umschreiben.

const PX = 1 / 96; // 1 Bildschirm-Pixel in Zoll (96 dpi)

// Seitliche Gold-Ränder bis ÜBER die Slide-Kante ziehen, damit kein
// Slide-Hintergrund durchblitzt (Jan: "Rand muss die ganze Slide bedienen,
// darf ruhig überstehen"). Innenkante bleibt unverändert.
const SIDE_BLEED = 2 * PX;

function isGold(hex) {
  // pdfminer-Gold ~ rgb(170,131,57) = AA8339 (Toleranz)
  if (!hex || hex.length !== 6) return false;
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return Math.abs(r - 170) < 40 && Math.abs(g - 131) < 40 && Math.abs(b - 57) < 40;
}

// liefert {x,y,w,h,fill} ggf. mit verbreitertem Seitenrand
function adjust(r, slideW) {
  const tall = r.h > 7;          // ~volle Seitenhöhe (7.5")
  const thin = r.w < 0.3;        // schmaler Streifen
  if (isGold(r.fill) && tall && thin) {
    const inner = r.x + r.w;
    if (r.x < 0.5) {                 // linker Rand -> Außenkante über Slide
      return { ...r, x: -SIDE_BLEED, w: inner + SIDE_BLEED };
    }
    if (inner > slideW - 0.5) {      // rechter Rand -> über rechte Kante
      return { ...r, w: slideW + SIDE_BLEED - r.x };
    }
  }
  return r;
}

// Anteil von rect r, der durch die Foto-Boxen überdeckt wird (0..1)
function coveredFrac(r, photos) {
  const A = r.w * r.h;
  if (A <= 0) return 0;
  let cov = 0;
  for (const p of photos) {
    const ix = Math.max(0, Math.min(r.x + r.w, p.x + p.w) - Math.max(r.x, p.x));
    const iy = Math.max(0, Math.min(r.y + r.h, p.y + p.h) - Math.max(r.y, p.y));
    cov += ix * iy;
  }
  return cov / A;
}

// Frame-Rand = goldener, dünner Streifen über (fast) volle Seitenkante
function isBorder(r, slideW, slideH) {
  if (!isGold(r.fill)) return false;
  const side = r.h > slideH * 0.9 && r.w < 0.3;
  const topbot = r.w > slideW * 0.9 && r.h < 0.3;
  return side || topbot;
}

// Design-HINTERGRUND (ohne Frame-Rand): vor den Fotos.
// Rects zu >=80% von Fotos überdeckt = Platzhalter -> weglassen.
function addDesign(pres, slide, rects, slideW, slideH, photos = []) {
  let n = 0;
  for (const raw of rects || []) {
    if (isBorder(raw, slideW, slideH)) continue;       // Frame kommt zuletzt
    const r = adjust(raw, slideW);
    if (coveredFrac(r, photos) >= 0.8) continue;
    slide.addShape(pres.ShapeType.rect, {
      x: r.x, y: r.y, w: r.w, h: r.h,
      fill: { color: r.fill }, line: { type: "none" },
    });
    n++;
  }
  return n;
}

// Gold-FRAME: äußerste Schicht, NACH den Fotos -> deckt Foto-Überstand ab.
// Seitenränder zusätzlich +1px (Jan-Wunsch) via adjust().
function addBorders(pres, slide, rects, slideW, slideH) {
  let n = 0;
  for (const raw of rects || []) {
    if (!isBorder(raw, slideW, slideH)) continue;
    const r = adjust(raw, slideW);
    slide.addShape(pres.ShapeType.rect, {
      x: r.x, y: r.y, w: r.w, h: r.h,
      fill: { color: r.fill }, line: { type: "none" },
    });
    n++;
  }
  return n;
}

module.exports = { addDesign, addBorders };
