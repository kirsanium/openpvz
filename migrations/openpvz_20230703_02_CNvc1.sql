-- telegram bot persistence table
-- depends: openpvz_20230703_01_g6Uzb

CREATE TABLE IF NOT EXISTS telegram_bot_persistence(
    data json NOT NULL
);
