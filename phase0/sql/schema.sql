-- pptxgenerator_v2 — Kompositions-Korpus (clean-room, eigene DB)
-- Eine "composition" = das vom Menschen kuratierte Foto-SET einer Slide
-- + deren Gericht-Text. Wiederverwendungs-Einheit (Harmonie geschenkt).
-- pgvector-Image vorhanden; Embedding-Spalte kommt erst wenn semantischer
-- Teil-Tausch nachweislich nötig ist (nicht jetzt).

CREATE TABLE IF NOT EXISTS composition (
  id        SERIAL PRIMARY KEY,
  deck      TEXT NOT NULL,
  page      INT  NOT NULL,
  n_photos  INT  NOT NULL,
  dishes    TEXT[] NOT NULL DEFAULT '{}',
  created   TIMESTAMPTZ DEFAULT now(),
  UNIQUE (deck, page)
);

CREATE TABLE IF NOT EXISTS image (
  id       SERIAL PRIMARY KEY,
  comp_id  INT REFERENCES composition(id) ON DELETE CASCADE,
  file     TEXT NOT NULL,        -- Basename des pdftohtml-Fotos
  x REAL, y REAL, w REAL, h REAL -- Zoll, Position im Set (Layout-Signatur)
  -- später: embedding vector(N)  -- pgvector, nur bei Bedarf
);

CREATE INDEX IF NOT EXISTS image_comp_idx ON image(comp_id);
CREATE INDEX IF NOT EXISTS comp_nphotos_idx ON composition(n_photos);
