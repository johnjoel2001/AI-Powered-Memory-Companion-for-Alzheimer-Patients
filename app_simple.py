"""
Simple Backend API - Just Receive Images and Audio
Confirms receipt, that's it!
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'data'
IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'audio')

# Create directories
Path(IMAGES_FOLDER).mkdir(parents=True, exist_ok=True)
Path(AUDIO_FOLDER).mkdir(parents=True, exist_ok=True)


@app.route('/health', methods=['GET'])
def health_check():
    """Check if backend is running"""
    return jsonify({
        'status': 'healthy',
        'service': 'alzheimer-camera-backend'
    }), 200


@app.route('/upload/image', methods=['POST'])
def upload_image():
    """Receive image and confirm"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400
        
        file = request.files['image']
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"image_{timestamp}.jpg"
        filepath = os.path.join(IMAGES_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Image received successfully',
            'filename': filename
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/upload/audio', methods=['POST'])
def upload_audio():
    """Receive audio and confirm"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio provided'
            }), 400
        
        file = request.files['audio']
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"audio_{timestamp}.wav"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Audio received successfully',
            'filename': filename
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/upload/batch', methods=['POST'])
def upload_batch():
    """Receive both image and audio together"""
    try:
        results = {}
        
        # Save image
        if 'image' in request.files:
            image = request.files['image']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            image_filename = f"image_{timestamp}.jpg"
            image.save(os.path.join(IMAGES_FOLDER, image_filename))
            results['image'] = image_filename
        
        # Save audio
        if 'audio' in request.files:
            audio = request.files['audio']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            audio_filename = f"audio_{timestamp}.wav"
            audio.save(os.path.join(AUDIO_FOLDER, audio_filename))
            results['audio'] = audio_filename
        
        return jsonify({
            'success': True,
            'message': 'Files received successfully',
            'files': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Alzheimer's Camera Backend - Simple Version")
    print("=" * 60)
    print(f"Images will be stored in: {IMAGES_FOLDER}")
    print(f"Audio will be stored in: {AUDIO_FOLDER}")
    print("=" * 60)
    
    # Run the app
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
