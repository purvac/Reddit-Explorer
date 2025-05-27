
# Airflow on Docker - My Setup Notes

This document contains essential notes and commands for running Apache Airflow using Docker Compose, focusing on initial setup, common operations, and troubleshooting.

## [Created a lightweight local version of Airflow with Docker](https://datatalks.club/blog/how-to-setup-lightweight-local-version-for-airflow.html)

## Why `docker-compose up airflow-init` first?

When bringing up an Airflow environment with Docker Compose, you typically run `docker-compose up airflow-init` before the full `docker-compose up`. This initial step is crucial for:

* **Database Initialization:** Airflow requires a database (like PostgreSQL) to store its metadata (DAG definitions, task states, connections, etc.). The `airflow-init` service runs commands such as `airflow db migrate` to set up the necessary database schema and `airflow users create` to establish an initial user for the Airflow UI.
* **Ensuring Dependencies:** This command ensures that your database service is fully up and ready before the Airflow webserver and scheduler try to connect to it.

Once `airflow-init` completes, its container usually exits, having fulfilled its one-time setup role.

## Essential Docker Compose Commands

Here are some key commands you'll use regularly:

1.  **`docker compose up airflow-init`**
    * **What it does:** Starts *only* the `airflow-init` service (and its dependencies, e.g., the database) as defined in your `docker-compose.yml`. This service performs crucial one-time setup steps like database migration and creating the initial Airflow user. The container will then exit upon completion.

2.   **`docker compose up`**
    * **Short Description:** This is the primary command to **build, create, start, and manage** all the services defined in your `docker-compose.yml` file. It brings your entire multi-container application stack to life. If containers already exist, it will start them; if their configuration or image has changed, it will recreate them.

3.  **`docker compose up --build`**
    * **What it does:** This is a variation of `docker compose up`.
        * It reads your `docker-compose.yml` and starts all defined services (webserver, scheduler, worker, database, etc.).
        * The `--build` flag tells Docker Compose to **rebuild the Docker images** for any services that have a `build` instruction in their definition (i.e., they are built from a `Dockerfile`). This is essential if you've made changes to your `Dockerfile`s or any code that gets copied into the image, ensuring your running containers use the latest image version.

4.  **`docker ps`**
    * **What it does:** Lists all **currently running** Docker containers on your system, along with their IDs, names, status, and port mappings.
    * **Use case:** Useful for quickly checking if your Airflow services are up and running, and to get the container ID/name if you need to `exec` into a specific container.

5.  **`docker compose down --volumes --rmi all`**
    * **What it does:** This is a powerful command to completely stop and clean up your Docker Compose project.
        * `docker compose down`: Stops and removes all containers, networks, and default volumes created by `docker compose up`.
        * `--volumes` (or `-v`): Removes any **named volumes** declared in the `volumes` section of your `docker-compose.yml` (e.g., for the database). **Be cautious:** This will delete your database data if your database uses a named volume, effectively resetting it!
        * `--rmi all`: Removes all images used by any service in your `docker-compose.yml`, even custom ones.
    * **Use case:** For a complete cleanup, starting fresh, or when you want to free up disk space. Use with extreme caution, especially with `--volumes`.

6.  **`docker exec -it <container-id> bash`**
    * **What it does:** Executes a command inside an **already running** Docker container.
        * `-it`: Stands for interactive (`-i`) and pseudo-TTY (`-t`), which allows you to interact with the shell (like typing commands).
        * `<container-id>`: Replace with the actual ID or name of the running container (e.g., `airflow-webserver`). You can get this from `docker ps`.
        * `bash`: The command to execute, which in this case opens an interactive bash shell within the container.
    * **Use case:** Debugging, inspecting files, running specific commands (like Airflow CLI commands), or getting an interactive terminal inside a container.

## Understanding `x-airflow-common` and Volume Mounting

In Airflow Docker Compose setups, you often see an `x-airflow-common` section used to define shared configurations:

```yaml
x-airflow-common:
  # ... other common settings
  volumes:
    - ./airflow/dags:/opt/airflow/dags
    - ./airflow/logs:/opt/airflow/logs
    - ./src:/usr/local/airflow/src
```

* **`x-airflow-common` Explained:** This is a YAML anchor that defines a block of common configurations. Services (like `airflow-webserver`, `airflow-scheduler`, `airflow-worker`) can then "inherit" these common settings using `<<: *x-airflow-common` (or whatever anchor name you choose). This avoids repeating the same configurations for multiple services, making your `docker-compose.yml` cleaner and easier to maintain.

* **Volumes in `x-airflow-common`:** The `volumes` listed within `x-airflow-common` are **accessible to all containers that inherit from it**.
    * For example, `- ./src:/usr/local/airflow/src` creates a **volume mount**. This means:
        * The `./src` directory on your **local host machine** (relative to where your `docker-compose.yml` is located)
        * is directly linked to the `/usr/local/airflow/src` directory **inside the Docker container**.
    * **Shared Space for Files:** This creates a shared, synchronized space between your host and the container. If your Python code inside the container writes a CSV file to `/usr/local/airflow/src/my_data.csv`, that file will **immediately appear in your local `./src/my_data.csv` on your host machine**. Conversely, any changes you make to files in `./src` on your host will be reflected instantly inside the container at `/usr/local/airflow/src`. This is incredibly useful for development, as it allows you to modify code on your host machine and have it instantly available within the running Docker containers without rebuilding images.

## Changing Airflow User Password (and other Airflow CLI tasks)

If you need to change an Airflow user's password, create a new user, or run any other Airflow Command Line Interface (CLI) commands, you must execute these commands **inside one of your running Airflow Docker containers** (typically the `webserver` or `scheduler` container, as they have the Airflow CLI installed and access to the metadata database).

Here's the general process:

1.  **Get into the Container's Bash Terminal:**
    * First, identify the container ID or name of your Airflow webserver (or scheduler) using `docker ps`.
    * Then, execute a bash shell inside it:
        ```bash
        docker exec -it <your_airflow_webserver_container_id_or_name> bash
        # Example: docker exec -it airflow-webserver-1 bash
        ```

2.  **Execute Airflow CLI Command:**
    * Once you are inside the container's bash prompt, you can run the Airflow CLI commands directly.
    * **To change a password:**
        ```bash
        airflow users set-password -u <username> -p <new_password>
        ```
        (Replace `<username>` and `<new_password>`)
    * **To create a new user:**
        ```bash
        airflow users create \
            --username <new_username> \
            --firstname <First> \
            --lastname <Last> \
            --role Admin \
            --email <email@example.com> \
            --password <new_password>
        ```
        (Replace placeholders with your desired values)

3.  **Exit the Container:**
    * Once done, simply type `exit` to leave the container's shell:
        ```bash
        exit
        ```

The changes made via the `airflow users` commands are instantly updated in the Airflow metadata database and will be reflected in the Airflow UI without needing to restart the webserver in most cases.
<<<<<<< HEAD
=======


# Understanding docker-compose.yaml: 
```
FROM apache/airflow:2.10.3
ADD requirements.txt . # copy the requirements.txt file into the docker image's current working directory (which is typically /opt/airflow)
RUN pip install -r requirements.txt # Install the Python packages listed in requirements.txt
RUN pip install redis # Install the 'redis' Python client. This is often needed if Airflow uses Redis for caching, XComs, or Celery executor.
RUN pip install python-dotenv # Useful for loading environment variables from .env files. 
```
>>>>>>> 21f11b6 (initial commit docker-info.md)
