"""
Train voice profile with multiple audio samples for better accuracy
"""

from voice_training_simple import SimpleVoiceTrainer
import numpy as np
import pickle

def train_with_multiple_samples(audio_files, output_path="patient_voice_profile_multi.pkl"):
    """
    Train on multiple audio samples from the patient
    This creates a more robust voice profile
    """
    print("="*60)
    print("TRAINING WITH MULTIPLE AUDIO SAMPLES")
    print("="*60)
    
    trainer = SimpleVoiceTrainer()
    all_features = []
    
    for audio_file in audio_files:
        print(f"\nProcessing: {audio_file}")
        features = trainer.extract_voice_features(audio_file)
        all_features.append(features)
    
    # Average the features from all samples
    avg_features = np.mean(all_features, axis=0)
    
    # Calculate standard deviation (for future use)
    std_features = np.std(all_features, axis=0)
    
    # Save the voice profile
    voice_profile = {
        'features': avg_features,
        'std_features': std_features,
        'num_samples': len(audio_files),
        'audio_files': audio_files,
        'trained_at': str(np.datetime64('now'))
    }
    
    with open(output_path, 'wb') as f:
        pickle.dump(voice_profile, f)
    
    print(f"\n✅ Multi-sample voice profile saved to: {output_path}")
    print(f"Trained on {len(audio_files)} audio samples")
    print(f"This should give better accuracy!")
    
    return voice_profile


if __name__ == "__main__":
    # List your patient's audio files here
    patient_audio_files = [
        "audio_2025-11-08+02-54.wav",
        "test_record.wav",
        # Add more patient audio files here
    ]
    
    print("Patient audio files to train on:")
    for f in patient_audio_files:
        print(f"  - {f}")
    
    profile = train_with_multiple_samples(patient_audio_files)
