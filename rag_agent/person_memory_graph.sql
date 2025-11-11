-- Person-Centric Memory Graph
-- Organizes memories by person name

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Person Memories Table (main graph structure)
CREATE TABLE IF NOT EXISTS person_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_name TEXT NOT NULL,
    conversation_text TEXT NOT NULL,  -- Full transcription of what was said
    summary TEXT NOT NULL,  -- Brief summary of the conversation
    topics TEXT[] DEFAULT '{}',
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative', 'mixed')),
    audio_chunk_id UUID REFERENCES audio_chunks(id) ON DELETE CASCADE,
    conversation_date TIMESTAMP NOT NULL,
    embedding vector(1536),  -- For semantic search
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_person_memories_name ON person_memories(person_name);
CREATE INDEX IF NOT EXISTS idx_person_memories_date ON person_memories(conversation_date);
CREATE INDEX IF NOT EXISTS idx_person_memories_audio ON person_memories(audio_chunk_id);

-- Vector similarity index
CREATE INDEX IF NOT EXISTS person_memories_embedding_idx 
ON person_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function to get all conversations with a specific person
CREATE OR REPLACE FUNCTION get_person_conversations(
    p_person_name TEXT,
    days_back INT DEFAULT 7
)
RETURNS TABLE (
    id uuid,
    conversation_text text,
    summary text,
    topics text[],
    sentiment text,
    conversation_date timestamp
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        person_memories.id,
        person_memories.conversation_text,
        person_memories.summary,
        person_memories.topics,
        person_memories.sentiment,
        person_memories.conversation_date
    FROM person_memories
    WHERE person_memories.person_name = p_person_name
    AND person_memories.conversation_date >= NOW() - (days_back || ' days')::INTERVAL
    ORDER BY person_memories.conversation_date DESC;
END;
$$;

-- Function to search conversations with a person semantically
CREATE OR REPLACE FUNCTION search_person_conversations(
    p_person_name TEXT,
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    conversation_text text,
    summary text,
    topics text[],
    conversation_date timestamp,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        person_memories.id,
        person_memories.conversation_text,
        person_memories.summary,
        person_memories.topics,
        person_memories.conversation_date,
        1 - (person_memories.embedding <=> query_embedding) as similarity
    FROM person_memories
    WHERE person_memories.person_name = p_person_name
    AND 1 - (person_memories.embedding <=> query_embedding) > match_threshold
    ORDER BY person_memories.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
