-- pptxgenerator_v2 — Produktiv-Korpus (Phase D).
-- menu_composition = die 1010 hand-kuratierten Speisen-Slides
--   (Ground-Truth = überlebende deck::page-Notizen in all_menus.pptx).
--   embedding = headline+body, gemini-embedding-001, SEMANTIC_SIMILARITY,
--   dim 768 — identisch zu compose_offer.embed → ANN-Match produktiv.
-- info_slide = Nicht-Speisen (Cover/Team/Ausstattung) — kuratiert raus,
--   Tabelle bleibt für späteren Bedarf.
-- image = per-Foto-Geometrie (feinere Granularität) — DEFERRED, leer.
-- src_pdf: Provenienz, damit der Composer (_deckpipe) re-extrahieren kann.

CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS image CASCADE;
DROP TABLE IF EXISTS composition CASCADE;
DROP TABLE IF EXISTS menu_composition CASCADE;
DROP TABLE IF EXISTS info_slide CASCADE;

CREATE TABLE menu_composition (
  id           SERIAL PRIMARY KEY,
  deck         TEXT NOT NULL,          -- slug (= Notiz-Key vor '::')
  src_pdf      TEXT NOT NULL,          -- abs. Pfad → _deckpipe-Re-Extraktion
  page         INT  NOT NULL,
  headline     TEXT NOT NULL DEFAULT '',
  body         TEXT NOT NULL DEFAULT '',
  module_type  INT,                    -- Cluster-ID (tags.json)
  module_label TEXT,                   -- repräsentative Headline des Clusters
  embedding    vector(768),            -- headline+body (Match-Vektor)
  created      TIMESTAMPTZ DEFAULT now(),
  UNIQUE (deck, page)
);

CREATE TABLE info_slide (
  id        SERIAL PRIMARY KEY,
  deck      TEXT NOT NULL,
  src_pdf   TEXT NOT NULL,
  page      INT  NOT NULL,
  role_hint TEXT,
  texts     TEXT[] NOT NULL DEFAULT '{}',
  created   TIMESTAMPTZ DEFAULT now(),
  UNIQUE (deck, page)
);

CREATE TABLE image (
  id         SERIAL PRIMARY KEY,
  slide_kind TEXT NOT NULL,            -- 'menu' | 'info'
  slide_id   INT  NOT NULL,
  file       TEXT NOT NULL,
  x REAL, y REAL, w REAL, h REAL
);

CREATE INDEX image_slide_idx   ON image(slide_kind, slide_id);
CREATE INDEX menu_module_idx   ON menu_composition(module_type);
-- ANN: Cosine; bei 1010 Zeilen exakt schnell, hnsw für Produktiv-Wachstum
CREATE INDEX menu_embed_idx ON menu_composition
  USING hnsw (embedding vector_cosine_ops);

-- ── ADDITIV (nicht von den DROPs oben betroffen) ──────────────────
-- static_slide = die am häufigsten generierten/kopierten Static-
-- Visual-Slides (Rahmen-Skelett). Assembler fügt is_golden verbatim
-- ein. tier A = byte-identisch; tier B = Layout fix, Fotos
-- event-spezifisch (golden = gekürtes Foto-Set, Rest is_golden=false).
-- Loader: phase0/scripts/db_load_static.py (idempotent).
CREATE TABLE IF NOT EXISTS static_slide (
  id SERIAL PRIMARY KEY, category TEXT NOT NULL, rank INT,
  cnt INT NOT NULL, tier CHAR(1) NOT NULL, skel_pos REAL,
  inclusion TEXT, deck TEXT NOT NULL, src_pdf TEXT NOT NULL,
  page INT NOT NULL, full_text TEXT, is_golden BOOLEAN DEFAULT TRUE,
  created TIMESTAMPTZ DEFAULT now(), UNIQUE (deck, page));
CREATE INDEX IF NOT EXISTS static_cat_idx    ON static_slide(category);
CREATE INDEX IF NOT EXISTS static_golden_idx ON static_slide(is_golden);
CREATE INDEX IF NOT EXISTS static_pos_idx    ON static_slide(skel_pos);
