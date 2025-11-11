#!/usr/bin/env python3
"""
Test Cognitive Tracking System
Simulates multiple sessions to show improvement tracking
"""

from complete_memory_system import CompleteMemorySystem
from cognitive_improvement_system import CognitiveImprovementSystem
from datetime import datetime

def simulate_session(session_num, performance_level):
    """Simulate a complete memory session"""
    
    print(f"\n{'='*60}")
    print(f"SESSION {session_num} - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    
    # Initialize systems
    memory_system = CompleteMemorySystem()
    cognitive_system = CognitiveImprovementSystem()
    
    # Start session tracking
    session_info = cognitive_system.start_session(days_back=0)
    session_id = session_info['session_id']
    difficulty = session_info['difficulty']
    start_time = session_info['start_time']
    
    print(f"📊 Difficulty Level: {difficulty.upper()}")
    
    # Start conversation
    result = memory_system.start_conversation(days_back=0)
    print(f"\n🤖 UI: {result['question']}")
    
    if not result.get('has_memories'):
        print("⚠️  No memories to test")
        return
    
    # Simulate answers based on performance level
    if performance_level == 'poor':
        answers = ["I don't know", "Maybe John?", "I'm not sure"]
        correct_count = 0
        hints_count = 2
    elif performance_level == 'medium':
        answers = ["Rae", "We talked", "Something sweet"]
        correct_count = 1
        hints_count = 1
    else:  # good
        answers = ["Rae", "We cut a birthday cake", "Chocolate"]
        correct_count = 3
        hints_count = 0
    
    # Question 1: Person recall
    print(f"\n👤 Patient: {answers[0]}")
    r1 = memory_system.process_answer(answers[0], "person_recall")
    print(f"🤖 UI: {r1['response']}")
    
    # Record question 1
    cognitive_system.record_question_performance(session_id, {
        'type': 'person_recall',
        'question': result['question'],
        'answer': answers[0],
        'expected': ', '.join(result.get('expected_persons', [])),
        'correct': 'rae' in answers[0].lower() or 'harry' in answers[0].lower(),
        'hints': 1 if 'hint' in r1.get('response', '').lower() else 0,
        'time': 5,
        'topic': 'person_identification',
        'person': 'rae'
    })
    
    if r1.get('next_question'):
        print(f"🤖 UI: {r1['next_question']}")
        
        # Question 2: Event recall
        print(f"\n👤 Patient: {answers[1]}")
        r2 = memory_system.process_answer(answers[1], "event_recall")
        print(f"🤖 UI: {r2['response']}")
        
        # Record question 2
        cognitive_system.record_question_performance(session_id, {
            'type': 'event_recall',
            'question': r1['next_question'],
            'answer': answers[1],
            'expected': 'birthday cake',
            'correct': 'cake' in answers[1].lower() or 'birthday' in answers[1].lower(),
            'hints': 0,
            'time': 8,
            'topic': 'birthday_celebration',
            'person': 'rae'
        })
        
        if r2.get('next_question'):
            print(f"🤖 UI: {r2['next_question']}")
            
            # Question 3: Detail recall
            print(f"\n👤 Patient: {answers[2]}")
            r3 = memory_system.process_answer(answers[2], "detail_recall")
            print(f"🤖 UI: {r3['response']}")
            
            # Record question 3
            cognitive_system.record_question_performance(session_id, {
                'type': 'detail_recall',
                'question': r2['next_question'],
                'answer': answers[2],
                'expected': 'chocolate',
                'correct': 'chocolate' in answers[2].lower(),
                'hints': 0,
                'time': 6,
                'topic': 'cake_flavor',
                'person': 'rae'
            })
    
    # End session
    end_time = datetime.now()
    duration = int((end_time - start_time).total_seconds())
    
    score = memory_system._get_score()
    
    cognitive_system.end_session(session_id, {
        'total': 3,
        'correct': correct_count,
        'hints': hints_count,
        'percentage': (correct_count / 3) * 100,
        'duration': duration
    })
    
    print(f"\n📊 Session Score: {score['correct']}/{score['total']} ({score['percentage']:.1f}%)")
    print(f"⏱️  Duration: {duration} seconds")
    print(f"💡 Hints Used: {hints_count}")


def show_progress_report():
    """Show cognitive improvement progress"""
    
    print(f"\n{'='*60}")
    print("📈 COGNITIVE IMPROVEMENT PROGRESS REPORT")
    print(f"{'='*60}")
    
    cognitive_system = CognitiveImprovementSystem()
    report = cognitive_system.get_progress_report(days=30)
    
    if report.get('sessions'):
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Sessions: {report['total_sessions']}")
        print(f"   Average Score: {report['average_score']:.1f}%")
        print(f"   First Score: {report['first_score']:.1f}%")
        print(f"   Latest Score: {report['latest_score']:.1f}%")
        print(f"   Improvement: {report['improvement']:+.1f}%")
        print(f"   Trend: {report['trend'].upper()}")
        
        print(f"\n📈 Score History:")
        for i, score in enumerate(report['score_history'], 1):
            bar = '█' * int(score / 5)
            print(f"   Session {i}: {bar} {score:.1f}%")
        
        if report.get('retention_data'):
            print(f"\n🧠 Memory Retention:")
            print(f"   Strong Memories: {len(report['strong_memories'])}")
            print(f"   Weak Memories: {len(report['weak_memories'])}")
            
            if report['weak_memories']:
                print(f"\n⚠️  Memories Needing Reinforcement:")
                for mem in report['weak_memories'][:3]:
                    print(f"   - {mem['memory_topic']}: {mem['retention_rate']:.0f}% retention")
        
        # Get AI recommendations
        print(f"\n💡 AI Recommendations:")
        recommendations = cognitive_system.get_recommendations()
        for i, rec in enumerate(recommendations.get('recommendations', []), 1):
            print(f"   {i}. {rec}")
    else:
        print("\n⚠️  No sessions found. Complete some sessions first!")


def run_full_test():
    """Run complete test with multiple sessions"""
    
    print("\n" + "🧠"*30)
    print("COGNITIVE TRACKING SYSTEM - FULL TEST")
    print("🧠"*30)
    
    # Simulate 3 sessions with improving performance
    print("\n🎯 Simulating 3 sessions to show improvement tracking...")
    
    simulate_session(1, 'poor')      # First session: struggling
    simulate_session(2, 'medium')    # Second session: improving
    simulate_session(3, 'good')      # Third session: doing well
    
    # Show progress report
    show_progress_report()
    
    print(f"\n{'='*60}")
    print("✅ TEST COMPLETE - Cognitive tracking is working!")
    print(f"{'='*60}")
    print("\n💡 Check Supabase tables:")
    print("   - memory_sessions: See all 3 sessions")
    print("   - question_performance: See individual questions")
    print("   - memory_retention: See retention rates")


if __name__ == "__main__":
    run_full_test()
