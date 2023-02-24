from flask import Flask, request, render_template, session, Response
from database import *
import numpy as np
from datetime import datetime, timedelta
import io, cv2, torch, base64
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aiot'

# @app.before_request
# def before_request():
#     session.permanent = True
#     app.permanent_session_lifetime = timedelta(minutes=5)
#     session.modified = True

# @app.teardown_request
# def shutdown_session(exception=None):
#     pass

@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template('index.html', login_status=login_status, product_name=collection, product_id = d_id)


##### login ####
@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        global login_status, collection, d_id
        collection = request.form['name']
        d_id = request.form['d_id']
        if get_device(collection, d_id) is False:
            return render_template('login.html', alert=True)
        else:
            login_status = True
            return render_template('index.html', login_status=login_status, product_name=collection, product_id = d_id)
    return render_template('login.html')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    global login_status
    login_status = False
    collection = False
    d_id = False
    # session.pop('logged_in', None)
    return render_template('index.html', login_status=login_status, product_name=collection, product_id = d_id)


############### 센서데이터 모니터링/대시보드 페이지 #################

@app.route("/monitor/", methods=['POST', 'GET'])
def monitor():
    if login_status :
        # 화면 리프레시 할 때 데이터 새로 고침을 위해 세션 미사용
        device = get_device(collection, d_id)
        m = get_monitor(device['sensor'][-1])
        g = get_growth((device['model'][-1]))
        return render_template('monitor.html', m = m, growth = g, login_status=login_status, product_name=collection, product_id = d_id)
    else:
        return render_template('login.html')

@app.route("/board/<type>", methods=['POST', 'GET'])
def board(type):
    if login_status :
        # 화면 리프레시 할 때 데이터 새로 고침을 위해 세션 미사용
        device = get_device(collection, d_id)
        sensors, times = get_board(device)
        values = get_chart(device, type)
        return render_template('board.html', sensors = sensors , times = times, values = values, login_status=login_status, product_name=collection, product_id = d_id)
    else:
        return render_template('login.html')

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
        'tp' : '{}℃'.format(round(sensor['tp'],1)),
        'hd' : '{}%'.format(round(sensor['hd'],1)),
        'wl' : '{}'.format(water_level),
        'ph' : '{}pH'.format(round(sensor['ph'],1)),
        'tb' : '{:.2f}ntu'.format(round(turbidity,1)),
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
        return [sensor['tp'] for sensor in sensors]
    elif type == 'hd':
        return [sensor['hd'] for sensor in sensors]
    elif type == 'ph':
        return [sensor['ph'] for sensor in sensors]
    elif type == 'tb':
        return [sensor['tb'] for sensor in sensors]





############### 웹캠 객체탐지관련 웹페이지 및 함수#################

# 탐지 대시보드 웹페이지
@app.route("/detect_webcam", methods=['POST', 'GET'])
def detect_webcam():
    return render_template('detect_webcam.html')



# 객체탐지 테이블 웹페이지
@app.route("/detect_table", methods=['POST', 'GET'])
def detect_table():
    device = get_device(collection, d_id)
    all_list = device['detect'][-20:]
    all_list.reverse()
    results = [all for all in all_list]
    return render_template('detect_table.html', data = results)

# 웹캠 실행
@app.route('/webcam')
def webcam():
    return Response(webcam_gen_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# 웹캠 opencv 실행 및 yolo 탐지
def webcam_gen_frame():
    input = 'webcam'
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) # 웹캠 opencv 로딩 속도 개선 cap_dshow 다이렉트쇼
    while(cam.isOpened()):
        success, frame = cam.read()
        if success == True:
            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()
            img = Image.open(io.BytesIO(frame))

            pred = model(img, size=640)

            # preprocessing & upload
            filename = file_naming(input, filename='realtime')
            upload_detect(pred, input='webcam', filename=filename)

            img = np.squeeze(pred.render())  # RGB
            img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            file_save(pred, img_BGR, filename)

        else:
            break

        frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# 객체탐지 DB 생성/업로드
def upload_detect(pred, input, filename=None):
    obj_count = pred_preprocessing(pred)
    if obj_count > 0:
        detect_data = {'update_time': datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
                       'class': detect_obj,
                       'count': obj_count,
                       'input': input,
                       'filename': filename
                       }
        doc_ref = db.collection(collection).document(d_id)
        doc_ref.update({'detect': firestore.ArrayUnion([detect_data])})

# 객체 탐지 갯수 리턴
def pred_preprocessing(pred) :
    pred_pd = pred.pandas().xyxy[0]
    obj_count = sum(pred_pd['name'] == detect_obj) # true length
    return obj_count

def file_naming(input, filename=None):
    filename = '_'.join([datetime.now().strftime("%Y_%m_%d_%H_%M_%S"), input, filename])+'.jpg'
    return filename

def file_save(pred, img, filename): # 탐지완료 파일 백업용
    if detect_obj in str(pred):
        img_path = "./static/secret/output/" + filename
        cv2.imwrite(img_path, img)
        # 스토리지 업로드를 위한 함수 호출
        upload_file(filename)

############### 사용자파일 객체탐지관련 웹페이지 및 함수 #################

# 사용자파일 객체탐지 웹앱 생성
@app.route("/detect_userfile", methods=['PgitOST', 'GET'])
def detect_userfile():
    if login_status:
        return render_template('detect_userfile.html', image=None, filename=None, login_status=login_status, product_name=collection, product_id = d_id)
    else:
        return render_template('login.html')




# 사용자파일 객체탐지 웹앱 내 업로드 기능 생성_결과DB적재 및 이미지파일 저장
@app.route('/file_upload', methods=['GET', 'POST'])
def file_upload():
    input = 'userfile'
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'You forgot Snap!'
        fs = request.files.get('file')
        filename = fs.filename

        if 'jpg' in filename:
            img = cv2.imdecode(np.frombuffer(fs.read(), np.uint8), cv2.IMREAD_UNCHANGED)

            # 예측결과 업로드
            pred = model(img, size=640)

            # preprocessing & upload
            filename = file_naming(input, filename.split('.')[0])
            upload_detect(pred, input=input, filename=filename)

            file_save(pred, img, filename)

            # 웹에서 디스플레이 되도록 인코딩
            img = np.squeeze(pred.render())  # RGB
            ret, buf = cv2.imencode('.jpg', img)
            file_save(pred, img, filename)
            b64_img = base64.b64encode(buf).decode('utf-8')

            return render_template('detect_userfile.html', image = b64_img , filename=None)

        else:
            return 'You forgot Snap!'

    return '빈페이지'

########################     실행     ########################
if __name__ == '__main__':

    # fake session
    login_status = False
    alert = False


    # 데이터 베이스 연동

    # collection = 'catFarm'  # device
    # d_id = datetime.now().strftime("%Y.%m.%d")
    # create_device(collection, d_id)
    collection = False
    d_id = False

    # 객체탐지 모델 로드
    detect_obj = 'cat'
    model_path = './static/secret/model/yolov5l.pt'
    model = torch.hub.load('ultralytics/yolov5', model='custom', path=model_path)  # backend에서 cuda 자동 설정
    # model = torch.hub.load('ultralytics/yolov5', 'yolov5l'
    model.conf = 0.6

    # 웹앱 실행
    # app.run('0.0.0.0', debug=True, use_reloader=False)
    app.run(debug=True, use_reloader=False)