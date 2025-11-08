"""
Test Voice Recognition System
Tests if the trained voice profile can detect the patient's voice
"""

from voice_training_simple import SimpleVoiceTrainer
import os

def test_voice_recognition():
    """Test the voice recognition system"""
    
    print("="*60)
    print("TESTING VOICE RECOGNITION SYSTEM")
    print("="*60)
    
    # Initialize trainer
    trainer = SimpleVoiceTrainer()
    
    # Load the trained patient profile
    print("\n1. Loading patient voice profile...")
    profile = trainer.load_patient_profile("patient_voice_profile.pkl")
    
    if not profile:
        print("❌ Failed to load profile!")
        return
    
    # Test with the same training audio (should match)
    print("\n" + "="*60)
    print("TEST 1: Verify with TRAINING AUDIO (should match)")
    print("="*60)
    
    training_audio = "audio_2025-11-08+02-54.wav"
    is_match, similarity = trainer.verify_voice(training_audio, profile, threshold=0.8)
    
    print(f"\nResult: {'✅ MATCH' if is_match else '❌ NO MATCH'}")
    print(f"Similarity: {similarity:.4f}")
    print(f"Expected: Should be HIGH similarity (>0.95)")
    
    # Test with different audio (if available)
    print("\n" + "="*60)
    print("TEST 2: Test with NEW AUDIO")
    print("="*60)
    
    # List available audio files
    audio_files = [f for f in os.listdir('.') if f.endswith('.wav')]
    print(f"\nAvailable audio files: {audio_files}")
    
    if len(audio_files) > 1:
        # Test with another audio file
        test_audio = [f for f in audio_files if f != training_audio][0]
        print(f"\nTesting with: {test_audio}")
        
        is_match, similarity = trainer.verify_voice(test_audio, profile, threshold=0.8)
        
        print(f"\nResult: {'✅ MATCH' if is_match else '❌ NO MATCH'}")
        print(f"Similarity: {similarity:.4f}")
    else:
        print("\n⚠️  No other audio files to test with")
        print("To test with new audio:")
        print("1. Record or download another audio file")
        print("2. Place it in this directory")
        print("3. Run this script again")
    
    # Show how to use in production
    print("\n" + "="*60)
    print("HOW TO USE IN PRODUCTION")
    print("="*60)
    print("""
# In your main application:

from voice_training_simple import SimpleVoiceTrainer

# Load once at startup
trainer = SimpleVoiceTrainer()
profile = trainer.load_patient_profile("patient_voice_profile.pkl")

# For each new audio chunk:
is_patient_speaking, similarity = trainer.verify_voice(
    "new_audio_chunk.wav", 
    profile, 
    threshold=0.8  # Adjust threshold as needed
)

if is_patient_speaking:
    print("✅ Patient detected - TAKE PHOTOS!")
    # Trigger camera to take photos
else:
    print("❌ Patient not speaking - SKIP PHOTOS")
    # Don't take photos
    """)
    
    print("\n" + "="*60)
    print("THRESHOLD GUIDE")
    print("="*60)
    print("""
Threshold values:
- 0.95+ : Very strict (only exact matches)
- 0.85-0.95 : Strict (recommended for same person)
- 0.75-0.85 : Moderate (allows some variation)
- 0.60-0.75 : Loose (may have false positives)

Recommended: Start with 0.8, adjust based on testing
    """)


if __name__ == "__main__":
    test_voice_recognition()
