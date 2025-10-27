-- Migration script to change embedding vector dimension
-- Use this when switching between embedding models with different dimensions
--
-- IMPORTANT: This will DROP all existing embeddings and require regeneration
-- Make sure to backup your data before running this migration
--
-- Usage:
--   1. Update EMBEDDING_MODEL in .env to your desired model
--   2. Update the dimension below to match (1536, 3072, etc.)
--   3. Run: docker-compose exec postgres psql -U faq_user -d faq_db -f /app/scripts/migrate_embedding_dimension.sql
--   4. Regenerate embeddings: docker-compose exec app python scripts/create_embeddings.py

-- Step 1: Drop the old vector index
DROP INDEX IF EXISTS faqs_embedding_idx;

-- Step 2: Drop the embedding column
ALTER TABLE faqs DROP COLUMN IF EXISTS embedding;

-- Step 3: Add new embedding column with new dimension
-- CHANGE THIS VALUE to match your new model:
--   text-embedding-3-small: 1536
--   text-embedding-3-large: 3072
--   text-embedding-ada-002: 1536
ALTER TABLE faqs ADD COLUMN embedding vector(1536);  -- ← CHANGE THIS

-- Step 4: Recreate the vector index
-- Adjust 'lists' parameter based on your dataset size
-- Rule of thumb: lists = rows / 1000 (max 1000)
CREATE INDEX faqs_embedding_idx ON faqs
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Verify the change
\d faqs

-- Next steps:
-- Run: docker-compose exec app python scripts/create_embeddings.py
-- This will regenerate all embeddings with the new model
