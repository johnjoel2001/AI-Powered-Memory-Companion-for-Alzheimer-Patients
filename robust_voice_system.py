"""
Robust Voice Recognition System
Uses multiple training samples and ensemble approach for better accuracy
"""

from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import numpy as np
import pickle
import librosa

class RobustVoiceSystem:
    def __init__(self):
        """Initialize the robust voice system"""
        print("Loading speaker encoder...")
        self.encoder = VoiceEncoder()
        print("✅ Model loaded!")
    
    def train_with_multiple_samples(self, audio_files, output_path="patient_voice_robust.pkl"):
        """
        Train on multiple audio samples from the patient
        This creates a much more robust voice profile
        """
        print("\n" + "="*60)
        print("ROBUST TRAINING - Multiple Audio Samples")
        print("="*60)
        
        embeddings = []
        
        for audio_file in audio_files:
            print(f"\nProcessing: {audio_file}")
            
            # Load and preprocess
            wav = preprocess_wav(Path(audio_file))
            
            # Extract embedding
            embedding = self.encoder.embed_utterance(wav)
            embeddings.append(embedding)
            
            # Get duration
            y, sr = librosa.load(audio_file)
            duration = len(y) / sr
            print(f"  Duration: {duration:.2f}s, Embedding extracted")
        
        # Calculate mean and std of all embeddings
        embeddings_array = np.array(embeddings)
        mean_embedding = np.mean(embeddings_array, axis=0)
        std_embedding = np.std(embeddings_array, axis=0)
        
        # Save profile
        profile = {
            'mean_embedding': mean_embedding,
            'std_embedding': std_embedding,
            'all_embeddings': embeddings_array,
            'num_samples': len(audio_files),
            'audio_files': audio_files,
            'model': 'resemblyzer-ensemble',
            'trained_at': str(np.datetime64('now'))
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(profile, f)
        
        print(f"\n✅ Robust profile saved: {output_path}")
        print(f"Trained on {len(audio_files)} samples")
        print(f"This should be MUCH more accurate!")
        
        return profile
    
    def load_profile(self, profile_path="patient_voice_robust.pkl"):
        """Load robust profile"""
        with open(profile_path, 'rb') as f:
            profile = pickle.load(f)
        
        print(f"✅ Loaded robust profile from: {profile_path}")
        print(f"Trained on {profile['num_samples']} samples")
        
        return profile
    
    def verify_voice_robust(self, test_audio_path, profile, threshold=0.70):
        """
        Robust verification using ensemble approach
        Compares against ALL training samples, not just average
        """
        print(f"\nVerifying: {test_audio_path}")
        
        # Extract test embedding
        wav = preprocess_wav(Path(test_audio_path))
        test_embedding = self.encoder.embed_utterance(wav)
        
        # Compare against ALL training embeddings
        similarities = []
        for train_embedding in profile['all_embeddings']:
            sim = np.dot(test_embedding, train_embedding) / (
                np.linalg.norm(test_embedding) * np.linalg.norm(train_embedding)
            )
            similarities.append(sim)
        
        # Use multiple metrics
        max_similarity = np.max(similarities)
        mean_similarity = np.mean(similarities)
        median_similarity = np.median(similarities)
        
        # Ensemble decision: if ANY metric passes threshold, it's a match
        is_match = max_similarity > threshold
        
        print(f"Max similarity: {max_similarity:.4f}")
        print(f"Mean similarity: {mean_similarity:.4f}")
        print(f"Median similarity: {median_similarity:.4f}")
        print(f"Threshold: {threshold}")
        print(f"Match: {'✅ YES' if is_match else '❌ NO'}")
        
        return is_match, max_similarity, mean_similarity


def main():
    """
    To use this system:
    1. Collect 5-10 audio samples of the patient speaking
    2. Train on all samples
    3. System will be much more accurate
    """
    
    print("="*60)
    print("ROBUST VOICE RECOGNITION SYSTEM")
    print("="*60)
    print("\nTo get started:")
    print("1. Collect 5-10 audio recordings of the patient")
    print("2. Add them to the list below")
    print("3. Run this script to train")
    print("\nThe more samples, the better the accuracy!")
    
    # Example: Add your patient's audio files here
    patient_audio_files = [
        "audio_2025-11-08+02-54.wav",
        # Add more patient audio files here:
        # "patient_sample_2.wav",
        # "patient_sample_3.wav",
        # etc.
    ]
    
    if len(patient_audio_files) < 3:
        print("\n⚠️  WARNING: Only 1-2 samples provided")
        print("For best accuracy, collect at least 5 samples!")
    
    # Train
    system = RobustVoiceSystem()
    profile = system.train_with_multiple_samples(patient_audio_files)


if __name__ == "__main__":
    main()
