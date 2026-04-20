import os
from dotenv import load_dotenv

load_dotenv()

# Roboflow
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = "wild-boar-deterrent-pzq5t/1"

# Detection thresholds
CONFIDENCE_THRESHOLD = 0.9
OVERLAP_THRESHOLD = 0.6

# Alert settings
ALERT_SOUND_FILE = os.path.join("static", "audio.mp3")
ALERT_COOLDOWN = 3  # seconds between alert sounds

# Video
VIDEO_FILE = os.path.join("static", "video1.mp4")

# Twilio SMS Alerts
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Comma-separated list of numbers to alert, e.g. "+1234567890,+0987654321"
_numbers = os.getenv("REGISTERED_NUMBERS", "")
REGISTERED_NUMBERS = [n.strip() for n in _numbers.split(",")] if _numbers else []

# Custom alert message string
ALERT_MESSAGE = os.getenv("ALERT_MESSAGE", "🚨 ALERT: Wild Boar detected! Stay Safe!")

# Admin Interface
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
