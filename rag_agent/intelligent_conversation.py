#!/usr/bin/env python3
"""
Intelligent Conversation System for Alzheimer's Patients
Proactively starts conversations and tests memory
"""

import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


class IntelligentConversation:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_state = {
            'current_question': None,
            'expected_answer': None,
            'context': None,
            'follow_up_questions': []
        }
    
    def start_conversation(self, days_back: int = 0) -> dict:
        """
        Start the conversation proactively
        Returns first question to ask the patient
        days_back: 0 = today, 1 = yesterday (default 0 for testing)
        """
        # Get data from specified day
        target_day = datetime.now() - timedelta(days=days_back)
        start_time = target_day.replace(hour=0, minute=0, second=0)
        end_time = target_day.replace(hour=23, minute=59, second=59)
        
        # Get audio chunks from yesterday
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
        
        # Get all persons from yesterday
        all_persons = set()
        conversations = []
        
        for audio in audio_data.data:
            audio_id = audio['id']
            transcription = audio.get('transcription', '')
            
            # Get images/persons for this audio
            images = self.supabase.table('images') \
                .select('*') \
                .eq('audio_chunk_id', audio_id) \
                .execute()
            
            persons_in_conversation = []
            for img in images.data:
                if img.get('detected_persons'):
                    persons_in_conversation.extend(img['detected_persons'])
            
            persons_in_conversation = list(set(persons_in_conversation))
            all_persons.update(persons_in_conversation)
            
            if transcription and persons_in_conversation:
                conversations.append({
                    'persons': persons_in_conversation,
                    'transcription': transcription,
                    'audio_id': audio_id
                })
        
        if not all_persons:
            return {
                'question': "Hello! How are you feeling today?",
                'type': 'greeting',
                'has_memories': False
            }
        
        # Store context for follow-up
        self.conversation_state['context'] = {
            'persons': list(all_persons),
            'conversations': conversations
        }
        
        # Generate first question: "Do you remember who you spoke with yesterday?"
        persons_list = ', '.join(list(all_persons))
        
        return {
            'question': "Hello! Do you remember who you spoke with yesterday?",
            'type': 'person_recall',
            'expected_persons': list(all_persons),
            'has_memories': True
        }
    
    def process_answer(self, user_answer: str, question_type: str) -> dict:
        """
        Process patient's answer and generate follow-up question
        """
        if question_type == 'person_recall':
            return self._handle_person_recall(user_answer)
        elif question_type == 'event_recall':
            return self._handle_event_recall(user_answer)
        elif question_type == 'detail_recall':
            return self._handle_detail_recall(user_answer)
        else:
            return {'response': "That's nice!", 'next_question': None}
    
    def _handle_person_recall(self, user_answer: str) -> dict:
        """Handle answer to 'who did you speak with yesterday?'"""
        
        expected_persons = self.conversation_state['context']['persons']
        conversations = self.conversation_state['context']['conversations']
        
        # Check if they mentioned any correct person
        mentioned_persons = []
        for person in expected_persons:
            if person.lower() in user_answer.lower():
                mentioned_persons.append(person)
        
        if mentioned_persons:
            # They remembered! Now ask about what they did
            person = mentioned_persons[0]
            
            # Find conversation with this person
            person_conversation = None
            for conv in conversations:
                if person in conv['persons']:
                    person_conversation = conv
                    break
            
            if person_conversation:
                # Use GPT to extract key events from the conversation
                events = self._extract_events(person_conversation['transcription'], person)
                
                if events:
                    event = events[0]  # Pick first event
                    
                    # Store for next answer
                    self.conversation_state['current_event'] = event
                    self.conversation_state['person'] = person
                    
                    return {
                        'response': f"Yes! You spoke with {person}. That's wonderful!",
                        'next_question': f"Do you remember what you did with {person}?",
                        'type': 'event_recall',
                        'hint': event  # For evaluation
                    }
        
        # They didn't remember or got it wrong
        person_names = ', '.join(expected_persons)
        return {
            'response': f"You spoke with {person_names} yesterday.",
            'next_question': f"Do you remember what you talked about with {expected_persons[0]}?",
            'type': 'event_recall',
            'hint': conversations[0]['transcription']
        }
    
    def _handle_event_recall(self, user_answer: str) -> dict:
        """Handle answer about what they did"""
        
        event = self.conversation_state.get('current_event', '')
        person = self.conversation_state.get('person', 'them')
        conversations = self.conversation_state['context']['conversations']
        
        # Use GPT to evaluate if they remembered correctly
        evaluation = self._evaluate_memory(user_answer, event)
        
        # Check if there are more events to ask about
        person_conversation = None
        for conv in conversations:
            if person in conv['persons']:
                person_conversation = conv
                break
        
        if evaluation['correct']:
            # Ask one more question about details
            if person_conversation:
                detail_question = self._generate_detail_question(
                    person_conversation['transcription'], 
                    person,
                    event
                )
                
                if detail_question:
                    self.conversation_state['current_detail'] = detail_question['answer']
                    return {
                        'response': f"Yes! That's right! {evaluation['feedback']}",
                        'next_question': detail_question['question'],
                        'type': 'detail_recall',
                        'success': True
                    }
            
            return {
                'response': f"Yes! That's right! {evaluation['feedback']} You have a wonderful memory!",
                'next_question': None,
                'type': 'end',
                'success': True
            }
        else:
            return {
                'response': f"Let me help you remember. {event}",
                'next_question': None,
                'type': 'end',
                'success': False
            }
    
    def _handle_detail_recall(self, user_answer: str) -> dict:
        """Handle answer about specific details"""
        
        expected_detail = self.conversation_state.get('current_detail', '')
        
        # Evaluate the detail
        evaluation = self._evaluate_memory(user_answer, expected_detail)
        
        if evaluation['correct']:
            return {
                'response': f"Excellent! {evaluation['feedback']} You're doing amazing! 🎉",
                'next_question': None,
                'type': 'end',
                'success': True
            }
        else:
            return {
                'response': f"That's okay! {expected_detail}. The important thing is we're helping you remember. 💙",
                'next_question': None,
                'type': 'end',
                'success': True
            }
    
    def _generate_detail_question(self, transcription: str, person: str, main_event: str) -> dict:
        """Generate a follow-up question about specific details"""
        
        try:
            prompt = f"""Based on this conversation, create ONE specific detail question.
Don't ask about "{main_event}" - we already asked that.
Ask about something else specific like: what flavor, what color, what time, what they said, etc.

Conversation with {person}:
{transcription}

Return JSON:
{{
    "question": "Do you remember what flavor the cake was?",
    "answer": "chocolate cake"
}}

Make it simple and specific.
"""
            
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Generate specific detail questions for memory testing."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error generating detail question: {e}")
            return None
    
    def _extract_events(self, transcription: str, person: str) -> list:
        """Extract key events from conversation using GPT"""
        
        try:
            prompt = f"""Extract key events/activities from this conversation with {person}.
Focus on specific actions like: "cut a cake", "had breakfast", "went for a walk", etc.

Conversation:
{transcription}

Return a JSON array of events (simple phrases):
["event1", "event2", ...]
"""
            
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract key events from conversations."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('events', [])
            
        except Exception as e:
            print(f"Error extracting events: {e}")
            return []
    
    def _evaluate_memory(self, user_answer: str, expected_event: str) -> dict:
        """Evaluate if patient remembered the event correctly"""
        
        try:
            prompt = f"""Evaluate if the patient remembered the event correctly.

Expected event: {expected_event}
Patient's answer: {user_answer}

Did they remember correctly? They don't need exact words, just the key idea.

Return JSON:
{{
    "correct": true/false,
    "feedback": "Encouraging message"
}}
"""
            
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are evaluating memory recall for Alzheimer's patients. Be encouraging."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error evaluating: {e}")
            return {'correct': False, 'feedback': 'Let me help you remember.'}


if __name__ == "__main__":
    # Test the conversation flow
    conv = IntelligentConversation()
    
    print("="*60)
    print("INTELLIGENT CONVERSATION TEST")
    print("="*60)
    
    # Step 1: Start conversation
    first_question = conv.start_conversation()
    print(f"\nUI: {first_question['question']}")
    
    if first_question['has_memories']:
        # Simulate patient answer
        print(f"\nPatient: Rae?")
        
        # Step 2: Process answer
        response = conv.process_answer("Rae", "person_recall")
        print(f"\nUI: {response['response']}")
        
        if response.get('next_question'):
            print(f"UI: {response['next_question']}")
            
            # Simulate patient answer
            print(f"\nPatient: We cut a cake?")
            
            # Step 3: Process event answer
            final_response = conv.process_answer("We cut a cake", "event_recall")
            print(f"\nUI: {final_response['response']}")
