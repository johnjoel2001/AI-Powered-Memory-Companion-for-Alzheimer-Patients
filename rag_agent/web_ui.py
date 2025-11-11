#!/usr/bin/env python3
"""
Simple Web UI for Memory RAG Agent
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from memory_rag_agent import MemoryRAGAgent
from memory_quiz_agent import MemoryQuizAgent
import os

app = Flask(__name__)
CORS(app)

# Initialize agents
agent = MemoryRAGAgent()
quiz_agent = MemoryQuizAgent()


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """Handle memory queries"""
    try:
        data = request.json
        question = data.get('question', '')
        days_back = data.get('days_back', 7)
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Get answer from RAG agent
        answer = agent.query_memories(question, days_back=days_back)
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/process', methods=['POST'])
def process_audio():
    """Process a specific audio chunk"""
    try:
        data = request.json
        audio_chunk_id = data.get('audio_chunk_id', '')
        
        if not audio_chunk_id:
            return jsonify({'error': 'No audio_chunk_id provided'}), 400
        
        result = agent.process_audio_chunk(audio_chunk_id)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the knowledge graph"""
    try:
        # Get counts from database
        summaries = agent.supabase.table('conversation_summaries').select('id', count='exact').execute()
        events = agent.supabase.table('memory_events').select('id', count='exact').execute()
        interactions = agent.supabase.table('person_interactions').select('id', count='exact').execute()
        
        return jsonify({
            'success': True,
            'stats': {
                'conversation_summaries': summaries.count if hasattr(summaries, 'count') else 0,
                'memory_events': events.count if hasattr(events, 'count') else 0,
                'person_interactions': interactions.count if hasattr(interactions, 'count') else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/quiz/question', methods=['GET'])
def get_quiz_question():
    """Generate a memory quiz question"""
    try:
        days_back = int(request.args.get('days_back', 1))
        question_data = quiz_agent.generate_memory_question(days_back=days_back)
        
        if question_data.get('question'):
            return jsonify({
                'success': True,
                'question': question_data['question'],
                'question_id': str(hash(question_data['question'])),  # Simple ID
                'context': {
                    'expected_answer': question_data['expected_answer'],
                    'full_context': question_data['context']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': question_data.get('error', 'Could not generate question')
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/quiz/evaluate', methods=['POST'])
def evaluate_quiz_answer():
    """Evaluate user's answer to a quiz question"""
    try:
        data = request.json
        user_answer = data.get('answer', '')
        expected_answer = data.get('expected_answer', '')
        context = data.get('context', {})
        
        if not user_answer:
            return jsonify({'error': 'No answer provided'}), 400
        
        evaluation = quiz_agent.evaluate_answer(user_answer, expected_answer, context)
        
        return jsonify({
            'success': True,
            'evaluation': evaluation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    print(f"\n🚀 Memory Assistant UI running on http://localhost:{port}")
    print("Open your browser and start asking questions!\n")
    app.run(host='0.0.0.0', port=port, debug=True)
