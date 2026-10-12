from sentiment import clean_text, preprocess_tweet, tokenize


def test_removes_urls():
    assert "http" not in clean_text("check this https://t.co/abc123 out www.example.com")


def test_removes_mentions():
    assert clean_text("@john_doe thanks for the help") == "thanks for the help"


def test_removes_special_characters_and_lowercases():
    assert clean_text("WOW!!! This is GREAT :) #happy") == "wow this is great happy"


def test_html_entities_and_negation():
    assert clean_text("I don&#39;t like this &amp; that") == "i dont like this that"


def test_repeated_letters_are_shortened():
    assert clean_text("soooooo good") == "soo good"


def test_tokenize():
    assert tokenize("i love this") == ["i", "love", "this"]
    assert preprocess_tweet("@bob I LOVE it! http://x.co") == ["i", "love", "it"]


def test_non_string_input():
    assert clean_text(None) == ""
    assert clean_text(123) == "123"
