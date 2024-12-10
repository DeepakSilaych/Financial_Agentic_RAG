# Server Setup Instructions

This project requires three servers to be running:

## 1. Vector Database Server

1. Create and activate a virtual environment:
```bash
python3 -m venv env
source env/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the vector database server:
```bash
python vector_store.py
```

## 2. Main Application Server

1. Start the main server:
```bash
source env/bin/activate
python app.py
```

## 3. Logging Server

1. Create and activate a virtual environment:
```bash
cd logging_server
python3 -m venv log_env
source log_env/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the logging server:
```bash
python server.py
```

4. Access the logging dashboard at: http://localhost:7000

## Docker usage

We have provided a docker image in this folder `docker-image.tar.gz`

```
# load the docker image using
docker load -i docker-image.tar.gz

# run the docker image using
docker run -p 7000:7000 pathway

# exec into docker image to get CLI access
docker exec -ti <container name> bash

# inside docker run
# after this command you can type in question
# and get answers
python3 chatbot.py

```

For added accuracy you can unzip `Cache.zip` and `data.zip` inside the `/app` directory of docker

You can also build a docker image from the provided Dockerfile

```
# to build a docker image
docker build . -t pathway

# to run docker image
docker run -p 7000:7000 pathway

# to run additional commands exec into the container
docker exec -ti <container name> bash
```

## Server Ports

- Vector Database Server: Port 7000
- Main Application Server: Port 8000

## Using the Logger in Code

To send logs from your Python code, use the `requests` library:

```python
import requests
import json

def send_log(message, level="INFO", component=None, question_id=None, track=None):
    log_data = {
        "message": message,
        "level": level,  # "INFO", "WARNING", or "ERROR"
        "component": component,
        "question_id": question_id,
        "track": track
    }
    
    try:
        response = requests.post(
            "http://localhost:7000/log",
            json=log_data
        )
        return response.json()
    except Exception as e:
        print(f"Failed to send log: {str(e)}")

# Examples:

# Basic log
send_log("Processing started")

# Log with component
send_log("Cache miss", component="vector_store")

# Log with question tracking
send_log("Generating answer", question_id="Q123", component="answer_generator")

# Log with track
send_log("Track completed", track="preprocessing", level="INFO")

# Error log
send_log("Database connection failed", level="ERROR", component="db_client")
```

The logs will be automatically grouped in the dashboard based on:
1. Question ID (if provided)
2. Track (if provided)
3. Component (if provided)
4. System logs (default)

## Server Manager

`server_manager.py` handles 1 fast indexing server and 2 slow indexing servers. The script is supposed to be kept running alongside the aforementioned 3 servers.

### Configuration Changes
Script has variables related to paths of data directories and cache directories of the 3 servers it manages. It loads values of these variables from `config.py`. Set the appropriate directory paths for all the servers in `config.py` for the server manager script to work properly.

### Running Instructions

Start the fast and slow servers with:
```
python3 run_fast_server.py
python3 run_multiserver.py
```

Fast server listens on port 7000 while Multiserver listens on port 8000

Now to run server manager execute:
```
python3 server_manager.py
```
Preferably run this script in a detached terminal session.


