# Just the visualization code of the zones
import cv2
import numpy as np
import math


class ThreatZoneOverlay:
    def __init__(self, threat_zones=None):
        # Define default threat zones if none are provided
        self.threat_zones = threat_zones or [
            {'min_angle': -30.0, 'max_angle': 30.0, 'min_distance': 0.0, 'max_distance': 300.0, 'color': (0, 255, 0),
             'alpha': 0.3},
            {'min_angle': -60.0, 'max_angle': -30.0, 'min_distance': 0.0, 'max_distance': 200.0, 'color': (0, 200, 255),
             'alpha': 0.3},
            {'min_angle': 30.0, 'max_angle': 60.0, 'min_distance': 0.0, 'max_distance': 200.0, 'color': (255, 200, 0),
             'alpha': 0.3},
            {'min_angle': -180.0, 'max_angle': 180.0, 'min_distance': 0.0, 'max_distance': 140.0,
             'color': (100, 100, 255), 'alpha': 0.2},
            {'min_angle': -180.0, 'max_angle': 180.0, 'min_distance': 0.0, 'max_distance': 50.0, 'color': (0, 0, 255),
             'alpha': 0.4}
        ]

    def _polar_to_cartesian(self, distance, angle_deg, frame):
        """
        Convert polar coordinates to cartesian coordinates relative to the frame center.
        """
        center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2
        angle_rad = math.radians(angle_deg)
        scaled_distance = distance * (frame.shape[0] / 400)  # Scale distance relative to frame size
        x = int(center_x + scaled_distance * math.cos(angle_rad))
        y = int(center_y - scaled_distance * math.sin(angle_rad))
        return x, y

    def overlay_threat_zones(self, frame):
        """
        Draw the defined threat zones on the provided frame with transparency.
        """
        overlay = frame.copy()  # Create a copy for overlaying
        for zone in self.threat_zones:
            min_angle, max_angle = zone['min_angle'], zone['max_angle']
            min_distance, max_distance = zone['min_distance'], zone['max_distance']
            color, alpha = zone['color'], zone.get('alpha', 0.3)

            # Compute polygon points for the zone
            points = [
                self._polar_to_cartesian(min_distance, min_angle, frame),
                self._polar_to_cartesian(max_distance, min_angle, frame),
                self._polar_to_cartesian(max_distance, max_angle, frame),
                self._polar_to_cartesian(min_distance, max_angle, frame)
            ]

            # Draw the zone
            polygon = np.array(points, np.int32)
            cv2.fillPoly(overlay, [polygon], color)
            cv2.polylines(frame, [polygon], True, color, 2)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        return frame


if __name__ == "__main__":
    # Initialize webcam feed
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video source.")
        exit()

    threat_overlay = ThreatZoneOverlay()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Resize frame for consistency
        frame = cv2.resize(frame, (640, 480))

        # Overlay threat zones
        frame = threat_overlay.overlay_threat_zones(frame)

        # Display the resulting frame
        cv2.imshow("Threat Zone Overlay", frame)

        # Break on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

'''
import numpy as np
import cv2
import math
from typing import List

class ThreatZoneVisualizer:
    def __init__(self, width=800, height=800):
        self.width = width
        self.height = height
        
        # Predefined threat zones from the original ThreatDetection class
        self.threat_zones = [
            {
                'min_angle': -30.0, 
                'max_angle': 30.0, 
                'min_distance': 0.0, 
                'max_distance': 300.0, 
                'color': (0, 255, 0),  # Green
                'name': 'Central Zone'
            },
            {
                'min_angle': -60.0, 
                'max_angle': -30.0, 
                'min_distance': 0.0, 
                'max_distance': 200.0, 
                'color': (0, 200, 255),  # Light Blue (Left)
                'name': 'Left Mid Zone'
            },
            {
                'min_angle': 30.0, 
                'max_angle': 60.0, 
                'min_distance': 0.0, 
                'max_distance': 200.0, 
                'color': (255, 200, 0),  # Orange (Right)
                'name': 'Right Mid Zone'
            },
            {
                'min_angle': -180.0, 
                'max_angle': 180.0, 
                'min_distance': 0.0, 
                'max_distance': 140.0, 
                'color': (100, 100, 255),  # Soft Blue
                'name': 'Wide Peripheral Zone'
            },
            {
                'min_angle': -180.0, 
                'max_angle': 180.0, 
                'min_distance': 0.0, 
                'max_distance': 50.0, 
                'color': (0, 0, 255),  # Red
                'name': 'Close Proximity Zone'
            }
        ]

    def _polar_to_cartesian(self, distance, angle_deg):
        """Convert polar coordinates to Cartesian coordinates."""
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Convert angle to radians
        angle_rad = math.radians(angle_deg)
        
        # Scale distance to fit visualization
        scaled_distance = distance * (self.height / 400)  # Adjust scaling factor as needed
        
        x = int(center_x + scaled_distance * math.cos(angle_rad))
        y = int(center_y - scaled_distance * math.sin(angle_rad))
        
        return x, y

    def visualize_threat_zones(self):
        """Create a visualization of threat zones."""
        # Create a blank white image
        frame = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        
        # Draw center crosshair
        center_x, center_y = self.width // 2, self.height // 2
        cv2.line(frame, (center_x, 0), (center_x, self.height), (200, 200, 200), 1)
        cv2.line(frame, (0, center_y), (self.width, center_y), (200, 200, 200), 1)

        # Visualization of threat zones
        for zone in self.threat_zones:
            min_angle = zone['min_angle']
            max_angle = zone['max_angle']
            min_distance = zone['min_distance']
            max_distance = zone['max_distance']
            color = zone['color']
            name = zone['name']

            # Create polygon points for the zone
            points = []
            for angle in [min_angle, max_angle]:
                # Minimum distance point
                x1, y1 = self._polar_to_cartesian(min_distance, angle)
                points.append((x1, y1))
                
                # Maximum distance point
                x2, y2 = self._polar_to_cartesian(max_distance, angle)
                points.append((x2, y2))

            # Ensure we have 4 points for the polygon
            if len(points) == 4:
                # Draw the zone with transparency
                overlay = frame.copy()
                pts = np.array(points, np.int32)
                cv2.fillPoly(overlay, [pts], color)
                cv2.polylines(frame, [pts], True, color, 2)
                
                # Add some transparency
                alpha = 0.3  # Transparency factor
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

                # Add zone name
                # Choose a point to place the text
                text_x = sum(p[0] for p in points) // 4
                text_y = sum(p[1] for p in points) // 4
                cv2.putText(frame, name, (text_x, text_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        # Add legend and explanation
        cv2.putText(frame, "Threat Zones Visualization", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, "Color intensity indicates threat level", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        return frame

    def save_visualization(self, filename='threat_zones_visualization.png'):
        """Save the visualization to a file."""
        frame = self.visualize_threat_zones()
        cv2.imwrite(filename, frame)
        print(f"Visualization saved to {filename}")

    def show_visualization(self):
        """Display the visualization in a window."""
        frame = self.visualize_threat_zones()
        cv2.imshow("Threat Zones Visualization", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    visualizer = ThreatZoneVisualizer()
    visualizer.save_visualization()
    visualizer.show_visualization()'''