from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from modules.prediction.service import prediction_service

prediction_bp = Blueprint("prediction", __name__, url_prefix="/api/prediction")

@prediction_bp.route("/forecast", methods=["GET"])
def get_forecast():
    """Returns the risk level, probability, and trend graph data for a given date."""
    date_str = request.args.get("date")
    
    # Parse date from query parameter, default to today
    if not date_str:
        target_date = datetime.now()
    else:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Get the prediction
    risk, probability = prediction_service.get_prediction(target_date)

    # Construct the base response
    response_data = {
        "selected_date": target_date.strftime("%Y-%m-%d"),
        "risk": risk,
        "probability": probability
    }

    # Only include trend data if explicitly requested
    if request.args.get("include_trend") == "true":
        # Calculate start date for trend (e.g., 10 days prior)
        start_date = target_date - timedelta(days=10)
        # Get trend data
        response_data["trend"] = prediction_service.get_trend(start_date.strftime("%Y-%m-%d"), target_date)

    return jsonify(response_data)
