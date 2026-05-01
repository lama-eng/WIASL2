# face_embedding.py

import numpy as np
from PIL import Image
from mtcnn.mtcnn import MTCNN
from keras_facenet import FaceNet
import os
import pickle

# Initialize FaceNet
embedder = FaceNet()

def extract_face_embedding(image_array):
    detector = MTCNN()
    results = detector.detect_faces(image_array)

    if not results:
        raise ValueError("No face detected in the image.")

    x1, y1, width, height = results[0]['box']
    x1, y1 = abs(x1), abs(y1)
    x2, y2 = x1 + width, y1 + height
    face = image_array[y1:y2, x1:x2]

    embeddings = embedder.extract(face, threshold=0.95)
    if not embeddings:
        raise ValueError("Failed to extract face embeddings.")

    return embeddings[0]['embedding']

def save_embedding(image_array, output_path):
    embedding = extract_face_embedding(image_array)
    with open(output_path, 'wb') as file:
        pickle.dump(embedding, file)
    print(f"Embedding saved to {output_path}")

if __name__ == "__main__":
    image_path = input("Enter the image path: ")
    output_path = input("Enter the path to save the embedding: ")
    image = Image.open(image_path).convert('RGB')
    image_array = np.asarray(image)
    save_embedding(image_array, output_path)
