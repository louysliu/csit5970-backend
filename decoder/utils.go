package decoder

import (
	"bytes"
	"fmt"
	"io"
	"os/exec"
	"strconv"
	"strings"
)

func parseFraction(s string) (int32, int32, error) {
	parts := strings.Split(s, "/")
	if len(parts) != 2 {
		return 0, 0, fmt.Errorf("expected 2 elements of fraction, got %d", len(parts))
	}
	num, err := strconv.ParseInt(parts[0], 10, 32)
	if err != nil {
		return 0, 0, err
	}
	den, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		return 0, 0, err
	}
	return int32(num), int32(den), nil
}

// parseMetadata returns the width, height, and estimated frame count of the video
func parseMetadata(s string) (int32, int32, int32, error) {
	metadata := strings.Split(strings.TrimSpace(s), "\n")

	if len(metadata) != 4 {
		return 0, 0, 0, fmt.Errorf("expected 4 elements of metadata, got %d", len(metadata))
	}

	width, err := strconv.ParseInt(metadata[0], 10, 32)
	if err != nil {
		return 0, 0, 0, err
	}
	height, err := strconv.ParseInt(metadata[1], 10, 32)
	if err != nil {
		return 0, 0, 0, err
	}
	frameRate1, frameRate2, err := parseFraction(metadata[2])
	if err != nil {
		return 0, 0, 0, err
	}

	duration, err := strconv.ParseFloat(metadata[3], 32)
	if err != nil {
		return 0, 0, 0, err
	}

	frames := int32(duration * float64(frameRate1) / float64(frameRate2))

	return int32(width), int32(height), frames, nil
}

func getMetadata(src io.ReadSeeker) (int32, int32, int32, error) {
	// get metadata, read from stdin
	ffprobe := exec.Command("ffprobe",
		"-v", "error",
		"-select_streams", "v:0",
		"-show_entries", "stream=width,height,avg_frame_rate",
		"-show_entries", "format=duration",
		"-of", "default=nk=1:nw=1",
		"-")

	var stdout bytes.Buffer
	var stderr bytes.Buffer
	ffprobe.Stdin = src
	ffprobe.Stdout = &stdout
	ffprobe.Stderr = &stderr

	if err := ffprobe.Run(); err != nil {
		return 0, 0, 0, fmt.Errorf("Failed to run ffprobe: %v", err)
	}

	return parseMetadata(stdout.String())
}
