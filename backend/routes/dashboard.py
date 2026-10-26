from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from backend.services import analytics_service

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")

@dashboard_bp.route("/api/dashboard/overview")
@login_required
def api_overview():
    return jsonify({"success": True, "data": analytics_service.overview()})

@dashboard_bp.route("/api/dashboard/sentiment")
@login_required
def api_sentiment():
    return jsonify({"success": True, "data": analytics_service.sentiment_distribution()})

@dashboard_bp.route("/api/dashboard/engagement")
@login_required
def api_engagement():
    return jsonify({"success": True, "data": analytics_service.engagement_over_time()})

@dashboard_bp.route("/api/dashboard/trends")
@login_required
def api_trends():
    return jsonify({"success": True, "data": analytics_service.sentiment_over_time()})

@dashboard_bp.route("/api/dashboard/gender")
@login_required
def api_gender():
    return jsonify({"success": True, "data": analytics_service.gender_distribution()})

@dashboard_bp.route("/api/dashboard/authors")
@login_required
def api_authors():
    return jsonify({"success": True, "data": analytics_service.top_authors()})