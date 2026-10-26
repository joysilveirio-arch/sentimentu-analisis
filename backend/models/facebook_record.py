from datetime import datetime
from backend import db

class FacebookRecord(db.Model):
    __tablename__ = "facebook_records"
    id = db.Column(db.Integer, primary_key=True)
    facebook_record_id = db.Column(db.String(255), unique=True, index=True)
    comment_id = db.Column(db.String(255), index=True)
    author_name = db.Column(db.String(255), index=True)
    author_facebook_id = db.Column(db.String(255), index=True)
    author_url = db.Column(db.String(500))
    gender = db.Column(db.String(20), index=True, default="UNKNOWN")
    post_title = db.Column(db.Text)
    text = db.Column(db.Text)
    cleaned_text = db.Column(db.Text)
    date = db.Column(db.DateTime, index=True)
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    facebook_url = db.Column(db.String(1000))
    profile_name = db.Column(db.String(255))
    attachment_type = db.Column(db.String(50))
    parent_comment_id = db.Column(db.String(255))
    language = db.Column(db.String(20), default="unknown")
    sentiment = db.Column(db.String(20), index=True)
    sentiment_score = db.Column(db.Float, default=0.0)
    positive_words = db.Column(db.Integer, default=0)
    negative_words = db.Column(db.Integer, default=0)
    label = db.Column(db.String(50), index=True)
    is_duplicate = db.Column(db.Boolean, default=False)
    is_clean = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "facebook_record_id": self.facebook_record_id,
            "comment_id": self.comment_id,
            "author_name": self.author_name,
            "author_facebook_id": self.author_facebook_id,
            "author_url": self.author_url,
            "gender": self.gender,
            "post_title": self.post_title,
            "text": self.text,
            "cleaned_text": self.cleaned_text,
            "date": self.date.isoformat() if self.date else None,
            "likes_count": self.likes_count or 0,
            "comments_count": self.comments_count or 0,
            "facebook_url": self.facebook_url,
            "profile_name": self.profile_name,
            "attachment_type": self.attachment_type,
            "parent_comment_id": self.parent_comment_id,
            "language": self.language,
            "sentiment": self.sentiment,
            "sentiment_score": self.sentiment_score,
            "positive_words": self.positive_words,
            "negative_words": self.negative_words,
            "label": self.label,
            "is_duplicate": self.is_duplicate,
            "is_clean": self.is_clean,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
