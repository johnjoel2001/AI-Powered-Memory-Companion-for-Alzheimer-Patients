-- Knowledge Graph Schema for Alzheimer's Memory Assistant
-- Extends existing audio_chunks and images tables

-- Conversation Summaries Table
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audio_chunk_id UUID REFERENCES audio_chunks(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative', 'mixed')),
    topics TEXT[] DEFAULT '{}',
    key_points TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Person Interactions Table (tracks who was present and what was discussed)
CREATE TABLE IF NOT EXISTS person_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audio_chunk_id UUID REFERENCES audio_chunks(id) ON DELETE CASCADE,
    person_name TEXT NOT NULL,
    interaction_type TEXT CHECK (interaction_type IN ('conversation', 'visit', 'activity')),
    context TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Memory Events Table (important events extracted from conversations)
CREATE TABLE IF NOT EXISTS memory_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audio_chunk_id UUID REFERENCES audio_chunks(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- e.g., 'meal', 'medication', 'visitor', 'activity'
    event_description TEXT NOT NULL,
    participants TEXT[] DEFAULT '{}',
    event_time TIMESTAMP NOT NULL,
    importance_score FLOAT DEFAULT 0.5, -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_audio ON conversation_summaries(audio_chunk_id);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_created ON conversation_summaries(created_at);
CREATE INDEX IF NOT EXISTS idx_person_interactions_name ON person_interactions(person_name);
CREATE INDEX IF NOT EXISTS idx_person_interactions_audio ON person_interactions(audio_chunk_id);
CREATE INDEX IF NOT EXISTS idx_memory_events_time ON memory_events(event_time);
CREATE INDEX IF NOT EXISTS idx_memory_events_type ON memory_events(event_type);
CREATE INDEX IF NOT EXISTS idx_memory_events_importance ON memory_events(importance_score);
