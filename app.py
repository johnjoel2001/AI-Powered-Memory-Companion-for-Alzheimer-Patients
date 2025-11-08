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
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Voice Recognition System (lazy loading)
voice_system = None
voice_profile = None

def get_voice_system():
    """Lazy load voice system only when needed"""
    global voice_system, voice_profile
    if voice_system is None:
        print("Loading voice recognition system...")
        voice_system = RobustVoiceSystem()
        voice_profile = voice_system.load_profile("patient_voice_robust.pkl")
        print("✅ Voice recognition ready!")
    return voice_system, voice_profile

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Initialize Supabase client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize OpenAI client
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
        
        # Check if folder parameter is provided (e.g., "temp")
        folder = request.form.get('folder', '')
        
        # Get detected persons (sent as JSON array or comma-separated string)
        detected_persons = None
        if 'detected_persons' in request.form:
            import json
            try:
                # Try parsing as JSON array
                detected_persons = json.loads(request.form.get('detected_persons'))
            except:
                # Fall back to comma-separated string
                detected_persons = [p.strip() for p in request.form.get('detected_persons').split(',')]
        
        # Use original filename from Raspberry Pi
        # Format: pic_2025-11-08+01-07.jpg (date + hour-minute)
        base_filename = file.filename if file.filename else f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # Add folder prefix if provided
        filename = f"{folder}/{base_filename}" if folder else base_filename
        
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
                from datetime import datetime
                
                # Parse timestamp from filename or use current time
                from datetime import timezone
                
                # Remove folder prefix before parsing
                base_filename = filename.split('/')[-1] if '/' in filename else filename
                
                if 'pic_' in base_filename and '+' in base_filename:
                    parts = base_filename.replace('pic_', '').replace('.jpg', '').replace('.png', '').split('+')
                    date_part = parts[0]  # 2025-11-08
                    time_part = parts[1].replace('-', ':')  # 17:37:03 or 17:37
                    
                    # Handle both formats: HH:MM:SS and HH:MM
                    if time_part.count(':') == 2:
                        # Format: HH:MM:SS (e.g., 17:37:03)
                        captured_at = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
                    else:
                        # Format: HH:MM (e.g., 17:37)
                        captured_at = datetime.strptime(f"{date_part} {time_part}:00", "%Y-%m-%d %H:%M:%S")
                else:
                    captured_at = datetime.now()
                
                # Make captured_at timezone-aware (UTC)
                if captured_at.tzinfo is None:
                    captured_at = captured_at.replace(tzinfo=timezone.utc)
                
                # Find matching audio chunk based on timestamp
                # Image captured_at should fall between audio start_time and end_time
                audio_chunk_id = None
                try:
                    result = supabase.table('audio_chunks').select('id, start_time, end_time, filename').execute()
                    for chunk in result.data:
                        # Parse timestamps and make timezone-aware
                        start_str = chunk['start_time'].replace('Z', '+00:00') if 'Z' in chunk['start_time'] else chunk['start_time']
                        end_str = chunk['end_time'].replace('Z', '+00:00') if 'Z' in chunk['end_time'] else chunk['end_time']
                        
                        start = datetime.fromisoformat(start_str)
                        end = datetime.fromisoformat(end_str)
                        
                        # Make timezone-aware if not already
                        if start.tzinfo is None:
                            start = start.replace(tzinfo=timezone.utc)
                        if end.tzinfo is None:
                            end = end.replace(tzinfo=timezone.utc)
                        
                        if start <= captured_at <= end:
                            audio_chunk_id = chunk['id']
                            print(f"✅ Matched image to audio chunk: {chunk['filename']}")
                            break
                except Exception as e:
                    print(f"⚠️  Could not find matching audio chunk: {e}")
                
                # Insert into images table with audio_chunk_id and detected_persons
                supabase.table('images').insert({
                    'filename': filename,
                    'storage_url': storage_url,
                    'captured_at': captured_at.isoformat(),
                    'detected_persons': detected_persons,
                    'audio_chunk_id': audio_chunk_id
                }).execute()
                print(f"✅ Image inserted with audio_chunk_id: {audio_chunk_id}, detected_persons: {detected_persons}")
            except Exception as e:
                print(f"⚠️  Could not insert into database: {e}")
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
        
        # Check if folder parameter is provided (e.g., "temp")
        folder = request.form.get('folder', '')
        
        # Use original filename from Raspberry Pi
        # Format: audio_2025-11-08+01-05.wav (date + hour-minute, end time of 5-min chunk)
        base_filename = file.filename if file.filename else f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        # Add folder prefix if provided
        filename = f"{folder}/{base_filename}" if folder else base_filename
        
        # Read file data
        file_data = file.read()
        
        # Save to temporary file for transcription
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(file_data)
            temp_path = temp_file.name
        
        # Transcribe audio using OpenAI Whisper (if available)
        transcription_text = None
        if openai_client:
            try:
                print(f"Auto-transcribing: {filename}")
                with open(temp_path, 'rb') as audio:
                    transcript = openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language="en"
                    )
                transcription_text = transcript.text
                print(f"✅ Transcription complete: {len(transcription_text)} characters")
            except Exception as e:
                print(f"⚠️  Transcription failed: {e}")
        
        # Clean up temp file
        os.unlink(temp_path)
        
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
                from datetime import datetime, timedelta
                
                # Try to parse timestamp from filename
                # Remove folder prefix (e.g., "temp/") before parsing
                base_filename = filename.split('/')[-1] if '/' in filename else filename
                
                if 'audio_' in base_filename and '+' in base_filename:
                    parts = base_filename.replace('audio_', '').replace('.wav', '').replace('.mp3', '').split('+')
                    date_part = parts[0]  # 2025-11-08
                    time_part = parts[1].replace('-', ':')  # 17:37:03 or 17:37
                    
                    # Handle both formats: HH:MM:SS and HH:MM
                    if time_part.count(':') == 2:
                        # Format: HH:MM:SS (e.g., 17:37:03)
                        end_time = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
                    else:
                        # Format: HH:MM (e.g., 17:37)
                        end_time = datetime.strptime(f"{date_part} {time_part}:00", "%Y-%m-%d %H:%M:%S")
                    
                    start_time = end_time - timedelta(minutes=5)
                else:
                    # Use current time if filename doesn't match pattern
                    end_time = datetime.now()
                    start_time = end_time - timedelta(minutes=5)
                
                # Insert into audio_chunks table with transcription
                supabase.table('audio_chunks').insert({
                    'filename': filename,
                    'storage_url': storage_url,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'transcription': transcription_text,
                    'transcribed_at': datetime.now().isoformat() if transcription_text else None
                }).execute()
                print(f"✅ Inserted into database: {filename}")
            except Exception as e:
                print(f"⚠️  Could not insert into database: {e}")
        else:
            # Fallback to local storage
            filepath = os.path.join(AUDIO_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(file_data)
            storage_url = f"/local/{filename}"
        
        return jsonify({
            'success': True,
            'message': 'Audio received, stored, and transcribed successfully',
            'filename': filename,
            'url': storage_url,
            'transcription': transcription_text,
            'transcription_length': len(transcription_text) if transcription_text else 0
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
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio provided'
            }), 400
        
        # Lazy load voice system
        try:
            vs, vp = get_voice_system()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Voice recognition not available: {str(e)}'
            }), 503
        
        audio_file = request.files['audio']
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Verify voice
            is_patient, max_similarity, mean_similarity = vs.verify_voice_robust(
                temp_path, 
                vp, 
                threshold=0.70
            )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return jsonify({
                'success': True,
                'is_patient_voice': bool(is_patient),
                'should_take_photos': bool(is_patient),
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


@app.route('/transcribe/audio', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio to text using OpenAI Whisper API
    and store in Supabase audio_chunks table
    """
    try:
        if not openai_client:
            return jsonify({
                'success': False,
                'error': 'OpenAI API not configured'
            }), 503
        
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio provided'
            }), 400
        
        audio_file = request.files['audio']
        filename = audio_file.filename
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Transcribe using OpenAI Whisper
            print(f"Transcribing: {filename}")
            with open(temp_path, 'rb') as audio:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="en"
                )
            
            transcription_text = transcript.text
            print(f"Transcription complete: {len(transcription_text)} characters")
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Update Supabase audio_chunks table with transcription
            if supabase:
                try:
                    result = supabase.table('audio_chunks').update({
                        'transcription': transcription_text,
                        'transcribed_at': datetime.now().isoformat()
                    }).eq('filename', filename).execute()
                    
                    print(f"✅ Transcription saved to Supabase for: {filename}")
                except Exception as db_error:
                    print(f"⚠️  Failed to save to Supabase: {db_error}")
            
            return jsonify({
                'success': True,
                'filename': filename,
                'transcription': transcription_text,
                'character_count': len(transcription_text),
                'message': 'Audio transcribed successfully'
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


@app.route('/sync/temp-audio', methods=['POST', 'GET'])
def sync_temp_audio():
    """
    Scan the 'temp' folder in Supabase storage and add audio files to database with transcription
    """
    try:
        if not supabase:
            return jsonify({
                'success': False,
                'error': 'Supabase not configured'
            }), 503
        
        # List all files in the temp folder
        files = supabase.storage.from_('alzheimer-audio').list('temp')
        
        synced_files = []
        errors = []
        
        for file_obj in files:
            try:
                filename = f"temp/{file_obj['name']}"
                
                # Check if already in database
                existing = supabase.table('audio_chunks').select('filename').eq('filename', filename).execute()
                if existing.data:
                    print(f"⏭️  Skipping (already in DB): {filename}")
                    continue
                
                # Download file from storage
                file_data = supabase.storage.from_('alzheimer-audio').download(filename)
                
                # Save to temp file for transcription
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_file.write(file_data)
                    temp_path = temp_file.name
                
                # Transcribe if OpenAI available
                transcription_text = None
                if openai_client:
                    try:
                        print(f"Transcribing: {filename}")
                        with open(temp_path, 'rb') as audio:
                            transcript = openai_client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio,
                                language="en"
                            )
                        transcription_text = transcript.text
                        print(f"✅ Transcribed: {len(transcription_text)} chars")
                    except Exception as e:
                        print(f"⚠️  Transcription failed: {e}")
                
                # Clean up temp file
                os.unlink(temp_path)
                
                # Get storage URL
                storage_url = supabase.storage.from_('alzheimer-audio').get_public_url(filename)
                
                # Parse timestamp or use current time
                from datetime import datetime, timedelta
                end_time = datetime.now()
                start_time = end_time - timedelta(minutes=5)
                
                # Insert into database
                supabase.table('audio_chunks').insert({
                    'filename': filename,
                    'storage_url': storage_url,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'transcription': transcription_text,
                    'transcribed_at': datetime.now().isoformat() if transcription_text else None
                }).execute()
                
                synced_files.append({
                    'filename': filename,
                    'transcription_length': len(transcription_text) if transcription_text else 0
                })
                print(f"✅ Synced: {filename}")
                
            except Exception as e:
                errors.append({
                    'filename': file_obj['name'],
                    'error': str(e)
                })
                print(f"❌ Error syncing {file_obj['name']}: {e}")
        
        return jsonify({
            'success': True,
            'synced_count': len(synced_files),
            'error_count': len(errors),
            'synced_files': synced_files,
            'errors': errors
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
