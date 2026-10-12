**Q1**
the MLflow database and artifacts are written inside the container's own writable filesystem. They remain while that specific container exists, but if the container is removed and a new container is created from the same image, that data is gone. The new container starts with a fresh MLflow database and an empty registry.

**Q2**
A named volume is useful because Docker manages it separately from the lifecycle of any individual container. This allows MLflow's database and artifacts to survive docker compose down and later be attached to a new MLflow container. A bind mount to a normal host folder could also work, especially for development, but it ties the setup to a specific host filesystem path.

**Q3**
In Lab 3, MLflow was running on the host machine, so the inference container had to use host.docker.internal to reach it. In Lab 4, Docker Compose puts the services on the same private network and provides DNS between them. Because of that, the hostname mlflow automatically resolves to the MLflow container, so the inference service can simply use http://mlflow:5000

**Q4**
The frontend reads urlL from an environment variable so the same image can be used in different environments. Inside Docker Compose it can use http://inference:8000, while if the frontend is run by itself it can use another address such as http://127.0.0.1:8000. Hardcoding the Compose hostname would make the image less reusable outside Compose.

**Q5**
The inference service does not publish port 8000 to the host because only the frontend needs to communicate with it. Both containers are on the same Compose network, so the frontend can reach it directly using http://inference:8000. A host port is only needed for services that a user needs to access directly, such as the MLflow UI on port 5000 and the Streamlit frontend on port 8501.

**Q6**
depends_on only controls the order in which containers are started. It does not guarantee that MLflow is ready or that the required registered model already exists. Since the inference service loads the model at startup, if MLflow is unavailable or the requested model cannot be found, the inference process fails and the container exits. In my case, MLflow was running, but the new registry did not yet contain food11, so the inference container exited

**Q7**
The mlflow service publishes port 5000 and the frontend service publishes port 8501. The inference service does not publish a port to the host; it only exposes port 8000 inside the Compose network. This matches the Compose file because the frontend can reach inference using the service name http://inference:8000, so the host does not need direct access to that port.

**Q8**
Changing the model alias in MLflow does not immediately change the model used by the running inference service, because serve.py loads the model only once at startup. The running container therefore continues using the old model until it is restarted. Running docker compose restart inference causes the service to start again and resolve the current food11@champion alias, so it picks up the new model version without rebuilding the image.

**Q9**
A restart is enough because the inference image contains the serving application and dependencies, but the model is loaded from MLflow at container startup. The image itself does not need to change when the active registered model version changes, so no rebuild is required.

**Q10**
After a normal docker compose down and docker compose up, the registered model and the champion alias were still there because the named volume was preserved.
After using docker compose down -v, the volume was deleted. When the stack was started again, MLflow started with a fresh database, so the registered models, versions, aliases, and artifacts were gone. This shows that the named volume is what provides persistence for MLflow data.

**Q11**
Docker Compose is mainly designed to run multiple containers on a single machine. To run several replicas of the inference service behind a load balancer, or to keep MLflow available if one machine fails, I would need a container orchestration platform such as Kubernetes or Docker Swarm.
An orchestrator can provide features such as replicas, service discovery, load balancing, health checks, automatic restarts, rolling updates, and scheduling containers across multiple machines. For MLflow, I would also need storage and a database that are not tied to one machine, such as a remote database and shared or cloud object storage.