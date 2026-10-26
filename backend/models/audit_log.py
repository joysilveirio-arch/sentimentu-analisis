from datetime import datetime
from backend import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100))
    target = db.Column(db.String(255))
    detail = db.Column(db.Text)
    ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id,
            "action": self.action, "target": self.target,
            "detail": self.detail, "ip": self.ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }