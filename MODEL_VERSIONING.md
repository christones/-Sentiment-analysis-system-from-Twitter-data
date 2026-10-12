# Model versioning and rollback

## How models are versioned

Every training run in the notebook calls `save_model_version(...)`, which:

1. Saves the fitted pipeline (cleaning + TF-IDF + logistic regression) to `models/vN/model.joblib`.
2. Writes `models/vN/metadata.json` with the creation time, validation/test metrics, hyper-parameters and notes.
3. Adds the version to `models/registry.json` and makes it the `current` one.

```
models/
  registry.json        {"current": "v2", "versions": {"v1": {...}, "v2": {...}}}
  v1/model.joblib
  v1/metadata.json
  v2/model.joblib
  v2/metadata.json
```

The `models/` folder is committed to Git, so **each commit records exactly which model was current**, and
every saved version is baked into the Docker image.

The API picks the version to serve in this order:

| Priority | Source | Typical use |
|---|---|---|
| 1 | `MODEL_VERSION` environment variable | Fast rollback in Docker / Kubernetes |
| 2 | `"current"` in `models/registry.json` | Normal operation |

`GET /model-info` and every `/predict` response report the `model_version` being served.

## How Docker images are tagged

The CI/CD pipeline pushes each build to Docker Hub with three tags:

| Tag | Meaning |
|---|---|
| `latest` | Most recent build of `main` |
| `sha-<7 chars>` | Exact Git commit - immutable, use this to roll back code + model together |
| `model-vN` | The model version that build serves by default |

## Rolling back

Pick the option that matches what went wrong.

**A. The new model is worse, the code is fine - switch model version (seconds, no rebuild)**

```bash
# Kubernetes
kubectl -n sentiment set env deployment/sentiment-api MODEL_VERSION=v1
kubectl -n sentiment rollout status deployment/sentiment-api

# Docker
docker run -p 5000:5000 -e MODEL_VERSION=v1 <user>/sentiment-api:latest
```

Undo it with `kubectl -n sentiment set env deployment/sentiment-api MODEL_VERSION-` (trailing dash removes the variable).

**B. A whole release is broken - roll the Kubernetes deployment back**

```bash
kubectl -n sentiment rollout history deployment/sentiment-api
kubectl -n sentiment rollout undo deployment/sentiment-api                 # previous revision
kubectl -n sentiment rollout undo deployment/sentiment-api --to-revision=3 # specific revision
```

The CI deploy job also runs `rollout undo` automatically if a new rollout doesn't become healthy.

**C. Pin an exact earlier image**

```bash
kubectl -n sentiment set image deployment/sentiment-api sentiment-api=<user>/sentiment-api:sha-abc1234
```

**D. Make the rollback permanent in Git** (so the next CI run doesn't redeploy the bad model)

```python
from sentiment.model_store import set_current_version
set_current_version("v1")   # rewrites models/registry.json
```

then commit and push - or `git revert <commit>` the commit that introduced the bad model. CI rebuilds,
tests and redeploys automatically.

**E. Re-run CI for a specific model** - in GitHub, *Actions -> CI/CD - Sentiment API -> Run workflow*,
enter e.g. `v1` as `model_version`.
