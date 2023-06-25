-- init migration
-- depends:

CREATE TYPE userrole AS ENUM (
    'superowner',
    'owner',
    'manager',
    'operator'
);

CREATE TABLE offices (
    id SERIAL NOT NULL, 
    name VARCHAR(50) NOT NULL, 
    location geography(POINT, 4326) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE users (
    id SERIAL NOT NULL, 
    chat_id INTEGER NOT NULL, 
    name VARCHAR(50) NOT NULL, 
    role userrole NOT NULL, 
    owner_id INTEGER, 
    PRIMARY KEY (id), 
    UNIQUE (chat_id), 
    FOREIGN KEY(owner_id) REFERENCES users (id)
);

CREATE TABLE notifications (
    id SERIAL NOT NULL, 
    code VARCHAR NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    office_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(office_id) REFERENCES offices (id)
);

CREATE TABLE working_hours (
    id SERIAL NOT NULL, 
    office_id INTEGER NOT NULL, 
    day_of_week INTEGER NOT NULL, 
    opening_time TIME WITHOUT TIME ZONE NOT NULL, 
    closing_time TIME WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(office_id) REFERENCES offices (id),
    CHECK (opening_time < closing_time)
);
