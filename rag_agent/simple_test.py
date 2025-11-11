#!/usr/bin/env python3
"""
SIMPLE TEST - Just see what data you have
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("="*60)
print("CHECKING YOUR DATA")
print("="*60)

# 1. Check audio chunks
print("\n1. AUDIO CHUNKS:")
audio = supabase.table('audio_chunks').select('*').limit(5).execute()
print(f"   Total: {len(audio.data)}")
for item in audio.data[:3]:
    print(f"   - {item.get('filename')}")
    print(f"     Text: {item.get('transcription', '')[:80]}...")

# 2. Check images
print("\n2. IMAGES:")
images = supabase.table('images').select('*').limit(5).execute()
print(f"   Total: {len(images.data)}")
for item in images.data[:3]:
    print(f"   - {item.get('filename')}")
    print(f"     Persons: {item.get('detected_persons', [])}")

# 3. Show one complete example
print("\n3. EXAMPLE - Audio + Images linked:")
if audio.data:
    audio_id = audio.data[0]['id']
    print(f"\n   Audio: {audio.data[0].get('filename')}")
    print(f"   Transcription: {audio.data[0].get('transcription', '')}")
    
    # Get images for this audio
    linked_images = supabase.table('images').select('*').eq('audio_chunk_id', audio_id).execute()
    print(f"\n   Linked Images: {len(linked_images.data)}")
    for img in linked_images.data:
        print(f"   - Persons detected: {img.get('detected_persons', [])}")

print("\n" + "="*60)
print("That's your current data!")
print("="*60)
