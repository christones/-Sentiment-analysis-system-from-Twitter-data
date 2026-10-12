import pytest

POSITIVE = [
    "I love this so much, best day ever!",
    "Thank you, this is awesome and makes me so happy :)",
    "Great news, I am really excited and grateful",
]
NEGATIVE = [
    "I hate this, worst day ever",
    "So sad and disappointed, this is terrible :(",
    "I feel sick and miserable, everything is awful",
]


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok"
    assert body["model_version"]


def test_model_info(client):
    res = client.get("/model-info")
    assert res.status_code == 200
    assert "version" in res.get_json()


def test_predict_response_shape(client):
    res = client.post("/predict", json={"tweet": "@friend I love it! http://t.co/x"})
    assert res.status_code == 200
    body = res.get_json()
    assert set(body) >= {"tweet", "cleaned", "sentiment", "label", "confidence", "model_version"}
    assert body["sentiment"] in {"positive", "negative"}
    assert 0.5 <= body["confidence"] <= 1.0
    assert "http" not in body["cleaned"] and "@" not in body["cleaned"]


@pytest.mark.parametrize("tweet", POSITIVE)
def test_predict_positive(client, tweet):
    res = client.post("/predict", json={"tweet": tweet})
    assert res.status_code == 200
    assert res.get_json()["sentiment"] == "positive"


@pytest.mark.parametrize("tweet", NEGATIVE)
def test_predict_negative(client, tweet):
    res = client.post("/predict", json={"tweet": tweet})
    assert res.status_code == 200
    assert res.get_json()["sentiment"] == "negative"


def test_batch(client):
    res = client.post("/predict/batch", json={"tweets": POSITIVE + NEGATIVE})
    assert res.status_code == 200
    labels = [r["sentiment"] for r in res.get_json()["results"]]
    assert labels == ["positive"] * len(POSITIVE) + ["negative"] * len(NEGATIVE)


@pytest.mark.parametrize("payload", [None, {}, {"text": "hi"}, {"tweet": ""},
                                     {"tweet": "   "}, {"tweet": 42}, {"tweet": "x" * 1001}])
def test_predict_rejects_bad_input(client, payload):
    res = client.post("/predict", json=payload) if payload is not None else \
        client.post("/predict", data="not json", content_type="text/plain")
    assert res.status_code == 400
    assert "error" in res.get_json()


@pytest.mark.parametrize("payload", [{}, {"tweets": []}, {"tweets": "hi"}, {"tweets": ["ok", ""]}])
def test_batch_rejects_bad_input(client, payload):
    res = client.post("/predict/batch", json=payload)
    assert res.status_code == 400
