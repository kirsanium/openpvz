-- init migration
-- depends:

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TYPE userrole AS ENUM (
    'SUPEROWNER',
    'OWNER',
    'MANAGER',
    'OPERATOR'
);

CREATE TABLE offices (
    id SERIAL NOT NULL, 
    name VARCHAR(50) NOT NULL, 
    location geography(POINT, 4326) NOT NULL, 
    is_open BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (id)
);

CREATE TABLE users (
    id SERIAL NOT NULL, 
    chat_id INTEGER NOT NULL, 
    name VARCHAR(50) NOT NULL UNIQUE, 
    role userrole NOT NULL, 
    owner_id INTEGER, 
    PRIMARY KEY (id), 
    UNIQUE (chat_id), 
    FOREIGN KEY(owner_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE notifications (
    id SERIAL NOT NULL, 
    code VARCHAR NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    office_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(office_id) REFERENCES offices (id) ON DELETE CASCADE
);

CREATE TABLE working_hours (
    id SERIAL NOT NULL, 
    office_id INTEGER NOT NULL, 
    day_of_week INTEGER NOT NULL, 
    opening_time TIME WITHOUT TIME ZONE NOT NULL, 
    closing_time TIME WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(office_id) REFERENCES offices (id) ON DELETE CASCADE,
    CHECK (opening_time < closing_time)
);
