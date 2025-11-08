#!/usr/bin/env python3
"""
Face Detection and Recognition using face_recognition package
Minimal implementation
"""

import cv2
import numpy as np
import face_recognition
from pathlib import Path
import pickle


class FaceRecognition:
    def __init__(self, known_faces_path="known_faces.pkl"):
        # Load or initialize face database
        self.known_faces = self._load_known_faces(known_faces_path)
        self.threshold = 0.6
        
    def _load_known_faces(self, path):
        """Load known faces from pickle file"""
        if Path(path).exists():
            with open(path, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def identify_face(self, embedding):
        """Identify face by comparing with known faces"""
        if not self.known_faces:
            return None, float('inf')
        
        names = list(self.known_faces.keys())
        known_embeddings = list(self.known_faces.values())
        
        # Calculate distances
        distances = face_recognition.face_distance(known_embeddings, embedding)
        min_distance = min(distances)
        
        if min_distance < self.threshold:
            identity = names[distances.argmin()]
        else:
            identity = None
        
        return identity, min_distance
    
    def process_image(self, image_path, output_path):
        """Process a single image: detect faces, recognize, and save with bounding boxes"""
        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Error loading image: {image_path}")
            return
        
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces and get encodings
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        # Process each detected face
        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            # Identify face
            identity, distance = self.identify_face(encoding)
            
            # Draw bounding box and label
            color = (0, 255, 0) if distance < self.threshold else (0, 165, 255)
            cv2.rectangle(image, (left, top), (right, bottom), color, 2)
            
            label = f"{identity} ({distance:.2f})" if identity else f"Unknown ({distance:.2f})"
            cv2.putText(image, label, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, color, 2)
        
        # Save output image
        cv2.imwrite(str(output_path), image)
        print(f"Processed: {image_path} -> {output_path} ({len(face_locations)} faces)")


def main():
    # Load all .jpg and .png files from the images/ directory into images as a list
    import glob

    images = glob.glob("images/*.jpg") + glob.glob("images/*.png")
    output_dir = "output"
    known_faces = "known_faces.pkl"
    threshold = 0.6
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize face recognition
    recognizer = FaceRecognition(known_faces)
    recognizer.threshold = threshold

    # Process images
    for image_path in images:
        image_path = Path(image_path)
        output_path = output_dir / f"detected_{image_path.name}"
        recognizer.process_image(image_path, output_path)
    
    print(f"\nProcessed {len(images)} images")


if __name__ == "__main__":
    main()
