// Orchestrator: emittiert elements.json 1:1 in PDF-Mal-Reihenfolge.
// Ein Loop, korrekte z-Order durch Reihenfolge — keine Heuristik
// (kein covered-skip / isBorder / fg-Flag). Logo-Transparenz via lib/logos.
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { resolve } = require("./lib/logos");
const { apply, setDeck } = require("./lib/overrides");
const { emitText } = require("./lib/text");
const { isFrame, bleed, backedBy } = require("./lib/frame");
// lib/gutter.js bewusst NICHT eingebunden: Original ist links eng -> 1:1

// Usage: reconstruct.js [elements.json] [out.pptx]
const EL_PATH = process.argv[2] || "elements.json";
const OUT_PATH = process.argv[3] || "reconstructed.pptx";
const U = 72;
const raw = JSON.parse(fs.readFileSync(EL_PATH, "utf8"));
const meta = raw._meta || { w_pt: 960, h_pt: 540 };   // Seitenmaß aus PDF
const el = Object.fromEntries(
  Object.entries(raw).filter(([k]) => k !== "_meta"));
const PAGE_W = meta.w_pt, PAGE_H = meta.h_pt;
const SW = PAGE_W / U, SH = PAGE_H / U;
setDeck(meta.deck);   // Deck-gekeyte Overrides aktivieren

const pres = new pptxgen();
pres.defineLayout({ name: "KF", width: SW, height: SH });
pres.layout = "KF";

// Defensiv: 1 kaputtes Element/Slide darf den Lauf nicht killen.
let R = 0, I = 0, T = 0, P = 0, SKIP = 0;
for (const pno of Object.keys(el).sort((a, b) => +a - +b)) {
  const s = pres.addSlide();
  try {
    const seq = el[pno];
    const frames = [];
    const bands = [];   // vollbreite Bänder (kein Voll-BG, kein Frame)
    // Grafik in echter pdfminer-Mal-Reihenfolge; Frame -> später (oben),
    // Backing-Rects (sofort von Bild übermalt) -> weglassen
    for (let i = 0; i < seq.length; i++) {
      const e = seq[i];
      try {
        if (e.t === "rect") {
          if (isFrame(e, SW, SH)) { frames.push(e); continue; }
          if (backedBy(e, seq[i + 1])) continue;
          const g = apply(pno, e);
          s.addShape(pres.ShapeType.rect, {
            x: g.x, y: g.y, w: g.w, h: g.h,
            fill: { color: e.fill }, line: { type: "none" },
          });
          if (g.w >= 0.85 * SW && g.h > 0.3 && g.h < 0.6 * SH) bands.push(g);
          R++;
        } else if (e.t === "image") {
          const src = resolve(e.src);
          const g = apply(pno, e);
          if (fs.existsSync(src)) {
            // faithful: Bild 1:1 an pdfminer-Bbox
            s.addImage({ path: src, x: g.x, y: g.y, w: g.w, h: g.h });
            I++;
          } else {
            // Fallback: fehlendes Asset -> neutraler Platzhalter
            s.addShape(pres.ShapeType.rect, {
              x: g.x, y: g.y, w: g.w, h: g.h,
              fill: { color: "EEEEEE" },
              line: { color: "CCCCCC", width: 0.5 },
            });
            P++;
            console.warn(`[placeholder] fehlendes Bild ${src} (S${pno})`);
          }
        }
      } catch (err) {
        SKIP++;
        console.warn(`[skip] Element S${pno}#${i}: ${err.message}`);
      }
    }
    // Text = oberste Ebene (gilt für Slide-Decks generell)
    for (const e of seq) {
      if (e.t !== "text") continue;
      try {
        const cx = e.x + e.w / 2, cy = e.y + e.h / 2;
        const band = bands.find((b) =>
          cx >= b.x && cx <= b.x + b.w && cy >= b.y && cy <= b.y + b.h);
        emitText(s, e, band);
        T++;
      } catch (err) {
        SKIP++;
        console.warn(`[skip] Text S${pno}: ${err.message}`);
      }
    }
    // Gold-Frame ganz zuletzt = äußerste Begrenzung, Kante übersteht
    for (const e of frames) {
      try {
        const g = bleed(e, SW, SH);
        s.addShape(pres.ShapeType.rect, {
          x: g.x, y: g.y, w: g.w, h: g.h,
          fill: { color: e.fill }, line: { type: "none" },
        });
        R++;
      } catch (err) {
        SKIP++;
        console.warn(`[skip] Frame S${pno}: ${err.message}`);
      }
    }
  } catch (err) {
    SKIP++;
    console.warn(`[slide-skip] S${pno}: ${err.message}`);
  }
}

pres.writeFile({ fileName: OUT_PATH }).then(() =>
  console.log(`OK: ${Object.keys(el).length} Slides @ ${PAGE_W}x${PAGE_H}pt | `
    + `${R} Rects, ${I} Bilder, ${T} Texte, ${P} Platzhalter, ${SKIP} skip → ${OUT_PATH}`));
