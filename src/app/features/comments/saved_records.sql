CREATE TABLE saved_records (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_saved_records_record UNIQUE (record_id)
);

CREATE INDEX idx_saved_records_record_saved_at ON saved_records(record_id, saved_at DESC);