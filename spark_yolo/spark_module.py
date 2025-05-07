from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StructType, StructField, StringType, BinaryType, IntegerType
import redis
from psycopg2.pool import SimpleConnectionPool



from spark_yolo.config import *
from spark_yolo.record_db import update_redis_batch, update_postgreSQL_batch
from spark_yolo.transmit import parse, decode_img
from spark_yolo.yolo_module import yolo_detect

# from config import *
# from record_db import update_redis_batch, update_postgreSQL_batch
# from transmit import parse, decode_img
# from yolo_module import yolo_detect


# connection pool. avoid repeated connection stuck
redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, max_connections=100)

# pg_pool = SimpleConnectionPool(
#     minconn=1, maxconn=10, 
#     dbname=PGSQL_DATABASE, user=PGSQL_USER, password=PGSQL_PWD, host=PGSQL_HOST
# )

def partition_yolo(partition_rows):
    redis_conn = redis.Redis(connection_pool=redis_pool)
    # pg_conn = pg_pool.getconn()
    buffer = []
    task_count = {}
    try:
        for row in partition_rows:
            try:
                image = decode_img(row.image)
                bboxes = yolo_detect(image)
            except Exception as e:
                print(f"Error during YOLO: {e}")
            
            try:
                buffer.append({"jobID": row.jobID, "frameID": row.frameID, "bboxes": bboxes})
                task_count[row.jobID] = task_count.get(row.jobID, 0) + 1

                # regularly update database and clear buffer
                if len(buffer) >= 100:
                    # update_postgreSQL_batch(pg_conn, buffer)
                    update_redis_batch(redis_conn, task_count)
                    buffer.clear()
                    task_count.clear()
            except Exception as e:
                print(f"Error during data update: {e}")

        # update rest results
        if buffer:
            update_postgreSQL_batch(pg_conn, buffer)
            update_redis_batch(redis_conn, task_count)
    finally:
        pass
        # pg_pool.putconn(pg_conn)  # return the connection

def run():
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
    
def test():
    pass

if __name__ == "__main__":
    test()



