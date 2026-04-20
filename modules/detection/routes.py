import base64
import cv2
import numpy as np
from flask import Blueprint, request, jsonify, Response

from config import MODEL_ID
from modules.detection.service import DetectionService

detection_bp = Blueprint("detection", __name__, url_prefix="/api/detection")

# Shared service instance — initialised by the app factory
_service: DetectionService | None = None


def init_service(service: DetectionService):
    """Called once at app startup to inject the service instance."""
    global _service
    _service = service


def _encode_frame(frame: np.ndarray) -> str:
    """Encode a BGR frame to a base64 JPEG string."""
    _, buf = cv2.imencode(".jpg", frame)
    return base64.b64encode(buf).decode("utf-8")


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@detection_bp.route("/status", methods=["GET"])
def status():
    """Health-check: is the model ready?"""
    ready = _service is not None and _service.is_ready()
    return jsonify({
        "status": "ready" if ready else "not_ready",
        "model": MODEL_ID,
    }), 200 if ready else 503


@detection_bp.route("/image", methods=["POST"])
def detect_image():
    """Accept an image upload and return detection results + annotated image.

    Expects multipart/form-data with a field named ``image``.
    """
    if _service is None or not _service.is_ready():
        return jsonify({"error": "Model not loaded"}), 503

    file = request.files.get("image")
    if file is None:
        return jsonify({"error": "No 'image' file provided"}), 400

    image_bytes = file.read()
    try:
        result = _service.detect_image_bytes(image_bytes)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    annotated_b64 = _encode_frame(result["annotated_frame"])

    return jsonify({
        "count": result["count"],
        "detections": result["detections"],
        "annotated_image_b64": annotated_b64,
    })


@detection_bp.route("/video", methods=["POST"])
def detect_video():
    """Accept a video upload, process every Nth frame, return summary.

    Expects multipart/form-data with a field named ``video``.
    Optional query param ``skip`` (int) — process every Nth frame (default 5).
    """
    if _service is None or not _service.is_ready():
        return jsonify({"error": "Model not loaded"}), 503

    file = request.files.get("video")
    if file is None:
        return jsonify({"error": "No 'video' file provided"}), 400

    skip = request.args.get("skip", 5, type=int)

    # Write to a temp file so OpenCV can seek
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(file.read())
    tmp.close()

    cap = cv2.VideoCapture(tmp.name)
    frame_idx = 0
    all_detections = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % skip == 0:
                result = _service.detect_frame(frame)
                if result["count"] > 0:
                    all_detections.append({
                        "frame": frame_idx,
                        "count": result["count"],
                        "detections": result["detections"],
                    })
            frame_idx += 1
    finally:
        cap.release()
        os.unlink(tmp.name)

    return jsonify({
        "total_frames": frame_idx,
        "frames_processed": frame_idx // skip + (1 if frame_idx % skip else 0),
        "frames_with_detections": len(all_detections),
        "results": all_detections,
    })


@detection_bp.route("/stream", methods=["GET"])
def stream():
    """Stream MJPEG from the server's webcam with live detection overlays.

    Open in a browser:  http://<host>:5000/api/detection/stream
    Query param ``camera`` (int) — camera index (default 0).
    """
    if _service is None or not _service.is_ready():
        return jsonify({"error": "Model not loaded"}), 503

    camera_index = request.args.get("camera", 0, type=int)

    def generate():
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                result = _service.detect_frame(frame)
                _, jpeg = cv2.imencode(".jpg", result["annotated_frame"])
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg.tobytes()
                    + b"\r\n"
                )
        finally:
            cap.release()

    return Response(
        generate(),
        mimetype= "multipart/x-mixed-replace; boundary=frame",
    )


@detection_bp.route("/frame", methods=["POST"])
def detect_frame():
    """Accept a single base64-encoded frame (from browser camera) and return detections.

    Expects JSON: {"image": "<base64 jpeg/png data>"}
    Returns JSON with count, detections, and annotated_image_b64.
    """
    if _service is None or not _service.is_ready():
        return jsonify({"error": "Model not loaded"}), 503

    data = request.get_json(silent=True)
    if not data or "image" not in data:
        return jsonify({"error": "JSON body with 'image' (base64) required"}), 400

    # Strip optional data-URI prefix  (e.g. "data:image/jpeg;base64,...")
    img_b64 = data["image"]
    if "," in img_b64:
        img_b64 = img_b64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(img_b64)
        result = _service.detect_image_bytes(image_bytes)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    annotated_b64 = _encode_frame(result["annotated_frame"])

    return jsonify({
        "count": result["count"],
        "detections": result["detections"],
        "annotated_image_b64": annotated_b64,
    })

