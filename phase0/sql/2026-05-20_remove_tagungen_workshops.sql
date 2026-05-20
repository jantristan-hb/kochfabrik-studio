-- 2026-05-20 — entfernt die 3 'TAGUNGEN & WORKSHOPS'-Rows aus
-- menu_composition. Triggerte falsche Slide-Picks im Legacy-Pfad
-- (/api/praesentation/* in kochfabrik-studio), wenn eine Gang-Headline
-- im Angebot semantisch nah an diesen Modul-Labels lag.
--
-- Betroffen (alle aus deck '26-02-2026-kf-x-bss'):
--   module_type=190  module_label='TAGUNGEN & WORKSHOPS'         page=9
--   module_type=270  module_label='TAGUNGEN & WORKSHOPS FOOD'    page=10
--   module_type=263  module_label='TAGUNGEN & WORKSHOPS DRINKS'  page=11
--
-- Die 20 'TAGUNG KAFFEE/FRÜHSTÜCK/LUNCH/KAFFEEPAUSE'-Module bleiben.
--
-- Apply:  psql -h localhost -p 5434 -U postgres -d pptxgen \
--           -f 2026-05-20_remove_tagungen_workshops.sql
--
-- Idempotent: DELETE-Filter trifft auch beim zweiten Lauf 0 Rows.

BEGIN;

DELETE FROM menu_composition
 WHERE module_label LIKE 'TAGUNGEN & WORKSHOPS%';

-- Verify-Counts werden als NOTICE rausgeschrieben (sichtbar im psql-
-- Output), damit die Migration ohne Extra-SELECT verifiziert ist.
DO $$
DECLARE
  total_rows  INT;
  tw_rows     INT;
BEGIN
  SELECT COUNT(*) INTO total_rows FROM menu_composition;
  SELECT COUNT(*) INTO tw_rows
    FROM menu_composition
    WHERE module_label LIKE 'TAGUNGEN & WORKSHOPS%';
  RAISE NOTICE 'menu_composition total rows: %', total_rows;
  RAISE NOTICE 'TAGUNGEN & WORKSHOPS rows remaining: %', tw_rows;
  IF tw_rows <> 0 THEN
    RAISE EXCEPTION 'expected 0 TAGUNGEN & WORKSHOPS rows, got %', tw_rows;
  END IF;
END $$;

COMMIT;
