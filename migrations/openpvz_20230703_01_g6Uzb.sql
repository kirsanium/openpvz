-- Adds `owner_id` column to `offices` table
-- depends: openpvz_20230625_01_nSrca

ALTER TABLE offices ADD COLUMN owner_id integer NOT NULL;
ALTER TABLE offices ADD FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE;
