from datetime import datetime
from backend import db

class ImportHistory(db.Model):
    __tablename__ = "imports"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    total_rows = db.Column(db.Integer, default=0)
    imported_rows = db.Column(db.Integer, default=0)
    failed_rows = db.Column(db.Integer, default=0)
    duplicate_rows = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="success")
    message = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "filename": self.filename,
            "total_rows": self.total_rows, "imported_rows": self.imported_rows,
            "failed_rows": self.failed_rows, "duplicate_rows": self.duplicate_rows,
            "source_rows": self.total_rows or 0,
            "cleaned_rows": max((self.total_rows or 0) - (self.failed_rows or 0), 0),
            "error_rows": self.failed_rows or 0,
            "status": self.status, "message": self.message,
            "error_message": self.message if (self.failed_rows or self.status == "failed") else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
