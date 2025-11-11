#!/usr/bin/env python3
"""
FULL TEST - Complete conversation simulation
Tests: correct answers, wrong answers, hints, scoring
"""

from complete_memory_system import CompleteMemorySystem

def test_scenario_1_perfect_memory():
    """Test: Patient remembers everything correctly"""
    print("\n" + "="*60)
    print("SCENARIO 1: Perfect Memory (All Correct Answers)")
    print("="*60)
    
    system = CompleteMemorySystem()
    
    # Start
    q1 = system.start_conversation(days_back=0)
    print(f"\n🤖 UI: {q1['question']}")
    print(f"   Expected: {q1.get('expected_persons', [])}")
    
    # Answer 1: Correct person
    print(f"\n👤 Patient: Rae")
    r1 = system.process_answer("Rae", "person_recall")
    print(f"🤖 UI: {r1['response']}")
    if r1.get('next_question'):
        print(f"🤖 UI: {r1['next_question']}")
        print(f"   Score: {r1.get('memory_score', {})}")
    
    # Answer 2: Correct event
    print(f"\n👤 Patient: We cut a cake")
    r2 = system.process_answer("We cut a cake", "event_recall")
    print(f"🤖 UI: {r2['response']}")
    if r2.get('next_question'):
        print(f"🤖 UI: {r2['next_question']}")
        print(f"   Score: {r2.get('memory_score', {})}")
    
    # Answer 3: Detail
    if r2.get('type') == 'detail_recall':
        print(f"\n👤 Patient: Chocolate")
        r3 = system.process_answer("Chocolate", "detail_recall")
        print(f"🤖 UI: {r3['response']}")
        print(f"   Final Score: {r3.get('memory_score', {})}")
        if r3.get('final_message'):
            print(f"🤖 UI: {r3['final_message']}")


def test_scenario_2_needs_hints():
    """Test: Patient needs hints"""
    print("\n" + "="*60)
    print("SCENARIO 2: Patient Needs Hints")
    print("="*60)
    
    system = CompleteMemorySystem()
    
    # Start
    q1 = system.start_conversation(days_back=0)
    print(f"\n🤖 UI: {q1['question']}")
    print(f"   Expected: {q1.get('expected_persons', [])}")
    
    # Answer 1: WRONG person
    print(f"\n👤 Patient: John")
    r1 = system.process_answer("John", "person_recall")
    print(f"🤖 UI: {r1['response']}")
    if r1.get('next_question'):
        print(f"🤖 UI: {r1['next_question']}")
        if r1.get('is_hint'):
            print(f"   💡 HINT GIVEN")
        print(f"   Score: {r1.get('memory_score', {})}")
    
    # Answer 2: Still wrong, but system helps
    print(f"\n👤 Patient: I don't remember")
    r2 = system.process_answer("I don't remember", "person_recall")
    print(f"🤖 UI: {r2['response']}")
    if r2.get('next_question'):
        print(f"🤖 UI: {r2['next_question']}")
        print(f"   Score: {r2.get('memory_score', {})}")
    
    # Answer 3: Now answer the event question
    print(f"\n👤 Patient: Birthday")
    r3 = system.process_answer("Birthday", "event_recall")
    print(f"🤖 UI: {r3['response']}")
    if r3.get('next_question'):
        print(f"🤖 UI: {r3['next_question']}")
        print(f"   Score: {r3.get('memory_score', {})}")


def test_scenario_3_multiple_persons():
    """Test: Check if system handles multiple persons"""
    print("\n" + "="*60)
    print("SCENARIO 3: Multiple Persons Detected")
    print("="*60)
    
    system = CompleteMemorySystem()
    
    # Start
    q1 = system.start_conversation(days_back=0)
    print(f"\n🤖 UI: {q1['question']}")
    
    expected = q1.get('expected_persons', [])
    print(f"   ✅ Found {len(expected)} persons: {expected}")
    
    # Check if both Rae and Harry are detected
    if 'rae' in expected and 'harry' in expected:
        print(f"   ✅ System correctly detected BOTH Rae and Harry!")
    
    # Answer with one person
    print(f"\n👤 Patient: Harry")
    r1 = system.process_answer("Harry", "person_recall")
    print(f"🤖 UI: {r1['response']}")
    if r1.get('next_question'):
        print(f"🤖 UI: {r1['next_question']}")


def test_scenario_4_check_data():
    """Test: Show what data the system is reading"""
    print("\n" + "="*60)
    print("SCENARIO 4: Data Check")
    print("="*60)
    
    system = CompleteMemorySystem()
    
    # Start to load data
    result = system.start_conversation(days_back=0)
    
    if result.get('has_memories'):
        person_convs = system.conversation_state.get('person_conversations', {})
        
        print(f"\n📊 Data Summary:")
        print(f"   Total persons detected: {len(person_convs)}")
        
        for person, conversations in person_convs.items():
            print(f"\n   👤 {person.upper()}:")
            print(f"      Conversations: {len(conversations)}")
            for i, conv in enumerate(conversations[:2], 1):  # Show first 2
                print(f"      {i}. {conv['transcription'][:80]}...")
    else:
        print("   ⚠️  No memories found")


# Run all tests
if __name__ == "__main__":
    print("\n" + "🧠"*30)
    print("COMPLETE MEMORY SYSTEM - FULL TEST SUITE")
    print("🧠"*30)
    
    test_scenario_4_check_data()
    test_scenario_3_multiple_persons()
    test_scenario_1_perfect_memory()
    test_scenario_2_needs_hints()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60)
