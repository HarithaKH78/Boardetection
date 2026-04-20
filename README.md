🐗 Boar Detection System
📌 Overview

The Boar Detection System is an AI-powered wildlife monitoring solution that detects wild boars in real-time using computer vision and deep learning. It helps reduce human-wildlife conflict by providing early alerts in agricultural and rural areas.

🎯 Problem Statement

Wild boars often damage crops and pose risks to farmers. Traditional monitoring methods are manual and ineffective. There is a need for an automated system to detect and respond quickly to such threats.

💡 Solution

This project uses the YOLOv8 deep learning model to detect wild boars from:

Live camera feeds
CCTV footage
Pre-recorded videos

Once detected, the system triggers alerts to enable immediate action.

🚀 Features
Real-time boar detection
Deep learning-based object detection (YOLOv8)
Works with live and recorded video
Instant alert system
Fast and accurate performance

🛠️ Tech Stack
Language: Python
Libraries: OpenCV, PyTorch
Model: YOLOv8
Tools: VS Code, Jupyter Notebook, Git

⚙️ How It Works
Capture video input (camera/video file)
Process frames using YOLOv8
Detect objects in each frame
Trigger alert if a boar is detected
