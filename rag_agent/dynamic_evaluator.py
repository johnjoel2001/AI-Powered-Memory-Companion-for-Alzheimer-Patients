#!/usr/bin/env python3
"""
Dynamic Conversation Flow Generator
Automatically generates questions from actual memory data
This is the HEART of the solution - adapts to any new conversations!
"""

import os
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
from difflib import SequenceMatcher
from family_context import FAMILY_CONTEXT, get_person_context

load_dotenv()


def fuzzy_match(word1, word2, threshold=0.75):
    """Check if two words are similar enough (handles typos)"""
    return SequenceMatcher(None, word1.lower(), word2.lower()).ratio() >= threshold


class DynamicConversationFlow:
    def __init__(self, days_back=1):
        """
        Initialize with dynamic question generation from actual memories
        """
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.current_step = 0
        self.wrong_attempts = {}
        self.days_back = days_back
        
        # Load memories and generate questions dynamically
        self.memories = self._load_memories()
        self.flow = self._generate_question_flow()
    
    def _load_memories(self):
        """Load memories from the database"""
        from datetime import datetime, timedelta
        
        # Get memories from specified days back
        end_time = datetime.now()
        start_time = end_time - timedelta(days=self.days_back)
        
        result = self.supabase.table('memory_store') \
            .select('*') \
            .gte('memory_time', start_time.isoformat()) \
            .lte('memory_time', end_time.isoformat()) \
            .execute()
        
        return result.data if result.data else []
    
    def _generate_question_flow(self):
        """
        Generate questions dynamically from actual memory data using GPT
        This is the CORE innovation - questions adapt to real conversations!
        """
        if not self.memories:
            return []
        
        # Prepare memory context for GPT - ONLY about John's experiences
        memory_context = ""
        for i, mem in enumerate(self.memories, 1):
            person_info = get_person_context(mem['person'])
            # Parse the conversation to extract what happened TO JOHN
            conv = mem['full_conversation']
            
            memory_context += f"\nMemory {i} - {person_info['relation']} ({mem['person'].title()}) visited John:\n"
            memory_context += f"- Event: {mem['event']}\n"
            memory_context += f"- Summary: {mem['summary_text']}\n"
            memory_context += f"- Conversation snippet: {conv[:300]}...\n"
        
        # Use GPT to generate a natural question flow
        prompt = f"""You are creating a gentle memory test for John (72, Alzheimer's patient) about HIS experiences yesterday.

IMPORTANT: John is the PATIENT. Ask about what happened TO JOHN, not about other people's events.

FAMILY CONTEXT:
{FAMILY_CONTEXT}

ACTUAL MEMORIES FROM YESTERDAY (John's perspective):
{memory_context}

Generate a natural conversation flow with 5-7 questions that test JOHN'S memory of what happened to HIM:
1. Start broad (what occasion/event happened to John)
2. Ask who came to visit JOHN
3. Ask what people brought FOR JOHN or did WITH JOHN
4. Ask about specific details of JOHN'S experience
5. Test memory progressively

CRITICAL: All questions must be from John's perspective (e.g., "Do you remember YOUR birthday?" not "Harry's birthday")

For EACH question, provide:
- question: The actual question to ask JOHN about HIS experience
- expected_keywords: List of words that indicate correct answer (include typo variations)
- correct_response: Warm, encouraging response when correct
- hints: Array of 3-4 progressive hints using the FAMILY CONTEXT above (vague → specific → almost answer)

HINT EXAMPLES (use the family profiles!):
- For Rae: "Think about your younger sister - the one who's 62, loves interior design, and has three chihuahuas named after 90s pop stars!"
- For Harry: "Think about your younger brother - the 66-year-old inventor who builds gadgets in his garage!"
- Use their personalities, ages, and fun facts from the family context!

Return ONLY valid JSON array of question objects. No markdown, no explanation.

Example format:
[
  {{
    "question": "Do you remember what special day it was yesterday?",
    "expected_keywords": ["birthday", "bday", "72", "seventy"],
    "correct_response": "Yes! That's right! It was your 72nd birthday! 🎂",
    "hints": [
      "It was a very special day for you!",
      "You turned 72 years old!",
      "It was your birthday, John!"
    ]
  }}
]
"""
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You generate JSON question flows for Alzheimer's memory testing. Output ONLY valid JSON, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            import json
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            flow = json.loads(content)
            
            print(f"📝 GPT generated {len(flow)} questions")
            
            # Post-process: FORCE inject our rich family-based hints
            flow = self._enhance_hints_with_family_context(flow)
            
            print(f"✅ Final flow with {len(flow)} questions ready!")
            return flow
            
        except Exception as e:
            print(f"❌ Error generating questions: {e}")
            # Fallback to basic questions
            return self._generate_fallback_questions()
    
    def _enhance_hints_with_family_context(self, flow):
        """
        Replace generic hints with rich family-based hints
        This ensures we ALWAYS use the detailed family profiles
        """
        # Rich hint templates for people AND items
        rich_hints = {
            # People
            'rae': [
                "That's okay, John. Think about your younger sister - the one who's 62 years old.",
                "She loves interior design and decorating. She has three adorable little dogs! 🐕",
                "Her name starts with 'R' - she's the one with the chihuahuas named after 90s pop stars!",
                "It's Rae, John! Your lovely sister Rae came to visit you. She was so happy to see you!"
            ],
            'harry': [
                "That's okay. Think about your younger brother - the 66-year-old inventor.",
                "He loves building gadgets in his garage! He's always making something new.",
                "His name starts with 'H' - he's the one who names his tools like 'Larry the Ladder'!",
                "It's Harry, John! Your brother Harry who loves inventing things!"
            ],
            # Items
            'cake': [
                "No worries, John. She brought something very sweet that she made especially for you - your favorite dessert!",
                "It's something you eat at birthdays! It's sweet and delicious. 🎂",
                "Think of something with frosting and candles - it starts with 'C'!",
                "It's a cake, John! Rae brought you a beautiful chocolate cake!"
            ],
            'chocolate': [
                "That's alright. It was your favorite flavor - think of something delicious, brown and sweet!",
                "It's a very popular flavor that many people love. It's made from cocoa beans! 🍫",
                "The flavor starts with 'Ch' - it's brown and comes from cocoa!",
                "It's chocolate, John! Rae made you a delicious chocolate cake!"
            ],
            'frame': [
                "That's alright, John. He brought you something special to display your pictures - something that connects to MemorEye!",
                "It's something that shows photos! You can put it on a table or wall. 🖼️",
                "Think of something that holds pictures - it's a smart one that connects to your camera!",
                "It's a smartphone frame, John! Harry brought you a frame that shows all your MemorEye pictures!"
            ],
            'gift': [
                "He brought you something special - a present just for you!",
                "Think about what people bring to birthdays - something wrapped up nicely! 🎁",
                "It's a present! Something thoughtful that Harry made or bought for you.",
                "It's a gift, John! Harry brought you a wonderful birthday gift!"
            ]
        }
        
        # Enhance each question's hints
        for question in flow:
            keywords = [k.lower() for k in question.get('expected_keywords', [])]
            question_text = question.get('question', '').lower()
            
            # PRIORITY: Match keywords first (the answer), not question text
            # This ensures "What did Rae bring?" matches "cake" not "rae"
            hint_matched = False
            
            # First: Check keywords (the expected answer)
            for topic, hints in rich_hints.items():
                if topic in keywords or any(topic in k for k in keywords):
                    question['hints'] = hints
                    print(f"✅ Injected rich hints for '{topic}' (from keywords)")
                    hint_matched = True
                    break
            
            # Second: If no match, check question text (but only for people, not items)
            if not hint_matched:
                people = ['rae', 'harry', 'walter', 'elaine']
                for person in people:
                    if person in question_text and person in rich_hints:
                        # Only use person hints if the question is asking WHO, not WHAT
                        if 'who' in question_text:
                            question['hints'] = rich_hints[person]
                            print(f"✅ Injected rich hints for '{person}' (from question)")
                            hint_matched = True
                            break
            
            # If no hints were set, add generic ones
            if 'hints' not in question or not question['hints']:
                question['hints'] = [
                    "Take your time, John. Think carefully.",
                    "Let me give you another clue...",
                    "You're doing great! Here's more help..."
                ]
        
        return flow
    
    def _generate_fallback_questions(self):
        """Fallback questions if GPT fails"""
        if not self.memories:
            return []
        
        # Extract basic info from memories
        people = list(set([m['person'] for m in self.memories]))
        events = [m['event'] for m in self.memories]
        
        questions = []
        
        # Question 1: About the event
        questions.append({
            'question': f"Do you remember what happened yesterday?",
            'expected_keywords': [word.lower() for event in events for word in event.split()[:3]],
            'correct_response': "Yes! That's right!",
            'hints': [
                "Think about yesterday...",
                f"It was about {events[0].split()[0]}...",
                f"It was {events[0]}!"
            ]
        })
        
        # Question 2: About people
        for person in people:
            person_info = get_person_context(person)
            questions.append({
                'question': f"Do you remember who was with you?",
                'expected_keywords': [person, person_info['relation'].split()[-1]],
                'correct_response': f"Yes! {person.title()} was there!",
                'hints': [
                    f"Think about {person_info['relation']}...",
                    f"It was {person_info['relation']}!",
                    f"It was {person.title()}!"
                ]
            })
        
        return questions
    
    def get_current_question(self):
        """Get the current question"""
        if self.current_step >= len(self.flow):
            return None
        return self.flow[self.current_step]['question']
    
    def is_question(self, answer):
        """Check if the user is asking a question"""
        answer_lower = answer.lower().strip()
        
        # Short answers with ? are likely uncertain answers
        words = answer_lower.replace('?', '').strip().split()
        if len(words) <= 2 and '?' in answer:
            return False
        
        # Statement patterns
        statement_patterns = ['was it my', 'was it your', 'is it my', 'is it your', 'it was', 'it is']
        for pattern in statement_patterns:
            if pattern in answer_lower:
                return False
        
        question_indicators = ['who', 'what', 'when', 'where', 'why', 'how']
        return any(answer_lower.startswith(word) for word in question_indicators)
    
    def answer_user_question(self, question, current_step):
        """Answer user's question using actual memory context"""
        question_lower = question.lower()
        
        # Use memories to answer
        people = [m['person'] for m in self.memories]
        events = [m['event'] for m in self.memories]
        
        if 'who' in question_lower and ('visit' in question_lower or 'came' in question_lower):
            people_str = ", ".join([f"{p.title()}" for p in people[:-1]]) + f" and {people[-1].title()}" if len(people) > 1 else people[0].title()
            return f"{people_str} came to see you yesterday! 💕"
        
        elif 'what' in question_lower and 'happen' in question_lower:
            return f"Yesterday was special - {events[0]}! 🎉"
        
        else:
            return "That's a great question! Let me help you remember yesterday's special moments. 💕"
    
    def evaluate_answer(self, answer):
        """Evaluate answer with fuzzy matching"""
        if self.current_step >= len(self.flow):
            return {
                'correct': True,
                'response': "🎉 You did wonderfully today, John! You remembered so many beautiful moments. I'm so proud of you! See you tomorrow! 💕",
                'next_question': None,
                'is_end': True
            }
        
        step = self.flow[self.current_step]
        answer_lower = answer.lower().strip()
        
        # Check if user is asking a question
        if self.is_question(answer):
            response = self.answer_user_question(answer, self.current_step)
            return {
                'correct': False,
                'response': response,
                'next_question': step['question'],
                'is_end': False,
                'is_user_question': True
            }
        
        # Handle acknowledgments
        acknowledgments = ['okay', 'ok', 'thanks', 'thank you', 'got it', 'i see', 'alright', 'understood']
        if any(ack == answer_lower for ack in acknowledgments):
            return {
                'correct': False,
                'response': "Great! Let's continue.",
                'next_question': step['question'],
                'is_end': False
            }
        
        # Handle "I don't know"
        if any(phrase in answer_lower for phrase in ["i don't know", "dont know", "i dont know", "not sure", "can't remember", "cant remember"]):
            if self.current_step not in self.wrong_attempts:
                self.wrong_attempts[self.current_step] = 0
            
            self.wrong_attempts[self.current_step] = max(self.wrong_attempts[self.current_step], 2)
            
            if 'hints' in step and step['hints']:
                hint_index = min(self.wrong_attempts[self.current_step], len(step['hints']) - 1)
                hint = step['hints'][hint_index]
            else:
                hint = "Let me help you more..."
            
            self.wrong_attempts[self.current_step] += 1
            
            return {
                'correct': False,
                'response': f"That's completely okay, John. Let me help you. {hint}",
                'next_question': None,
                'is_end': False
            }
        
        # Check answer with fuzzy matching
        is_correct = False
        
        # Exact match first
        for keyword in step['expected_keywords']:
            if keyword in answer_lower:
                is_correct = True
                break
        
        # Fuzzy match for typos
        if not is_correct:
            answer_words = answer_lower.split()
            for keyword in step['expected_keywords']:
                for word in answer_words:
                    if fuzzy_match(word, keyword, threshold=0.75):
                        is_correct = True
                        break
                if is_correct:
                    break
        
        if is_correct:
            # Correct! Move to next question
            if self.current_step in self.wrong_attempts:
                del self.wrong_attempts[self.current_step]
            
            self.current_step += 1
            next_q = self.get_current_question()
            
            return {
                'correct': True,
                'response': step['correct_response'],
                'next_question': next_q,
                'is_end': next_q is None
            }
        else:
            # Wrong answer: give progressive hint
            if self.current_step not in self.wrong_attempts:
                self.wrong_attempts[self.current_step] = 0
            
            attempt = self.wrong_attempts[self.current_step]
            
            if 'hints' in step and step['hints']:
                hint_index = min(attempt, len(step['hints']) - 1)
                hint = step['hints'][hint_index]
            else:
                hint = "Try again!"
            
            self.wrong_attempts[self.current_step] += 1
            
            return {
                'correct': False,
                'response': hint,
                'next_question': None,
                'is_end': False
            }


if __name__ == "__main__":
    # Test the dynamic question generator
    print("Testing Dynamic Question Generator...")
    flow = DynamicConversationFlow(days_back=1)
    
    print(f"\n✅ Generated {len(flow.flow)} questions:")
    for i, q in enumerate(flow.flow, 1):
        print(f"\n{i}. {q['question']}")
        print(f"   Keywords: {q['expected_keywords']}")
