#!/usr/bin/env python3
"""
Test what happens when patient gives wrong answer
"""

from intelligent_conversation import IntelligentConversation

print("="*60)
print("TEST: Patient gives WRONG answer")
print("="*60)

conv = IntelligentConversation()

# Step 1: Start conversation
print("\n🤖 UI starts the conversation")
print("-" * 60)
first_question = conv.start_conversation()
print(f"UI: {first_question['question']}")

if first_question.get('has_memories'):
    expected_persons = first_question.get('expected_persons', [])
    print(f"\n(Expected answer: {expected_persons})")
    
    # Step 2: Patient gives WRONG answer
    print("\n👤 Patient gives WRONG answer")
    print("-" * 60)
    wrong_answer = "Harry"  # But correct is "Rae"
    print(f"Patient: {wrong_answer}")
    
    response = conv.process_answer(wrong_answer, "person_recall")
    print(f"\nUI: {response['response']}")
    
    if response.get('next_question'):
        print(f"UI: {response['next_question']}")
        print("\n✅ System helps patient by telling them the correct answer!")
        print("   Then continues the conversation")
