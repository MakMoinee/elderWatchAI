import cv2
import torch
from devices import Devices
import sys
from datetime import datetime
import requests

import firebase_admin
from firebase_admin import credentials, firestore, messaging

from flask import Flask, Response

username = 'briansia321@gmail.com'
password = 'Dagolmanyak321'
if len(sys.argv) < 4:
    print("Please provide the complete required paramaters [ip,userID,phoneNumber] as a command-line argument.")
    sys.exit(1)

ip = sys.argv[1]
userID = sys.argv[2]
phoneNumber = sys.argv[3]
rtsp_url = f"rtsp://{ip}/live/ch00_0"
acceptable_confidence = 0.52

# Initialize Firebase Admin SDK
cred = credentials.Certificate('./elderwatch.json')  # Replace with your service account key file
firebase_admin.initialize_app(cred)
db = firestore.client()

key_ref = db.collection('keys')
queryKey = key_ref.where(field_path='isActive',op_string='==',value=True)
listOfKey = [doc.to_dict() for doc in queryKey.get()] 
smsApiKey = listOfKey[0]['apiKey']

token_ref = db.collection('tokens')
queryToken = token_ref.where(field_path='userID', op_string='==', value=userID)
listOfTokens = [doc.to_dict() for doc in queryToken.get()] 

registration_token = listOfTokens[0]['deviceToken']



## parent token
pg_ref = db.collection("patient_guardian")
pgQuery = pg_ref.where('caregiverID', '==', userID).where('ip', '==', ip)
pgResults = [doc.to_dict() for doc in pgQuery.get()] 
parentTokens = []
if len(pgResults)>0:
    token_ref = db.collection('tokens')
    parentQueryToken = token_ref.where('userIDMap','==',pgResults[0]['userID'])
    parentTokens = [doc.to_dict() for doc in parentQueryToken.get()] 

print(listOfTokens)

def manual_trigger():
    print("Starting manual trigger of notif")
    for tk in listOfTokens:
        message = messaging.Message(
            notification=messaging.Notification(
            title='ElderWatch',
            body='Patient Might Be In Danger, Please Review By Clicking Here'
            ),
            token=tk['deviceToken'],
        )
        res = messaging.send(message)
        print('Successfully sent message:', res)
    
    for pTk in parentTokens:
        message = messaging.Message(
            notification=messaging.Notification(
            title='ElderWatch',
            body='Patient Might Be In Danger, Please Review By Clicking Here'
            ),
            token=pTk['deviceToken'],
        )
        res = messaging.send(message)
        print('Successfully sent message:', res)
    exit()
    

def send_sms(api_key, recipient_number, message):
    url = "https://api.semaphore.co/api/v4/priority"
    payload = {
        "apikey": api_key,
        "number": recipient_number,
        "message": message
    }
    try:
        print(f"Sending SMS to {recipient_number}...")
        response = requests.post(url, data=payload)
        result = response.json()
        print(f"SMS API Response: {result}")
        
        if response.status_code == 200:
            print("SMS sent successfully!")
        else:
            print(f"SMS failed with status code: {response.status_code}")
        
        return result
    except Exception as e:
        print(f"ERROR sending SMS: {e}")
        return {"error": str(e)}

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

def save_activity_history(image_name):
    print("Saving activity history ...")
    activityHistory = {}
    activityHistory['caregiverID'] = userID
    activityHistory['ip'] = ip
    activityHistory['imagePath'] = f"./gallery/{image_name}"
    activityHistory['createdAt'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    activityHistory['status'] = "Unread"
    ref = db.collection('activity_history')
    ref.add(activityHistory)
    print("Successfully saved activity history")
    

def save_image_with_boxes(frame, detections):
    detected_objects = []
    for index, detection in detections.iterrows():
        if detection['confidence'] >= acceptable_confidence:
            box = [
                int(detection['xmin']),
                int(detection['ymin']),
                int(detection['xmax']),
                int(detection['ymax'])
            ]
            # Draw bounding box on the frame
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 2)
            cv2.putText(frame, f"{detection['name']} {detection['confidence']:.2f}",
                        (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            detected_objects.append({
                'name': detection['name'],
                'confidence': detection['confidence'],
                'bbox': box
            })

    if detected_objects:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_name = f"detected_{timestamp}.jpg"
        cv2.imwrite(f"./gallery/{image_name}", frame)
        return image_name, detected_objects

    return None, None

# Initialize the model
model_path = "./best.pt"  # Replace this with the path to your custom YOLOv5 .pt file
model = load_model(model_path)
updateOnce = False
# Set the model to evaluation mode
model.eval()

stream = cv2.VideoCapture(rtsp_url)
detectedCount = 0

try:
    while stream.isOpened():
        ret, frame = stream.read()
        if not ret:
            break

        if (updateOnce is not True):
            updateOnce = True
            print("Updating Device Status")
            err = updateStatus(userID, ip, 'Active')
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
                    detectedCount += 1
                    print(f"Fall detected! Count: {detectedCount}/100")
                if (detectedCount == 100):
                    print("Reached the desired detected count")
                    for tk in listOfTokens:
                        message = messaging.Message(
                            notification=messaging.Notification(
                                title='ElderWatch',
                                body='Patient Might Be In Danger, Please Review By Clicking Here'
                            ),
                            token=tk['deviceToken'],
                        )
                        res = messaging.send(message)
                        print('Successfully sent message:', res)
                    
                    for pTk in parentTokens:
                        message = messaging.Message(
                            notification=messaging.Notification(
                                title='ElderWatch',
                                body='Patient Might Be In Danger, Please Review By Clicking Here'
                            ),
                            token=pTk['deviceToken'],
                        )
                        res = messaging.send(message)
                        print('Successfully sent message:', res)
                    
                    im,s = save_image_with_boxes(frame,detections)
                    detectedCount = 0
                    
                    # Send SMS notification
                    sms_response = send_sms(smsApiKey, phoneNumber, "Patient Might Be In Danger, Please Review By Opening ElderWatch App")
                    print(f"SMS Response: {sms_response}")
                    
                    save_activity_history(im)
        
        cv2.imshow('Real-time Detection', results.render()[0])

        if cv2.waitKey(1) == ord('q'):
            break

except cv2.error as e:
    print(f"OpenCV error: {e}")
except KeyboardInterrupt:
    print("Keyboard Interrupt detected. Exiting...")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Release resources
    updateStatus(userID,ip,"Inactive")
    stream.release()
    cv2.destroyAllWindows()

