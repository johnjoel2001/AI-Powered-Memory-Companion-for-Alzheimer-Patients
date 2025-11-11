#!/usr/bin/env python3
"""
Simple UI for Intelligent Conversation
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from intelligent_conversation import IntelligentConversation
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Store conversation instances per session
conversations = {}


@app.route('/')
def index():
    """Serve the conversation UI"""
    return render_template('conversation.html')


@app.route('/api/start', methods=['POST'])
def start_conversation():
    """Start a new conversation"""
    try:
        # Create new conversation instance
        conv = IntelligentConversation()
        session_id = secrets.token_hex(8)
        conversations[session_id] = conv
        
        # Get first question
        first_question = conv.start_conversation()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'question': first_question['question'],
            'type': first_question['type'],
            'has_memories': first_question.get('has_memories', False)
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
        
        if not session_id or session_id not in conversations:
            return jsonify({'error': 'Invalid session'}), 400
        
        conv = conversations[session_id]
        response = conv.process_answer(answer, question_type)
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'next_question': response.get('next_question'),
            'type': response.get('type'),
            'success_status': response.get('success', None)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    print(f"\n🧠 Intelligent Conversation UI running on http://localhost:{port}")
    print("Open your browser to start the conversation!\n")
    app.run(host='0.0.0.0', port=port, debug=True)
