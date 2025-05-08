# Congifurations
import os

env_dict = os.environ

# k8s
SPARK_MASTER = env_dict.get("SPARK_MASTER", "local[*]")

# kafka
KAFKA_VER = env_dict.get(
    "KAFKA_VER", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.9.0"
)

# redis
REDIS_HOST = env_dict.get("REDIS_HOST", "local_host")
REDIS_PORT = env_dict.get("REDIS_PORT", 6379)
REDIS_DB = env_dict.get("REDIS_DB", 0)
REDIS_PWD = env_dict.get("REDIS_PWD", "password")
REDIS_PROCESSED_FIELD = env_dict.get("REDIS_PROCESSED_FIELD", "frames_processed")
REDIS_HASH_JOBID = env_dict.get("REDIS_HASH_JOBID", "jobID")
REDIS_UPDATE_FREQ = env_dict.get("REDIS_UPDATE_FREQ", 100)

# PostgreSQL
PGSQL_DATABASE = env_dict.get("PGSQL_DATABASE", "yolo")
PGSQL_USER = env_dict.get("PGSQL_USER", "tester")
PGSQL_PWD = env_dict.get("PGSQL_PWD", "password")
PGSQL_HOST = env_dict.get("PGSQL_HOST", "localhost")
PGSQL_PORT = env_dict.get("PGSQL_PORT", 5432)
PGSQL_YOLO_RESULT_TABLE = env_dict.get("PGSQL_YOLO_RESULT_TABLE", "bbox")
