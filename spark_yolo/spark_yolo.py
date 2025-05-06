from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StructType, StructField, StringType, BinaryType, IntegerType
import redis
import psycopg2


from spark_yolo.config import *
from spark_yolo.record_db import update_redis_batch, update_postgreSQL_batch
from spark_yolo.transmit import parse, decode_img
from spark_yolo.yolo_module import yolo_detect



def partition_yolo(partition_rows):
    buffer = []
    task_count = {}
    redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PWD)
    pgsql_conn = psycopg2.connect(dbname=PGSQL_DATABASE, user=PGSQL_USER, password=PGSQL_PWD, host=PGSQL_HOST)
    for row in partition_rows:
        image = decode_img(row.image)  # binary
        # process on single image
        boxes = yolo_detect(image)

        # store in buffer
        buffer.append({"jobID":row.jobID, "frameID": row.framID, "boxes": boxes})
        if task_count.get(row.jobID, None) is not None: 
            task_count[row.jobID] += 1
        else:
            task_count[row.jobID] = 1
    update_redis_batch(redis_conn, task_count)
    update_postgreSQL_batch(pgsql_conn, buffer)

    
    

if __name__ == "__main__":
    # init session
    spark = SparkSession.builder \
            .appName("YOLO") \
            .master(SPARK_MASTER) \
            .config("spark.jars.packages", KAFKA_VER) \
            .getOrCreate()
    # load data  
    raw_df = spark.readStream \
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
        .repartition("jobID") # group by jobID
    parsed_df.rdd.foreachpartition(partition_yolo)



