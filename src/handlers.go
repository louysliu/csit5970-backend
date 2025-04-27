package main

import (
	"fmt"
	"net/http"

	"github.com/gorilla/mux"
)

func jobStatusHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	jobId := vars["jobId"]

	fmt.Fprintf(w, "Job status for %s", jobId)
}

func videoUploadHandler(w http.ResponseWriter, r *http.Request) {

}
