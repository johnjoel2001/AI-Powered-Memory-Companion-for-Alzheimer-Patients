#!/usr/bin/env python3
"""
Conversation Combiner
Combines consecutive audio chunks into complete conversations
If end_time difference <= 1 minute, merge them
"""

import os
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


class ConversationCombiner:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    def combine_conversations(self, person_name: str) -> list:
        """
        Combine audio chunks for a specific person into complete conversations
        
        Logic:
        1. Get all audio chunks with this person
        2. Sort by start_time ascending
        3. If end_time difference <= 1 minute, combine them
        4. Return list of combined conversations
        """
        
        # Get all images with this person
        images = self.supabase.table('images') \
            .select('audio_chunk_id, detected_persons') \
            .execute()
        
        # Find audio_chunk_ids where this person appears
        audio_chunk_ids = []
        for img in images.data:
            if img.get('detected_persons') and person_name.lower() in [p.lower() for p in img['detected_persons']]:
                audio_chunk_ids.append(img['audio_chunk_id'])
        
        audio_chunk_ids = list(set(audio_chunk_ids))  # Remove duplicates
        
        if not audio_chunk_ids:
            return []
        
        # Get all audio chunks for this person
        audio_chunks = []
        for chunk_id in audio_chunk_ids:
            result = self.supabase.table('audio_chunks') \
                .select('*') \
                .eq('id', chunk_id) \
                .execute()
            
            if result.data:
                audio_chunks.extend(result.data)
        
        # Sort by start_time
        audio_chunks.sort(key=lambda x: x.get('start_time', ''))
        
        # Combine consecutive chunks
        combined_conversations = []
        current_conversation = None
        
        for chunk in audio_chunks:
            start_time = datetime.fromisoformat(chunk['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(chunk['end_time'].replace('Z', '+00:00'))
            transcription = chunk.get('transcription', '')
            
            if not transcription:
                continue
            
            if current_conversation is None:
                # Start new conversation
                current_conversation = {
                    'person': person_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'transcription': transcription,
                    'audio_chunk_ids': [chunk['id']],
                    'chunk_count': 1
                }
            else:
                # Check if this chunk is within 1 minute of previous
                time_diff = (start_time - current_conversation['end_time']).total_seconds()
                
                if time_diff <= 60:  # <= 1 minute
                    # Combine with current conversation
                    current_conversation['transcription'] += ' ' + transcription
                    current_conversation['end_time'] = end_time
                    current_conversation['audio_chunk_ids'].append(chunk['id'])
                    current_conversation['chunk_count'] += 1
                else:
                    # Save current conversation and start new one
                    combined_conversations.append(current_conversation)
                    current_conversation = {
                        'person': person_name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'transcription': transcription,
                        'audio_chunk_ids': [chunk['id']],
                        'chunk_count': 1
                    }
        
        # Add last conversation
        if current_conversation:
            combined_conversations.append(current_conversation)
        
        return combined_conversations
    
    def combine_all_conversations(self) -> dict:
        """Combine conversations for ALL detected persons"""
        
        # Get all unique persons
        images = self.supabase.table('images').select('detected_persons').execute()
        
        all_persons = set()
        for img in images.data:
            if img.get('detected_persons'):
                all_persons.update([p.lower() for p in img['detected_persons']])
        
        all_persons = list(all_persons)
        
        # Combine conversations for each person
        results = {}
        for person in all_persons:
            conversations = self.combine_conversations(person)
            results[person] = conversations
        
        return results
    
    def print_summary(self, results: dict):
        """Print summary of combined conversations"""
        
        print("\n" + "="*60)
        print("COMBINED CONVERSATIONS SUMMARY")
        print("="*60)
        
        for person, conversations in results.items():
            print(f"\n👤 {person.upper()}:")
            print(f"   Total Conversations: {len(conversations)}")
            
            for i, conv in enumerate(conversations, 1):
                duration = (conv['end_time'] - conv['start_time']).total_seconds()
                print(f"\n   Conversation {i}:")
                print(f"   ├─ Duration: {duration:.0f} seconds")
                print(f"   ├─ Chunks Combined: {conv['chunk_count']}")
                print(f"   ├─ Start: {conv['start_time'].strftime('%H:%M:%S')}")
                print(f"   ├─ End: {conv['end_time'].strftime('%H:%M:%S')}")
                print(f"   └─ Text: {conv['transcription'][:100]}...")
    
    def create_combined_conversations_table(self):
        """Create table to store combined conversations"""
        
        sql = """
        -- Combined Conversations Table
        CREATE TABLE IF NOT EXISTS combined_conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            person_name TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            duration_seconds INT NOT NULL,
            full_transcription TEXT NOT NULL,
            audio_chunk_ids UUID[] NOT NULL,
            chunk_count INT NOT NULL,
            conversation_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_combined_conversations_person ON combined_conversations(person_name);
        CREATE INDEX IF NOT EXISTS idx_combined_conversations_date ON combined_conversations(conversation_date);
        CREATE INDEX IF NOT EXISTS idx_combined_conversations_start ON combined_conversations(start_time);
        """
        
        return sql
    
    def save_combined_conversations(self, results: dict):
        """Save combined conversations to database"""
        
        for person, conversations in results.items():
            for conv in conversations:
                duration = int((conv['end_time'] - conv['start_time']).total_seconds())
                
                data = {
                    'person_name': person,
                    'start_time': conv['start_time'].isoformat(),
                    'end_time': conv['end_time'].isoformat(),
                    'duration_seconds': duration,
                    'full_transcription': conv['transcription'],
                    'audio_chunk_ids': conv['audio_chunk_ids'],
                    'chunk_count': conv['chunk_count'],
                    'conversation_date': conv['start_time'].date().isoformat()
                }
                
                self.supabase.table('combined_conversations').insert(data).execute()
        
        print("\n✅ Combined conversations saved to database!")


if __name__ == "__main__":
    combiner = ConversationCombiner()
    
    print("="*60)
    print("CONVERSATION COMBINER")
    print("="*60)
    print("\nCombining audio chunks within 1 minute...")
    
    # Combine all conversations
    results = combiner.combine_all_conversations()
    
    # Print summary
    combiner.print_summary(results)
    
    # Show SQL for table creation
    print("\n" + "="*60)
    print("SQL TO CREATE TABLE (run in Supabase):")
    print("="*60)
    print(combiner.create_combined_conversations_table())
    
    # Ask if user wants to save
    print("\n" + "="*60)
    print("To save combined conversations to database:")
    print("1. Run the SQL above in Supabase")
    print("2. Then run: combiner.save_combined_conversations(results)")
    print("="*60)
