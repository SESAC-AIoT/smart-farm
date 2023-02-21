from flask import Flask, request, render_template, redirect, url_for, session, Response
from database import *
import numpy as np
import argparse, io, os, sys, datetime, cv2, torch

from PIL import Image
from time import sleep

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aiot'

collection = 'converea'  # device
d_id = '0.2v' # 'd000001'
create_device(d_id)

# (추가처리) 객체탐지를 위한 모델로드
path='../../secret/model/yolov5/models/yolov5s.pt'
model = torch.hub.load('ultralytics/yolov5', model='custom', path=path)

# device = torch.device('cuda')
# model.load_state_dict(torch.load(path, map_location="cuda:0"))  # 사용할 GPU 장치 번호 선택.
# model.to(device)  # CUDA Tensor 형 변환

# model.eval()
model.conf = 0.6
model.iou = 0.45


# (추가처리) 객체탐지를 위한 함수생성
def gen():
    cap=cv2.VideoCapture(0)
    while(cap.isOpened()):
        success, frame = cap.read()
        if success == True:
            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()
            img = Image.open(io.BytesIO(frame))
            results = model(img, size=640)
            update_detect(results)
            img = np.squeeze(results.render()) #RGB
            img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) #BGR
        else:
            break

        frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# (추가처리) 객체탐지 및 DB연동을 위한 함수생성
def update_detect(result):
    if 'Cats' in str(result):
        #print(str(result)[19:26])
        result_text = str(result)[19:26]
        detect_data = {'update_time': 'test', 'result': 'test'}
        detect_data['update_time'] = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        detect_data['result'] =  result_text
        doc_ref = db.collection(collection).document(d_id)
        doc = doc_ref.get()
        doc_ref.update({ 'detect': firestore.ArrayUnion([detect_data])})

# (추가처리) 객체탐지 웹앱 내 웹캠 생성
@app.route("/detect", methods=['POST', 'GET'])
def detect():
    device = db.collection(collection).document(d_id).get()
    session['d'] = device.to_dict()
    device = session['d']
    # all_list = device['detect']
    # all_list.reverse()
    # results = [all for all in all_list]
    results = 0
    return render_template('detect.html', times=results)










@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=5)
    session.modified = True

@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@app.route("/monitor/", methods=['POST', 'GET'])
def monitor():
    if 'd' not in session:
        session['d'] = get_device(collection, d_id)
    device = session['d']
    print(device['sensor'][-1]) # 가장 마지막(최근) 데이터
    m = get_monitor(device['sensor'][-1])
    g = get_growth((device['model'][-1]))
    return render_template('monitor.html', m = m, growth = g)

@app.route("/board/<type>", methods=['POST', 'GET'])
def board(type = 'temp'):
    if 'd' not in session:
        session['d'] = get_device(collection, d_id)
    device = session['d']
    sensors, times = get_board(device)
    values = get_chart(device, type)
    return render_template('board.html', sensors = sensors , times = times, values = values)

@app.route("/register", methods=['POST', 'GET'])
def register():

    return render_template('sregister.html')


@app.teardown_request
def shutdown_session(exception=None):
    pass

def get_growth(growth):
    if growth['growth_level'] == '0':
        return '0주차 씨앗'
    elif growth['growth_level'] == '1':
        return '1주차 새싹'
    elif growth['growth_level'] == '2':
        return '2주차 성장'
    elif growth['growth_level'] == '3':
        return '3주차 성숙'

def get_monitor(sensor):
    if sensor['water_level'] == 0:
        water_level = '부족상태'
    else:
        water_level = '유지상태'
    turbidity = -1120.4 * np.square(sensor['turbidity']) + 5742.3 * sensor['turbidity'] - 4352.9
    if 'fan' in sensor:
        if sensor['fan'] == 'on':
            fan = '회전'
        else:
            fan = '비회전'
    else:
        fan = '비회전'
    return {
        'temp' : '{}℃'.format(sensor['temp']),
        'humidity' : '{}%'.format(sensor['humidity']),
        'water_level' : '{}'.format(water_level),
        'ph' : '{}pH'.format(sensor['ph']),
        'turbidity' : '{:.2f}ntu'.format(turbidity),
        'fan' : '{}중'.format(fan),
    }

def get_board(device):
    cnt = len(device['sensor'])
    if cnt >20:
        cnt = 20
        sensors = device['sensor'][-20:] # 최근 20개
        sensors.reverse() # 최근 순으로 정렬
        timeline = [sensor['update_time'] for sensor in sensors][-20:]

    else:
        sensors = device['sensor']
        sensors.reverse()
        timeline = [sensor['update_time'] for sensor in sensors]

    #print(sensors)
    msensors = [get_monitor(sensor) for sensor in sensors]

    return msensors, timeline

def get_chart(device, type):
    cnt = len(device['sensor'])
    if cnt > 20:
        cnt = 20
        sensors = device['sensor'][-20:]
        sensors.reverse()
    else:
        sensors = device['sensor']
        sensors.reverse()

    if type == 'temp':
        return [sensor['temp'] for sensor in sensors]
    elif type == 'humidity':
        return [sensor['humidity'] for sensor in sensors]
    elif type == 'ph':
        return [sensor['ph'] for sensor in sensors]
    elif type == 'turbidity':
        return [sensor['turbidity'] for sensor in sensors]

if __name__ == '__main__':
    #(변경처리) 추가웹앱 적용을 위한 메인소스 수정
    # parser = argparse.ArgumentParser(description="Flask app exposing yolov5 models")
    # parser.add_argument("--port", default=5000, type=int, help="port number")
    # args = parser.parse_args()
    # app.run('0.0.0.0',port=args.port, debug=True) # port 9999

    app.run('0.0.0.0', 9999, debug=True, use_reloader=False)