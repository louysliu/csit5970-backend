#!/bin/bash

# external services
# pgsql
kubectl apply -f ./k8s/external/pgsql-external.yml
# redis
kubectl apply -f ./k8s/external/redis-external.yml

# kafka
# kafka ns
kubectl apply -f ./k8s/kafka/kafka-namespace.yml
# Strimzi
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
kubectl apply -f ./k8s/kafka/kafka-cluster.yml -n kafka
# kafka dashboard
kubectl apply -f ./k8s/kafka/kafka-ui.yml

# backend
kubectl apply -f ./k8s/backend/backend.yml

# spark
# spark operator
kubectl apply -f ./k8s/spark/spark-apps-namespace.yml
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update
helm install my-release spark-operator/spark-operator --namespace spark-operator --create-namespace --set webhook.enable=true --set "spark.jobNamespaces={spark-apps}" --wait
# spark job
kubectl apply -f ./k8s/spark/spark-job.yml
