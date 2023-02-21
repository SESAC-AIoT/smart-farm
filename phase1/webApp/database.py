import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

# Use a service account.
cred = credentials.Certificate('../../secret/nugunaaiot-maeng-1004a11a5af7.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()


def get_device(collection, d_id):
    device = db.collection(collection).document(d_id).get()
    if device.exists:
        return device.to_dict()

