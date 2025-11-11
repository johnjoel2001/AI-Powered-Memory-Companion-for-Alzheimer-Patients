#!/usr/bin/env python3
"""
Simple, deterministic conversation flow
Uses rich family context and actual conversation details
"""

from difflib import SequenceMatcher

def fuzzy_match(word1, word2, threshold=0.75):
    """Check if two words are similar enough (handles typos)"""
    return SequenceMatcher(None, word1.lower(), word2.lower()).ratio() >= threshold

class SimpleConversationFlow:
    def __init__(self, memory_data):
        """
        memory_data should have:
        - person: "rae"
        - event: "birthday celebration"
        - details: {"occasion": "birthday", "who": ["rae", "harry"], "item": "cake", "flavor": "chocolate"}
        """
        self.memory = memory_data
        self.current_step = 0
        self.wrong_attempts = {}  # Track wrong attempts per question
        
        # Define the conversation flow with RICH FAMILY CONTEXT
        self.flow = [
            {
                'question': 'Do you remember what special occasion we celebrated yesterday?',
                'expected_keywords': ['birthday', 'bday', 'birth day', '72'],
                'correct_response': "Yes! That's absolutely right! It was your 72nd birthday. 🎂",
                'wrong_response': "That's okay, John. Let me help you - yesterday was a very special day for you. You turned 72 years old!",
                'next_step': 1
            },
            {
                'question': 'Do you remember who came to visit you in the morning?',
                'expected_keywords': ['rae', 'sister'],
                'correct_response': "Yes! That's wonderful! Your sister Rae came to visit you. 💕",
                'hints': [
                    "That's okay, John. Think about your younger sister - the one who's 62 years old. She loves you very much!",
                    "She's the one who loves interior design and decorating. She has three adorable little dogs! 🐕",
                    "Her name starts with 'R' - she's the one with the chihuahuas named after 90s pop stars! Can you remember?",
                    "It's Rae, John! Your lovely sister Rae came to visit you. She was so happy to see you!"
                ],
                'next_step': 2
            },
            {
                'question': 'Do you remember what Rae brought for you?',
                'expected_keywords': ['cake'],
                'correct_response': "Yes! That's exactly right! She brought you a beautiful cake. 🎂",
                'wrong_response': "No worries, John. She brought something very sweet that she made especially for you - your favorite dessert!",
                'next_step': 3
            },
            {
                'question': 'What kind of cake was it?',
                'expected_keywords': ['chocolate', 'choco'],
                'correct_response': "Perfect! Yes, it was chocolate cake - your absolute favorite! 🍫",
                'hints': [
                    "That's alright. It was your favorite flavor - think of something delicious, brown and sweet!",
                    "It's a very popular flavor that many people love. It's made from cocoa beans! 🍫",
                    "The flavor starts with 'Ch' - it's brown and comes from cocoa!",
                    "It's chocolate, John! Rae made you a delicious chocolate cake!"
                ],
                'next_step': 4
            },
            {
                'question': 'Do you remember who else came to celebrate with you?',
                'expected_keywords': ['harry', 'brother'],
                'correct_response': "Yes! That's wonderful! Your brother Harry was there too! He loves you so much. 💙",
                'wrong_response': "That's okay. Think about your younger brother - the 66-year-old inventor who loves building gadgets in his garage!",
                'next_step': 5
            },
            {
                'question': 'Do you remember what Harry brought for you?',
                'expected_keywords': ['frame', 'smart', 'phone', 'picture', 'gift'],
                'correct_response': "Yes! That's exactly right! He brought you a smartphone frame! What a thoughtful gift! 🎁",
                'wrong_response': "That's alright, John. He brought you something special to display your pictures - something that connects to MemorEye!",
                'next_step': 6
            },
            {
                'question': 'What does the smartphone frame do?',
                'expected_keywords': ['pictures', 'photos', 'memories', 'memorai', 'memoreye', 'show'],
                'correct_response': "Excellent! Yes! It shows all your beautiful pictures from MemorEye! 📸",
                'wrong_response': "That's okay. It displays something very special - all the wonderful moments captured by your camera!",
                'next_step': 7
            }
        ]
    
    def get_current_question(self):
        """Get the current question"""
        if self.current_step >= len(self.flow):
            return None
        return self.flow[self.current_step]['question']
    
    def is_question(self, answer):
        """Check if the user is asking a question (but not statements like 'was it my birthday?')"""
        answer_lower = answer.lower().strip()
        
        # If it's just a single word with ?, it's likely an uncertain answer, not a question
        words = answer_lower.replace('?', '').strip().split()
        if len(words) <= 2 and '?' in answer:
            return False  # "frame?" or "chocolate?" is an answer, not a question
        
        # Check for statement patterns that aren't really questions
        # "was it my birthday?" = statement, not question
        # "is it a mobile?" = real question
        statement_patterns = [
            'was it my',
            'was it your',
            'is it my',
            'is it your',
            'it was',
            'it is'
        ]
        
        for pattern in statement_patterns:
            if pattern in answer_lower:
                return False  # It's a statement/answer, not a question
        
        question_indicators = ['who', 'what', 'when', 'where', 'why', 'how']
        return any(answer_lower.startswith(word) for word in question_indicators)
    
    def answer_user_question(self, question, current_step):
        """Answer user's question using context"""
        question_lower = question.lower()
        
        # Check what question we're currently on to give context-aware answers
        current_question = self.flow[current_step]['question'].lower() if current_step < len(self.flow) else ""
        
        # If asking about Harry's gift while on that question
        if 'harry' in current_question and 'brought' in current_question:
            if 'mobile' in question_lower or 'phone' in question_lower:
                return "Very close! It's not exactly a mobile phone, but it's related - it's a smartphone frame that displays pictures! 📱➡️🖼️"
            elif 'frame' in question_lower or 'picture' in question_lower:
                return "Yes! You're on the right track! It's a frame for pictures!"
        
        # If asking about Rae's gift
        if 'rae' in current_question and 'brought' in current_question:
            if 'cake' in question_lower:
                return "Yes! You're thinking of the right thing! It was a cake!"
        
        # General questions
        if 'who' in question_lower and ('visit' in question_lower or 'came' in question_lower):
            return "Your sister Rae and your brother Harry came to visit you yesterday for your birthday! 💕"
        elif 'what' in question_lower and 'harry' in question_lower and ('bring' in question_lower or 'brought' in question_lower):
            return "Harry brought you a smartphone frame - it displays all your pictures from MemorEye! 🎁"
        elif 'what' in question_lower and 'rae' in question_lower and ('bring' in question_lower or 'brought' in question_lower):
            return "Rae brought you a delicious chocolate cake! 🎂"
        elif 'birthday' in question_lower or 'occasion' in question_lower:
            return "Yesterday was your 72nd birthday! It was a wonderful celebration! 🎂"
        else:
            return "That's a great question! Let me help you - we're talking about your birthday celebration yesterday with Rae and Harry. 💕"
    
    def evaluate_answer(self, answer):
        """Simple keyword matching"""
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
            # Return with the SAME question to continue the flow
            return {
                'correct': False,
                'response': response,
                'next_question': step['question'],  # Ask the same question again
                'is_end': False,
                'is_user_question': True
            }
        
        # Handle acknowledgments like "okay", "thanks", "got it" - continue with same question
        acknowledgments = ['okay', 'ok', 'thanks', 'thank you', 'got it', 'i see', 'alright', 'understood']
        if any(ack == answer_lower for ack in acknowledgments):
            return {
                'correct': False,
                'response': "Great! Let's continue.",
                'next_question': step['question'],  # Ask the same question again
                'is_end': False
            }
        
        # Special handling for "I don't know" - skip ahead in hints
        if any(phrase in answer_lower for phrase in ["i don't know", "dont know", "i dont know", "not sure", "can't remember", "cant remember"]):
            # Jump to a more helpful hint
            if self.current_step not in self.wrong_attempts:
                self.wrong_attempts[self.current_step] = 0
            
            # Skip to hint 2 or 3 (more specific)
            self.wrong_attempts[self.current_step] = max(self.wrong_attempts[self.current_step], 2)
            
            if 'hints' in step:
                hint_index = min(self.wrong_attempts[self.current_step], len(step['hints']) - 1)
                hint = step['hints'][hint_index]
            else:
                hint = step.get('wrong_response', 'Let me help you more...')
            
            self.wrong_attempts[self.current_step] += 1
            
            return {
                'correct': False,
                'response': f"That's completely okay, John. Let me help you. {hint}",
                'next_question': None,
                'is_end': False
            }
        
        # Check if any expected keyword is in the answer (with fuzzy matching for typos)
        is_correct = False
        
        # First try exact match
        for keyword in step['expected_keywords']:
            if keyword in answer_lower:
                is_correct = True
                break
        
        # If no exact match, try fuzzy matching for typos
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
            # Correct! Move to next question and reset attempts
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
            
            # Get hint based on attempt number
            if 'hints' in step:
                # Use progressive hints
                hint_index = min(attempt, len(step['hints']) - 1)
                hint = step['hints'][hint_index]
            else:
                # Fallback to single wrong_response
                hint = step.get('wrong_response', 'Try again!')
            
            self.wrong_attempts[self.current_step] += 1
            
            return {
                'correct': False,
                'response': hint,
                'next_question': None,  # Don't repeat - just give hint and wait
                'is_end': False
            }
