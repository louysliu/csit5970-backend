package decoder

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
)

var (
	jpegSOI = [2]byte{0xFF, 0xD8}
	jpegEOI = [2]byte{0xFF, 0xD9}
)

func ProduceFrames(videoFile io.ReadSeekCloser, jobID string) {
	defer videoFile.Close()
	// reset src to start
	videoFile.Seek(0, io.SeekStart)

	ffmpeg := exec.Command("ffmpeg",
		"-i", "-", // Read from stdin
		// "-vf", fmt.Sprintf("fps=%f"), // set fps
		"-f", "mjpeg", // Use jpeg
		"-") // Output to stdout

	var stderr bytes.Buffer

	ffmpeg.Stdin = videoFile
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

	stdoutReader := bufio.NewReader(stdout)

	var frameID int32

	for frameID = 0; ; frameID++ {
		frame, err := readFrame(stdoutReader)
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
}

// read a single jpeg frame from the stream
func readFrame(stream *bufio.Reader) ([]byte, error) {
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

	// write to file
	filename := fmt.Sprintf("decoded/%s-%d.jpg", jobID, frameID)

	if err := os.WriteFile(filename, frame, 0644); err != nil {
		return fmt.Errorf("failed to write frame to file: %v", err)
	}

	return nil
}
