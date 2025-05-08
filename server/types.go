package server

// Detection represents a single detection in a frame
type Detection [6]any

// JobResult represents the complete job result
type JobSuccess struct {
	Status  int32            `json:"status"`
	Frames  int32            `json:"frames"`
	Labels  map[int32]string `json:"labels"`
	Results [][]Detection    `json:"results"`
}

type JobFailure struct {
	Status  int32  `json:"status"`
	Message string `json:"message"`
}

type JobInProgress struct {
	Status    int32 `json:"status"`
	Frames    int32 `json:"frames"`
	Processed int32 `json:"processed_frames"`
}

// Result for a frame in the DB
type DetectionFromDB struct {
	Left   int32   `json:"left"`
	Top    int32   `json:"top"`
	Right  int32   `json:"right"`
	Bottom int32   `json:"bottom"`
	Class  string  `json:"class"`
	Conf   float32 `json:"conf"`
}
