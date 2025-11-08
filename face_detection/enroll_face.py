#!/usr/bin/env python3
"""
Face Enrollment Script - Capture photos and register faces
"""

import cv2
import numpy as np
import face_recognition
import pickle
from pathlib import Path


class FaceEnrollment:
    def __init__(self, known_faces_path="known_faces.pkl"):
        # Load existing known faces
        self.known_faces_path = known_faces_path
        self.known_faces = self._load_known_faces()
    
    def _load_known_faces(self):
        """Load known faces from pickle file"""
        if Path(self.known_faces_path).exists():
            with open(self.known_faces_path, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def save_known_faces(self):
        """Save known faces to pickle file"""
        with open(self.known_faces_path, 'wb') as f:
            pickle.dump(self.known_faces, f)
        print(f"✓ Saved to {self.known_faces_path}")
    
    def detect_face(self, frame):
        """Detect largest face in frame"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) == 0:
            return None, None
        
        # Get largest face (top, right, bottom, left format)
        largest = max(face_locations, key=lambda loc: (loc[2]-loc[0]) * (loc[1]-loc[3]))
        top, right, bottom, left = largest
        
        # Convert to (x, y, w, h) format
        x, y, w, h = left, top, right - left, bottom - top
        return rgb_frame, (x, y, w, h)
    
    def get_embedding(self, frame):
        """Extract face embedding"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_frame)
        return encodings[0] if encodings else None
    
    def capture_photos(self, num_photos=5):
        """Capture multiple photos from camera"""
        print("\n" + "="*50)
        print("FACE ENROLLMENT")
        print("="*50)
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("✗ Cannot open camera")
            return None, None
        
        print(f"\nInstructions:")
        print(f"- Position your face in the frame")
        print(f"- Press SPACE to capture ({num_photos} photos needed)")
        print(f"- Vary your pose slightly between captures")
        print(f"- Press Q to quit\n")
        
        embeddings = []
        
        while len(embeddings) < num_photos:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect face
            rgb_frame, bbox = self.detect_face(frame)
            
            # Draw bounding box
            display_frame = frame.copy()
            if bbox:
                x, y, w, h = bbox
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(display_frame, "Face Detected", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(display_frame, "No face detected", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Show progress
            cv2.putText(display_frame, f"Captured: {len(embeddings)}/{num_photos}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            cv2.imshow('Enrollment - Press SPACE to capture', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):  # Space bar
                if bbox is not None:
                    # Get embedding
                    embedding = self.get_embedding(frame)
                    if embedding is not None:
                        embeddings.append(embedding)
                        print(f"✓ Photo {len(embeddings)}/{num_photos} captured")
                    else:
                        print("✗ Could not extract embedding, try again")
                else:
                    print("✗ No face detected, try again")
            
            elif key == ord('q'):
                print("\n✗ Enrollment cancelled")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if len(embeddings) < num_photos:
            return None
        
        return embeddings
    
    def enroll_person(self, num_photos=5):
        """Complete enrollment process"""
        # Capture photos
        embeddings = self.capture_photos(num_photos)
        
        if embeddings is None:
            return False
        
        # Prompt for name
        print("\n" + "-"*50)
        name = input("Enter person's name: ").strip()
        
        if not name:
            print("✗ Name cannot be empty")
            return False
        
        # Compute average embedding
        avg_embedding = np.mean(embeddings, axis=0)
        
        # Check if name exists
        if name in self.known_faces:
            print(f"\n⚠ '{name}' already exists. Overwriting...")
        
        # Save
        self.known_faces[name] = avg_embedding
        self.save_known_faces()
        
        print(f"\n✓ Successfully enrolled '{name}'")
        print(f"  - Photos captured: {len(embeddings)}")
        print(f"  - Embedding dimensions: {len(avg_embedding)}")
        print(f"  - Total people enrolled: {len(self.known_faces)}")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enroll faces for recognition')
    parser.add_argument('--known-faces', default='known_faces.pkl', help='Known faces database')
    parser.add_argument('--num-photos', type=int, default=9, help='Number of photos to capture')
    parser.add_argument('--list', action='store_true', help='List enrolled people')
    
    args = parser.parse_args()
    
    # Initialize enrollment
    enrollment = FaceEnrollment(args.known_faces)
    
    # List mode
    if args.list:
        print("\nEnrolled people:")
        print("-" * 30)
        if enrollment.known_faces:
            for i, name in enumerate(enrollment.known_faces.keys(), 1):
                print(f"{i}. {name}")
            print(f"\nTotal: {len(enrollment.known_faces)} people")
        else:
            print("(none)")
        return
    
    # Enrollment mode
    try:
        enrollment.enroll_person(args.num_photos)
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
