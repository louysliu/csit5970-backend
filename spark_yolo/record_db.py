import asyncio
from redis.asyncio import Redis
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
        # print(f"jobID: {job_id} adds {count}, current count: {conn.hgetall(job_id)}")
        
def update_postgreSQL_batch(conn, buffer):
    """_summary_

    Args:
        conn (psycogp2.connect): _description_
        buffer (list): [{"jobID": xxx, "frameID": xxx, "boxes": []}]
    """
    for boxes in buffer:
        box_list = [
            {
                "left": box["xyxy"][0], "top": box["xyxy"][1],
                "right": box["xyxy"][2], "bottom": box["xyxy"][3],
                "class": box["label"], "conf": box["conf"]
            }
            for box in boxes
        ]
        box_json = json.dumps(box_list)

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {PGSQL_YOLO_RESULT_TABLE} (jobID, frameID, objects)
                VALUES (%s, %d, %s)
                ON CONFLICT (jobID, framID) DO UPDATE
                SET objects = EXCLUDED.objects
            """, (boxes["jobID"], boxes["frameID"], box_json))
    conn.commit()
    
        
