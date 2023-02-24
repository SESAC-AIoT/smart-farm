import RPi.GPIO as GPIO
import spidev
import board
import adafruit_dht
import digitalio
from time import sleep
from datetime import datetime

GPIO.setmode(GPIO.BCM)
WL = 22
GPIO.setup(WL, GPIO.IN)

# Initial the dht device, with data pin connected to:
# DHT_pin = digitalio.DigitalInOut(board.D27)
dhtDevice = adafruit_dht.DHT22(board.D27, False)

print("Digital IO ok!")





sample = 10

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000


def temp_read():
    
    temperature_c = dhtDevice.temperature
#     temperature_f = temperature_c * (9 / 5) + 32
    humidity = dhtDevice.humidity
    if temperature_c is None:
        temperature_c = 0
    elif humidity is None:
        humidity = 0
    return temperature_c, humidity


def water_level_read_digital():
    water_level = GPIO.input(WL)
    if water_level in [1,0]:
        return water_level
    else:
        raise Exception()


def adc_read(channel):
    r = spi.xfer2([1, (0x08 + channel) << 4, 0])
    adc_out = ((r[1] & 0x03) << 8) + r[2]
    return adc_out


def phSensor_read(channel):
    sampleValue = []
    for i in range(sample):
        adc = adc_read(channel)
        sampleValue.append(adc)

    sampleValue.sort()

    avg = 0
    for i in range(2, 8):
        avg += sampleValue[i]

    phValue = float(avg * 5 / 1024 / 6)
    phValue = float(3.5 * phValue)
    return phValue


def turbidity_read(channel):
    sampleValue = []
    for i in range(sample):
        adc = adc_read(channel)
        voltage = adc * (5.0 / 1024.0)
        sampleValue.append(voltage)

    sampleValue.sort() # 왜 정렬하지?
    avg = 0
    for i in range(2, 8):
        avg += sampleValue[i]
    voltage = avg / 6
    return voltage



def avg_sensor(sensors):
    s_len = len(sensors)
    sd = {'water_level': 0,
          'ph': 0,
          'turbidity': 0,
          'temp': 0,
          'humidity': 0,
          'update_time' : 0}
    
    for s in sensors:
        print(s)
        print(s[0])

        sd['water_level'] += s[0]
        sd['ph'] += s[1]
        sd['turbidity'] += s[2]
        sd['temp'] += s[3]
        sd['humidity'] += s[4]


    if sd['water_level'] >= s_len / 2:
        sd['water_level'] = 1
    else:
        sd['water_level'] = 0

    sd['ph'] = round(sd['ph'] / s_len , 1)
    sd['turbidity'] = round(sd['turbidity'] / s_len, 1)
    sd['temp'] = round(sd['temp'] / s_len, 1)
    sd['humidity'] = round(sd['humidity'] / s_len, 1)
    sd['update_time'] = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    return sd

#  fancode

# fan
fan_ch = 5
GPIO.setup(fan_ch, GPIO.OUT)
# sensor input data is GPIO.IN, electric output is GPIO.OUT

def fan(tp):

    if tp >= 24.0:
        GPIO.output(fan_ch, GPIO.LOW) # 
        print('fan off')
    else:
        GPIO.output(fan_ch, GPIO.HIGH)
        print('fan on')



# excute
if __name__ == '__main__':
    
    ######## fire base ########
    import firebase_admin
    from firebase_admin import credentials, firestore
    # option
    db_collection = 'converea' # database collection id
    db_id = '0.3v' # database document id
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

    def upload_sensor(sensor):
        #doc_ref = db.collection(db_collection).document(db_id)
        doc_ref.update({'is_running': True,'sensor': firestore.ArrayUnion([sensor])})
        print('data upload')
    
    create_device(db_id)
    doc_ref = db.collection(db_collection).document(db_id)    

    # option
    interval = 2 # sec
    sensors = []

        
    
    # store to database
    while True:
        try:
            wl = water_level_read_digital()
            ph = phSensor_read(1)
            tb = turbidity_read(17)
            tp, hd = temp_read()
            upt = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
                 
            print('update_time = {}, waterLevel ={}, ph = {}, turbidity= {}, temp = {}, humidity = {}'.format(upt, wl, ph, tb, tp, hd))
            sensors.append([wl, ph, tb, tp, hd, upt])

            print(len(sensors))
            
            if len(sensors) >= 10:
                sensor_data = avg_sensor(sensors)
                upload_sensor(sensor_data)
                fan(sensor_data['temp'])
                print(sensor_data)
                print('='*50)
                sensors = []
            
            sleep(interval)
            
        except KeyboardInterrupt:
            GPIO.cleanup()
            dhtDevice.exit()
            doc_ref.update({'is_running': False})

        except RuntimeError:
            print('runtime error pass')
            pass 
