from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from backend import db
from backend.models.model_training_history import ModelTrainingHistory
from backend.models.prediction_history import PredictionHistory
from backend.services.ml_service import train_model, predict_text
from backend.utils.auth import admin_required

ml_bp = Blueprint("ml", __name__)

@ml_bp.route("/ml")
@admin_required
def ml_page():
    return render_template("admin/ml.html")

@ml_bp.route("/model-evaluation")
@login_required
def eval_page():
    return render_template("admin/ml.html")

@ml_bp.route("/api/admin/ml/train", methods=["POST"])
@admin_required
def api_train():
    d = request.get_json() or {}
    result = train_model(
        max_depth=int(d.get("max_depth", 15)),
        test_size=float(d.get("test_size", 0.2)),
        max_features=int(d.get("max_features", 5000)),
    )
    return jsonify(result)

@ml_bp.route("/api/admin/ml/history")
@admin_required
def api_history():
    rows = ModelTrainingHistory.query.order_by(ModelTrainingHistory.created_at.desc()).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in rows]})

@ml_bp.route("/api/admin/ml/evaluation")
@login_required
def api_evaluation():
    latest = ModelTrainingHistory.query.order_by(ModelTrainingHistory.created_at.desc()).first()
    if not latest:
        return jsonify({"success": False, "message": "No model trained yet"}), 404
    return jsonify({"success": True, "data": latest.to_dict()})

@ml_bp.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    d = request.get_json() or {}
    text = d.get("text", "").strip()
    if not text:
        return jsonify({"success": False, "message": "Text required"}), 400
    result = predict_text(text)
    if result.get("success"):
        ph = PredictionHistory(
            input_text=text,
            predicted_label=result["predicted_label"],
            confidence=result.get("confidence"),
            model_version="decision_tree",
            user_id=current_user.id,
        )
        db.session.add(ph)
        db.session.commit()
    return jsonify(result)

@ml_bp.route("/api/predict/batch", methods=["POST"])
@login_required
def api_predict_batch():
    d = request.get_json() or {}
    texts = d.get("texts", [])
    results = [predict_text(t) for t in texts]
    return jsonify({"success": True, "data": results})