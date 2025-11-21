CREATE TABLE records (
    id BIGSERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    country VARCHAR(80) NOT NULL,
    city VARCHAR(80) NOT NULL,
    housing_type VARCHAR(20) NOT NULL CHECK (housing_type IN ('apartamento', 'casa', 'comercial')),
    monthly_rent NUMERIC(12, 2) NOT NULL CHECK (monthly_rent > 0),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_records_country_city ON records(country, city);

CREATE INDEX idx_records_housing_type ON records(housing_type);

CREATE TABLE record_images (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_record_images_record ON record_images(record_id);
