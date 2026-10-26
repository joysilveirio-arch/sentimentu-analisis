from datetime import datetime
from backend import db

class SentimentWord(db.Model):
    __tablename__ = "sentiment_words"
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(120), nullable=False, index=True)
    sentiment = db.Column(db.String(20), nullable=False)  # Positive/Negative/Neutral
    score = db.Column(db.Integer, nullable=False, default=1)
    language = db.Column(db.String(20), nullable=False, default="unknown")
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("word", "language", name="uq_word_lang"),)

    def to_dict(self):
        return {
            "id": self.id, "word": self.word, "sentiment": self.sentiment,
            "score": self.score, "language": self.language, "status": self.status,
        }