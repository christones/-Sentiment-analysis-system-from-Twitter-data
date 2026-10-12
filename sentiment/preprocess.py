"""Tweet cleaning and tokenization shared by the notebook, the model and the API.

Keeping this in one module guarantees that the text the API receives is
processed exactly the same way as the text the model was trained on.
"""
import html
import re

from sklearn.base import BaseEstimator, TransformerMixin

URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
REPEAT_RE = re.compile(r"(\w)\1{2,}")          # "soooo" -> "soo"
NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")      # special characters
SPACES_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[a-z0-9]+")


def clean_text(text):
    """Remove URLs, mentions and special characters, then lowercase."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    text = html.unescape(text)                 # &amp; -> &, &quot; -> "
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = HASHTAG_RE.sub(r"\1", text)         # keep the hashtag word
    text = text.lower()
    text = text.replace("'", "")               # don't -> dont (keeps negation)
    text = REPEAT_RE.sub(r"\1\1", text)
    text = NON_ALNUM_RE.sub(" ", text)
    return SPACES_RE.sub(" ", text).strip()


def tokenize(text):
    """Split already-cleaned text into lowercase word tokens."""
    return TOKEN_RE.findall(text.lower())


def preprocess_tweet(text):
    """clean_text + tokenize in one call."""
    return tokenize(clean_text(text))


class TextCleaner(BaseEstimator, TransformerMixin):
    """Stateless sklearn step so the saved Pipeline cleans raw tweets itself."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [clean_text(t) for t in X]

    def __sklearn_is_fitted__(self):
        return True
