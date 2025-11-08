"""
Test Advanced Voice Recognition Model
"""

from advanced_voice_training import AdvancedVoiceTrainer

def test_all_audio():
    """Test the advanced model with all audio files"""
    
    print("="*60)
    print("TESTING ADVANCED VOICE RECOGNITION MODEL")
    print("="*60)
    
    # Initialize trainer and load profile
    trainer = AdvancedVoiceTrainer()
    profile = trainer.load_patient_profile("patient_voice_profile_advanced.pkl")
    
    # Test files
    test_files = [
        ("audio_2025-11-08+02-54.wav", "Training audio (YOUR voice)"),
        ("test_record.wav", "Record online (YOUR voice)"),
        ("harry_Audio.wav", "Harry's voice (NOT yours)"),
        ("whatsapp_test.wav", "WhatsApp audio (?)"),
    ]
    
    print("\n" + "="*60)
    print("TESTING ALL AUDIO FILES")
    print("="*60)
    
    results = []
    
    for audio_file, description in test_files:
        print(f"\n{'='*60}")
        print(f"Testing: {audio_file}")
        print(f"Description: {description}")
        print("="*60)
        
        try:
            is_match, similarity = trainer.verify_voice(audio_file, profile, threshold=0.75)
            results.append((audio_file, description, similarity, is_match))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((audio_file, description, 0.0, False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"{'Audio File':<30} {'Similarity':<12} {'Match?':<10} {'Description'}")
    print("-"*80)
    
    for audio_file, description, similarity, is_match in results:
        match_str = "✅ YES" if is_match else "❌ NO"
        print(f"{audio_file:<30} {similarity:.4f}      {match_str:<10} {description}")
    
    print("\n" + "="*60)
    print("INTERPRETATION")
    print("="*60)
    print("Threshold: 0.75")
    print("- Above 0.75: Patient's voice → TAKE PHOTOS")
    print("- Below 0.75: Different person → SKIP PHOTOS")


if __name__ == "__main__":
    test_all_audio()
