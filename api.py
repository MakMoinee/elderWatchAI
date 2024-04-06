from quart import Quart, jsonify, request,send_from_directory
from scapy.all import *
import firebase_admin
from firebase_admin import credentials, firestore
import cv2
import asyncio
import subprocess
import socket  # Import the socket library

app = Quart(__name__)

ip_started = {}

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

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return None

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
    
@app.route("/start", methods=['GET'])
async def start_camera():
    ip = request.args.get('ip')  # Get the 'ip' parameter from the request query string
    if not ip:
        return jsonify({"message": "IP address is missing in the request parameters"}), 400
    
    userID = request.args.get('id')  # Get the 'ip' parameter from the request query string
    if not userID:
        return jsonify({"message": "id is missing in the request parameters"}), 400
    
    phoneNumber = request.args.get('phoneNumber')  # Get the 'ip' parameter from the request query string
    if not phoneNumber:
        return jsonify({"message": "phoneNumber is missing in the request parameters"}), 400

    rtsp_url = f"rtsp://{ip}/live/ch00_0"

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, is_rtsp_accessible, rtsp_url)

    if result:
        command =  f"start cmd /k \"cd /d C:\\Users\\Brian\\Documents\\elderWatchAI && activate && python data.py {ip} {userID} {phoneNumber}\""
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ip_started[ip] = True
        return jsonify({"ip": ip, "status": "RTSP URL is accessible and working"}), 200
    else:
        return jsonify({"ip": ip, "status": "RTSP URL may not be accessible or is not working"}), 200

@app.route('/gallery/<path:filename>', methods=['GET'])
async def get_gallery_image(filename):
    return await send_from_directory('./gallery', filename)


if __name__ == '__main__':
    local_ip = get_local_ip()  # Get the local IP address dynamically
    if local_ip:
        app.run(host=local_ip, debug=True)
    else:
        print("Failed to retrieve local IP address.")
