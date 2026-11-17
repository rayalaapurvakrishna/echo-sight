import cv2
import logging
import threading

import numpy as np
import speech_recognition as sr
import queue
from datetime import datetime
import time
from object_detection import ObjectDetection, DetectedObject
from threat_detection import ThreatDetection, ThreatAssessment
from announcement import Announcer
from config import SystemConfig


class DetectionSystem:
    def __init__(self):
        self.config = SystemConfig.load_from_yaml()
        self.object_detector = ObjectDetection(self.config)
        self.threat_detector = ThreatDetection(self.config)
        self.announcer = Announcer(self.config)
        self.message_queue = queue.Queue()
        self.running = True

    def start(self):
        self.announcer.announce_startup_info()
        # Start background threads
        threading.Thread(target=self._process_announcements, daemon=True).start()
        threading.Thread(target=self._listen_for_commands, daemon=True).start()

        # Main detection loop
        self._run_detection_loop()

    def _process_announcements(self):
        while self.running:
            try:
                message = self.message_queue.get(timeout=1)
                self.announcer.announce(message)
            except queue.Empty:
                continue

    def _listen_for_commands(self):
        recognizer = sr.Recognizer()

        while self.running:
            with sr.Microphone() as source:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=2)
                    text = recognizer.recognize_google(audio).lower()

                    if "help" in text or "emergency" in text:
                        self.message_queue.put("Emergency command recognized. Sending SOS.")
                        self.announcer.send_sos()
                    elif "status" in text:
                        self._announce_status()
                    elif "weather" in text:
                        self._announce_weather()

                except (sr.WaitTimeoutError, sr.UnknownValueError):
                    continue
                except Exception as e:
                    logging.error(f"Speech recognition error: {e}")

    def _run_detection_loop(self):
        cap = cv2.VideoCapture(self.config.camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
        cap.set(cv2.CAP_PROP_FPS, self.config.fps)

        last_status_time = time.time()

        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    continue

                # Detect and assess objects
                detected_objects = self.object_detector.detect_objects(frame)

                for obj in detected_objects:
                    assessment = self.threat_detector.assess_threat(obj)

                    if assessment.threat_level in ["High", "Medium"]:
                        self.message_queue.put(assessment.recommended_action)

                    self._draw_detection_info(frame, obj, assessment)

                # Periodic status updates
                if time.time() - last_status_time > 300:  # Every 5 minutes
                    self._announce_status()
                    last_status_time = time.time()

                cv2.imshow("Detection System", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.announcer.send_sos()
                elif key == ord('w'):
                    self._announce_weather()

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.running = False

    def _draw_detection_info(self, frame, obj: DetectedObject, assessment: ThreatAssessment):
        x1, y1, x2, y2 = obj.box_coords

        # Color based on threat level
        color = {
            "High": (0, 0, 255),  # Red
            "Medium": (0, 165, 255),  # Orange
            "Low": (0, 255, 0)  # Green
        }[assessment.threat_level]

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Draw information
        info_text = f"{obj.class_name}: {obj.distance:.1f}cm"
        if obj.velocity:
            info_text += f" Speed: {np.sqrt(obj.velocity[0] ** 2 + obj.velocity[1] ** 2):.1f}px/f"
        if assessment.collision_time:
            info_text += f" TColl: {assessment.collision_time:.1f}s"

        cv2.putText(frame, info_text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def _announce_status(self):
        current_time = datetime.now().strftime("%H:%M")
        status = f"Status update at {current_time}. System running normally."
        self.message_queue.put(status)

    def _announce_weather(self):
        weather_info = self.announcer.weather_news.get_weather()
        self.message_queue.put(weather_info)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    system = DetectionSystem()
    system.start()