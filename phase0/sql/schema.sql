-- pptxgenerator_v2 — Korpus, getrennt nach Slide-Rolle.
-- menu_composition = dedizierte Speisen-/Menü-Slides (Composer-Quelle für
--   Gericht/Grill-Matching; das kuratierte Foto-SET = Harmonie geschenkt).
-- info_slide       = Cover/Über-uns/Team/Kontakt/Agenda/Ausstattung etc.
-- src_pdf: Provenienz, damit der Composer das Deck re-extrahieren kann.

DROP TABLE IF EXISTS image CASCADE;
DROP TABLE IF EXISTS composition CASCADE;
DROP TABLE IF EXISTS menu_composition CASCADE;
DROP TABLE IF EXISTS info_slide CASCADE;

CREATE TABLE menu_composition (
  id        SERIAL PRIMARY KEY,
  deck      TEXT NOT NULL,
  src_pdf   TEXT NOT NULL,
  page      INT  NOT NULL,
  n_photos  INT  NOT NULL,
  dishes    TEXT[] NOT NULL DEFAULT '{}',
  created   TIMESTAMPTZ DEFAULT now(),
  UNIQUE (deck, page)
);

CREATE TABLE info_slide (
  id        SERIAL PRIMARY KEY,
  deck      TEXT NOT NULL,
  src_pdf   TEXT NOT NULL,
  page      INT  NOT NULL,
  n_photos  INT  NOT NULL,
  role_hint TEXT,                 -- cover / ueber-uns / kontakt / agenda / ?
  texts     TEXT[] NOT NULL DEFAULT '{}',
  created   TIMESTAMPTZ DEFAULT now(),
  UNIQUE (deck, page)
);

CREATE TABLE image (
  id         SERIAL PRIMARY KEY,
  slide_kind TEXT NOT NULL,       -- 'menu' | 'info'
  slide_id   INT  NOT NULL,
  file       TEXT NOT NULL,
  x REAL, y REAL, w REAL, h REAL
  -- später: embedding vector(N)  -- pgvector, nur bei Bedarf
);

CREATE INDEX image_slide_idx  ON image(slide_kind, slide_id);
CREATE INDEX menu_nphotos_idx ON menu_composition(n_photos);
