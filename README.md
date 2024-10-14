# Real-Time Log Analytics System with ClickHouse, Vector.dev, and Python

![Log Analytics Dashboard](https://github.com/NamanSudan/LogStream-Observatory/blob/main/log_gen_ui.png)

## Table of Contents

- [Introduction](#introduction)
- [Architecture](#architecture)
- [Components](#components)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [1. ClickHouse Setup](#1-clickhouse-setup)
  - [2. Vector.dev Setup](#2-vectordev-setup)
  - [3. Log Generator Setup](#3-log-generator-setup)
  - [4. Flask Web Application Setup](#4-flask-web-application-setup)
- [Running the Project](#running-the-project)
- [Testing the System](#testing-the-system)
- [Deployment to Replit](#deployment-to-replit)
- [Future Enhancements](#future-enhancements)
- [Troubleshooting](#troubleshooting)
- [Conclusion](#conclusion)
- [References](#references)

---

## Introduction

This project implements a real-time log analytics system using ClickHouse, Vector.dev, and Python. The system collects application logs, processes them through a data pipeline, stores them in ClickHouse, and provides a web-based user interface for visualization and analysis.

This project demonstrates proficiency in data pipeline technologies, large-scale data analytics platforms, and observability solutions, relevant to a ClickHouse Data Engineer role.

---

## Architecture

```plaintext
+----------------+       +-----------+       +------------+       +------------------+
|                |       |           |       |            |       |                  |
|  Log Generator +------->  Vector   +------->  ClickHouse+------->  Flask Web App   |
|  (Python)      |       |  (Vector) |       |            |       |  (Python/Flask)  |
|                |       |           |       |            |       |                  |
+----------------+       +-----------+       +------------+       +------------------+
```

---

## Components

1. **Log Generator**: A Python script that simulates application logs and sends them to Vector.dev.

2. **Vector.dev**: An open-source observability data pipeline that receives logs from the Log Generator, processes them, and forwards them to ClickHouse.

3. **ClickHouse**: A column-oriented database management system that stores the processed logs for analytical querying.

4. **Flask Web Application**: A Python web app that connects to ClickHouse to retrieve and display logs through a user-friendly interface.

---

## Prerequisites

Ensure you have the following installed on your machine:

- **Docker**: For running ClickHouse and Vector.dev containers.
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop)

- **Python 3.7 or higher**: For running Python scripts and applications.
  - [Download Python](https://www.python.org/downloads/)

- **Git**: For version control (optional but recommended).
  - [Download Git](https://git-scm.com/downloads)

---

## Setup Instructions

### 1. ClickHouse Setup

#### 1.1. Pull the ClickHouse Docker Image

```bash
docker pull clickhouse/clickhouse-server:latest
```

#### 1.2. Run the ClickHouse Server

```bash
docker run -d \
  --name clickhouse-server \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server:latest
```

#### 1.3. Create the Database and Table

Access the ClickHouse client:

```bash
docker exec -it clickhouse-server clickhouse-client
```

Within the client, execute the following commands:

```sql
-- Create the 'logs' database
CREATE DATABASE IF NOT EXISTS logs;

-- Use the 'logs' database
USE logs;

-- Create the 'application_logs' table
CREATE TABLE IF NOT EXISTS application_logs (
    timestamp DateTime,
    log_level String,
    message String,
    source String
) ENGINE = MergeTree()
ORDER BY timestamp;
```

Exit the client:

```sql
EXIT;
```

---

### 2. Vector.dev Setup

#### 2.1. Pull the Vector.dev Docker Image

```bash
docker pull timberio/vector:latest-alpine
```

#### 2.2. Create a Vector.dev Configuration File

Create a directory and configuration file:

```bash
mkdir vector
cd vector
touch vector.toml
```

Edit `vector.toml` with the following content:

```toml
# vector.toml

[sources.log_generator]
  type = "socket"
  address = "0.0.0.0:9001"
  mode = "tcp"

[sinks.clickhouse]
  type = "clickhouse"
  inputs = ["log_generator"]
  database = "logs"
  table = "application_logs"
  endpoint = "http://clickhouse-server:8123/"
  skip_unknown_fields = true
  encoding.codec = "json"
```

#### 2.3. Create a Docker Network

```bash
docker network create vector-net
```

#### 2.4. Run the ClickHouse Server on the Network

Stop and remove existing ClickHouse container (if needed):

```bash
docker stop clickhouse-server
docker rm clickhouse-server
```

Run the ClickHouse container on `vector-net`:

```bash
docker run -d \
  --name clickhouse-server \
  --network vector-net \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server:latest
```

#### 2.5. Run the Vector.dev Container

```bash
docker run -d \
  --name vector \
  --network vector-net \
  -p 9001:9001 \
  -v $(pwd)/vector.toml:/etc/vector/vector.toml:ro \
  timberio/vector:latest-alpine
```

---

### 3. Log Generator Setup

#### 3.1. Create a Project Directory

```bash
mkdir log_generator
cd log_generator
```

#### 3.2. Create a Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate
```

#### 3.3. Install Dependencies

If using TCP sockets, no additional dependencies are required.

If using HTTP, install `requests`:

```bash
pip install requests
```

Create a `requirements.txt` file:

```bash
pip freeze > requirements.txt
```

#### 3.4. Write the Log Generator Script (`log_generator.py`)

**Using TCP Sockets:**

```python
import time
import random
import socket
import json

VECTOR_HOST = 'localhost'
VECTOR_PORT = 9001

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

#### 3.5. Run the Log Generator

Activate the virtual environment and run the script:

```bash
python log_generator.py
```

---

### 4. Flask Web Application Setup

#### 4.1. Create the Project Structure

```bash
mkdir flask_app
cd flask_app
```

#### 4.2. Create a Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate
```

#### 4.3. Install Dependencies

```bash
pip install flask clickhouse-driver
pip freeze > requirements.txt
```

#### 4.4. Write the Application Script (`app.py`)

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

#### 4.5. Create the Template (`templates/index.html`)

Create a `templates` directory:

```bash
mkdir templates
```

Create `templates/index.html` with the following content:

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

---

## Running the Project

### 1. Start the Docker Containers

Ensure that both ClickHouse and Vector.dev containers are running:

```bash
docker start clickhouse-server
docker start vector
```

### 2. Run the Log Generator

In the `log_generator` directory:

```bash
source venv/bin/activate
python log_generator.py
```

### 3. Run the Flask Web Application

In the `flask_app` directory:

```bash
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

Access the application at `http://127.0.0.1:5000/`.

---

## Testing the System

- **Verify Data Flow**: Ensure that logs generated by the Log Generator are received by Vector.dev and stored in ClickHouse.
- **Check ClickHouse Data**:

  ```bash
  docker exec -it clickhouse-server clickhouse-client
  ```

  ```sql
  SELECT * FROM logs.application_logs LIMIT 10;
  ```

- **Test the Web Application**: Navigate to `http://127.0.0.1:5000/` and verify that logs are displayed correctly.

---

## Deployment to Replit

Due to network restrictions, Replit cannot access local instances of ClickHouse. To deploy the Flask application to Replit:

1. **Set Up a Remote ClickHouse Instance**:

   - Use a cloud-based ClickHouse service (e.g., ClickHouse Cloud, Altinity.Cloud).
   - Ensure the remote ClickHouse instance is securely accessible over the internet.

2. **Modify the Flask Application**:

   Update the ClickHouse client in `app.py`:

   ```python
   client = Client(
       host='your_remote_clickhouse_host',
       user='your_username',
       password='your_password',
       port=9440,  # Adjust port if necessary
       secure=True,
   )
   ```

3. **Create a Replit Account and New Repl**:

   - Sign up at [Replit](https://replit.com/).
   - Create a new Python Repl.

4. **Upload your Files**:

   - Upload `app.py`, the `templates` directory, and `requirements.txt`.

5. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

6. **Run the Application**:

   - Click the **"Run"** button in Replit.
   - Access your application via the provided URL.

---

## Future Enhancements

- **Implement Search and Filtering**: Allow users to search logs by log level, source, or message content.
- **Pagination and Sorting**: Add pagination and enable sorting by different columns.
- **Advanced Visualization**: Integrate with visualization tools like Grafana.
- **Error Handling and Logging**: Improve robustness by handling exceptions and logging errors.
- **Authentication**: Secure the web application to prevent unauthorized access.
- **Scaling the Log Generator**: Simulate higher volumes of logs to test system scalability.

---

## Troubleshooting

- **Docker Networking Issues**:

  - Ensure that the Docker network `vector-net` exists and containers are connected to it.

- **Connection Refused Errors**:

  - Verify that all services are running (`docker ps`).
  - Check that ports are correctly mapped and not in use by other applications.

- **Module Not Found Errors**:

  - Ensure virtual environments are activated.
  - Verify that all dependencies are installed (`pip install -r requirements.txt`).

- **Logs and Debugging**:

  - View Docker container logs:

    ```bash
    docker logs clickhouse-server
    docker logs vector
    ```

---

## Conclusion

This real-time log analytics system showcases the integration of ClickHouse, Vector.dev, and Python to collect, process, store, and visualize log data. It demonstrates key skills in data pipeline design, large-scale data analytics, and web application development.

By following this guide, you can set up the system, understand its components, and explore enhancements to extend its functionality.

---

## References

- **ClickHouse Documentation**: [https://clickhouse.com/docs/en/](https://clickhouse.com/docs/en/)
- **Vector.dev Documentation**: [https://vector.dev/docs/](https://vector.dev/docs/)
- **Flask Documentation**: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- **ClickHouse Python Driver**: [https://github.com/mymarilyn/clickhouse-driver](https://github.com/mymarilyn/clickhouse-driver)
- **Docker Documentation**: [https://docs.docker.com/](https://docs.docker.com/)

---