package decoder

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"

	"google.golang.org/protobuf/proto"

	"csit5970/backend/connector"
	"csit5970/backend/framepb"
)

var (
	jpegSOI = [2]byte{0xFF, 0xD8}
	jpegEOI = [2]byte{0xFF, 0xD9}
)

func ProduceFrames(videoFile string, jobID string) {
	defer os.Remove(videoFile)

	ffmpeg := exec.Command("ffmpeg",
		"-i", videoFile, // Read from stdin
		// "-vf", fmt.Sprintf("fps=%f"), // set fps
		"-f", "mjpeg", // Use jpeg
		"-") // Output to stdout

	var stderr bytes.Buffer
	ffmpeg.Stderr = &stderr

	stdout, err := ffmpeg.StdoutPipe()
	if err != nil {
		log.Printf("Job %s: Failed to create stdout pipe for ffmpeg: %v", jobID, err)
		return
	}
	defer stdout.Close()

	if err := ffmpeg.Start(); err != nil {
		log.Printf("Job %s: Failed to start ffmpeg: %v", jobID, err)
		return
	}

	// Set the frame counter in Redis to 0
	connector.SetJobField(jobID, "frames_processed", 0)

	stdoutReader := bufio.NewReader(stdout)

	var frameID int32

	for frameID = 0; ; frameID++ {
		frame, err := nextFrame(stdoutReader)
		if err == io.EOF {
			break
		} else if err != nil {
			log.Printf("Job %s: Failed to read frame %d: %v", jobID, frameID, err)
			return
		}

		// Create a copy of the frame data for the goroutine
		frameCopy := make([]byte, len(frame))
		copy(frameCopy, frame)

		go func(frame []byte, id int32) {
			if err := sendFrame(frame, jobID, id); err != nil {
				log.Printf("Job %s: Failed to send frame %d: %v", jobID, id, err)
			}
		}(frameCopy, frameID)
	}

	err = ffmpeg.Wait()
	if err != nil {
		log.Printf("Job %s: ffmpeg exited with error: %v\nstderr: %s", jobID, err, stderr.String())
	}

	// Write the total frame count to Redis
	connector.SetJobField(jobID, "frames_total", int(frameID))

	log.Printf("Job %s: Produced %d frames", jobID, frameID)
}

// read a single jpeg frame from the stream
func nextFrame(stream *bufio.Reader) ([]byte, error) {
	var buffer bytes.Buffer
	start, err := stream.Peek(2)
	if err != nil {
		return nil, err
	}
	if !bytes.Equal(start, jpegSOI[:]) {
		return nil, fmt.Errorf("expected JPEG SOI marker, got %v", start)
	}

	buffer.Write(start)
	stream.Discard(2)

	for {
		data, err := stream.ReadBytes(jpegEOI[0])
		if err != nil {
			return nil, err
		}
		buffer.Write(data)

		next, err := stream.ReadByte()
		if err != nil {
			return nil, err
		}
		buffer.WriteByte(next)
		if next == jpegEOI[1] {
			break
		}
	}

	return buffer.Bytes(), nil
}

func sendFrame(frame []byte, jobID string, frameID int32) error {
	// TODO: Send frame to kafka
	frameMessage := framepb.FrameMessage{
		JobID:     jobID,
		FrameID:   frameID,
		FrameData: frame,
	}

	frameBytes, err := proto.Marshal(&frameMessage)
	if err != nil {
		return fmt.Errorf("failed to marshal frame protobuf: %v", err)
	}

	err = connector.ProduceToKafka("frames", frameBytes)
	if err != nil {
		return fmt.Errorf("failed to produce frame to kafka: %v", err)
	}

	return nil
}
