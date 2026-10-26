from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.utils.auth import admin_required

labeling_bp = Blueprint("labeling", __name__)

@labeling_bp.route("/labeling")
@admin_required
def labeling_page():
    return render_template("labeling.html")

@labeling_bp.route("/api/admin/labeling/assign", methods=["POST"])
@admin_required
def api_assign_label():
    d = request.get_json() or {}
    try:
        rid = int(d.get("record_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "A valid record ID is required"}), 400
    label = d.get("label")
    if rid <= 0:
        return jsonify({"success": False, "message": "A valid record ID is required"}), 400
    if label not in {"Positive", "Negative", "Neutral"}:
        return jsonify({"success": False, "message": "Label must be Positive, Negative, or Neutral"}), 400

    rec = db.session.get(FacebookRecord, rid)
    if not rec:
        return jsonify({"success": False, "message": "Record not found"}), 404

    if not (rec.cleaned_text or "").strip() and d.get("confirm_empty_text") is not True:
        return jsonify({
            "success": False,
            "message": "Cleaned text is empty; confirm this record or correct its text before labeling",
        }), 409

    rec.label = label
    db.session.commit()
    return jsonify({"success": True, "data": rec.to_dict()})
