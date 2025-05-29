CREATE TABLE currencies (
    id SERIAL PRIMARY KEY,
    country VARCHAR(255) NOT NULL,
    currency_name VARCHAR(255) NOT NULL,
    code VARCHAR(3) NOT NULL,
    UNIQUE (code)
);