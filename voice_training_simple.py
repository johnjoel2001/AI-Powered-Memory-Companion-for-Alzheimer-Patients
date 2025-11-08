"""
Simple Voice Training System - Train on Alzheimer's Patient Voice
Uses MFCC features for voice fingerprinting
"""

import librosa
import numpy as np
import pickle
import os
from sklearn.preprocessing import StandardScaler

class SimpleVoiceTrainer:
    def __init__(self):
        """Initialize the voice trainer"""
        print("Initializing Simple Voice Trainer...")
        self.scaler = StandardScaler()
        print("✅ Ready!")
    
    def extract_voice_features(self, audio_path, duration=None):
        """Extract MFCC features from audio file"""
        print(f"Processing: {audio_path}")
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000, duration=duration)
        
        # Extract MFCC features (voice fingerprint)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        
        # Calculate statistics over time
        mfcc_mean = np.mean(mfccs, axis=1)
        mfcc_std = np.std(mfccs, axis=1)
        mfcc_max = np.max(mfccs, axis=1)
        mfcc_min = np.min(mfccs, axis=1)
        
        # Combine all features
        features = np.concatenate([mfcc_mean, mfcc_std, mfcc_max, mfcc_min])
        
        print(f"  Extracted {len(features)} features")
        return features
    
    def train_patient_voice(self, training_audio_path, output_path="patient_voice_profile.pkl"):
        """Train on patient's voice and save the profile"""
        print("\n" + "="*60)
        print("TRAINING ALZHEIMER'S PATIENT VOICE PROFILE")
        print("="*60)
        
        if not os.path.exists(training_audio_path):
            print(f"❌ Error: Training audio not found: {training_audio_path}")
            return None
        
        # Get audio duration
        duration = librosa.get_duration(path=training_audio_path)
        print(f"Audio duration: {duration:.2f} seconds")
        
        # Extract voice features from training audio
        features = self.extract_voice_features(training_audio_path)
        
        # Normalize features
        features_normalized = self.scaler.fit_transform(features.reshape(1, -1)).flatten()
        
        # Save the voice profile
        voice_profile = {
            'features': features,
            'features_normalized': features_normalized,
            'scaler_mean': self.scaler.mean_,
            'scaler_scale': self.scaler.scale_,
            'audio_path': training_audio_path,
            'audio_duration': duration,
            'trained_at': str(np.datetime64('now'))
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(voice_profile, f)
        
        print(f"\n✅ Voice profile saved to: {output_path}")
        print(f"Feature vector size: {len(features)}")
        print(f"Audio analyzed: {duration:.2f} seconds")
        
        return voice_profile
    
    def load_patient_profile(self, profile_path="patient_voice_profile.pkl"):
        """Load saved patient voice profile"""
        if not os.path.exists(profile_path):
            print(f"❌ Error: Profile not found: {profile_path}")
            return None
            
        with open(profile_path, 'rb') as f:
            profile = pickle.load(f)
        
        # Restore scaler
        self.scaler.mean_ = profile['scaler_mean']
        self.scaler.scale_ = profile['scaler_scale']
        
        print(f"✅ Loaded patient voice profile from: {profile_path}")
        print(f"Trained on: {profile['trained_at']}")
        print(f"Training audio duration: {profile['audio_duration']:.2f} seconds")
        
        return profile
    
    def verify_voice(self, test_audio_path, patient_profile, threshold=0.8):
        """
        Check if voice in test audio matches patient's voice
        Returns: (is_match, similarity_score)
        """
        print(f"\nVerifying voice in: {test_audio_path}")
        
        # Extract features from test audio
        test_features = self.extract_voice_features(test_audio_path)
        
        # Calculate cosine similarity directly (without normalization issues)
        patient_features = patient_profile['features']
        
        # Cosine similarity
        similarity = np.dot(test_features, patient_features) / (
            np.linalg.norm(test_features) * np.linalg.norm(patient_features) + 1e-10
        )
        
        is_match = similarity > threshold
        
        print(f"Similarity score: {similarity:.4f}")
        print(f"Threshold: {threshold}")
        print(f"Match: {'✅ YES' if is_match else '❌ NO'}")
        
        return is_match, similarity


def main():
    """Train on patient's voice"""
    # Path to training audio
    training_audio = "audio_2025-11-08+02-54.wav"
    
    if not os.path.exists(training_audio):
        print(f"❌ Error: Training audio not found: {training_audio}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in directory: {os.listdir('.')}")
        return
    
    # Initialize trainer
    trainer = SimpleVoiceTrainer()
    
    # Train on patient's voice
    profile = trainer.train_patient_voice(training_audio)
    
    if profile:
        print("\n" + "="*60)
        print("TRAINING COMPLETE!")
        print("="*60)
        print("\nYou can now use this profile to detect the patient's voice")
        print("in future audio recordings.")
        print("\nNext steps:")
        print("1. Use verify_voice() to check if new audio contains patient's voice")
        print("2. Set threshold (default 0.8) - higher = stricter matching")


if __name__ == "__main__":
    main()
