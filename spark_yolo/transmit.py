from spark_yolo.frame_pb2 import FrameMessage
from PIL import Image
import io
import cv2
import numpy as np


def encode(job_id, frame_id, frame):
    frame_msg = FrameMessage()
    frame_msg.jobID = job_id
    frame_msg.frameID = frame_id
    frame_msg.frameData = frame

    # 序列化为二进制
    binary_data = frame_msg.SerializeToString()
    print("length of message", len(binary_data))  
    # with open("test_msg.txt", "wb") as f:
    #     f.write(binary_data)
    return binary_data
 
def parse(msg):
    frame_msg = FrameMessage()
    frame_msg.ParseFromString(msg)
    return frame_msg.jobID, frame_msg.frameID, frame_msg.frameDATA
    
def decode_img(frame_data):
    # decode
    frame = Image.open(io.BytesIO(frame_data))
    return frame

def decode_bytes(frame_data):
    decoded_frame = cv2.imdecode(
        np.frombuffer(frame_data, dtype=np.uint8), 
        cv2.IMREAD_COLOR  # 或 cv2.IMREAD_UNCHANGED
    )
    return decoded_frame

def make_test_info():
    encoded_info = []
    job_id_num = 8
    
    frameID = 0
    video_path = 'spark_yolo/example.mp4'  # 替换为你的视频文件路径
    cap = cv2.VideoCapture(video_path)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("end")
            break
        _, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        jobID = f"job{frameID % job_id_num}"
        # encoded_text = encode(jobID, frameID, encoded.tobytes())
        encoded_text = {
            "jobID": jobID,
            "frameID": frameID,
            "frameDATA": encoded.tobytes()
        }
        frameID += 1
        encoded_info.append(encoded_text)
    return encoded_info
        
            
        
        

if __name__ == "__main__":
    # make_test_info()
    pass
