from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('./elderwatch.json')  # Replace with your service account key file
firebase_admin.initialize_app(cred)
db = firestore.client()

# Endpoint to retrieve users
@app.route('/users', methods=['GET'])
def get_users():
    users_ref = db.collection('users')
    users = [doc.to_dict() for doc in users_ref.stream()]
    return jsonify({'users': users})

if __name__ == '__main__':
    app.run(debug=True)
