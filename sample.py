import cv2
from flask import Flask, Response
import threading
from devices import Devices
import sys
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore, messaging

app = Flask(__name__)

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
token_ref = db.collection('tokens')
queryToken = token_ref.where(field_path='userID', op_string='==', value=userID)
listOfTokens = [doc.to_dict() for doc in queryToken.get()] 

registration_token = listOfTokens[0]['deviceToken']
message = messaging.Message(
    notification=messaging.Notification(
        title='ElderWatch',
        body='Patient Might Be In Danger, Please Review By Clicking Here'
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

def generate_frames():
    global processed_frame

    while True:
        if processed_frame is not None:
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask_app():
    app.run(host='0.0.0.0', debug=True, use_reloader=False)

def real_time_detection():
    global processed_frame
    # Your while loop for real-time detection with YOLOv5 model
    # This part needs to be integrated with your YOLOv5 detection logic

    while True:
        ret, frame = stream.read()
        if not ret:
            break

        # Perform inference and processing on the frame
        # Update processed_frame with the annotated frame

        # Example: processed_frame = annotated_frame
        # Replace 'annotated_frame' with your processed frame

        # Ensure processed_frame is updated with the processed frame

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
                if (detectedCount == 100):
                    print("Reached the desired detected count")
                    res = messaging.send(message)
                    print('Successfully sent message:', res)
                    im,s = save_image_with_boxes(frame,detections)
                    detectedCount = 0
                    save_activity_history(im)
        
        cv2.imshow('Real-time Detection', results.render()[0])

        if cv2.waitKey(1) == ord('q'):
            break

if __name__ == '__main__':
    # Your existing code to initialize Firebase, YOLOv5 model, and video capture stream
    # Ensure these parts are integrated into the appropriate sections above

    processed_frame = None

    detection_thread = threading.Thread(target=real_time_detection)
    detection_thread.start()

    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()
