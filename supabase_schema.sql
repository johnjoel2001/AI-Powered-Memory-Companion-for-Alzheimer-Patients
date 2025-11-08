-- Supabase Database Schema - Simple

-- Audio Chunks Table
CREATE TABLE audio_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL UNIQUE,
    storage_url TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    has_conversation BOOLEAN DEFAULT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Images Table (only taken when conversation detected)
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL UNIQUE,
    storage_url TEXT NOT NULL,
    captured_at TIMESTAMP NOT NULL,
    audio_chunk_id UUID REFERENCES audio_chunks(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audio_chunks_time ON audio_chunks(start_time, end_time);
CREATE INDEX idx_images_captured_at ON images(captured_at);
CREATE INDEX idx_images_audio_chunk ON images(audio_chunk_id);
