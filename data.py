import cv2
import torch
from devices import Devices
import sys

import firebase_admin
from firebase_admin import credentials, firestore, messaging

username = 'briansia321@gmail.com'
password = 'Dagolmanyak321'
if len(sys.argv) < 3:
    print("Please provide the IP address as a command-line argument.")
    sys.exit(1)

ip = sys.argv[1]
userID = sys.argv[2]
rtsp_url = f"rtsp://{ip}/live/ch00_0"
acceptable_confidence = 0.52

# Initialize Firebase Admin SDK
cred = credentials.Certificate('./elderwatch.json')  # Replace with your service account key file
firebase_admin.initialize_app(cred)
db = firestore.client()


registration_token = "c-GoAsJBSgyPJJCJynbuCp:APA91bFl5vQSCuQFWcG0tAqosJan1UUX28ecM1QCLFFtZdeyTbH6pXxW-OVV991tUqbgZyJCOCe_S8xo97VjJgwRZviBcB53w3mJ9v7MuNeqtuz_4lM7JH8iOfe3lCG0qiUhgKIN4uJs"
message = messaging.Message(
    notification=messaging.Notification(
        title='ElderWatch',
        body='sample'
    ),
    token=registration_token,
)

# Load YOLOv5 model
def load_model(weights_path):
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path)
    return model

def updateStatus(user_id,ip,status):
    users_ref = db.collection('devices')
    query = users_ref.where('userID', '==', user_id).where('ip',"==",ip).limit(1)
    device_docs = query.get()
    err ={}
    if len(device_docs) == 0:
        err = {'error': 'Device not exist'}
        print({'error': 'Device not exist'})

    for doc in device_docs:
        doc.reference.update({'status': status})
        
    return err

# Initialize the model
model_path = "./best.pt"  # Replace this with the path to your custom YOLOv5 .pt file
model = load_model(model_path)
updateOnce = False
# Set the model to evaluation mode
model.eval()

stream = cv2.VideoCapture(rtsp_url)
detectedCount = 0

while stream.isOpened():
    ret, frame = stream.read()
    if not ret:
        break

    
    if (updateOnce is not True):
        updateOnce = True
        print("Updating Device Status")
        err = updateStatus(userID,ip,'Active')
        if 'error' in err and err['error'] != "":
            stream.release()
            cv2.destroyAllWindows()
            sys.exit()
    # Perform inference
    results = model(frame)
    detections = results.pandas().xyxy[0]
    for index, detection in detections.iterrows():
        if (detection['confidence'] >= acceptable_confidence):
            print(f"Confidence: {detection['confidence']}, Name: {detection['name']}")
            if "fall" in detection['name']:
                detectedCount = detectedCount + 1
            if (detectedCount==500):
                print("reached the desired detected count")
                res = messaging.send(message)
                print('Successfully sent message:', res)
                detectedCount=0
    
    cv2.imshow('Real-time Detection', results.render()[0])

    if cv2.waitKey(1) == ord('q'):
        break

# Release resources
updateStatus(userID,ip,"Inactive")
stream.release()
cv2.destroyAllWindows()
