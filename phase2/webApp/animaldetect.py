import numpy as np
import tensorflow as tf
from tensorflow import keras
import cv2
import numpy as np
import torch
from PIL import Image
import argparse, io, os, sys, datetime, cv2, torch

#model = keras.models.load_model("./model/Model_animals.h5")
path='../../secret/model/yolov5/models/yolov5s.pt'
model = torch.hub.load('ultralytics/yolov5', model='custom', path =path) # cuda를 backend에서 자동으로 잡음
# model.eval()
model.conf = 0.6
model.iou = 0.45
#model(np.zeros((1,150,150,3)))

#declass = {0:'butterfly', 1:'cat', 2:'chicken', 3:'cow', 4:'dog', 5:'elephant', 6:'horse', 7:'sheep', 8: 'spider', 9:'squirre'}

def detect_image(image):
    inp = image
    out = model(inp)
    outs = str(out)
    print(outs)
    ind = "미탐지"
    if 'cat' in outs:
        detect_log = str(outs)[19:26]
        ind = detect_log
        print(ind)
    return ind

def detect_batch(images):
    inp = np.asarray(images) / 255.0
    #out = model.predict(inp)
    out = model(inp)
    print(out)
    inds = np.argmax(out, axis=1)
    print(inds)
    #classes = []
    #for i, ind in enumerate(inds):
    #    if out[i][ind] < 0.4:
    #        classes.append('none')
    #    else:
    #        classes.append(declass[ind])
    #print(classes)
    #return classes
    return inds