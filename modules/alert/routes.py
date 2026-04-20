from flask import Blueprint, request, jsonify

from modules.alert.service import alert_service

alert_bp = Blueprint("alert", __name__, url_prefix="/api/alert")

@alert_bp.route("/status", methods=["GET"])
def get_status():
    """Check if the SMS alert system is configured and enabled."""
    return jsonify({
        "enabled": alert_service.is_enabled()
    })

@alert_bp.route("/test", methods=["POST"])
def test_alert():
    """Trigger a test SMS alert manually."""
    if not alert_service.is_enabled():
        return jsonify({"error": "Alerts are disabled. Configure Twilio credentials."}), 503
        
    data = request.get_json(silent=True) or {}
    message = data.get("message", "Test Alert: system is working correctly!")
    
    result = alert_service.send_sms_alert(message)
    return jsonify(result)
