# File: object_detection.py
from dataclasses import dataclass
from typing import Tuple, List, Optional
import cv2
import numpy as np

from ultralytics import YOLO
import logging
from config import SystemConfig


@dataclass
class DetectedObject:
    class_name: str
    confidence: float
    distance: float
    angle: float
    direction: str
    box_coords: Tuple[int, int, int, int]
    velocity: Optional[Tuple[float, float]] = None  # (dx, dy) in pixels/frame
    tracked_id: Optional[int] = None


class ObjectTracker:
    def __init__(self):
        self.tracker = cv2.TrackerKCF.create()
        self.tracked_objects = {}
        self.last_positions = {}

    def update(self, frame, detected_objects: List[DetectedObject]) -> List[DetectedObject]:
        current_objects = {}

        # Update existing trackers
        for obj_id, tracker in self.tracked_objects.items():
            success, box = tracker.update(frame)
            if success:
                current_objects[obj_id] = box

        # Calculate velocities and update tracked objects
        for obj in detected_objects:
            if obj.tracked_id in self.last_positions:
                last_pos = self.last_positions[obj.tracked_id]
                current_pos = obj.box_coords
                dx = (current_pos[0] - last_pos[0]) / 2  # Average x velocity
                dy = (current_pos[1] - last_pos[1]) / 2  # Average y velocity
                obj.velocity = (dx, dy)

            self.last_positions[obj.tracked_id] = obj.box_coords

        return detected_objects


class ObjectDetection:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.model = YOLO(config.model_path)
        self.tracker = ObjectTracker()
        self.object_history = {}  # For tracking object persistence

    def estimate_distance(self, width_pixels: float) -> float:
        return 35.0+(self.config.object_real_width * self.config.focal_length) / max(width_pixels, 1)

    def calculate_angle(self, center_x: float, img_width: int) -> float:
        dx = center_x - img_width / 2
        return np.degrees(np.arctan(dx / self.config.focal_length))

    def classify_direction(self, center_x: float, img_width: int) -> str:
        relative_pos = center_x / img_width
        if relative_pos < 0.33:
            return "Left"
        elif relative_pos < 0.66:
            return "Center"
        return "Right"

    def detect_objects(self, frame) -> List[DetectedObject]:
        results = self.model(frame, conf=self.config.confidence_threshold)
        img_width = frame.shape[1]
        detected_objects = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                width_pixels = x2 - x1
                center_x = (x1 + x2) / 2
                
                # Get the class name and replace "dog" with "person"
                class_name = self.model.names[int(box.cls[0].tolist())]
                if class_name == "dog":
                    class_name = "person"

                obj = DetectedObject(
                    class_name=class_name,  # Use the modified class_namess_name
                    confidence=float(box.conf[0].tolist()),
                    distance=self.estimate_distance(width_pixels),
                    angle=self.calculate_angle(center_x, img_width),
                    direction=self.classify_direction(center_x, img_width),
                    box_coords=(x1, y1, x2, y2),   
                    #
                    tracked_id=int(box.id[0]) if box.id is not None else None) #if box.id is not None else None
                detected_objects.append(obj)

        # Update object tracking        # Update object tracking


        return self.tracker.update(frame, detected_objects)       
        #return self.tracker.update(frame, detected_objects)
