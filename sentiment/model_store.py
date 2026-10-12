"""Tiny file-based model registry.

Layout:
    models/
      registry.json          {"current": "v2", "versions": {"v1": {...}, "v2": {...}}}
      v1/model.joblib
      v1/metadata.json
      v2/...

The version that gets served is chosen in this order:
    1. the `version` argument
    2. the MODEL_VERSION environment variable (used for rollbacks in Docker/K8s)
    3. "current" in registry.json
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import joblib

DEFAULT_MODELS_DIR = Path(os.environ.get(
    "MODELS_DIR", Path(__file__).resolve().parent.parent / "models"))


def _registry_path(models_dir):
    return Path(models_dir) / "registry.json"


def read_registry(models_dir=DEFAULT_MODELS_DIR):
    path = _registry_path(models_dir)
    if not path.exists():
        return {"current": None, "versions": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_registry(registry, models_dir):
    path = _registry_path(models_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _next_version(registry):
    nums = [int(m.group(1)) for v in registry["versions"]
            if (m := re.fullmatch(r"v(\d+)", v))]
    return f"v{max(nums, default=0) + 1}"


def save_model_version(pipeline, metrics, params=None, notes="",
                       models_dir=DEFAULT_MODELS_DIR, set_current=True):
    """Save a fitted pipeline as the next version (v1, v2, ...) and register it."""
    models_dir = Path(models_dir)
    registry = read_registry(models_dir)
    version = _next_version(registry)
    vdir = models_dir / version
    vdir.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, vdir / "model.joblib", compress=3)
    metadata = {
        "version": version,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metrics": metrics,
        "params": params or {},
        "notes": notes,
        "size_mb": round((vdir / "model.joblib").stat().st_size / 1e6, 2),
    }
    (vdir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    registry["versions"][version] = {
        k: metadata[k] for k in ("created_utc", "metrics", "notes")}
    if set_current or registry["current"] is None:
        registry["current"] = version
    _write_registry(registry, models_dir)
    return version


def set_current_version(version, models_dir=DEFAULT_MODELS_DIR):
    """Point the registry at another saved version (a rollback without rebuilding)."""
    registry = read_registry(models_dir)
    if version not in registry["versions"]:
        raise ValueError(f"Unknown model version {version!r}; "
                         f"available: {sorted(registry['versions'])}")
    registry["current"] = version
    _write_registry(registry, models_dir)


def resolve_version(version=None, models_dir=DEFAULT_MODELS_DIR):
    version = version or os.environ.get("MODEL_VERSION") or read_registry(models_dir)["current"]
    if not version:
        raise FileNotFoundError(
            f"No trained model found in {models_dir}. Run the notebook's training section first.")
    return version


def load_model(version=None, models_dir=DEFAULT_MODELS_DIR):
    """Return (pipeline, metadata) for the requested / configured version."""
    version = resolve_version(version, models_dir)
    vdir = Path(models_dir) / version
    if not (vdir / "model.joblib").exists():
        raise FileNotFoundError(f"Model file missing: {vdir / 'model.joblib'}")
    pipeline = joblib.load(vdir / "model.joblib")
    meta_path = vdir / "metadata.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    metadata.setdefault("version", version)
    return pipeline, metadata
