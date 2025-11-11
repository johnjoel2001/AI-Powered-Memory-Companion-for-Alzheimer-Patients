-- Combined Conversations Table
-- This stores conversations that combine multiple audio chunks within 1 minute

CREATE TABLE IF NOT EXISTS combined_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_name TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds INT NOT NULL,
    full_transcription TEXT NOT NULL,
    audio_chunk_ids UUID[] NOT NULL,
    chunk_count INT NOT NULL,
    conversation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_combined_conversations_person ON combined_conversations(person_name);
CREATE INDEX IF NOT EXISTS idx_combined_conversations_date ON combined_conversations(conversation_date);
CREATE INDEX IF NOT EXISTS idx_combined_conversations_start ON combined_conversations(start_time);
