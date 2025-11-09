#!/usr/bin/env python3
"""
Image Memory Chat UI
Web interface for photo-based memory questions
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from image_memory_chat import ImageMemoryChat
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Store active sessions
sessions = {}


@app.route('/')
def index():
    """Serve the image chat UI"""
    return render_template('image_chat.html')


@app.route('/api/start', methods=['POST'])
def start_conversation():
    """Start image-based conversation"""
    try:
        session_id = secrets.token_hex(8)
        
        # Create image chat
        chat = ImageMemoryChat()
        result = chat.start_conversation()
        
        if not result['success']:
            return jsonify(result), 400
        
        # Store session
        sessions[session_id] = {
            'chat': chat,
            'questions': result['questions'],
            'current_index': 0,
            'correct_answers': 0,
            'attempts': {}
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'greeting': result['greeting'],
            'image_url': result['image_url'],
            'question': result['question'],
            'total_questions': result['total_questions']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/answer', methods=['POST'])
def submit_answer():
    """Submit answer to current question"""
    try:
        data = request.json
        session_id = data.get('session_id')
        answer = data.get('answer', '')
        
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session'
            }), 400
        
        session_data = sessions[session_id]
        current_index = session_data['current_index']
        questions = session_data['questions']
        
        if current_index >= len(questions):
            return jsonify({
                'success': True,
                'is_end': True,
                'response': "🎉 You did wonderfully today, John! You remembered everyone! I'm so proud of you! 💕",
                'score': {
                    'correct': session_data['correct_answers'],
                    'total': len(questions)
                }
            })
        
        current_question = questions[current_index]
        
        # Get attempt count for this question
        attempt = session_data['attempts'].get(current_index, 0)
        
        # Evaluate answer
        result = session_data['chat'].evaluate_answer(
            answer,
            current_question,
            attempt
        )
        
        if result['correct']:
            # Correct! Move to next question
            session_data['correct_answers'] += 1
            session_data['current_index'] += 1
            session_data['attempts'][current_index] = 0
            
            # Get next question
            next_index = session_data['current_index']
            if next_index < len(questions):
                next_question = questions[next_index]
                return jsonify({
                    'success': True,
                    'correct': True,
                    'response': result['response'],
                    'image_url': next_question['image_url'],
                    'next_question': next_question['question'],
                    'is_end': False,
                    'score': {
                        'correct': session_data['correct_answers'],
                        'total': len(questions)
                    }
                })
            else:
                # All questions done
                return jsonify({
                    'success': True,
                    'correct': True,
                    'response': result['response'],
                    'is_end': True,
                    'final_message': "🎉 You did wonderfully today, John! You remembered everyone! I'm so proud of you! 💕",
                    'score': {
                        'correct': session_data['correct_answers'],
                        'total': len(questions)
                    }
                })
        else:
            # Wrong answer - give hint
            session_data['attempts'][current_index] = result['attempt']
            
            return jsonify({
                'success': True,
                'correct': False,
                'response': result['response'],
                'is_end': False
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5005))
    print(f"\n🖼️ Image Memory Chat UI running on port {port}")
    print("Show photos and ask recognition questions!\n")
    app.run(host='0.0.0.0', port=port, debug=True)
