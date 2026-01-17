## Project Setup Instructions: 

### Prerequisites

Before you begin, ensure the following are installed on your system:

- **Python 3.10 or higher**
- **Docker Desktop** (Mac/Windows) or **Docker Engine** (Linux)

You will also need:
- A **Reddit Developer account** (to obtain API credentials)

---

### 1. Clone the Repository

```
git clone https://github.com/purvac/Reddit-Explorer.git
cd Reddit-Explorer
```
### 2. Install Python Dependencies

This project includes Python scripts that are used by Airflow tasks.
```
pip install -r requirements.txt
```
### 3. Configure Environment Variables

Create a .env file in the same directory as docker_compose.yaml file and fill in the required variable values.
```
AIRFLOW_UID=<airflow-uid-number>
client_id=<client-id-value>
client_secret=<client-secret-value>
user_agent=<user-agent-name>
password=<password>
username=<reddit-username>
```
Create ~/.aws/credentials file and store the following variables in it
```
[default]
aws_access_key_id=<aws-access-key>
aws_secret_access_key=<aws-secret-key>
```

### 4. 4. Start the Docker Containers

Start all required services (Airflow, scheduler, workers, etc.) using Docker Compose:
```
docker compose up airflow-init
docker compose up
```

To rebuild containers:
```
docker compose up --build
```

For a full list of useful Docker commands, refer [here](https://github.com/purvac/Reddit-Explorer/blob/master/documentation/docker-info.md)

### 5. Access the Airflow Web Interface

Once the containers are running, open your browser and go to:
```
http://localhost:8080
```
If you have issues logging in to the Airflow web interface, you can access the Airflow container and reset credentials from inside the container.

### 6. Run the Reddit Pipeline

In the Airflow UI, locate the DAG named 'reddit_dag'. Turn the DAG on and run the DAG to start the pipeline. 
