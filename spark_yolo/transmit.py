from frame_pb2 import FrameMessage
from PIL import Image
import io


def encode(job_id, frame_id, frame):
    frame_msg = FrameMessage()
    frame_msg.jobID = job_id
    frame_msg.frameID = frame_id
    frame_msg.frameData = frame

    # 序列化为二进制
    binary_data = frame_msg.SerializeToString()
    print("length of message", len(binary_data))  
    with open("test_msg.txt", "wb") as f:
        f.write(binary_data)
    
def decode(msg):
    # decode
    frame_msg = FrameMessage()
    frame_msg.ParseFromString(msg)
    frame = Image.open(io.BytesIO(frame_msg.frameData))
    return frame_msg.jobID, frame_msg.frameID, frame

if __name__ == "__main__":
    jobID = "1"
    frameID = 2
    with open("spark_yolo/test.jpg", "rb") as f:
        jpeg_data = f.read()
    encode(jobID, frameID, jpeg_data)
