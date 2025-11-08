# API Testing Guide for Raspberry Pi

## Backend URL
```
https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app
```

## File Naming Format

### Images
**Format**: `pic_YYYY-MM-DD+HH-MM.jpg`

**Examples**:
- `pic_2025-11-08+01-00.jpg` (taken at 1:00 AM)
- `pic_2025-11-08+01-05.jpg` (taken at 1:05 AM)
- `pic_2025-11-08+14-30.jpg` (taken at 2:30 PM)

### Audio (5-minute chunks)
**Format**: `audio_YYYY-MM-DD+HH-MM.wav`

**Examples**:
- `audio_2025-11-08+01-05.wav` (covers 01:00 to 01:05)
- `audio_2025-11-08+01-10.wav` (covers 01:05 to 01:10)
- `audio_2025-11-08+14-35.wav` (covers 14:30 to 14:35)

**Note**: The time in the filename is the END time of the 5-minute chunk.

---

## API Endpoints

### 1. Health Check
```bash
curl https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "alzheimer-camera-backend"
}
```

---

### 2. Upload Image
```bash
curl -X POST \
  -F "image=@pic_2025-11-08+01-07.jpg" \
  https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/upload/image
```

**Response**:
```json
{
  "success": true,
  "message": "Image received and stored successfully",
  "filename": "pic_2025-11-08+01-07.jpg",
  "url": "https://aidxatmmfpmhxxpkmnny.supabase.co/storage/v1/object/public/alzheimer-images/pic_2025-11-08+01-07.jpg"
}
```

---

### 3. Upload Audio
```bash
curl -X POST \
  -F "audio=@audio_2025-11-08+01-05.wav" \
  https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/upload/audio
```

**Response**:
```json
{
  "success": true,
  "message": "Audio received and stored successfully",
  "filename": "audio_2025-11-08+01-05.wav",
  "url": "https://aidxatmmfpmhxxpkmnny.supabase.co/storage/v1/object/public/alzheimer-audio/audio_2025-11-08+01-05.wav"
}
```

---

### 4. List All Files
```bash
curl https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/files
```

**Response**:
```json
{
  "success": true,
  "images": {
    "count": 2,
    "files": ["pic_2025-11-08+01-00.jpg", "pic_2025-11-08+01-05.jpg"]
  },
  "audio": {
    "count": 1,
    "files": ["audio_2025-11-08+01-05.wav"]
  }
}
```

---

## Python Code for Raspberry Pi

```python
import requests
from datetime import datetime

BACKEND_URL = "https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app"

def upload_image(image_path):
    """Upload an image to the backend"""
    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(f"{BACKEND_URL}/upload/image", files=files)
        return response.json()

def upload_audio(audio_path):
    """Upload an audio file to the backend"""
    with open(audio_path, 'rb') as f:
        files = {'audio': f}
        response = requests.post(f"{BACKEND_URL}/upload/audio", files=files)
        return response.json()

# Example usage
if __name__ == "__main__":
    # Test image upload
    result = upload_image("pic_2025-11-08+01-07.jpg")
    print("Image upload:", result)
    
    # Test audio upload
    result = upload_audio("audio_2025-11-08+01-05.wav")
    print("Audio upload:", result)
```

---

## Testing Steps

1. **Check if backend is running**:
   ```bash
   curl https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/health
   ```

2. **Upload a test image**:
   ```bash
   curl -X POST -F "image=@your_image.jpg" \
     https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/upload/image
   ```

3. **Upload a test audio file**:
   ```bash
   curl -X POST -F "audio=@your_audio.wav" \
     https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/upload/audio
   ```

4. **Verify files are uploaded**:
   ```bash
   curl https://2025-ai-hackathon-raspberry-api-api-production.up.railway.app/files
   ```

---

## Important Notes

- ✅ Use the exact filename format
- ✅ Images must be `.jpg` format
- ✅ Audio must be `.wav` format
- ✅ Audio filename time = END time of 5-minute chunk
- ✅ All files are stored permanently in Supabase
- ✅ You can access uploaded files via the returned URL

---

## Need Help?

If you get errors, check:
1. Is the filename format correct?
2. Is the file a valid image/audio file?
3. Is the backend URL correct?
4. Check the error message in the response
