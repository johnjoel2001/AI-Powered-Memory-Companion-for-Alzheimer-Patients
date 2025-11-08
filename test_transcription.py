"""
Test Speech-to-Text Transcription
"""

import os
from openai import OpenAI

# Set API key
OPENAI_API_KEY = "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"

client = OpenAI(api_key=OPENAI_API_KEY)

# Test with a small audio file
audio_file = "Record (online-voice-recorder.com)-5.mp3"

print("="*60)
print("TESTING OPENAI WHISPER TRANSCRIPTION")
print("="*60)
print(f"\nTranscribing: {audio_file}")

with open(audio_file, 'rb') as audio:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
        language="en"
    )

print(f"\n✅ Transcription complete!")
print(f"Characters: {len(transcript.text)}")
print("\n" + "="*60)
print("TRANSCRIPTION:")
print("="*60)
print(transcript.text)
print("="*60)
