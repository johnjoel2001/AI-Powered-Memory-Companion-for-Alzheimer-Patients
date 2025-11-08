"""
Advanced Voice Training System using Deep Learning
Uses Resemblyzer for speaker embeddings (more accurate than MFCC)
"""

from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import numpy as np
import pickle
import librosa
import soundfile as sf

class AdvancedVoiceTrainer:
    def __init__(self):
        """Initialize the advanced speaker encoder"""
        print("Loading advanced speaker encoder (Resemblyzer)...")
        self.encoder = VoiceEncoder()
        print("✅ Model loaded!")
    
    def extract_voice_embedding(self, audio_path):
        """Extract deep learning voice embedding"""
        print(f"Processing: {audio_path}")
        
        # Load and preprocess audio
        wav = preprocess_wav(Path(audio_path))
        
        # Extract embedding
        embedding = self.encoder.embed_utterance(wav)
        
        print(f"  Extracted embedding (dimension: {len(embedding)})")
        return embedding
    
    def train_patient_voice(self, training_audio_path, output_path="patient_voice_profile_advanced.pkl"):
        """Train on patient's voice using deep learning"""
        print("\n" + "="*60)
        print("ADVANCED VOICE TRAINING (Deep Learning)")
        print("="*60)
        
        # Extract voice embedding
        embedding = self.extract_voice_embedding(training_audio_path)
        
        # Get audio duration
        y, sr = librosa.load(training_audio_path)
        duration = len(y) / sr
        
        # Save the voice profile
        voice_profile = {
            'embedding': embedding,
            'audio_path': training_audio_path,
            'audio_duration': duration,
            'model': 'resemblyzer',
            'trained_at': str(np.datetime64('now'))
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(voice_profile, f)
        
        print(f"\n✅ Advanced voice profile saved to: {output_path}")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"Audio analyzed: {duration:.2f} seconds")
        print(f"Model: Resemblyzer (Deep Learning)")
        
        return voice_profile
    
    def load_patient_profile(self, profile_path="patient_voice_profile_advanced.pkl"):
        """Load saved patient voice profile"""
        with open(profile_path, 'rb') as f:
            profile = pickle.load(f)
        
        print(f"✅ Loaded advanced voice profile from: {profile_path}")
        print(f"Trained on: {profile['trained_at']}")
        print(f"Model: {profile['model']}")
        
        return profile
    
    def verify_voice(self, test_audio_path, patient_profile, threshold=0.75):
        """
        Verify if voice matches patient using deep learning
        Resemblyzer uses cosine similarity:
        - 0.80+ : Very high match (same person)
        - 0.70-0.80 : High match (likely same person)
        - 0.60-0.70 : Moderate (uncertain)
        - <0.60 : Different person
        """
        print(f"\nVerifying voice in: {test_audio_path}")
        
        # Extract embedding from test audio
        test_embedding = self.extract_voice_embedding(test_audio_path)
        
        # Calculate cosine similarity
        patient_embedding = patient_profile['embedding']
        similarity = np.dot(test_embedding, patient_embedding) / (
            np.linalg.norm(test_embedding) * np.linalg.norm(patient_embedding)
        )
        
        is_match = similarity > threshold
        
        print(f"Similarity score: {similarity:.4f}")
        print(f"Threshold: {threshold}")
        print(f"Match: {'✅ YES' if is_match else '❌ NO'}")
        
        # Confidence level
        if similarity > 0.80:
            confidence = "Very High - Definitely same person"
        elif similarity > 0.70:
            confidence = "High - Likely same person"
        elif similarity > 0.60:
            confidence = "Moderate - Uncertain"
        else:
            confidence = "Low - Different person"
        
        print(f"Confidence: {confidence}")
        
        return is_match, similarity


def main():
    """Train on patient's voice with advanced model"""
    training_audio = "audio_2025-11-08+02-54.wav"
    
    # Initialize trainer
    trainer = AdvancedVoiceTrainer()
    
    # Train on patient's voice
    profile = trainer.train_patient_voice(training_audio)
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print("\nThis advanced model uses deep learning and should be")
    print("much more accurate at distinguishing different speakers.")
    print("\nRecommended threshold: 0.75")
    print("- Above 0.75: Patient's voice")
    print("- Below 0.75: Different person")


if __name__ == "__main__":
    main()
