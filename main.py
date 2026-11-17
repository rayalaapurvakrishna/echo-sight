import cv2
import logging
import threading
import numpy as np
import  speech_recognition as sr
import queue
from datetime import datetime
import time
from object_detection import ObjectDetection, DetectedObject
from threat_detection import ThreatDetection, ThreatAssessment
from announcement import Announcer
from config import SystemConfig
from utilities import SOSSystem  # Add this import
import socket
class UDPVideoReceiver:
    def __init__(self, host="0.0.0.0", port=12345, buffer_size=65535):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.sock = None
        self.frame_buffer = bytearray()

    def setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(1.0)

    def receive_frame(self):
        try:
            data, _ = self.sock.recvfrom(self.buffer_size)
            if len(data) != 8:
                return None

            frame_size, num_packets = np.frombuffer(data, dtype=np.uint32)
            self.frame_buffer = bytearray()

            for _ in range(num_packets):
                packet_data, _ = self.sock.recvfrom(self.buffer_size)
                self.frame_buffer.extend(packet_data)

            if len(self.frame_buffer) != frame_size:
                return None

            np_arr = np.frombuffer(self.frame_buffer, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return frame

        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error receiving frame: {e}")
            return None

class DetectionSystem:
    def __init__(self):
        self.config = SystemConfig.load_from_yaml()
        self.object_detector = ObjectDetection(self.config)
        self.threat_detector = ThreatDetection(self.config)
        self.announcer = Announcer(self.config)
        self.sos_system = SOSSystem()
        self.message_queue = queue.Queue()
        self.running = True
        self.udp_receiver = UDPVideoReceiver()

    def start(self):
        self.udp_receiver.setup_socket()
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
        last_status_time = time.time()

        try:
            while self.running:
                frame = self.udp_receiver.receive_frame()
                if frame is None:
                    continue

                # Detect and assess objects
                detected_objects = self.object_detector.detect_objects(frame)

                for obj in detected_objects:
                    assessment = self.threat_detector.assess_threat(obj)
                    # Store object in SOS system
                    self.sos_system.add_detected_object(obj, frame.copy())

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
            self.udp_receiver.sock.close()
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