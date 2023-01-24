# DEM
This project contains the source code for DEM challenge and has been implemented as fastapi. (For detailed screenshots please review the word document DEM Section 1 and 2 in the repo)

### Prerequisites
- Fastapi
- Docker
- Python
- Pipenv
- Local Kubernetes environment
(Using minikube instead of Docker Desktop). Use `brew upgrade minikube` if you have an older version of minikube, as some incompatibilities may exist.
- Kubectl. Aliases are optional but highly recommended.


### Setup
We will setup a kube cluster and deploy the application locally.
This repo supports unix like operating systems like Linux, Mac, & WSL. Native windows is not supported.

It is normal for the initial run of build-minikube.sh to take a long time. Subsequent reruns, even if minikube delete is run in between, should be much faster.

1. Clone the main/master branch.
    - Run docker build command to prep the image on local
2. If you have run `minikube start` at any point beforehand run `minikube delete` before continuing to next step.
3. To use minikube run `sh build.sh` 
    - It is normal for pods to briefly have the **CrashLoopback** status during startup. If this status persists for more than 30 seconds something is likely wrong and needs troubleshooting.
    - After the script completes you can run `kubectl get pods` to review if the pods are running. *Note* if you do not see STATUS = Running for all pods listed something went wrong.

    Note: If you minikube registry is not configured correctly feel free to build the image separately and push the image to minikube docker registry.
    Cmd1:
    `docker build -f Dockerfile -t web:latest_52 .`
    Cmd2:
    `minikube cache add web:latest_52`

4. Once you have the pods running you want to grab the web svc pod name and port forward to expose the application:
    `kubectl port-forward web-7f694969c6-g2zt4 8080:8080`
    `kubectl port-forward <pod_name> 8080:8080`
5. You should be able to access the application through: http://localhost:8080/docs#



