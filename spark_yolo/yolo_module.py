from ultralytics import YOLO
import torch
import threading
from spark_yolo.transmit import decode_img

_model = None
_model_lock = threading.Lock()

def get_model():
    global _model
    with _model_lock:
        if _model is None:
            _model = YOLO("yolo11n.pt")  # 或 torch.load(...)
        return _model

def yolo_detect(frame):
    """

    Args:
        frame (ndarray, filepath, ...): image

    Returns:
        list: [{"label": str, "xyxy": list, "conf": float}, {xxx}]
    """
    if frame is None:
        return {"boxes": {}}
    model = get_model()
    results = model(frame, verbose=False)[0]
    names = results.names
    results_list = []
    for i in range(len(results.boxes.cls)):
        cls_i = names[int(results.boxes.cls[i])]
        xyxy = results.boxes.xyxy[i]
        conf = results.boxes.conf[i]
        results_list.append({"label": cls_i,"xyxy":xyxy.cpu().to(torch.int).tolist(), "conf": conf.item()})
    return results_list

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
    model = YOLO("yolo11n")
    with open("test_msg.txt", "rb") as f:
        msg = f.read()
    job_id, frame_id, frame = decode_img(msg)
    boxes = yolo_detect(job_id, frame_id, frame, model)
    print(boxes)
    