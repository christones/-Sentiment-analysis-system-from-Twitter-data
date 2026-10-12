"""Flask API that classifies the sentiment of a tweet.

Endpoints
    GET  /health         liveness/readiness probe
    GET  /model-info     which model version is being served, with its metrics
    POST /predict        {"tweet": "I love this!"}
    POST /predict/batch  {"tweets": ["...", "..."]}
"""
import logging
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sentiment import clean_text, load_model  # noqa: E402

LABELS = {0: "negative", 1: "positive"}
MAX_BATCH = 1000
MAX_CHARS = 1000

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sentiment-api")


def create_app(model_version=None, models_dir=None):
    app = Flask(__name__)
    kwargs = {"version": model_version}
    if models_dir:
        kwargs["models_dir"] = models_dir
    model, metadata = load_model(**kwargs)
    version = metadata.get("version")
    log.info("Loaded sentiment model %s", version)

    def classify(tweets):
        probs = model.predict_proba(tweets)[:, 1]
        results = []
        for tweet, p in zip(tweets, probs):
            label = int(p >= 0.5)
            results.append({
                "tweet": tweet,
                "cleaned": clean_text(tweet),
                "sentiment": LABELS[label],
                "label": label,
                "confidence": round(float(p if label else 1 - p), 4),
                "model_version": version,
            })
        return results

    def bad_request(message):
        return jsonify({"error": message}), 400

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "model_version": version})

    @app.get("/model-info")
    def model_info():
        return jsonify(metadata)

    @app.post("/predict")
    def predict():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or "tweet" not in data:
            return bad_request('Send JSON like {"tweet": "your text"}')
        tweet = data["tweet"]
        if not isinstance(tweet, str) or not tweet.strip():
            return bad_request('"tweet" must be a non-empty string')
        if len(tweet) > MAX_CHARS:
            return bad_request(f'"tweet" must be at most {MAX_CHARS} characters')
        return jsonify(classify([tweet])[0])

    @app.post("/predict/batch")
    def predict_batch():
        data = request.get_json(silent=True)
        tweets = data.get("tweets") if isinstance(data, dict) else None
        if not isinstance(tweets, list) or not tweets:
            return bad_request('Send JSON like {"tweets": ["text 1", "text 2"]}')
        if len(tweets) > MAX_BATCH:
            return bad_request(f"At most {MAX_BATCH} tweets per request")
        if not all(isinstance(t, str) and t.strip() and len(t) <= MAX_CHARS for t in tweets):
            return bad_request(f"Every tweet must be a non-empty string of at most {MAX_CHARS} characters")
        return jsonify({"model_version": version, "results": classify(tweets)})

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
