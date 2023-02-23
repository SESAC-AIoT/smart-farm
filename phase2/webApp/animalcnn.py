import numpy as np
import tensorflow as tf
from tensorflow import keras
import cv2
import numpy as np

model = keras.models.load_model("../../secret/model/Model_animals.h5")
model.predict(np.zeros((1,150,150,3)))

declass = {0:'butterfly', 1:'cat', 2:'chicken', 3:'cow', 4:'dog', 5:'elephant', 6:'horse', 7:'sheep', 8: 'spider', 9:'squirre'}

def predict_image(image):
    im = cv2.resize(image, (150, 150), interpolation=cv2.INTER_AREA)
    print(im.shape)
    inp = np.asarray(im).reshape((1,150,150,3)) / 255.0
    out = model.predict(inp)
    print(out)
    ind = np.argmax(out)
    print(ind)
    if out[0][ind] < 0.4:
        return '판별 불가'
    return declass[ind]

def predict_batch(images):

    inp = np.asarray(images) / 255.0
    out = model.predict(inp)
    print(out)
    inds = np.argmax(out, axis=1)
    print(inds)
    classes = []
    for i, ind in enumerate(inds):
        if out[i][ind] < 0.4:
            classes.append('none')
        else:
            classes.append(declass[ind])
    print(classes)
    return classes