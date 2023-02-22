import firebase_admin
from firebase_admin import credentials, firestore
from time import sleep
from datetime import datetime
from random import randint, uniform
import random

cred = credentials.Certificate('../../secret/nugunaaiot-maeng-1004a11a5af7.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

collection = 'converea'
d_id = '0.4v'
interval = 20  # sec
sensors = []

def create_device(d_id):
    # 도큐먼트 스넵샷에서 (get함수의 결과) .exists 필드로 id 유무 확인 가능
    doc_ref = db.collection(collection).document(d_id)
    doc = doc_ref.get()
    if doc.exists:
        return None
    else:
        doc_ref.set({
            'id': d_id,
            'is_running': False,
            'manufacture_date': datetime.now(),
            'detect': [],
            'model': [],
            'sensor': []
        })

def upload_data(d_id, sensor, detect, model):
    doc_ref = db.collection(collection).document(d_id)
    doc_ref.update({
        # 'is_running': True,  # 실행여부 bool 기본값 false
        'sensor': firestore.ArrayUnion([sensor]),
        'detect': firestore.ArrayUnion([detect]),
        'model': firestore.ArrayUnion([model])
    })


while True:
    try:
        sensor = {
            'update_time' : datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
            'fan' : str(random.choice([1,1,1,0,0])),
            'wl' : str(random.choice([1, 0, 1, 1, 0])),  # 수위 센서, 5개중 하나 선택
            'ph' : round(uniform(5, 8),1),  # ph센서
            'tb' : round(uniform(4, 8),1),  # 탁도 센서
            'tp' : round(uniform(15, 30),1),  # 온도 센서
            'hd' : round(uniform(40, 70),1)  # 습도 센서
        }
        detect = {
            'update_time': datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
            'result' : str(randint(1, 5)) + ' cat'
        }
        model = {
            'update_time': datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
            'growth_level': random.choice(['1', '2', '3', '4'])
        }

        print(sensor)
        print(detect)
        print(model)
        print('='*50)

        upload_data(d_id, sensor, detect, model) # fire store db에 추가
        sensors = []

        sleep(interval)

    except KeyboardInterrupt:
        print('중지됨')
        break



#### 실행 ####
create_device(d_id)