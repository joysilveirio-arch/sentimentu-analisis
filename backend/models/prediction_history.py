from datetime import datetime
from backend import db

class PredictionHistory(db.Model):
    __tablename__ = "prediction_history"
    id = db.Column(db.Integer, primary_key=True)
    input_text = db.Column(db.Text)
    predicted_label = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    model_version = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "input_text": self.input_text,
            "predicted_label": self.predicted_label,
            "confidence": self.confidence,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }