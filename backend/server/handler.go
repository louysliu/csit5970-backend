package server

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	"csit5970/backend/decoder"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
)

func JobStatusHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	jobId := vars["jobId"]

	status, framesTotal, framesProcessed, err := CheckJobStatus(jobId)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "application/json")

	switch status {
	case Success:
		w.WriteHeader(http.StatusOK)
		json, err := SuccessJSON(jobId, framesTotal, framesProcessed)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Write(json)
	case InProgress:
		w.WriteHeader(http.StatusOK)
		json, err := InProgressJSON(jobId, framesTotal, framesProcessed)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Write(json)
	case Failure:
		w.WriteHeader(http.StatusInternalServerError)
		json, err := FailureJSON(jobId, "")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Write(json)
	}
}

func VideoUploadHandler(w http.ResponseWriter, r *http.Request) {
	r.Body = http.MaxBytesReader(w, r.Body, 128<<20) // 128MB

	reader, err := r.MultipartReader()
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	part, err := reader.NextPart()
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if part.FormName() != "video" {
		http.Error(w, "expected video, got "+part.FormName(), http.StatusBadRequest)
		return
	}

	jobID := uuid.New().String()

	tmpFile, err := os.CreateTemp("", fmt.Sprintf("%s.tmp", jobID))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer tmpFile.Close()

	_, err = io.Copy(tmpFile, part)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Printf("Job %s: Start producing frames", jobID)
	go decoder.ProduceFrames(tmpFile.Name(), jobID)

	// return success JSON
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"job_id": "` + jobID + `"}`))
}
