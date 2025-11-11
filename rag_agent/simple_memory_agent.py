#!/usr/bin/env python3
"""
SIMPLE Memory Agent - No complex database, just works!
"""

import os
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

class SimpleMemoryAgent:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def ask_question(self, question: str) -> str:
        """Ask a question about memories - SIMPLE!"""
        
        # 1. Get all audio and images
        audio_data = self.supabase.table('audio_chunks').select('*').execute()
        images_data = self.supabase.table('images').select('*').execute()
        
        # 2. Build simple context
        context = "Here's what I remember:\n\n"
        
        for audio in audio_data.data:
            audio_id = audio['id']
            transcription = audio.get('transcription', '')
            
            # Find persons in this conversation
            persons = []
            for img in images_data.data:
                if img.get('audio_chunk_id') == audio_id:
                    persons.extend(img.get('detected_persons', []))
            
            persons = list(set(persons))  # Remove duplicates
            
            if transcription:
                context += f"Conversation with {', '.join(persons) if persons else 'someone'}:\n"
                context += f"{transcription}\n\n"
        
        # 3. Ask GPT-4
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful memory assistant. Answer questions based on the conversation history provided."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}"
                }
            ]
        )
        
        return response.choices[0].message.content
    
    def generate_quiz_question(self) -> dict:
        """Generate a simple quiz question"""
        
        # Get random conversation
        audio_data = self.supabase.table('audio_chunks').select('*').limit(1).execute()
        images_data = self.supabase.table('images').select('*').execute()
        
        if not audio_data.data:
            return {"question": None, "answer": None}
        
        audio = audio_data.data[0]
        transcription = audio.get('transcription', '')
        
        # Get persons
        persons = []
        for img in images_data.data:
            if img.get('audio_chunk_id') == audio['id']:
                persons.extend(img.get('detected_persons', []))
        
        persons = list(set(persons))
        
        # Ask GPT to create a quiz question
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Create a memory quiz question based on this conversation."
                },
                {
                    "role": "user",
                    "content": f"Conversation with {', '.join(persons)}:\n{transcription}\n\nCreate a question like 'Do you remember...?'"
                }
            ]
        )
        
        question = response.choices[0].message.content
        
        return {
            "question": question,
            "answer": transcription,
            "persons": persons
        }


if __name__ == "__main__":
    agent = SimpleMemoryAgent()
    
    # Test 1: Ask a question
    print("="*60)
    print("TEST 1: Ask a Question")
    print("="*60)
    answer = agent.ask_question("What did Rae and I talk about?")
    print(f"\nAnswer: {answer}\n")
    
    # Test 2: Get quiz question
    print("="*60)
    print("TEST 2: Quiz Question")
    print("="*60)
    quiz = agent.generate_quiz_question()
    print(f"\nQuestion: {quiz['question']}")
    print(f"Persons: {quiz['persons']}\n")
