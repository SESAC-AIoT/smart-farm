import cv2
import numpy as np
from time import sleep
from datetime import datetime
from collections import Counter

import os
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

import tensorflow as tf
growth_model= tf.saved_model.load('./model/converea')

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=800,
    display_height=480,
    framerate= 30,
    flip_method= 0,
):
    return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def show():
    num = 0
    window_title = 'converea'
    video_capture = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if video_capture.isOpened():
        try:
            window_handle = cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
            
            while True:
                num += 1
                ret_val, frame = video_capture.read()
                if frame is None:
                    print('empty frame, reboot please', num)
                    sleep(1)
                else:
                    if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                        cv2.imshow(window_title, frame)
                        
                        try : 
                            #img = cv2.imread(removed)
                            img = frame[0:460, 80:560]
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            img = cv2.resize(img, (150,150)) / 255.0 # inputµ¥ÀÌÅÍ¸¦ ½ºÄÉÀÏ¸µÇß±â ¶§¹®¿¡ ¿¹ÃøÇÒ ¶§¿¡µµ ½ºÄÉÀÏ¸µ ÇØ¾ßÇÔ
                            
                            pred = growth_model([img])
                            #print(pred)
                            growth_level = str(np.argmax(pred, axis=1)[0])
                            print(num, ' growth level', growth_level)

                        except Exception as e:
                            print(e)
                            break
                    else:
                        print('????')
                        
                # firestore upload
                upt = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
                gl = Counter(growth_level).most_common(1)[0][0]
                result = {'growth_level' : gl,
                          'update_time' : upt}
                #model_result.append([gl, upt])
                print(result)
                upload_growth(result) #  [('cherry', 4)] 
                
                keyCode = cv2.waitKey(10) & 0xFF
                if keyCode == 27 or keyCode == ord('q'):
                    video_capture.release()
                    cv2.destroyAllWindows()
                    doc_ref.update({'is_running': False})
                    sleep(1)
                    break
                
                sleep(interval)
            # while loop finish
            
        finally:
            doc_ref.update({'is_running': False})
            video_capture.release()
            cv2.destroyAllWindows()
            sleep(1)
    else:
        doc_ref.update({'is_running': False})
        print("Error: Unable to open camera")
        




if __name__ == "__main__":
    
    ######## fire base ########
    import firebase_admin
    from firebase_admin import credentials, firestore
    # option
    db_collection = 'converea' # database collection id
    db_id = '0.2v' # database document id
    db_key = 'nugunaaiot-maeng-1004a11a5af7.json'
    # Cloud Database : firestore
    cred = credentials.Certificate(f'../../secret/{db_key}')
    app = firebase_admin.initialize_app(cred)
    db = firestore.client()

    def create_device(db_id):
        doc_ref = db.collection(db_collection).document(db_id)
        doc = doc_ref.get()
        if doc.exists :
            pass
        else:
            doc_ref.set({
                'id': db_id,
                 'is_running': True,
                 'manufacture_date': datetime.now(),
                 'model':[],
                 'sensor':[]
            })        

    def upload_growth(result):
        #doc_ref = db.collection(db_collection).document(db_id)
        doc_ref.update({'is_running': True, 'model': firestore.ArrayUnion([result])})
        print('data upload')
    
    create_device(db_id)
    doc_ref = db.collection(db_collection).document(db_id)
    
    # option
    interval = 2 # sec
    
    while True :    
        show()
        