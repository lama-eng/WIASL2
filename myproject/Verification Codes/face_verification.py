# face_verification.py

import numpy as np
from PIL import Image
from keras_facenet import FaceNet
from face_embedding import extract_face_embedding

# Initialize FaceNet
embedder = FaceNet()

def verify_faces(image_array1, image_array2):
    embedding1 = extract_face_embedding(image_array1)
    embedding2 = extract_face_embedding(image_array2)
    
    distance = embedder.compute_distance(embedding1, embedding2)
    
    return distance < 0.5

if __name__ == "__main__":
    image_path1 = "tom2.jpg"
    #image_path2= "Al_Pacino_1.jpg"
    image_path2 = "tom.jpg"
    
    image1 = Image.open(image_path1).convert('RGB')
    image_array1 = np.asarray(image1)
    
    image2 = Image.open(image_path2).convert('RGB')
    image_array2 = np.asarray(image2)
    
    try:
        result = verify_faces(image_array1, image_array2)
        if result:
            print("The images belong to the same person.")
        else:
            print("The images belong to different persons.")
    except:
        print("No faces found in one image")

