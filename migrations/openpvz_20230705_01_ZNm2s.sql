-- tie office to timezone
-- depends: openpvz_20230703_02_CNvc1

ALTER TABLE offices ADD COLUMN timezone VARCHAR(40) NOT NULL DEFAULT 'Europe/Moscow';
