package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"csit5970/backend/framepb"

	"github.com/confluentinc/confluent-kafka-go/kafka"
	"google.golang.org/protobuf/proto"
)

func deserializeFrameMessage(msg []byte) (*framepb.FrameMessage, error) {
	frame := &framepb.FrameMessage{}
	err := proto.Unmarshal(msg, frame)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal frame message: %v", err)
	}
	return frame, nil
}

func main() {
	// Kafka configuration
	config := &kafka.ConfigMap{
		"bootstrap.servers": "localhost:9094",
		"group.id":          "mock-consumer-group",
		"auto.offset.reset": "earliest",
	}

	// Create consumer
	consumer, err := kafka.NewConsumer(config)
	if err != nil {
		log.Fatalf("Failed to create consumer: %v", err)
	}
	defer consumer.Close()

	// Subscribe to topic
	topic := "frames"
	err = consumer.Subscribe(topic, nil)
	if err != nil {
		log.Fatalf("Failed to subscribe to topic %s: %v", topic, err)
	}

	// Handle graceful shutdown
	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGINT, syscall.SIGTERM)

	// Start consuming messages
	fmt.Printf("Starting to consume messages from topic: %s\n", topic)
	run := true
	for run {
		select {
		case sig := <-sigchan:
			fmt.Printf("Caught signal %v: terminating\n", sig)
			run = false
		default:
			ev, err := consumer.ReadMessage(100)
			if err == nil {
				frame, err := deserializeFrameMessage(ev.Value)
				if err != nil {
					fmt.Printf("Error deserializing message: %v\n", err)
					continue
				}
				fmt.Printf("Received frame - JobID: %s, FrameID: %d, Data size: %d bytes\n",
					frame.GetJobID(), frame.GetFrameID(), len(frame.GetFrameData()))
			} else if err.(kafka.Error).Code() != kafka.ErrTimedOut {
				fmt.Printf("Error while consuming message: %v\n", err)
			}
		}
	}

	fmt.Println("Consumer stopped")
}
