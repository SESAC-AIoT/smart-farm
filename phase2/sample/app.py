from flask import Flask, request, make_response, render_template, redirect, url_for, session
import cv2
import numpy as np
import datetime
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
from yolov3.utils import Load_Yolo_model, detect_realtime_image
from yolov3.configs import *


yolo = Load_Yolo_model()


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


def send_file_data(data, mimetype='image/jpeg', filename='output.jpg'):

    response = make_response(data)
    response.headers.set('Content-Type', mimetype)
    response.headers.set('Content-Disposition', 'attachment', filename=filename)

    return response


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        fs = request.files.get('snap')
        if fs:
            img = cv2.imdecode(np.frombuffer(fs.read(), np.uint8), cv2.IMREAD_UNCHANGED)
            img = detect_realtime_image(yolo, img)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            ret, buf = cv2.imencode('.jpg', img)

            return send_file_data(buf.tobytes())
        else:
            return 'You forgot Snap!'

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)