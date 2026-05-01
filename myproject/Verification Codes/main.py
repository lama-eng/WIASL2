#-------------------------------------Essential Imports-------------------------------#
import os
import csv
import cv2
from PIL import Image
import numpy as np
from keras_facenet import FaceNet
import matplotlib.pyplot as plt
import tensorflow as tf
from mtcnn.mtcnn import MTCNN
import pandas as pd
#-------------------------------------------------------------------------------------#
print("Starting FaceNet... This step can take a while if you are running it for the first time.\n")
embedder = FaceNet() # Instance of FaceNet object
facenet_model = embedder.model # Facenet model instance for getting the face embedding
print(facenet_model.summary()) # Summary of the model to check it is loaded successfully
def create_directory(directory): #This function is responsible for creating local directories
    if not os.path.exists(directory): #If the directory does not exist
        os.makedirs(directory) #Create the directory

def extract_face_from_camera(): #This function is responsible for extracting the face from the camera
    cap = cv2.VideoCapture(0) # Instiate a video capture using open CV
    detector = MTCNN() # Create an instance of MTCNN that will detect the face
    while True: # The camera stays turned on until a face is detected 
        ret, frame = cap.read() #ret checks that something is returned from the camera, frame is the image that will be checked for the face
        cv2.imshow('Camera', frame) # Show the camera feed
        cv2.waitKey(1)  # Wait for a key press to update the window
        if not ret: # if there is no return from the camera 
            break   # break out of the loop
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # open cv gets the image in BGR so it should be converted to RGB
        results = detector.detect_faces(rgb_frame) # detect the faces in the frame
        if results:
            x1, y1, width, height = results[0]['box'] # get the box coordinates where the face is present
            x1, y1 = abs(x1), abs(y1)   # convert x1 and y1 to their absolute value
            x2, y2 = x1 + width, y1 + height # get the coordinates of th second bottom right point of the box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # Draw rectangle around the face

            
            cv2.putText(frame, 'Face Detected', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2) #write Face Detected
            
            cv2.imshow('Camera', frame) # show the updated fram
            cv2.waitKey(1000) #wait for a sec
            face = rgb_frame[y1:y2, x1:x2] # cut the image from those coordinates
            
            if embedder.extract(face, threshold=0.95) == []:
                print("Failed to capture face... trying again.")
            else:
                cap.release()
                cv2.destroyAllWindows()
                return face
    cap.release() # close the camera
    cv2.destroyAllWindows()
    return face # return the face

def get_face(filename): #This function is responsible for returning the face from the database
    image = Image.open(filename) # open the image
    image = image.convert('RGB') #Convert it to RGB
    face_array = np.asarray(image) #convert it to array
    return face_array # return the face array

def Face_Verification(face1, face2): # This function is responsible for face Verification
    #-----------------------------------Just for Debugging-------------------------------------#
    # Display faces
    # plt.imshow(face1)
    # plt.title("Face 1")
    # plt.show()
    
    # plt.imshow(face2)
    # plt.title("Face 2")
    # plt.show()
    #-----------------------------------------------------------------------------------------#

    # Extract embeddings
    detect_ii = embedder.extract(face1, threshold=0.95) # Extract the embedding of the input face
    detect_jj = embedder.extract(face2, threshold=0.95) # Extract the embedding of the database face

    # Compute distance between embeddings
    dd = embedder.compute_distance(detect_ii[0]['embedding'], detect_jj[0]['embedding']) # This step is responsible for getting the distance between the embeddings using Cosine Similarity
    
    if dd < 0.5: # If the distance is less than 0.5
        print('Same Person') #The face belongs to the same person
        return True # return True to indicate it is the same person
    else:
        print('Different Person') #The face belongs to a different person
        return False # return false to indicate it is the same person
    
def sign_up(): # This function is responsible for signning up new users
    username = input("Enter username: ") # prompt the user to enter a username
    password = input("Enter password: ") # prompt the user to enter a password

    # Check if user already exists
    if os.path.exists(f"userDatabase/{username}"): # If user already exists in database
        print("User already exists.") # print that the user already exists
        return # return to the main menu

    # Create user directory
    create_directory(f"userDatabase/{username}") #if the user doesn't exist, add him to the database

    # Capture and save user's photo
    while True: #keep trying to capture a face, until we find one
        face = extract_face_from_camera() # extract the user's face from the camera
        if (embedder.extract(face, threshold=0.95)==[]): # if the user embedding can't be formed (the face is not detected correctly)
            print("failed to capture face... trying again.")  #we will try again
        else: #if the face was captured correctly
            break # exit the while loop
    cv2.imwrite(f"userDatabase/{username}/{username}.jpg", cv2.cvtColor(face, cv2.COLOR_RGB2BGR)) # add the face of this user to the database

    # Check if usersData.csv exists, if not create it with column headings
    if not os.path.exists('userDatabase/usersData.csv'): #if the excel file doesn't exist
        with open('userDatabase/usersData.csv', 'w', newline='') as file: #create the excel file
            writer = csv.writer(file) #institate the writer
            writer.writerow(['username', 'password']) #add the column headings for the excel file

    # Write to CSV
    with open('userDatabase/usersData.csv', 'a', newline='') as file: #open the excel file
        writer = csv.writer(file) #institate the writer
        writer.writerow([username, password]) #add the username and the password to the excel file

def sign_in(): # This function is responsible for signing in existing users
    username = input("Enter username: ") # prompt the user to enter a username
    password = input("Enter password: ") # prompt the user to enter a password

    # Read usersData.csv
    if not os.path.exists('userDatabase/usersData.csv'): # if the excel file doesn't exist
        print("User database not found.") # print that the user database not found
        return # return to the main menu

    df = pd.read_csv('userDatabase/usersData.csv', dtype={'username': str, 'password': str}) # read the user database
    #-----------------------------------Just for Debugging-------------------------------------#
    print(df)
    print(df['username'] == username)
    print(df['password'] == password)
    print(df['password'])
    #-----------------------------------------------------------------------------------------#
    if not df[(df['username'] == username) & (df['password'] == password)].empty: # if the user database contains the entered username and password
        print("User and password match!") # print that the user and password match
        print("Camera is starting...") # print that the camera is starting
        while True:  #keep trying to capture a face, until we find one
            face1 = extract_face_from_camera()# extract the user's face from the camera
            if (embedder.extract(face1, threshold=0.95)==[]):# if the user embedding can't be formed (the face is not detected correctly)
                print("failed to capture face... trying again.") #we will try again
            else: #if the face is captured correctly
                break # exit the while loop

        face2 = get_face(f"userDatabase/{username}/{username}.jpg") # retrive the face of this user from the database
        print("Verifying Face...") # print that the face is being verified
        if (Face_Verification(face1, face2) == True): # if the face is verified
            print("Sign in successful!") # print that the sign in is successful
        else:
            print("Face verification failed. Please try again.") # print that the face verification failed, the sign in is not successful    
    else:
        print("Invalid username or password.") # print that the username or password is invalid

if __name__ == "__main__": # The main function
    create_directory('userDatabase') # create the user database directory

    while True:
        print("Choose an option:") # print the options
        print("1. Sign Up") # Sign up
        print("2. Sign In") # Sign in
        print("3. Exit") # Exit

        choice = input("Enter your choice: ") # prompt the user to enter their choice

        if choice == '1': # if the user chooses to sign up
            sign_up() # call the sign up function
        elif choice == '2': # if the user chooses to sign in
            sign_in() # call the sign in function
        elif choice == '3': # if the user chooses to sign out
            break # break
        else: # if the user enters an invalid choice
            print("Invalid choice. Please choose again.") # print the error message
