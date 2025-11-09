#!/usr/bin/env python3
"""
Image-Based Memory Chat
Shows photos from Supabase storage and asks recognition questions
"""

import os
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv
from family_context import get_person_context
from datetime import datetime, timedelta

load_dotenv()


class ImageMemoryChat:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.current_step = 0
        self.wrong_attempts = {}
        
    def get_recent_photos(self, days_back=7):
        """Get photos from database by detected_persons"""
        try:
            # Query images table for photos with detected persons
            result = self.supabase.table('images') \
                .select('id, storage_url, detected_persons, captured_at') \
                .not_.is_('detected_persons', 'null') \
                .order('captured_at', desc=True) \
                .limit(20) \
                .execute()
            
            # Group photos by person
            person_photos = {
                'harry': [],
                'rae': []
            }
            
            for image in result.data:
                detected = image.get('detected_persons', [])
                
                # Check if Harry or Rae is detected
                if 'harry' in [p.lower() for p in detected]:
                    person_photos['harry'].append({
                        'id': image['id'],
                        'url': image['storage_url'],
                        'captured_at': image.get('captured_at'),
                        'person': 'harry'
                    })
                
                if 'rae' in [p.lower() for p in detected]:
                    person_photos['rae'].append({
                        'id': image['id'],
                        'url': image['storage_url'],
                        'captured_at': image.get('captured_at'),
                        'person': 'rae'
                    })
            
            print(f"✅ Found {len(person_photos['harry'])} Harry photos, {len(person_photos['rae'])} Rae photos")
            return person_photos
            
        except Exception as e:
            print(f"❌ Error fetching photos: {e}")
            return {'harry': [], 'rae': []}
    
    def create_image_questions(self, person_photos):
        """Create questions based on available photos - one unique photo per person"""
        questions = []
        used_photo_ids = set()
        
        # Question for each person with photos
        for person, photos in person_photos.items():
            if photos:
                # Find first photo that hasn't been used yet
                photo = None
                for p in photos:
                    if p['id'] not in used_photo_ids:
                        photo = p
                        used_photo_ids.add(p['id'])
                        break
                
                # If all photos used, skip this person
                if not photo:
                    continue
                
                person_info = get_person_context(person)
                
                questions.append({
                    'image_url': photo['url'],
                    'image_id': photo['id'],
                    'person': person,
                    'question': f"Hello John! 🌅 Do you remember who this person is?",
                    'expected_keywords': [person, person_info['relation'].split()[-1]],  # e.g., 'rae', 'sister'
                    'correct_response': f"Yes! That's wonderful! This is {person.title()}, your {person_info['relation']}! 💕",
                    'hints': self._get_person_hints(person, person_info)
                })
        
        return questions
    
    def _get_person_hints(self, person, person_info):
        """Generate progressive hints for person recognition"""
        hints = {
            'rae': [
                "That's okay, John. Think about your younger sister - the one who's 62 years old.",
                "She loves interior design and decorating. She has three adorable little dogs! 🐕",
                "Her name starts with 'R' - she's the one with the chihuahuas named after 90s pop stars!",
                "It's Rae, John! Your lovely sister Rae. She was so happy to see you!"
            ],
            'harry': [
                "That's okay, John. Think about your younger brother - the 66-year-old inventor.",
                "He loves building gadgets in his garage! He's always making something new.",
                "His name starts with 'H' - he's the one who names his tools like 'Larry the Ladder'!",
                "It's Harry, John! Your brother Harry who loves inventing things!"
            ]
        }
        
        return hints.get(person, [
            f"This is your {person_info['relation']}.",
            f"They are {person_info['age']} years old.",
            f"It's {person.title()}!"
        ])
    
    def start_conversation(self):
        """Start the image-based conversation"""
        # Get recent photos
        person_photos = self.get_recent_photos(days_back=7)
        
        # Create questions
        questions = self.create_image_questions(person_photos)
        
        if not questions:
            return {
                'success': False,
                'message': "No photos found in storage. Please upload photos of Harry and Rae."
            }
        
        # Return first question
        first_question = questions[0]
        
        return {
            'success': True,
            'greeting': "Good morning John! 🌅",
            'image_url': first_question['image_url'],
            'question': first_question['question'],
            'person': first_question['person'],
            'total_questions': len(questions),
            'questions': questions  # Store for later
        }
    
    def evaluate_answer(self, answer, current_question, attempt=0):
        """Evaluate user's answer with progressive hints"""
        answer_lower = answer.lower().strip()
        expected = current_question['expected_keywords']
        
        # Check if answer is correct
        is_correct = any(keyword in answer_lower for keyword in expected)
        
        if is_correct:
            return {
                'correct': True,
                'response': current_question['correct_response'],
                'next_question': None  # Will be set by caller
            }
        else:
            # Give progressive hint
            hints = current_question.get('hints', [])
            hint_index = min(attempt, len(hints) - 1)
            hint = hints[hint_index] if hints else "Try again, John. Think carefully."
            
            return {
                'correct': False,
                'response': hint,
                'attempt': attempt + 1
            }


if __name__ == "__main__":
    # Test the image memory chat
    chat = ImageMemoryChat()
    
    print("🖼️ Testing Image Memory Chat\n")
    
    # Start conversation
    result = chat.start_conversation()
    
    if result['success']:
        print(f"✅ {result['greeting']}")
        print(f"📸 Image: {result['image_url']}")
        print(f"❓ {result['question']}")
        print(f"\n📊 Total questions: {result['total_questions']}")
    else:
        print(f"❌ {result['message']}")
