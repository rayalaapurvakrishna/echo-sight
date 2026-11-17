from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import numpy as np
import time
#from Adv.new.utilities import SOSSystem
from utilities import SOSSystem
from object_detection import DetectedObject
from config import SystemConfig


@dataclass
class ThreatZone:
    min_angle: float
    max_angle: float
    min_distance: float
    max_distance: float
    threat_score: int

    def calculate_dynamic_score(self, distance: float, angle: float) -> float:
        angle_center = (self.max_angle + self.min_angle) / 2
        angle_factor = 1 - (abs(angle - angle_center) / (self.max_angle - self.min_angle))
        distance_factor = np.exp(-distance / self.max_distance)
        return self.threat_score * angle_factor * distance_factor


@dataclass
class ThreatAssessment:
    threat_level: str
    object_type: str
    distance: float
    angle: float
    velocity: Optional[Tuple[float, float]]
    collision_time: Optional[float]
    recommended_action: str
    priority: int
    confidence_score: float
    threat_trajectory: List[Tuple[float, float]]


class ThreatDetection:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.threat_history = {}
        self.trajectory_buffer: Dict[str, List[Tuple[float, float, float]]] = {}
        self.current_id = 0  # Add a counter for generating unique IDs
        self.last_seen = {}  # Track when objects were last seen
        self. SOSSystem = SOSSystem()

        self.threat_zones = [
            ThreatZone(-30.0, 30.0, 0.0, 300.0, 40), # minimum angle, maximum angle, minimum distance, maximum distance, threat zone
            ThreatZone(-60.0, -30.0, 0.0, 200.0, 30),
            ThreatZone(30.0, 60.0, 0.0, 200.0, 30),
            ThreatZone(-180.0, 180.0, 0.0, 140.0, 35),
            ThreatZone(-180.0, 180.0, 0.0, 50.0, 60),
        ]

        self.object_priority = {
            'person': {
                'base_priority': 5,
                'size_factor': 1.2,
                'speed_threshold': 2.0,
                'erratic_movement_penalty': 15
            },
            'car': {
                'base_priority': 5,
                'size_factor': 1.5,
                'speed_threshold': 5.0,
                'erratic_movement_penalty': 20
            },
            'truck': {
                'base_priority': 5,
                'size_factor': 2.0,
                'speed_threshold': 4.0,
                'erratic_movement_penalty': 25
            },
            'motorcycle': {
                'base_priority': 4,
                'size_factor': 1.3,
                'speed_threshold': 8.0,
                'erratic_movement_penalty': 18
            },
            'bicycle': {
                'base_priority': 4,
                'size_factor': 1.2,
                'speed_threshold': 3.0,
                'erratic_movement_penalty': 15
            },
            'dog': {
                'base_priority': 3,
                'size_factor': 1.1,
                'speed_threshold': 3.0,
                'erratic_movement_penalty': 12
            },
            'cat': {
                'base_priority': 2,
                'size_factor': 1.0,
                'speed_threshold': 2.0,
                'erratic_movement_penalty': 10
            }
        }

    def _generate_object_id(self, obj: DetectedObject) -> str:
        """Generate a unique ID for an object based on its properties."""
        self.current_id += 1
        return f"{obj.class_name}_{self.current_id}"

    def _get_object_id(self, obj: DetectedObject) -> str:
        """Get or create an object ID based on its position and class."""
        # Clean up old trajectories
        current_time = time.time()
        for obj_id in list(self.last_seen.keys()):
            if current_time - self.last_seen[obj_id] > 8.0:  # Remove after 8 seconds
                self.last_seen.pop(obj_id)
                self.trajectory_buffer.pop(obj_id, None)

        # Try to match with existing objects
        for obj_id in self.trajectory_buffer:
            if len(self.trajectory_buffer[obj_id]) > 0:
                last_pos = self.trajectory_buffer[obj_id][-1]
                # If position and class match within threshold, consider it the same object
                if (abs(last_pos[0] - obj.distance) < 50 and  # 50cm threshold
                        abs(last_pos[1] - obj.angle) < 15 and  # 15 degrees threshold
                        obj_id.startswith(obj.class_name)):
                    return obj_id

        # If no match found, generate new ID
        new_id = self._generate_object_id(obj)
        return new_id

    def estimate_collision_time(self, obj: DetectedObject) -> Optional[float]:
        if not obj.velocity:
            return None

        dx, dy = obj.velocity
        if abs(dx) <= 0.1 and abs(dy) <= 0.1:
            return None

        relative_velocity = np.sqrt(dx ** 2 + dy ** 2)
        velocity_cms = relative_velocity * (obj.distance / 100)  #  distance to velocity calculation

        obj_id = self._get_object_id(obj)
        if obj_id in self.trajectory_buffer:
            positions = self.trajectory_buffer[obj_id]
            if len(positions) >= 3:
                recent_positions = positions[-3:]
                accelerations = []
                for i in range(1, len(recent_positions) - 1):
                    t1, t2 = recent_positions[i - 1][2], recent_positions[i + 1][2]
                    v1 = (recent_positions[i][0] - recent_positions[i - 1][0]) / (t2 - t1)
                    v2 = (recent_positions[i + 1][0] - recent_positions[i][0]) / (t2 - t1)
                    accelerations.append((v2 - v1) / (t2 - t1))

                if accelerations:
                    avg_acceleration = np.mean(accelerations)
                    a = 0.5 * avg_acceleration
                    b = velocity_cms
                    c = -obj.distance
                    discriminant = b ** 2 - 4 * a * c
                    if discriminant >= 0:
                        t1 = (-b + np.sqrt(discriminant)) / (2 * a)
                        t2 = (-b - np.sqrt(discriminant)) / (2 * a)
                        return min(t for t in [t1, t2] if t > 0) if any(t > 0 for t in [t1, t2]) else None

        return obj.distance / velocity_cms if velocity_cms > 0 else None

    def calculate_zone_threat(self, obj: DetectedObject) -> float:
        total_threat_score = 0
        obj_id = self._get_object_id(obj)

        obj_props = self.object_priority.get(obj.class_name.lower(), {
            'base_priority': 1,
            'size_factor': 1.0,
            'speed_threshold': 2.0,
            'erratic_movement_penalty': 10
        })

        speed = 0
        if obj.velocity:
            dx, dy = obj.velocity
            speed = np.sqrt(dx ** 2 + dy ** 2)

            if obj_id in self.trajectory_buffer:
                positions = self.trajectory_buffer[obj_id]
                if len(positions) >= 3:
                    recent_positions = positions[-3:]
                    direction_changes = 0
                    for i in range(1, len(recent_positions) - 1):
                        prev_dir = np.arctan2(recent_positions[i][1] - recent_positions[i - 1][1],
                                              recent_positions[i][0] - recent_positions[i - 1][0])
                        curr_dir = np.arctan2(recent_positions[i + 1][1] - recent_positions[i][1],
                                              recent_positions[i + 1][0] - recent_positions[i][0])
                        if abs(curr_dir - prev_dir) > np.pi / 4:
                            direction_changes += 1

                    if direction_changes > 0:
                        total_threat_score += obj_props['erratic_movement_penalty'] * direction_changes

        for zone in self.threat_zones:
            if (zone.min_angle <= obj.angle <= zone.max_angle and
                    zone.min_distance <= obj.distance <= zone.max_distance):

                zone_score = zone.calculate_dynamic_score(obj.distance, obj.angle)
                zone_score *= obj_props['size_factor']

                if speed > obj_props['speed_threshold']:
                    speed_factor = (speed / obj_props['speed_threshold'])
                    zone_score *= speed_factor

                if obj.velocity:
                    dx, dy = obj.velocity
                    velocity_angle = np.arctan2(dy, dx)
                    path_angle = np.arctan2(-obj.distance * np.sin(np.radians(obj.angle)),
                                            -obj.distance * np.cos(np.radians(obj.angle)))
                    angle_diff = abs(velocity_angle - path_angle)
                    direction_factor = 1 + np.cos(angle_diff)
                    zone_score *= direction_factor

                total_threat_score += zone_score

        return total_threat_score

    def assess_threat(self, obj: DetectedObject) -> ThreatAssessment:
        # Get or generate object ID
        obj_id = self._get_object_id(obj)

        # Update trajectory buffer
        current_time = time.time()
        if obj_id not in self.trajectory_buffer:
            self.trajectory_buffer[obj_id] = []

        self.trajectory_buffer[obj_id].append((obj.distance, obj.angle, current_time))
        self.last_seen[obj_id] = current_time

        # Keep only recent history
        self.trajectory_buffer[obj_id] = self.trajectory_buffer[obj_id][-10:]

        collision_time = self.estimate_collision_time(obj)
        threat_score = self.calculate_zone_threat(obj)
        confidence_score = self._calculate_confidence_score(obj)

        if threat_score >= 70 and confidence_score > 0.7:
            threat_level = "High"
            priority = 3
            action = self._generate_high_threat_action(obj, collision_time, True)
        elif threat_score >= 40 or (threat_score >= 30 and confidence_score > 0.8):
            threat_level = "Medium"
            priority = 2
            action = self._generate_medium_threat_action(obj, collision_time, True)
        else:
            threat_level = "Low"
            priority = 1
            action = ""

        trajectory = [(pos[0], pos[1]) for pos in self.trajectory_buffer[obj_id]]

        return ThreatAssessment(
            threat_level=threat_level,
            object_type=obj.class_name,
            distance=obj.distance,
            angle=obj.angle,
            velocity=obj.velocity,
            collision_time=collision_time,
            recommended_action=action,
            priority=priority,
            confidence_score=confidence_score,
            threat_trajectory=trajectory
        )

    def _calculate_confidence_score(self, obj: DetectedObject) -> float:
        obj_id = self._get_object_id(obj)
        confidence = getattr(obj, 'detection_score', 0.5)

        if obj_id in self.trajectory_buffer:
            history_length = len(self.trajectory_buffer[obj_id])
            if history_length >= 5:
                confidence *= 1.2

            if history_length >= 3:
                positions = self.trajectory_buffer[obj_id]
                velocity_changes = []
                for i in range(1, len(positions) - 1):
                    # Check for minimum time delta to avoid division by zero
                    time_delta1 = positions[i][2] - positions[i - 1][2]
                    time_delta2 = positions[i + 1][2] - positions[i][2]

                    # Only calculate velocity changes if time deltas are significant
                    if time_delta1 > 1e-6 and time_delta2 > 1e-6:
                        v1 = (positions[i][0] - positions[i - 1][0]) / time_delta1
                        v2 = (positions[i + 1][0] - positions[i][0]) / time_delta2
                        if v1>0 and v2>0:
                          velocity_changes.append(abs(v2 - v1))


                if velocity_changes:
                    smoothness = 1 / (1 + np.mean(velocity_changes))
                    confidence *= (0.8 + 0.4 * smoothness)

        return min(max(confidence, 0.0), 1.0)

    def _generate_high_threat_action(self, obj: DetectedObject, collision_time: Optional[float],
                                     moving_towards: bool) -> str:
        direction = "ahead" if abs(obj.angle) < 30 else \
            "on your left" if obj.angle < 0 else "on your right"

        action = f"Warning! {obj.class_name} {direction} at {obj.distance:.0f} centimeters"

        if moving_towards:
            action += " moving toward you"
            if collision_time:
                action += f", potential collision in {collision_time:.1f} seconds"

        return action

    def _generate_medium_threat_action(self, obj: DetectedObject, collision_time: Optional[float],
                                       moving_towards: bool) -> str:
        if moving_towards:
            action = f"Caution! {obj.class_name} approaching at {obj.distance:.0f} centimeters"
            if obj.velocity:
                dx, dy = obj.velocity
                speed = np.sqrt(dx ** 2 + dy ** 2)
                action += f", speed approximately {speed:.1f} units per second"
            return action
        return ""