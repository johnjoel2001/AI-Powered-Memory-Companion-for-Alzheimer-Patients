-- Supabase Database Schema for Alzheimer's Camera System

-- 1. Audio Chunks Table
CREATE TABLE audio_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL UNIQUE,
    storage_url TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds INTEGER DEFAULT 300, -- 5 minutes
    has_conversation BOOLEAN DEFAULT NULL, -- NULL = not processed yet
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

-- 2. Images Table
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL UNIQUE,
    storage_url TEXT NOT NULL,
    captured_at TIMESTAMP NOT NULL,
    audio_chunk_id UUID REFERENCES audio_chunks(id) ON DELETE SET NULL,
    has_faces BOOLEAN DEFAULT NULL, -- NULL = not processed yet
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- 3. Conversations Table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audio_chunk_id UUID REFERENCES audio_chunks(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    detected_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_conversation_time CHECK (end_time > start_time)
);

-- 4. Transcriptions Table
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    audio_chunk_id UUID REFERENCES audio_chunks(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    confidence FLOAT,
    transcribed_at TIMESTAMP DEFAULT NOW()
);

-- 5. People Table (Face Recognition)
CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    relationship TEXT, -- e.g., "Father", "Mother", "Friend"
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Face Detections Table
CREATE TABLE face_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID REFERENCES images(id) ON DELETE CASCADE,
    person_id UUID REFERENCES people(id) ON DELETE SET NULL,
    confidence FLOAT,
    bounding_box JSONB, -- {x, y, width, height}
    detected_at TIMESTAMP DEFAULT NOW()
);

-- 7. Memories Table (Final processed memories)
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT,
    people_involved UUID[] DEFAULT '{}', -- Array of person IDs
    image_ids UUID[] DEFAULT '{}', -- Array of image IDs
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_audio_chunks_time ON audio_chunks(start_time, end_time);
CREATE INDEX idx_images_captured_at ON images(captured_at);
CREATE INDEX idx_images_audio_chunk ON images(audio_chunk_id);
CREATE INDEX idx_conversations_audio_chunk ON conversations(audio_chunk_id);
CREATE INDEX idx_transcriptions_conversation ON transcriptions(conversation_id);
CREATE INDEX idx_face_detections_image ON face_detections(image_id);
CREATE INDEX idx_face_detections_person ON face_detections(person_id);
CREATE INDEX idx_memories_time ON memories(start_time, end_time);

-- Enable Row Level Security (optional - disable for now during development)
-- ALTER TABLE audio_chunks ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE images ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transcriptions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE people ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE face_detections ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
