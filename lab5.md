**Q1**
Loading the real MLflow model in a unit test would make the test depend on external services instead of only testing the code. The test could fail even when the code is correct if the MLflow server is offline, if the network connection fails, if the registered model or alias is unavilable, or if the model artifact cannot be downloaded. It would also make the tests much slower because the real model is large.

**Q2**
The fake-model test proves that the API can accept an uploaded image, preprocess it, call a model, interpret the model output, choose the correct category, and return valid JSON containing a category and confidence. It does not prove that the real trained Food-11 model is accurate, that MLflow can load the model correctly, or that the real model will predict Bread correctly.

**Q3**
The content-hash check detected the duplicate images across dataset splits. In my dataset, the validator actually found several pre-existing duplicates before I intentionaly added one, so I removed the later copies and then repeated the test by copying one training image into the evaluation split. The duplicate check failed as expected. A train/test duplicate is especially dangerous because it causes data leakage: the model can be evaluated on content it already saw during training. A corrupted image is usually easier to notice because it causes the pipeline to fail, whereas duplicated data can silently produce misleading evaluation results.

**Q4**
validate_data.py should run in places where the actual dataset is available. locally before pushing or updating the DVC-tracked dataset, so invalid data is caught before it is shared. A second place is on a machine or self-hosted CI/training runner that has access to the DVC remote, where the dataset can be pulled first and then validated. The normal GitHub-hosted CI runner cannot perform this check if the dataset is stored only in a local DVC remote, because that runner does not have access to the data.

**Q5**
The smoke job uses needs: test, so it only runs if the test job completes successfully. If a unit test or lint check fails, the smoke job is skipped. Without needs: test, GitHub Actions could run the two jobs independently or in parallel, so the Docker image might still be built and tested even though the unit tests failed.

**Q6**
The first successful CI run took 5 minutes 13 seconds. After pushing an empty commit and running the workflow again, the second run took 4 minutes 51 seconds, so it was 22 seconds faster. The dependency setup step became faster because setup-uv was configured with caching enabled, so some downloaded packages could be reused instead of being fetched again from scratch

**Q7**
Tagging the image with the commit SHA makes the image version immutable and traceable to the exact source code that produced it. Using only latest is ambiguous because the tag can be overwritten. For example, Machine A could pull latest in the morning, then a new image could be pushed with the same latest tag, and Machine B could pull it later. Both machines would appear to run latest, but they would actually be running different code. Using the commit SHA avoids this because both machines must explicitly pull the same immutable version.

**Q8**
The push job declares permissions: explicitly so the workflow receives only the access it needs: read access to the repository contents and write access to packages. This follows the principle of least privilege. If a compromised workflow step had a token with broad write access, it could potentially modify repository contents, publish or delete packages, change releases, or perform other actions using the repository's credentials. Restricting the token reduces the damage a compromised step could cause.

**Q9**
The pull request showed that the required CI checks were not successful. The deliberately broken code caused the test job to fail, and because the smoke job depends on test, it was skipped. The merge button was disabled because these checks were required by the branch protection rules. After fixing the code and pushing again, the checks passed and the pull request could be merged. This is safer for a team than relying on everyone to run tests manually, because GitHub enforces the checks automatically and prevents broken code from being merged even if someone forgets to test locally.

**Q10**
Candidate version 2 had a test accuracy of 0.1129, while the current champion, version 1, had an acuracy of 0.7723. With a test-set size of 1054, 2 × SE was 0.0258, or about 2.58 percentage points, so the promotion threshold was 0.7981. Version 2 was far below this threshold, so it was kept out of champion and assigned the challenger alias.Candidate 3 had a test accuracy of 0.7780. This was slightly higher than the champions 0.7723, but it was still below the required threshold of 0.7981. Therefore, version 1 remained champion, and version 3 was also assigned as challenger.In both cases, the gate rejected promotion. The important point is that a candidate does not become champion just because its raw accuracy is a little higher; it must improve by at least 2 × SE, which in this experiment was about 2.58 accuracy points.

**Q11**
promote.py cannot run on a normal GitHub-hosted runner while MLflow is only available on my laptop. One solution is to use a self-hosted GitHub Actions runner on a machine that can access the local MLflow server. Another solution is to move MLflow to a remotely accessible hosted service, such as DagsHub MLflow, so the promotion script can run automatically from a cloud CI/CD or training pipeline after a model is trained.

**Q12**
flowchart TD
    A[Developer] -->|git push| B[GitHub Repository]
    B --> C[GitHub Actions CI]
    C --> D[Test Job]
    D --> D1[uv sync]
    D --> D2[Ruff]
    D --> D3[Pytest]
    D --> E[Smoke Job]
    E --> E1[Build Docker Image]
    E --> E2[Start with SKIP_MODEL=1]
    E --> E3[Check /health]
    E --> F[Push Job - main only]
    F --> G[GitHub Container Registry]
    G --> H["Image tagged with Git commit SHA"]
    H --> I["CODE VERSION = commit SHA"]
    J[Model Training] --> K[MLflow Run]
    K --> L[MLflow Model Registry]
    L --> M["promote.py quality gate"]
    M -->|Pass| N["Move champion alias"]
    M -->|Fail| O["Assign challenger alias"]
    N --> P["MODEL VERSION = food11@champion"]
    O --> P
    H --> Q[Inference Container]
    P --> Q
    Q --> R[Running Food-11 API]
The code and model are versioned independently. The code version is selected by the Git commit SHA used to tag the Docker image in GHCR, while the model version is selected through the MLflow champion alias. Linting, testing, smoke testing, and image publishing are automatic after a push. Model training and starting the promotion process are still manual in the current setup, while the promotion decision itself is automated by promote.py.
