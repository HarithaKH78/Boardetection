import os
from twilio.rest import Client

from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    REGISTERED_NUMBERS,
)

class AlertService:
    def __init__(self):
        # We only initialize the client if credentials are provided
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False

    def is_enabled(self):
        return self.enabled

    def send_sms_alert(self, message: str) -> dict:
        """Send an SMS to all registered numbers."""
        if not self.enabled:
            return {"status": "disabled", "message": "Twilio credentials not configured"}

        if not REGISTERED_NUMBERS:
            return {"status": "error", "message": "No registered numbers to send alerts to"}

        results = []
        for number in REGISTERED_NUMBERS:
            try:
                msg = self.client.messages.create(
                    body=message,
                    from_=TWILIO_PHONE_NUMBER,
                    to=number
                )
                print(f"[AlertModule] ✅ SMS sent successfully to {number} (SID: {msg.sid})")
                results.append({"to": number, "status": "sent", "sid": msg.sid})
            except Exception as e:
                print(f"[AlertModule] ❌ SMS failed to send to {number}. Error: {e}")
                results.append({"to": number, "status": "error", "error": str(e)})

        return {"status": "success", "details": results}

# Global instance
alert_service = AlertService()
