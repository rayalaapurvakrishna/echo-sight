# Echo-Sight: Real-Time Object Detection and Navigation for the Visually Impaired

## Project Overview
**Echo-Sight** is a groundbreaking initiative designed to assist visually impaired individuals by providing real-time object detection, spatial awareness, and voice-guided navigation in a wearable device. The project now includes two distinct modes—**Traveling Mode** for real-time navigation and safety, and **Normal Mode** for identifying objects, familiar persons, and customizable object detection settings. This system enhances independence, mobility, and safety while delivering critical information such as emergency alerts, live tracking, and more.

[Visit the Project Website](https://humorous-successes-384092.framer.app/)


## Key Features

### **1. Real-Time Object Detection & Spatial Awareness**
- **Traveling Mode**: Detects objects (vehicles, obstacles, etc.) in the user’s path, providing real-time feedback on name, distance, and position (left, right, center).
- **Normal Mode**: Detects familiar people, specific objects, and allows user-customized object specifications. Users can also define which objects or people to focus on.

### **2. Navigation Guide**
- **Traveling Mode**: Step-by-step voice-guided navigation based on integrated map services, helping users navigate through both familiar and unfamiliar locations.
- **Emergency Alerts**: Alerts predefined emergency contacts with the user’s location in case of any emergencies.
- **Live Tracking**: Caregivers or family members can monitor the user’s real-time location for added safety.

### **3. Information Access**
- **Weather and News Updates**: Real-time weather and news headlines delivered via Bluetooth earbuds, keeping users updated on current events.
  
### **4. Safety Features**
- **Obstacle Detection**: Detects critical obstacles such as potholes, vehicles, or other dangers in the environment.
- **Emergency Contact Alerts**: Automatic notifications sent to emergency contacts in case of critical incidents.
  
### **5. User Customization**
- **Normal Mode**: Customize the objects or people to be detected and specify how often alerts or updates should be given.
- **Adjustable Sensitivity**: Adjust the sensitivity of the detection system based on the user’s preferences.

---

## Modes of Operation

### **Traveling Mode**
- Designed for outdoor mobility and navigation.
- Detects moving vehicles, potholes, and traffic signs.
- Provides real-time navigation guidance, including path directions, turns, and obstacles.
- Sends emergency alerts to predefined contacts when activated.
  
### **Normal Mode**
- Used for indoor or stationary situations.
- Identifies familiar objects (e.g., furniture, appliances) and people.
- Users can set customizable alerts for specific objects or people (e.g., recognizing familiar faces or identifying specific items).
  
---

## How It Works

### 1. **Object Detection and Positioning**
- The wearable camera module captures video frames, which are processed by the **YOLOv8** model for object detection.
- Objects are classified in real-time, and their relative distance and position (left, right, straight) are calculated.

### 2. **Voice Feedback**
- Bluetooth earbuds provide real-time audio feedback about the detected objects and navigation instructions.
- The system announces objects, positions, and distances, ensuring smooth interaction between the user and their environment.

### 3. **Navigation Guidance**
- **Traveling Mode** utilizes map services for voice-guided step-by-step navigation.
- Users are guided through turns, pathways, and intersections based on real-time map data.

### 4. **Live Tracking & Emergency System**
- Caregivers can track the user's real-time location via the live tracking feature.
- The system can automatically send alerts with location data to emergency contacts if the user signals distress or encounters dangerous situations.

---


## To-Do

- [ ] Improve real-time processing performance for object detection.
- [ ] Enhance emergency alert feature with voice activation.
- [ ] Add more customization options for object detection in Normal Mode.
- [ ] Integrate more advanced route planning and location services in Traveling Mode.

---

## Impact

Echo-sight has the potential to significantly improve the quality of life for visually impaired individuals by offering them real-time guidance, object awareness, and safety mechanisms. With the addition of the two modes, users can experience customized assistance for both daily activities and traveling.
