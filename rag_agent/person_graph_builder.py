#!/usr/bin/env python3
"""
Person Memory Graph Builder
Builds a knowledge graph organized by person name
Structure: {person_name: [conversations, summaries]}
"""

import os
import json
from datetime import datetime
from typing import List, Dict
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class PersonGraphBuilder:
    def __init__(self):
        """Initialize the Person Graph Builder"""
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
    
    def build_person_memory(self, audio_chunk_id: str) -> Dict:
        """
        Build person-centric memory from audio chunk
        
        Process:
        1. Get audio transcription
        2. Get detected persons from images
        3. For each person, extract what was said to/about them
        4. Create summary
        5. Generate embedding
        6. Store in person_memories table
        """
        # Get audio chunk
        audio_result = self.supabase.table('audio_chunks').select('*').eq('id', audio_chunk_id).execute()
        
        if not audio_result.data:
            return {"error": "Audio chunk not found"}
        
        audio_chunk = audio_result.data[0]
        transcription = audio_chunk.get('transcription', '')
        conversation_date = audio_chunk.get('end_time', datetime.now().isoformat())
        
        if not transcription:
            return {"error": "No transcription available"}
        
        # Get detected persons from images
        images_result = self.supabase.table('images').select('*').eq('audio_chunk_id', audio_chunk_id).execute()
        
        detected_persons = set()
        for img in images_result.data:
            if img.get('detected_persons'):
                detected_persons.update(img['detected_persons'])
        
        detected_persons = list(detected_persons)
        
        if not detected_persons:
            print("⚠️  No persons detected in images")
            return {"error": "No persons detected"}
        
        print(f"📸 Detected persons: {', '.join(detected_persons)}")
        
        # For each person, extract their conversation
        results = []
        for person_name in detected_persons:
            person_memory = self._extract_person_conversation(
                person_name,
                transcription,
                audio_chunk_id,
                conversation_date
            )
            
            if person_memory:
                results.append(person_memory)
        
        return {
            "success": True,
            "persons": detected_persons,
            "memories_created": len(results),
            "results": results
        }
    
    def _extract_person_conversation(
        self,
        person_name: str,
        full_transcription: str,
        audio_chunk_id: str,
        conversation_date: str
    ) -> Dict:
        """Extract conversation specific to this person"""
        
        try:
            # Use LLM to extract person-specific conversation
            prompt = f"""Analyze this conversation and extract what was said TO or ABOUT {person_name}.

Full Conversation:
{full_transcription}

Person: {person_name}

Provide a JSON response:
{{
    "conversation_text": "The parts of conversation involving {person_name}",
    "summary": "Brief summary of what was discussed with/about {person_name}",
    "topics": ["topic1", "topic2"],
    "sentiment": "positive/neutral/negative/mixed",
    "key_points": ["point1", "point2"]
}}

If {person_name} is not mentioned or involved, return empty strings.
"""
            
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are extracting person-specific conversations for memory assistance."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            conversation_text = analysis.get('conversation_text', '')
            
            # Skip if no relevant conversation
            if not conversation_text or len(conversation_text) < 10:
                print(f"  ⏭️  No relevant conversation for {person_name}")
                return None
            
            summary = analysis.get('summary', '')
            
            # Generate embedding for the conversation
            embedding = self._generate_embedding(f"{person_name}: {conversation_text}")
            
            # Store in database
            insert_data = {
                'person_name': person_name,
                'conversation_text': conversation_text,
                'summary': summary,
                'topics': analysis.get('topics', []),
                'sentiment': analysis.get('sentiment', 'neutral'),
                'audio_chunk_id': audio_chunk_id,
                'conversation_date': conversation_date
            }
            
            if embedding:
                insert_data['embedding'] = embedding
            
            result = self.supabase.table('person_memories').insert(insert_data).execute()
            
            print(f"  ✅ Stored memory for {person_name}")
            print(f"     Summary: {summary[:80]}...")
            
            return {
                'person_name': person_name,
                'summary': summary,
                'topics': analysis.get('topics', []),
                'sentiment': analysis.get('sentiment', 'neutral')
            }
            
        except Exception as e:
            print(f"  ❌ Error processing {person_name}: {e}")
            return None
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = self.openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def get_person_memories(self, person_name: str, days_back: int = 7) -> List[Dict]:
        """Get all memories for a specific person"""
        try:
            result = self.supabase.rpc(
                'get_person_conversations',
                {
                    'p_person_name': person_name,
                    'days_back': days_back
                }
            ).execute()
            
            return result.data
        except Exception as e:
            print(f"Error getting person memories: {e}")
            return []
    
    def query_person_memory(self, person_name: str, query: str) -> str:
        """Query memories about a specific person"""
        
        # Generate embedding for query
        query_embedding = self._generate_embedding(query)
        
        if not query_embedding:
            # Fallback to recent memories
            memories = self.get_person_memories(person_name, days_back=7)
        else:
            # Semantic search
            try:
                result = self.supabase.rpc(
                    'search_person_conversations',
                    {
                        'p_person_name': person_name,
                        'query_embedding': query_embedding,
                        'match_threshold': 0.7,
                        'match_count': 5
                    }
                ).execute()
                
                memories = result.data
            except Exception as e:
                print(f"Error in semantic search: {e}")
                memories = self.get_person_memories(person_name, days_back=7)
        
        if not memories:
            return f"I don't have any recent memories about conversations with {person_name}."
        
        # Build context
        context = f"Memories about {person_name}:\n\n"
        for memory in memories[:5]:
            context += f"- {memory.get('summary', '')}\n"
            context += f"  Topics: {', '.join(memory.get('topics', []))}\n"
            context += f"  Date: {memory.get('conversation_date', '')}\n\n"
        
        # Generate answer
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful memory assistant. Use the provided memories to answer questions about conversations with specific people."
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}"
                    }
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return f"Here's what I remember about {person_name}:\n{context}"


if __name__ == "__main__":
    # Example usage
    builder = PersonGraphBuilder()
    
    # Get all audio chunks
    result = builder.supabase.table('audio_chunks').select('id, filename').execute()
    
    print(f"Found {len(result.data)} audio chunks")
    print("\nProcessing first chunk as example...")
    
    if result.data:
        chunk_id = result.data[0]['id']
        result = builder.build_person_memory(chunk_id)
        print(json.dumps(result, indent=2))
