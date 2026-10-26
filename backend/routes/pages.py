from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from backend import db
from backend.models.facebook_record import FacebookRecord

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html")

@pages_bp.route("/search")
@login_required
def search_page():
    return render_template("search.html")

@pages_bp.route("/api/search")
@login_required
def api_search():
    keyword = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 20)), 100)
    if not keyword:
        return jsonify({"success": True, "data": []})
    like = f"%{keyword}%"
    rows = FacebookRecord.query.filter(
        FacebookRecord.is_duplicate.isnot(True),
        db.or_(
            FacebookRecord.text.ilike(like),
            FacebookRecord.author_name.ilike(like),
            FacebookRecord.post_title.ilike(like),
        )
    ).limit(limit).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in rows]})
