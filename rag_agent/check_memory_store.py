#!/usr/bin/env python3
"""Check what's in the memory store"""

from memerai_rag_system import MemerAIRAG

rag = MemerAIRAG()

# Check memory store
result = rag.supabase.table('memory_store').select('*').execute()

print("="*60)
print("MEMORY STORE CONTENTS")
print("="*60)

for mem in result.data:
    print(f"\n📝 Memory ID: {mem['id']}")
    print(f"   Person: {mem['person']}")
    print(f"   Event: {mem['event']}")
    print(f"   Summary: {mem['summary_text']}")
    print(f"   Has Embedding: {'✅' if mem.get('embedding') else '❌'}")
    print(f"   Time: {mem['memory_time']}")

print(f"\n📊 Total memories: {len(result.data)}")
