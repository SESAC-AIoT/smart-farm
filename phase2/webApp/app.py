from flask import Flask, render_template,session, Response
from database import *
import numpy as np
import io, datetime, cv2, torch
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aiot'

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=5)
    session.modified = True

@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@app.route("/register", methods=['POST', 'GET'])
def register():
    return render_template('sregister.html')

@app.teardown_request
def shutdown_session(exception=None):
    pass

############### 센서데이터 모니터링/대시보드 페이지 #################

@app.route("/monitor/", methods=['POST', 'GET'])
def monitor():
    # 화면 리프레시 할 때 데이터 새로 고침을 위해 세션 미사용
    device = get_device(collection, d_id)
    print(device['sensor'][-1]) # 가장 마지막(최근) 데이터
    m = get_monitor(device['sensor'][-1])
    g = get_growth((device['model'][-1]))
    return render_template('monitor.html', m = m, growth = g)

@app.route("/board/<type>", methods=['POST', 'GET'])
def board(type = 'tp'):
    # 화면 리프레시 할 때 데이터 새로 고침을 위해 세션 미사용
    device = get_device(collection, d_id)
    sensors, times = get_board(device)
    values = get_chart(device, type)
    return render_template('board.html', sensors = sensors , times = times, values = values)

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
    if sensor['wl'] == 0:
        water_level = '부족상태'
    else:
        water_level = '유지상태'
    turbidity = -1120.4 * np.square(sensor['tb']) + 5742.3 * sensor['tb'] - 4352.9
    if 'fan' in sensor:
        if sensor['fan'] == 1 :
            fan = '회전'
        else:
            fan = '비회전'
    else:
        fan = '비회전'
    return {
        'temp' : '{}℃'.format(round(sensor['tp'],1)),
        'humidity' : '{}%'.format(round(sensor['hd'],1)),
        'water_level' : '{}'.format(water_level),
        'ph' : '{}pH'.format(round(sensor['ph'],1)),
        'turbidity' : '{:.2f}ntu'.format(round(turbidity,1)),
        'fan' : '{}중'.format(fan),
    }

# 그래프는 우측 최신 정렬
def get_board(device):
    cnt = len(device['sensor'])
    if cnt >20:
        sensors = device['sensor'][-20:] # 최근 20개
        timeline = [sensor['update_time'] for sensor in sensors]
    else:
        sensors = device['sensor']
        timeline = [sensor['update_time'] for sensor in sensors]

    msensors = [get_monitor(sensor) for sensor in sensors]


    return msensors, timeline

# 테이블은 상단 최신 정렬
def get_chart(device, type):
    cnt = len(device['sensor'])
    if cnt > 20:
        sensors = device['sensor'][-20:]
        sensors.reverse()
    else:
        sensors = device['sensor']
        sensors.reverse()

    if type == 'tp':
        return [round(sensor['tp'],1) for sensor in sensors]
    elif type == 'hd':
        return [round(sensor['hd'],1) for sensor in sensors]
    elif type == 'ph':
        return [round(sensor['ph'],1) for sensor in sensors]
    elif type == 'td':
        return [round(sensor['td'],1) for sensor in sensors]





############### 웹캠 객체탐지 페이지 #################

# 객체탐지를 위한 함수생성
def gen_frame():
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) # 웹캠 opencv 로딩 속도 개선 cap_dshow 다이렉트쇼
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

# 객체탐지 및 DB연동을 위한 함수생성
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

# 객체탐지 웹앱 내 웹캠 생성
@app.route("/detect", methods=['POST', 'GET'])
def detect():
    if 'd' not in session:
        session['d'] = get_device(collection, d_id)
    device = session['d']
    all_list = device['detect'][-20:]
    all_list.reverse()
    results = [all for all in all_list]
    return render_template('detect.html', times = results)

# 객체탐지 웹앱 내 웹캠 생성
@app.route('/webcam')
def webcam():
    return Response(gen_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


########################     실행     ########################
if __name__ == '__main__':

    # 데이터 베이스 연동
    collection = 'converea'  # device
    d_id = '0.4v'
    create_device(collection, d_id)

    # 객체탐지 모델 로드
    model_path = '../../secret/model/yolov5/models/yolov5s.pt'
    model = torch.hub.load('ultralytics/yolov5', model='custom', path=model_path)  # backend에서 cuda 자동 설정

    # 웹앱 실행
    app.run('0.0.0.0', debug=True, use_reloader=False)