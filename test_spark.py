from pyspark import SparkContext
from pyspark.streaming import StreamingContext
import time
from collections import defaultdict
import redis
import psycopg2

from spark_yolo.transmit import make_test_info, decode_img
# from spark_yolo.spark_module import partition_yolo
from spark_yolo.yolo_module import yolo_detect
from spark_yolo.record_db import update_redis_batch, update_postgreSQL_batch
from spark_yolo.config import *

# redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, max_connections=100)

_redis_conn = None
_pg_conn = None

def get_redis_connection():
    global _redis_conn
    if _redis_conn is None:
        _redis_conn = redis.Redis(host='localhost', port=6379, db=0)
    return _redis_conn

def get_pg_connection():
    global _pg_conn
    if _pg_conn is None:
        _pg_conn = psycopg2.connect(
            dbname=PGSQL_DATABASE,
            user=PGSQL_USER,
            password=PGSQL_PWD,
            host=PGSQL_HOST,
            port=PGSQL_PORT
        )
    return _pg_conn
# 示例数据 - 包含重复jobID的字典列表
data = make_test_info()

# 初始化Spark上下文
sc = SparkContext("local[4]", "JobIDPartitionExample")
ssc = StreamingContext(sc, 1)  # 批处理间隔为2秒

# 将数据分成几个批次
batch_size = 24
batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
rdd_queue = [sc.parallelize(batch) for batch in batches]

# 创建DStream
input_stream = ssc.queueStream(rdd_queue)

# 模拟tasker处理函数
def tasker_process(partition_records):
    # 按jobID分组处理
    # redis_conn = redis.Redis(connection_pool=redis_pool)
    redis_conn = get_redis_connection()
    pgsql_conn = get_pg_connection()
    buffer = []
    task_count = {}
    print("\nTasker开始处理分区数据:")
    for row in partition_records:
         
        job_id = row[1]["jobID"]
        frame_id = row[1]["frameID"]
        fram_data = decode_img(row[1]["frameDATA"])
        bboxes = yolo_detect(fram_data)
        print(f"  处理jobID={job_id}的{frame_id}, box size={len(bboxes)}")
        try:
            # print(f"row: {row}")
            buffer.append({"jobID": job_id, "frameID": frame_id, "bboxes": bboxes})
            task_count[job_id] = task_count.get(job_id, 0) + 1

            # regularly update database and clear buffer
            if len(buffer) >= 10:
                update_postgreSQL_batch(pgsql_conn, buffer)
                update_redis_batch(redis_conn, task_count)
                buffer.clear()
                task_count.clear()
        except Exception as e:
            print(f"Error during data update: {e}")
    if buffer:
        update_redis_batch(redis_conn, task_count)
        update_postgreSQL_batch(pgsql_conn, buffer)
    print("分区处理完成")

# 主处理流程
def process_stream(rdd):
    if not rdd.isEmpty():
        # 按jobID重新分区，确保相同jobID到同一分区
        # 使用3个分区(对应3个tasker)
        pair_rdd = rdd.map(lambda x: (x["jobID"], x))
        
        # 按jobID分区
        partitioned_rdd = pair_rdd.partitionBy(4)
        # partitioned_rdd = rdd.partitionby("jobID").cache()
        
        # 使用foreachPartition处理每个分区
        partitioned_rdd.foreachPartition(tasker_process)

# 应用处理函数
input_stream.foreachRDD(process_stream)

# 启动流式上下文
ssc.start()

# 等待流处理完成
time.sleep(10)

# 停止流式上下文
ssc.stop(stopSparkContext=True, stopGraceFully=True)