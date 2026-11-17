# File: config.py
from dataclasses import dataclass
from typing import Dict, Any
import yaml
import os


@dataclass
class SystemConfig:
    """Configuration settings for the detection system"""
    # Camera settings
    camera_id: int = 0
    frame_width: int = 640
    frame_height: int = 480
    fps: int = 30

    # Detection settings
    model_path: str = r"C:\Users\nithi\python\dood\yolov8s.pt"
    confidence_threshold: float = 0.5
    focal_length: float = 840
    object_real_width: float = 6.3

    # Threat assessment settings
    high_threat_angle: float = 30.0
    high_threat_distance: float = 200.0
    medium_threat_distance: float = 100.0

    # Audio settings
    speech_rate: int = 150
    volume: float = 1.0

    # API credentials
    weather_api_key: str = ""   #ac92624c486840e5a0e91217240211
    news_api_key: str = ""      #e29d3d2f188f452699a4e77ab459c943
    twilio_account_sid: str = ""#ACbf3a84933c8187f5933baec382de3945
    twilio_auth_token: str = "" #79bd543b69a4166a2d64634e21e58d57
    emergency_number: str = ""  #+919347632259
    twilio_number: str = ""     #14155238886

    @classmethod
    def load_from_yaml(cls, path: str = "config.yaml") -> 'SystemConfig':
        if os.path.exists(path):
            with open(path, 'r') as f:
                config_dict = yaml.safe_load(f)
                return cls(**config_dict)
        return cls()