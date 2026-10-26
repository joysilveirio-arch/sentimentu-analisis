from datetime import datetime
from backend import db

class Label(db.Model):
    __tablename__ = "labels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    color = db.Column(db.String(20), default="#2563EB")
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name,
            "description": self.description, "color": self.color,
            "status": self.status,
        }