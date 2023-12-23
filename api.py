from flask import Flask, jsonify, request
from scapy.all import *
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('./elderwatch.json')  # Replace with your service account key file
firebase_admin.initialize_app(cred)
db = firestore.client()

def is_camera(ip_address):
    packet = IP(dst=ip_address) / TCP(dport=554, flags='S')  # RTSP port 554 used by many cameras

    # Sending packet and waiting for response
    response = sr1(packet, timeout=2, verbose=0)

    if response is not None and response.haslayer(TCP):
        if response[TCP].flags == 18:  # Checking for a TCP response indicating an open port
            return True

    return False

# Endpoint to retrieve users
@app.route('/users', methods=['GET'])
def get_users():
    users_ref = db.collection('users')
    users = [doc.to_dict() for doc in users_ref.stream()]
    return jsonify({'users': users})


@app.route("/ping", methods=['GET'])
def ping_ip():
    ip = request.args.get('ip')  # Get the 'ip' parameter from the request query string
    if not ip:
        return jsonify({"message": "IP address is missing in the request parameters"}), 400

    print(f"Pinging IP: {ip}")

    is_camera_ip = is_camera(ip)

    if is_camera_ip:
        return jsonify({"message": f"The IP address {ip} is associated with a camera."}), 200
    else:
        return jsonify({"message": f"The IP address {ip} may not be a camera or is not responding on the RTSP port."}), 200


if __name__ == '__main__':
    app.run(debug=True)
