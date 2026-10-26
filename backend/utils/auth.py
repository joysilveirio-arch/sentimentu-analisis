from functools import wraps
from flask import jsonify
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"success": False, "message": "Login required"}), 401
        if current_user.role != "ADMIN":
            return jsonify({"success": False, "message": "Admin privilege required"}), 403
        return f(*args, **kwargs)
    return decorated

def login_required_api(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"success": False, "message": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated