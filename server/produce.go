package server

import (
	"io"
	"log"
)

func ProduceVideo(src io.Reader, jobID string) error {
	log.Printf("Producing video for job %s", jobID)

	// TODO: Read video data and send to Kafka
	// For now, just return nil
	return nil
}
