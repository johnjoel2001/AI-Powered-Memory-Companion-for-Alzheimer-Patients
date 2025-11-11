#!/usr/bin/env python3
"""
Cognitive Improvement System for Alzheimer's Patients
Tracks memory performance over time and adapts to improve cognition
"""

import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


class CognitiveImprovementSystem:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.patient_id = "patient_001"  # Can be dynamic
    
    def create_memory_tracking_tables(self):
        """Create tables to track memory performance over time"""
        
        sql = """
        -- Memory Performance Tracking
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
            session_id UUID REFERENCES memory_sessions(id),
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
        
        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_memory_sessions_patient ON memory_sessions(patient_id);
        CREATE INDEX IF NOT EXISTS idx_memory_sessions_date ON memory_sessions(session_date);
        CREATE INDEX IF NOT EXISTS idx_question_performance_patient ON question_performance(patient_id);
        CREATE INDEX IF NOT EXISTS idx_memory_retention_patient ON memory_retention(patient_id);
        """
        
        return sql
    
    def start_session(self, days_back: int = 0):
        """Start a new memory session and create session record"""
        
        # Create session record
        session_data = {
            'patient_id': self.patient_id,
            'session_date': datetime.now().isoformat(),
            'difficulty_level': self._get_adaptive_difficulty()
        }
        
        result = self.supabase.table('memory_sessions').insert(session_data).execute()
        session_id = result.data[0]['id']
        
        return {
            'session_id': session_id,
            'difficulty': session_data['difficulty_level'],
            'start_time': datetime.now()
        }
    
    def _get_adaptive_difficulty(self):
        """Determine difficulty based on recent performance"""
        
        try:
            # Get last 5 sessions
            result = self.supabase.table('memory_sessions') \
                .select('score_percentage') \
                .eq('patient_id', self.patient_id) \
                .order('session_date', desc=True) \
                .limit(5) \
                .execute()
            
            if not result.data:
                return 'easy'
            
            # Calculate average score
            scores = [s['score_percentage'] for s in result.data]
            avg_score = sum(scores) / len(scores)
            
            # Adaptive difficulty
            if avg_score >= 80:
                return 'hard'
            elif avg_score >= 60:
                return 'medium'
            else:
                return 'easy'
        except:
            return 'easy'
    
    def record_question_performance(self, session_id, question_data):
        """Record performance for a single question"""
        
        perf_data = {
            'session_id': session_id,
            'patient_id': self.patient_id,
            'question_type': question_data['type'],
            'question_text': question_data['question'],
            'patient_answer': question_data.get('answer', ''),
            'correct_answer': question_data.get('expected', ''),
            'was_correct': question_data.get('correct', False),
            'hints_given': question_data.get('hints', 0),
            'response_time_seconds': question_data.get('time', 0),
            'memory_topic': question_data.get('topic', '')
        }
        
        self.supabase.table('question_performance').insert(perf_data).execute()
        
        # Update retention tracking
        self._update_retention_tracking(question_data)
    
    def _update_retention_tracking(self, question_data):
        """Track how well patient retains specific memories over time"""
        
        topic = question_data.get('topic', '')
        person = question_data.get('person', '')
        
        if not topic:
            return
        
        # Check if we've asked about this before
        result = self.supabase.table('memory_retention') \
            .select('*') \
            .eq('patient_id', self.patient_id) \
            .eq('memory_topic', topic) \
            .execute()
        
        if result.data:
            # Update existing record
            record = result.data[0]
            times_asked = record['times_asked'] + 1
            times_correct = record['times_correct'] + (1 if question_data.get('correct') else 0)
            retention_rate = (times_correct / times_asked) * 100
            
            self.supabase.table('memory_retention') \
                .update({
                    'last_asked': datetime.now().isoformat(),
                    'times_asked': times_asked,
                    'times_correct': times_correct,
                    'retention_rate': retention_rate
                }) \
                .eq('id', record['id']) \
                .execute()
        else:
            # Create new record
            self.supabase.table('memory_retention').insert({
                'patient_id': self.patient_id,
                'memory_topic': topic,
                'person_involved': person,
                'times_asked': 1,
                'times_correct': 1 if question_data.get('correct') else 0,
                'retention_rate': 100 if question_data.get('correct') else 0
            }).execute()
    
    def end_session(self, session_id, session_stats):
        """End session and update final statistics"""
        
        self.supabase.table('memory_sessions') \
            .update({
                'total_questions': session_stats['total'],
                'correct_answers': session_stats['correct'],
                'hints_used': session_stats['hints'],
                'score_percentage': session_stats['percentage'],
                'session_duration_seconds': session_stats['duration']
            }) \
            .eq('id', session_id) \
            .execute()
    
    def get_progress_report(self, days: int = 30):
        """Generate cognitive improvement progress report"""
        
        # Get sessions from last N days
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        sessions = self.supabase.table('memory_sessions') \
            .select('*') \
            .eq('patient_id', self.patient_id) \
            .gte('session_date', start_date) \
            .order('session_date', desc=False) \
            .execute()
        
        if not sessions.data:
            return {
                'message': 'No sessions found',
                'sessions': []
            }
        
        # Calculate trends
        scores = [s['score_percentage'] for s in sessions.data]
        
        report = {
            'total_sessions': len(sessions.data),
            'average_score': sum(scores) / len(scores) if scores else 0,
            'latest_score': scores[-1] if scores else 0,
            'first_score': scores[0] if scores else 0,
            'improvement': scores[-1] - scores[0] if len(scores) > 1 else 0,
            'trend': 'improving' if len(scores) > 1 and scores[-1] > scores[0] else 'stable',
            'sessions': sessions.data,
            'score_history': scores
        }
        
        # Get retention data
        retention = self.supabase.table('memory_retention') \
            .select('*') \
            .eq('patient_id', self.patient_id) \
            .order('retention_rate', desc=False) \
            .execute()
        
        report['retention_data'] = retention.data
        report['weak_memories'] = [r for r in retention.data if r['retention_rate'] < 50]
        report['strong_memories'] = [r for r in retention.data if r['retention_rate'] >= 80]
        
        return report
    
    def get_recommendations(self):
        """Get AI-powered recommendations for cognitive improvement"""
        
        report = self.get_progress_report(days=7)
        
        if report.get('sessions'):
            prompt = f"""Based on this Alzheimer's patient's memory performance, provide recommendations:

Recent Performance:
- Average Score: {report['average_score']:.1f}%
- Improvement: {report['improvement']:.1f}%
- Weak Memories: {len(report['weak_memories'])}
- Strong Memories: {len(report['strong_memories'])}

Provide 3-5 specific recommendations to improve cognitive function.
Return JSON: {{"recommendations": ["rec1", "rec2", ...]}}
"""
            
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a cognitive health specialist."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        
        return {"recommendations": ["Complete more sessions to get personalized recommendations"]}


if __name__ == "__main__":
    system = CognitiveImprovementSystem()
    
    print("="*60)
    print("COGNITIVE IMPROVEMENT SYSTEM")
    print("="*60)
    
    # Show SQL for table creation
    print("\n📊 Database Schema:")
    print(system.create_memory_tracking_tables())
    
    print("\n✅ System ready to track cognitive improvement!")
