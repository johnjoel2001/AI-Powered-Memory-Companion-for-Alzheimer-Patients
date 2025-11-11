#!/usr/bin/env python3
"""
Batch Processor - Process all audio chunks to build knowledge graph
"""

import os
import time
from datetime import datetime
from memory_rag_agent import MemoryRAGAgent


def process_all_audio_chunks():
    """Process all audio chunks that haven't been analyzed yet"""
    agent = MemoryRAGAgent()
    
    print("="*60)
    print("BATCH PROCESSOR - Building Knowledge Graph")
    print("="*60)
    
    # Get all audio chunks
    result = agent.supabase.table('audio_chunks').select('id, filename, transcription').execute()
    audio_chunks = result.data
    
    print(f"\nFound {len(audio_chunks)} audio chunks")
    
    # Check which ones have already been processed
    processed_result = agent.supabase.table('conversation_summaries').select('audio_chunk_id').execute()
    processed_ids = {item['audio_chunk_id'] for item in processed_result.data}
    
    unprocessed = [chunk for chunk in audio_chunks if chunk['id'] not in processed_ids]
    
    print(f"Already processed: {len(processed_ids)}")
    print(f"To process: {len(unprocessed)}")
    
    if not unprocessed:
        print("\n✅ All audio chunks have been processed!")
        return
    
    # Process each unprocessed chunk
    print("\nProcessing audio chunks...")
    successful = 0
    failed = 0
    
    for i, chunk in enumerate(unprocessed, 1):
        try:
            print(f"\n[{i}/{len(unprocessed)}] Processing: {chunk['filename']}")
            
            if not chunk.get('transcription'):
                print("  ⚠️  No transcription available, skipping")
                continue
            
            result = agent.process_audio_chunk(chunk['id'])
            
            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
                failed += 1
            else:
                print(f"  ✅ Summary: {result.get('summary', '')[:100]}...")
                print(f"  📊 Sentiment: {result.get('sentiment', 'N/A')}")
                print(f"  🏷️  Topics: {', '.join(result.get('topics', []))}")
                successful += 1
            
            # Rate limiting to avoid API overload
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error processing chunk: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(unprocessed)}")


def reprocess_chunk(audio_chunk_id: str):
    """Reprocess a specific audio chunk (useful for testing)"""
    agent = MemoryRAGAgent()
    
    print(f"Reprocessing audio chunk: {audio_chunk_id}")
    
    # Delete existing summaries/events for this chunk
    agent.supabase.table('conversation_summaries').delete().eq('audio_chunk_id', audio_chunk_id).execute()
    agent.supabase.table('person_interactions').delete().eq('audio_chunk_id', audio_chunk_id).execute()
    agent.supabase.table('memory_events').delete().eq('audio_chunk_id', audio_chunk_id).execute()
    
    # Process again
    result = agent.process_audio_chunk(audio_chunk_id)
    
    print("\nResult:")
    print(f"Summary: {result.get('summary', '')}")
    print(f"Sentiment: {result.get('sentiment', '')}")
    print(f"Topics: {', '.join(result.get('topics', []))}")
    print(f"Memory Events: {len(result.get('memory_events', []))}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Reprocess specific chunk
        chunk_id = sys.argv[1]
        reprocess_chunk(chunk_id)
    else:
        # Process all unprocessed chunks
        process_all_audio_chunks()
