import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
# 스토리지 사용 및 파일삭제
from firebase_admin import storage
import os

# Use a service account.
PROJECT_ID = "nugunaaiot-maeng"
cred = credentials.Certificate(f'./static/secret/{PROJECT_ID}-1004a11a5af7.json')
app = firebase_admin.initialize_app(cred,  {'storageBucket': f"{PROJECT_ID}.appspot.com"})
db = firestore.client()


def get_device(collection, d_id):
    device = db.collection(collection).document(d_id).get()
    if device.exists:
        return device.to_dict()

def create_device(collection, d_id):
    doc_ref = db.collection(collection).document(d_id)
    if not doc_ref.get().exists:
        doc_ref.set({
            'upload_date': d_id,#  datetime.now()
            'upload_num': 0,
            'is_running': False,
            'manufacture_date': datetime.now(),
            'detect': [],
            'model': [],
            'sensor':[]
        })

# 스토리지 파일 업로드 소스
def upload_file(filename):
    bucket = storage.bucket()
    img_path = "./static/secret/output/" + filename
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename=img_path, content_type='image/jpeg')
    if os.path.exists(img_path):
        os.remove(img_path)