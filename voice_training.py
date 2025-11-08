"""
Voice Training System - Train on Alzheimer's Patient Voice
Uses speaker embeddings to create a voice profile
"""

import torch
import torchaudio
from pyannote.audio import Model
from pyannote.audio.pipelines import SpeakerDiarization
import numpy as np
import pickle
import os

class VoiceTrainer:
    def __init__(self, hf_token=None):
        """Initialize the speaker recognition model"""
        print("Loading speaker embedding model...")
        # Use pyannote.audio for speaker embeddings
        self.model = Model.from_pretrained(
            "pyannote/embedding",
            use_auth_token=hf_token
        )
        print("✅ Model loaded!")
    
    def extract_voice_embedding(self, audio_path):
        """Extract voice embedding from audio file"""
        print(f"Processing: {audio_path}")
        
        # Load audio
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Extract embedding using pyannote
        with torch.no_grad():
            embedding = self.model({"waveform": waveform, "sample_rate": 16000})
        
        return embedding.squeeze().cpu().numpy()
    
    def train_patient_voice(self, training_audio_path, output_path="patient_voice_profile.pkl"):
        """Train on patient's voice and save the profile"""
        print("\n" + "="*60)
        print("TRAINING ALZHEIMER'S PATIENT VOICE PROFILE")
        print("="*60)
        
        # Extract voice embedding from training audio
        embedding = self.extract_voice_embedding(training_audio_path)
        
        # Save the voice profile
        voice_profile = {
            'embedding': embedding,
            'audio_path': training_audio_path,
            'trained_at': str(np.datetime64('now'))
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(voice_profile, f)
        
        print(f"\n✅ Voice profile saved to: {output_path}")
        print(f"Embedding shape: {embedding.shape}")
        print(f"Embedding norm: {np.linalg.norm(embedding):.4f}")
        
        return voice_profile
    
    def load_patient_profile(self, profile_path="patient_voice_profile.pkl"):
        """Load saved patient voice profile"""
        with open(profile_path, 'rb') as f:
            profile = pickle.load(f)
        print(f"✅ Loaded patient voice profile from: {profile_path}")
        return profile
    
    def verify_voice(self, test_audio_path, patient_profile, threshold=0.25):
        """
        Check if voice in test audio matches patient's voice
        Returns: (is_match, similarity_score)
        """
        # Extract embedding from test audio
        test_embedding = self.extract_voice_embedding(test_audio_path)
        
        # Calculate cosine similarity
        patient_embedding = patient_profile['embedding']
        similarity = np.dot(test_embedding, patient_embedding) / (
            np.linalg.norm(test_embedding) * np.linalg.norm(patient_embedding)
        )
        
        # Convert to distance (lower is more similar)
        distance = 1 - similarity
        
        is_match = distance < threshold
        
        return is_match, similarity, distance


def main():
    """Train on patient's voice"""
    # Path to training audio
    training_audio = "audio_2025-11-08+02-54.wav"
    
    if not os.path.exists(training_audio):
        print(f"❌ Error: Training audio not found: {training_audio}")
        return
    
    # Initialize trainer
    trainer = VoiceTrainer()
    
    # Train on patient's voice
    profile = trainer.train_patient_voice(training_audio)
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print("\nYou can now use this profile to detect the patient's voice")
    print("in future audio recordings.")


if __name__ == "__main__":
    main()
