import re

from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.models.sentiment_word import SentimentWord
from backend.models.sentiment_result import SentimentResult
from backend.services.cleaning_service import clean_text

def load_wordlist():
    words = SentimentWord.query.filter_by(status="active").all()
    lex = {}
    for w in words:
        # Normalize lexicon entries with the same Unicode/token rules used for
        # submitted text. This handles accidental casing, surrounding spaces,
        # and punctuation without making partial-word matches.
        normalized = re.findall(
            r"[^\W_]+", clean_text(w.word or "").casefold(), flags=re.UNICODE
        )
        if len(normalized) == 1:
            lex[normalized[0]] = {
                "sentiment": (w.sentiment or "").strip().casefold().title(),
                "score": w.score,
            }
    return lex

def analyze_text(text, lex=None):
    if lex is None:
        lex = load_wordlist()
    if not text:
        return {"sentiment": "Neutral", "score": 0.0, "positive": 0, "negative": 0, "method": "wordlist"}

    # Strip punctuation and emoji around words before exact wordlist matching
    # (for example, "cantik!" and "cantik🥰" should match "cantik").
    tokens = re.findall(r"[^\W_]+", clean_text(text).casefold(), flags=re.UNICODE)
    pos, neg = 0, 0
    score = 0.0
    for tok in tokens:
        if tok in lex:
            entry = lex[tok]
            if entry["sentiment"] == "Positive":
                pos += 1
                score += entry["score"]
            elif entry["sentiment"] == "Negative":
                neg += 1
                score -= entry["score"]

    if score > 0:
        label = "Positive"
    elif score < 0:
        label = "Negative"
    else:
        label = "Neutral"

    return {"sentiment": label, "score": score, "positive": pos, "negative": neg, "method": "wordlist"}

def analyze_records_batch(records=None, user_id=None):
    if records is None:
        records = FacebookRecord.query.filter(
            FacebookRecord.is_clean.is_(True),
            FacebookRecord.is_duplicate.isnot(True),
            FacebookRecord.cleaned_text.isnot(None),
            FacebookRecord.cleaned_text != "",
        ).all()
    else:
        records = [
            record for record in records
            if record.is_clean is True
            and record.is_duplicate is not True
            and (record.cleaned_text or "").strip()
        ]

    lex = load_wordlist()
    updated = 0
    for r in records:
        # Reuse the persisted cleaned text so every report is based on the
        # same text produced by the cleaning step. Fall back to cleaning raw
        # text for records analyzed before a cleaning run.
        source_text = r.cleaned_text or clean_text(r.text or "")
        result = analyze_text(source_text, lex)
        r.sentiment = result["sentiment"]
        r.sentiment_score = result["score"]
        r.positive_words = result["positive"]
        r.negative_words = result["negative"]

        # Keep one result per Facebook record. Older databases may already
        # contain rows from both import and repeated cleaning runs; preserve
        # the most recent result and update it in place.
        matches = SentimentResult.query.filter_by(record_id=r.id).order_by(
            SentimentResult.id.desc()
        ).all()
        sr = matches[0] if matches else SentimentResult(record_id=r.id)
        for duplicate in matches[1:]:
            db.session.delete(duplicate)
        sr.sentiment = result["sentiment"]
        sr.sentiment_score = result["score"]
        sr.positive_words = result["positive"]
        sr.negative_words = result["negative"]
        sr.method = "wordlist"
        if not matches:
            db.session.add(sr)
        updated += 1

    db.session.commit()
    return updated
