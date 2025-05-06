package server

import (
	"log"
	"sync"

	"github.com/confluentinc/confluent-kafka-go/kafka"
)

var (
	KafkaProducer *kafka.Producer
	once          sync.Once
)

// InitKafkaProducer initializes the Kafka producer as a singleton
func InitKafkaProducer() error {
	var err error
	once.Do(func() {
		config := &kafka.ConfigMap{
			"bootstrap.servers": "localhost:9094", // Using the external listener port
			"client.id":         "video-processor",
		}

		KafkaProducer, err = kafka.NewProducer(config)
		if err != nil {
			log.Printf("Failed to create producer: %v", err)
			return
		}

		// Start a goroutine to handle delivery reports
		go func() {
			for e := range KafkaProducer.Events() {
				switch ev := e.(type) {
				case *kafka.Message:
					if ev.TopicPartition.Error != nil {
						log.Printf("Delivery failed: %v", ev.TopicPartition.Error)
					}
				}
			}
		}()
	})
	return err
}

// CloseKafkaProducer closes the Kafka producer
func CloseKafkaProducer() {
	if KafkaProducer != nil {
		KafkaProducer.Close()
	}
}
