**Q1**
The registered model was given version 1. The logged model artifact belongs to a specific MLflow run and is stored as an output of that training run. A registered model is a separately managed model entry in the MLflow Model Registry, where the same model name can have multiple versions created from different runs.

**Q2**
MLflow uss aliases lik champion instead of the old built in stages like Staging and Production. The model is versioned separately from the run so multiple trained runs can contribute different versions under the same registered model name. An alias is more flexible because it is just a pointer to a model version, so champion can later be moved from version 1 to version 2 without changing the model name or deleting the old version.

**Q3**
Loading the model using models:/food11@champion avoids depending on a specific .pth file path and lets the serving code use whichever registered model version currently has the champion alias.

**Q4**
pyproject.toml and uv.lock are copied before the source code so Docker can cache the dependency installation layer. If only serve.py changes, Docker can reuse the dependency layer instead of reinstalling all packages, which makes rebuilding much faster.

**Q5**
The multi-stage image was about 6.28 GB, while the single-stage image was about 6.38 GB, so the multi-stage build saved roughly 100 MB. The difference is not very large because most of the image size comes from the Python virtual environment, especially PyTorch, torchvision, and their dependencies. From docker history, the largest layer in both images is the environment itself, at around 6.16–6.18 GB. The single-stage image also keeps build-time tools such as uv, which adds extra size.

**Q6**
Without a .dockerignore, Docker sends unnecessary files such as the dataset, Git history, local virtual environment, MLflow artifacts, and caches into the build context. This makes builds slower and can make the image larger. Large folders such as .venv/, data/, and mlruns/ are especially unnecessary and can cause problems because they may contain platform-specific files or a very large amount of data.

**Q7**
The container cannot use 127.0.0.1:5000 to reach the MLflow server on the host because inside the container, 127.0.0.1 refers to the container itself, not to the Windows machine running Docker.host.docker.internal resolves to the host machine, so the container can use http://host.docker.internal:5000 to reach the MLflow server running outside the container.

**Q8**
After stopping the container and starting a new one from the same Docker image, the model still loaded correctly without rebuilding the image. This shows that the application code and Python environment are baked into the image, while the registered model is resolved and loaded at runtime through MLflow. In my setup, the actual model artifact is accessed from the mounted mlruns directory on the host.

**Q9**
The Dockerfile is versioned in Git, but the built Docker image is only stored locally on my machine. Before another machine, CI runner, or Kubernetes cluster can reliably run the exact same image, the image needs to be pushed to a container registry such as Docker Hub, GitHub Container Registry, or another registry. It should also be tagged with a specific version instead of relying only on latest, so the exact image can be pulled and reproduced later.