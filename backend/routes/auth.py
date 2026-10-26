from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, current_user
from backend.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_page"))

    return render_template("login.html")


@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    print("\n========== LOGIN DEBUG ==========")
    print("Username received:", repr(username))
    print("Password received:", repr(password))

    if not username or not password:
        print("ERROR: username/password empty")

        return jsonify({
            "success": False,
            "message": "Username and password required"
        }), 400

    user = User.query.filter(
        (User.username == username) |
        (User.email == username)
    ).first()

    print("User found:", user is not None)

    if user:
        print("User ID:", user.id)
        print("User username:", user.username)
        print("User email:", user.email)
        print("User role:", user.role)
        print("User status:", user.status)
        print("Password valid:", user.check_password(password))

    if not user:
        print("ERROR: USER NOT FOUND")

        return jsonify({
            "success": False,
            "message": "Invalid credentials"
        }), 401

    if not user.check_password(password):
        print("ERROR: PASSWORD DOES NOT MATCH")

        return jsonify({
            "success": False,
            "message": "Invalid credentials"
        }), 401

    if user.status != "active":
        print("ERROR: ACCOUNT INACTIVE")

        return jsonify({
            "success": False,
            "message": "Account inactive"
        }), 403

    login_user(user)

    print("SUCCESS: LOGIN OK")
    print("================================\n")

    return jsonify({
        "success": True,
        "data": user.to_dict()
    })


@auth_bp.route("/api/auth/logout", methods=["POST"])
def api_logout():
    logout_user()

    return jsonify({
        "success": True,
        "message": "Logged out"
    })


@auth_bp.route("/api/auth/me", methods=["GET"])
def api_me():
    if not current_user.is_authenticated:
        return jsonify({
            "success": False,
            "message": "Not logged in"
        }), 401

    return jsonify({
        "success": True,
        "data": current_user.to_dict()
    })