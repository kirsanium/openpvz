-- created_at default now()
-- depends: openpvz_20230710_01_hqmlb

ALTER TABLE notifications ALTER COLUMN created_at SET default now();
