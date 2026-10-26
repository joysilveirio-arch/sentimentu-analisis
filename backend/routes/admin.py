import os
import csv
import io
from flask import Blueprint, jsonify, request, render_template, current_app, Response
from flask_login import current_user
from werkzeug.utils import secure_filename
from backend import db
from backend.models.user import User
from backend.models.sentiment_word import SentimentWord
from backend.models.label import Label
from backend.models.import_history import ImportHistory
from backend.models.cleaning_log import CleaningLog
from backend.models.audit_log import AuditLog
from backend.models.facebook_record import FacebookRecord
from backend.models.sentiment_result import SentimentResult
from backend.services.data_service import import_csv
from backend.services.cleaning_service import build_cleaning_preview, run_cleaning
from backend.utils.auth import admin_required
from backend.utils.validators import allowed_file

admin_bp = Blueprint("admin", __name__)

# ========= USERS =========
@admin_bp.route("/admin/users")
@admin_required
def users_page():
    return render_template("admin/users.html")

@admin_bp.route("/api/admin/users")
@admin_required
def api_users():
    return jsonify({"success": True, "data": [u.to_dict() for u in User.query.all()]})

@admin_bp.route("/api/admin/users", methods=["POST"])
@admin_required
def api_users_create():
    d = request.get_json() or {}
    if not d.get("username") or not d.get("password"):
        return jsonify({"success": False, "message": "Username & password required"}), 400
    if User.query.filter_by(username=d["username"]).first():
        return jsonify({"success": False, "message": "Username exists"}), 400
    u = User(username=d["username"], email=d.get("email", f"{d['username']}@local"),
             role=d.get("role", "USER"))
    u.set_password(d["password"])
    db.session.add(u)
    db.session.commit()
    return jsonify({"success": True, "data": u.to_dict()})

@admin_bp.route("/api/admin/users/<int:uid>", methods=["PUT"])
@admin_required
def api_users_update(uid):
    u = User.query.get_or_404(uid)
    d = request.get_json() or {}
    if "email" in d: u.email = d["email"]
    if "role" in d: u.role = d["role"]
    if "status" in d: u.status = d["status"]
    if d.get("password"): u.set_password(d["password"])
    db.session.commit()
    return jsonify({"success": True, "data": u.to_dict()})

@admin_bp.route("/api/admin/users/<int:uid>", methods=["DELETE"])
@admin_required
def api_users_delete(uid):
    if uid == current_user.id:
        return jsonify({"success": False, "message": "Cannot delete self"}), 400
    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return jsonify({"success": True})

# ========= IMPORT =========
@admin_bp.route("/admin/import")
@admin_required
def import_page():
    return render_template("admin/import.html")

@admin_bp.route("/api/admin/import", methods=["POST"])
@admin_required
def api_import():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file"}), 400
    f = request.files["file"]
    if not f.filename or not allowed_file(f.filename):
        return jsonify({"success": False, "message": "Only CSV allowed"}), 400
    filename = secure_filename(f.filename)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    f.save(save_path)
    hist = import_csv(save_path, user_id=current_user.id)
    if hist.status == "failed":
        return jsonify({"success": False, "message": hist.message, "data": hist.to_dict()}), 500
    return jsonify({"success": True, "data": hist.to_dict()})

@admin_bp.route("/api/admin/import/history")
@admin_required
def api_import_history():
    rows = ImportHistory.query.order_by(ImportHistory.created_at.desc()).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in rows]})

# ========= CLEANING =========
@admin_bp.route("/admin/cleaning")
@admin_required
def cleaning_page():
    return render_template("admin/cleaning.html")

@admin_bp.route("/api/admin/clean/preview", methods=["POST"])
@admin_required
def api_clean_preview():
    return jsonify({"success": True, "data": build_cleaning_preview()})

@admin_bp.route("/api/admin/clean", methods=["POST"])
@admin_required
def api_clean():
    return jsonify({"success": True, "data": run_cleaning()})

@admin_bp.route("/api/admin/clean/export.csv")
@admin_required
def api_clean_export():
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["id", "text", "cleaned_text", "status"])
    records = FacebookRecord.query.order_by(FacebookRecord.id).all()
    for record in records:
        if record.is_duplicate:
            status = "Duplicate"
        elif not (record.text or "").strip():
            status = "Missing text"
        elif not (record.cleaned_text or "").strip():
            status = "Mamuk depois cleaning"
        else:
            status = "Cleaned"
        writer.writerow([record.id, record.text or "", record.cleaned_text or "", status])
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=facebook_cleaning.csv"},
    )

@admin_bp.route("/api/admin/cleaning/history")
@admin_required
def api_cleaning_history():
    rows = CleaningLog.query.order_by(CleaningLog.created_at.desc()).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in rows]})

# ========= WORDLIST =========
@admin_bp.route("/admin/wordlist")
@admin_required
def wordlist_page():
    return render_template("admin/wordlist.html")

@admin_bp.route("/api/admin/wordlist")
@admin_required
def api_wordlist():
    rows = SentimentWord.query.order_by(SentimentWord.sentiment, SentimentWord.word).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in rows]})

@admin_bp.route("/api/admin/wordlist", methods=["POST"])
@admin_required
def api_wordlist_create():
    d = request.get_json() or {}
    if not d.get("word") or not d.get("sentiment"):
        return jsonify({"success": False, "message": "Word & sentiment required"}), 400
    w = SentimentWord(
        word=d["word"].strip().lower(),
        sentiment=d["sentiment"],
        score=int(d.get("score", 1)),
        language=d.get("language", "unknown"),
    )
    db.session.add(w)
    db.session.commit()
    return jsonify({"success": True, "data": w.to_dict()})

@admin_bp.route("/api/admin/wordlist/<int:wid>", methods=["PUT"])
@admin_required
def api_wordlist_update(wid):
    w = SentimentWord.query.get_or_404(wid)
    d = request.get_json() or {}
    for k in ["word", "sentiment", "language", "status"]:
        if k in d:
            setattr(w, k, d[k].lower() if k == "word" else d[k])
    if "score" in d: w.score = int(d["score"])
    db.session.commit()
    return jsonify({"success": True, "data": w.to_dict()})

@admin_bp.route("/api/admin/wordlist/<int:wid>", methods=["DELETE"])
@admin_required
def api_wordlist_delete(wid):
    w = SentimentWord.query.get_or_404(wid)
    db.session.delete(w)
    db.session.commit()
    return jsonify({"success": True})

# ========= LABELS =========
@admin_bp.route("/api/admin/labels")
@admin_required
def api_labels():
    rows = Label.query.all()
    return jsonify({"success": True, "data": [r.to_dict() for r in rows]})

@admin_bp.route("/api/admin/labels", methods=["POST"])
@admin_required
def api_labels_create():
    d = request.get_json() or {}
    if not d.get("name"):
        return jsonify({"success": False, "message": "Name required"}), 400
    l = Label(name=d["name"], description=d.get("description"), color=d.get("color", "#2563EB"))
    db.session.add(l)
    db.session.commit()
    return jsonify({"success": True, "data": l.to_dict()})

@admin_bp.route("/api/admin/labels/<int:lid>", methods=["PUT"])
@admin_required
def api_labels_update(lid):
    l = Label.query.get_or_404(lid)
    d = request.get_json() or {}
    for k in ["name", "description", "color", "status"]:
        if k in d: setattr(l, k, d[k])
    db.session.commit()
    return jsonify({"success": True, "data": l.to_dict()})

@admin_bp.route("/api/admin/labels/<int:lid>", methods=["DELETE"])
@admin_required
def api_labels_delete(lid):
    l = Label.query.get_or_404(lid)
    db.session.delete(l)
    db.session.commit()
    return jsonify({"success": True})

# ========= DATABASE =========
@admin_bp.route("/admin/database")
@admin_required
def database_page():
    return render_template("admin/database.html")

@admin_bp.route("/api/admin/database/info")
@admin_required
def api_db_info():
    return jsonify({"success": True, "data": {
        "users": User.query.count(),
        "facebook_records": FacebookRecord.query.count(),
        "sentiment_words": SentimentWord.query.count(),
        "labels": Label.query.count(),
        "imports": ImportHistory.query.count(),
        "cleaning_logs": CleaningLog.query.count(),
        "audit_logs": AuditLog.query.count(),
    }})

@admin_bp.route("/api/admin/database/records")
@admin_required
def api_database_records():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 50, type=int), 1), 100)
    pagination = FacebookRecord.query.order_by(FacebookRecord.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "success": True,
        "data": [record.to_dict() for record in pagination.items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })

# ========= HISTORY =========
@admin_bp.route("/admin/history")
@admin_required
def history_page():
    return render_template("admin/history.html")

@admin_bp.route("/api/admin/audit")
@admin_required
def api_audit():
    rows = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in rows]})
