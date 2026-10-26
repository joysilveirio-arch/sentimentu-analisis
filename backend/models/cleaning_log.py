from datetime import datetime
from backend import db

class CleaningLog(db.Model):
    __tablename__ = "cleaning_logs"
    id = db.Column(db.Integer, primary_key=True)
    original_records = db.Column(db.Integer, default=0)
    duplicate_records = db.Column(db.Integer, default=0)
    missing_values = db.Column(db.Integer, default=0)
    invalid_records = db.Column(db.Integer, default=0)
    clean_records = db.Column(db.Integer, default=0)
    removed_records = db.Column(db.Integer, default=0)
    quality_score = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "original_records": self.original_records,
            "duplicate_records": self.duplicate_records,
            "missing_values": self.missing_values,
            "invalid_records": self.invalid_records,
            "clean_records": self.clean_records,
            "removed_records": self.removed_records,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }