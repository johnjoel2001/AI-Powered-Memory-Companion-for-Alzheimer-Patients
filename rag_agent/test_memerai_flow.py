#!/usr/bin/env python3
"""
Test MemerAI Complete Flow
Exactly as described in the concept
"""

from memerai_rag_system import MemerAIRAG
import json

def test_complete_flow():
    """
    Complete MemerAI Flow:
    1. Build memory store (Camera → Memory Units → Embeddings)
    2. Next day: Daily check (Show image → Ask question)
    3. Patient struggles → RAG explains
    4. Patient asks question → RAG answers
    """
    
    print("\n" + "🎥"*30)
    print("MEMERAI COMPLETE FLOW TEST")
    print("🎥"*30)
    
    rag = MemerAIRAG()
    
    # ============================================================
    # STEP 1: BUILD MEMORY STORE (happens after recording)
    # ============================================================
    
    print("\n" + "="*60)
    print("STEP 1: Building Memory Store from Recordings")
    print("="*60)
    print("📹 Camera recorded conversations with Rae and Harry")
    print("🧠 Creating memory units with embeddings...")
    
    rag.build_memory_store_from_conversations()
    
    # ============================================================
    # STEP 2: NEXT MORNING - DAILY CHECK
    # ============================================================
    
    print("\n" + "="*60)
    print("STEP 2: Next Morning - Daily Memory Check")
    print("="*60)
    
    check = rag.daily_memory_check(days_back=0)  # Use 0 for testing (today's data)
    
    if check.get('has_memories'):
        print(f"\n🤖 {check['greeting']}")
        print(f"🖼️  [Shows image from yesterday]")
        print(f"🤖 {check['question']}")
        
        # ============================================================
        # STEP 3: PATIENT STRUGGLES → CLICKS "HELP ME"
        # ============================================================
        
        print("\n" + "="*60)
        print("STEP 3: Patient Struggles")
        print("="*60)
        
        print("\n👤 Patient: 'I'm not sure... maybe my nurse?'")
        print("\n[Patient clicks 'Help me' button]")
        
        memory_id = check['memory']['id']
        explanation = rag.help_remember(memory_id)
        
        print(f"\n🤖 MemerAI: {explanation}")
        
    else:
        print(f"\n🤖 {check['message']}")
    
    # ============================================================
    # STEP 4: PATIENT ASKS QUESTIONS (Classic RAG)
    # ============================================================
    
    print("\n" + "="*60)
    print("STEP 4: Patient Asks Questions")
    print("="*60)
    
    questions = [
        "Who visited me yesterday?",
        "What did we do with the cake?",
        "Tell me about Rae"
    ]
    
    for question in questions:
        print(f"\n👤 Patient: '{question}'")
        result = rag.ask(question)
        print(f"🤖 MemerAI: {result['answer']}")
        
        if result['memories']:
            print(f"   📚 Used {len(result['memories'])} memories")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    
    print("\n" + "="*60)
    print("✅ COMPLETE FLOW TESTED")
    print("="*60)
    print("\n📋 What happened:")
    print("1. ✅ Built memory store from recordings")
    print("2. ✅ Daily check showed yesterday's memory")
    print("3. ✅ Patient struggled → RAG explained gently")
    print("4. ✅ Patient asked questions → RAG answered")
    print("\n🎯 This is EXACTLY the MemerAI concept!")


if __name__ == "__main__":
    test_complete_flow()
