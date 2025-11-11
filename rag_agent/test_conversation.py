#!/usr/bin/env python3
"""
Test the intelligent conversation system
"""

from intelligent_conversation import IntelligentConversation

print("="*60)
print("TESTING INTELLIGENT CONVERSATION")
print("="*60)

conv = IntelligentConversation()

# Step 1: Start conversation
print("\n🤖 STEP 1: UI starts the conversation")
print("-" * 60)
first_question = conv.start_conversation()
print(f"UI: {first_question['question']}")
print(f"Type: {first_question['type']}")
print(f"Has memories: {first_question.get('has_memories', False)}")

if first_question.get('has_memories'):
    # Step 2: Patient answers about who they spoke with
    print("\n👤 STEP 2: Patient answers")
    print("-" * 60)
    patient_answer_1 = "Rae"
    print(f"Patient: {patient_answer_1}")
    
    response_1 = conv.process_answer(patient_answer_1, "person_recall")
    print(f"\nUI: {response_1['response']}")
    
    if response_1.get('next_question'):
        print(f"UI: {response_1['next_question']}")
        
        # Step 3: Patient answers about what they did
        print("\n👤 STEP 3: Patient answers about event")
        print("-" * 60)
        patient_answer_2 = "We cut a cake"
        print(f"Patient: {patient_answer_2}")
        
        response_2 = conv.process_answer(patient_answer_2, "event_recall")
        print(f"\nUI: {response_2['response']}")
        
        if response_2.get('success'):
            print("\n✅ SUCCESS: Patient remembered correctly!")
        else:
            print("\n⚠️  Patient needed help remembering")
else:
    print("\n⚠️  No memories from yesterday found in database")
    print("💡 Tip: The system looks for conversations from yesterday")
    print("   Your data is from today, so it won't find anything")
    print("\n   To test with real data:")
    print("   1. Wait until tomorrow, OR")
    print("   2. Manually change the dates in your Supabase data")

print("\n" + "="*60)
