# CSIT5970 Course Project – Group 8

## Group Members

| name         | student id | email                   | contributions                                               |
| ------------ | ---------- | ----------------------- | ----------------------------------------------------------- |
| ZHAO Tianci  | 21093775   | tzhaoat@connect.ust.hk  | system architectural design, DevOps & client implementation |
| JIANG Yihang | 21076351   | yjiangeg@connect.ust.hk |
| LIU Yishan   | 21086382   | yliuoj@connect.ust.hk   |

## Project Presentation Video

TODO: add video link

## Project File Structure

TODO: add file structure

## Deploy the System Locally

### Prerequisites

- `docker` 28.0.1
- `docker-compose` v2.34.0
- `minikube` v1.35.0
- `kubectl` v1.33.0
- `helm` v3.17.3

### Start Databases

```sh
docker compose create
docker compose start
```

### Create `Minikube` Cluster

```sh
./start-cluster.sh # you may want to change the memory and cpu settings
```

### Deploy Services

```sh
./start-deployment.sh
```

### Run with Client Docker Image

```sh
docker run -it --rm \
  --network host \
  -v ./input_dir \
  dwtwilight/csit5970-yolo-client:latest \
  --server_addr http://$(minikube ip) \
  --input example.mp4
```
