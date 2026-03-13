# 🤖 WALL-E: Wireless Autonomous Localization & Logistics Explorer

## 🎯 The Problem We Are Solving
Navigating and mapping unknown or hazardous environments typically requires expensive, proprietary robotics equipment (like LiDAR or commercial SLAM modules). 
Our project democratizes autonomous exploration by building a **low-cost, vision-enabled mapping robot** using off-the-shelf microcontrollers, custom-fabricated hardware, and a hybrid edge/local-compute network architecture. WALL-E is capable of manual remote-controlled scouting, autonomous obstacle avoidance, real-time video streaming, and precise odometry tracking for future ArUco marker mapping.

## ✨ Key Features
* **Hybrid Control Modes:** Seamlessly switch between Manual (Bluetooth Gamepad) and Autonomous (Obstacle Avoidance) modes on the fly.
* **Custom Odometry Hardware:** We engineered and fabricated custom 10-hole wooden encoder disks, paired with LM393 optocouplers, to track wheel ticks and calculate exact real-world distances.
* **Real-Time Telemetry:** The robot's edge-computer (ESP32) calculates distance, wheel ticks, and system state, broadcasting it wirelessly via UDP to a mission control dashboard.
* **Vision & Edge Streaming:** An independent ESP32-CAM node streams live HTTP video to the laptop for spatial awareness and computer vision processing (OpenCV).
* **Animatronic Feedback:** 2-Axis servo-driven "head" for realistic, dynamic panning and tilting during exploration.

---

## 🛠️ Hardware Architecture
We utilized a distributed processing approach to prevent bottlenecking a single microcontroller:
* **The Brain (ESP32 NodeMCU):** Handles motor PWM, hardware interrupts (encoders), ultrasonic distance polling, and BLE Gamepad hosting.
* **The Eyes (ESP32-CAM):** Dedicated entirely to capturing and streaming high-framerate video over a local Wi-Fi hotspot.
* **The Muscle (L298N + 12V Motors):** 12V 300RPM heavy-duty motors driven by an L298N H-Bridge.
* **The Sensors:** * HC-SR04 Ultrasonic Sensor (Front collision detection)
  * 2x LM393 Speed Sensors with **Custom 10-Hole Wooden Encoder Disks**
  * 2x SG90 Micro Servos (Pan/Tilt head mechanism)
* **Controller:** Standard Bluetooth Gamepad (via Bluepad32 library).

---

## 💻 Software & Network Topology
Our software stack bridges embedded C++ and Python via a mobile hotspot router:
### Microcontroller (C++ / Arduino IDE)
* `Bluepad32` for Bluetooth controller hosting.
* `ESP32Servo` for jitter-free hardware timer PWM.
* `WiFiUDP` for broadcasting high-speed, connectionless telemetry without crashing the main loop.

### Mission Control Dashboard (Python 3)
* `OpenCV (cv2)` captures the HTTP MJPEG stream from the ESP32-CAM.
* `Socket` listens asynchronously for UDP broadcasts.
* Overlays real-time encoder ticks, safety distances, and driving modes directly onto the HUD.

### 📡 The "Invisible Cable" Network
To bypass ESP32 Bluetooth limitations, we designed a localized network:
1. **Gamepad** ➔ *(Bluetooth BLE)* ➔ **Main ESP32**
2. **ESP32-CAM** ➔ *(Wi-Fi HTTP)* ➔ **Phone Hotspot** ➔ **Laptop Python Script**
3. **Main ESP32** ➔ *(Wi-Fi UDP Blast)* ➔ **Phone Hotspot** ➔ **Laptop Python Script**

---

## 🚀 How to Run the Project

### 1. Hardware Boot Sequence
1. Turn on the local Wi-Fi Hotspot (configured to the SSID/Password in the ESP32 sketch).
2. Connect the 12V Power Supply to the L298N (which steps down 5V to the ESP32 nodes).
3. Turn on the Bluetooth Gamepad (will auto-pair to the ESP32).
4. Verify both the Main ESP32 and ESP32-CAM have connected to the hotspot.

### 2. Software Launch
1. Check the router/hotspot settings to find the IP address assigned to the ESP32-CAM.
2. Open `dashboard.py` and update the `CAM_IP` variable.
3. Install dependencies and run the Python script:
   ```bash
   pip install opencv-python
   python dashboard.py