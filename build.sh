#! /bin/bash
if ! minikube status;
then
    minikube delete
    minikube start --vm=true --addons=ingress --addons=metrics-server --memory=8g --cpus=4 --mount=true --mount-string=${PWD}:/mnt/DEM/code

fi


# NOTE: Prior to running minikube cache add web:latest_52 build the docker image on your local 
# cd into the DEM directory after cloning the repo and run : docker build -f Dockerfile -t web:latest_52 .

# eval $(minikube -p minikube docker-env)
# docker build -f Dockerfile -t web:latest_52 .
minikube cache add web:latest_52
if ! kubectl get secret artcred; then
    kubectl create secret generic artcred --from-file=.dockerconfigjson=${HOME}/.docker/config.json --type=kubernetes.io/dockerconfigjson
fi
echo "Starting"
set -x
set -e
SHELL=$(which bash)
kubectl apply -f db-service.yaml,pgadmin-service.yaml,web-service.yaml,db-deployment.yaml,pgadmin-deployment.yaml,web-deployment.yaml,web-claim0-persistentvolumeclaim.yaml
set +x
echo "DEM Swagger UI at http://localhost:8080/docs#"
echo "Complete"
