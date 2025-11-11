#!/usr/bin/env python3
"""
Memory Quiz Agent - Proactively tests patient's memory
Asks questions like "Do you remember who visited you yesterday?"
"""

import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from memory_rag_agent import MemoryRAGAgent


class MemoryQuizAgent:
    def __init__(self):
        """Initialize the Memory Quiz Agent"""
        self.rag_agent = MemoryRAGAgent()
        
    def generate_memory_question(self, days_back: int = 1) -> Dict:
        """
        Generate a memory test question based on recent events
        Returns: {
            'question': 'Do you remember who visited you yesterday?',
            'expected_answer': 'Harry visited you',
            'context': {...}  # Full event details
        }
        """
        # Get recent events and conversations
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        # Get data from knowledge graph
        summaries = self.rag_agent._get_recent_summaries(start_time, end_time)
        events = self.rag_agent._get_recent_events(start_time, end_time)
        interactions = self.rag_agent._get_recent_interactions(start_time, end_time)
        
        if not summaries and not events and not interactions:
            return {
                'question': None,
                'expected_answer': None,
                'context': None,
                'error': 'No recent memories found'
            }
        
        # Choose what type of question to ask
        question_types = []
        if events:
            question_types.append('event')
        if interactions:
            question_types.append('person')
        if summaries:
            question_types.append('conversation')
        
        question_type = random.choice(question_types)
        
        if question_type == 'event':
            return self._generate_event_question(events, days_back)
        elif question_type == 'person':
            return self._generate_person_question(interactions, days_back)
        else:
            return self._generate_conversation_question(summaries, days_back)
    
    def _generate_event_question(self, events: List[Dict], days_back: int) -> Dict:
        """Generate question about a specific event"""
        # Pick a random event
        event = random.choice(events)
        event_type = event.get('event_type', 'event')
        description = event.get('event_description', '')
        participants = event.get('participants', [])
        
        # Generate question based on event type
        time_phrase = self._get_time_phrase(days_back)
        
        questions = []
        if event_type == 'meal':
            questions = [
                f"Do you remember what you ate {time_phrase}?",
                f"Can you recall what you had for your meal {time_phrase}?"
            ]
        elif event_type == 'medication':
            questions = [
                f"Do you remember if you took your medication {time_phrase}?",
                f"Can you recall taking your medicine {time_phrase}?"
            ]
        elif event_type == 'visitor':
            if participants:
                questions = [
                    f"Do you remember who visited you {time_phrase}?",
                    f"Can you recall who came to see you {time_phrase}?"
                ]
            else:
                questions = [
                    f"Do you remember having any visitors {time_phrase}?",
                ]
        elif event_type == 'activity':
            questions = [
                f"Do you remember what activity you did {time_phrase}?",
                f"Can you recall what you were doing {time_phrase}?"
            ]
        else:
            questions = [
                f"Do you remember what happened {time_phrase}?",
            ]
        
        return {
            'question': random.choice(questions),
            'expected_answer': description,
            'participants': participants,
            'event_type': event_type,
            'context': event
        }
    
    def _generate_person_question(self, interactions: List[Dict], days_back: int) -> Dict:
        """Generate question about a person interaction"""
        interaction = random.choice(interactions)
        person_name = interaction.get('person_name', 'someone')
        context = interaction.get('context', '')
        
        time_phrase = self._get_time_phrase(days_back)
        
        questions = [
            f"Do you remember what you and {person_name} talked about {time_phrase}?",
            f"Can you recall your conversation with {person_name} {time_phrase}?",
            f"Do you remember what {person_name} said {time_phrase}?"
        ]
        
        return {
            'question': random.choice(questions),
            'expected_answer': context,
            'person': person_name,
            'context': interaction
        }
    
    def _generate_conversation_question(self, summaries: List[Dict], days_back: int) -> Dict:
        """Generate question about a conversation"""
        summary_data = random.choice(summaries)
        summary = summary_data.get('summary', '')
        topics = summary_data.get('topics', [])
        
        time_phrase = self._get_time_phrase(days_back)
        
        if topics:
            topic = random.choice(topics)
            questions = [
                f"Do you remember discussing {topic} {time_phrase}?",
                f"Can you recall the conversation about {topic} {time_phrase}?"
            ]
        else:
            questions = [
                f"Do you remember what you talked about {time_phrase}?",
                f"Can you recall any conversations {time_phrase}?"
            ]
        
        return {
            'question': random.choice(questions),
            'expected_answer': summary,
            'topics': topics,
            'context': summary_data
        }
    
    def _get_time_phrase(self, days_back: int) -> str:
        """Convert days_back to natural language"""
        if days_back == 0:
            return "today"
        elif days_back == 1:
            return "yesterday"
        elif days_back == 2:
            return "two days ago"
        elif days_back <= 7:
            return f"{days_back} days ago"
        else:
            return "recently"
    
    def evaluate_answer(self, user_answer: str, expected_answer: str, context: Dict) -> Dict:
        """
        Use LLM to evaluate if the user's answer is correct
        Returns: {
            'correct': True/False,
            'feedback': 'Great job! You remembered correctly.',
            'hint': 'Think about...' (if incorrect)
        }
        """
        try:
            prompt = f"""You are evaluating a memory test for an Alzheimer's patient.

Question Context: {context}
Expected Answer: {expected_answer}
User's Answer: {user_answer}

Evaluate if the user's answer shows they remember the event correctly.
They don't need to use exact words - understanding the key details is enough.

Provide a JSON response:
{{
    "correct": true/false,
    "confidence": 0.0-1.0,
    "feedback": "Encouraging feedback message",
    "hint": "Gentle hint if incorrect (don't reveal full answer)"
}}

Be encouraging and supportive. Focus on what they remembered correctly.
"""
            
            response = self.rag_agent.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a supportive memory assessment assistant for Alzheimer's patients."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            return {
                'correct': False,
                'confidence': 0.0,
                'feedback': "Let me help you remember...",
                'hint': expected_answer
            }


if __name__ == "__main__":
    # Example usage
    quiz_agent = MemoryQuizAgent()
    
    # Generate a question about yesterday
    question_data = quiz_agent.generate_memory_question(days_back=1)
    
    if question_data.get('question'):
        print(f"\nQuestion: {question_data['question']}")
        print(f"Expected: {question_data['expected_answer']}")
        
        # Simulate user answer
        user_answer = input("\nYour answer: ")
        
        # Evaluate
        evaluation = quiz_agent.evaluate_answer(
            user_answer,
            question_data['expected_answer'],
            question_data['context']
        )
        
        print(f"\n{evaluation['feedback']}")
        if not evaluation['correct'] and evaluation.get('hint'):
            print(f"Hint: {evaluation['hint']}")
    else:
        print("No recent memories to quiz about.")
