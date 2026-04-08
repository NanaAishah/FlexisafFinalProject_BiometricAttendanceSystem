import os
import time # For the shutdown timer

# UBUNTU COMPATIBILITY
os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["LC_ALL"] = "C.UTF-8"

import cv2
import numpy as np
import face_recognition
import pyttsx3
from datetime import datetime

# INITIALIZE VOICE ENGINE 
engine = pyttsx3.init()
engine.setProperty('rate', 145)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# DYNAMIC DATABASE LOADING
path = 'Training_images'
images = []
classNames = []
encodeListKnown = []

def load_and_encode():
    myList = os.listdir(path)
    for cl in myList:
        curImg = cv2.imread(f'{path}/{cl}')
        if curImg is not None:
            images.append(curImg)
            classNames.append(os.path.splitext(cl)[0].replace("_", " ").upper())
    
    encodeList = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img_rgb)
        if len(encodings) > 0:
            encodeList.append(encodings[0])
    return encodeList

print("System: Initializing Database...")
encodeListKnown = load_and_encode()
print(f"✅ {len(encodeListKnown)} Users Loaded.")

# ATTENDANCE LOGIC 
def mark_attendance(name):
    if not os.path.exists('attendance.csv'):
        with open('attendance.csv', 'w') as f: f.writelines('Name,Timestamp')
    with open('attendance.csv', 'r+') as f:
        data = f.readlines()
        nameList = [line.split(',')[0] for line in data]
        if name not in nameList:
            dtString = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.writelines(f'\n{name},{dtString}')
            print(f"✅ Logged: {name}")
            speak(f"Welcome {name}")

# MAIN ENGINE WITH AUTO-SHUTDOWN
cap = cv2.VideoCapture(0)

# Timer Variables
unknown_start_time = None
SHUTDOWN_LIMIT = 5 
system_running = True

print(f"--- Scanner Active. Auto-shutdown in {SHUTDOWN_LIMIT}s of Unknown status ---")

while system_running:
    success, img = cap.read()
    if not success: break

    # UI Header
    cv2.rectangle(img, (0, 0), (img.shape[1], 50), (30, 30, 30), cv2.FILLED)
    cv2.putText(img, f"SECURITY SCANNER | {datetime.now().strftime('%H:%M:%S')}", 
                (20, 32), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 255), 1)

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    img_rgb = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceLocs = face_recognition.face_locations(img_rgb)
    encodes = face_recognition.face_encodings(img_rgb, faceLocs)

    # FLAG: Did we find a valid person in THIS frame?
    any_authorized_found = False
    any_unknown_found = False

    for encodeFace, faceLoc in zip(encodes, faceLocs):
        name = "UNKNOWN"
        color = (0, 0, 255) 
        
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        
        if len(faceDis) > 0:
            matchIndex = np.argmin(faceDis)
            dist = round(faceDis[matchIndex], 2)
            print(f"Math Analysis -> Distance: {dist}") # The math output you wanted

            if dist < 0.45: # Strict match
                name = classNames[matchIndex]
                color = (0, 255, 0)
                any_authorized_found = True
                mark_attendance(name)
            else:
                any_unknown_found = True

        # Draw Box
        y1, x2, y2, x1 = [v*4 for v in faceLoc]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, f"{name} {dist if 'dist' in locals() else ''}", (x1, y1-10), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)

    # SHUTDOWN LOGIC
    if any_unknown_found and not any_authorized_found:
        # Start timer if not already started
        if unknown_start_time is None:
            unknown_start_time = time.time()
        
        elapsed = int(time.time() - unknown_start_time)
        remaining = SHUTDOWN_LIMIT - elapsed
        
        # VISUAL COUNTDOWN: Show the user how much time is left
        cv2.putText(img, f"SHUTDOWN IN: {remaining}s", (img.shape[1]-250, 32), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 2)
        
        if elapsed >= SHUTDOWN_LIMIT:
            print("SECURITY SHUTDOWN: Unauthorized access detected.")
            speak("Security Alert. Unauthorized user. System locking.")
            system_running = False
    else:
        # Reset the timer if a valid person appears or no one is there
        unknown_start_time = None

    cv2.imshow('Security Hub', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()