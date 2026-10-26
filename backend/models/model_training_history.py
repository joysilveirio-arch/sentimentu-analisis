from datetime import datetime
import json
from backend import db

class ModelTrainingHistory(db.Model):
    __tablename__ = "model_training_history"
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), default="decision_tree")
    algorithm = db.Column(db.String(50), default="DecisionTreeClassifier")
    training_records = db.Column(db.Integer, default=0)
    testing_records = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    precision = db.Column(db.Float, default=0.0)
    recall = db.Column(db.Float, default=0.0)
    f1_score = db.Column(db.Float, default=0.0)
    configuration = db.Column(db.Text)
    confusion_matrix = db.Column(db.Text)
    classification_report = db.Column(db.Text)
    model_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        try:
            cfg = json.loads(self.configuration) if self.configuration else {}
        except Exception:
            cfg = {}
        try:
            cm = json.loads(self.confusion_matrix) if self.confusion_matrix else []
        except Exception:
            cm = []
        return {
            "id": self.id, "model_name": self.model_name,
            "algorithm": self.algorithm,
            "training_records": self.training_records,
            "testing_records": self.testing_records,
            "accuracy": self.accuracy, "precision": self.precision,
            "recall": self.recall, "f1_score": self.f1_score,
            "configuration": cfg, "confusion_matrix": cm,
            "classification_report": self.classification_report,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }