import cv2
import numpy as np
from keras.models import load_model
from keras.preprocessing.image import img_to_array
import threading
import winsound
from tkinter import messagebox

class DrowsinessDetector:
    def __init__(self, model_path):
        self.model_path = model_path
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.left_eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_lefteye_2splits.xml')
        self.right_eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_righteye_2splits.xml')

    def start_alarm(self):
        try:
            winsound.Beep(1000, 1000)
        except Exception as e:
            print(f"Error playing alarm: {str(e)}")

    def run_detection(self, journey_active_callback, update_drowsiness_count):
        import warnings
        warnings.filterwarnings('ignore')
        
        cap = None
        try:
            model = load_model(self.model_path, compile=False)
            model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror("Camera Error", "Could not access the camera")
                return
                
            frame_counter = 0
            alarm_on = False

            while journey_active_callback():
                ret, frame = cap.read()
                if not ret:
                    messagebox.showerror("Camera Error", "Failed to capture frame")
                    break
                    
                # Your existing detection code here
                # (The entire content of the while loop from run_drowsiness_detection)
                # Replace self.drowsiness_count += 1 with update_drowsiness_count()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            if cap is not None and cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()