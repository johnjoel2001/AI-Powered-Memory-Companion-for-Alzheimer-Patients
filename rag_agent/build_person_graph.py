#!/usr/bin/env python3
"""
Build Person Memory Graph from all audio chunks
"""

from person_graph_builder import PersonGraphBuilder
import time


def build_graph_for_all_chunks():
    """Process all audio chunks and build person-centric memory graph"""
    
    builder = PersonGraphBuilder()
    
    print("="*60)
    print("BUILDING PERSON MEMORY GRAPH")
    print("="*60)
    
    # Get all audio chunks
    result = builder.supabase.table('audio_chunks').select('id, filename').execute()
    audio_chunks = result.data
    
    print(f"\nFound {len(audio_chunks)} audio chunks")
    
    # Check which ones have been processed
    processed_result = builder.supabase.table('person_memories').select('audio_chunk_id').execute()
    processed_ids = {item['audio_chunk_id'] for item in processed_result.data}
    
    unprocessed = [chunk for chunk in audio_chunks if chunk['id'] not in processed_ids]
    
    print(f"Already processed: {len(processed_ids)}")
    print(f"To process: {len(unprocessed)}")
    
    if not unprocessed:
        print("\n✅ All audio chunks have been processed!")
        return
    
    # Process each chunk
    print("\nProcessing audio chunks...")
    successful = 0
    failed = 0
    total_memories = 0
    
    for i, chunk in enumerate(unprocessed, 1):
        try:
            print(f"\n[{i}/{len(unprocessed)}] Processing: {chunk['filename']}")
            
            result = builder.build_person_memory(chunk['id'])
            
            if result.get('success'):
                memories_count = result.get('memories_created', 0)
                print(f"  ✅ Created {memories_count} person memories")
                successful += 1
                total_memories += memories_count
            else:
                print(f"  ⚠️  {result.get('error', 'Unknown error')}")
                failed += 1
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("GRAPH BUILDING COMPLETE")
    print("="*60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total person memories created: {total_memories}")
    print(f"📈 Average memories per chunk: {total_memories/successful if successful > 0 else 0:.1f}")


def show_person_summary():
    """Show summary of all persons in the graph"""
    
    builder = PersonGraphBuilder()
    
    print("\n" + "="*60)
    print("PERSON MEMORY GRAPH SUMMARY")
    print("="*60)
    
    # Get unique persons
    result = builder.supabase.table('person_memories').select('person_name').execute()
    
    persons = {}
    for item in result.data:
        name = item['person_name']
        persons[name] = persons.get(name, 0) + 1
    
    print(f"\nTotal persons: {len(persons)}")
    print(f"Total conversations: {sum(persons.values())}")
    
    print("\nPer person:")
    for name, count in sorted(persons.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {count} conversations")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'summary':
        show_person_summary()
    else:
        build_graph_for_all_chunks()
        show_person_summary()
