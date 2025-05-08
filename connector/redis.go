package connector

import (
	"context"

	"github.com/redis/go-redis/v9"
)

var (
	redisClient *redis.Client
)

func InitRedisClient(addr string) error {
	redisClient = redis.NewClient(&redis.Options{
		Addr: addr,
	})

	return redisClient.Ping(context.Background()).Err()
}

func CloseRedisClient() error {
	return redisClient.Close()
}

func SetJobField(jobID string, field string, value int) error {
	return redisClient.HSet(context.Background(), jobID, field, value).Err()
}

func GetJobField(jobID string, field string) (int, error) {
	return redisClient.HGet(context.Background(), jobID, field).Int()
}
