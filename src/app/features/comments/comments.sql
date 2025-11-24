CREATE TABLE comments (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_review_id ON comments(review_id);

CREATE INDEX idx_comments_review_created ON comments(review_id, created_at DESC);