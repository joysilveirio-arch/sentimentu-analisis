from backend import db
from backend.models.sentiment_word import SentimentWord
from backend.services.sentiment_service import analyze_text, load_wordlist

def test_sentiment_positive(app):
    with app.app_context():
        r = analyze_text("good diak love")
        assert r["sentiment"] == "Positive"
        assert r["positive"] >= 1

def test_sentiment_negative(app):
    with app.app_context():
        r = analyze_text("bad aat hate")
        assert r["sentiment"] == "Negative"

def test_sentiment_neutral(app):
    with app.app_context():
        r = analyze_text("this is a plain sentence")
        assert r["sentiment"] == "Neutral"

def test_analyze_text_endpoint(user_client):
    r = user_client.post("/api/sentiment/analyze-text", json={"text": "good"})
    assert r.status_code == 200
    assert r.get_json()["data"]["sentiment"] == "Positive"

def test_tetum_wordlist_normalization_and_live_api(user_client, app):
    sample = "HAU hadomi O DOben ❤️❤️❤️"
    with app.app_context():
        # This confirms the exact project fixture's active Wordlist, rather
        # than assuming a sentiment for a word that is not present.
        assert "hadomi" not in load_wordlist()

    # The live endpoint uses the current Wordlist. Since `hadomi` is absent,
    # the observed response is Neutral with zero matches.
    r = user_client.post("/api/sentiment/analyze-text", json={"text": sample})
    data = r.get_json()["data"]
    assert data == {
        "sentiment": "Neutral", "score": 0.0, "positive": 0, "negative": 0,
        "method": "wordlist",
    }

    # Simulate adding the manually verified Tetum term through the same
    # persisted Wordlist model; casing, whitespace, punctuation and emoji
    # must not prevent an exact token match.
    with app.app_context():
        db.session.add(SentimentWord(
            word="  HAdomi! ", sentiment="positive", score=2,
            language="tet", status="active",
        ))
        db.session.commit()
    r = user_client.post("/api/sentiment/analyze-text", json={"text": sample})
    data = r.get_json()["data"]
    assert data["sentiment"] == "Positive"
    assert data["score"] == 2
    assert data["positive"] == 1
    assert data["method"] == "wordlist"

def test_api_positive_negative_and_neutral_examples(user_client):
    expected = [
        ("GOOD! ❤️", "Positive", 1, 0),
        ("BAD... 😢", "Negative", 0, 1),
        ("ordinary words", "Neutral", 0, 0),
    ]
    for text, sentiment, positive, negative in expected:
        response = user_client.post("/api/sentiment/analyze-text", json={"text": text})
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert (data["sentiment"], data["positive"], data["negative"]) == (
            sentiment, positive, negative
        )
        assert data["method"] == "wordlist"
