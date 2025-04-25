## API Definition

### Video Upload: ``POST /upload``

Returns: 
```json
{"job_id": "jobid" }
```

### Check job status: ``GET /job/{job_id}``

Returns:

Success:

```json
{
    "status": 0,
    "frames": 1000,

    "labels": {
        "0": "person",
        "1": "cat"
    },

    "results":  [
        [ // frame 0
            [0, 0.9, 100, 100, 200, 200], // [label_id, confidence, x1, y1, x2, y2]
            [1, 0.8, 100, 100, 200, 200]
        ],
        [ // frame 1
            [0, 0.9, 100, 100, 200, 200],
        ],
    ]
}
```

In progress:

```json
{
    "status": 1,
    "frames": 1000,
    "processed_frames": 100
}
```

Failed:

```json
{
    "status": 2,
    "message": "error message"
}
```