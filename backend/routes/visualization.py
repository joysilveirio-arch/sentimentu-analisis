from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from backend.services import analytics_service

viz_bp = Blueprint("viz", __name__)

@viz_bp.route("/visualization")
@login_required
def viz_page():
    return render_template("visualization.html")

@viz_bp.route("/analysis")
@login_required
def analysis_page():
    return render_template("analysis.html")

@viz_bp.route("/api/viz/sentiment-by-gender")
@login_required
def api_sent_by_gender():
    return jsonify({"success": True, "data": analytics_service.sentiment_by_gender()})

@viz_bp.route("/api/viz/top-posts")
@login_required
def api_top_posts():
    return jsonify({"success": True, "data": analytics_service.top_posts()})

@viz_bp.route("/api/viz/likes-comments")
@login_required
def api_lc():
    return jsonify({"success": True, "data": analytics_service.likes_vs_comments()})

@viz_bp.route("/api/viz/top-positive-words")
@login_required
def api_top_pos():
    return jsonify({"success": True, "data": analytics_service.top_words("Positive")})

@viz_bp.route("/api/viz/top-negative-words")
@login_required
def api_top_neg():
    return jsonify({"success": True, "data": analytics_service.top_words("Negative")})

@viz_bp.route("/api/viz/label-distribution")
@login_required
def api_label_dist():
    return jsonify({"success": True, "data": analytics_service.label_distribution()})