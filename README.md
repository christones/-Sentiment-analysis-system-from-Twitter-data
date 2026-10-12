# Twitter Sentiment Analysis System

End-to-end MLOps project: Sentiment140 tweets -> cleaning -> TF-IDF + logistic regression ->
Flask API -> Docker -> GitHub Actions CI/CD -> Kubernetes.

Everything is walked through, step by step, in **`Sentiment_Analysis_Pipeline.ipynb`**.

## Project layout

```
.
|-- Sentiment_Analysis_Pipeline.ipynb   # the whole project, step by step
|-- data/                               # downloaded Sentiment140 data (not committed)
|-- sentiment/                          # shared code
|   |-- preprocess.py                   # clean_text / tokenize (used in training AND the API)
|   `-- model_store.py                  # versioned model registry
|-- app/                                # Flask API
|   |-- app.py
|   `-- wsgi.py                         # gunicorn entry point
|-- models/                             # versioned models (v1, v2, ...) + registry.json
|-- tests/                              # pytest: preprocessing + API tests
|-- Dockerfile  .dockerignore
|-- .github/workflows/ci-cd.yml         # test -> build -> smoke test -> push -> deploy
|-- k8s/                                # namespace, deployment, service, autoscaler
|-- MODEL_VERSIONING.md                 # versioning + rollback guide
|-- requirements.txt                    # API runtime deps
|-- requirements-dev.txt                # notebook + test deps
`-- requirements-bert.txt               # optional torch/transformers for BERT experiments
```

## Quick start

```bash
pip install -r requirements-dev.txt
jupyter notebook Sentiment_Analysis_Pipeline.ipynb   # downloads Sentiment140 on first run, then trains models/v1
pytest -v
python app/app.py                                     # http://localhost:5000
curl -X POST localhost:5000/predict -H "Content-Type: application/json" -d "{\"tweet\": \"I love this!\"}"
```

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | - | `{"status": "ok", "model_version": "v1"}` |
| GET | `/model-info` | - | metadata + metrics of the served model |
| POST | `/predict` | `{"tweet": "..."}` | `sentiment`, `label` (0/1), `confidence`, `cleaned`, `model_version` |
| POST | `/predict/batch` | `{"tweets": ["...", "..."]}` | list of the above (max 1000) |

## Docker

```bash
docker build -t <dockerhub-user>/sentiment-api:latest .
docker run -p 5000:5000 <dockerhub-user>/sentiment-api:latest
docker login && docker push <dockerhub-user>/sentiment-api:latest
```

## CI/CD (GitHub Actions)

Add these repository secrets (*Settings -> Secrets and variables -> Actions*):

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | your Docker Hub username |
| `DOCKERHUB_TOKEN` | a Docker Hub access token (*Account settings -> Personal access tokens*) |
| `KUBE_CONFIG` *(optional)* | `base64` of a kubeconfig for a reachable cluster - enables the deploy job |

On every push / PR: lint + pytest. On push to `main`: build image, smoke-test it, push to Docker Hub with tags
`latest`, `sha-<commit>`, `model-<version>`, then deploy to Kubernetes if `KUBE_CONFIG` is set.

## Kubernetes

```bash
# replace DOCKERHUB_USERNAME in k8s/deployment.yaml first (the notebook does it for you)
kubectl apply -f k8s/
kubectl -n sentiment get pods,svc,hpa
curl -X POST http://localhost:30080/predict -H "Content-Type: application/json" -d "{\"tweet\": \"great day\"}"
```

On minikube use `minikube service sentiment-api -n sentiment --url` for the URL and
`minikube addons enable metrics-server` for autoscaling. On AWS EKS change the Service to `type: LoadBalancer`.

Model versioning and rollback: see [MODEL_VERSIONING.md](MODEL_VERSIONING.md).
