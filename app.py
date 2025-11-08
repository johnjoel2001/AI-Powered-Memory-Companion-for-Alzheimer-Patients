"""
Backend API - Receive Images and Audio, Store in Supabase
Includes Voice Recognition for Patient Detection
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from pathlib import Path
from supabase import create_client, Client
from robust_voice_system import RobustVoiceSystem
import tempfile

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Voice Recognition System
print("Loading voice recognition system...")
voice_system = RobustVoiceSystem()
try:
    voice_profile = voice_system.load_profile("patient_voice_robust.pkl")
    print("✅ Voice recognition ready!")
except Exception as e:
    print(f"⚠️  Voice recognition not available: {e}")
    voice_profile = None

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# Initialize Supabase client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Local storage as fallback
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
    """Receive image and store in Supabase"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400
        
        file = request.files['image']
        
        # Use original filename from Raspberry Pi
        # Format: pic_2025-11-08+01-07.jpg (date + hour-minute)
        filename = file.filename if file.filename else f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # Read file data
        file_data = file.read()
        
        # Upload to Supabase Storage
        if supabase:
            supabase.storage.from_('alzheimer-images').upload(
                filename,
                file_data,
                file_options={"content-type": "image/jpeg", "upsert": "true"}
            )
            storage_url = supabase.storage.from_('alzheimer-images').get_public_url(filename)
            
            # Extract timestamp from filename: pic_2025-11-08+01-07.jpg
            # Format: pic_YYYY-MM-DD+HH-MM.jpg
            try:
                parts = filename.replace('pic_', '').replace('.jpg', '').split('+')
                date_part = parts[0]  # 2025-11-08
                time_part = parts[1].replace('-', ':')  # 01:07 -> 01:07
                captured_at = f"{date_part} {time_part}:00"  # 2025-11-08 01:07:00
                
                # Insert into images table
                supabase.table('images').insert({
                    'filename': filename,
                    'storage_url': storage_url,
                    'captured_at': captured_at
                }).execute()
            except Exception as e:
                print(f"Warning: Could not insert into database: {e}")
        else:
            # Fallback to local storage
            filepath = os.path.join(IMAGES_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(file_data)
            storage_url = f"/local/{filename}"
        
        return jsonify({
            'success': True,
            'message': 'Image received and stored successfully',
            'filename': filename,
            'url': storage_url
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/upload/audio', methods=['POST'])
def upload_audio():
    """Receive audio and store in Supabase"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio provided'
            }), 400
        
        file = request.files['audio']
        
        # Use original filename from Raspberry Pi
        # Format: audio_2025-11-08+01-05.wav (date + hour-minute, end time of 5-min chunk)
        filename = file.filename if file.filename else f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        # Read file data
        file_data = file.read()
        
        # Upload to Supabase Storage
        if supabase:
            supabase.storage.from_('alzheimer-audio').upload(
                filename,
                file_data,
                file_options={"content-type": "audio/wav", "upsert": "true"}
            )
            storage_url = supabase.storage.from_('alzheimer-audio').get_public_url(filename)
            
            # Extract timestamp from filename: audio_2025-11-08+01-05.wav
            # Format: audio_YYYY-MM-DD+HH-MM.wav (end time of 5-min chunk)
            try:
                parts = filename.replace('audio_', '').replace('.wav', '').split('+')
                date_part = parts[0]  # 2025-11-08
                end_time_part = parts[1].replace('-', ':')  # 01:05
                
                # Calculate start and end times (5-minute chunk)
                from datetime import datetime, timedelta
                end_time = datetime.strptime(f"{date_part} {end_time_part}:00", "%Y-%m-%d %H:%M:%S")
                start_time = end_time - timedelta(minutes=5)
                
                # Insert into audio_chunks table
                supabase.table('audio_chunks').insert({
                    'filename': filename,
                    'storage_url': storage_url,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                }).execute()
            except Exception as e:
                print(f"Warning: Could not insert into database: {e}")
        else:
            # Fallback to local storage
            filepath = os.path.join(AUDIO_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(file_data)
            storage_url = f"/local/{filename}"
        
        return jsonify({
            'success': True,
            'message': 'Audio received and stored successfully',
            'filename': filename,
            'url': storage_url
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


@app.route('/files', methods=['GET'])
def list_files():
    """List all uploaded files from Supabase"""
    try:
        images = []
        audio = []
        
        # List from Supabase if available
        if supabase:
            # List images
            image_list = supabase.storage.from_('alzheimer-images').list()
            images = [f['name'] for f in image_list if f['name'].endswith('.jpg')]
            
            # List audio
            audio_list = supabase.storage.from_('alzheimer-audio').list()
            audio = [f['name'] for f in audio_list if f['name'].endswith('.wav')]
        else:
            # Fallback to local storage
            if os.path.exists(IMAGES_FOLDER):
                images = sorted([f for f in os.listdir(IMAGES_FOLDER) if f.endswith('.jpg')])
            
            if os.path.exists(AUDIO_FOLDER):
                audio = sorted([f for f in os.listdir(AUDIO_FOLDER) if f.endswith('.wav')])
        
        return jsonify({
            'success': True,
            'images': {
                'count': len(images),
                'files': sorted(images)
            },
            'audio': {
                'count': len(audio),
                'files': sorted(audio)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/verify/voice', methods=['POST'])
def verify_voice():
    """
    Verify if audio contains patient's voice
    Returns: should_take_photos (boolean)
    """
    try:
        if not voice_profile:
            return jsonify({
                'success': False,
                'error': 'Voice recognition not available'
            }), 503
        
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio provided'
            }), 400
        
        audio_file = request.files['audio']
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Verify voice
            is_patient, max_similarity, mean_similarity = voice_system.verify_voice_robust(
                temp_path, 
                voice_profile, 
                threshold=0.70
            )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return jsonify({
                'success': True,
                'is_patient_voice': is_patient,
                'should_take_photos': is_patient,
                'max_similarity': float(max_similarity),
                'mean_similarity': float(mean_similarity),
                'threshold': 0.70,
                'message': 'Patient detected - take photos!' if is_patient else 'Patient not speaking - skip photos'
            }), 200
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
        
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
