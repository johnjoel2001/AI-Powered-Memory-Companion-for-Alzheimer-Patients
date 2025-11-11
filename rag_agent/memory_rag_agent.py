#!/usr/bin/env python3
"""
Memory RAG Agent - Retrieval Augmented Generation for Alzheimer's Memory Assistant
Processes audio transcriptions and images to build a knowledge graph
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MemoryRAGAgent:
    def __init__(
        self,
        supabase_url: str = None,
        supabase_key: str = None,
        openai_api_key: str = None
    ):
        """Initialize the Memory RAG Agent"""
        self.supabase: Client = create_client(
            supabase_url or os.getenv("SUPABASE_URL"),
            supabase_key or os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"  # OpenAI embedding model
        
    def process_audio_chunk(self, audio_chunk_id: str) -> Dict:
        """
        Process an audio chunk to extract:
        - Summary
        - Sentiment
        - Topics
        - Key points
        - Memory events
        """
        # Get audio chunk with transcription
        result = self.supabase.table('audio_chunks').select('*').eq('id', audio_chunk_id).execute()
        
        if not result.data:
            return {"error": "Audio chunk not found"}
        
        audio_chunk = result.data[0]
        transcription = audio_chunk.get('transcription', '')
        
        if not transcription:
            return {"error": "No transcription available"}
        
        # Get associated images (detected persons)
        images_result = self.supabase.table('images').select('*').eq('audio_chunk_id', audio_chunk_id).execute()
        detected_persons = []
        for img in images_result.data:
            if img.get('detected_persons'):
                detected_persons.extend(img['detected_persons'])
        detected_persons = list(set(detected_persons))  # Remove duplicates
        
        # Use LLM to analyze the conversation
        analysis = self._analyze_conversation(transcription, detected_persons)
        
        # Store in knowledge graph
        self._store_conversation_summary(audio_chunk_id, analysis)
        self._store_person_interactions(audio_chunk_id, analysis, detected_persons)
        self._store_memory_events(audio_chunk_id, analysis, audio_chunk)
        
        return analysis
    
    def _analyze_conversation(self, transcription: str, detected_persons: List[str]) -> Dict:
        """Use LLM to analyze conversation and extract insights"""
        
        prompt = f"""Analyze this conversation transcription and extract key information.

Detected persons present: {', '.join(detected_persons) if detected_persons else 'Unknown'}

Transcription:
{transcription}

Please provide a JSON response with the following structure:
{{
    "summary": "Brief 2-3 sentence summary of the conversation",
    "sentiment": "positive/neutral/negative/mixed",
    "topics": ["topic1", "topic2", ...],
    "key_points": ["point1", "point2", ...],
    "memory_events": [
        {{
            "event_type": "meal/medication/visitor/activity/other",
            "event_description": "What happened",
            "participants": ["person1", "person2"],
            "importance_score": 0.0-1.0
        }}
    ],
    "person_interactions": [
        {{
            "person_name": "Name",
            "interaction_type": "conversation/visit/activity",
            "context": "What they discussed or did"
        }}
    ]
}}

Focus on:
- Important events (meals, medications, visitors, activities)
- Emotional tone and sentiment
- Key topics discussed
- Who was involved and what they did
"""
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI assistant helping analyze conversations for Alzheimer's patients. Extract key information to help them remember important events and interactions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            print(f"Error analyzing conversation: {e}")
            return {
                "summary": transcription[:200] + "...",
                "sentiment": "neutral",
                "topics": [],
                "key_points": [],
                "memory_events": [],
                "person_interactions": []
            }
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def _store_conversation_summary(self, audio_chunk_id: str, analysis: Dict):
        """Store conversation summary in database with embedding"""
        try:
            summary = analysis.get('summary', '')
            
            # Generate embedding for the summary
            embedding = self._generate_embedding(summary)
            
            insert_data = {
                'audio_chunk_id': audio_chunk_id,
                'summary': summary,
                'sentiment': analysis.get('sentiment', 'neutral'),
                'topics': analysis.get('topics', []),
                'key_points': analysis.get('key_points', [])
            }
            
            # Add embedding if generated successfully
            if embedding:
                insert_data['embedding'] = embedding
            
            self.supabase.table('conversation_summaries').insert(insert_data).execute()
        except Exception as e:
            print(f"Error storing conversation summary: {e}")
    
    def _store_person_interactions(self, audio_chunk_id: str, analysis: Dict, detected_persons: List[str]):
        """Store person interactions in database"""
        try:
            interactions = analysis.get('person_interactions', [])
            for interaction in interactions:
                self.supabase.table('person_interactions').insert({
                    'audio_chunk_id': audio_chunk_id,
                    'person_name': interaction.get('person_name', 'Unknown'),
                    'interaction_type': interaction.get('interaction_type', 'conversation'),
                    'context': interaction.get('context', '')
                }).execute()
        except Exception as e:
            print(f"Error storing person interactions: {e}")
    
    def _store_memory_events(self, audio_chunk_id: str, analysis: Dict, audio_chunk: Dict):
        """Store memory events in database with embeddings"""
        try:
            events = analysis.get('memory_events', [])
            for event in events:
                # Use audio chunk end_time as event time
                event_time = audio_chunk.get('end_time', datetime.now().isoformat())
                event_description = event.get('event_description', '')
                
                # Generate embedding for the event description
                embedding = self._generate_embedding(event_description)
                
                insert_data = {
                    'audio_chunk_id': audio_chunk_id,
                    'event_type': event.get('event_type', 'other'),
                    'event_description': event_description,
                    'participants': event.get('participants', []),
                    'event_time': event_time,
                    'importance_score': event.get('importance_score', 0.5)
                }
                
                # Add embedding if generated successfully
                if embedding:
                    insert_data['embedding'] = embedding
                
                self.supabase.table('memory_events').insert(insert_data).execute()
        except Exception as e:
            print(f"Error storing memory events: {e}")
    
    def query_memories(self, query: str, days_back: int = 7) -> str:
        """
        Query memories using natural language with semantic search
        Examples:
        - "What did I do yesterday?"
        - "Who visited me this week?"
        - "Did I take my medication today?"
        """
        # Generate embedding for the query
        query_embedding = self._generate_embedding(query)
        
        # Get relevant time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        # Use semantic search to find similar conversations and events
        if query_embedding:
            summaries = self._semantic_search_summaries(query_embedding, start_time, end_time)
            events = self._semantic_search_events(query_embedding, start_time, end_time)
        else:
            # Fallback to time-based retrieval if embedding fails
            summaries = self._get_recent_summaries(start_time, end_time)
            events = self._get_recent_events(start_time, end_time)
        
        # Get person interactions (no embedding search for these)
        interactions = self._get_recent_interactions(start_time, end_time)
        
        # Build context for LLM
        context = self._build_context(summaries, events, interactions)
        
        # Use LLM to answer the query
        answer = self._generate_answer(query, context)
        
        return answer
    
    def _semantic_search_summaries(self, query_embedding: List[float], start_time: datetime, end_time: datetime, limit: int = 10) -> List[Dict]:
        """Search for similar conversation summaries using vector similarity"""
        try:
            # Call the Supabase function for semantic search
            result = self.supabase.rpc(
                'search_similar_conversations',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.7,
                    'match_count': limit
                }
            ).execute()
            
            # Filter by time range
            filtered = [
                item for item in result.data
                if start_time.isoformat() <= item.get('created_at', '') <= end_time.isoformat()
            ]
            
            return filtered
        except Exception as e:
            print(f"Error in semantic search for summaries: {e}")
            return self._get_recent_summaries(start_time, end_time)
    
    def _semantic_search_events(self, query_embedding: List[float], start_time: datetime, end_time: datetime, limit: int = 10) -> List[Dict]:
        """Search for similar memory events using vector similarity"""
        try:
            # Call the Supabase function for semantic search
            result = self.supabase.rpc(
                'search_similar_events',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.7,
                    'match_count': limit
                }
            ).execute()
            
            # Filter by time range
            filtered = [
                item for item in result.data
                if start_time.isoformat() <= item.get('event_time', '') <= end_time.isoformat()
            ]
            
            return filtered
        except Exception as e:
            print(f"Error in semantic search for events: {e}")
            return self._get_recent_events(start_time, end_time)
    
    def _get_recent_summaries(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get conversation summaries within time range"""
        try:
            result = self.supabase.table('conversation_summaries') \
                .select('*, audio_chunks(start_time, end_time)') \
                .gte('created_at', start_time.isoformat()) \
                .lte('created_at', end_time.isoformat()) \
                .order('created_at', desc=True) \
                .execute()
            return result.data
        except Exception as e:
            print(f"Error getting summaries: {e}")
            return []
    
    def _get_recent_events(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get memory events within time range"""
        try:
            result = self.supabase.table('memory_events') \
                .select('*') \
                .gte('event_time', start_time.isoformat()) \
                .lte('event_time', end_time.isoformat()) \
                .order('importance_score', desc=True) \
                .execute()
            return result.data
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    def _get_recent_interactions(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get person interactions within time range"""
        try:
            result = self.supabase.table('person_interactions') \
                .select('*') \
                .gte('created_at', start_time.isoformat()) \
                .lte('created_at', end_time.isoformat()) \
                .order('created_at', desc=True) \
                .execute()
            return result.data
        except Exception as e:
            print(f"Error getting interactions: {e}")
            return []
    
    def _build_context(self, summaries: List[Dict], events: List[Dict], interactions: List[Dict]) -> str:
        """Build context string from retrieved data"""
        context_parts = []
        
        if summaries:
            context_parts.append("## Recent Conversations:")
            for summary in summaries[:5]:  # Top 5
                context_parts.append(f"- {summary.get('summary', '')}")
                context_parts.append(f"  Topics: {', '.join(summary.get('topics', []))}")
                context_parts.append(f"  Sentiment: {summary.get('sentiment', 'neutral')}")
        
        if events:
            context_parts.append("\n## Important Events:")
            for event in events[:10]:  # Top 10
                context_parts.append(f"- {event.get('event_type', 'event')}: {event.get('event_description', '')}")
                if event.get('participants'):
                    context_parts.append(f"  With: {', '.join(event.get('participants', []))}")
        
        if interactions:
            context_parts.append("\n## Person Interactions:")
            for interaction in interactions[:10]:  # Top 10
                context_parts.append(f"- {interaction.get('person_name', 'Someone')}: {interaction.get('context', '')}")
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM with retrieved context"""
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful memory assistant for an Alzheimer's patient. Use the provided context to answer their questions warmly and clearly. If you don't have enough information, say so gently."
                    },
                    {
                        "role": "user",
                        "content": f"Context from recent memories:\n{context}\n\nQuestion: {query}"
                    }
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return "I'm having trouble accessing your memories right now. Please try again."


if __name__ == "__main__":
    # Example usage
    agent = MemoryRAGAgent()
    
    # Process a specific audio chunk
    # audio_chunk_id = "your-audio-chunk-id"
    # result = agent.process_audio_chunk(audio_chunk_id)
    # print(json.dumps(result, indent=2))
    
    # Query memories
    answer = agent.query_memories("What did I do yesterday?")
    print(answer)
