from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StructType, StructField, StringType, BinaryType, IntegerType
import redis
import psycopg2
from psycopg2.pool import SimpleConnectionPool



from spark_yolo.config import *
from spark_yolo.record_db import update_redis_batch, update_postgreSQL_batch
from spark_yolo.transmit import parse, decode_img
from spark_yolo.yolo_module import yolo_detect

_redis_conn = None
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


def partition_yolo(partition_rows):
    redis_conn = get_redis_connection()
    pgsql_conn = get_pg_connection()
    buffer = []
    task_count = {}
    try:
        for row in partition_rows:
            try:
                # print("start yolo")
                image = decode_img(row["frameDATA"])
                bboxes = yolo_detect(image)
            except Exception as e:
                print(f"Error during YOLO: {e}")
            try:
                buffer.append({"jobID": row["jobID"], "frameID": row["frameID"], "bboxes": bboxes})
                task_count[row["jobID"]] = task_count.get(row["jobID"], 0) + 1

                # regularly update database and clear buffer
                if len(buffer) >= REDIS_UPDATE_FREQ:
                    update_postgreSQL_batch(pgsql_conn, buffer)
                    update_redis_batch(redis_conn, task_count)
                    buffer.clear()
                    task_count.clear()
            except Exception as e:
                print(f"Error during data update: {e}")

        # update rest results
        if buffer:
            update_postgreSQL_batch(pgsql_conn, buffer)
            update_redis_batch(redis_conn, task_count)
    finally:
        pass

def run_spark():
    # init session
    # init spark session for streaming
    spark = SparkSession.builder \
        .appName("YOLO") \
        .master(SPARK_MASTER) \
        .config("spark.jars.packages", KAFKA_VER) \
        .getOrCreate()
    # load data  
    raw_df = spark\
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "host1:port1,host2:port2") \
        .option("subscribe", "topic-yolo") \
        .load()
    # df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
    value_df = raw_df.select(col("value"))

    # decode protobuf
    schema = StructType([
        StructField("jobID", StringType(), True),
        StructField("frameID", IntegerType(), True),
        StructField("frameDATA", BinaryType(), True)
    ])
    parse_udf = udf(parse, schema)
    parsed_df = value_df\
        .withColumn("parsed", parse_udf(col("value")))\
        .select("parsed.*")\
        .partitionBy("jobID")
        
    
    parsed_df.rdd.foreachpartition(partition_yolo)




