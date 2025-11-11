-- Cognitive Improvement Tracking Schema
-- Run this in Supabase SQL Editor

-- Memory Performance Tracking (Session-level)
CREATE TABLE IF NOT EXISTS memory_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id TEXT NOT NULL,
    session_date TIMESTAMP DEFAULT NOW(),
    total_questions INT DEFAULT 0,
    correct_answers INT DEFAULT 0,
    hints_used INT DEFAULT 0,
    score_percentage FLOAT DEFAULT 0,
    difficulty_level TEXT DEFAULT 'easy',
    session_duration_seconds INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Individual Question Performance
CREATE TABLE IF NOT EXISTS question_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES memory_sessions(id) ON DELETE CASCADE,
    patient_id TEXT NOT NULL,
    question_type TEXT NOT NULL, -- person_recall, event_recall, detail_recall
    question_text TEXT NOT NULL,
    patient_answer TEXT,
    correct_answer TEXT,
    was_correct BOOLEAN DEFAULT FALSE,
    hints_given INT DEFAULT 0,
    response_time_seconds INT DEFAULT 0,
    memory_topic TEXT, -- e.g., "birthday", "conversation with Rae"
    created_at TIMESTAMP DEFAULT NOW()
);

-- Memory Retention Tracking (same question over time)
CREATE TABLE IF NOT EXISTS memory_retention (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id TEXT NOT NULL,
    memory_topic TEXT NOT NULL,
    person_involved TEXT,
    first_asked TIMESTAMP DEFAULT NOW(),
    last_asked TIMESTAMP DEFAULT NOW(),
    times_asked INT DEFAULT 1,
    times_correct INT DEFAULT 0,
    retention_rate FLOAT DEFAULT 0,
    days_since_event INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_memory_sessions_patient ON memory_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_memory_sessions_date ON memory_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_question_performance_patient ON question_performance(patient_id);
CREATE INDEX IF NOT EXISTS idx_question_performance_session ON question_performance(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_retention_patient ON memory_retention(patient_id);
CREATE INDEX IF NOT EXISTS idx_memory_retention_topic ON memory_retention(memory_topic);

-- View: Latest Session Performance
CREATE OR REPLACE VIEW latest_session_performance AS
SELECT 
    patient_id,
    session_date,
    score_percentage,
    total_questions,
    correct_answers,
    hints_used,
    difficulty_level
FROM memory_sessions
ORDER BY session_date DESC;

-- View: Memory Retention Summary
CREATE OR REPLACE VIEW memory_retention_summary AS
SELECT 
    patient_id,
    memory_topic,
    person_involved,
    retention_rate,
    times_asked,
    times_correct,
    CASE 
        WHEN retention_rate >= 80 THEN 'Strong'
        WHEN retention_rate >= 50 THEN 'Moderate'
        ELSE 'Weak'
    END as memory_strength
FROM memory_retention
ORDER BY retention_rate ASC;

-- Function: Get Patient Progress
CREATE OR REPLACE FUNCTION get_patient_progress(
    p_patient_id TEXT,
    p_days INT DEFAULT 30
)
RETURNS TABLE (
    session_date TIMESTAMP,
    score_percentage FLOAT,
    total_questions INT,
    improvement FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH sessions AS (
        SELECT 
            ms.session_date,
            ms.score_percentage,
            ms.total_questions,
            LAG(ms.score_percentage) OVER (ORDER BY ms.session_date) as prev_score
        FROM memory_sessions ms
        WHERE ms.patient_id = p_patient_id
        AND ms.session_date >= NOW() - (p_days || ' days')::INTERVAL
        ORDER BY ms.session_date
    )
    SELECT 
        s.session_date,
        s.score_percentage,
        s.total_questions,
        COALESCE(s.score_percentage - s.prev_score, 0.0) as improvement
    FROM sessions s;
END;
$$;

-- Function: Get Weak Memories (need reinforcement)
CREATE OR REPLACE FUNCTION get_weak_memories(
    p_patient_id TEXT,
    p_threshold FLOAT DEFAULT 50.0
)
RETURNS TABLE (
    memory_topic TEXT,
    person_involved TEXT,
    retention_rate FLOAT,
    times_asked INT,
    last_asked TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mr.memory_topic,
        mr.person_involved,
        mr.retention_rate,
        mr.times_asked,
        mr.last_asked
    FROM memory_retention mr
    WHERE mr.patient_id = p_patient_id
    AND mr.retention_rate < p_threshold
    ORDER BY mr.retention_rate ASC, mr.last_asked ASC;
END;
$$;
