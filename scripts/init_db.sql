-- Enable pgVector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Trigger function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- FAQ Table
-- IMPORTANT: These values must match constants.py configuration:
--   - embedding dimension must match EMBEDDING_MODEL in .env
--     text-embedding-3-small: 1536, text-embedding-3-large: 3072
--   - collection_name VARCHAR length must match MAX_COLLECTION_NAME_LENGTH (100)
--   - DEFAULT 'default' must match DEFAULT_COLLECTION_NAME constant
-- Changing embedding model requires ALTER TABLE migration (see migrate_embedding_dimension.sql)
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding vector(1536),  -- Default for text-embedding-3-small (see constants.py)
    collection_name VARCHAR(100) DEFAULT 'default',  -- See constants.py: MAX_COLLECTION_NAME_LENGTH, DEFAULT_COLLECTION_NAME
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger to automatically update updated_at on row update
DROP TRIGGER IF EXISTS update_faqs_updated_at ON faqs;
CREATE TRIGGER update_faqs_updated_at
    BEFORE UPDATE ON faqs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Index for similarity search using cosine distance
CREATE INDEX IF NOT EXISTS faqs_embedding_idx ON faqs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Collections Table (Optional for organization)
-- IMPORTANT: VARCHAR(100) must match MAX_COLLECTION_NAME_LENGTH in constants.py
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,  -- See constants.py: MAX_COLLECTION_NAME_LENGTH
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default collection
-- IMPORTANT: These values must match constants.py: DEFAULT_COLLECTION_NAME, DEFAULT_COLLECTION_DESCRIPTION
INSERT INTO collections (name, description)
VALUES ('default', 'Default FAQ collection')
ON CONFLICT (name) DO NOTHING;
