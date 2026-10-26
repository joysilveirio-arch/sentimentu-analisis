from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.services.sentiment_service import analyze_records_batch, analyze_text, load_wordlist
from backend.utils.auth import admin_required

sentiment_bp = Blueprint("sentiment", __name__)

@sentiment_bp.route("/sentiment")
@login_required
def sentiment_page():
    return render_template("sentiment.html")

@sentiment_bp.route("/api/admin/sentiment/analyze", methods=["POST"])
@admin_required
def api_analyze_all():
    count = analyze_records_batch()
    return jsonify({"success": True, "data": {"updated": count}})

@sentiment_bp.route("/api/sentiment/analyze-text", methods=["POST"])
@login_required
def api_analyze_text():
    d = request.get_json() or {}
    text = d.get("text", "")
    result = analyze_text(text)
    return jsonify({"success": True, "data": result})