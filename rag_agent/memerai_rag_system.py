#!/usr/bin/env python3
"""
MemerAI RAG System
Exactly as described: Camera → Memory Store → Smart Brain

Flow:
1. Create memory units from conversations
2. Convert to embeddings (vectors)
3. Store in vector DB
4. Next day: Show image → Ask question → RAG retrieves & explains
"""

import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
from family_context import FAMILY_CONTEXT, get_person_context

load_dotenv()


class MemerAIRAG:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
    
    # ============================================================
    # STEP 1: CREATE MEMORY UNITS
    # ============================================================
    
    def create_memory_unit(self, conversation_data: dict) -> dict:
        """
        Create a memory unit from combined conversation
        
        Memory Unit Structure:
        {
            "id": "mem_001",
            "time": "2025-11-08 10:05",
            "people": ["Rae (sister)"],
            "event": "Birthday cake in living room",
            "text": "Rae came in the morning, brought chocolate cake...",
            "image_path": "images/bday_morning_rae.jpg"
        }
        """
        
        person = conversation_data['person_name']
        transcription = conversation_data['full_transcription']
        start_time = conversation_data['start_time']
        
        # Use LLM to create structured memory
        prompt = f"""Create a memory unit from this conversation.

Person: {person}
Conversation: {transcription}

Extract:
- A short event description (e.g., "Birthday cake in living room")
- A simple summary sentence (e.g., "Rae came with chocolate cake for 72nd birthday")

Return JSON:
{{
    "event": "short event description",
    "summary": "one simple sentence about what happened"
}}
"""
        
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract key information from conversations."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Create memory unit
        memory_unit = {
            "person": person,
            "time": start_time,
            "event": result.get('event', ''),
            "text": result.get('summary', ''),
            "full_conversation": transcription,
            "duration_seconds": conversation_data['duration_seconds']
        }
        
        return memory_unit
    
    # ============================================================
    # STEP 2: CONVERT TO EMBEDDINGS
    # ============================================================
    
    def create_embedding(self, text: str) -> list:
        """Convert text to vector embedding"""
        try:
            response = self.openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return None
    
    # ============================================================
    # STEP 3: STORE IN MEMORY STORE
    # ============================================================
    
    def store_memory(self, memory_unit: dict):
        """Store memory unit with embedding in database"""
        
        # Create searchable text (for embedding)
        searchable_text = f"{memory_unit['person']}: {memory_unit['event']}. {memory_unit['text']}"
        
        # Generate embedding
        embedding = self.create_embedding(searchable_text)
        
        if not embedding:
            print("⚠️  Failed to create embedding")
            return
        
        # Store in database
        data = {
            'person': memory_unit['person'],
            'event': memory_unit['event'],
            'summary_text': memory_unit['text'],
            'full_conversation': memory_unit['full_conversation'],
            'memory_time': memory_unit['time'],
            'duration_seconds': memory_unit['duration_seconds'],
            'embedding': embedding,
            'searchable_text': searchable_text
        }
        
        self.supabase.table('memory_store').insert(data).execute()
        print(f"✅ Stored memory: {memory_unit['event']}")
    
    def build_memory_store_from_conversations(self):
        """Build complete memory store from combined conversations"""
        
        print("\n" + "="*60)
        print("BUILDING MEMORY STORE")
        print("="*60)
        
        # Get all combined conversations
        result = self.supabase.table('combined_conversations').select('*').execute()
        
        if not result.data:
            print("⚠️  No combined conversations found")
            return
        
        print(f"\nFound {len(result.data)} conversations")
        
        for conv in result.data:
            print(f"\nProcessing: {conv['person_name']}")
            
            # Create memory unit
            memory_unit = self.create_memory_unit(conv)
            
            # Store with embedding
            self.store_memory(memory_unit)
        
        print("\n✅ Memory store built successfully!")
    
    # ============================================================
    # STEP 4: RECALL / RETRIEVAL (RAG)
    # ============================================================
    
    def recall(self, query: str, top_k: int = 3) -> list:
        """
        RAG Retrieval: Find relevant memories
        
        Example queries:
        - "Who visited me yesterday?"
        - "What did we do with the cake?"
        - "Tell me about Rae"
        """
        
        # Convert query to embedding
        query_embedding = self.create_embedding(query)
        
        if not query_embedding:
            return []
        
        # Search vector DB using RPC function
        try:
            result = self.supabase.rpc(
                'search_memories',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.5,
                    'match_count': top_k
                }
            ).execute()
            
            return result.data
        except Exception as e:
            print(f"Error searching memories: {e}")
            # Fallback: get recent memories
            result = self.supabase.table('memory_store') \
                .select('*') \
                .order('memory_time', desc=True) \
                .limit(top_k) \
                .execute()
            return result.data
    
    def generate_response(self, query: str, memories: list) -> str:
        """
        Generate response using retrieved memories
        This is the "Smart Brain" part
        """
        
        # Build context from memories
        context = "Here are the relevant memories:\n\n"
        for i, mem in enumerate(memories, 1):
            context += f"{i}. {mem['person']}: {mem['summary_text']}\n"
            context += f"   Event: {mem['event']}\n\n"
        
        # Generate response
        prompt = f"""You are MemerAI, a gentle memory assistant for Alzheimer's patients.

{context}

Patient's question: {query}

Answer in ONE simple sentence using ONLY the memories above.
Be warm, clear, and reassuring.
"""
        
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a gentle memory assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    def ask(self, query: str) -> dict:
        """
        Complete RAG pipeline: Query → Retrieve → Generate
        
        This is the main API endpoint
        """
        
        print(f"\n🔍 Query: {query}")
        
        # Step 1: Retrieve relevant memories
        memories = self.recall(query, top_k=3)
        
        if not memories:
            return {
                'answer': "I don't have any memories about that yet.",
                'memories': []
            }
        
        print(f"📚 Found {len(memories)} relevant memories")
        
        # Step 2: Generate response
        answer = self.generate_response(query, memories)
        
        return {
            'answer': answer,
            'memories': memories
        }
    
    # ============================================================
    # STEP 5: DAILY CHECK (PROACTIVE MODE)
    # ============================================================
    
    def daily_memory_check(self, days_back: int = 1, patient_name: str = "John") -> dict:
        """
        Morning check: Show yesterday's memories
        Generate lovely, personalized questions
        
        Returns:
        {
            'greeting': 'Good morning John!',
            'memory': {...},
            'question': 'Do you remember it was your birthday yesterday?'
        }
        """
        
        # Get memories from yesterday
        target_day = datetime.now() - timedelta(days=days_back)
        start_time = target_day.replace(hour=0, minute=0, second=0)
        end_time = target_day.replace(hour=23, minute=59, second=59)
        
        result = self.supabase.table('memory_store') \
            .select('*') \
            .gte('memory_time', start_time.isoformat()) \
            .lte('memory_time', end_time.isoformat()) \
            .execute()
        
        if not result.data:
            return {
                'greeting': f'Good morning {patient_name}!',
                'has_memories': False,
                'message': 'No memories from yesterday.'
            }
        
        # Get ALL memories and create a comprehensive question
        all_memories = result.data
        
        # Pick first memory for initial question
        memory = all_memories[0]
        
        # Use GPT to generate a lovely, personalized question
        question = self._generate_lovely_question(memory, patient_name)
        
        return {
            'greeting': f'Good morning {patient_name}! 🌅',
            'has_memories': True,
            'memory': memory,
            'all_memories': all_memories,  # Store all memories for follow-up questions
            'question': question,
            'hint_available': True
        }
    
    def _generate_lovely_question(self, memory: dict, patient_name: str) -> str:
        """Generate a warm, personalized FIRST question about the memory"""
        
        person = memory['person']
        event = memory['event']
        summary = memory['summary_text']
        
        prompt = f"""You are starting a conversation with {patient_name} (Alzheimer's patient) about yesterday.

Memory details:
- Person involved: {person} (this is {patient_name}'s family member)
- Event: {event}
- What happened: {summary}

Generate the FIRST question to start naturally:
1. Start by asking about the SPECIAL DAY (like "Do you remember what day it was yesterday?")
2. Or ask if it was a special occasion
3. Be warm and gentle
4. Don't mention names yet - let them recall

Examples:
- "Do you remember what special day it was yesterday?"
- "Can you recall if yesterday was a special occasion for you?"
- "Do you remember what you celebrated yesterday?"

Return ONLY the question, nothing else.
"""
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You generate warm, simple questions for Alzheimer's patients."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content.strip()
        except:
            return f"Do you remember what happened with {person} yesterday?"
    
    def help_remember(self, memory_id: str, patient_name: str = "John", hint_level: int = 1) -> str:
        """
        When patient clicks "Help me" button
        Gives progressive hints, not full answer
        
        hint_level 1: Just relationship hint
        hint_level 2: Add event hint
        hint_level 3: Full gentle explanation
        """
        
        # Get memory
        result = self.supabase.table('memory_store') \
            .select('*') \
            .eq('id', memory_id) \
            .execute()
        
        if not result.data:
            return "I don't have that memory."
        
        memory = result.data[0]
        person = memory['person']
        
        # Determine relationship
        relationship_map = {
            'rae': 'your sister',
            'harry': 'your brother'
        }
        relationship = relationship_map.get(person.lower(), 'someone special')
        
        if hint_level == 1:
            # First hint: Just the relationship
            return f"💡 Hint: This person is {relationship}."
        
        elif hint_level == 2:
            # Second hint: Relationship + event type
            event_hint = memory['event'].split()[0:3]  # First few words
            return f"💡 Hint: This is {relationship}, {person.title()}. Think about {' '.join(event_hint)}..."
        
        else:
            # Full explanation (only after 2 hints)
            prompt = f"""You are helping {patient_name} remember. Give a SHORT, warm explanation (2-3 sentences max).

Memory:
- Person: {person} (this is {relationship})
- Event: {memory['event']}

Be brief, warm, and encouraging. Example: "This is your sister Rae! Yesterday was your birthday, and she brought you chocolate cake. She loves celebrating with you!"

Generate SHORT explanation:
"""
            
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You give SHORT, warm hints for Alzheimer's patients. Maximum 2-3 sentences."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
    
    def evaluate_answer(self, patient_answer: str, memory: dict, question: str, all_memories: list = None) -> dict:
        """
        Sophisticated RAG-based answer evaluation
        Uses family context to intelligently assess responses
        """
        
        person = memory['person']
        event = memory['event']
        summary = memory['summary_text']
        
        # Get rich family context
        person_info = get_person_context(person)
        
        # Build context about ALL people who were there
        all_people_context = ""
        if all_memories and len(all_memories) > 1:
            all_people_context = "\n\nOTHER PEOPLE WHO WERE ALSO THERE:\n"
            for mem in all_memories:
                if mem['person'] != person:
                    other_person_info = get_person_context(mem['person'])
                    all_people_context += f"- {mem['person'].title()} ({other_person_info['relation']}): {mem['summary_text']}\n"
        
        prompt = f"""You are evaluating John Thompson's (72, Alzheimer's patient) answer about a memory.

FAMILY CONTEXT:
{FAMILY_CONTEXT}

MEMORY BEING TESTED:
- Person: {person} ({person_info['relation']})
- Event: {event}
- What happened: {summary}
{all_people_context}

QUESTION ASKED: "{question}"
JOHN'S ANSWER: "{patient_answer}"

Evaluate if John's answer shows memory:
1. Did he identify the correct person or event?
2. If he said the WRONG person (e.g., "Harry" when it was Rae), gently correct him with a clue about the RIGHT person
3. Be encouraging even if wrong

Return JSON:
{{
    "correct": true/false,
    "confidence": 0.0-1.0,
    "response": "Warm, encouraging response - ONLY respond to their answer, don't add extra info",
    "next_question": "ONE single follow-up question",
    "correction_hint": "Gentle hint about the right person if wrong"
}}

Examples:
- If John says "Harry" but it was Rae: "Not quite, John. Think about your sister who loves decorating and has those three little dogs. Do you remember now?"
- If John says "no" or "I don't know": "That's okay! Let me give you a hint..."
- If John is correct about birthday: "Yes! That's right! It was your birthday." (STOP HERE, don't mention cake yet)

CRITICAL RULES:
1. In "response": ONLY acknowledge their answer. Don't add extra information.
2. In "next_question": Ask ONE single question only
3. Don't combine information - separate each piece into its own question

NATURAL PROGRESSION (ONE STEP AT A TIME):
1. First: Ask about the special day → "What special occasion was yesterday?"
2. Second: Ask who came to visit → "Do you remember who came to visit you?"
3. Third: Ask what they brought → "Do you remember what Rae brought?"
4. Fourth: Ask about the item → "What kind of cake was it?"
5. Fifth: Ask who else came → "Do you remember who else came to celebrate?"

NEVER say things like "Rae brought you that delicious chocolate cake" in the response - that's giving away future answers!
Keep response SHORT - just acknowledge their current answer.
Ask next_question separately.
"""
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sophisticated memory evaluation system for Alzheimer's patients. Use family context to provide intelligent, warm responses."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            return {
                'correct': False,
                'confidence': 0.0,
                'response': "Let me help you remember...",
                'next_question': None,
                'correction_hint': None
            }


if __name__ == "__main__":
    rag = MemerAIRAG()
    
    print("="*60)
    print("MEMERAI RAG SYSTEM")
    print("="*60)
    
    # Example: Build memory store
    print("\n1. Building memory store from conversations...")
    # rag.build_memory_store_from_conversations()
    
    # Example: Daily check
    print("\n2. Daily memory check...")
    check = rag.daily_memory_check(days_back=0)
    print(json.dumps(check, indent=2, default=str))
    
    # Example: Ask question
    print("\n3. Ask question...")
    result = rag.ask("Who visited me yesterday?")
    print(f"Answer: {result['answer']}")
