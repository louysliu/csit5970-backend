import asyncio
from redis.asyncio import Redis
import psycopg2
import json
from spark_yolo.config import * 
def update_redis_batch(conn, tasks):
    """_summary_

    Args:
        conn (redis.connect): 
        tasks (dict): {jobID: count, ...}
    """
    for job_id, count in tasks.items():
        
        conn.hincrby(job_id, "processed_frames", count)
    print(f"insert redis {job_id} adds {count}")
        # print(f"jobID: {job_id} adds {count}, current count: {conn.hgetall(job_id)}")
        
def update_postgreSQL_batch(conn, buffer):
    """_summary_

    Args:
        conn (psycogp2.connect): _description_
        buffer (list): [{"jobID": xxx, "frameID": xxx, "boxes": []}]
    """
    print("gogogo")
    for frame_buf in buffer:
        box_list = [
            {
                "left": box["xyxy"][0], "top": box["xyxy"][1],
                "right": box["xyxy"][2], "bottom": box["xyxy"][3],
                "class": box["label"], "conf": box["conf"]
            }
            for box in frame_buf["bboxes"]
        ]
        box_json = json.dumps(box_list)

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {PGSQL_YOLO_RESULT_TABLE} (jobID, frameID, bboxes)
                VALUES (%s, %s, %s)
                ON CONFLICT (jobID, frameID) DO UPDATE
                SET bboxes = EXCLUDED.bboxes
            """, (frame_buf["jobID"], frame_buf["frameID"], box_json))
    conn.commit()
    print(f"insert sql: {frame_buf['jobID']}, {frame_buf['frameID']}")
    
if __name__ == "__main__":
    pg_conn = psycopg2.connect(
            dbname=PGSQL_DATABASE,
            user=PGSQL_USER,
            password=PGSQL_PWD,
            host=PGSQL_HOST,
            port=PGSQL_PORT
        )
    buffer = [
        {"jobID": "job1", "frameID": 1, 
         "boxes": [{"label": "cat", "conf": 0.5, "xyxy": [100, 200, 300, 400]},
                   {"label": "dog", "conf": 0.5, "xyxy": [100, 300, 300, 400]}]}]
    update_postgreSQL_batch(pg_conn, buffer)
