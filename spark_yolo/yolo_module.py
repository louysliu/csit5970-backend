from ultralytics import YOLO
import torch
import base64
import numpy as np
import cv2

model = YOLO("yolo11n.pt")

def decode_base64_image(b64_str):
    img_data = base64.b64decode(b64_str)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

def yolo_detect(video_id, frame_id, frame_b64, model):
    img = decode_base64_image(frame_b64)
    if img is None:
        return f"{video_id},{frame_id},ERROR"

    results = model(img)
    result_strs = []
    for *box, conf, cls in results.xyxy[0].tolist():
        label = model.names[int(cls)]
        result_strs.append(f"{label}({conf:.2f})")

    return f"{video_id},{frame_id}," + ";".join(result_strs)

def yolo_test(frame, model):
    if frame is None:
        return {"boxes": []}
    results = model(frame)[0]
    names = results.names
    results_list = []
    for i in range(len(results.boxes.cls)):
        cls_i = names[int(results.boxes.cls[i])]
        xyxy = results.boxes.xyxy[i]
        conf = results.boxes.conf[i]
        results_list.append({"label": cls_i,"xyxy":xyxy.cpu().to(torch.int).tolist(), "conf": conf.item()})
    return {"boxes": results_list}

if __name__ == "__main__":
    frame = "spark_yolo/test.jpg"
    res = yolo_test(frame, model)
    print(res)