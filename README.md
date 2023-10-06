# Server and Client Ball Tracking Application

This project is a real-time ball tracking application that utilizes WebRTC and AIORTC to enable communication and coordination between a server and a client. The server is responsible for sending video frames containing a ball to the client, which tracks the ball's coordinates and sends them back to the server for further processing. The project includes server and client implementations, as well as corresponding test files and deployment configurations.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Deployment](#deployment)

## Features

- Real-time video streaming from server to client.
- Ball tracking on the client side.
- Calculation of error between actual and estimated ball coordinates.
- Test cases for server and client functionality.
- Deployment configurations for server and client.

## Prerequisites

Before running the application, make sure you have the following prerequisites installed:

- Python 3.9 or higher
- OpenCV
- aiortc library
- Docker (for deployment purposes)
- Kubernetes (for deployment purposes)

## Installation

1. Unzip the folder containing the project
2. Change into the project directory:

```
cd real-time-ball-tracking
```
3. Install the required dependencies:
```
pip install -r requirements.txt
```
## Usage
### Server
```
python src/server.py
```

The server will start running and listening for connections on the specified port.

### Client
```
python src/client.py
```

The client will connect to the server and start receiving video frames. The ball coordinates will be tracked and sent back to the server for further processing.

## Testing

The project includes test cases for the server and client functionalities.
```
python -m pytest src/tests
```

The test results will be displayed in the terminal.

## Deployment

1. Build the Docker images:
```
docker build -t server-image -f src/server_docker/Dockerfile .
docker build -t client-image -f src/client_docker/Dockerfile .
```
2. Further, details for deploying kubernetes are provided in the kubernetes Minikube document. These commands can be used to deploy:
```
kubectl apply -f server-deployment.yaml
kubectl apply -f client-deployment.yaml
```








