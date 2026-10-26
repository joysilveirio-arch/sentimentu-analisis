from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.models.sentiment_result import SentimentResult
from backend.utils.auth import admin_required
from backend.utils.validators import safe_int
from backend.services.cleaning_service import clean_text, detect_language
from backend.services.sentiment_service import analyze_text

data_bp = Blueprint("data", __name__)

@data_bp.route("/dataset")
@login_required
def dataset_page():
    return render_template("dataset.html")

@data_bp.route("/api/data")
@login_required
def list_data():
    page = safe_int(request.args.get("page", 1), 1)
    per_page = min(safe_int(request.args.get("per_page", 20), 20), 100)
    search = request.args.get("search", "").strip()
    sentiment = request.args.get("sentiment")
    gender = request.args.get("gender")
    label = request.args.get("label")
    author = request.args.get("author")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    # Duplicate rows remain in storage for the cleaning comparison/audit, but
    # are excluded from user-facing dataset results after cleaning.
    q = FacebookRecord.query.filter(FacebookRecord.is_duplicate.isnot(True))
    if search:
        like = f"%{search}%"
        q = q.filter(db.or_(
            FacebookRecord.text.ilike(like),
            FacebookRecord.cleaned_text.ilike(like),
            FacebookRecord.author_name.ilike(like),
        ))
    if sentiment:
        q = q.filter(FacebookRecord.sentiment == sentiment)
    if gender:
        q = q.filter(FacebookRecord.gender == gender)
    if label:
        q = q.filter(FacebookRecord.label == label)
    if author:
        q = q.filter(FacebookRecord.author_name.ilike(f"%{author}%"))
    if date_from:
        q = q.filter(FacebookRecord.date >= date_from)
    if date_to:
        q = q.filter(FacebookRecord.date <= date_to)

    q = q.order_by(FacebookRecord.date.desc().nullslast())
    paginate = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "success": True,
        "data": [r.to_dict() for r in paginate.items],
        "pagination": {
            "page": page, "per_page": per_page,
            "total": paginate.total, "pages": paginate.pages,
        },
    })

@data_bp.route("/api/data/<int:rid>")
@login_required
def get_one(rid):
    rec = FacebookRecord.query.filter(
        FacebookRecord.id == rid,
        FacebookRecord.is_duplicate.isnot(True),
    ).first_or_404()
    return jsonify({"success": True, "data": rec.to_dict()})

@data_bp.route("/api/data", methods=["POST"])
@admin_required
def create_record():
    data = request.get_json() or {}
    if not data.get("text") and not data.get("author_name"):
        return jsonify({"success": False, "message": "Text or author required"}), 400
    raw_text = data.get("text")
    cleaned = clean_text(raw_text)
    analysis = analyze_text(cleaned)
    rec = FacebookRecord(
        facebook_record_id=data.get("facebook_record_id"),
        author_name=data.get("author_name"),
        text=raw_text,
        cleaned_text=cleaned or None,
        post_title=data.get("post_title"),
        gender=data.get("gender", "UNKNOWN"),
        sentiment=analysis["sentiment"],
        sentiment_score=analysis["score"],
        positive_words=analysis["positive"],
        negative_words=analysis["negative"],
        label=data.get("label") or None,
        likes_count=safe_int(data.get("likes_count")),
        comments_count=safe_int(data.get("comments_count")),
        language=detect_language(cleaned),
        is_clean=bool(cleaned),
    )
    db.session.add(rec)
    db.session.commit()
    return jsonify({"success": True, "data": rec.to_dict()})

@data_bp.route("/api/data/<int:rid>", methods=["PUT"])
@admin_required
def update_record(rid):
    rec = FacebookRecord.query.get_or_404(rid)
    data = request.get_json() or {}
    for k in ["author_name", "post_title", "label", "gender"]:
        if k in data:
            setattr(rec, k, data[k])
    if "text" in data:
        rec.text = data["text"]
        rec.cleaned_text = clean_text(rec.text) or None
        rec.language = detect_language(rec.cleaned_text)
        rec.is_clean = bool(rec.cleaned_text)
        analysis = analyze_text(rec.cleaned_text)
        rec.sentiment = analysis["sentiment"]
        rec.sentiment_score = analysis["score"]
        rec.positive_words = analysis["positive"]
        rec.negative_words = analysis["negative"]
    if "sentiment" in data:
        rec.sentiment = data["sentiment"]
    if "likes_count" in data:
        rec.likes_count = safe_int(data["likes_count"])
    if "comments_count" in data:
        rec.comments_count = safe_int(data["comments_count"])
    db.session.commit()
    return jsonify({"success": True, "data": rec.to_dict()})

@data_bp.route("/api/data/<int:rid>", methods=["DELETE"])
@admin_required
def delete_record(rid):
    rec = FacebookRecord.query.get_or_404(rid)
    SentimentResult.query.filter_by(record_id=rid).delete(synchronize_session=False)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"success": True})
