-- Enable pgvector extension for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding columns to existing tables
ALTER TABLE conversation_summaries 
ADD COLUMN IF NOT EXISTS embedding vector(1536);

ALTER TABLE memory_events 
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create indexes for fast vector similarity search
CREATE INDEX IF NOT EXISTS conversation_summaries_embedding_idx 
ON conversation_summaries USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS memory_events_embedding_idx 
ON memory_events USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function to search similar conversations
CREATE OR REPLACE FUNCTION search_similar_conversations(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    summary text,
    topics text[],
    sentiment text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        conversation_summaries.id,
        conversation_summaries.summary,
        conversation_summaries.topics,
        conversation_summaries.sentiment,
        1 - (conversation_summaries.embedding <=> query_embedding) as similarity
    FROM conversation_summaries
    WHERE 1 - (conversation_summaries.embedding <=> query_embedding) > match_threshold
    ORDER BY conversation_summaries.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to search similar events
CREATE OR REPLACE FUNCTION search_similar_events(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    event_type text,
    event_description text,
    participants text[],
    event_time timestamp,
    importance_score float,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        memory_events.id,
        memory_events.event_type,
        memory_events.event_description,
        memory_events.participants,
        memory_events.event_time,
        memory_events.importance_score,
        1 - (memory_events.embedding <=> query_embedding) as similarity
    FROM memory_events
    WHERE 1 - (memory_events.embedding <=> query_embedding) > match_threshold
    ORDER BY memory_events.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
