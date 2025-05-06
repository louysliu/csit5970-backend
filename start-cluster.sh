#!/bin/bash

minikube start --memory=8192 --cpus=8

minikube addons enable ingress

minikube addons enable metrics-server

minikube addons enable dashboard
