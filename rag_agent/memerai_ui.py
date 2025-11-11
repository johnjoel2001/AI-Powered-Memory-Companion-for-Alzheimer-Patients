#!/usr/bin/env python3
"""
MemerAI Web UI
Bot initiates conversation proactively
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from memerai_rag_system import MemerAIRAG
# from complete_memory_system import CompleteMemorySystem  # Not needed for basic API
# from cognitive_improvement_system import CognitiveImprovementSystem  # Not needed for basic API
# from dynamic_evaluator import DynamicConversationFlow  # Dynamic questions from real data!
from simple_evaluator import SimpleConversationFlow  # Static - reliable and tested
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Initialize systems
rag = MemerAIRAG()
# memory_system = CompleteMemorySystem()  # Commented out for Railway deployment
# cognitive_system = CognitiveImprovementSystem()  # Commented out for Railway deployment

# Store active sessions
sessions = {}


@app.route('/')
def index():
    """Serve the MemerAI UI"""
    return render_template('memerai.html')


@app.route('/api/start', methods=['POST'])
def start_conversation():
    """
    Bot initiates conversation proactively
    Shows daily memory check
    """
    try:
        # Create session
        session_id = secrets.token_hex(8)
        
        # Start cognitive tracking (disabled for Railway)
        # cognitive_session = cognitive_system.start_session(days_back=0)
        
        # Get daily memory check (patient name is John)
        check = rag.daily_memory_check(days_back=0, patient_name="John")
        
        # Create simple conversation flow (static, reliable)
        conversation_flow = SimpleConversationFlow({
            'person': 'rae',
            'event': 'birthday celebration',
            'details': {
                'occasion': 'birthday',
                'who': ['rae', 'harry'],
                'item': 'cake',
                'flavor': 'chocolate'
            }
        })
        
        # Store session
        sessions[session_id] = {
            # 'cognitive_session_id': cognitive_session['session_id'],
            # 'start_time': cognitive_session['start_time'],
            'current_memory': check.get('memory'),
            'all_memories': check.get('all_memories', []),
            'conversation_flow': conversation_flow,  # Simple deterministic flow
            'questions_asked': 0,
            'correct_answers': 0,
            'hints_used': 0,
            'hint_level': 0
        }
        
        if check.get('has_memories'):
            memory = check['memory']
            
            # Get first question from simple flow
            first_question = conversation_flow.get_current_question()
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'greeting': check['greeting'],
                'question': first_question,
                'memory_id': memory['id'],
                'person': memory['person'],
                'event': memory['event'],
                'has_hint': True,
                'type': 'conversation'
            })
        else:
            return jsonify({
                'success': True,
                'session_id': session_id,
                'greeting': 'Good morning!',
                'question': 'How are you feeling today?',
                'has_hint': False,
                'type': 'greeting'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/answer', methods=['POST'])
def process_answer():
    """Process patient's answer"""
    try:
        data = request.json
        session_id = data.get('session_id')
        answer = data.get('answer', '')
        question_type = data.get('type', '')
        
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        session_data = sessions[session_id]
        session_data['questions_asked'] += 1
        
        # Get conversation flow
        conversation_flow = session_data.get('conversation_flow')
        
        if not conversation_flow:
            return jsonify({'error': 'No conversation flow'}), 400
        
        # Use simple deterministic evaluation
        evaluation = conversation_flow.evaluate_answer(answer)
        
        # Track performance
        is_correct = evaluation.get('correct', False)
        
        if is_correct:
            session_data['correct_answers'] += 1
        
        # Determine if conversation should end
        should_end = evaluation.get('is_end', False)
        
        return jsonify({
            'success': True,
            'response': evaluation['response'],
            'next_question': evaluation.get('next_question') if not should_end else None,
            'type': 'follow_up' if evaluation.get('next_question') and not should_end else 'end',
            'is_end': should_end,
            'score': {
                'correct': session_data['correct_answers'],
                'total': session_data['questions_asked']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/help', methods=['POST'])
def get_help():
    """When patient clicks 'Help me' button"""
    try:
        data = request.json
        session_id = data.get('session_id')
        memory_id = data.get('memory_id')
        
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        # Track hint usage and level
        sessions[session_id]['hints_used'] += 1
        sessions[session_id]['hint_level'] += 1
        
        hint_level = sessions[session_id]['hint_level']
        
        # Get progressive hint (patient name is John)
        explanation = rag.help_remember(memory_id, patient_name="John", hint_level=hint_level)
        
        return jsonify({
            'success': True,
            'explanation': explanation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Patient asks a question (classic RAG)"""
    try:
        data = request.json
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Use RAG to answer
        result = rag.ask(question)
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'memories_used': len(result.get('memories', []))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5004))
    print(f"\n🧠 MemerAI UI running on port {port}")
    print("Bot will initiate conversation proactively!\n")
    app.run(host='0.0.0.0', port=port, debug=False)
