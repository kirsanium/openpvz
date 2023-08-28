-- add column notifications.source_user_id
-- depends: openpvz_20230711_01_txT5O

ALTER TABLE notifications ADD COLUMN source_user_id integer NOT NULL;
ALTER TABLE notifications ADD FOREIGN KEY (source_user_id) REFERENCES users (id) ON DELETE CASCADE;
