import time
from datetime import datetime

import cv2
import numpy as np
import pygame
import supervision as sv
from inference import get_model

from config import (
    ROBOFLOW_API_KEY,
    MODEL_ID,
    CONFIDENCE_THRESHOLD,
    OVERLAP_THRESHOLD,
    ALERT_SOUND_FILE,
    ALERT_COOLDOWN,
    ALERT_MESSAGE,
)


class DetectionService:
    """Wraps Roboflow model loading and inference for boar detection."""

    def __init__(self):
        self.model = None
        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()

        # Audio alert state
        pygame.mixer.init()
        self._alert_sound = pygame.mixer.Sound(ALERT_SOUND_FILE)
        self._last_alert_time = 0

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------
    def load_model(self):
        """Load the Roboflow model. Call once at startup."""
        self.model = get_model(model_id=MODEL_ID, api_key=ROBOFLOW_API_KEY)

    def is_ready(self) -> bool:
        return self.model is not None

    # ------------------------------------------------------------------
    # Core inference
    # ------------------------------------------------------------------
    def detect_frame(self, frame: np.ndarray) -> dict:
        """Run inference on a single BGR frame.

        Returns a dict with:
          - detections: list of dicts (class_name, confidence, bbox)
          - annotated_frame: the frame with bounding boxes drawn (np.ndarray)
        """
        if not self.is_ready():
            raise RuntimeError("Model not loaded. Call load_model() first.")

        results = self.model.infer(
            frame,
            confidence=CONFIDENCE_THRESHOLD,
            iou_threshold=OVERLAP_THRESHOLD,
        )[0]

        detections = sv.Detections.from_inference(results)

        # Build structured detection list
        detection_list = []
        for class_name, confidence, xyxy in zip(
            detections["class_name"],
            detections.confidence,
            detections.xyxy,
        ):
            detection_list.append(
                {
                    "class_name": class_name,
                    "confidence": round(float(confidence), 4),
                    "bbox": [round(float(c), 2) for c in xyxy],
                }
            )

        # Annotate
        labels = [
            f"{d['class_name']} {d['confidence']:.0%}" for d in detection_list
        ]
        annotated = self.box_annotator.annotate(scene=frame.copy(), detections=detections)
        annotated = self.label_annotator.annotate(
            scene=annotated, detections=detections, labels=labels
        )

        # Play alert sound and send SMS on the server if boar detected
        if detection_list:
            from database import db_manager
            
            # --- 1. Log to MongoDB (Historical Count) ---
            db_manager.insert_detection({
                "timestamp": datetime.utcnow(),
                "count": len(detection_list),
                "model_id": MODEL_ID
            })

            # --- 2. Live Feed Feedback Loop (Correct Prediction) ---
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            db_manager.upsert_prediction(today_str, "High", 1.0)

            # --- 3. Trigger Alerts ---
            now = time.time()
            if now - self._last_alert_time >= ALERT_COOLDOWN:
                self._last_alert_time = now
                self._alert_sound.play()
                
                # Send SMS alert in a non-blocking way (simple fire-and-forget for now)
                from modules.alert.service import alert_service
                if alert_service.is_enabled():
                    # In a production app, this should be sent to a background worker queue (like Celery)
                    # to prevent blocking the video frame processing loop. 
                    import threading
                    threading.Thread(
                        target=alert_service.send_sms_alert, 
                        args=(ALERT_MESSAGE,),
                        daemon=True
                    ).start()

        return {
            "detections": detection_list,
            "count": len(detection_list),
            "annotated_frame": annotated,
        }

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def detect_image_bytes(self, image_bytes: bytes) -> dict:
        """Decode raw image bytes and run detection."""
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Could not decode image bytes.")
        return self.detect_frame(frame)

    def detect_image_path(self, path: str) -> dict:
        """Load an image from disk and run detection."""
        frame = cv2.imread(path)
        if frame is None:
            raise FileNotFoundError(f"Cannot read image at '{path}'")
        return self.detect_frame(frame)
