package server

import (
	"context"
	"csit5970/backend/connector"
	"encoding/json"

	"github.com/redis/go-redis/v9"
)

type JobStatus int8

const (
	Success JobStatus = iota
	InProgress
	Failure
)

func SuccessJSON(jobID string, framesTotal int32, framesProcessed int32) ([]byte, error) {
	jobResults, err := GetJobResults(jobID)
	if err != nil {
		return nil, err
	}

	labels, detections, err := ConvertResults(jobResults)
	if err != nil {
		return nil, err
	}

	return json.Marshal(JobSuccess{
		Status:  int32(Success),
		Frames:  framesTotal,
		Labels:  labels,
		Results: detections,
	})
}

func InProgressJSON(jobID string, framesTotal int32, framesProcessed int32) ([]byte, error) {
	return json.Marshal(JobInProgress{
		Status:    int32(InProgress),
		Frames:    framesTotal,
		Processed: framesProcessed,
	})
}

func FailureJSON(jobID string, err string) ([]byte, error) {
	return json.Marshal(JobFailure{
		Status:  int32(Failure),
		Message: err,
	})
}

// returns (status, total frames, frames processed, error)
func CheckJobStatus(jobID string) (JobStatus, int32, int32, error) {
	framesProcessed, err := connector.GetJobField(jobID, "frames_processed")
	if err != nil {
		if err != redis.Nil {
			return -1, -1, -1, err
		}
		framesProcessed = -1
	}

	framesTotal, err := connector.GetJobField(jobID, "frames_total")
	if err != nil {
		if err != redis.Nil {
			return -1, -1, -1, err
		}
		framesTotal = -1
	}

	if framesProcessed != -1 && framesProcessed == framesTotal {
		return Success, int32(framesTotal), int32(framesProcessed), nil
	}

	return InProgress, int32(framesTotal), int32(framesProcessed), nil
}

func GetJobResults(jobID string) ([][]DetectionFromDB, error) {
	results, err := connector.QueryJobResults(context.Background(), jobID)
	if err != nil {
		return nil, err
	}

	frameResults := make([][]DetectionFromDB, len(results))
	for i, result := range results {
		err := json.Unmarshal([]byte(result), &frameResults[i])
		if err != nil {
			return nil, err
		}
	}

	return frameResults, nil
}

func ConvertResults(results [][]DetectionFromDB) (map[int32]string, [][]Detection, error) {
	labelSet := make(map[string]struct{})
	labels := make(map[int32]string)
	detections := make([][]Detection, len(results))

	for frameID, frameDetections := range results {
		for _, d := range frameDetections {
			var labelID int32
			if _, ok := labelSet[d.Class]; !ok {
				labelID = int32(len(labelSet))
				labelSet[d.Class] = struct{}{}
				labels[labelID] = d.Class
			}
			detections[frameID] = append(detections[frameID], Detection{
				labelID,
				d.Conf,
				d.Left,
				d.Top,
				d.Right,
				d.Bottom,
			})
		}
	}

	return labels, detections, nil
}
