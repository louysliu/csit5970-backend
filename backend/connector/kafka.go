package connector

import (
	"fmt"
	"log"

	"github.com/confluentinc/confluent-kafka-go/kafka"
)

var (
	kafkaProducer *kafka.Producer
)

// InitKafkaProducer initializes the Kafka producer as a singleton
func InitKafkaProducer(host string, port int, clientID string) error {
	var err error

	config := &kafka.ConfigMap{
		"bootstrap.servers": fmt.Sprintf("%s:%d", host, port),
		"client.id":         clientID,
	}

	kafkaProducer, err = kafka.NewProducer(config)
	if err != nil {
		log.Printf("Failed to create producer: %v", err)
		return err
	}

	// Start a goroutine to handle delivery reports
	go func() {
		for e := range kafkaProducer.Events() {
			switch ev := e.(type) {
			case *kafka.Message:
				if ev.TopicPartition.Error != nil {
					log.Printf("Delivery failed: %v", ev.TopicPartition.Error)
				}
			}
		}
	}()

	return nil
}

// CloseKafkaProducer closes the Kafka producer
func CloseKafkaProducer() {
	if kafkaProducer != nil {
		kafkaProducer.Close()
	}
}

func ProduceToKafka(topic string, value []byte) error {
	return kafkaProducer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
		Value:          value,
	}, nil)
}
