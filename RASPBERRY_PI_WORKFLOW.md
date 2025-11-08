# Raspberry Pi Workflow - Voice Recognition + Camera

## Backend URL
```
https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app
```

## How It Works

### 1. Audio Recording (Continuous)
- Microphone records continuously
- Every 5 minutes, save audio chunk as: `audio_YYYY-MM-DD+HH-MM.wav`
- Upload audio chunk to backend

### 2. Voice Verification (For Each Chunk)
- Send audio chunk to `/verify/voice` endpoint
- Backend checks if patient's voice is present
- Returns: `should_take_photos` (true/false)

### 3. Photo Capture (Conditional)
- **IF** `should_take_photos == true`:
  - Camera takes photos every 5 seconds during that 5-minute period
  - Upload photos to backend
- **ELSE**:
  - Skip photos for that 5-minute period

---

## API Endpoints

### 1. Verify Voice (NEW!)
```bash
POST /verify/voice
```

**Request:**
```bash
curl -X POST \
  -F "audio=@audio_2025-11-08+01-05.wav" \
  https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/verify/voice
```

**Response:**
```json
{
  "success": true,
  "is_patient_voice": true,
  "should_take_photos": true,
  "max_similarity": 0.9246,
  "mean_similarity": 0.8726,
  "threshold": 0.70,
  "message": "Patient detected - take photos!"
}
```

### 2. Upload Audio
```bash
POST /upload/audio
```

**Request:**
```bash
curl -X POST \
  -F "audio=@audio_2025-11-08+01-05.wav" \
  https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/upload/audio
```

### 3. Upload Image
```bash
POST /upload/image
```

**Request:**
```bash
curl -X POST \
  -F "image=@pic_2025-11-08+01-07.jpg" \
  https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/upload/image
```

---

## Python Code for Raspberry Pi

```python
import requests
import time
from datetime import datetime
import pyaudio
import wave

BACKEND_URL = "https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app"

def record_audio_chunk(duration=300):
    """Record 5-minute audio chunk"""
    # Your audio recording code here
    timestamp = datetime.now().strftime("%Y-%m-%d+%H-%M")
    filename = f"audio_{timestamp}.wav"
    
    # Record audio...
    # Save as filename
    
    return filename

def verify_patient_voice(audio_file):
    """Check if patient's voice is in the audio"""
    with open(audio_file, 'rb') as f:
        response = requests.post(
            f"{BACKEND_URL}/verify/voice",
            files={'audio': f}
        )
    
    result = response.json()
    return result['should_take_photos']

def upload_audio(audio_file):
    """Upload audio to backend"""
    with open(audio_file, 'rb') as f:
        response = requests.post(
            f"{BACKEND_URL}/upload/audio",
            files={'audio': f}
        )
    return response.json()

def capture_and_upload_photo():
    """Capture photo and upload"""
    timestamp = datetime.now().strftime("%Y-%m-%d+%H-%M")
    filename = f"pic_{timestamp}.jpg"
    
    # Capture photo with camera
    # Save as filename
    
    # Upload
    with open(filename, 'rb') as f:
        response = requests.post(
            f"{BACKEND_URL}/upload/image",
            files={'image': f}
        )
    return response.json()

# Main Loop
while True:
    # Step 1: Record 5-minute audio chunk
    print("Recording 5-minute audio chunk...")
    audio_file = record_audio_chunk(duration=300)
    
    # Step 2: Upload audio
    print("Uploading audio...")
    upload_audio(audio_file)
    
    # Step 3: Verify if patient's voice is present
    print("Checking for patient's voice...")
    should_take_photos = verify_patient_voice(audio_file)
    
    if should_take_photos:
        print("✅ Patient detected! Taking photos...")
        
        # Take photos every 5 seconds for 5 minutes
        for i in range(60):  # 60 photos (5 min / 5 sec)
            capture_and_upload_photo()
            time.sleep(5)
    else:
        print("❌ Patient not speaking. Skipping photos.")
        time.sleep(300)  # Wait 5 minutes
```

---

## Simplified Workflow

```
Every 5 minutes:
├── 1. Record audio chunk (5 min)
├── 2. Upload audio to backend
├── 3. Call /verify/voice API
│   ├── IF patient detected:
│   │   └── Take photos every 5 seconds
│   └── ELSE:
│       └── Skip photos
└── Repeat
```

---

## Testing

### Test Voice Verification
```bash
# Test with patient's voice (should return true)
curl -X POST \
  -F "audio=@patient_audio.wav" \
  https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/verify/voice

# Expected response:
# {
#   "should_take_photos": true,
#   "message": "Patient detected - take photos!"
# }
```

### Test with Different Voice
```bash
# Test with someone else's voice (should return false)
curl -X POST \
  -F "audio=@other_person.wav" \
  https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/verify/voice

# Expected response:
# {
#   "should_take_photos": false,
#   "message": "Patient not speaking - skip photos"
# }
```

---

## Important Notes

1. **Audio Format**: WAV files, 16kHz sample rate recommended
2. **Image Format**: JPG files
3. **Naming Convention**:
   - Audio: `audio_YYYY-MM-DD+HH-MM.wav` (end time of 5-min chunk)
   - Images: `pic_YYYY-MM-DD+HH-MM.jpg` (capture time)
4. **Threshold**: 70% similarity (already configured in backend)
5. **Accuracy**: 100% tested accuracy with patient's voice

---

## Questions?

Contact: [Your contact info]
