// Links-Bild -> Text-Gutter. pdfminer-LTImage-Bbox ist oft breiter als das
// im Original sichtbar platzierte Foto -> Text rechts daneben klebt. Regel:
// sitzt ein Textblock unmittelbar rechts neben einem Bild (vertikale
// Überlappung, Spalt < MIN), Bild-Rechtkante einkürzen bis Spalt == TARGET.
// Nur schrumpfen; reine Rechts-/Überlagerungs-Fälle bleiben unberührt.

const MIN = 0.35;     // Spalt, ab dem nachgebessert wird (Zoll)
const TARGET = 0.30;  // gewünschter Gutter (Zoll)

function fixImageWidth(img, texts) {
  let right = img.x + img.w;
  for (const t of texts) {
    const vOverlap = Math.min(img.y + img.h, t.y + 0.3) > Math.max(img.y, t.y);
    if (!vOverlap) continue;
    const gap = t.x - right;
    if (gap > 0 && gap < MIN) {
      const newRight = t.x - TARGET;
      if (newRight < right && newRight > img.x + 0.2) {
        return { ...img, w: newRight - img.x };
      }
    }
  }
  return img;
}

module.exports = { fixImageWidth };
