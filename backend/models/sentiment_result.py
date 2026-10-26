from datetime import datetime
from backend import db

class SentimentResult(db.Model):
    __tablename__ = "sentiment_results"
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("facebook_records.id"), index=True, unique=True)
    sentiment = db.Column(db.String(20))
    sentiment_score = db.Column(db.Float)
    positive_words = db.Column(db.Integer, default=0)
    negative_words = db.Column(db.Integer, default=0)
    method = db.Column(db.String(50), default="wordlist")
    predicted_label = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "record_id": self.record_id,
            "sentiment": self.sentiment, "sentiment_score": self.sentiment_score,
            "positive_words": self.positive_words, "negative_words": self.negative_words,
            "method": self.method, "predicted_label": self.predicted_label,
            "confidence": self.confidence,
        }
