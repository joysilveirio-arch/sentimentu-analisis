from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import func
from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.models.sentiment_word import SentimentWord


def clean_records_query():
    """Return the canonical clean dataset stored in facebook_records.

    The project does not have a separate CleanRecord model/table. A record is
    part of the cleaned dataset when it was marked clean, has cleaned text,
    and was not identified as a duplicate.
    """
    return FacebookRecord.query.filter(
        FacebookRecord.is_clean.is_(True),
        FacebookRecord.is_duplicate.is_not(True),
        FacebookRecord.cleaned_text.isnot(None),
        func.trim(FacebookRecord.cleaned_text) != "",
    )


def overview():
    clean = clean_records_query().with_entities(FacebookRecord.id)
    total = clean.count()
    total_likes = db.session.query(func.coalesce(func.sum(FacebookRecord.likes_count), 0)).filter(FacebookRecord.id.in_(clean)).scalar() or 0
    total_comments = db.session.query(func.coalesce(func.sum(FacebookRecord.comments_count), 0)).filter(FacebookRecord.id.in_(clean)).scalar() or 0

    sentiments = db.session.query(
        FacebookRecord.sentiment, func.count(FacebookRecord.id)
    ).filter(FacebookRecord.id.in_(clean)).group_by(FacebookRecord.sentiment).all()
    sent_map = {k or "Unlabeled": v for k, v in sentiments}

    return {
        "total_records": total,
        "total_likes": int(total_likes),
        "total_comments": int(total_comments),
        "total_shares": 0,
        "positive": sent_map.get("Positive", 0),
        "negative": sent_map.get("Negative", 0),
        "neutral": sent_map.get("Neutral", 0),
        "unlabeled": sent_map.get("Unlabeled", 0),
    }

def sentiment_distribution():
    rows = db.session.query(
        FacebookRecord.sentiment, func.count(FacebookRecord.id)
    ).filter(FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))).group_by(FacebookRecord.sentiment).all()
    return [{"label": k or "Unlabeled", "value": v} for k, v in rows]

def sentiment_over_time():
    rows = db.session.query(
        func.date(FacebookRecord.date),
        FacebookRecord.sentiment,
        func.count(FacebookRecord.id),
    ).filter(FacebookRecord.date.isnot(None), FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))).group_by(
        func.date(FacebookRecord.date), FacebookRecord.sentiment
    ).order_by(func.date(FacebookRecord.date)).all()
    data = {}
    for d, s, c in rows:
        dkey = str(d)
        data.setdefault(dkey, {"date": dkey, "Positive": 0, "Negative": 0, "Neutral": 0, "Unlabeled": 0})
        data[dkey][s or "Unlabeled"] = c
    return sorted(data.values(), key=lambda x: x["date"])

def engagement_over_time():
    rows = db.session.query(
        func.date(FacebookRecord.date),
        func.sum(FacebookRecord.likes_count),
        func.sum(FacebookRecord.comments_count),
    ).filter(FacebookRecord.date.isnot(None), FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))).group_by(
        func.date(FacebookRecord.date)
    ).order_by(func.date(FacebookRecord.date)).all()
    return [{"date": str(d), "likes": int(l or 0), "comments": int(c or 0)} for d, l, c in rows]

def gender_distribution():
    rows = db.session.query(
        FacebookRecord.gender, func.count(FacebookRecord.id)
    ).filter(FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))).group_by(FacebookRecord.gender).all()
    return [{"label": k or "UNKNOWN", "value": v} for k, v in rows]

def sentiment_by_gender():
    rows = db.session.query(
        FacebookRecord.gender, FacebookRecord.sentiment, func.count(FacebookRecord.id)
    ).filter(FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))).group_by(FacebookRecord.gender, FacebookRecord.sentiment).all()
    data = {}
    for g, s, c in rows:
        gkey = g or "UNKNOWN"
        data.setdefault(gkey, {"gender": gkey, "Positive": 0, "Negative": 0, "Neutral": 0, "Unlabeled": 0})
        data[gkey][s or "Unlabeled"] = c
    return list(data.values())

def top_authors(limit=10):
    rows = db.session.query(
        FacebookRecord.author_name, func.count(FacebookRecord.id)
    ).filter(FacebookRecord.author_name.isnot(None), FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))).group_by(
        FacebookRecord.author_name
    ).order_by(func.count(FacebookRecord.id).desc()).limit(limit).all()
    return [{"name": k, "count": v} for k, v in rows]

def top_posts(limit=10):
    rows = db.session.query(
        FacebookRecord.post_title, func.count(FacebookRecord.id)
    ).filter(FacebookRecord.post_title.isnot(None), FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))).group_by(
        FacebookRecord.post_title
    ).order_by(func.count(FacebookRecord.id).desc()).limit(limit).all()
    return [{"title": (k[:80] if k else "N/A"), "count": v} for k, v in rows]

def likes_vs_comments():
    rows = db.session.query(FacebookRecord.likes_count, FacebookRecord.comments_count).filter(
        FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))
    ).limit(500).all()
    return [{"likes": int(l or 0), "comments": int(c or 0)} for l, c in rows]

def top_words(sentiment_type="Positive", limit=15):
    words = SentimentWord.query.filter_by(sentiment=sentiment_type, status="active").limit(limit).all()
    return [{"word": w.word, "score": w.score} for w in words]

def label_distribution():
    rows = db.session.query(
        FacebookRecord.label, func.count(FacebookRecord.id)
    ).filter(FacebookRecord.id.in_(clean_records_query().with_entities(FacebookRecord.id))).group_by(FacebookRecord.label).all()
    return [{"label": k or "Unlabeled", "value": v} for k, v in rows]
