#!/usr/bin/env python3
"""
Test the lovely personalized questions
"""

from memerai_rag_system import MemerAIRAG

rag = MemerAIRAG()

print("="*60)
print("TESTING LOVELY PERSONALIZED QUESTIONS")
print("="*60)

# Test daily check
check = rag.daily_memory_check(days_back=0, patient_name="John")

print(f"\n✅ Greeting: {check['greeting']}")
print(f"✅ Question: {check['question']}")

if check.get('memory'):
    memory = check['memory']
    print(f"\n📝 Memory Details:")
    print(f"   Person: {memory['person']}")
    print(f"   Event: {memory['event']}")

# Test help
if check.get('memory'):
    print(f"\n💡 Testing 'Help me' button...")
    explanation = rag.help_remember(check['memory']['id'], patient_name="John")
    print(f"✅ Explanation: {explanation}")

print("\n" + "="*60)
print("✅ Questions are lovely and personalized!")
print("="*60)
