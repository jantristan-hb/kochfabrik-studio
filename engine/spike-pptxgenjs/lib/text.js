// Text-Modul (gehärtet): EIN editierbares Textfeld pro Block; Zeilen als
// Rich-Text-Runs (Stil je Zeile erhalten) -> als Block editierbar, nicht
// Zeile-für-Zeile. Gewicht -> installierte Open-Sans-Faces. Entities sind
// in extract.py dekodiert. Größe 1:1 (pdfminer-size == pt, verifiziert).

const WEIGHT = {
  ExtraBold: { face: "Open Sans Extrabold", bold: false },
  Bold: { face: "Open Sans", bold: true },
  Semibold: { face: "Open Sans Semibold", bold: false },
  Light: { face: "Open Sans Light", bold: false },
  Regular: { face: "Open Sans", bold: false },
};

// pdfminer char.size überschätzt die echte pt-Größe (Subset-Font-Bbox).
// Kalibrierbarer Korrekturfaktor (visuell gegen Original abgeglichen).
const SIZE_K = 0.78;
const LINE_K = 0.9;    // Zeilenabstand etwas enger (Original ist kompakt)
// pdfminer-LTTextBox-Top hat Leading über dem Glyph -> Block sitzt zu tief.
// Block-Y um diesen Anteil der (gerenderten) erste-Zeile-Größe anheben.
const Y_OFF_K = 0.18;

// band (optional): {x,y,w,h} -> Titel exakt in diesem Panel zentrieren
function emitText(slide, e, band) {
  const lines = e.lines || [];
  const runs = lines.map((l, i) => {
    const w = WEIGHT[l.weight] || WEIGHT.Regular;
    return {
      text: l.txt,
      options: {
        fontSize: Math.round(l.size * SIZE_K * 10) / 10,
        color: l.color || "FFFFFF",
        // Pro-Text-Schriftart-Override (l.font) schlägt die aus dem Gewicht
        // abgeleitete Open-Sans-Face. Ohne Override unverändert.
        fontFace: l.font || w.face,
        bold: w.bold,
        italic: !!l.italic,
        breakLine: i < lines.length - 1, // Zeilenumbruch zwischen Zeilen
      },
    };
  });
  if (!runs.length) return;

  // Titel in einem Panel -> Box = Panel, zentriert (h + v)
  if (band) {
    slide.addText(runs, {
      x: band.x, y: band.y, w: band.w, h: band.h,
      align: "center", valign: "middle", margin: 0,
      wrap: false, lineSpacingMultiple: LINE_K,
    });
    return;
  }

  // Block-Y-Offset: gerenderte erste-Zeile-Größe (pt) -> Zoll * Faktor
  const rs = Math.round((lines[0].size || 12) * SIZE_K * 10) / 10;
  const yOff = (rs / 72) * Y_OFF_K;
  slide.addText(runs, {
    x: e.x, y: Math.max(0, e.y - yOff),
    w: e.w + 0.3, h: e.h + 0.12,   // Padding gegen Clipping
    align: "left",
    valign: "top",
    margin: 0,
    // Default `wrap:false` (Präsentations-Faithful — Zeilen wie im
    // Original). Opt-in per Element `wrap:true` für Angebot-Felder
    // wie {KONZEPT}, deren Text laufzeit-dynamisch ist und in eine
    // breitere Box hineinwrappt.
    wrap: e.wrap === true,
    lineSpacingMultiple: LINE_K,
  });
}

module.exports = { emitText };
