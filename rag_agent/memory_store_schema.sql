-- MemerAI Memory Store
-- This is the core RAG database

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Memory Store Table
CREATE TABLE IF NOT EXISTS memory_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person TEXT NOT NULL,
    event TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    full_conversation TEXT NOT NULL,
    memory_time TIMESTAMP NOT NULL,
    duration_seconds INT NOT NULL,
    searchable_text TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_memory_store_person ON memory_store(person);
CREATE INDEX IF NOT EXISTS idx_memory_store_time ON memory_store(memory_time);

-- Vector similarity index
CREATE INDEX IF NOT EXISTS memory_store_embedding_idx 
ON memory_store USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- RAG Search Function
CREATE OR REPLACE FUNCTION search_memories(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 3
)
RETURNS TABLE (
    id uuid,
    person text,
    event text,
    summary_text text,
    memory_time timestamp,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        memory_store.id,
        memory_store.person,
        memory_store.event,
        memory_store.summary_text,
        memory_store.memory_time,
        1 - (memory_store.embedding <=> query_embedding) as similarity
    FROM memory_store
    WHERE memory_store.embedding IS NOT NULL
    AND 1 - (memory_store.embedding <=> query_embedding) > match_threshold
    ORDER BY memory_store.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
