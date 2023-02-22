from time import sleep
from datetime import datetime
from dateutil.relativedelta import relativedelta
from random import randint, uniform
import random, sys
from database import *

def upload_data(d_id, sensor, detect, model, upload_num):
    doc_ref = db.collection(collection).document(d_id)
    data = {
        'is_running': True,  # 실행여부 bool 기본값 false
        'upload_date': d_id,
        'upload_num': upload_num,
        'sensor': firestore.ArrayUnion([sensor]),
        'detect': firestore.ArrayUnion([detect]),
        'model': firestore.ArrayUnion([model])
    }
    doc_ref.update(data)

    # print('b', sys.getsizeof(data)) 업로드 데이터 용량 체크
    # print('kb', sys.getsizeof(data) / 1000)
    # print('mb', sys.getsizeof(data) / 1000 / 1000)


def gen_run(d_id, upload_num):
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

    upload_data(d_id, sensor, detect, model, upload_num) # fire store db에 추가


def did_gen(d_id) :
    device = get_device(collection, d_id)
    last_did = device['upload_date']
    last_num = device['upload_num']
    day1 = relativedelta(days=1)

    # 전송 횟수와 오늘 날짜 비교
    if last_num >= upload_limit and last_did == d_id: # 오늘날짜, 전송횟수 초과
        print('gg')
        d_id = (datetime.now() + day1).strftime("%Y.%m.%d") # 다음날로 변경
        upload_num = 0
        return d_id, upload_num

    elif last_num < upload_limit and last_did == d_id: # 오늘 날짜, 전송횟수 남음
        print('4')
        return last_did, last_num

    else : # 날짜가 매칭되지 않을 경우
        print('5')
        upload_num = 0
        return d_id, upload_num
    print('6')
    return last_did, last_num


#### 실행 ####
if __name__ == '__main__':
    collection = 'catFarm'
    interval = 20  # 20sec
    upload_limit = 3000

    d_id_default = datetime.now().strftime("%Y.%m.%d")
    create_device(collection, d_id_default)
    d_id, upload_num = did_gen(d_id_default)


    # GCP firebase firestore free documents write 20,000/day, documents date limit 1mb/document
    # interval 20sec  -> 4,320/day

    # data size 0.232kb -> x4 = 1kb -> x4000 = 1mb  -> 20초 기준 일내 doc용량 초과(yolo 데이터 미포함)
    # 여유있게 약 4천회 마다 d_id change
    # 도큐먼트 삭제 : db.collection(u'cities').document(u'DC').delete()
    while True :
        try:
            if upload_num >= upload_limit : # 최초 실행 or 전송 횟수 초과시 신규 did 생성
                d_id, upload_num = did_gen(d_id)
                create_device(collection, d_id)

            sensors = []
            upload_num += 1
            gen_run(d_id, upload_num)
            print(d_id, upload_num, 'upload success')
            print('=' * 50)
            sleep(interval)

        except :
            doc_ref = db.collection(collection).document(d_id)
            data = {
                'is_running': False,
                'upload_date': d_id,
                'upload_num': upload_num,
            }
            doc_ref.update(data)

            print('중지됨')
            break