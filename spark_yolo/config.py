# Congifurations

# k8s
SPARK_MASTER = "local[*]" # k8s version: k8s://https://<k8s-apiserver-host>:<k8s-apiserver-port>

# kafka
KAFKA_VER = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.9.0"

# redis
REDIS_HOST = "localhost" 
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PWD = "password"

# PostgreSQL
PGSQL_DATABASE = "db"
PGSQL_USER= "user"
PGSQL_PWD = "password"
PGSQL_HOST = "localhost"
PGSQL_PORT = "5432"
PGSQL_YOLO_RESULT_TABLE = "yolo_results"