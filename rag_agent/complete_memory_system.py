#!/usr/bin/env python3
"""
COMPLETE Intelligent Memory System for Alzheimer's Patients
- Reads all conversations from Supabase
- Links detected persons to conversations
- Asks progressive questions with hints
- Tracks memory performance
"""

import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


class CompleteMemorySystem:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_state = {}
        self.memory_score = {'correct': 0, 'total': 0}
    
    def start_conversation(self, days_back: int = 0) -> dict:
        """
        Start intelligent conversation
        Gets ALL conversations from specified day
        """
        # Get target day's data
        target_day = datetime.now() - timedelta(days=days_back)
        start_time = target_day.replace(hour=0, minute=0, second=0)
        end_time = target_day.replace(hour=23, minute=59, second=59)
        
        # Get ALL audio chunks
        audio_data = self.supabase.table('audio_chunks') \
            .select('*') \
            .gte('end_time', start_time.isoformat()) \
            .lte('end_time', end_time.isoformat()) \
            .execute()
        
        if not audio_data.data:
            return {
                'question': "Hello! How are you feeling today?",
                'type': 'greeting',
                'has_memories': False
            }
        
        # Get ALL images
        images_data = self.supabase.table('images').select('*').execute()
        
        # Build complete memory map: person -> conversations
        person_conversations = {}
        
        for audio in audio_data.data:
            audio_id = audio['id']
            transcription = audio.get('transcription', '')
            
            if not transcription:
                continue
            
            # Find persons in this conversation
            persons = []
            for img in images_data.data:
                if img.get('audio_chunk_id') == audio_id:
                    detected = img.get('detected_persons', [])
                    persons.extend(detected)
            
            persons = list(set(persons))  # Remove duplicates
            
            # Store conversation for each person
            for person in persons:
                if person not in person_conversations:
                    person_conversations[person] = []
                
                person_conversations[person].append({
                    'transcription': transcription,
                    'audio_id': audio_id,
                    'time': audio.get('end_time', '')
                })
        
        if not person_conversations:
            return {
                'question': "Hello! How are you feeling today?",
                'type': 'greeting',
                'has_memories': False
            }
        
        # Store in state
        self.conversation_state = {
            'person_conversations': person_conversations,
            'all_persons': list(person_conversations.keys()),
            'current_person': None,
            'current_question_level': 1,
            'hints_given': 0
        }
        
        # Ask first question
        all_persons = list(person_conversations.keys())
        
        return {
            'question': f"Hello! Do you remember who you spoke with recently?",
            'type': 'person_recall',
            'expected_persons': all_persons,
            'has_memories': True,
            'hint': f"There were {len(all_persons)} people"
        }
    
    def process_answer(self, user_answer: str, question_type: str) -> dict:
        """Process answer with intelligent hints and tracking"""
        
        if question_type == 'person_recall':
            return self._handle_person_recall(user_answer)
        elif question_type == 'event_recall':
            return self._handle_event_recall(user_answer)
        elif question_type == 'detail_recall':
            return self._handle_detail_recall(user_answer)
        else:
            return {'response': "That's nice!", 'next_question': None}
    
    def _handle_person_recall(self, user_answer: str) -> dict:
        """Handle: Who did you speak with?"""
        
        all_persons = self.conversation_state['all_persons']
        
        # Check if they mentioned any correct person
        mentioned_persons = []
        for person in all_persons:
            if person.lower() in user_answer.lower():
                mentioned_persons.append(person)
        
        if mentioned_persons:
            # CORRECT! They remembered
            person = mentioned_persons[0]
            self.conversation_state['current_person'] = person
            self.memory_score['correct'] += 1
            self.memory_score['total'] += 1
            
            # Get their conversations
            conversations = self.conversation_state['person_conversations'][person]
            
            # Extract what they talked about
            all_text = " ".join([c['transcription'] for c in conversations])
            topics = self._extract_topics(all_text, person)
            
            self.conversation_state['current_topics'] = topics
            
            return {
                'response': f"Yes! You spoke with {person}. That's wonderful! 🎉",
                'next_question': f"Do you remember what you talked about with {person}?",
                'type': 'event_recall',
                'memory_score': self._get_score(),
                'hint': f"Think about what you did together..."
            }
        else:
            # WRONG or don't remember
            self.memory_score['total'] += 1
            hints_given = self.conversation_state.get('hints_given', 0)
            
            if hints_given == 0:
                # Give first hint
                self.conversation_state['hints_given'] = 1
                return {
                    'response': "Take your time. Let me give you a hint...",
                    'next_question': f"You spoke with someone whose name starts with '{all_persons[0][0]}'. Can you remember?",
                    'type': 'person_recall',
                    'is_hint': True,
                    'memory_score': self._get_score()
                }
            else:
                # Give answer and continue
                person = all_persons[0]
                self.conversation_state['current_person'] = person
                
                conversations = self.conversation_state['person_conversations'][person]
                all_text = " ".join([c['transcription'] for c in conversations])
                topics = self._extract_topics(all_text, person)
                self.conversation_state['current_topics'] = topics
                
                return {
                    'response': f"That's okay! You spoke with {person}. Let me help you remember more.",
                    'next_question': f"Do you remember what you talked about with {person}?",
                    'type': 'event_recall',
                    'memory_score': self._get_score(),
                    'hint': f"Think about what you did together..."
                }
    
    def _handle_event_recall(self, user_answer: str) -> dict:
        """Handle: What did you talk about?"""
        
        person = self.conversation_state['current_person']
        topics = self.conversation_state.get('current_topics', [])
        
        if not topics:
            return {
                'response': "Great effort! You're doing well! 🌟",
                'next_question': None,
                'type': 'end',
                'memory_score': self._get_score()
            }
        
        # Check if they mentioned any topic
        mentioned_topics = []
        for topic in topics:
            if any(word.lower() in user_answer.lower() for word in topic.split()):
                mentioned_topics.append(topic)
        
        if mentioned_topics:
            # CORRECT!
            self.memory_score['correct'] += 1
            self.memory_score['total'] += 1
            
            # Ask detail question
            conversations = self.conversation_state['person_conversations'][person]
            all_text = " ".join([c['transcription'] for c in conversations])
            
            detail_q = self._generate_detail_question(all_text, person, mentioned_topics[0])
            
            if detail_q:
                self.conversation_state['current_detail'] = detail_q['answer']
                return {
                    'response': f"Yes! That's right! You talked about {mentioned_topics[0]}. Excellent! 🎉",
                    'next_question': detail_q['question'],
                    'type': 'detail_recall',
                    'memory_score': self._get_score()
                }
        
        # Wrong or don't remember
        self.memory_score['total'] += 1
        hints_given = self.conversation_state.get('event_hints_given', 0)
        
        if hints_given == 0:
            # Give hint
            self.conversation_state['event_hints_given'] = 1
            return {
                'response': "Let me help you remember...",
                'next_question': f"You talked about {topics[0]}. Does that ring a bell?",
                'type': 'event_recall',
                'is_hint': True,
                'memory_score': self._get_score()
            }
        
        return {
            'response': f"That's okay! You talked about {', '.join(topics)}. These are wonderful memories! 💙",
            'next_question': None,
            'type': 'end',
            'memory_score': self._get_score()
        }
    
    def _handle_detail_recall(self, user_answer: str) -> dict:
        """Handle: Specific detail question"""
        
        expected_detail = self.conversation_state.get('current_detail', '')
        
        # Simple check if they got it
        if any(word.lower() in user_answer.lower() for word in expected_detail.split()):
            self.memory_score['correct'] += 1
            self.memory_score['total'] += 1
            
            return {
                'response': f"Excellent! That's right! You have an amazing memory! 🎉🌟",
                'next_question': None,
                'type': 'end',
                'memory_score': self._get_score(),
                'final_message': self._get_final_message()
            }
        else:
            self.memory_score['total'] += 1
            
            return {
                'response': f"That's okay! It was {expected_detail}. You did great today! 💙",
                'next_question': None,
                'type': 'end',
                'memory_score': self._get_score(),
                'final_message': self._get_final_message()
            }
    
    def _extract_topics(self, transcription: str, person: str) -> list:
        """Extract main topics from conversation"""
        try:
            prompt = f"""Extract 2-3 main topics/events from this conversation with {person}.
Be specific: "cut a birthday cake", "talked about healthcare", "discussed Obama", etc.

Conversation:
{transcription[:500]}

Return JSON: {{"topics": ["topic1", "topic2"]}}
"""
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract conversation topics."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('topics', [])
        except:
            return []
    
    def _generate_detail_question(self, transcription: str, person: str, main_topic: str) -> dict:
        """Generate specific detail question"""
        try:
            prompt = f"""Create ONE specific detail question about this conversation.
Main topic: {main_topic}

Conversation:
{transcription[:500]}

Ask about: flavor, color, time, what they said, etc.
Return JSON: {{"question": "Do you remember...", "answer": "short answer"}}
"""
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Generate detail questions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return None
    
    def _get_score(self) -> dict:
        """Get current memory score"""
        total = self.memory_score['total']
        correct = self.memory_score['correct']
        percentage = (correct / total * 100) if total > 0 else 0
        
        return {
            'correct': correct,
            'total': total,
            'percentage': round(percentage, 1)
        }
    
    def _get_final_message(self) -> str:
        """Get encouraging final message based on score"""
        score = self._get_score()
        percentage = score['percentage']
        
        if percentage >= 80:
            return "🌟 Outstanding! Your memory is working wonderfully today!"
        elif percentage >= 60:
            return "💙 Great job! You're remembering so well!"
        elif percentage >= 40:
            return "🌈 Good effort! Every day we're helping your memory get stronger!"
        else:
            return "💙 Thank you for trying! We're here to help you remember. You're doing great!"


if __name__ == "__main__":
    system = CompleteMemorySystem()
    
    print("="*60)
    print("COMPLETE MEMORY SYSTEM TEST")
    print("="*60)
    
    # Start
    result = system.start_conversation(days_back=0)
    print(f"\nUI: {result['question']}")
    print(f"Expected: {result.get('expected_persons', [])}")
