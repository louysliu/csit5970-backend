from ultralytics import YOLO
import torch
import base64
import numpy as np
import cv2
from transmit import decode

def yolo_detect(job_id, frame_id, frame, model):
    if frame is None:
        return {"boxes": {}}

    results = model(frame, verbose=False)[0]
    names = results.names
    results_list = []
    for i in range(len(results.boxes.cls)):
        cls_i = names[int(results.boxes.cls[i])]
        xyxy = results.boxes.xyxy[i]
        conf = results.boxes.conf[i]
        results_list.append({"label": cls_i,"xyxy":xyxy.cpu().to(torch.int).tolist(), "conf": conf.item()})
    return {"boxes": results_list}

def yolo_test(frame, model):
    if frame is None:
        return {"boxes": []}
    results = model.predict(frame, verbose=False)[0]
    names = results.names
    results_list = []
    for i in range(len(results.boxes.cls)):
        cls_i = names[int(results.boxes.cls[i])]
        xyxy = results.boxes.xyxy[i]
        conf = results.boxes.conf[i]
        results_list.append({"label": cls_i,"xyxy":xyxy.cpu().to(torch.int).tolist(), "conf": conf.item()})
    return {"boxes": results_list}

if __name__ == "__main__":
    model = YOLO("yolo11n.pt")
    with open("test_msg.txt", "rb") as f:
        msg = f.read()
    job_id, frame_id, frame = decode(msg)
    boxes = yolo_detect(job_id, frame_id, frame, model)
    print(boxes)
    