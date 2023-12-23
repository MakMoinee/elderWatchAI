from quart import Quart, jsonify, request
from scapy.all import *
import firebase_admin
from firebase_admin import credentials, firestore
import cv2
import asyncio

app = Quart(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('./elderwatch.json')  # Replace with your service account key file
firebase_admin.initialize_app(cred)
db = firestore.client()

def is_rtsp_accessible(rtsp_url):
    try:
        cap = cv2.VideoCapture(rtsp_url)
        if cap.isOpened():
            cap.release()
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

# Endpoint to retrieve users
@app.route('/users', methods=['GET'])
def get_users():
    users_ref = db.collection('users')
    users = [doc.to_dict() for doc in users_ref.stream()]
    return jsonify({'users': users})


@app.route("/ping", methods=['GET'])
async def ping_ip():
    ip = request.args.get('ip')  # Get the 'ip' parameter from the request query string
    if not ip:
        return jsonify({"message": "IP address is missing in the request parameters"}), 400

    rtsp_url = f"rtsp://{ip}/live/ch00_0"

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, is_rtsp_accessible, rtsp_url)

    if result:
        return jsonify({"ip": ip, "status": "RTSP URL is accessible and working"}), 200
    else:
        return jsonify({"ip": ip, "status": "RTSP URL may not be accessible or is not working"}), 200


if __name__ == '__main__':
    app.run(debug=True)
