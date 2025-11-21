CREATE TABLE records (
    id BIGSERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    country VARCHAR(80) NOT NULL,
    city VARCHAR(80) NOT NULL,
    housing_type VARCHAR(20) NOT NULL CHECK (
        housing_type IN ('apartamento', 'casa', 'comercial')
    ),
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

-- =====================================================
-- 3) REVIEWS (reseñas del inmueble)
-- =====================================================
CREATE TABLE reviews (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    title VARCHAR(120),
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    rating INT NOT NULL CHECK (
        rating BETWEEN 1
        AND 5
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviews_record ON reviews(record_id);

CREATE TABLE review_images (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_images_review ON review_images(review_id);

-- =====================================================
-- 5) REVIEW COMMENTS (comentarios dentro de reseñas)
-- HU6
-- =====================================================
CREATE TABLE comments (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_review_id ON comments(review_id);

CREATE INDEX idx_comments_review_created ON comments(review_id, created_at DESC);

-- =====================================================
-- 6) SAVED RECORDS (lista de guardados)
-- HU5
-- =====================================================
CREATE TABLE saved_records (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_saved_records_record UNIQUE (record_id)
);

CREATE INDEX idx_saved_records_record_saved_at ON saved_records(record_id, saved_at DESC);