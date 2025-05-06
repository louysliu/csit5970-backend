package server

import (
	"fmt"
	"net/http"

	"csit5970/backend/decoder"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
)

func JobStatusHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	jobId := vars["jobId"]

	fmt.Fprintf(w, "Job status for %s", jobId)
}

func VideoUploadHandler(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(32 << 20); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	file, _, err := r.FormFile("video")
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	jobID := uuid.New().String()

	go decoder.ProduceFrames(file, jobID)

	// return success JSON
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"job_id": "` + jobID + `"}`))
}
