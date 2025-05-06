# Readme

## Test

```sh
python distributed_yolo.py --server_addr http://$(minikube ip) --input /home/tianci-zhao/Documents/projects/HKUST/cloud/group_project/client/out/demo.mp4
```

## Build Docker Image

```sh
docker build -t dwtwilight/csit5970-yolo-client:latest .
```

## Run with Docker Image

```sh
docker run -it --rm \
  --network host \
  -v ./out:/data \
  dwtwilight/csit5970-yolo-client:latest \
  --server_addr http://$(minikube ip) \
  --input /data/demo.mp4
```

- permission issue

```sh
sudo chown user filename
```
