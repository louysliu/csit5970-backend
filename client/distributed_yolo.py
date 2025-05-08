import argparse
import requests
import cv2
import json
import time
import os
import colorsys
import random
from tqdm import tqdm

headers = {"Host": "yolo-backend"}


class UploadProgressWrapper:
    def __init__(self, file_obj, progress_bar):
        self.file_obj = file_obj
        self.progress_bar = progress_bar

    def read(self, size=-1):
        data = self.file_obj.read(size)
        if data:
            self.progress_bar.update(len(data))
        return data


def upload_video(server_addr, video_path):
    url = f"{server_addr}/upload"

    try:
        file_size = os.path.getsize(video_path)
    except OSError as e:
        raise RuntimeError(f"File error: {str(e)}")

    try:
        with tqdm(
            total=file_size, unit="B", unit_scale=True, desc="Uploading"
        ) as progress_bar:
            with open(video_path, "rb") as f:
                wrapped_file = UploadProgressWrapper(f, progress_bar)
                response = requests.post(
                    url, files={"video": wrapped_file}, headers=headers
                )

            if response.status_code == 200:
                return response.json()["job_id"]
            response.raise_for_status()

    except (requests.exceptions.RequestException, KeyError) as e:
        raise RuntimeError(f"Upload Request failed: {str(e)}")


def poll_job_status(server_addr, job_id, max_retry=5):
    status_url = f"{server_addr}/job/{job_id}"
    progress_bar = None
    cur_retry = 0

    while True:
        try:
            response = requests.get(status_url, headers=headers)
            data = response.json()
            cur_retry = 0

            if data["status"] == 0:  # Success
                if progress_bar:
                    progress_bar.n = data["frames"]
                    progress_bar.refresh()
                    progress_bar.close()
                return data
            elif data["status"] == 1:  # In progress
                if not progress_bar:
                    progress_bar = tqdm(total=data["frames"], desc="Processing")
                progress_bar.n = data["processed_frames"]
                progress_bar.refresh()
                time.sleep(2)
            elif data["status"] == 2:  # Failed
                raise RuntimeError(
                    f"Job failed: {data.get('message', 'Unknown error')}"
                )
            else:
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            if cur_retry >= max_retry:
                raise RuntimeError(f"Job failed with max retry times reached: {str(e)}")
            cur_retry += 1
            print(f"Retry#{cur_retry}: Poll request failed, will retry in 5 seconds")
            time.sleep(5)


def generate_color_map(labels):
    color_map = {}
    label_ids = [int(k) for k in labels.keys()]

    golden_ratio = 0.618033988749895
    for i, label_id in enumerate(sorted(label_ids)):
        hue = (i * golden_ratio) % 1.0
        saturation = 0.7 + random.random() * 0.3
        value = 0.5 + random.random() * 0.4

        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        color_map[label_id] = (int(r * 255), int(g * 255), int(b * 255))
    return color_map


def draw_bboxes(frame, frame_results, labels, color_map, confidence_threshold):
    for box in frame_results:
        label_id, conf, x1, y1, x2, y2 = box
        if conf < confidence_threshold:
            continue

        color = color_map.get(label_id, (0, 255, 0))
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

        label_text = f"{labels[str(label_id)]} {conf:.2f}"
        (text_width, text_height), _ = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )

        cv2.rectangle(
            frame,
            (int(x1), int(y1) - text_height - 10),
            (int(x1) + text_width, int(y1)),
            color,
            -1,
        )

        cv2.putText(
            frame,
            label_text,
            (int(x1), int(y1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
    return frame


def process_output_video(input_path, output_path, result_data, confidence_threshold):
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    labels = result_data["labels"]
    color_map = generate_color_map(labels)

    with tqdm(total=result_data["frames"], desc="Rendering") as pbar:
        for frame_idx, frame_results in enumerate(result_data["results"]):
            ret, frame = cap.read()
            if not ret:
                break

            frame = draw_bboxes(
                frame, frame_results, labels, color_map, confidence_threshold
            )
            out.write(frame)
            pbar.update(1)

    cap.release()
    out.release()


def main():
    parser = argparse.ArgumentParser(
        description="Distributed YOLO Video Processing Client"
    )
    parser.add_argument("--server_addr", required=True, help="Server address")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--confidence_threshold", type=float, default=0.5)
    parser.add_argument("--output", help="Output video path")
    parser.add_argument("--bbox_output", help="Bounding box JSON output path")
    parser.add_argument("--max_retry", type=int, default=5)

    args = parser.parse_args()

    # Set default output paths
    output_path = args.output or f"{args.input.rsplit('.', 1)[0]}_yolo.mp4"
    bbox_path = args.bbox_output or f"{args.input.rsplit('.', 1)[0]}_bbox.json"

    print(f"Processing File: {args.input}, Output Path: {output_path}, {bbox_path}")

    try:
        # Step 1: Upload video
        job_id = upload_video(args.server_addr, args.input)
        print(f"File Upload Successful, Job ID: {job_id}")

        # Step 2: Poll job status
        result_data = poll_job_status(args.server_addr, job_id, args.max_retry)

        # Step 3: Save bounding box data
        with open(bbox_path, "w") as f:
            json.dump(result_data, f, indent=2)

        # Step 4: Render output video
        process_output_video(
            args.input, output_path, result_data, args.confidence_threshold
        )

        print(
            f"\nProcessing complete!\nOutput video: {output_path}\nBBox data: {bbox_path}"
        )

    except Exception as e:
        print(f"\nError: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
