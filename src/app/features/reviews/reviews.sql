CREATE TABLE reviews (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    title VARCHAR(120),
    email VARCHAR(320) NOT NULL CHECK (
        length(email) <= 320
        AND email ~* '^[A-Z0-9._%+-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)+$'
    ),
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
