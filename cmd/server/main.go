package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"csit5970/backend/server"

	"github.com/gorilla/mux"
)

func main() {
	// command line arguments
	host := flag.String("host", "127.0.0.1", "Host to bind the server to")
	port := flag.Int("port", 8000, "Port number to listen on")
	debug := flag.Bool("debug", false, "Enable debug mode")
	logFilePath := flag.String("logfile", "backend.log", "Log file to write to")

	flag.Parse()

	// Prefix for logs
	if *debug {
		log.SetFlags(log.LstdFlags | log.Lshortfile)
	} else {
		log.SetFlags(log.LstdFlags)
	}

	// Open Log file
	logFile, err := os.OpenFile(*logFilePath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Panic(err)
	}
	defer logFile.Close()

	// Set the log output to the file
	log.SetOutput(logFile)

	// Create a new router
	r := mux.NewRouter()

	// Apply the logging middleware
	r.Use(server.LoggingMiddleware)

	// Routes
	r.HandleFunc("/job/{jobId}", server.JobStatusHandler).Methods("GET")
	r.HandleFunc("/upload", server.VideoUploadHandler).Methods("POST")

	log.Printf("Server listening on %s:%d", *host, *port)

	// Initialize the Kafka producer
	/*
		if err := server.InitKafkaProducer(); err != nil {
			log.Panic(err)
		}
		defer server.CloseKafkaProducer()
	*/

	// Start the server
	err = http.ListenAndServe(fmt.Sprintf("%s:%d", *host, *port), r)
	if err != nil {
		log.Panic(err)
	}
}
