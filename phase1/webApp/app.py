from flask import Flask, request, make_response, render_template, redirect, url_for, session, Response
from database import *
import numpy as np
import argparse, io, os, sys, datetime, cv2, torch
# os.environ['CUDA_VISIBLE_DEVICES'] = '0'
from PIL import Image
from time import sleep


app = Flask(__name__)
app.config['SECRET_KEY'] = 'aiot'

create_device(d_id)

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
    # if 'd' not in session:
    #     session['d'] = get_device(collection, d_id)
    # device = session['d']
    # 화면 리프레시 할 때 데이터 새로 고침을 위해 세션 미사용
    device = get_device(collection, d_id)
    print(device['sensor'][-1]) # 가장 마지막(최근) 데이터
    m = get_monitor(device['sensor'][-1])
    g = get_growth((device['model'][-1]))
    return render_template('monitor.html', m = m, growth = g)

@app.route("/board/<type>", methods=['POST', 'GET'])
def board(type = 'temp'):
    # if 'd' not in session:
    #     session['d'] = get_device(collection, d_id)
    # device = session['d']
    # 화면 리프레시 할 때 데이터 새로 고침을 위해 세션 미사용
    device = get_device(collection, d_id)
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
        # sensors.reverse() # 최근 순으로 정렬
        timeline = [sensor['update_time'] for sensor in sensors]

    else:
        sensors = device['sensor']
        # sensors.reverse()
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





############### 웹캠 객체탐지 페이지 #################

# (추가처리) 객체탐지를 위한 모델로드
path='../../secret/model/yolov5/models/yolov5s.pt'
model = torch.hub.load('ultralytics/yolov5', model='custom', path =path) # cuda를 backend에서 자동으로 잡음
# model.eval()
# model.conf = 0.6
# model.iou = 0.45

# (추가처리) 객체탐지를 위한 함수생성
def gen_frame():
    cam = cv2.VideoCapture(0)
    while(cam.isOpened()):
        success, frame = cam.read()
        if success == True:
            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()
            img = Image.open(io.BytesIO(frame))

            results = model(img, size=640)
            upload_detect(str(results))

            img = np.squeeze(results.render()) #RGB
            img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) #BGR
        else:
            break

        frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# (추가처리) 객체탐지 및 DB연동을 위한 함수생성
def upload_detect(results):
    if 'cat' in results:
        # print(str(results).split())
        detect_log = str(results)[19:25]
        # print(str(results)[19:26])
        detect_data = {'update_time': 'test', 'result': 'test'}
        detect_data['update_time'] = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        detect_data['result'] = detect_log
        doc_ref = db.collection(collection).document(d_id)
        doc_ref.update({'detect': firestore.ArrayUnion([detect_data])})

# (추가처리) 객체탐지 웹앱 내 웹캠 생성
@app.route("/detect", methods=['POST', 'GET'])
def detect():
    if 'd' not in session:
        session['d'] = get_device(collection, d_id)
    device = session['d']
    all_list = device['detect'][-20:]
    all_list.reverse()
    results = [all for all in all_list]
    return render_template('detect.html', times = results)

# (추가처리) 객체탐지 웹앱 내 웹캠 생성
@app.route('/webcam')
def webcam():
    return Response(gen_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')




if __name__ == '__main__':
    #(변경처리) 추가웹앱 적용을 위한 메인소스 수정
    parser = argparse.ArgumentParser(description="Flask app exposing yolov5 models")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()
    app.run('0.0.0.0',port=args.port, debug=True, use_reloader=False) # port 9999