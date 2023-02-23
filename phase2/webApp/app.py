from flask import Flask, make_response, request, render_template, session, Response, send_file
from database import *
import numpy as np
from datetime import datetime, timedelta
import io, cv2, torch
from PIL import Image

from animalcnn import predict_image, predict_batch
import tempfile, base64
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aiot'

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)
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
def board(type):
    # 화면 리프레시 할 때 데이터 새로 고침을 위해 세션 미사용
    device = get_device(collection, d_id)
    sensors, times = get_board(device)
    values = get_chart(device, type)
    print(values)
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
@app.route("/detect", methods=['POST', 'GET'])
def detect():
    # if 'd' not in session:
    #     session['d'] = get_device(collection, d_id)
    # device = session['d']
    # all_list = device['detect'][-20:]
    # all_list.reverse()
    # results = [all for all in all_list]
    # return render_template('detect.html', times = results)
    return render_template('detect.html')

# 객체탐지 테이블 웹페이지
@app.route("/detect_table", methods=['POST', 'GET'])
def detect_table():
    # device = db.collection(collection).document(d_id).get()
    # session['d'] = device.to_dict()
    # device = session['d']
    device = get_device(collection, d_id)
    all_list = device['detect'][-20:]
    all_list.reverse()
    results = [all for all in all_list]
    return render_template('detect_table.html', times = results)

# 웹캠 실행
@app.route('/webcam')
def webcam():
    return Response(gen_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# 웹캠 opencv 실행 및 yolo 탐지
def gen_frame():
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) # 웹캠 opencv 로딩 속도 개선 cap_dshow 다이렉트쇼
    while(cam.isOpened()):
        success, frame = cam.read()
        if success == True:
            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()
            img = Image.open(io.BytesIO(frame))

            results = model(img, size=640)
            upload_detect(results)

            img = np.squeeze(results.render()) #RGB
            img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) #BGR
        else:
            break

        frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# 객체탐지 DB 생성 및 업로드
def upload_detect(results):
    results_raw = results
    results = str(results)
    if 'cat' in results:
        # print(str(results).split())
        # print(str(results)[19:26])
        detect_log = results[19:26]
        detect_data = {'update_time': datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
                       'class' : '고양이',
                       'count' : detect_log[0],# [0:1]
                       'input' : '웹캠',
                       'filename' : datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + "_webcam_image.jpg"
                       }
        doc_ref = db.collection(collection).document(d_id)
        doc_ref.update({'detect': firestore.ArrayUnion([detect_data])})

        # img = np.squeeze(results_raw.render())  # RGB
        # img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # BGR
        #
        # filename= str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) + "_webcam_image.jpg"
        # img_path = "./static/" +filename
        # cv2.imwrite(img_path, img_BGR)



############### 사용자파일 객체탐지관련 웹페이지 및 함수 #################

# 사용자파일 객체탐지 웹앱 생성
@app.route("/detect_upload", methods=['POST', 'GET'])
def detect_upload():
    return render_template('detect_upload.html', image=None, filename=None)

# 사용자파일 객체탐지 웹앱 내 업로드 기능 생성_결과DB적재 및 이미지파일 저장
@app.route('/file_upload', methods=['GET', 'POST'])
def file_upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            # flash('No file part')
            return 'You forgot Snap!'
        fs = request.files.get('file')
        # print(fs.read(), file=sys.stderr)
        if 'jpg' in fs.filename:
            img = cv2.imdecode(np.frombuffer(fs.read(), np.uint8), cv2.IMREAD_UNCHANGED)
            pred = predict_image(img)
            ret, buf = cv2.imencode('.jpeg', img)
            b64_img = base64.b64encode(buf).decode('utf-8')

            # 데이터베이스 추가 (고양이 예측시)
            if pred == "cat":
                detect_data = {'update_time': 'yyyy.mm.dd hh:mm:ss'}
                detect_data['update_time'] = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
                detect_data['class'] = "고양이"
                detect_data['count'] = 1
                detect_data['input'] = "사용자파일_이미지"
                detect_data["filename"] = str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) + "_userfile_image.jpg"
                doc_ref = db.collection(collection).document(d_id)
                doc_ref.update({'detect': firestore.ArrayUnion([detect_data])})

                img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # BGR
                filename = str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) + "_userfile_image.jpg"
                img_path = "./static/" + filename
                cv2.imwrite(img_path, img_BGR)

            return render_template('detect_upload.html', image=b64_img, predict=pred, filename=None)

        # elif 'mp4' in fs.filename:
        #     with tempfile.TemporaryDirectory() as td:
        #         temp_filename = Path(td) / 'uploaded_video'
        #         fs.save(temp_filename)
        #         vidcap = cv2.VideoCapture(str(temp_filename))
        #         filename = batch_frames(vidcap)
        #
        #         # 데이터베이스 추가
        #         if pred == "cat":
        #             detect_data = {'update_time': 'yyyy.mm.dd hh:mm:ss'}
        #             detect_data['update_time'] = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        #             detect_data['class'] = "고양이"
        #             detect_data['count'] = 1
        #             detect_data['input'] = "사용자파일_영상"
        #             detect_data["filename"] = str(
        #                 datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) + "_userfile_mp4.jpg"
        #             doc_ref = db.collection(collection).document(d_id)
        #             doc_ref.update({'detect': firestore.ArrayUnion([detect_data])})
        #
        #             img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # BGR
        #             filename = str(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) + "_userfile_mp4.jpg"
        #             img_path = "./static/" + filename
        #             cv2.imwrite(img_path, img_BGR)
        #
        #         return send_file('./static/{}'.format(filename), download_name=filename, as_attachment=True)

        else:
            return 'You forgot Snap!'

    return '빈페이지'



# 파일 교환 관련 함수(송신)
def send_file_data(data, mimetype='image/jpeg', filename='output.jpg'):
    response = make_response(data)
    response.headers.set('Content-Type', mimetype)
    response.headers.set('Content-Disposition', 'attachment', filename=filename)
    return response

# 파일 교환 관련 함수(객체탐지_단일이미지)
def gen_frames(cap):
    w = round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    filename = 'pred_video.mp4'
    out = cv2.VideoWriter('./static/' + filename, fourcc, 30, (w, h))
    cnt = 0
    while True:
        success, frame = cap.read()  # read the camera frame
        if not success:
            break
        cnt += 1
        if cnt % 3 == 0:
            continue
        pred = predict_image(frame)
        font = cv2.FONT_HERSHEY_SIMPLEX
        org = (300, 100)
        fontScale = 1
        color = (255, 0, 0)
        thickness = 2
        frame = cv2.putText(frame, pred, org, font,
                            fontScale, color, thickness, cv2.LINE_AA)
        out.write(frame)
    cap.release()
    out.release()
    return filename


# 파일 교환 관련 함수(객체탐지_영상이미지)
def batch_frames(cap):
    # 여러프레임 한번에 예측 (영상화 시킬때 사용)
    w = round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    filename = 'pred_video.mp4'
    out = cv2.VideoWriter('./static/'+filename, fourcc, 30, (w, h))
    cnt = 0
    origins = []
    images = []
    while True:
      success, frame = cap.read()  # read the camera frame
      if not success:
          # del session['temp_filename']
          break
      cnt+=1
      if cnt % 3 ==0:
          continue
      im = cv2.resize(frame, (150, 150), interpolation=cv2.INTER_AREA)
      origins.append(frame.copy())
      images.append(im)
      if len(images) > 10:
          preds = predict_batch(images)
          for ori, pred in zip(origins, preds):
              font = cv2.FONT_HERSHEY_SIMPLEX
              org = (150, 150)
              fontScale = 1
              color = (255, 0, 0)
              thickness = 2
              frame = cv2.putText(ori, pred, org, font,
                                  fontScale, color, thickness, cv2.LINE_AA)
              out.write(frame)
          images = []
          origins = []
    cap.release()
    out.release()
    return filename





########################     실행     ########################
if __name__ == '__main__':

    # 데이터 베이스 연동
    collection = 'catFarm'  # device
    d_id = datetime.now().strftime("%Y.%m.%d")
    create_device(collection, d_id)

    # 객체탐지 모델 로드
    model_path = '../../secret/model/yolov5/models/yolov5s.pt'
    model = torch.hub.load('ultralytics/yolov5', model='custom', path=model_path)  # backend에서 cuda 자동 설정

    # 웹앱 실행
    app.run('0.0.0.0', debug=True, use_reloader=False)