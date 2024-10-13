# Project Setup Documentation

This document provides step-by-step instructions to set up the backend and frontend components of your real-time log analytics system using ClickHouse, **Vector.dev**, and Python. Each section includes setup instructions for the technologies used, following best practices. Virtual environments (`venv`) are utilized to avoid installing packages globally on your machine.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Backend Setup](#backend-setup)
  - [1. ClickHouse Setup](#1-clickhouse-setup)
  - [2. Vector.dev Setup](#2-vectordev-setup)
  - [3. Log Generator Setup](#3-log-generator-setup)
- [Frontend Setup](#frontend-setup)
  - [1. Flask Application Setup](#1-flask-application-setup)
  - [2. Deploying to Replit](#2-deploying-to-replit)
- [Conclusion](#conclusion)
- [Additional Notes](#additional-notes)

---

## Prerequisites

Before starting, ensure you have the following installed on your machine:

- **Docker**: To run ClickHouse and Vector.dev containers.
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop) for your operating system.
- **Python 3.7 or higher**: For running Python scripts and applications.
  - [Download Python](https://www.python.org/downloads/)
- **Git**: For version control (optional but recommended).
  - [Download Git](https://git-scm.com/downloads)

---

## Backend Setup

### 1. ClickHouse Setup

#### 1.1. Pull the ClickHouse Docker Image

Open a terminal and run:

```bash
docker pull clickhouse/clickhouse-server:latest
```

#### 1.2. Run the ClickHouse Server

Start the ClickHouse server container:

```bash
docker run -d \
  --name clickhouse-server \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server:latest
```

- **Explanation**:
  - `-d`: Run the container in detached mode.
  - `--name clickhouse-server`: Name the container for easier reference.
  - `-p 8123:8123`: Map the HTTP interface port.
  - `-p 9000:9000`: Map the native TCP interface port.

#### 1.3. Verify ClickHouse is Running

Check if the ClickHouse server is running:

```bash
docker ps
```

You should see `clickhouse-server` listed.

#### 1.4. Access ClickHouse Client (Optional)

To interact with ClickHouse using the command-line client:

```bash
docker exec -it clickhouse-server clickhouse-client
```

#### 1.5. Create Database and Table

**Using ClickHouse Client**:

1. Access the client:

   ```bash
   docker exec -it clickhouse-server clickhouse-client
   ```

2. Create a database:

   ```sql
   CREATE DATABASE IF NOT EXISTS logs;
   ```

3. Use the `logs` database:

   ```sql
   USE logs;
   ```

4. Create the `application_logs` table:

   ```sql
   CREATE TABLE IF NOT EXISTS application_logs (
       timestamp DateTime,
       log_level String,
       message String,
       source String
   ) ENGINE = MergeTree()
   ORDER BY timestamp;
   ```

5. Exit the client:

   ```sql
   EXIT;
   ```

---

### 2. Vector.dev Setup

#### 2.1. Pull the Vector.dev Docker Image

Pull the Vector.dev image:

```bash
docker pull timberio/vector:latest-alpine
```

#### 2.2. Create a Vector Configuration Directory

Create a directory to store the configuration:

```bash
mkdir vector
cd vector
```

#### 2.3. Create the Vector Configuration File

Create a file named `vector.yaml`:

```bash
touch vector.yaml
```

Edit `vector.yaml` with the following content:

```yaml
# vector.yaml

# vector.yaml

sources:
  log_generator:
    type: socket
    address: 0.0.0.0:9001  # Adjust the port if needed.
    mode: tcp

sinks:
  clickhouse:
    type: clickhouse
    inputs:
      - log_generator
    database: logs
    table: application_logs
    endpoint: http://localhost:8123/  # Adjust if ClickHouse is remote.
    encoding:
      # was giving error with this
      # codec: json  # Assuming logs are in JSON format.
      timestamp_format: "unix"
```

- **Explanation**:
  - **Source**:
    - `type = "socket"`: Listens for logs over TCP.
    - `address = "0.0.0.0:9000"`: Listens on port `9000`.
    - `mode = "tcp"`: Specifies TCP mode.
  - **Transform**:
    - `type = "json_parser"`: Parses incoming JSON logs.
    - `inputs = ["logs_in"]`: Takes input from the `logs_in` source.
    - `drop_invalid = true`: Discards invalid JSON messages.
  - **Sink**:
    - `type = "clickhouse"`: Sends logs to ClickHouse.
    - `endpoint`: URL of the ClickHouse server.
    - `database` and `table`: Specify the target database and table.
    - `skip_unknown_fields = true`: Ignores fields not present in the table schema.
    - `encoding.codec = "json"`: Specifies the data format.

#### 2.4. Run the Vector.dev Container

##### 2.4.1. Create a Docker Network

Create a Docker network to allow containers to communicate:

```bash
docker network create vector-net
```

##### 2.4.2. Run the ClickHouse Server on the Network

Stop and remove the existing ClickHouse container (if necessary):

```bash
docker stop clickhouse-server
docker rm clickhouse-server
```

Run the ClickHouse container on the `vector-net` network:

```bash
docker run -d \
  --name clickhouse-server \
  --network vector-net \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server:latest
```

##### 2.4.3. Run the Vector.dev Container on the Network

In the `vector` directory (where `vector.toml` is located):

```bash
docker run -d \
  --name vector \
  --network vector-net \
  -p 9000:9000 \
  -v $(pwd)/vector.toml:/etc/vector/vector.toml:ro \
  timberio/vector:latest-alpine
```

- **Explanation**:
  - `--network vector-net`: Connects the container to the custom network.
  - `-p 9000:9000`: Exposes port `9000` for receiving logs.
  - `-v $(pwd)/vector.toml:/etc/vector/vector.toml:ro`: Mounts the configuration file into the container.

#### 2.5. Verify Vector.dev is Running

Check the container status:

```bash
docker ps
```

You should see `vector` listed among the running containers.

---

### 3. Log Generator Setup

#### 3.1. Create a Project Directory

Navigate back to the parent directory and create a new directory:

```bash
cd ..
mkdir log_generator
cd log_generator
```

#### 3.2. Create a Python Virtual Environment

Create a virtual environment to isolate dependencies:

```bash
python3 -m venv venv
```

Activate the virtual environment:

- On macOS/Linux:

  ```bash
  source venv/bin/activate
  ```

- On Windows:

  ```bash
  venv\Scripts\activate
  ```

#### 3.3. Install Required Python Packages

- If using TCP sockets, no additional packages are needed.
- If using HTTP to send logs to Vector.dev, install the `requests` package:

  ```bash
  pip install requests
  ```

Create a `requirements.txt` file:

```bash
pip freeze > requirements.txt
```

#### 3.4. Create the Log Generator Script

Create a file named `log_generator.py`:

```bash
touch log_generator.py
```

Add the following content:

**Option 1: Using TCP Sockets**

```python
import time
import random
import socket
import json

VECTOR_HOST = 'localhost'
VECTOR_PORT = 9000

log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
sources = ['auth', 'payment', 'search', 'profile']

while True:
    log_level = random.choice(log_levels)
    source_module = random.choice(sources)
    message = f"Sample log message from {source_module} at level {log_level}"
    log_entry = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'log_level': log_level,
        'message': message,
        'source': source_module
    }
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((VECTOR_HOST, VECTOR_PORT))
        s.sendall(json.dumps(log_entry).encode('utf-8') + b'\n')
    time.sleep(1)
```

**Option 2: Using HTTP**

If you prefer to use HTTP, update `vector.toml` to include an HTTP source and adjust the log generator accordingly.

Update `vector.toml`:

```toml
# Replace the [sources.logs_in] section with:

[sources.logs_in]
  type = "http"
  address = "0.0.0.0:9000"
  encoding = "json"
```

Update `log_generator.py`:

```python
import time
import random
import requests

VECTOR_ENDPOINT = 'http://localhost:9000'

log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
sources = ['auth', 'payment', 'search', 'profile']

while True:
    log_level = random.choice(log_levels)
    source_module = random.choice(sources)
    message = f"Sample log message from {source_module} at level {log_level}"
    log_entry = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'log_level': log_level,
        'message': message,
        'source': source_module
    }
    response = requests.post(VECTOR_ENDPOINT, json=log_entry)
    if response.status_code != 200:
        print(f"Failed to send log: {response.text}")
    time.sleep(1)
```

#### 3.5. Run the Log Generator

Ensure the virtual environment is activated:

```bash
source venv/bin/activate  # Or venv\Scripts\activate on Windows
```

Run the script:

```bash
python log_generator.py
```

Logs will start generating and sending to Vector.dev, which forwards them to ClickHouse.

#### 3.6. Verify Logs in ClickHouse

Access the ClickHouse client:

```bash
docker exec -it clickhouse-server clickhouse-client
```

Run the query:

```sql
SELECT * FROM logs.application_logs LIMIT 10;
```

You should see entries corresponding to the generated logs.

---

## Frontend Setup

### 1. Flask Application Setup

#### 1.1. Create a Project Directory

Navigate back to the parent directory and create a new directory:

```bash
cd ..
mkdir flask_app
cd flask_app
```

#### 1.2. Create a Python Virtual Environment

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

- On macOS/Linux:

  ```bash
  source venv/bin/activate
  ```

- On Windows:

  ```bash
  venv\Scripts\activate
  ```

#### 1.3. Install Required Python Packages

Install Flask and ClickHouse driver:

```bash
pip install flask clickhouse-driver
```

Create a `requirements.txt` file:

```bash
pip freeze > requirements.txt
```

#### 1.4. Create the Flask Application

Create `app.py`:

```bash
touch app.py
```

Add the following content:

```python
from flask import Flask, render_template
from clickhouse_driver import Client

app = Flask(__name__)

client = Client(host='localhost')

@app.route('/')
def index():
    query = """
        SELECT timestamp, log_level, message, source
        FROM logs.application_logs
        ORDER BY timestamp DESC
        LIMIT 100
    """
    logs = client.execute(query)
    return render_template('index.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)
```

#### 1.5. Create the Template Directory and HTML File

Create a templates directory:

```bash
mkdir templates
```

Create `templates/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Log Analytics Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        h1 {
            text-align: center;
        }
        table {
            border-collapse: collapse;
            margin: 0 auto;
            width: 90%;
        }
        th, td {
            text-align: left;
            padding: 8px;
            font-size: 14px;
        }
        tr:nth-child(even) {background-color: #f2f2f2;}
        th {
            background-color: #4CAF50;
            color: white;
        }
        .container {
            width: 100%;
            margin: 0 auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Recent Logs</h1>
        <table border="1">
            <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Source</th>
                <th>Message</th>
            </tr>
            {% for log in logs %}
            <tr>
                <td>{{ log[0] }}</td>
                <td>{{ log[1] }}</td>
                <td>{{ log[3] }}</td>
                <td>{{ log[2] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
```

#### 1.6. Run the Flask Application Locally

Ensure the virtual environment is activated:

```bash
source venv/bin/activate  # Or venv\Scripts\activate on Windows
```

Set environment variables and run the app:

- On macOS/Linux:

  ```bash
  export FLASK_APP=app.py
  export FLASK_ENV=development
  flask run
  ```

- On Windows Command Prompt:

  ```cmd
  set FLASK_APP=app.py
  set FLASK_ENV=development
  flask run
  ```

- On Windows PowerShell:

  ```powershell
  $env:FLASK_APP = "app.py"
  $env:FLASK_ENV = "development"
  flask run
  ```

The application will be accessible at `http://127.0.0.1:5000/`.

#### 1.7. Test the Application

Open a web browser and navigate to `http://127.0.0.1:5000/`. You should see a table displaying the recent logs from ClickHouse.

---

### 2. Deploying to Replit

#### 2.1. Create a Replit Account

- Go to [Replit](https://replit.com/) and sign up or log in.

#### 2.2. Create a New Repl

- Click on **"Create"**.
- Choose **"Import from GitHub"** if you have your code in a GitHub repository.
- Alternatively, select **"Python"** as the language and name your Repl.

#### 2.3. Upload Your Flask Application

- Upload `app.py`, the `templates` directory, and `requirements.txt` to your Repl.
- You can drag and drop files or use the upload button.

#### 2.4. Install Dependencies on Replit

- In the Replit Shell, run:

  ```bash
  pip install -r requirements.txt
  ```

#### 2.5. Modify the Application for Replit

- **ClickHouse Accessibility**:

  - Replit cannot access your local ClickHouse instance directly.
  - Use a cloud-based ClickHouse instance or host ClickHouse on a server accessible over the internet.
  - Update the `client` initialization in `app.py`:

    ```python
    client = Client(
        host='your_clickhouse_host',
        user='your_username',
        password='your_password',
        port=9440,  # Adjust port if necessary
        secure=True,  # Use SSL/TLS if supported
    )
    ```

#### 2.6. Run the Flask Application on Replit

- Click the **"Run"** button at the top of the Replit editor.
- The Replit console will show the application logs.
- Click on the **"Open in new tab"** button to view the web application.

#### 2.7. Test the Application

- Ensure that the application is able to connect to the ClickHouse instance.
- If you encounter connection issues, check network configurations and ensure that your ClickHouse instance allows remote connections from Replit's IP ranges.

---

## Conclusion

You have successfully set up both the backend and frontend components of your real-time log analytics system. The backend collects and processes logs using Vector.dev, storing them in ClickHouse, while the frontend provides a web interface to view and analyze the logs.

By following best practices, including using virtual environments and containerization, you've created an isolated and manageable development environment.

---

## Additional Notes

### Security Considerations

- **Exposing ClickHouse**:
  - If you expose ClickHouse over the internet, ensure it's secured with proper authentication and encryption.
  - Use secure connections (`secure=True` in the ClickHouse client) and certificates if supported.

- **Credentials Management**:
  - Do not hard-code sensitive credentials in your code.
  - Use environment variables or configuration files excluded from version control.

### Cleanup

- **Stopping Docker Containers**:

  ```bash
  docker stop vector clickhouse-server
  ```

- **Removing Docker Containers**:

  ```bash
  docker rm vector clickhouse-server
  ```

- **Deactivating Virtual Environments**:

  ```bash
  deactivate
  ```

### Extending the Project

- **Implement Search and Filtering**:
  - Add functionality in the Flask app to search logs based on level, source, or message content.

- **Data Transformation with Airflow**:
  - Integrate Apache Airflow to schedule data transformation tasks, such as aggregating logs or generating reports.

- **Visualization Tools**:
  - Use tools like Grafana to create more advanced dashboards connected to ClickHouse.

- **Error Handling and Logging**:
  - Enhance the Flask app with proper error handling and logging mechanisms.

### Troubleshooting

- **Common Issues**:
  - **Connection Refused**: Ensure that all services are running and ports are correctly mapped.
  - **Module Not Found**: Verify that the virtual environment is activated and all dependencies are installed.

- **Logs and Debugging**:
  - Check Docker container logs using:

    ```bash
    docker logs clickhouse-server
    docker logs vector
    ```

  - Add debug statements or use breakpoints in your Python code to trace issues.

### Resources

- **ClickHouse Documentation**: [https://clickhouse.com/docs/en/](https://clickhouse.com/docs/en/)
- **Vector.dev Documentation**: [https://vector.dev/docs/](https://vector.dev/docs/)
- **Flask Documentation**: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- **ClickHouse Python Driver**: [https://github.com/mymarilyn/clickhouse-driver](https://github.com/mymarilyn/clickhouse-driver)

---
