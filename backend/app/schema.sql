CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id           BIGSERIAL PRIMARY KEY,
    url          TEXT NOT NULL UNIQUE,
    agency       TEXT NOT NULL,
    title        TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id          BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    heading     TEXT NOT NULL DEFAULT '',
    content     TEXT NOT NULL,
    embedding   VECTOR(384) NOT NULL,
    search      TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', heading), 'A') ||
        setweight(to_tsvector('english', content), 'B')
    ) STORED,
    UNIQUE (document_id, position)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_search_idx ON chunks USING gin (search);
