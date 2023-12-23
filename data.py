import cv2
import torch
from models.devices import Devices

import firebase_admin
from firebase_admin import credentials, firestore

username = 'briansia321@gmail.com'
password = 'Dagolmanyak321'
ip = "192.168.1.7"
rtsp_url = f"rtsp://{ip}/live/ch00_0"
acceptable_confidence = 0.52

# Load YOLOv5 model
def load_model(weights_path):
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path)
    return model

# Initialize the model
model_path = "./best.pt"  # Replace this with the path to your custom YOLOv5 .pt file
model = load_model(model_path)

# Set the model to evaluation mode
model.eval()

stream = cv2.VideoCapture(rtsp_url)

while stream.isOpened():
    ret, frame = stream.read()
    if not ret:
        break

    # Perform inference
    results = model(frame)
    detections = results.pandas().xyxy[0]
    for index, detection in detections.iterrows():
        if (detection['confidence'] >= acceptable_confidence):
            print(f"Confidence: {detection['confidence']}, Name: {detection['name']}")
            if "fall" in detection['name']:
                print("hey")
    
    cv2.imshow('Real-time Detection', results.render()[0])

    if cv2.waitKey(1) == ord('q'):
        break

# Release resources
stream.release()
cv2.destroyAllWindows()
