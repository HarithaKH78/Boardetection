import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, render_template

import dotenv
from config import ADMIN_PASSWORD
from database import db_manager
from modules.prediction.service import prediction_service
from modules.detection.routes import init_service

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ------------------------------------------------------------------
# UI Routes (Jinja Templates)
# ------------------------------------------------------------------

@admin_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("admin_login.html")

@admin_bp.route("/", methods=["GET"])
@admin_bp.route("/dashboard", methods=["GET"])
def dashboard_page():
    if not session.get("logged_in"):
        return render_template("admin_login.html")
    return render_template("admin_dashboard.html")

@admin_bp.route("/settings", methods=["GET"])
def settings_page():
    if not session.get("logged_in"):
        return render_template("admin_login.html")
    return render_template("admin_settings.html")


# ------------------------------------------------------------------
# API Routes
# ------------------------------------------------------------------

@admin_bp.route("/api/login", methods=["POST"])
def auth_login():
    data = request.get_json(silent=True) or {}
    password = data.get("password")
    
    if password == ADMIN_PASSWORD:
        session["logged_in"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid password"}), 401


@admin_bp.route("/api/logout", methods=["POST"])
def auth_logout():
    session.pop("logged_in", None)
    return jsonify({"success": True})


@admin_bp.route("/api/settings", methods=["GET"])
def get_settings():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    
    # Read fresh from .env
    return jsonify({
        "ROBOFLOW_API_KEY": os.getenv("ROBOFLOW_API_KEY", ""),
        "REGISTERED_NUMBERS": os.getenv("REGISTERED_NUMBERS", ""),
        "ALERT_MESSAGE": os.getenv("ALERT_MESSAGE", "")
    })


@admin_bp.route("/api/settings", methods=["POST"])
def update_settings():
    """Rewrite physical .env file and optionally reload services in memory."""
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    env_file = ".env"
    
    # Update properties in .env
    for key, value in data.items():
        if key in ["ROBOFLOW_API_KEY", "REGISTERED_NUMBERS", "ALERT_MESSAGE"]:
            dotenv.set_key(env_file, key, value)
            # Update working memory so we don't need a hard restart immediately
            os.environ[key] = value

    return jsonify({"success": True, "message": "Settings updated successfully."})


@admin_bp.route("/api/graph-data", methods=["GET"])
def graph_data():
    """Returns aggregated Actual MongoDB Detections vs Targeted Predictions."""
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    period = request.args.get("period", "week")  # 'day', 'week', 'month'
    
    now = datetime.utcnow()
    if period == "day":
        start_date = now - timedelta(days=1)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # default week
        start_date = now - timedelta(days=7)

    # 1. Fetch Actuals from MongoDB
    actuals = []
    col = db_manager.get_collection("detections")
    if col is not None:
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "total_boars": {"$sum": "$count"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        mongo_res = list(col.aggregate(pipeline))
        for item in mongo_res:
            actuals.append({"date": item["_id"], "count": item["total_boars"]})

    # 2. Fetch Prediction Trend
    # The trend gives a base 'score' for historical dates. We'll map that to standard dates.
    prediction_trend = prediction_service.get_trend(start_date.strftime("%Y-%m-%d"), now)

    return jsonify({
        "actuals": actuals,
        "predictions": prediction_trend
    })
